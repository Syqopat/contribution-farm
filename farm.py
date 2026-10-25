#!/usr/bin/env python3
import argparse
import datetime
import json
import os
import random
import subprocess
import sys
import uuid

if sys.platform == "win32":
    if sys.stdout is None:
        sys.stdout = open(os.devnull, "w", encoding="utf-8")
    if sys.stderr is None:
        sys.stderr = open(os.devnull, "w", encoding="utf-8")

NO_WINDOW_FLAG = 0x08000000 if sys.platform == "win32" else 0
CRON_TAG = "# ContributionFarmDaily"

def _get_subprocess_kwargs():
    if sys.platform == "win32":
        return {"creationflags": NO_WINDOW_FLAG}
    return {}

REALISTIC_COMMIT_TEMPLATES = [
    "feat(engine): refine background telemetry dispatcher",
    "fix(ledger): correct sequential activity indexing",
    "perf(core): optimize memory usage in payload serialization",
    "refactor(pipeline): simplify state persistence handler",
    "test(suite): add validation cases for date offset generator",
    "docs(readme): expand documentation on telemetry integration",
    "chore(deps): update routine ledger verification checksum",
    "style(format): standardize event logging payload structure",
    "feat(worker): enhance jitter distribution algorithm",
    "fix(sync): prevent race condition during ledger rotation",
    "perf(io): streamline json serialization write buffer",
    "refactor(utils): decompose date computation helpers",
    "test(farm): expand coverage for weekend scheduler modes",
    "chore(build): refresh workflow execution prerequisites",
    "feat(logger): improve Windows event log formatting"
]

DEFAULT_CONFIG = {
    "schedule": {
        "mode": "random",
        "fixed_count": 5,
        "min_count": 3,
        "max_count": 7,
        "weekend_mode": "reduce",
        "weekend_min": 1,
        "weekend_max": 2,
        "skip_weekends": False,
        "message_mode": "realistic",
        "jitter_enabled": True,
        "jitter_spread_minutes": 180
    },
    "git": {
        "author_name": "Syqopat",
        "author_email": "203693835+Syqopat@users.noreply.github.com",
        "branch": "main",
        "auto_push": True,
        "data_file": "data/activity.json"
    },
    "telemetry": {
        "enabled": True,
        "system_log": True,
        "file_log": True,
        "log_file": "farm.log",
        "syslog_ident": "ContributionFarm"
    },
    "windows_event_log": {
        "enabled": True,
        "log_name": "Application",
        "source_name": "Application",
        "event_id": 100
    }
}

def get_silent_python_executable():
    current_exe = sys.executable
    if sys.platform == "win32":
        dir_name = os.path.dirname(current_exe)
        candidate = os.path.join(dir_name, "pythonw.exe")
        if os.path.exists(candidate):
            return candidate
    return current_exe

def load_configuration(config_file_path):
    if not os.path.exists(config_file_path):
        return DEFAULT_CONFIG
    try:
        with open(config_file_path, "r", encoding="utf-8") as file_handle:
            loaded_data = json.load(file_handle)
            merged = DEFAULT_CONFIG.copy()
            for section_key, section_val in loaded_data.items():
                if isinstance(section_val, dict) and section_key in merged:
                    merged[section_key] = {**merged[section_key], **section_val}
                else:
                    merged[section_key] = section_val
            return merged
    except Exception:
        return DEFAULT_CONFIG

def generate_commit_message(index, total, mode="realistic"):
    if mode == "realistic":
        template = random.choice(REALISTIC_COMMIT_TEMPLATES)
        return f"{template} [{index}/{total}]"
    return f"chore(farm): update daily activity record [{index}/{total}]"

def calculate_commit_timestamp(index, total, base_datetime=None, jitter_enabled=True, spread_minutes=180):
    if base_datetime is None:
        base_datetime = datetime.datetime.now(datetime.timezone.utc)
    if not jitter_enabled or total <= 1:
        return base_datetime
    step = spread_minutes / total
    minutes_before = spread_minutes - ((index - 1) * step) + random.randint(-4, 4)
    minutes_before = max(0, minutes_before)
    return base_datetime - datetime.timedelta(minutes=minutes_before)

def determine_contribution_count(schedule_config, args, target_date=None):
    if args.count is not None:
        return max(1, args.count)
    if target_date is None:
        target_date = datetime.datetime.now(datetime.timezone.utc)
    is_weekend = target_date.weekday() in (5, 6)
    if is_weekend:
        if args.skip_weekends or schedule_config.get("skip_weekends", False):
            print("Weekend detected and skip_weekends is enabled. Skipping contributions.")
            return 0
        weekend_mode = schedule_config.get("weekend_mode", "reduce")
        if weekend_mode == "reduce":
            w_min = schedule_config.get("weekend_min", 1)
            w_max = schedule_config.get("weekend_max", 2)
            if w_min > w_max:
                w_min, w_max = w_max, w_min
            chosen = random.randint(w_min, w_max)
            print(f"Weekend mode active: selected {chosen} contributions from range [{w_min}, {w_max}].")
            return chosen
    mode = "random" if args.randomize else (args.mode or schedule_config.get("mode", "random"))
    min_val = args.min if args.min is not None else schedule_config.get("min_count", 3)
    max_val = args.max if args.max is not None else schedule_config.get("max_count", 7)
    if min_val > max_val:
        min_val, max_val = max_val, min_val
    if mode == "random":
        chosen = random.randint(min_val, max_val)
        print(f"Randomizer selected {chosen} contributions from range [{min_val}, {max_val}].")
        return chosen
    fixed = schedule_config.get("fixed_count", 5)
    return max(1, fixed)

def write_windows_event_log(message, event_type="Information", event_id=100, log_name="Application"):
    if sys.platform != "win32":
        return False
    try:
        import win32evtlog
        type_mapping = {
            "Information": win32evtlog.EVENTLOG_INFORMATION_TYPE,
            "Warning": win32evtlog.EVENTLOG_WARNING_TYPE,
            "Error": win32evtlog.EVENTLOG_ERROR_TYPE,
        }
        log_type = type_mapping.get(event_type, win32evtlog.EVENTLOG_INFORMATION_TYPE)
        handle = win32evtlog.OpenEventLog(None, log_name)
        win32evtlog.ReportEvent(handle, log_type, 0, event_id, None, [message], None)
        win32evtlog.CloseEventLog(handle)
        return True
    except Exception:
        try:
            sanitized_message = message.replace("'", "''").replace('"', '`"')
            powershell_command = (
                f"$log = New-Object System.Diagnostics.EventLog('{log_name}'); "
                f"$log.Source = '{log_name}'; "
                f"$log.WriteEntry('{sanitized_message}', "
                f"[System.Diagnostics.EventLogEntryType]::{event_type}, {event_id})"
            )
            subprocess.run(
                ["powershell", "-NoProfile", "-Command", powershell_command],
                capture_output=True,
                text=True,
                check=False,
                **_get_subprocess_kwargs()
            )
            return True
        except Exception:
            return False

def write_linux_syslog(message, event_type="Information", ident="ContributionFarm"):
    if not (sys.platform.startswith("linux") or sys.platform == "darwin"):
        return False
    try:
        import syslog
        priority_map = {
            "Information": syslog.LOG_INFO,
            "Warning": syslog.LOG_WARNING,
            "Error": syslog.LOG_ERR,
        }
        level = priority_map.get(event_type, syslog.LOG_INFO)
        syslog.openlog(ident=ident, facility=syslog.LOG_USER)
        syslog.syslog(level, message)
        syslog.closelog()
        return True
    except Exception:
        try:
            priority_flag = "user.info" if event_type == "Information" else ("user.warning" if event_type == "Warning" else "user.err")
            subprocess.run(["logger", "-t", ident, "-p", priority_flag, message], check=False, **_get_subprocess_kwargs())
            return True
        except Exception:
            return False

def append_file_log(message, event_type="Information", log_file="farm.log"):
    try:
        now_str = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"[{now_str}] [{event_type.upper()}] {message}\n")
        return True
    except Exception:
        return False

def write_telemetry_event(message, event_type="Information", config=None):
    cfg = config or {}
    telemetry_cfg = cfg.get("telemetry", {})
    win_cfg = cfg.get("windows_event_log", {})
    enabled = telemetry_cfg.get("enabled", win_cfg.get("enabled", True))
    if not enabled:
        return False

    success = False
    if sys.platform == "win32":
        success = write_windows_event_log(
            message=message,
            event_type=event_type,
            event_id=win_cfg.get("event_id", 100),
            log_name=win_cfg.get("log_name", "Application")
        )
    else:
        ident = telemetry_cfg.get("syslog_ident", "ContributionFarm")
        success = write_linux_syslog(message=message, event_type=event_type, ident=ident)

    if telemetry_cfg.get("file_log", True):
        log_file = telemetry_cfg.get("log_file", "farm.log")
        if log_file:
            append_file_log(message=message, event_type=event_type, log_file=log_file)

    return success

def parse_task_time(task_time_str):
    """
    Parses time formats: '12:00PM', '02:30PM', '9:15AM', '14:30', or '12:00'
    into (hour_24, minute). Defaults to (12, 0) upon malformed inputs.
    """
    time_str = str(task_time_str).strip().upper()
    is_pm = "PM" in time_str
    is_am = "AM" in time_str
    cleaned = time_str.replace("PM", "").replace("AM", "").strip()
    parts = cleaned.split(":")
    if len(parts) != 2:
        return 12, 0
    try:
        hour = int(parts[0])
        minute = int(parts[1])
    except ValueError:
        return 12, 0

    if is_pm and hour < 12:
        hour += 12
    elif is_am and hour == 12:
        hour = 0
    return max(0, min(23, hour)), max(0, min(59, minute))

def get_cron_command(script_path, working_dir, python_exe=None):
    py_bin = python_exe or sys.executable
    log_path = os.path.join(working_dir, "farm.log")
    return f"cd '{working_dir}' && '{py_bin}' '{script_path}' --push >> '{log_path}' 2>&1 {CRON_TAG}"

def install_cron_task(task_time="12:00PM", script_path=None, working_dir=None):
    script_path = os.path.abspath(script_path or __file__)
    working_dir = working_dir or os.path.dirname(script_path)
    hour, minute = parse_task_time(task_time)
    cron_cmd = get_cron_command(script_path, working_dir)
    cron_line = f"{minute} {hour} * * * {cron_cmd}"

    try:
        proc = subprocess.run(["crontab", "-l"], capture_output=True, text=True, check=False)
        current_crontab = proc.stdout if proc.returncode == 0 else ""
        lines = [line for line in current_crontab.splitlines() if CRON_TAG not in line and line.strip()]
        lines.append(cron_line)
        new_crontab = "\n".join(lines) + "\n"
        sub = subprocess.run(["crontab", "-"], input=new_crontab, text=True, capture_output=True)
        if sub.returncode == 0:
            print(f"Crontab: Daily contribution task registered successfully for {hour:02d}:{minute:02d}.")
            write_telemetry_event(
                f"ContributionFarm: Crontab daily task registered for {hour:02d}:{minute:02d}.",
                event_type="Information"
            )
            return True
        else:
            print(f"Failed to register cron task: {sub.stderr.strip()}", file=sys.stderr)
            return False
    except Exception as exc:
        print(f"Error registering crontab: {exc}", file=sys.stderr)
        return False

def uninstall_cron_task():
    try:
        proc = subprocess.run(["crontab", "-l"], capture_output=True, text=True, check=False)
        if proc.returncode != 0:
            print("No crontab found to uninstall.")
            return True
        lines = [line for line in proc.stdout.splitlines() if CRON_TAG not in line and line.strip()]
        if not lines:
            subprocess.run(["crontab", "-r"], capture_output=True, check=False)
        else:
            new_crontab = "\n".join(lines) + "\n"
            subprocess.run(["crontab", "-"], input=new_crontab, text=True, capture_output=True, check=True)
        print("Crontab: Contribution Farm scheduled job removed successfully.")
        write_telemetry_event(
            "ContributionFarm: Crontab daily task unregistered.",
            event_type="Information"
        )
        return True
    except Exception as exc:
        print(f"Error removing crontab entry: {exc}", file=sys.stderr)
        return False

def install_systemd_task(task_time="12:00PM", script_path=None, working_dir=None):
    script_path = os.path.abspath(script_path or __file__)
    working_dir = working_dir or os.path.dirname(script_path)
    hour, minute = parse_task_time(task_time)
    time_formatted = f"{hour:02d}:{minute:02d}:00"

    systemd_user_dir = os.path.expanduser("~/.config/systemd/user")
    os.makedirs(systemd_user_dir, exist_ok=True)

    service_file = os.path.join(systemd_user_dir, "contribution-farm.service")
    timer_file = os.path.join(systemd_user_dir, "contribution-farm.timer")

    service_content = f"""[Unit]
Description=Daily Contribution Farm Runner
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
WorkingDirectory={working_dir}
ExecStart={sys.executable} "{script_path}" --push
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=default.target
"""

    timer_content = f"""[Unit]
Description=Daily Timer for Contribution Farm
Requires=contribution-farm.service

[Timer]
OnCalendar=*-*-* {time_formatted}
Persistent=true

[Install]
WantedBy=timers.target
"""

    try:
        with open(service_file, "w", encoding="utf-8") as f:
            f.write(service_content)
        with open(timer_file, "w", encoding="utf-8") as f:
            f.write(timer_content)

        subprocess.run(["systemctl", "--user", "daemon-reload"], check=True, capture_output=True)
        subprocess.run(["systemctl", "--user", "enable", "--now", "contribution-farm.timer"], check=True, capture_output=True)
        print(f"Systemd: Timer 'contribution-farm.timer' registered and activated for daily execution at {time_formatted}.")
        write_telemetry_event(
            f"ContributionFarm: Systemd user timer registered for daily run at {time_formatted}.",
            event_type="Information"
        )
        return True
    except Exception as exc:
        print(f"Failed to register systemd timer: {exc}", file=sys.stderr)
        return False

def uninstall_systemd_task():
    systemd_user_dir = os.path.expanduser("~/.config/systemd/user")
    service_file = os.path.join(systemd_user_dir, "contribution-farm.service")
    timer_file = os.path.join(systemd_user_dir, "contribution-farm.timer")

    try:
        subprocess.run(["systemctl", "--user", "disable", "--now", "contribution-farm.timer"], capture_output=True, check=False)
        for p in (timer_file, service_file):
            if os.path.exists(p):
                try:
                    os.remove(p)
                except OSError:
                    pass
        subprocess.run(["systemctl", "--user", "daemon-reload"], capture_output=True, check=False)
        print("Systemd: 'contribution-farm.timer' and service unregistered successfully.")
        write_telemetry_event(
            "ContributionFarm: Systemd user timer unregistered.",
            event_type="Information"
        )
        return True
    except Exception as exc:
        print(f"Failed to unregister systemd task: {exc}", file=sys.stderr)
        return False

def install_task(task_time="12:00PM", scheduler="auto"):
    if sys.platform == "win32":
        install_windows_task(task_time=task_time)
    else:
        if scheduler == "systemd":
            install_systemd_task(task_time=task_time)
        else:
            install_cron_task(task_time=task_time)

def uninstall_task(scheduler="auto"):
    if sys.platform == "win32":
        uninstall_windows_task()
    else:
        if scheduler == "systemd":
            uninstall_systemd_task()
        elif scheduler == "cron":
            uninstall_cron_task()
        else:
            uninstall_cron_task()
            uninstall_systemd_task()

def install_windows_task(task_name="ContributionFarmDaily", task_time="12:00PM"):
    python_exe = get_silent_python_executable()
    script_path = os.path.abspath(__file__)
    working_dir = os.path.dirname(script_path)
    cmd = (
        f"$action = New-ScheduledTaskAction -Execute '{python_exe}' "
        f"-Argument '\"{script_path}\" --push' -WorkingDirectory '{working_dir}'; "
        f"$trigger = New-ScheduledTaskTrigger -Daily -At '{task_time}'; "
        f"$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries "
        f"-DontStopIfGoingOnBatteries -StartWhenAvailable -Hidden; "
        f"Register-ScheduledTask -TaskName '{task_name}' -Action $action -Trigger $trigger -Settings $settings -Force -Description 'Daily Silent Contribution Farm Runner'"
    )
    result = subprocess.run(
        ["powershell", "-NoProfile", "-Command", cmd],
        capture_output=True,
        text=True,
        **_get_subprocess_kwargs()
    )
    if result.returncode == 0:
        print(f"Windows Task Scheduler: '{task_name}' registered successfully as silent background task at {task_time} (using {os.path.basename(python_exe)}).")
        write_telemetry_event(
            f"ContributionFarm: Silent daily task '{task_name}' registered for {task_time} with {os.path.basename(python_exe)}.",
            event_type="Information"
        )
    else:
        print(f"Failed to register Windows task: {result.stderr.strip()}", file=sys.stderr)

def uninstall_windows_task(task_name="ContributionFarmDaily"):
    cmd = f"Unregister-ScheduledTask -TaskName '{task_name}' -Confirm:$false"
    result = subprocess.run(
        ["powershell", "-NoProfile", "-Command", cmd],
        capture_output=True,
        text=True,
        **_get_subprocess_kwargs()
    )
    if result.returncode == 0:
        print(f"Windows Task Scheduler: '{task_name}' unregistered successfully.")
        write_telemetry_event(
            f"ContributionFarm: Scheduled daily task '{task_name}' unregistered.",
            event_type="Information"
        )
    else:
        print(f"Failed to unregister Windows task: {result.stderr.strip()}", file=sys.stderr)

def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Automated GitHub contribution generator and activity manager for Linux & Windows."
    )
    parser.add_argument("--config", type=str, default="config.json", help="Path to config.json file.")
    parser.add_argument("--mode", type=str, choices=["fixed", "random"], help="Execution mode: fixed or random.")
    parser.add_argument("--randomize", action="store_true", help="Force random contribution generation.")
    parser.add_argument("--min", type=int, help="Minimum contributions for random mode.")
    parser.add_argument("--max", type=int, help="Maximum contributions for random mode.")
    parser.add_argument("--count", type=int, help="Fixed contribution count override.")
    parser.add_argument("--author-name", type=str, help="Author name for git commits.")
    parser.add_argument("--author-email", type=str, help="Author email for git commits.")
    parser.add_argument("--branch", type=str, help="Target git branch.")
    parser.add_argument("--data-file", type=str, help="Path to activity tracking JSON file.")
    parser.add_argument("--dry-run", action="store_true", help="Simulate run without making commits.")
    parser.add_argument("--push", action="store_true", help="Push commits to remote repository.")
    parser.add_argument("--skip-weekends", action="store_true", help="Skip generating contributions on weekends.")
    parser.add_argument("--message-mode", type=str, choices=["realistic", "standard"], help="Commit message template style.")
    parser.add_argument("--backfill-days", type=int, help="Backfill realistic contributions for the last N days.")
    parser.add_argument("--backfill-start", type=str, help="Historical backfill start date (YYYY-MM-DD).")
    parser.add_argument("--backfill-end", type=str, help="Historical backfill end date (YYYY-MM-DD).")
    parser.add_argument("--install-task", action="store_true", help="Register scheduled daily background task (OS native).")
    parser.add_argument("--uninstall-task", action="store_true", help="Unregister scheduled daily task.")
    parser.add_argument("--install-cron", action="store_true", help="Register daily task in Linux Crontab.")
    parser.add_argument("--uninstall-cron", action="store_true", help="Unregister daily task from Linux Crontab.")
    parser.add_argument("--install-systemd", action="store_true", help="Register daily task as Linux Systemd user timer.")
    parser.add_argument("--uninstall-systemd", action="store_true", help="Unregister daily task from Linux Systemd.")
    parser.add_argument("--scheduler", type=str, choices=["auto", "cron", "systemd"], default="auto", help="Scheduler backend for Linux (auto, cron, systemd).")
    parser.add_argument("--task-time", type=str, default="12:00PM", help="Daily execution time (e.g. '12:00PM', '14:30').")
    return parser.parse_args()

def load_activity_data(file_path):
    if not os.path.exists(file_path):
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        return {"total_contributions": 0, "last_run": None, "history": []}
    with open(file_path, "r", encoding="utf-8") as file_handle:
        try:
            return json.load(file_handle)
        except json.JSONDecodeError:
            return {"total_contributions": 0, "last_run": None, "history": []}

def save_activity_data(file_path, data):
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as file_handle:
        json.dump(data, file_handle, indent=2, ensure_ascii=False)
        file_handle.write("\n")

def record_activity_entry(file_path, run_id, index, total, timestamp=None):
    data = load_activity_data(file_path)
    now_iso = timestamp or datetime.datetime.now(datetime.timezone.utc).isoformat()
    data["total_contributions"] = data.get("total_contributions", 0) + 1
    data["last_run"] = now_iso
    data.setdefault("history", []).append({
        "run_id": run_id,
        "entry_index": index,
        "total_in_run": total,
        "timestamp": now_iso
    })
    save_activity_data(file_path, data)
    return data["total_contributions"]

def execute_git(args, env=None):
    process_env = os.environ.copy()
    if env:
        process_env.update(env)
    result = subprocess.run(
        ["git"] + args,
        capture_output=True,
        text=True,
        env=process_env,
        **_get_subprocess_kwargs()
    )
    if result.returncode != 0:
        raise RuntimeError(f"Git command failed: git {' '.join(args)}\n{result.stderr.strip()}")
    return result.stdout.strip()

def configure_git_identity(author_name, author_email):
    execute_git(["config", "user.name", author_name])
    execute_git(["config", "user.email", author_email])

def create_contributions(
    count,
    author_name,
    author_email,
    data_file,
    dry_run=False,
    base_time=None,
    message_mode="realistic",
    jitter_enabled=True,
    spread_minutes=180
):
    if count <= 0:
        return None, 0
    run_id = str(uuid.uuid4())
    print(f"Starting contribution run {run_id} with count: {count}")
    if not dry_run:
        configure_git_identity(author_name, author_email)
    total_cumulative = 0
    for index in range(1, count + 1):
        commit_time = calculate_commit_timestamp(
            index=index,
            total=count,
            base_datetime=base_time,
            jitter_enabled=jitter_enabled,
            spread_minutes=spread_minutes
        )
        timestamp_iso = commit_time.isoformat()
        if dry_run:
            total_cumulative = load_activity_data(data_file).get("total_contributions", 0) + index
        else:
            total_cumulative = record_activity_entry(data_file, run_id, index, count, timestamp=timestamp_iso)
        message = generate_commit_message(index, count, mode=message_mode)
        formatted_date = commit_time.strftime("%Y-%m-%d %H:%M:%S +0000")
        git_env = {
            "GIT_AUTHOR_NAME": author_name,
            "GIT_AUTHOR_EMAIL": author_email,
            "GIT_COMMITTER_NAME": author_name,
            "GIT_COMMITTER_EMAIL": author_email,
            "GIT_AUTHOR_DATE": formatted_date,
            "GIT_COMMITTER_DATE": formatted_date
        }
        if dry_run:
            print(f"[DRY-RUN] Step {index}/{count} | Date: {formatted_date} | {message}")
        else:
            execute_git(["add", data_file])
            execute_git(["commit", "-m", message], env=git_env)
            print(f"Committed {index}/{count} ({formatted_date}): {message}")
    print(f"Successfully processed {count} contribution entries.")
    return run_id, total_cumulative

def backfill_history(
    start_date_str,
    end_date_str,
    author_name,
    author_email,
    data_file,
    schedule_cfg,
    args
):
    start_date = datetime.date.fromisoformat(start_date_str)
    end_date = datetime.date.fromisoformat(end_date_str)
    if start_date > end_date:
        start_date, end_date = end_date, start_date
    current = start_date
    total_days = (end_date - start_date).days + 1
    print(f"Starting historical backfill from {start_date} to {end_date} ({total_days} days)...")
    total_backfilled = 0
    message_mode = args.message_mode or schedule_cfg.get("message_mode", "realistic")
    jitter_enabled = schedule_cfg.get("jitter_enabled", True)
    spread_minutes = schedule_cfg.get("jitter_spread_minutes", 180)
    while current <= end_date:
        target_dt = datetime.datetime.combine(current, datetime.time(14, 30), tzinfo=datetime.timezone.utc)
        count = determine_contribution_count(schedule_cfg, args, target_date=target_dt)
        if count > 0:
            run_id, cum = create_contributions(
                count=count,
                author_name=author_name,
                author_email=author_email,
                data_file=data_file,
                dry_run=args.dry_run,
                base_time=target_dt,
                message_mode=message_mode,
                jitter_enabled=jitter_enabled,
                spread_minutes=spread_minutes
            )
            total_backfilled += count
        current += datetime.timedelta(days=1)
    print(f"Backfill finished. Generated {total_backfilled} historical contributions.")
    return total_backfilled

def push_changes(branch):
    print(f"Pushing commits to branch '{branch}'...")
    output = execute_git(["push", "origin", branch])
    print("Push completed successfully.")
    return output

def main():
    args = parse_arguments()
    if args.install_cron:
        install_cron_task(task_time=args.task_time)
        return
    if args.uninstall_cron:
        uninstall_cron_task()
        return
    if args.install_systemd:
        install_systemd_task(task_time=args.task_time)
        return
    if args.uninstall_systemd:
        uninstall_systemd_task()
        return
    if args.install_task:
        install_task(task_time=args.task_time, scheduler=args.scheduler)
        return
    if args.uninstall_task:
        uninstall_task(scheduler=args.scheduler)
        return

    config = load_configuration(args.config)
    schedule_cfg = config.get("schedule", {})
    git_cfg = config.get("git", {})

    author_name = args.author_name or os.environ.get("FARM_AUTHOR_NAME") or git_cfg.get("author_name", "Syqopat")
    author_email = args.author_email or os.environ.get("FARM_AUTHOR_EMAIL") or git_cfg.get("author_email", "203693835+Syqopat@users.noreply.github.com")
    branch = args.branch or os.environ.get("FARM_BRANCH") or git_cfg.get("branch", "main")
    data_file = args.data_file or git_cfg.get("data_file", "data/activity.json")
    auto_push = args.push or git_cfg.get("auto_push", False)
    message_mode = args.message_mode or schedule_cfg.get("message_mode", "realistic")
    jitter_enabled = schedule_cfg.get("jitter_enabled", True)
    spread_minutes = schedule_cfg.get("jitter_spread_minutes", 180)

    if args.backfill_days:
        end_d = datetime.date.today() - datetime.timedelta(days=1)
        start_d = end_d - datetime.timedelta(days=args.backfill_days - 1)
        backfill_history(
            start_d.isoformat(),
            end_d.isoformat(),
            author_name,
            author_email,
            data_file,
            schedule_cfg,
            args
        )
        if auto_push and not args.dry_run:
            push_changes(branch)
        return

    if args.backfill_start and args.backfill_end:
        backfill_history(
            args.backfill_start,
            args.backfill_end,
            author_name,
            author_email,
            data_file,
            schedule_cfg,
            args
        )
        if auto_push and not args.dry_run:
            push_changes(branch)
        return

    count = determine_contribution_count(schedule_cfg, args)
    if count == 0:
        print("Scheduled count is 0 for today. No commits to create.")
        return

    start_log_message = (
        f"ContributionFarm started: Target count={count}, Author={author_name}, "
        f"Branch={branch}, DryRun={args.dry_run}"
    )
    write_telemetry_event(start_log_message, event_type="Information", config=config)

    try:
        run_id, total_cumulative = create_contributions(
            count=count,
            author_name=author_name,
            author_email=author_email,
            data_file=data_file,
            dry_run=args.dry_run,
            message_mode=message_mode,
            jitter_enabled=jitter_enabled,
            spread_minutes=spread_minutes
        )
        if auto_push and not args.dry_run:
            push_changes(branch)

        finish_log_message = (
            f"ContributionFarm completed successfully: {count} contributions generated. "
            f"Run ID={run_id}, Cumulative total={total_cumulative}."
        )
        write_telemetry_event(finish_log_message, event_type="Information", config=config)
    except Exception as exc:
        error_message = f"ContributionFarm failed: {exc}"
        print(error_message, file=sys.stderr)
        write_telemetry_event(error_message, event_type="Error", config=config)
        sys.exit(1)

if __name__ == "__main__":
    main()
