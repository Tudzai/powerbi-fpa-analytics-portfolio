# Changelog

## v01-build-ready

- Created standard BI project folder structure.
- Generated deterministic FP&A sample raw data.
- Created prepared star-schema data for Power BI.
- Added source summary, quality report, data dictionary, and reconciliation QA.
- Added DAX measure library for Actual/Budget/Forecast, variance, cash, and commentary.
- Added Power Query build script and orange executive theme.
- Added page map and visual map for five Power BI pages.
- Added PBIX build instructions and handoff notes.
- Added static HTML preview to inspect layout and orange theme before PBIX build.
- Updated PBIX status after detecting Power BI Desktop Store app; PBIX authoring and visual QA remain pending.

## v02-model-pbix

- Pushed the FP&A semantic model into Power BI Desktop local Analysis Services.
- Saved valid Power BI Desktop model files as `output/dashboard_model.pbix` and `output/dashboard_final.pbix`.
- Verified the Desktop model has 13 tables, 19 relationships, and 49 measures.
- DAX spot check passed for May 2026 current-month revenue.
- Attempted direct report-layout injection and restored the PBIX after Desktop rejected unsupported internal layout edits.
- Updated handoff status to distinguish complete semantic model from pending report-canvas authoring.

## v03-visible-dashboard

- Rebuilt the HTML dashboard renderer so `output/dashboard.html` is the visible dashboard deliverable.
- Added KPI cards for Revenue, Gross Margin, EBITDA, Opex, Cash, and Orders.
- Added Actual vs Budget vs Forecast comparison, 12-month trend, EBITDA bridge, variance drivers, commentary, and drill-down tabs.
- Mirrored the dashboard to `output/exports/fpa_dashboard_preview.html`.
- Updated PBIX status and handoff notes to distinguish the visible dashboard from the model-only PBIX.

## v04-powerbi-project-dashboard

- Generated a visible Power BI Project dashboard entry point at `output/open_dashboard_powerbi.pbip`.
- Added PBIR report definition with 4 pages and 16 visuals.
- Added local semantic model folder with TMSL `model.bim` exported from the FP&A Desktop model.
- Added `output/OPEN_POWERBI_DASHBOARD.md` as the clear dashboard entry note.
- Validated 27 generated Power BI project JSON files parse successfully.

## v05-final-pbix-dashboard

- Added `build/scripts/09_build_legacy_pbix_report.ps1`.
- Generated final Power BI Desktop report canvas directly into `output/dashboard_final.pbix`.
- Added 4 PBIX report pages: Executive Overview, Variance Bridge, Customer / Product Drilldown, and Opex & Cash Control.
- Added 366 generated visual containers with orange FP&A styling, KPI cards, 12-month trend, bridge, variance diagnostics, commentary, and drill-down pages.
- Removed `/SecurityBindings` from the generated PBIX package so Power BI Desktop opens the target file instead of falling back to a blank report.
- Validated `output/dashboard_final.pbix` with `PowerBIPackager.Validate`.
- Opened `output/dashboard_final.pbix` in Power BI Desktop and confirmed the model contains 13 tables, 19 relationships, and 49 measures.
- Saved verification screenshot at `output/screenshots/dashboard_final_powerbi_final.png`.

## v06-native-kpi-dashboard

- Rebuilt `output/dashboard_final.pbix` as a native Power BI visual dashboard instead of the legacy textbox/shape canvas.
- Removed commentary/insight sections from the dashboard canvas.
- Focused the first page on key FP&A indicators: Revenue, Gross Margin %, EBITDA, Opex, and Cash.
- Fixed currency display so cards show values like `333M`, `38M`, `920M`, and `115M` instead of `0.0MM`.
- Added current-month Cash and DSO measures so Cash no longer returns blank when actual data stops at May 2026.
- Constrained all visuals to a safe left-zone of the 1280px canvas so data is not hidden or clipped in Power BI Desktop.
- Final PBIX audit: 4 pages, 40 visual containers, 10 native KPI cards, 13 slicers, 5 bar charts, 3 column charts, 4 tables, 1 waterfall chart, and 4 page-title textboxes.
- Final screenshot saved at `output/screenshots/dashboard_final_v06_native_safezone_final.png`.

## v07-balanced-layout

- Expanded the native dashboard layout to use more of the 1280px report canvas while preserving right-edge safety.
- Increased KPI card, chart, and table widths versus v06 safe-zone layout.
- Kept all visuals within max right edge 1066 to avoid the Power BI Desktop crop issue seen at wider layouts.
- Shortened slicer labels, including `BU` and `Dept`, and hid the slicer header to avoid duplicated labels.
- Final screenshot saved at `output/screenshots/dashboard_final_v07_balanced_layout.png`.

## v08-right-insight-driver

- Added `Revenue Variance by Region` to the Executive KPI page to fill the lower-right dashboard space with an FP&A driver chart.
- Split the bottom Executive section into a scenario KPI table plus a regional revenue variance chart.
- Expanded KPI cards, trend chart, bridge/drilldown/cash visuals, and downstream page tables to use more of the 1280px canvas.
- Final PBIX audit: 4 pages, 41 visual containers, 10 KPI cards, 13 slicers, 6 bar charts, 3 column charts, 4 tables, 1 waterfall chart, and 4 page-title textboxes.
- Final screenshot saved at `output/screenshots/dashboard_final_v08_right_insight.png`.
