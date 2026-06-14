# Metric Definitions

Project: Monthly FP&A Performance Pack

Latest complete actual month: May 2026

## Core KPI

### Revenue

- Business definition: Net revenue by month and reporting scenario.
- Formula: `SUM(FactFinancials[Revenue])`
- Grain: month, scenario, business unit, product, region, customer.
- Unit: VND.
- Format: `#,0,,.0M`
- Source: `data/prepared/fact_financials.csv`
- Caveat: Synthetic portfolio sample, not company actuals.

### COGS

- Business definition: Direct cost attached to the revenue line.
- Formula: `SUM(FactFinancials[COGS])`
- Grain: same as Revenue.
- Unit: VND.
- Format: `#,0,,.0M`

### Gross Margin

- Business definition: Revenue less COGS.
- Formula: `[Revenue] - [COGS]`
- Unit: VND.
- Format: `#,0,,.0M`

### Gross Margin %

- Business definition: Gross Margin divided by Revenue.
- Formula: `DIVIDE([Gross Margin], [Revenue])`
- Unit: percent.
- Format: `0.0%`
- Caveat: Blank when Revenue is zero.

### Opex

- Business definition: Operating expense used for management reporting.
- Formula for product/customer drill-down: `SUM(FactFinancials[AllocatedOpex])`
- Formula for department analysis: `SUM(FactOpexDepartment[Opex])`
- Unit: VND.
- Format: `#,0,,.0M`
- Caveat: Department Opex lives in a separate fact table to keep department grain clean.

### EBITDA

- Business definition: Gross Margin less allocated Opex.
- Formula: `[Gross Margin] - [Allocated Opex]`
- Unit: VND.
- Format: `#,0,,.0M`

### EBITDA %

- Business definition: EBITDA divided by Revenue.
- Formula: `DIVIDE([EBITDA], [Revenue])`
- Unit: percent.
- Format: `0.0%`

### Cash Balance

- Business definition: Month-end cash balance at the latest visible month.
- Formula: sum FactCash CashBalance for the latest visible month only.
- Unit: VND.
- Format: `#,0,,.0M`
- Caveat: Do not sum CashBalance across months.

### Revenue Variance vs Budget

- Business definition: Actual Revenue less Budget Revenue at the selected filter context.
- Formula: `[Actual Revenue] - [Budget Revenue]`
- Unit: VND.
- Format: `#,0,,.0M`

### EBITDA Variance vs Budget

- Business definition: Actual EBITDA less Budget EBITDA at the selected filter context.
- Formula: `[Actual EBITDA] - [Budget EBITDA]`
- Unit: VND.
- Format: `#,0,,.0M`

### Forecast Gap

- Business definition: Forecast less Budget for the selected metric.
- Formula: `[Forecast Metric] - [Budget Metric]`
- Unit: VND.
- Format: `#,0,,.0M`

## Commentary

### What Happened

- Business definition: short monthly narrative of performance movement.
- Source: `data/prepared/fact_commentary.csv`

### Why

- Business definition: management explanation of drivers.
- Source: `data/prepared/fact_commentary.csv`

### What Next

- Business definition: next management action.
- Source: `data/prepared/fact_commentary.csv`
