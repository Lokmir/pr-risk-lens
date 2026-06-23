from typer.testing import CliRunner

from pr_risk_lens.cli import app

runner = CliRunner()


def test_analyze_command_displays_project_name() -> None:
    result = runner.invoke(app, ["analyze"])

    assert result.exit_code == 0
    assert "PR Risk Lens" in result.output
    assert "MVP skeleton ready" in result.output