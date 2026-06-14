# E-commerce Executive Performance Dashboard

This is a portfolio BI project generated from the BI A-Z master prompt v2.

The dashboard is designed for ecommerce executives who need a fast read on business performance: GMV, net revenue, orders, AOV, conversion rate, refund/cancel rate, top category, and traffic channel performance.

## Current Status

- Data package: ready.
- Semantic model spec: ready.
- DAX measures: ready.
- Dashboard preview: ready.
- PBIX authoring mode: `COMPUTER_USE_PLUS_SCRIPTED_DESKTOP_PBIX`.
- Power BI final PBIX: ready at `output/dashboard_final.pbix`.
- Power BI Desktop screenshot evidence: `output/screenshots/powerbi_desktop_dashboard_final.png`.

The final PBIX was created from the project model, package-validated, reopened in Power BI Desktop, and screenshot-verified.

## KPI Snapshot

| KPI | Value |
|---|---:|
| GMV | $52,427,077 |
| Net Revenue | $45,636,440 |
| Orders | 128,271 |
| AOV | $408.72 |
| Conversion Rate | 3.30% |
| Refund/Cancel Rate | 7.89% |
| Top Category | Electronics |
| Top Traffic Channel | Organic Search |

## Key Folders

- `data/raw/`: generated synthetic source files.
- `data/prepared/`: clean star schema CSV files for Power BI.
- `model/`: data dictionary, KPI definitions, DAX, relationship map.
- `build/config/`: page map, visual map, slicer map, theme.
- `powerbi/notes/`: build and desktop runbooks.
- `_agent/pbix_authoring_decision.md`: v2 authoring strategy decision.
- `_agent/scripted_desktop_pbix_check.md`: scripted desktop PBIX route evidence.
- `output/`: preview HTML, screenshots, and export PDF.
- `qa/`: QA checklist, validation JSON, reconciliation workbook.
- `docs/`: handoff, refresh, rebuild, changelog, issue log.

## Rebuild

```powershell
& "C:\Users\Win\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" .\build\scripts\00_create_project_structure.py
```

## PBIX

Open `output/dashboard_final.pbix` in Power BI Desktop for the finished portfolio dashboard. Supporting validation is in `qa/pbix_validation.json`, `qa/pbix_native_report_validation.json`, and `qa/scripted_desktop_pbix_check.json`.
