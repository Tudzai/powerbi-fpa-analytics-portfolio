# QA Checklist

- Data QA: pass
- Metric QA: pass; DAX catalog contains 26 documented measures.
- Bridge QA: 0 groups outside $1 tolerance; max abs diff $0.02
- HTML visual QA: pass at 2026-06-14T19:42:21.318Z; 3 tabs checked, 12 KPI cards, 24 panels, 8 tables, 14 SVG charts, no console errors/overflow/NaN on desktop and mobile.
- PBIX QA: pass; native final PBIX at `output/dashboard_final.pbix` has 3 tabs, PowerBIPackager.Validate passed, Power BI Desktop opened the exact file, rendering-error text scan returned 0 errors on each tab, and pbi-tools extract/export-data passed.
