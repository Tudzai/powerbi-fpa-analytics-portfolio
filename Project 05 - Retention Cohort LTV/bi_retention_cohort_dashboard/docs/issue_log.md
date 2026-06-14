# Issue Log

## ISSUE-001 - Final PBIX requires Desktop save

- Status: Fixed
- Severity: High
- Found in: current build
- Page: File QA
- Visual: n/a
- Expected: `output/dashboard_final.pbix` exists and passes open/save/refresh QA.
- Actual: PBIX final was not produced by the scripted package alone.
- Root cause: Full import-model PBIX authoring requires Power BI Desktop interactive save or a supported source project route.
- Fix: Opened PBIP in Power BI Desktop via Computer Use, refreshed model/data, changed Save As type to `Power BI file (*.pbix)`, saved to `output/dashboard_final.pbix`, reran QA.
- Regression: PASS - prepared data QA and PBIX file QA passed.
- Fixed in: v03

## ISSUE-002 - PBIX opened with blank report canvas

- Status: Fixed
- Severity: Critical
- Found in: user open check
- Page: Report canvas
- Visual: all report visuals
- Expected: `dashboard_final.pbix` opens to a populated Retention & Cohort Dashboard.
- Actual: model/tables existed, but report layout had no visual pages.
- Root cause: the PBIX was saved with an empty report canvas.
- Fix: generated native Power BI layout JSON with 4 report pages and 57 visual containers, patched `/Report/Layout` into the PBIX, and saved in Desktop.
- Regression: PASS - Page 1, Page 2, Page 3, and Page 4 rendered in Power BI Desktop.
- Fixed in: v03

## ISSUE-003 - Visuals showed data fetch errors after layout patch

- Status: Fixed
- Severity: Critical
- Found in: Power BI Desktop render QA
- Page: all data-bound visuals
- Visual: cards, line charts, tables
- Expected: DAX measures render numeric KPIs and chart values.
- Actual: visuals showed `Error fetching data for this visual`; technical detail: `SUM cannot work with values of type String`.
- Root cause: CSV partitions promoted headers but did not apply `Table.TransformColumnTypes`, so numeric columns arrived as text.
- Fix: updated model column metadata and M partition expressions to use date, int64, and number types; patched the source build script to generate typed M queries on rebuild.
- Regression: PASS - all 4 pages render with zero visual fetch errors.
- Fixed in: v03
