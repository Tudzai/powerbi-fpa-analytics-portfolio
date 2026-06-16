# DAX Measures

## Beginning MRR

```DAX
Beginning MRR = SUM ( FactSubscriptionMonthly[BeginningMRR] )
```

Format: `$#,0,,.0M`

## Ending MRR

```DAX
Ending MRR = SUM ( FactSubscriptionMonthly[EndingMRR] )
```

Format: `$#,0,,.0M`

## ARR

```DAX
ARR = [Ending MRR] * 12
```

Format: `$#,0,,.0M`

## New ARR

```DAX
New ARR = SUM ( FactSubscriptionMonthly[NewMRR] ) * 12
```

Format: `$#,0,,.0M`

## Expansion ARR

```DAX
Expansion ARR = SUM ( FactSubscriptionMonthly[ExpansionMRR] ) * 12
```

Format: `$#,0,,.0M`

## Contraction ARR

```DAX
Contraction ARR = ABS ( SUM ( FactSubscriptionMonthly[ContractionMRR] ) ) * 12
```

Format: `$#,0,,.0M`

## Churn ARR

```DAX
Churn ARR = ABS ( SUM ( FactSubscriptionMonthly[ChurnMRR] ) ) * 12
```

Format: `$#,0,,.0M`

## Net New ARR

```DAX
Net New ARR = [New ARR] + [Expansion ARR] - [Contraction ARR] - [Churn ARR]
```

Format: `$#,0,,.0M`

## ARR Movement

```DAX
ARR Movement = SUM ( FactMRRMovement[ARRMovement] )
```

Format: `$#,0,,.0M`

## Revenue

```DAX
Revenue = SUM ( FactSubscriptionMonthly[RecognizedRevenue] )
```

Format: `$#,0,,.0M`

## Gross Margin

```DAX
Gross Margin = SUM ( FactSubscriptionMonthly[GrossMargin] )
```

Format: `$#,0,,.0M`

## Gross Margin %

```DAX
Gross Margin % = DIVIDE ( [Gross Margin], [Revenue] )
```

Format: `0.0%`

## Starting Customers

```DAX
Starting Customers = SUM ( FactSubscriptionMonthly[StartingLogo] )
```

Format: `#,0`

## Active Customers

```DAX
Active Customers = SUM ( FactSubscriptionMonthly[ActiveLogo] )
```

Format: `#,0`

## New Customers

```DAX
New Customers = SUM ( FactSubscriptionMonthly[NewLogo] )
```

Format: `#,0`

## Churned Customers

```DAX
Churned Customers = SUM ( FactSubscriptionMonthly[ChurnedLogo] )
```

Format: `#,0`

## NRR

```DAX
NRR = DIVIDE ( [Ending MRR] - SUM ( FactSubscriptionMonthly[NewMRR] ), [Beginning MRR] )
```

Format: `0.0%`

## GRR

```DAX
GRR = DIVIDE ( [Beginning MRR] - [Contraction ARR] / 12 - [Churn ARR] / 12, [Beginning MRR] )
```

Format: `0.0%`

## Revenue Churn Rate

```DAX
Revenue Churn Rate = DIVIDE ( [Churn ARR], [Beginning MRR] * 12 )
```

Format: `0.0%`

## Logo Churn Rate

```DAX
Logo Churn Rate = DIVIDE ( [Churned Customers], [Starting Customers] )
```

Format: `0.0%`

## S&M Spend

```DAX
S&M Spend = SUM ( FactAcquisitionMonthly[SalesMarketingSpend] )
```

Format: `$#,0,,.0M`

## New ARR Booked

```DAX
New ARR Booked = SUM ( FactAcquisitionMonthly[NewARRBooked] )
```

Format: `$#,0,,.0M`

## CAC

```DAX
CAC = DIVIDE ( [S&M Spend], SUM ( FactAcquisitionMonthly[NewCustomers] ) )
```

Format: `$#,0`

## ARPA

```DAX
ARPA = DIVIDE ( [Ending MRR], [Active Customers] )
```

Format: `$#,0`

## LTV

```DAX
LTV = DIVIDE ( [ARPA] * 12 * [Gross Margin %], [Revenue Churn Rate] )
```

Format: `$#,0`

## LTV CAC Ratio

```DAX
LTV CAC Ratio = DIVIDE ( [LTV], [CAC] )
```

Format: `0.0x`

## CAC Payback Months

```DAX
CAC Payback Months = DIVIDE ( [CAC], DIVIDE ( [Gross Margin], [Active Customers] ) )
```

Format: `0.0`

## Magic Number

```DAX
Magic Number = DIVIDE ( [Net New ARR], [S&M Spend] )
```

Format: `0.0x`

## EBITDA

```DAX
EBITDA = SUM ( FactFinanceMonthly[EBITDA] )
```

Format: `$#,0,,.0M`

## EBITDA Margin

```DAX
EBITDA Margin = DIVIDE ( [EBITDA], SUM ( FactFinanceMonthly[Revenue] ) )
```

Format: `0.0%`

## ARR Growth %

```DAX
ARR Growth % = AVERAGE ( FactFinanceMonthly[ARRGrowthPct] )
```

Format: `0.0%`

## Rule of 40

```DAX
Rule of 40 = [ARR Growth %] + [EBITDA Margin]
```

Format: `0.0%`

## Net Burn

```DAX
Net Burn = SUM ( FactFinanceMonthly[NetBurn] )
```

Format: `$#,0,,.0M`

## Cash Balance

```DAX
Cash Balance = SUM ( FactFinanceMonthly[CashBalance] )
```

Format: `$#,0,,.0M`

## Burn Multiple

```DAX
Burn Multiple = DIVIDE ( [Net Burn], DIVIDE ( [Net New ARR], 12 ) )
```

Format: `0.0x`

## Forecast ARR

```DAX
Forecast ARR = SUM ( FactFinanceMonthly[ForecastARR] )
```

Format: `$#,0,,.0M`

## Plan ARR

```DAX
Plan ARR = SUM ( FactFinanceMonthly[PlanARR] )
```

Format: `$#,0,,.0M`

## Forecast Accuracy

```DAX
Forecast Accuracy = 1 - DIVIDE ( ABS ( [ARR] - [Forecast ARR] ), [ARR] )
```

Format: `0.0%`

## Cohort NRR

```DAX
Cohort NRR = DIVIDE ( SUM ( FactCohortRetention[RetainedMRR] ), SUM ( FactCohortRetention[CohortStartMRR] ) )
```

Format: `0.0%`

## Cohort GRR

```DAX
Cohort GRR = DIVIDE ( SUM ( FactCohortRetention[RetainedMRR] ) - SUM ( FactCohortRetention[ExpansionMRR] ), SUM ( FactCohortRetention[CohortStartMRR] ) )
```

Format: `0.0%`

## Cohort Active Logos

```DAX
Cohort Active Logos = SUM ( FactCohortRetention[ActiveLogos] )
```

Format: `#,0`

## Cohort LTV

```DAX
Cohort LTV = DIVIDE ( SUM ( FactCohortRetention[RetainedMRR] ) * 12, SUM ( FactCohortRetention[StartLogos] ) )
```

Format: `$#,0`

## Scenario ARR

```DAX
Scenario ARR = SUM ( FactForecast[ARRValue] )
```

Format: `$#,0,,.0M`

## Account Health Score

```DAX
Account Health Score = AVERAGE ( FactAccountHealth[HealthScore] )
```

Format: `0.0`

## Latest ARR

```DAX
Latest ARR = VAR m = MAX ( DimDate[MonthStart] ) RETURN CALCULATE ( [ARR], FILTER ( ALLSELECTED ( DimDate ), DimDate[MonthStart] = m ) )
```

Format: `$#,0,,.0M`

## Latest Net New ARR

```DAX
Latest Net New ARR = VAR m = MAX ( DimDate[MonthStart] ) RETURN CALCULATE ( [Net New ARR], FILTER ( ALLSELECTED ( DimDate ), DimDate[MonthStart] = m ) )
```

Format: `$#,0,,.0M`

## Latest NRR

```DAX
Latest NRR = VAR m = MAX ( DimDate[MonthStart] ) RETURN CALCULATE ( [NRR], FILTER ( ALLSELECTED ( DimDate ), DimDate[MonthStart] = m ) )
```

Format: `0.0%`

## Latest GRR

```DAX
Latest GRR = VAR m = MAX ( DimDate[MonthStart] ) RETURN CALCULATE ( [GRR], FILTER ( ALLSELECTED ( DimDate ), DimDate[MonthStart] = m ) )
```

Format: `0.0%`

## Latest CAC Payback

```DAX
Latest CAC Payback = VAR m = MAX ( DimDate[MonthStart] ) RETURN CALCULATE ( [CAC Payback Months], FILTER ( ALLSELECTED ( DimDate ), DimDate[MonthStart] = m ) )
```

Format: `0.0`

## Latest LTV CAC Ratio

```DAX
Latest LTV CAC Ratio = VAR m = MAX ( DimDate[MonthStart] ) RETURN CALCULATE ( [LTV CAC Ratio], FILTER ( ALLSELECTED ( DimDate ), DimDate[MonthStart] = m ) )
```

Format: `0.0x`

## Latest Rule of 40

```DAX
Latest Rule of 40 = VAR m = MAX ( DimDate[MonthStart] ) RETURN CALCULATE ( [Rule of 40], FILTER ( ALLSELECTED ( DimDate ), DimDate[MonthStart] = m ) )
```

Format: `0.0%`

## Latest Forecast Accuracy

```DAX
Latest Forecast Accuracy = VAR m = MAX ( DimDate[MonthStart] ) RETURN CALCULATE ( [Forecast Accuracy], FILTER ( ALLSELECTED ( DimDate ), DimDate[MonthStart] = m ) )
```

Format: `0.0%`
