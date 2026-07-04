from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from api.database import get_db
from api.models import (
    SalesSummaryResponse, MonthlySalesResponse,
    CustomerHistoryResponse, IngestSaleRequest, IngestSaleResponse
)
from typing import Optional
from datetime import datetime

router = APIRouter(prefix="/sales", tags=["Sales"])


@router.get("/summary", response_model=SalesSummaryResponse)
def get_sales_summary(
    start_date: Optional[str] = Query(None, example="2011-01-01"),
    end_date: Optional[str] = Query(None, example="2011-12-31"),
    db: Session = Depends(get_db)
):
    """Revenue + order count, optionally filtered by date range."""
    where = "WHERE is_cancelled = FALSE AND is_return = FALSE"
    params = {}

    if start_date:
        where += " AND invoice_date >= :start_date"
        params["start_date"] = start_date
    if end_date:
        where += " AND invoice_date <= :end_date"
        params["end_date"] = end_date

    sql = text(f"""
        SELECT
            ROUND(SUM(revenue)::numeric, 2)         AS total_revenue,
            COUNT(DISTINCT invoice_no)               AS total_orders,
            SUM(quantity)                            AS total_items_sold
        FROM fact_sales
        {where}
    """)

    row = db.execute(sql, params).fetchone()
    total_revenue = float(row.total_revenue or 0)
    total_orders = int(row.total_orders or 0)
    avg_order_value = round(total_revenue / total_orders, 2) if total_orders > 0 else 0.0

    return SalesSummaryResponse(
        start_date=start_date,
        end_date=end_date,
        total_revenue=total_revenue,
        total_orders=total_orders,
        total_items_sold=int(row.total_items_sold or 0),
        avg_order_value=avg_order_value
    )


@router.get("/monthly", response_model=MonthlySalesResponse)
def get_monthly_sales(db: Session = Depends(get_db)):
    """Monthly revenue trend across full dataset."""
    sql = text("""
        SELECT
            d.year,
            d.month,
            ROUND(SUM(f.revenue)::numeric, 2) AS revenue,
            COUNT(DISTINCT f.invoice_no)       AS orders
        FROM fact_sales f
        JOIN dim_date d ON f.date_key = d.date_key
        WHERE f.is_cancelled = FALSE AND f.is_return = FALSE
        GROUP BY d.year, d.month
        ORDER BY d.year, d.month
    """)
    rows = db.execute(sql).fetchall()
    return MonthlySalesResponse(
        data=[{"year": r.year, "month": r.month,
               "revenue": float(r.revenue), "orders": r.orders}
              for r in rows]
    )


@router.get("/customers/{customer_id}/history", response_model=CustomerHistoryResponse)
def get_customer_history(customer_id: str, db: Session = Depends(get_db)):
    """Full order history for a specific customer."""
    sql = text("""
        SELECT
            f.invoice_no, f.invoice_date, f.stock_code,
            p.description, f.quantity, f.unit_price,
            f.revenue, f.is_cancelled, f.is_return
        FROM fact_sales f
        LEFT JOIN dim_product p ON f.stock_code = p.stock_code
        WHERE f.customer_id = :cid
        ORDER BY f.invoice_date DESC
    """)
    rows = db.execute(sql, {"cid": customer_id}).fetchall()
    if not rows:
        raise HTTPException(status_code=404, detail=f"Customer '{customer_id}' not found")

    total_revenue = round(sum(r.revenue for r in rows if not r.is_cancelled and not r.is_return), 2)
    return CustomerHistoryResponse(
        customer_id=customer_id,
        total_orders=len(set(r.invoice_no for r in rows)),
        total_revenue=total_revenue,
        data=[dict(r._mapping) for r in rows]
    )


@router.post("/ingest", response_model=IngestSaleResponse, status_code=201)
def ingest_sale(payload: IngestSaleRequest, db: Session = Depends(get_db)):
    """Accept and insert a new validated sale record."""
    revenue = round(payload.quantity * payload.unit_price, 2)

    # Upsert dim_product if new
    db.execute(text("""
        INSERT INTO dim_product (stock_code, description)
        VALUES (:sc, :desc)
        ON CONFLICT (stock_code) DO NOTHING
    """), {"sc": payload.stock_code, "desc": payload.description})

    # Upsert dim_customer if new
    is_guest = payload.customer_id == "GUEST"
    db.execute(text("""
        INSERT INTO dim_customer (customer_id, country, is_guest)
        VALUES (:cid, :country, :guest)
        ON CONFLICT (customer_id) DO NOTHING
    """), {"cid": payload.customer_id, "country": payload.country, "guest": is_guest})

    # Insert fact row
    date_key = db.execute(text("""
                INSERT INTO dim_date
                (date_key, full_date, year, month, day, quarter, day_of_week, week_of_year)

                VALUES

                (
                :dk,
                :fd,
                :year,
                :month,
                :day,
                :quarter,
                :dow,
                :week
                )

                ON CONFLICT (date_key)

                DO NOTHING
                """),
                {
                "dk": date_key,
                "fd": payload.invoice_date.date(),
                "year": payload.invoice_date.year,
                "month": payload.invoice_date.month,
                "day": payload.invoice_date.day,
                "quarter": ((payload.invoice_date.month-1)//3)+1,
                "dow": payload.invoice_date.weekday(),
                "week": payload.invoice_date.isocalendar()[1]
                })

    return IngestSaleResponse(
        message="Sale record ingested successfully",
        invoice_no=payload.invoice_no,
        revenue=revenue
    )