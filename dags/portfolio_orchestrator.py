from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator

# Default arguments for the Airflow DAG
default_args = {
    'owner': 'data_engineer',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=2),
}

# Define the DAG
with DAG(
    'portfolio_analytics_pipeline',
    default_args=default_args,
    description='End-to-end portfolio analytics ETL pipeline',
    schedule_interval='0 18 * * 1-5',  # Run at 6 PM EST Monday to Friday (market close)
    start_date=datetime(2026, 1, 1),
    catchup=False,
) as dag:

    # Task 1: Ingest stock prices from Yahoo Finance
    # Inside the Docker network, the Postgres database is reachable at the host name 'postgres'
    ingest_stock_data = BashOperator(
        task_id='ingest_stock_data',
        bash_command='POSTGRES_HOST=postgres POSTGRES_PORT=5432 python /opt/airflow/scripts/extract_data.py',
    )
