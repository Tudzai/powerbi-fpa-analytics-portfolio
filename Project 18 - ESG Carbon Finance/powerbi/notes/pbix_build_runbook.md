# PBIX Build Runbook

Delivered route: `SCRIPTED_DESKTOP_PBIX`.

1. Generate data, docs, and validation artifacts:

```powershell
python build/scripts/build_project18_assets.py
```

2. Generate the static native report layout:

```powershell
python build/scripts/build_powerbi_native_assets.py
```

3. Patch the layout into the saved PBIX seed while preserving Desktop theme metadata:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File build/scripts/03_apply_native_layout_to_pbix.ps1
```

4. Validate output:

```powershell
python build/scripts/04_validate_output.py
```

Final file: `output/dashboard_final.pbix`.

Manual authoring references remain available in `model/relationship_map.md`, `model/MEASURES.dax`, `build/config/theme.json`, and `report/report_spec.md`.
