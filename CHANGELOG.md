# Changelog

All notable changes to PR Risk Lens will be documented in this file.

## Unreleased

## v0.3.2 - 2026-06-24

### Added

* Review-focused Markdown summary designed for pull request comments.
* Review focus section in Markdown reports and summaries.
* Generated PR Risk Lens report files in `.gitignore`.

### Changed

* Made full Markdown reports and Markdown summaries more distinct.
* Improved full Markdown reports with a verdict, detailed summary table, risk factor table, and interpretation section.
* Improved Markdown summaries with a compact decision-oriented layout.
* Improved risk factor wording with singular and plural labels such as `1 file` and `2 files`.

## v0.3.1 - 2026-06-24

### Added

* Short Markdown summary mode with `pr-risk-lens analyze --format markdown --summary`.
* GitHub Actions example for commenting pull requests with a PR Risk Lens Markdown summary.

### Changed

* Improved Markdown report readability with a summary table and review guidance.
* Documented Markdown summary output for pull request comments.

## v0.3.0 - 2026-06-24

### Added

* Markdown output format with `pr-risk-lens analyze --format markdown`.
* Structured output format option with `--format text`, `--format json`, and `--format markdown`.
* Output file option with `pr-risk-lens analyze --output FILE`.
* GitHub Actions example for generating a Markdown risk report artifact.

### Changed

* Kept `--json` as a backwards-compatible shortcut for JSON output.
* Reorganized the README for clearer project usage, CI examples, output formats, and project links.

## v0.2.0 - 2026-06-24

### Added

* Ruff linting and formatting configuration.
* Ruff checks in GitHub Actions.
* Package build verification in GitHub Actions.
* Installed CLI smoke test in GitHub Actions.
* CLI version option with `pr-risk-lens --version`.
* `CHANGELOG.md`.
* `CONTRIBUTING.md`.
* Package build metadata for future PyPI publishing.
* Package metadata validation with `twine check`.

### Changed

* Updated README with version command documentation.
* Improved CI workflow to validate linting, formatting, tests, package build, package metadata, and installed CLI behavior.

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