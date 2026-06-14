# Power BI Desktop UI Runbook

1. Close old Power BI Desktop reports from prior prompt work without saving them.
2. Confirm `output/dashboard_final.pbix` does not already exist. If `output/rejected_dashboard_final_wrong_model.pbix` exists, leave it quarantined.
3. Run `powerbi/launch_powerbi.ps1`.
4. Create or refresh the import workbook with `build/scripts/create_powerbi_import_workbook.py`.
5. Import `powerbi/marketing_campaign_roi_import.xlsx`.
6. In Navigator, select the table entries without numeric suffixes: `DimCampaign`, `DimChannel`, `DimDate`, `DimMonth`, `FactCampaignDaily`.
7. Load and apply changes. Confirm the Data pane contains only Project 06 - Marketing Campaign ROI tables, not old tables such as `dim_seller`, `fact_seller_month`, `fact_ads_spend`, `fact_orders`, `fact_sessions`, or ecommerce/funnel tables.
8. Set date columns to Date, monetary fields to Decimal, counts to Whole Number.
9. Create relationships from `model/relationship_map.md`.
10. Create DAX measures from `model/dax_measures.md`.
11. Apply `build/config/theme.json`.
12. Build pages from `build/config/page_map.json` and `build/config/visual_map.json`.
13. Add slicers from `build/config/slicer_map.json`.
14. Save as `output/dashboard_final.pbix`.
15. Reopen, refresh, save again, extract/inspect the PBIX model, and capture screenshots before marking final.
