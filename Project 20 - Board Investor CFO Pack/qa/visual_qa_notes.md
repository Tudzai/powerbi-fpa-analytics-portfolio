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

## V75 Signature Source Favicon Correction

The signature area now uses the actual source favicon asset from `assets/favicon.svg`, which matches `C:\Users\Win\OneDrive\Codex\Portfolio\assets\favicon.svg` with SHA256 `9A20197C48B172C5DB4495CD61D15ED1E0246C652EE7DBBAC7CA2D883924D62C`.
The build script reads that SVG file and embeds it into the semantic model as the `Portfolio Signature SVG` ImageUrl measure, rendered through a native `tableEx` visual in the PBIX.
The `TDAT` label remains as a separate editable text box beside the favicon.

This replaces the earlier recreated/native-shape signature attempt. The legacy rectangle approximation and generated `assets/favicon_signature.png` file were removed.

Validation:

- Final PBIX: `output/dashboard_final.pbix`
- Snapshot: `output/dashboard_final_v75_signature_source_favicon.pbix`
- Direct PBIX verification: `qa/pbix_direct_verification_v75_signature_source_favicon.json`
- Desktop full capture: `output/playwright/project20_v75_signature_source_favicon_full.png`
- Desktop signature crop: `output/playwright/project20_v75_signature_source_favicon_crop.png`
- Playwright QA page: `output/playwright/project20_v75_signature_source_favicon_qa.html`
- Playwright QA screenshot: `output/playwright/project20_v75_signature_source_favicon_qa.png`
