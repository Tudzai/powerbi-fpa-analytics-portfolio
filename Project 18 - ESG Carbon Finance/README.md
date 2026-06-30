# Project 18 - ESG Carbon Finance

Executive-ready portfolio BI build connecting emissions, carbon cost exposure, supplier intensity, abatement ROI, and risk/action governance.

## Current Build Status

- Data/model/report source package: ready.
- Supplemental HTML preview: `output/dashboard_preview.html`.
- Final PBIX target: `output/dashboard_final.pbix`.
- Final PBIX status: v39 dynamic table-card release passed Power BI Desktop QA on 2026-06-30.
- Final PBIX SHA256: `DDD78E1286BEB961AD744839C2356E8FB7D2AD20F187D68F9083AA6D964D3C0D`.
- Release evidence: `qa/project18_visual_product_qa.md`, `qa/dynamic_table_cards_slicer_qa.json`, and `output/screenshots/project18_v39_dynamic_table_cards_full.png`.

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
