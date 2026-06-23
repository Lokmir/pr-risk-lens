# PR Risk Lens

Transparent risk scoring for Python pull requests.

PR Risk Lens is a local-first Python CLI tool that analyzes Git changes and produces a clear, transparent risk report.

The goal is not to replace human code review.
The goal is to provide a first simple, explainable signal before review.

## Current status

Early MVP.

The tool can currently:

* detect changed files in a Git repository;
* include modified and untracked files;
* count added and deleted lines;
* compute a simple transparent risk score;
* explain which factors contributed to the score.

No LLM or external API is used.

## Installation for development

Requirements:

* Python 3.11 or higher
* Git

Create and activate a virtual environment:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

Install the project in editable mode:

```powershell
python -m pip install -e ".[dev]"
```

Run the tests:

```powershell
pytest
```

## Usage

From inside a Git repository, run:

```powershell
pr-risk-lens analyze
```

Example output:

```text
PR Risk Lens
Transparent risk scoring for Python pull requests.

Changed files:
- src/pr_risk_lens/cli.py
- src/pr_risk_lens/report.py
- tests/test_cli.py
- tests/test_report.py

Diff stats:
Lines added: 150
Lines deleted: 7

Risk:
Risk score: 40/100
Risk level: Medium

Risk factors:
- Change size: 157 changed lines (+25)
- Files changed: 4 files (+15)
```
### JSON output

PR Risk Lens can also output the report as JSON:

```powershell
pr-risk-lens analyze --json
```

Example output:

```json
{
  "changed_files": [
    "README.md",
    "src/pr_risk_lens/cli.py"
  ],
  "diff_stats": {
    "lines_added": 20,
    "lines_deleted": 4,
    "total_changed_lines": 24
  },
  "risk": {
    "score": 15,
    "level": "Low",
    "factors": [
      {
        "label": "Change size: 24 changed lines",
        "points": 10
      },
      {
        "label": "Files changed: 2 files",
        "points": 5
      }
    ]
  }
}
```

This is useful for automation, CI workflows, or future integrations.


### Branch comparison mode

By default, PR Risk Lens analyzes local working tree changes:

```powershell
pr-risk-lens analyze
```

This is useful before committing your local changes.

To analyze the current branch against a base branch, use:

```powershell
pr-risk-lens analyze --base main
```

This compares the current branch against `main`, which is closer to how a Pull Request is reviewed.

Example:

```text
PR Risk Lens
Transparent risk scoring for Python pull requests.

Mode: branch comparison against main

Changed files:
- src/payment.py
- tests/test_payment.py

Diff stats:
Lines added: 80
Lines deleted: 12

Tests:
Test files changed: Yes
- tests/test_payment.py

Risk:
Risk score: 30/100
Risk level: Low

Risk factors:
- Change size: 92 changed lines (+25)
- Files changed: 2 files (+5)
```

Use this mode when you are working on a feature branch and want to compare it with the main branch before opening a Pull Request.

## Risk scoring rules

The current score is intentionally simple and transparent.

Change size:

* 1 to 50 changed lines: +10
* 51 to 200 changed lines: +25
* More than 200 changed lines: +40

Files changed:

* 1 to 3 files: +5
* 4 to 10 files: +15
* More than 10 files: +25

Risk levels:

* 0: None
* 1 to 30: Low
* 31 to 60: Medium
* 61 and above: High

## Project philosophy

PR Risk Lens should be:

* local-first;
* simple to understand;
* transparent in its scoring;
* useful before human review;
* friendly for Python beginners and open source maintainers.

## Roadmap

Possible next steps:

* add JSON output;
* detect risky file types;
* detect test changes;
* add configuration;
* support comparison against a base branch;
* optionally add AI explanations later.
