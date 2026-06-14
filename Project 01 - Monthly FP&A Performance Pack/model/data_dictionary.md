# Data Dictionary

## Raw Tables

### raw_fpa_financials

Grain: one row per month, scenario, business unit, product, region, customer.

| Column | Meaning |
|---|---|
| RecordID | Stable source row id. |
| MonthStart | First day of the financial month. |
| Scenario | Actual, Budget, or Forecast. |
| BusinessUnit | FP&A reporting business unit. |
| Product | Service/product line within business unit. |
| Region | Reporting region. |
| Customer | Customer or grouped long-tail customer bucket. |
| CustomerSegment | Strategic, Enterprise, Growth, or SMB. |
| Industry | Customer industry. |
| Revenue | Net revenue for the row. |
| COGS | Cost of goods/services for the row. |
| GrossMargin | Revenue less COGS. |
| AllocatedOpex | Allocated operating expense for segment drill-down. |
| EBITDA | GrossMargin less AllocatedOpex. |
| Orders | Operational volume proxy. |
| CashImpact | Estimated cash contribution for the row. |

### raw_fpa_opex_department

Grain: one row per month, scenario, business unit, region, department.

### raw_fpa_cash

Grain: one row per month, scenario, business unit, region. CashBalance is a month-end balance.

### raw_fpa_budget_actual_bridge

Grain: one row per May 2026 bridge step, business unit, region.

### raw_monthly_commentary

Grain: one row per monthly FP&A narrative.
