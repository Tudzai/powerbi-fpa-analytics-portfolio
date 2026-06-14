from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_PATH = PROJECT_ROOT / "data" / "raw" / "driver_forecasting_raw.xlsx"

SEED = 20260608
LATEST_ACTUAL_MONTH = pd.Timestamp("2026-05-01")
START_MONTH = pd.Timestamp("2024-01-01")
END_MONTH = pd.Timestamp("2027-12-01")
FORECAST_START_MONTH = pd.Timestamp("2026-06-01")


REGIONS = [
    {"RegionKey": "VN_NORTH", "Region": "Vietnam North", "Country": "Vietnam", "Hub": "Ha Noi", "RegionWeight": 1.05},
    {"RegionKey": "VN_SOUTH", "Region": "Vietnam South", "Country": "Vietnam", "Hub": "Ho Chi Minh", "RegionWeight": 1.18},
    {"RegionKey": "VN_CENTRAL", "Region": "Vietnam Central", "Country": "Vietnam", "Hub": "Da Nang", "RegionWeight": 0.74},
    {"RegionKey": "TH", "Region": "Thailand", "Country": "Thailand", "Hub": "Bangkok", "RegionWeight": 0.62},
    {"RegionKey": "CN", "Region": "China", "Country": "China", "Hub": "Shanghai", "RegionWeight": 0.82},
]

SERVICES = [
    {"ServiceKey": "AIR", "ServiceLine": "Air Freight", "BusinessUnit": "Freight Forwarding", "BaseJobs": 78, "BaseRateUSD": 1450, "CostRatio": 0.69, "WorkingCapitalIntensity": 0.90},
    {"ServiceKey": "FCL", "ServiceLine": "Ocean FCL", "BusinessUnit": "Freight Forwarding", "BaseJobs": 128, "BaseRateUSD": 980, "CostRatio": 0.73, "WorkingCapitalIntensity": 1.08},
    {"ServiceKey": "LCL", "ServiceLine": "Ocean LCL", "BusinessUnit": "Freight Forwarding", "BaseJobs": 110, "BaseRateUSD": 540, "CostRatio": 0.67, "WorkingCapitalIntensity": 0.96},
    {"ServiceKey": "CLS", "ServiceLine": "Contract Logistics", "BusinessUnit": "Contract Logistics", "BaseJobs": 64, "BaseRateUSD": 1320, "CostRatio": 0.58, "WorkingCapitalIntensity": 0.78},
    {"ServiceKey": "CUS", "ServiceLine": "Customs Brokerage", "BusinessUnit": "Customs", "BaseJobs": 150, "BaseRateUSD": 205, "CostRatio": 0.42, "WorkingCapitalIntensity": 0.52},
    {"ServiceKey": "TRK", "ServiceLine": "Domestic Trucking", "BusinessUnit": "Transport", "BaseJobs": 175, "BaseRateUSD": 310, "CostRatio": 0.61, "WorkingCapitalIntensity": 0.84},
]

SEGMENTS = [
    {"SegmentKey": "ENT", "CustomerSegment": "Enterprise", "SegmentWeight": 1.22, "DiscountPct": 0.035, "DSODays": 48},
    {"SegmentKey": "MM", "CustomerSegment": "Mid Market", "SegmentWeight": 1.00, "DiscountPct": 0.022, "DSODays": 42},
    {"SegmentKey": "SME", "CustomerSegment": "SME", "SegmentWeight": 0.76, "DiscountPct": 0.010, "DSODays": 34},
    {"SegmentKey": "SKA", "CustomerSegment": "Strategic Key Account", "SegmentWeight": 1.36, "DiscountPct": 0.048, "DSODays": 55},
]

DEPARTMENTS = [
    {"DepartmentKey": "SALES", "Department": "Sales", "FunctionGroup": "Commercial", "BaseFTE": 16, "AvgSalaryUSD": 1850},
    {"DepartmentKey": "OPS", "Department": "Operations", "FunctionGroup": "Operations", "BaseFTE": 42, "AvgSalaryUSD": 1320},
    {"DepartmentKey": "CS", "Department": "Customer Success", "FunctionGroup": "Operations", "BaseFTE": 17, "AvgSalaryUSD": 1180},
    {"DepartmentKey": "FIN", "Department": "Finance", "FunctionGroup": "G&A", "BaseFTE": 9, "AvgSalaryUSD": 1550},
    {"DepartmentKey": "IT", "Department": "IT & Data", "FunctionGroup": "G&A", "BaseFTE": 6, "AvgSalaryUSD": 1700},
    {"DepartmentKey": "MGT", "Department": "Management", "FunctionGroup": "G&A", "BaseFTE": 5, "AvgSalaryUSD": 3100},
]

SCENARIOS = [
    {
        "ScenarioKey": "ACTUAL",
        "Scenario": "Actual",
        "SortOrder": 0,
        "VolumeMultiplier": 1.00,
        "RateMultiplier": 1.00,
        "CostInflationPct": 0.00,
        "HeadcountGrowthPct": 0.00,
        "SalaryInflationPct": 0.00,
        "DSODaysAdjustment": 0,
        "DPODaysAdjustment": 0,
        "Description": "Actual historical performance through May 2026.",
    },
    {
        "ScenarioKey": "BASE",
        "Scenario": "Base",
        "SortOrder": 1,
        "VolumeMultiplier": 1.00,
        "RateMultiplier": 1.00,
        "CostInflationPct": 0.045,
        "HeadcountGrowthPct": 0.060,
        "SalaryInflationPct": 0.055,
        "DSODaysAdjustment": 0,
        "DPODaysAdjustment": 0,
        "Description": "Management case: moderate market growth and controlled cost inflation.",
    },
    {
        "ScenarioKey": "UPSIDE",
        "Scenario": "Upside",
        "SortOrder": 2,
        "VolumeMultiplier": 1.14,
        "RateMultiplier": 1.035,
        "CostInflationPct": 0.030,
        "HeadcountGrowthPct": 0.085,
        "SalaryInflationPct": 0.060,
        "DSODaysAdjustment": -3,
        "DPODaysAdjustment": 2,
        "Description": "Upside case: stronger volumes, modest pricing lift, improved collections.",
    },
    {
        "ScenarioKey": "DOWNSIDE",
        "Scenario": "Downside",
        "SortOrder": 3,
        "VolumeMultiplier": 0.86,
        "RateMultiplier": 0.965,
        "CostInflationPct": 0.075,
        "HeadcountGrowthPct": 0.015,
        "SalaryInflationPct": 0.045,
        "DSODaysAdjustment": 6,
        "DPODaysAdjustment": -2,
        "Description": "Downside case: demand softens, pricing pressure rises, customers pay slower.",
    },
]


def month_range(start: pd.Timestamp, end: pd.Timestamp) -> pd.DatetimeIndex:
    return pd.date_range(start=start, end=end, freq="MS")


def scenario_for_month(month: pd.Timestamp) -> list[dict]:
    if month <= LATEST_ACTUAL_MONTH:
        return [SCENARIOS[0]]
    return SCENARIOS[1:]


def seasonal_multiplier(month_number: int, service_key: str) -> float:
    base = 1 + 0.08 * np.sin((month_number - 1) / 12 * 2 * np.pi)
    peak = 1.0
    if service_key in {"AIR", "FCL", "LCL"} and month_number in {8, 9, 10, 11}:
        peak += 0.10
    if service_key in {"TRK", "CUS"} and month_number in {1, 12}:
        peak += 0.07
    if service_key == "CLS":
        peak += 0.04 if month_number in {4, 5, 6} else 0
    return base * peak


def build_revenue_and_cost(rng: np.random.Generator) -> tuple[pd.DataFrame, pd.DataFrame]:
    revenue_rows: list[dict] = []
    cost_rows: list[dict] = []
    months = month_range(START_MONTH, END_MONTH)

    for month in months:
        month_index = (month.year - START_MONTH.year) * 12 + month.month - START_MONTH.month
        actual_period = month <= LATEST_ACTUAL_MONTH
        plan_period = "Actual" if actual_period else "Forecast"
        trend = 1 + 0.0065 * month_index

        for scenario in scenario_for_month(month):
            for region in REGIONS:
                for service in SERVICES:
                    for segment in SEGMENTS:
                        scenario_key = scenario["ScenarioKey"]
                        season = seasonal_multiplier(month.month, service["ServiceKey"])
                        service_mix_noise = rng.normal(1.0, 0.045 if actual_period else 0.025)
                        base_jobs = service["BaseJobs"] * region["RegionWeight"] * segment["SegmentWeight"]

                        if actual_period:
                            volume_multiplier = 1.0
                            rate_multiplier = 1.0
                            cost_inflation = 0.018 + 0.002 * (month.year - 2024)
                        else:
                            forecast_month_index = (month.year - FORECAST_START_MONTH.year) * 12 + month.month - FORECAST_START_MONTH.month
                            volume_multiplier = scenario["VolumeMultiplier"] * (1 + 0.006 * forecast_month_index)
                            rate_multiplier = scenario["RateMultiplier"] * (1 + 0.0025 * forecast_month_index)
                            cost_inflation = scenario["CostInflationPct"] + 0.0015 * forecast_month_index

                        jobs = max(6, int(round(base_jobs * trend * season * volume_multiplier * service_mix_noise)))
                        avg_rate = service["BaseRateUSD"] * rate_multiplier * (1 + 0.004 * month_index)
                        avg_rate *= rng.normal(1.0, 0.035 if actual_period else 0.018)

                        surcharge_pct = 0.042 + (0.014 if service["ServiceKey"] in {"AIR", "FCL", "TRK"} else 0.006)
                        surcharge_pct += 0.004 * np.sin(month.month / 12 * 2 * np.pi)
                        discount_pct = segment["DiscountPct"]
                        gross_revenue = jobs * avg_rate
                        surcharge_usd = gross_revenue * surcharge_pct
                        discounts_usd = gross_revenue * discount_pct
                        revenue_usd = gross_revenue + surcharge_usd - discounts_usd

                        teu = 0.0
                        cbm = 0.0
                        kg = 0.0
                        if service["ServiceKey"] == "FCL":
                            teu = jobs * rng.uniform(1.15, 1.65)
                        elif service["ServiceKey"] == "LCL":
                            cbm = jobs * rng.uniform(4.5, 8.2)
                        elif service["ServiceKey"] == "AIR":
                            kg = jobs * rng.uniform(650, 1500)

                        rev_key = f"{month:%Y%m}_{scenario_key}_{region['RegionKey']}_{service['ServiceKey']}_{segment['SegmentKey']}"
                        revenue_rows.append(
                            {
                                "RevenueDriverKey": rev_key,
                                "MonthStart": month.date().isoformat(),
                                "PlanPeriod": plan_period,
                                "ScenarioKey": scenario_key,
                                "RegionKey": region["RegionKey"],
                                "ServiceKey": service["ServiceKey"],
                                "SegmentKey": segment["SegmentKey"],
                                "VolumeJobs": jobs,
                                "TEU": round(teu, 2),
                                "CBM": round(cbm, 2),
                                "ChargeableKg": round(kg, 2),
                                "AvgRateUSD": round(avg_rate, 2),
                                "SurchargeUSD": round(surcharge_usd, 2),
                                "DiscountUSD": round(discounts_usd, 2),
                                "RevenueUSD": round(revenue_usd, 2),
                                "DataSource": "Synthetic planning model",
                            }
                        )

                        carrier_cost = revenue_usd * service["CostRatio"] * (1 + cost_inflation)
                        handling_cost = jobs * rng.uniform(18, 72) * (1 + cost_inflation)
                        fuel_cost = revenue_usd * (0.026 + (0.020 if service["ServiceKey"] in {"AIR", "TRK"} else 0.010))
                        customs_cost = jobs * (28 if service["ServiceKey"] == "CUS" else rng.uniform(3, 10))
                        direct_cost = carrier_cost + handling_cost + fuel_cost + customs_cost

                        cost_rows.append(
                            {
                                "CostDriverKey": f"COST_{rev_key}",
                                "RevenueDriverKey": rev_key,
                                "MonthStart": month.date().isoformat(),
                                "PlanPeriod": plan_period,
                                "ScenarioKey": scenario_key,
                                "RegionKey": region["RegionKey"],
                                "ServiceKey": service["ServiceKey"],
                                "SegmentKey": segment["SegmentKey"],
                                "CarrierCostUSD": round(carrier_cost, 2),
                                "HandlingCostUSD": round(handling_cost, 2),
                                "FuelCostUSD": round(fuel_cost, 2),
                                "CustomsCostUSD": round(customs_cost, 2),
                                "DirectCostUSD": round(direct_cost, 2),
                                "VariableCostPerJobUSD": round(direct_cost / jobs, 2),
                                "CostInflationPct": round(cost_inflation, 4),
                            }
                        )

    return pd.DataFrame(revenue_rows), pd.DataFrame(cost_rows)


def build_headcount(rng: np.random.Generator, revenue: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict] = []
    monthly_volume = revenue.groupby(["MonthStart", "ScenarioKey", "RegionKey"], as_index=False)["VolumeJobs"].sum()
    monthly_volume["MonthStart"] = pd.to_datetime(monthly_volume["MonthStart"])

    for _, vol in monthly_volume.iterrows():
        month = vol["MonthStart"]
        scenario = next(s for s in SCENARIOS if s["ScenarioKey"] == vol["ScenarioKey"])
        region = next(r for r in REGIONS if r["RegionKey"] == vol["RegionKey"])
        month_index = (month.year - START_MONTH.year) * 12 + month.month - START_MONTH.month
        plan_period = "Actual" if month <= LATEST_ACTUAL_MONTH else "Forecast"
        volume_scale = vol["VolumeJobs"] / (sum(s["BaseJobs"] for s in SERVICES) * region["RegionWeight"] * 4)

        for dept in DEPARTMENTS:
            dept_factor = 1.0
            if dept["DepartmentKey"] == "OPS":
                dept_factor = 1.18
            elif dept["DepartmentKey"] in {"FIN", "IT", "MGT"}:
                dept_factor = 0.82
            if plan_period == "Actual":
                growth = 1 + 0.004 * month_index
                noise = rng.normal(1.0, 0.035)
                salary_growth = 1 + 0.003 * month_index
            else:
                forecast_month_index = (month.year - FORECAST_START_MONTH.year) * 12 + month.month - FORECAST_START_MONTH.month
                growth = 1 + scenario["HeadcountGrowthPct"] + 0.003 * forecast_month_index
                noise = 1.0
                salary_growth = 1 + scenario["SalaryInflationPct"] + 0.002 * forecast_month_index

            fte = max(1, round(dept["BaseFTE"] * region["RegionWeight"] * dept_factor * (0.65 + volume_scale * 0.35) * growth * noise, 1))
            new_hires = max(0, round(fte * (0.012 + (0.016 if plan_period == "Forecast" else 0.006)), 1))
            attrition = max(0, round(fte * (0.008 + (0.005 if dept["DepartmentKey"] == "SALES" else 0.002)), 1))
            avg_salary = dept["AvgSalaryUSD"] * salary_growth * (1.08 if region["RegionKey"] in {"CN", "TH"} else 1.0)
            payroll = fte * avg_salary

            rows.append(
                {
                    "HeadcountPlanKey": f"HC_{month:%Y%m}_{vol['ScenarioKey']}_{vol['RegionKey']}_{dept['DepartmentKey']}",
                    "MonthStart": month.date().isoformat(),
                    "PlanPeriod": plan_period,
                    "ScenarioKey": vol["ScenarioKey"],
                    "RegionKey": vol["RegionKey"],
                    "DepartmentKey": dept["DepartmentKey"],
                    "FTE": fte,
                    "NewHires": new_hires,
                    "Attrition": attrition,
                    "AvgSalaryUSD": round(avg_salary, 2),
                    "PayrollCostUSD": round(payroll, 2),
                    "JobsPerFTE": round(vol["VolumeJobs"] / max(fte, 1), 2),
                }
            )

    return pd.DataFrame(rows)


def build_opex(rng: np.random.Generator, headcount: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict] = []
    hc = headcount.copy()
    hc["MonthStart"] = pd.to_datetime(hc["MonthStart"])
    for _, row in hc.iterrows():
        month_index = (row["MonthStart"].year - START_MONTH.year) * 12 + row["MonthStart"].month - START_MONTH.month
        plan_period = row["PlanPeriod"]
        scenario = next(s for s in SCENARIOS if s["ScenarioKey"] == row["ScenarioKey"])
        inflation = 1 + 0.0025 * month_index
        if plan_period == "Forecast":
            inflation *= 1 + scenario["CostInflationPct"]
        fte = row["FTE"]
        dept = row["DepartmentKey"]
        rent = 3800 * (1.2 if row["RegionKey"] in {"VN_SOUTH", "CN"} else 0.85) * inflation
        software = fte * (42 if dept in {"IT", "FIN", "SALES"} else 18) * inflation
        marketing = (5200 if dept == "SALES" else 450) * inflation
        travel = fte * (115 if dept in {"SALES", "OPS"} else 35) * inflation
        ga = fte * 55 * inflation
        if plan_period == "Actual":
            rent *= rng.normal(1.0, 0.025)
            software *= rng.normal(1.0, 0.035)
            marketing *= rng.normal(1.0, 0.08)
            travel *= rng.normal(1.0, 0.07)
            ga *= rng.normal(1.0, 0.04)
        total = rent + software + marketing + travel + ga
        rows.append(
            {
                "OpexDriverKey": f"OPEX_{row['MonthStart']:%Y%m}_{row['ScenarioKey']}_{row['RegionKey']}_{dept}",
                "MonthStart": row["MonthStart"].date().isoformat(),
                "PlanPeriod": plan_period,
                "ScenarioKey": row["ScenarioKey"],
                "RegionKey": row["RegionKey"],
                "DepartmentKey": dept,
                "RentUSD": round(rent, 2),
                "SoftwareUSD": round(software, 2),
                "MarketingUSD": round(marketing, 2),
                "TravelUSD": round(travel, 2),
                "GAUSD": round(ga, 2),
                "NonPayrollOpexUSD": round(total, 2),
            }
        )

    return pd.DataFrame(rows)


def build_cash_impact(
    revenue: pd.DataFrame,
    cost: pd.DataFrame,
    headcount: pd.DataFrame,
    opex: pd.DataFrame,
) -> pd.DataFrame:
    rev = revenue.groupby(["MonthStart", "ScenarioKey", "PlanPeriod"], as_index=False)["RevenueUSD"].sum()
    direct = cost.groupby(["MonthStart", "ScenarioKey"], as_index=False)["DirectCostUSD"].sum()
    payroll = headcount.groupby(["MonthStart", "ScenarioKey"], as_index=False)["PayrollCostUSD"].sum()
    non_payroll = opex.groupby(["MonthStart", "ScenarioKey"], as_index=False)["NonPayrollOpexUSD"].sum()

    df = rev.merge(direct, on=["MonthStart", "ScenarioKey"]).merge(payroll, on=["MonthStart", "ScenarioKey"]).merge(non_payroll, on=["MonthStart", "ScenarioKey"])
    df["MonthStart"] = pd.to_datetime(df["MonthStart"])
    rows = []
    ending_cash_by_scenario: dict[str, float] = {}

    for _, row in df.sort_values(["ScenarioKey", "MonthStart"]).iterrows():
        scenario = next(s for s in SCENARIOS if s["ScenarioKey"] == row["ScenarioKey"])
        gross_profit = row["RevenueUSD"] - row["DirectCostUSD"]
        ebitda = gross_profit - row["PayrollCostUSD"] - row["NonPayrollOpexUSD"]
        tax_paid = max(0, ebitda * 0.17)
        capex = 32000 if row["MonthStart"].month in {3, 9} else 8500
        dso = 43 + scenario["DSODaysAdjustment"]
        dpo = 31 + scenario["DPODaysAdjustment"]
        working_capital = (row["RevenueUSD"] * dso / 30) - (row["DirectCostUSD"] * dpo / 30)
        prev_cash = ending_cash_by_scenario.get(row["ScenarioKey"], 1850000.0)
        operating_cash_flow = ebitda - tax_paid - (working_capital * 0.035)
        ending_cash = prev_cash + operating_cash_flow - capex
        ending_cash_by_scenario[row["ScenarioKey"]] = ending_cash
        rows.append(
            {
                "CashImpactKey": f"CASH_{row['MonthStart']:%Y%m}_{row['ScenarioKey']}",
                "MonthStart": row["MonthStart"].date().isoformat(),
                "PlanPeriod": row["PlanPeriod"],
                "ScenarioKey": row["ScenarioKey"],
                "RevenueUSD": round(row["RevenueUSD"], 2),
                "DirectCostUSD": round(row["DirectCostUSD"], 2),
                "PayrollCostUSD": round(row["PayrollCostUSD"], 2),
                "NonPayrollOpexUSD": round(row["NonPayrollOpexUSD"], 2),
                "GrossProfitUSD": round(gross_profit, 2),
                "EBITDAUSD": round(ebitda, 2),
                "TaxPaidUSD": round(tax_paid, 2),
                "CapexUSD": round(capex, 2),
                "DSODays": dso,
                "DPODays": dpo,
                "WorkingCapitalUSD": round(working_capital, 2),
                "OperatingCashFlowUSD": round(operating_cash_flow, 2),
                "EndingCashUSD": round(ending_cash, 2),
            }
        )

    return pd.DataFrame(rows)


def build_forecast_accuracy(rng: np.random.Generator, revenue: pd.DataFrame) -> pd.DataFrame:
    actual = revenue[revenue["ScenarioKey"] == "ACTUAL"].copy()
    months = pd.date_range("2025-01-01", LATEST_ACTUAL_MONTH, freq="MS")
    rows: list[dict] = []
    for month in months:
        month_actual = actual[actual["MonthStart"] == month.date().isoformat()]
        grouped = month_actual.groupby(["RegionKey", "ServiceKey"], as_index=False)["RevenueUSD"].sum()
        for _, row in grouped.iterrows():
            for horizon in [1, 2, 3]:
                bias = 0.012 * horizon
                forecast_error = rng.normal(loc=bias, scale=0.055 + 0.012 * horizon)
                forecast_revenue = row["RevenueUSD"] * (1 + forecast_error)
                abs_error = abs(forecast_revenue - row["RevenueUSD"])
                rows.append(
                    {
                        "ForecastAccuracyKey": f"FA_{month:%Y%m}_{horizon}M_{row['RegionKey']}_{row['ServiceKey']}",
                        "MonthStart": month.date().isoformat(),
                        "ForecastHorizonMonths": horizon,
                        "RegionKey": row["RegionKey"],
                        "ServiceKey": row["ServiceKey"],
                        "ScenarioKey": "BASE",
                        "ActualRevenueUSD": round(row["RevenueUSD"], 2),
                        "ForecastRevenueUSD": round(forecast_revenue, 2),
                        "ForecastErrorUSD": round(forecast_revenue - row["RevenueUSD"], 2),
                        "AbsoluteErrorUSD": round(abs_error, 2),
                        "AbsolutePctError": round(abs_error / row["RevenueUSD"], 5),
                        "ForecastBiasPct": round((forecast_revenue - row["RevenueUSD"]) / row["RevenueUSD"], 5),
                    }
                )
    return pd.DataFrame(rows)


def build_assumption_tables() -> dict[str, pd.DataFrame]:
    what_if = pd.DataFrame(
        [
            {"ParameterKey": "VOL_GROWTH", "Parameter": "Volume Growth %", "Unit": "%", "BaseValue": 0.060, "UpsideValue": 0.140, "DownsideValue": -0.080, "AppliesTo": "Revenue volume", "Description": "Multiplier applied to planned job volume."},
            {"ParameterKey": "RATE_CHANGE", "Parameter": "Average Rate Change %", "Unit": "%", "BaseValue": 0.000, "UpsideValue": 0.035, "DownsideValue": -0.035, "AppliesTo": "Revenue pricing", "Description": "Average selling rate change versus management case."},
            {"ParameterKey": "COST_INFLATION", "Parameter": "Direct Cost Inflation %", "Unit": "%", "BaseValue": 0.045, "UpsideValue": 0.030, "DownsideValue": 0.075, "AppliesTo": "Direct cost", "Description": "Carrier, fuel, handling and customs cost inflation."},
            {"ParameterKey": "HC_GROWTH", "Parameter": "Headcount Growth %", "Unit": "%", "BaseValue": 0.060, "UpsideValue": 0.085, "DownsideValue": 0.015, "AppliesTo": "Headcount", "Description": "FTE expansion versus current capacity."},
            {"ParameterKey": "SALARY_INFLATION", "Parameter": "Salary Inflation %", "Unit": "%", "BaseValue": 0.055, "UpsideValue": 0.060, "DownsideValue": 0.045, "AppliesTo": "Payroll cost", "Description": "Average salary increase in forecast period."},
            {"ParameterKey": "DSO", "Parameter": "DSO Days Adjustment", "Unit": "days", "BaseValue": 0, "UpsideValue": -3, "DownsideValue": 6, "AppliesTo": "Cash conversion", "Description": "Customer payment speed adjustment."},
            {"ParameterKey": "DPO", "Parameter": "DPO Days Adjustment", "Unit": "days", "BaseValue": 0, "UpsideValue": 2, "DownsideValue": -2, "AppliesTo": "Cash conversion", "Description": "Supplier payment timing adjustment."},
        ]
    )
    return {
        "Scenario_Assumptions": pd.DataFrame(SCENARIOS),
        "WhatIf_Parameters": what_if,
        "DimServices": pd.DataFrame(SERVICES),
        "DimRegions": pd.DataFrame(REGIONS),
        "DimSegments": pd.DataFrame(SEGMENTS),
        "DimDepartments": pd.DataFrame(DEPARTMENTS),
    }


def main() -> None:
    rng = np.random.default_rng(SEED)
    RAW_PATH.parent.mkdir(parents=True, exist_ok=True)

    revenue, cost = build_revenue_and_cost(rng)
    headcount = build_headcount(rng, revenue)
    opex = build_opex(rng, headcount)
    cash = build_cash_impact(revenue, cost, headcount, opex)
    accuracy = build_forecast_accuracy(rng, revenue)
    assumptions = build_assumption_tables()

    sheets = {
        "RevenueDrivers_Raw": revenue,
        "CostDrivers_Raw": cost,
        "HeadcountPlan_Raw": headcount,
        "OpexDrivers_Raw": opex,
        "CashImpact_Raw": cash,
        "ForecastAccuracy_Raw": accuracy,
        **assumptions,
    }

    with pd.ExcelWriter(RAW_PATH, engine="openpyxl") as writer:
        for sheet_name, frame in sheets.items():
            frame.to_excel(writer, sheet_name=sheet_name, index=False)

    print(f"Created raw workbook: {RAW_PATH}")
    for sheet_name, frame in sheets.items():
        print(f"{sheet_name}: {len(frame):,} rows x {len(frame.columns):,} columns")


if __name__ == "__main__":
    main()
