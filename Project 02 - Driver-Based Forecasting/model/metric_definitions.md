# Metric Definitions

Currency: USD. Forecast horizon: June 2026 to December 2027. Historical actuals: January 2024 to May 2026.

## Revenue

- Business definition: Net revenue after surcharge and discount at current filter context.
- DAX: `Revenue = SUM(FactRevenueDriver[RevenueUSD])`
- Unit: USD
- Format: `$#,0;($#,0);$0`
- Filter context: Current report/page/visual filters.

## Direct Cost

- Business definition: Carrier, handling, fuel and customs direct costs.
- DAX: `Direct Cost = SUM(FactCostDriver[DirectCostUSD])`
- Unit: USD
- Format: `$#,0;($#,0);$0`
- Filter context: Current report/page/visual filters.

## Gross Profit

- Business definition: Revenue less direct cost.
- DAX: `Gross Profit = [Revenue] - [Direct Cost]`
- Unit: USD
- Format: `$#,0;($#,0);$0`
- Filter context: Current report/page/visual filters.

## Gross Margin %

- Business definition: Gross profit divided by revenue.
- DAX: `Gross Margin % = DIVIDE([Gross Profit], [Revenue])`
- Unit: %
- Format: `0.0%`
- Filter context: Current report/page/visual filters.

## Payroll Cost

- Business definition: Salary cost from the headcount plan.
- DAX: `Payroll Cost = SUM(FactHeadcountPlan[PayrollCostUSD])`
- Unit: USD
- Format: `$#,0;($#,0);$0`
- Filter context: Current report/page/visual filters.

## Non Payroll OPEX

- Business definition: Rent, software, marketing, travel and G&A cost excluding payroll.
- DAX: `Non Payroll OPEX = SUM(FactOpexDriver[NonPayrollOpexUSD])`
- Unit: USD
- Format: `$#,0;($#,0);$0`
- Filter context: Current report/page/visual filters.

## EBITDA

- Business definition: Forecast P&L operating profit proxy before tax and capex.
- DAX: `EBITDA = [Gross Profit] - [Payroll Cost] - [Non Payroll OPEX]`
- Unit: USD
- Format: `$#,0;($#,0);$0`
- Filter context: Current report/page/visual filters.

## EBITDA Margin %

- Business definition: EBITDA divided by revenue.
- DAX: `EBITDA Margin % = DIVIDE([EBITDA], [Revenue])`
- Unit: %
- Format: `0.0%`
- Filter context: Current report/page/visual filters.

## Jobs

- Business definition: Total shipment or service jobs.
- DAX: `Jobs = SUM(FactRevenueDriver[VolumeJobs])`
- Unit: jobs
- Format: `#,0`
- Filter context: Current report/page/visual filters.

## Revenue / Job

- Business definition: Revenue productivity per job.
- DAX: `Revenue per Job = DIVIDE([Revenue], [Jobs])`
- Unit: USD/job
- Format: `$#,0.0`
- Filter context: Current report/page/visual filters.

## Variable Cost / Job

- Business definition: Direct cost productivity per job.
- DAX: `Variable Cost per Job = DIVIDE([Direct Cost], [Jobs])`
- Unit: USD/job
- Format: `$#,0.0`
- Filter context: Current report/page/visual filters.

## Average FTE

- Business definition: Average monthly FTE in the selected period.
- DAX: `Average FTE = AVERAGEX(VALUES(DimDate[YearMonth]), SUM(FactHeadcountPlan[FTE]))`
- Unit: FTE
- Format: `#,0.0`
- Filter context: Current report/page/visual filters.

## Jobs / FTE

- Business definition: Capacity productivity based on average monthly FTE.
- DAX: `Jobs per FTE = DIVIDE([Jobs], [Average FTE])`
- Unit: jobs/FTE
- Format: `#,0.0`
- Filter context: Current report/page/visual filters.

## Operating Cash Flow

- Business definition: EBITDA less tax and working-capital drag.
- DAX: `Operating Cash Flow = SUM(FactCashImpact[OperatingCashFlowUSD])`
- Unit: USD
- Format: `$#,0;($#,0);$0`
- Filter context: Current report/page/visual filters.

## Ending Cash

- Business definition: Ending cash balance at latest visible period.
- DAX: `Ending Cash Latest Month = CALCULATE(SUM(FactCashImpact[EndingCashUSD]), LASTNONBLANK(DimDate[Date], [Operating Cash Flow]))`
- Unit: USD
- Format: `$#,0;($#,0);$0`
- Filter context: Current report/page/visual filters.

## Working Capital

- Business definition: AR and AP timing impact based on DSO and DPO assumptions.
- DAX: `Working Capital = SUM(FactCashImpact[WorkingCapitalUSD])`
- Unit: USD
- Format: `$#,0;($#,0);$0`
- Filter context: Current report/page/visual filters.

## DSO

- Business definition: Average days sales outstanding in current scenario.
- DAX: `DSO Days = AVERAGE(FactCashImpact[DSODays])`
- Unit: days
- Format: `#,0`
- Filter context: Current report/page/visual filters.

## DPO

- Business definition: Average days payable outstanding in current scenario.
- DAX: `DPO Days = AVERAGE(FactCashImpact[DPODays])`
- Unit: days
- Format: `#,0`
- Filter context: Current report/page/visual filters.

## MAPE

- Business definition: Mean absolute percentage error for forecast accuracy tracking.
- DAX: `MAPE = AVERAGE(FactForecastAccuracy[AbsolutePctError])`
- Unit: %
- Format: `0.0%`
- Filter context: Current report/page/visual filters.

## Forecast Bias %

- Business definition: Average signed forecast bias.
- DAX: `Forecast Bias % = AVERAGE(FactForecastAccuracy[ForecastBiasPct])`
- Unit: %
- Format: `0.0%`
- Filter context: Current report/page/visual filters.

## Base Revenue

- Business definition: Base scenario revenue for variance comparisons.
- DAX: `Base Revenue = CALCULATE([Revenue], DimScenario[Scenario] = "Base")`
- Unit: USD
- Format: `$#,0;($#,0);$0`
- Filter context: Current report/page/visual filters.

## Revenue Var vs Base

- Business definition: Selected scenario revenue less base scenario revenue.
- DAX: `Scenario Revenue Variance vs Base = [Revenue] - [Base Revenue]`
- Unit: USD
- Format: `$#,0;($#,0);$0`
- Filter context: Current report/page/visual filters.

## Revenue Var % vs Base

- Business definition: Selected scenario revenue variance percentage versus base.
- DAX: `Scenario Revenue Variance % vs Base = DIVIDE([Scenario Revenue Variance vs Base], [Base Revenue])`
- Unit: %
- Format: `0.0%`
- Filter context: Current report/page/visual filters.
