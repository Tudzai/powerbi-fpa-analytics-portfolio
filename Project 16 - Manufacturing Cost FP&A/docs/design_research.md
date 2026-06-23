# Design Research

Selected seed/template:
- Technical seed: `Template/04_Profitability_Margin/Packt_Ch10_PVM.pbix`.
- Reason: manufacturing cost FP&A is a variance bridge problem, and the PVM finance pattern is the closest available seed for bridge-style decomposition.
- Rejected as primary seed: `Microsoft_Customer_Profitability.pbix` is useful for product/customer margin inspiration but less direct for standard cost variance; `Microsoft_Procurement_Analysis.pbix` is useful for manufacturing spend/vendor context but too procurement-centered for this 3-tab dashboard.

Research references:
- Microsoft Power BI dashboard design tips: keep the main story visible at a glance and remove clutter. https://learn.microsoft.com/en-us/power-bi/create-reports/service-dashboards-design-tips
- Microsoft Power BI report themes: use themes to apply consistent colors and default formatting across visuals. https://learn.microsoft.com/en-us/power-bi/create-reports/desktop-report-themes
- Microsoft Customer Profitability sample: CFO-oriented profitability sample for products, customers, and gross margin. https://learn.microsoft.com/en-us/power-bi/create-reports/sample-customer-profitability
- Microsoft Procurement Analysis sample: manufacturing company spend sample covering vendors, categories, and locations. https://learn.microsoft.com/en-us/power-bi/create-reports/sample-procurement
- Packt Power BI for Finance repository: includes Price Volume Mix Analysis and planning/finance PBIX examples. https://github.com/PacktPublishing/Power-BI-for-Finance

Applied layout:
- 3 tabs only, as requested.
- Each tab starts with a dedicated top filter bar, then four focused KPI cards, then trend/bridge, driver breakdown, and action table.
- Slicers use compact dropdown visuals in four equal-width top slots so controls are visible without a sidebar or scroll.
- KPI cards use native card visuals plus native mini line-chart sparklines driven by a disconnected spark date table, so selecting Month does not collapse the trend.
- Tables use stronger header fills, row banding, row padding, and measure alignment for faster scanning.
- Visual palette is industrial FP&A light: steel blue for primary measures, teal for margin/yield, amber/red for cost pressure and risk, violet for working capital.
