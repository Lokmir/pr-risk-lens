from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import Any

from pr_risk_lens.git import DiffStat


@dataclass(frozen=True)
class RiskFactor:
    label: str
    points: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "label": self.label,
            "points": self.points,
        }


@dataclass(frozen=True)
class RiskReport:
    changed_files: list[str]
    test_files: list[str]
    total_additions: int
    total_deletions: int
    risk_score: int
    risk_level: str
    risk_factors: list[RiskFactor]

    @property
    def has_changes(self) -> bool:
        return bool(self.changed_files)

    @property
    def has_test_changes(self) -> bool:
        return bool(self.test_files)

    @property
    def total_changed_lines(self) -> int:
        return self.total_additions + self.total_deletions

    def to_dict(self) -> dict[str, Any]:
        return {
            "changed_files": self.changed_files,
            "test_changes": {
                "has_test_changes": self.has_test_changes,
                "test_files": self.test_files,
            },
            "diff_stats": {
                "lines_added": self.total_additions,
                "lines_deleted": self.total_deletions,
                "total_changed_lines": self.total_changed_lines,
            },
            "risk": {
                "score": self.risk_score,
                "level": self.risk_level,
                "factors": [
                    factor.to_dict()
                    for factor in self.risk_factors
                ],
            },
        }


def build_risk_report(
    changed_files: list[str],
    diff_stats: list[DiffStat],
) -> RiskReport:
    """
    Build a basic risk report from Git data.

    The score is intentionally simple and transparent.
    Each risk factor explains how many points it adds.
    """
    total_additions = sum(stat.additions for stat in diff_stats)
    total_deletions = sum(stat.deletions for stat in diff_stats)
    total_changed_lines = total_additions + total_deletions

    test_files = [
        file_path
        for file_path in changed_files
        if _is_test_file(file_path)
    ]

    has_python_source_changes = any(
        _is_python_source_file(file_path)
        for file_path in changed_files
    )

    risk_factors = _build_risk_factors(
        changed_file_count=len(changed_files),
        total_changed_lines=total_changed_lines,
        has_python_source_changes=has_python_source_changes,
        has_test_changes=bool(test_files),
    )

    risk_score = sum(factor.points for factor in risk_factors)

    return RiskReport(
        changed_files=changed_files,
        test_files=test_files,
        total_additions=total_additions,
        total_deletions=total_deletions,
        risk_score=risk_score,
        risk_level=_risk_level_from_score(risk_score),
        risk_factors=risk_factors,
    )


def _build_risk_factors(
    changed_file_count: int,
    total_changed_lines: int,
    has_python_source_changes: bool,
    has_test_changes: bool,
) -> list[RiskFactor]:
    factors: list[RiskFactor] = []

    if changed_file_count == 0:
        return factors

    factors.append(_change_size_factor(total_changed_lines))
    factors.append(_changed_files_factor(changed_file_count))

    if has_python_source_changes and not has_test_changes:
        factors.append(
            RiskFactor(
                label="No test changes detected for Python code changes",
                points=10,
            )
        )

    return factors


def _change_size_factor(total_changed_lines: int) -> RiskFactor:
    if total_changed_lines <= 50:
        return RiskFactor(
            label=f"Change size: {total_changed_lines} changed lines",
            points=10,
        )

    if total_changed_lines <= 200:
        return RiskFactor(
            label=f"Change size: {total_changed_lines} changed lines",
            points=25,
        )

    return RiskFactor(
        label=f"Change size: {total_changed_lines} changed lines",
        points=40,
    )


def _changed_files_factor(changed_file_count: int) -> RiskFactor:
    if changed_file_count <= 3:
        return RiskFactor(
            label=f"Files changed: {changed_file_count} files",
            points=5,
        )

    if changed_file_count <= 10:
        return RiskFactor(
            label=f"Files changed: {changed_file_count} files",
            points=15,
        )

    return RiskFactor(
        label=f"Files changed: {changed_file_count} files",
        points=25,
    )


def _is_python_source_file(file_path: str) -> bool:
    return file_path.endswith(".py") and not _is_test_file(file_path)


def _is_test_file(file_path: str) -> bool:
    path = PurePosixPath(file_path.replace("\\", "/"))
    file_name = path.name

    return (
        "tests" in path.parts
        or file_name.startswith("test_")
        or file_name.endswith("_test.py")
    )


def _risk_level_from_score(score: int) -> str:
    if score == 0:
        return "None"

    if score <= 30:
        return "Low"

    if score <= 60:
        return "Medium"

    return "High"