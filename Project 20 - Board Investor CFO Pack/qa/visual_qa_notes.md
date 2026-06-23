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

## V77 Tab Layout Sync

Scope: sync the user-adjusted `Performance` layout into the following tabs without rebuilding the model or overwriting the manual layout source.

- Used `output/dashboard_final.pbix` as the source of truth and restored from `tmp/dashboard_final_before_v77_tab_sync.pbix` after finding a full JSON reserialize made Power BI reject the file.
- Patched only section-scoped visual coordinates in `Report/Layout`: `Current Lens`, four KPI card image visuals, and the top chart row for `Cash Plan` and `Risk & Valuation`.
- Removed stale `SecurityBindings` after the PBIX zip edit so Power BI Desktop opens the final file normally.
- Verified the final PBIX directly: both target tabs match the adjusted `Performance` slots for Lens, KPI row, and top chart row.
- Opened `dashboard_final.pbix` in Power BI Desktop and captured all three tabs for visual QA.

Validation:

- Final PBIX: `output/dashboard_final.pbix`
- Snapshot: `output/dashboard_final_v77_tabs_synced.pbix`
- Pre-patch backup: `tmp/dashboard_final_before_v77_tab_sync.pbix`
- Direct PBIX verification: `qa/pbix_direct_verification_v77_tabs_synced.json`
- Performance capture: `output/playwright/project20_v77_performance_full.jpg`
- Cash Plan capture: `output/playwright/project20_v77_cash_plan_full.jpg`
- Risk & Valuation capture: `output/playwright/project20_v77_risk_valuation_full.jpg`
- Playwright QA page: `output/playwright/project20_v77_tabs_synced_qa.html`
- Playwright QA screenshot: `output/playwright/project20_v77_tabs_synced_qa.png`
- Playwright snapshot: `output/playwright/project20_v77_tabs_synced_snapshot.txt`
