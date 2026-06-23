# Project 19 - Finance Data Quality BI Governance

Portfolio Power BI governance monitor for finance data quality, refresh reliability, reconciliation, report usage, and access controls.

## Current Build

- Final PBIX: `output/dashboard_final.pbix`
- Versioned PBIX snapshot: `output/dashboard_final_v5_project20_sparklines.pbix`
- HTML QA preview: `output/dashboard_final.html`
- Power BI source package: `output/powerbi_project/Finance_Data_Quality_BI_Governance.pbip`
- Status: final PBIX Desktop verified.
- Enhancement version: `v5_20260623_project20_sparklines`

## Pages

1. Governance Overview
2. Reliability & Quality
3. Adoption & Controls
4. Risk & Action Queue

## Verification

- Final PBIX opened in Power BI Desktop as `dashboard_final` and was saved at 10:24 PM on 2026-06-23.
- Package audit: 117 native visual definitions, 16 KPI cards, 16 native KPI sparklines, 8 dropdown slicers, DataModel present.
- Desktop screenshots and slicer interaction evidence are under `output/screenshots`.

## Rebuild

Use Python with `pandas` and `numpy`. Verified local command:

```powershell
& "C:\Users\Win\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" build\scripts\build_project19.py
```

Portable command:

```powershell
python build\scripts\build_project19.py
```
