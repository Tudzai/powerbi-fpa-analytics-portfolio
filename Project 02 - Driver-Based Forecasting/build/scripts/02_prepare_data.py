from __future__ import annotations

from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_PATH = PROJECT_ROOT / "data" / "raw" / "driver_forecasting_raw.xlsx"
PREPARED_DIR = PROJECT_ROOT / "data" / "prepared"


def add_date_keys(df: pd.DataFrame) -> pd.DataFrame:
    if "MonthStart" not in df.columns:
        return df
    out = df.copy()
    out["MonthStart"] = pd.to_datetime(out["MonthStart"]).dt.date.astype(str)
    out["DateKey"] = out["MonthStart"].str.replace("-", "", regex=False).astype(int)
    out["YearMonth"] = out["MonthStart"].str.slice(0, 7)
    return out


def build_dim_date(start: str = "2024-01-01", end: str = "2027-12-31") -> pd.DataFrame:
    dates = pd.date_range(start=start, end=end, freq="D")
    dim = pd.DataFrame({"Date": dates})
    dim["DateKey"] = dim["Date"].dt.strftime("%Y%m%d").astype(int)
    dim["MonthStart"] = dim["Date"].dt.to_period("M").dt.to_timestamp().dt.date.astype(str)
    dim["Year"] = dim["Date"].dt.year
    dim["Quarter"] = "Q" + dim["Date"].dt.quarter.astype(str)
    dim["MonthNumber"] = dim["Date"].dt.month
    dim["MonthName"] = dim["Date"].dt.strftime("%b")
    dim["YearMonth"] = dim["Date"].dt.strftime("%Y-%m")
    dim["MonthSort"] = dim["Date"].dt.strftime("%Y%m").astype(int)
    dim["IsLatestActualMonth"] = dim["MonthStart"].eq("2026-05-01")
    dim["IsForecastMonth"] = dim["Date"] >= pd.Timestamp("2026-06-01")
    dim["FiscalYear"] = dim["Year"]
    return dim


def clean_currency_cols(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for col in out.columns:
        if col.endswith("USD") or col.endswith("Pct") or col in {"FTE", "NewHires", "Attrition", "JobsPerFTE", "VolumeJobs", "TEU", "CBM", "ChargeableKg"}:
            out[col] = pd.to_numeric(out[col], errors="coerce").round(4)
    return out


def main() -> None:
    if not RAW_PATH.exists():
        raise FileNotFoundError(f"Missing raw workbook. Run 00_generate_synthetic_raw.py first: {RAW_PATH}")
    PREPARED_DIR.mkdir(parents=True, exist_ok=True)
    sheets = pd.read_excel(RAW_PATH, sheet_name=None)

    prepared = {
        "fact_revenue_driver": sheets["RevenueDrivers_Raw"],
        "fact_cost_driver": sheets["CostDrivers_Raw"],
        "fact_headcount_plan": sheets["HeadcountPlan_Raw"],
        "fact_opex_driver": sheets["OpexDrivers_Raw"],
        "fact_cash_impact": sheets["CashImpact_Raw"],
        "fact_forecast_accuracy": sheets["ForecastAccuracy_Raw"],
        "dim_scenario": sheets["Scenario_Assumptions"],
        "what_if_parameters": sheets["WhatIf_Parameters"],
        "dim_service": sheets["DimServices"],
        "dim_region": sheets["DimRegions"],
        "dim_customer_segment": sheets["DimSegments"],
        "dim_department": sheets["DimDepartments"],
        "dim_date": build_dim_date(),
    }

    for name, df in prepared.items():
        out = add_date_keys(clean_currency_cols(df))
        out_path = PREPARED_DIR / f"{name}.csv"
        out.to_csv(out_path, index=False, encoding="utf-8-sig")
        print(f"Wrote {out_path} ({len(out):,} rows)")


if __name__ == "__main__":
    main()
