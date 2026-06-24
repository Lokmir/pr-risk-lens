import json

from typer.testing import CliRunner

from pr_risk_lens.cli import app
from pr_risk_lens.git import DiffStat, GitCommandError

runner = CliRunner()


def test_analyze_command_displays_project_name(monkeypatch) -> None:
    def fake_get_changed_files(base_ref: str | None = None) -> list[str]:
        return []

    def fake_get_diff_stats(base_ref: str | None = None) -> list[DiffStat]:
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
    assert "Mode: local working tree" in result.output
    assert "No changed files detected." in result.output


def test_analyze_command_displays_changed_files(monkeypatch) -> None:
    def fake_get_changed_files(base_ref: str | None = None) -> list[str]:
        return ["README.md", "src/pr_risk_lens/cli.py", "tests/test_cli.py"]

    def fake_get_diff_stats(base_ref: str | None = None) -> list[DiffStat]:
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
    assert "Sensitive files changed: No" in result.output
    assert "Risk score: 15/100" in result.output
    assert "Risk level: Low" in result.output
    assert "Change size: 23 changed lines (+10)" in result.output
    assert "Files changed: 3 files (+5)" in result.output


def test_analyze_command_can_output_json(monkeypatch) -> None:
    def fake_get_changed_files(base_ref: str | None = None) -> list[str]:
        return ["README.md", "tests/test_readme.py"]

    def fake_get_diff_stats(base_ref: str | None = None) -> list[DiffStat]:
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
    assert data["sensitive_changes"]["has_sensitive_changes"] is False
    assert data["sensitive_changes"]["sensitive_files"] == []
    assert data["diff_stats"]["lines_added"] == 8
    assert data["diff_stats"]["lines_deleted"] == 3
    assert data["diff_stats"]["total_changed_lines"] == 11
    assert data["risk"]["score"] == 15
    assert data["risk"]["level"] == "Low"


def test_analyze_command_accepts_base_option(monkeypatch) -> None:
    seen_base_refs: list[str | None] = []

    def fake_get_changed_files(base_ref: str | None = None) -> list[str]:
        seen_base_refs.append(base_ref)
        return ["src/pr_risk_lens/cli.py"]

    def fake_get_diff_stats(base_ref: str | None = None) -> list[DiffStat]:
        seen_base_refs.append(base_ref)
        return [
            DiffStat(file_path="src/pr_risk_lens/cli.py", additions=10, deletions=2),
        ]

    monkeypatch.setattr(
        "pr_risk_lens.cli.get_changed_files",
        fake_get_changed_files,
    )
    monkeypatch.setattr(
        "pr_risk_lens.cli.get_diff_stats",
        fake_get_diff_stats,
    )

    result = runner.invoke(app, ["analyze", "--base", "main"])

    assert result.exit_code == 0
    assert "Mode: branch comparison against main" in result.output
    assert seen_base_refs == ["main", "main"]


def test_analyze_command_displays_sensitive_files(monkeypatch) -> None:
    def fake_get_changed_files(base_ref: str | None = None) -> list[str]:
        return ["pyproject.toml", "src/pr_risk_lens/cli.py", "tests/test_cli.py"]

    def fake_get_diff_stats(base_ref: str | None = None) -> list[DiffStat]:
        return [
            DiffStat(file_path="pyproject.toml", additions=2, deletions=1),
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
    assert "Sensitive files changed: Yes" in result.output
    assert "pyproject.toml" in result.output
    assert "Risk-sensitive files changed (+10)" in result.output


def test_analyze_command_succeeds_when_score_is_under_max_score(monkeypatch) -> None:
    def fake_get_changed_files(base_ref: str | None = None) -> list[str]:
        return ["README.md"]

    def fake_get_diff_stats(base_ref: str | None = None) -> list[DiffStat]:
        return [
            DiffStat(file_path="README.md", additions=5, deletions=2),
        ]

    monkeypatch.setattr(
        "pr_risk_lens.cli.get_changed_files",
        fake_get_changed_files,
    )
    monkeypatch.setattr(
        "pr_risk_lens.cli.get_diff_stats",
        fake_get_diff_stats,
    )

    result = runner.invoke(app, ["analyze", "--max-score", "20"])

    assert result.exit_code == 0
    assert "Risk score: 15/100" in result.output


def test_analyze_command_fails_when_score_exceeds_max_score(monkeypatch) -> None:
    def fake_get_changed_files(base_ref: str | None = None) -> list[str]:
        return ["README.md"]

    def fake_get_diff_stats(base_ref: str | None = None) -> list[DiffStat]:
        return [
            DiffStat(file_path="README.md", additions=5, deletions=2),
        ]

    monkeypatch.setattr(
        "pr_risk_lens.cli.get_changed_files",
        fake_get_changed_files,
    )
    monkeypatch.setattr(
        "pr_risk_lens.cli.get_diff_stats",
        fake_get_diff_stats,
    )

    result = runner.invoke(app, ["analyze", "--max-score", "10"])

    assert result.exit_code == 1
    assert "Risk score: 15/100" in result.output
    assert "Risk score 15 exceeds max score 10." in result.output


def test_analyze_command_displays_clean_git_error(monkeypatch) -> None:
    def fake_get_changed_files(base_ref: str | None = None) -> list[str]:
        raise GitCommandError("Not inside a Git repository.")

    monkeypatch.setattr(
        "pr_risk_lens.cli.get_changed_files",
        fake_get_changed_files,
    )

    result = runner.invoke(app, ["analyze"])

    assert result.exit_code == 2
    assert "Error:" in result.output
    assert "Not inside a Git repository." in result.output


def test_version_option_displays_installed_version(monkeypatch) -> None:
    def fake_get_package_version(package_name: str) -> str:
        assert package_name == "pr-risk-lens"
        return "0.1.0"

    monkeypatch.setattr(
        "pr_risk_lens.cli.get_package_version",
        fake_get_package_version,
    )

    result = runner.invoke(app, ["--version"])

    assert result.exit_code == 0
    assert "PR Risk Lens 0.1.0" in result.output


def test_analyze_command_can_output_markdown(monkeypatch) -> None:
    def fake_get_changed_files(base_ref: str | None = None) -> list[str]:
        return [
            "README.md",
            "src/pr_risk_lens/cli.py",
            "tests/test_cli.py",
        ]

    def fake_get_diff_stats(base_ref: str | None = None) -> list[DiffStat]:
        return [
            DiffStat(file_path="README.md", additions=5, deletions=1),
            DiffStat(file_path="src/pr_risk_lens/cli.py", additions=10, deletions=2),
            DiffStat(file_path="tests/test_cli.py", additions=8, deletions=0),
        ]

    monkeypatch.setattr(
        "pr_risk_lens.cli.get_changed_files",
        fake_get_changed_files,
    )
    monkeypatch.setattr(
        "pr_risk_lens.cli.get_diff_stats",
        fake_get_diff_stats,
    )

    result = runner.invoke(app, ["analyze", "--format", "markdown"])

    assert result.exit_code == 0
    assert "# PR Risk Lens Report" in result.output
    assert "## Summary" in result.output
    assert "| Risk score |" in result.output
    assert "## Review guidance" in result.output
    assert "- `README.md`" in result.output
    assert "- `tests/test_cli.py`" in result.output
    assert "## Risk factors" in result.output


def test_analyze_command_can_output_json_with_format_option(monkeypatch) -> None:
    def fake_get_changed_files(base_ref: str | None = None) -> list[str]:
        return ["README.md"]

    def fake_get_diff_stats(base_ref: str | None = None) -> list[DiffStat]:
        return [DiffStat(file_path="README.md", additions=5, deletions=1)]

    monkeypatch.setattr(
        "pr_risk_lens.cli.get_changed_files",
        fake_get_changed_files,
    )
    monkeypatch.setattr(
        "pr_risk_lens.cli.get_diff_stats",
        fake_get_diff_stats,
    )

    result = runner.invoke(app, ["analyze", "--format", "json"])

    assert result.exit_code == 0
    assert '"changed_files"' in result.output
    assert '"risk"' in result.output


def test_analyze_command_rejects_json_flag_with_format_option(monkeypatch) -> None:
    result = runner.invoke(app, ["analyze", "--json", "--format", "markdown"])

    assert result.exit_code == 2
    assert "Use either --json or --format, not both." in result.output


def test_analyze_command_can_write_markdown_output_to_file(
    monkeypatch, tmp_path
) -> None:
    output_file = tmp_path / "risk-report.md"

    def fake_get_changed_files(base_ref: str | None = None) -> list[str]:
        return [
            "README.md",
            "tests/test_cli.py",
        ]

    def fake_get_diff_stats(base_ref: str | None = None) -> list[DiffStat]:
        return [
            DiffStat(file_path="README.md", additions=5, deletions=1),
            DiffStat(file_path="tests/test_cli.py", additions=8, deletions=0),
        ]

    monkeypatch.setattr(
        "pr_risk_lens.cli.get_changed_files",
        fake_get_changed_files,
    )
    monkeypatch.setattr(
        "pr_risk_lens.cli.get_diff_stats",
        fake_get_diff_stats,
    )

    result = runner.invoke(
        app,
        [
            "analyze",
            "--format",
            "markdown",
            "--output",
            str(output_file),
        ],
    )

    assert result.exit_code == 0
    assert "Report written to" in result.output

    content = output_file.read_text(encoding="utf-8")

    assert "# PR Risk Lens Report" in content
    assert "- `README.md`" in content
    assert "- `tests/test_cli.py`" in content


def test_analyze_command_can_write_json_output_to_file(monkeypatch, tmp_path) -> None:
    output_file = tmp_path / "risk-report.json"

    def fake_get_changed_files(base_ref: str | None = None) -> list[str]:
        return ["README.md"]

    def fake_get_diff_stats(base_ref: str | None = None) -> list[DiffStat]:
        return [DiffStat(file_path="README.md", additions=5, deletions=1)]

    monkeypatch.setattr(
        "pr_risk_lens.cli.get_changed_files",
        fake_get_changed_files,
    )
    monkeypatch.setattr(
        "pr_risk_lens.cli.get_diff_stats",
        fake_get_diff_stats,
    )

    result = runner.invoke(
        app,
        [
            "analyze",
            "--format",
            "json",
            "--output",
            str(output_file),
        ],
    )

    assert result.exit_code == 0
    assert "Report written to" in result.output

    content = output_file.read_text(encoding="utf-8")

    assert '"changed_files"' in content
    assert '"risk"' in content

def test_analyze_command_can_output_markdown_summary(monkeypatch) -> None:
    def fake_get_changed_files(base_ref: str | None = None) -> list[str]:
        return [
            "README.md",
            "src/pr_risk_lens/cli.py",
            "tests/test_cli.py",
        ]

    def fake_get_diff_stats(base_ref: str | None = None) -> list[DiffStat]:
        return [
            DiffStat(file_path="README.md", additions=5, deletions=1),
            DiffStat(file_path="src/pr_risk_lens/cli.py", additions=10, deletions=2),
            DiffStat(file_path="tests/test_cli.py", additions=8, deletions=0),
        ]

    monkeypatch.setattr(
        "pr_risk_lens.cli.get_changed_files",
        fake_get_changed_files,
    )
    monkeypatch.setattr(
        "pr_risk_lens.cli.get_diff_stats",
        fake_get_diff_stats,
    )

    result = runner.invoke(app, ["analyze", "--format", "markdown", "--summary"])

    assert result.exit_code == 0
    assert "# PR Risk Lens Summary" in result.output
    assert "## Summary" in result.output
    assert "| Risk score |" in result.output
    assert "## Review guidance" in result.output
    assert "## Risk factors" in result.output
    assert "## Changed files" not in result.output


def test_analyze_command_rejects_summary_without_markdown() -> None:
    result = runner.invoke(app, ["analyze", "--summary"])

    assert result.exit_code == 2
    assert "Use --summary with --format markdown." in result.output


def test_analyze_command_can_write_markdown_summary_to_file(
    monkeypatch,
    tmp_path,
) -> None:
    output_file = tmp_path / "risk-summary.md"

    def fake_get_changed_files(base_ref: str | None = None) -> list[str]:
        return [
            "README.md",
            "tests/test_cli.py",
        ]

    def fake_get_diff_stats(base_ref: str | None = None) -> list[DiffStat]:
        return [
            DiffStat(file_path="README.md", additions=5, deletions=1),
            DiffStat(file_path="tests/test_cli.py", additions=8, deletions=0),
        ]

    monkeypatch.setattr(
        "pr_risk_lens.cli.get_changed_files",
        fake_get_changed_files,
    )
    monkeypatch.setattr(
        "pr_risk_lens.cli.get_diff_stats",
        fake_get_diff_stats,
    )

    result = runner.invoke(
        app,
        [
            "analyze",
            "--format",
            "markdown",
            "--summary",
            "--output",
            str(output_file),
        ],
    )

    assert result.exit_code == 0
    assert "Report written to" in result.output

    content = output_file.read_text(encoding="utf-8")

    assert "# PR Risk Lens Summary" in content
    assert "| Risk score |" in content
    assert "## Changed files" not in content