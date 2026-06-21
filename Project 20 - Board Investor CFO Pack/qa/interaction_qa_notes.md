# Interaction QA Notes

Slicer-focus polish built on the v58 checkpoint.

- Final product is a real PBIX rebuilt through TOM model push and native layout patch, not an HTML-only preview.
- Left rail now separates filter intent into `Global Lens` and `P&L Lens`.
- `Year` and `Scenario` are synced single-select dropdown slicers across all three pages.
- `Business Unit` and `Region` are synced multi-select dropdown slicers across all three pages.
- The four sync groups are present in the final PBIX layout: `global_year`, `global_scenario`, `global_bu`, and `global_region`.
- Compact rail controls use separate labels, accent markers, light control fill, and consistent 142x42 geometry.
- Direct PBIX verification confirms 12 sidebar slicers, 174 visual containers, and zero slicer metadata issues.
- Desktop capture validates the final PBIX opens and renders; Playwright QA validates overview, slicer metadata, and a full rail spec render.

Evidence:

- Direct PBIX verification: `qa/pbix_direct_verification_slicer_focus.json`
- Desktop capture: `qa/screenshots/project20_slicer_focus_desktop_full.jpg`
- Playwright QA: `output/playwright/project20_slicer_focus_qa.png`
- Full slicer rail spec: `output/playwright/project20_slicer_rail_spec.png`
