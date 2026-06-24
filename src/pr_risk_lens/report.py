import re
from dataclasses import dataclass

from pr_risk_lens.git import AddedLine, DiffStat

SENSITIVE_FILE_NAMES = {
    "pyproject.toml",
    "requirements.txt",
    "requirements-dev.txt",
    "setup.py",
    "setup.cfg",
    "tox.ini",
    "Dockerfile",
    "docker-compose.yml",
    "docker-compose.yaml",
}


@dataclass(frozen=True)
class RiskFactor:
    label: str
    points: int


@dataclass(frozen=True)
class RiskyKeywordRule:
    keyword: str
    pattern: str
    points: int


@dataclass(frozen=True)
class RiskyKeywordMatch:
    keyword: str
    file_path: str
    line_number: int
    line_content: str
    points: int


RISKY_KEYWORD_RULES = (
    RiskyKeywordRule(
        keyword="password",
        pattern=r"['\"]?password['\"]?\s*[:=]",
        points=10,
    ),
    RiskyKeywordRule(
        keyword="secret",
        pattern=r"['\"]?secret['\"]?\s*[:=]",
        points=10,
    ),
    RiskyKeywordRule(
        keyword="token",
        pattern=r"['\"]?token['\"]?\s*[:=]",
        points=10,
    ),
    RiskyKeywordRule(
        keyword="api_key",
        pattern=r"['\"]?api[_-]?key['\"]?\s*[:=]",
        points=10,
    ),
    RiskyKeywordRule(
        keyword="private_key",
        pattern=r"['\"]?private[_-]?key['\"]?\s*[:=]",
        points=10,
    ),
    RiskyKeywordRule(keyword="eval", pattern=r"\beval\s*\(", points=10),
    RiskyKeywordRule(keyword="exec", pattern=r"\bexec\s*\(", points=10),
    RiskyKeywordRule(
        keyword="shell=True",
        pattern=r"(?<!keyword=['\"])\bshell\s*=\s*True\b",
        points=10,
    ),
    RiskyKeywordRule(
        keyword="verify=False",
        pattern=r"(?<!keyword=['\"])\bverify\s*=\s*False\b",
        points=10,
    ),
)


def should_scan_for_risky_keywords(file_path: str) -> bool:
    normalized_path = _normalize_path(file_path)
    file_name = normalized_path.split("/")[-1].lower()

    if is_test_file(normalized_path):
        return False

    if normalized_path.startswith("docs/"):
        return False

    if file_name in {"readme.md", "changelog.md", "license", "license.md"}:
        return False

    if normalized_path.endswith((".md", ".rst")):
        return False

    return True


@dataclass(frozen=True)
class RiskReport:
    changed_files: list[str]
    diff_stats: list[DiffStat]
    test_files: list[str]
    sensitive_files: list[str]
    risky_keyword_matches: list[RiskyKeywordMatch]
    risk_factors: list[RiskFactor]
    risk_score: int

    @property
    def has_changes(self) -> bool:
        return bool(self.changed_files)

    @property
    def total_additions(self) -> int:
        return sum(stat.additions for stat in self.diff_stats)

    @property
    def total_deletions(self) -> int:
        return sum(stat.deletions for stat in self.diff_stats)

    @property
    def total_changed_lines(self) -> int:
        return self.total_additions + self.total_deletions

    @property
    def has_test_changes(self) -> bool:
        return bool(self.test_files)

    @property
    def has_sensitive_changes(self) -> bool:
        return bool(self.sensitive_files)

    @property
    def has_risky_keyword_matches(self) -> bool:
        return bool(self.risky_keyword_matches)

    @property
    def risk_level(self) -> str:
        if self.risk_score == 0:
            return "None"

        if self.risk_score <= 30:
            return "Low"

        if self.risk_score <= 60:
            return "Medium"

        return "High"

    def to_dict(self) -> dict[str, object]:
        return {
            "changed_files": self.changed_files,
            "test_changes": {
                "has_test_changes": self.has_test_changes,
                "test_files": self.test_files,
            },
            "sensitive_changes": {
                "has_sensitive_changes": self.has_sensitive_changes,
                "sensitive_files": self.sensitive_files,
            },
            "risky_keyword_matches": [
                {
                    "keyword": match.keyword,
                    "file_path": match.file_path,
                    "line_number": match.line_number,
                    "line_content": match.line_content,
                    "points": match.points,
                }
                for match in self.risky_keyword_matches
            ],
            "diff_stats": {
                "lines_added": self.total_additions,
                "lines_deleted": self.total_deletions,
                "total_changed_lines": self.total_changed_lines,
            },
            "risk": {
                "score": self.risk_score,
                "level": self.risk_level,
                "factors": [
                    {
                        "label": factor.label,
                        "points": factor.points,
                    }
                    for factor in self.risk_factors
                ],
            },
        }


def build_risk_report(
    changed_files: list[str],
    diff_stats: list[DiffStat],
    added_lines: list[AddedLine] | None = None,
) -> RiskReport:
    if added_lines is None:
        added_lines = []

    test_files = sorted(
        file_path for file_path in changed_files if is_test_file(file_path)
    )
    sensitive_files = sorted(
        file_path for file_path in changed_files if is_sensitive_file(file_path)
    )
    risky_keyword_matches = find_risky_keyword_matches(added_lines)

    risk_factors = _build_risk_factors(
        changed_files=changed_files,
        diff_stats=diff_stats,
        test_files=test_files,
        sensitive_files=sensitive_files,
        risky_keyword_matches=risky_keyword_matches,
    )

    risk_score = min(sum(factor.points for factor in risk_factors), 100)

    return RiskReport(
        changed_files=changed_files,
        diff_stats=diff_stats,
        test_files=test_files,
        sensitive_files=sensitive_files,
        risky_keyword_matches=risky_keyword_matches,
        risk_factors=risk_factors,
        risk_score=risk_score,
    )


def find_risky_keyword_matches(
    added_lines: list[AddedLine],
) -> list[RiskyKeywordMatch]:
    matches: list[RiskyKeywordMatch] = []

    for added_line in added_lines:
        if not should_scan_for_risky_keywords(added_line.file_path):
            continue

        for rule in RISKY_KEYWORD_RULES:
            if re.search(rule.pattern, added_line.content, flags=re.IGNORECASE):
                matches.append(
                    RiskyKeywordMatch(
                        keyword=rule.keyword,
                        file_path=added_line.file_path,
                        line_number=added_line.line_number,
                        line_content="<hidden>",
                        points=rule.points,
                    )
                )

    return sorted(
        matches,
        key=lambda match: (
            match.file_path,
            match.line_number,
            match.keyword,
        ),
    )


def is_test_file(file_path: str) -> bool:
    normalized_path = _normalize_path(file_path)
    path_parts = normalized_path.split("/")
    file_name = path_parts[-1]

    return (
        "tests" in path_parts
        or file_name.startswith("test_")
        or file_name.endswith("_test.py")
    )


def is_sensitive_file(file_path: str) -> bool:
    normalized_path = _normalize_path(file_path)

    if normalized_path in SENSITIVE_FILE_NAMES:
        return True

    return normalized_path.startswith(".github/workflows/") and (
        normalized_path.endswith(".yml") or normalized_path.endswith(".yaml")
    )


def _build_risk_factors(
    changed_files: list[str],
    diff_stats: list[DiffStat],
    test_files: list[str],
    sensitive_files: list[str],
    risky_keyword_matches: list[RiskyKeywordMatch],
) -> list[RiskFactor]:
    if not changed_files:
        return []

    risk_factors: list[RiskFactor] = []
    total_changed_lines = sum(stat.additions + stat.deletions for stat in diff_stats)

    risk_factors.append(_build_change_size_factor(total_changed_lines))
    risk_factors.append(_build_changed_files_factor(len(changed_files)))

    has_python_source_changes = any(
        file_path.endswith(".py") and not is_test_file(file_path)
        for file_path in changed_files
    )

    if has_python_source_changes and not test_files:
        risk_factors.append(
            RiskFactor(
                label="Python source changes without test changes",
                points=10,
            )
        )

    if sensitive_files:
        risk_factors.append(
            RiskFactor(
                label="Risk-sensitive files changed",
                points=10,
            )
        )

    if risky_keyword_matches:
        risk_factors.append(_build_risky_keyword_factor(risky_keyword_matches))

    return risk_factors


def _build_change_size_factor(total_changed_lines: int) -> RiskFactor:
    if total_changed_lines <= 50:
        points = 10
    elif total_changed_lines <= 200:
        points = 25
    else:
        points = 40

    return RiskFactor(
        label=(
            f"Change size: {total_changed_lines} "
            f"{_pluralize(total_changed_lines, 'changed line')}"
        ),
        points=points,
    )


def _build_changed_files_factor(changed_file_count: int) -> RiskFactor:
    if changed_file_count <= 3:
        points = 5
    elif changed_file_count <= 10:
        points = 15
    else:
        points = 25

    return RiskFactor(
        label=(
            f"Files changed: {changed_file_count} "
            f"{_pluralize(changed_file_count, 'file')}"
        ),
        points=points,
    )


def _build_risky_keyword_factor(
    risky_keyword_matches: list[RiskyKeywordMatch],
) -> RiskFactor:
    match_count = len(risky_keyword_matches)
    raw_points = sum(match.points for match in risky_keyword_matches)

    return RiskFactor(
        label=(
            f"Risky keyword matches: {match_count} "
            f"{_pluralize(match_count, 'match', 'matches')}"
        ),
        points=min(raw_points, 30),
    )


def _normalize_path(file_path: str) -> str:
    return file_path.replace("\\", "/")


def _pluralize(count: int, singular: str, plural: str | None = None) -> str:
    if count == 1:
        return singular

    if plural is not None:
        return plural

    return f"{singular}s"
