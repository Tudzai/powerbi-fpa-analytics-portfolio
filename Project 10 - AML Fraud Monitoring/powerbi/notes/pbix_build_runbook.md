# PBIX Build Runbook

1. Copy a valid technical seed PBIX into `output/dashboard_model.pbix`.
2. Launch that exact file in Power BI Desktop.
3. Run `build/scripts/07_push_model_to_powerbi_desktop.ps1`.
4. Save the exact file in Desktop.
5. Run `build/scripts/10_apply_native_pbix_report.ps1`.
6. Open `output/dashboard_final.pbix` in Desktop and verify 3 pages with native visuals and no visual error.
