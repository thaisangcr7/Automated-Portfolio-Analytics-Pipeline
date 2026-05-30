# Project Roadmap

**Automated Portfolio Analytics Pipeline**
Full-stack data engineering project: ingest → store → transform → orchestrate → visualize.

---

## Phase 1 — Infrastructure ✅
Docker environment with PostgreSQL and pgAdmin.

- [x] `docker-compose.yml` — PostgreSQL + pgAdmin services with health checks
- [x] `.env` / `.env.example` — secrets management, no hardcoded passwords
- [x] `.gitignore` — protects secrets and build artifacts
- [x] Verified containers start and pgAdmin connects to Postgres

---

## Phase 2 — Ingestion ✅
Python script pulls daily stock prices from Yahoo Finance into the raw schema.

- [x] `scripts/extract_data.py` — fetches AAPL, MSFT, GOOG, JPM, C via yfinance
- [x] Loads into `raw.stock_prices` using append-only pattern
- [x] Verified raw data in pgAdmin

---

## Phase 3 — Orchestration ✅
Apache Airflow schedules and monitors the pipeline daily at 6 PM EST.

- [x] Extended `docker-compose.yml` with Airflow services (webserver, scheduler, init)
- [x] `dags/portfolio_orchestrator.py` — DAG with daily cron schedule
- [x] Fixed `multitasking==0.0.10` pin — Python 3.8 compatibility in Airflow container
- [x] Fixed `AIRFLOW__WEBSERVER__SECRET_KEY` — webserver and scheduler now share same key
- [x] Verified end-to-end: DAG triggered → 15 rows loaded into `raw.stock_prices` ✅

---

## Phase 4 — Transformation ✅
dbt models transform raw data into analytics-ready tables (medallion architecture).

- [x] `models/staging/stg_stock_prices.sql` — deduplicate, rename columns, cast types (Bronze)
- [x] `models/staging/stg_portfolio_holdings.sql` — load seed data into staging layer
- [x] `models/intermediate/int_stock_prices_enriched.sql` — 50d & 200d MA via SQL WINDOW (Silver)
- [x] `models/marts/dim_companies.sql` — dimension table, 5 rows (Gold)
- [x] `models/marts/fct_portfolio_valuation.sql` — fact table, 1,260 rows (Gold)
- [x] dbt tests — 26 tests passing: unique, not_null, accepted_values, relationships
- [x] `dbt seed` → 5 rows, `dbt run` → 5 models, `dbt test` → 26/26 PASS ✅
- [x] Added dbt_seed + dbt_run + dbt_test tasks to Airflow DAG
- [x] Full 4-task pipeline verified end-to-end via Airflow: ingest → seed → run → test ✅

---

## Phase 5 — Visualization ✅
Metabase dashboard reads from the Gold layer and displays portfolio analytics.

- [x] Added Metabase service to `docker-compose.yml` (port 3000, backed by Postgres)
- [x] Connected Metabase to `analytics` schema in PostgreSQL
- [x] Built 5 dashboard charts:
  - Total Portfolio Value (number card — latest day)
  - Portfolio Value Over Time (line chart — all 5 tickers)
  - Unrealized P&L by Stock (bar chart)
  - AAPL Moving Averages (line chart — close_price, ma_50d, ma_200d)
  - Sector Allocation (pie chart — Technology vs Financials)
- [x] Dashboard saved as `Portfolio Analytics` in Metabase ✅
