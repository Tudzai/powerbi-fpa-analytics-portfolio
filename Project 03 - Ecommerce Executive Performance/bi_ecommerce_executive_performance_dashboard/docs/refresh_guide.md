# Refresh Guide

For demo data:

1. Run `build/scripts/00_create_project_structure.py`.
2. Open Power BI Desktop.
3. Refresh all queries.
4. Validate KPI cards against `data/validated/kpi_summary.csv`.
5. Save and export screenshots.

For production data:

1. Replace the synthetic source generation step with official ecommerce exports.
2. Preserve the same prepared schema where possible.
3. Re-run data QA and metric QA before changing dashboard visuals.
