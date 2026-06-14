# Neobank Growth, Retention & LTV Dashboard

Final target: `output/dashboard_final.pbix`
Build package: `output/Project11_Neobank_BI_BuildPackage.zip`

Tabs:
- Growth Overview
- Funnel & Cohort Retention
- LTV, Churn & Marketing ROI

Latest month: May 2026
New users: 10,443
Active users: 19,928
Funded accounts: 2,024
Deposits: $12.4M
Revenue: $200.9K
CAC: $327
LTV/CAC: 0.4x

## QA Status

- Data QA: PASS (`data/validated/validation_summary.json`)
- Desktop QA: PASS, opened exact `dashboard_final.pbix` in Power BI Desktop and checked all 3 pages.
- PBIX extract: PASS (`qa/pbix_extract_final_project11`)
- PBIX export-data: PASS (`qa/export_data_final`)
- Final validation: PASS (`qa/pbix_final_validation.json`)

## Rebuild

Run `python build/scripts/01_build_project.py` to regenerate data/model/layout assets.
Run `build/scripts/02_push_model_bim_via_tom.ps1` against the seed PBIX, then `build/scripts/03_apply_native_layout_to_pbix.ps1` to recreate `output/dashboard_final.pbix`.
