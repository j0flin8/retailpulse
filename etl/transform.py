import pandas as pd
import numpy as np

def transform_sales_data(df: pd.DataFrame) -> pd.DataFrame:
    """Clean and enrich raw sales data."""
    df = df.copy()

    # 1. Standardize column names (lowercase, snake_case)
    df.columns = [c.strip().lower() for c in df.columns]

    # 2. Parse date
    df["invoicedate"] = pd.to_datetime(df["invoicedate"], format="%m/%d/%Y %H:%M", errors="coerce")

    # 3. Flag cancelled invoices (InvoiceNo starting with 'C')
    df["is_cancelled"] = df["invoiceno"].astype(str).str.startswith("C")

    # 4. Flag guest customers (missing CustomerID)
    df["is_guest"] = df["customerid"].isna()
    df["customerid"] = df["customerid"].fillna(-1).astype(int).astype(str)
    df.loc[df["customerid"] == "-1", "customerid"] = "GUEST"

    # 5. Drop rows with missing description (can't sell an unnamed product)
    df = df.dropna(subset=["description"])
    df["description"] = df["description"].str.strip()

    # 6. Compute revenue
    df["revenue"] = df["quantity"] * df["unitprice"]

    # 7. Separate returns (negative quantity) — flag, don't drop
    df["is_return"] = df["quantity"] < 0

    # 8. Rename columns to clean final schema
    df = df.rename(columns={
        "invoiceno": "invoice_no",
        "stockcode": "stock_code",
        "unitprice": "unit_price",
        "customerid": "customer_id",
        "invoicedate": "invoice_date",
    })

    print(f"Transformed: {len(df)} rows remain")
    print(f"Cancelled invoices: {df['is_cancelled'].sum()}")
    print(f"Guest orders: {df['is_guest'].sum()}")
    print(f"Returns: {df['is_return'].sum()}")
    # Drop exact duplicate rows (same invoice + stock + qty + price)
    before = len(df)
    df = df.drop_duplicates(subset=["invoice_no", "stock_code", "quantity", "unit_price"])
    print(f"Dropped {before - len(df)} exact duplicate rows. Final: {len(df)} rows")
    return df

if __name__ == "__main__":
    from extract import extract_sales_data
    raw = extract_sales_data()
    clean = transform_sales_data(raw)
    print(clean.head())
    print(clean.dtypes)