# PBIX Build Status

Status: BLOCKED_PBIX_PERSISTENCE

`output/dashboard_final.pbix` exists as a patched seed/container and now embeds the upgraded Project 20-style report layout. It is still not a fully validated final PBIX because the offline PBIX DataModel persistence remains blocked until a clean Power BI Desktop save/reopen path writes the Project 16 model into the package.

2026-06-23 latest layout update:
- Top filter bar remains on every page with slicers at `y=72`, `296x52` slots.
- KPI row was upgraded to four larger focused cards per page at `296x94`.
- Each KPI card now has a native mini line-chart sparkline layered inside the card.
- Main trend panels use native line charts instead of column charts.
- Tables now include header fill, row banding, row padding, column widths, and measure alignment.
- Direct layout, embedded PBIX layout, and embedded PBIT layout verification passed in `qa/project20_full_upgrade_verification.json`.

Current embedded report layout evidence:
- Pages: 3.
- Visual containers: 51.
- Visual types: 3 textboxes, 12 slicers, 12 cardVisuals, 14 lineCharts, 6 barCharts, 3 tableEx visuals, 1 waterfallChart.

Persistence blocker that remains:
- The offline `output/dashboard_final.pbix` DataModel still needs a Desktop save/reopen path that persists Project 16 tables and measures.
- Existing `qa/pbix_final_validation.json` is still `PENDING_DESKTOP`.

Validation evidence:
- Upgraded layout verification: `qa/project20_full_upgrade_verification.json`.
- Native layout summary: `build/native_report_layout_project16_summary.json`.
- Live Desktop export after previous model push: `qa/live_export_after_model_push` contains Project 16 tables.
- Live model extract: `qa/live_pbixproj_from_session/Model/database.json` contains Project 16 tables, relationships, and measures.
- Offline `output/dashboard_final.pbix` export after prior Save attempt still showed seed tables (`Calendar`, `Prices`, `Products`, `Sales`, `Year`).
- Supplemental PBIT schema package: `output/dashboard_project16_model_schema.pbit` extract-validates with the Project 16 model and now embeds the same 51-visual upgraded report layout.

Next retry path:
1. Open a clean Power BI Desktop workspace with unrelated Power BI sessions closed.
2. Open `output/dashboard_project16_model_schema.pbit`.
3. Refresh/apply local CSV sources from `data/prepared`.
4. Save As `output/dashboard_final.pbix`.
5. Validate with `pbi-tools export-data -pbixPath output/dashboard_final.pbix`.
