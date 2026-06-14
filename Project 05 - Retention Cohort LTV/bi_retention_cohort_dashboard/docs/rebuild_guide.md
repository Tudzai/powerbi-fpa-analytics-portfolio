# Rebuild Guide

Run the project from the project root:

```powershell
python build/scripts/01_build_project.py
powershell -ExecutionPolicy Bypass -File build/scripts/00_environment_check.ps1
python build/scripts/03_validate_prepared_data.py
python build/scripts/05_validate_output.py
```

To complete the Power BI final, open the PBIP source package in Desktop, refresh, verify visuals and interactions, then save as `output/dashboard_final.pbix`.
