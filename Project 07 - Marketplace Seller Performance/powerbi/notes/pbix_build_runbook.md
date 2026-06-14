# PBIX Build Runbook

Build mode: `computer_use_powerbi_desktop`.
Authoring mode: `COMPUTER_USE`.
Authoring blocker: `none`.

## Final PBIX Criteria

- `output/dashboard_final.pbix` exists. PASS.
- File opens/extracts without repair prompts. PASS via `pbi-tools extract`.
- Model data can be exported from the PBIX. PASS via `pbi-tools export-data`.
- KPI card reconciles to model totals. PASS in visual accessibility: Seller GMV `$3M`, fulfillment `97.7%`, cancellation `8.1%`, rating `4.15`, active sellers `122`.
- Seller table binds `seller_name`, Seller GMV, Fulfillment Rate, Cancellation Rate, Average Rating, and Stock Availability. PASS.
- Report is saved by Power BI Desktop. PASS.
