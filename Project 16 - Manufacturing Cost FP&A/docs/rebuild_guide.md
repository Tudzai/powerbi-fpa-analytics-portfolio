# Rebuild Guide

1. Run `python build/scripts/00_build_project16.py`.
2. Run `python build/scripts/10_apply_native_report_project16.py` to patch the seed layout into `output/dashboard_final.pbix`.
3. Launch with `powerbi/launch_powerbi.ps1`.
4. After the exact Project 16 PBIX opens, run `build/scripts/08_push_project16_model_to_powerbi_desktop.ps1`.
5. Save the report in Power BI Desktop.
6. Reopen the exact file and validate with `pbi-tools extract` and `pbi-tools export-data`.
