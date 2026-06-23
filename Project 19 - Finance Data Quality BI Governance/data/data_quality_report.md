# Data Quality Report

- Synthetic seed: `20260615`
- Date range: `2025-01-01` through `2026-05-31`
- Latest complete month: `May 2026`

| Table | Rows | Columns | Duplicate Rows | Null Cells |
|---|---:|---:|---:|---:|
| DimDate | 516 | 11 | 0 | 0 |
| DimDataset | 12 | 10 | 0 | 0 |
| DimReport | 9 | 8 | 0 | 0 |
| DimDepartment | 8 | 4 | 0 | 0 |
| FactDatasetDaily | 6,192 | 13 | 0 | 0 |
| FactRefreshRuns | 6,192 | 8 | 0 | 0 |
| FactReconciliation | 612 | 9 | 0 | 0 |
| FactUsage | 4,644 | 9 | 0 | 0 |
| FactAccessReview | 1,224 | 10 | 0 | 0 |
| FactIncidents | 240 | 9 | 0 | 0 |

All generated primary-key grains are non-null. Numeric QA confirms no percentages are pre-summed in prepared extracts; final rates are defined as DAX measures with `DIVIDE`.
