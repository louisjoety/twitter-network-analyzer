"""API contracts and static frontend serving, using deterministic fixtures."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from backend.app import create_app
from tests.support import METRICS, fixture_rows


class ApiTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(create_app(fixture_rows(), {**METRICS, "mode": "emr", "job_run_id": "testjob123"}))

    def tearDown(self):
        self.client.close()

    def test_health_exposes_analysis_provenance(self):
        body = self.client.get("/api/health").json()
        self.assertEqual((body["status"], body["mode"], body["users"], body["job_run_id"]),
                         ("ready", "emr", 5, "testjob123"))

    def test_user_lookup_returns_follower_and_followee_counts(self):
        self.assertEqual(self.client.get("/api/users/200").json(),
                         {"user_id": "200", "followers": 2, "followees": 2})

    def test_one_sided_users_retain_zero_counts(self):
        self.assertEqual(self.client.get("/api/users/400").json()["followers"], 0)
        self.assertEqual(self.client.get("/api/users/500").json()["followees"], 0)

    def test_unknown_numeric_user_returns_404(self):
        self.assertEqual(self.client.get("/api/users/999").status_code, 404)

    def test_invalid_user_ids_return_400(self):
        for value in ["abc", "-1", "1.5", "１２３"]:
            with self.subTest(value=value):
                self.assertEqual(self.client.get("/api/users/" + value).status_code, 400)

    def test_pagination_has_stable_boundaries_and_total(self):
        first = self.client.get("/api/users?offset=0&limit=2").json()
        second = self.client.get("/api/users?offset=2&limit=2").json()
        self.assertEqual([row["user_id"] for row in first["items"]], ["100", "200"])
        self.assertEqual([row["user_id"] for row in second["items"]], ["300", "400"])
        self.assertEqual((first["total"], second["total"]), (5, 5))

    def test_out_of_range_page_returns_empty_items(self):
        self.assertEqual(self.client.get("/api/users?offset=100").json()["items"], [])

    def test_invalid_page_parameters_return_422(self):
        for query in ["limit=0", "limit=201", "offset=-1", "offset=abc"]:
            with self.subTest(query=query):
                self.assertEqual(self.client.get("/api/users?" + query).status_code, 422)

    def test_home_serves_built_frontend_and_assets(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            dist = root / "frontend" / "dist"
            (dist / "assets").mkdir(parents=True)
            (dist / "index.html").write_text("<!doctype html><title>Test UI</title>")
            (dist / "assets" / "test.js").write_text("console.log('ok')")
            with patch("backend.app.BASE_DIR", root), TestClient(create_app([], {})) as client:
                self.assertEqual(client.get("/").status_code, 200)
                self.assertIn("Test UI", client.get("/").text)
                self.assertEqual(client.get("/assets/test.js").status_code, 200)

    def test_missing_frontend_build_returns_actionable_503(self):
        with tempfile.TemporaryDirectory() as folder, patch("backend.app.BASE_DIR", Path(folder)):
            with TestClient(create_app([], {})) as client:
                response = client.get("/")
                self.assertEqual(response.status_code, 503)
                self.assertIn("Build the frontend", response.json()["detail"])
