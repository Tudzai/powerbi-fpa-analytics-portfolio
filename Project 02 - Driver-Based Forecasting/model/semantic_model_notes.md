# Semantic Model Notes

## Model Intent

This model supports monthly business planning and scenario decisions, not only historical reporting. Actuals run through May 2026; forecast scenarios run from June 2026 through December 2027.

## Fact Tables

- `FactRevenueDriver`: volume, rate, surcharge, discount, and revenue by month/scenario/region/service/segment.
- `FactCostDriver`: direct cost components tied to the same revenue-driver grain.
- `FactHeadcountPlan`: FTE, hiring, attrition, salary and payroll by month/scenario/region/department.
- `FactOpexDriver`: non-payroll OPEX by month/scenario/region/department.
- `FactCashImpact`: monthly P&L-to-cash bridge by scenario.
- `FactForecastAccuracy`: actual versus forecast revenue by month/horizon/region/service.

## Dimensional Rules

- `DimScenario` should be sorted by `SortOrder`: Actual, Base, Upside, Downside.
- `DimDate[MonthName]` should be sorted by `DimDate[MonthNumber]`; `DimDate[YearMonth]` by `DimDate[MonthSort]`.
- Hide technical keys after relationships are created.

## What-if Guidance

The `what_if_parameters` table documents the planning levers. In Power BI Desktop, create numeric What-if parameters for high-value levers such as Volume Growth %, Rate Change %, Direct Cost Inflation %, and DSO Days. Use these parameter values to create adjusted revenue, cost, and cash measures without overwriting the official Base/Upside/Downside scenarios.