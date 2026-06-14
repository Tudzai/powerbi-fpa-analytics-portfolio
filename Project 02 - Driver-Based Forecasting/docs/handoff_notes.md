# Handoff Notes

## Output

- Required final BI file: `output/dashboard_final.pbix`
- Current status: complete. `output/dashboard_final.pbix` was saved in Power BI Desktop and verified by extracting the final PBIX.
- Prepared data: `data/prepared/`
- DAX measures: `powerbi/Project2_Measures.dax`
- Power Query snippets: `powerbi/PowerQuery_M.txt`
- Theme: `build/config/theme.json`
- Page and visual maps: `build/config/page_map.json`, `build/config/visual_map.json`
- Power BI source project: `build/pbixproj/Project2_Forecasting`
- PBIT template: `output/Project2_Driver_Forecasting_Template_v2.pbit`
- Power BI-style mockup: `output/exports/powerbi_dashboard_mockup.html`
- Mockup screenshots: `output/screenshots/powerbi_mockup/`

## Pages

1. Executive Planning Overview
2. Revenue & Cost Drivers
3. Headcount & Capacity Plan
4. Cash & Forecast Accuracy
5. Detail & Exceptions

## Refresh Instructions

1. Replace or regenerate `data/raw/driver_forecasting_raw.xlsx`.
2. Re-run profile, prepare and validate scripts.
3. Open PBIX and refresh all queries.
4. Check `qa/reconciliation.xlsx` and `qa/qa_checklist.md` before promoting to final.

## Known Issues

- No open PBIX build issue.
- What-if assumptions are available in `WhatIfParameters`; numeric Power BI slider parameters can be added later for deeper interactive sensitivity controls.
