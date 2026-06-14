# Relationship Map

- `FactAUMMonthly[MonthStart]` -> `DimDate[MonthStart]` (many-to-one, single direction)
- `FactAllocationMonthly[MonthStart]` -> `DimDate[MonthStart]` (many-to-one, single direction)
- `FactRetentionActions[MonthStart]` -> `DimDate[MonthStart]` (many-to-one, single direction)
- `FactAUMMonthly[ClientID]` -> `DimClient[ClientID]` (many-to-one, single direction)
- `FactAllocationMonthly[ClientID]` -> `DimClient[ClientID]` (many-to-one, single direction)
- `FactRetentionActions[ClientID]` -> `DimClient[ClientID]` (many-to-one, single direction)
- `FactAUMMonthly[ModelPortfolio]` -> `DimPortfolio[ModelPortfolio]` (many-to-one, single direction)
- `FactAllocationMonthly[ModelPortfolio]` -> `DimPortfolio[ModelPortfolio]` (many-to-one, single direction)
