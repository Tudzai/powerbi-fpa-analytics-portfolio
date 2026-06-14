# Semantic Model Notes

The model uses a star-schema style around transactions, alerts, cases, and rule governance events.
All executive KPIs are DAX measures in the disconnected `KPI Measures` table. Rate measures use DIVIDE.
Date filtering uses DimDate relationships to transaction, alert, case-created, and governance-change dates.
The data is deterministic synthetic portfolio data generated from seed 20260611.
