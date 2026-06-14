# Data Dictionary

Generated from `data/raw/driver_forecasting_raw.xlsx`.

## RevenueDrivers_Raw

- Grain: one row per month, scenario, region, service line, customer segment
- Rows: 10,320

| Column | Type | Non-null | Example |
|---|---:|---:|---|
| RevenueDriverKey | str | 10,320 | 202401_ACTUAL_VN_NORTH_AIR_ENT |
| MonthStart | str | 10,320 | 2024-01-01 |
| PlanPeriod | str | 10,320 | Actual |
| ScenarioKey | str | 10,320 | ACTUAL |
| RegionKey | str | 10,320 | VN_NORTH |
| ServiceKey | str | 10,320 | AIR |
| SegmentKey | str | 10,320 | ENT |
| VolumeJobs | int64 | 10,320 | 94 |
| TEU | float64 | 10,320 | 0.0 |
| CBM | float64 | 10,320 | 0.0 |
| ChargeableKg | float64 | 10,320 | 62011.76 |
| AvgRateUSD | float64 | 10,320 | 1450.17 |
| SurchargeUSD | float64 | 10,320 | 7906.3 |
| DiscountUSD | float64 | 10,320 | 4771.04 |
| RevenueUSD | float64 | 10,320 | 139450.77 |
| DataSource | str | 10,320 | Synthetic planning model |

## CostDrivers_Raw

- Grain: one row per revenue driver row with direct cost components
- Rows: 10,320

| Column | Type | Non-null | Example |
|---|---:|---:|---|
| CostDriverKey | str | 10,320 | COST_202401_ACTUAL_VN_NORTH_AIR_ENT |
| RevenueDriverKey | str | 10,320 | 202401_ACTUAL_VN_NORTH_AIR_ENT |
| MonthStart | str | 10,320 | 2024-01-01 |
| PlanPeriod | str | 10,320 | Actual |
| ScenarioKey | str | 10,320 | ACTUAL |
| RegionKey | str | 10,320 | VN_NORTH |
| ServiceKey | str | 10,320 | AIR |
| SegmentKey | str | 10,320 | ENT |
| CarrierCostUSD | float64 | 10,320 | 97953.01 |
| HandlingCostUSD | float64 | 10,320 | 3099.96 |
| FuelCostUSD | float64 | 10,320 | 6414.74 |
| CustomsCostUSD | float64 | 10,320 | 621.07 |
| DirectCostUSD | float64 | 10,320 | 108088.77 |
| VariableCostPerJobUSD | float64 | 10,320 | 1149.88 |
| CostInflationPct | float64 | 10,320 | 0.018 |

## HeadcountPlan_Raw

- Grain: one row per month, scenario, region, department
- Rows: 2,580

| Column | Type | Non-null | Example |
|---|---:|---:|---|
| HeadcountPlanKey | str | 2,580 | HC_202401_ACTUAL_CN_SALES |
| MonthStart | str | 2,580 | 2024-01-01 |
| PlanPeriod | str | 2,580 | Actual |
| ScenarioKey | str | 2,580 | ACTUAL |
| RegionKey | str | 2,580 | CN |
| DepartmentKey | str | 2,580 | SALES |
| FTE | float64 | 2,580 | 13.8 |
| NewHires | float64 | 2,580 | 0.2 |
| Attrition | float64 | 2,580 | 0.2 |
| AvgSalaryUSD | float64 | 2,580 | 1998.0 |
| PayrollCostUSD | float64 | 2,580 | 27572.4 |
| JobsPerFTE | float64 | 2,580 | 185.29 |

## OpexDrivers_Raw

- Grain: one row per month, scenario, region, department
- Rows: 2,580

| Column | Type | Non-null | Example |
|---|---:|---:|---|
| OpexDriverKey | str | 2,580 | OPEX_202401_ACTUAL_CN_SALES |
| MonthStart | str | 2,580 | 2024-01-01 |
| PlanPeriod | str | 2,580 | Actual |
| ScenarioKey | str | 2,580 | ACTUAL |
| RegionKey | str | 2,580 | CN |
| DepartmentKey | str | 2,580 | SALES |
| RentUSD | float64 | 2,580 | 4395.57 |
| SoftwareUSD | float64 | 2,580 | 597.07 |
| MarketingUSD | float64 | 2,580 | 4708.23 |
| TravelUSD | float64 | 2,580 | 1399.45 |
| GAUSD | float64 | 2,580 | 763.53 |
| NonPayrollOpexUSD | float64 | 2,580 | 11863.84 |

## CashImpact_Raw

- Grain: one row per month and scenario
- Rows: 86

| Column | Type | Non-null | Example |
|---|---:|---:|---|
| CashImpactKey | str | 86 | CASH_202401_ACTUAL |
| MonthStart | str | 86 | 2024-01-01 |
| PlanPeriod | str | 86 | Actual |
| ScenarioKey | str | 86 | ACTUAL |
| RevenueUSD | float64 | 86 | 9158504.17 |
| DirectCostUSD | float64 | 86 | 7194669.71 |
| PayrollCostUSD | float64 | 86 | 698722.84 |
| NonPayrollOpexUSD | float64 | 86 | 226956.27 |
| GrossProfitUSD | float64 | 86 | 1963834.46 |
| EBITDAUSD | float64 | 86 | 1038155.35 |
| TaxPaidUSD | float64 | 86 | 176486.41 |
| CapexUSD | int64 | 86 | 8500 |
| DSODays | int64 | 86 | 43 |
| DPODays | int64 | 86 | 31 |
| WorkingCapitalUSD | float64 | 86 | 5692697.28 |
| OperatingCashFlowUSD | float64 | 86 | 662424.54 |
| EndingCashUSD | float64 | 86 | 2503924.54 |

## ForecastAccuracy_Raw

- Grain: one row per month, horizon, region, service line
- Rows: 1,530

| Column | Type | Non-null | Example |
|---|---:|---:|---|
| ForecastAccuracyKey | str | 1,530 | FA_202501_1M_CN_AIR |
| MonthStart | str | 1,530 | 2025-01-01 |
| ForecastHorizonMonths | int64 | 1,530 | 1 |
| RegionKey | str | 1,530 | CN |
| ServiceKey | str | 1,530 | AIR |
| ScenarioKey | str | 1,530 | BASE |
| ActualRevenueUSD | float64 | 1,530 | 438656.51 |
| ForecastRevenueUSD | float64 | 1,530 | 461022.13 |
| ForecastErrorUSD | float64 | 1,530 | 22365.62 |
| AbsoluteErrorUSD | float64 | 1,530 | 22365.62 |
| AbsolutePctError | float64 | 1,530 | 0.05099 |
| ForecastBiasPct | float64 | 1,530 | 0.05099 |

## Scenario_Assumptions

- Grain: one row per planning scenario
- Rows: 4

| Column | Type | Non-null | Example |
|---|---:|---:|---|
| ScenarioKey | str | 4 | ACTUAL |
| Scenario | str | 4 | Actual |
| SortOrder | int64 | 4 | 0 |
| VolumeMultiplier | float64 | 4 | 1.0 |
| RateMultiplier | float64 | 4 | 1.0 |
| CostInflationPct | float64 | 4 | 0.0 |
| HeadcountGrowthPct | float64 | 4 | 0.0 |
| SalaryInflationPct | float64 | 4 | 0.0 |
| DSODaysAdjustment | int64 | 4 | 0 |
| DPODaysAdjustment | int64 | 4 | 0 |
| Description | str | 4 | Actual historical performance through May 2026. |

## WhatIf_Parameters

- Grain: one row per configurable planning lever
- Rows: 7

| Column | Type | Non-null | Example |
|---|---:|---:|---|
| ParameterKey | str | 7 | VOL_GROWTH |
| Parameter | str | 7 | Volume Growth % |
| Unit | str | 7 | % |
| BaseValue | float64 | 7 | 0.06 |
| UpsideValue | float64 | 7 | 0.14 |
| DownsideValue | float64 | 7 | -0.08 |
| AppliesTo | str | 7 | Revenue volume |
| Description | str | 7 | Multiplier applied to planned job volume. |

## DimServices

- Grain: one row per service line
- Rows: 6

| Column | Type | Non-null | Example |
|---|---:|---:|---|
| ServiceKey | str | 6 | AIR |
| ServiceLine | str | 6 | Air Freight |
| BusinessUnit | str | 6 | Freight Forwarding |
| BaseJobs | int64 | 6 | 78 |
| BaseRateUSD | int64 | 6 | 1450 |
| CostRatio | float64 | 6 | 0.69 |
| WorkingCapitalIntensity | float64 | 6 | 0.9 |

## DimRegions

- Grain: one row per operating region
- Rows: 5

| Column | Type | Non-null | Example |
|---|---:|---:|---|
| RegionKey | str | 5 | VN_NORTH |
| Region | str | 5 | Vietnam North |
| Country | str | 5 | Vietnam |
| Hub | str | 5 | Ha Noi |
| RegionWeight | float64 | 5 | 1.05 |

## DimSegments

- Grain: one row per customer segment
- Rows: 4

| Column | Type | Non-null | Example |
|---|---:|---:|---|
| SegmentKey | str | 4 | ENT |
| CustomerSegment | str | 4 | Enterprise |
| SegmentWeight | float64 | 4 | 1.22 |
| DiscountPct | float64 | 4 | 0.035 |
| DSODays | int64 | 4 | 48 |

## DimDepartments

- Grain: one row per department
- Rows: 6

| Column | Type | Non-null | Example |
|---|---:|---:|---|
| DepartmentKey | str | 6 | SALES |
| Department | str | 6 | Sales |
| FunctionGroup | str | 6 | Commercial |
| BaseFTE | int64 | 6 | 16 |
| AvgSalaryUSD | int64 | 6 | 1850 |
