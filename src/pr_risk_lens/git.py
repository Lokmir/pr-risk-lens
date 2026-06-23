from dataclasses import dataclass
import subprocess


@dataclass(frozen=True)
class DiffStat:
    file_path: str
    additions: int
    deletions: int


class GitCommandError(RuntimeError):
    """
    Raised when a Git command cannot be executed successfully.
    """


def get_changed_files(base_ref: str | None = None) -> list[str]:
    """
    Return the list of changed files.

    Without base_ref:
        detect local working tree changes using:
            git status --porcelain

    With base_ref:
        compare the current branch against the base reference using:
            git diff --name-only <base_ref>...HEAD
    """
    if base_ref:
        return _get_changed_files_against_base(base_ref)

    return _get_changed_files_from_working_tree()


def get_diff_stats(base_ref: str | None = None) -> list[DiffStat]:
    """
    Return line-level diff statistics.

    Without base_ref:
        compare local changes against HEAD using:
            git diff --numstat HEAD

    With base_ref:
        compare the current branch against the base reference using:
            git diff --numstat <base_ref>...HEAD
    """
    if base_ref:
        command = ["git", "diff", "--numstat", f"{base_ref}...HEAD"]
    else:
        command = ["git", "diff", "--numstat", "HEAD"]

    result = _run_git(command)

    stats: list[DiffStat] = []

    for line in result.stdout.splitlines():
        stat = _parse_numstat_line(line)
        if stat:
            stats.append(stat)

    return stats


def _get_changed_files_from_working_tree() -> list[str]:
    result = _run_git(["git", "status", "--porcelain"])

    changed_files: list[str] = []

    for line in result.stdout.splitlines():
        file_path = _parse_porcelain_line(line)
        if file_path:
            changed_files.append(file_path)

    return changed_files


def _get_changed_files_against_base(base_ref: str) -> list[str]:
    result = _run_git(
        ["git", "diff", "--name-only", f"{base_ref}...HEAD"]
    )

    return result.stdout.splitlines()


def _run_git(command: list[str]) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=True,
        )
    except FileNotFoundError as error:
        raise GitCommandError(
            "Git is not installed or not available in PATH."
        ) from error
    except subprocess.CalledProcessError as error:
        raise GitCommandError(
            _format_git_error(error)
        ) from error


def _format_git_error(error: subprocess.CalledProcessError) -> str:
    stderr = error.stderr.strip() if error.stderr else ""

    if "not a git repository" in stderr.lower():
        return "Not inside a Git repository."

    if "unknown revision" in stderr.lower() or "ambiguous argument" in stderr.lower():
        return "Git reference not found. Check the branch or base ref name."

    if stderr:
        return stderr

    return "Git command failed."


def _parse_porcelain_line(line: str) -> str:
    """
    Extract the file path from one line of 'git status --porcelain'.

    Example lines:
        " M README.md"
        "?? new_file.py"
        "A  src/example.py"
    """
    return line[3:]


def _parse_numstat_line(line: str) -> DiffStat | None:
    """
    Extract line statistics from one line of 'git diff --numstat'.

    Example line:
        "5\t2\tREADME.md"
    """
    parts = line.split("\t", maxsplit=2)

    if len(parts) != 3:
        return None

    additions_text, deletions_text, file_path = parts

    return DiffStat(
        file_path=file_path,
        additions=_parse_numstat_number(additions_text),
        deletions=_parse_numstat_number(deletions_text),
    )


def _parse_numstat_number(value: str) -> int:
    """
    Convert a Git numstat value to an integer.

    Git may return '-' for binary files. For the MVP, we count that as 0.
    """
    if value == "-":
        return 0

    return int(value)