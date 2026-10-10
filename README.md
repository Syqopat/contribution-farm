# Contribution Farm

[![CI](https://github.com/Syqopat/contribution-farm/actions/workflows/ci.yml/badge.svg)](https://github.com/Syqopat/contribution-farm/actions/workflows/ci.yml)
[![Daily Contribution Farm](https://github.com/Syqopat/contribution-farm/actions/workflows/daily-contributions.yml/badge.svg)](https://github.com/Syqopat/contribution-farm/actions/workflows/daily-contributions.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

Contribution Farm is an automated open-source GitHub activity engine and contribution manager. It provides configurable daily runs, dynamic randomized contribution ranges, automatic Windows Event Log telemetry, and native Windows Task Scheduler integration alongside cloud GitHub Actions workflows.

## Key Features

- **Automated Daily Scheduling**: Operates daily via GitHub Actions in the cloud and natively via Windows Task Scheduler locally.
- **Configurable Contribution Engine**: Fully customizable via `config.json` with support for fixed quotas or dynamic randomized ranges.
- **Dynamic Randomization**: Generates a randomized number of contributions within a specified range (for example, between 3 and 7 commits per day) to simulate realistic developer activity patterns.
- **Windows Event Log Telemetry**: Automatically records run lifecycle events (start status, commit counts, cumulative totals, errors) directly into the Windows Application Event Log.
- **Task Scheduler Integration**: One-command installation and uninstallation of daily background tasks on Windows.
- **Structured Activity Ledger**: Tracks every contribution batch with UUIDs, timestamps, cumulative counts, and run parameters inside `data/activity.json`.
- **Zero Third-Party Dependencies**: Pure Python standard library implementation with optional native `pywin32` / PowerShell fallbacks.

## Configuration (`config.json`)

The application is controlled by `config.json` at the root of the repository:

```json
{
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
    "auto_push": true,
    "data_file": "data/activity.json"
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
| `git` | `author_name` | String | `"Syqopat"` | Git commit author and committer name |
| `git` | `author_email` | String | `"203693835+Syqopat@users.noreply.github.com"` | Git commit author and committer email |
| `git` | `branch` | String | `"main"` | Target branch to update and push |
| `git` | `auto_push` | Boolean | `true` | Automatically pushes commits to remote |
| `git` | `data_file` | String | `"data/activity.json"` | Path to JSON activity ledger |
| `windows_event_log` | `enabled` | Boolean | `true` | Enables writing telemetry to Windows Event Log |
| `windows_event_log` | `log_name` | String | `"Application"` | Windows Event Log channel |
| `windows_event_log` | `event_id` | Integer | `100` | Event ID used for recorded entries |

## Automation Setup

### 1. Windows Task Scheduler (Daily Local Automation)

To register Contribution Farm to run automatically every day on Windows:

```bash
python farm.py --install-task --task-time "12:00PM"
```

The scheduled task is configured with `pythonw.exe`, `-Hidden`, and `CREATE_NO_WINDOW`, ensuring that no terminal window, console, or popup appears when it runs.

To remove the scheduled task:

```bash
python farm.py --uninstall-task
```

### 2. Instant Silent Execution (`run_silent.vbs`)

To run the farm silently in the background on demand without any command prompt window:

- Double-click `run_silent.vbs`, or
- Run `wscript.exe run_silent.vbs` from terminal or shortcut.

### 3. GitHub Actions (Daily Cloud Automation)

Contribution Farm runs in GitHub Actions every day at 12:00 UTC. Ensure workflow write permissions are active:

1. Open your repository on GitHub.
2. Go to **Settings** > **Actions** > **General**.
3. Under **Workflow permissions**, select **Read and write permissions**.
4. Save your changes.

You can also trigger runs on demand via the **Actions** tab with custom mode and contribution counts.

## Windows Event Log Telemetry

Every execution writes telemetry events to the Windows `Application` log:

- **Start Event**: Logs execution start, targeted contribution quota, branch, and configuration mode.
- **Completion Event**: Logs the successful run ID, total contributions produced, and overall cumulative count.
- **Error Event**: Logs any uncaught exceptions with full diagnostic details.

To view logged events in PowerShell:

```powershell
Get-EventLog -LogName Application -Source Application -Newest 5 | Format-List TimeGenerated, Message
```

## Local CLI Usage

Run using `config.json` settings:

```bash
python farm.py --push
```

Generate a randomized number of contributions between 2 and 6:

```bash
python farm.py --randomize --min 2 --max 6 --push
```

Run in dry-run mode to preview without committing:

```bash
python farm.py --dry-run
```

Generate an explicit fixed count of 10 contributions:

```bash
python farm.py --count 10 --push
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
| `--install-task` | Flag | Register Windows scheduled task |
| `--uninstall-task` | Flag | Unregister Windows scheduled task |
| `--task-time` | String | Scheduled daily execution time (e.g. `"12:00PM"`) |

## Running Tests

Execute all unit tests:

```bash
python -m unittest discover tests
```

## Community and Governance

- [Contributing Guidelines](CONTRIBUTING.md)
- [Code of Conduct](CODE_OF_CONDUCT.md)
- [Security Policy](SECURITY.md)

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
