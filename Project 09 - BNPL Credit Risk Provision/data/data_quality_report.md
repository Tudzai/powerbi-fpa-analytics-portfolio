# Data Quality Report

- Synthetic data: yes, seed 90209.
- Latest closed snapshot month: 2026-05-01.
- Prepared tables: 14.

| Table | Rows | Columns | Missing cells | Duplicate key count |
|---|---:|---:|---:|---:|
| dim_date | 882 | 5 | 0 | 0 |
| dim_month | 29 | 4 | 0 | 0 |
| dim_product | 4 | 4 | 0 | 0 |
| dim_channel | 5 | 2 | 0 | 0 |
| dim_risk_band | 5 | 4 | 0 | 0 |
| dim_merchant | 60 | 4 | 0 | 0 |
| dim_customer_segment | 4 | 2 | 0 | 0 |
| fact_applications | 52,000 | 19 | 0 | 0 |
| fact_loans | 33,051 | 19 | 0 | 0 |
| fact_loan_monthly | 218,547 | 27 | 0 | 0 |
| fact_collections | 40,586 | 17 | 0 | 0 |
| fact_vintage | 344 | 13 | 0 | 0 |
| fact_roll_rate | 1,775 | 6 | 0 | 0 |
| fact_provision_forecast | 21 | 7 | 0 | 0 |
