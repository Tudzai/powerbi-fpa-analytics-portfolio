# Relationship Map

| From table | From column | To table | To column | Cardinality | Filter |
|---|---|---|---|---|---|
| fact_payment_month | year_month | dim_date | year_month | many-to-one | single |
| fact_payment_month | merchant_id | dim_merchant | merchant_id | many-to-one | single |
| fact_payment_month | payment_method_id | dim_payment_method | payment_method_id | many-to-one | single |
| fact_payment_month | channel_id | dim_channel | channel_id | many-to-one | single |
| fact_fee_bridge | year_month | dim_date | year_month | many-to-one | single |

`dim_scenario` is intentionally disconnected and used by DAX scenario measures through `SELECTEDVALUE`.
