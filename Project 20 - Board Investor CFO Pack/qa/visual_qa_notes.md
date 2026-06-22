# Visual QA Notes

v67 fixes the visible signature issue after the user reported that the v66 change was hard to see in Power BI Desktop.

- Final product is a real PBIX patched through the native layout route, not an HTML-only preview.
- The sidebar signature now uses a larger `58x52` logo block, wider `FC` text box, and `15.5pt` `FC` typography so the mark no longer renders like a clipped single letter.
- The `Finance Control` label was shifted right to avoid crowding the larger mark.
- The v66 slicer and Current Lens improvements are preserved: all 12 sidebar slicers are `150x40` with centered item alignment, and Current Lens remains `164x62` with a `154x52` SVG.
- File Explorer can be misleading because old snapshots such as `dashboard_final_v65_alignment_lens.pbix` may sit near the final file; use `output/dashboard_final.pbix` or the v67 snapshot for review.

Evidence:

- Direct PBIX verification: `qa/pbix_direct_verification_v67_signature_visible.json`
- Desktop render crop: `output/playwright/project20_v67_signature_crop.jpg`
- Playwright QA crop: `output/playwright/project20_v67_signature_slicer_preview.png`
- Snapshot PBIX: `output/dashboard_final_v67_signature_visible.pbix`
