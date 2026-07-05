import os
import io
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

LOCAL_PATH = Path(__file__).resolve().parent.parent / "data" / "raw" / "online_retail.csv"


def extract_from_s3() -> pd.DataFrame:
    """Pull raw CSV directly from S3 bucket into a DataFrame."""
    import boto3

    s3 = boto3.client(
        "s3",
        region_name=os.getenv("AWS_REGION"),
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    )

    bucket = os.getenv("S3_BUCKET")
    key    = os.getenv("S3_KEY")

    print(f"Extracting from S3: s3://{bucket}/{key}")
    response = s3.get_object(Bucket=bucket, Key=key)
    content  = response["Body"].read()

    df = pd.read_csv(io.BytesIO(content), encoding="latin1")
    return df


def extract_from_local(filepath: Path = LOCAL_PATH) -> pd.DataFrame:
    """Fallback: read from local file."""
    print(f"Extracting from local: {filepath}")
    if filepath.suffix == ".xlsx":
        return pd.read_excel(filepath)
    return pd.read_csv(filepath, encoding="latin1")


def extract_sales_data() -> pd.DataFrame:
    """
    Extract raw sales data.
    Uses S3 if AWS credentials are configured, otherwise falls back to local.
    """
    use_s3 = all([
        os.getenv("AWS_ACCESS_KEY_ID"),
        os.getenv("AWS_SECRET_ACCESS_KEY"),
        os.getenv("S3_BUCKET"),
    ])

    if use_s3:
        df = extract_from_s3()
    else:
        df = extract_from_local()

    print(f"Extracted {len(df)} rows, {len(df.columns)} columns")
    print(f"Columns: {list(df.columns)}")
    return df


if __name__ == "__main__":
    df = extract_sales_data()
    print(df.head())