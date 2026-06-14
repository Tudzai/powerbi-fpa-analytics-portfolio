# Rebuild Guide

1. Run `python build/scripts/00_build_project8.py` from Project 08 - Digital Payments Profitability.
2. Launch Power BI Desktop with `powerbi/launch_powerbi.ps1`.
3. Push the model with `build/scripts/08_push_project8_model_to_powerbi_desktop.ps1`.
4. Save the Desktop report to `output/dashboard_final.pbix`.
5. Apply native report layout with `python build/scripts/09_build_native_report.py` if needed.
6. Reopen and save in Power BI Desktop.
7. Validate with `pbi-tools extract` and `pbi-tools export-data`.
