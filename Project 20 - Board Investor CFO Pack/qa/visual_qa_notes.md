# Visual QA Notes

v71 fixes the PBIX-rendered spacing and scrollbar issues called out by the user.

- Final product is a real PBIX rebuilt through TOM model push and native layout patch, not an HTML-only preview.
- KPI cards are expanded to `260x190`, use native layered visuals, and no longer use top-row tableEx SVG containers that caused internal scrollbars.
- KPI value cards have a wider numeric area and slightly smaller value font so `$36.7M`, `77.8%`, `$14.3M`, and `$376.7M` render without ellipses in Power BI Desktop.
- Sidebar signature is native shape/text, so the `AT` mark, `TDAT`, and `Finance Control` render without a nested scrollbar. The two right-side gray bars share the same x-axis and dimensions.
- Sidebar slicers remain compact `146x43` containers with no bad-height records in PBIX metadata.
- Current Lens is rebuilt from native shape/text/card visuals and no longer uses a tableEx SVG container.
- Playwright evidence is generated from a Power BI Desktop render captured from the actual `output/dashboard_final.pbix`.

Evidence:

- Direct PBIX verification: `qa/pbix_direct_verification_v71_kpi_fit_no_scroll.json`
- Desktop render capture: `output/playwright/project20_v71_pbix_final_full.png`
- Playwright QA evidence: `output/playwright/project20_v71_pbix_qa_evidence.png`
- Snapshot PBIX: `output/dashboard_final_v71_kpi_fit_no_scroll.pbix`
