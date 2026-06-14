# Desktop UI Runbook

Build target: `output/dashboard_final.pbix`.

Import order:

1. `dim_date.csv`
2. `dim_product.csv`
3. `dim_customer.csv`
4. `dim_region.csv`
5. `dim_channel.csv`
6. `dim_device.csv`
7. `fact_orders.csv`
8. `fact_sessions.csv`
9. `fact_marketing_spend.csv`

Page 1: Executive Overview

- Top KPI strip: GMV, Net Revenue, Orders, AOV, Conversion Rate, Refund/Cancel Rate.
- Trend: GMV and Net Revenue by Month, Orders as secondary axis.
- Category ranking: GMV by Category.
- Traffic channel mix: GMV by Channel.
- Risk callout: Refund/Cancel Rate and status distribution.

Page 2: Revenue & Category

- Matrix by Category and Subcategory.
- Region GMV view.
- Customer Segment GMV and AOV.

Page 3: Traffic & Conversion

- Funnel: Sessions, Add to Cart, Checkout Starts, Orders.
- Channel table: Sessions, Orders, Conversion Rate, AOV, Spend, ROAS.
- Device conversion comparison.

Page 4: Refunds & Operations

- Refund/Cancel Rate trend.
- Refund reasons.
- Category risk matrix.

QA after save:

- Reopen `dashboard_final.pbix`.
- Refresh all.
- Confirm no relationship ambiguity warnings.
- Export screenshots to `output/screenshots/`.
- Update `qa/pbix_validation.json`.
