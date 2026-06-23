# Rebuild Guide

Run from the project folder:

```powershell
python build/scripts/build_project18_assets.py
python build/scripts/build_powerbi_native_assets.py
powershell -NoProfile -ExecutionPolicy Bypass -File build/scripts/03_apply_native_layout_to_pbix.ps1
```

Then open Power BI Desktop and import the prepared CSVs from:

```text
C:\Users\Win\OneDrive\Codex\Portfolio\BI\Project 18 - ESG Carbon Finance\data\prepared
```

The scripted route regenerates data/docs, model/layout source, then patches the native layout into `output/dashboard_final.pbix`. If building manually, create relationships according to `model/relationship_map.md`, add measures from `model/MEASURES.dax`, apply `build/config/theme.json`, and build the four pages in `report/report_spec.md`.
