# Project 02 - Driver-Based Forecasting & Scenario Planning

## Objective

Build a Power BI planning product that helps FP&A and business leaders compare Base, Upside and Downside scenarios, test key drivers, review forecast P&L, understand cash impact and monitor forecast accuracy.

## Status

- Final PBIX is complete: `output/dashboard_final.pbix`.
- The PBIX was opened, refreshed, saved in Power BI Desktop, and extract-verified with 5 report pages, 23 measures and 32 relationships.
- Source build project: `build/pbixproj/Project2_Forecasting`; template: `output/Project2_Driver_Forecasting_Template_v2.pbit`.

## Core Dataset

- Raw source: `data/raw/driver_forecasting_raw.xlsx`
- Prepared data: `data/prepared/*.csv`
- Actual period: Jan 2024 to May 2026
- Forecast period: Jun 2026 to Dec 2027
- Scenarios: Actual, Base, Upside, Downside

## Key Portfolio Signals

- Historical actual revenue: $314.6M
- Base forecast revenue: $273.3M
- Upside forecast revenue: $322.8M
- Downside forecast revenue: $226.9M
- Base direct cost: $219.6M
- Base ending cash at forecast horizon: $21.9M
- Historical forecast MAPE: 6.4%

## Build Order

1. Run `python build/scripts/00_generate_synthetic_raw.py`.
2. Run `python build/scripts/01_profile_data.py`.
3. Run `python build/scripts/02_prepare_data.py`.
4. Run `python build/scripts/03_validate_prepared_data.py`.
5. Run `python build/scripts/04_generate_powerbi_artifacts.py`.
6. Run `python build/scripts/07_build_powerbi_pbixproj.py`.
7. Compile the PbixProj to PBIT with `pbi-tools.core`, open it in Power BI Desktop, refresh and save as `output/dashboard_final.pbix`.
8. Extract-verify the saved PBIX before handoff.
