# QA Checklist

- Data QA: pass
- Metric QA: pass; measures cataloged in `model/measure_catalog.json`.
- Visual QA: pass; final PBIX opened in Power BI Desktop after layout repair with no render error dialog and no remaining "Visuals are loading" state.
- HTML preview screenshot QA: pass; desktop and mobile screenshots saved under `output/screenshots/` with no console errors, overflow, NaN, or undefined text.
- Interaction QA: pass at file/page level; 3 native report tabs exist with visible slicers and native visuals. Deep cross-filter behavior is documented as manual follow-up if published to Power BI Service.
- File QA: pass; `output/dashboard_final.pbix` exists, package validation passed, exact final path opened in Desktop, and final was saved from Desktop.
