# Semantic Model Notes

- Main grain: monthly plant x line x product in `fact_manufacturing_month`.
- Standard cost variance is decomposed into material, labor, overhead, and yield loss drivers.
- Product/plant/line/date are conformed dimensions for all operational finance visuals.
- `dim_scenario` is disconnected and drives scenario measures without filtering facts directly.
- Rates and percentages are DAX measures with `DIVIDE`; raw rate columns are not used as KPI totals.
