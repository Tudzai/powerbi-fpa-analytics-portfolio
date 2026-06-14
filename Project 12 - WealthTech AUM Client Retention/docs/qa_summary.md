# QA Summary

- Data quality status: `passed`.
- Synthetic data seed: `20260611`.
- Latest complete month: `2026-05-01`.
- Row counts:
  - DimDate: 29
  - DimClient: 860
  - DimPortfolio: 4
  - FactAUMMonthly: 11,540
  - FactAllocationMonthly: 57,700
  - FactRetentionActions: 211
- Reconciliation:
  - Latest fact AUM equals monthly KPI AUM: `True`.
  - Net new money formula passes: `True`.
  - Ending AUM nonnegative: `True`.

PBIX QA is written to `qa/pbix_native_report_validation.json` after `10_apply_native_pbix_report.ps1` runs.

## Browser QA

- Preview URL tested: `http://127.0.0.1:8122/dashboard_preview.html`.
- Desktop viewport: no horizontal overflow, all 3 tabs switch successfully, each tab has 3 nonblank SVG charts.
- Mobile viewport `390px`: no horizontal overflow, overview cards stack cleanly, 3 nonblank SVG charts.
- Screenshots:
  - `output/screenshots/dashboard_desktop_viewport.png`
  - `output/screenshots/dashboard_mobile_viewport.png`

## Native PBIX QA

- Model push status: `passed` via Power BI Desktop XMLA/TOM.
- Model PBIX: `output/dashboard_model.pbix`.
- Final PBIX: `output/dashboard_final.pbix`.
- Native layout validation: `passed`.
- Final PBIX size: `3,406,418` bytes.
- Pages:
  - AUM & Revenue Overview
  - Portfolio & Client Segments
  - Risk, Suitability & Retention
- Visual containers: `47`.
- Offline PBIX data export passed with row counts:
  - DimDate: 29
  - DimClient: 860
  - DimPortfolio: 4
  - FactAUMMonthly: 11,540
  - FactAllocationMonthly: 57,700
  - FactRetentionActions: 211
  - KPI Measures: 1
