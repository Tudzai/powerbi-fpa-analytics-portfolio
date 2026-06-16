# Rebuild Guide

Run from the project folder:

```powershell
cd "C:\Users\Win\OneDrive\Codex\Portfolio\BI\Project 14 - Treasury Working Capital"
python tools/build_project14.py
python tools/validate_dashboard.py
python tools/build_native_pbix_assets.py
```

Then run the Power BI scripts in order:

```powershell
powershell -ExecutionPolicy Bypass -File powerbi/prepare_seed_pbix.ps1
& "C:\Users\Win\AppData\Local\Programs\pbi-tools\current\pbi-tools.exe" launch-pbi output/dashboard_model_seed_ch07.pbix
powershell -ExecutionPolicy Bypass -File powerbi/push_model_bim_to_desktop.ps1
powershell -ExecutionPolicy Bypass -File powerbi/apply_native_layout_to_pbix.ps1
```
