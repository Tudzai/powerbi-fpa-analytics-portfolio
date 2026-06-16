# Relationship Map

| From table | From column | To table | To column | Cardinality | Filter |
|---|---|---|---|---|---|
| fact_manufacturing_month | year_month | dim_date | year_month | many-to-one | single |
| fact_manufacturing_month | plant_id | dim_plant | plant_id | many-to-one | single |
| fact_manufacturing_month | line_id | dim_line | line_id | many-to-one | single |
| fact_manufacturing_month | product_id | dim_product | product_id | many-to-one | single |
| fact_cost_variance_bridge | year_month | dim_date | year_month | many-to-one | single |

`dim_scenario` is intentionally disconnected and used by scenario measures via `SELECTEDVALUE`.
