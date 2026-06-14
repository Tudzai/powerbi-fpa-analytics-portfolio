# PBIX Build Runbook

Current build state: final PBIX is complete and verified in Power BI Desktop.

Routes:

1. Native layout route: generate `build/native_report_layout_retention.json`, patch `/Report/Layout` into a valid model PBIX, then validate with `Microsoft.PowerBI.Packaging.PowerBIPackager`.
2. Desktop verification route: open `output/dashboard_final.pbix`, refresh/model-check if needed, verify all 4 report pages, and save.
3. PBIP source route: use `powerbi/pbip/Project5_Retention_Cohort/Project5_Retention_Cohort.pbip` as the source package, then save as PBIX in Desktop if the report source needs rebuilding.

Final verification completed on 2026-06-11: all 4 pages rendered with zero visual fetch errors.
