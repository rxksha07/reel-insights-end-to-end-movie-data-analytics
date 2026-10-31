-- SQLite reference schema for the inspected TMDB CSV files.
-- The Python loader infers these same tables from the CSV headers and only
-- applies a primary key when the key columns are present and unique.
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS movies (
    movie_id INTEGER PRIMARY KEY,
    title TEXT,
    original_language TEXT,
    release_date TEXT,
    runtime REAL,
    budget REAL,
    revenue REAL,
    popularity REAL,
    vote_average REAL,
    vote_count INTEGER,
    status TEXT,
    overview TEXT
);

CREATE TABLE IF NOT EXISTS genres (
    genre_id INTEGER PRIMARY KEY,
    genre_name TEXT
);

CREATE TABLE IF NOT EXISTS cast (
    cast_row_id INTEGER PRIMARY KEY,
    movie_id INTEGER,
    person_id INTEGER,
    actor_name TEXT,
    character_name TEXT,
    cast_order INTEGER,
    FOREIGN KEY (movie_id) REFERENCES movies(movie_id)
);

CREATE TABLE IF NOT EXISTS crew (
    crew_row_id INTEGER PRIMARY KEY,
    movie_id INTEGER,
    person_id INTEGER,
    person_name TEXT,
    job TEXT,
    department TEXT,
    FOREIGN KEY (movie_id) REFERENCES movies(movie_id)
);

CREATE TABLE IF NOT EXISTS movie_genres (
    movie_id INTEGER,
    genre_id INTEGER,
    PRIMARY KEY (movie_id, genre_id),
    FOREIGN KEY (movie_id) REFERENCES movies(movie_id),
    FOREIGN KEY (genre_id) REFERENCES genres(genre_id)
);

CREATE TABLE IF NOT EXISTS movie_keywords (
    movie_id INTEGER,
    keyword_id INTEGER,
    keyword_name TEXT,
    PRIMARY KEY (movie_id, keyword_id),
    FOREIGN KEY (movie_id) REFERENCES movies(movie_id)
);
