# Data Dictionary

## DimDate

Grain: one row per month

Rows: 29

Columns: MonthStart, MonthLabel, MonthIndex, Year, Quarter, IsLatestCompleteMonth

## DimScenario

Grain: one row per scenario

Rows: 3

Columns: ScenarioID, ScenarioName, RevenueIndex, MarginIndex, BurnIndex, ScenarioSort

## DimBusinessUnit

Grain: one row per business unit

Rows: 4

Columns: BusinessUnitID, BusinessUnit, RevenueFamily, MixWeight, TargetGrossMargin, GrowthIndex

## DimRegion

Grain: one row per region

Rows: 4

Columns: RegionID, Region, RegionMaturity, MixWeight, DemandIndex

## DimCostCategory

Grain: one row per cost category

Rows: 4

Columns: CostCategoryID, CostCategory, RevenueLoad

## FactPnlMonthly

Grain: one row per month, scenario, business unit, and region

Rows: 1,392

Columns: MonthStart, ScenarioID, BusinessUnitID, RegionID, Revenue, PlanRevenue, ForecastRevenue, COGS, GrossProfit, OperatingExpense, EBITDA, PlanEBITDA, ForecastEBITDA, NetIncome, IsSynthetic

## FactOpexMonthly

Grain: one row per month, scenario, and cost category

Rows: 348

Columns: MonthStart, ScenarioID, CostCategoryID, OperatingExpense, PlanOperatingExpense, ForecastOperatingExpense

## FactCashMonthly

Grain: one row per month and scenario

Rows: 87

Columns: MonthStart, ScenarioID, CashBalance, OperatingCashFlow, Capex, FreeCashFlow, NetBurn, RunwayMonths, FundingNeed, Debt, WorkingCapital, FinancingInflow

## FactStatementLines

Grain: one row per month, scenario, and financial statement line

Rows: 957

Columns: MonthStart, ScenarioID, Statement, LineItem, LineSort, ValueActual, ValuePlan, ValueForecast

## FactCovenantMonthly

Grain: one row per month and scenario

Rows: 87

Columns: MonthStart, ScenarioID, RevenueLTM, EBITDALTM, NetDebt, LeverageRatio, LeverageLimit, LeverageHeadroom, InterestCoverage, InterestCoverageLimit, Liquidity, LiquidityMinimum, LiquidityHeadroom, CovenantStatus, RiskScore

## FactValuation

Grain: one row per scenario and valuation method

Rows: 15

Columns: ScenarioID, Method, MethodSort, Multiple, EnterpriseValue, EquityValue, LowValue, HighValue

## FactSensitivity

Grain: one row per scenario, driver, and case

Rows: 36

Columns: ScenarioID, Driver, CaseLabel, DriverCase, EquityValueDelta, EquityValue

## FactRiskRegister

Grain: one row per scenario and risk

Rows: 30

Columns: ScenarioID, RiskID, RiskCategory, Risk, Severity, Probability, ExposureUSD, Owner, MitigationStatus, BoardAsk

## FactKpiScorecard

Grain: one row per board KPI status item

Rows: 8

Columns: MetricName, MetricFamily, ActualDisplay, PlanDisplay, VarianceDisplay, Status, BoardNarrative, SortOrder
