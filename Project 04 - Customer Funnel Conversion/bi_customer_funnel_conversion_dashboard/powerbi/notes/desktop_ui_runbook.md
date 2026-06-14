# Desktop UI Runbook

1. Open Power BI Desktop using `powerbi/launch_powerbi.ps1`.
2. If a blank report opens, run `build/scripts/07_push_model_to_powerbi_desktop.ps1` from PowerShell.
3. In Power BI Desktop, save the report as `output/dashboard_model.pbix`.
4. Build the visuals using `build/config/page_map.json` and `build/config/visual_map.json`, or use the generated HTML preview as the layout reference.
5. Save final as `output/dashboard_final.pbix`.
6. Refresh and validate against `qa/reconciliation.xlsx`.
