# Relationship Map

| From Table | From Column | To Table | To Column | Cardinality | Filter |
|---|---|---|---|---|---|
| FactOrders | UserID | DimUser | UserID | Many-to-one | Single direction from dimension |
| FactOrders | OrderMonth | DimMonth | MonthStart | Many-to-one | Single direction from dimension |
| FactUserMonth | UserID | DimUser | UserID | Many-to-one | Single direction from dimension |
| FactUserMonth | MonthStart | DimMonth | MonthStart | Many-to-one | Single direction from dimension |
| MonthlyKPIs | MonthStart | DimMonth | MonthStart | Many-to-one | Single direction from dimension |
| MonthlyLifecycleMix | MonthStart | DimMonth | MonthStart | Many-to-one | Single direction from dimension |
| CohortRetention | ActivityMonth | DimMonth | MonthStart | Many-to-one | Single direction from dimension |
| ChurnRiskSnapshot | UserID | DimUser | UserID | Many-to-one | Single direction from dimension |
| SegmentMonthly | MonthStart | DimMonth | MonthStart | Many-to-one | Single direction from dimension |
