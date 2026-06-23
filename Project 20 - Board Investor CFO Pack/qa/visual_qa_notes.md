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

## v74 Signature Favicon Correction

- Scope is intentionally limited to the left-rail Signature mark after rollback requests.
- The final PBIX uses native Power BI shapes/text based on `C:\Users\Win\OneDrive\Codex\Portfolio\assets\favicon.svg`.
- The Signature no longer uses an `image` visual or `tableEx`, avoiding placeholder icons, scrollbars, and crop artifacts.
- Each report page now has 10 native shape layers plus one `A` textbox and one `TDAT` textbox, positioned within the sidebar bounds.
- The `T` is drawn with native bars so it stays visible and does not depend on textbox clipping behavior.

Evidence:

- Final PBIX: `output/dashboard_final.pbix`
- Snapshot: `output/dashboard_final_v74_signature_favicon_exact.pbix`
- Direct PBIX verification: `qa/pbix_direct_verification_v74_signature_favicon_exact.json`
- Desktop full capture: `output/playwright/project20_v74_signature_favicon_exact_full.png`
- Desktop Signature crop: `output/playwright/project20_v74_signature_favicon_exact_crop.png`
- Playwright QA page: `output/playwright/project20_v74_signature_favicon_exact_qa.html`
- Playwright QA screenshot: `output/playwright/project20_v74_signature_favicon_exact_qa.png`
