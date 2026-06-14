# Interaction QA Notes

Status: pending PBIX build.

## Required Checks

- Year, MonthYear, BusinessUnit, and Region slicers sync across all report pages.
- Department slicer, if added, should affect Opex visuals only.
- Customer slicer must use dropdown/search mode.
- Drillthrough target from Executive Overview to Business Unit Deep Dive should pass BusinessUnit and Region.
- Matrix drill-down should move from BusinessUnit to Region or Product without breaking totals.
- Reset bookmark should clear all slicers to May 2026 default.
