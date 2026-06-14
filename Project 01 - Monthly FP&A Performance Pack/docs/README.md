# Monthly FP&A Performance Pack

Power BI portfolio project for Automation Reporting / FP&A Dashboard.

## Goal

Build a management reporting pack that helps FP&A review monthly performance:

- Actual vs Budget vs Forecast.
- Revenue, Gross Margin, EBITDA, Opex, Cash.
- Variance by business unit, product, region, customer, and department.
- Budget to Actual EBITDA waterfall.
- 12-month trends.
- Commentary: What happened, Why, What next.
- Drill-down from company level to BU, product, customer, and department.

## Status

Build-ready package complete.

PBIX final status: pending Desktop build and QA. Power BI Desktop Store app is installed, but `output/dashboard_final.pbix` has not yet been authored and visually tested.

Expected final deliverable after desktop build:

`output/dashboard_final.pbix`

## Folder Guide

- `data/raw/`: generated source sample data. Do not edit manually.
- `data/prepared/`: star-schema CSVs for Power BI import.
- `model/`: metric definitions, DAX, relationship map, semantic notes.
- `build/scripts/`: repeatable data and validation scripts.
- `build/config/`: theme, Power Query, page map, visual map.
- `powerbi/`: PBIX build instructions.
- `qa/`: reconciliation, QA checklist, visual/interaction notes.
- `docs/`: handoff, changelog, issue log, delivery plan.
- `output/`: final PBIX target and build status.

## Rebuild Commands

Run from this project folder:

```powershell
& 'C:\Users\Win\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' 'build\scripts\00_generate_sample_raw.py'
& 'C:\Users\Win\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' 'build\scripts\01_profile_data.py'
& 'C:\Users\Win\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' 'build\scripts\02_prepare_data.py'
& 'C:\Users\Win\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' 'build\scripts\03_validate_prepared_data.py'
& 'C:\Users\Win\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' 'build\scripts\04_build_or_update_model.py'
& 'C:\Users\Win\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' 'build\scripts\05_validate_output.py'
& 'C:\Users\Win\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' 'build\scripts\06_render_static_preview.py'
```

## Power BI Build

Follow `powerbi/PBIX_build_instructions.md`.

Static preview:

`output/exports/fpa_dashboard_preview.html`

This preview is only a layout/theme aid and does not replace the final PBIX.

After building, save:

- `output/dashboard_v01.pbix`
- `output/dashboard_final.pbix` after QA passes

## Portfolio Talking Points

- Shows FP&A management reporting thinking, not only chart design.
- Uses scenario modeling for Actual/Budget/Forecast.
- Separates P&L, Opex department, cash balance, bridge, and commentary facts.
- Protects cash balance from incorrect time aggregation.
- Includes data profiling, reconciliation, issue log, changelog, and QA gates.
