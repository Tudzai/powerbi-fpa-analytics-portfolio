# Visual QA Notes

v66 focuses on the sidebar slicer alignment and the Current Lens card fit.

- Final product is a real PBIX rebuilt through the TOM model push and native layout patch route, not an HTML-only preview.
- All 12 global sidebar slicers across the 3 pages now use a `150x40` dropdown container, centered item alignment, and `8.1` pt item typography.
- Current Lens is enlarged to a `164x62` visual frame with a `154x52` SVG image, so the lens content has more breathing room inside the lower sidebar.
- Sidebar signature remains the compact `FC` / `Finance Control` mark; the previous `TDAT`, `AT Signature`, and Portfolio Signature visual artifacts are absent from the final PBIX layout.
- The final PBIX model was re-saved through TOM before the final layout patch, and the extracted PBIX model confirms `Lens Summary SVG` now uses `width='154' height='52' viewBox='0 0 154 52'`.

Evidence:

- Direct PBIX verification: `qa/pbix_direct_verification_v66_slicer_lens_fit.json`
- Model push verification: `qa/seed_model_push_via_tom.json`
- Playwright visual crop: `output/playwright/project20_v66_slicer_lens_preview.png`
- Snapshot PBIX: `output/dashboard_final_v66_slicer_lens_fit.pbix`
