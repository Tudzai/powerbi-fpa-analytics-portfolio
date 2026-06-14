# Data Dictionary

Synthetic portfolio dataset. Date anchor: latest complete month May 2026.

## DimUser

Grain: One row per synthetic user.

| Column | Type | Sample |
|---|---:|---|
| UserID | str | U000001 |
| SignupDate | str | 2024-02-20 |
| SignupMonth | str | 2024-02-01 |
| AcquisitionChannel | str | Organic |
| Campaign | str | ORG-2402 |
| Region | str | Europe |
| DeviceType | str | Desktop |
| PlanTier | str | Free |
| CustomerSegment | str | Consumer |
| FirstOrderDate | str |  |
| FirstOrderMonth | str |  |
| IsTestUser | int64 | 0 |

## DimMonth

Grain: One row per calendar month.

| Column | Type | Sample |
|---|---:|---|
| MonthStart | str | 2024-01-01 |
| MonthYear | str | Jan 2024 |
| MonthIndex | int64 | 1 |
| Year | int64 | 2024 |
| Quarter | str | Q1 |
| IsLatestCompleteMonth | int64 | 0 |

## FactOrders

Grain: One row per completed order.

| Column | Type | Sample |
|---|---:|---|
| OrderID | str | O00000001 |
| UserID | str | U000002 |
| OrderDate | str | 2026-03-13 |
| OrderMonth | str | 2026-03-01 |
| ProductCategory | str | Core Subscription |
| GrossRevenue | float64 | 82.42 |
| DiscountAmount | float64 | 0.0 |
| RefundAmount | float64 | 0.0 |
| NetRevenue | float64 | 82.42 |
| OrderStatus | str | Completed |

## FactUserMonth

Grain: One row per user per calendar month after signup.

| Column | Type | Sample |
|---|---:|---|
| UserID | str | U000001 |
| MonthStart | str | 2024-02-01 |
| SessionCount | int64 | 6 |
| FeatureEvents | int64 | 11 |
| SupportTickets | int64 | 0 |
| FailedPaymentCount | int64 | 0 |
| OrderCount | float64 | 0.0 |
| NetRevenue | float64 | 0.0 |
| SignupMonth | str | 2024-02-01 |
| FirstOrderMonth | str |  |
| FirstOrderDate | str |  |
| AcquisitionChannel | str | Organic |
| Region | str | Europe |
| PlanTier | str | Free |
| CustomerSegment | str | Consumer |
| MonthIndex | int64 | 2 |
| MonthsSinceSignup | int64 | 0 |
| MonthsSinceFirstOrder | int64 | -1 |
| IsActiveUser | int64 | 1 |
| IsPurchaser | int64 | 0 |
| CumulativeOrders | int64 | 0 |
| CumulativeNetRevenue | float64 | 0.0 |
| IsNewUser | int64 | 1 |
| IsReturningUser | int64 | 0 |
| IsNewCustomer | int64 | 0 |
| IsReturningCustomer | int64 | 0 |
| IsRepeatPurchaser | int64 | 0 |
| DaysSinceLastPurchase | int64 | 9999 |
| RiskScore | float64 | 100.0 |
| IsChurnSignal | int64 | 0 |

## CohortRetention

Grain: One row per first-purchase cohort month and months since cohort.

| Column | Type | Sample |
|---|---:|---|
| CohortMonth | str | 2024-01-01 |
| CohortMonthLabel | str | Jan 2024 |
| ActivityMonth | str | 2024-01-01 |
| MonthsSinceCohort | int64 | 0 |
| CohortSize | int64 | 47 |
| RetainedCustomers | int64 | 47 |
| RepeatCustomers | int64 | 20 |
| NetRevenue | float64 | 4325.9 |
| CumulativeRevenue | float64 | 4325.9 |
| RetentionRate | float64 | 1.0 |
| RepeatPurchaseRate | float64 | 0.4255 |
| CumulativeLTV | float64 | 92.04 |
| IsCompleteCohort | int64 | 1 |

## MonthlyKPIs

Grain: One row per calendar month with dashboard-ready KPI values.

| Column | Type | Sample |
|---|---:|---|
| MonthStart | str | 2024-01-01 |
| NewUsers | int64 | 161 |
| ActiveUsers | int64 | 98 |
| ReturningUsers | int64 | 0 |
| NewCustomers | int64 | 47 |
| ActiveCustomers | int64 | 47 |
| ReturningCustomers | int64 | 0 |
| RepeatPurchasers | int64 | 20 |
| ChurnSignalCustomers | int64 | 0 |
| ChurnRiskRevenue | float64 | 0.0 |
| NetRevenue | float64 | 4325.9 |
| MonthYear | str | Jan 2024 |
| RepeatPurchaseRate | float64 | 0.4255 |
| LTVToDate | float64 | 92.04 |
| M1Retention | float64 | 0.4468 |
| M3Retention | float64 | 0.4043 |
| M6Retention | float64 | 0.2979 |

## MonthlyLifecycleMix

Grain: One row per month and lifecycle bucket.

| Column | Type | Sample |
|---|---:|---|
| MonthStart | str | 2024-01-01 |
| MonthYear | str | Jan 2024 |
| LifecycleType | str | New Users |
| Users | int64 | 161 |

## ChurnRiskSnapshot

Grain: One row per user at the latest complete month.

| Column | Type | Sample |
|---|---:|---|
| UserID | str | U000001 |
| LastOrderDate | str |  |
| DaysSinceLastPurchase | int64 | 9999 |
| LifetimeOrders | int64 | 0 |
| LifetimeNetRevenue | float64 | 0.0 |
| AcquisitionChannel | str | Organic |
| Region | str | Europe |
| PlanTier | str | Free |
| CustomerSegment | str | Consumer |
| RiskScore | float64 | 100.0 |
| RiskBand | str | High |
| ChurnSignal | int64 | 0 |
| RecommendedAction | str | Winback offer |

## SegmentMonthly

Grain: One row per month and segment value.

| Column | Type | Sample |
|---|---:|---|
| MonthStart | str | 2024-01-01 |
| SegmentType | str | Channel |
| SegmentName | str | Lifecycle Email |
| ActiveCustomers | int64 | 3 |
| RepeatPurchaseRate | float64 | 0.6667 |
| RetentionM3 | float64 | 0.4043 |
| NetRevenue | float64 | 572.1 |
| ChurnSignalCustomers | int64 | 0 |
| LTVToDate | float64 | 190.7 |
