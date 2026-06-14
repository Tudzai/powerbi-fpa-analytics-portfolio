# Relationship Map

| Relationship | From | To | Direction |
|---|---|---|---|
| FactTransactions_Date | FactTransactions[DateKey] | DimDate[DateKey] | Single |
| FactTransactions_Customer | FactTransactions[CustomerKey] | DimCustomer[CustomerKey] | Single |
| FactTransactions_Corridor | FactTransactions[CorridorKey] | DimCorridor[CorridorKey] | Single |
| FactTransactions_Channel | FactTransactions[ChannelKey] | DimChannel[ChannelKey] | Single |
| FactTransactions_Product | FactTransactions[ProductKey] | DimProduct[ProductKey] | Single |
| FactAlerts_Date | FactAlerts[AlertDateKey] | DimDate[DateKey] | Single |
| FactAlerts_Customer | FactAlerts[CustomerKey] | DimCustomer[CustomerKey] | Single |
| FactAlerts_Rule | FactAlerts[RuleKey] | DimRule[RuleKey] | Single |
| FactAlerts_Corridor | FactAlerts[CorridorKey] | DimCorridor[CorridorKey] | Single |
| FactAlerts_Channel | FactAlerts[ChannelKey] | DimChannel[ChannelKey] | Single |
| FactAlerts_Product | FactAlerts[ProductKey] | DimProduct[ProductKey] | Single |
| FactCases_Date | FactCases[CreatedDateKey] | DimDate[DateKey] | Single |
| FactCases_Customer | FactCases[CustomerKey] | DimCustomer[CustomerKey] | Single |
| FactCases_Rule | FactCases[RuleKey] | DimRule[RuleKey] | Single |
| FactCases_Corridor | FactCases[CorridorKey] | DimCorridor[CorridorKey] | Single |
| FactCases_Analyst | FactCases[AnalystKey] | DimAnalyst[AnalystKey] | Single |
| FactRuleGovernance_Date | FactRuleGovernance[ChangeDateKey] | DimDate[DateKey] | Single |
| FactRuleGovernance_Rule | FactRuleGovernance[RuleKey] | DimRule[RuleKey] | Single |
