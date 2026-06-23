# Project 20 Style Upgrade Handoff

Date: 2026-06-23

What changed:
- Added a dedicated top filter bar to every page.
- Standardized slicer positions to `x=24/336/648/960`, `y=72`, `width=296`, `height=52`.
- Shifted KPI cards to `y=142`, charts to `y=244`, and tables lower on the canvas to prevent overlap.
- Regenerated native layout JSON, slicer map, PBIX container layout, and screenshot previews.
- Patched the supplemental PBIT schema package layout to match the PBIX/source layout.

Pages upgraded:
- 01 Manufacturing FP&A Overview
- 02 Standard Cost Variance
- 03 Yield Capacity & WC

Evidence:
- Source layout: `build/native_report_layout_project16.json`
- Config: `build/config/slicer_map.json`
- PBIX layout patch: `qa/native_layout_validation.json`
- Supplemental PBIT: `output/dashboard_project16_model_schema.pbit`
- Screenshots: `output/screenshots/`
- QA note: `qa/project20_upgrade_qa.md`
- Verification: `qa/project20_upgrade_verification.json`

Known issue:
- `output/dashboard_final.pbix` remains blocked as a final PBIX because the saved file still contains the seed DataModel when validated offline. The report layout is updated inside both the PBIX container and supplemental PBIT package, but the DataModel persistence issue remains documented in `output/PBIX_BUILD_STATUS.md`.
