# Automated Portfolio Analytics Pipeline

An end-to-end data engineering pipeline that automatically ingests daily stock market data, stores it in a PostgreSQL data warehouse, transforms it through three analytical layers using dbt, orchestrates everything with Apache Airflow, and visualizes portfolio performance in Metabase — all running locally in Docker.

---

## Pipeline Architecture

```mermaid
flowchart TD
    subgraph Sources["Data Sources"]
        A1["📈 Yahoo Finance API\n(yfinance)"]
        A2["📄 portfolio_holdings.csv\n(Static Seed)"]
    end

    subgraph Ingestion["Ingestion Layer · Python"]
        B["extract_data.py\nFetches AAPL · MSFT · GOOG · JPM · C"]
    end

    subgraph Warehouse["Data Warehouse · PostgreSQL"]
        C[("raw.stock_prices\nAppend-only raw table")]
    end

    subgraph Transform["Transformation Layer · dbt Core"]
        D["staging/\nstg_stock_prices\nstg_portfolio_holdings"]
        E["intermediate/\nint_stock_prices_enriched\n50d & 200d Moving Averages"]
        F["marts/\ndim_companies\nfct_portfolio_valuation"]
    end

    subgraph BI["Visualization · Metabase"]
        G["📊 Portfolio Dashboard\nValue · P&L · Moving Averages · Sectors"]
    end

    subgraph Orchestration["Orchestration · Apache Airflow"]
        H["portfolio_analytics_pipeline DAG\n⏰ Daily at 6 PM EST  Mon–Fri"]
    end

    A1 -->|"HTTP pull"| B
    A2 -->|"dbt seed"| D
    B -->|"INSERT rows"| C
    C -->|"SELECT"| D
    D --> E
    E --> F
    F -->|"analytics schema"| G
    H -.->|"triggers"| B
    H -.->|"triggers"| D

    style Sources fill:#fef3c7,stroke:#d97706
    style Ingestion fill:#dbeafe,stroke:#2563eb
    style Warehouse fill:#d1fae5,stroke:#059669
    style Transform fill:#ede9fe,stroke:#7c3aed
    style BI fill:#fce7f3,stroke:#db2777
    style Orchestration fill:#fee2e2,stroke:#dc2626
```

---

## Medallion Architecture (Data Layers)

Data flows through three quality tiers — a pattern used at companies like Databricks, Airbnb, and Uber.

```mermaid
flowchart LR
    subgraph Bronze["🥉 Bronze — Raw"]
        B1["raw.stock_prices\n• Exactly as received\n• Append-only\n• Never modified"]
    end

    subgraph Silver["🥈 Silver — Cleaned & Enriched"]
        S1["stg_stock_prices\n• Renamed columns\n• Correct types\n• Deduplicated"]
        S2["int_stock_prices_enriched\n• 50-day moving avg\n• 200-day moving avg\n• Daily returns"]
    end

    subgraph Gold["🥇 Gold — Business Ready"]
        G1["dim_companies\nTicker · Name · Sector"]
        G2["fct_portfolio_valuation\nDate · Ticker · Value · P&L"]
    end

    B1 --> S1 --> S2 --> G1
    S2 --> G2

    style Bronze fill:#fef3c7,stroke:#d97706
    style Silver fill:#e2e8f0,stroke:#64748b
    style Gold fill:#fef9c3,stroke:#ca8a04
```

---

## Star Schema (Dimensional Model)

The Gold layer follows a **star schema** — the standard pattern for analytical data warehouses.

```mermaid
erDiagram
    dim_companies {
        string ticker PK
        string company_name
        string sector
        string market
    }

    fct_portfolio_valuation {
        date price_date PK
        string ticker PK
        float close_price
        float shares_held
        float cost_basis
        float market_value
        float unrealized_pnl
        float pnl_pct
        float ma_50d
        float ma_200d
    }

    dim_companies ||--o{ fct_portfolio_valuation : "ticker"
```

---

## Airflow DAG

```mermaid
flowchart LR
    T1["ingest_stock_data\nPython script pulls\nYahoo Finance → Postgres"]
    T2["dbt_run\ndbt run transforms\nraw → analytics schema"]
    T3["dbt_test\ndbt test validates\nnulls · uniqueness · refs"]

    T1 --> T2 --> T3

    style T1 fill:#dbeafe,stroke:#2563eb
    style T2 fill:#ede9fe,stroke:#7c3aed
    style T3 fill:#d1fae5,stroke:#059669
```

---

## Tech Stack

| Layer | Tool | Purpose |
|-------|------|---------|
| Containerization | Docker + Docker Compose | Reproducible local environment |
| Data Warehouse | PostgreSQL 15 | Stores raw and analytical data |
| Ingestion | Python + yfinance | Pulls stock prices from Yahoo Finance |
| Transformation | dbt Core | SQL models, tests, and documentation |
| Orchestration | Apache Airflow 2.7 | Schedules and monitors the pipeline |
| Visualization | Metabase | Business intelligence dashboard |
| DB Admin | pgAdmin 4 | Browse and query tables manually |

---

## Project Structure

```
.
├── docker-compose.yml          # All services: Postgres, Airflow, pgAdmin, Metabase
├── .env.example                # Environment variable template (copy → .env)
├── requirements.txt            # Python dependencies
│
├── scripts/
│   └── extract_data.py         # Ingestion: Yahoo Finance → Postgres raw schema
│
├── dags/
│   └── portfolio_orchestrator.py  # Airflow DAG: daily pipeline schedule
│
└── dbt_project/
    ├── dbt_project.yml         # dbt project config and materialization strategy
    ├── profiles.yml            # Database connection settings
    ├── seeds/
    │   └── portfolio_holdings.csv  # Static: shares held per ticker
    └── models/
        ├── staging/            # Bronze → Silver: clean and cast
        ├── intermediate/       # Silver: 50d & 200d moving averages
        └── marts/              # Gold: star schema fact & dimension tables
```

---

## Local Setup

### Prerequisites
- [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- Python 3.9+

### 1. Clone & configure

```bash
git clone <your-repo-url>
cd Data_Engineer
cp .env.example .env        # Edit .env with your passwords
```

### 2. Start all services

```bash
docker-compose up airflow-init   # One-time database setup
docker-compose up -d             # Start everything in background
```

### 3. Access the tools

| Service | URL | Credentials |
|---------|-----|-------------|
| Airflow UI | http://localhost:8080 | admin / admin |
| pgAdmin | http://localhost:8082 | admin@admin.com / admin |
| Metabase | http://localhost:3000 | Set up on first visit |

### 4. Run the pipeline

In Airflow UI → enable `portfolio_analytics_pipeline` DAG → trigger manually.

---

## Key Data Engineering Concepts Demonstrated

- **ELT pattern** — Load raw data first, transform inside the warehouse (vs ETL which transforms before loading)
- **Idempotency** — The pipeline can run multiple times without duplicating or corrupting data
- **Medallion architecture** — Bronze / Silver / Gold data quality tiers
- **Star schema** — Fact and dimension tables optimized for analytical queries
- **SQL window functions** — Used in dbt to compute rolling 50-day and 200-day moving averages
- **Data quality testing** — dbt tests enforce uniqueness, non-null constraints, and referential integrity
- **Infrastructure as code** — Entire environment defined in `docker-compose.yml` and `.env`

---

## Build Status

| Phase | Status | Description |
|-------|--------|-------------|
| 1 — Infrastructure | ✅ Done | Docker, Postgres, pgAdmin |
| 2 — Ingestion | ✅ Done | Python extracts Yahoo Finance → raw schema |
| 3 — Orchestration | 🔧 In Progress | Airflow DAG defined, pending verification |
| 4 — Transformation | ⬜ Planned | dbt staging → intermediate → marts |
| 5 — Visualization | ⬜ Planned | Metabase dashboard |
