# Relationship Map

| From | Column | To | Column | Cardinality | Filter |
|---|---|---|---|---|---|
| FactCampaignDaily | date | DimDate | date | Many-to-one | Single |
| FactCampaignDaily | month_key | DimMonth | month_key | Many-to-one | Single |
| FactCampaignDaily | channel_key | DimChannel | channel_key | Many-to-one | Single |
| FactCampaignDaily | campaign_key | DimCampaign | campaign_key | Many-to-one | Single |

Mark DimDate as the date table. Hide technical keys where possible.
