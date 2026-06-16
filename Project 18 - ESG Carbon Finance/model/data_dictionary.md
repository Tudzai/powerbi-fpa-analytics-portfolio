# Data Dictionary

All data in this portfolio build is synthetic demo data generated with seed 180418.

## dim_date.csv
- Row count: 29
- Grain: Dimension table.
- Columns:
  - `date_key`
  - `month_start`
  - `year`
  - `quarter`
  - `month_no`
  - `month_name`
  - `fiscal_year`
  - `month_index`

## dim_business_unit.csv
- Row count: 5
- Grain: Dimension table.
- Columns:
  - `business_unit_id`
  - `business_unit`
  - `portfolio`
  - `annual_revenue_usd`

## dim_facility.csv
- Row count: 8
- Grain: Dimension table.
- Columns:
  - `facility_id`
  - `facility`
  - `country`
  - `region`
  - `default_business_unit`
  - `latitude`
  - `longitude`

## dim_activity.csv
- Row count: 9
- Grain: Dimension table.
- Columns:
  - `activity_id`
  - `activity`
  - `scope`
  - `ghg_category`
  - `activity_unit`
  - `base_emission_factor`

## dim_supplier.csv
- Row count: 24
- Grain: Dimension table.
- Columns:
  - `supplier_id`
  - `supplier`
  - `supplier_category`
  - `supplier_country`
  - `carbon_risk_tier`
  - `target_status`
  - `data_quality_score`

## dim_carbon_scenario.csv
- Row count: 3
- Grain: Dimension table.
- Columns:
  - `scenario_id`
  - `scenario`
  - `carbon_price_usd_per_t`
  - `probability_weight`

## fact_emissions.csv
- Row count: 1189
- Grain: Monthly emission activity record.
- Columns:
  - `emission_record_id`
  - `date_key`
  - `business_unit_id`
  - `facility_id`
  - `supplier_id`
  - `activity_id`
  - `scope`
  - `ghg_category`
  - `activity_volume`
  - `activity_unit`
  - `emission_factor`
  - `emissions_tco2e`
  - `spend_usd`
  - `revenue_usd`
  - `data_quality_score`

## fact_supplier_month.csv
- Row count: 535
- Grain: Monthly supplier summary.
- Columns:
  - `date_key`
  - `supplier_id`
  - `supplier`
  - `supplier_category`
  - `carbon_risk_tier`
  - `supplier_country`
  - `target_status`
  - `emissions_tco2e`
  - `spend_usd`
  - `supplier_intensity_tco2e_per_musd`
  - `data_quality_score`

## fact_carbon_exposure.csv
- Row count: 87
- Grain: Monthly emissions by carbon price scenario.
- Columns:
  - `date_key`
  - `scenario_id`
  - `scenario`
  - `carbon_price_usd_per_t`
  - `emissions_tco2e`
  - `carbon_cost_usd`
  - `probability_weighted_cost_usd`

## fact_abatement_initiatives.csv
- Row count: 12
- Grain: One row per abatement initiative.
- Columns:
  - `initiative_id`
  - `initiative`
  - `scope`
  - `business_unit`
  - `implementation_status`
  - `start_year`
  - `capex_usd`
  - `annual_reduction_tco2e`
  - `annual_opex_savings_usd`
  - `avoided_carbon_cost_usd_at_90`
  - `net_annual_benefit_usd_at_90`
  - `payback_years_at_90`
  - `roi_at_90`
  - `macc_usd_per_tco2e`

## powerbi_flat_emissions.csv
- Row count: 1189
- Grain: Dimension table.
- Columns:
  - `emission_record_id`
  - `date_key`
  - `business_unit_id`
  - `facility_id`
  - `supplier_id`
  - `activity_id`
  - `scope`
  - `ghg_category`
  - `activity_volume`
  - `activity_unit`
  - `emission_factor`
  - `emissions_tco2e`
  - `spend_usd`
  - `revenue_usd`
  - `data_quality_score`
  - `month_start`
  - `year`
  - `quarter`
  - `month_name`
  - `business_unit`
  - `portfolio`
  - `facility`
  - `country`
  - `region`
  - `activity`
  - `supplier`
  - `supplier_category`
  - `carbon_risk_tier`
  - `target_status`
