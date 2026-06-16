# Project 18 - ESG Carbon Finance

Executive-ready portfolio BI build connecting emissions, carbon cost exposure, supplier intensity, and abatement ROI.

## Current Build Status

- Data/model/report source package: ready.
- Supplemental HTML preview: `output/dashboard_preview.html`.
- Final PBIX target: `output/dashboard_final.pbix`.
- Final PBIX status: delivered and opened in Power BI Desktop.
- Build route: `SCRIPTED_DESKTOP_PBIX` with TOM model push, native static report layout, and preserved Desktop theme metadata.

## Dashboard Pages

1. ESG Finance Overview
2. Emissions & Supplier Intensity
3. Carbon Scenario & Abatement ROI

## Rebuild

```powershell
python build/scripts/build_project18_assets.py
python build/scripts/build_powerbi_native_assets.py
powershell -NoProfile -ExecutionPolicy Bypass -File build/scripts/03_apply_native_layout_to_pbix.ps1
```

See `docs/rebuild_guide.md`, `docs/handoff_notes.md`, and `powerbi/notes/pbix_build_runbook.md`.
