# Data Dictionary

Synthetic portfolio dataset for a digital payments profitability dashboard. Grain is monthly merchant x payment method x channel for the main fact table.

| Table | Rows | Columns |
|---|---:|---:|
| dim_date | 29 | 9 |
| dim_merchant | 200 | 15 |
| dim_payment_method | 5 | 7 |
| dim_channel | 5 | 5 |
| dim_scenario | 6 | 6 |
| fact_payment_month | 69,600 | 29 |
| fact_fee_bridge | 6 | 5 |

Core fact columns include GMV, transaction count, revenue fee, refund/chargeback amounts, cost components, contribution margin, take rate, cost per transaction, and auth success rate.
