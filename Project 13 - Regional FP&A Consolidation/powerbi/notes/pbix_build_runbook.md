# PBIX Build Runbook

1. Open Power BI Desktop.
2. Import CSVs from `data/prepared/`.
3. Apply relationships from `model/relationship_map.md`.
4. Add measures from `model/MEASURES.dax`.
5. Apply theme from `build/config/theme.json`.
6. Recreate pages using `build/config/page_map.json` and `build/config/visual_map.json`.
7. Save as `output/dashboard_final.pbix`.
8. Reopen the exact PBIX and complete QA files under `qa/`.
