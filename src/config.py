"""Shared paths, plotting setup, and download helpers."""
from __future__ import annotations

from pathlib import Path
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns

ROOT = Path(__file__).resolve().parents[1]
DATA_RAW = ROOT / "data" / "raw"
OUTPUTS = ROOT / "outputs"
PRESENTATIONS = ROOT / "presentations"
ASSIGNMENTS = ROOT / "docs" / "assignments"

for path in (DATA_RAW, OUTPUTS, PRESENTATIONS, ASSIGNMENTS):
    path.mkdir(parents=True, exist_ok=True)

sns.set_theme(style="whitegrid", context="talk")
plt.rcParams.update(
    {
        "figure.figsize": (11, 6),
        "savefig.dpi": 140,
        "savefig.bbox": "tight",
        "axes.titlesize": 14,
        "axes.labelsize": 12,
    }
)

USER_AGENT = {"User-Agent": "EDA-Projects/1.0 (academic analysis)"}


def project_output(slug: str) -> Path:
    path = OUTPUTS / slug
    path.mkdir(parents=True, exist_ok=True)
    (path / "figures").mkdir(exist_ok=True)
    return path


def savefig(path: Path) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(path)
    plt.close()
    return str(path)
