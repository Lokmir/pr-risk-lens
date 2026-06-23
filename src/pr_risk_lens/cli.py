import json

import typer
from rich.console import Console

from pr_risk_lens.git import get_changed_files, get_diff_stats
from pr_risk_lens.report import RiskReport, build_risk_report

app = typer.Typer(
    help="Transparent risk scoring for Python pull requests.",
    no_args_is_help=True,
)

console = Console()


@app.callback()
def main() -> None:
    """
    PR Risk Lens command line interface.
    """
    pass


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
) -> None:
    """
    Analyze Git changes and print a risk report.
    """
    changed_files = get_changed_files(base_ref=base)
    diff_stats = get_diff_stats(base_ref=base)
    report = build_risk_report(changed_files, diff_stats)

    if json_output:
        _print_json_report(report)
        return

    _print_text_report(report, base_ref=base)


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
    console.print(
        f"Test files changed: {'Yes' if report.has_test_changes else 'No'}"
    )

    for file_path in report.test_files:
        console.print(f"- {file_path}")

    console.print()
    console.print("[bold]Risk:[/bold]")
    console.print(f"Risk score: {report.risk_score}/100")
    console.print(f"Risk level: {report.risk_level}")

    console.print()
    console.print("[bold]Risk factors:[/bold]")

    for factor in report.risk_factors:
        console.print(f"- {factor.label} (+{factor.points})")