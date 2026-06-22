# Visual QA Notes

v68 fixes the "khong thay thay doi" issue by patching the actual `output/dashboard_final.pbix` while the old PBIX was closed and unlocked.

- Final product is a real PBIX patched through the native layout route, not an HTML-only preview.
- Sidebar signature now uses the portfolio `AT` SVG mark plus `TDAT` and `Finance Control`; the old `FC` text run is removed.
- The sidebar slicers are tightened to `146x36`, remain center-aligned in PBIX metadata, and leave more room for Current Lens.
- Current Lens is enlarged to a `170x80` visual container with `152x62` image sizing so it renders without its own scrollbar.
- KPI card containers are expanded to `255x164`, starting at `y=50`, leaving a tighter `12px` gap before the chart row.
- Playwright evidence is generated from a Power BI Desktop render captured from the actual PBIX.

Evidence:

- Direct PBIX verification: `qa/pbix_direct_verification_v68_signature_tdat_lens_kpi.json`
- Desktop render capture: `output/playwright/project20_v68_computer_use_full.png`
- Playwright QA evidence: `output/playwright/project20_v68_pbix_qa_evidence.png`
- Snapshot PBIX: `output/dashboard_final_v68_signature_tdat_lens_kpi.pbix`
