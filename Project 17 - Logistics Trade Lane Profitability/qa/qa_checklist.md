# QA Checklist

- Data QA: pass.
- Metric QA: pass; measures cataloged in model/measure_catalog.json.
- Package QA: pass; PowerBIPackager.Validate passed for output/dashboard_v01.pbix and output/dashboard_final.pbix after the 2026-06-23 21:30 slicer-polish patch.
- Layout QA: pass; embedded /Report/Layout in output/dashboard_final.pbix matches uild/native_report_layout_project17.json with SHA-256 d0fb927fabed6c30138e18547ca9def2641c1fa9807f673017152b0e8c618c13.
- Slicer QA: pass at file level; all 9 top-row slicers are at y=82, height 56, and have hidden visual-container titles so only the slicer header renders.
- Project 20-style QA: pass at file level; each page has 1 Current Lens, 1 Decision Chip, and 6 KPI sparkline micro-trends.
- Field reference QA: pass; 112 visual prototype refs checked, 0 missing refs against model/model.bim.
- Desktop render QA: earlier final build opened in Power BI Desktop with no visual error; latest final-file Desktop screenshot was not completed after the 21:30 patch. Live Desktop recheck after the latest slicer-polish patch was attempted with Computer Use and pbi-tools. Power BI Desktop exposed open windows named dashboard_model_seed and dashboard_final, but pbi-tools info showed the open dashboard_final session belonged to Project 18 and the seed session was not Project 17 final. No final-file Project 17 Desktop screenshot was accepted as evidence.
