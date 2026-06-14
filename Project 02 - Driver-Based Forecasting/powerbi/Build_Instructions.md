# Power BI Build Instructions

## 1. Import Data

Use `powerbi/PowerQuery_M.txt` as the query source pattern. Import every CSV from `data/prepared/` in Import mode.

## 2. Rename Tables

- `fact_revenue_driver` -> `FactRevenueDriver`
- `fact_cost_driver` -> `FactCostDriver`
- `fact_headcount_plan` -> `FactHeadcountPlan`
- `fact_opex_driver` -> `FactOpexDriver`
- `fact_cash_impact` -> `FactCashImpact`
- `fact_forecast_accuracy` -> `FactForecastAccuracy`
- `dim_date` -> `DimDate`
- `dim_scenario` -> `DimScenario`
- `dim_service` -> `DimService`
- `dim_region` -> `DimRegion`
- `dim_customer_segment` -> `DimCustomerSegment`
- `dim_department` -> `DimDepartment`
- `what_if_parameters` -> `WhatIfParameters`

## 3. Relationships

Build relationships exactly as listed in `model/relationship_map.md`. Use single-direction filtering from dimensions to facts.

## 4. Measures

Create a blank measure table named `KPI_Measures`, then paste measures from `powerbi/Project2_Measures.dax`.

## 5. Theme and Pages

Import `build/config/theme.json`. Build pages using `build/config/page_map.json` and `build/config/visual_map.json`.

## 6. Save and QA

Automated source build is available through `build/scripts/07_build_powerbi_pbixproj.py`. The reviewed final file is `output/dashboard_final.pbix`; refresh and rerun `qa/qa_checklist.md` before promoting any future revision.
