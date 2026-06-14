# Data Quality Report

## Source Inventory

| Sheet | Rows | Columns | Grain | Date Range | Duplicate Key Count |
|---|---:|---:|---|---|---:|
| RevenueDrivers_Raw | 10,320 | 16 | one row per month, scenario, region, service line, customer segment | 2024-01-01 to 2027-12-01 | 0 |
| CostDrivers_Raw | 10,320 | 15 | one row per revenue driver row with direct cost components | 2024-01-01 to 2027-12-01 | 0 |
| HeadcountPlan_Raw | 2,580 | 12 | one row per month, scenario, region, department | 2024-01-01 to 2027-12-01 | 0 |
| OpexDrivers_Raw | 2,580 | 12 | one row per month, scenario, region, department | 2024-01-01 to 2027-12-01 | 0 |
| CashImpact_Raw | 86 | 17 | one row per month and scenario | 2024-01-01 to 2027-12-01 | 0 |
| ForecastAccuracy_Raw | 1,530 | 12 | one row per month, horizon, region, service line | 2025-01-01 to 2026-05-01 | 0 |
| Scenario_Assumptions | 4 | 11 | one row per planning scenario | n/a | 0 |
| WhatIf_Parameters | 7 | 8 | one row per configurable planning lever | n/a | 0 |
| DimServices | 6 | 7 | one row per service line | n/a | 0 |
| DimRegions | 5 | 5 | one row per operating region | n/a | 0 |
| DimSegments | 4 | 5 | one row per customer segment | n/a | 0 |
| DimDepartments | 6 | 5 | one row per department | n/a | 0 |

## KPI Totals

- actual_revenue_usd: 314,587,311.83
- actual_direct_cost_usd: 246,486,412.02
- forecast_base_revenue_usd: 273,305,308.79
- forecast_base_direct_cost_usd: 219,573,328.21
- forecast_base_payroll_usd: 17,095,127.29
- forecast_base_non_payroll_opex_usd: 5,263,452.54
- latest_base_ending_cash_usd: 21,888,341.67
- actual_jobs: 438,269
- forecast_base_jobs: 340,357

## Data Quality Flags

- ForecastAccuracy_Raw: 25 rows have absolute pct error above 20%; kept for accuracy monitoring

## QA Decision

Synthetic source is accepted for portfolio build. High forecast-error rows are intentionally retained so the Forecast Accuracy page can show real monitoring behavior.