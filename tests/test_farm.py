import json
import os
import shutil
import tempfile
import unittest

from farm import (
    create_contributions,
    load_activity_data,
    record_activity_entry,
    save_activity_data,
)

class TestContributionFarm(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.data_file = os.path.join(self.test_dir, "test_activity.json")

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_load_nonexistent_file(self):
        data = load_activity_data(self.data_file)
        self.assertEqual(data["total_contributions"], 0)
        self.assertIsNone(data["last_run"])
        self.assertEqual(data["history"], [])

    def test_save_and_load_file(self):
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

    def test_dry_run_contributions(self):
        create_contributions(
            count=5,
            author_name="Syqopat",
            author_email="203693835+Syqopat@users.noreply.github.com",
            data_file=self.data_file,
            dry_run=True
        )
        loaded = load_activity_data(self.data_file)
        self.assertEqual(loaded["total_contributions"], 5)
        self.assertEqual(len(loaded["history"]), 5)

    def test_invalid_count(self):
        with self.assertRaises(ValueError):
            create_contributions(
                count=0,
                author_name="Syqopat",
                author_email="203693835+Syqopat@users.noreply.github.com",
                data_file=self.data_file,
                dry_run=True
            )

if __name__ == "__main__":
    unittest.main()
