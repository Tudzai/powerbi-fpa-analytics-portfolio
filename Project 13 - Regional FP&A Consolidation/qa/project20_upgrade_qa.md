# Project 20 Style Upgrade QA

Run date: 2026-06-23

## Scope

Upgrade Project 13 native PBIX toward Project 20 standards: top slicer band, readable slicer labels, polished charts/tables, KPI cards with compact native sparklines, and a board-style 3-page story.

## Checks

| Check | Status | Evidence |
|---|---:|---|
| Backup created before edit | Pass | $backup |
| Generator updated | Pass | 	ools/build_native_pbix_assets.py now builds top filter bar, native KPI cards, mini sparklines, decision panels, chart/table polish |
| Layout JSON regenerated | Pass | uild/native_report_layout_project13.json |
| Final PBIX patched | Pass | output/dashboard_final.pbix, 5225657 bytes |
| Package validation | Pass | qa/pbix_native_report_validation.json; PowerBIPackager.Validate passed for output and final PBIX |
| Slicers top aligned | Pass | 8 slicers at y=86 and height=44; labels sized for dropdown readability |
| Sparkline implementation | Pass | 12 native combo-chart mini sparklines; no SVG queryRefs required in final PBIX layout |
| Missing visual fields | Pass | Static layout/model queryRef check found no missing refs |
| Page start | Pass | ctiveSectionIndex = 0 |
| Visual bottom bounds | Pass | Max visual bottom = 696 on 720px canvas |
| Desktop visual screenshot after final patch | Not rerun | Final verification was package/internal-layout validation. Earlier Power BI UI automation targeted the wrong window, so it was not used for the final patch. |

## Notes

- The source model still includes the Project 20-style SVG/ImageUrl measures for future use, and TOM push to a live Power BI session succeeded with 69 measures and 15 ImageUrl measures.
- Power BI Desktop did not persist TOM-only model changes back into the seed PBIX via Ctrl+S, so the final PBIX layout intentionally uses native KPI cards and native mini sparklines that work with the existing seed model.
- Final PBIX internal /Report/Layout was read back and confirmed to contain 3 pages, 130 visual containers, 8 top slicers, and zero *SVG* queryRefs.
