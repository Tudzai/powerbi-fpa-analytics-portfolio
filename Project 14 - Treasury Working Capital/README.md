# Project 14 - Treasury Working Capital

Executive-ready treasury BI product for cash forecasting, working capital control, liquidity monitoring, and FX exposure.

## Main Artifacts

- Final Power BI report: `output/dashboard_final.pbix`
- Supplemental HTML preview: `output/dashboard_final.html`
- Data and model package: `data/`, `model/`, `build/config/`, `powerbi/`
- Desktop QA screenshot: `output/screenshots/pbix_project20_upgrade_dynamic_svg_v21.png`

## Dashboard Tabs

1. Treasury Command Center
2. Working Capital Control
3. Forecast, FX & Risk

## Data

Synthetic portfolio/demo data with fixed seed 14042. Do not use as production financial data.

## Rebuild

```powershell
python tools/build_project14.py
python tools/validate_dashboard.py
python tools/build_native_pbix_assets.py
```

To rebuild the native PBIX after the model seed is prepared and saved in Power BI Desktop:

```powershell
powershell -ExecutionPolicy Bypass -File powerbi/apply_native_layout_to_pbix.ps1
```

## Current Status

Project 20 style upgrade is validated. The final PBIX uses 3 pages, 18 model tables, 17 relationships, 47 measures, 111 native visual containers, and 12 dynamic SVG KPI cards rendered through `tableEx` ImageUrl measures.
