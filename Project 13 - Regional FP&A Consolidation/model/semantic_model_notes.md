# Semantic Model Notes

This portfolio model uses a star schema around monthly FP&A summary and detailed account facts.

- Grain: month x entity x business unit x scenario for `FactFinancialSummary`; month x entity x business unit x scenario x account for `FactFinancials`.
- Reporting currency: USD.
- Local currency: retained on account facts using generated FX rates.
- Scenario logic: Actual, Budget, Forecast, and Prior Year are modeled as scenario rows, not separate columns.
- Bridge logic: `FactVarianceDriverBridge` sums exactly to Actual EBITDA minus Budget EBITDA at month/entity/BU grain.
- Close-risk logic: `FactCloseExceptions` carries `business_unit_id` so the BU slicer can filter close-risk KPIs, action lists, and funnel views.
- KPI safety: margin and variance rates use `DIVIDE` in DAX definitions; rates are not additive.
- Currency format safety: currency measure format strings intentionally avoid literal million suffixes; visuals can set display units without producing `MM` labels.
- Data status: synthetic portfolio/demo data with fixed seed `13042`.
