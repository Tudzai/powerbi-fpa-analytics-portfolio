# Data Quality Report

Data mode: synthetic demo data.
Seed: 180418
Date range: Jan 2024 to May 2026.

## Row Counts

- dim_date.csv: 29
- dim_business_unit.csv: 5
- dim_facility.csv: 8
- dim_activity.csv: 9
- dim_supplier.csv: 24
- dim_carbon_scenario.csv: 3
- fact_emissions.csv: 1,189
- fact_supplier_month.csv: 535
- fact_carbon_exposure.csv: 87
- fact_abatement_initiatives.csv: 12
- powerbi_flat_emissions.csv: 1,189

## Key Checks

- Critical key nulls in fact_emissions: 0
- Duplicate date keys: 0
- Duplicate supplier keys: 0
- Duplicate emission record IDs: 0

## KPI Reconciliation

- Total emissions: 719,452.61 tCO2e
- Scope 1: 260,249.32 tCO2e
- Scope 2: 87,642.71 tCO2e
- Scope 3: 371,560.58 tCO2e
- Base carbon cost at $50/t: 35,972,630 USD
- Latest month YoY emissions change: -12.8%

Status: pass for portfolio/demo use.
