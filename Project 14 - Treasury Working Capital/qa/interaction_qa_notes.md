# Interaction QA Notes

Status: PASS with one documented limitation.

## Checked

- HTML filters cover Region, Entity, Scenario, and Forecast Week.
- Native Power BI slicer inventory is documented in `build/config/slicer_map.json`.
- Final native layout contains 12 slicers total: 4 compact left-rail dropdown slicers on each of the 3 pages.
- Slicer layout is configured at 136x38 with compact title/header/item typography, visible white control backgrounds, border radius, and left-rail alignment to reduce clipped text risk.
- Fresh Desktop screenshot `output/screenshots/pbix_project20_upgrade_dynamic_svg_v21.png` confirms the command-center slicer labels are visible after the dynamic SVG KPI rebuild.
- Slicers are model-bound and placed above the dark sidebar background layer by z-order in the generated layout.
- Page navigation is visible in the left rail. In Power BI Desktop edit mode, action-style navigation requires Ctrl+Click; in reading mode/Service, normal click applies.

## Limitation

Explicit native slicer sync-group metadata was not found in `build/native_report_layout_project14.json`. The report repeats the global/lens slicer set on each page and validates slicer presence, text sizing, and layering structurally. Cross-page sync behavior should be manually spot-checked in Power BI Desktop if published interaction parity is required.
