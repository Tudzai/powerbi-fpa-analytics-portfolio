# Data Quality Report

## Scope

Project 04 - Customer Funnel Conversion uses deterministic synthetic ecommerce funnel data generated with seed `4042026`. Raw files keep realistic noise such as duplicate product-view events and bot traffic. Prepared files apply the dashboard business grain: one qualified session per row for funnel KPIs.

## Table Profile

| Table | Rows | Columns | Duplicate rows | Null cells |
|---|---:|---:|---:|---:|
| raw_sessions | 163,026 | 20 | 0 | 0 |
| raw_events | 428,943 | 15 | 0 | 0 |
| raw_orders | 18,567 | 20 | 0 | 0 |
| raw_spend | 5,160 | 7 | 0 | 0 |
| dim_date | 516 | 11 | 0 | 0 |
| dim_device | 3 | 4 | 0 | 0 |
| dim_channel | 7 | 5 | 0 | 0 |
| dim_campaign | 10 | 8 | 0 | 0 |
| dim_category | 6 | 5 | 0 | 0 |
| dim_product | 48 | 9 | 0 | 0 |
| dim_funnel_stage | 5 | 5 | 0 | 0 |
| fact_sessions | 161,097 | 22 | 0 | 0 |
| fact_orders | 18,567 | 20 | 0 | 0 |
| fact_stage_sessions | 187,175 | 7 | 0 | 0 |
| fact_stage_transition | 240,128 | 12 | 0 | 0 |
| fact_monthly_funnel | 2,970 | 16 | 0 | 0 |
| fact_marketing_spend | 5,160 | 7 | 0 | 0 |

## Critical Checks

| Check | Result |
|---|---|
| Funnel stage counts are monotonic | PASS |
| Orders reconcile to purchase sessions | PASS |
| Raw duplicate product views are not used as session-stage counts | PASS |
| Bot/test traffic excluded from prepared `fact_sessions` | PASS |
| Campaign/channel/device/category keys exist for every prepared session | PASS |

## Stage Totals

| Stage | Sessions |
|---|---:|
| Visit | 161,097 |
| Product View | 137,530 |
| Add to Cart | 51,170 |
| Checkout | 31,518 |
| Purchase | 18,567 |

## Known Data Design Notes

- Raw `funnel_events_raw.csv` can contain multiple product-view events for the same session.
- Funnel KPIs are session-based; the dashboard counts whether a session reached a stage, not how many event rows occurred.
- `Direct / None`, `SEO Evergreen`, and `Review Partners` intentionally carry zero paid media spend.
- Refunds are post-purchase adjustments; purchase sessions still count as purchases, while net revenue deducts refunds.
