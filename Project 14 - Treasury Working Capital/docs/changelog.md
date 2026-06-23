# Changelog

- 2026-06-23T17:08:30: Created Project 14 treasury working-capital BI package with 3-tab design, synthetic data, semantic model, HTML preview, and native PBIX build scaffolding.
- 2026-06-23T17:51:24: Upgraded Project 14 to Project 20 cockpit style. Added 17 new KPI/lens/chip measures, renamed the measure table to `KPI_Measures`, and validated the first native PBIX build through PowerBIPackager plus Desktop screenshot QA.
- 2026-06-23T21:46:54: Rebuilt the final PBIX with dynamic model-bound `tableEx` SVG KPI cards instead of the temporary static native KPI fallback. Final validation now reports 111 native visual containers, including 12 dynamic SVG KPI cards, 12 slicers, 9 detail tables, 3 lens visuals, and 3 decision-chip visuals.
