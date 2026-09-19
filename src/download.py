"""Download public copies of the three assignment datasets with URL fallbacks."""
from __future__ import annotations

import io
import zipfile
from pathlib import Path

import pandas as pd
import requests

from .config import DATA_RAW, USER_AGENT

TIMEOUT = 60

PLAY_URLS = [
    "https://raw.githubusercontent.com/ingledarshan/Data-Science-Advanced-Datasets/main/googleplaystore.csv",
    "https://raw.githubusercontent.com/DoyenPyth/Google-Play-Store-Apps/master/googleplaystore.csv",
    "https://raw.githubusercontent.com/DoyenPyth/Google-Play-Store-Apps/main/googleplaystore.csv",
]
PLAY_REVIEW_URLS = [
    "https://raw.githubusercontent.com/DoyenPyth/Google-Play-Store-Apps/master/googleplaystore_user_reviews.csv",
    "https://raw.githubusercontent.com/DoyenPyth/Google-Play-Store-Apps/main/googleplaystore_user_reviews.csv",
    "https://raw.githubusercontent.com/ingledarshan/Data-Science-Advanced-Datasets/main/googleplaystore_user_reviews.csv",
]
HOTEL_URLS = [
    "https://raw.githubusercontent.com/rfordatascience/tidytuesday/master/data/2020/2020-02-11/hotels.csv",
    "https://raw.githubusercontent.com/jessieyang0320/Hotel-booking-demand-analysis/master/hotel_bookings.csv",
]
HEART_URLS = [
    "https://raw.githubusercontent.com/plotly/datasets/master/heart.csv",
    "https://raw.githubusercontent.com/kb22/Heart-Disease-Prediction/master/dataset.csv",
    "https://raw.githubusercontent.com/rashida048/Datasets/master/heart.csv",
]


def _get(url: str) -> bytes:
    response = requests.get(url, headers=USER_AGENT, timeout=TIMEOUT)
    response.raise_for_status()
    return response.content


def _read_csv_from_urls(urls: list[str], dest: Path) -> pd.DataFrame:
    if dest.exists() and dest.stat().st_size > 0:
        return pd.read_csv(dest)
    last_error: Exception | None = None
    for url in urls:
        try:
            content = _get(url)
            df = pd.read_csv(io.BytesIO(content))
            if df.empty or df.shape[1] < 3:
                continue
            dest.write_bytes(content)
            return df
        except Exception as exc:  # noqa: BLE001 - try next mirror
            last_error = exc
    raise RuntimeError(f"Could not download {dest.name}. Last error: {last_error}")


def load_play_store() -> tuple[pd.DataFrame, pd.DataFrame | None]:
    apps = _read_csv_from_urls(PLAY_URLS, DATA_RAW / "googleplaystore.csv")
    reviews = None
    try:
        reviews = _read_csv_from_urls(PLAY_REVIEW_URLS, DATA_RAW / "googleplaystore_user_reviews.csv")
    except Exception:
        reviews = None
    return apps, reviews


def load_hotels() -> pd.DataFrame:
    return _read_csv_from_urls(HOTEL_URLS, DATA_RAW / "hotel_bookings.csv")


def load_heart() -> pd.DataFrame:
    df = _read_csv_from_urls(HEART_URLS, DATA_RAW / "heart.csv")
    rename = {
        "condition": "target",
        "num": "target",
        "output": "target",
    }
    df = df.rename(columns={k: v for k, v in rename.items() if k in df.columns})
    return df
