import json
from enum import StrEnum
from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as get_package_version

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

    try:
        changed_files = get_changed_files(base_ref=base)
        diff_stats = get_diff_stats(base_ref=base)
    except GitCommandError as error:
        console.print(f"[red]Error:[/red] {error}")
        raise typer.Exit(code=2) from error

    report = build_risk_report(changed_files, diff_stats)

    _print_report(
        report=report,
        base_ref=base,
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


def _get_installed_version() -> str:
    try:
        return get_package_version(PACKAGE_NAME)
    except PackageNotFoundError:
        return "unknown"


def _print_report(
    report: RiskReport,
    base_ref: str | None,
    output_format: OutputFormat,
) -> None:
    if output_format == OutputFormat.json:
        _print_json_report(report)
        return

    if output_format == OutputFormat.markdown:
        _print_markdown_report(report, base_ref=base_ref)
        return

    _print_text_report(report, base_ref=base_ref)


def _print_json_report(report: RiskReport) -> None:
    console.print(json.dumps(report.to_dict(), indent=2))


def _print_markdown_report(report: RiskReport, base_ref: str | None = None) -> None:
    console.print(_build_markdown_report(report, base_ref=base_ref), markup=False)


def _build_markdown_report(report: RiskReport, base_ref: str | None = None) -> str:
    lines: list[str] = [
        "# PR Risk Lens Report",
        "",
        "Transparent risk scoring for Python pull requests.",
        "",
        "## Mode",
        "",
    ]

    if base_ref:
        lines.append(f"Branch comparison against `{base_ref}`.")
    else:
        lines.append("Local working tree.")

    lines.extend(
        [
            "",
            "## Summary",
            "",
            f"- **Risk score:** {report.risk_score}/100",
            f"- **Risk level:** {report.risk_level}",
            f"- **Changed files:** {len(report.changed_files)}",
            f"- **Lines added:** {report.total_additions}",
            f"- **Lines deleted:** {report.total_deletions}",
            f"- **Test files changed:** {_yes_no(report.has_test_changes)}",
            f"- **Sensitive files changed:** {_yes_no(report.has_sensitive_changes)}",
            "",
        ]
    )

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

    if report.risk_factors:
        for factor in report.risk_factors:
            lines.append(f"- {factor.label} `+{factor.points}`")
    else:
        lines.append("No risk factors detected.")

    lines.append("")

    return "\n".join(lines)


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


def _yes_no(value: bool) -> str:
    return "Yes" if value else "No"


def _print_text_report(report: RiskReport, base_ref: str | None = None) -> None:
    console.print("[bold]PR Risk Lens[/bold]")
    console.print("Transparent risk scoring for Python pull requests.")
    console.print()

    if base_ref:
        console.print(f"Mode: branch comparison against {base_ref}")
    else:
        console.print("Mode: local working tree")

    console.print()

    if not report.has_changes:
        console.print("No changed files detected.")
        return

    console.print("[bold]Changed files:[/bold]")

    for file_path in report.changed_files:
        console.print(f"- {file_path}")

    console.print()
    console.print("[bold]Diff stats:[/bold]")
    console.print(f"Lines added: {report.total_additions}")
    console.print(f"Lines deleted: {report.total_deletions}")

    console.print()
    console.print("[bold]Tests:[/bold]")
    console.print(f"Test files changed: {'Yes' if report.has_test_changes else 'No'}")

    for file_path in report.test_files:
        console.print(f"- {file_path}")

    console.print()
    console.print("[bold]Sensitive files:[/bold]")
    console.print(
        f"Sensitive files changed: {'Yes' if report.has_sensitive_changes else 'No'}"
    )

    for file_path in report.sensitive_files:
        console.print(f"- {file_path}")

    console.print()
    console.print("[bold]Risk:[/bold]")
    console.print(f"Risk score: {report.risk_score}/100")
    console.print(f"Risk level: {report.risk_level}")

    console.print()
    console.print("[bold]Risk factors:[/bold]")

    for factor in report.risk_factors:
        console.print(f"- {factor.label} (+{factor.points})")


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
