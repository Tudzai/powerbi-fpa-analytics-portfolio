# Handoff Notes

Final PBIX: `output/dashboard_final.pbix`.

v39 status: source/model/layout package refreshed, patched into the final PBIX, saved in Power BI Desktop, and validated with full-canvas screenshot evidence on 2026-06-30 19:02 +07:00.

Final PBIX SHA256: `DDD78E1286BEB961AD744839C2356E8FB7D2AD20F187D68F9083AA6D964D3C0D`.

Dashboard purpose: connect emissions, supplier intensity, carbon price scenarios, abatement ROI, and risk/action governance for ESG finance decisions.

Audience: CFO, ESG finance, procurement, and operations leaders.

Canvas standard: upgraded toward the Project 20 pattern with native dropdown slicers, native KPI cards/charts/tables, widened filter labels, chart/table polish, and compact KPI sparkline callouts.

Pages:
1. ESG Finance Overview
2. Emissions & Supplier Intensity
3. Carbon Scenario & Abatement ROI
4. Risk & Action Control Tower

Key KPIs:
- Total Emissions tCO2e
- Carbon Cost USD
- Emissions Intensity
- Supplier Intensity
- High Risk Supplier Emissions
- Average Data Quality Score
- Abatement ROI
- MACC USD per tCO2e
- Planned Abatement Capex USD

Data source: synthetic demo CSVs generated with seed 180418.

Desktop QA evidence:
- `qa/desktop_open_check.json`
- `qa/pbix_final_validation.json`
- `qa/dynamic_table_cards_slicer_qa.json`
- `output/screenshots/project18_v39_dynamic_table_cards_full.png`
- `output/screenshots/project18_v39_dynamic_table_cards_canvas_crop.png`
- `output/screenshots/project18_v39_dynamic_table_cards_bottom_crop.png`

Known issue: none after the 2026-06-30 v39 dynamic table-card QA pass.
