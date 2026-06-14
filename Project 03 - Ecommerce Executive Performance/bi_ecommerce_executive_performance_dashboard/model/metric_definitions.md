# Metric Definitions

Audience: CEO, ecommerce general manager, commercial leadership, marketing leadership.

Grain rule: core KPI measures aggregate from prepared fact tables and should not use raw numeric fields directly inside visuals.

| KPI | Definition | Business Use |
|---|---|---|
| GMV | Sum of `fact_orders[gmv]` before refunds and cancellations | Demand and marketplace scale |
| Net Revenue | Sum of `fact_orders[net_revenue]` for completed orders after discounts and shipping | Monetized sales performance |
| Orders | Count of distinct `fact_orders[order_id]` | Demand volume |
| AOV | GMV divided by Orders | Basket quality and pricing leverage |
| Conversion Rate | Orders divided by Sessions | Traffic monetization effectiveness |
| Refund/Cancel Rate | Refunded plus cancelled orders divided by Orders | Fulfillment and customer experience risk |
| Top Category | Category with highest GMV in current filter context | Category leadership focus |
| Top Traffic Channel | Channel with highest GMV in current filter context | Acquisition channel priority |
| Marketing Spend | Sum of `fact_marketing_spend[spend]` | Acquisition investment |
| ROAS | Net Revenue divided by Marketing Spend | Marketing efficiency |
