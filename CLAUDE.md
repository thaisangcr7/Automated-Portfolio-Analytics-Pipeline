# CLAUDE.md — Automated Portfolio Analytics Pipeline

This file is automatically loaded by Claude Code at the start of every session.
Read it fully before writing any code or making any changes.

---

## What This Project Is

An end-to-end **Data Engineering portfolio project** built by a beginner DE learning
the craft by doing. The goal is to demonstrate the full data engineering lifecycle:
ingest → store → transform → orchestrate → visualize.

**The owner is actively learning.** Every decision should be explained. Prefer simple,
readable patterns over clever ones. Never over-engineer.

---

## Architecture (plain English)

```
Yahoo Finance API
      │  Python (extract_data.py) pulls OHLCV prices for AAPL, MSFT, GOOG, JPM, C
      ▼
PostgreSQL  →  raw schema       ← append-only, never modified
      │  dbt transforms in 3 layers (medallion architecture)
      ├─ staging/    (Bronze)   ← clean, rename, cast, deduplicate
      ├─ intermediate/ (Silver) ← 50-day & 200-day moving averages (SQL WINDOW)
      └─ marts/      (Gold)     ← dim_companies + fct_portfolio_valuation (star schema)
      │
      ▼
PostgreSQL  →  analytics schema ← business-ready tables for dashboards
      │
      ▼
Metabase dashboard              ← portfolio value, P&L, moving averages, sector allocation

Apache Airflow orchestrates the whole pipeline: runs daily at 6 PM EST Mon–Fri.
Everything runs inside Docker — fully reproducible local environment.
```

---

## Tech Stack

| Tool | Version | Purpose |
|------|---------|---------|
| Docker + Compose | latest | Containerized local environment |
| PostgreSQL | 15-alpine | Data warehouse (raw + analytics schemas) |
| Python | 3.9 | Data ingestion via yfinance |
| Apache Airflow | 2.7.2 | Pipeline orchestration & scheduling |
| dbt Core | latest | SQL transformations & data quality tests |
| Metabase | latest | Business intelligence dashboard |
| pgAdmin | 4 | Manual DB inspection & query tool |

---

## Directory Structure

```
/
├── CLAUDE.md                        ← you are here
├── docker-compose.yml               ← all services defined here
├── .env                             ← secrets (never commit — in .gitignore)
├── .env.example                     ← template for .env (safe to commit)
├── requirements.txt                 ← Python dependencies
├── implementation_plan.md           ← full phased roadmap (read this for context)
├── ROADMAP.md                       ← current phase status and task checklist
│
├── docs/
│   └── architecture.svg             ← pipeline diagram (embedded in README)
│
├── scripts/
│   └── extract_data.py              ← ingestion: Yahoo Finance → raw.stock_prices
│
├── dags/
│   └── portfolio_orchestrator.py    ← Airflow DAG: daily pipeline schedule
│
└── dbt_project/
    ├── dbt_project.yml              ← project config + materialization strategy
    ├── profiles.yml                 ← DB connection (dev=localhost, docker=container)
    ├── seeds/
    │   └── portfolio_holdings.csv   ← static: shares, cost basis, sector per ticker
    └── models/                      ← NOT YET CREATED — Phase 4 work
        ├── staging/
        ├── intermediate/
        └── marts/
```

---

## Current Phase Status

| Phase | Status | Notes |
|-------|--------|-------|
| 1 — Docker + Postgres + pgAdmin | ✅ Done | Health checks added to docker-compose |
| 2 — Python ingestion | ✅ Done | extract_data.py, append pattern, env vars |
| 3 — Airflow orchestration | 🔧 In Progress | DAG file exists, needs end-to-end verification |
| 4 — dbt transformation | ⬜ Not started | models/ folder doesn't exist yet |
| 5 — Metabase dashboard | ⬜ Not started | Service not yet in docker-compose |

**Before writing any new code, check `ROADMAP.md` for the current state.**

---

## Key Patterns — Follow These Exactly

### ELT, not ETL
We load raw data first, then transform inside the warehouse using dbt.
Do NOT transform data in Python before loading — that defeats the purpose.

### Append-only ingestion
`extract_data.py` always appends rows to `raw.stock_prices`. It never deletes or
updates. Deduplication happens in dbt staging models. This preserves an audit trail.

### Credentials via environment variables
Passwords live in `.env` only. Docker Compose reads them as `${VARIABLE}`.
Python reads them via `os.getenv()`. **Never hardcode credentials anywhere.**

### dbt materialization strategy
```
staging/      → materialized: view   (lightweight, no storage cost)
intermediate/ → materialized: view   (same reason)
marts/        → materialized: table  (optimized for dashboard queries)
```

### dbt profiles
- Use `dev` profile when running dbt locally (host: localhost)
- Use `docker` profile when running dbt inside the Airflow container (host: postgres)

---

## What NOT To Do

- **Do not** add error handling for scenarios that can't happen
- **Do not** create helper abstractions "for future use" — build only what the current phase needs
- **Do not** add comments explaining what the code does — only add a comment if the WHY is non-obvious
- **Do not** commit `.env` — it is gitignored for a reason
- **Do not** modify `raw.stock_prices` in dbt — staging models SELECT from raw, never alter it
- **Do not** use `git add .` or `git add -A` — stage files explicitly to avoid committing secrets

---

## Common Commands

```bash
# Start all services
docker-compose up airflow-init        # run once to initialize Airflow DB
docker-compose up -d                  # start everything in background

# Check running containers
docker ps

# Run ingestion manually (from project root)
python scripts/extract_data.py --backfill    # load last 365 days
python scripts/extract_data.py               # load last 5 days

# dbt (run from dbt_project/ directory)
cd dbt_project
dbt debug                             # test DB connection
dbt seed                              # load portfolio_holdings.csv
dbt run                               # run all models
dbt test                              # run data quality tests
dbt run --select staging              # run only staging models

# Service URLs
# Airflow:  http://localhost:8080  (admin / admin)
# pgAdmin:  http://localhost:8082  (admin@admin.com / admin)
# Metabase: http://localhost:3000  (set up on first visit)
```

---

## Interview Concepts This Project Demonstrates

When explaining this project to an employer, highlight:

- **ELT pattern** — why load first, transform later (scalability, auditability)
- **Idempotency** — the pipeline can run multiple times without corrupting data
- **Medallion architecture** — Bronze/Silver/Gold data quality tiers
- **Star schema** — fact and dimension tables optimized for analytical queries
- **SQL window functions** — used for 50/200-day moving averages in intermediate models
- **Data quality testing** — dbt tests enforce uniqueness, not-null, referential integrity
- **Infrastructure as code** — entire environment reproducible from `docker-compose.yml` + `.env`
- **Pipeline orchestration** — Airflow DAG with task dependencies and retry logic

---

## GitHub

Repo: https://github.com/thaisangcr7/Automated-Portfolio-Analytics-Pipeline
Branch: main
