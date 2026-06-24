from pr_risk_lens.git import DiffStat
from pr_risk_lens.report import (
    RiskFactor,
    RiskReport,
    build_risk_report,
    is_sensitive_file,
    is_test_file,
)


def test_build_risk_report_computes_totals() -> None:
    report = build_risk_report(
        changed_files=["README.md", "src/pr_risk_lens/cli.py"],
        diff_stats=[
            DiffStat(file_path="README.md", additions=5, deletions=2),
            DiffStat(file_path="src/pr_risk_lens/cli.py", additions=10, deletions=1),
        ],
    )

    assert report.changed_files == ["README.md", "src/pr_risk_lens/cli.py"]
    assert report.diff_stats == [
        DiffStat(file_path="README.md", additions=5, deletions=2),
        DiffStat(file_path="src/pr_risk_lens/cli.py", additions=10, deletions=1),
    ]
    assert report.test_files == []
    assert report.sensitive_files == []
    assert report.total_additions == 15
    assert report.total_deletions == 3
    assert report.total_changed_lines == 18
    assert report.risk_score == 25
    assert report.risk_level == "Low"
    assert report.risk_factors == [
        RiskFactor(label="Change size: 18 changed lines", points=10),
        RiskFactor(label="Files changed: 2 files", points=5),
        RiskFactor(label="Python source changes without test changes", points=10),
    ]


def test_risk_report_knows_if_it_has_changes() -> None:
    report = RiskReport(
        changed_files=[],
        diff_stats=[],
        test_files=[],
        sensitive_files=[],
        risk_factors=[],
        risk_score=0,
    )

    assert report.has_changes is False
    assert report.total_additions == 0
    assert report.total_deletions == 0
    assert report.total_changed_lines == 0
    assert report.risk_level == "None"


def test_build_risk_report_detects_test_files() -> None:
    report = build_risk_report(
        changed_files=[
            "src/pr_risk_lens/cli.py",
            "tests/test_cli.py",
            "test_report.py",
            "report_test.py",
        ],
        diff_stats=[
            DiffStat(file_path="src/pr_risk_lens/cli.py", additions=5, deletions=1),
            DiffStat(file_path="tests/test_cli.py", additions=4, deletions=0),
            DiffStat(file_path="test_report.py", additions=3, deletions=0),
            DiffStat(file_path="report_test.py", additions=2, deletions=0),
        ],
    )

    assert report.has_test_changes is True
    assert report.test_files == [
        "report_test.py",
        "test_report.py",
        "tests/test_cli.py",
    ]


def test_build_risk_report_detects_sensitive_files() -> None:
    report = build_risk_report(
        changed_files=[
            "pyproject.toml",
            ".github/workflows/tests.yml",
            "src/pr_risk_lens/cli.py",
            "tests/test_cli.py",
        ],
        diff_stats=[
            DiffStat(file_path="pyproject.toml", additions=2, deletions=1),
            DiffStat(file_path=".github/workflows/tests.yml", additions=4, deletions=0),
            DiffStat(file_path="src/pr_risk_lens/cli.py", additions=10, deletions=2),
            DiffStat(file_path="tests/test_cli.py", additions=5, deletions=0),
        ],
    )

    assert report.has_sensitive_changes is True
    assert report.sensitive_files == [
        ".github/workflows/tests.yml",
        "pyproject.toml",
    ]
    assert RiskFactor(label="Risk-sensitive files changed", points=10) in (
        report.risk_factors
    )


def test_build_risk_report_returns_medium_risk_for_medium_change() -> None:
    report = build_risk_report(
        changed_files=[
            "file_1.py",
            "file_2.py",
            "file_3.py",
            "file_4.py",
        ],
        diff_stats=[
            DiffStat(file_path="file_1.py", additions=80, deletions=20),
        ],
    )

    assert report.risk_score == 50
    assert report.risk_level == "Medium"
    assert report.risk_factors == [
        RiskFactor(label="Change size: 100 changed lines", points=25),
        RiskFactor(label="Files changed: 4 files", points=15),
        RiskFactor(label="Python source changes without test changes", points=10),
    ]


def test_build_risk_report_returns_high_risk_for_large_change() -> None:
    report = build_risk_report(
        changed_files=[
            "file_1.py",
            "file_2.py",
            "file_3.py",
            "file_4.py",
            "file_5.py",
            "file_6.py",
            "file_7.py",
            "file_8.py",
            "file_9.py",
            "file_10.py",
            "file_11.py",
        ],
        diff_stats=[
            DiffStat(file_path="file_1.py", additions=250, deletions=20),
        ],
    )

    assert report.risk_score == 75
    assert report.risk_level == "High"
    assert report.risk_factors == [
        RiskFactor(label="Change size: 270 changed lines", points=40),
        RiskFactor(label="Files changed: 11 files", points=25),
        RiskFactor(label="Python source changes without test changes", points=10),
    ]


def test_risk_report_can_be_converted_to_dict() -> None:
    report = RiskReport(
        changed_files=["README.md", "tests/test_readme.py", "pyproject.toml"],
        diff_stats=[
            DiffStat(file_path="README.md", additions=2, deletions=1),
            DiffStat(file_path="tests/test_readme.py", additions=2, deletions=1),
            DiffStat(file_path="pyproject.toml", additions=1, deletions=0),
        ],
        test_files=["tests/test_readme.py"],
        sensitive_files=["pyproject.toml"],
        risk_factors=[
            RiskFactor(label="Change size: 7 changed lines", points=10),
            RiskFactor(label="Files changed: 3 files", points=5),
            RiskFactor(label="Risk-sensitive files changed", points=10),
        ],
        risk_score=25,
    )

    assert report.to_dict() == {
        "changed_files": ["README.md", "tests/test_readme.py", "pyproject.toml"],
        "test_changes": {
            "has_test_changes": True,
            "test_files": ["tests/test_readme.py"],
        },
        "sensitive_changes": {
            "has_sensitive_changes": True,
            "sensitive_files": ["pyproject.toml"],
        },
        "diff_stats": {
            "lines_added": 5,
            "lines_deleted": 2,
            "total_changed_lines": 7,
        },
        "risk": {
            "score": 25,
            "level": "Low",
            "factors": [
                {
                    "label": "Change size: 7 changed lines",
                    "points": 10,
                },
                {
                    "label": "Files changed: 3 files",
                    "points": 5,
                },
                {
                    "label": "Risk-sensitive files changed",
                    "points": 10,
                },
            ],
        },
    }


def test_is_test_file_detects_supported_test_patterns() -> None:
    assert is_test_file("tests/test_cli.py") is True
    assert is_test_file("src/tests/test_cli.py") is True
    assert is_test_file("test_report.py") is True
    assert is_test_file("report_test.py") is True
    assert is_test_file("src/report.py") is False


def test_is_sensitive_file_detects_supported_sensitive_patterns() -> None:
    assert is_sensitive_file("pyproject.toml") is True
    assert is_sensitive_file("requirements.txt") is True
    assert is_sensitive_file("Dockerfile") is True
    assert is_sensitive_file("docker-compose.yml") is True
    assert is_sensitive_file(".github/workflows/tests.yml") is True
    assert is_sensitive_file(".github/workflows/tests.yaml") is True
    assert is_sensitive_file("src/app.py") is False


def test_risk_factor_labels_use_singular_words() -> None:
    report = build_risk_report(
        changed_files=["src/app.py"],
        diff_stats=[
            DiffStat(file_path="src/app.py", additions=1, deletions=0),
        ],
    )

    labels = [factor.label for factor in report.risk_factors]

    assert "Change size: 1 changed line" in labels
    assert "Files changed: 1 file" in labels


def test_risk_factor_labels_use_plural_words() -> None:
    report = build_risk_report(
        changed_files=["src/app.py", "tests/test_app.py"],
        diff_stats=[
            DiffStat(file_path="src/app.py", additions=2, deletions=1),
            DiffStat(file_path="tests/test_app.py", additions=1, deletions=0),
        ],
    )

    labels = [factor.label for factor in report.risk_factors]

    assert "Change size: 4 changed lines" in labels
    assert "Files changed: 2 files" in labels
