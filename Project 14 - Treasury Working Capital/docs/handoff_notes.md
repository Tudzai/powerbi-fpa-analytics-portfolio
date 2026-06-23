# Handoff Notes

- Main PBIX: `output/dashboard_final.pbix`
- Supplemental preview: `output/dashboard_final.html`
- Build route: scripted Desktop PBIX using TOM model push, native `/Report/Layout` patch, dynamic `tableEx` SVG KPI cards, and PowerBIPackager validation.
- Current PBIX status: final build validated on 2026-06-23 at 21:46:54 +07:00.
- Data source: synthetic portfolio/demo treasury data, seed 14042.
- Pages: Treasury Command Center; Working Capital Control; Forecast, FX & Risk.
- Model: 18 tables, 17 relationships, 47 measures, with KPI measures stored in `KPI_Measures`.
- Project 20 style upgrade: left rail, compact lens slicers, decision chips, dynamic SVG KPI cockpit row, diagnostic chart grid, and execution detail tables.
- KPI row implementation: 12 model-bound `tableEx` ImageUrl SVG KPI cards, 4 per page, with sparkline bands/markers and PY/delta footer logic.
- QA evidence: `qa/project20_upgrade_verification.json`, `qa/pbix_native_report_validation.json`, `qa/pbix_final_validation.json`, `qa/project20_upgrade_qa.md`, and `output/screenshots/pbix_project20_upgrade_dynamic_svg_v21.png`.
