# Handoff Notes

Project: Manufacturing Cost FP&A.
Main output target: `output/dashboard_final.pbix`.
Supplemental preview: `output/dashboard_final.html`.
Supplemental Power BI template package: `output/dashboard_project16_model_schema.pbit`.

PBIX build status: blocked for final PBIX persistence. The Project 16 model was pushed into the live Power BI Desktop session on port `56532`, and the 3-tab native layout was patched into the PBIX container. However, Desktop did not persist the new DataModel back into `output/dashboard_final.pbix`; offline `pbi-tools export-data` still returns the Packt seed tables (`Sales`, `Prices`, `Calendar`, `Products`, `Year`). Treat the PBIX file as a seed/container until this save blocker is cleared.

Latest-month snapshot:
- Revenue: $46.1M
- Actual COGS: $27.3M
- Cost variance vs standard: $1.7M
- Gross margin: $18.8M
- Gross margin %: 40.8%
- Yield: 96.8%
- Utilization: 61.3%
- Inventory value: $24.3M

Data is synthetic with seed `160416` and is suitable for portfolio/demo use, not production decisioning.

Validated non-PBIX artifacts:
- `data/prepared/*.csv`
- `model/MEASURES.dax`
- `build/native_report_layout_project16.json`
- `output/dashboard_final.html`
- `output/dashboard_project16_model_schema.pbit`
- `qa/live_pbixproj_from_session`
- `qa/live_export_after_model_push`
