# Refresh Guide

1. Run `python build/scripts/00_build_aml_project.py` to regenerate synthetic data and configs.
2. Open the Project 10 - AML Fraud Monitoring model PBIX in Power BI Desktop.
3. Run `build/scripts/07_push_model_to_powerbi_desktop.ps1` to rebuild the semantic model from `data/prepared`.
4. Save in Power BI Desktop.
5. Run `build/scripts/10_apply_native_pbix_report.ps1` to create `output/dashboard_final.pbix`.
6. Reopen the exact final PBIX and capture QA screenshots.
