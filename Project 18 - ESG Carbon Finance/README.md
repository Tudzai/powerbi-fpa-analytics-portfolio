# Project 18 - ESG Carbon Finance

Executive-ready portfolio BI build connecting emissions, carbon cost exposure, supplier intensity, abatement ROI, and risk/action governance.

## Current Build Status

- Data/model/report source package: ready.
- Supplemental HTML preview: `output/dashboard_preview.html`.
- Final PBIX target: `output/dashboard_final.pbix`.
- Final PBIX status: v3 source/layout package refreshed; run fresh Power BI Desktop open-check after PBIX patch.

## Dashboard Pages

1. ESG Finance Overview
2. Emissions & Supplier Intensity
3. Carbon Scenario & Abatement ROI
4. Risk & Action Control Tower

## Rebuild

```powershell
python build/scripts/build_project18_assets.py
python build/scripts/build_powerbi_native_assets.py
powershell -NoProfile -ExecutionPolicy Bypass -File build/scripts/03_apply_native_layout_to_pbix.ps1
```

See `docs/rebuild_guide.md`, `docs/handoff_notes.md`, and `powerbi/notes/pbix_build_runbook.md`.
