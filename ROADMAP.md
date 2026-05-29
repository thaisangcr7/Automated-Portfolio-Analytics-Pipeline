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

## Phase 4 — Transformation ⬜ Not Started
dbt models transform raw data into analytics-ready tables (medallion architecture).

- [ ] `models/staging/` — deduplicate, rename columns, cast types (Bronze)
- [ ] `models/intermediate/` — 50-day & 200-day moving averages via SQL WINDOW (Silver)
- [ ] `models/marts/` — `dim_companies` + `fct_portfolio_valuation` star schema (Gold)
- [ ] dbt tests — unique, not_null, referential integrity
- [ ] Add `dbt run` and `dbt test` as Airflow tasks

---

## Phase 5 — Visualization ⬜ Not Started
Metabase dashboard reads from the Gold layer and displays portfolio analytics.

- [ ] Add Metabase service to `docker-compose.yml`
- [ ] Connect Metabase to `analytics` schema in PostgreSQL
- [ ] Build dashboards: portfolio value, P&L, moving averages, sector allocation
