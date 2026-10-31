# Reel Insights: TMDB Global Movie Industry EDA

An end-to-end beginner-friendly data analytics project using six related TMDB CSV datasets: inspection, conservative cleaning, Pandas EDA, 27 SQLite analysis queries, charts, and a Streamlit dashboard.

**By [Rakshatha B](https://github.com/rxksha07) · BCA Graduate | Aspiring Data Scientist**

> Passionate about Python, SQL, Data Analytics, and Machine Learning. Continuously learning, building real-world projects, and transforming data into meaningful insights.

> **Dataset scope:** these supplied files contain a few thousand movie records. They are a sample for analysis, not a complete or statistically representative census of the global movie industry. All numbers and insights are calculated from the files at run time.

## Project contents

```text
Reel_Insights/
├── data/
│   ├── raw/                 # Add the six CSV files here; not included in this public repo
│   └── processed/           # Cleaned CSVs and quality report (generated locally)
├── notebooks/               # Four guided Jupyter notebooks
├── sql/                     # Reference DDL and 27 analysis queries
├── src/                     # Loading, cleaning, analysis, and SQLite modules
├── outputs/
│   ├── charts/              # Generated PNG/HTML charts
│   └── reports/             # Generated EDA report
├── app.py                   # Streamlit interactive dashboard
├── .streamlit/config.toml   # Accessible teal-and-slate theme
├── requirements.txt
└── README.md
```

The six source CSVs were inspected while building and validating the project. Dataset columns are:

| File | Purpose | Key columns |
|---|---|---|
| `movies.csv` | Movie-level attributes | `movie_id`, `title`, `release_date`, `runtime`, `budget`, `revenue`, `vote_average` |
| `cast.csv` | Cast members and characters | `cast_row_id`, `movie_id`, `person_id`, `actor_name` |
| `crew.csv` | Crew members and jobs | `crew_row_id`, `movie_id`, `person_id`, `person_name`, `job` |
| `genres.csv` | Genre lookup values | `genre_id`, `genre_name` |
| `movie_genres.csv` | Movie/genre bridge table | `movie_id`, `genre_id` |
| `movie_keywords.csv` | Movie keyword labels | `movie_id`, `keyword_id`, `keyword_name` |

The primary relationship is `movies.movie_id` to each related table's `movie_id`; `movie_genres.genre_id` refers to `genres.genre_id`. A movie can have many cast/crew/genre/keyword rows. Relationship checks are performed on the current snapshot.

## Requirements and installation (Windows PowerShell)

1. Extract the downloaded archive:

```powershell
Expand-Archive -LiteralPath "$HOME\Downloads\Reel_Insights_Complete_Project.zip" -DestinationPath "$HOME\Desktop" -Force
```

2. Open the extracted project folder in VS Code:

```powershell
Set-Location "$HOME\Desktop\Reel_Insights"
code .
```

If `code` is not recognized, open VS Code and select **File > Open Folder...**.

3. Open the VS Code terminal with **Terminal > New Terminal** (`Ctrl+``).
4. Check installed Python versions, then create and activate a Python 3.13 environment (the version used for validation):

```powershell
py -0p
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If Python 3.13 is not listed, substitute another installed Python 3.12+ version, for example `py -3.12 -m venv .venv`.

If PowerShell blocks activation for this terminal, run this command for the current process only, then activate again:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

5. Install the project requirements and confirm key packages:

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip show pandas numpy matplotlib seaborn plotly streamlit sqlalchemy jupyter
```

In VS Code, choose the `.venv` interpreter when prompted, or open the Command Palette (`Ctrl+Shift+P`) and select **Python: Select Interpreter**.

## Dataset setup and inspection

The public GitHub repository does not include the source CSVs, cleaned copies, SQLite database, or generated data outputs. Download the six original CSVs from the shared links below and save each one in `data/raw/` using the exact filename shown. If a link asks for access, request access from the file owner. Do not commit the data files unless you have permission to redistribute them.

Original shared-file links:

| File | Download link |
|---|---|
| `movies.csv` | <https://drive.google.com/uc?export=download&id=1c_dibUMQxKg07NtjeBOmXkwV6U4BUEa3> |
| `cast.csv` | <https://drive.google.com/uc?export=download&id=1qOc4tKD9wPCf79IcLZNEVwHSc4ZubgXn> |
| `crew.csv` | <https://drive.google.com/uc?export=download&id=1_hqUsES9cTsvErncv0NFjJXbfT33bS4c> |
| `genres.csv` | <https://drive.google.com/uc?export=download&id=19-A18CBKCQS23oqvJIHHQOY-MytwmcJg> |
| `movie_genres.csv` | <https://drive.google.com/uc?export=download&id=1Yd17Xf7Usi2B5QjhVw1KgYXxXGVzL2RD> |
| `movie_keywords.csv` | <https://drive.google.com/uc?export=download&id=13jArnrcqbopWoc4GVFDoRerGm3N6yU0M> |

To re-download all six with PowerShell, run this from the project root:

```powershell
$files = @{
  "movies.csv" = "1c_dibUMQxKg07NtjeBOmXkwV6U4BUEa3"
  "cast.csv" = "1qOc4tKD9wPCf79IcLZNEVwHSc4ZubgXn"
  "crew.csv" = "1_hqUsES9cTsvErncv0NFjJXbfT33bS4c"
  "genres.csv" = "19-A18CBKCQS23oqvJIHHQOY-MytwmcJg"
  "movie_genres.csv" = "1Yd17Xf7Usi2B5QjhVw1KgYXxXGVzL2RD"
  "movie_keywords.csv" = "13jArnrcqbopWoc4GVFDoRerGm3N6yU0M"
}
New-Item -ItemType Directory -Force -Path ".\data\raw" | Out-Null
foreach ($file in $files.GetEnumerator()) {
  $url = "https://drive.google.com/uc?export=download&id=$($file.Value)"
  Invoke-WebRequest -Uri $url -OutFile (Join-Path ".\data\raw" $file.Key)
}
```

```text
data\raw\movies.csv
data\raw\cast.csv
data\raw\crew.csv
data\raw\genres.csv
data\raw\movie_genres.csv
data\raw\movie_keywords.csv
```

Run inspection and cleaning from the project root:

```powershell
python -m src.data_loader
python src\clean_data.py
```

The inspection command above checks files, dimensions, column names/types, samples, missingness, duplicates, and relationship candidates.

The cleaner removes exact duplicate rows only. It retains incomplete rows; invalid numeric/date values are converted to missing values and reported. IQR outliers are flagged for investigation (identifier columns are excluded), never deleted automatically. Processed files and `data_quality_report.json` appear in `data/processed/`.

## SQLite database and SQL

Build/refresh the local SQLite database after cleaning:

```powershell
python src\database.py
```

The database is written to `data\reel_insights.db`. Tables are inferred from actual cleaned CSV headers, with primary keys applied only when the candidate key exists and is unique. Verified relationships are expressed as foreign keys where the corresponding tables/columns are present. SQL examples are in `sql\analysis_queries.sql`.

To analyze manually, open that SQL file or use the dashboard's SQL Query Explorer. The dashboard runs only predefined read-only SELECT/CTE queries against SQLite opened in read-only mode.

## Full project walkthrough: what happens and why

This section explains the project from the original CSVs through the dashboard. Run commands from the `Reel_Insights` project root. The supplied files are a TMDB sample, not a complete census of every movie made worldwide.

### 1. Understand the six tables

The files describe movies and related records. `movies` is the central table; the other files contain multiple records for a movie.

| Table | Rows after cleaning in the current files | How it is used |
|---|---:|---|
| `movies` | 2,503 | One row per movie, including title, release date, runtime, budget, revenue, popularity, and ratings |
| `cast` | 24,902 | Actor and character records; several rows can refer to one movie |
| `crew` | 7,289 | Crew-member and job records; a person can have different jobs or work on several movies |
| `genres` | 19 | Lookup table that translates a genre ID into a readable genre name |
| `movie_genres` | 6,878 | Bridge table connecting movie IDs to genre IDs |
| `movie_keywords` | 41,681 | Keyword records associated with movies |

The key relationships are `movies.movie_id` to `cast.movie_id`, `crew.movie_id`, `movie_genres.movie_id`, and `movie_keywords.movie_id`; and `genres.genre_id` to `movie_genres.genre_id`. Since these are one-to-many or many-to-many relationships, joining multiple child tables at once can multiply rows. Use `COUNT(DISTINCT movie_id)` when the question is about unique movies.

### 2. Inspect the raw files

Run:

```powershell
python -m src.data_loader
```

`src/data_loader.py` reads each available CSV and reports its row and column counts, column names and data types, sample rows, missing values, exact duplicate rows, candidate primary-key checks, and foreign-key matches. It does not silently rename columns to match assumptions. The current snapshot has all six expected tables and no unmatched movie/genre references; it has exact duplicate rows that the cleaning stage reports below.

### 3. Clean conservatively

Run:

```powershell
python src\clean_data.py
```

`src/clean_data.py` applies the same reusable steps every time:

1. Remove exact full-row duplicates only; do not delete records just because some fields are missing.
2. Convert known numeric fields such as `budget`, `revenue`, `runtime`, and ID columns to numeric types where present.
3. Parse known release-date columns where present.
4. Trim surrounding whitespace in text and treat blank text as missing.
5. Convert malformed numeric/date strings to missing values and record how many were affected.
6. Flag numeric IQR outlier candidates (excluding IDs) for review; do not remove them automatically.
7. Save cleaned CSVs and a before/after report in `data/processed/`.

For the files currently supplied, exact duplicate rows removed were: movies 6, cast 15, crew 8, genres 0, movie_genres 10, and movie_keywords 20. The 11 missing `character_name` values in cast are retained; they are not enough reason to discard the cast rows. The resulting quality report is `data/processed/data_quality_report.json`.

### 4. Build and query the SQLite database

Run:

```powershell
python src\database.py
```

`src/database.py` creates or refreshes `data/reel_insights.db` using the cleaned CSVs. It infers SQLite column types from the data and only adds candidate primary keys when the relevant columns exist and are unique. It adds foreign-key constraints only for available relationships. SQLite is local, so no database server is needed.

The query file contains 27 questions. Open `sql/analysis_queries.sql` to read or copy the SQL. The dashboard's SQL Query Explorer runs one predefined read-only query at a time.

1. How many movies are in the table?
2. How many movies have a release date?
3. Which release years have the most records?
4. Which movies have the highest ratings among titles with at least 100 votes?
5. Which movies have the highest recorded revenue?
6. Which movies have the highest recorded budget?
7. Which movies have the longest recorded runtimes?
8. What are the count, average, minimum, and maximum available ratings?
9. What are the average runtime and available budget/revenue totals?
10. How many distinct movies are associated with each genre?
11. What is the average rating for each genre (with a minimum sample size)?
12. Which genres have the highest summed recorded revenue?
13. Which actors appear in the most distinct movies?
14. Which actors have the most top-billed cast records (`cast_order = 0`)?
15. Which directors are associated with the most distinct movies?
16. Which keywords are associated with the most distinct movies?
17. Which movies have the largest cast records?
18. What positive budget/revenue pairs can be used to calculate their relationship?
19. Which movies have the highest estimated revenue minus budget?
20. How does average rating vary by release year?
21. Which original languages occur most often?
22. How many movie records are associated with each status?
23. Which movies rate above the dataset-wide average?
24. Which movies rank in the top three by rating within each release year?
25. Which movies are associated with more than one genre?
26. Which movies have the most keyword records?
27. How do average rating and positive average revenue compare across genres?

The SQL handles revenue and budget as recorded values; zero is excluded from questions that specifically require a positive financial amount. Estimated profit is `revenue - budget`, not accounting profit: it does not include marketing, distribution, taxes, or other costs. Budget/revenue correlation is calculated in Python from positive pairs and is an association, not proof that budget causes revenue.

### 5. Explore with Pandas and NumPy

Run:

```powershell
python src\analyze_data.py
```

`src/analyze_data.py` summarizes table sizes, missingness, duplicates, release-year counts, descriptive statistics for available numeric movie columns, the positive budget/revenue correlation, and genre counts. It saves `outputs/reports/eda_summary.json` and charts in `outputs/charts/`. The matching notebook, `notebooks/03_pandas_analysis.ipynb`, adds explanations beside the code and displays the tables in Jupyter.

Current results from the cleaned files include:

- 2,503 unique movie records.
- Mean recorded rating: about 6.943; this is an average of the available `vote_average` values in this sample.
- Mean recorded runtime: about 114.41 minutes.
- Most frequent genres by distinct movie count: Drama (937), Action (808), Comedy (762), Adventure (674), and Thriller (673). One movie can count toward several genres, so these numbers do not add up to the number of movies.
- Positive budget/revenue Pearson correlation: about 0.678. This describes a moderate positive association in the subset with both values greater than zero; it does not show causation.

Examples of results from the current SQL database:

| Question | Result in the current files |
|---|---|
| Which release year has the most movie records? | 2016, with 121 |
| Highest-rated movie with the query's 100-vote minimum | *The Shawshank Redemption*, 8.727 (30,915 votes) |
| Highest recorded revenue | *Avatar*, 2,923,706,026 |
| Director associated with the most movies | Steven Spielberg, 27 |
| Actor appearing in the most movies | Samuel L. Jackson, 39 |
| Most frequent keyword | `based on novel or book`, on 449 movies |

Use the outputs as a snapshot only. Re-run the scripts after changing the source CSVs; the analysis is recalculated from those files.

### 6. Generate charts

The script creates these static charts with Matplotlib and Seaborn:

- `outputs/charts/movies_by_year.png` — movie records by release year.
- `outputs/charts/genre_distribution.png` — the most common genres.
- `outputs/charts/rating_distribution.png` — the distribution of recorded ratings.

`notebooks/04_visualizations.ipynb` also demonstrates interactive Plotly visualizations, including a genre chart and a positive-budget/positive-revenue scatter plot. Charts describe the supplied sample only. In particular, releases by year should not be read as total historical global production.

### 7. Use the Streamlit dashboard

The application is `app.py`. It loads cleaned CSVs when they exist and otherwise tries the raw CSVs. Its sidebar pages are:

- **Home / Overview** — table sizes, sample scope, and table relationships.
- **Movie Explorer** — search/filter the movie table and inspect a selected record.
- **Analytics Dashboard** — summary metrics, release trend, and financial comparison when the fields are available.
- **Genre Analysis** — genre counts and related movie information.
- **Cast and Crew** — browse actor, character, and crew job records.
- **Keyword Analysis** — inspect frequent keywords and associated titles.
- **Visualizations** — rating, runtime, release-year, and numeric-correlation charts.
- **Data Quality** — table sizes, schema, missing cells, duplicates, and a report download.
- **SQL Query Explorer** — run a selected predefined read-only query from the 27-query library.

Sidebar year and language filters narrow the movie set and related movie tables. Widgets update the page when changed. The query explorer does not accept arbitrary SQL.

### 8. Run the entire project in Windows PowerShell

Open the project folder in VS Code, choose its `.venv` Python interpreter, and open a terminal. Then run:

```powershell
cd "C:\Users\Lakshmi\Desktop\webi\Reel_Insights"
.\.venv\Scripts\Activate.ps1
python -m src.data_loader
python src\clean_data.py
python src\database.py
python src\analyze_data.py
python -m streamlit run app.py
```

When Streamlit prints a **Local URL**, open it in a browser. The default is `http://localhost:8501`. Leave the terminal open while using the app; press **Ctrl+C** in that terminal to stop it. If the port is occupied, start on another port, for example:

```powershell
python -m streamlit run app.py --server.port 8503
```

To run the four notebooks interactively instead, start Jupyter from this same project root:

```powershell
python -m jupyter notebook
```

Then open `notebooks/01_data_cleaning.ipynb`, `02_sql_analysis.ipynb`, `03_pandas_analysis.ipynb`, and `04_visualizations.ipynb` in order. Select the project's `.venv` kernel if VS Code/Jupyter asks for one.

### 9. How to present this project

In a portfolio or interview, describe the flow as: **six related CSVs → schema and relationship checks → conservative cleaning → SQLite tables → SQL and Pandas analysis → charts and interactive dashboard**. Explain that exact duplicates were removed while incomplete records were retained; that joins can multiply movie rows; that financial zeros are treated as unavailable for positive-value comparisons; and that results describe this sample rather than the entire global movie industry. You can demonstrate one SQL join, one analysis chart, and a dashboard filter.

## Run the notebooks and analysis scripts

```powershell
python -m jupyter notebook
```

Open and run notebooks `01_data_cleaning.ipynb` through `04_visualizations.ipynb` in order. To run the reusable Pandas analysis and save report/charts without notebooks:

```powershell
python src\analyze_data.py
```

Charts are written to `outputs\charts\`; the computed summary is written to `outputs\reports\eda_summary.json`.

## Launch the Streamlit dashboard

From the project root and with the virtual environment active:

```powershell
python -m streamlit run app.py
```

Streamlit opens a local browser tab. Use the sidebar to navigate between the project overview, movie explorer, metrics, genre/cast/crew/keyword analysis, charts, data quality, and predefined SQL explorer. The app reports missing/empty data rather than inventing values.

The dashboard uses a light teal-and-slate theme, a filter-aware overview with collection metrics, accessible chart descriptions, a compact dataset inventory, and a direct link to this source repository. The overview also explains that the displayed figures describe the supplied sample rather than the entire global movie industry.

## Troubleshooting

- **Missing CSV:** verify the filename and location in `data\raw\`; run `python -m src.data_loader` for a clear inspection.
- **`ModuleNotFoundError`:** activate `.venv` and run `python -m pip install -r requirements.txt` again.
- **Notebook cannot import `src`:** start Jupyter from the project root using the command above.
- **Execution policy error:** use the process-scoped PowerShell setting in the activation instructions; it is not a permanent system policy change.
- **SQL database/table unavailable:** run `python src\clean_data.py`, then `python src\database.py` from the root.
- **Port already in use:** use `python -m streamlit run app.py --server.port 8502`.
- **Unexpected columns:** inspection reports the actual columns. Dashboard views that need unavailable fields show a message; scripts do not fill unknown values with invented data.
- **Google Drive access denied:** ask the owner for viewer access and download each CSV manually. The included copy is the content obtained from the supplied share links at project creation.

## Interview and portfolio presentation ideas

Explain the table relationships, why duplicate rows were removed but missing records were retained, what columns support each metric, and how you prevented double counting across genres. Demonstrate a SQL join and a dashboard filter. Be explicit that the source files are a supplied sample and discuss possible selection bias, missingness, zero-value financial placeholders, and why correlation does not imply causation.

## What was validated

The six Drive files were downloaded, their headers and row counts were checked, and the project source/notebooks were created for those actual schemas. Before sharing results from a modified copy, rerun the inspection, cleaning, database, notebooks, and Streamlit app against that copy. Dashboard and analysis figures update from the supplied files and are not prewritten claims.
