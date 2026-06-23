# Project 20 Upgrade Handoff

## Final Output

- Final PBIX: `output/dashboard_final.pbix`
- Supplemental preview: `output/dashboard_final.html`
- Screenshot evidence: `output/screenshots/pbix_project20_upgrade_dynamic_svg_v21.png`
- Build route: scripted Desktop PBIX using TOM model push, native `/Report/Layout` patch, dynamic `tableEx` SVG KPI cards, and PowerBIPackager validation.

## Pages Upgraded

1. Treasury Command Center
2. Working Capital Control
3. Forecast, FX & Risk

## Project 20 Patterns Applied

- Dark left rail with compact dropdown slicers.
- Four dynamic SVG KPI cards per page, backed by DAX ImageUrl measures.
- Current Lens context and page-level decision chips.
- Diagnostic chart grid with chart-panel styling.
- Detail/action tables with subtle header fill, row banding, and compact finance typography.
- Native layout verification and Desktop screenshot QA.

## Model And Visual Scale

- Tables: 18
- Relationships: 17
- Measures: 47
- Measure table: `KPI_Measures`
- Visual containers: 111
- Visual mix: 21 tableEx visuals, 12 bar charts, 2 column charts, 1 waterfall chart, 24 shapes, 39 textboxes, 12 slicers.

## QA Evidence

- `qa/pbix_final_validation.json`: final PBIX file/package/model/report validation.
- `qa/project20_upgrade_verification.json`: Project 20 structural pattern checks by page.
- `qa/project20_upgrade_qa.md`: human-readable upgrade QA checklist.
- `qa/qa_checklist.md`: overall pass/fail checklist.
- `qa/visual_qa_notes.md`: Desktop/mobile/visual QA notes.

## Known Limitations

- Explicit slicer sync-group metadata was not found in the generated native layout; repeated compact slicers are present on every page.
- Synthetic data is for portfolio/demo use only.

## Rebuild

```powershell
python tools/build_project14.py
python tools/validate_dashboard.py
python tools/build_native_pbix_assets.py
powershell -ExecutionPolicy Bypass -File powerbi/apply_native_layout_to_pbix.ps1
```
