from src.presentations import build_html, build_pptx
from src.config import PRESENTATIONS


def _payload():
    return {
        "slug": "demo",
        "code": "EDA 00",
        "title": "Demo Deck",
        "dataset": "unit test",
        "overview": "Overview text",
        "problem_statement": "Problem text",
        "methodology": ["Step A", "Step B"],
        "data_overview": {"rows_clean": 100},
        "key_findings": ["F1", "F2", "F3", "F4"],
        "limitations": ["L1"],
        "conclusion": "Done",
        "recommendations": ["R1", "R2"],
        "qa": {"basic": [{"q": "Q", "a": "A"}], "medium": [], "advanced": []},
        "figures": [],
        "stakeholders": {"internal": ["A"], "external": ["B"]},
    }


def test_presentation_exports(tmp_path, monkeypatch):
    monkeypatch.setattr("src.presentations.PRESENTATIONS", tmp_path)
    findings = _payload()
    pptx = build_pptx(findings)
    html = build_html(findings)
    assert pptx.exists() and pptx.stat().st_size > 1000
    text = html.read_text(encoding="utf-8")
    for heading in [
        "1) Overview",
        "Problem Statement",
        "Proposed Methodology",
        "Data Overview",
        "Key Findings",
        "Limitations",
        "Conclusion",
        "Recommendations",
    ]:
        assert heading.split(") ")[-1] in text or heading in text
    assert PRESENTATIONS.name  # config still importable
