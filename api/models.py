from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Optional

# ── Response schemas ──────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str
    db_connected: bool
    total_sales_records: int

class SalesSummaryResponse(BaseModel):
    start_date: Optional[str]
    end_date: Optional[str]
    total_revenue: float
    total_orders: int
    total_items_sold: int
    avg_order_value: float

class MonthlySalesItem(BaseModel):
    year: int
    month: int
    revenue: float
    orders: int

class MonthlySalesResponse(BaseModel):
    data: list[MonthlySalesItem]

class TopProductItem(BaseModel):
    stock_code: str
    description: str
    total_revenue: float
    total_quantity: int

class TopProductsResponse(BaseModel):
    limit: int
    data: list[TopProductItem]

class CustomerOrderItem(BaseModel):
    invoice_no: str
    invoice_date: datetime
    stock_code: str
    description: Optional[str]
    quantity: int
    unit_price: float
    revenue: float
    is_cancelled: bool
    is_return: bool

class CustomerHistoryResponse(BaseModel):
    customer_id: str
    total_orders: int
    total_revenue: float
    data: list[CustomerOrderItem]

# ── Request schemas ───────────────────────────────────────────

class IngestSaleRequest(BaseModel):
    invoice_no: str = Field(..., min_length=1, max_length=20)
    stock_code: str = Field(..., min_length=1, max_length=20)
    description: str = Field(..., min_length=1)
    quantity: int = Field(..., gt=0, description="Must be positive")
    invoice_date: datetime
    unit_price: float = Field(..., gt=0, description="Must be positive")
    customer_id: Optional[str] = "GUEST"
    country: str = Field(..., min_length=1)

    @field_validator("invoice_no")
    @classmethod
    def invoice_no_not_cancelled(cls, v):
        if v.startswith("C"):
            raise ValueError("Cancelled invoices (starting with C) cannot be ingested")
        return v.upper()

class IngestSaleResponse(BaseModel):
    message: str
    invoice_no: str
    revenue: float