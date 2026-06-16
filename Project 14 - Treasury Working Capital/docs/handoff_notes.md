# Handoff Notes

Final output: `output/dashboard_final.pbix`
Supplemental preview: `output/dashboard_final.html`
Status: pass
Checked: 2026-06-15 03:51:54 +07:00

Build route: scripted Desktop PBIX using Ch07 Group Reporting as the technical seed, TOM model replacement, and native `/Report/Layout` patching.

Tabs:
1. Treasury Command Center
2. Working Capital Control
3. Forecast, FX & Risk

Model:
- 18 tables
- 17 relationships
- 30 DAX measures
- Synthetic portfolio/demo treasury data, seed 14042

QA evidence:
- `qa/pbix_validation.json`
- `qa/pbix_final_validation.json`
- `qa/pbix_native_report_validation.json`
- `qa/export_data_final`
- `qa/pbix_extract_final`
- `qa/html_validation.json`
- `output/screenshots/pbix_final_desktop_verified.png`
