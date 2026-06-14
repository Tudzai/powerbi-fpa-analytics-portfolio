from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_PATH = PROJECT_ROOT / "data" / "raw" / "driver_forecasting_raw.xlsx"
SOURCE_SUMMARY_PATH = PROJECT_ROOT / "data" / "source_summary.json"
DATA_QUALITY_PATH = PROJECT_ROOT / "data" / "data_quality_report.md"
DATA_DICTIONARY_PATH = PROJECT_ROOT / "model" / "data_dictionary.md"

KEY_COLUMNS = ["Key", "MonthStart", "ScenarioKey", "RegionKey", "ServiceKey", "SegmentKey", "DepartmentKey"]


def infer_grain(sheet_name: str) -> str:
    mapping = {
        "RevenueDrivers_Raw": "one row per month, scenario, region, service line, customer segment",
        "CostDrivers_Raw": "one row per revenue driver row with direct cost components",
        "HeadcountPlan_Raw": "one row per month, scenario, region, department",
        "OpexDrivers_Raw": "one row per month, scenario, region, department",
        "CashImpact_Raw": "one row per month and scenario",
        "ForecastAccuracy_Raw": "one row per month, horizon, region, service line",
        "Scenario_Assumptions": "one row per planning scenario",
        "WhatIf_Parameters": "one row per configurable planning lever",
        "DimServices": "one row per service line",
        "DimRegions": "one row per operating region",
        "DimSegments": "one row per customer segment",
        "DimDepartments": "one row per department",
    }
    return mapping.get(sheet_name, "not classified")


def profile_sheet(sheet_name: str, df: pd.DataFrame) -> dict:
    date_min = None
    date_max = None
    if "MonthStart" in df.columns:
        dates = pd.to_datetime(df["MonthStart"], errors="coerce")
        date_min = dates.min().date().isoformat()
        date_max = dates.max().date().isoformat()

    primary_key = next((c for c in df.columns if c.endswith("Key") and c not in {"ScenarioKey", "RegionKey", "ServiceKey", "SegmentKey", "DepartmentKey"}), None)
    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    nulls = {c: int(v) for c, v in df.isna().sum().items() if v > 0}
    duplicate_keys = 0
    if primary_key:
        duplicate_keys = int(df[primary_key].duplicated().sum())

    return {
        "name": sheet_name,
        "rows": int(len(df)),
        "columns": int(len(df.columns)),
        "grain": infer_grain(sheet_name),
        "main_date_column": "MonthStart" if "MonthStart" in df.columns else None,
        "date_min": date_min,
        "date_max": date_max,
        "primary_key_candidate": primary_key,
        "duplicate_primary_keys": duplicate_keys,
        "numeric_columns": numeric_cols,
        "null_counts": nulls,
    }


def metric_totals(sheets: dict[str, pd.DataFrame]) -> dict:
    revenue = sheets["RevenueDrivers_Raw"]
    cost = sheets["CostDrivers_Raw"]
    headcount = sheets["HeadcountPlan_Raw"]
    opex = sheets["OpexDrivers_Raw"]
    cash = sheets["CashImpact_Raw"]
    actual_filter = revenue["ScenarioKey"] == "ACTUAL"
    base_filter = revenue["ScenarioKey"] == "BASE"
    return {
        "actual_revenue_usd": round(float(revenue.loc[actual_filter, "RevenueUSD"].sum()), 2),
        "actual_direct_cost_usd": round(float(cost.loc[cost["ScenarioKey"] == "ACTUAL", "DirectCostUSD"].sum()), 2),
        "forecast_base_revenue_usd": round(float(revenue.loc[base_filter, "RevenueUSD"].sum()), 2),
        "forecast_base_direct_cost_usd": round(float(cost.loc[cost["ScenarioKey"] == "BASE", "DirectCostUSD"].sum()), 2),
        "forecast_base_payroll_usd": round(float(headcount.loc[headcount["ScenarioKey"] == "BASE", "PayrollCostUSD"].sum()), 2),
        "forecast_base_non_payroll_opex_usd": round(float(opex.loc[opex["ScenarioKey"] == "BASE", "NonPayrollOpexUSD"].sum()), 2),
        "latest_base_ending_cash_usd": round(float(cash.loc[cash["ScenarioKey"] == "BASE"].sort_values("MonthStart")["EndingCashUSD"].iloc[-1]), 2),
        "actual_jobs": int(revenue.loc[actual_filter, "VolumeJobs"].sum()),
        "forecast_base_jobs": int(revenue.loc[base_filter, "VolumeJobs"].sum()),
    }


def build_quality_flags(profiles: list[dict], sheets: dict[str, pd.DataFrame]) -> list[str]:
    flags: list[str] = []
    for profile in profiles:
        if profile["duplicate_primary_keys"]:
            flags.append(f"{profile['name']}: {profile['duplicate_primary_keys']} duplicate primary keys")
        if profile["null_counts"]:
            flags.append(f"{profile['name']}: nulls detected {profile['null_counts']}")

    revenue = sheets["RevenueDrivers_Raw"]
    if (revenue["RevenueUSD"] <= 0).any():
        flags.append("RevenueDrivers_Raw: non-positive revenue rows detected")
    if (revenue["VolumeJobs"] <= 0).any():
        flags.append("RevenueDrivers_Raw: non-positive job volume rows detected")

    accuracy = sheets["ForecastAccuracy_Raw"]
    high_error = accuracy[accuracy["AbsolutePctError"] > 0.20]
    if not high_error.empty:
        flags.append(f"ForecastAccuracy_Raw: {len(high_error)} rows have absolute pct error above 20%; kept for accuracy monitoring")

    if not flags:
        flags.append("No blocking data quality issues found in synthetic source.")
    return flags


def write_data_dictionary(sheets: dict[str, pd.DataFrame]) -> None:
    lines = ["# Data Dictionary", "", "Generated from `data/raw/driver_forecasting_raw.xlsx`.", ""]
    for sheet_name, df in sheets.items():
        lines.append(f"## {sheet_name}")
        lines.append("")
        lines.append(f"- Grain: {infer_grain(sheet_name)}")
        lines.append(f"- Rows: {len(df):,}")
        lines.append("")
        lines.append("| Column | Type | Non-null | Example |")
        lines.append("|---|---:|---:|---|")
        for col in df.columns:
            sample = df[col].dropna().iloc[0] if df[col].dropna().shape[0] else ""
            lines.append(f"| {col} | {str(df[col].dtype)} | {df[col].notna().sum():,} | {sample} |")
        lines.append("")
    DATA_DICTIONARY_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    if not RAW_PATH.exists():
        raise FileNotFoundError(f"Missing raw workbook. Run 00_generate_synthetic_raw.py first: {RAW_PATH}")

    sheets = pd.read_excel(RAW_PATH, sheet_name=None)
    profiles = [profile_sheet(name, df) for name, df in sheets.items()]
    flags = build_quality_flags(profiles, sheets)
    totals = metric_totals(sheets)
    summary = {
        "source_files": [str(RAW_PATH.relative_to(PROJECT_ROOT)).replace("\\", "/")],
        "latest_actual_month": "2026-05-01",
        "forecast_horizon": {"start": "2026-06-01", "end": "2027-12-01"},
        "tables": profiles,
        "kpi_totals": totals,
        "data_quality_flags": flags,
    }

    SOURCE_SUMMARY_PATH.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    write_data_dictionary(sheets)

    lines = [
        "# Data Quality Report",
        "",
        "## Source Inventory",
        "",
        "| Sheet | Rows | Columns | Grain | Date Range | Duplicate Key Count |",
        "|---|---:|---:|---|---|---:|",
    ]
    for p in profiles:
        date_range = f"{p['date_min']} to {p['date_max']}" if p["date_min"] else "n/a"
        lines.append(f"| {p['name']} | {p['rows']:,} | {p['columns']:,} | {p['grain']} | {date_range} | {p['duplicate_primary_keys']:,} |")

    lines.extend(["", "## KPI Totals", ""])
    for key, value in totals.items():
        lines.append(f"- {key}: {value:,}" if isinstance(value, int) else f"- {key}: {value:,.2f}")

    lines.extend(["", "## Data Quality Flags", ""])
    lines.extend([f"- {flag}" for flag in flags])
    lines.extend(
        [
            "",
            "## QA Decision",
            "",
            "Synthetic source is accepted for portfolio build. High forecast-error rows are intentionally retained so the Forecast Accuracy page can show real monitoring behavior.",
        ]
    )
    DATA_QUALITY_PATH.write_text("\n".join(lines), encoding="utf-8")

    print(f"Wrote {SOURCE_SUMMARY_PATH}")
    print(f"Wrote {DATA_QUALITY_PATH}")
    print(f"Wrote {DATA_DICTIONARY_PATH}")


if __name__ == "__main__":
    main()
