# Relationship Map

Recommended Power BI model is a star schema.

## Relationships

- dim_date[date_key] 1:* fact_emissions[date_key]
- dim_date[date_key] 1:* fact_supplier_month[date_key]
- dim_date[date_key] 1:* fact_carbon_exposure[date_key]
- dim_business_unit[business_unit_id] 1:* fact_emissions[business_unit_id]
- dim_facility[facility_id] 1:* fact_emissions[facility_id]
- dim_activity[activity_id] 1:* fact_emissions[activity_id]
- dim_supplier[supplier_id] 1:* fact_emissions[supplier_id]
- dim_supplier[supplier_id] 1:* fact_supplier_month[supplier_id]
- dim_carbon_scenario[scenario_id] 1:* fact_carbon_exposure[scenario_id]

## Filter Direction

Single direction from dimensions to facts. No many-to-many relationships are required.
