# Project Walkthrough — Plain English Guide

> This document explains every file in this project from scratch.
> Written for someone who is new to Data Engineering.
> Read this if you want to understand WHY each piece exists, not just what it does.

---

## The One-Sentence Summary

We built a system that **automatically pulls stock prices every day, stores them in a
database, cleans and enriches the data using SQL, and displays the results on a
dashboard** — and every piece runs inside Docker so it works on any computer.

---

## The Mental Model — Think of a Factory

Before reading about individual files, understand the factory analogy:

```
RAW MATERIALS       DELIVERY TRUCK       WAREHOUSE         FACTORY FLOOR        SHOWROOM
Yahoo Finance   →   Python script   →   PostgreSQL   →       dbt            →   Metabase
(stock prices)    (extract_data.py)   (raw schema)    (SQL transforms)       (dashboard)

                    ↑
            Apache Airflow is the FACTORY MANAGER
            It schedules the whole process every day at 6 PM
            Docker is the BUILDING that contains everything
```

Each tool has one job. Nothing does two jobs. This is the Data Engineering principle
called **separation of concerns**.

---

## Part 1: The Container — Docker

### What is Docker?

Imagine you install software on your laptop. It works. Your colleague installs the
same software on their laptop. It breaks. Why? Because their laptop has a different
operating system version, different settings, different other software installed.

**Docker solves this.** It packages software inside a "container" — a sealed box that
includes the software AND everything it needs to run. The container behaves identically
on every machine.

### `docker-compose.yml`

**What it is:** A single file that defines ALL the services (containers) in this project.

**Why we need it:** Instead of starting Postgres, pgAdmin, Airflow, and Metabase
separately with long terminal commands, one file describes all of them and
`docker-compose up -d` starts everything at once.

Here's what each service in the file does:

```yaml
services:
  postgres:        ← Our database. Stores ALL data (raw prices + transformed tables)
  pgadmin:         ← A visual tool to browse the database (like Excel for Postgres)
  airflow-init:    ← Runs ONCE to set up Airflow's own internal database
  airflow-webserver: ← The Airflow UI at localhost:8080
  airflow-scheduler: ← The Airflow brain that watches for scheduled jobs
```

**Key concepts in docker-compose.yml:**

```yaml
healthcheck:            ← Postgres tells Docker "I'm ready" before Airflow tries to connect
  test: pg_isready      ← Without this, Airflow crashes because Postgres wasn't ready yet

depends_on:
  postgres:
    condition: service_healthy  ← "Don't start me until Postgres is healthy"

volumes:
  - postgres_data:/var/lib/postgresql/data  ← Data survives container restarts
  - ./dags:/opt/airflow/dags                ← Your DAG files appear inside the container

networks:
  de_network:       ← All services share this private network so they can talk to each other
                      Inside Docker, Postgres is reachable as "postgres" (not "localhost")
```

**Interview talking point:** "I used Docker Compose to define infrastructure as code.
The entire environment is reproducible from one file — anyone can clone the repo and
run it in minutes."

---

## Part 2: Secrets Management

### Why not just hardcode passwords?

If you write `password: mypassword` directly in `docker-compose.yml`, it gets
committed to GitHub. Your password is now public forever. Even if you delete it later,
git history remembers it.

The solution: put passwords in a file that git ignores.

### `.env`

**What it is:** A plain text file with `KEY=VALUE` pairs. Lives on your machine only.

```
POSTGRES_PASSWORD=postgres
PGADMIN_DEFAULT_PASSWORD=admin
```

Docker Compose reads this file automatically. When it sees `${POSTGRES_PASSWORD}` in
docker-compose.yml, it substitutes the real value from `.env`.

**This file is in `.gitignore` — it is NEVER committed to GitHub.**

### `.env.example`

**What it is:** The same structure as `.env` but with placeholder values instead of
real ones. This IS committed to GitHub.

**Why it exists:** When someone clones your project, they see `.env.example` and know
exactly what variables they need to set. Without it, they'd have no idea.

### `.gitignore`

**What it is:** A list of files and folders git should pretend don't exist.

```
.env              ← Never commit real passwords
.venv/            ← Python virtual environment (thousands of files, not your code)
__pycache__/      ← Python's temporary compiled files
dbt_project/target/  ← dbt's build output (can always be regenerated)
```

**Rule of thumb:** If you didn't write it and it can be regenerated, it goes in `.gitignore`.

---

## Part 3: Python Dependencies

### `requirements.txt`

**What it is:** A list of Python libraries this project needs.

```
yfinance       ← Downloads stock prices from Yahoo Finance
pandas         ← Manipulates data in tables (DataFrames)
sqlalchemy     ← Connects Python to databases
psycopg2-binary ← The actual PostgreSQL driver (sqlalchemy uses this under the hood)
```

**Why it's a file instead of just installing things:** Anyone who clones the project
runs `pip install -r requirements.txt` and gets the exact same libraries. Reproducible.

---

## Part 4: The Ingestion Script

### `scripts/extract_data.py`

**What it does:** Pulls stock price data from Yahoo Finance and writes it to PostgreSQL.

**Why Python?** Python has `yfinance`, a free library that wraps Yahoo Finance's API.
Writing this in SQL isn't possible — you need a programming language to make HTTP
requests to an external API.

Let's walk through the key functions:

```python
def get_db_engine():
    # Reads credentials from environment variables (never hardcoded)
    # Creates a "connection object" that other functions can use to talk to Postgres
    db_host = os.getenv("POSTGRES_HOST", "localhost")
    #                                     ↑ default value if the env var isn't set
    # When running locally: host = localhost
    # When running inside Docker: host = postgres (the container name)
```

```python
def extract_stock_data(tickers, start_date, end_date):
    # Loops through each ticker: AAPL, MSFT, GOOG, JPM, C
    # Downloads OHLCV data (Open, High, Low, Close, Volume) for each
    # Adds extracted_at timestamp — this is important for deduplication later in dbt
    # Returns one combined DataFrame with all tickers
```

```python
def load_data_to_postgres(df, table_name, schema_name="raw"):
    # Creates the "raw" schema if it doesn't exist
    # Writes the DataFrame to raw.stock_prices
    # if_exists="append" ← ALWAYS appends, never replaces
    #                       This is the append-only pattern
```

```python
def main():
    # Handles command-line arguments:
    # python extract_data.py --backfill    → loads last 365 days
    # python extract_data.py               → loads last 5 days
```

**Key DE concept — Append-only ingestion:**
We never delete or update the raw table. Every run adds new rows. Why?

- You always have a full audit trail ("what data did we have on March 3rd?")
- If a bug corrupts transformed data, raw is untouched — you can always re-transform
- Deduplication is handled in the dbt staging layer, not here

---

## Part 5: Orchestration

### What is Apache Airflow?

Imagine you have 3 tasks that must happen in order every weekday at 6 PM:
1. Run the Python ingestion script
2. Run dbt to transform the data
3. Run dbt tests to check data quality

You could do this manually. But you'd have to remember every day, be at your computer
at 6 PM, and notice if something failed. That's not scalable.

**Airflow is a scheduler and monitor.** You write your pipeline as a DAG (Directed
Acyclic Graph), tell Airflow when to run it, and Airflow handles the rest. If a task
fails, it retries automatically and sends an alert.

**DAG = Directed Acyclic Graph.** Sounds fancy. It just means:
- **Directed:** Tasks have a defined order (Task 1 must finish before Task 2 starts)
- **Acyclic:** No loops (Task 3 can't point back to Task 1)
- **Graph:** A visual map of tasks and their dependencies

### `dags/portfolio_orchestrator.py`

```python
with DAG(
    'portfolio_analytics_pipeline',
    schedule_interval='0 18 * * 1-5',  # Cron: 6 PM, Monday-Friday
    #                  ↑ ↑↑  ↑   ↑
    #                  │ ││  │   └─ Day of week (1=Mon, 5=Fri)
    #                  │ ││  └───── Month (every month)
    #                  │ │└──────── Day of month (every day)
    #                  │ └───────── Hour (18 = 6 PM)
    #                  └─────────── Minute (0 = on the hour)
    catchup=False,     # If Airflow was offline for 3 days, don't run 3 catch-up jobs
    start_date=datetime(2026, 1, 1),
) as dag:

    ingest_stock_data = BashOperator(
        task_id='ingest_stock_data',
        bash_command='python /opt/airflow/scripts/extract_data.py',
        # Runs inside the Airflow container, where scripts/ is mounted as a volume
    )
```

**What's coming in Phase 4:** We'll add two more tasks after ingestion:
```
ingest_stock_data >> dbt_run >> dbt_test
       ↓                ↓           ↓
  Pulls data      Transforms    Validates
  from API        raw → gold    data quality
```

---

## Part 6: The Transformation Layer — dbt

### What is dbt?

dbt (data build tool) lets you write transformations as SQL `SELECT` statements. You
write "here's the query I want", and dbt:
- Executes it against your database
- Materializes the result as a view or table
- Tracks the lineage (which model depends on which)
- Runs tests to check data quality
- Generates documentation automatically

**Before dbt existed**, data teams wrote raw SQL scripts and ran them in a specific
order manually. Fragile and hard to test.

**With dbt**, transformations are version-controlled, tested, and documented.

### `dbt_project/dbt_project.yml`

**What it is:** The configuration file for the whole dbt project.

```yaml
name: 'portfolio_analytics'
profile: 'portfolio_profile'   ← Which connection profile to use (defined in profiles.yml)

models:
  portfolio_analytics:
    staging:
      +materialized: view      ← Staging models are views (no data stored, just a query)
    intermediate:
      +materialized: view      ← Same for intermediate
    marts:
      +materialized: table     ← Marts are tables (data physically stored, fast for dashboards)
```

**Why views for staging/intermediate but tables for marts?**
- Views are computed on-the-fly — no storage cost, always fresh
- Tables are pre-computed — they take storage but dashboards query them instantly
- Gold layer (marts) is what Metabase reads, so speed matters there

### `dbt_project/profiles.yml`

**What it is:** The database connection settings for dbt.

```yaml
dev:
  host: localhost   ← Use this when running dbt on your local machine
docker:
  host: postgres    ← Use this when running dbt inside a Docker container
                      (containers talk to each other by service name, not localhost)
```

This is why we have two profiles — same database, different host names depending on
where dbt is running.

### `dbt_project/seeds/portfolio_holdings.csv`

**What it is:** A CSV file with static data about our portfolio.

```csv
ticker,shares,cost_basis,purchase_date,sector
AAPL,50,165.50,2025-01-10,Technology
JPM,60,172.80,2025-01-20,Financials
```

**Why is this here and not in the database already?**
This data doesn't change often — it's the "what did we buy and when" record. `dbt seed`
loads it into the database as a table. Then our dbt models join stock prices against
this to calculate portfolio value.

**What `dbt seed` does:** Reads the CSV, creates a table in the database called
`portfolio_analytics.portfolio_holdings`, loads all the rows.

---

## Part 7: The AI Context File

### `CLAUDE.md`

**What it is:** Instructions for any AI assistant working on this project.

Claude Code (and other AI tools) automatically read this file at the start of every
session. It tells the AI:
- What this project is
- What patterns must be followed
- What not to do
- What the current status is

Without this file, every AI session starts cold and you'd spend 5 minutes re-explaining
context. With it, you can just say "continue Phase 4" and the AI already knows
everything.

---

## Part 8: How Everything Connects

Here's the complete story, from raw data to dashboard:

```
1. Every weekday at 6 PM, Airflow wakes up

2. Task 1: extract_data.py runs
   → Calls Yahoo Finance API
   → Downloads today's prices for AAPL, MSFT, GOOG, JPM, C
   → Appends rows to raw.stock_prices in PostgreSQL
   → Row example: {date: 2026-05-29, ticker: AAPL, close: 211.50, ...}

3. Task 2: dbt run
   → stg_stock_prices: deduplicates raw, renames columns, casts types
   → stg_portfolio_holdings: cleans the seed CSV data
   → int_stock_prices_enriched: calculates 50-day and 200-day moving averages
      using SQL WINDOW functions
   → dim_companies: one row per company (ticker, name, sector)
   → fct_portfolio_valuation: joins prices × shares held = market value per day

4. Task 3: dbt test
   → Checks: no duplicate rows in fact table?
   → Checks: no null ticker values?
   → Checks: every ticker in facts exists in dim_companies?
   → If any check fails → pipeline stops and alerts

5. Metabase reads from analytics schema
   → Displays charts: portfolio value over time, P&L, moving averages, sector allocation
```

---

## The 5 Interview Concepts to Know

When someone asks you to explain this project, these are the terms to use:

| Concept | What to say |
|---------|-------------|
| **ELT** | "We load raw data first, then transform inside the warehouse. This is different from ETL which transforms before loading. ELT is better for scalability and gives you an audit trail." |
| **Medallion Architecture** | "Data moves through three quality tiers: Bronze (raw), Silver (cleaned + enriched), Gold (business-ready). Each tier adds more value and trust." |
| **Idempotency** | "The pipeline can run multiple times without corrupting data. If Airflow re-runs a failed job, you don't get duplicate records." |
| **Star Schema** | "The Gold layer uses a fact table (measurements) joined to dimension tables (context). It's optimized for analytical queries — the standard for data warehouses." |
| **Infrastructure as Code** | "The entire environment — database, scheduler, dashboard tool — is defined in one docker-compose.yml file. Anyone can clone the repo and reproduce it exactly." |
