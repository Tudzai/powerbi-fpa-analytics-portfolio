# Rebuild Guide

1. Run `python build/scripts/01_build_project.py`.
2. Copy a valid seed PBIX to `output/dashboard_model_seed.pbix`.
3. Launch seed with `pbi-tools launch-pbi`.
4. Run `build/scripts/02_push_model_bim_via_tom.ps1`.
5. Save in Desktop.
6. Run `build/scripts/03_apply_native_layout_to_pbix.ps1`.
7. Open/save/check `output/dashboard_final.pbix`.
