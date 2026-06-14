# Changelog

## v01 - 2026-06-11

- Rebuilt Project 04 - Customer Funnel Conversion from the v2 master prompt.
- Generated deterministic synthetic funnel data with seed `4042026`.
- Added prepared star-schema CSVs, metric definitions, DAX, relationship map, theme, page map, visual map, QA checklist, reconciliation workbook, HTML preview, and Power BI build package.
- Power BI Desktop and pbi-tools environment checks documented.
- Fixed Power BI TOM type inference for text business keys and verified semantic model push to Desktop.
- Recorded PBIX File QA blocker: `output/dashboard_model.pbix` still requires Desktop Save As/manual-assisted UI control.

## v02 - Design Refresh

- Researched executive Power BI, marketing, and funnel dashboard template patterns.
- Rebuilt the HTML preview as `Growth Command Center v2` with sidebar navigation, slicer rail, KPI-first layout, insight pill, funnel progression board, leakage watchlist, and denser diagnostic pages.
- Updated theme, page map, and visual map to match the refreshed portfolio-ready layout.

## v03 - Complete Interactive Dashboard

- Added `build/scripts/11_render_complete_dashboard.py`.
- Built `output/dashboard_payload_complete.json`, a 21,840-row aggregate cube at month x device x channel x campaign x category x product grain.
- Replaced `output/dashboard.html` with a five-page complete dashboard: Executive Funnel, Segment Diagnostics, Category & Product, Marketing Efficiency, and Data & QA.
- Upgraded slicers so device, channel, campaign, and category filters update KPI cards, funnel, trend, tables, product diagnostics, and marketing efficiency.
- Added URL state support for reproducible page/filter screenshots.
- Fixed zero-spend ROAS/CAC display for owned channels and direct/referral campaigns.
- Added final QA evidence in `qa/complete_dashboard_qa.json` and regenerated `page_p1_complete.png` through `page_p5_complete.png`.
- Re-verified Power BI Desktop model push through process `34720` / port `57777`; this was superseded by the v04 native PBIX workflow.

## v04 - Native PBIX File

- Added `build/scripts/12_build_powerbi_template_compat.py` to create Power BI template-compatible Project 04 - Customer Funnel Conversion tables.
- Added `build/scripts/13_push_template_compat_model.ps1` to push the compatibility model into a specific PBIX Desktop session by file path.
- Created `output/dashboard_final.pbix` as the final native Power BI file.
- Validated the saved PBIX by offline export: 18,567 orders, 161,097 sessions, and `$1,558,769.34` net revenue.
- Wrote PBIX validation evidence to `qa/pbix_file_validation.json`.
