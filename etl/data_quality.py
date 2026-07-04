import pandas as pd

class DataQualityReport:
    def __init__(self, df: pd.DataFrame):
        self.df = df
        self.issues = []

    def check_nulls(self, columns: list[str]):
        for col in columns:
            null_count = self.df[col].isna().sum()
            if null_count > 0:
                self.issues.append(f"Column '{col}' has {null_count} null values")

    def check_negative_prices(self):
        bad = (self.df["unit_price"] < 0).sum()
        if bad > 0:
            self.issues.append(f"{bad} rows have negative unit_price")

    def check_zero_prices(self):
        zero = (self.df["unit_price"] == 0).sum()
        if zero > 0:
            self.issues.append(f"{zero} rows have unit_price == 0 (likely bad/adjustment records)")

    def check_duplicate_line_items(self):
        invoice_product_dupes = self.df.duplicated(
            subset=["invoice_no", "stock_code"]
        ).sum()

        duplicate_groups = self.df.duplicated(keep=False).sum()
        removable_duplicates = self.df.duplicated().sum()

        if invoice_product_dupes:
            self.issues.append(
                f"{invoice_product_dupes} duplicate invoice/stock_code line items found"
            )

        if duplicate_groups:
            self.issues.append(
                f"{duplicate_groups} rows participate in exact duplicate groups"
            )

        if removable_duplicates:
            self.issues.append(
                f"{removable_duplicates} duplicate rows will be removed during load"
            )
            
    def check_date_range(self):
        min_date, max_date = self.df["invoice_date"].min(), self.df["invoice_date"].max()
        self.issues.append(f"Date range: {min_date} to {max_date}")

    def run_all(self):
        self.check_nulls(["description", "invoice_date"])
        self.check_negative_prices()
        self.check_zero_prices()
        self.check_duplicate_line_items()
        self.check_date_range()
        return self.issues

    def print_report(self):
        print("\n=== DATA QUALITY REPORT ===")
        for issue in self.issues:
            print(f"  - {issue}")
        print("============================\n")


if __name__ == "__main__":
    from extract import extract_sales_data
    from transform import transform_sales_data

    raw = extract_sales_data()
    clean = transform_sales_data(raw)

    report = DataQualityReport(clean)
    report.run_all()
    report.print_report()