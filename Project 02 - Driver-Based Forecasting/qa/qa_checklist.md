# QA Checklist

## Data QA

- [x] Revenue rows have positive revenue
- [x] Revenue driver keys are unique
- [x] Cost driver keys are unique
- [x] Headcount plan keys are unique
- [x] No null scenario keys in facts
- [x] Forecast accuracy MAPE is computable
- [x] Cash table reconciles to P&L aggregate

## Metric QA

- [x] Revenue, direct cost, payroll, OPEX and EBITDA reconcile from fact tables to cash impact table.
- [x] Margin metrics are calculated as ratios, not summed percentages.
- [x] Forecast accuracy keeps high-error rows to support monitoring and variance diagnosis.

## Visual QA

- [x] Page map keeps each page to a small set of decision-oriented visuals.
- [x] KPI cards use measures only; raw numeric fields are not used as final KPI logic.
- [x] Theme uses neutral background with distinct scenario colors.

## Interaction QA

- [x] Planned slicers: Scenario, Year, Month, Region, Service Line, Customer Segment.
- [x] Scenario slicer is expected to sync across all planning pages.
- [x] Reset bookmark is specified in visual map; requires Power BI Desktop implementation.

## File / Performance QA

- [x] Prepared extracts are compact enough for Import mode.
- [x] Rebuild scripts are available in `build/scripts/`.
- [ ] PBIX open/save/refresh QA is pending until the report is built in Power BI Desktop.