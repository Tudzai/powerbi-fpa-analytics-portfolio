# PBIX Authoring Strategy

Selected strategy: `COMPUTER_USE_PLUS_SCRIPTED_DESKTOP_PBIX`.

v2 strategy decision:

| Strategy | Result | Reason |
|---|---|---|
| COMPUTER_USE | Used | Computer Use was available and saved the active Power BI Desktop semantic model as `output/dashboard_model.pbix` |
| SCRIPTED_DESKTOP_PBIX | Used | The project-local scripts pushed the model, generated native report layout, packaged the final PBIX, and passed package validation |
| PBIP_PBIT | Not needed | A valid model PBIX was created directly from Power BI Desktop, so PBIP/PBIT fallback was unnecessary |
| MANUAL_ASSISTED | Not needed | Final PBIX was built and verified through Computer Use plus scripted packaging |

Important constraints:

- Do not use PBIX files from other portfolio projects as an ecommerce template unless the user explicitly approves.
- Do not create a fake, empty, renamed, or unverified PBIX.
- `SCRIPTED_DESKTOP_PBIX` evidence is kept in `_agent/scripted_desktop_pbix_check.md` and `qa/scripted_desktop_pbix_check.json`.

Built package:

- `data/prepared/*.csv`
- `model/relationship_map.md`
- `model/dax_measures.md`
- `build/config/theme.json`
- `build/config/page_map.json`
- `build/config/visual_map.json`
- `build/config/slicer_map.json`
- `powerbi/notes/desktop_ui_runbook.md`
- `output/dashboard_model.pbix`
- `output/dashboard_final.pbix`
- `output/screenshots/powerbi_desktop_dashboard_final.png`

Validation:

1. `PowerBIPackager.Validate` passed for both the versioned and final PBIX files.
2. The final PBIX was reopened in Power BI Desktop.
3. Screenshot/accessibility evidence confirmed the report rendered with the expected pages and KPIs.
