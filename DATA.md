# Dataset

## anime
This dataset contains information about animes.

- `MAL_ID`: Unique anime identifier (integer)
- `Name`: Name of the anime (string)

## animelist
This dataset contains user-specific anime ratings and progress information.

- `user_id`: Unique user identifier (integer)
- `anime_id`: Unique anime identifier (integer)
- `rating`: Rating given by the user for the anime (float)
- `watching_status`: Current status of the anime (e.g., "Watching", "Completed", "On Hold", "Dropped") (string)
- `watched_episodes`: The number of episodes the user has watched (integer)

## anime_with_synopsis
This dataset contains additional information about the anime, including a short synopsis.

- `MAL_ID`: Unique anime identifier (integer)
- `Name`: Title of the anime (string)
- `Scores`: Overall rating of the anime (float)
- `Genres`: The genre(s) of the anime (string)
- `synopsis`: A brief introduction or synopsis of the anime (string)

## rating_complete
This dataset contains the ratings provided by users for various animes.

- `user_id`: Unique user identifier (integer)
- `anime_id`: Unique anime identifier (integer)
- `rating`: Rating given by the user to the anime (float)

## watching_status
This dataset contains descriptions for different anime watching statuses.

- `status`: Watching status (e.g., "Watching", "Completed", "On Hold", "Dropped") (string)
- `description`: Explanation of what the status means (string)

> [!NOTE]
> The `rating_complete` and `animelist` datasets come from the same data source, which is stored in the [`data/users`](data/users/) folder. The source code used to gather the data can be found in the [Section 6 + 7 of the web scraping notebook](notebooks/web_scraping.ipynb).
