# RetailPulse 🛒📊
### End-to-End Sales Analytics ETL Platform

A production-style data engineering project that ingests raw e-commerce sales data, runs it through a multi-stage ETL pipeline, loads it into a PostgreSQL data warehouse, and exposes business insights through a REST API — fully containerized and deployed with CI/CD.
---

## Architecture

```
AWS S3 (raw CSV)
      │
      ▼
 extract.py          ← Pull data from S3 (or local fallback)
      │
      ▼
 transform.py        ← Clean, enrich, flag anomalies (Pandas)
      │
      ▼
 data_quality.py     ← Audit report: nulls, dupes, price issues
      │
      ▼
 load.py             ← Star schema upsert into PostgreSQL
      │
      ▼
 PostgreSQL           ← dim_date, dim_product, dim_customer, fact_sales
      │
      ▼
 FastAPI              ← REST API serving analytics endpoints
```

---

## Tech Stack

| Layer            | Technology                          |
|------------------|-------------------------------------|
| Cloud Storage    | AWS S3, boto3                       |
| Extraction       | Python, pandas                      |
| Transformation   | Pandas                              |
| Data Quality     | Custom `DataQualityReport` class    |
| Warehousing      | PostgreSQL 16, SQLAlchemy           |
| API              | FastAPI, Pydantic, Uvicorn          |
| Containerization | Docker, Docker Compose              |
| CI/CD            | GitHub Actions                      |
| Version Control  | Git, GitHub                         |

---

## Dataset

- **Source:** [Kaggle Online Retail Dataset](https://www.kaggle.com/datasets/vijayuv/onlineretail)
- **Raw records:** 541,909 rows across 8 columns
- **After cleaning:** 535,184 rows (nulls dropped, exact dupes removed)
- **Date range:** December 2010 – December 2011 (UK e-commerce retailer)
- **Data issues found:** 2 negative prices, 1,056 zero-price records, 5,271 exact duplicate rows, 9,288 cancelled invoices, 133,626 guest orders

---

## Star Schema

```
              ┌─────────────┐
              │  dim_date   │
              │─────────────│
              │ date_key PK │
              │ full_date   │
              │ year        │
              │ month       │
              │ quarter     │
              └──────┬──────┘
                     │
┌──────────────┐     │     ┌────────────────┐
│ dim_product  │     │     │  dim_customer  │
│──────────────│     │     │────────────────│
│ stock_code PK│     │     │ customer_id PK │
│ description  │     │     │ country        │
└──────┬───────┘     │     │ is_guest       │
       │             │     └───────┬────────┘
       │      ┌──────▼──────┐      │
       └──────►  fact_sales ◄──────┘
              │─────────────│
              │ id PK       │
              │ invoice_no  │
              │ stock_code  │
              │ customer_id │
              │ date_key    │
              │ quantity    │
              │ unit_price  │
              │ revenue     │
              │ is_cancelled│
              │ is_return   │
              └─────────────┘

dim_date:      305 rows   (unique trading days)
dim_product:  3,958 rows  (unique products)
dim_customer: 4,373 rows  (unique customers + guests)
fact_sales:  535,184 rows (transaction line items)
```

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | API health check + DB connectivity + record count |
| `GET` | `/sales/summary` | Total revenue, orders, items sold (filterable by date) |
| `GET` | `/sales/monthly` | Monthly revenue trend across full dataset |
| `GET` | `/products/top?limit=N` | Top N products by revenue (excludes returns) |
| `GET` | `/sales/customers/{id}/history` | Full order history for a customer |
| `POST` | `/sales/ingest` | Validate and ingest a new sale record |

### Example responses

**GET /sales/summary?start_date=2011-01-01&end_date=2011-06-30**
```json
{
  "start_date": "2011-01-01",
  "end_date": "2011-06-30",
  "total_revenue": 3950606.18,
  "total_orders": 8061,
  "total_items_sold": 2127952,
  "avg_order_value": 490.09
}
```

**GET /products/top?limit=3**
```json
{
  "limit": 3,
  "data": [
    { "stock_code": "DOT", "description": "DOTCOM POSTAGE", "total_revenue": 206248.77, "total_quantity": 708 },
    { "stock_code": "22423", "description": "REGENCY CAKESTAND 3 TIER", "total_revenue": 174132.30, "total_quantity": 10992 }
  ]
}
```

---

## Project Structure

```
retailpulse/
├── etl/
│   ├── extract.py          # S3 + local extraction
│   ├── transform.py        # Pandas cleaning + enrichment
│   ├── data_quality.py     # Audit report
│   ├── load.py             # Star schema creation + upsert
│   └── run_pipeline.py     # Single-command ETL orchestrator
├── api/
│   ├── main.py             # FastAPI app entry point
│   ├── database.py         # SQLAlchemy engine + session
│   ├── models.py           # Pydantic request/response schemas
│   └── routers/
│       ├── sales.py        # /sales/* endpoints
│       └── products.py     # /products/* endpoints
├── tests/
│   └── test_transform.py   # 7 pytest unit tests
├── .github/
│   └── workflows/
│       └── ci.yml          # GitHub Actions: lint + test + Docker build
├── docker-compose.yml      # FastAPI + PostgreSQL stack
├── Dockerfile
├── requirements.txt
└── .env.example
```

---

## Quick Start

### Prerequisites
- Docker Desktop installed
- Python 3.10+
- AWS account with S3 bucket (or skip for local mode)

### 1. Clone the repo

```bash
git clone https://github.com/j0flin8/retailpulse.git
cd retailpulse
```

### 2. Configure environment

```bash
cp .env.example .env
# Fill in your DB credentials and AWS keys
```

### 3. Start the full stack

```bash
docker-compose up --build
```

This starts both PostgreSQL and the FastAPI server. The API will be live at `http://localhost:8000`.

### 4. Run the ETL pipeline

```bash
python etl/run_pipeline.py
```

Expected output:
```
[1/4] Extracting...   541,909 rows
[2/4] Transforming... 535,184 rows after cleaning
[3/4] Quality checks... report printed
[4/4] Loading...
  ✓ dim_date:      305 rows
  ✓ dim_product:  3,958 rows
  ✓ dim_customer: 4,373 rows
  ✓ fact_sales:  535,184 rows
Pipeline finished in ~248s ✓
```

### 5. Explore the API

```
http://localhost:8000/docs
```

---

## Running Tests

```bash
pytest tests/ -v
```

```
tests/test_transform.py::test_row_count_drops_null_description  PASSED
tests/test_transform.py::test_cancelled_invoice_flagged         PASSED
tests/test_transform.py::test_return_flagged_on_negative_quantity PASSED
tests/test_transform.py::test_guest_customer_filled             PASSED
tests/test_transform.py::test_revenue_computed_correctly        PASSED
tests/test_transform.py::test_invoice_date_is_datetime          PASSED
tests/test_transform.py::test_column_names_are_snake_case       PASSED

7 passed in 0.42s
```

---

## CI/CD Pipeline

Every push to `main` triggers:

```
Push → Install deps → flake8 lint → pytest (7 tests) → Docker build
                                                              ↑
                                              Only runs if tests pass
```

---

## Key Engineering Decisions

**Flag, don't delete** — Cancellations, returns, and guest orders are preserved with boolean flags rather than discarded. Real warehouses never silently lose information.

**Schema-first loading** — `create_schema()` with `checkfirst=True` runs before every load. Data is inserted via `TRUNCATE + append`, never `replace`, so FK constraints and indexes are never dropped.

**S3 with local fallback** — `extract.py` checks for AWS credentials at runtime. If present, it pulls from S3. If not, it reads from local disk. Same codebase works in development and production.

**Transaction safety** — The `/sales/ingest` endpoint wraps all 4 inserts (dim_date, dim_product, dim_customer, fact_sales) in a single `with db.begin()` block. If any insert fails, all roll back.

**Indexed fact table** — Indexes on `date_key`, `customer_id`, `stock_code`, and `invoice_no` mean customer history and product queries don't scan all 535,184 rows.

---

## Future Improvements

- Swap `chunksize=1000` bulk insert for PostgreSQL `COPY` command (~10x faster load)
- Add Airflow or Prefect for pipeline scheduling
- Deploy FastAPI to AWS EC2 or Azure App Service
- Add Redis caching for `/products/top` (rarely changing, frequently queried)
- Implement pagination on `/customers/{id}/history` for large accounts

---

## Author

**Joe Flinton**
B.Tech Computer Science — SRM Institute of Science and Technology, 2026
Abu Dhabi, UAE

[LinkedIn](https://www.linkedin.com/in/joe-flinton-283194284/) · [GitHub](https://github.com/j0flin8)
