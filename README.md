# Contribution Farm

[![CI](https://github.com/Syqopat/contribution-farm/actions/workflows/ci.yml/badge.svg)](https://github.com/Syqopat/contribution-farm/actions/workflows/ci.yml)
[![Daily Contribution Farm](https://github.com/Syqopat/contribution-farm/actions/workflows/daily-contributions.yml/badge.svg)](https://github.com/Syqopat/contribution-farm/actions/workflows/daily-contributions.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

Contribution Farm is an automated open-source GitHub activity engine and contribution manager. It executes scheduled daily commits (defaulting to 5 contributions daily) to keep repository metrics up to date while recording structured telemetry in an activity ledger.

## Features

- **Automated Daily Schedule**: Runs automatically once per day via GitHub Actions cron schedule.
- **Configurable Contribution Quota**: Default of 5 contributions per day, adjustable via workflow inputs or command-line parameters.
- **Structured Activity Ledger**: Tracks every contribution batch with UUIDs, timestamps, cumulative counts, and run parameters inside `data/activity.json`.
- **Zero Third-Party Dependencies**: Pure Python standard library implementation requiring no external package installations.
- **Manual Trigger Support**: Trigger runs anytime with custom commit counts via GitHub Actions `workflow_dispatch`.
- **Continuous Integration**: Complete unit test suite with CI validation across pull requests and pushes.

## Architecture

The system operates through an automated pipeline:

1. **Trigger**: GitHub Actions scheduler activates the workflow daily at 12:00 UTC (or manually through `workflow_dispatch`).
2. **Execution**: The runner invokes `farm.py` with the desired contribution count and author metadata.
3. **Ledger Update**: The script updates `data/activity.json` incrementally, calculating cumulative statistics.
4. **Git Operations**: Individual git commits are generated adhering to Conventional Commits standards.
5. **Synchronization**: Commits are pushed to the target branch (`main`), updating GitHub activity graphs.

## Repository Setup

To ensure automated runs have permission to write to your repository:

1. Open your repository on GitHub.
2. Navigate to **Settings** > **Actions** > **General**.
3. Scroll to **Workflow permissions**.
4. Select **Read and write permissions**.
5. Click **Save**.

## Local Usage

### Prerequisites

- Python 3.10 or higher
- Git installed and configured

### Running the Engine

Perform a dry run to inspect the contribution plan without making git commits:

```bash
python farm.py --count 5 --dry-run
```

Generate 5 local commits:

```bash
python farm.py --count 5
```

Generate 5 commits and push them to remote:

```bash
python farm.py --count 5 --push
```

### Command Line Options

| Option | Type | Default | Description |
| --- | --- | --- | --- |
| `--count` | Integer | `5` | Number of contributions to generate in the current run |
| `--author-name` | String | `Syqopat` | Git author and committer name |
| `--author-email` | String | `203693835+Syqopat@users.noreply.github.com` | Git author and committer email |
| `--branch` | String | `main` | Target branch to commit and push |
| `--data-file` | String | `data/activity.json` | Path to the activity tracking JSON file |
| `--dry-run` | Flag | `False` | Simulates the run without executing git commits |
| `--push` | Flag | `False` | Pushes generated commits to the remote repository |

## Environment Variables

| Variable | Description |
| --- | --- |
| `FARM_COMMIT_COUNT` | Default number of contributions when `--count` is omitted |
| `FARM_AUTHOR_NAME` | Default git author name |
| `FARM_AUTHOR_EMAIL` | Default git author email |
| `FARM_BRANCH` | Default target git branch |

## Running Tests

Execute the unit test suite:

```bash
python -m unittest discover tests
```

## Community and Governance

- [Contributing Guidelines](CONTRIBUTING.md)
- [Code of Conduct](CODE_OF_CONDUCT.md)
- [Security Policy](SECURITY.md)

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
