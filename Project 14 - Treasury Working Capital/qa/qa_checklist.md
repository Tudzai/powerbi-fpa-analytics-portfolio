# QA Checklist

- Data QA: pass.
- Metric QA: pass; DAX catalog contains 47 documented measures.
- HTML visual QA: pass via `python tools/validate_dashboard.py` on desktop and mobile viewports.
- Native PBIX package QA: pass via `powerbi/apply_native_layout_to_pbix.ps1` and PowerBIPackager validation.
- Project 20 style structural QA: pass via `qa/project20_upgrade_verification.json` across all 3 PBIX pages.
- Dynamic KPI/SVG QA: pass; final PBIX has 12 model-bound `tableEx` SVG KPI cards, 4 per page, using ImageUrl measures with mini sparklines.
- Desktop visual QA: pass via `output/screenshots/pbix_project20_upgrade_dynamic_svg_v21.png`; command-center KPI row renders dynamic SVG cards and slicer labels remain visible.
