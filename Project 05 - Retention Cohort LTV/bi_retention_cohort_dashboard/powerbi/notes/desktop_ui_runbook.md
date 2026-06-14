# Desktop UI Runbook

1. Run `powerbi/launch_powerbi.ps1` if Desktop is not open.
2. Open `powerbi/pbip/Project5_Retention_Cohort/Project5_Retention_Cohort.pbip`.
3. If prompted for source privacy or credentials, choose local file settings for the CSV files under `data/prepared`.
4. Refresh all data.
5. Verify model relationships:
   - DimUser to FactOrders, FactUserMonth, ChurnRiskSnapshot
   - DimMonth to FactOrders, FactUserMonth, MonthlyKPIs, MonthlyLifecycleMix, CohortRetention, SegmentMonthly
6. Confirm measures from `model/dax_measures.md`.
7. Apply theme `build/config/theme.json`.
8. Check all four pages against `build/config/page_map.json` and `build/config/visual_map.json`.
9. Save as `output/dashboard_final.pbix`.
10. Reopen the PBIX, refresh, and rerun `python build/scripts/05_validate_output.py`.
