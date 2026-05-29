from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator

default_args = {
    'owner': 'data_engineer',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=2),
}

# dbt runs inside the Docker network, so it uses the 'docker' profile (host: postgres)
DBT_CMD = "dbt --no-write-json {command} --target docker --profiles-dir /opt/airflow/dbt_project --project-dir /opt/airflow/dbt_project"

with DAG(
    'portfolio_analytics_pipeline',
    default_args=default_args,
    description='End-to-end portfolio analytics pipeline: ingest → seed → transform → test',
    schedule_interval='0 18 * * 1-5',  # 6 PM EST Monday–Friday (after market close)
    start_date=datetime(2026, 1, 1),
    catchup=False,
) as dag:

    # Task 1: Pull fresh stock prices from Yahoo Finance into raw.stock_prices
    ingest_stock_data = BashOperator(
        task_id='ingest_stock_data',
        bash_command='POSTGRES_HOST=postgres POSTGRES_PORT=5432 python /opt/airflow/scripts/extract_data.py',
    )

    # Task 2: Load static seed data (portfolio_holdings.csv → analytics.stg_portfolio_holdings)
    # dbt seed is idempotent — safe to run every day even though the data doesn't change
    dbt_seed = BashOperator(
        task_id='dbt_seed',
        bash_command=DBT_CMD.format(command='seed'),
    )

    # Task 3: Run all dbt models — staging → intermediate → marts
    # Transforms raw prices into the star schema (dim_companies + fct_portfolio_valuation)
    dbt_run = BashOperator(
        task_id='dbt_run',
        bash_command=DBT_CMD.format(command='run'),
    )

    # Task 4: Run all 26 data quality tests — fails the DAG if any test fails
    dbt_test = BashOperator(
        task_id='dbt_test',
        bash_command=DBT_CMD.format(command='test'),
    )

    # Pipeline order: fresh data → load seeds → transform → validate
    ingest_stock_data >> dbt_seed >> dbt_run >> dbt_test
