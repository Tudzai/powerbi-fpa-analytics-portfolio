# Visual QA Notes

Interactive-data update built on the v58 checkpoint requested by the user.

- Final product is a real PBIX rebuilt through TOM model push and native layout patch, not an HTML-only preview.
- Data was adjusted to make Scenario, Year, BU, and Region interactions move KPI cards, charts, and sparklines more clearly while preserving the CFO pack meaning.
- Base Case still anchors the familiar board story: May 2026 revenue is about `$36.7M`, gross margin is `77.8%`, EBITDA is about `$14.3M`, and cash is about `$376.7M`.
- Downside now creates visible liquidity pressure: May 2026 runway drops to `18.5x` and funding need is about `$13.9M`.
- Playwright evidence is generated from a Power BI Desktop render crop.

Evidence:

- Data interaction QA: `qa/data_interaction_variation_check.json`
- Direct PBIX verification: `qa/pbix_direct_verification_interactive_data.json`
- Desktop capture: `qa/screenshots/project20_interactive_data_desktop_full.jpg`
- Playwright crop: `output/playwright/project20_interactive_data_desktop_crop.png`
