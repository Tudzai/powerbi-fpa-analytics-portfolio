# Project 20 Upgrade Handoff

Project path: `C:\Users\Win\OneDrive\Codex\Portfolio\BI\Project 15 - SaaS CFO Metrics`

Final target: `output/dashboard_final.pbix`

Current final status: upgraded PBIX rebuilt and checked in Power BI Desktop on 2026-06-23. `output/dashboard_final.pbix` is the upgraded final.

Upgrade approach:
- Preserve Project 15's SaaS CFO domain story, metric hierarchy, and light/navy finance mood.
- Reuse Project 20 as a pattern library for polish: left sidebar, compact slicers, four SVG KPI cards, Current Lens, decision chips, chart/table rhythm, and QA evidence.

Files/source changed by generator:
- `build/scripts/01_build_project.py`
- `build/native_report_layout_saas_cfo.json`
- `model/model.bim`
- `model/MEASURES.dax`
- `model/measure_map.json`
- `build/config/*.json`
- `docs/*`
- `qa/*`

PBIX rebuild route used:
1. Run `python build/scripts/01_build_project.py`.
2. Copy a known-good PBIX container to `output/dashboard_model_seed.pbix`.
3. Open exact `output/dashboard_model_seed.pbix` in Power BI Desktop Store App.
4. Run `build/scripts/02_push_model_bim_via_tom.ps1 -Port 58188 -PbiProcessId 24340` after confirming the seed process/workspace.
5. Save the seed in Desktop.
6. Run `build/scripts/03_apply_native_layout_to_pbix.ps1`.
7. Open/save/reopen exact `output/dashboard_final.pbix`.

QA evidence:
- `qa/project20_upgrade_verification.json`
- `qa/seed_model_push_via_tom.json`
- `qa/pbix_native_report_validation.json`
- `qa/pbix_final_validation.json`
- `qa/powerbi_desktop_evidence.json`

Known note:
- A transient Microsoft .NET Framework `Error creating window handle` dialog appeared during first final open while several unrelated Power BI instances were running. It was dismissed once; all three pages then rendered.
