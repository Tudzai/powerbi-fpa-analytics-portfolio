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

## V76 SVG Fit Correction

Scope: Signature SVG, KPI Card SVG sizing, and Current Lens SVG sizing/backing.

- Signature: removed the visible white top line by removing inner white-line rectangles from the SVG source and adding a small same-sidebar-color layout mask over the tableEx header artifact.
- KPI cards: increased generated SVG canvas to `252x158` and tableEx image size to `249x158` inside each `255x164` card frame.
- Current Lens: increased generated SVG canvas to `166x76`, tableEx image size to `166x76` inside the `170x80` frame, and matched the outside backing to sidebar `#250642` so the pale-purple edge no longer shows.

Validation:

- Final PBIX: `output/dashboard_final.pbix`
- Snapshot: `output/dashboard_final_v76_svg_fit.pbix`
- Direct PBIX verification: `qa/pbix_direct_verification_v76_svg_fit.json`
- Desktop full capture: `output/playwright/project20_v76_svg_fit_full.png`
- Signature crop: `output/playwright/project20_v76_svg_fit_signature_crop.png`
- KPI crop: `output/playwright/project20_v76_svg_fit_kpi_crop.png`
- Playwright QA page: `output/playwright/project20_v76_svg_fit_qa.html`
- Playwright QA screenshot: `output/playwright/project20_v76_svg_fit_qa.png`
