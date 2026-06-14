# Relationship Map

Recommended Power BI model: star schema with single-direction filters from dimensions to facts.

| From Table | From Column | To Table | To Column | Cardinality | Direction |
|---|---|---|---|---|---|
| dim_date | date | fact_orders | order_date | 1:* | Single |
| dim_date | date | fact_sessions | session_date | 1:* | Single |
| dim_date | year_month | fact_marketing_spend | month | 1:* | Single |
| dim_product | product_id | fact_orders | product_id | 1:* | Single |
| dim_customer | customer_id | fact_orders | customer_id | 1:* | Single |
| dim_region | region | fact_orders | region | 1:* | Single |
| dim_region | region | fact_sessions | region | 1:* | Single |
| dim_channel | channel | fact_orders | channel | 1:* | Single |
| dim_channel | channel | fact_sessions | channel | 1:* | Single |
| dim_channel | channel | fact_marketing_spend | channel | 1:* | Single |
| dim_device | device | fact_orders | device | 1:* | Single |
| dim_device | device | fact_sessions | device | 1:* | Single |
