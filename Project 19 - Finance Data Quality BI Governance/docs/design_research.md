# Design Research

Template direction selected: finance governance control room. The layout uses a top KPI strip, left-to-right trend and diagnostic visuals, compact slicers, and exception tables for operational follow-up.

Research inputs:

- [Microsoft Power BI dashboard design tips](https://learn.microsoft.com/en-us/power-bi/create-reports/service-dashboards-design-tips): keep dashboards clean, uncluttered, and make the most important information stand out.
- [Microsoft Learn: Design effective reports in Power BI](https://learn.microsoft.com/en-us/training/paths/power-bi-effective/): define audience and report design requirements before choosing visuals and filters.
- [IBM data quality dimensions](https://www.ibm.com/think/topics/data-quality-dimensions): completeness, accuracy, consistency, and related quantitative measures should be monitored.
- [Collibra data quality dimensions](https://www.collibra.com/blog/the-6-dimensions-of-data-quality): data quality should make data reliable and usable through dimensions such as accuracy, completeness, and consistency.
- [Qlik financial dashboard examples](https://www.qlik.com/us/dashboard-examples/financial-dashboards): finance dashboards should move beyond static reporting toward monitoring and action.

Applied choices:

- Page 1 emphasizes executive status and trust: DQ score, freshness, refresh success, incidents, reconciliation exposure.
- Page 2 diagnoses reliability and quality drivers: refresh causes, completeness, reconciliation aging, incidents.
- Page 3 covers adoption and controls: report usage, performance, access risk, RLS exceptions, deployment control.
- Page 4 converts monitoring into action: incident queue, access-review queue, aged reconciliation exposure, and sensitive export risk.
