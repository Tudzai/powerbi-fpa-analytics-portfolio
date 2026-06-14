# PBIX Build Runbook

1. Run `python build/scripts/build_project9.py` from the Project 09 - BNPL Credit Risk Provision root to regenerate data, model, native layout source, preview, and baseline QA files.
2. Copy a validated seed PBIX to `output/dashboard_model_seed.pbix`.
3. Open the exact seed PBIX in Power BI Desktop, or run `powerbi/launch_powerbi.ps1` after adjusting the target path if needed.
4. Run `build/scripts/12_push_model_bim_via_tom.ps1` to push `model/model.bim` into the live Desktop session.
5. Save the seed PBIX in Power BI Desktop.
6. Run `build/scripts/13_apply_native_layout_to_pbix.ps1` to write the native report layout and produce `output/dashboard_final.pbix`.
7. Open `output/dashboard_final.pbix` in Power BI Desktop and verify the three pages render without visual errors.
8. Run pbi-tools extract and export-data into `qa/pbix_extract_final` and `qa/export_data_final` for final validation.

Current final QA status: passed.
