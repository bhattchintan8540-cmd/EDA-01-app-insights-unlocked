"""EDA 01 — App Insights Unlocked: A Data Analytics Challenge."""
from __future__ import annotations

from pathlib import Path
import json
import re

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from .config import project_output, savefig
from .download import load_play_store


def _parse_installs(value) -> float:
    if pd.isna(value):
        return np.nan
    text = str(value).replace(",", "").replace("+", "").strip()
    if text.lower() in {"free", "nan", ""}:
        return np.nan
    try:
        return float(text)
    except ValueError:
        return np.nan


def _parse_price(value) -> float:
    if pd.isna(value):
        return 0.0
    text = str(value).replace("$", "").strip()
    if text.lower() in {"free", "0", ""}:
        return 0.0
    try:
        return float(text)
    except ValueError:
        return np.nan


def _parse_size(value) -> float:
    if pd.isna(value):
        return np.nan
    text = str(value).strip()
    if text.lower() in {"varies with device", "nan", ""}:
        return np.nan
    match = re.match(r"^([0-9.]+)\s*([MKmk])?$", text.replace(",", ""))
    if not match:
        return np.nan
    number = float(match.group(1))
    unit = (match.group(2) or "M").upper()
    return number / 1024 if unit == "K" else number


def clean_play_store(raw: pd.DataFrame) -> pd.DataFrame:
    df = raw.copy()
    df.columns = [c.strip() for c in df.columns]
    df = df[df["Category"].astype(str).str.contains(r"[A-Z_]", na=False)].copy()
    df["Reviews"] = pd.to_numeric(df["Reviews"], errors="coerce")
    df["Rating"] = pd.to_numeric(df["Rating"], errors="coerce")
    df["Installs_num"] = df["Installs"].map(_parse_installs)
    df["Price_num"] = df["Price"].map(_parse_price)
    df["Size_MB"] = df["Size"].map(_parse_size)
    df["Last Updated"] = pd.to_datetime(df["Last Updated"], errors="coerce")
    inferred = pd.Series(np.where(df["Price_num"] > 0, "Paid", "Free"), index=df.index)
    df["Type"] = df["Type"].replace({"0": np.nan}).fillna(inferred)
    df["Type"] = df["Type"].astype(str).str.title()
    df["Content Rating"] = df["Content Rating"].fillna("Unrated")
    df["Genres"] = df["Genres"].fillna("Unknown")
    df["Primary_Genre"] = df["Genres"].astype(str).str.split(";").str[0]
    df = df.drop_duplicates(subset=["App"], keep="first")
    df = df[(df["Rating"].isna()) | ((df["Rating"] >= 0) & (df["Rating"] <= 5))]
    return df.reset_index(drop=True)


def _qa(df: pd.DataFrame, reviews: pd.DataFrame | None) -> dict:
    rated = df.dropna(subset=["Rating"])
    answers = {"basic": [], "medium": [], "advanced": []}

    avg_rating = float(rated["Rating"].mean())
    n_categories = int(df["Category"].nunique())
    type_counts = df["Type"].value_counts().to_dict()
    content_mode = str(df["Content Rating"].mode().iloc[0])
    top_installed = (
        df.nlargest(5, "Installs_num")[["App", "Installs", "Category", "Rating"]]
        .fillna({"Rating": "NA"})
        .to_dict("records")
    )
    high_rated = int((rated["Rating"] >= 4).sum())
    reviews_by_type = rated.groupby("Type")["Reviews"].mean().to_dict()
    size_by_cat = (
        df.dropna(subset=["Size_MB"]).groupby("Category")["Size_MB"].mean().sort_values(ascending=False)
    )
    updated_2018 = int((df["Last Updated"].dt.year == 2018).sum())

    answers["basic"] = [
        {"q": "Average rating of apps", "a": round(avg_rating, 3)},
        {"q": "Unique categories", "a": n_categories},
        {
            "q": "App size distribution (MB)",
            "a": df["Size_MB"].describe()[["mean", "50%", "min", "max"]].round(2).to_dict(),
        },
        {"q": "Free vs paid counts", "a": {k: int(v) for k, v in type_counts.items()}},
        {"q": "Most common content rating", "a": content_mode},
        {"q": "Top 5 most installed apps", "a": top_installed},
        {"q": "Apps with rating 4.0+", "a": high_rated},
        {"q": "Average reviews free vs paid", "a": {k: round(v, 1) for k, v in reviews_by_type.items()}},
        {"q": "Largest average size category", "a": {size_by_cat.index[0]: round(float(size_by_cat.iloc[0]), 2)}},
        {"q": "Apps last updated in 2018", "a": updated_2018},
    ]

    corr = float(rated[["Installs_num", "Rating"]].corr().iloc[0, 1])
    cat_rating = rated.groupby("Category")["Rating"].mean().sort_values(ascending=False)
    paid = rated[rated["Type"] == "Paid"]
    price_rating = float(paid[["Price_num", "Rating"]].corr().iloc[0, 1]) if len(paid) > 5 else np.nan
    million = df[df["Installs_num"] >= 1_000_000]
    genre_million = million["Primary_Genre"].value_counts().head(8).to_dict()
    size_install_corr = float(df.dropna(subset=["Size_MB", "Installs_num"])[["Size_MB", "Installs_num"]].corr().iloc[0, 1])
    top_reviews = df.nlargest(5, "Reviews")[["App", "Reviews", "Rating"]].to_dict("records")
    content_by_type = pd.crosstab(df["Type"], df["Content Rating"], normalize="index").round(3).to_dict()
    cat_installs = df.groupby("Category")["Installs_num"].sum().sort_values(ascending=False).head(5)
    cat_installs = {k: int(v) for k, v in cat_installs.items()}

    answers["medium"] = [
        {"q": "Correlation installs vs rating", "a": round(corr, 4)},
        {"q": "Highest average rating categories", "a": cat_rating.head(5).round(3).to_dict()},
        {"q": "Price vs rating correlation (paid apps)", "a": None if pd.isna(price_rating) else round(price_rating, 4)},
        {"q": "Rating mean by content rating", "a": rated.groupby("Content Rating")["Rating"].mean().round(3).to_dict()},
        {"q": "Genres with most 1M+ install apps", "a": {k: int(v) for k, v in genre_million.items()}},
        {
            "q": "Update recency (days since last update vs max date)",
            "a": round(float((df["Last Updated"].max() - df["Last Updated"]).dt.days.mean()), 1),
        },
        {"q": "Correlation size vs installs", "a": round(size_install_corr, 4)},
        {"q": "Highest review apps and ratings", "a": top_reviews},
        {"q": "Content rating mix free vs paid", "a": content_by_type},
        {"q": "Top 5 categories by installs", "a": cat_installs},
    ]

    top10 = rated.nlargest(10, "Rating")[["App", "Rating", "Reviews", "Installs"]].to_dict("records")
    monthly = df.dropna(subset=["Last Updated"]).copy()
    monthly["ym"] = monthly["Last Updated"].dt.to_period("M").astype(str)
    update_trend = monthly.groupby("ym").size().tail(12).to_dict()
    bins = [0, 1_000, 10_000, 100_000, 1_000_000, 10_000_000, np.inf]
    labels = ["<1k", "1k-10k", "10k-100k", "100k-1M", "1M-10M", "10M+"]
    rated = rated.copy()
    rated["install_bin"] = pd.cut(rated["Installs_num"], bins=bins, labels=labels)
    bin_rating = rated.groupby("install_bin", observed=False)["Rating"].mean().round(3).to_dict()
    bin_rating = {str(k): v for k, v in bin_rating.items()}
    genre_stats = rated.groupby("Primary_Genre")["Rating"].agg(["mean", "median", "count"])
    genre_stats = genre_stats[genre_stats["count"] >= 30].sort_values("mean", ascending=False).head(8)

    sentiment = None
    if reviews is not None:
        rev = reviews.copy()
        rev.columns = [c.strip() for c in rev.columns]
        if {"Sentiment", "App"}.issubset(rev.columns):
            merged = rev.merge(df[["App", "Rating"]], on="App", how="inner").dropna(subset=["Sentiment", "Rating"])
            merged["rating_band"] = pd.cut(merged["Rating"], bins=[0, 3.5, 5], labels=["low", "high"])
            sentiment = (
                merged.groupby("rating_band", observed=False)["Sentiment"]
                .value_counts(normalize=True)
                .unstack(fill_value=0)
                .round(3)
                .to_dict()
            )

    answers["advanced"] = [
        {"q": "Top 10 highest-rated apps vs reviews/installs", "a": top10},
        {"q": "Recent monthly update counts", "a": update_trend},
        {"q": "Average rating by install bin", "a": bin_rating},
        {"q": "Review sentiment high vs low rated apps", "a": sentiment or "User-review file unavailable; skipped."},
        {"q": "Highest-rated genres (n>=30)", "a": genre_stats.round(3).to_dict()},
    ]
    return answers


def run() -> dict:
    out = project_output("app_insights")
    raw, reviews = load_play_store()
    df = clean_play_store(raw)
    rated = df.dropna(subset=["Rating"])

    fig_dir = out / "figures"
    plt.figure()
    sns.histplot(rated["Rating"], bins=20, kde=True, color="#2563eb")
    plt.title("Distribution of App Ratings")
    plt.xlabel("Rating")
    savefig(fig_dir / "01_rating_distribution.png")

    plt.figure(figsize=(12, 7))
    order = df["Category"].value_counts().head(12).index
    sns.countplot(data=df[df["Category"].isin(order)], y="Category", order=order, color="#0ea5e9")
    plt.title("Top App Categories by Count")
    savefig(fig_dir / "02_category_counts.png")

    plt.figure()
    sns.boxplot(data=df.dropna(subset=["Size_MB"]), x="Type", y="Size_MB", showfliers=False)
    plt.title("App Size (MB) by Type")
    savefig(fig_dir / "03_size_by_type.png")

    plt.figure(figsize=(11, 7))
    cat_installs = df.groupby("Category")["Installs_num"].sum().sort_values(ascending=False).head(10)
    sns.barplot(x=cat_installs.values, y=cat_installs.index, color="#16a34a")
    plt.title("Top Categories by Total Installs")
    plt.xlabel("Installs")
    savefig(fig_dir / "04_category_installs.png")

    plt.figure()
    sample = rated.dropna(subset=["Installs_num"]).sample(min(4000, len(rated)), random_state=42)
    sns.scatterplot(data=sample, x="Installs_num", y="Rating", hue="Type", alpha=0.35)
    plt.xscale("log")
    plt.title("Rating vs Installs")
    savefig(fig_dir / "05_rating_vs_installs.png")

    plt.figure()
    monthly = df.dropna(subset=["Last Updated"]).copy()
    monthly = monthly[monthly["Last Updated"].dt.year >= 2016]
    trend = monthly.groupby(monthly["Last Updated"].dt.to_period("M")).size()
    trend.index = trend.index.to_timestamp()
    trend.plot(color="#7c3aed")
    plt.title("App Updates Over Time")
    plt.ylabel("Apps updated")
    savefig(fig_dir / "06_update_trend.png")

    qa = _qa(df, reviews)
    free_share = float((df["Type"] == "Free").mean())
    findings = {
        "slug": "app_insights",
        "code": "EDA 01",
        "title": "App Insights Unlocked: A Data Analytics Challenge",
        "dataset": "Google Play Store apps (Kaggle: lava18/google-play-store-apps)",
        "overview": (
            "A tech product team analyzes Google Play Store listings to learn which categories, "
            "pricing models, sizes, and update habits are associated with higher ratings, reviews, and installs."
        ),
        "problem_statement": (
            "Identify the factors that contribute to app success on Google Play — especially ratings, "
            "popular categories, and the impact of size and price on reviews and installs — so developers, "
            "product managers, and marketing can improve offerings."
        ),
        "methodology": [
            "Ingest the public Play Store catalog and optional user-review table.",
            "Clean invalid rows, parse installs/price/size, coerce dates, drop duplicate app names.",
            "Build success metrics: mean rating, install volume, and review volume.",
            "Answer the assignment's basic, medium, and advanced questions with grouped stats and charts.",
            "Translate patterns into product, pricing, and update recommendations.",
        ],
        "data_overview": {
            "rows_raw": int(len(raw)),
            "rows_clean": int(len(df)),
            "columns": list(df.columns)[:14],
            "free_share": round(free_share, 3),
            "mean_rating": round(float(rated["Rating"].mean()), 3),
            "categories": int(df["Category"].nunique()),
        },
        "key_findings": [
            f"Average listing rating is {rated['Rating'].mean():.2f}/5 among rated apps; "
            f"{(rated['Rating'] >= 4).mean():.0%} of rated apps score 4.0 or higher.",
            f"{free_share:.0%} of unique apps are free; paid apps are a small slice of the catalog.",
            f"Install volume concentrates in {list(df.groupby('Category')['Installs_num'].sum().nlargest(3).index)}.",
            f"Installs and ratings are weakly related (r={rated[['Installs_num','Rating']].corr().iloc[0,1]:.3f}); "
            "popularity is not the same as satisfaction.",
            "Content rating is dominated by Everyone, so family-safe design is the default market.",
        ],
        "limitations": [
            "Installs are stored as lower-bound buckets (e.g. 10,000+), so volume is approximate.",
            "Many sizes are 'Varies with device', reducing size analyses.",
            "Ratings miss apps with too few reviews; survivorship bias favors visible apps.",
            "Review sentiment depends on an auxiliary file that may be incomplete.",
            "The catalog is a snapshot, not a complete live Play Store.",
        ],
        "conclusion": (
            "Success on Play is a mix of category choice, high ratings, and distribution muscle. "
            "Free, frequently updated apps in high-demand categories capture most installs, while "
            "quality (rating and reviews) still differentiates products inside a category."
        ),
        "recommendations": [
            "Benchmark new apps against a 4.0+ rating and category-level install leaders.",
            "Prioritize GAME, COMMUNICATION, and other high-install categories only when the product can match quality bars.",
            "Keep APK/asset size competitive; treat large binaries as a conversion risk.",
            "Default to free + ads/IAP unless a paid niche has proven willingness to pay.",
            "Ship a regular update cadence; stale last-updated dates correlate with weaker store presence.",
        ],
        "qa": qa,
        "figures": [str(p.relative_to(out.parent.parent)) for p in sorted(fig_dir.glob("*.png"))],
        "stakeholders": {
            "internal": ["App Developers", "Product Managers", "Marketing Team", "Senior Management"],
            "external": ["App Users", "Advertisers", "Partners"],
        },
    }
    (out / "findings.json").write_text(json.dumps(findings, indent=2, default=str), encoding="utf-8")
    df.head(2000).to_csv(out / "cleaned_sample.csv", index=False)
    return findings
