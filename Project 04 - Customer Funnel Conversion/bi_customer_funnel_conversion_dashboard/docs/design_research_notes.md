# Design Research Notes

## Sources Reviewed

- Microsoft Learn: dashboard design tips for clean, uncluttered, important-information-first Power BI dashboards.
- ZoomCharts template gallery: executive KPI and interactive report gallery patterns.
- Supermetrics marketing dashboard examples: paid media, ecommerce, campaign, device, spend, revenue, and conversion pattern coverage.
- Catchr Power BI design best practices: KPI-to-trend-to-breakdown hierarchy, grid alignment, consistent spacing, and concise titles.
- Tabular Editor KPI card guide: KPI cards as the first visible decision layer.

## Applied Template Direction

Template name: `Growth Command Center v2`

Design decisions:

- Use a persistent left rail for navigation and slicers.
- Put KPI cards first, with accent colors and small context labels.
- Replace generic titles with insight-oriented titles.
- Keep the main funnel as the visual center of page 1.
- Add a leakage watchlist to make the largest drop-offs obvious.
- Split diagnostics into focused operational pages: segment, category, and marketing efficiency.
- Use a mixed but restrained palette: cyan, teal, amber, violet, rose, blue, and green.
- Keep visual containers at 8px radius and avoid decorative background blobs.

## Files Updated

- `output/dashboard.html`
- `output/exports/customer_funnel_dashboard_preview.html`
- `build/scripts/06_render_executive_preview.py`
- `build/config/theme.json`
- `build/config/page_map.json`
- `build/config/visual_map.json`
- `output/screenshots/`
