# PBIX Build Runbook

Build mode: `computer_use_powerbi_desktop`.
Authoring mode: `COMPUTER_USE`.

Final PBIX criteria:
- `output/dashboard_final.pbix` exists.
- File opens in Power BI Desktop.
- `pbi-tools extract` passes.
- `pbi-tools export-data` passes.
- Native pages contain cards, slicers, charts, and tables for all three requested tabs.
