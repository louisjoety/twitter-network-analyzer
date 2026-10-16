"""Startup modes must not accidentally submit paid jobs."""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from backend.app import main, read_config
from tests.support import CONFIG, METRICS, FakeSession, fixture_rows


class StartupTests(unittest.TestCase):
    def test_offline_mode_reads_cache_without_aws(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "runtime").mkdir()
            (root / "runtime/results.json").write_text(json.dumps({"rows": fixture_rows(), "metrics": METRICS}))
            with patch("backend.app.BASE_DIR", root), patch("backend.app.boto3.Session", side_effect=AssertionError("AWS accessed")), patch("backend.app.uvicorn.run") as serve:
                main(["--offline"])
            with TestClient(serve.call_args.args[0]) as client:
                self.assertTrue(client.get("/api/health").json()["offline"])
                self.assertEqual(client.get("/api/users/200").json()["followers"], 2)

    def test_missing_offline_cache_fails_without_aws(self):
        with tempfile.TemporaryDirectory() as folder, patch("backend.app.BASE_DIR", Path(folder)), patch("backend.app.boto3.Session", side_effect=AssertionError("AWS accessed")):
            with self.assertRaises(SystemExit) as failure:
                main(["--offline"])
            self.assertEqual(failure.exception.code, 1)

    def test_demo_mode_is_explicit_and_does_not_access_aws(self):
        with patch("backend.app.boto3.Session", side_effect=AssertionError("AWS accessed")), patch("backend.app.uvicorn.run") as serve:
            main(["--demo"])
        with TestClient(serve.call_args.args[0]) as client:
            self.assertEqual(client.get("/api/health").json()["mode"], "demo")

    def test_paid_and_offline_modes_are_mutually_exclusive(self):
        with self.assertRaises(SystemExit) as failure:
            main(["--offline", "--run-job"])
        self.assertEqual(failure.exception.code, 2)

    def test_configuration_rejects_placeholders(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "config.json"
            path.write_text(json.dumps({**CONFIG, "application_id": "YOUR_APPLICATION_ID"}))
            with self.assertRaisesRegex(ValueError, "application_id"):
                read_config(path)

    def test_configuration_normalizes_prefix_slashes(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "config.json"
            path.write_text(json.dumps({**CONFIG, "output_prefix": "/output/"}))
            self.assertEqual(read_config(path)["output_prefix"], "output")

    def test_default_startup_loads_saved_results_and_creates_offline_cache(self):
        session = FakeSession()
        session.s3.add_output("output/runs/completed")
        session.s3.objects["output/latest.json"] = json.dumps({
            "run_prefix": "output/runs/completed", "job_run_id": "completed-job",
        }).encode()
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "config").mkdir()
            (root / "config/local.json").write_text(json.dumps(CONFIG))
            with patch("backend.app.BASE_DIR", root), patch("backend.app.boto3.Session", return_value=session) as connect, patch("backend.app.uvicorn.run"):
                main(["--profile", "test-profile"])
            connect.assert_called_once_with(profile_name="test-profile", region_name=CONFIG["region"])
            self.assertEqual(session.client_requests, ["s3"])
            self.assertEqual(session.emr.submissions, [])
            cached = json.loads((root / "runtime/results.json").read_text())
            self.assertEqual(cached["rows"], fixture_rows())
            self.assertEqual(cached["metrics"]["job_run_id"], "completed-job")
