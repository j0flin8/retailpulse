import pandas as pd
from pathlib import Path

RAW_DATA_PATH = Path("data/raw/online_retail.csv")

def extract_sales_data(filepath: Path = RAW_DATA_PATH) -> pd.DataFrame:
    """Extract raw sales data from CSV source."""
    if filepath.suffix == ".xlsx":
        df = pd.read_excel(filepath)
    else:
        df = pd.read_csv(filepath, encoding="latin1")  # this dataset often needs latin1 encoding
    
    print(f"Extracted {len(df)} rows, {len(df.columns)} columns")
    print(f"Columns: {list(df.columns)}")
    return df

if __name__ == "__main__":
    df = extract_sales_data()
    print(df.head())
    print(df.info())