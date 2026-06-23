# Project 13 - Regional FP&A Consolidation

Portfolio BI product for regional FP&A consolidation across countries, entities, currencies, scenarios, intercompany eliminations, and business units.

## Main Artifact

- Native Power BI dashboard: `output/dashboard_final.pbix`
- Portable dashboard backup: `output/dashboard_final.html`
- PBIX status: pass; built from a finance group-reporting PBIX seed, Project 13 model push, and native layout patch.
- Layout upgrade: slicers now sit in a top filter bar above the KPI strip on every native PBIX page.

## Business Questions

- Which countries and entities are driving revenue, EBITDA, and cash variance?
- How much variance comes from volume, price, mix, FX, intercompany eliminations, and OPEX discipline?
- Which markets need management attention before the regional close package is finalized?

## Dashboard Pages

1. Executive Summary
2. P&L Variance
3. Controls & Storyboard

## Data And Model

- Synthetic portfolio data, seed `13042`.
- Latest complete period `2026-05`.
- Star schema with Date, Entity, Business Unit, Account, Scenario, Financial Summary, Financial Detail, FX Rates, Variance Bridge, and Close Exceptions.
- Measures are documented in `model/MEASURES.dax` and `model/measure_catalog.json`.

## Rebuild

```powershell
python tools/build_project13.py
python tools/validate_dashboard.py
python tools/build_native_pbix_assets.py
```

Native PBIX build uses `powerbi/prepare_seed_pbix.ps1`, `powerbi/push_model_bim_to_desktop.ps1`, and `powerbi/apply_native_layout_to_pbix.ps1`.

## Latest Upgrade

- 2026-06-23: moved native slicers to the top filter bar, regenerated `build/native_report_layout_project13.json`, patched `output/dashboard_final.pbix`, and validated with Power BI Desktop screenshot evidence.
- Evidence: `qa/project20_upgrade_verification.json`, `qa/project20_upgrade_qa.md`, and `output/screenshots/powerbi_desktop_top_slicer_final_20260623.png`.
