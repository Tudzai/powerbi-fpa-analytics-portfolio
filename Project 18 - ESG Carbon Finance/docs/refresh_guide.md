# Refresh Guide

This is a synthetic portfolio build. Refresh means regenerating the deterministic synthetic source and reloading the prepared CSVs.

Steps:
1. Run `python build/scripts/build_project18_assets.py`.
2. Refresh the Power BI model.
3. Check row counts in `data/validated/validation_summary.json`.
4. Reconcile KPIs using `qa/reconciliation.csv`.
5. Re-run visual QA.
