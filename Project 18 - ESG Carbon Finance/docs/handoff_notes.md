# Handoff Notes

Final PBIX: `output/dashboard_final.pbix`.

v3 status: source/model/layout package refreshed and patched into the final PBIX. Power BI Desktop open-check passed on 2026-06-23 22:39 +07:00 with 0 visual error-string hits.

Final PBIX SHA256: `644011EB707D39FD8A9F13B8E4BCE32156E45E943AD3A7F69F4FDE1565A95923`.

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
- `output/screenshots/desktop_qa_contact_sheet.png`
- `output/screenshots/desktop_page1_overview.png` through `desktop_page4_risk.png`

Known issue: none after the 2026-06-23 Desktop QA pass.
