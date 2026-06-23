# PBIX Build Runbook

1. Open Power BI Desktop.
2. Import prepared CSVs from `data/prepared`.
3. Set datatypes:
   - keys as text
   - dates as date
   - emissions/spend/revenue/capex as decimal numbers
4. Create star-schema relationships from `model/relationship_map.md`.
5. Add DAX measures from `model/MEASURES.dax`.
6. Import theme from `build/config/theme.json`.
7. Build the 4 pages from `report/report_spec.md`.
8. Save as `output/dashboard_final.pbix`.
9. Reopen exact file and complete `qa/pbix_final_validation.json`.
