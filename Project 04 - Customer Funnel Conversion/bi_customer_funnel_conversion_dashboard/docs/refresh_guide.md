# Refresh Guide

1. Run `python build/scripts/00_build_project4.py` to regenerate synthetic raw/prepared data and docs.
2. Run `python build/scripts/11_render_complete_dashboard.py` to rebuild `output/dashboard.html` and the complete filter cube.
3. Validate KPI totals against `qa/reconciliation.xlsx` and `qa/complete_dashboard_qa.json`.
4. For native PBIX only, open Power BI Desktop and import/refresh CSVs from `data/prepared/`.
5. Save PBIX to `output/dashboard_final.pbix` only after clean report-layout File QA passes.
