# QA Checklist

| QA Layer | Status | Evidence |
|---|---|---|
| Data QA | PASS | `data/validated/data_quality_checks.csv` |
| Metric QA | PASS | `data/validated/kpi_summary.csv`, `qa/reconciliation.xlsx` |
| Visual QA | PASS | `output/screenshots/dashboard_final.png`, `output/screenshots/powerbi_desktop_dashboard_final.png` |
| Interaction QA | PASS basic PBIX smoke test | Power BI Desktop opened with slicers/page tabs visible |
| File QA | PASS | `output/dashboard_model.pbix`, `output/dashboard_final.pbix`, `qa/pbix_validation.json` |

Critical note: preview artifacts are supplemental. The final deliverable is `output/dashboard_final.pbix`.
