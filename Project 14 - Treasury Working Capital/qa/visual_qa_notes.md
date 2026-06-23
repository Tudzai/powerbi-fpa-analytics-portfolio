# Visual QA Notes

Status: PASS
Latest Desktop evidence: `output/screenshots/pbix_project20_upgrade_dynamic_svg_v21.png`

## Desktop PBIX Check

- Exact final PBIX was rebuilt at 2026-06-23 21:46:54 +07:00 and opened in Power BI Desktop as `dashboard_final`.
- Power BI title bar shows last saved at 9:46 PM.
- KPI row renders as dynamic model-bound SVG cards through `tableEx`, not static text/shape tiles.
- Each visible KPI card includes label, current value, PY/delta footer, semantic color, and sparkline with reference band/markers.
- Left-rail slicers render as compact dropdowns; visible labels do not lose text on the command-center page.
- Chart panels and detail tables render with compact titles/subtitles, light panel styling, and subtle shadows.

## Supplemental HTML QA

HTML visual QA passed at 2026-06-23T10:54:59.561Z. Desktop and mobile HTML screenshots remain in `output/screenshots/` as supplemental preview evidence.
