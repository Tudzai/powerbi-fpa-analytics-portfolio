# Project 18 Visual Product QA

Status: PASS after v39 dynamic table-card fix
Checked at: 2026-06-30T19:02:14+07:00
PBIX SHA256: DDD78E1286BEB961AD744839C2356E8FB7D2AD20F187D68F9083AA6D964D3C0D

## Evidence

- Full Desktop evidence: `output/screenshots/project18_v39_dynamic_table_cards_full.png`
- Canvas crop: `output/screenshots/project18_v39_dynamic_table_cards_canvas_crop.png`
- Bottom table/chart crop: `output/screenshots/project18_v39_dynamic_table_cards_bottom_crop.png`
- Dynamic DAX evidence: `qa/dynamic_table_cards_slicer_qa.json`

## Fixed Issues

- Slicer labels are visible and no longer clipped.
- Current Lens is in the dark header, enlarged, and does not show a white header strip.
- Current Lens Scope context now shows `All BU | All Scopes | All Prices` without the Carbon cost chip covering the text.
- Scope context has a fixed SVG clip region before the Carbon cost chip, and the validator now checks that no-overlap contract.
- Page navigation is larger and generated with clickable internal page links.
- KPI row is reduced to 4 cards, widened to 300 px each, and uses larger values with visible sparklines.
- Main chart area starts at y=315 or lower.
- Executive Detail was rebuilt as a dynamic SVG-backed TableEx card to remove table scrollbars and grey artifacts.
- Supplier Risk, Abatement Action Queue, and Risk Action Queue were also converted from static Python snapshot rows to DAX-driven SVG tables.
- Table cards now have header badges, rounded row surfaces, status pills, and numeric microbars for tCO2e/cost/intensity/ROI impact.
- The validator now checks `table_card_polish_pass`, `dynamic_table_cards_no_static_rows_pass`, and `dynamic_table_cards_slicer_sensitive_pass` so the report cannot pass with a plain native scrolling table or static table snapshot.
- Dynamic table-card QA passed across default, APAC, EMEA, Scope 3, Logistics, and stress-price states.
- No duplicate Current Lens card is visible inside the canvas.
- No selected resize handles are visible in the final Desktop capture.

## Remaining Watch Items

- The full screenshot includes the Power BI Desktop authoring chrome and panes, but the report canvas itself is clean.
- Future QA should always capture the full report canvas with Fit to page and DWM/DPI-aware screenshot logic before marking release pass.
