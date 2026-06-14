# Semantic Model Notes

Fact tables:

- `fact_orders`: one row per order line. Measures for GMV, net revenue, orders, AOV, refunds, cancellations, and contribution margin.
- `fact_sessions`: one row per date, channel, device, and region. Measures for sessions, visitors, add to cart, checkout starts, and conversion.
- `fact_marketing_spend`: one row per month and channel. Measures for spend, clicks, impressions, CPC, CPM, and ROAS.

Dimension tables:

- `dim_date`, `dim_product`, `dim_customer`, `dim_region`, `dim_channel`, `dim_device`.

Modeling choices:

- Use single-direction relationships from dimensions into facts.
- Hide technical keys and raw flag columns from report view.
- Keep percentage measures formatted as percentages and never sum them.
- Use `dim_date[date]` as the primary date table and mark it as Date table in Power BI.
