# Data Dictionary

Synthetic BNPL credit risk dataset. Grain is documented per table.

## DimDate
- Grain: dimension lookup

| Column | Type |
|---|---|
| date | datetime64[us] |
| month_start | datetime64[s] |
| month_label | str |
| year | int32 |
| quarter | str |

## DimMonth
- Grain: dimension lookup

| Column | Type |
|---|---|
| month_start | datetime64[us] |
| month_label | str |
| month_index | int64 |
| year | int32 |

## DimProduct
- Grain: dimension lookup

| Column | Type |
|---|---|
| product_type | str |
| term_months | int64 |
| product_family | str |
| apr_policy | float64 |

## DimChannel
- Grain: dimension lookup

| Column | Type |
|---|---|
| channel | str |
| channel_group | str |

## DimRiskBand
- Grain: dimension lookup

| Column | Type |
|---|---|
| risk_band | str |
| risk_order | int64 |
| risk_appetite | str |
| pd_floor | float64 |

## DimMerchant
- Grain: dimension lookup

| Column | Type |
|---|---|
| merchant_id | str |
| merchant_name | str |
| merchant_category | str |
| merchant_tier | str |

## DimCustomerSegment
- Grain: dimension lookup

| Column | Type |
|---|---|
| customer_segment | str |
| repeat_type | str |

## FactApplications
- Grain: one credit application

| Column | Type |
|---|---|
| application_id | str |
| application_date | datetime64[us] |
| application_month | datetime64[us] |
| product_type | str |
| channel | str |
| customer_segment | str |
| region | str |
| merchant_id | str |
| merchant_category | str |
| requested_amount | float64 |
| credit_score | int64 |
| risk_band | str |
| pd_12m | float64 |
| lgd | float64 |
| approved_flag | int64 |
| disbursed_flag | int64 |
| approved_amount | float64 |
| funded_amount | float64 |
| decision | str |

## FactLoans
- Grain: one funded loan

| Column | Type |
|---|---|
| loan_id | str |
| application_id | str |
| application_date | datetime64[us] |
| origination_month | datetime64[us] |
| product_type | str |
| channel | str |
| customer_segment | str |
| region | str |
| merchant_id | str |
| merchant_category | str |
| funded_amount | float64 |
| credit_score | int64 |
| risk_band | str |
| pd_12m | float64 |
| lgd | float64 |
| term_months | int64 |
| apr | float64 |
| expected_loss_at_origination | float64 |
| limit_utilization | float64 |

## FactLoanMonthly
- Grain: one loan per snapshot month

| Column | Type |
|---|---|
| loan_id | str |
| snapshot_month | datetime64[us] |
| mob | int64 |
| product_type | str |
| channel | str |
| customer_segment | str |
| region | str |
| merchant_id | str |
| merchant_category | str |
| risk_band | str |
| dpd_bucket | str |
| prior_dpd_bucket | str |
| funded_amount | float64 |
| current_principal | float64 |
| delinquency_balance | float64 |
| dpd30_balance | float64 |
| dpd60_balance | float64 |
| npl_balance | float64 |
| chargeoff_amount | float64 |
| expected_loss_amount | float64 |
| provision_amount | float64 |
| payment_due | float64 |
| payment_received | float64 |
| autopay_failure_flag | int64 |
| npl_flag | int64 |
| dpd30_flag | int64 |
| dpd60_flag | int64 |

## FactCollections
- Grain: one collections case

| Column | Type |
|---|---|
| case_id | str |
| loan_id | str |
| snapshot_month | datetime64[us] |
| dpd_bucket | str |
| risk_band | str |
| product_type | str |
| channel | str |
| customer_segment | str |
| region | str |
| queue | str |
| contacted_flag | int64 |
| promise_to_pay_flag | int64 |
| resolved_flag | int64 |
| sla_hours | float64 |
| within_sla_flag | int64 |
| recovery_amount | float64 |
| case_balance | float64 |

## FactVintage
- Grain: one origination cohort per MOB

| Column | Type |
|---|---|
| origination_month | datetime64[us] |
| mob | int64 |
| loan_count | int64 |
| originated_amount | float64 |
| outstanding_balance | float64 |
| dpd30_balance | float64 |
| dpd60_balance | float64 |
| npl_balance | float64 |
| chargeoff_amount | float64 |
| dpd30_rate | float64 |
| dpd60_rate | float64 |
| npl_rate | float64 |
| cumulative_loss_rate | float64 |

## FactRollRate
- Grain: one month, from bucket, to bucket

| Column | Type |
|---|---|
| snapshot_month | datetime64[us] |
| prior_dpd_bucket | str |
| dpd_bucket | str |
| loan_count | int64 |
| balance | float64 |
| roll_rate | float64 |

## FactProvisionForecast
- Grain: one scenario per forecast month

| Column | Type |
|---|---|
| forecast_month | datetime64[us] |
| scenario | str |
| forecast_balance | float64 |
| forecast_expected_loss | float64 |
| forecast_recovery | float64 |
| forecast_provision | float64 |
| incremental_provision | float64 |
