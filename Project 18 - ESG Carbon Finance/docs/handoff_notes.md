# Handoff Notes

Final PBIX: `output/dashboard_final.pbix` delivered and opened in Power BI Desktop.

Dashboard purpose: connect emissions, supplier intensity, carbon price scenarios, and abatement ROI for ESG finance decisions.

Audience: CFO, ESG finance, procurement, and operations leaders.

Pages:
1. ESG Finance Overview
2. Emissions & Supplier Intensity
3. Carbon Scenario & Abatement ROI

Key KPIs:
- Total Emissions tCO2e
- Carbon Cost USD
- Emissions Intensity
- Supplier Intensity
- Abatement ROI
- MACC USD per tCO2e

Data source: synthetic demo CSVs generated with seed 180418.

Build route: `SCRIPTED_DESKTOP_PBIX`. The model was pushed through TOM, then the report layout was patched into the saved PBIX while preserving Power BI Desktop theme metadata.

Open-check: passed on Power BI Desktop PID 3736 / HWND 268138. Evidence screenshot: `output/screenshots/powerbi_desktop_static_opencheck_page1.png`.

Known issues: none blocking. The report pages use static native textbox/shape visuals for reliable Desktop rendering; the semantic model and DAX measures remain available in Data/Model view for exploration.
