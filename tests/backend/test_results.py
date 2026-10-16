"""Reject incomplete or corrupted aggregate data before it reaches the UI."""

import json
import unittest

from backend.app import load_results, saved_results
from tests.support import CONFIG, METRICS, FakeSession, fixture_rows


class ResultTests(unittest.TestCase):
    def setUp(self):
        self.session = FakeSession()
        self.s3 = self.session.s3
        self.s3.add_output("output/test")
        self.manifest = {"run_prefix": "output/test", "job_run_id": "testjob123"}

    def load(self):
        return load_results(self.s3, CONFIG, self.manifest)

    def test_multiple_csv_parts_and_paginated_s3_listing(self):
        data = self.s3.objects.pop("output/test/users/part-000.csv").splitlines(keepends=True)
        self.s3.objects["output/test/users/part-002.csv"] = data[0] + b"".join(data[3:])
        self.s3.objects["output/test/users/part-001.csv"] = b"".join(data[:3])
        self.s3.objects["output/test/users/ignored.csv"] = b"not a Spark result"
        rows, metrics = self.load()
        self.assertEqual(rows, fixture_rows())
        self.assertEqual(metrics["unique_edges"], 6)

    def test_missing_output_parts_are_rejected(self):
        del self.s3.objects["output/test/users/part-000.csv"]
        with self.assertRaisesRegex(ValueError, "Incomplete"):
            self.load()

    def test_multiple_metrics_parts_are_rejected(self):
        self.s3.objects["output/test/metrics/part-001.json"] = json.dumps(METRICS).encode()
        with self.assertRaisesRegex(ValueError, "Incomplete"):
            self.load()

    def test_wrong_csv_schema_is_rejected(self):
        self.s3.objects["output/test/users/part-000.csv"] = b"id,followers,followees\n100,1,2\n"
        with self.assertRaisesRegex(ValueError, "columns"):
            self.load()

    def test_duplicate_user_rows_are_rejected_even_with_matching_row_count(self):
        key = "output/test/users/part-000.csv"
        self.s3.objects[key] = self.s3.objects[key].replace(b"500,1,0", b"100,1,0")
        with self.assertRaisesRegex(ValueError, "row count"):
            self.load()

    def test_corrupt_follower_or_followee_totals_are_rejected(self):
        key = "output/test/users/part-000.csv"
        original = self.s3.objects[key]
        for field, value in [("followers", b"100,9,2"), ("followees", b"100,1,9")]:
            with self.subTest(field=field):
                self.s3.objects[key] = original.replace(b"100,1,2", value)
                with self.assertRaisesRegex(ValueError, field + " total"):
                    self.load()

    def test_negative_counts_are_rejected_even_if_global_sum_balances(self):
        key = "output/test/users/part-000.csv"
        self.s3.objects[key] = (self.s3.objects[key].replace(b"100,1,2", b"100,-1,2")
                               .replace(b"200,2,2", b"200,4,2"))
        with self.assertRaisesRegex(ValueError, "nonnegative"):
            self.load()

    def test_nonnumeric_result_user_id_is_rejected(self):
        key = "output/test/users/part-000.csv"
        self.s3.objects[key] = self.s3.objects[key].replace(b"100,1,2", b"abc,1,2")
        with self.assertRaisesRegex(ValueError, "numeric user ID"):
            self.load()

    def test_missing_saved_pointer_has_clear_first_run_error(self):
        with self.assertRaisesRegex(ValueError, "No saved analysis"):
            saved_results(self.session, CONFIG)
