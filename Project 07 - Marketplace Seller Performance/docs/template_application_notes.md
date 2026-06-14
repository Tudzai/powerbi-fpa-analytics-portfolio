# Template Application Notes

## Research Direction

- Use an executive-first command center: KPI strip, trend, marketplace mix, then seller action table.
- Keep a light operating dashboard surface: off-white page, white visual containers, thin borders, compact spacing.
- Use marketplace color semantics: orange for commerce/GMV, green for good operating health, red for cancellation risk, violet for inventory/risk, blue/cyan for platform mix.
- Prefer Power BI report themes over manual one-off visual formatting, so the PBIX stays openable and easier to maintain.

## Applied To PBIX

- Created custom theme JSON: `build/config/marketplace_command_center_theme.json`.
- Applied the theme to `output/dashboard_final.pbix` and `output/dashboard_complete.pbix`.
- Applied the complete 4-page chart layout to `output/dashboard_final.pbix` and `output/dashboard_complete.pbix`.
- Power BI Desktop opened the complete PBIX successfully and saved it again.
- When changing `Report/Layout`, remove stale `SecurityBindings` before opening in Power BI Desktop; Desktop regenerates valid bindings on save.

## Source-Inspired Rules

- Microsoft dashboard design guidance: important information should stand out and remain uncluttered.
- Microsoft report theme guidance: report themes apply colors and default visual formatting across the report.
- Fabric ecommerce dashboard examples: include ecommerce KPIs, category/operational insights, and monthly trends.
- ZoomCharts and marketplace/ecommerce galleries: use KPI-first, operationally scannable layouts.
- The final PBIX follows a four-view marketplace operating pattern: executive status, seller portfolio, growth drivers, and operational risk.

## Sources

- Microsoft Learn - Dashboard design tips: https://learn.microsoft.com/en-us/power-bi/create-reports/service-dashboards-design-tips
- Microsoft Learn - Report themes: https://learn.microsoft.com/en-us/power-bi/create-reports/desktop-report-themes
- Fabric Community - Ecommerce Sales Dashboard Template: https://community.fabric.microsoft.com/t5/Data-Stories-Gallery/Ecommerce-Sales-Dashboard-Template/m-p/4363102
- ZoomCharts - Power BI dashboard examples: https://zoomcharts.com/en/microsoft-power-bi-custom-visuals/dashboard-and-report-examples/
- Coupler.io - Ecommerce dashboard examples: https://www.coupler.io/dashboard-examples/ecommerce-dashboard
