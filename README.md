# Contribution Farm

[![CI](https://github.com/Syqopat/contribution-farm/actions/workflows/ci.yml/badge.svg)](https://github.com/Syqopat/contribution-farm/actions/workflows/ci.yml)
[![Daily Contribution Farm](https://github.com/Syqopat/contribution-farm/actions/workflows/daily-contributions.yml/badge.svg)](https://github.com/Syqopat/contribution-farm/actions/workflows/daily-contributions.yml)
[![Platform](https://img.shields.io/badge/platform-Linux%20%7C%20Windows-blue.svg)](#)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

Contribution Farm is an automated open-source GitHub activity engine and contribution manager with full cross-platform support for **Linux** and **Windows**. It provides configurable daily schedules, dynamic randomized contribution ranges, cross-platform telemetry (Linux Syslog / journalctl & Windows Event Log), and native OS scheduling (Linux Crontab, Systemd user timers, and Windows Task Scheduler) alongside cloud GitHub Actions workflows.

---

## Key Features

- **Cross-Platform Scheduling**: Runs natively on Linux via **Crontab** or **Systemd User Timers**, on Windows via **Task Scheduler**, and in the cloud via **GitHub Actions**.
- **Configurable Contribution Engine**: Fully customizable via `config.json` with support for fixed quotas or dynamic randomized ranges.
- **Dynamic Randomization**: Generates a natural, randomized number of contributions within a specified range (e.g. 3 to 7 commits/day) to simulate authentic developer activity.
- **Weekend Awareness**: Automatically reduces quotas or skips contributions entirely on weekends according to your preferences.
- **Jitter & Natural Timestamps**: Naturally disperses commit timestamps across an execution window instead of clustering them in a single second.
- **Cross-Platform Telemetry**:
  - **Linux**: Automatically streams lifecycle events to the system log (`syslog` / `journalctl`).
  - **Windows**: Automatically logs start, completion, and error events to the Windows `Application` Event Log.
  - **File Logging**: Appends timestamped execution records to `farm.log`.
- **Silent Background Execution**:
  - **Linux**: Execute silently in the background with `./run_silent.sh`.
  - **Windows**: Execute silently with no popup window using `run_silent.vbs`.
- **Structured Activity Ledger**: Tracks every contribution batch with UUIDs, timestamps, cumulative counts, and run parameters inside `data/activity.json`.
- **Zero Third-Party Dependencies**: Pure Python standard library implementation with zero external package requirements.

---

## Quick Start

### On Linux

```bash
# Clone the repository
git clone https://github.com/Syqopat/contribution-farm.git
cd contribution-farm

# Ensure script is executable
chmod +x farm.py run_silent.sh

# Run a test dry-run
./farm.py --dry-run

# Run and push contributions
./farm.py --push

# Register automated daily cron job at 12:00 PM
./farm.py --install-cron --task-time "12:00PM"
```

### On Windows

```cmd
# Clone the repository
git clone https://github.com/Syqopat/contribution-farm.git
cd contribution-farm

# Run a test dry-run
python farm.py --dry-run

# Run and push contributions
python farm.py --push

# Register automated daily task at 12:00 PM
python farm.py --install-task --task-time "12:00PM"
```

---

## Configuration (`config.json`)

The application is controlled by `config.json` at the root of the repository:

```json
{
  "schedule": {
    "mode": "random",
    "fixed_count": 5,
    "min_count": 3,
    "max_count": 7,
    "weekend_mode": "reduce",
    "weekend_min": 1,
    "weekend_max": 2,
    "skip_weekends": false,
    "message_mode": "realistic",
    "jitter_enabled": true,
    "jitter_spread_minutes": 180
  },
  "git": {
    "author_name": "Syqopat",
    "author_email": "203693835+Syqopat@users.noreply.github.com",
    "branch": "main",
    "auto_push": true,
    "data_file": "data/activity.json"
  },
  "telemetry": {
    "enabled": true,
    "system_log": true,
    "file_log": true,
    "log_file": "farm.log",
    "syslog_ident": "ContributionFarm"
  },
  "windows_event_log": {
    "enabled": true,
    "log_name": "Application",
    "source_name": "Application",
    "event_id": 100
  }
}
```

### Configuration Fields

| Section | Key | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `schedule` | `mode` | String | `"random"` | Execution mode: `"random"` or `"fixed"` |
| `schedule` | `fixed_count` | Integer | `5` | Exact number of contributions when mode is `"fixed"` |
| `schedule` | `min_count` | Integer | `3` | Minimum contributions per day when mode is `"random"` |
| `schedule` | `max_count` | Integer | `7` | Maximum contributions per day when mode is `"random"` |
| `schedule` | `weekend_mode` | String | `"reduce"` | Weekend quota behavior: `"reduce"` or `"normal"` |
| `schedule` | `weekend_min` | Integer | `1` | Lower contribution bound for weekends |
| `schedule` | `weekend_max` | Integer | `2` | Upper contribution bound for weekends |
| `schedule` | `skip_weekends` | Boolean | `false` | Completely skip contribution generation on weekends |
| `schedule` | `message_mode` | String | `"realistic"` | Commit message generator: `"realistic"` or `"standard"` |
| `schedule` | `jitter_enabled` | Boolean | `true` | Naturally spreads commit timestamps across a time window |
| `schedule` | `jitter_spread_minutes` | Integer | `180` | Distribution window size in minutes |
| `git` | `author_name` | String | `"Syqopat"` | Git commit author and committer name |
| `git` | `author_email` | String | `"<your-email>"` | Git commit author and committer email |
| `git` | `branch` | String | `"main"` | Target branch to update and push |
| `git` | `auto_push` | Boolean | `true` | Automatically pushes commits to remote |
| `git` | `data_file` | String | `"data/activity.json"` | Path to JSON activity ledger |
| `telemetry` | `enabled` | Boolean | `true` | Enables system and file telemetry logging |
| `telemetry` | `system_log` | Boolean | `true` | Enables Linux `syslog` / Windows Event Log |
| `telemetry` | `file_log` | Boolean | `true` | Enables appending run events to `farm.log` |
| `telemetry` | `log_file` | String | `"farm.log"` | Path to the local log file |
| `telemetry` | `syslog_ident` | String | `"ContributionFarm"` | Syslog identifier tag on Linux |
| `windows_event_log` | `enabled` | Boolean | `true` | Enables Windows Event Log telemetry |
| `windows_event_log` | `log_name` | String | `"Application"` | Windows Event Log channel |
| `windows_event_log` | `event_id` | Integer | `100` | Event ID used for recorded entries on Windows |

---

## Automation Setup

### 1. Linux Automation

Contribution Farm provides two native Linux scheduling options:

#### Option A: Crontab (Recommended for universal Linux support)

Install a daily scheduled job in user crontab:

```bash
# Register daily execution at 12:00 PM (or specify any time like "14:30")
./farm.py --install-cron --task-time "12:00PM"

# Or use the OS-agnostic flag:
./farm.py --install-task --task-time "12:00PM"
```

To remove the cron job:

```bash
./farm.py --uninstall-cron
```

#### Option B: Systemd User Timer (For modern systemd environments)

Register and activate a persistent systemd user service and timer:

```bash
./farm.py --install-systemd --task-time "12:00PM"
```

To remove the systemd user service and timer:

```bash
./farm.py --uninstall-systemd
```

### 2. Linux Silent Execution (`run_silent.sh`)

To run the farm silently in the background on Linux on demand:

```bash
./run_silent.sh
```

Or pass custom arguments:

```bash
./run_silent.sh --randomize --min 4 --max 8
```

---

### 3. Windows Task Scheduler

To register Contribution Farm to run automatically every day on Windows:

```bash
python farm.py --install-task --task-time "12:00PM"
```

The scheduled task is configured with `pythonw.exe`, `-Hidden`, and `CREATE_NO_WINDOW`, ensuring that no terminal window, console, or popup appears when it runs.

To remove the scheduled task:

```bash
python farm.py --uninstall-task
```

### 4. Windows Silent Execution (`run_silent.vbs`)

To run the farm silently in the background on demand without any command prompt window:

- Double-click `run_silent.vbs`, or
- Run `wscript.exe run_silent.vbs` from terminal or shortcut.

---

### 5. GitHub Actions (Daily Cloud Automation)

Contribution Farm runs in GitHub Actions every day at 12:00 UTC. Ensure workflow write permissions are active:

1. Open your repository on GitHub.
2. Go to **Settings** > **Actions** > **General**.
3. Under **Workflow permissions**, select **Read and write permissions**.
4. Save your changes.

You can also trigger runs on demand via the **Actions** tab with custom mode and contribution counts.

---

## Telemetry & Diagnostics

Every execution records lifecycle events (start status, commit counts, cumulative totals, errors):

### Viewing Telemetry on Linux

View logs recorded in the system journal:

```bash
# View recent system journal logs
journalctl -t ContributionFarm -n 20 --no-pager

# Or view the persistent local log file
tail -n 20 farm.log
```

### Viewing Telemetry on Windows

View logged events in PowerShell:

```powershell
Get-EventLog -LogName Application -Source Application -Newest 5 | Format-List TimeGenerated, Message
```

---

## Local CLI Usage

Run using `config.json` settings:

```bash
./farm.py --push
```

Generate a randomized number of contributions between 2 and 6:

```bash
./farm.py --randomize --min 2 --max 6 --push
```

Run in dry-run mode to preview without committing:

```bash
./farm.py --dry-run
```

Generate an explicit fixed count of 10 contributions:

```bash
./farm.py --count 10 --push
```

### Command Line Arguments

| Argument | Type | Description |
| --- | --- | --- |
| `--config` | String | Path to custom configuration JSON file |
| `--mode` | String | Set mode (`fixed` or `random`) |
| `--randomize` | Flag | Enable random mode |
| `--min` | Integer | Lower bound for random contribution count |
| `--max` | Integer | Upper bound for random contribution count |
| `--count` | Integer | Override with an exact contribution count |
| `--author-name` | String | Git author name override |
| `--author-email` | String | Git author email override |
| `--branch` | String | Target git branch override |
| `--data-file` | String | Custom ledger path |
| `--dry-run` | Flag | Preview run without creating commits |
| `--push` | Flag | Push commits upon completion |
| `--skip-weekends` | Flag | Skip generating contributions on weekends |
| `--message-mode` | String | Message style (`realistic` or `standard`) |
| `--backfill-days` | Integer | Backfill contributions for the last N days |
| `--backfill-start` | String | Historical backfill start date (`YYYY-MM-DD`) |
| `--backfill-end` | String | Historical backfill end date (`YYYY-MM-DD`) |
| `--install-task` | Flag | Register scheduled daily task (Windows Task Scheduler or Linux Cron) |
| `--uninstall-task` | Flag | Unregister scheduled daily task |
| `--install-cron` | Flag | Register daily task in Linux Crontab |
| `--uninstall-cron` | Flag | Unregister daily task from Linux Crontab |
| `--install-systemd` | Flag | Register daily task as Linux Systemd user timer |
| `--uninstall-systemd` | Flag | Unregister daily task from Linux Systemd |
| `--scheduler` | String | Scheduler backend on Linux (`auto`, `cron`, `systemd`) |
| `--task-time` | String | Scheduled daily execution time (e.g. `"12:00PM"`, `"14:30"`) |

---

## Historical Backfilling

To populate past empty dates on your GitHub contribution graph with realistic contributions:

Backfill the last 14 days:

```bash
./farm.py --backfill-days 14 --push
```

Backfill a specific historical date range:

```bash
./farm.py --backfill-start 2026-09-01 --backfill-end 2026-09-30 --push
```

---

## Verified SSH Commit Signing

Contribution Farm automatically creates cryptographically signed Git commits using your configured SSH signing key.

To display the green **Verified** badge next to your commits on GitHub:

1. Copy your public signing key:
   ```text
   ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIH8lGFqhlqOYgfafhqMd3gShXO1W8t20AOw+ABMPsdJb 203693835+Syqopat@users.noreply.github.com
   ```
2. Navigate to [GitHub SSH and GPG keys](https://github.com/settings/ssh/new).
3. Set **Key type** to **Signing Key**.
4. Paste the key and click **Add SSH key**.

---

## Running Tests

Execute all unit tests across both platforms:

```bash
python3 -m unittest discover tests
```

---

## Community and Governance

- [Contributing Guidelines](CONTRIBUTING.md)
- [Code of Conduct](CODE_OF_CONDUCT.md)
- [Security Policy](SECURITY.md)

---

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
