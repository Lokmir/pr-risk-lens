from dataclasses import dataclass
import subprocess


@dataclass(frozen=True)
class DiffStat:
    file_path: str
    additions: int
    deletions: int


def get_changed_files() -> list[str]:
    """
    Return the list of changed files in the current Git working tree.

    This uses:
        git status --porcelain

    It detects:
    - modified files
    - added files
    - deleted files
    - untracked files
    """
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        capture_output=True,
        text=True,
        check=True,
    )

    changed_files: list[str] = []

    for line in result.stdout.splitlines():
        file_path = _parse_porcelain_line(line)
        if file_path:
            changed_files.append(file_path)

    return changed_files


def get_diff_stats() -> list[DiffStat]:
    """
    Return line-level diff statistics for tracked files.

    This uses:
        git diff --numstat HEAD

    It detects lines added and deleted compared to the last commit.
    """
    result = subprocess.run(
        ["git", "diff", "--numstat", "HEAD"],
        capture_output=True,
        text=True,
        check=True,
    )

    stats: list[DiffStat] = []

    for line in result.stdout.splitlines():
        stat = _parse_numstat_line(line)
        if stat:
            stats.append(stat)

    return stats


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
    Extract line statistics from one line of 'git diff --numstat HEAD'.

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