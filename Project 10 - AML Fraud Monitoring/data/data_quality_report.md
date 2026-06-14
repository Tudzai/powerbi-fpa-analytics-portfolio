# Data Quality Report

Data is deterministic synthetic portfolio data generated for an AML / Fraud Monitoring Command Center. It is not production, customer, or regulated data.

| Table | Rows | Columns | Duplicate Key Check | Missing Critical Values |
|---|---:|---:|---|---:|
| dim_date | 516 | 10 | 0 duplicate rows | 0 |
| dim_country | 12 | 5 | 0 duplicate rows | 0 |
| dim_corridor | 12 | 7 | 0 duplicate rows | 0 |
| dim_channel | 8 | 4 | 0 duplicate rows | 0 |
| dim_product | 8 | 4 | 0 duplicate rows | 0 |
| dim_rule | 10 | 8 | 0 duplicate rows | 0 |
| dim_analyst | 8 | 4 | 0 duplicate rows | 0 |
| dim_customer | 180 | 12 | 0 duplicate rows | 0 |
| fact_transactions | 36,000 | 12 | 0 duplicate rows | 0 |
| fact_alerts | 6,611 | 19 | 0 duplicate rows | 0 |
| fact_cases | 3,556 | 17 | 0 duplicate rows | 0 |
| fact_rule_governance | 26 | 10 | 0 duplicate rows | 0 |
