# PBIX Build Runbook

Current build status: `final_pbix_built_and_verified`.

Actual route: `COMPUTER_USE_PLUS_SCRIPTED_DESKTOP_PBIX`.

Prepared build package:

- `data/prepared/*.csv`
- `model/relationship_map.md`
- `model/dax_measures.md`
- `build/config/theme.json`
- `build/config/page_map.json`
- `build/config/visual_map.json`
- `powerbi/notes/desktop_ui_runbook.md`
- `build/native_report_layout_ecommerce.json`
- `output/dashboard_model.pbix`

Final PBIX status:

- `output/dashboard_final.pbix`: created.
- `PowerBIPackager.Validate`: passed.
- Power BI Desktop open check: passed.
- Screenshot evidence: `output/screenshots/powerbi_desktop_dashboard_final.png`.

Build notes:

- The semantic model was first pushed into Power BI Desktop and saved as `output/dashboard_model.pbix`.
- The native report layout was applied with `10_apply_native_pbix_report.ps1`.
- A theme config render error was fixed by moving `themeCollection` into the top-level Layout `config` JSON before repackaging.
