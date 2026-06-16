# Data Dictionary

| Table | Grain | Rows | Description |
|---|---:|---:|---|
| dim_date | 1 row per month | 17 | Monthly calendar for working capital trend analysis. |
| dim_week | 1 row per forecast week | 13 | 13-week forecast calendar. |
| dim_entity | 1 row per entity | 6 | Legal entity, country, region, and functional currency. |
| dim_customer | 1 row per customer | 20 | Customer master with sector, entity, credit terms, and risk rating. |
| dim_vendor | 1 row per vendor | 16 | Vendor master with category, entity, terms, and criticality. |
| dim_bank | 1 row per bank | 6 | Bank counterparty dimension. |
| dim_scenario | 1 row per scenario | 3 | Forecast scenarios. |
| dim_cash_category | 1 row per category | 6 | Cash flow category classification. |
| fact_cash_position | snapshot_date x entity x bank | 18 | Latest bank cash position by entity, bank, and currency. |
| fact_liquidity_facility | facility x entity | 6 | Liquidity facilities and covenants by entity. |
| fact_working_capital | month x entity | 102 | Monthly revenue, COGS, AR, AP, inventory, and working capital days by entity. |
| fact_ar_invoice | 1 row per AR invoice | 1250 | Invoice-level AR aging and expected collection timing. |
| fact_ap_invoice | 1 row per AP invoice | 900 | Invoice-level AP due schedule and payment priority. |
| fact_cash_forecast | week x entity x scenario | 234 | 13-week direct cash forecast by entity and scenario. |
| fact_forecast_accuracy | historical week x entity | 48 | Historical weekly forecast accuracy by entity. |
| fact_fx_exposure | entity x exposure currency | 24 | FX receivable, payable, hedged, and unhedged exposure. |
| fact_treasury_risk_action | 1 row per action item | 75 | Treasury risks, action owners, status, value, and due date. |

All portfolio data is synthetic with fixed seed 14042. Currency values are USD equivalents unless the field name says local.
