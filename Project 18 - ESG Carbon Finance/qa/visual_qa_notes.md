Native layout JSON defines four pages with slicers, SVG-backed KPI cards, line/bar charts, clickable page navigation, and TableEx image cards.

Fresh Desktop QA passed on 2026-06-30 19:02 +07:00 for `output/dashboard_final.pbix` SHA256 `DDD78E1286BEB961AD744839C2356E8FB7D2AD20F187D68F9083AA6D964D3C0D`.

Evidence:
- Full-canvas screenshot: `output/screenshots/project18_v39_dynamic_table_cards_full.png`
- Canvas crop: `output/screenshots/project18_v39_dynamic_table_cards_canvas_crop.png`
- Bottom table crop: `output/screenshots/project18_v39_dynamic_table_cards_bottom_crop.png`
- Dynamic table-card DAX QA: `qa/dynamic_table_cards_slicer_qa.json`
- `build/scripts/04_validate_output.py` release gates all pass, including `dynamic_table_cards_no_static_rows_pass` and `dynamic_table_cards_slicer_sensitive_pass`.
