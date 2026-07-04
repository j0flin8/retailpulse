from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from api.database import get_db
from api.models import HealthResponse
from api.routers import sales, products

app = FastAPI(
    title="RetailPulse Analytics API",
    description="Sales analytics API built on an ETL pipeline over the Online Retail dataset.",
    version="1.0.0"
)

app.include_router(sales.router)
app.include_router(products.router)

@app.get("/health", response_model=HealthResponse, tags=["System"])
def health_check(db: Session = Depends(get_db)):
    """Check API health and DB connectivity."""
    try:
        count = db.execute(text("SELECT COUNT(*) FROM fact_sales")).scalar()
        return HealthResponse(status="ok", db_connected=True, total_sales_records=count)
    except Exception:
        return HealthResponse(status="degraded", db_connected=False, total_sales_records=0)