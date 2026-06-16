# Handoff Notes

Final PBIX: `output/dashboard_final.pbix`
Build route: seed PBIX + TOM model replacement + native layout patch + Power BI Desktop QA.
Data: synthetic board/investor CFO demo data, seed `20260615`.
Model: 14 data tables, 16 relationships, 51 DAX measures.
Pages: Board Performance Overview; Financial Plan & Cash Runway; Valuation, Covenants & Risk Monitor.
Layout: ZoomCharts official-preview aligned left sidebar, visible Year/Scenario list slicers, compact BU/Region dropdowns, five taller layered KPI cards with large values, DAX/SVG-informed mini trend panels, colored markers, PY/YoY KPI footers, six rounded chart/table panels, no KPI chip bars, and no note boxes.
Template download note: the ZoomCharts PBIX download endpoint was tried but required account/credits; the public preview image was used as the template reference.
Source caveat: no production source data was provided; synthetic demo data is explicit and deterministic.
QA: data QA `pass`; final extract/aesthetic validation is `qa/pbix_v19_aesthetic_validation.json`; Desktop screenshot evidence is `qa/screenshots/pbi_v19_powerbi_capture.png`.
