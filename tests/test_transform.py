import pandas as pd
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from etl.transform import transform_sales_data

@pytest.fixture
def raw_sample():
    """Minimal raw DataFrame mimicking the Online Retail dataset."""
    return pd.DataFrame({
        "InvoiceNo":   ["536365", "536365", "C536379", "536370", "536370"],
        "StockCode":   ["85123A", "71053",  "85123A",  "22752",  "22752"],
        "Description": ["WHITE HEART", "LANTERN", "WHITE HEART", "CAKE STAND", None],
        "Quantity":    [6, 6, -6, 12, 12],
        "InvoiceDate": ["12/1/2010 8:26", "12/1/2010 8:26",
                        "12/1/2010 9:00", "12/1/2010 9:12", "12/1/2010 9:12"],
        "UnitPrice":   [2.55, 3.39, 2.55, 1.95, 1.95],
        "CustomerID":  [17850.0, 17850.0, 17850.0, None, None],
        "Country":     ["United Kingdom"] * 5,
    })


def test_row_count_drops_null_description(raw_sample):
    """Row with null Description should be dropped."""
    result = transform_sales_data(raw_sample)
    assert len(result) == 4  # 1 null description dropped


def test_cancelled_invoice_flagged(raw_sample):
    """Invoice starting with C must be flagged as cancelled."""
    result = transform_sales_data(raw_sample)
    cancelled = result[result["invoice_no"] == "C536379"]
    assert len(cancelled) == 1
    assert cancelled.iloc[0]["is_cancelled"] == True


def test_return_flagged_on_negative_quantity(raw_sample):
    """Negative quantity rows must be flagged as returns."""
    result = transform_sales_data(raw_sample)
    returns = result[result["is_return"] == True]
    assert len(returns) == 1


def test_guest_customer_filled(raw_sample):
    """Null CustomerID must become GUEST, not NaN."""
    result = transform_sales_data(raw_sample)
    assert "GUEST" in result["customer_id"].values
    assert result["customer_id"].isna().sum() == 0


def test_revenue_computed_correctly(raw_sample):
    """Revenue must equal quantity × unit_price."""
    result = transform_sales_data(raw_sample)
    row = result[result["stock_code"] == "85123A"].iloc[0]
    assert round(row["revenue"], 2) == round(6 * 2.55, 2)


def test_invoice_date_is_datetime(raw_sample):
    """InvoiceDate must be parsed to datetime, not remain a string."""
    result = transform_sales_data(raw_sample)
    assert pd.api.types.is_datetime64_any_dtype(result["invoice_date"])


def test_column_names_are_snake_case(raw_sample):
    """All columns must be lowercase snake_case after transform."""
    result = transform_sales_data(raw_sample)
    for col in result.columns:
        assert col == col.lower(), f"Column '{col}' is not lowercase"