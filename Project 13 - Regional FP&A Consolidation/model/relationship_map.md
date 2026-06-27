| From | To | Cardinality | Direction |
|---|---|---:|---|
| DimDate[date_id] | FactFinancials[date_id] | 1:* | single |
| DimDate[date_id] | FactFinancialSummary[date_id] | 1:* | single |
| DimDate[date_id] | FactVarianceDriverBridge[date_id] | 1:* | single |
| DimDate[date_id] | FactCloseExceptions[date_id] | 1:* | single |
| DimDate[date_id] | FactFXRate[date_id] | 1:* | single |
| DimEntity[entity_id] | FactFinancials[entity_id] | 1:* | single |
| DimEntity[entity_id] | FactFinancialSummary[entity_id] | 1:* | single |
| DimEntity[entity_id] | FactVarianceDriverBridge[entity_id] | 1:* | single |
| DimEntity[entity_id] | FactCloseExceptions[entity_id] | 1:* | single |
| DimBusinessUnit[business_unit_id] | FactFinancials[business_unit_id] | 1:* | single |
| DimBusinessUnit[business_unit_id] | FactFinancialSummary[business_unit_id] | 1:* | single |
| DimBusinessUnit[business_unit_id] | FactVarianceDriverBridge[business_unit_id] | 1:* | single |
| DimBusinessUnit[business_unit_id] | FactCloseExceptions[business_unit_id] | 1:* | single |
| DimScenario[scenario_id] | FactFinancials[scenario_id] | 1:* | single |
| DimScenario[scenario_id] | FactFinancialSummary[scenario_id] | 1:* | single |
| DimAccount[account_id] | FactFinancials[account_id] | 1:* | single |
