# PBIX Build Status

Status: complete. Aesthetic refresh complete.

Final PBIX:

- `C:\Users\Win\OneDrive\Codex\Portfolio\BI\Project 10 - AML Fraud Monitoring\output\dashboard_final.pbix`

The AML / Fraud Monitoring Command Center now has a validated native PBIX final with a dark command-center aesthetic pass. The earlier failure was caused by patching a PBIR-style report layout into the legacy PBIX `Report/Layout` stream. Power BI Desktop could open the model but failed to load the report canvas. The final build was repaired by generating a legacy visual container layout, patching it into a clean AML model PBIX, then restyling the report with a Power BI-safe dark visual system.

Final contents:

- 3 report pages:
  - Fraud & Compliance Overview
  - Alert & Customer Risk Deep Dive
  - Case SLA & Rule Governance
- 52 visual containers across cards, slicers, combo charts, bar/column charts, donut chart, tables, dark header accents, and section structure.
- AML semantic model with 13 tables, 18 relationships, and 26 measures.
- Deterministic synthetic data generated with seed `20260611`.
- Dark control-room canvas, light KPI tiles, semantic risk colors, compact header, and dark analytical panels.

Validation completed:

- `PowerBIPackager.Validate` passed.
- Power BI Desktop open-check passed for the exact final PBIX.
- `pbi-tools export-data` passed from the final PBIX and returned expected AML row counts.
- `pbi-tools extract` passed from the final PBIX.
- Screenshot evidence captured at `qa\screenshots\dashboard_final_pbix_dark_aesthetic_final.png`.

Supplemental artifacts:

- `output\dashboard_final.html` - interactive HTML dashboard preview.
- `output\dashboard_final.pbip` - PBIP shortcut to the repaired Power BI project.
- `output\dashboard_final_project\AML_Fraud_Monitoring_Command_Center.pbip` - repaired Power BI project package.
- `build\legacy_report_layout_aml.json` - final legacy PBIX report layout.
- `docs\aesthetic_redesign_brief.md` - visual system guidance created during the agent-led aesthetic pass.
- `build\scripts\13_apply_legacy_pbix_report.ps1` - script used to apply and validate the final legacy layout.
