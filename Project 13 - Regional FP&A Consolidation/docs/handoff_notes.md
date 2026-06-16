# Handoff Notes

- Main native Power BI dashboard: `output/dashboard_final.pbix`
- Portable dashboard backup: `output/dashboard_final.html`
- PBIX status: pass; built from finance seed template using TOM model push and native layout patch.
- Data source: synthetic portfolio/demo data with seed `13042`.
- Latest complete period: `2026-05`.
- Pages: Executive Summary, P&L Variance, Controls & Storyboard.
- QA: data QA pass; bridge tie-out pass; HTML QA pass at 2026-06-14T19:42:21.318Z; PBIX QA pass via PowerBIPackager.Validate, Desktop open-check, per-tab rendering-error text scan, pbi-tools extract, and pbi-tools export-data.
- PBIX seed template: `C:\Users\Win\OneDrive\Codex\Portfolio\BI\Template\01_Core_Financial_Statements\Packt_Ch07_Group_Reporting.pbix`
- Rebuild command: `python tools/build_project13.py`; `python tools/build_native_pbix_assets.py`; run `powerbi\prepare_seed_pbix.ps1`, open/save seed after TOM push, then run `powerbi\apply_native_layout_to_pbix.ps1`.
