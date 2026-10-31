"""SQLite database creation and safe loading of cleaned CSV tables."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd

try:
    from .data_loader import DATASET_FILES, PROJECT_ROOT, PROCESSED_DATA_DIR
except ImportError:
    from data_loader import DATASET_FILES, PROJECT_ROOT, PROCESSED_DATA_DIR

DATABASE_PATH = PROJECT_ROOT / "data" / "reel_insights.db"
PK_CANDIDATES = {
    "movies": ("movie_id",),
    "cast": ("cast_row_id",),
    "crew": ("crew_row_id",),
    "genres": ("genre_id",),
    "movie_genres": ("movie_id", "genre_id"),
    "movie_keywords": ("movie_id", "keyword_id"),
}


def _quote(identifier: str) -> str:
    return '"' + identifier.replace('"', '""') + '"'


def _sqlite_type(series: pd.Series) -> str:
    if pd.api.types.is_integer_dtype(series.dtype):
        return "INTEGER"
    if pd.api.types.is_numeric_dtype(series.dtype):
        return "REAL"
    return "TEXT"


def create_database(
    processed_dir: str | Path = PROCESSED_DATA_DIR,
    database_path: str | Path = DATABASE_PATH,
) -> Path:
    """Create tables from the available cleaned CSV schemas and populate SQLite."""
    data_path, db_path = Path(processed_dir), Path(database_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    frames: dict[str, pd.DataFrame] = {}
    for table, filename in DATASET_FILES.items():
        csv_path = data_path / filename
        if csv_path.is_file():
            frames[table] = pd.read_csv(csv_path, low_memory=False)
    if not frames:
        raise FileNotFoundError(
            f"No processed CSVs found in {data_path}. Run python src\\clean_data.py first."
        )
    with sqlite3.connect(db_path) as connection:
        connection.execute("PRAGMA foreign_keys = ON")
        for table in reversed(DATASET_FILES):
            connection.execute(f"DROP TABLE IF EXISTS {_quote(table)}")
        for table, frame in frames.items():
            if not len(frame.columns):
                raise ValueError(f"{table}.csv has no columns and cannot become a table.")
            if any(not str(column).strip() for column in frame.columns):
                raise ValueError(f"{table}.csv has an empty column name.")
            candidates = PK_CANDIDATES.get(table, ())
            primary_key = tuple(column for column in candidates if column in frame.columns)
            if len(primary_key) != len(candidates) or (
                primary_key and frame.duplicated(list(primary_key)).any()
            ):
                primary_key = ()
            definitions = [
                f"{_quote(str(column))} {_sqlite_type(frame[column])}"
                for column in frame.columns
            ]
            if primary_key:
                definitions.append(
                    "PRIMARY KEY (" + ", ".join(_quote(column) for column in primary_key) + ")"
                )
            foreign_keys = {
                "cast": {"movie_id": ("movies", "movie_id")},
                "crew": {"movie_id": ("movies", "movie_id")},
                "movie_genres": {
                    "movie_id": ("movies", "movie_id"),
                    "genre_id": ("genres", "genre_id"),
                },
                "movie_keywords": {"movie_id": ("movies", "movie_id")},
            }.get(table, {})
            for column, (parent, parent_column) in foreign_keys.items():
                if column in frame.columns and parent in frames and parent_column in frames[parent].columns:
                    definitions.append(
                        f"FOREIGN KEY ({_quote(column)}) REFERENCES "
                        f"{_quote(parent)} ({_quote(parent_column)})"
                    )
            connection.execute(
                f"CREATE TABLE {_quote(table)} ({', '.join(definitions)})"
            )
            if not frame.empty:
                columns = ", ".join(_quote(str(column)) for column in frame.columns)
                placeholders = ", ".join("?" for _ in frame.columns)
                connection.executemany(
                    f"INSERT INTO {_quote(table)} ({columns}) VALUES ({placeholders})",
                    frame.astype(object).where(pd.notna(frame), None).itertuples(
                        index=False, name=None
                    ),
                )
        connection.commit()
    print(f"SQLite database ready: {db_path}")
    print("Tables loaded: " + ", ".join(frames))
    return db_path


if __name__ == "__main__":
    try:
        create_database()
    except (OSError, sqlite3.Error, ValueError) as exc:
        print(f"DATABASE ERROR: {exc}")
        raise SystemExit(1) from exc
