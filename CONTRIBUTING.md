# Contributing to PR Risk Lens

Thank you for your interest in contributing to PR Risk Lens.

PR Risk Lens is a local-first CLI tool for transparent risk scoring of Python pull requests. The project aims to stay simple, deterministic, explainable, and useful in CI.

## Development setup

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

Install the project with development dependencies:

```powershell
python -m pip install -e ".[dev]"
```

## Run checks locally

Before submitting a change, run:

```powershell
ruff check .
ruff format --check .
pytest
```

To automatically fix supported Ruff issues:

```powershell
ruff check . --fix
ruff format .
```

Then run the full checks again:

```powershell
ruff check .
ruff format --check .
pytest
```

## Project principles

PR Risk Lens should remain:

* local-first;
* transparent;
* deterministic;
* lightweight;
* easy to understand;
* useful in CI;
* friendly to beginner contributors.

Avoid adding external services, network calls, or AI-based behavior to the core MVP path.

## Contribution workflow

1. Create a branch from `main`.
2. Make a focused change.
3. Add or update tests when behavior changes.
4. Run Ruff and pytest locally.
5. Open a pull request with a clear explanation of the change.

## Pull request checklist

Before opening a pull request, check that:

* `ruff check .` passes;
* `ruff format --check .` passes;
* `pytest` passes;
* the README or changelog is updated when needed;
* the change keeps the scoring logic explainable.

## Reporting issues

When reporting a bug, please include:

* the command you ran;
* the expected behavior;
* the actual behavior;
* your operating system;
* your Python version;
* relevant Git state, if possible.

Example:

```text
Command:
pr-risk-lens analyze --base main

Expected:
A risk report is displayed.

Actual:
The command exits with an error.

Environment:
Windows 11
Python 3.11
```

## Scope

Good first contributions include:

* improving documentation;
* adding tests;
* improving error messages;
* refining transparent scoring rules;
* improving CLI output readability.

Large changes to the scoring model should stay explainable and be covered by tests.