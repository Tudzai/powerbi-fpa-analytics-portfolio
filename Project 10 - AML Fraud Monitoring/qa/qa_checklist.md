# QA Checklist

## Data QA

- [x] Synthetic data generated with fixed seed 20260611.
- [x] Row counts, duplicate key checks, and missing critical values captured.
- [x] Prepared CSVs exist for facts and dimensions.

## Metric QA

- [x] KPI definitions documented in `model/metric_definitions.md`.
- [x] DAX measures use DIVIDE for rates.
- [x] Reconciliation CSV/XLSX generated.

## Visual QA

- [x] HTML dashboard preview generated.
- [x] Final HTML dashboard generated as `output/dashboard_final.html`.
- [x] Native Power BI report layout JSON generated.
- [x] Repaired final PBIP project generated as `output/dashboard_final.pbip`.
- [x] Legacy PBIX report layout generated as `build/legacy_report_layout_aml.json`.
- [x] Agent-led aesthetic refresh applied to the final PBIX layout.
- [x] Exact PBIX opened in Power BI Desktop.
- [x] Report canvas loaded without the previous fatal layout error.
- [x] PBIX validation documented in `output/PBIX_BUILD_STATUS.md` and `qa/final_pbix_validation.json`.

## File QA

- [x] Project folders and handoff docs created.
- [x] Repaired PBIP manifest generated as `output/dashboard_final_pbip_manifest.json`.
- [x] `output/dashboard_final.pbix` validated after Desktop build.
