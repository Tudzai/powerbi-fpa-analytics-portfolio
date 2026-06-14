# Design Research Notes

Date: 2026-06-11

Goal: improve the Power BI ecommerce executive dashboard visual design while keeping it usable, native, and maintainable.

Sources reviewed:

- Microsoft Power BI dashboard design tips: https://learn.microsoft.com/en-us/power-bi/create-reports/service-dashboards-design-tips
  - Applied: clean, uncluttered one-screen story; highest-level metrics at the top; important information placed high and left.
- Tabular Editor KPI card guidance: https://tabulareditor.com/blog/kpi-card-best-practices-dashboard-design
  - Applied: KPI cards are clearer and less cluttered, with title plus value instead of duplicated card labels.
- Microsoft Fabric Community eCommerce Power BI dashboard template: https://community.fabric.microsoft.com/t5/Themes-Gallery/eCommerce-Power-BI-Dashboard-Template/m-p/4329619
  - Applied: ecommerce report structure keeps sales, category/product, customer/channel, and operating pages separated while surfacing revenue and AOV.
- Supermetrics Power BI marketing/ecommerce examples: https://supermetrics.com/blog/power-bi-marketing-dashboard-examples
  - Applied: executive ecommerce view connects sales outcomes with traffic, marketing spend, channel contribution, conversion, and acquisition metrics.
- ZoomCharts report template gallery: https://zoomcharts.com/en/microsoft-power-bi-custom-visuals/dashboard-and-report-examples/
  - Applied: overview-first report structure, consistent cards, and drill-style supporting pages.

Applied design direction:

- Dark executive header on every page with compact slicer chips.
- Dark KPI tiles for stronger first-read hierarchy.
- Light analytic panels on a soft gray canvas for contrast.
- Consistent 8px card radius, subtle shadows, and restrained navy/teal/blue/amber/red palette.
- Overview page flow: KPI strip, movement trend, top category, channel contribution, detail table.
- Detail pages preserve the same structure for revenue/category, traffic/conversion, and refunds/operations.
