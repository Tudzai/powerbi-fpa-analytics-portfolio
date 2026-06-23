# QA Checklist

Data QA: PASS

Metric QA: PASS at source/model generation level. SVG KPI measures are generated into `model/MEASURES.dax` and tagged as Image URL in `model/model.bim`.

Source Layout QA: PASS. See `qa/project20_upgrade_verification.json`; final source layout has 9 page-navigation action buttons and 32 table width rules.

Visual QA: PASS. Power BI Desktop rendered all 3 Project 15 pages from a uniquely named copy of the exact final PBIX; the Desktop-saved copy was copied back to `output/dashboard_final.pbix`. Evidence was recorded in `qa/powerbi_desktop_evidence.json`.

Interaction QA: PASS. Sidebar slicers are synced compact dropdowns, action-button page navigation is present, and Desktop accessibility exposed page-navigation controls.

File QA: PASS. TOM model push, native layout patch, Desktop save/copyback, file size/hash, final package readback, and final PBIX validation were recorded in `qa/pbix_final_validation.json`.

Evidence added: `qa/reconciliation.csv`, `qa/pbix_validation.json`, `data/data_dictionary.md`, and `qa/desktop_render_walkthrough_20260623.json`.
