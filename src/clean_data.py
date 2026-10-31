"""Repeatable, conservative cleaning pipeline for all available raw CSV files."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

try:
    from .data_loader import (
        DATASET_FILES,
        PROCESSED_DATA_DIR,
        RAW_DATA_DIR,
        DataFileError,
        inspect_datasets,
        load_datasets,
        relationship_checks,
    )
except ImportError:
    from data_loader import (
        DATASET_FILES,
        PROCESSED_DATA_DIR,
        RAW_DATA_DIR,
        DataFileError,
        inspect_datasets,
        load_datasets,
        relationship_checks,
    )

NUMERIC_COLUMNS = {
    "runtime", "budget", "revenue", "popularity", "vote_average", "vote_count",
    "cast_order", "movie_id", "genre_id", "person_id", "keyword_id", "cast_row_id",
    "crew_row_id",
}
DATE_COLUMNS = {"release_date", "release date"}


def clean_frame(frame: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, object]]:
    """Clean obvious formatting/type issues without dropping incomplete records."""
    cleaned = frame.copy()
    before_rows = len(cleaned)
    duplicate_rows = int(cleaned.duplicated().sum())
    cleaned = cleaned.drop_duplicates().copy()
    converted_numeric: list[str] = []
    converted_dates: list[str] = []
    invalid_numeric: dict[str, int] = {}
    invalid_dates: dict[str, int] = {}
    for column in cleaned.columns:
        normalized = str(column).strip().lower()
        if normalized in NUMERIC_COLUMNS:
            original_non_null = cleaned[column].notna()
            converted = pd.to_numeric(cleaned[column], errors="coerce")
            invalid = int((original_non_null & converted.isna()).sum())
            if invalid:
                invalid_numeric[column] = invalid
            cleaned[column] = converted
            converted_numeric.append(column)
        elif normalized in DATE_COLUMNS:
            original_non_null = cleaned[column].notna()
            converted = pd.to_datetime(cleaned[column], errors="coerce")
            invalid = int((original_non_null & converted.isna()).sum())
            if invalid:
                invalid_dates[column] = invalid
            cleaned[column] = converted
            converted_dates.append(column)
        elif pd.api.types.is_object_dtype(cleaned[column]):
            values = cleaned[column].astype("string").str.strip()
            cleaned[column] = values.replace("", pd.NA)

    quality: dict[str, object] = {
        "rows_before": int(before_rows),
        "rows_after": int(len(cleaned)),
        "exact_duplicate_rows_removed": duplicate_rows,
        "rows_with_any_missing_values_before": int(frame.isna().any(axis=1).sum()),
        "rows_with_any_missing_values_after": int(cleaned.isna().any(axis=1).sum()),
        "missing_values_after": {c: int(n) for c, n in cleaned.isna().sum().items() if n},
        "numeric_columns_converted": converted_numeric,
        "date_columns_converted": converted_dates,
        "invalid_numeric_values_coerced_to_missing": invalid_numeric,
        "invalid_dates_coerced_to_missing": invalid_dates,
        "numeric_outlier_candidates_iqr": {},
        "note": (
            "Only exact duplicate rows were removed. Incomplete rows were retained. "
            "IQR outliers are reported for investigation, never automatically deleted."
        ),
    }
    for column in cleaned.select_dtypes(include="number").columns:
        if str(column).strip().lower() == "id" or str(column).strip().lower().endswith("_id"):
            continue
        values = cleaned[column].dropna()
        if len(values) >= 4:
            q1, q3 = values.quantile([0.25, 0.75])
            lower, upper = q1 - 1.5 * (q3 - q1), q3 + 1.5 * (q3 - q1)
            quality["numeric_outlier_candidates_iqr"][column] = int(  # type: ignore[index]
                ((values < lower) | (values > upper)).sum()
            )
    return cleaned, quality


def clean_all(
    raw_dir: str | Path = RAW_DATA_DIR,
    output_dir: str | Path = PROCESSED_DATA_DIR,
    *,
    require_all: bool = False,
) -> dict[str, pd.DataFrame]:
    """Clean each available table and save it with per-table data-quality reports."""
    raw_path, output_path = Path(raw_dir), Path(output_dir)
    datasets = load_datasets(raw_path, require_all=require_all)
    if not datasets:
        raise DataFileError(f"No CSV datasets were found in {raw_path}.")
    output_path.mkdir(parents=True, exist_ok=True)
    cleaned_data: dict[str, pd.DataFrame] = {}
    quality_report: dict[str, object] = {
        "source_directory": str(raw_path),
        "output_directory": str(output_path),
        "tables": {},
        "relationships_after_cleaning": [],
    }
    for name, frame in datasets.items():
        cleaned, table_report = clean_frame(frame)
        cleaned.to_csv(output_path / DATASET_FILES[name], index=False)
        cleaned_data[name] = cleaned
        quality_report["tables"][name] = table_report  # type: ignore[index]
        print(
            f"{name}: {len(frame):,} -> {len(cleaned):,} rows; "
            f"removed {table_report['exact_duplicate_rows_removed']} exact duplicates"
        )
    quality_report["relationships_after_cleaning"] = relationship_checks(cleaned_data)
    quality_report["input_summary"] = inspect_datasets(datasets)
    with (output_path / "data_quality_report.json").open("w", encoding="utf-8") as report_file:
        json.dump(quality_report, report_file, indent=2, default=str)
    print(f"\nCleaned files and report saved to: {output_path}")
    return cleaned_data


if __name__ == "__main__":
    try:
        clean_all(require_all=False)
    except (DataFileError, OSError, ValueError) as exc:
        print(f"CLEANING ERROR: {exc}")
        raise SystemExit(1) from exc
