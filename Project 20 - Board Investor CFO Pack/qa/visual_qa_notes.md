# Visual QA Notes

v72 rolls back the v71 KPI enlargement pass and focuses only on the sidebar Signature.

- Final product is a real PBIX patched through the native layout route, not an HTML-only preview.
- The Signature now uses a centered native favicon-style mark: dark navy rounded square, white `AT`, and two small blue/teal accent strokes.
- The adjacent `TDAT` / `Finance Control` text boxes were removed because they rendered as small overflow rectangles in Power BI Desktop.
- The old `Portfolio Signature SVG` tableEx visual is no longer used in the Signature area, so the logo does not create its own scrollbar.
- Direct PBIX verification confirms `signature_tableEx = 0`, `right_side_signature_visuals = 0`, `brand_textboxes = 0`, and `v71_kpi_geometry_260x190 = 0`.
- Playwright evidence is generated from a Power BI Desktop render captured from the actual `output/dashboard_final.pbix`.

Evidence:

- Direct PBIX verification: `qa/pbix_direct_verification_v72_signature_only.json`
- Desktop render capture: `output/playwright/project20_v72_signature_favicon_only_full.png`
- Playwright QA evidence: `output/playwright/project20_v72_signature_favicon_only_qa.png`
- Snapshot PBIX: `output/dashboard_final_v72_signature_favicon_only.pbix`
