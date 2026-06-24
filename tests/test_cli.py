import json

from typer.testing import CliRunner

from pr_risk_lens.cli import app
from pr_risk_lens.git import DiffStat, GitCommandError

runner = CliRunner()


def _mock_git_changes(
    monkeypatch,
    changed_files: list[str],
    diff_stats: list[DiffStat],
) -> None:
    def fake_get_changed_files(base_ref: str | None = None) -> list[str]:
        return changed_files

    def fake_get_diff_stats(base_ref: str | None = None) -> list[DiffStat]:
        return diff_stats

    monkeypatch.setattr(
        "pr_risk_lens.cli.get_changed_files",
        fake_get_changed_files,
    )
    monkeypatch.setattr(
        "pr_risk_lens.cli.get_diff_stats",
        fake_get_diff_stats,
    )


def test_analyze_command_displays_project_name(monkeypatch) -> None:
    _mock_git_changes(
        monkeypatch=monkeypatch,
        changed_files=[],
        diff_stats=[],
    )

    result = runner.invoke(app, ["analyze"])

    assert result.exit_code == 0
    assert "PR Risk Lens" in result.output
    assert "Mode: local working tree" in result.output
    assert "No changed files detected." in result.output


def test_analyze_command_displays_changed_files(monkeypatch) -> None:
    _mock_git_changes(
        monkeypatch=monkeypatch,
        changed_files=[
            "README.md",
            "src/pr_risk_lens/cli.py",
            "tests/test_cli.py",
        ],
        diff_stats=[
            DiffStat(file_path="README.md", additions=5, deletions=2),
            DiffStat(file_path="src/pr_risk_lens/cli.py", additions=10, deletions=1),
            DiffStat(file_path="tests/test_cli.py", additions=5, deletions=0),
        ],
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
    _mock_git_changes(
        monkeypatch=monkeypatch,
        changed_files=[
            "README.md",
            "tests/test_readme.py",
        ],
        diff_stats=[
            DiffStat(file_path="README.md", additions=5, deletions=2),
            DiffStat(file_path="tests/test_readme.py", additions=3, deletions=1),
        ],
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
    _mock_git_changes(
        monkeypatch=monkeypatch,
        changed_files=[
            "pyproject.toml",
            "src/pr_risk_lens/cli.py",
            "tests/test_cli.py",
        ],
        diff_stats=[
            DiffStat(file_path="pyproject.toml", additions=2, deletions=1),
            DiffStat(file_path="src/pr_risk_lens/cli.py", additions=10, deletions=1),
            DiffStat(file_path="tests/test_cli.py", additions=5, deletions=0),
        ],
    )

    result = runner.invoke(app, ["analyze"])

    assert result.exit_code == 0
    assert "Sensitive files changed: Yes" in result.output
    assert "pyproject.toml" in result.output
    assert "Risk-sensitive files changed (+10)" in result.output


def test_analyze_command_succeeds_when_score_is_under_max_score(monkeypatch) -> None:
    _mock_git_changes(
        monkeypatch=monkeypatch,
        changed_files=["README.md"],
        diff_stats=[
            DiffStat(file_path="README.md", additions=5, deletions=2),
        ],
    )

    result = runner.invoke(app, ["analyze", "--max-score", "20"])

    assert result.exit_code == 0
    assert "Risk score: 15/100" in result.output


def test_analyze_command_fails_when_score_exceeds_max_score(monkeypatch) -> None:
    _mock_git_changes(
        monkeypatch=monkeypatch,
        changed_files=["README.md"],
        diff_stats=[
            DiffStat(file_path="README.md", additions=5, deletions=2),
        ],
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
    _mock_git_changes(
        monkeypatch=monkeypatch,
        changed_files=[
            "README.md",
            "src/pr_risk_lens/cli.py",
            "tests/test_cli.py",
        ],
        diff_stats=[
            DiffStat(file_path="README.md", additions=5, deletions=1),
            DiffStat(file_path="src/pr_risk_lens/cli.py", additions=10, deletions=2),
            DiffStat(file_path="tests/test_cli.py", additions=8, deletions=0),
        ],
    )

    result = runner.invoke(app, ["analyze", "--format", "markdown"])

    assert result.exit_code == 0
    assert "# PR Risk Lens Report" in result.output
    assert "## Verdict" in result.output
    assert "**Risk:** Low" in result.output
    assert "**Score:** 15/100" in result.output
    assert "## Review focus" in result.output
    assert "## Summary" in result.output
    assert "| Lines changed | 26 |" in result.output
    assert "## Changed files" in result.output
    assert "- `README.md`" in result.output
    assert "- `tests/test_cli.py`" in result.output
    assert "## Risk factors" in result.output
    assert "| Factor | Points |" in result.output
    assert "| Change size: 26 changed lines | +10 |" in result.output


def test_analyze_command_can_output_json_with_format_option(monkeypatch) -> None:
    _mock_git_changes(
        monkeypatch=monkeypatch,
        changed_files=["README.md"],
        diff_stats=[
            DiffStat(file_path="README.md", additions=5, deletions=1),
        ],
    )

    result = runner.invoke(app, ["analyze", "--format", "json"])

    assert result.exit_code == 0
    assert '"changed_files"' in result.output
    assert '"risk"' in result.output


def test_analyze_command_rejects_json_flag_with_format_option() -> None:
    result = runner.invoke(app, ["analyze", "--json", "--format", "markdown"])

    assert result.exit_code == 2
    assert "Use either --json or --format, not both." in result.output


def test_analyze_command_can_write_markdown_output_to_file(
    monkeypatch,
    tmp_path,
) -> None:
    output_file = tmp_path / "risk-report.md"

    _mock_git_changes(
        monkeypatch=monkeypatch,
        changed_files=[
            "README.md",
            "tests/test_cli.py",
        ],
        diff_stats=[
            DiffStat(file_path="README.md", additions=5, deletions=1),
            DiffStat(file_path="tests/test_cli.py", additions=8, deletions=0),
        ],
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
    assert "## Verdict" in content
    assert "## Review focus" in content
    assert "## Changed files" in content
    assert "- `README.md`" in content
    assert "- `tests/test_cli.py`" in content


def test_analyze_command_can_write_json_output_to_file(monkeypatch, tmp_path) -> None:
    output_file = tmp_path / "risk-report.json"

    _mock_git_changes(
        monkeypatch=monkeypatch,
        changed_files=["README.md"],
        diff_stats=[
            DiffStat(file_path="README.md", additions=5, deletions=1),
        ],
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
    _mock_git_changes(
        monkeypatch=monkeypatch,
        changed_files=[
            "README.md",
            "src/pr_risk_lens/cli.py",
            "tests/test_cli.py",
        ],
        diff_stats=[
            DiffStat(file_path="README.md", additions=5, deletions=1),
            DiffStat(file_path="src/pr_risk_lens/cli.py", additions=10, deletions=2),
            DiffStat(file_path="tests/test_cli.py", additions=8, deletions=0),
        ],
    )

    result = runner.invoke(app, ["analyze", "--format", "markdown", "--summary"])

    assert result.exit_code == 0
    assert "## PR Risk Lens Summary" in result.output
    assert "# PR Risk Lens Report" not in result.output
    assert "**Risk:** Low" in result.output
    assert "**Score:** 15/100" in result.output
    assert "### Review focus" in result.output
    assert "### Key metrics" in result.output
    assert "| Lines changed | 26 |" in result.output
    assert "### Risk factors" in result.output
    assert "## Changed files" not in result.output
    assert "Transparent risk scoring" not in result.output


def test_analyze_command_rejects_summary_without_markdown() -> None:
    result = runner.invoke(app, ["analyze", "--summary"])

    assert result.exit_code == 2
    assert "Use --summary with --format markdown." in result.output


def test_analyze_command_can_write_markdown_summary_to_file(
    monkeypatch,
    tmp_path,
) -> None:
    output_file = tmp_path / "risk-summary.md"

    _mock_git_changes(
        monkeypatch=monkeypatch,
        changed_files=[
            "README.md",
            "tests/test_cli.py",
        ],
        diff_stats=[
            DiffStat(file_path="README.md", additions=5, deletions=1),
            DiffStat(file_path="tests/test_cli.py", additions=8, deletions=0),
        ],
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

    assert "## PR Risk Lens Summary" in content
    assert "# PR Risk Lens Report" not in content
    assert "**Risk:** Low" in content
    assert "### Review focus" in content
    assert "### Key metrics" in content
    assert "## Changed files" not in content


def test_markdown_summary_highlights_python_changes_without_tests(monkeypatch) -> None:
    _mock_git_changes(
        monkeypatch=monkeypatch,
        changed_files=["src/app.py"],
        diff_stats=[
            DiffStat(file_path="src/app.py", additions=1, deletions=0),
        ],
    )

    result = runner.invoke(app, ["analyze", "--format", "markdown", "--summary"])
    normalized_output = " ".join(result.output.split())

    assert result.exit_code == 0
    assert "## PR Risk Lens Summary" in result.output
    assert "**Risk:** Low" in result.output
    assert "**Score:** 25/100" in result.output
    assert (
        "Risk appears low, but check whether tests are needed "
        "for the Python source change."
    ) in normalized_output
    assert (
        "- Low-risk change with missing test signal: check whether tests are needed."
    ) in normalized_output
    assert (
        "- No test file changes detected for Python source changes."
    ) in result.output
    assert "Python source changes without test changes `+10`" in result.output


def test_markdown_summary_highlights_sensitive_file_changes(monkeypatch) -> None:
    _mock_git_changes(
        monkeypatch=monkeypatch,
        changed_files=["pyproject.toml"],
        diff_stats=[
            DiffStat(file_path="pyproject.toml", additions=3, deletions=0),
        ],
    )

    result = runner.invoke(app, ["analyze", "--format", "markdown", "--summary"])

    assert result.exit_code == 0
    assert "## PR Risk Lens Summary" in result.output
    assert "**Risk:** Low" in result.output
    assert "**Score:** 25/100" in result.output
    assert "Risk appears low, but review sensitive file changes carefully." in (
        result.output
    )
    assert (
        "- Sensitive files changed: review configuration, dependency, or CI impact."
    ) in result.output
    assert "| Sensitive files changed | Yes |" in result.output
    assert "Risk-sensitive files changed `+10`" in result.output
