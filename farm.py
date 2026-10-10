import argparse
import datetime
import json
import os
import random
import subprocess
import sys
import uuid

DEFAULT_CONFIG = {
    "schedule": {
        "mode": "random",
        "fixed_count": 5,
        "min_count": 3,
        "max_count": 7
    },
    "git": {
        "author_name": "Syqopat",
        "author_email": "203693835+Syqopat@users.noreply.github.com",
        "branch": "main",
        "auto_push": True,
        "data_file": "data/activity.json"
    },
    "windows_event_log": {
        "enabled": True,
        "log_name": "Application",
        "source_name": "Application",
        "event_id": 100
    }
}

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
                check=False
            )
            return True
        except Exception:
            return False

def determine_contribution_count(schedule_config, args):
    if args.count is not None:
        return max(1, args.count)
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

def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Automated GitHub contribution generator and activity manager."
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
    parser.add_argument("--install-task", action="store_true", help="Register daily task in Windows Task Scheduler.")
    parser.add_argument("--uninstall-task", action="store_true", help="Unregister daily task from Windows Task Scheduler.")
    parser.add_argument("--task-time", type=str, default="12:00PM", help="Daily execution time for Windows Task Scheduler.")
    return parser.parse_args()

def install_windows_task(task_name="ContributionFarmDaily", task_time="12:00PM"):
    python_exe = sys.executable
    script_path = os.path.abspath(__file__)
    working_dir = os.path.dirname(script_path)
    cmd = (
        f"$action = New-ScheduledTaskAction -Execute '{python_exe}' "
        f"-Argument '\"{script_path}\" --push' -WorkingDirectory '{working_dir}'; "
        f"$trigger = New-ScheduledTaskTrigger -Daily -At '{task_time}'; "
        f"$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries; "
        f"Register-ScheduledTask -TaskName '{task_name}' -Action $action -Trigger $trigger -Settings $settings -Force -Description 'Daily Contribution Farm Runner'"
    )
    result = subprocess.run(["powershell", "-NoProfile", "-Command", cmd], capture_output=True, text=True)
    if result.returncode == 0:
        print(f"Windows Task Scheduler: '{task_name}' registered successfully to run daily at {task_time}.")
        write_windows_event_log(
            f"ContributionFarm: Scheduled daily task '{task_name}' registered for {task_time}.",
            event_type="Information",
            event_id=100
        )
    else:
        print(f"Failed to register Windows task: {result.stderr.strip()}", file=sys.stderr)

def uninstall_windows_task(task_name="ContributionFarmDaily"):
    cmd = f"Unregister-ScheduledTask -TaskName '{task_name}' -Confirm:$false"
    result = subprocess.run(["powershell", "-NoProfile", "-Command", cmd], capture_output=True, text=True)
    if result.returncode == 0:
        print(f"Windows Task Scheduler: '{task_name}' unregistered successfully.")
        write_windows_event_log(
            f"ContributionFarm: Scheduled daily task '{task_name}' unregistered.",
            event_type="Information",
            event_id=100
        )
    else:
        print(f"Failed to unregister Windows task: {result.stderr.strip()}", file=sys.stderr)

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

def record_activity_entry(file_path, run_id, index, total):
    data = load_activity_data(file_path)
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
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
        env=process_env
    )
    if result.returncode != 0:
        raise RuntimeError(f"Git command failed: git {' '.join(args)}\n{result.stderr.strip()}")
    return result.stdout.strip()

def configure_git_identity(author_name, author_email):
    execute_git(["config", "user.name", author_name])
    execute_git(["config", "user.email", author_email])

def create_contributions(count, author_name, author_email, data_file, dry_run=False):
    if count <= 0:
        raise ValueError("Commit count must be greater than zero.")
    run_id = str(uuid.uuid4())
    print(f"Starting contribution run {run_id} with count: {count}")
    if not dry_run:
        configure_git_identity(author_name, author_email)
    git_env = {
        "GIT_AUTHOR_NAME": author_name,
        "GIT_AUTHOR_EMAIL": author_email,
        "GIT_COMMITTER_NAME": author_name,
        "GIT_COMMITTER_EMAIL": author_email
    }
    total_cumulative = 0
    for index in range(1, count + 1):
        total_cumulative = record_activity_entry(data_file, run_id, index, count)
        message = f"chore(farm): update daily activity record [{index}/{count}]"
        if dry_run:
            print(f"[DRY-RUN] Step {index}/{count} | Cumulative: {total_cumulative} | {message}")
        else:
            execute_git(["add", data_file])
            execute_git(["commit", "-m", message], env=git_env)
            print(f"Committed {index}/{count} (Total: {total_cumulative}): {message}")
    print(f"Successfully processed {count} contribution entries.")
    return run_id, total_cumulative

def push_changes(branch):
    print(f"Pushing commits to branch '{branch}'...")
    output = execute_git(["push", "origin", branch])
    print("Push completed successfully.")
    return output

def main():
    args = parse_arguments()
    if args.install_task:
        install_windows_task(task_time=args.task_time)
        return
    if args.uninstall_task:
        uninstall_windows_task()
        return

    config = load_configuration(args.config)
    schedule_cfg = config.get("schedule", {})
    git_cfg = config.get("git", {})
    win_cfg = config.get("windows_event_log", {})

    count = determine_contribution_count(schedule_cfg, args)
    author_name = args.author_name or os.environ.get("FARM_AUTHOR_NAME") or git_cfg.get("author_name", "Syqopat")
    author_email = args.author_email or os.environ.get("FARM_AUTHOR_EMAIL") or git_cfg.get("author_email", "203693835+Syqopat@users.noreply.github.com")
    branch = args.branch or os.environ.get("FARM_BRANCH") or git_cfg.get("branch", "main")
    data_file = args.data_file or git_cfg.get("data_file", "data/activity.json")
    auto_push = args.push or git_cfg.get("auto_push", False)

    start_log_message = (
        f"ContributionFarm started: Target count={count}, Author={author_name}, "
        f"Branch={branch}, DryRun={args.dry_run}"
    )
    if win_cfg.get("enabled", True):
        write_windows_event_log(
            start_log_message,
            event_type="Information",
            event_id=win_cfg.get("event_id", 100),
            log_name=win_cfg.get("log_name", "Application")
        )

    try:
        run_id, total_cumulative = create_contributions(
            count=count,
            author_name=author_name,
            author_email=author_email,
            data_file=data_file,
            dry_run=args.dry_run
        )
        if auto_push and not args.dry_run:
            push_changes(branch)

        finish_log_message = (
            f"ContributionFarm completed successfully: {count} contributions generated. "
            f"Run ID={run_id}, Cumulative total={total_cumulative}."
        )
        if win_cfg.get("enabled", True):
            write_windows_event_log(
                finish_log_message,
                event_type="Information",
                event_id=win_cfg.get("event_id", 100),
                log_name=win_cfg.get("log_name", "Application")
            )
    except Exception as exc:
        error_message = f"ContributionFarm failed: {exc}"
        print(error_message, file=sys.stderr)
        if win_cfg.get("enabled", True):
            write_windows_event_log(
                error_message,
                event_type="Error",
                event_id=win_cfg.get("event_id", 100),
                log_name=win_cfg.get("log_name", "Application")
            )
        sys.exit(1)

if __name__ == "__main__":
    main()
