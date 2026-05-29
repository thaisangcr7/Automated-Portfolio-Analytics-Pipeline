import os
import argparse
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text

# Tickers to fetch (Tech + Finance/Citi)
DEFAULT_TICKERS = ["AAPL", "MSFT", "GOOG", "JPM", "C"]

def get_db_engine():
    """
    Establish connection to PostgreSQL using environment variables.
    """
    db_user = os.getenv("POSTGRES_USER", "postgres")
    db_pass = os.getenv("POSTGRES_PASSWORD", "postgres")
    db_host = os.getenv("POSTGRES_HOST", "localhost")
    db_port = os.getenv("POSTGRES_PORT", "5432")
    db_name = os.getenv("POSTGRES_DB", "portfolio_db")
    
    connection_uri = f"postgresql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"
    return create_engine(connection_uri)

def extract_stock_data(tickers, start_date, end_date):
    """
    Fetch historical stock prices from Yahoo Finance API.
    """
    print(f"Fetching data for {tickers} from {start_date} to {end_date}...")
    all_data = []
    
    for ticker in tickers:
        try:
            # Download stock data
            df = yf.download(ticker, start=start_date, end=end_date)
            if df.empty:
                print(f"No data returned for ticker {ticker}")
                continue
                
            # Reset index to move 'Date' from index to column
            df = df.reset_index()
            
            # Handle MultiIndex columns (common in newer yfinance versions)
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
                
            df['ticker'] = ticker
            
            # Standardize column names (lower case, no spaces)
            df.columns = [str(col).lower().replace(" ", "_") for col in df.columns]
            
            # Add extraction timestamp (crucial for staging deduplication in dbt)
            df['extracted_at'] = datetime.now()
            
            all_data.append(df)
        except Exception as e:
            print(f"Error fetching data for ticker {ticker}: {str(e)}")
            
    if not all_data:
        print("No stock data was fetched successfully.")
        return pd.DataFrame()
        
    return pd.concat(all_data, ignore_index=True)

def load_data_to_postgres(df, table_name, schema_name="raw"):
    """
    Load Pandas DataFrame into PostgreSQL database under raw schema.
    """
    if df.empty:
        print("Empty DataFrame. Skipping load step.")
        return
        
    engine = get_db_engine()
    
    # Create the schema if it does not exist
    with engine.begin() as conn:
        conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema_name};"))
        
    # Write to SQL
    print(f"Loading {len(df)} rows into {schema_name}.{table_name}...")
    df.to_sql(
        name=table_name,
        con=engine,
        schema=schema_name,
        if_exists="append", # Simple append pattern; we will deduplicate in dbt
        index=False,
        method="multi"
    )
    print("Load completed successfully.")

def main():
    parser = argparse.ArgumentParser(description="Extract stock price data from Yahoo Finance and load to Postgres.")
    parser.add_argument("--tickers", nargs="+", default=DEFAULT_TICKERS, help="List of tickers to fetch")
    parser.add_argument("--start-date", help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end-date", help="End date (YYYY-MM-DD)")
    parser.add_argument("--backfill", action="store_true", help="Load historical data (last 365 days)")
    
    args = parser.parse_args()
    
    # Calculate dates based on args
    if args.backfill:
        # Load one year of historical data
        start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
        end_date = datetime.now().strftime("%Y-%m-%d")
    else:
        # Pull last 5 days of data to cover weekends and holidays
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=5)).strftime("%Y-%m-%d")
        
    if args.start_date:
        start_date = args.start_date
    if args.end_date:
        end_date = args.end_date
        
    df = extract_stock_data(args.tickers, start_date, end_date)
    load_data_to_postgres(df, "stock_prices")

if __name__ == "__main__":
    main()
