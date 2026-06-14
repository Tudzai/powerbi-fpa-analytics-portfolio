# Desktop UI Runbook

1. Run `powerbi/launch_powerbi.ps1` and wait for a blank Power BI Desktop window.
2. Run `build/scripts/07_push_model_to_powerbi_desktop.ps1`.
3. Verify `qa/scripted_model_push.json` records the selected process id and local port.
4. Save the active Desktop file as `C:\Users\Win\OneDrive\Codex\Portfolio\BI\Project 12 - WealthTech AUM Client Retention\output\dashboard_model.pbix`.
5. Run `build/scripts/10_apply_native_pbix_report.ps1` to create `C:\Users\Win\OneDrive\Codex\Portfolio\BI\Project 12 - WealthTech AUM Client Retention\output\dashboard_final.pbix`.
6. Reopen the final PBIX and confirm pages render without visual errors.
