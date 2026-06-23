# Data Dictionary

## dim_date

| Column | Type | Non-null | Example |
|---|---|---:|---|
| date_key | int64 | 29 | 20240101 |
| month_start_date | str | 29 | 2024-01-01 |
| year_month | str | 29 | 2024-01 |
| year | int32 | 29 | 2024 |
| quarter | str | 29 | Q1 |
| month_no | int32 | 29 | 1 |
| month_name | str | 29 | Jan |
| month_index | int64 | 29 | 1 |
| is_latest_complete_month | int64 | 29 | 0 |

## dim_spark_date

| Column | Type | Non-null | Example |
|---|---|---:|---|
| date_key | int64 | 29 | 20240101 |
| month_start_date | str | 29 | 2024-01-01 |
| year_month | str | 29 | 2024-01 |
| year | int32 | 29 | 2024 |
| quarter | str | 29 | Q1 |
| month_no | int32 | 29 | 1 |
| month_name | str | 29 | Jan |
| month_index | int64 | 29 | 1 |
| is_latest_complete_month | int64 | 29 | 0 |

## dim_plant

| Column | Type | Non-null | Example |
|---|---|---:|---|
| plant_id | str | 5 | P01 |
| plant_name | str | 5 | Bac Ninh Electronics |
| region | str | 5 | Vietnam North |
| country | str | 5 | Vietnam |
| productivity_index | float64 | 5 | 0.96 |
| labor_rate_usd | float64 | 5 | 4.9 |
| fixed_overhead_rate_usd | float64 | 5 | 18.0 |
| material_price_index | float64 | 5 | 1.05 |

## dim_product

| Column | Type | Non-null | Example |
|---|---|---:|---|
| product_id | str | 24 | SKU001 |
| product | str | 24 | Controller A |
| product_line | str | 24 | Electronics Assembly |
| lifecycle_stage | str | 24 | Core |
| standard_price_usd | float64 | 24 | 77.26 |
| standard_material_cost_usd | float64 | 24 | 28.53 |
| standard_labor_hours | float64 | 24 | 0.408 |
| standard_machine_hours | float64 | 24 | 0.259 |
| complexity_index | float64 | 24 | 1.012 |
| base_monthly_units | int64 | 24 | 2734 |

## dim_line

| Column | Type | Non-null | Example |
|---|---|---:|---|
| line_id | str | 12 | L01 |
| plant_id | str | 12 | P01 |
| line_name | str | 12 | SMT Line 1 |
| product_line | str | 12 | Electronics Assembly |
| monthly_capacity_units | int64 | 12 | 89000 |
| shift_count | float64 | 12 | 2.1 |
| plant_name | str | 12 | Bac Ninh Electronics |

## dim_scenario

| Column | Type | Non-null | Example |
|---|---|---:|---|
| scenario_id | str | 6 | S00 |
| scenario_name | str | 6 | Base |
| material_cost_reduction_pct | float64 | 6 | 0.0 |
| labor_efficiency_gain_pct | float64 | 6 | 0.0 |
| overhead_absorption_gain_pct | float64 | 6 | 0.0 |
| scrap_reduction_pct | float64 | 6 | 0.0 |
| volume_delta_pct | float64 | 6 | 0.0 |
| description | str | 6 | Current run rate. |

## fact_manufacturing_month

| Column | Type | Non-null | Example |
|---|---|---:|---|
| date_key | int64 | 2088 | 20240101 |
| month_start_date | str | 2088 | 2024-01-01 |
| year_month | str | 2088 | 2024-01 |
| month_index | int64 | 2088 | 1 |
| plant_id | str | 2088 | P01 |
| line_id | str | 2088 | L01 |
| product_id | str | 2088 | SKU001 |
| budget_units | float64 | 2088 | 11063.0 |
| produced_units | float64 | 2088 | 11684.0 |
| good_units | float64 | 2088 | 11325.0 |
| scrap_units | float64 | 2088 | 360.0 |
| rework_units | float64 | 2088 | 130.0 |
| capacity_units | float64 | 2088 | 12124.0 |
| available_hours | float64 | 2088 | 361.2 |
| run_hours | float64 | 2088 | 217.41 |
| downtime_hours | float64 | 2088 | 19.43 |
| actual_revenue | float64 | 2088 | 888903.71 |
| budget_revenue | float64 | 2088 | 854733.52 |
| standard_material_cost | float64 | 2088 | 333358.34 |
| standard_labor_cost | float64 | 2088 | 23359.62 |
| standard_overhead_cost | float64 | 2088 | 54473.07 |
| standard_cogs | float64 | 2088 | 411191.02 |
| actual_material_cost | float64 | 2088 | 337321.81 |
| actual_labor_cost | float64 | 2088 | 25770.37 |
| actual_overhead_cost | float64 | 2088 | 54048.93 |
| scrap_cost | float64 | 2088 | 10663.91 |
| rework_cost | float64 | 2088 | 145.12 |
| actual_cogs | float64 | 2088 | 427950.13 |
| material_variance | float64 | 2088 | 3963.47 |
| labor_variance | float64 | 2088 | 2410.75 |
| overhead_variance | float64 | 2088 | -424.14 |
| yield_loss_cost | float64 | 2088 | 10809.03 |
| gross_margin | float64 | 2088 | 460953.57 |
| inventory_units | float64 | 2088 | 8932.0 |
| inventory_value | float64 | 2088 | 293122.93 |
| slow_moving_inventory_value | float64 | 2088 | 3276.32 |

## fact_cost_variance_bridge

| Column | Type | Non-null | Example |
|---|---|---:|---|
| year_month | str | 6 | 2026-05 |
| bridge_order | int64 | 6 | 1 |
| bridge_step | str | 6 | Standard COGS |
| bridge_amount | float64 | 6 | 25551467.32 |
| bridge_type | str | 6 | start |
