"""Spark job for EMR Serverless. Input and output are S3 URIs."""

import argparse
import json
import time
from datetime import datetime, timezone

from pyspark.sql import SparkSession, functions as F


def compute_stats(spark, input_uri):
    """Clean directed edges, count both degrees and check the global totals."""
    lines = spark.read.text(input_uri).select(F.trim("value").alias("line")).cache()
    raw_lines = lines.count()
    blank_lines = lines.filter(F.col("line").rlike(r"^\s*$")).count()
    pattern = r"^\s*([0-9]+)\s+([0-9]+)\s*$"
    valid = lines.filter(F.col("line").rlike(pattern)).select(
        F.regexp_extract("line", pattern, 1).alias("src"),
        F.regexp_extract("line", pattern, 2).alias("dst"),
    )
    valid_edges = valid.count()
    edges = valid.dropDuplicates(["src", "dst"]).cache()
    unique_edges = edges.count()
    if not unique_edges:
        raise ValueError("The dataset contains no valid relationships.")

    # src follows dst: src gains one followee, dst gains one follower.
    followees = edges.groupBy("src").count().select(
        F.col("src").alias("user_id"), F.col("count").alias("followees")
    )
    followers = edges.groupBy("dst").count().select(
        F.col("dst").alias("user_id"), F.col("count").alias("followers")
    )
    # Retain IDs present in only one column, with zero for the missing count.
    stats = (
        followers.join(followees, "user_id", "full_outer")
        .fillna(0, subset=["followers", "followees"])
        .select("user_id", "followers", "followees")
        .cache()
    )
    totals = stats.agg(
        F.count("*").alias("users"),
        F.sum("followers").alias("total_followers"),
        F.sum("followees").alias("total_followees"),
    ).first().asDict()
    if totals["total_followers"] != unique_edges or totals["total_followees"] != unique_edges:
        raise RuntimeError("Degree sums must both equal the unique relationship count.")

    return stats, {
        "raw_lines": raw_lines,
        "blank_lines": blank_lines,
        "invalid_lines": raw_lines - blank_lines - valid_edges,
        "valid_edges": valid_edges,
        "unique_edges": unique_edges,
        "duplicate_edges_removed": valid_edges - unique_edges,
        **totals,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="s3://bucket/input/twitter_combined.txt")
    parser.add_argument("--output", required=True, help="A new s3://bucket/output/runs/... prefix")
    args = parser.parse_args()
    started = time.perf_counter()

    # EMR supplies the cluster master and Spark installation. Do not set local[2].
    spark = (
        SparkSession.builder.appName("twitter-network-analyzer")
        .config("spark.sql.shuffle.partitions", "4")
        .getOrCreate()
    )
    spark.sparkContext.setLogLevel("WARN")
    try:
        stats, metrics = compute_stats(spark, args.input)
        output = args.output.rstrip("/")
        # Use a fresh run prefix, preserving previous runs and avoiding stale parts.
        stats.write.mode("errorifexists").option("header", True).csv(output + "/users")
        metrics.update({
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "spark_version": spark.version,
            "spark_master": spark.sparkContext.master,
            "input_source": args.input,
            "output_location": output,
            "elapsed_seconds": round(time.perf_counter() - started, 2),
        })
        spark.createDataFrame([metrics]).coalesce(1).write.mode("errorifexists").json(output + "/metrics")
        print("ANALYSIS_COMPLETE " + json.dumps(metrics, sort_keys=True))
        required = stats.filter(F.col("user_id").isin("214328887", "107830991"))
        required.show(truncate=False)
    finally:
        spark.stop()
