# Issue Log

- Resolved: the first promoted PBIX failed in Power BI Desktop with a report-load error. Root cause was an incompatible PBIR/new-layout `Report/Layout` payload patched into a legacy PBIX report stream.
- Resolved: final PBIX was rebuilt from a clean Power BI Desktop session, with the AML model persisted into `output/dashboard_model_clean.pbix`, then promoted to `output/dashboard_final.pbix`.
- Resolved: final report layout was regenerated in legacy visual container format using `build/scripts/12_generate_legacy_report_layout.py`.
- Resolved: final layout was applied and package-validated using `build/scripts/13_apply_legacy_pbix_report.ps1`.
- Verified: Power BI Desktop open-check passed for `output/dashboard_final.pbix`.
- Verified: offline `pbi-tools export-data` from the final PBIX returned all expected AML tables and row counts.
- Verified: offline `pbi-tools extract` from the final PBIX succeeded.
- Improved: KPI card layout was regenerated with more vertical space and explicit value formatting, then revalidated in `output/dashboard_final.pbix`.
- Improved: an agent-led aesthetic pass replaced the plain default-Power-BI look with a dark command-center visual system, semantic risk colors, light KPI tiles, compact header treatment, and dark analytical panels.
- Supplemental fallback artifacts remain available: `output/dashboard_final.html` and repaired `output/dashboard_final.pbip` / `output/dashboard_final_project/AML_Fraud_Monitoring_Command_Center.pbip`.
