# Relationship Map

| From | To | Cardinality | Direction |
|---|---|---|---|
| FactCashPosition[entity_id] | DimEntity[entity_id] | Many-to-one | Single |
| FactCashPosition[bank_id] | DimBank[bank_id] | Many-to-one | Single |
| FactLiquidityFacility[entity_id] | DimEntity[entity_id] | Many-to-one | Single |
| FactWorkingCapital[date_id] | DimDate[date_id] | Many-to-one | Single |
| FactWorkingCapital[entity_id] | DimEntity[entity_id] | Many-to-one | Single |
| FactARInvoice[entity_id] | DimEntity[entity_id] | Many-to-one | Single |
| FactARInvoice[customer_id] | DimCustomer[customer_id] | Many-to-one | Single |
| FactARInvoice[expected_collection_week_id] | DimWeek[week_id] | Many-to-one | Single |
| FactAPInvoice[entity_id] | DimEntity[entity_id] | Many-to-one | Single |
| FactAPInvoice[vendor_id] | DimVendor[vendor_id] | Many-to-one | Single |
| FactAPInvoice[payment_week_id] | DimWeek[week_id] | Many-to-one | Single |
| FactCashForecast[week_id] | DimWeek[week_id] | Many-to-one | Single |
| FactCashForecast[entity_id] | DimEntity[entity_id] | Many-to-one | Single |
| FactCashForecast[scenario_id] | DimScenario[scenario_id] | Many-to-one | Single |
| FactForecastAccuracy[entity_id] | DimEntity[entity_id] | Many-to-one | Single |
| FactFXExposure[entity_id] | DimEntity[entity_id] | Many-to-one | Single |
| FactTreasuryRiskAction[entity_id] | DimEntity[entity_id] | Many-to-one | Single |
