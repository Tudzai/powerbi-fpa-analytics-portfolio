# Power BI Build Steps

1. Run `powerbi/launch_powerbi.ps1`.
2. Import every CSV from `data/prepared/`.
3. Create relationships from `model/relationship_map.md`.
4. Add measures from `model/dax_measures.md` or `model/MEASURES.dax`.
5. Apply `build/config/theme.json`.
6. Build pages from `build/config/page_map.json`, `build/config/visual_map.json`, and `build/config/slicer_map.json`.
7. Refresh, validate against `qa/reconciliation.xlsx`, and save as `output/dashboard_final.pbix`.

Detected build mode: `computer_use_powerbi_desktop`. Authoring mode: `COMPUTER_USE`.

Final PBIX was created through Power BI Desktop UI automation, then validated with `pbi-tools extract` and `pbi-tools export-data`.
