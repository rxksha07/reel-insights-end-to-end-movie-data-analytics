-- Q01: Count all movies
SELECT COUNT(*) AS movie_count FROM movies;

-- Q02: Number of movies with a release date
SELECT COUNT(*) AS dated_movies FROM movies WHERE release_date IS NOT NULL;

-- Q03: Releases by year
SELECT strftime('%Y', release_date) AS release_year, COUNT(*) AS movie_count
FROM movies WHERE release_date IS NOT NULL
GROUP BY release_year ORDER BY movie_count DESC;

-- Q04: Most highly rated movies (at least 100 votes)
SELECT title, vote_average, vote_count FROM movies
WHERE vote_average IS NOT NULL AND vote_count >= 100
ORDER BY vote_average DESC, vote_count DESC LIMIT 20;

-- Q05: Highest revenue movies
SELECT title, revenue FROM movies
WHERE revenue > 0 ORDER BY revenue DESC LIMIT 20;

-- Q06: Highest budget movies
SELECT title, budget FROM movies
WHERE budget > 0 ORDER BY budget DESC LIMIT 20;

-- Q07: Runtime leaders
SELECT title, runtime FROM movies
WHERE runtime > 0 ORDER BY runtime DESC LIMIT 20;

-- Q08: Rating summary
SELECT COUNT(vote_average) AS rated_movies, AVG(vote_average) AS average_rating,
       MIN(vote_average) AS minimum_rating, MAX(vote_average) AS maximum_rating
FROM movies;

-- Q09: Average runtime and budget/revenue totals
SELECT AVG(runtime) AS average_runtime_minutes, SUM(budget) AS sum_budget,
       SUM(revenue) AS sum_revenue FROM movies;

-- Q10: Genre movie counts
SELECT g.genre_name, COUNT(DISTINCT mg.movie_id) AS movie_count
FROM genres g JOIN movie_genres mg ON g.genre_id = mg.genre_id
GROUP BY g.genre_id, g.genre_name ORDER BY movie_count DESC;

-- Q11: Genre ratings
SELECT g.genre_name, COUNT(DISTINCT m.movie_id) AS rated_movies,
       AVG(m.vote_average) AS average_rating
FROM genres g JOIN movie_genres mg ON g.genre_id = mg.genre_id
JOIN movies m ON m.movie_id = mg.movie_id
WHERE m.vote_average IS NOT NULL
GROUP BY g.genre_id, g.genre_name HAVING COUNT(DISTINCT m.movie_id) >= 3
ORDER BY average_rating DESC;

-- Q12: Genres by summed revenue
SELECT g.genre_name, SUM(m.revenue) AS sum_revenue
FROM genres g JOIN movie_genres mg ON g.genre_id = mg.genre_id
JOIN movies m ON m.movie_id = mg.movie_id
WHERE m.revenue > 0 GROUP BY g.genre_id, g.genre_name
ORDER BY sum_revenue DESC;

-- Q13: Most frequent actors
SELECT actor_name, COUNT(DISTINCT movie_id) AS movie_count
FROM cast WHERE actor_name IS NOT NULL
GROUP BY actor_name ORDER BY movie_count DESC, actor_name LIMIT 20;

-- Q14: Actors associated with the most top-billed roles
SELECT actor_name, COUNT(*) AS top_billed_roles
FROM cast WHERE cast_order = 0 AND actor_name IS NOT NULL
GROUP BY actor_name ORDER BY top_billed_roles DESC LIMIT 20;

-- Q15: Directors with the most movies
SELECT person_name AS director, COUNT(DISTINCT movie_id) AS movie_count
FROM crew WHERE lower(job) = 'director'
GROUP BY person_id, person_name ORDER BY movie_count DESC, director LIMIT 20;

-- Q16: Most frequent keywords
SELECT keyword_name, COUNT(DISTINCT movie_id) AS movie_count
FROM movie_keywords WHERE keyword_name IS NOT NULL
GROUP BY keyword_id, keyword_name ORDER BY movie_count DESC LIMIT 25;

-- Q17: Movies with the largest cast
SELECT m.title, COUNT(c.cast_row_id) AS cast_size
FROM movies m LEFT JOIN cast c ON c.movie_id = m.movie_id
GROUP BY m.movie_id, m.title ORDER BY cast_size DESC LIMIT 20;

-- Q18: Budget and revenue correlation inputs (calculate correlation in Python)
SELECT budget, revenue FROM movies
WHERE budget > 0 AND revenue > 0;

-- Q19: Estimated profit for movies with both positive values
SELECT title, revenue - budget AS estimated_profit, budget, revenue
FROM movies WHERE budget > 0 AND revenue > 0
ORDER BY estimated_profit DESC LIMIT 20;

-- Q20: Average ratings by release year
SELECT strftime('%Y', release_date) AS release_year,
       AVG(vote_average) AS average_rating, COUNT(*) AS rated_movies
FROM movies WHERE release_date IS NOT NULL AND vote_average IS NOT NULL
GROUP BY release_year HAVING COUNT(*) >= 3 ORDER BY release_year;

-- Q21: Languages with the most movies
SELECT original_language, COUNT(*) AS movie_count
FROM movies WHERE original_language IS NOT NULL
GROUP BY original_language ORDER BY movie_count DESC LIMIT 20;

-- Q22: Movie counts by release status
SELECT status, COUNT(*) AS movie_count FROM movies
WHERE status IS NOT NULL GROUP BY status ORDER BY movie_count DESC;

-- Q23: Movies above the dataset average rating
SELECT title, vote_average FROM movies
WHERE vote_average > (SELECT AVG(vote_average) FROM movies)
ORDER BY vote_average DESC LIMIT 25;

-- Q24: Rank movies within their release year by rating (SQLite window function)
WITH rated AS (
    SELECT title, strftime('%Y', release_date) AS release_year, vote_average,
           RANK() OVER (
               PARTITION BY strftime('%Y', release_date)
               ORDER BY vote_average DESC
           ) AS year_rank
    FROM movies WHERE release_date IS NOT NULL AND vote_average IS NOT NULL
)
SELECT release_year, title, vote_average, year_rank FROM rated
WHERE year_rank <= 3 ORDER BY release_year, year_rank;

-- Q25: Movies mapped to more than one genre
SELECT m.title, COUNT(DISTINCT mg.genre_id) AS genre_count
FROM movies m JOIN movie_genres mg ON mg.movie_id = m.movie_id
GROUP BY m.movie_id, m.title HAVING COUNT(DISTINCT mg.genre_id) > 1
ORDER BY genre_count DESC, m.title LIMIT 25;

-- Q26: Films with the most keywords
SELECT m.title, COUNT(mk.keyword_id) AS keyword_count
FROM movies m LEFT JOIN movie_keywords mk ON mk.movie_id = m.movie_id
GROUP BY m.movie_id, m.title ORDER BY keyword_count DESC LIMIT 20;

-- Q27: Genre revenue and ratings together
SELECT g.genre_name, AVG(m.vote_average) AS average_rating,
       AVG(NULLIF(m.revenue, 0)) AS average_positive_revenue,
       COUNT(DISTINCT m.movie_id) AS movie_count
FROM genres g JOIN movie_genres mg ON mg.genre_id = g.genre_id
JOIN movies m ON m.movie_id = mg.movie_id
GROUP BY g.genre_id, g.genre_name
ORDER BY average_positive_revenue DESC;
