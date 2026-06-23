# Project 15 - SaaS CFO Metrics

Final target: `output/dashboard_final.pbix`

Current final status: upgraded PBIX rebuilt and Desktop-checked on 2026-06-23. The final file contains the Project 20-style source upgrade, TOM-pushed model, native layout patch, and Power BI Desktop open-check evidence. See `qa/pbix_final_validation.json` and `qa/powerbi_desktop_evidence.json`.

Upgrade target: Project 20 quality benchmark while preserving the original light SaaS CFO / navy finance style.

Tabs:
- Executive Overview
- Revenue & Retention
- Efficiency & Forecast

Project 20 upgrade patterns applied:
- Left sidebar with page identity, compact dropdown slicers, and Current Lens SVG.
- Four SVG KPI cards per page with latest-month value, PY, YoY, target-band sparkline, and semantic color.
- Page-level decision chips for executive context.
- Synced slicer groups: Year, Segment, Motion, Region.
- Metric-aware chart units so percentages, ratios, months, and multiples are not forced into money units.
- Banded tables and synchronized chart/KPI slots across pages.

PBIX QA:
- Final PBIX: `output/dashboard_final.pbix`
- Size after Desktop save: 4,391,319 bytes
- SHA256 after Desktop save: `B93D9FB627EF5164F43B0B1DAD796ED1FEFC8E39BEBB65771D32235FFD93021C`
- Desktop pages checked: Executive Overview; Revenue & Retention; Efficiency & Forecast.

Latest complete month: May 2026
ARR: $25.3M
Net New ARR: $-24.8K
NRR: 99.5%
GRR: 96.8%
Logo churn: 2.9%

Data is synthetic portfolio/demo data generated with seed `20260615`.
