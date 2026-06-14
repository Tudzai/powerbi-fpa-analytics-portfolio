# Refresh Guide

1. Open `powerbi/pbip/Project5_Retention_Cohort/Project5_Retention_Cohort.pbip` in Power BI Desktop.
2. Confirm CSV paths point to `data/prepared/*.csv`.
3. Refresh all tables.
4. Validate KPI cards against `qa/reconciliation.xlsx`.
5. Save as `output/dashboard_final.pbix`.
6. Run `python build/scripts/05_validate_output.py`.
