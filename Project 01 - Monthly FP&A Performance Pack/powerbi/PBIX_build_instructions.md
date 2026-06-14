# PBIX Build Instructions

Target final file: `output/dashboard_final.pbix`

Current status: pending Desktop build and QA.

Power BI Desktop Store app was detected:

`Microsoft.MicrosoftPowerBIDesktop_8wekyb3d8bbwe!Microsoft.MicrosoftPowerBIDesktop`

## Build Steps

1. Open Power BI Desktop.
2. Import theme: `build/config/theme.json`.
3. In Power Query, create text parameter `pProjectRoot`.
4. Set `pProjectRoot` to this project folder:
   `C:\Users\Win\OneDrive\Codex\Portfolio\BI\Project 01 - Monthly FP&A Performance Pack`
5. Use `build/config/PowerQuery_AllTables.pq` to create helper query `LoadPreparedCsv` and each Dim/Fact query.
6. Rename queries exactly:
   - DimDate
   - DimScenario
   - DimBusinessUnit
   - DimProduct
   - DimRegion
   - DimCustomer
   - DimDepartment
   - FactFinancials
   - FactOpexDepartment
   - FactCash
   - FactBridge
   - FactCommentary
7. Apply relationships from `model/relationship_map.md`.
8. Create a measure table named `KPI Measures`.
9. Add DAX from `model/measures.dax`.
10. Set sort-by columns:
    - DimDate[MonthName] by DimDate[MonthNumber]
    - DimDate[MonthYear] by DimDate[MonthIndex]
    - DimScenario[Scenario] by DimScenario[ScenarioSort]
    - FactBridge[BridgeStep] by FactBridge[BridgeOrder]
11. Build pages from `build/config/page_map.json` and `build/config/visual_map.json`.
12. Save as `output/dashboard_v01.pbix`.
13. Refresh and run QA checklist.
14. After QA passes, save a copy as `output/dashboard_final.pbix`.

## QA Gates Before Final

- Data totals reconcile with `qa/reconciliation.xlsx`.
- KPI cards use DAX measures, not raw numeric fields.
- Slicers work in Reading view.
- Waterfall bridge shows Budget EBITDA to Actual EBITDA for May 2026.
- Trend charts show at least 12 months.
- Cash uses latest visible month logic.
- No cropped labels, blank visuals, or duplicate slicer titles.
