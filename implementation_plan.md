# Implementation Plan: Automated Portfolio Analytics Pipeline

This plan outlines the architecture, setup, directory structure, and step-by-step roadmap for building a production-grade, end-to-end Automated Portfolio Analytics Pipeline.

The goal is to ingest historical and daily financial data, load it into a PostgreSQL data warehouse, transform it into a star schema using dbt, orchestrate it using Apache Airflow, and visualize portfolio performance in Metabase—all running inside a containerized Docker environment.

---

## Architecture Diagram

```mermaid
flowchart TD
    subgraph Raw Data Ingestion
        A1["Yahoo Finance API (yfinance)"] -->|Extract JSON/CSV| B["Python Ingestion Script"]
        A2["Static Seeds (portfolio_holdings.csv)"] -->|Seed Load| B
    end

    subgraph Orchestration [Apache Airflow]
        B -->|Orchestrated load| C[("PostgreSQL (raw schema)")]
    end

    subgraph Data Warehousing & Transformation [dbt Core]
        C -->|dbt run| D["staging models (Bronze)"]
        D -->|dbt run| E["intermediate models (Silver)"]
        E -->|dbt run| F["marts models (Gold)"]
        F -->|dbt test| G[("PostgreSQL (analytics schema)")]
    end

    subgraph Visualization [BI Layer]
        G -->|Read Marts| H["Metabase Dashboard"]
    end
    
    style Orchestration fill:#f9f,stroke:#333,stroke-width:2px
    style Data Warehousing & Transformation fill:#bbf,stroke:#333,stroke-width:2px
```

---

## Directory Structure

We will organize the project under `/Users/sangth/Projects/Data_Engineer/` using the following professional structure:

```
/Users/sangth/Projects/Data_Engineer/
├── CLAUDE.md                   # Always-on AI context file (loaded every session)
├── docker-compose.yml          # All services: Postgres, Airflow, pgAdmin, Metabase
├── .env                        # Secrets — never committed (in .gitignore)
├── .env.example                # Template for .env — safe to commit
├── requirements.txt            # Python dependencies for ingestion scripts
├── implementation_plan.md      # Full phased roadmap (this file)
├── task.md                     # Current task checklist (tracks progress)
├── docs/
│   └── architecture.svg        # Pipeline diagram (embedded in README)
├── dags/                       # Apache Airflow DAGs
│   └── portfolio_orchestrator.py
├── scripts/                    # Core Python modules for ingestion
│   └── extract_data.py
└── dbt_project/                # dbt project root
    ├── dbt_project.yml         # dbt project config + materialization strategy
    ├── profiles.yml            # Database connection (dev=localhost, docker=container)
    ├── seeds/
    │   └── portfolio_holdings.csv
    └── models/
        ├── staging/            # Bronze: stg_stock_prices, stg_portfolio_holdings
        ├── intermediate/       # Silver: int_stock_prices_enriched
        └── marts/              # Gold: dim_companies, fct_portfolio_valuation
```

---

## Proposed Changes & Phased Roadmap

We will build the project iteratively, verifying each component before moving to the next.

### Phase 1: Environment & Warehousing (Docker, Postgres, pgAdmin)
Set up the core local infrastructure.
*   **Create** `docker-compose.yml` to define:
    *   **Postgres** database container.
    *   **pgAdmin** container (GUI tool to verify tables and run raw queries).
*   **Verify:** Ensure containers communicate with each other, and pgAdmin can connect to Postgres.

### Phase 2: Ingestion & Extraction (Python & Yahoo Finance API)
Write the script that pulls raw financial data.
*   **Create** `scripts/extract_data.py` using `yfinance` to fetch stock prices for a specific portfolio (AAPL, MSFT, GOOG, JPM, C).
*   **Load:** Load this data into a `raw` schema inside our Postgres container.
*   **Verify:** Check database tables in pgAdmin to verify the data was successfully loaded with appropriate types.

### Phase 3: Orchestration (Apache Airflow)
Automate and schedule the data pipeline.
*   Add **Apache Airflow** services to `docker-compose.yml`.
*   **Create** `dags/portfolio_orchestrator.py` to schedule the pipeline (e.g., running daily at the market close).
*   The DAG will:
    1.  Extract raw data from the API.
    2.  Write it to the Postgres raw staging table.
*   **Verify:** Trigger the DAG via the Airflow UI, check logs, and confirm new records populate Postgres.

### Phase 4: Analytics Engineering (dbt Core)
Model the raw data into business-ready analytical structures.
*   Initialize a new dbt project under `dbt_project/`.
*   Create staging models to clean timestamps, convert column names, and cast types.
*   Create intermediate models to calculate **50-day and 200-day moving averages** using SQL window functions.
*   Implement dimensional modeling:
    *   `dim_companies`: Details about ticker symbols, sectors, and names.
    *   `fct_portfolio_valuation`: Combines stock prices with static holdings (`portfolio_holdings.csv`) to show the total portfolio value over time.
*   Write schema tests (e.g., ensuring stock price dates are unique, and fields are not null).
*   Add dbt models to the Airflow orchestrator so that transformations execute automatically after ingestion.

### Phase 5: Visualization & Dashboarding (Metabase)
Build the final business layer.
*   Add **Metabase** to `docker-compose.yml`.
*   Connect Metabase to the `analytics` (marts) schema in Postgres.
*   Build a dashboard showing:
    *   Total Portfolio Value over time.
    *   Daily portfolio gain/loss.
    *   Individual stock trends plotted against 50-day and 200-day moving averages.
    *   Asset allocation breakdown (sector distribution).

---

## How to Leverage AI Effectively on this Project

To get the most out of this project and ensure you understand every aspect of it, we should interact in a **collaborative mentorship mode**:

1.  **Explanation First:** Before we write configuration code (like Docker Compose or dbt configurations), I will explain *what* each block of code does, so you understand the networking, volume mount, and environment variables.
2.  **Interactive Debugging:** If you see any errors (e.g., Airflow task failures, database connection errors, dbt syntax errors), we will analyze the logs together. I will explain *why* the error happened and how to prevent it.
3.  **Interview Preparation (DE Concepts):** As we build, I will point out concepts that frequently appear in Data Engineering interviews (e.g., Idempotency, Incremental materialization, Star Schema vs. Snowflake Schema, SCDs).

---

## Verification Plan

### Automated Tests
- Run `dbt test` to check uniqueness, null values, and referential integrity.
- Airflow health checks & task success logs.

### Manual Verification
- Querying PostgreSQL schemas directly using pgAdmin to verify structures.
- Visually inspecting the Metabase charts to check that calculations are mathematically correct.
