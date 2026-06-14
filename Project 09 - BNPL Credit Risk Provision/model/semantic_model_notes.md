# Semantic Model Notes

- Star schema with application, funded loan, monthly portfolio, collections, vintage, roll-rate, and forecast facts.
- KPI measures live in `KPI Measures`; key rates use `DIVIDE`.
- Date analysis uses `DimMonth` for monthly risk reporting, with daily `DimDate` retained for source extensibility.
- Rates are not summed; visuals use DAX measures for approval, delinquency, NPL, expected loss, recovery, SLA, vintage, and roll-rate.
