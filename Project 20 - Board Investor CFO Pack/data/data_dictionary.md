# Data Dictionary

## DimDate

Grain: one row per month

Rows: 29

Columns:
- `MonthStart`: `str`
- `MonthLabel`: `str`
- `MonthIndex`: `int64`
- `Year`: `int64`
- `Quarter`: `str`
- `IsLatestCompleteMonth`: `int64`

## DimScenario

Grain: one row per scenario

Rows: 3

Columns:
- `ScenarioID`: `str`
- `ScenarioName`: `str`
- `RevenueIndex`: `float64`
- `MarginIndex`: `float64`
- `BurnIndex`: `float64`
- `ScenarioSort`: `int64`

## DimBusinessUnit

Grain: one row per business unit

Rows: 4

Columns:
- `BusinessUnitID`: `str`
- `BusinessUnit`: `str`
- `RevenueFamily`: `str`
- `MixWeight`: `float64`
- `TargetGrossMargin`: `float64`
- `GrowthIndex`: `float64`

## DimRegion

Grain: one row per region

Rows: 4

Columns:
- `RegionID`: `str`
- `Region`: `str`
- `RegionMaturity`: `str`
- `MixWeight`: `float64`
- `DemandIndex`: `float64`

## DimCostCategory

Grain: one row per cost category

Rows: 4

Columns:
- `CostCategoryID`: `str`
- `CostCategory`: `str`
- `RevenueLoad`: `float64`

## FactPnlMonthly

Grain: one row per month, scenario, business unit, and region

Rows: 1,392

Columns:
- `MonthStart`: `str`
- `ScenarioID`: `str`
- `BusinessUnitID`: `str`
- `RegionID`: `str`
- `Revenue`: `float64`
- `PlanRevenue`: `float64`
- `ForecastRevenue`: `float64`
- `COGS`: `float64`
- `GrossProfit`: `float64`
- `OperatingExpense`: `float64`
- `EBITDA`: `float64`
- `PlanEBITDA`: `float64`
- `ForecastEBITDA`: `float64`
- `NetIncome`: `float64`
- `IsSynthetic`: `str`

## FactOpexMonthly

Grain: one row per month, scenario, and cost category

Rows: 348

Columns:
- `MonthStart`: `str`
- `ScenarioID`: `str`
- `CostCategoryID`: `str`
- `OperatingExpense`: `float64`
- `PlanOperatingExpense`: `float64`
- `ForecastOperatingExpense`: `float64`

## FactCashMonthly

Grain: one row per month and scenario

Rows: 87

Columns:
- `MonthStart`: `str`
- `ScenarioID`: `str`
- `CashBalance`: `float64`
- `OperatingCashFlow`: `float64`
- `Capex`: `float64`
- `FreeCashFlow`: `float64`
- `NetBurn`: `float64`
- `RunwayMonths`: `float64`
- `FundingNeed`: `float64`
- `Debt`: `float64`
- `WorkingCapital`: `float64`
- `FinancingInflow`: `float64`

## FactStatementLines

Grain: one row per month, scenario, and financial statement line

Rows: 957

Columns:
- `MonthStart`: `str`
- `ScenarioID`: `str`
- `Statement`: `str`
- `LineItem`: `str`
- `LineSort`: `int64`
- `ValueActual`: `float64`
- `ValuePlan`: `float64`
- `ValueForecast`: `float64`

## FactCovenantMonthly

Grain: one row per month and scenario

Rows: 87

Columns:
- `MonthStart`: `str`
- `ScenarioID`: `str`
- `RevenueLTM`: `float64`
- `EBITDALTM`: `float64`
- `NetDebt`: `float64`
- `LeverageRatio`: `float64`
- `LeverageLimit`: `float64`
- `LeverageHeadroom`: `float64`
- `InterestCoverage`: `float64`
- `InterestCoverageLimit`: `float64`
- `Liquidity`: `float64`
- `LiquidityMinimum`: `int64`
- `LiquidityHeadroom`: `float64`
- `CovenantStatus`: `str`
- `RiskScore`: `float64`

## FactValuation

Grain: one row per scenario and valuation method

Rows: 15

Columns:
- `ScenarioID`: `str`
- `Method`: `str`
- `MethodSort`: `int64`
- `Multiple`: `float64`
- `EnterpriseValue`: `float64`
- `EquityValue`: `float64`
- `LowValue`: `float64`
- `HighValue`: `float64`

## FactSensitivity

Grain: one row per scenario, driver, and case

Rows: 36

Columns:
- `ScenarioID`: `str`
- `Driver`: `str`
- `CaseLabel`: `str`
- `DriverCase`: `str`
- `EquityValueDelta`: `float64`
- `EquityValue`: `float64`

## FactRiskRegister

Grain: one row per scenario and risk

Rows: 30

Columns:
- `ScenarioID`: `str`
- `RiskID`: `str`
- `RiskCategory`: `str`
- `Risk`: `str`
- `Severity`: `str`
- `Probability`: `float64`
- `ExposureUSD`: `float64`
- `Owner`: `str`
- `MitigationStatus`: `str`
- `BoardAsk`: `str`

## FactKpiScorecard

Grain: one row per board KPI status item

Rows: 8

Columns:
- `MetricName`: `str`
- `MetricFamily`: `str`
- `ActualDisplay`: `str`
- `PlanDisplay`: `str`
- `VarianceDisplay`: `str`
- `Status`: `str`
- `BoardNarrative`: `str`
- `SortOrder`: `int64`
