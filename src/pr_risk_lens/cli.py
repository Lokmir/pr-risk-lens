import typer
from rich.console import Console

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
def analyze() -> None:
    """
    Analyze Git changes and print a first risk report.
    """
    console.print("[bold]PR Risk Lens[/bold]")
    console.print("Transparent risk scoring for Python pull requests.")
    console.print("Status: MVP skeleton ready.")