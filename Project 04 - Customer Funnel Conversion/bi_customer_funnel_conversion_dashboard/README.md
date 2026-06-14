# Project 04 - Customer Funnel Conversion

This folder contains a complete BI build package for a customer funnel dashboard:

Visit -> Product View -> Add to Cart -> Checkout -> Purchase.

Breakdowns: device, channel, campaign, category.

## Key Files

- `data/prepared/` - star-schema CSVs.
- `model/metric_definitions.md` - KPI definitions.
- `model/dax_measures.md` - Power BI measures.
- `build/config/page_map.json` and `build/config/visual_map.json` - dashboard design.
- `output/dashboard.html` - completed interactive dashboard.
- `output/dashboard_final.pbix` - final native Power BI file.
- `output/dashboard_payload_complete.json` - aggregate cube powering dashboard-wide filters.
- `output/screenshots/page_p1_complete.png` to `page_p5_complete.png` - verified page screenshots.
- `qa/complete_dashboard_qa.json` - final HTML dashboard QA evidence.
- `qa/pbix_file_validation.json` - final PBIX file validation evidence.
- `qa/reconciliation.xlsx` - KPI reconciliation.
- `_agent/environment_check.md` - tool environment evidence.
- `powerbi/notes/pbix_build_runbook.md` - PBIX build steps.

## Rebuild

Run:

```powershell
$py = 'C:\Users\Win\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
& $py 'build\scripts\00_build_project4.py'
& $py 'build\scripts\11_render_complete_dashboard.py'
```

Current synthetic seed: `4042026`.

## Current Status

- Complete HTML dashboard: passed.
- Native PBIX: created at `output/dashboard_final.pbix` and offline export validated.
