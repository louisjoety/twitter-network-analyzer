"""Job lifecycle safety with fake AWS clients and the real request schema."""

import json
import unittest
from unittest.mock import patch

from backend.app import run_job, saved_results
from tests.support import CONFIG, FakeSession


class OrchestrationTests(unittest.TestCase):
    def test_successful_job_uses_s3_and_publishes_validated_output(self):
        session = FakeSession()
        with patch("backend.app.time.sleep"):
            actual = run_job(session, CONFIG)
        self.assertEqual(saved_results(session, CONFIG), actual)
        parameters = session.emr.submissions[0]
        spark = parameters["jobDriver"]["sparkSubmit"]
        self.assertEqual(spark["entryPoint"], "s3://test-bucket/scripts/analysis.py")
        self.assertNotIn("local[", spark["sparkSubmitParameters"])
        self.assertEqual(parameters["executionTimeoutMinutes"], 20)
        self.assertEqual(session.emr.cancelled, [])

    def test_failed_or_cancelled_job_preserves_previous_pointer(self):
        for state in ["FAILED", "CANCELLED"]:
            with self.subTest(state=state):
                session = FakeSession([state])
                session.s3.objects["output/latest.json"] = b"previous run"
                with self.assertRaisesRegex(RuntimeError, state):
                    run_job(session, CONFIG)
                self.assertEqual(session.s3.objects["output/latest.json"], b"previous run")
                self.assertEqual(session.emr.cancelled, [])

    def test_interrupt_cancels_unfinished_job(self):
        session = FakeSession(["INTERRUPT"])
        with self.assertRaises(KeyboardInterrupt):
            run_job(session, CONFIG)
        self.assertEqual(len(session.emr.cancelled), 1)
        self.assertNotIn("output/latest.json", session.s3.objects)

    def test_polling_failure_cancels_unfinished_job(self):
        session = FakeSession()
        with patch.object(session.emr, "get_job_run", side_effect=RuntimeError("Polling failed")):
            with self.assertRaisesRegex(RuntimeError, "Polling failed"):
                run_job(session, CONFIG)
        self.assertEqual(len(session.emr.cancelled), 1)

    def test_wait_timeout_cancels_unfinished_job(self):
        session = FakeSession()
        with patch("backend.app.time.monotonic", side_effect=[0, 1801]):
            with self.assertRaises(TimeoutError):
                run_job(session, CONFIG)
        self.assertEqual(len(session.emr.cancelled), 1)

    def test_bad_output_does_not_publish_a_success_pointer(self):
        session = FakeSession(["SUCCESS"])
        with patch("backend.app.load_results", side_effect=ValueError("Incomplete output")):
            with self.assertRaisesRegex(ValueError, "Incomplete"):
                run_job(session, CONFIG)
        self.assertNotIn("output/latest.json", session.s3.objects)

    def test_loading_saved_results_does_not_create_an_emr_client(self):
        session = FakeSession(["SUCCESS"])
        run_job(session, CONFIG)
        session.client_requests.clear()
        saved_results(session, CONFIG)
        self.assertEqual(session.client_requests, ["s3"])

    def test_separate_jobs_use_separate_run_prefixes(self):
        session = FakeSession(["SUCCESS"])
        run_job(session, CONFIG)
        first = json.loads(session.s3.objects["output/latest.json"])["run_prefix"]
        run_job(session, CONFIG)
        second = json.loads(session.s3.objects["output/latest.json"])["run_prefix"]
        self.assertNotEqual(first, second)
        self.assertIn(first + "/users/part-000.csv", session.s3.objects)
