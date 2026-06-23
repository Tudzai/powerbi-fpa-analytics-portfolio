# Project 20 Style Upgrade Handoff

## Result

Project 13 has been upgraded so slicers sit in a top filter bar above the KPI strip on all native PBIX pages.

- Final PBIX: `output/dashboard_final.pbix`
- Layout source: `build/native_report_layout_project13.json`
- Rebuild source: `tools/build_native_pbix_assets.py`
- Screenshot evidence: `output/screenshots/powerbi_desktop_top_slicer_final_20260623.png`
- Verification JSON: `qa/project20_upgrade_verification.json`

## Pages Updated

- Executive Summary: Period, Region, BU slicers now sit at y=84.
- P&L Variance: Country and Scenario slicers now sit at y=84.
- Controls & Storyboard: Currency, Severity, Status slicers now sit at y=84.

## Layout Changes

- Added reusable `top_filter_bar(...)` to the native layout generator.
- Added a `FILTER LENS` top band under the page header.
- Moved KPI cards from y=92 to y=150.
- Moved chart/table rows down so max visual bottom is 696 on a 720px canvas.
- Cleaned a small pre-existing header text overlap between the brand line and page title.

## QA Evidence

- `PowerBIPackager.Validate`: pass.
- `pbi-tools extract`: pass; extracted report source is in `output/dashboard_final/`.
- Desktop exact-file open: pass via `pbi-tools info`.
- Desktop screenshot: pass, captured after render wait.
- Direct layout check: 8 slicers at y=84; non-shape overlap check pass.
- Project 13 Desktop sessions left running: none. Other open sessions belonged to unrelated projects and were ignored.

## Rebuild

Run:

```powershell
python tools/build_native_pbix_assets.py
powershell -ExecutionPolicy Bypass -File .\powerbi\apply_native_layout_to_pbix.ps1
```

Then re-run the validation checks documented in `qa/project20_upgrade_qa.md`.
