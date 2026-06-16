# Metric Definitions

Core KPIs are DAX measures, not raw numeric fields.

- Revenue, EBITDA, and plan variance default to the Base scenario when no scenario is selected.
- Rates and margins use `DIVIDE`.
- Cash, runway, covenant, and valuation cards use latest complete month logic where applicable.
- KPI footer labels, status colors, and SVG sparklines are DAX decoration measures so micro-details can respond to slicers.
- Board KPI scorecard values are denormalized display strings to preserve mixed units in the status table.
- Scenario analytics use `DimScenario` so Base/Upside/Downside comparisons stay consistent across pages.
