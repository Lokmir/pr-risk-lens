# PR Risk Lens

[![Tests](https://github.com/Lokmir/pr-risk-lens/actions/workflows/tests.yml/badge.svg)](https://github.com/Lokmir/pr-risk-lens/actions/workflows/tests.yml)

Transparent risk scoring for Python pull requests.

PR Risk Lens is a local-first CLI tool that analyzes Git changes and produces a simple, explainable risk score for Python pull requests.

The goal is not to block developers with a black-box score. The goal is to make pull request risk easier to understand by showing clear factors such as changed files, line changes, test coverage signals, and sensitive file changes.

## Project links

- [Changelog](CHANGELOG.md)
- [Contributing guide](CONTRIBUTING.md)
- [Releases](https://github.com/Lokmir/pr-risk-lens/releases)

## Features

PR Risk Lens can:

* analyze local Git working tree changes;
* compare the current branch against a base branch;
* list changed files;
* count added and deleted lines;
* detect test file changes;
* detect risk-sensitive files;
* compute a transparent risk score;
* output text, JSON, or Markdown reports;
* write reports to files;
* fail with a non-zero exit code when the score exceeds a maximum threshold;
* run in CI workflows.

## Installation for development

Clone the repository:

```powershell
git clone https://github.com/Lokmir/pr-risk-lens.git
cd pr-risk-lens
```

Create and activate a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install the project in editable mode with development dependencies:

```powershell
python -m pip install -e ".[dev]"
```

Run the checks:

```powershell
ruff check .
ruff format --check .
pytest
```

## Quick start

Analyze local working tree changes:

```powershell
pr-risk-lens analyze
```

Compare the current branch against `main`:

```powershell
pr-risk-lens analyze --base main
```

Generate a Markdown report:

```powershell
pr-risk-lens analyze --format markdown
```

Write a Markdown report to a file:

```powershell
pr-risk-lens analyze --format markdown --output pr-risk-report.md
```

Fail when the risk score is above a threshold:

```powershell
pr-risk-lens analyze --base main --max-score 60
```

Show the installed version:

```powershell
pr-risk-lens --version
```

## Example text output

```text
PR Risk Lens
Transparent risk scoring for Python pull requests.

Mode: local working tree

Changed files:
- README.md
- src/pr_risk_lens/cli.py
- tests/test_cli.py

Diff stats:
Lines added: 42
Lines deleted: 8

Tests:
Test files changed: Yes
- tests/test_cli.py

Sensitive files:
Sensitive files changed: No

Risk:
Risk score: 15/100
Risk level: Low

Risk factors:
- Change size: 50 changed lines (+10)
- Files changed: 3 files (+5)
```

## Output formats

PR Risk Lens supports three output formats.

| Format   | Command                                  | Use case                           |
| -------- | ---------------------------------------- | ---------------------------------- |
| Text     | `pr-risk-lens analyze --format text`     | Human-readable terminal output     |
| JSON     | `pr-risk-lens analyze --format json`     | Automation and scripts             |
| Markdown | `pr-risk-lens analyze --format markdown` | CI reports, PR comments, artifacts |

Text output is the default:

```powershell
pr-risk-lens analyze
```

The legacy `--json` flag is still supported for backwards compatibility:

```powershell
pr-risk-lens analyze --json
```

You can write any format to a file:

```powershell
pr-risk-lens analyze --format markdown --output pr-risk-report.md
```

## Example Markdown output

```markdown
# PR Risk Lens Report

Transparent risk scoring for Python pull requests.

## Mode

Branch comparison against `main`.

## Summary

- **Risk score:** 45/100
- **Risk level:** Medium
- **Changed files:** 3
- **Lines added:** 120
- **Lines deleted:** 18
- **Test files changed:** Yes
- **Sensitive files changed:** No

## Changed files

- `src/pr_risk_lens/cli.py`
- `src/pr_risk_lens/report.py`
- `tests/test_cli.py`

## Risk factors

- Change size: 138 changed lines `+25`
- Files changed: 3 files `+5`
```

## CI usage

PR Risk Lens can be used in GitHub Actions to analyze pull-request-like changes.

### Fail when risk is too high

```yaml
name: PR Risk Lens

on:
  pull_request:
    branches:
      - main

jobs:
  risk:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout repository
        uses: actions/checkout@v6
        with:
          fetch-depth: 0

      - name: Set up Python
        uses: actions/setup-python@v6
        with:
          python-version: "3.11"

      - name: Install PR Risk Lens
        run: python -m pip install -e .

      - name: Analyze pull request risk
        run: pr-risk-lens analyze --base origin/main --max-score 60
```

In this example:

* `--base origin/main` compares the pull request branch against the main branch;
* `--max-score 60` fails the workflow if the risk score is greater than `60`;
* `fetch-depth: 0` gives Git enough history to compare branches correctly.

### Generate a Markdown report artifact

```yaml
name: PR Risk Lens Report

on:
  pull_request:
    branches:
      - main

jobs:
  risk-report:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout repository
        uses: actions/checkout@v6
        with:
          fetch-depth: 0

      - name: Set up Python
        uses: actions/setup-python@v6
        with:
          python-version: "3.11"

      - name: Install PR Risk Lens
        run: python -m pip install -e .

      - name: Generate Markdown risk report
        run: |
          pr-risk-lens analyze \
            --base origin/main \
            --format markdown \
            --output pr-risk-report.md

      - name: Upload risk report
        uses: actions/upload-artifact@v7
        with:
          name: pr-risk-report
          path: pr-risk-report.md
```

This workflow:

* compares the pull request branch against `origin/main`;
* generates a Markdown report;
* stores the report as a downloadable GitHub Actions artifact.

## Maximum score threshold

PR Risk Lens can fail the command when the risk score is greater than a chosen threshold:

```powershell
pr-risk-lens analyze --max-score 60
```

Behavior:

* if the risk score is less than or equal to the threshold, the command exits with code `0`;
* if the risk score is greater than the threshold, the command exits with code `1`.

Example:

```text
Risk:
Risk score: 75/100
Risk level: High

Risk score 75 exceeds max score 60.
```

## Risk scoring

The score is intentionally simple and transparent.

Current factors:

| Factor                                         | Points |
| ---------------------------------------------- | -----: |
| Small change size, up to 50 changed lines      |    +10 |
| Medium change size, up to 200 changed lines    |    +25 |
| Large change size, more than 200 changed lines |    +40 |
| Up to 3 changed files                          |     +5 |
| Up to 10 changed files                         |    +15 |
| More than 10 changed files                     |    +25 |
| Python source changes without test changes     |    +10 |
| Risk-sensitive files changed                   |    +10 |

Risk levels:

|        Score | Level  |
| -----------: | ------ |
|            0 | None   |
|      1 to 30 | Low    |
|     31 to 60 | Medium |
| 61 and above | High   |

## Detection rules

### Test files

A file is considered a test file when:

* it is inside a `tests` folder;
* its name starts with `test_`;
* its name ends with `_test.py`.

Examples:

```text
tests/test_cli.py
test_report.py
report_test.py
```

### Risk-sensitive files

The following files are currently considered risk-sensitive:

```text
pyproject.toml
requirements.txt
requirements-dev.txt
setup.py
setup.cfg
tox.ini
Dockerfile
docker-compose.yml
docker-compose.yaml
.github/workflows/*.yml
.github/workflows/*.yaml
```

Changing these files adds risk because they may affect packaging, dependencies, CI, or runtime behavior.

## Git behavior

For local working tree analysis, PR Risk Lens uses Git to inspect:

* tracked file changes;
* untracked files;
* added and deleted lines;
* renamed files.

For untracked files, PR Risk Lens counts readable text lines as added lines. Binary or unreadable untracked files are counted as `0` added lines so the analysis does not crash.

Git output is normalized to keep reports stable:

* changed files are sorted;
* duplicate paths are removed;
* duplicate diff stats are merged;
* renamed files use the destination path.

## Exit codes

| Exit code | Meaning                           |
| --------: | --------------------------------- |
|         0 | Analysis succeeded                |
|         1 | Risk score exceeded `--max-score` |
|         2 | Git command error                 |

## Development

Run all checks locally:

```powershell
ruff check .
ruff format --check .
pytest
```

Automatically fix supported Ruff issues:

```powershell
ruff check . --fix
ruff format .
```

Build the package:

```powershell
python -m build
twine check dist/*
```

Clean generated build files:

```powershell
Remove-Item -Recurse -Force dist -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force build -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force src/pr_risk_lens.egg-info -ErrorAction SilentlyContinue
```

## Project philosophy

PR Risk Lens should stay:

* local-first;
* transparent;
* explainable;
* lightweight;
* useful in CI;
* understandable without AI or external services.

AI may be explored later, but the core scoring should remain deterministic and rule-based.

## License

This project is licensed under the MIT License.