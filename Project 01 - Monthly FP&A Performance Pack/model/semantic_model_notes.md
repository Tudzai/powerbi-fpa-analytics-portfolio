# Semantic Model Notes

## Purpose

This model supports a Monthly FP&A Performance Pack for management reporting:

- Actual vs Budget vs Forecast.
- Revenue, Gross Margin, EBITDA, Opex, Cash.
- Variance analysis by business unit, product, region, customer, and department.
- Budget-to-Actual bridge.
- 12-month trend and latest-month commentary.

## Tables

### Dimensions

- DimDate: month-level date dimension.
- DimScenario: Actual, Budget, Forecast.
- DimBusinessUnit: reporting business unit.
- DimProduct: product/service line.
- DimRegion: reporting geography.
- DimCustomer: customer, segment, industry.
- DimDepartment: department for Opex analysis.

### Facts

- FactFinancials: P&L by month/scenario/BU/product/region/customer.
- FactOpexDepartment: Opex by month/scenario/BU/region/department.
- FactCash: cash, AR, DSO, capex by month/scenario/BU/region.
- FactBridge: Budget to Actual EBITDA bridge for May 2026.
- FactCommentary: monthly narrative blocks.

## Power BI Build Status

Status: pending Desktop build and QA.

Reason: Power BI Desktop Store app is detected, but the PBIX has not yet been authored and visually QA-tested. The package includes source data, prepared data, Power Query, DAX, theme, page map, visual map, QA, and handoff notes so the PBIX can be built and validated in Power BI Desktop.

Expected final file after desktop build:

`output/dashboard_final.pbix`
