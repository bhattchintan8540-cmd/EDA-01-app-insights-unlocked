# App Insights Unlocked: A Data Analytics Challenge

**EDA 01** — Google Play Store apps

This repository is a standalone Exploratory Data Analysis project from the assignment brief in `docs/assignments/`.

## Presentations

Slides follow:

1. Overview
2. Problem Statement
3. Proposed Methodology
4. Data Overview
5. Key Findings
6. Limitations
7. Conclusion
8. Recommendations

- HTML: `presentations/EDA01_app_insights.html`
- PowerPoint: `presentations/EDA01_app_insights.pptx`

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
```

## Run

```bash
python run.py
python -m pytest -q
```

Outputs land in `outputs/` (figures, `findings.json` with the solution guide) and `presentations/`.
