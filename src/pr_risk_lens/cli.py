import json
from enum import StrEnum
from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as get_package_version
from pathlib import Path

import typer
from rich.console import Console

from pr_risk_lens.git import GitCommandError, get_changed_files, get_diff_stats
from pr_risk_lens.report import RiskReport, build_risk_report

PACKAGE_NAME = "pr-risk-lens"
APP_NAME = "PR Risk Lens"


class OutputFormat(StrEnum):
    text = "text"
    json = "json"
    markdown = "markdown"


app = typer.Typer(
    help="Transparent risk scoring for Python pull requests.",
    no_args_is_help=True,
    invoke_without_command=True,
)
console = Console()

OUTPUT_FORMAT_OPTION = typer.Option(
    OutputFormat.text,
    "--format",
    help="Output format: text, json, or markdown.",
)
OUTPUT_FILE_OPTION = typer.Option(
    None,
    "--output",
    "-o",
    help="Write the report to a file instead of printing it to the terminal.",
)
SUMMARY_OPTION = typer.Option(
    False,
    "--summary",
    help="Output a short Markdown summary instead of the full Markdown report.",
)


@app.callback()
def main(
    show_version: bool = typer.Option(
        False,
        "--version",
        help="Show the installed version and exit.",
        is_eager=True,
    ),
) -> None:
    """
    PR Risk Lens command line interface.
    """
    if show_version:
        console.print(f"{APP_NAME} {_get_installed_version()}")
        raise typer.Exit()


@app.command()
def analyze(
    base: str | None = typer.Option(
        None,
        "--base",
        help="Compare the current branch against a base ref, for example main.",
    ),
    output_format: OutputFormat = OUTPUT_FORMAT_OPTION,
    output_file: Path | None = OUTPUT_FILE_OPTION,
    summary: bool = SUMMARY_OPTION,
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Output the report as JSON. Kept for backwards compatibility.",
    ),
    max_score: int | None = typer.Option(
        None,
        "--max-score",
        help="Exit with code 1 if the risk score is greater than this value.",
    ),
) -> None:
    """
    Analyze Git changes and print a risk report.
    """
    output_format = _resolve_output_format(
        output_format=output_format,
        json_output=json_output,
    )
    _validate_summary_option(
        output_format=output_format,
        summary=summary,
    )

    try:
        changed_files = get_changed_files(base_ref=base)
        diff_stats = get_diff_stats(base_ref=base)
    except GitCommandError as error:
        console.print(f"[red]Error:[/red] {error}")
        raise typer.Exit(code=2) from error

    report = build_risk_report(changed_files, diff_stats)

    report_output = _build_report_output(
        report=report,
        base_ref=base,
        output_format=output_format,
        summary=summary,
    )
    _write_or_print_report(
        report_output=report_output,
        output_file=output_file,
        output_format=output_format,
    )
    _exit_if_score_is_too_high(
        report=report,
        max_score=max_score,
        output_format=output_format,
    )


def _resolve_output_format(
    output_format: OutputFormat,
    json_output: bool,
) -> OutputFormat:
    if json_output and output_format != OutputFormat.text:
        console.print("[red]Error:[/red] Use either --json or --format, not both.")
        raise typer.Exit(code=2)

    if json_output:
        return OutputFormat.json

    return output_format


def _validate_summary_option(
    output_format: OutputFormat,
    summary: bool,
) -> None:
    if summary and output_format != OutputFormat.markdown:
        console.print("[red]Error:[/red] Use --summary with --format markdown.")
        raise typer.Exit(code=2)


def _get_installed_version() -> str:
    try:
        return get_package_version(PACKAGE_NAME)
    except PackageNotFoundError:
        return "unknown"


def _build_report_output(
    report: RiskReport,
    base_ref: str | None,
    output_format: OutputFormat,
    summary: bool,
) -> str:
    if output_format == OutputFormat.json:
        return _build_json_report(report)

    if output_format == OutputFormat.markdown:
        if summary:
            return _build_markdown_summary_report(report, base_ref=base_ref)
        return _build_markdown_report(report, base_ref=base_ref)

    return _build_text_report(report, base_ref=base_ref)


def _write_or_print_report(
    report_output: str,
    output_file: Path | None,
    output_format: OutputFormat,
) -> None:
    if output_file:
        output_file.write_text(report_output, encoding="utf-8")
        console.print(f"Report written to {output_file}")
        return

    if output_format == OutputFormat.markdown:
        console.print(report_output, markup=False)
        return

    console.print(report_output)


def _build_json_report(report: RiskReport) -> str:
    return json.dumps(report.to_dict(), indent=2)


def _build_text_report(report: RiskReport, base_ref: str | None = None) -> str:
    lines: list[str] = [
        "PR Risk Lens",
        "Transparent risk scoring for Python pull requests.",
        "",
    ]

    if base_ref:
        lines.append(f"Mode: branch comparison against {base_ref}")
    else:
        lines.append("Mode: local working tree")

    lines.append("")

    if not report.has_changes:
        lines.append("No changed files detected.")
        return "\n".join(lines)

    lines.append("Changed files:")
    for file_path in report.changed_files:
        lines.append(f"- {file_path}")

    lines.extend(
        [
            "",
            "Diff stats:",
            f"Lines added: {report.total_additions}",
            f"Lines deleted: {report.total_deletions}",
            "",
            "Tests:",
            f"Test files changed: {_yes_no(report.has_test_changes)}",
        ]
    )

    for file_path in report.test_files:
        lines.append(f"- {file_path}")

    lines.extend(
        [
            "",
            "Sensitive files:",
            f"Sensitive files changed: {_yes_no(report.has_sensitive_changes)}",
        ]
    )

    for file_path in report.sensitive_files:
        lines.append(f"- {file_path}")

    lines.extend(
        [
            "",
            "Risk:",
            f"Risk score: {report.risk_score}/100",
            f"Risk level: {report.risk_level}",
            "",
            "Risk factors:",
        ]
    )

    if report.risk_factors:
        for factor in report.risk_factors:
            lines.append(f"- {factor.label} (+{factor.points})")
    else:
        lines.append("No risk factors detected.")

    return "\n".join(lines)


def _build_markdown_report(report: RiskReport, base_ref: str | None = None) -> str:
    lines: list[str] = [
        "# PR Risk Lens Report",
        "",
        "Transparent risk scoring for Python pull requests.",
        "",
        "This report is deterministic, rule-based, and generated locally.",
        "",
        "## Verdict",
        "",
        _build_markdown_verdict(report),
        "",
        _build_markdown_review_guidance(report),
        "",
        "## Review focus",
        "",
    ]

    lines.extend(_build_markdown_review_focus_lines(report))

    lines.extend(
        [
            "",
            "## Mode",
            "",
        ]
    )

    if base_ref:
        lines.append(f"Branch comparison against `{base_ref}`.")
    else:
        lines.append("Local working tree.")

    lines.extend(
        [
            "",
            "## Summary",
            "",
        ]
    )
    lines.extend(_build_markdown_summary_table(report))

    lines.extend(_build_markdown_file_section("Changed files", report.changed_files))
    lines.extend(_build_markdown_file_section("Test files", report.test_files))
    lines.extend(
        _build_markdown_file_section("Sensitive files", report.sensitive_files)
    )

    lines.extend(
        [
            "## Risk factors",
            "",
        ]
    )
    lines.extend(_build_markdown_risk_factor_table(report))

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            (
                "This score is not a quality judgment. It is a review signal "
                "based on change size, file count, test coverage signals, "
                "and sensitive file changes."
            ),
            "",
        ]
    )

    return "\n".join(lines)


def _build_markdown_summary_report(
    report: RiskReport,
    base_ref: str | None = None,
) -> str:
    lines: list[str] = [
        "## PR Risk Lens Summary",
        "",
        _build_markdown_verdict(report),
        "",
        _build_markdown_review_guidance(report),
        "",
    ]

    if base_ref:
        lines.extend(
            [
                f"_Mode: branch comparison against `{base_ref}`._",
                "",
            ]
        )

    lines.extend(
        [
            "### Review focus",
            "",
        ]
    )
    lines.extend(_build_markdown_review_focus_lines(report))

    lines.extend(
        [
            "",
            "### Key metrics",
            "",
        ]
    )
    lines.extend(_build_markdown_compact_summary_table(report))

    lines.extend(
        [
            "### Risk factors",
            "",
        ]
    )
    lines.extend(_build_markdown_risk_factor_lines(report))
    lines.append("")

    return "\n".join(lines)


def _build_markdown_verdict(report: RiskReport) -> str:
    return f"**Risk:** {report.risk_level} - **Score:** {report.risk_score}/100"


def _has_python_source_without_test_changes(report: RiskReport) -> bool:
    return any(
        factor.label == "Python source changes without test changes"
        for factor in report.risk_factors
    )


def _build_markdown_summary_table(report: RiskReport) -> list[str]:
    return [
        "| Metric | Value |",
        "| --- | --- |",
        f"| Risk score | {report.risk_score}/100 |",
        f"| Risk level | {report.risk_level} |",
        f"| Changed files | {len(report.changed_files)} |",
        f"| Lines added | {report.total_additions} |",
        f"| Lines deleted | {report.total_deletions} |",
        f"| Lines changed | {report.total_changed_lines} |",
        f"| Test files changed | {_yes_no(report.has_test_changes)} |",
        f"| Sensitive files changed | {_yes_no(report.has_sensitive_changes)} |",
        "",
    ]


def _build_markdown_compact_summary_table(report: RiskReport) -> list[str]:
    return [
        "| Metric | Value |",
        "| --- | --- |",
        f"| Changed files | {len(report.changed_files)} |",
        f"| Lines changed | {report.total_changed_lines} |",
        f"| Test files changed | {_yes_no(report.has_test_changes)} |",
        f"| Sensitive files changed | {_yes_no(report.has_sensitive_changes)} |",
        "",
    ]


def _build_markdown_review_guidance(report: RiskReport) -> str:
    if not report.has_changes:
        return "No changed files were detected."

    has_missing_test_signal = _has_python_source_without_test_changes(report)

    if report.risk_level == "High":
        return (
            "Review carefully before merging. "
            "Consider splitting the change or adding focused tests."
        )

    if report.risk_level == "Medium":
        if report.has_sensitive_changes and has_missing_test_signal:
            return (
                "Review the changed areas, sensitive file changes, "
                "and whether focused tests should be added."
            )

        if report.has_sensitive_changes:
            return (
                "Review the changed areas and sensitive file changes carefully "
                "before merging."
            )

        if has_missing_test_signal:
            return (
                "Review the changed areas and risk factors before merging. "
                "Check whether focused tests should be added."
            )

        return "Review the changed areas and risk factors before merging."

    if report.risk_level == "Low":
        if report.has_sensitive_changes and has_missing_test_signal:
            return (
                "Risk appears low, but review sensitive file changes and check "
                "whether tests are needed."
            )

        if report.has_sensitive_changes:
            return "Risk appears low, but review sensitive file changes carefully."

        if has_missing_test_signal:
            return (
                "Risk appears low, but check whether tests are needed "
                "for the Python source change."
            )

        return "Risk appears low, but review the listed changes normally."

    return "No meaningful risk factors were detected."


def _build_markdown_review_focus_lines(report: RiskReport) -> list[str]:
    if not report.has_changes:
        return ["- No changed files detected."]

    focus_lines: list[str] = []
    has_missing_test_signal = _has_python_source_without_test_changes(report)

    if report.risk_level == "High":
        focus_lines.append("- High-risk change: review carefully before merging.")
    elif report.risk_level == "Medium":
        if has_missing_test_signal:
            focus_lines.append(
                "- Medium-risk change with missing test signal: "
                "check whether focused tests should be added."
            )
        else:
            focus_lines.append("- Medium-risk change: review the impacted areas.")
    elif report.risk_level == "Low":
        if has_missing_test_signal:
            focus_lines.append(
                "- Low-risk change with missing test signal: "
                "check whether tests are needed."
            )
        else:
            focus_lines.append("- Low-risk change: review normally.")
    else:
        focus_lines.append("- No meaningful risk factors detected.")

    focus_lines.append(f"- {_format_count(len(report.changed_files), 'changed file')}.")
    focus_lines.append(
        f"- {_format_count(report.total_changed_lines, 'changed line')}."
    )

    if report.has_test_changes:
        focus_lines.append("- Test files changed.")
    elif has_missing_test_signal:
        focus_lines.append("- No test file changes detected for Python source changes.")
    else:
        focus_lines.append("- No test file changes detected.")

    if report.has_sensitive_changes:
        focus_lines.append(
            "- Sensitive files changed: review configuration, dependency, or CI impact."
        )
    else:
        focus_lines.append("- No sensitive files changed.")

    return focus_lines


def _build_markdown_risk_factor_lines(report: RiskReport) -> list[str]:
    if not report.risk_factors:
        return ["No risk factors detected."]

    lines: list[str] = []

    for factor in report.risk_factors:
        lines.append(f"- {factor.label} `+{factor.points}`")

    return lines


def _build_markdown_risk_factor_table(report: RiskReport) -> list[str]:
    if not report.risk_factors:
        return ["No risk factors detected."]

    lines = [
        "| Factor | Points |",
        "| --- | ---: |",
    ]

    for factor in report.risk_factors:
        lines.append(f"| {factor.label} | +{factor.points} |")

    return lines


def _build_markdown_file_section(title: str, file_paths: list[str]) -> list[str]:
    lines = [
        f"## {title}",
        "",
    ]

    if not file_paths:
        lines.extend(
            [
                "None.",
                "",
            ]
        )
        return lines

    for file_path in file_paths:
        lines.append(f"- `{file_path}`")

    lines.append("")
    return lines


def _format_count(count: int, singular: str, plural: str | None = None) -> str:
    if count == 1:
        return f"1 {singular}"

    if plural is not None:
        return f"{count} {plural}"

    return f"{count} {singular}s"


def _yes_no(value: bool) -> str:
    return "Yes" if value else "No"


def _exit_if_score_is_too_high(
    report: RiskReport,
    max_score: int | None,
    output_format: OutputFormat,
) -> None:
    if max_score is None:
        return

    if report.risk_score <= max_score:
        return

    if output_format == OutputFormat.text:
        console.print()
        console.print(
            f"[red]Risk score {report.risk_score} exceeds max score {max_score}.[/red]"
        )

    raise typer.Exit(code=1)
