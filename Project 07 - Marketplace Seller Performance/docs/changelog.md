# Changelog

## v10 - 2026-06-11

- Rebuilt the final PBIX as a complete native Power BI dashboard with 4 pages and 47 visuals.
- Added native chart coverage: KPI cards, GMV trend line charts, GMV/platform bar charts, seller leaderboard tables, growth driver visuals, and ops risk visuals.
- Fixed the Power BI Desktop open error for layout-patched PBIX files by omitting stale `SecurityBindings` after `Report/Layout` changes and saving the result in Desktop.
- Verified `output/dashboard_final.pbix` opens in Power BI Desktop with named page tabs, `Page 1 of 4`, chart visuals, and seller tables.
- Copied the Desktop-saved final PBIX to `output/dashboard_complete.pbix`.
- Revalidated the Desktop-saved PBIX with `pbi-tools extract` and `pbi-tools export-data`.

## v09 - 2026-06-11

- Researched Power BI/ecommerce dashboard design patterns from Microsoft Learn, Fabric Community, ZoomCharts, and Coupler.io examples.
- Created `build/config/marketplace_command_center_theme.json` with marketplace-oriented colors, card/table defaults, light page background, and restrained borders.
- Applied the report theme to the final openable PBIX files: `output/dashboard_final.pbix` and `output/dashboard_complete.pbix`.
- Verified `output/dashboard_final.pbix` opens in Power BI Desktop with no corrupted-file dialog after the theme change.
- Revalidated the themed PBIX with `pbi-tools extract` and `pbi-tools export-data`.

## v08 - 2026-06-11

- Fixed Power BI open failure after `output/dashboard_complete.pbix` and `output/dashboard_final.pbix` were rejected by Power BI Desktop as corrupted/unrecognized.
- Archived the corrupted script-patched PBIX files under `archive/old_versions/`.
- Restored both output PBIX files from the last Power BI Desktop-saved backup: `archive/old_versions/dashboard_final_before_visual_refresh_20260611_123505.pbix`.
- Verified the restored file opens in Power BI Desktop with window title `dashboard_final`.
- Revalidated with `pbi-tools extract` and `pbi-tools export-data`.
- Disabled direct PBIX layout patching by default in the visual refresh and complete PBIX scripts to prevent accidental regeneration of corrupted files.

## v07 - 2026-06-11

- Created one complete Power BI file: `output/dashboard_complete.pbix`.
- Replaced `output/dashboard_final.pbix` with the same complete PBIX content.
- Expanded the native Power BI report to 4 pages and 47 visuals: 8 textboxes, 24 cards, 5 line charts, 6 bar charts, and 4 tables.
- Added complete PBIX build script: `build/scripts/11_build_complete_pbix.py`.
- Validated the complete PBIX with `pbi-tools extract` and `pbi-tools export-data`.

## v06 - 2026-06-11

- Added a self-contained interactive dashboard: `output/dashboard_complete.html`.
- Added global filters for month, platform, seller tier, and seller search.
- Added four complete dashboard views: Executive Cockpit, Seller Portfolio, Growth Drivers, and Ops Risk.
- Added dashboard QA output: `qa/dashboard_complete_validation.json`.
- Added handoff doc for the complete dashboard: `docs/dashboard_complete_handoff.md`.

## v05 - 2026-06-11

- Researched Power BI/ecommerce dashboard template patterns and documented sources in `docs/template_research.md`.
- Applied `Marketplace Command Center v3` visual refresh.
- Updated native PBIX layout from 2 visuals to 11 visuals: title/meta text, 6 KPI cards, GMV trend line chart, platform GMV bar chart, and seller performance table.
- Regenerated polished 4-page preview screenshots and `output/dashboard_preview.html`.
- Revalidated PBIX with `pbi-tools extract` and `pbi-tools export-data`.

## v04 - 2026-06-11

- Re-ran authoring after the Computer Use skill became callable.
- Replaced prior Project 06 - Marketing Campaign ROI/Marketing model in the target Power BI session with Project 07 - Marketplace Seller Performance marketplace seller model.
- Added project-local Power BI model push script: `build/scripts/08_push_project7_model_to_powerbi_desktop.ps1`.
- Created native PBIX visuals: KPI card and seller performance table.
- Saved real final PBIX and copied it to `output/dashboard_final.pbix`.
- QA passed: PBIX extract, model data export, and native visual binding checks.

## v03 - 2026-06-11

- Rebuilt after explicit Computer Use request.
- Initial tool discovery did not expose a callable click/screenshot/UI-control surface before the dedicated Computer Use skill was invoked.

## v02 - 2026-06-11

- Rebuilt Project 07 - Marketplace Seller Performance from scratch following BI A-Z Master Prompt v2.
- Added PBIX authoring decision and authoring strategy docs.
- Generated synthetic marketplace data, model specs, DAX, page maps, visual maps, QA files, and screenshots.
- QA passed: data and metric package checks; file QA remains blocked pending PBIX authoring.
