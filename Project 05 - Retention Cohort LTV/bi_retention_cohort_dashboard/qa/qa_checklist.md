# QA Checklist

## Data QA

- Status: PASS
- Customer grain unique: checked
- Order grain unique: checked
- Completed revenue reconciliation: checked
- Customer-month grain unique: checked
- Retention and repeat rates bounded: checked

## Metric QA

- Status: PASS
- Rates use DIVIDE-style logic and are not summed.
- Repeat purchase denominator is active customers.
- Cohort retention denominator is original first-purchase cohort size.
- Churn signal is labeled as a proxy signal, not a hard cancellation event.

## Visual QA

- Status: PASS
- Four page screenshots generated in `output/screenshots`.
- HTML/PDF preview generated.
- Native Power BI pages render in Desktop with zero visual fetch errors.

## Interaction QA

- Status: PASS
- Power BI Desktop opened the final PBIX, slicers/tabs were accessible, and all four report pages rendered.

## File QA

- Status: PASS
- `output/dashboard_final.pbix` exists, passed package/file validation, and was saved from Power BI Desktop after render QA.
