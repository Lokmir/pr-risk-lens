import subprocess

import pytest

from pr_risk_lens.git import (
    DiffStat,
    GitCommandError,
    get_changed_files,
    get_diff_stats,
)


def test_get_changed_files_returns_git_status_output(monkeypatch) -> None:
    def fake_run(*args, **kwargs):
        return subprocess.CompletedProcess(
            args=["git", "status", "--porcelain"],
            returncode=0,
            stdout=(
                " M README.md\n"
                "?? src/pr_risk_lens/new_file.py\n"
                "A  tests/new_test.py\n"
            ),
            stderr="",
        )

    monkeypatch.setattr(subprocess, "run", fake_run)

    changed_files = get_changed_files()

    assert changed_files == [
        "README.md",
        "src/pr_risk_lens/new_file.py",
        "tests/new_test.py",
    ]


def test_get_changed_files_returns_empty_list_when_no_changes(monkeypatch) -> None:
    def fake_run(*args, **kwargs):
        return subprocess.CompletedProcess(
            args=["git", "status", "--porcelain"],
            returncode=0,
            stdout="",
            stderr="",
        )

    monkeypatch.setattr(subprocess, "run", fake_run)

    changed_files = get_changed_files()

    assert changed_files == []


def test_get_diff_stats_returns_git_numstat_output(monkeypatch) -> None:
    def fake_run(*args, **kwargs):
        command = args[0]

        if command == ["git", "diff", "--numstat", "--find-renames", "HEAD"]:
            return subprocess.CompletedProcess(
                args=command,
                returncode=0,
                stdout=(
                    "5\t2\tREADME.md\n"
                    "12\t0\tsrc/pr_risk_lens/git.py\n"
                ),
                stderr="",
            )

        if command == ["git", "ls-files", "--others", "--exclude-standard"]:
            return subprocess.CompletedProcess(
                args=command,
                returncode=0,
                stdout="",
                stderr="",
            )

        raise AssertionError(f"Unexpected command: {command}")

    monkeypatch.setattr(subprocess, "run", fake_run)

    diff_stats = get_diff_stats()

    assert diff_stats == [
        DiffStat(file_path="README.md", additions=5, deletions=2),
        DiffStat(file_path="src/pr_risk_lens/git.py", additions=12, deletions=0),
    ]


def test_get_diff_stats_handles_binary_files(monkeypatch) -> None:
    def fake_run(*args, **kwargs):
        command = args[0]

        if command == ["git", "diff", "--numstat", "--find-renames", "HEAD"]:
            return subprocess.CompletedProcess(
                args=command,
                returncode=0,
                stdout="-\t-\timage.png\n",
                stderr="",
            )

        if command == ["git", "ls-files", "--others", "--exclude-standard"]:
            return subprocess.CompletedProcess(
                args=command,
                returncode=0,
                stdout="",
                stderr="",
            )

        raise AssertionError(f"Unexpected command: {command}")

    monkeypatch.setattr(subprocess, "run", fake_run)

    diff_stats = get_diff_stats()

    assert diff_stats == [
        DiffStat(file_path="image.png", additions=0, deletions=0),
    ]


def test_get_changed_files_can_compare_against_base(monkeypatch) -> None:
    def fake_run(*args, **kwargs):
        assert args[0] == [
            "git",
            "diff",
            "--name-only",
            "--find-renames",
            "main...HEAD",
        ]

        return subprocess.CompletedProcess(
            args=["git", "diff", "--name-only", "--find-renames", "main...HEAD"],
            returncode=0,
            stdout="README.md\nsrc/pr_risk_lens/cli.py\n",
            stderr="",
        )

    monkeypatch.setattr(subprocess, "run", fake_run)

    changed_files = get_changed_files(base_ref="main")

    assert changed_files == [
        "README.md",
        "src/pr_risk_lens/cli.py",
    ]


def test_get_diff_stats_can_compare_against_base(monkeypatch) -> None:
    def fake_run(*args, **kwargs):
        assert args[0] == [
            "git",
            "diff",
            "--numstat",
            "--find-renames",
            "main...HEAD",
        ]

        return subprocess.CompletedProcess(
            args=["git", "diff", "--numstat", "--find-renames", "main...HEAD"],
            returncode=0,
            stdout="5\t2\tREADME.md\n",
            stderr="",
        )

    monkeypatch.setattr(subprocess, "run", fake_run)

    diff_stats = get_diff_stats(base_ref="main")

    assert diff_stats == [
        DiffStat(file_path="README.md", additions=5, deletions=2),
    ]


def test_get_changed_files_raises_clear_error_when_git_is_missing(monkeypatch) -> None:
    def fake_run(*args, **kwargs):
        raise FileNotFoundError()

    monkeypatch.setattr(subprocess, "run", fake_run)

    with pytest.raises(GitCommandError) as error:
        get_changed_files()

    assert str(error.value) == "Git is not installed or not available in PATH."


def test_get_changed_files_raises_clear_error_outside_git_repository(monkeypatch) -> None:
    def fake_run(*args, **kwargs):
        raise subprocess.CalledProcessError(
            returncode=128,
            cmd=["git", "status", "--porcelain"],
            stderr="fatal: not a git repository (or any of the parent directories): .git",
        )

    monkeypatch.setattr(subprocess, "run", fake_run)

    with pytest.raises(GitCommandError) as error:
        get_changed_files()

    assert str(error.value) == "Not inside a Git repository."


def test_get_changed_files_raises_clear_error_for_unknown_base_ref(monkeypatch) -> None:
    def fake_run(*args, **kwargs):
        raise subprocess.CalledProcessError(
            returncode=128,
            cmd=["git", "diff", "--name-only", "unknown...HEAD"],
            stderr=(
                "fatal: ambiguous argument 'unknown...HEAD': "
                "unknown revision or path not in the working tree."
            ),
        )

    monkeypatch.setattr(subprocess, "run", fake_run)

    with pytest.raises(GitCommandError) as error:
        get_changed_files(base_ref="unknown")

    assert str(error.value) == (
        "Git reference not found. Check the branch or base ref name."
    )


def test_get_diff_stats_counts_untracked_file_lines(monkeypatch, tmp_path) -> None:
    untracked_file = tmp_path / "new_module.py"
    untracked_file.write_text(
        "def hello():\n"
        "    return 'hello'\n"
        "\n",
        encoding="utf-8",
    )

    monkeypatch.chdir(tmp_path)

    def fake_run(*args, **kwargs):
        command = args[0]

        if command == ["git", "diff", "--numstat", "--find-renames", "HEAD"]:
            return subprocess.CompletedProcess(
                args=command,
                returncode=0,
                stdout="5\t2\tREADME.md\n",
                stderr="",
            )

        if command == ["git", "ls-files", "--others", "--exclude-standard"]:
            return subprocess.CompletedProcess(
                args=command,
                returncode=0,
                stdout="new_module.py\n",
                stderr="",
            )

        raise AssertionError(f"Unexpected command: {command}")

    monkeypatch.setattr(subprocess, "run", fake_run)

    diff_stats = get_diff_stats()

    assert diff_stats == [
        DiffStat(file_path="README.md", additions=5, deletions=2),
        DiffStat(file_path="new_module.py", additions=3, deletions=0),
    ]


def test_get_changed_files_returns_sorted_unique_paths(monkeypatch) -> None:
    def fake_run(*args, **kwargs):
        return subprocess.CompletedProcess(
            args=["git", "status", "--porcelain"],
            returncode=0,
            stdout=(
                " M z_file.py\n"
                " M a_file.py\n"
                " M z_file.py\n"
            ),
            stderr="",
        )

    monkeypatch.setattr(subprocess, "run", fake_run)

    changed_files = get_changed_files()

    assert changed_files == [
        "a_file.py",
        "z_file.py",
    ]


def test_get_diff_stats_merges_duplicates_and_sorts_by_file_path(monkeypatch) -> None:
    def fake_run(*args, **kwargs):
        command = args[0]

        if command == ["git", "diff", "--numstat", "--find-renames", "HEAD"]:
            return subprocess.CompletedProcess(
                args=command,
                returncode=0,
                stdout=(
                    "2\t1\tz_file.py\n"
                    "5\t2\ta_file.py\n"
                    "3\t4\tz_file.py\n"
                ),
                stderr="",
            )

        if command == ["git", "ls-files", "--others", "--exclude-standard"]:
            return subprocess.CompletedProcess(
                args=command,
                returncode=0,
                stdout="",
                stderr="",
            )

        raise AssertionError(f"Unexpected command: {command}")

    monkeypatch.setattr(subprocess, "run", fake_run)

    diff_stats = get_diff_stats()

    assert diff_stats == [
        DiffStat(file_path="a_file.py", additions=5, deletions=2),
        DiffStat(file_path="z_file.py", additions=5, deletions=5),
    ]


def test_get_changed_files_uses_destination_path_for_renamed_files(monkeypatch) -> None:
    def fake_run(*args, **kwargs):
        return subprocess.CompletedProcess(
            args=["git", "status", "--porcelain"],
            returncode=0,
            stdout="R  old_name.py -> new_name.py\n",
            stderr="",
        )

    monkeypatch.setattr(subprocess, "run", fake_run)

    changed_files = get_changed_files()

    assert changed_files == ["new_name.py"]


def test_get_diff_stats_uses_destination_path_for_simple_rename(monkeypatch) -> None:
    def fake_run(*args, **kwargs):
        command = args[0]

        if command == ["git", "diff", "--numstat", "--find-renames", "HEAD"]:
            return subprocess.CompletedProcess(
                args=command,
                returncode=0,
                stdout="0\t0\told_name.py => new_name.py\n",
                stderr="",
            )

        if command == ["git", "ls-files", "--others", "--exclude-standard"]:
            return subprocess.CompletedProcess(
                args=command,
                returncode=0,
                stdout="",
                stderr="",
            )

        raise AssertionError(f"Unexpected command: {command}")

    monkeypatch.setattr(subprocess, "run", fake_run)

    diff_stats = get_diff_stats()

    assert diff_stats == [
        DiffStat(file_path="new_name.py", additions=0, deletions=0),
    ]


def test_get_diff_stats_uses_destination_path_for_braced_rename(monkeypatch) -> None:
    def fake_run(*args, **kwargs):
        command = args[0]

        if command == ["git", "diff", "--numstat", "--find-renames", "HEAD"]:
            return subprocess.CompletedProcess(
                args=command,
                returncode=0,
                stdout="0\t0\tsrc/{old_name.py => new_name.py}\n",
                stderr="",
            )

        if command == ["git", "ls-files", "--others", "--exclude-standard"]:
            return subprocess.CompletedProcess(
                args=command,
                returncode=0,
                stdout="",
                stderr="",
            )

        raise AssertionError(f"Unexpected command: {command}")

    monkeypatch.setattr(subprocess, "run", fake_run)

    diff_stats = get_diff_stats()

    assert diff_stats == [
        DiffStat(file_path="src/new_name.py", additions=0, deletions=0),
    ]

def test_get_diff_stats_counts_binary_untracked_file_as_zero_lines(
    monkeypatch,
    tmp_path,
) -> None:
    binary_file = tmp_path / "image.png"
    binary_file.write_bytes(b"\xff\xfe\x00\x00")

    monkeypatch.chdir(tmp_path)

    def fake_run(*args, **kwargs):
        command = args[0]

        if command == ["git", "diff", "--numstat", "--find-renames", "HEAD"]:
            return subprocess.CompletedProcess(
                args=command,
                returncode=0,
                stdout="",
                stderr="",
            )

        if command == ["git", "ls-files", "--others", "--exclude-standard"]:
            return subprocess.CompletedProcess(
                args=command,
                returncode=0,
                stdout="image.png\n",
                stderr="",
            )

        raise AssertionError(f"Unexpected command: {command}")

    monkeypatch.setattr(subprocess, "run", fake_run)

    diff_stats = get_diff_stats()

    assert diff_stats == [
        DiffStat(file_path="image.png", additions=0, deletions=0),
    ]


def test_get_diff_stats_counts_missing_untracked_file_as_zero_lines(
    monkeypatch,
    tmp_path,
) -> None:
    monkeypatch.chdir(tmp_path)

    def fake_run(*args, **kwargs):
        command = args[0]

        if command == ["git", "diff", "--numstat", "--find-renames", "HEAD"]:
            return subprocess.CompletedProcess(
                args=command,
                returncode=0,
                stdout="",
                stderr="",
            )

        if command == ["git", "ls-files", "--others", "--exclude-standard"]:
            return subprocess.CompletedProcess(
                args=command,
                returncode=0,
                stdout="missing_file.py\n",
                stderr="",
            )

        raise AssertionError(f"Unexpected command: {command}")

    monkeypatch.setattr(subprocess, "run", fake_run)

    diff_stats = get_diff_stats()

    assert diff_stats == [
        DiffStat(file_path="missing_file.py", additions=0, deletions=0),
    ]