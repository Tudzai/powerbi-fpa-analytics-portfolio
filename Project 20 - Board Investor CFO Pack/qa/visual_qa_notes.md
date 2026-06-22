# Visual QA Notes

## v65 Alignment + Current Lens QA

Follow-up polish for the user-reported sidebar rectangles, missing Current Lens, and uneven KPI distribution.

- Removed the separate action button overlay from sidebar navigation; the nav shape itself now carries the page link.
- Restored `Current Lens` as a larger `154x58` dynamic SVG card with `16px` horizontal and vertical render budget.
- Widened the four KPI cards to `255px` and reduced the gap to `12px`; the KPI strip now runs from `x=204` to `x=1260`.
- Increased sidebar label textbox heights to avoid internal text clipping/scroll artifacts.
- Restored the native `FC / Finance Control` signature and removed `TDAT`/Portfolio Signature canvas artifacts from the final PBIX layout.

Evidence:

- Final PBIX direct verification: `qa/pbix_direct_verification_v65_alignment_lens.json`
- Playwright sanity screenshot from generated preview: `output/playwright/project20_v65_preview_full.png`

Note:

- Final acceptance is based on direct inspection of `Report/Layout` inside `output/dashboard_final.pbix`. Power BI Desktop was used during QA, but the final PBIX was patched after Desktop save because Desktop rewrote the sidebar signature textbox back to `TDAT`; the final direct verification confirms the shipped PBIX layout is clean.
