# QA Checklist

Data QA: PASS

Metric QA: PASS

Visual QA: PASS
- Opened exact `output/dashboard_final.pbix` in Power BI Desktop.
- Checked `Growth Overview`, `Funnel & Cohort Retention`, and `LTV, Churn & Marketing ROI`.
- No `Visual error`, `Something's wrong`, or `Error fetching data` indicators detected in Desktop QA.

File QA: PASS
- `pbi-tools extract` completed to `qa/pbix_extract_final_project11`.
- `pbi-tools export-data` completed to `qa/export_data_final`.
- `build/scripts/04_validate_output.py` returned `pass`.
