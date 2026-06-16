# Rebuild Guide

1. Run `python build/scripts/01_build_project20.py`.
2. Copy a valid seed PBIX to `output/dashboard_model_seed.pbix`.
3. Launch seed with `pbi-tools launch-pbi output/dashboard_model_seed.pbix`.
4. Run `powershell -ExecutionPolicy Bypass -File build/scripts/02_push_model_bim_via_tom.ps1`.
5. Save the seed PBIX in Power BI Desktop.
6. Run `powershell -ExecutionPolicy Bypass -File build/scripts/03_apply_native_layout_to_pbix.ps1`.
7. Open/save/check `output/dashboard_final.pbix`.
