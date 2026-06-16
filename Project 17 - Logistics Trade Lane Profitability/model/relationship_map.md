# Relationship Map

| From | Column | To | Column | Cardinality | Filter |
|---|---|---|---|---|---|
| FactShipmentProfitability | date_id | DimDate | date_id | Many-to-one | Single |
| FactCostDriverBridge | date_id | DimDate | date_id | Many-to-one | Single |
| FactActionQueue | date_id | DimDate | date_id | Many-to-one | Single |
| FactShipmentProfitability | customer_id | DimCustomer | customer_id | Many-to-one | Single |
| FactCostDriverBridge | customer_id | DimCustomer | customer_id | Many-to-one | Single |
| FactActionQueue | customer_id | DimCustomer | customer_id | Many-to-one | Single |
| FactShipmentProfitability | lane_id | DimTradeLane | lane_id | Many-to-one | Single |
| FactCostDriverBridge | lane_id | DimTradeLane | lane_id | Many-to-one | Single |
| FactActionQueue | lane_id | DimTradeLane | lane_id | Many-to-one | Single |
| FactShipmentProfitability | service_id | DimService | service_id | Many-to-one | Single |
| FactShipmentProfitability | office_id | DimOffice | office_id | Many-to-one | Single |
| FactActionQueue | office_id | DimOffice | office_id | Many-to-one | Single |
| FactShipmentProfitability | carrier_id | DimCarrier | carrier_id | Many-to-one | Single |
