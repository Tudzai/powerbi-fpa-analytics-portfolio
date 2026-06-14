# Build Steps

1. Run `build/scripts/00_create_project_structure.py` with the bundled Python runtime to regenerate the project.
2. Open Power BI Desktop.
3. Import all CSV files in `data/prepared/`.
4. Create relationships using `model/relationship_map.md`.
5. Add measures from `model/dax_measures.md`.
6. Apply `build/config/theme.json`.
7. Build pages using `build/config/page_map.json` and `build/config/visual_map.json`.
8. Add slicers from `build/config/slicer_map.json`.
9. Save as `output/dashboard_final.pbix`.
10. Reopen, refresh, save, and screenshot for File QA.

Important: do not place a fake PBIX at `output/dashboard_final.pbix`. The file must be a real Power BI file that opens, refreshes, and saves.
