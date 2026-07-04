# RetailPulse Star Schema

## Fact Table

### fact_sales

- invoice_no
- stock_code (FK)
- customer_id (FK)
- date_key (FK)
- quantity
- unit_price
- revenue
- is_cancelled
- is_return

**Grain**

One row represents one invoice line item.

---

## Dimension Tables

### dim_product

- stock_code (PK)
- description

### dim_customer

- customer_id (PK)
- country
- is_guest

### dim_date

- date_key (PK)
- full_date
- year
- month
- day
- quarter