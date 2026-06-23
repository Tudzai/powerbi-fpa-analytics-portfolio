# Project 20 Style Upgrade QA

Date: 2026-06-23

Checks performed:
- Read current native layout source and verified page/visual counts.
- Backed up PBIX, layout JSON, and build script before modification.
- Regenerated `build/native_report_layout_project16.json`.
- Patched the regenerated report layout into `output/dashboard_final.pbix`.
- Direct-read `Report/Layout` from the PBIX and confirmed top slicer coordinates on all pages.
- Patched and direct-read `Report/Layout` from `output/dashboard_project16_model_schema.pbit`.
- Regenerated supplemental screenshots with the top slicer bar visible.

Result:
- Layout source QA: PASS.
- PBIX report-layout readback QA: PASS.
- PBIT report-layout readback QA: PASS.
- Screenshot preview QA: PASS.
- Desktop click interaction QA: PENDING, blocked by the existing final PBIX persistence workflow.
- Final PBIX DataModel QA: STILL BLOCKED; see `qa/pbix_final_validation.json`.

Top slicer contract:
- Page 1 and 2: Month, Plant, Product Line, Line.
- Page 3: Month, Plant, Product Line, Scenario.
- Coordinates: `x=24/336/648/960`, `y=72`, `width=296`, `height=52`.
