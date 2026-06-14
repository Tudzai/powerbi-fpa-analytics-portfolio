# QA Checklist

## Data QA

- [x] Source summary generated.
- [x] Prepared data excludes bot traffic.
- [x] Funnel stage totals are monotonic.
- [x] Orders reconcile to purchase sessions.

## Metric QA

- [x] Visits = `161,097`.
- [x] Purchases = `18,567`.
- [x] Overall conversion = `11.53%`.
- [x] Revenue = `$1,558,769`.
- [x] Percentage/rate measures use division, not sums.

## Complete HTML Visual QA

- [x] Complete HTML dashboard renders KPI cards, funnel, trend, segment tables, product table, marketing efficiency, and Data & QA page.
- [x] Five pages captured at 1440x1100: `page_p1_complete.png` through `page_p5_complete.png`.
- [x] Page map and visual map define all Power BI pages.
- [x] Screenshot pixel checks confirm every page is nonblank.

## Interaction QA

- [x] HTML slicers for device, channel, campaign, category update KPI cards, funnel, trend, tables, and efficiency views.
- [x] Filter reconciliation passed for Mobile + Paid Search: visits `14,173`, purchases `1,294`, CVR `9.13%`.
- [x] QA evidence written to `qa/complete_dashboard_qa.json`.
- [x] Native PBIX model fields support template slicers for channel/device/category/product dimensions.

## File QA

- [x] `output/dashboard_final.pbix` exists.
- [x] Power BI Desktop launch verified.
- [x] Compatibility semantic model push to Desktop local session passed on 2026-06-11, process `27840`, port `62691`.
- [x] Offline export from `output/dashboard_final.pbix` passed.
- [x] PBIX file validation evidence written to `qa/pbix_file_validation.json`.
