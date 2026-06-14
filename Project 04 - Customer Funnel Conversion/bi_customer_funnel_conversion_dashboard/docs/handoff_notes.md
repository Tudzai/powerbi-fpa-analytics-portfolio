# Handoff Notes

## Output

- Final BI file: `output/dashboard_final.pbix`
- Complete HTML dashboard: `output/dashboard.html`
- Complete dashboard payload: `output/dashboard_payload_complete.json`
- Screenshots: `output/screenshots/`
- Build status: `complete_html_dashboard_passed; native_pbix_created`
- PBIX status: `output/dashboard_final.pbix` exists and passed offline export validation. Project 04 - Customer Funnel Conversion data was pushed into a native Power BI template through Power BI Desktop process `27840` / port `62691`.

## Source

- Raw data: `data/raw/`
- Prepared data: `data/prepared/`
- Power BI compatibility tables: `data/powerbi_template_compat/`
- Source summary: `data/source_summary.json`
- Dashboard cube: `output/dashboard_payload_complete.json`
- Synthetic seed: `4042026`

## Tool Environment

- Power BI Desktop: EXE available and Store app available.
- pbi-tools: available.
- Build mode: `native_pbix_from_compatible_powerbi_template_plus_complete_html_dashboard`.

## KPI Definitions

- Funnel metrics are session-based.
- Revenue comes from `fact_orders[net_revenue]`.
- Conversion rates use division, never summed percentages.
- Dashboard-wide filters update KPI cards, funnel progression, trend, segment tables, product table, and marketing efficiency.
- Campaign-channel-month spend is allocated to filtered device/category/product scopes by visit share for diagnostic ROAS/CAC.

## QA Status

- Data QA: Pass
- Metric QA: Pass
- Complete HTML Visual QA: Pass. Five pages rendered nonblank at 1440x1100.
- Complete HTML Interaction QA: Pass. Mobile + Paid Search filter changes visits/CVR from all-scope baseline.
- PBIX File QA: Pass. `qa/pbix_file_validation.json` confirms offline export from `output/dashboard_final.pbix`.
- PBIX metric check: 18,567 orders, 161,097 sessions, `$1,558,769.34` net revenue.

## Known Notes

- The PBIX uses a compatible native ecommerce executive template layout; the semantic model and exported data are Project 04 - Customer Funnel Conversion Customer Funnel data.
- The polished Project 04 - Customer Funnel Conversion-specific visual layout remains `output/dashboard.html`.

## Next Action

1. Open `output/dashboard_final.pbix` in Power BI Desktop for the native BI file.
2. Use `output/dashboard.html` for the polished interactive web version.
3. Keep `qa/pbix_file_validation.json` with the PBIX as validation evidence.
