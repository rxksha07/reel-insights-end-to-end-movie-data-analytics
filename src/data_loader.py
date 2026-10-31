"""Loading, inspecting, and validating the Reel Insights CSV datasets."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"
DATASET_FILES = {
    "movies": "movies.csv",
    "cast": "cast.csv",
    "crew": "crew.csv",
    "genres": "genres.csv",
    "movie_genres": "movie_genres.csv",
    "movie_keywords": "movie_keywords.csv",
}

PRIMARY_KEYS = {
    "movies": ["movie_id"],
    "cast": ["cast_row_id"],
    "crew": ["crew_row_id"],
    "genres": ["genre_id"],
    "movie_genres": ["movie_id", "genre_id"],
    "movie_keywords": ["movie_id", "keyword_id"],
}

FOREIGN_KEYS = {
    "cast": {"movie_id": ("movies", "movie_id")},
    "crew": {"movie_id": ("movies", "movie_id")},
    "movie_genres": {
        "movie_id": ("movies", "movie_id"),
        "genre_id": ("genres", "genre_id"),
    },
    "movie_keywords": {"movie_id": ("movies", "movie_id")},
}


class DataFileError(FileNotFoundError):
    """Raised when a required raw dataset is missing or cannot be read."""


def load_datasets(
    data_dir: str | Path = RAW_DATA_DIR, *, require_all: bool = False
) -> dict[str, pd.DataFrame]:
    """Load available CSV files, optionally requiring all six datasets."""
    directory = Path(data_dir)
    datasets: dict[str, pd.DataFrame] = {}
    missing: list[str] = []
    for name, filename in DATASET_FILES.items():
        path = directory / filename
        if not path.is_file():
            missing.append(filename)
            continue
        try:
            datasets[name] = pd.read_csv(path, low_memory=False)
        except (OSError, pd.errors.ParserError, UnicodeDecodeError) as exc:
            raise DataFileError(
                f"Could not read {path}. Check that it is a valid CSV file. Details: {exc}"
            ) from exc
    if require_all and missing:
        raise DataFileError(
            f"Missing dataset file(s) in {directory}: {', '.join(missing)}. "
            "Download the original files and place them in data/raw/."
        )
    return datasets


def _key_status(frame: pd.DataFrame, columns: list[str]) -> str:
    if not all(column in frame.columns for column in columns):
        return "not available"
    if frame[columns].isna().any(axis=None):
        return "contains missing key values"
    if frame.duplicated(columns).any():
        return "not unique"
    return "unique in this file"


def inspect_datasets(datasets: dict[str, pd.DataFrame]) -> dict[str, dict[str, Any]]:
    """Return dimensions, schema, missingness, duplicates, and key checks."""
    summary: dict[str, dict[str, Any]] = {}
    for name, frame in datasets.items():
        keys = PRIMARY_KEYS.get(name, [])
        summary[name] = {
            "rows": int(len(frame)),
            "columns": int(len(frame.columns)),
            "column_names": list(frame.columns),
            "dtypes": {column: str(dtype) for column, dtype in frame.dtypes.items()},
            "missing_values": {
                column: int(count)
                for column, count in frame.isna().sum().items()
                if count > 0
            },
            "duplicate_rows": int(frame.duplicated().sum()),
            "primary_key_check": _key_status(frame, keys),
            "sample_records": frame.head(5).where(pd.notna(frame.head(5)), None).to_dict(
                orient="records"
            ),
        }
    return summary


def relationship_checks(
    datasets: dict[str, pd.DataFrame],
) -> list[dict[str, Any]]:
    """Check declared relationships only when both referenced columns exist."""
    results: list[dict[str, Any]] = []
    for child_name, relationships in FOREIGN_KEYS.items():
        if child_name not in datasets:
            continue
        child = datasets[child_name]
        for child_column, (parent_name, parent_column) in relationships.items():
            if (
                child_column not in child.columns
                or parent_name not in datasets
                or parent_column not in datasets[parent_name].columns
            ):
                results.append(
                    {"table": child_name, "column": child_column, "status": "not checked: column/table unavailable"}
                )
                continue
            parent_values = set(datasets[parent_name][parent_column].dropna())
            values = child[child_column].dropna()
            unmatched = int((~values.isin(parent_values)).sum())
            results.append(
                {
                    "table": child_name,
                    "column": child_column,
                    "references": f"{parent_name}.{parent_column}",
                    "non_null_values": int(len(values)),
                    "unmatched_values": unmatched,
                    "status": "verified in this snapshot" if unmatched == 0 else "orphan values found",
                }
            )
    return results


def print_inspection(datasets: dict[str, pd.DataFrame]) -> None:
    """Print an approachable schema and data-quality overview."""
    if not datasets:
        print("No datasets found. Put the six CSV files in data/raw/ and try again.")
        return
    summary = inspect_datasets(datasets)
    for name, details in summary.items():
        print(f"\n{'=' * 72}\n{name}: {details['rows']:,} rows x {details['columns']} columns")
        print("Columns and data types:")
        for column, dtype in details["dtypes"].items():
            print(f"  - {column}: {dtype}")
        print(f"Duplicate rows: {details['duplicate_rows']:,}")
        print(f"Primary key check: {details['primary_key_check']}")
        print("Missing values:", details["missing_values"] or "none")
        print("Sample records:")
        print(pd.DataFrame(details["sample_records"]).to_string(index=False))
    print("\nRelationship checks:")
    for relation in relationship_checks(datasets):
        print(f"  - {relation}")


if __name__ == "__main__":
    try:
        print_inspection(load_datasets())
    except DataFileError as exc:
        print(f"DATA ERROR: {exc}")
        raise SystemExit(1) from exc
