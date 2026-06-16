# Data Dictionary

## DimDate

Rows: 29

Columns: MonthStart, MonthLabel, MonthIndex, Year, Quarter, IsLatestCompleteMonth

## DimPlan

Rows: 5

Columns: PlanID, PlanName, Segment, BaseMRR, GrossMarginTarget, MonthlyChurnTarget, TargetCAC, BenchmarkPaybackMonths

## DimChannel

Rows: 5

Columns: ChannelID, ChannelName, Motion, SourceType, CACIndex, QualityIndex

## DimRegion

Rows: 4

Columns: RegionID, Region, GeoGroup, ScaleIndex

## DimCustomer

Rows: 520

Columns: CustomerID, AccountName, PlanID, PlanName, Segment, ChannelID, ChannelName, Motion, RegionID, Region, Industry, AcquisitionMonth

## FactSubscriptionMonthly

Rows: 6,494

Columns: MonthStart, CustomerID, PlanID, ChannelID, RegionID, BeginningMRR, NewMRR, ExpansionMRR, ContractionMRR, ChurnMRR, EndingMRR, RecognizedRevenue, GrossMargin, Seats, StartingLogo, ActiveLogo, NewLogo, ChurnedLogo, IsSynthetic

## FactMRRMovement

Rows: 116

Columns: MonthStart, MovementType, MovementSort, ARRMovement, FavorableFlag

## FactCohortRetention

Rows: 4,806

Columns: CohortMonth, CohortLabel, ActivityMonth, MonthsSinceCohort, PlanID, ChannelID, CohortStartMRR, RetainedMRR, ExpansionMRR, ContractionMRR, StartLogos, ActiveLogos, ChurnedLogos, NetRetentionRate, GrossRetentionRate

## FactAcquisitionMonthly

Rows: 447

Columns: MonthStart, PlanID, ChannelID, RegionID, NewCustomers, NewARRBooked, SalesMarketingSpend, SalesPipelineARR

## FactFinanceMonthly

Rows: 29

Columns: MonthStart, Revenue, COGS, GrossMargin, SalesMarketingExpense, ResearchDevelopmentExpense, GeneralAdminExpense, CustomerSuccessExpense, EBITDA, CashBalance, NetBurn, ActualARR, PlanARR, ForecastARR, ARRGrowthPct

## FactForecast

Rows: 87

Columns: MonthStart, Scenario, ARRValue, RevenueValue

## FactAccountHealth

Rows: 240

Columns: CustomerID, AccountName, PlanID, ChannelID, RegionID, Segment, Industry, CurrentARR, Seats, HealthScore, RenewalRisk, NextAction

## MonthlyKPIs

Rows: 29

Columns: MonthStart, BeginningMRR, NewMRR, ExpansionMRR, ContractionMRR, ChurnMRR, EndingMRR, RecognizedRevenue, GrossMargin, StartingCustomers, ActiveCustomers, NewCustomers, ChurnedCustomers, MonthLabel, MonthIndex, ARR, NetNewARR, NRR, GRR, RevenueChurnRate, LogoChurnRate, GrossMarginPct, ARRGrowthPct
