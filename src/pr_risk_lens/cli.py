import json
from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as get_package_version

import typer
from rich.console import Console

from pr_risk_lens.git import GitCommandError, get_changed_files, get_diff_stats
from pr_risk_lens.report import RiskReport, build_risk_report

PACKAGE_NAME = "pr-risk-lens"
APP_NAME = "PR Risk Lens"

app = typer.Typer(
    help="Transparent risk scoring for Python pull requests.",
    no_args_is_help=True,
    invoke_without_command=True,
)

console = Console()


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
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Output the report as JSON.",
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
    try:
        changed_files = get_changed_files(base_ref=base)
        diff_stats = get_diff_stats(base_ref=base)
    except GitCommandError as error:
        console.print(f"[red]Error:[/red] {error}")
        raise typer.Exit(code=2) from error

    report = build_risk_report(changed_files, diff_stats)

    if json_output:
        _print_json_report(report)
    else:
        _print_text_report(report, base_ref=base)

    _exit_if_score_is_too_high(
        report=report,
        max_score=max_score,
        json_output=json_output,
    )


def _get_installed_version() -> str:
    try:
        return get_package_version(PACKAGE_NAME)
    except PackageNotFoundError:
        return "unknown"


def _print_json_report(report: RiskReport) -> None:
    console.print(json.dumps(report.to_dict(), indent=2))


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
    json_output: bool,
) -> None:
    if max_score is None:
        return

    if report.risk_score <= max_score:
        return

    if not json_output:
        console.print()
        console.print(
            f"[red]Risk score {report.risk_score} exceeds max score {max_score}.[/red]"
        )

    raise typer.Exit(code=1)
