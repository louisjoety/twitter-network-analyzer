"""Local web app coordinating EMR Serverless analysis and S3 results."""

import argparse
import csv
import io
import json
import logging
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

import boto3
import uvicorn
from botocore.exceptions import ClientError
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

BASE_DIR = Path(__file__).resolve().parent.parent
LOGGER = logging.getLogger("twitter-network-analyzer")


def read_config(path):
    config = json.loads(path.read_text(encoding="utf-8-sig"))
    for key in ("region", "bucket", "application_id", "execution_role_arn"):
        value = config.get(key)
        if not isinstance(value, str) or not value or "YOUR_" in value:
            raise ValueError(f"Fill in '{key}' in {path.name}.")
    for key, default in {
        "input_key": "input/twitter_combined.txt", "script_key": "scripts/analysis.py",
        "output_prefix": "output", "logs_prefix": "logs",
    }.items():
        config.setdefault(key, default)
        if not isinstance(config[key], str) or not config[key].strip("/"):
            raise ValueError(f"'{key}' must be a nonempty S3 key/prefix.")
        config[key] = config[key].strip("/")
    return config


def read_text(s3, bucket, key):
    with s3.get_object(Bucket=bucket, Key=key)["Body"] as body:
        return body.read().decode("utf-8")


def part_keys(s3, bucket, prefix, suffix):
    keys = []
    for page in s3.get_paginator("list_objects_v2").paginate(Bucket=bucket, Prefix=prefix):
        keys.extend(
            item["Key"] for item in page.get("Contents", [])
            if Path(item["Key"]).name.startswith("part-") and item["Key"].endswith(suffix)
        )
    return sorted(keys)


def load_results(s3, config, manifest):
    bucket = config["bucket"]
    prefix = manifest["run_prefix"].rstrip("/")
    csv_keys = part_keys(s3, bucket, prefix + "/users/", ".csv")
    metrics_keys = part_keys(s3, bucket, prefix + "/metrics/", ".json")
    if not csv_keys or len(metrics_keys) != 1:
        raise ValueError("Incomplete EMR output: expected CSV parts and one metrics JSON part.")
    rows = []
    for key in csv_keys:
        reader = csv.DictReader(io.StringIO(read_text(s3, bucket, key)))
        if reader.fieldnames != ["user_id", "followers", "followees"]:
            raise ValueError("Unexpected CSV columns in EMR output.")
        for row in reader:
            user_id = row["user_id"]
            if not user_id.isascii() or not user_id.isdecimal():
                raise ValueError("Expected a numeric user ID in EMR output.")
            followers, followees = int(row["followers"]), int(row["followees"])
            if followers < 0 or followees < 0:
                raise ValueError("Follower and followee counts must be nonnegative.")
            rows.append({"user_id": user_id, "followers": followers, "followees": followees})
    rows.sort(key=lambda row: (len(row["user_id"]), row["user_id"]))
    metrics = json.loads(read_text(s3, bucket, metrics_keys[0]))
    if len(rows) != metrics["users"] or len({row["user_id"] for row in rows}) != len(rows):
        raise ValueError("Result row count does not match the analysis metrics.")
    for field in ("followers", "followees"):
        if sum(row[field] for row in rows) != metrics["unique_edges"]:
            raise ValueError(f"Invalid {field} total in the saved results.")
    metrics.update({
        "mode": "emr", "region": config["region"], "job_run_id": manifest["job_run_id"],
        "application_id": config["application_id"],
    })
    return rows, metrics


def run_job(session, config):
    s3 = session.client("s3")
    emr = session.client("emr-serverless")
    bucket = config["bucket"]
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_prefix = f"{config['output_prefix']}/runs/{stamp}-{uuid.uuid4().hex[:8]}"
    script_uri = f"s3://{bucket}/{config['script_key']}"
    LOGGER.info("Uploading Spark script to %s", script_uri)
    s3.upload_file(str(BASE_DIR / "analysis" / "job.py"), bucket, config["script_key"])
    response = emr.start_job_run(
        applicationId=config["application_id"], executionRoleArn=config["execution_role_arn"],
        clientToken=str(uuid.uuid4()), name="twitter-network-analyzer", executionTimeoutMinutes=20,
        jobDriver={"sparkSubmit": {
            "entryPoint": script_uri,
            "entryPointArguments": ["--input", f"s3://{bucket}/{config['input_key']}",
                                    "--output", f"s3://{bucket}/{run_prefix}"],
            "sparkSubmitParameters": (
                "--conf spark.dynamicAllocation.enabled=false "
                "--conf spark.executor.instances=2 --conf spark.executor.cores=1 "
                "--conf spark.executor.memory=4g --conf spark.driver.cores=1 "
                "--conf spark.driver.memory=4g"
            ),
        }},
        configurationOverrides={"monitoringConfiguration": {"s3MonitoringConfiguration": {
            "logUri": f"s3://{bucket}/{config['logs_prefix']}/"
        }}},
    )
    job_id = response["jobRunId"]
    LOGGER.info("EMR job submitted: %s", job_id)
    terminal = False
    try:
        deadline = time.monotonic() + 30 * 60
        previous = None
        while time.monotonic() < deadline:
            job = emr.get_job_run(applicationId=config["application_id"], jobRunId=job_id)["jobRun"]
            state = job["state"]
            if state != previous:
                LOGGER.info("EMR job %s: %s", job_id, state)
                previous = state
            if state == "SUCCESS":
                terminal = True
                break
            if state in {"FAILED", "CANCELLED"}:
                terminal = True
                raise RuntimeError(f"EMR job {state}: {job.get('stateDetails', 'See the EMR job logs.')}")
            time.sleep(10)
        else:
            raise TimeoutError("EMR job did not finish within 30 minutes.")
    finally:
        if not terminal:
            LOGGER.warning("Cancelling unfinished EMR job %s", job_id)
            try:
                emr.cancel_job_run(applicationId=config["application_id"], jobRunId=job_id)
            except Exception:
                LOGGER.exception("Could not cancel the job. Check it in the EMR console.")

    manifest = {"run_prefix": run_prefix, "job_run_id": job_id, "completed_at": datetime.now(timezone.utc).isoformat()}
    rows, metrics = load_results(s3, config, manifest)
    # Publish the pointer only after a successful job and validated result readback.
    s3.put_object(Bucket=bucket, Key=f"{config['output_prefix']}/latest.json",
                  Body=json.dumps(manifest).encode("utf-8"), ContentType="application/json")
    return rows, metrics


def saved_results(session, config):
    s3 = session.client("s3")
    try:
        manifest = json.loads(read_text(s3, config["bucket"], f"{config['output_prefix']}/latest.json"))
    except ClientError as failure:
        if failure.response["Error"]["Code"] in {"NoSuchKey", "404"}:
            raise ValueError("No saved analysis found. Run once with --run-job.") from failure
        raise
    return load_results(s3, config, manifest)


def create_app(rows, metrics):
    by_id = {row["user_id"]: row for row in rows}
    application = FastAPI(title="twitter-network-analyzer")
    frontend = BASE_DIR / "frontend" / "dist"
    if (frontend / "assets").is_dir():
        application.mount("/assets", StaticFiles(directory=frontend / "assets"), name="assets")

    @application.get("/", include_in_schema=False)
    def home():
        if not (frontend / "index.html").is_file():
            raise HTTPException(status_code=503, detail="Build the frontend with npm run build, or open the Vite dev server.")
        return FileResponse(frontend / "index.html")

    @application.get("/api/health")
    def health():
        return {"status": "ready", **metrics}

    @application.get("/api/users")
    def list_users(offset: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=200)):
        return {"items": rows[offset:offset + limit], "offset": offset, "limit": limit, "total": len(rows)}

    @application.get("/api/users/{user_id}")
    def get_user(user_id: str):
        if not user_id.isascii() or not user_id.isdecimal():
            raise HTTPException(status_code=400, detail="Use a numeric user ID.")
        if user_id not in by_id:
            raise HTTPException(status_code=404, detail="User not found in this dataset.")
        return by_id[user_id]

    return application


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=BASE_DIR / "config" / "local.json")
    parser.add_argument("--profile", help="Your existing AWS CLI profile; omit to use the default credential chain")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--run-job", action="store_true", help="Run a new EMR job before starting the web app")
    mode.add_argument("--demo", action="store_true", help="Preview the UI using the bundled sample graph; no AWS calls")
    mode.add_argument("--offline", action="store_true", help="Use the locally saved cloud results; no AWS calls")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    try:
        cache_file = BASE_DIR / "runtime" / "results.json"
        if args.demo:
            with (BASE_DIR / "tests" / "fixtures" / "users.csv").open(newline="", encoding="utf-8") as handle:
                rows = [{"user_id": row["user_id"], "followers": int(row["followers"]), "followees": int(row["followees"])} for row in csv.DictReader(handle)]
            metrics = {"mode": "demo", "users": len(rows), "unique_edges": sum(row["followers"] for row in rows)}
        elif args.offline:
            if not cache_file.is_file():
                raise ValueError("No local results yet. Complete one cloud run or load saved S3 results first.")
            cached = json.loads(cache_file.read_text(encoding="utf-8"))
            rows, metrics = cached["rows"], {**cached["metrics"], "offline": True}
        else:
            config = read_config(args.config)
            session = boto3.Session(profile_name=args.profile, region_name=config["region"])
            rows, metrics = run_job(session, config) if args.run_job else saved_results(session, config)
            cache_file.parent.mkdir(parents=True, exist_ok=True)
            cache_file.write_text(json.dumps({"rows": rows, "metrics": metrics}), encoding="utf-8")
    except KeyboardInterrupt:
        raise SystemExit(130)
    except Exception as failure:
        parser.exit(1, f"Startup failed: {failure}\n")
    LOGGER.info("Loaded analysis:\n%s", json.dumps(metrics, indent=2))
    lookup = {row["user_id"]: row for row in rows}
    for user_id in ("214328887", "107830991"):
        LOGGER.info("Required user %s: %s", user_id, lookup.get(user_id, "not in dataset"))
    LOGGER.info("Open http://localhost:%s/", args.port)
    uvicorn.run(create_app(rows, metrics), host=args.host, port=args.port)


if __name__ == "__main__":
    main()
