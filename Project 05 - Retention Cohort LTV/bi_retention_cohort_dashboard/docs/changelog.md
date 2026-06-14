# Changelog

## v01 - 2026-06-11

- Rebuilt Project 05 - Retention Cohort LTV from scratch for Retention & Cohort Dashboard.
- Added fixed-seed synthetic lifecycle data.
- Added prepared customer-month, cohort retention, monthly KPI, segment, and churn-risk tables.
- Added model definitions, DAX measures, relationship map, page map, visual map, theme, previews, QA, and handoff docs.
- QA passed: data, metric, visual preview.
- Initial QA gap: final PBIX required Desktop save/refresh before handoff.

## v02 - 2026-06-11

- Researched Power BI dashboard design/template guidance and applied a modern product analytics console style.
- Rebuilt preview screenshots with sidebar navigation, compact filter chips, contextual KPI cards, improved heatmap styling, and clearer diagnostic panels.
- Updated Power BI theme colors and visual container styling for a cleaner portfolio presentation.
- Added design research and design system documentation.

## v03 - 2026-06-11

- Added native PBIX report layout with 4 pages and 57 visual containers.
- Patched final PBIX report canvas so it no longer opens blank.
- Fixed CSV import typing in the model so DAX measures aggregate numeric/date fields correctly.
- Verified all 4 report pages in Power BI Desktop with zero visual fetch errors.
- Saved final dashboard as `output/dashboard_final.pbix` and reran PBIX file QA successfully.
