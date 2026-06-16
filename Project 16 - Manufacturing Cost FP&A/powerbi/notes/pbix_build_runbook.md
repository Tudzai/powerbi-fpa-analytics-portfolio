# PBIX Build Runbook

Route: `SCRIPTED_DESKTOP_PBIX`.

Critical final criteria:
- `output/dashboard_final.pbix` exists.
- Exact PBIX opens in Power BI Desktop.
- Model contains Project 16 manufacturing tables and KPI measures.
- Report has 3 native pages and native visuals.
- `pbi-tools extract` and `pbi-tools export-data` pass where available.
