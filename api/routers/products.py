from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from api.database import get_db
from api.models import TopProductsResponse

router = APIRouter(prefix="/products", tags=["Products"])

@router.get("/top", response_model=TopProductsResponse)
def get_top_products(
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Top N products by total revenue (excludes returns/cancellations)."""
    sql = text("""
        SELECT
            f.stock_code,
            p.description,
            ROUND(SUM(f.revenue)::numeric, 2) AS total_revenue,
            SUM(f.quantity)                   AS total_quantity
        FROM fact_sales f
        JOIN dim_product p ON f.stock_code = p.stock_code
        WHERE f.is_cancelled = FALSE AND f.is_return = FALSE
        GROUP BY f.stock_code, p.description
        ORDER BY total_revenue DESC
        LIMIT :limit
    """)
    rows = db.execute(sql, {"limit": limit}).fetchall()
    return TopProductsResponse(
        limit=limit,
        data=[dict(r._mapping) for r in rows]
    )