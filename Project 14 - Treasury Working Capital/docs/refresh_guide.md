# Refresh Guide

Portfolio refresh:
1. Re-run `python tools/build_project14.py`.
2. Re-run HTML validation.
3. Rebuild native PBIX assets and refresh the Desktop seed session.

Production source replacement:
- Replace synthetic raw exports with bank statement, AR subledger, AP subledger, ERP working-capital, treasury forecast, facility, and FX exposure extracts.
- Preserve the documented table grain and keys.
- Stop publish if row-count reconciliation, key uniqueness, forecast continuity, or FX hedge-ratio checks fail.
