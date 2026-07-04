import time
from extract import extract_sales_data
from transform import transform_sales_data
from data_quality import DataQualityReport
from load import load_all

def run():
    start = time.time()
    print("=" * 45)
    print("  RetailPulse ETL Pipeline — Starting")
    print("=" * 45)

    print("\n[1/4] Extracting...")
    raw = extract_sales_data()

    print("\n[2/4] Transforming...")
    clean = transform_sales_data(raw)

    print("\n[3/4] Running Data Quality Checks...")
    report = DataQualityReport(clean)
    report.run_all()
    report.print_report()

    print("\n[4/4] Loading to Warehouse...")
    load_all(clean)

    elapsed = round(time.time() - start, 2)
    print(f"\nPipeline finished in {elapsed}s ✓")

if __name__ == "__main__":
    run()