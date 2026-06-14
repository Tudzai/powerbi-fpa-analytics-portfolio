# Data Quality Report

## Source Status

- Source type: synthetic FP&A portfolio sample.
- Latest complete actual month: 2026-05-01.
- Generated raw files are deterministic from `build/scripts/00_generate_sample_raw.py`.
- No source rows are manually edited in `data/raw/`.

## File Profile

### data/raw/raw_fpa_budget_actual_bridge.csv

- Rows: 112
- Columns: 6
- Date range: 2026-05-01 to 2026-05-01
- Missing values: none detected.

### data/raw/raw_fpa_cash.csv

- Rows: 656
- Columns: 8
- Date range: 2025-01-01 to 2026-12-01
- Missing values: none detected.

### data/raw/raw_fpa_financials.csv

- Rows: 17712
- Columns: 16
- Date range: 2025-01-01 to 2026-12-01
- Missing values: none detected.

### data/raw/raw_fpa_opex_department.csv

- Rows: 3280
- Columns: 7
- Date range: 2025-01-01 to 2026-12-01
- Missing values: none detected.

### data/raw/raw_monthly_commentary.csv

- Rows: 3
- Columns: 6
- Date range: 2026-03-01 to 2026-05-01
- Missing values: none detected.

## Key Controls

- Revenue, COGS, gross margin, opex, EBITDA, orders, and cash impact are positive numeric fields.
- Gross margin equals Revenue minus COGS in source, within rounding tolerance.
- EBITDA equals GrossMargin minus AllocatedOpex in source, within rounding tolerance.
- Budget and Forecast cover Jan 2026-Dec 2026; Actual covers Jan 2025-May 2026.

## Known Caveats

- This package is build-ready for Power BI but is not final PBIX until opened, refreshed, and QA-tested in Power BI Desktop.
- Forecast values are sample management assumptions, not a statistically generated forecast model.
