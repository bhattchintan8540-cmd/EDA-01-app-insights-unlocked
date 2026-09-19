"""Run this project's analysis, assessments, and presentation export."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.app_insights import run
from src.presentations import build_all
from src.config import OUTPUTS, PRESENTATIONS


def assess(findings: dict) -> list[str]:
    errors = []
    if findings["data_overview"].get("rows_clean", 0) < 50:
        errors.append("too few cleaned rows")
    if len(findings.get("key_findings", [])) < 4:
        errors.append("insufficient key findings")
    if len(findings.get("figures", [])) < 4:
        errors.append("expected at least 4 figures")
    qa = findings.get("qa", {})
    for level in ("basic", "medium", "advanced"):
        if len(qa.get(level, [])) < 3:
            errors.append(f"incomplete {level} Q&A")
    return errors


def main() -> int:
    findings = run()
    issues = assess(findings)
    paths = build_all([findings])
    report = {
        "title": findings["title"],
        "rows_clean": findings["data_overview"].get("rows_clean"),
        "assessment_issues": issues,
        "presentations": [str(p) for p in paths],
    }
    (OUTPUTS / "run_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("Cleaned rows:", report["rows_clean"])
    print("Presentations:")
    for p in paths:
        print(" -", p)
    if issues:
        print("Assessment notes:", issues)
        return 1
    print("Pipeline completed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
