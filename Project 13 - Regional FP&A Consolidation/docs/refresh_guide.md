# Refresh Guide

For the portfolio version, refresh means rerunning the deterministic generator:

```powershell
python tools/build_project13.py
python tools/validate_dashboard.py
```

For production, replace `data/raw/` with ERP, EPM, consolidation, FX, and close-management exports. Preserve the documented table grain, keys, and sign conventions, then regenerate `data/prepared/` plus QA.

Suggested operating controls:

- Cadence: monthly close refresh after regional consolidation lock.
- Owner: FP&A analytics owner; backup: regional finance systems owner.
- Schema checks: row counts, required keys, numeric types, scenario list, currency list, and account hierarchy completeness.
- Reconciliation thresholds: account-detail totals to summary totals at $1 tolerance; variance bridge to Actual vs Budget EBITDA at $1 tolerance.
- Failure handling: stop publish on failed FK, duplicate grain, missing scenario, bridge mismatch, or HTML QA failure.
- Production extension: add incremental refresh once real source date partitions are available.
