# Data Quality Report

Dataset status: Synthetic portfolio demo data generated with seed `20260611`.

Date range: `2025-01-01` to `2026-05-31`.

## Source Inventory

| Table | Rows | Purpose |
|---|---:|---|
| ecommerce_orders_raw | 128,271 | Order line grain, one product per order row |
| ecommerce_sessions_raw | 65,016 | Daily traffic by channel, device, and region |
| ecommerce_products_raw | 256 | Product catalog attributes |
| ecommerce_customers_raw | 18,000 | Customer profile and home region |
| ecommerce_returns_raw | 5,614 | Refund transactions tied to orders |
| ecommerce_campaigns_raw | 119 | Monthly marketing spend and traffic inputs |

## Validation Summary

- Order IDs are unique.
- GMV, revenue, refund amount, and sessions are non-negative.
- Prepared date dimension has a continuous daily range.
- Raw data is preserved in `data/raw/`; transforms are written to `data/prepared/`.
- PBIX file QA remains blocked until a real Power BI Desktop build is created and opened/saved/refreshed.
