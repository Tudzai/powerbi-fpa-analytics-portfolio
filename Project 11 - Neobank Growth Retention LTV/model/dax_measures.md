# DAX Measures

## New Users

```DAX
New Users = SUM ( FactGrowthMonthly[NewUsers] )
```

Format: `#,0`

## KYC Submitted

```DAX
KYC Submitted = SUM ( FactGrowthMonthly[KycSubmitted] )
```

Format: `#,0`

## KYC Approved

```DAX
KYC Approved = SUM ( FactGrowthMonthly[KycApproved] )
```

Format: `#,0`

## Activated Users

```DAX
Activated Users = SUM ( FactGrowthMonthly[ActivatedUsers] )
```

Format: `#,0`

## Funded Accounts

```DAX
Funded Accounts = SUM ( FactGrowthMonthly[FundedAccounts] )
```

Format: `#,0`

## Active Users

```DAX
Active Users = SUM ( FactGrowthMonthly[ActiveUsers] )
```

Format: `#,0`

## Deposit Volume

```DAX
Deposit Volume = SUM ( FactGrowthMonthly[DepositVolume] )
```

Format: `$#,0,,.0M`

## Revenue

```DAX
Revenue = SUM ( FactGrowthMonthly[TotalRevenue] )
```

Format: `$#,0,,.0M`

## Gross Profit

```DAX
Gross Profit = SUM ( FactGrowthMonthly[GrossProfit] )
```

Format: `$#,0,,.0M`

## Marketing Spend

```DAX
Marketing Spend = SUM ( FactGrowthMonthly[MarketingSpend] )
```

Format: `$#,0,,.0M`

## Churned Users

```DAX
Churned Users = SUM ( FactGrowthMonthly[ChurnedUsers] )
```

Format: `#,0`

## Dormant Customers

```DAX
Dormant Customers = SUM ( FactGrowthMonthly[DormantCustomers] )
```

Format: `#,0`

## Churn Risk Users

```DAX
Churn Risk Users = SUM ( FactGrowthMonthly[ChurnRiskUsers] )
```

Format: `#,0`

## KYC Completion Rate

```DAX
KYC Completion Rate = DIVIDE ( [KYC Approved], [New Users] )
```

Format: `0.0%`

## Activation Rate

```DAX
Activation Rate = DIVIDE ( [Activated Users], [New Users] )
```

Format: `0.0%`

## Funded Rate

```DAX
Funded Rate = DIVIDE ( [Funded Accounts], [New Users] )
```

Format: `0.0%`

## CAC

```DAX
CAC = DIVIDE ( [Marketing Spend], [Funded Accounts] )
```

Format: `$#,0`

## Monthly ARPU

```DAX
Monthly ARPU = DIVIDE ( [Revenue], [Active Users] )
```

Format: `$#,0.00`

## Churn Rate

```DAX
Churn Rate = DIVIDE ( [Churned Users], [Active Users] + [Churned Users] )
```

Format: `0.0%`

## LTV

```DAX
LTV = DIVIDE ( [Monthly ARPU] * 0.68, [Churn Rate] )
```

Format: `$#,0`

## LTV CAC Ratio

```DAX
LTV CAC Ratio = DIVIDE ( [LTV], [CAC] )
```

Format: `0.0x`

## Payback Months

```DAX
Payback Months = DIVIDE ( [CAC], DIVIDE ( [Gross Profit], [Active Users] ) )
```

Format: `0.0`

## Marketing ROI

```DAX
Marketing ROI = DIVIDE ( [Gross Profit] - [Marketing Spend], [Marketing Spend] )
```

Format: `0.0%`

## Contribution Profit

```DAX
Contribution Profit = [Gross Profit] - [Marketing Spend]
```

Format: `$#,0,,.0M`

## Funnel Users

```DAX
Funnel Users = SUM ( FunnelMonthly[UserCount] )
```

Format: `#,0`

## Cohort Retention Rate

```DAX
Cohort Retention Rate = DIVIDE ( SUM ( CohortRetention[RetainedUsers] ), SUM ( CohortRetention[CohortSize] ) )
```

Format: `0.0%`

## Cohort LTV

```DAX
Cohort LTV = DIVIDE ( SUM ( CohortRetention[CumulativeRevenue] ), SUM ( CohortRetention[CohortSize] ) )
```

Format: `$#,0`

## Campaign Spend

```DAX
Campaign Spend = SUM ( CampaignMonthly[Spend] )
```

Format: `$#,0,,.0M`

## Campaign Revenue

```DAX
Campaign Revenue = SUM ( CampaignMonthly[Revenue] )
```

Format: `$#,0,,.0M`

## Campaign Gross Profit

```DAX
Campaign Gross Profit = SUM ( CampaignMonthly[GrossProfit] )
```

Format: `$#,0,,.0M`

## Campaign Funded Accounts

```DAX
Campaign Funded Accounts = SUM ( CampaignMonthly[FundedAccounts] )
```

Format: `#,0`

## Campaign CAC

```DAX
Campaign CAC = DIVIDE ( [Campaign Spend], [Campaign Funded Accounts] )
```

Format: `$#,0`

## Campaign ROI

```DAX
Campaign ROI = DIVIDE ( [Campaign Gross Profit] - [Campaign Spend], [Campaign Spend] )
```

Format: `0.0%`

## Campaign Payback Months

```DAX
Campaign Payback Months = DIVIDE ( [Campaign CAC], DIVIDE ( [Campaign Gross Profit], [Campaign Funded Accounts] ) )
```

Format: `0.0`

## Latest New Users

```DAX
Latest New Users = VAR m = MAX ( DimMonth[MonthStart] ) RETURN CALCULATE ( [New Users], FILTER ( ALLSELECTED ( DimMonth ), DimMonth[MonthStart] = m ) )
```

Format: `#,0`

## Latest Active Users

```DAX
Latest Active Users = VAR m = MAX ( DimMonth[MonthStart] ) RETURN CALCULATE ( [Active Users], FILTER ( ALLSELECTED ( DimMonth ), DimMonth[MonthStart] = m ) )
```

Format: `#,0`

## Latest Funded Accounts

```DAX
Latest Funded Accounts = VAR m = MAX ( DimMonth[MonthStart] ) RETURN CALCULATE ( [Funded Accounts], FILTER ( ALLSELECTED ( DimMonth ), DimMonth[MonthStart] = m ) )
```

Format: `#,0`

## Latest Deposits

```DAX
Latest Deposits = VAR m = MAX ( DimMonth[MonthStart] ) RETURN CALCULATE ( [Deposit Volume], FILTER ( ALLSELECTED ( DimMonth ), DimMonth[MonthStart] = m ) )
```

Format: `$#,0,,.0M`

## Latest Revenue

```DAX
Latest Revenue = VAR m = MAX ( DimMonth[MonthStart] ) RETURN CALCULATE ( [Revenue], FILTER ( ALLSELECTED ( DimMonth ), DimMonth[MonthStart] = m ) )
```

Format: `$#,0,,.0M`

## Latest CAC

```DAX
Latest CAC = VAR m = MAX ( DimMonth[MonthStart] ) RETURN CALCULATE ( [CAC], FILTER ( ALLSELECTED ( DimMonth ), DimMonth[MonthStart] = m ) )
```

Format: `$#,0`

## Latest LTV

```DAX
Latest LTV = VAR m = MAX ( DimMonth[MonthStart] ) RETURN CALCULATE ( [LTV], FILTER ( ALLSELECTED ( DimMonth ), DimMonth[MonthStart] = m ) )
```

Format: `$#,0`

## Latest LTV CAC Ratio

```DAX
Latest LTV CAC Ratio = VAR m = MAX ( DimMonth[MonthStart] ) RETURN CALCULATE ( [LTV CAC Ratio], FILTER ( ALLSELECTED ( DimMonth ), DimMonth[MonthStart] = m ) )
```

Format: `0.0x`
