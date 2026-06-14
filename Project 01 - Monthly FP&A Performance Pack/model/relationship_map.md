# Relationship Map

Use a star-schema model with single-direction filters from dimensions to facts.

## Relationships

| From Dimension | Key | To Fact | Key | Cardinality | Direction | Active |
|---|---:|---|---:|---|---|---|
| DimDate | DateKey | FactFinancials | DateKey | 1:* | Single | Yes |
| DimScenario | ScenarioKey | FactFinancials | ScenarioKey | 1:* | Single | Yes |
| DimBusinessUnit | BusinessUnitKey | FactFinancials | BusinessUnitKey | 1:* | Single | Yes |
| DimProduct | ProductKey | FactFinancials | ProductKey | 1:* | Single | Yes |
| DimRegion | RegionKey | FactFinancials | RegionKey | 1:* | Single | Yes |
| DimCustomer | CustomerKey | FactFinancials | CustomerKey | 1:* | Single | Yes |
| DimDate | DateKey | FactOpexDepartment | DateKey | 1:* | Single | Yes |
| DimScenario | ScenarioKey | FactOpexDepartment | ScenarioKey | 1:* | Single | Yes |
| DimBusinessUnit | BusinessUnitKey | FactOpexDepartment | BusinessUnitKey | 1:* | Single | Yes |
| DimRegion | RegionKey | FactOpexDepartment | RegionKey | 1:* | Single | Yes |
| DimDepartment | DepartmentKey | FactOpexDepartment | DepartmentKey | 1:* | Single | Yes |
| DimDate | DateKey | FactCash | DateKey | 1:* | Single | Yes |
| DimScenario | ScenarioKey | FactCash | ScenarioKey | 1:* | Single | Yes |
| DimBusinessUnit | BusinessUnitKey | FactCash | BusinessUnitKey | 1:* | Single | Yes |
| DimRegion | RegionKey | FactCash | RegionKey | 1:* | Single | Yes |
| DimDate | DateKey | FactBridge | DateKey | 1:* | Single | Yes |
| DimBusinessUnit | BusinessUnitKey | FactBridge | BusinessUnitKey | 1:* | Single | Yes |
| DimRegion | RegionKey | FactBridge | RegionKey | 1:* | Single | Yes |
| DimDate | DateKey | FactCommentary | DateKey | 1:* | Single | Yes |

## Sort By Columns

- DimDate[MonthName] sort by DimDate[MonthNumber]
- DimDate[MonthYear] sort by DimDate[MonthIndex]
- DimScenario[Scenario] sort by DimScenario[ScenarioSort]
- FactBridge[BridgeStep] sort by FactBridge[BridgeOrder]

## Modeling Notes

- Keep relationships single direction to avoid accidental many-to-many filter behavior.
- Do not relate DimProduct directly to DimBusinessUnit; FactFinancials already carries both keys.
- CashBalance is a balance metric. Use `Cash Balance Latest Month`, not raw sum across time.
- Department Opex is intentionally separated from customer/product P&L grain.
