# Handoff Notes

Final PBIX: `output/dashboard_final.pbix`
Build route: seed PBIX + TOM model replacement + native layout patch + Power BI Desktop QA.
Data: synthetic board/investor CFO demo data, seed `20260615`.
Model: 14 data tables, 16 relationships, 96 DAX measures.
Pages: Board Performance Overview; Financial Plan & Cash Runway; Valuation, Covenants & Risk Monitor.
Layout: ZoomCharts official-preview aligned left sidebar, compact dropdown slicers, four focused layered KPI cards per page with latest-month native numeric KPI measures, compact mini trend panels with target band and markers, PY/YoY KPI footers, six rounded chart/table panels, no KPI chip bars, and no note boxes.
Template download note: the ZoomCharts PBIX download endpoint was tried but required account/credits; the public preview image was used as the template reference.
Source caveat: no production source data was provided; synthetic demo data is explicit and deterministic.
QA: data QA `pass`; final extract/aesthetic validation is `qa/pbix_v24_aesthetic_validation.json`; Playwright KPI/card crop evidence is `qa/playwright_project20_v24_kpi_check.json`; Desktop render evidence is `qa/screenshots/powerbi_desktop_v24_afterwait_capture.png`.
