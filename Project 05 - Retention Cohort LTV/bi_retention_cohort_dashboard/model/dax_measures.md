# DAX Measures

## Latest Month

```DAX
Latest Month = MAX ( DimMonth[MonthStart] )
```
Format: `yyyy-mm-dd`

## New Users

```DAX
New Users = SUM ( MonthlyKPIs[NewUsers] )
```
Format: `#,0`

## Active Users

```DAX
Active Users = SUM ( MonthlyKPIs[ActiveUsers] )
```
Format: `#,0`

## Returning Users

```DAX
Returning Users = SUM ( MonthlyKPIs[ReturningUsers] )
```
Format: `#,0`

## New Customers

```DAX
New Customers = SUM ( MonthlyKPIs[NewCustomers] )
```
Format: `#,0`

## Active Customers

```DAX
Active Customers = SUM ( MonthlyKPIs[ActiveCustomers] )
```
Format: `#,0`

## Returning Customers

```DAX
Returning Customers = SUM ( MonthlyKPIs[ReturningCustomers] )
```
Format: `#,0`

## Repeat Purchasers

```DAX
Repeat Purchasers = SUM ( MonthlyKPIs[RepeatPurchasers] )
```
Format: `#,0`

## Repeat Purchase Rate

```DAX
Repeat Purchase Rate = DIVIDE ( [Repeat Purchasers], [Active Customers] )
```
Format: `0.0%`

## Churn Signal Customers

```DAX
Churn Signal Customers = SUM ( MonthlyKPIs[ChurnSignalCustomers] )
```
Format: `#,0`

## Churn Risk Revenue

```DAX
Churn Risk Revenue = SUM ( MonthlyKPIs[ChurnRiskRevenue] )
```
Format: `$#,0,.0K`

## Net Revenue

```DAX
Net Revenue = SUM ( MonthlyKPIs[NetRevenue] )
```
Format: `$#,0,.0K`

## LTV To Date

```DAX
LTV To Date = AVERAGE ( MonthlyKPIs[LTVToDate] )
```
Format: `$#,0`

## Cohort Retention %

```DAX
Cohort Retention % = DIVIDE ( SUM ( CohortRetention[RetainedCustomers] ), SUM ( CohortRetention[CohortSize] ) )
```
Format: `0.0%`

## Cohort Repeat Purchase %

```DAX
Cohort Repeat Purchase % = DIVIDE ( SUM ( CohortRetention[RepeatCustomers] ), SUM ( CohortRetention[CohortSize] ) )
```
Format: `0.0%`

## Cumulative LTV

```DAX
Cumulative LTV = DIVIDE ( SUM ( CohortRetention[CumulativeRevenue] ), SUM ( CohortRetention[CohortSize] ) )
```
Format: `$#,0`

## Latest Active Users

```DAX
Latest Active Users = VAR m = [Latest Month] RETURN CALCULATE ( [Active Users], DimMonth[MonthStart] = m )
```
Format: `#,0`

## Latest Returning Users

```DAX
Latest Returning Users = VAR m = [Latest Month] RETURN CALCULATE ( [Returning Users], DimMonth[MonthStart] = m )
```
Format: `#,0`

## Latest Repeat Purchase Rate

```DAX
Latest Repeat Purchase Rate = VAR m = [Latest Month] RETURN CALCULATE ( [Repeat Purchase Rate], DimMonth[MonthStart] = m )
```
Format: `0.0%`

## Latest Churn Signals

```DAX
Latest Churn Signals = VAR m = [Latest Month] RETURN CALCULATE ( [Churn Signal Customers], DimMonth[MonthStart] = m )
```
Format: `#,0`

## Latest Net Revenue

```DAX
Latest Net Revenue = VAR m = [Latest Month] RETURN CALCULATE ( [Net Revenue], DimMonth[MonthStart] = m )
```
Format: `$#,0,.0K`
