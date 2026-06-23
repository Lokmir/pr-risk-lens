from pr_risk_lens.git import DiffStat
from pr_risk_lens.report import RiskFactor, RiskReport, build_risk_report


def test_build_risk_report_computes_totals() -> None:
    report = build_risk_report(
        changed_files=["README.md", "src/pr_risk_lens/cli.py"],
        diff_stats=[
            DiffStat(file_path="README.md", additions=5, deletions=2),
            DiffStat(file_path="src/pr_risk_lens/cli.py", additions=10, deletions=1),
        ],
    )

    assert report == RiskReport(
        changed_files=["README.md", "src/pr_risk_lens/cli.py"],
        total_additions=15,
        total_deletions=3,
        risk_score=15,
        risk_level="Low",
        risk_factors=[
            RiskFactor(label="Change size: 18 changed lines", points=10),
            RiskFactor(label="Files changed: 2 files", points=5),
        ],
    )


def test_risk_report_knows_if_it_has_changes() -> None:
    report = RiskReport(
        changed_files=[],
        total_additions=0,
        total_deletions=0,
        risk_score=0,
        risk_level="None",
        risk_factors=[],
    )

    assert report.has_changes is False
    assert report.total_changed_lines == 0


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

    assert report.risk_score == 40
    assert report.risk_level == "Medium"
    assert report.risk_factors == [
        RiskFactor(label="Change size: 100 changed lines", points=25),
        RiskFactor(label="Files changed: 4 files", points=15),
    ]


def test_build_risk_report_returns_high_risk_for_large_change() -> None:
    report = build_risk_report(
        changed_files=[f"file_{index}.py" for index in range(11)],
        diff_stats=[
            DiffStat(file_path="large_file.py", additions=250, deletions=20),
        ],
    )

    assert report.risk_score == 65
    assert report.risk_level == "High"

def test_risk_report_can_be_converted_to_dict() -> None:
    report = RiskReport(
        changed_files=["README.md"],
        total_additions=5,
        total_deletions=2,
        risk_score=15,
        risk_level="Low",
        risk_factors=[
            RiskFactor(label="Change size: 7 changed lines", points=10),
            RiskFactor(label="Files changed: 1 files", points=5),
        ],
    )

    assert report.to_dict() == {
        "changed_files": ["README.md"],
        "diff_stats": {
            "lines_added": 5,
            "lines_deleted": 2,
            "total_changed_lines": 7,
        },
        "risk": {
            "score": 15,
            "level": "Low",
            "factors": [
                {
                    "label": "Change size: 7 changed lines",
                    "points": 10,
                },
                {
                    "label": "Files changed: 1 files",
                    "points": 5,
                },
            ],
        },
    }