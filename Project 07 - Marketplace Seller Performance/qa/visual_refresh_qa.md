# Visual Refresh QA

- Refresh version: Marketplace Command Center v3
- Applied on: 2026-06-11
- PBIX target: `output/dashboard_final.pbix`
- Native visual count after refresh: 11
- Native visual types: textbox, textbox, cardVisual x6, lineChart, barChart, tableEx
- `pbi-tools extract`: PASS
- `pbi-tools export-data`: PASS
- Preview screenshots: PASS by visual inspection for Page 1 through Page 4

Design checks:

- KPI label/value overlap removed.
- Page 4 risk KPI row uses the same 6-card layout as Page 1.
- Seller table fits within the panel without covering the panel title.
- Colors carry metric meaning: commerce orange, good green, risk red/amber, rating teal, stock/risk violet, platform blue/cyan.
