# Visual QA Notes

Interactive-data update built on the v58 checkpoint requested by the user.

- Final product is a real PBIX rebuilt through TOM model push and native layout patch, not an HTML-only preview.
- Data is tuned so Scenario, Year, BU, and Region interactions move KPI cards, charts, and sparklines more clearly while preserving the CFO pack meaning.
- Base Case still anchors the familiar board story: May 2026 revenue is about `$36.7M`, gross margin is `77.8%`, EBITDA is about `$14.3M`, and cash is about `$376.7M`.
- Downside creates visible liquidity pressure: May 2026 runway drops to `18.5x` and funding need is about `$13.9M`.
- Playwright evidence is generated from a Power BI Desktop render crop.

Evidence:

- Data interaction QA: `qa/data_interaction_variation_check.json`
- Direct PBIX verification: `qa/pbix_direct_verification_interactive_data.json`
- Desktop capture: `qa/screenshots/project20_interactive_data_desktop_full.jpg`
- Playwright crop: `output/playwright/project20_interactive_data_desktop_crop.png`

## v64 Scroll-Fix QA

Focused fix for the user-reported visual polish issues: uneven rectangles, internal scrollbars in chips/KPI cards/slicers, unclear signature, oversized slicer frames, and the Board KPI Details table not fitting its panel.

- Replaced the signature SVG table visual with native shapes/text so the logo is crisp and cannot produce a scrollbar.
- Removed the Lens Summary mini table from the sidebar because its container was too small and added visual clutter.
- Reduced slicer dropdown height to `38px` and tightened the sidebar lens grouping so the filter rail feels balanced.
- Removed the rectangular value backplate behind KPI main values, then resized KPI SVG table images to keep `32px` width and `28px` height breathing room inside each KPI card.
- Enlarged decision-chip visual containers to `544x60` while keeping chip SVG image content at `500x32`, leaving `44px` horizontal and `28px` vertical budget to avoid internal scrollbars.
- Increased the Board KPI Details table panel height and tuned table row padding, header size, value size, and sparkline column width so the table fits the shape more deliberately.

Evidence:

- Direct PBIX verification: `qa/pbix_direct_verification_v64_scrollfix.json`
- Desktop full capture: `qa/screenshots/project20_v64_scrollfix_desktop_full.jpg`
- Playwright chip crop: `output/playwright/project20_v64_chips_crop.png`
- Playwright KPI crop: `output/playwright/project20_v64_kpi_crop.png`
- Playwright sidebar crop: `output/playwright/project20_v64_sidebar_crop.png`
