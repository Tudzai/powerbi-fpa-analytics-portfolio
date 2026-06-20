# Design Research

Selected template direction: ZoomCharts Inventory-style finance control tower, adapted for CFO/Board use. The reference dashboard emphasizes a deep purple app canvas, dark purple left sidebar, visible filter pills, KPI cards, small sparklines, PY/YoY context, rounded pale panels, and a dense operational dashboard grid.

Research sources:

- Microsoft Power BI dashboard design tips: https://learn.microsoft.com/en-us/power-bi/create-reports/service-dashboards-design-tips
- Microsoft Power BI KPI visual requirements: https://learn.microsoft.com/en-us/power-bi/visuals/power-bi-visualization-kpi
- NetSuite CFO KPI list, including cash runway formula: https://www.netsuite.com/portal/resource/articles/accounting/cfo-kpis.shtml
- Oracle CFO KPI dashboard overview: https://www.oracle.com/erp/cfo/cfo-kpis/
- Microsoft Fabric Community Modern Finance Dashboard Template reference: https://community.fabric.microsoft.com/t5/Data-Stories-Gallery/Modern-Finance-Dashboard-Template/m-p/3159868
- ZoomCharts Inventory Management Dashboard April 2025 reference: https://zoomcharts.com/en/microsoft-power-bi-custom-visuals/dashboard-and-report-examples/view/inventory-management-dashboard-april-2025
- Board reporting guide emphasizing 8-12 KPIs, context, and risk/funding questions: https://www.lucid.now/blog/custom-reporting-for-boards-guide/
- Local template library: `Template/03_FPnA_Budget_Spend/Packt_Ch12_Planning_Case_Study.pbix`, `Template/01_Core_Financial_Statements/Packt_Ch07_Group_Reporting.pbix`

Design choices:

- 3 tabs only, compressed from the README's 5 planned pages.
- Board Performance Overview answers whether the business is on track.
- Financial Plan & Cash Runway combines 3-statement planning, cash, burn and funding scenarios.
- Valuation, Covenants & Risk Monitor combines investor valuation range, sensitivity, covenant headroom and risk actions.
- Palette: deep purple canvas, dark purple sidebar, light neutral Power BI outspace, pale panel surfaces, violet primary bars, blue/teal analytics, green favorable states, amber watch states, and red risk states.
- Layout revision: global slicers moved into the left sidebar as compact dropdowns, each page uses 4 focused KPI cards instead of the crowded 5-card strip, KPI values are latest-complete-month numeric measures, compact canvas sparklines include a target band and markers, DAX SVG sparkline measures remain in the model for future Image URL decoration, and each page uses six rounded chart/table panels.
- Template download note: the official `?download=1` endpoint returned account-gated HTML, not a PBIX binary. The build therefore uses the public official preview asset in `archive/zoomcharts_asset_00_-20250423-135032-pherzy-john-diez-main.webp` to align the canvas proportions, KPI card structure, and grid placement.
