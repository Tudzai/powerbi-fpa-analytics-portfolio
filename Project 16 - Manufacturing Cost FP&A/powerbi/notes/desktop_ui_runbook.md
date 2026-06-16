# Desktop UI Runbook

1. Confirm existing Project 13 sessions are ignored.
2. Run `powerbi/launch_powerbi.ps1`.
3. Confirm `pbi-tools info` shows a session with `PbixPath` equal to Project 16 `output/dashboard_final.pbix`.
4. Run `build/scripts/08_push_project16_model_to_powerbi_desktop.ps1`.
5. Save in Desktop.
6. Reopen exact PBIX and capture screenshots/validation notes.
