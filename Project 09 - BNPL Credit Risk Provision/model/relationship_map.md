# Relationship Map

| From | Column | To | Column | Direction |
|---|---|---|---|---|
| FactApplications | application_month | DimMonth | month_start | one direction |
| FactApplications | product_type | DimProduct | product_type | one direction |
| FactApplications | channel | DimChannel | channel | one direction |
| FactApplications | risk_band | DimRiskBand | risk_band | one direction |
| FactApplications | merchant_id | DimMerchant | merchant_id | one direction |
| FactApplications | customer_segment | DimCustomerSegment | customer_segment | one direction |
| FactLoans | origination_month | DimMonth | month_start | one direction |
| FactLoans | product_type | DimProduct | product_type | one direction |
| FactLoans | channel | DimChannel | channel | one direction |
| FactLoans | risk_band | DimRiskBand | risk_band | one direction |
| FactLoans | merchant_id | DimMerchant | merchant_id | one direction |
| FactLoans | customer_segment | DimCustomerSegment | customer_segment | one direction |
| FactLoanMonthly | snapshot_month | DimMonth | month_start | one direction |
| FactLoanMonthly | product_type | DimProduct | product_type | one direction |
| FactLoanMonthly | channel | DimChannel | channel | one direction |
| FactLoanMonthly | risk_band | DimRiskBand | risk_band | one direction |
| FactLoanMonthly | merchant_id | DimMerchant | merchant_id | one direction |
| FactLoanMonthly | customer_segment | DimCustomerSegment | customer_segment | one direction |
| FactCollections | snapshot_month | DimMonth | month_start | one direction |
| FactCollections | product_type | DimProduct | product_type | one direction |
| FactCollections | channel | DimChannel | channel | one direction |
| FactCollections | risk_band | DimRiskBand | risk_band | one direction |
| FactCollections | customer_segment | DimCustomerSegment | customer_segment | one direction |
| FactVintage | origination_month | DimMonth | month_start | one direction |
| FactRollRate | snapshot_month | DimMonth | month_start | one direction |
