# Authoring Strategy

Selected mode: `COMPUTER_USE`.

## Strategy Order Checked

1. `TEMPLATE_FIRST`: no Project 07 - Marketplace Seller Performance PBIX/PBIT seed in `powerbi/templates/`.
2. `COMPUTER_USE`: selected after the Computer Use skill exposed callable Windows UI automation.
3. `PBIP_PBIT`: no valid Project 07 - Marketplace Seller Performance Power BI source exists to compile.
4. `DESKTOP_FALLBACK`: no longer needed for the final cut.

## pbi-tools Rule

`pbi-tools` was used for extraction/source validation, not to author the dashboard from zero. No unrelated project source was compiled or copied as the final dashboard.

## Computer Use Path

1. Connect to the running Power BI Desktop local XMLA session.
2. Push Project 07 - Marketplace Seller Performance model with `build/scripts/08_push_project7_model_to_powerbi_desktop.ps1`.
3. Use Computer Use to create a native KPI card and native seller performance table.
4. Save the Power BI Desktop file and place the real PBIX at `output/dashboard_final.pbix`.
5. Validate with `pbi-tools extract` and `pbi-tools export-data`.
