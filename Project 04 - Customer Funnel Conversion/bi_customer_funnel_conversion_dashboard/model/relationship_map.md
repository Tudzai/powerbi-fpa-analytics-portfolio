# Relationship Map

| From table | From column | To table | To column | Cardinality | Filter |
|---|---|---|---|---|---|
| fact_sessions | date_key | dim_date | date_key | many-to-one | Single |
| fact_sessions | device_key | dim_device | device_key | many-to-one | Single |
| fact_sessions | channel_key | dim_channel | channel_key | many-to-one | Single |
| fact_sessions | campaign_key | dim_campaign | campaign_key | many-to-one | Single |
| fact_sessions | category_key | dim_category | category_key | many-to-one | Single |
| fact_sessions | product_key | dim_product | product_key | many-to-one | Single |
| fact_orders | date_key | dim_date | date_key | many-to-one | Single |
| fact_orders | device_key | dim_device | device_key | many-to-one | Single |
| fact_orders | channel_key | dim_channel | channel_key | many-to-one | Single |
| fact_orders | campaign_key | dim_campaign | campaign_key | many-to-one | Single |
| fact_orders | category_key | dim_category | category_key | many-to-one | Single |
| fact_orders | product_key | dim_product | product_key | many-to-one | Single |
| fact_stage_sessions | date_key | dim_date | date_key | many-to-one | Single |
| fact_stage_sessions | stage_key | dim_funnel_stage | stage_key | many-to-one | Single |
| fact_stage_sessions | device_key | dim_device | device_key | many-to-one | Single |
| fact_stage_sessions | channel_key | dim_channel | channel_key | many-to-one | Single |
| fact_stage_sessions | campaign_key | dim_campaign | campaign_key | many-to-one | Single |
| fact_stage_sessions | category_key | dim_category | category_key | many-to-one | Single |
| fact_stage_transition | date_key | dim_date | date_key | many-to-one | Single |
| fact_stage_transition | stage_key | dim_funnel_stage | stage_key | many-to-one | Single |
| fact_stage_transition | device_key | dim_device | device_key | many-to-one | Single |
| fact_stage_transition | channel_key | dim_channel | channel_key | many-to-one | Single |
| fact_stage_transition | campaign_key | dim_campaign | campaign_key | many-to-one | Single |
| fact_stage_transition | category_key | dim_category | category_key | many-to-one | Single |
| fact_marketing_spend | date_key | dim_date | date_key | many-to-one | Single |
| fact_marketing_spend | channel_key | dim_channel | channel_key | many-to-one | Single |
| fact_marketing_spend | campaign_key | dim_campaign | campaign_key | many-to-one | Single |
