# Visual QA Notes

Signature-only correction built after rolling back the v71 KPI-card enlargement.

- Final product is a real PBIX rebuilt through TOM model push and native layout patch, not an HTML-only preview.
- Scope is intentionally limited to the left-sidebar Signature block.
- The Signature now uses native Power BI shapes/text: a compact favicon-style `AT` logo plus a separate `TDAT` wordmark.
- The old scroll-prone Signature table visual is removed; direct PBIX verification reports `signature_tableEx = 0`.
- The old overflowing `Finance Control` Signature textbox is removed; direct PBIX verification reports `finance_control_textboxes = 0`.
- The `AT` and `TDAT` textboxes are sized to fit without horizontal or vertical scroll; direct PBIX verification reports `at_textboxes_fit = 1` and `tdat_textboxes_fit = 1`.
- KPI geometry remains rolled back from v71; direct PBIX verification reports `v71_kpi_geometry_260x190 = 0`.

Evidence:

- Direct PBIX verification: `qa/pbix_direct_verification_v73_signature_tdat_fit.json`
- Power BI Desktop render: `output/playwright/project20_v73_signature_tdat_fit_full.png`
- Playwright evidence page: `output/playwright/project20_v73_signature_tdat_fit_qa.html`
- Playwright evidence screenshot: `output/playwright/project20_v73_signature_tdat_fit_qa.png`
- PBIX snapshot: `output/dashboard_final_v73_signature_tdat_fit.pbix`
