import argparse
import datetime
import json
import os
import shutil
import tempfile
import unittest

from farm import (
    append_file_log,
    backfill_history,
    calculate_commit_timestamp,
    create_contributions,
    determine_contribution_count,
    generate_commit_message,
    get_cron_command,
    load_activity_data,
    load_configuration,
    parse_task_time,
    record_activity_entry,
    save_activity_data,
    write_linux_syslog,
    write_telemetry_event,
    write_windows_event_log,
)

class TestContributionFarm(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.data_file = os.path.join(self.test_dir, "test_activity.json")
        self.config_file = os.path.join(self.test_dir, "test_config.json")
        self.log_file = os.path.join(self.test_dir, "test_farm.log")

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

    def test_generate_commit_message(self):
        msg_std = generate_commit_message(1, 5, mode="standard")
        self.assertEqual(msg_std, "chore(farm): update daily activity record [1/5]")
        msg_real = generate_commit_message(2, 5, mode="realistic")
        self.assertTrue("[2/5]" in msg_real)
        self.assertTrue("(" in msg_real and "):" in msg_real)

    def test_calculate_commit_timestamp(self):
        base = datetime.datetime(2026, 10, 10, 15, 0, 0, tzinfo=datetime.timezone.utc)
        t1 = calculate_commit_timestamp(1, 4, base_datetime=base, jitter_enabled=True, spread_minutes=180)
        t4 = calculate_commit_timestamp(4, 4, base_datetime=base, jitter_enabled=True, spread_minutes=180)
        self.assertLessEqual(t1, t4)

    def test_weekend_mode_detection(self):
        saturday = datetime.datetime(2026, 10, 10, 12, 0, tzinfo=datetime.timezone.utc)
        cfg_skip = {"skip_weekends": True, "weekend_mode": "reduce"}
        args = argparse.Namespace(count=None, randomize=False, mode=None, min=None, max=None, skip_weekends=False)
        count = determine_contribution_count(cfg_skip, args, target_date=saturday)
        self.assertEqual(count, 0)

        cfg_reduce = {"skip_weekends": False, "weekend_mode": "reduce", "weekend_min": 1, "weekend_max": 2}
        count_red = determine_contribution_count(cfg_reduce, args, target_date=saturday)
        self.assertTrue(1 <= count_red <= 2)

    def test_backfill_dry_run(self):
        cfg = {"mode": "fixed", "fixed_count": 2, "skip_weekends": False, "weekend_mode": "normal", "message_mode": "realistic"}
        args = argparse.Namespace(count=2, randomize=False, mode=None, min=None, max=None, skip_weekends=False, message_mode="realistic", dry_run=True)
        total = backfill_history("2026-10-01", "2026-10-03", "Syqopat", "test@test.com", self.data_file, cfg, args)
        self.assertEqual(total, 6)

    def test_windows_event_log_execution(self):
        result = write_windows_event_log("Test event message from test suite")
        self.assertIsInstance(result, bool)

    def test_parse_task_time(self):
        self.assertEqual(parse_task_time("12:00PM"), (12, 0))
        self.assertEqual(parse_task_time("12:00AM"), (0, 0))
        self.assertEqual(parse_task_time("02:30PM"), (14, 30))
        self.assertEqual(parse_task_time("9:15AM"), (9, 15))
        self.assertEqual(parse_task_time("14:45"), (14, 45))
        self.assertEqual(parse_task_time("invalid"), (12, 0))

    def test_cron_command_generation(self):
        cmd = get_cron_command("/path/to/farm.py", "/path/to", python_exe="/usr/bin/python3")
        self.assertIn("cd '/path/to'", cmd)
        self.assertIn("'/usr/bin/python3'", cmd)
        self.assertIn("'/path/to/farm.py' --push", cmd)
        self.assertIn("# ContributionFarmDaily", cmd)

    def test_append_file_log(self):
        result = append_file_log("Test unit log message", event_type="Information", log_file=self.log_file)
        self.assertTrue(result)
        self.assertTrue(os.path.exists(self.log_file))
        with open(self.log_file, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("[INFORMATION] Test unit log message", content)

    def test_linux_syslog_execution(self):
        result = write_linux_syslog("Test Linux Syslog from test suite")
        self.assertIsInstance(result, bool)

    def test_write_telemetry_event(self):
        cfg = {
            "telemetry": {
                "enabled": True,
                "file_log": True,
                "log_file": self.log_file,
                "syslog_ident": "ContributionFarmTest"
            }
        }
        success = write_telemetry_event("Test telemetry dispatch", event_type="Information", config=cfg)
        self.assertIsInstance(success, bool)
        self.assertTrue(os.path.exists(self.log_file))
        with open(self.log_file, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("Test telemetry dispatch", content)

if __name__ == "__main__":
    unittest.main()
