from typer.testing import CliRunner

from pr_risk_lens.cli import app
from pr_risk_lens.git import DiffStat

runner = CliRunner()


def test_analyze_command_displays_project_name(monkeypatch) -> None:
    def fake_get_changed_files() -> list[str]:
        return []

    def fake_get_diff_stats() -> list[DiffStat]:
        return []

    monkeypatch.setattr(
        "pr_risk_lens.cli.get_changed_files",
        fake_get_changed_files,
    )
    monkeypatch.setattr(
        "pr_risk_lens.cli.get_diff_stats",
        fake_get_diff_stats,
    )

    result = runner.invoke(app, ["analyze"])

    assert result.exit_code == 0
    assert "PR Risk Lens" in result.output
    assert "No changed files detected." in result.output


def test_analyze_command_displays_changed_files(monkeypatch) -> None:
    def fake_get_changed_files() -> list[str]:
        return ["README.md", "src/pr_risk_lens/cli.py"]

    def fake_get_diff_stats() -> list[DiffStat]:
        return [
            DiffStat(file_path="README.md", additions=5, deletions=2),
            DiffStat(file_path="src/pr_risk_lens/cli.py", additions=10, deletions=1),
        ]

    monkeypatch.setattr(
        "pr_risk_lens.cli.get_changed_files",
        fake_get_changed_files,
    )
    monkeypatch.setattr(
        "pr_risk_lens.cli.get_diff_stats",
        fake_get_diff_stats,
    )

    result = runner.invoke(app, ["analyze"])

    assert result.exit_code == 0
    assert "Changed files:" in result.output
    assert "README.md" in result.output
    assert "src/pr_risk_lens/cli.py" in result.output
    assert "Lines added: 15" in result.output
    assert "Lines deleted: 3" in result.output
    assert "Risk score: 15/100" in result.output
    assert "Risk level: Low" in result.output
    assert "Change size: 18 changed lines (+10)" in result.output
    assert "Files changed: 2 files (+5)" in result.output