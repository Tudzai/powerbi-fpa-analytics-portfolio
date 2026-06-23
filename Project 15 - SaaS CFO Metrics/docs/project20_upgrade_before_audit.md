# Project 20 Upgrade Before Audit

Target: Project 15 - SaaS CFO Metrics.

Before-state inventory:
- Final PBIX existed at `output/dashboard_final.pbix`.
- Source build path used synthetic data, `model/model.bim`, native `Report/Layout` JSON, and seed PBIX/TOM/layout patch scripts.
- Pages: Executive Overview; Revenue & Retention; Efficiency & Forecast.
- Model: 13 data tables, 17 relationships, 52 DAX measures before upgrade.
- Layout: 47 native visual containers before upgrade.
- Style signals to preserve: light finance canvas, dark navy header/control language, SaaS CFO metrics, board-ready but not purple investor-pack skin.

Gaps versus Project 20 quality:
- KPI strip used native cards and crowded 5-6 card rows on some pages.
- No Current Lens SVG or page-level decision-chip context.
- No SVG KPI cards with PY/YoY/sparkline/target-band logic.
- Chart display units were not metric-aware for all ratio/percentage visuals.
- Upgrade-specific QA/handoff docs were missing.
