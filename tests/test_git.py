import subprocess

from pr_risk_lens.git import DiffStat, get_changed_files, get_diff_stats


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
        return subprocess.CompletedProcess(
            args=["git", "diff", "--numstat", "HEAD"],
            returncode=0,
            stdout=(
                "5\t2\tREADME.md\n"
                "12\t0\tsrc/pr_risk_lens/git.py\n"
            ),
            stderr="",
        )

    monkeypatch.setattr(subprocess, "run", fake_run)

    diff_stats = get_diff_stats()

    assert diff_stats == [
        DiffStat(file_path="README.md", additions=5, deletions=2),
        DiffStat(file_path="src/pr_risk_lens/git.py", additions=12, deletions=0),
    ]


def test_get_diff_stats_handles_binary_files(monkeypatch) -> None:
    def fake_run(*args, **kwargs):
        return subprocess.CompletedProcess(
            args=["git", "diff", "--numstat", "HEAD"],
            returncode=0,
            stdout="-\t-\timage.png\n",
            stderr="",
        )

    monkeypatch.setattr(subprocess, "run", fake_run)

    diff_stats = get_diff_stats()

    assert diff_stats == [
        DiffStat(file_path="image.png", additions=0, deletions=0),
    ]