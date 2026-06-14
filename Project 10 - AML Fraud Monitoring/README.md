# AML / Fraud Monitoring Command Center

This project is a complete BI portfolio package for AML and fraud monitoring.

Open quick preview:

- `output/dashboard.html`

Main Power BI target:

- `output/dashboard_final.pbix`

Validated Power BI final:

- `output/dashboard_final.pbix` opens in Power BI Desktop.
- Offline `pbi-tools export-data` and `pbi-tools extract` passed.
- Validation details are in `qa/final_pbix_validation.json`.
- The final PBIX has a dark AML command-center aesthetic refresh documented in `docs/aesthetic_redesign_brief.md`.

Build package:

- `data/prepared/*.csv`
- `model/measures.dax`
- `build/config/*.json`
- `build/native_report_layout_aml.json`
- `build/legacy_report_layout_aml.json`
- `output/open_dashboard_powerbi.pbip`

The data is deterministic synthetic demo data generated with seed 20260611.
