# PBIX Build Status

Status: BLOCKED_PBIX_PERSISTENCE

`output/dashboard_final.pbix` exists as a patched seed/container, but it is not a validated final PBIX. The live Power BI Desktop session on port `56532` contains the Project 16 model and the 3-tab report layout, but Desktop did not persist the live DataModel to the PBIX package on disk.

Validation evidence:
- Live Desktop export after model push: `qa/live_export_after_model_push` contains Project 16 tables.
- Live model extract: `qa/live_pbixproj_from_session/Model/database.json` contains 8 tables, 5 relationships, and 61 measures.
- Offline `output/dashboard_final.pbix` export after Save attempt: `qa/pbix_export_data_final_after_save` still contains seed tables (`Calendar`, `Prices`, `Products`, `Sales`, `Year`).
- Supplemental PBIT schema package: `output/dashboard_project16_model_schema.pbit` extract-validates with the Project 16 model.

Next retry path:
1. Open a clean Power BI Desktop workspace with unrelated Power BI sessions closed.
2. Open `output/dashboard_project16_model_schema.pbit`.
3. Refresh/apply local CSV sources from `data/prepared`.
4. Save As `output/dashboard_final.pbix`.
5. Validate with `pbi-tools export-data -pbixPath output/dashboard_final.pbix`.
