# Power BI Desktop Evidence

Date: 2026-06-11

## Result

- Final PBIX: `output/dashboard_final.pbix`
- Status: PASS
- File size after final save: 1,881,639 bytes

## Desktop Route Completed

1. Patched native report layout into `output/dashboard_final.pbix`.
2. Opened `output/dashboard_final.pbix` in Power BI Desktop.
3. Confirmed Page 1 was no longer blank.
4. Fixed model data types where CSV columns had loaded as text.
5. Saved the final PBIX from Power BI Desktop.

## Render QA

- Page 1: Lifecycle Overview - PASS; cards and charts rendered, no visual fetch errors.
- Page 2: Monthly Cohort Retention - PASS; cohort table and retention charts rendered, no visual fetch errors.
- Page 3: LTV & Revenue Cohorts - PASS; LTV/revenue charts and segment table rendered, no visual fetch errors.
- Page 4: Churn Signal & Winback - PASS; churn/risk page rendered, no visual fetch errors.

## Validation

- `python build/scripts/03_validate_prepared_data.py`: PASS
- `python build/scripts/05_validate_output.py`: PASS
- `qa/pbix_native_report_validation.json`: PASS package validation after native layout patch.
