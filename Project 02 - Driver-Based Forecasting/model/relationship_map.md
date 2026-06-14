# Relationship Map

Use a star schema. Keep all filters single-direction from dimensions to facts.

| From Table | From Column | To Table | To Column | Cardinality | Cross Filter |
|---|---|---|---|---|---|
| DimDate | DateKey | FactRevenueDriver | DateKey | 1:* | Single |
| DimDate | DateKey | FactCostDriver | DateKey | 1:* | Single |
| DimDate | DateKey | FactHeadcountPlan | DateKey | 1:* | Single |
| DimDate | DateKey | FactOpexDriver | DateKey | 1:* | Single |
| DimDate | DateKey | FactCashImpact | DateKey | 1:* | Single |
| DimDate | DateKey | FactForecastAccuracy | DateKey | 1:* | Single |
| DimScenario | ScenarioKey | FactRevenueDriver | ScenarioKey | 1:* | Single |
| DimScenario | ScenarioKey | FactCostDriver | ScenarioKey | 1:* | Single |
| DimScenario | ScenarioKey | FactHeadcountPlan | ScenarioKey | 1:* | Single |
| DimScenario | ScenarioKey | FactOpexDriver | ScenarioKey | 1:* | Single |
| DimScenario | ScenarioKey | FactCashImpact | ScenarioKey | 1:* | Single |
| DimRegion | RegionKey | FactRevenueDriver | RegionKey | 1:* | Single |
| DimRegion | RegionKey | FactCostDriver | RegionKey | 1:* | Single |
| DimRegion | RegionKey | FactHeadcountPlan | RegionKey | 1:* | Single |
| DimRegion | RegionKey | FactOpexDriver | RegionKey | 1:* | Single |
| DimService | ServiceKey | FactRevenueDriver | ServiceKey | 1:* | Single |
| DimService | ServiceKey | FactCostDriver | ServiceKey | 1:* | Single |
| DimService | ServiceKey | FactForecastAccuracy | ServiceKey | 1:* | Single |
| DimCustomerSegment | SegmentKey | FactRevenueDriver | SegmentKey | 1:* | Single |
| DimCustomerSegment | SegmentKey | FactCostDriver | SegmentKey | 1:* | Single |
| DimDepartment | DepartmentKey | FactHeadcountPlan | DepartmentKey | 1:* | Single |
| DimDepartment | DepartmentKey | FactOpexDriver | DepartmentKey | 1:* | Single |

## Notes

- Do not create fact-to-fact relationships. Measures reconcile by shared conformed dimensions.
- `FactCostDriver[RevenueDriverKey]` is retained for audit only; keep it hidden in report view.
- `what_if_parameters` is disconnected and used as an assumptions reference table. For interactive sliders, create Power BI numeric parameters and connect them to adjusted measures.