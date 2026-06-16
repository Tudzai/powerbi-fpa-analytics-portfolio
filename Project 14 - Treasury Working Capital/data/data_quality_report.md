# Data Quality Report

Status: **pass**

| Check | Status | Detail |
|---|---|---|
| FactCashForecast grain uniqueness | pass | 0 duplicate keys on week_id, entity_id, scenario_id |
| FactCashPosition grain uniqueness | pass | 0 duplicate keys on snapshot_date, entity_id, bank_id |
| FactWorkingCapital grain uniqueness | pass | 0 duplicate keys on date_id, entity_id |
| FactFXExposure grain uniqueness | pass | 0 duplicate keys on exposure_id |
| 13-week forecast cash continuity | pass | 0 opening-to-prior-closing mismatches |
| AR/AP outstanding non-negative | pass | 0 invoices with negative outstanding balance |
| Working capital days within realistic portfolio band | pass | DSO outliers=0, DPO outliers=0 |
| FX hedge ratios bounded | pass | 0 rows outside 0-1 hedge ratio range |
| Entity foreign keys valid | pass | 0 invalid entity references |
