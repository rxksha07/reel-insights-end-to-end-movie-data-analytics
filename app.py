"""Interactive Streamlit dashboard for the Reel Insights TMDB project."""

from __future__ import annotations

import re
import sqlite3
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from src.data_loader import DATASET_FILES, PROJECT_ROOT, PROCESSED_DATA_DIR, load_datasets
from src.database import DATABASE_PATH

st.set_page_config(page_title="Reel Insights | TMDB", page_icon="🎬", layout="wide")

PAGES = [
    "Home / Overview",
    "Movie Explorer",
    "Analytics Dashboard",
    "Genre Analysis",
    "Cast and Crew",
    "Keyword Analysis",
    "Visualizations",
    "Data Quality",
    "SQL Query Explorer",
]


@st.cache_data(show_spinner="Loading movie datasets...")
def get_datasets() -> dict[str, pd.DataFrame]:
    """Load cleaned datasets when present, otherwise use the original CSVs."""
    cleaned = load_datasets(PROCESSED_DATA_DIR)
    return cleaned if cleaned else load_datasets(PROJECT_ROOT / "data" / "raw")


def _available_message(label: str) -> None:
    st.info(f"{label} is not available in the current files or does not contain the required columns.")


def _show_movie_table(frame: pd.DataFrame, columns: list[str] | None = None) -> None:
    if frame.empty:
        st.info("No records match the current filters.")
        return
    display = frame if columns is None else frame[[c for c in columns if c in frame.columns]]
    st.dataframe(display, width="stretch", hide_index=True)


def page_home(data: dict[str, pd.DataFrame]) -> None:
    st.title("🎬 Reel Insights")
    st.subheader("An End-to-End Exploratory Data Analysis of the Global Movie Industry")
    st.write(
        "Explore the supplied TMDB movie, cast, crew, genre, and keyword tables. "
        "All metrics are calculated from the files you provide; this sample should not be treated as a complete census."
    )
    overview = []
    for name, frame in data.items():
        overview.append({"Dataset": DATASET_FILES[name], "Rows": len(frame), "Columns": len(frame.columns)})
    st.markdown("#### Dataset overview")
    _show_movie_table(pd.DataFrame(overview))
    total_movies = data.get("movies", pd.DataFrame())
    if "movie_id" in total_movies:
        st.metric("Unique movie records", f"{total_movies['movie_id'].nunique():,}")
    st.markdown("#### Dataset relationships")
    st.markdown(
        "- `movies.movie_id` links movies to cast, crew, genres, and keywords.\n"
        "- `movie_genres.genre_id` links to `genres.genre_id`.\n"
        "- Cast/crew and genres are one-to-many or many-to-many relationships; joins can repeat movie rows."
    )
    st.markdown("#### Technologies")
    st.write("Python · Pandas · NumPy · SQLite · SQL · Streamlit · Plotly · Matplotlib · Seaborn")
    if not data:
        st.warning("No CSV files were found. Add the six original files to `data/raw/` and reload this page.")


def page_explorer(data: dict[str, pd.DataFrame]) -> None:
    st.title("Movie Explorer")
    movies = data.get("movies", pd.DataFrame())
    if movies.empty:
        _available_message("Movie explorer")
        return
    filtered = movies.copy()
    if "title" in filtered:
        search = st.text_input("Search title", placeholder="Enter part of a title")
        if search.strip():
            filtered = filtered[filtered["title"].astype("string").str.contains(search, case=False, na=False)]
    year_column = next((c for c in ("release_date", "release_year") if c in filtered), None)
    if year_column:
        years = (
            pd.to_datetime(filtered[year_column], errors="coerce").dt.year
            if year_column == "release_date"
            else pd.to_numeric(filtered[year_column], errors="coerce")
        )
        available_years = sorted(int(y) for y in years.dropna().unique())
        if available_years:
            selected_years = st.slider(
                "Release year range",
                min_value=min(available_years),
                max_value=max(available_years),
                value=(min(available_years), max(available_years)),
            )
            filtered = filtered[years.between(*selected_years)]
    for column, label in (("original_language", "Original language"), ("status", "Status")):
        if column in filtered:
            options = sorted(filtered[column].dropna().astype(str).unique())
            selected = st.multiselect(label, options, default=[])
            if selected:
                filtered = filtered[filtered[column].astype(str).isin(selected)]
    rating_col = next((c for c in ("vote_average", "rating", "imdb_rating") if c in filtered), None)
    if rating_col:
        rating = pd.to_numeric(filtered[rating_col], errors="coerce")
        limits = rating.dropna()
        if not limits.empty and limits.min() < limits.max():
            rating_range = st.slider(
                "Rating range",
                float(limits.min()),
                float(limits.max()),
                (float(limits.min()), float(limits.max())),
            )
            filtered = filtered[rating.between(*rating_range)]
    genres = data.get("movie_genres", pd.DataFrame())
    genre_names = data.get("genres", pd.DataFrame())
    if {"movie_id", "genre_id"}.issubset(genres.columns) and "genre_name" in genre_names:
        available = sorted(genre_names["genre_name"].dropna().astype(str).unique())
        selected_genres = st.multiselect("Genre", available, default=[])
        if selected_genres:
            selected_ids = genre_names.loc[
                genre_names["genre_name"].astype(str).isin(selected_genres), "genre_id"
            ]
            movie_ids = genres.loc[genres["genre_id"].isin(selected_ids), "movie_id"]
            filtered = filtered[filtered["movie_id"].isin(movie_ids)]
    st.caption(f"{len(filtered):,} matching movie record(s)")
    _show_movie_table(filtered)
    if not filtered.empty and "title" in filtered:
        selected_title = st.selectbox("Explore a movie", filtered["title"].dropna().astype(str).unique())
        selected_movie = filtered[filtered["title"].astype(str) == selected_title].iloc[0]
        st.json(selected_movie.to_dict())


def page_analytics(data: dict[str, pd.DataFrame]) -> None:
    st.title("Analytics Dashboard")
    movies = data.get("movies", pd.DataFrame())
    if movies.empty:
        _available_message("Analytics dashboard")
        return
    kpis = []
    kpis.append(("Movies", f"{movies['movie_id'].nunique():,}" if "movie_id" in movies else f"{len(movies):,}"))
    for column, label, formatter in (
        ("vote_average", "Average rating", "{:.2f}"),
        ("revenue", "Average positive revenue", "${:,.0f}"),
        ("runtime", "Average runtime (min)", "{:.0f}"),
    ):
        if column in movies:
            series = pd.to_numeric(movies[column], errors="coerce").dropna()
            if column == "revenue":
                series = series[series > 0]
            if not series.empty:
                kpis.append((label, formatter.format(series.mean())))
    metric_cols = st.columns(len(kpis))
    for column, (label, value) in zip(metric_cols, kpis):
        column.metric(label, value)
    if "release_date" in movies:
        years = pd.to_datetime(movies["release_date"], errors="coerce").dt.year
        counts = years.value_counts().sort_index().rename_axis("Release year").rename("Movies").reset_index()
        st.plotly_chart(px.line(counts, x="Release year", y="Movies", markers=True, title="Movie releases by year"), width="stretch")
    if {"budget", "revenue"}.issubset(movies.columns):
        chart_data = movies.copy()
        chart_data[["budget", "revenue"]] = chart_data[["budget", "revenue"]].apply(pd.to_numeric, errors="coerce")
        chart_data = chart_data[(chart_data["budget"] > 0) & (chart_data["revenue"] > 0)]
        if not chart_data.empty:
            st.plotly_chart(
                px.scatter(chart_data, x="budget", y="revenue", hover_name="title" if "title" in chart_data else None,
                           log_x=True, log_y=True, title="Budget vs. revenue (positive values)"),
                width="stretch",
            )


def page_genres(data: dict[str, pd.DataFrame]) -> None:
    st.title("Genre Analysis")
    links, genres, movies = (
        data.get("movie_genres", pd.DataFrame()),
        data.get("genres", pd.DataFrame()),
        data.get("movies", pd.DataFrame()),
    )
    if not {"movie_id", "genre_id"}.issubset(links.columns) or not {"genre_id", "genre_name"}.issubset(genres.columns):
        _available_message("Genre analysis")
        return
    joined = links.merge(genres, on="genre_id", how="left")
    counts = joined.groupby("genre_name", dropna=False)["movie_id"].nunique().sort_values(ascending=False)
    counts_frame = counts.rename("Unique movies").reset_index()
    st.plotly_chart(px.bar(counts_frame, x="genre_name", y="Unique movies", title="Unique movie count by genre"), width="stretch")
    if {"movie_id", "vote_average"}.issubset(movies.columns):
        rated = joined.merge(movies[["movie_id", "vote_average"]], on="movie_id", how="left")
        rated["vote_average"] = pd.to_numeric(rated["vote_average"], errors="coerce")
        averages = rated.groupby("genre_name")["vote_average"].agg(["mean", "count"]).reset_index()
        averages = averages[averages["count"] >= 3].sort_values("mean", ascending=False)
        if not averages.empty:
            st.plotly_chart(px.bar(averages, x="genre_name", y="mean", title="Average rating by genre (3+ rated movies)"), width="stretch")
    st.dataframe(counts_frame, width="stretch", hide_index=True)


def page_cast_crew(data: dict[str, pd.DataFrame]) -> None:
    st.title("Cast and Crew")
    cast = data.get("cast", pd.DataFrame())
    crew = data.get("crew", pd.DataFrame())
    if "actor_name" in cast:
        st.subheader("Frequently appearing actors")
        actors = cast.groupby("actor_name")["movie_id"].nunique().sort_values(ascending=False).head(20)
        st.dataframe(actors.rename("Movies").rename_axis("Actor").reset_index(), width="stretch", hide_index=True)
        actor = st.selectbox("Find an actor", sorted(cast["actor_name"].dropna().astype(str).unique()))
        st.dataframe(cast[cast["actor_name"].astype(str) == actor], width="stretch", hide_index=True)
    else:
        _available_message("Cast exploration")
    if {"person_name", "job"}.issubset(crew.columns):
        directors = crew[crew["job"].astype("string").str.casefold().eq("director")]
        st.subheader("Directors with most movies")
        st.dataframe(
            directors.groupby("person_name")["movie_id"].nunique().sort_values(ascending=False)
            .head(20).rename("Movies").rename_axis("Director").reset_index(),
            width="stretch", hide_index=True,
        )
    else:
        _available_message("Crew/director analysis")


def page_keywords(data: dict[str, pd.DataFrame]) -> None:
    st.title("Keyword Analysis")
    keywords, movies = data.get("movie_keywords", pd.DataFrame()), data.get("movies", pd.DataFrame())
    if not {"keyword_name", "movie_id"}.issubset(keywords.columns):
        _available_message("Keyword analysis")
        return
    counts = keywords.groupby("keyword_name")["movie_id"].nunique().sort_values(ascending=False).head(30)
    st.plotly_chart(px.bar(counts.sort_values().reset_index(), x="keyword_name", y="movie_id", title="Most common keywords"), width="stretch")
    st.dataframe(counts.rename("Movies").rename_axis("Keyword").reset_index(), width="stretch", hide_index=True)
    search = st.text_input("Search keyword")
    if search:
        matching = keywords[keywords["keyword_name"].astype("string").str.contains(search, case=False, na=False)]
        if "movie_id" in movies and "title" in movies:
            matching = matching.merge(movies[["movie_id", "title"]], on="movie_id", how="left")
        st.dataframe(matching, width="stretch", hide_index=True)


def page_visuals(data: dict[str, pd.DataFrame]) -> None:
    st.title("Visualizations")
    movies = data.get("movies", pd.DataFrame())
    if "vote_average" in movies:
        values = pd.to_numeric(movies["vote_average"], errors="coerce").dropna()
        if not values.empty:
            st.plotly_chart(px.histogram(values, nbins=25, title="Rating distribution", labels={"value": "Average vote", "count": "Movies"}), width="stretch")
    if "runtime" in movies:
        runtime = pd.to_numeric(movies["runtime"], errors="coerce").dropna()
        runtime = runtime[runtime > 0]
        if not runtime.empty:
            st.plotly_chart(px.histogram(runtime, nbins=30, title="Runtime distribution", labels={"value": "Runtime (minutes)", "count": "Movies"}), width="stretch")
    if "release_date" in movies:
        years = pd.to_datetime(movies["release_date"], errors="coerce").dt.year.dropna()
        if not years.empty:
            trend = years.value_counts().sort_index().rename_axis("Year").rename("Movies").reset_index()
            st.plotly_chart(px.line(trend, x="Year", y="Movies", markers=True, title="Releases by year"), width="stretch")
    numeric = movies.select_dtypes(include="number")
    if len(numeric.columns) >= 2:
        corr = numeric.corr(min_periods=3)
        st.plotly_chart(px.imshow(corr, text_auto=".2f", title="Numeric correlation matrix", color_continuous_scale="RdBu_r", zmin=-1, zmax=1), width="stretch")
    if not any(column in movies for column in ("vote_average", "runtime", "release_date")):
        _available_message("Movie visualizations")


def page_quality(data: dict[str, pd.DataFrame]) -> None:
    st.title("Data Quality")
    if not data:
        _available_message("Data quality report")
        st.caption("Copy the real CSV files into data/raw/ and reload.")
        return
    summaries = []
    for name, frame in data.items():
        summaries.append({
            "Dataset": DATASET_FILES[name],
            "Rows": len(frame),
            "Columns": len(frame.columns),
            "Missing cells": int(frame.isna().sum().sum()),
            "Duplicate rows": int(frame.duplicated().sum()),
        })
        with st.expander(f"{name}: schema and missing values"):
            schema = pd.DataFrame({
                "Column": frame.columns,
                "Data type": [str(dtype) for dtype in frame.dtypes],
                "Missing": [int(frame[c].isna().sum()) for c in frame.columns],
            })
            st.dataframe(schema, width="stretch", hide_index=True)
    st.dataframe(pd.DataFrame(summaries), width="stretch", hide_index=True)
    report_path = PROCESSED_DATA_DIR / "data_quality_report.json"
    if report_path.exists():
        st.download_button("Download cleaning quality report", report_path.read_bytes(), file_name=report_path.name, mime="application/json")
    else:
        st.caption("Run `python src\\clean_data.py` to save the detailed before/after report.")


def _read_queries() -> list[tuple[str, str]]:
    path = PROJECT_ROOT / "sql" / "analysis_queries.sql"
    if not path.is_file():
        return []
    text = path.read_text(encoding="utf-8")
    sections = re.split(r"(?m)^-- (Q\d+: .+)$", text)
    queries: list[tuple[str, str]] = []
    for index in range(1, len(sections), 2):
        title = sections[index]
        statement = sections[index + 1].split(";", 1)[0].strip()
        if statement:
            queries.append((title, statement))
    return queries


def page_sql() -> None:
    st.title("SQL Query Explorer")
    st.write("Choose from the project's predefined, read-only analytical queries. Arbitrary SQL is not accepted.")
    queries = _read_queries()
    if not queries:
        _available_message("SQL query library")
        return
    if not DATABASE_PATH.is_file():
        st.warning("The SQLite database has not been created yet. Run the cleaning and database commands in README.md.")
        return
    title = st.selectbox("Predefined query", [item[0] for item in queries])
    if st.button("Run selected query", type="primary"):
        statement = next(query for query_title, query in queries if query_title == title)
        first_word = statement.lstrip().split(None, 1)[0].lower()
        if first_word not in {"select", "with"} or ";" in statement:
            st.error("This query is not a single read-only SELECT/CTE statement.")
            return
        try:
            uri = f"file:{DATABASE_PATH.as_posix()}?mode=ro"
            with sqlite3.connect(uri, uri=True) as connection:
                result = pd.read_sql_query(statement, connection)
            st.dataframe(result, width="stretch", hide_index=True)
        except (sqlite3.Error, pd.errors.DatabaseError) as exc:
            st.error(f"Query could not run. Build or refresh the database first. Details: {exc}")


def main() -> None:
    try:
        data = get_datasets()
    except (OSError, pd.errors.ParserError, UnicodeDecodeError) as exc:
        st.error(f"Unable to load datasets: {exc}")
        st.stop()
    with st.sidebar:
        st.title("Reel Insights")
        page = st.radio("Navigate", PAGES)
        st.caption("Global filters")
        filtered_data = dict(data)
        movies = data.get("movies", pd.DataFrame())
        if "movie_id" in movies:
            filtered_movies = movies.copy()
            if "release_date" in movies:
                years = pd.to_datetime(movies["release_date"], errors="coerce").dt.year
                available_years = sorted(int(year) for year in years.dropna().unique())
                if available_years and available_years[0] < available_years[-1]:
                    selected_years = st.slider(
                        "Release year",
                        min_value=available_years[0],
                        max_value=available_years[-1],
                        value=(available_years[0], available_years[-1]),
                    )
                    filtered_movies = filtered_movies.loc[years.between(*selected_years)]
            if "original_language" in filtered_movies:
                languages = sorted(filtered_movies["original_language"].dropna().astype(str).unique())
                selected_languages = st.multiselect("Original language", languages)
                if selected_languages:
                    filtered_movies = filtered_movies[
                        filtered_movies["original_language"].astype(str).isin(selected_languages)
                    ]
            movie_ids = set(filtered_movies["movie_id"].dropna())
            filtered_data["movies"] = filtered_movies
            for table_name in ("cast", "crew", "movie_genres", "movie_keywords"):
                table = data.get(table_name)
                if table is not None and "movie_id" in table:
                    filtered_data[table_name] = table[table["movie_id"].isin(movie_ids)]
        st.caption("Data source: cleaned CSVs if available; otherwise raw CSVs.")
    if page == PAGES[0]:
        page_home(filtered_data)
    elif page == PAGES[1]:
        page_explorer(filtered_data)
    elif page == PAGES[2]:
        page_analytics(filtered_data)
    elif page == PAGES[3]:
        page_genres(filtered_data)
    elif page == PAGES[4]:
        page_cast_crew(filtered_data)
    elif page == PAGES[5]:
        page_keywords(filtered_data)
    elif page == PAGES[6]:
        page_visuals(filtered_data)
    elif page == PAGES[7]:
        page_quality(filtered_data)
    else:
        page_sql()


if __name__ == "__main__":
    main()
