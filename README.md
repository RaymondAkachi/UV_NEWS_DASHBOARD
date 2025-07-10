# UV News Dashboard

UV News Dashboard is a Python-based web application that aggregates, analyzes, and visualizes news article sentiments from Google News RSS feeds. Built with a strong emphasis on robust backend data processing, this project fetches news articles, performs sentiment analysis, stores data in a PostgreSQL database, caches results in Redis, and displays insights through a Dash-based web interface. The dashboard provides visualizations such as daily average sentiment trends, sentiment distribution pie charts, and top news sources by article count, with support for filtering by time period (weekly or monthly) and category (e.g., business, sports).

**Note**: As a backend developer, my focus was on creating a robust data pipeline and backend logic. The UI is functional but basic, as frontend development is not my primary expertise. I encourage frontend developers to contribute by enhancing the UI to make it more polished and user-friendly!

## Table of Contents

* [Project Overview](#project-overview)
* [Features](#features)
* [Architecture](#architecture)
* [Tech Stack](#tech-stack)
* [Setup Instructions](#setup-instructions)
* [Usage](#usage)
* [Contributing](#contributing)
* [Future Improvements](#future-improvements)
* [License](#license)

## Project Overview

The UV News Dashboard is designed to provide real-time insights into news article sentiments by scraping Google News RSS feeds, analyzing article sentiments, and presenting the results through interactive visualizations. The project leverages asynchronous Python for efficient data fetching and processing, SQLAlchemy for database interactions, Redis for caching, and Dash for the web interface.

### Key Highlights

* **Backend Focus**: The core strength lies in the data pipeline, which fetches, processes, and stores news articles efficiently using async/await patterns.
* **Sentiment Analysis**: Articles are categorized into positive (>0.4), neutral (-0.4 to 0.4), and negative (<0.4) sentiments.
* **Interactive Visualizations**: Includes a line graph for daily sentiment trends, a pie chart for sentiment distribution, and a table for top sources.
* **Scalability**: Uses Redis for caching to reduce database load and improve performance.
* **Extensibility**: Supports filtering by category and time period, with room for additional features.

The UI, while functional, is intentionally minimal. As a backend developer, I prioritized data integrity and processing logic over frontend polish. Frontend developers are welcome to enhance the UI to improve user experience!

## Features

* **Real-Time News Aggregation**: Fetches news articles from Google News RSS feeds (configurable via `.env`).
* **Sentiment Analysis**: Computes sentiment scores for articles and categorizes them into positive, neutral, and negative.
* **Interactive Dashboard**:
    * **Line Graph**: Displays daily average sentiment over the last 7 or 30 days.
    * **Pie Chart**: Shows the distribution of positive, neutral, and negative articles.
    * **Top Sources Table**: Lists the top 10 news sources by article count, with their average sentiment.
* **Time Period Filtering**: Toggle between weekly (last 7 days) and monthly (last 30 days) views.
* **Category Filtering**: Filter data by categories like business, sports, etc.
* **Caching**: Uses Redis to cache dashboard data, updated hourly via a scheduler.
* **Asynchronous Processing**: Leverages `asyncio` for non-blocking RSS fetching, database queries, and sentiment analysis.
* **Database Storage**: Stores articles in a PostgreSQL database with a robust schema for querying.

## Architecture

The project follows a modular architecture:

### Data Ingestion:

* Fetches RSS feeds from Google News using `feedparser`.
* Processes articles asynchronously to extract title, source, publication date, category, and sentiment.

### Database Storage:

* Stores articles in a PostgreSQL database using SQLAlchemy with an async engine (`asyncpg`).

#### Schema (`news_articles` table):

| Column    | Type     | Constraints        |
| :-------- | :------- | :----------------- |
| `id`      | Integer  | Primary Key, Index |
| `title`   | String   | Not Null           |
| `source_id` | String   | Not Null           |
| `country` | String   | Not Null           |
| `pubDate` | DateTime | Not Null           |
| `sentiment` | Float    | Not Null           |
| `category` | String   | Not Null           |
| `link`    | String   |                    |

### Data Processing:

* **Sentiment Analysis**: Computes sentiment scores (mocked or via a library like TextBlob or VADER).
* **Aggregation**:
    * `get_daily_avg_sentiment`: Computes daily average sentiment for the line graph.
    * `get_sentiment_pie_data`: Counts articles by sentiment category for the pie chart.
    * `get_top_sources_with_avg_sentiment`: Aggregates top sources by article count and average sentiment.

### Caching:

* Uses Upstash Redis to cache dashboard data (`monthly_summary`, `weekly_summary`) to reduce database queries.
* Updates cache hourly using a scheduler.

### Web Interface:

* Built with Dash (Plotly) for visualizations.
* **Components**:
    * Dropdown for time period (weekly, monthly).
    * Dropdown for category filtering.
    * Line graph, pie chart, and table for data visualization.
    * Updates every hour via `dcc.Interval`.

### Scheduler:

* Runs background tasks to refresh RSS data and cache using `asyncio`.

## Tech Stack

| Component     | Technology                            |
| :------------ | :------------------------------------ |
| Backend       | Python 3.13, SQLAlchemy (asyncpg), Redis, feedparser, aiohttp, python-dotenv, uv |
| Database      | PostgreSQL                            |
| Caching       | Redis (Upstash)                       |
| Frontend      | Dash (Plotly), HTML/CSS               |
| Deployment    | Docker                                |

## Setup Instructions

### Prerequisites

* Python 3.13
* PostgreSQL (version 15 or later)
* Redis (local or Upstash account)
* Docker (optional for containerized deployment)
* `uv` (for dependency management)

### Installation

1.  **Clone the Repository**:
    ```bash
    git clone https://github.com/RaymondAkachi/uv-news-dashboard.git
    cd uv-news-dashboard
    ```

2.  **Set Up Environment Variables**: Create a `.env` file in the project root:
    ```ini
    DATABASE_URL=postgresql+asyncpg://postgres:your_password@127.0.0.1:5432/news-dashboard?sslmode=disable
    REDIS_URL=rediss://default:your_redis_key@your-redis-endpoint.upstash.io:6379
    RSS_URL=[https://news.google.com/rss?hl=en-US&gl=NG&ceid=US:en](https://news.google.com/rss?hl=en-US&gl=NG&ceid=US:en)
    ```
    * Replace `your_password` with your PostgreSQL password.
    * Replace `your_redis_key` and `your-redis-endpoint` with your Upstash Redis credentials.

3.  **Install Dependencies**:
    ```bash
    uv sync
    ```

4.  **Set Up PostgreSQL**:
    * Ensure PostgreSQL is running:
        ```bash
        pg_ctl -D "C:\Program Files\PostgreSQL\15\data" start
        ```
    * Create the `news-dashboard` database:
        ```bash
        createdb -h localhost -p 5432 -U postgres news-dashboard
        ```
    * Initialize the database schema:
        ```bash
        export RUN_CREATE_TABLES=true
        uv run python -m app.db_logic.models
        ```

5.  **Run the Application**:
    ```bash
    uv run python -m src.app.main
    ```
    Access the dashboard at `http://127.0.0.1:8000`.

### Optional: Docker Deployment:

1.  **Build and run with Docker Compose**:
    ```bash
    docker build -t news-dashboard .
    docker-compose up
    ```
2.  **Update `docker-compose.yml` with your `.env` variables**:
    ```yaml
    services:
      app:
        image: news-dashboard
        build:
          context: .
          dockerfile: Dockerfile
        ports:
          - "8000:8000"
        environment:
          - DATABASE_URL=postgresql+asyncpg://postgres:your_password@host.docker.internal:5432/news-dashboard?sslmode=disable
          - REDIS_URL=rediss://default:your_redis_key@your-redis-endpoint.upstash.io:6379
          - RSS_URL=[https://news.google.com/rss?hl=en-US&gl=NG&ceid=US:en](https://news.google.com/rss?hl=en-US&gl=NG&ceid=US:en)
    ```

## Usage

### Access the Dashboard:

* Open `http://127.0.0.1:8000` in your browser.
* Use the dropdowns to select weekly or monthly time periods and a category (e.g., business).
* View the line graph (daily sentiment trends), pie chart (sentiment distribution), and table (top sources).

### Data Refresh:

* The dashboard updates every hour via `dcc.Interval` (set to `3600 * 1000` milliseconds).
* The scheduler fetches new RSS data and updates the Redis cache.

### Debugging:

* Check logs for database connection issues or query errors.
* Enable SQLAlchemy debug logging by setting `echo=True` in `create_async_engine`.

## Contributing

Contributions are welcome, especially for improving the UI! As a backend developer, I focused on building a robust data pipeline, but the frontend could use some love. Here’s how you can contribute:

### Frontend Improvements

* Enhance the Dash UI with better styling (e.g., Tailwind CSS, Bootstrap).
* Add responsive design for mobile devices.
* Improve chart interactivity (e.g., tooltips, zoom).
* **Example**: Update `src/app/main.py` to use a custom CSS framework or redesign the layout.

### Backend Enhancements

* Add support for more RSS feeds or external APIs.
* Implement advanced sentiment analysis (e.g., using Hugging Face transformers).
* Optimize database queries with additional indexes.

### How to Contribute

1.  Fork the repository.
2.  Create a branch: `git checkout -b feature/your-feature`.
3.  Commit changes: `git commit -m "Add your feature"`.
4.  Push to your fork: `git push origin feature/your-feature`.
5.  Open a pull request.

Please follow the [Code of Conduct](link-to-code-of-conduct) and include tests for new features.

## Future Improvements

* **UI Enhancements**: Collaborate with frontend developers to create a more polished, responsive interface.
* **Sentiment Analysis**: Integrate a more sophisticated NLP model (e.g., BERT) for better sentiment accuracy.
* **Real-Time Updates**: Reduce the update interval or add WebSocket support for live data.
* **Additional Visualizations**: Add heatmaps, word clouds, or geographic visualizations for article origins.
* **Multi-Source Support**: Aggregate news from multiple RSS feeds or APIs.
* **Authentication**: Add user authentication for personalized dashboards.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

Built with 💻 by a backend enthusiast!

Feel free to star ⭐ this repository and contribute to making the UI shine or adding new features. Let’s make news analysis more accessible and visually appealing together!
