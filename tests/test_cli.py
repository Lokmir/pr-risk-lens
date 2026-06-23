import json

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
        return ["README.md", "src/pr_risk_lens/cli.py", "tests/test_cli.py"]

    def fake_get_diff_stats() -> list[DiffStat]:
        return [
            DiffStat(file_path="README.md", additions=5, deletions=2),
            DiffStat(file_path="src/pr_risk_lens/cli.py", additions=10, deletions=1),
            DiffStat(file_path="tests/test_cli.py", additions=5, deletions=0),
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
    assert "tests/test_cli.py" in result.output
    assert "Lines added: 20" in result.output
    assert "Lines deleted: 3" in result.output
    assert "Test files changed: Yes" in result.output
    assert "Risk score: 15/100" in result.output
    assert "Risk level: Low" in result.output
    assert "Change size: 23 changed lines (+10)" in result.output
    assert "Files changed: 3 files (+5)" in result.output


def test_analyze_command_can_output_json(monkeypatch) -> None:
    def fake_get_changed_files() -> list[str]:
        return ["README.md", "tests/test_readme.py"]

    def fake_get_diff_stats() -> list[DiffStat]:
        return [
            DiffStat(file_path="README.md", additions=5, deletions=2),
            DiffStat(file_path="tests/test_readme.py", additions=3, deletions=1),
        ]

    monkeypatch.setattr(
        "pr_risk_lens.cli.get_changed_files",
        fake_get_changed_files,
    )
    monkeypatch.setattr(
        "pr_risk_lens.cli.get_diff_stats",
        fake_get_diff_stats,
    )

    result = runner.invoke(app, ["analyze", "--json"])

    assert result.exit_code == 0

    data = json.loads(result.output)

    assert data["changed_files"] == ["README.md", "tests/test_readme.py"]
    assert data["test_changes"]["has_test_changes"] is True
    assert data["test_changes"]["test_files"] == ["tests/test_readme.py"]
    assert data["diff_stats"]["lines_added"] == 8
    assert data["diff_stats"]["lines_deleted"] == 3
    assert data["diff_stats"]["total_changed_lines"] == 11
    assert data["risk"]["score"] == 15
    assert data["risk"]["level"] == "Low"