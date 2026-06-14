# Project 07 - Marketplace Seller Performance

Built from `BI_A2Z_Master_Prompt_v2.md`.

- Core KPIs: Seller GMV, fulfillment rate, cancellation rate, rating, stock availability, top/bottom sellers.
- Data: synthetic demo data, seed `7207`.
- Latest complete month: `2026-05`.
- Build mode: `computer_use_powerbi_desktop`.
- PBIX authoring mode: `COMPUTER_USE`.
- Computer Use requested: `True`.
- Computer Use status: `callable_via_computer_use_skill`.
- Complete BI file: `output/dashboard_final.pbix`.
- PBIX status: complete openable Power BI Desktop dashboard with 4 pages and 47 native visuals, using the researched `Marketplace Command Center` design.
- Open test: PASS in Power BI Desktop, window title `dashboard_final`.
- Visual QA: PASS in Power BI Desktop; cards, line chart, bar chart, seller tables, and page tabs render.
- Model QA: extracted and data-export validated with `pbi-tools`.
- PBIX pages: `01 Executive Cockpit`, `02 Seller Portfolio`, `03 Growth Drivers`, `04 Ops Risk`.
- Native visuals: 8 textboxes, 24 cards, 5 line charts, 6 bar charts, 4 tables.
- Visual design research: ecommerce/marketplace command-center patterns; applied theme and source notes in `docs/template_application_notes.md`.
- Supplemental interactive HTML: `output/dashboard_complete.html`.
- Preview gallery: `output/dashboard_preview.html` and `output/screenshots/`.
- PBIX openability QA: `qa/pbix_validation.json`.
- Theme QA: `qa/theme_application_validation.json`.

Rebuild:

```powershell
python "build\scripts\build_project7_v2.py"
powershell -NoProfile -ExecutionPolicy Bypass -File "build\scripts\08_push_project7_model_to_powerbi_desktop.ps1"
python "build\scripts\10_build_complete_dashboard.py"
$env:PROJECT7_ALLOW_DIRECT_PBIX_PATCH='1'
python "build\scripts\11_build_complete_pbix.py"
```

After rebuilding the complete PBIX, open `output/dashboard_final.pbix` in Power BI Desktop and save it once. The script removes stale `SecurityBindings` when the report layout changes; Desktop regenerates valid bindings on save.
