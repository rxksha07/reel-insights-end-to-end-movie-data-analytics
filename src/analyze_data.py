"""Pandas EDA summaries and charts that adapt to columns found in the data."""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

try:
    from .data_loader import PROJECT_ROOT, PROCESSED_DATA_DIR, load_datasets, DATASET_FILES
except ImportError:
    from data_loader import PROJECT_ROOT, PROCESSED_DATA_DIR, load_datasets, DATASET_FILES

OUTPUT_DIR = PROJECT_ROOT / "outputs"
CHART_DIR = OUTPUT_DIR / "charts"
REPORT_DIR = OUTPUT_DIR / "reports"


def _load_processed() -> dict[str, pd.DataFrame]:
    datasets = load_datasets(PROCESSED_DATA_DIR)
    if datasets:
        return datasets
    return load_datasets(PROJECT_ROOT / "data" / "raw")


def build_summary(datasets: dict[str, pd.DataFrame]) -> dict[str, object]:
    """Calculate descriptive summaries only where expected fields exist."""
    report: dict[str, object] = {"dataset_dimensions": {}, "analyses": {}}
    for name, frame in datasets.items():
        report["dataset_dimensions"][name] = {
            "rows": int(len(frame)),
            "columns": int(len(frame.columns)),
            "missing_cells": int(frame.isna().sum().sum()),
            "duplicate_rows": int(frame.duplicated().sum()),
        }  # type: ignore[index]
    movies = datasets.get("movies", pd.DataFrame())
    analyses = report["analyses"]
    if "movie_id" in movies:
        analyses["movie_count"] = int(movies["movie_id"].nunique())  # type: ignore[index]
    if "release_date" in movies:
        dates = pd.to_datetime(movies["release_date"], errors="coerce")
        years = dates.dt.year.value_counts().sort_index()
        analyses["releases_by_year"] = {str(int(k)): int(v) for k, v in years.items()}  # type: ignore[index]
    for column in ("vote_average", "runtime", "budget", "revenue", "popularity"):
        if column in movies:
            numeric = pd.to_numeric(movies[column], errors="coerce")
            analyses[f"{column}_describe"] = {  # type: ignore[index]
                key: float(value) for key, value in numeric.describe().items()
            }
    if {"budget", "revenue"}.issubset(movies.columns):
        budget = pd.to_numeric(movies["budget"], errors="coerce")
        revenue = pd.to_numeric(movies["revenue"], errors="coerce")
        valid = budget.notna() & revenue.notna() & (budget > 0) & (revenue > 0)
        if valid.sum() >= 2:
            analyses["budget_revenue_correlation"] = float(  # type: ignore[index]
                budget[valid].corr(revenue[valid])
            )
    if {"movie_id", "genre_id"}.issubset(datasets.get("movie_genres", pd.DataFrame()).columns):
        links = datasets["movie_genres"].merge(
            datasets.get("genres", pd.DataFrame()), on="genre_id", how="left"
        )
        label = "genre_name" if "genre_name" in links else "genre_id"
        analyses["genre_counts"] = {  # type: ignore[index]
            str(key): int(value) for key, value in links[label].value_counts().items()
        }
    return report


def generate_charts(datasets: dict[str, pd.DataFrame]) -> list[Path]:
    """Create and save charts only when the required source columns are present."""
    CHART_DIR.mkdir(parents=True, exist_ok=True)
    sns.set_theme(style="whitegrid")
    generated: list[Path] = []
    movies = datasets.get("movies", pd.DataFrame())
    if "release_date" in movies:
        years = pd.to_datetime(movies["release_date"], errors="coerce").dt.year.dropna()
        if not years.empty:
            counts = years.value_counts().sort_index()
            fig, ax = plt.subplots(figsize=(11, 5))
            sns.lineplot(x=counts.index, y=counts.values, marker="o", ax=ax)
            ax.set(title="Movies by Release Year", xlabel="Release year", ylabel="Movies")
            fig.tight_layout()
            target = CHART_DIR / "movies_by_year.png"
            fig.savefig(target, dpi=150)
            plt.close(fig)
            generated.append(target)
    genre_links = datasets.get("movie_genres", pd.DataFrame())
    if "genre_id" in genre_links and "genre_id" in datasets.get("genres", pd.DataFrame()):
        counts = genre_links.merge(datasets["genres"], on="genre_id", how="left")
        label = "genre_name" if "genre_name" in counts else "genre_id"
        counts = counts[label].value_counts().head(15).sort_values()
        if not counts.empty:
            fig, ax = plt.subplots(figsize=(9, 6))
            counts.plot(kind="barh", ax=ax, color="#3977a8")
            ax.set(title="Most Frequent Genres", xlabel="Movie-genre links", ylabel="Genre")
            fig.tight_layout()
            target = CHART_DIR / "genre_distribution.png"
            fig.savefig(target, dpi=150)
            plt.close(fig)
            generated.append(target)
    if "vote_average" in movies:
        ratings = pd.to_numeric(movies["vote_average"], errors="coerce").dropna()
        if not ratings.empty:
            fig, ax = plt.subplots(figsize=(9, 5))
            sns.histplot(ratings, bins=20, kde=True, ax=ax, color="#4c9b77")
            ax.set(title="Movie Rating Distribution", xlabel="Average vote", ylabel="Movies")
            fig.tight_layout()
            target = CHART_DIR / "rating_distribution.png"
            fig.savefig(target, dpi=150)
            plt.close(fig)
            generated.append(target)
    return generated


def run_analysis() -> dict[str, object]:
    datasets = _load_processed()
    if not datasets:
        raise FileNotFoundError(
            f"No datasets found. Add the six CSVs to {PROJECT_ROOT / 'data' / 'raw'}."
        )
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    report = build_summary(datasets)
    generated_charts = generate_charts(datasets)
    report["charts_saved"] = [str(path.relative_to(PROJECT_ROOT)) for path in generated_charts]
    report_path = REPORT_DIR / "eda_summary.json"
    report_path.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    print(json.dumps(report, indent=2, default=str))
    print(f"\nReport saved to {report_path}")
    print(f"Charts saved: {len(generated_charts)}")
    return report


if __name__ == "__main__":
    try:
        run_analysis()
    except (OSError, ValueError, KeyError) as exc:
        print(f"ANALYSIS ERROR: {exc}")
        raise SystemExit(1) from exc
