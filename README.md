# PR Risk Lens

[![Tests](https://github.com/Lokmir/pr-risk-lens/actions/workflows/tests.yml/badge.svg)](https://github.com/Lokmir/pr-risk-lens/actions/workflows/tests.yml)

Transparent risk scoring for Python pull requests.

PR Risk Lens is a local-first CLI tool that analyzes Git changes and produces a simple, explainable risk score for Python pull requests.

The goal is not to block developers with a black-box score. The goal is to make pull request risk easier to understand by showing clear factors such as changed files, line changes, test coverage signals, and sensitive file changes.

## Current status

PR Risk Lens is currently an MVP.

It can:

* analyze local Git working tree changes;
* compare the current branch against a base branch;
* list changed files;
* count added and deleted lines;
* detect test file changes;
* detect risk-sensitive files;
* compute a transparent risk score;
* output a human-readable report;
* output JSON;
* exit with a non-zero code when the score exceeds a maximum threshold.

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

Run the tests:

```powershell
pytest
```

## Usage

Analyze local working tree changes:

```powershell
pr-risk-lens analyze
```

Example output:

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

## Compare against a base branch

Analyze the current branch against a base reference:

```powershell
pr-risk-lens analyze --base main
```

This is useful when analyzing pull-request-like changes locally.

## JSON output

Output the report as JSON:

```powershell
pr-risk-lens analyze --json
```

You can also combine JSON output with a base branch:

```powershell
pr-risk-lens analyze --base main --json
```

## Maximum score threshold

PR Risk Lens can fail the command when the risk score is greater than a chosen threshold:

```powershell
pr-risk-lens analyze --max-score 60
```

This is useful in CI because a non-zero exit code can fail a workflow.

You can combine it with branch comparison:

```powershell
pr-risk-lens analyze --base main --max-score 60
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

## Test file detection

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

## Sensitive file detection

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

Run all tests:

```powershell
pytest
```

Run the CLI locally:

```powershell
pr-risk-lens analyze
```

Run JSON output:

```powershell
pr-risk-lens analyze --json
```

Run branch comparison:

```powershell
pr-risk-lens analyze --base main
```

Run threshold mode:

```powershell
pr-risk-lens analyze --max-score 60
```

## Project philosophy

PR Risk Lens should stay:

* local-first;
* transparent;
* explainable;
* lightweight;
* useful in CI;
* understandable without AI or external services.

AI may be explored later, but the MVP is deliberately deterministic and rule-based.