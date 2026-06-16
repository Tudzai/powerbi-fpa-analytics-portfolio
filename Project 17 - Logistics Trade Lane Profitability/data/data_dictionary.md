# Model Data Dictionary

| Table | Grain | Purpose |
|---|---|---|
| DimDate | Month | Time slicing and trend axis |
| DimCustomer | Customer | Customer, segment, industry, account manager |
| DimTradeLane | Origin-destination lane | Lane, mode, cluster, strategic lane |
| DimService | Service | Ocean/Air/Road/Brokerage service family |
| DimOffice | Office | Operating office and region |
| DimCarrier | Carrier | Carrier/vendor segmentation |
| FactShipmentProfitability | Month x customer x lane x service x office x carrier | Revenue, cost, margin, volume, service KPIs |
| FactCostDriverBridge | Month x customer x lane x driver | Margin gap driver bridge versus target |
| FactActionQueue | Action item | Margin recovery actions and owner queue |
