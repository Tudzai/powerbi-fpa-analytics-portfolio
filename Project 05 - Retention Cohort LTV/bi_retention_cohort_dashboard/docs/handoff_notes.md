# Handoff Notes

## Output

- Final PBIX: `output/dashboard_final.pbix`
- Current final status: complete. Power BI Desktop opened `output/dashboard_final.pbix`, rendered all four native pages, and saved the final PBIX.
- Build package: `output/Project5_Retention_Cohort_BuildPackage.zip`
- Preview HTML: `output/dashboard_preview.html`
- Preview PDF: `output/exports/dashboard_preview.pdf`
- Screenshots: `output/screenshots/`

## Source

- Raw data: `data/raw/`
- Prepared data: `data/prepared/`
- Source summary: `data/source_summary.json`
- Source type: fixed-seed synthetic portfolio data, not company production data.

## Tool Environment

- Environment check: `_agent/environment_check.md`
- Power BI launch check: `_agent/powerbi_launch_check.md`
- PBIX authoring decision: `_agent/pbix_authoring_decision.md`

## PBIX Authoring Strategy

- Authoring mode: native PBIX layout patch plus Power BI Desktop verification.
- Power BI source available: `powerbi/pbip/Project5_Retention_Cohort/Project5_Retention_Cohort.pbip`
- pbi-tools role: environment/source support only; pbi-tools PBIX compile is not a full import-model PBIX route.
- PBIX final: `output/dashboard_final.pbix` contains 4 native report pages and was saved from Power BI Desktop after render QA.

## Subagent Execution

- Requested mode: TRUE/AUTO
- Execution mode: real subagents
- Notes: manager, data/KPI, Power BI, and UI/UX workstreams were used for independent checks.
- Subagent plan: `_agent/subagent_plan.md`

## Pages

- Page 1: Lifecycle Overview - new vs returning users, repeat purchase, revenue, churn signals.
- Page 2: Monthly Cohort Retention - cohort heatmap and retention horizons.
- Page 3: LTV & Revenue Cohorts - cumulative LTV and value drivers.
- Page 4: Churn Signal & Winback - at-risk users and recommended actions.

## KPI Definitions

- See `model/metric_definitions.md`
- See `model/dax_measures.md`

## Refresh Instructions

Open Power BI Desktop, open the PBIP under `powerbi/pbip/Project5_Retention_Cohort`, refresh the CSV-backed model, apply theme `build/config/theme.json`, then save as `output/dashboard_final.pbix`.

## Rebuild Instructions

See `docs/rebuild_guide.md` and `powerbi/notes/desktop_ui_runbook.md`.

## QA Status

- Data QA: PASS
- Metric QA: PASS
- Visual QA: PASS - all 4 native Power BI pages rendered
- Interaction QA: PASS - report tabs and slicer surfaces are accessible
- File QA: PASS - PBIX exists after package validation and Desktop save

## Known Issues

- PBIP/PBIT and screenshots remain supplemental build artifacts; the final deliverable is the real PBIX in `output/dashboard_final.pbix`.
