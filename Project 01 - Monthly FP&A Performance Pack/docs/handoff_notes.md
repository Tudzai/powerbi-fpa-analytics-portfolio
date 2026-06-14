# Handoff Notes

## What Was Built

A Power BI-ready Monthly FP&A Performance Pack with an orange executive theme.

The package includes:

- Raw and prepared FP&A data.
- Star-schema model.
- DAX measure library.
- Power Query instructions.
- Relationship map.
- Page and visual design map.
- QA checklist and reconciliation.
- Issue log and changelog.
- PBIX build instructions.
- Visible HTML dashboard at `output/dashboard.html`.
- Export mirror at `output/exports/fpa_dashboard_preview.html`.
- Final Power BI Desktop file at `output/dashboard_final.pbix`.
- Power BI Project backup dashboard at `output/open_dashboard_powerbi.pbip`.
- Valid Power BI Desktop model backup at `output/dashboard_model.pbix`.

## Final Power BI Deliverable

`output/dashboard_final.pbix` is the final handoff file. It opens in Power BI Desktop with:

- 4 report pages.
- 41 native report visual containers.
- Orange FP&A dashboard canvas with no commentary/insight text sections.
- 13 imported tables.
- 19 relationships.
- 53 DAX measures.

Pages:

1. Executive KPI
2. Variance Bridge
3. Dimension Drilldown
4. Opex & Cash

The PBIX includes KPI cards, Actual/Budget/Forecast comparison, 12-month trend, EBITDA variance drivers, Revenue Variance by Region, Budget to Actual bridge, Opex/Cash controls, and drill-down pages for business unit, product, region, and customer. The dashboard canvas intentionally excludes long commentary blocks.

Verification screenshot: `output/screenshots/dashboard_final_v08_right_insight.png`.

## Recommended Build Order In Power BI

1. Open `output/dashboard_final.pbix`.
2. If Power BI prompts for model refresh, click Refresh.
3. Review pages and visuals.
4. Use Fields/Model view for the semantic model and DAX measures.
5. Use `output/dashboard.html` only as a retained browser reference from the earlier build; the PBIX is the final deliverable.

## Known Caveats

- Data is synthetic and for portfolio demonstration.
- Forecast assumptions are management-scenario sample values.
- Department Opex uses a separate fact table from product/customer P&L.
- CashBalance is a balance metric and must use latest visible month logic.
- The report canvas was generated automatically from prepared data as a portfolio-ready native Power BI visual layer. The semantic model is complete for further slicer-sync and drill-through polish.

## Next Review Points

- Replace synthetic raw files with real finance export if available.
- Confirm whether Opex should be allocated to customer/product level in actual company reporting.
- Confirm exact currency display: VND, USD, or VND million.
- Optionally add slicer sync, tooltip pages, and formal click drill-through if the portfolio requires deeper interaction polish.
