# Project 20 Upgrade QA

QA date: 2026-06-23
Status: PASS
Final PBIX: `output/dashboard_final.pbix`
Desktop evidence: `output/screenshots/pbix_project20_upgrade_dynamic_svg_v21.png`
Structural evidence: `qa/project20_upgrade_verification.json`
Package evidence: `qa/pbix_final_validation.json`

## Requirement Checks

| Requirement | Result | Evidence |
|---|---:|---|
| Final PBIX exists and is validated | PASS | `qa/pbix_final_validation.json` reports the final PBIX and PowerBIPackager validation passed. |
| Project 20-style page structure | PASS | 3 decision-flow pages: Treasury Command Center; Working Capital Control; Forecast, FX & Risk. |
| Four KPI cards per page | PASS | `qa/project20_upgrade_verification.json` reports 4 dynamic SVG KPI cards on each page. |
| Sparklines / mini trends | PASS | 12 ImageUrl DAX KPI card measures render through `tableEx`; visible Desktop evidence shows sparkline bands, trend lines, and markers. |
| Compact slicers without clipped labels | PASS | 12 slicers total; each page has 4 compact dropdown slicers, 136x38 left-rail layout, title/header text configured at compact font sizes. |
| Current Lens and decision chips | PASS | One Current Lens and one decision-chip visual per page verified structurally. |
| Chart polish | PASS | Each page has 3 top chart slots; chart shells use short titles/subtitles, restrained palette, and metric-specific visual types. |
| Table polish | PASS | 9 detail table visuals use subtle header fill, row banding, compact typography, row padding, borders, and finance panel styling. |
| No placeholder/card scrollbar issue | PASS | Fresh Desktop screenshot shows SVG KPI cards rendering as report content, not image placeholders. |
| No blank/report-only/model-only output | PASS | Final PBIX contains 111 native visual containers across 3 pages with 18 tables, 17 relationships, and 47 measures. |

## Notes

- The earlier static native KPI fallback has been replaced. Final KPI cards are dynamic model-bound `tableEx` visuals backed by DAX ImageUrl SVG measures.
- Runtime slicer click testing is evidenced by Desktop screenshot and structural layout checks. Explicit slicer sync-group metadata was not found; repeated left-rail slicers are present on every page and configured as compact dropdowns.
- Project 20 purple was not copied. The final report uses a treasury-specific muted finance palette documented in `docs/design_research.md`.
