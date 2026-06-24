import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class DiffStat:
    file_path: str
    additions: int
    deletions: int


@dataclass(frozen=True)
class AddedLine:
    file_path: str
    line_number: int
    content: str


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
            git diff --name-only --find-renames <base_ref>...HEAD

    Returned file paths are sorted and deduplicated for stable output.
    """
    if base_ref:
        return _get_changed_files_against_base(base_ref)

    return _get_changed_files_from_working_tree()


def get_diff_stats(base_ref: str | None = None) -> list[DiffStat]:
    """
    Return line-level diff statistics.

    Without base_ref:
        compare local tracked changes against HEAD and also count untracked files.

    With base_ref:
        compare the current branch against the base reference using:
            git diff --numstat --find-renames <base_ref>...HEAD

    Returned stats are sorted by file path and duplicate paths are merged.
    """
    if base_ref:
        return _get_diff_stats_against_base(base_ref)

    tracked_stats = _get_tracked_diff_stats_from_working_tree()
    untracked_stats = [
        _build_untracked_file_stat(file_path) for file_path in _get_untracked_files()
    ]

    return _merge_and_sort_diff_stats(tracked_stats + untracked_stats)


def get_added_lines(base_ref: str | None = None) -> list[AddedLine]:
    """
    Return added lines from Git changes.

    Without base_ref:
    - parse tracked changes from git diff HEAD
    - include readable untracked text files

    With base_ref:
    - parse added lines from git diff base...HEAD
    """
    if base_ref:
        return _get_added_lines_against_base(base_ref)

    tracked_lines = _get_tracked_added_lines_from_working_tree()
    untracked_lines = _get_untracked_added_lines()

    return _sort_added_lines(tracked_lines + untracked_lines)


def _get_changed_files_from_working_tree() -> list[str]:
    result = _run_git(["git", "status", "--porcelain"])

    changed_files: list[str] = []

    for line in result.stdout.splitlines():
        file_path = _parse_porcelain_line(line)
        if file_path:
            changed_files.append(file_path)

    return _unique_sorted(changed_files)


def _get_changed_files_against_base(base_ref: str) -> list[str]:
    result = _run_git(
        ["git", "diff", "--name-only", "--find-renames", f"{base_ref}...HEAD"]
    )

    return _unique_sorted(result.stdout.splitlines())


def _get_tracked_diff_stats_from_working_tree() -> list[DiffStat]:
    result = _run_git(["git", "diff", "--numstat", "--find-renames", "HEAD"])

    return _parse_numstat_output(result.stdout)


def _get_diff_stats_against_base(base_ref: str) -> list[DiffStat]:
    result = _run_git(
        ["git", "diff", "--numstat", "--find-renames", f"{base_ref}...HEAD"]
    )

    return _merge_and_sort_diff_stats(_parse_numstat_output(result.stdout))


def _get_untracked_files() -> list[str]:
    result = _run_git(["git", "ls-files", "--others", "--exclude-standard"])

    return _unique_sorted(result.stdout.splitlines())


def _build_untracked_file_stat(file_path: str) -> DiffStat:
    return DiffStat(
        file_path=file_path,
        additions=_count_file_lines(file_path),
        deletions=0,
    )


def _count_file_lines(file_path: str) -> int:
    path = Path(file_path)

    try:
        content = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return 0
    except OSError:
        return 0

    if not content:
        return 0

    return len(content.splitlines())


def _unique_sorted(file_paths: list[str]) -> list[str]:
    return sorted(set(file_paths))


def _merge_and_sort_diff_stats(stats: list[DiffStat]) -> list[DiffStat]:
    totals: dict[str, tuple[int, int]] = {}

    for stat in stats:
        current_additions, current_deletions = totals.get(
            stat.file_path,
            (0, 0),
        )

        totals[stat.file_path] = (
            current_additions + stat.additions,
            current_deletions + stat.deletions,
        )

    return [
        DiffStat(
            file_path=file_path,
            additions=totals[file_path][0],
            deletions=totals[file_path][1],
        )
        for file_path in sorted(totals)
    ]


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
        raise GitCommandError(_format_git_error(error)) from error


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
        "R  old_name.py -> new_name.py"
    """
    file_path = line[3:]

    if " -> " in file_path:
        return file_path.split(" -> ", maxsplit=1)[1]

    return file_path


def _parse_numstat_output(output: str) -> list[DiffStat]:
    stats: list[DiffStat] = []

    for line in output.splitlines():
        stat = _parse_numstat_line(line)
        if stat:
            stats.append(stat)

    return stats


def _parse_numstat_line(line: str) -> DiffStat | None:
    """
    Extract line statistics from one line of 'git diff --numstat'.

    Example lines:
        "5\t2\tREADME.md"
        "0\t0\told_name.py => new_name.py"
        "0\t0\tsrc/{old_name.py => new_name.py}"
    """
    parts = line.split("\t", maxsplit=2)

    if len(parts) != 3:
        return None

    additions_text, deletions_text, file_path = parts

    return DiffStat(
        file_path=_normalize_git_path(file_path),
        additions=_parse_numstat_number(additions_text),
        deletions=_parse_numstat_number(deletions_text),
    )


def _normalize_git_path(file_path: str) -> str:
    """
    Normalize Git rename paths to keep the destination path.

    Examples:
        "old.py => new.py" -> "new.py"
        "src/{old.py => new.py}" -> "src/new.py"
    """
    if "=>" not in file_path:
        return file_path

    if "{" in file_path and "}" in file_path:
        prefix = file_path.split("{", maxsplit=1)[0]
        inside = file_path.split("{", maxsplit=1)[1].split("}", maxsplit=1)[0]
        suffix = file_path.split("}", maxsplit=1)[1]

        new_name = inside.split("=>", maxsplit=1)[1].strip()

        return f"{prefix}{new_name}{suffix}"

    return file_path.split("=>", maxsplit=1)[1].strip()


def _parse_numstat_number(value: str) -> int:
    """
    Convert a Git numstat value to an integer.

    Git may return '-' for binary files. For the MVP, we count that as 0.
    """
    if value == "-":
        return 0

    return int(value)


def _get_tracked_added_lines_from_working_tree() -> list[AddedLine]:
    result = _run_git(["git", "diff", "--unified=0", "--find-renames", "HEAD"])
    return _parse_unified_diff_added_lines(result.stdout)


def _get_added_lines_against_base(base_ref: str) -> list[AddedLine]:
    result = _run_git(
        ["git", "diff", "--unified=0", "--find-renames", f"{base_ref}...HEAD"]
    )
    return _parse_unified_diff_added_lines(result.stdout)


def _get_untracked_added_lines() -> list[AddedLine]:
    added_lines: list[AddedLine] = []

    for file_path in _get_untracked_files():
        added_lines.extend(_build_untracked_added_lines(file_path))

    return added_lines


def _build_untracked_added_lines(file_path: str) -> list[AddedLine]:
    path = Path(file_path)

    try:
        content = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return []
    except OSError:
        return []

    return [
        AddedLine(
            file_path=file_path,
            line_number=line_number,
            content=line,
        )
        for line_number, line in enumerate(content.splitlines(), start=1)
    ]


def _parse_unified_diff_added_lines(output: str) -> list[AddedLine]:
    added_lines: list[AddedLine] = []
    current_file: str | None = None
    current_line_number: int | None = None

    for line in output.splitlines():
        if line.startswith("+++ "):
            current_file = _parse_diff_new_file_path(line)
            continue

        if line.startswith("@@ "):
            current_line_number = _parse_hunk_new_start(line)
            continue

        if current_file is None or current_line_number is None:
            continue

        if line.startswith("+") and not line.startswith("+++ "):
            added_lines.append(
                AddedLine(
                    file_path=current_file,
                    line_number=current_line_number,
                    content=line[1:],
                )
            )
            current_line_number += 1
            continue

        if line.startswith("-") and not line.startswith("--- "):
            continue

        current_line_number += 1

    return _sort_added_lines(added_lines)


def _parse_diff_new_file_path(line: str) -> str | None:
    file_path = line.removeprefix("+++ ").strip()

    if file_path == "/dev/null":
        return None

    if file_path.startswith("b/"):
        return file_path[2:]

    return file_path


def _parse_hunk_new_start(line: str) -> int:
    for part in line.split():
        if part.startswith("+"):
            return int(part[1:].split(",", maxsplit=1)[0])

    return 0


def _sort_added_lines(added_lines: list[AddedLine]) -> list[AddedLine]:
    return sorted(
        added_lines,
        key=lambda added_line: (
            added_line.file_path,
            added_line.line_number,
            added_line.content,
        ),
    )
