# Project 14 - Treasury Working Capital

Executive-ready treasury BI product for cash forecasting, working capital control, liquidity monitoring, and FX exposure.

## Main Artifacts

- Expected final Power BI report: `output/dashboard_final.pbix`
- Supplemental HTML preview: `output/dashboard_final.html`
- Data and model package: `data/`, `model/`, `build/config/`, `powerbi/`

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
