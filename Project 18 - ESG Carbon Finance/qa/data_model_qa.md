# Data Model QA

Status: pass for synthetic portfolio data.

Checks:
- Prepared CSVs exist.
- Date range covers Jan 2024 through May 2026.
- Dimension keys are unique.
- Fact record IDs are unique.
- Critical key fields are non-null.
- Rate measures are defined with DIVIDE in DAX.
