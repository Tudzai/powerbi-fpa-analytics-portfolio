# QA Checklist

Status: pass
Checked: 2026-06-15 03:51:54 +07:00

| Area | Status | Evidence |
|---|---|---|
| Data validation | pass | data/validated/validation_summary.json |
| HTML dashboard QA | pass | qa/html_validation.json; desktop and mobile viewport checks |
| PBIX package validation | pass | qa/pbix_native_report_validation.json |
| PBIX export-data | pass | qa/export_data_final contains all 18 model tables |
| PBIX extract | pass | qa/pbix_extract_final contains report and raw model |
| Power BI Desktop open-check | pass | output/screenshots/pbix_final_desktop_verified.png |
| Page count | pass | 3 tabs: Treasury Command Center, Working Capital Control, Forecast, FX & Risk |
| Visual surface | pass | 57 visuals: 18 cards, 12 bar charts, 2 column charts, 1 waterfall, 9 slicers, 9 textboxes, 6 shapes |
