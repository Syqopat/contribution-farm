import argparse
import json
import os
import shutil
import tempfile
import unittest

from farm import (
    create_contributions,
    determine_contribution_count,
    load_activity_data,
    load_configuration,
    record_activity_entry,
    save_activity_data,
    write_windows_event_log,
)

class TestContributionFarm(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.data_file = os.path.join(self.test_dir, "test_activity.json")
        self.config_file = os.path.join(self.test_dir, "test_config.json")

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_load_nonexistent_activity_file(self):
        data = load_activity_data(self.data_file)
        self.assertEqual(data["total_contributions"], 0)
        self.assertIsNone(data["last_run"])
        self.assertEqual(data["history"], [])

    def test_save_and_load_activity_file(self):
        initial = {
            "total_contributions": 10,
            "last_run": "2026-10-10T12:00:00Z",
            "history": []
        }
        save_activity_data(self.data_file, initial)
        loaded = load_activity_data(self.data_file)
        self.assertEqual(loaded["total_contributions"], 10)
        self.assertEqual(loaded["last_run"], "2026-10-10T12:00:00Z")

    def test_record_activity_entry(self):
        total1 = record_activity_entry(self.data_file, "run-1", 1, 5)
        self.assertEqual(total1, 1)
        total2 = record_activity_entry(self.data_file, "run-1", 2, 5)
        self.assertEqual(total2, 2)
        with open(self.data_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.assertEqual(data["total_contributions"], 2)
        self.assertEqual(len(data["history"]), 2)
        self.assertEqual(data["history"][0]["entry_index"], 1)
        self.assertEqual(data["history"][1]["entry_index"], 2)

    def test_load_configuration(self):
        custom_config = {
            "schedule": {
                "mode": "random",
                "min_count": 2,
                "max_count": 6
            }
        }
        with open(self.config_file, "w", encoding="utf-8") as f:
            json.dump(custom_config, f)
        loaded = load_configuration(self.config_file)
        self.assertEqual(loaded["schedule"]["mode"], "random")
        self.assertEqual(loaded["schedule"]["min_count"], 2)
        self.assertEqual(loaded["schedule"]["max_count"], 6)
        self.assertEqual(loaded["schedule"]["fixed_count"], 5)

    def test_determine_contribution_count_fixed(self):
        schedule_config = {"mode": "fixed", "fixed_count": 5}
        args = argparse.Namespace(count=None, randomize=False, mode=None, min=None, max=None)
        count = determine_contribution_count(schedule_config, args)
        self.assertEqual(count, 5)

    def test_determine_contribution_count_override(self):
        schedule_config = {"mode": "fixed", "fixed_count": 5}
        args = argparse.Namespace(count=8, randomize=False, mode=None, min=None, max=None)
        count = determine_contribution_count(schedule_config, args)
        self.assertEqual(count, 8)

    def test_determine_contribution_count_random(self):
        schedule_config = {"mode": "random", "min_count": 4, "max_count": 6}
        args = argparse.Namespace(count=None, randomize=False, mode=None, min=None, max=None)
        counts = {determine_contribution_count(schedule_config, args) for _ in range(50)}
        for val in counts:
            self.assertTrue(4 <= val <= 6)

    def test_dry_run_contributions(self):
        run_id, total = create_contributions(
            count=3,
            author_name="Syqopat",
            author_email="203693835+Syqopat@users.noreply.github.com",
            data_file=self.data_file,
            dry_run=True
        )
        self.assertIsNotNone(run_id)
        self.assertEqual(total, 3)
        loaded = load_activity_data(self.data_file)
        self.assertEqual(loaded["total_contributions"], 3)
        self.assertEqual(len(loaded["history"]), 3)

    def test_invalid_count(self):
        with self.assertRaises(ValueError):
            create_contributions(
                count=0,
                author_name="Syqopat",
                author_email="203693835+Syqopat@users.noreply.github.com",
                data_file=self.data_file,
                dry_run=True
            )

    def test_windows_event_log_execution(self):
        result = write_windows_event_log("Test event message from test suite")
        self.assertIsInstance(result, bool)

if __name__ == "__main__":
    unittest.main()
