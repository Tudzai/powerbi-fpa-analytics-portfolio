# Visual QA Notes

ZoomCharts Inventory-style Finance Control Tower v19 layout target: deep purple canvas, light neutral outspace, dark purple left sidebar, visible sidebar slicers, KPI dashboard cards with icon badges, DAX SVG decoration measures, stable drawn mini sparklines, progress bars, colored high/low/current markers, PY/YoY KPI footers, balanced gutter between sidebar and content, six rounded chart/table panels, and no note boxes. The official PBIX download was account-gated, so the public official preview asset was used to align proportions.

Final evidence:
- `qa/pbix_v19_aesthetic_validation.json`: PASS, with 0 `cardVisual`, 0 `lineChart`, 0 empty non-text visuals, and 5 ImageUrl SVG decoration measures.
- `qa/screenshots/pbi_v19_powerbi_capture.png`: Power BI Desktop screenshot shows KPI labels, mini trend panels, progress bars, and no visible `Fix this` / `See details` overlay.
