# Changelog

All notable changes to PR Risk Lens will be documented in this file.

## Unreleased

### Added

* Markdown output format with `pr-risk-lens analyze --format markdown`.
* Structured output format option with `--format text`, `--format json`, and `--format markdown`.

### Changed

* Kept `--json` as a backwards-compatible shortcut for JSON output.

## v0.2.0 - 2026-06-24

### Added

- Ruff linting and formatting configuration.
- Ruff checks in GitHub Actions.
- Package build verification in GitHub Actions.
- Installed CLI smoke test in GitHub Actions.
- CLI version option with `pr-risk-lens --version`.
- `CHANGELOG.md`.
- `CONTRIBUTING.md`.
- Package build metadata for future PyPI publishing.
- Package metadata validation with `twine check`.

### Changed

- Updated README with version command documentation.
- Improved CI workflow to validate linting, formatting, tests, package build, package metadata, and installed CLI behavior.


## v0.1.0 - 2026-06-23

### Added

* Initial MVP release.
* Local Git working tree analysis.
* Base branch comparison with `--base`.
* Human-readable risk report.
* JSON output with `--json`.
* Maximum risk threshold with `--max-score`.
* Transparent risk scoring.
* Test file detection.
* Risk-sensitive file detection.
* Added and deleted line counting.
* Untracked file support.
* Binary or unreadable untracked file handling.
* Stable sorted output.
* Duplicate diff stat merging.
* Git rename normalization.
* Clean Git error messages.
* GitHub Actions test workflow.
* MIT license.
* README documentation.