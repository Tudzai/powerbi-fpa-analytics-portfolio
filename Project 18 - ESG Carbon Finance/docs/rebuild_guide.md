# Rebuild Guide

Run from the project folder:

```powershell
python build/scripts/build_project18_assets.py
python build/scripts/build_powerbi_native_assets.py
powershell -NoProfile -ExecutionPolicy Bypass -File build/scripts/03_apply_native_layout_to_pbix.ps1
python build/scripts/04_validate_output.py
```

The delivered PBIX route uses the saved Desktop seed at `output/dashboard_model_seed.pbix`, preserves its theme metadata, and patches the generated 3-page static native layout into `output/dashboard_final.pbix`.

Manual authoring references remain available in `model/relationship_map.md`, `model/MEASURES.dax`, `build/config/theme.json`, and `report/report_spec.md`.
