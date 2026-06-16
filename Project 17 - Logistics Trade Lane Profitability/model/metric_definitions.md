# Metric Definitions

Core profitability is measured at shipment profitability grain, then aggregated through DAX measures.

| Metric | Definition | Notes |
|---|---|---|
| Net Revenue | Sum of shipment revenue after credits/rebates | Excludes tax and pass-through only items |
| Gross Profit | Net Revenue less freight, fuel, handling, customs, demurrage, claims, and last-mile cost | Primary margin outcome |
| GP Margin % | Gross Profit / Net Revenue | Uses `DIVIDE`; never summed |
| Target Margin % | Weighted target margin by lane/service row | Used for margin gap and action queue |
| Reprice Opportunity | Value needed to bring negative-margin shipments back to zero GP | Conservative floor, not full target recovery |
| On-Time % | On-time shipment count / shipment count | Service guardrail |
| Utilization % | Average capacity/equipment utilization | Cost-to-serve guardrail |
