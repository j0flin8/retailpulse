import os
import pandas as pd
from sqlalchemy import (
    create_engine, MetaData, Table, Column,
    String, Integer, Float, DateTime, Boolean, Date, ForeignKey, text
)
from dotenv import load_dotenv
from pathlib import Path

# Load env vars
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

def get_engine():
    url = (
        f"postgresql+psycopg2://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
        f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
    )
    return create_engine(url)


def create_schema(engine):
    """Create all star schema tables if they don't exist."""
    meta = MetaData()

    Table("dim_date", meta,
        Column("date_key", Integer, primary_key=True),   # YYYYMMDD int e.g. 20101201
        Column("full_date", Date, nullable=False),
        Column("year", Integer),
        Column("month", Integer),
        Column("day", Integer),
        Column("quarter", Integer),
        Column("day_of_week", Integer),
        Column("week_of_year", Integer),
    )

    Table("dim_product", meta,
        Column("stock_code", String(20), primary_key=True),
        Column("description", String(255)),
    )

    Table("dim_customer", meta,
        Column("customer_id", String(20), primary_key=True),
        Column("country", String(100)),
        Column("is_guest", Boolean, default=False),
    )

    Table("fact_sales", meta,
        Column("id", Integer, primary_key=True, autoincrement=True),
        Column("invoice_no", String(20)),
        Column("stock_code", String(20),ForeignKey("dim_product.stock_code"), nullable=False),       # FK → dim_product
        Column("customer_id", String(20)),      # FK → dim_customer
        Column("date_key",Integer,ForeignKey("dim_date.date_key"),nullable=False),            # FK → dim_date
        Column("invoice_date", DateTime),
        Column("quantity", Integer),
        Column("unit_price", Float),
        Column("revenue", Float),
        Column("country", String(100)),
        Column("is_cancelled", Boolean),
        Column("is_return", Boolean),
        Column("is_guest", Boolean),
    )

    meta.create_all(engine, checkfirst=True)
    with engine.begin() as conn:

        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_fact_date
            ON fact_sales(date_key)
        """))

        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_fact_customer
            ON fact_sales(customer_id)
        """))

        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_fact_product
            ON fact_sales(stock_code)
        """))

        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_fact_invoice
            ON fact_sales(invoice_no)
        """))
    print("Schema created successfully.")


def build_dim_date(df: pd.DataFrame) -> pd.DataFrame:
    """Build date dimension from all unique dates in the dataset."""
    dates = df["invoice_date"].dropna().dt.date
    dates = pd.Series(dates.unique(), name="full_date")
    dim = pd.DataFrame({"full_date": pd.to_datetime(dates)})
    dim["date_key"] = dim["full_date"].dt.strftime("%Y%m%d").astype(int)
    dim["year"] = dim["full_date"].dt.year
    dim["month"] = dim["full_date"].dt.month
    dim["day"] = dim["full_date"].dt.day
    dim["quarter"] = dim["full_date"].dt.quarter
    dim["day_of_week"] = dim["full_date"].dt.dayofweek
    dim["week_of_year"] = dim["full_date"].dt.isocalendar().week.astype(int)
    dim["full_date"] = dim["full_date"].dt.date
    return dim.drop_duplicates(subset=["date_key"])


def build_dim_product(df: pd.DataFrame) -> pd.DataFrame:
    """Build product dimension — one row per stock_code."""
    dim = (
        df[["stock_code", "description"]]
        .dropna(subset=["stock_code"])
        .drop_duplicates(subset=["stock_code"])
        .sort_values("stock_code")
        .reset_index(drop=True)
    )
    return dim


def build_dim_customer(df: pd.DataFrame) -> pd.DataFrame:
    """Build customer dimension — one row per customer_id."""
    dim = (
        df[["customer_id", "country", "is_guest"]]
        .drop_duplicates(subset=["customer_id"])
        .sort_values("customer_id")
        .reset_index(drop=True)
    )
    return dim


def build_fact_sales(df: pd.DataFrame) -> pd.DataFrame:
    """Build fact table with FK keys attached."""
    fact = df.copy()
    fact["date_key"] = fact["invoice_date"].dt.strftime("%Y%m%d").astype("Int64")
    fact = fact[[
        "invoice_no", "stock_code", "customer_id", "date_key",
        "invoice_date", "quantity", "unit_price", "revenue",
        "country", "is_cancelled", "is_return", "is_guest"
    ]]
    return fact


def load_table(df: pd.DataFrame, table_name: str, engine):
    """
    Load a DataFrame into Postgres safely:
    - First run: table already created by create_schema() with proper constraints
    - Uses 'append' so constraints are never dropped
    - Truncates first to avoid duplicates on re-runs
    """
    with engine.connect() as conn:
        conn.execute(text(f"TRUNCATE TABLE {table_name} CASCADE"))
        conn.commit()

    df.to_sql(
        table_name, engine,
        if_exists="append",   # append into existing schema, never replace it
        index=False,
        method="multi",
        chunksize=1000
    )
    print(f"Loaded {len(df):,} rows → {table_name}")


def load_all(df: pd.DataFrame):
    engine = get_engine()
    create_schema(engine)   # creates tables only if they don't exist (safe to re-run)

    print("\nBuilding dimension tables...")
    dim_date     = build_dim_date(df)
    dim_product  = build_dim_product(df)
    dim_customer = build_dim_customer(df)
    fact_sales   = build_fact_sales(df)

    print("\nLoading into Postgres...")
    # Load dims first (fact table references them)
    load_table(dim_date,     "dim_date",     engine)
    load_table(dim_product,  "dim_product",  engine)
    load_table(dim_customer, "dim_customer", engine)
    load_table(fact_sales,   "fact_sales",   engine)

    # Verification
    with engine.connect() as conn:
        for table in ["dim_date", "dim_product", "dim_customer", "fact_sales"]:
            count = conn.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
            print(f"  ✓ {table}: {count:,} rows in DB")

    print("\nLoad complete.")

if __name__ == "__main__":
    from extract import extract_sales_data
    from transform import transform_sales_data

    raw = extract_sales_data()
    clean = transform_sales_data(raw)
    load_all(clean)