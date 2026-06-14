# Data Dictionary

Synthetic data generated for Project 04 - Customer Funnel Conversion. All prepared tables are sourced from `data/prepared/`.

## dim_date

| Column | Type | Nulls | Sample |
|---|---|---:|---|
| date_key | int64 | 0 | 20250101 |
| date | str | 0 | 2025-01-01 |
| year | int64 | 0 | 2025 |
| quarter | str | 0 | Q1 |
| month_number | int64 | 0 | 1 |
| month_name | str | 0 | Jan |
| year_month | str | 0 | 2025-01 |
| month_start | str | 0 | 2025-01-01 |
| week_start | str | 0 | 2024-12-30 |
| day_of_week | str | 0 | Wed |
| is_weekend | int64 | 0 | 0 |

## dim_device

| Column | Type | Nulls | Sample |
|---|---|---:|---|
| device_key | str | 0 | DEV_DESKTOP |
| device | str | 0 | Desktop |
| device_group | str | 0 | Large screen |
| sort_order | int64 | 0 | 1 |

## dim_channel

| Column | Type | Nulls | Sample |
|---|---|---:|---|
| channel_key | str | 0 | CH_DIRECT |
| channel | str | 0 | Direct |
| channel_group | str | 0 | Owned / Direct |
| paid_flag | int64 | 0 | 0 |
| sort_order | int64 | 0 | 1 |

## dim_campaign

| Column | Type | Nulls | Sample |
|---|---|---:|---|
| campaign_key | str | 0 | CMP_DIRECT_NONE |
| campaign | str | 0 | Direct / None |
| channel_key | str | 0 | CH_DIRECT |
| campaign_type | str | 0 | Always-on |
| objective | str | 0 | Navigation |
| start_date | str | 0 | 2025-01-01 |
| end_date | str | 0 | 2026-05-31 |
| daily_budget | int64 | 0 | 0 |

## dim_category

| Column | Type | Nulls | Sample |
|---|---|---:|---|
| category_key | str | 0 | CAT_APPAREL |
| category | str | 0 | Apparel |
| merchandising_owner | str | 0 | Softlines |
| base_price | int64 | 0 | 58 |
| sort_order | int64 | 0 | 1 |

## dim_product

| Column | Type | Nulls | Sample |
|---|---|---:|---|
| product_key | str | 0 | SKU_1001 |
| product | str | 0 | Apparel Outerwear 1 |
| category_key | str | 0 | CAT_APPAREL |
| category | str | 0 | Apparel |
| subcategory | str | 0 | Outerwear |
| brand | str | 0 | Mova |
| unit_price | float64 | 0 | 55.32 |
| gross_margin_rate | float64 | 0 | 0.347745 |
| launch_date | str | 0 | 2024-01-01 |

## dim_funnel_stage

| Column | Type | Nulls | Sample |
|---|---|---:|---|
| stage_key | int64 | 0 | 1 |
| stage | str | 0 | Visit |
| stage_short | str | 0 | Visit |
| stage_order | int64 | 0 | 1 |
| previous_stage_key | object | 0 |  |

## fact_sessions

| Column | Type | Nulls | Sample |
|---|---|---:|---|
| session_id | str | 0 | S00000001 |
| user_id | str | 0 | U70934 |
| session_date | str | 0 | 2025-01-01 |
| date_key | int64 | 0 | 20250101 |
| session_start_ts | str | 0 | 2025-01-01 11:03:33 |
| device_key | str | 0 | DEV_DESKTOP |
| channel_key | str | 0 | CH_PAID_SEARCH |
| campaign_key | str | 0 | CMP_GENERIC_SEARCH |
| category_key | str | 0 | CAT_ELECTRONICS |
| product_key | str | 0 | SKU_1020 |
| region | str | 0 | Northeast |
| new_returning | str | 0 | Returning |
| landing_page | str | 0 | Category |
| is_bot_traffic | int64 | 0 | 0 |
| visit_flag | int64 | 0 | 1 |
| product_view_flag | int64 | 0 | 1 |
| add_to_cart_flag | int64 | 0 | 0 |
| checkout_flag | int64 | 0 | 0 |
| purchase_flag | int64 | 0 | 0 |
| reached_stage_key | int64 | 0 | 2 |
| qualified_session_flag | int64 | 0 | 1 |
| session_month | str | 0 | 2025-01 |

## fact_orders

| Column | Type | Nulls | Sample |
|---|---|---:|---|
| order_id | str | 0 | O00000001 |
| session_id | str | 0 | S00000010 |
| user_id | str | 0 | U63985 |
| order_date | str | 0 | 2025-01-01 |
| date_key | int64 | 0 | 20250101 |
| device_key | str | 0 | DEV_DESKTOP |
| channel_key | str | 0 | CH_ORGANIC |
| campaign_key | str | 0 | CMP_ORG_EVERGREEN |
| category_key | str | 0 | CAT_APPAREL |
| product_key | str | 0 | SKU_1002 |
| region | str | 0 | Midwest |
| quantity | int64 | 0 | 1 |
| unit_price | float64 | 0 | 68.86 |
| gross_revenue | float64 | 0 | 68.86 |
| discount_amount | float64 | 0 | 7.59 |
| refund_flag | int64 | 0 | 0 |
| refund_amount | float64 | 0 | 0.0 |
| net_revenue | float64 | 0 | 61.27 |
| order_status | str | 0 | Completed |
| currency | str | 0 | USD |

## fact_stage_sessions

| Column | Type | Nulls | Sample |
|---|---|---:|---|
| date_key | int64 | 0 | 20250101 |
| device_key | str | 0 | DEV_DESKTOP |
| channel_key | str | 0 | CH_AFFILIATE |
| campaign_key | str | 0 | CMP_AFF_MARKETPLACE |
| category_key | str | 0 | CAT_APPAREL |
| stage_key | int64 | 0 | 1 |
| sessions | int64 | 0 | 1 |

## fact_stage_transition

| Column | Type | Nulls | Sample |
|---|---|---:|---|
| date_key | int64 | 0 | 20250101 |
| device_key | str | 0 | DEV_DESKTOP |
| channel_key | str | 0 | CH_AFFILIATE |
| campaign_key | str | 0 | CMP_AFF_MARKETPLACE |
| category_key | str | 0 | CAT_APPAREL |
| stage_key | int64 | 0 | 2 |
| transition | str | 0 | Visit to Product View |
| previous_stage_sessions | int64 | 0 | 1 |
| current_stage_sessions | int64 | 0 | 1 |
| dropoff_sessions | int64 | 0 | 0 |
| step_conversion_rate | float64 | 0 | 1.0 |
| dropoff_rate | float64 | 0 | 0.0 |

## fact_monthly_funnel

| Column | Type | Nulls | Sample |
|---|---|---:|---|
| month_start | str | 0 | 2025-01-01 |
| device_key | str | 0 | DEV_DESKTOP |
| channel_key | str | 0 | CH_AFFILIATE |
| campaign_key | str | 0 | CMP_AFF_MARKETPLACE |
| category_key | str | 0 | CAT_APPAREL |
| visits | int64 | 0 | 32 |
| product_views | int64 | 0 | 27 |
| add_to_carts | int64 | 0 | 11 |
| checkouts | int64 | 0 | 9 |
| purchases | int64 | 0 | 9 |
| orders | float64 | 0 | 9.0 |
| revenue | float64 | 0 | 559.59 |
| gross_revenue | float64 | 0 | 602.45 |
| refund_amount | float64 | 0 | 0.0 |
| overall_conversion_rate | float64 | 0 | 0.28125 |
| cart_to_purchase_rate | float64 | 0 | 0.818182 |

## fact_marketing_spend

| Column | Type | Nulls | Sample |
|---|---|---:|---|
| date | str | 0 | 2025-01-01 |
| date_key | int64 | 0 | 20250101 |
| campaign_key | str | 0 | CMP_DIRECT_NONE |
| channel_key | str | 0 | CH_DIRECT |
| spend | float64 | 0 | 0.0 |
| impressions | int64 | 0 | 0 |
| clicks | int64 | 0 | 0 |
