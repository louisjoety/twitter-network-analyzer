"""Small deterministic tests of the production Spark algorithm, not a dataset auditor."""

import os
import sys
import tempfile
import unittest
from pathlib import Path

try:
    from pyspark.sql import SparkSession
except ImportError:
    SparkSession = None

if SparkSession is not None:
    from analysis.job import compute_stats


@unittest.skipIf(SparkSession is None, "PySpark is installed separately in the CI analysis job")
class AnalysisTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.environ.setdefault("SPARK_LOCAL_IP", "127.0.0.1")
        os.environ.setdefault("PYSPARK_PYTHON", sys.executable)
        cls.spark = (SparkSession.builder.master("local[2]").appName("AnalysisTests")
                     .config("spark.ui.enabled", "false")
                     .config("spark.sql.shuffle.partitions", "2").getOrCreate())
        cls.spark.sparkContext.setLogLevel("ERROR")
        cls.folder = tempfile.TemporaryDirectory()

    @classmethod
    def tearDownClass(cls):
        cls.spark.stop()
        cls.folder.cleanup()

    def tearDown(self):
        self.spark.catalog.clearCache()

    def evaluate(self, text):
        path = Path(self.folder.name) / (self._testMethodName + ".txt")
        path.write_text(text, encoding="utf-8")
        stats, metrics = compute_stats(self.spark, str(path.resolve()))
        return {row.user_id: (row.followers, row.followees) for row in stats.collect()}, metrics

    def test_direction_assigns_followee_to_source_and_follower_to_destination(self):
        rows, _ = self.evaluate("100 200\n")
        self.assertEqual(rows, {"100": (0, 1), "200": (1, 0)})

    def test_duplicate_pairs_keep_one_relationship(self):
        rows, metrics = self.evaluate("100 200\n100 200\n100 200\n")
        self.assertEqual(rows, {"100": (0, 1), "200": (1, 0)})
        self.assertEqual((metrics["unique_edges"], metrics["duplicate_edges_removed"]), (1, 2))

    def test_reciprocal_and_different_neighbor_edges_survive(self):
        rows, _ = self.evaluate("100 200\n200 100\n100 300\n")
        self.assertEqual(rows, {"100": (1, 2), "200": (1, 1), "300": (1, 0)})

    def test_one_sided_users_keep_zero_counts(self):
        rows, _ = self.evaluate("100 200\n400 200\n")
        self.assertEqual(rows, {"100": (0, 1), "200": (2, 0), "400": (0, 1)})

    def test_self_loop_counts_once_on_both_sides(self):
        rows, _ = self.evaluate("100 100\n100 100\n")
        self.assertEqual(rows, {"100": (1, 1)})

    def test_whitespace_blank_and_malformed_lines(self):
        rows, metrics = self.evaluate(" 100\t200 \n\nbad\n1 2 3\n")
        self.assertEqual(rows, {"100": (0, 1), "200": (1, 0)})
        self.assertEqual((metrics["blank_lines"], metrics["invalid_lines"], metrics["valid_edges"]), (1, 2, 1))

    def test_no_valid_relationships_fail_instead_of_producing_empty_results(self):
        with self.assertRaisesRegex(ValueError, "no valid relationships"):
            self.evaluate("bad\n\n")

    def test_large_numeric_ids_remain_exact_strings(self):
        uid = "99999999999999999999"
        rows, metrics = self.evaluate(uid + " 100\n")
        self.assertEqual(rows[uid], (0, 1))
        self.assertEqual((metrics["total_followers"], metrics["total_followees"]), (1, 1))
