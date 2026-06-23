from __future__ import annotations

import json
import math
import os
import random
import shutil
import subprocess
import tempfile
import uuid
import zipfile
from collections import Counter
from datetime import datetime
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
PORTFOLIO_ROOT = ROOT.parents[2]
TEMPLATE_ROOT = ROOT.parent / "Template"
SEED = 160416
TODAY = "2026-06-15"
LATEST_MONTH = "2026-05"
PREVIOUS_MONTH = "2026-04"
MEASURE_TABLE = "KPI Measures"

COLORS = {
    "bg": "#F6F7F9",
    "panel": "#FFFFFF",
    "pale": "#F8FAFC",
    "card": "#FFFFFF",
    "ink": "#111827",
    "muted": "#667085",
    "line": "#D9DEE7",
    "chart_grid": "#E2E8F0",
    "table_header": "#F1F5F9",
    "table_row": "#FFFFFF",
    "table_alt": "#F8FAFC",
    "track": "#E5E7EB",
    "steel": "#2563EB",
    "teal": "#0F766E",
    "amber": "#D97706",
    "red": "#DC2626",
    "slate": "#475569",
    "violet": "#7C3AED",
    "green": "#16A34A",
    "charcoal": "#1F2937",
}


def p(rel: str) -> Path:
    return ROOT / rel


def ensure_dirs() -> None:
    for rel in [
        "_agent",
        "data/raw",
        "data/prepared",
        "data/validated",
        "data/synthetic",
        "data/profile",
        "model",
        "build/scripts",
        "build/config",
        "build/pbix_work",
        "powerbi/notes",
        "powerbi/seed",
        "output/screenshots",
        "output/exports",
        "qa",
        "docs",
        "archive/old_versions",
    ]:
        p(rel).mkdir(parents=True, exist_ok=True)


def write_text(rel: str, content: str) -> None:
    path = p(rel)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.strip() + "\n", encoding="utf-8")


def write_json(rel: str, payload: object) -> None:
    path = p(rel)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def write_csv(rel: str, df: pd.DataFrame) -> None:
    path = p(rel)
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)


def money(value: float) -> str:
    sign = "-" if value < 0 else ""
    value = abs(float(value))
    if value >= 1_000_000:
        return f"{sign}${value / 1_000_000:,.1f}M"
    if value >= 1_000:
        return f"{sign}${value / 1_000:,.1f}K"
    return f"{sign}${value:,.0f}"


def num(value: float) -> str:
    value = float(value)
    if abs(value) >= 1_000_000:
        return f"{value / 1_000_000:,.1f}M"
    if abs(value) >= 1_000:
        return f"{value / 1_000:,.1f}K"
    return f"{value:,.0f}"


def pct(value: float) -> str:
    return f"{float(value) * 100:,.1f}%"


def month_sequence() -> pd.DataFrame:
    months = pd.date_range("2024-01-01", "2026-05-01", freq="MS")
    return pd.DataFrame(
        {
            "date_key": [int(d.strftime("%Y%m%d")) for d in months],
            "month_start_date": months.strftime("%Y-%m-%d"),
            "year_month": months.strftime("%Y-%m"),
            "year": months.year,
            "quarter": [f"Q{q}" for q in months.quarter],
            "month_no": months.month,
            "month_name": months.strftime("%b"),
            "month_index": range(1, len(months) + 1),
            "is_latest_complete_month": [1 if ym == LATEST_MONTH else 0 for ym in months.strftime("%Y-%m")],
        }
    )


def generate_dimensions() -> dict[str, pd.DataFrame]:
    rng = np.random.default_rng(SEED)
    py_rng = random.Random(SEED)

    dim_date = month_sequence()

    plants = [
        ("P01", "Bac Ninh Electronics", "Vietnam North", "Vietnam", 0.96, 4.9, 18.0, 1.05),
        ("P02", "HCMC Precision", "Vietnam South", "Vietnam", 1.00, 5.4, 20.0, 1.00),
        ("P03", "Da Nang Assembly", "Vietnam Central", "Vietnam", 0.92, 4.7, 17.5, 1.10),
        ("P04", "Rayong Components", "Thailand", "Thailand", 1.08, 6.1, 22.0, 0.95),
        ("P05", "Johor Packaging Systems", "Malaysia", "Malaysia", 1.03, 5.8, 21.0, 1.02),
    ]
    dim_plant = pd.DataFrame(
        plants,
        columns=[
            "plant_id",
            "plant_name",
            "region",
            "country",
            "productivity_index",
            "labor_rate_usd",
            "fixed_overhead_rate_usd",
            "material_price_index",
        ],
    )

    family_specs = [
        ("Electronics Assembly", "Controller", 72, 31, 0.38, 0.28, 1.10),
        ("Electronics Assembly", "Sensor Module", 44, 17, 0.30, 0.18, 0.92),
        ("Industrial Components", "Pump Housing", 118, 49, 0.72, 0.55, 1.25),
        ("Industrial Components", "Valve Set", 86, 36, 0.52, 0.38, 1.06),
        ("Packaging Systems", "Film Cartridge", 28, 9, 0.16, 0.12, 0.80),
        ("Packaging Systems", "Label Applicator", 135, 54, 0.82, 0.66, 1.32),
        ("Precision Parts", "CNC Bracket", 64, 24, 0.44, 0.42, 1.02),
        ("Precision Parts", "Machined Shaft", 96, 41, 0.62, 0.56, 1.18),
    ]
    products = []
    product_id = 1
    for family, base_name, base_price, base_material, labor_hours, machine_hours, complexity in family_specs:
        for variant in ["A", "B", "C"]:
            price = base_price * rng.uniform(0.88, 1.18)
            material = base_material * rng.uniform(0.90, 1.16)
            products.append(
                {
                    "product_id": f"SKU{product_id:03d}",
                    "product": f"{base_name} {variant}",
                    "product_line": family,
                    "lifecycle_stage": py_rng.choice(["Growth", "Core", "Mature", "Rationalize"]),
                    "standard_price_usd": round(price, 2),
                    "standard_material_cost_usd": round(material, 2),
                    "standard_labor_hours": round(labor_hours * rng.uniform(0.90, 1.12), 3),
                    "standard_machine_hours": round(machine_hours * rng.uniform(0.88, 1.15), 3),
                    "complexity_index": round(complexity * rng.uniform(0.92, 1.16), 3),
                    "base_monthly_units": int(rng.integers(1800, 7200) / complexity),
                }
            )
            product_id += 1
    dim_product = pd.DataFrame(products)

    line_specs = [
        ("L01", "P01", "SMT Line 1", "Electronics Assembly", 89000, 2.1),
        ("L02", "P01", "SMT Line 2", "Electronics Assembly", 76000, 2.0),
        ("L03", "P02", "CNC Cell 1", "Precision Parts", 43000, 2.4),
        ("L04", "P02", "CNC Cell 2", "Precision Parts", 39000, 2.2),
        ("L05", "P02", "Assembly Cell", "Industrial Components", 34000, 2.0),
        ("L06", "P03", "Mixed Assembly", "Electronics Assembly", 54000, 1.8),
        ("L07", "P03", "Packaging Cell", "Packaging Systems", 63000, 1.7),
        ("L08", "P04", "Foundry Cell", "Industrial Components", 28000, 2.5),
        ("L09", "P04", "Machining Cell", "Precision Parts", 36000, 2.3),
        ("L10", "P05", "Packaging Line 1", "Packaging Systems", 92000, 2.0),
        ("L11", "P05", "Packaging Line 2", "Packaging Systems", 84000, 2.0),
        ("L12", "P05", "Final Assembly", "Industrial Components", 31000, 1.9),
    ]
    dim_line = pd.DataFrame(
        line_specs,
        columns=["line_id", "plant_id", "line_name", "product_line", "monthly_capacity_units", "shift_count"],
    ).merge(dim_plant[["plant_id", "plant_name"]], on="plant_id", how="left")

    dim_scenario = pd.DataFrame(
        [
            ["S00", "Base", 0.000, 0.000, 0.000, 0.000, 0.000, "Current run rate."],
            ["S01", "Supplier renegotiation", 0.035, 0.000, 0.000, 0.000, -0.004, "Reduce material price with limited supply friction."],
            ["S02", "Yield recovery sprint", 0.000, 0.000, 0.000, 0.180, 0.006, "Scrap/rework kaizen on the highest variance lines."],
            ["S03", "Overtime control", 0.000, 0.075, 0.000, 0.030, -0.010, "Reduce overtime and stabilize schedules."],
            ["S04", "Capacity leveling", 0.000, 0.025, 0.060, 0.050, 0.018, "Move demand from constrained lines to available capacity."],
            ["S05", "Full cost reset", 0.045, 0.060, 0.055, 0.120, 0.010, "Combined procurement, labor, overhead, and yield program."],
        ],
        columns=[
            "scenario_id",
            "scenario_name",
            "material_cost_reduction_pct",
            "labor_efficiency_gain_pct",
            "overhead_absorption_gain_pct",
            "scrap_reduction_pct",
            "volume_delta_pct",
            "description",
        ],
    )

    dim_spark_date = dim_date.copy()

    return {
        "dim_date": dim_date,
        "dim_spark_date": dim_spark_date,
        "dim_plant": dim_plant,
        "dim_product": dim_product,
        "dim_line": dim_line,
        "dim_scenario": dim_scenario,
    }


def generate_facts(dims: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    rng = np.random.default_rng(SEED + 1)
    dates = dims["dim_date"]
    plants = dims["dim_plant"].set_index("plant_id")
    products = dims["dim_product"]
    lines = dims["dim_line"]

    seasonality = {1: 0.89, 2: 0.92, 3: 1.01, 4: 1.03, 5: 1.04, 6: 1.08, 7: 1.07, 8: 1.06, 9: 1.03, 10: 1.11, 11: 1.16, 12: 1.20}
    family_demand = {
        "Electronics Assembly": 1.18,
        "Industrial Components": 0.86,
        "Packaging Systems": 1.02,
        "Precision Parts": 0.94,
    }
    rows = []
    for _, line in lines.iterrows():
        plant = plants.loc[line.plant_id]
        compatible = products[products.product_line.eq(line.product_line)].copy()
        compatible["mix_weight"] = compatible["base_monthly_units"] * rng.uniform(0.85, 1.20, size=len(compatible))
        compatible["mix_share"] = compatible["mix_weight"] / compatible["mix_weight"].sum()
        for _, month in dates.iterrows():
            month_index = int(month.month_index)
            trend = 1 + (month_index - 1) * 0.006
            family_factor = family_demand[line.product_line]
            maintenance_drag = 0.94 if month.month_no in [2, 8] and rng.random() < 0.35 else 1.0
            for _, product in compatible.iterrows():
                capacity_units = line.monthly_capacity_units * product.mix_share * maintenance_drag
                budget_units = capacity_units * rng.uniform(0.70, 0.88) * seasonality[int(month.month_no)] * trend * family_factor
                actual_units = budget_units * rng.normal(1.0, 0.075)
                actual_units *= 0.94 if plant.region == "Vietnam Central" and month.year_month in ["2024-10", "2024-11"] else 1.0
                actual_units = max(120, actual_units)

                utilization_raw = actual_units / max(capacity_units, 1)
                overload = max(0, utilization_raw - 0.88)
                base_scrap = 0.018 + 0.012 * product.complexity_index + 0.016 * overload
                scrap_rate = float(np.clip(rng.normal(base_scrap, 0.006), 0.006, 0.115))
                rework_rate = float(np.clip(scrap_rate * rng.uniform(0.25, 0.42), 0.002, 0.045))
                scrap_units = actual_units * scrap_rate
                rework_units = actual_units * rework_rate
                good_units = max(0, actual_units - scrap_units)

                price_realization = rng.normal(1.0, 0.012)
                actual_revenue = good_units * product.standard_price_usd * price_realization
                budget_revenue = budget_units * product.standard_price_usd

                std_material = actual_units * product.standard_material_cost_usd
                std_labor = actual_units * product.standard_labor_hours * plant.labor_rate_usd
                std_overhead = actual_units * product.standard_machine_hours * plant.fixed_overhead_rate_usd
                standard_cogs = std_material + std_labor + std_overhead

                material_var_pct = rng.normal(0.025 * plant.material_price_index, 0.035)
                if month.year_month >= "2025-10":
                    material_var_pct += 0.018
                actual_material = std_material * (1 + material_var_pct)

                labor_eff_pct = rng.normal(0.018 / plant.productivity_index, 0.045) + 0.04 * overload
                overtime_pct = max(0, utilization_raw - 0.82) * rng.uniform(0.16, 0.30)
                actual_labor = std_labor * (1 + labor_eff_pct) * (1 + overtime_pct)

                overhead_absorption_pct = rng.normal(0.010, 0.030) - max(0, 0.78 - utilization_raw) * 0.10
                actual_overhead = std_overhead * (1 + overhead_absorption_pct)
                scrap_cost = scrap_units * (product.standard_material_cost_usd + product.standard_labor_hours * plant.labor_rate_usd * 0.55)
                rework_cost = rework_units * product.standard_labor_hours * plant.labor_rate_usd * rng.uniform(0.45, 0.75)
                actual_cogs = actual_material + actual_labor + actual_overhead + scrap_cost + rework_cost

                available_hours = line.shift_count * 8 * 21.5
                run_hours = actual_units * product.standard_machine_hours / max(plant.productivity_index * 14.5, 1)
                downtime_hours = max(0, available_hours * (0.045 + 0.08 * overload + rng.normal(0, 0.010)))
                utilization = min(1.20, run_hours / max(available_hours, 1))

                inventory_units = max(0, good_units * rng.uniform(0.45, 1.35) + capacity_units * rng.uniform(0.02, 0.10))
                inventory_value = inventory_units * (standard_cogs / max(actual_units, 1)) * rng.uniform(0.92, 1.08)
                slow_moving_value = inventory_value * max(0, rng.normal(0.08 + 0.09 * (1 if product.lifecycle_stage == "Rationalize" else 0), 0.035))

                rows.append(
                    {
                        "date_key": int(month.date_key),
                        "month_start_date": month.month_start_date,
                        "year_month": month.year_month,
                        "month_index": month_index,
                        "plant_id": line.plant_id,
                        "line_id": line.line_id,
                        "product_id": product.product_id,
                        "budget_units": round(budget_units, 0),
                        "produced_units": round(actual_units, 0),
                        "good_units": round(good_units, 0),
                        "scrap_units": round(scrap_units, 0),
                        "rework_units": round(rework_units, 0),
                        "capacity_units": round(capacity_units, 0),
                        "available_hours": round(available_hours, 2),
                        "run_hours": round(run_hours, 2),
                        "downtime_hours": round(downtime_hours, 2),
                        "actual_revenue": round(actual_revenue, 2),
                        "budget_revenue": round(budget_revenue, 2),
                        "standard_material_cost": round(std_material, 2),
                        "standard_labor_cost": round(std_labor, 2),
                        "standard_overhead_cost": round(std_overhead, 2),
                        "standard_cogs": round(standard_cogs, 2),
                        "actual_material_cost": round(actual_material, 2),
                        "actual_labor_cost": round(actual_labor, 2),
                        "actual_overhead_cost": round(actual_overhead, 2),
                        "scrap_cost": round(scrap_cost, 2),
                        "rework_cost": round(rework_cost, 2),
                        "actual_cogs": round(actual_cogs, 2),
                        "material_variance": round(actual_material - std_material, 2),
                        "labor_variance": round(actual_labor - std_labor, 2),
                        "overhead_variance": round(actual_overhead - std_overhead, 2),
                        "yield_loss_cost": round(scrap_cost + rework_cost, 2),
                        "gross_margin": round(actual_revenue - actual_cogs, 2),
                        "inventory_units": round(inventory_units, 0),
                        "inventory_value": round(inventory_value, 2),
                        "slow_moving_inventory_value": round(slow_moving_value, 2),
                    }
                )

    fact = pd.DataFrame(rows)
    latest = fact[fact.year_month.eq(LATEST_MONTH)]
    bridge_rows = [
        [LATEST_MONTH, 1, "Standard COGS", latest.standard_cogs.sum(), "start"],
        [LATEST_MONTH, 2, "Material price / usage", latest.material_variance.sum(), "increase" if latest.material_variance.sum() >= 0 else "decrease"],
        [LATEST_MONTH, 3, "Labor efficiency", latest.labor_variance.sum(), "increase" if latest.labor_variance.sum() >= 0 else "decrease"],
        [LATEST_MONTH, 4, "OH absorption", latest.overhead_variance.sum(), "increase" if latest.overhead_variance.sum() >= 0 else "decrease"],
        [LATEST_MONTH, 5, "Yield / scrap loss", latest.yield_loss_cost.sum(), "increase"],
        [LATEST_MONTH, 6, "Actual COGS", latest.actual_cogs.sum(), "total"],
    ]
    bridge = pd.DataFrame(bridge_rows, columns=["year_month", "bridge_order", "bridge_step", "bridge_amount", "bridge_type"])
    return {"fact_manufacturing_month": fact, "fact_cost_variance_bridge": bridge}


def enrich_exports(dims: dict[str, pd.DataFrame], facts: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    fact = facts["fact_manufacturing_month"]
    enriched = (
        fact.merge(dims["dim_plant"], on="plant_id", how="left")
        .merge(dims["dim_line"][["line_id", "plant_id", "line_name"]], on=["line_id", "plant_id"], how="left")
        .merge(dims["dim_product"], on="product_id", how="left")
    )
    latest = enriched[enriched.year_month.eq(LATEST_MONTH)].copy()
    product = latest.groupby(["product_id", "product", "product_line"], as_index=False).agg(
        actual_revenue=("actual_revenue", "sum"),
        actual_cogs=("actual_cogs", "sum"),
        standard_cogs=("standard_cogs", "sum"),
        gross_margin=("gross_margin", "sum"),
        good_units=("good_units", "sum"),
        cost_variance=("material_variance", "sum"),
        yield_loss_cost=("yield_loss_cost", "sum"),
        inventory_value=("inventory_value", "sum"),
    )
    product["gross_margin_pct"] = product["gross_margin"] / product["actual_revenue"]
    product["unit_cost"] = product["actual_cogs"] / product["good_units"]

    line = latest.groupby(["plant_name", "line_name", "product_line"], as_index=False).agg(
        produced_units=("produced_units", "sum"),
        good_units=("good_units", "sum"),
        scrap_units=("scrap_units", "sum"),
        run_hours=("run_hours", "sum"),
        available_hours=("available_hours", "sum"),
        downtime_hours=("downtime_hours", "sum"),
        cost_variance=("material_variance", "sum"),
        actual_cogs=("actual_cogs", "sum"),
        inventory_value=("inventory_value", "sum"),
    )
    line["yield_pct"] = line["good_units"] / line["produced_units"]
    line["scrap_rate"] = line["scrap_units"] / line["produced_units"]
    line["utilization_pct"] = line["run_hours"] / line["available_hours"]
    line["inventory_days"] = 30 * line["inventory_value"] / line["actual_cogs"]
    line["action_priority_score"] = (
        (1 - line["yield_pct"]) * 40
        + line["scrap_rate"] * 50
        + line["utilization_pct"].clip(lower=0.88) * 10
        + line["inventory_days"].clip(upper=90) / 9
    )
    return {
        "latest_product_margin": product.sort_values("gross_margin", ascending=False),
        "latest_line_watchlist": line.sort_values("action_priority_score", ascending=False),
        "latest_enriched_detail": latest,
    }


def profile_tables(tables: dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows = []
    for name, df in tables.items():
        rows.append(
            {
                "table": name,
                "rows": len(df),
                "columns": len(df.columns),
                "duplicate_rows": int(df.duplicated().sum()),
                "missing_cells": int(df.isna().sum().sum()),
                "date_min": str(df["month_start_date"].min()) if "month_start_date" in df.columns else "",
                "date_max": str(df["month_start_date"].max()) if "month_start_date" in df.columns else "",
            }
        )
    return pd.DataFrame(rows)


def validate_data(dims: dict[str, pd.DataFrame], facts: dict[str, pd.DataFrame]) -> dict:
    fact = facts["fact_manufacturing_month"]
    latest = fact[fact.year_month.eq(LATEST_MONTH)]
    bridge = facts["fact_cost_variance_bridge"]
    duplicate_keys = int(fact.duplicated(["year_month", "plant_id", "line_id", "product_id"]).sum())
    required_missing = int(
        fact[
            [
                "actual_revenue",
                "actual_cogs",
                "standard_cogs",
                "good_units",
                "scrap_units",
                "inventory_value",
            ]
        ].isna().sum().sum()
    )
    variance_tie = float(
        abs(
            latest.actual_cogs.sum()
            - (
                latest.standard_cogs.sum()
                + latest.material_variance.sum()
                + latest.labor_variance.sum()
                + latest.overhead_variance.sum()
                + latest.yield_loss_cost.sum()
            )
        )
    )
    bridge_tie = float(abs(bridge.loc[bridge.bridge_step.eq("Actual COGS"), "bridge_amount"].iloc[0] - latest.actual_cogs.sum()))
    checks = [
        {"check": "fact key uniqueness", "status": "PASS" if duplicate_keys == 0 else "FAIL", "value": duplicate_keys},
        {"check": "critical missing values", "status": "PASS" if required_missing == 0 else "FAIL", "value": required_missing},
        {"check": "latest month exists", "status": "PASS" if len(latest) > 0 else "FAIL", "value": len(latest)},
        {"check": "variance tie-out", "status": "PASS" if variance_tie < 5 else "FAIL", "value": round(variance_tie, 2)},
        {"check": "bridge actual cogs tie-out", "status": "PASS" if bridge_tie < 1 else "FAIL", "value": round(bridge_tie, 2)},
    ]
    return {
        "status": "PASS" if all(c["status"] == "PASS" for c in checks) else "FAIL",
        "checks": checks,
        "row_counts": {name: len(df) for name, df in {**dims, **facts}.items()},
        "date_range": {
            "start": str(fact.month_start_date.min()),
            "end": str(fact.month_start_date.max()),
            "latest_complete_month": LATEST_MONTH,
        },
    }


def metric_snapshot(facts: dict[str, pd.DataFrame]) -> dict:
    fact = facts["fact_manufacturing_month"]
    cur = fact[fact.year_month.eq(LATEST_MONTH)]
    prev = fact[fact.year_month.eq(PREVIOUS_MONTH)]

    def snap(df: pd.DataFrame) -> dict[str, float]:
        revenue = float(df.actual_revenue.sum())
        cogs = float(df.actual_cogs.sum())
        std = float(df.standard_cogs.sum())
        gm = float(df.gross_margin.sum())
        produced = float(df.produced_units.sum())
        good = float(df.good_units.sum())
        scrap = float(df.scrap_units.sum())
        run_hours = float(df.run_hours.sum())
        avail_hours = float(df.available_hours.sum())
        inv = float(df.inventory_value.sum())
        return {
            "actual_revenue": revenue,
            "actual_cogs": cogs,
            "standard_cogs": std,
            "cost_variance": cogs - std,
            "gross_margin": gm,
            "gross_margin_pct": gm / revenue if revenue else 0,
            "good_units": good,
            "produced_units": produced,
            "yield_pct": good / produced if produced else 0,
            "scrap_rate": scrap / produced if produced else 0,
            "unit_cost": cogs / good if good else 0,
            "utilization_pct": run_hours / avail_hours if avail_hours else 0,
            "inventory_value": inv,
            "inventory_days": 30 * inv / cogs if cogs else 0,
            "material_variance": float(df.material_variance.sum()),
            "labor_variance": float(df.labor_variance.sum()),
            "overhead_variance": float(df.overhead_variance.sum()),
            "yield_loss_cost": float(df.yield_loss_cost.sum()),
            "capacity_gap_units": float(df.capacity_units.sum() - df.produced_units.sum()),
            "slow_moving_inventory_value": float(df.slow_moving_inventory_value.sum()),
        }

    current = snap(cur)
    previous = snap(prev)
    current["mom_gross_margin_growth"] = (current["gross_margin"] - previous["gross_margin"]) / previous["gross_margin"]
    current["mom_cost_variance_growth"] = (current["cost_variance"] - previous["cost_variance"]) / abs(previous["cost_variance"])
    return {"current": current, "previous": previous}


def dax_measures() -> str:
    return r"""
```DAX
Actual Revenue = SUM ( fact_manufacturing_month[actual_revenue] )
Budget Revenue = SUM ( fact_manufacturing_month[budget_revenue] )
Actual COGS = SUM ( fact_manufacturing_month[actual_cogs] )
Standard COGS = SUM ( fact_manufacturing_month[standard_cogs] )
Actual Material Cost = SUM ( fact_manufacturing_month[actual_material_cost] )
Actual Labor Cost = SUM ( fact_manufacturing_month[actual_labor_cost] )
Actual Overhead Cost = SUM ( fact_manufacturing_month[actual_overhead_cost] )
Scrap Cost = SUM ( fact_manufacturing_month[scrap_cost] )
Rework Cost = SUM ( fact_manufacturing_month[rework_cost] )
Yield Loss Cost = SUM ( fact_manufacturing_month[yield_loss_cost] )
Material Variance = SUM ( fact_manufacturing_month[material_variance] )
Labor Variance = SUM ( fact_manufacturing_month[labor_variance] )
Overhead Variance = SUM ( fact_manufacturing_month[overhead_variance] )
Cost Variance vs Standard = [Actual COGS] - [Standard COGS]
Gross Margin = [Actual Revenue] - [Actual COGS]
Gross Margin % = DIVIDE ( [Gross Margin], [Actual Revenue] )
Produced Units = SUM ( fact_manufacturing_month[produced_units] )
Good Units = SUM ( fact_manufacturing_month[good_units] )
Scrap Units = SUM ( fact_manufacturing_month[scrap_units] )
Rework Units = SUM ( fact_manufacturing_month[rework_units] )
Yield % = DIVIDE ( [Good Units], [Produced Units] )
Scrap Rate = DIVIDE ( [Scrap Units], [Produced Units] )
Unit Cost = DIVIDE ( [Actual COGS], [Good Units] )
Standard Unit Cost = DIVIDE ( [Standard COGS], [Good Units] )
Run Hours = SUM ( fact_manufacturing_month[run_hours] )
Available Hours = SUM ( fact_manufacturing_month[available_hours] )
Downtime Hours = SUM ( fact_manufacturing_month[downtime_hours] )
Utilization % = DIVIDE ( [Run Hours], [Available Hours] )
Capacity Units = SUM ( fact_manufacturing_month[capacity_units] )
Capacity Gap Units = [Capacity Units] - [Produced Units]
Inventory Value = SUM ( fact_manufacturing_month[inventory_value] )
Slow Moving Inventory = SUM ( fact_manufacturing_month[slow_moving_inventory_value] )
Inventory Days = DIVIDE ( [Inventory Value], [Actual COGS] ) * 30
Bridge Amount = SUM ( fact_cost_variance_bridge[bridge_amount] )
Current Month Index = COALESCE ( SELECTEDVALUE ( dim_date[month_index] ), MAXX ( ALL ( dim_date ), dim_date[month_index] ) )
Current Revenue = VAR CurrentMonth = [Current Month Index] RETURN CALCULATE ( [Actual Revenue], FILTER ( ALL ( dim_date ), dim_date[month_index] = CurrentMonth ) )
Current Actual COGS = VAR CurrentMonth = [Current Month Index] RETURN CALCULATE ( [Actual COGS], FILTER ( ALL ( dim_date ), dim_date[month_index] = CurrentMonth ) )
Current Standard COGS = VAR CurrentMonth = [Current Month Index] RETURN CALCULATE ( [Standard COGS], FILTER ( ALL ( dim_date ), dim_date[month_index] = CurrentMonth ) )
Current Gross Margin = VAR CurrentMonth = [Current Month Index] RETURN CALCULATE ( [Gross Margin], FILTER ( ALL ( dim_date ), dim_date[month_index] = CurrentMonth ) )
Current GM % = DIVIDE ( [Current Gross Margin], [Current Revenue] )
Current Cost Variance = [Current Actual COGS] - [Current Standard COGS]
Current Unit Cost = VAR CurrentMonth = [Current Month Index] RETURN CALCULATE ( [Unit Cost], FILTER ( ALL ( dim_date ), dim_date[month_index] = CurrentMonth ) )
Current Yield % = VAR CurrentMonth = [Current Month Index] RETURN CALCULATE ( [Yield %], FILTER ( ALL ( dim_date ), dim_date[month_index] = CurrentMonth ) )
Current Scrap Rate = VAR CurrentMonth = [Current Month Index] RETURN CALCULATE ( [Scrap Rate], FILTER ( ALL ( dim_date ), dim_date[month_index] = CurrentMonth ) )
Current Utilization % = VAR CurrentMonth = [Current Month Index] RETURN CALCULATE ( [Utilization %], FILTER ( ALL ( dim_date ), dim_date[month_index] = CurrentMonth ) )
Current Inventory Value = VAR CurrentMonth = [Current Month Index] RETURN CALCULATE ( [Inventory Value], FILTER ( ALL ( dim_date ), dim_date[month_index] = CurrentMonth ) )
Current Inventory Days = VAR CurrentMonth = [Current Month Index] RETURN CALCULATE ( [Inventory Days], FILTER ( ALL ( dim_date ), dim_date[month_index] = CurrentMonth ) )
Current Material Variance = VAR CurrentMonth = [Current Month Index] RETURN CALCULATE ( [Material Variance], FILTER ( ALL ( dim_date ), dim_date[month_index] = CurrentMonth ) )
Current Labor Variance = VAR CurrentMonth = [Current Month Index] RETURN CALCULATE ( [Labor Variance], FILTER ( ALL ( dim_date ), dim_date[month_index] = CurrentMonth ) )
Current Overhead Variance = VAR CurrentMonth = [Current Month Index] RETURN CALCULATE ( [Overhead Variance], FILTER ( ALL ( dim_date ), dim_date[month_index] = CurrentMonth ) )
Current Yield Loss Cost = VAR CurrentMonth = [Current Month Index] RETURN CALCULATE ( [Yield Loss Cost], FILTER ( ALL ( dim_date ), dim_date[month_index] = CurrentMonth ) )
Current Capacity Gap Units = VAR CurrentMonth = [Current Month Index] RETURN CALCULATE ( [Capacity Gap Units], FILTER ( ALL ( dim_date ), dim_date[month_index] = CurrentMonth ) )
Scenario Material Cost Reduction % = SELECTEDVALUE ( dim_scenario[material_cost_reduction_pct], 0 )
Scenario Labor Efficiency Gain % = SELECTEDVALUE ( dim_scenario[labor_efficiency_gain_pct], 0 )
Scenario OH Absorption Gain % = SELECTEDVALUE ( dim_scenario[overhead_absorption_gain_pct], 0 )
Scenario Scrap Reduction % = SELECTEDVALUE ( dim_scenario[scrap_reduction_pct], 0 )
Scenario Volume Delta % = SELECTEDVALUE ( dim_scenario[volume_delta_pct], 0 )
Scenario Cost Savings = [Current Material Variance] * [Scenario Material Cost Reduction %] + [Current Labor Variance] * [Scenario Labor Efficiency Gain %] + [Current Overhead Variance] * [Scenario OH Absorption Gain %] + [Current Yield Loss Cost] * [Scenario Scrap Reduction %]
Scenario Gross Margin = [Current Gross Margin] + [Scenario Cost Savings] + [Current Gross Margin] * [Scenario Volume Delta %]
Scenario GM % = DIVIDE ( [Scenario Gross Margin], [Current Revenue] * ( 1 + [Scenario Volume Delta %] ) )
Scenario EBITDA Uplift = [Scenario Gross Margin] - [Current Gross Margin]
Spark Revenue Trend = VAR SparkMonth = SELECTEDVALUE ( dim_spark_date[year_month] ) RETURN CALCULATE ( [Actual Revenue], REMOVEFILTERS ( dim_date ), TREATAS ( { SparkMonth }, dim_date[year_month] ) )
Spark Gross Margin Trend = VAR SparkMonth = SELECTEDVALUE ( dim_spark_date[year_month] ) RETURN CALCULATE ( [Gross Margin], REMOVEFILTERS ( dim_date ), TREATAS ( { SparkMonth }, dim_date[year_month] ) )
Spark GM % Trend = VAR SparkMonth = SELECTEDVALUE ( dim_spark_date[year_month] ) RETURN CALCULATE ( [Gross Margin %], REMOVEFILTERS ( dim_date ), TREATAS ( { SparkMonth }, dim_date[year_month] ) )
Spark Cost Variance Trend = VAR SparkMonth = SELECTEDVALUE ( dim_spark_date[year_month] ) RETURN CALCULATE ( [Cost Variance vs Standard], REMOVEFILTERS ( dim_date ), TREATAS ( { SparkMonth }, dim_date[year_month] ) )
Spark Unit Cost Trend = VAR SparkMonth = SELECTEDVALUE ( dim_spark_date[year_month] ) RETURN CALCULATE ( [Unit Cost], REMOVEFILTERS ( dim_date ), TREATAS ( { SparkMonth }, dim_date[year_month] ) )
Spark Yield Trend = VAR SparkMonth = SELECTEDVALUE ( dim_spark_date[year_month] ) RETURN CALCULATE ( [Yield %], REMOVEFILTERS ( dim_date ), TREATAS ( { SparkMonth }, dim_date[year_month] ) )
Spark Material Variance Trend = VAR SparkMonth = SELECTEDVALUE ( dim_spark_date[year_month] ) RETURN CALCULATE ( [Material Variance], REMOVEFILTERS ( dim_date ), TREATAS ( { SparkMonth }, dim_date[year_month] ) )
Spark Labor Variance Trend = VAR SparkMonth = SELECTEDVALUE ( dim_spark_date[year_month] ) RETURN CALCULATE ( [Labor Variance], REMOVEFILTERS ( dim_date ), TREATAS ( { SparkMonth }, dim_date[year_month] ) )
Spark Overhead Variance Trend = VAR SparkMonth = SELECTEDVALUE ( dim_spark_date[year_month] ) RETURN CALCULATE ( [Overhead Variance], REMOVEFILTERS ( dim_date ), TREATAS ( { SparkMonth }, dim_date[year_month] ) )
Spark Yield Loss Trend = VAR SparkMonth = SELECTEDVALUE ( dim_spark_date[year_month] ) RETURN CALCULATE ( [Yield Loss Cost], REMOVEFILTERS ( dim_date ), TREATAS ( { SparkMonth }, dim_date[year_month] ) )
Spark Actual COGS Trend = VAR SparkMonth = SELECTEDVALUE ( dim_spark_date[year_month] ) RETURN CALCULATE ( [Actual COGS], REMOVEFILTERS ( dim_date ), TREATAS ( { SparkMonth }, dim_date[year_month] ) )
Spark Standard COGS Trend = VAR SparkMonth = SELECTEDVALUE ( dim_spark_date[year_month] ) RETURN CALCULATE ( [Standard COGS], REMOVEFILTERS ( dim_date ), TREATAS ( { SparkMonth }, dim_date[year_month] ) )
Spark Scrap Rate Trend = VAR SparkMonth = SELECTEDVALUE ( dim_spark_date[year_month] ) RETURN CALCULATE ( [Scrap Rate], REMOVEFILTERS ( dim_date ), TREATAS ( { SparkMonth }, dim_date[year_month] ) )
Spark Utilization Trend = VAR SparkMonth = SELECTEDVALUE ( dim_spark_date[year_month] ) RETURN CALCULATE ( [Utilization %], REMOVEFILTERS ( dim_date ), TREATAS ( { SparkMonth }, dim_date[year_month] ) )
Spark Capacity Gap Trend = VAR SparkMonth = SELECTEDVALUE ( dim_spark_date[year_month] ) RETURN CALCULATE ( [Capacity Gap Units], REMOVEFILTERS ( dim_date ), TREATAS ( { SparkMonth }, dim_date[year_month] ) )
Spark Inventory Value Trend = VAR SparkMonth = SELECTEDVALUE ( dim_spark_date[year_month] ) RETURN CALCULATE ( [Inventory Value], REMOVEFILTERS ( dim_date ), TREATAS ( { SparkMonth }, dim_date[year_month] ) )
Spark Inventory Days Trend = VAR SparkMonth = SELECTEDVALUE ( dim_spark_date[year_month] ) RETURN CALCULATE ( [Inventory Days], REMOVEFILTERS ( dim_date ), TREATAS ( { SparkMonth }, dim_date[year_month] ) )
Spark Scenario EBITDA Uplift Trend = VAR SparkMonth = SELECTEDVALUE ( dim_spark_date[year_month] ) RETURN CALCULATE ( [Scenario EBITDA Uplift], REMOVEFILTERS ( dim_date ), TREATAS ( { SparkMonth }, dim_date[year_month] ) )
```
""".strip()


MEASURE_FORMATS = {
    "Actual Revenue": "$#,0",
    "Budget Revenue": "$#,0",
    "Actual COGS": "$#,0",
    "Standard COGS": "$#,0",
    "Actual Material Cost": "$#,0",
    "Actual Labor Cost": "$#,0",
    "Actual Overhead Cost": "$#,0",
    "Scrap Cost": "$#,0",
    "Rework Cost": "$#,0",
    "Yield Loss Cost": "$#,0",
    "Material Variance": "$#,0",
    "Labor Variance": "$#,0",
    "Overhead Variance": "$#,0",
    "Cost Variance vs Standard": "$#,0",
    "Gross Margin": "$#,0",
    "Gross Margin %": "0.0%",
    "Produced Units": "#,0",
    "Good Units": "#,0",
    "Scrap Units": "#,0",
    "Rework Units": "#,0",
    "Yield %": "0.0%",
    "Scrap Rate": "0.0%",
    "Unit Cost": "$0.00",
    "Standard Unit Cost": "$0.00",
    "Run Hours": "#,0",
    "Available Hours": "#,0",
    "Downtime Hours": "#,0",
    "Utilization %": "0.0%",
    "Capacity Units": "#,0",
    "Capacity Gap Units": "#,0",
    "Inventory Value": "$#,0",
    "Slow Moving Inventory": "$#,0",
    "Inventory Days": "0.0",
    "Bridge Amount": "$#,0",
    "Current Revenue": "$#,0",
    "Current Actual COGS": "$#,0",
    "Current Standard COGS": "$#,0",
    "Current Gross Margin": "$#,0",
    "Current GM %": "0.0%",
    "Current Cost Variance": "$#,0",
    "Current Unit Cost": "$0.00",
    "Current Yield %": "0.0%",
    "Current Scrap Rate": "0.0%",
    "Current Utilization %": "0.0%",
    "Current Inventory Value": "$#,0",
    "Current Inventory Days": "0.0",
    "Current Material Variance": "$#,0",
    "Current Labor Variance": "$#,0",
    "Current Overhead Variance": "$#,0",
    "Current Yield Loss Cost": "$#,0",
    "Current Capacity Gap Units": "#,0",
    "Scenario Material Cost Reduction %": "0.0%",
    "Scenario Labor Efficiency Gain %": "0.0%",
    "Scenario OH Absorption Gain %": "0.0%",
    "Scenario Scrap Reduction %": "0.0%",
    "Scenario Volume Delta %": "0.0%",
    "Scenario Cost Savings": "$#,0",
    "Scenario Gross Margin": "$#,0",
    "Scenario GM %": "0.0%",
    "Scenario EBITDA Uplift": "$#,0",
    "Spark Revenue Trend": "$#,0",
    "Spark Gross Margin Trend": "$#,0",
    "Spark GM % Trend": "0.0%",
    "Spark Cost Variance Trend": "$#,0",
    "Spark Unit Cost Trend": "$0.00",
    "Spark Yield Trend": "0.0%",
    "Spark Material Variance Trend": "$#,0",
    "Spark Labor Variance Trend": "$#,0",
    "Spark Overhead Variance Trend": "$#,0",
    "Spark Yield Loss Trend": "$#,0",
    "Spark Actual COGS Trend": "$#,0",
    "Spark Standard COGS Trend": "$#,0",
    "Spark Scrap Rate Trend": "0.0%",
    "Spark Utilization Trend": "0.0%",
    "Spark Capacity Gap Trend": "#,0",
    "Spark Inventory Value Trend": "$#,0",
    "Spark Inventory Days Trend": "0.0",
    "Spark Scenario EBITDA Uplift Trend": "$#,0",
}


def visual_id() -> str:
    return uuid.uuid4().hex[:20]


def pbi_literal(value: str | bool | int | float) -> dict:
    if isinstance(value, bool):
        rendered = "true" if value else "false"
    elif isinstance(value, int):
        rendered = f"{value}L"
    elif isinstance(value, float):
        rendered = f"{value}D"
    else:
        rendered = value
    return {"expr": {"Literal": {"Value": rendered}}}


def text(value: str) -> dict:
    return pbi_literal("'" + value.replace("'", "''") + "'")


def color(value: str) -> dict:
    return {"solid": {"color": text(value)}}


def position(x: int, y: int, z: int, width: int, height: int) -> dict:
    return {"x": x, "y": y, "z": z, "width": width, "height": height, "tabOrder": z}


def source_ref(alias: str) -> dict:
    return {"SourceRef": {"Source": alias}}


def entity_ref(alias: str) -> dict:
    return {"SourceRef": {"Entity": alias}}


def column_select(alias: str, table: str, column: str, display: str) -> dict:
    return {
        "Column": {"Expression": source_ref(alias), "Property": column},
        "Name": f"{table}.{column}",
        "NativeReferenceName": display,
    }


def measure_select(alias: str, measure: str, display: str) -> dict:
    return {
        "Measure": {"Expression": source_ref(alias), "Property": measure},
        "Name": f"{MEASURE_TABLE}.{measure}",
        "NativeReferenceName": display,
    }


def column_transform(alias: str, table: str, column: str, display: str, role: str) -> dict:
    return {
        "displayName": display,
        "queryName": f"{table}.{column}",
        "roles": {role: True},
        "type": {"category": None, "underlyingType": 1},
        "expr": {"Column": {"Expression": entity_ref(alias), "Property": column}},
    }


def measure_format(measure: str) -> str:
    return MEASURE_FORMATS.get(measure, "#,0")


def chart_display_units(measures: list[str]) -> float:
    formats = [measure_format(measure) for measure in measures]
    if formats and all("$" in fmt for fmt in formats):
        return 1000000.0
    return 0.0


def measure_transform(measure: str, display: str, role: str, fmt: str) -> dict:
    return {
        "displayName": display,
        "queryName": f"{MEASURE_TABLE}.{measure}",
        "roles": {role: True},
        "type": {"category": None, "underlyingType": 259},
        "expr": {"Measure": {"Expression": entity_ref("m"), "Property": measure}},
        "format": fmt,
        "sort": 2,
        "sortOrder": 0,
    }


def make_query(from_items: list[dict], selects: list[dict], order_by: dict | None = None, top: bool = False) -> str:
    query = {"Version": 2, "From": from_items, "Select": selects}
    if order_by:
        query["OrderBy"] = [order_by]
    data_reduction = {"DataVolume": 4, "Primary": {"Top": {}} if top else {"Window": {"Count": 1000}}}
    return json.dumps(
        {
            "Commands": [
                {
                    "SemanticQueryDataShapeCommand": {
                        "Query": query,
                        "Binding": {
                            "Primary": {"Groupings": [{"Projections": list(range(len(selects)))}]},
                            "DataReduction": data_reduction,
                            "Version": 1,
                        },
                        "ExecutionMetricsKind": 1,
                    }
                }
            ]
        },
        separators=(",", ":"),
    )


def data_transforms(
    objects: dict,
    roles: list[tuple[str, int, bool]],
    metadata: list[dict],
    selects: list[dict],
    projection_ordering: dict,
    active_items: dict | None = None,
) -> str:
    payload = {
        "objects": objects,
        "projectionOrdering": projection_ordering,
        "queryMetadata": {"Select": metadata},
        "visualElements": [
            {"DataRoles": [{"Name": role, "Projection": idx, "isActive": active} for role, idx, active in roles]}
        ],
        "selects": selects,
    }
    if active_items:
        payload["projectionActiveItems"] = active_items
    return json.dumps(payload, separators=(",", ":"))


def visual_frame(
    title: str | None = None,
    subtitle: str | None = None,
    fill: str = "#FFFFFF",
    title_size: float = 9.0,
    subtitle_size: float = 7.0,
    radius: float = 6.0,
    shadow: bool = True,
) -> dict:
    vc = {
        "background": [{"properties": {"show": pbi_literal(True), "color": color(fill), "transparency": pbi_literal(0.0)}}],
        "border": [{"properties": {"show": pbi_literal(True), "color": color("#D8DEE8"), "radius": pbi_literal(radius), "width": pbi_literal(1.0)}}],
        "dropShadow": [{"properties": {"show": pbi_literal(shadow), "position": text("Outer"), "color": color("#CBD5E1"), "transparency": pbi_literal(86.0), "angle": pbi_literal(45.0), "distance": pbi_literal(1.5)}}],
        "visualHeader": [{"properties": {"show": pbi_literal(False)}}],
    }
    if title:
        vc["title"] = [{"properties": {"show": pbi_literal(True), "text": text(title), "fontFamily": text("Segoe UI Semibold"), "fontSize": pbi_literal(title_size), "fontColor": color("#111827"), "alignment": text("left")}}]
    if subtitle:
        vc["subTitle"] = [{"properties": {"show": pbi_literal(True), "text": text(subtitle), "fontFamily": text("Segoe UI"), "fontSize": pbi_literal(subtitle_size), "fontColor": color("#64748B")}}]
    return vc


def transparent_frame() -> dict:
    return {
        "background": [{"properties": {"show": pbi_literal(False)}}],
        "border": [{"properties": {"show": pbi_literal(False)}}],
        "title": [{"properties": {"show": pbi_literal(False)}}],
        "subTitle": [{"properties": {"show": pbi_literal(False)}}],
        "visualHeader": [{"properties": {"show": pbi_literal(False)}}],
    }


def add_container(config: dict, pos: dict, query: str | None = None, transforms: str | None = None) -> dict:
    config["layouts"] = [{"id": 0, "position": pos}]
    payload = {
        "x": pos["x"],
        "y": pos["y"],
        "z": pos["z"],
        "width": pos["width"],
        "height": pos["height"],
        "config": json.dumps(config, separators=(",", ":")),
        "filters": "[]",
        "tabOrder": pos["tabOrder"],
    }
    if query:
        payload["query"] = query
    if transforms:
        payload["dataTransforms"] = transforms
    return payload


def title_text(title: str, subtitle: str, pos: dict) -> dict:
    objects = {
        "general": [
            {
                "properties": {
                    "paragraphs": [
                        {
                            "textRuns": [
                                {"value": title, "textStyle": {"fontFamily": "Segoe UI Semibold", "fontSize": "20pt", "color": "#111827"}},
                                {"value": f"\n{subtitle}", "textStyle": {"fontFamily": "Segoe UI", "fontSize": "8.5pt", "color": "#64748B"}},
                            ]
                        }
                    ]
                }
            }
        ]
    }
    config = {
        "name": visual_id(),
        "singleVisual": {
            "visualType": "textbox",
            "drillFilterOtherVisuals": True,
            "objects": objects,
            "vcObjects": {"background": [{"properties": {"show": pbi_literal(False)}}], "border": [{"properties": {"show": pbi_literal(False)}}], "visualHeader": [{"properties": {"show": pbi_literal(False)}}]},
        },
    }
    return add_container(config, pos)


def card(measure: str, display: str, pos: dict, value_color: str = "#2563EB", value_font: float = 21.0) -> dict:
    qref = f"{MEASURE_TABLE}.{measure}"
    objects = {
        "layout": [{"properties": {"rectangleRoundedCurve": pbi_literal(6), "cellPadding": pbi_literal(6.0), "paddingUniform": pbi_literal(6.0)}, "selector": {"id": "default"}}, {"properties": {}}],
        "fillCustom": [{"properties": {"show": pbi_literal(False)}}],
        "outline": [{"properties": {"show": pbi_literal(False)}, "selector": {"id": "default"}}],
        "value": [{"properties": {"fontSize": pbi_literal(value_font), "fontFamily": text("Segoe UI Semibold"), "fontColor": color(value_color)}, "selector": {"metadata": qref}}],
        "label": [{"properties": {"show": pbi_literal(False)}, "selector": {"metadata": qref}}],
        "divider": [{"properties": {"show": pbi_literal(False)}, "selector": {"metadata": qref}}],
        "referenceLabelDetail": [{"properties": {"show": pbi_literal(False)}, "selector": {"metadata": qref}}],
    }
    selects = [measure_select("m", measure, display)]
    from_items = [{"Name": "m", "Entity": MEASURE_TABLE, "Type": 0}]
    config = {
        "name": visual_id(),
        "singleVisual": {
            "visualType": "cardVisual",
            "projections": {"Data": [{"queryRef": qref}]},
            "prototypeQuery": {"Version": 2, "From": from_items, "Select": selects},
            "columnProperties": {qref: {"displayName": display}},
            "drillFilterOtherVisuals": True,
            "hasDefaultSort": True,
            "objects": objects,
            "vcObjects": visual_frame(display, fill=COLORS["card"], title_size=8.4),
        },
    }
    transforms = data_transforms(
        objects,
        [("Data", 0, False)],
        [{"Restatement": display, "Name": qref, "Type": 1, "Format": measure_format(measure)}],
        [measure_transform(measure, display, "Data", measure_format(measure))],
        {"Data": [0]},
    )
    return add_container(config, pos, make_query(from_items, selects), transforms)


def slicer(
    table: str,
    column: str,
    display: str,
    pos: dict,
    single_select: bool = False,
    sync_group: str | None = None,
) -> dict:
    qref = f"{table}.{column}"
    objects = {
        "data": [{"properties": {"mode": text("Dropdown")}}],
        "selection": [{"properties": {"selectAllCheckboxEnabled": pbi_literal(not single_select), "singleSelect": pbi_literal(single_select)}}],
        "header": [{"properties": {"show": pbi_literal(False)}}],
        "items": [{"properties": {"textSize": pbi_literal(7.2), "fontColor": color("#111827"), "fontFamily": text("Segoe UI"), "alignment": text("center")}}],
    }
    from_items = [{"Name": "f", "Entity": table, "Type": 0}]
    selects = [column_select("f", table, column, display)]
    config = {
        "name": visual_id(),
        "singleVisual": {
            "visualType": "slicer",
            "projections": {"Values": [{"queryRef": qref, "active": True}]},
            "prototypeQuery": {"Version": 2, "From": from_items, "Select": selects},
            "drillFilterOtherVisuals": True,
            "hasDefaultSort": True,
            "objects": objects,
            "vcObjects": visual_frame(display, fill=COLORS["pale"], title_size=7.8, radius=6.0, shadow=False),
        },
    }
    if sync_group:
        config["singleVisual"]["syncGroup"] = {"groupName": sync_group, "fieldChanges": True, "filterChanges": True}
    transforms = data_transforms(
        objects,
        [("Values", 0, True)],
        [{"Restatement": display, "Name": qref, "Type": 2048}],
        [column_transform("f", table, column, display, "Values")],
        {"Values": [0]},
    )
    return add_container(config, pos, make_query(from_items, selects), transforms)


def chart_objects(fill: str = "#2563EB", show_labels: bool = True, display_units: float = 1000000.0) -> dict:
    return {
        "valueAxis": [{"properties": {"showAxisTitle": pbi_literal(False), "gridlineShow": pbi_literal(False), "gridlineColor": color(COLORS["chart_grid"]), "labelDisplayUnits": pbi_literal(display_units), "fontSize": pbi_literal(7.0), "color": color(COLORS["muted"])}}],
        "categoryAxis": [{"properties": {"showAxisTitle": pbi_literal(False), "gridlineShow": pbi_literal(False), "concatenateLabels": pbi_literal(False), "fontSize": pbi_literal(7.0), "color": color(COLORS["ink"])}}],
        "labels": [{"properties": {"show": pbi_literal(show_labels), "labelDisplayUnits": pbi_literal(display_units), "fontSize": pbi_literal(7.0), "color": color(COLORS["ink"])}}],
        "legend": [{"properties": {"showTitle": pbi_literal(False), "position": text("Top"), "fontSize": pbi_literal(7.0), "labelColor": color(COLORS["muted"])}}],
        "dataPoint": [{"properties": {"fill": color(fill)}}],
    }


def sparkline_chart(measure: str, display: str, pos: dict, fill: str = "#2563EB") -> dict:
    category_ref = "dim_spark_date.year_month"
    measure_ref = f"{MEASURE_TABLE}.{measure}"
    objects = {
        "valueAxis": [{"properties": {"show": pbi_literal(False), "showAxisTitle": pbi_literal(False), "gridlineShow": pbi_literal(False)}}],
        "categoryAxis": [{"properties": {"show": pbi_literal(False), "showAxisTitle": pbi_literal(False), "gridlineShow": pbi_literal(False)}}],
        "labels": [{"properties": {"show": pbi_literal(False)}}],
        "legend": [{"properties": {"show": pbi_literal(False)}}],
        "dataPoint": [{"properties": {"fill": color(fill), "strokeWidth": pbi_literal(2.25), "showAllDataPoints": pbi_literal(True), "markerSize": pbi_literal(2.4)}}],
    }
    from_items = [{"Name": "c", "Entity": "dim_spark_date", "Type": 0}, {"Name": "m", "Entity": MEASURE_TABLE, "Type": 0}]
    selects = [column_select("c", "dim_spark_date", "year_month", "Month"), measure_select("m", measure, display)]
    order_by = {"Direction": 1, "Expression": {"Column": {"Expression": source_ref("c"), "Property": "month_index"}}}
    config = {
        "name": visual_id(),
        "singleVisual": {
            "visualType": "lineChart",
            "projections": {"Category": [{"queryRef": category_ref, "active": True}], "Y": [{"queryRef": measure_ref}]},
            "prototypeQuery": {"Version": 2, "From": from_items, "Select": selects, "OrderBy": [order_by]},
            "drillFilterOtherVisuals": False,
            "hasDefaultSort": True,
            "objects": objects,
            "vcObjects": transparent_frame(),
        },
    }
    transforms = data_transforms(
        objects,
        [("Category", 0, True), ("Y", 1, False)],
        [
            {"Restatement": "Month", "Name": category_ref, "Type": 2048},
            {"Restatement": display, "Name": measure_ref, "Type": 1, "Format": measure_format(measure)},
        ],
        [
            column_transform("c", "dim_spark_date", "year_month", "Month", "Category"),
            measure_transform(measure, display, "Y", measure_format(measure)),
        ],
        {"Category": [0], "Y": [1]},
        {"Category": [{"queryRef": category_ref, "suppressConcat": False}]},
    )
    return add_container(config, pos, make_query(from_items, selects, order_by), transforms)


def kpi_card_stack(measure: str, display: str, spark_measure: str, pos: dict, value_color: str = "#2563EB") -> list[dict]:
    spark_pos = position(
        int(pos["x"] + 14),
        int(pos["y"] + pos["height"] - 34),
        int(pos["z"] + 500),
        int(pos["width"] - 28),
        28,
    )
    return [
        card(measure, display, pos, value_color, value_font=20.5),
        sparkline_chart(spark_measure, f"{display} Trend", spark_pos, value_color),
    ]


def single_measure_chart(
    visual_type: str,
    title: str,
    subtitle: str,
    category_table: str,
    category_column: str,
    category_display: str,
    measure: str,
    measure_display: str,
    pos: dict,
    fill: str = "#2563EB",
    order_measure: bool = True,
    ascending: bool = False,
) -> dict:
    category_ref = f"{category_table}.{category_column}"
    measure_ref = f"{MEASURE_TABLE}.{measure}"
    objects = chart_objects(fill=fill, show_labels=visual_type not in {"lineChart"}, display_units=chart_display_units([measure]))
    from_items = [{"Name": "c", "Entity": category_table, "Type": 0}, {"Name": "m", "Entity": MEASURE_TABLE, "Type": 0}]
    selects = [column_select("c", category_table, category_column, category_display), measure_select("m", measure, measure_display)]
    if order_measure:
        order_by = {"Direction": 1 if ascending else 2, "Expression": {"Measure": {"Expression": source_ref("m"), "Property": measure}}}
    else:
        order_by = {"Direction": 1 if ascending else 2, "Expression": {"Column": {"Expression": source_ref("c"), "Property": category_column}}}
    config = {
        "name": visual_id(),
        "singleVisual": {
            "visualType": visual_type,
            "projections": {"Category": [{"queryRef": category_ref, "active": True}], "Y": [{"queryRef": measure_ref}]},
            "prototypeQuery": {"Version": 2, "From": from_items, "Select": selects, "OrderBy": [order_by]},
            "drillFilterOtherVisuals": True,
            "hasDefaultSort": True,
            "objects": objects,
            "vcObjects": visual_frame(title, subtitle),
        },
    }
    transforms = data_transforms(
        objects,
        [("Category", 0, True), ("Y", 1, False)],
        [
            {"Restatement": category_display, "Name": category_ref, "Type": 2048},
            {"Restatement": measure_display, "Name": measure_ref, "Type": 1, "Format": measure_format(measure)},
        ],
        [column_transform("c", category_table, category_column, category_display, "Category"), measure_transform(measure, measure_display, "Y", measure_format(measure))],
        {"Category": [0], "Y": [1]},
        {"Category": [{"queryRef": category_ref, "suppressConcat": False}]},
    )
    return add_container(config, pos, make_query(from_items, selects, order_by, top=visual_type == "waterfallChart"), transforms)


def multi_measure_column(
    title: str,
    subtitle: str,
    category_table: str,
    category_column: str,
    category_display: str,
    measures: list[tuple[str, str]],
    pos: dict,
    fill: str = "#2563EB",
    order_column: str | None = None,
    visual_type: str = "columnChart",
) -> dict:
    category_ref = f"{category_table}.{category_column}"
    objects = chart_objects(fill=fill, show_labels=False, display_units=chart_display_units([measure for measure, _ in measures]))
    from_items = [{"Name": "c", "Entity": category_table, "Type": 0}, {"Name": "m", "Entity": MEASURE_TABLE, "Type": 0}]
    selects = [column_select("c", category_table, category_column, category_display)]
    projections_y = []
    metadata = [{"Restatement": category_display, "Name": category_ref, "Type": 2048}]
    transform_selects = [column_transform("c", category_table, category_column, category_display, "Category")]
    roles = [("Category", 0, True)]
    for measure, display in measures:
        idx = len(selects)
        qref = f"{MEASURE_TABLE}.{measure}"
        selects.append(measure_select("m", measure, display))
        projections_y.append({"queryRef": qref})
        metadata.append({"Restatement": display, "Name": qref, "Type": 1, "Format": measure_format(measure)})
        transform_selects.append(measure_transform(measure, display, "Y", measure_format(measure)))
        roles.append(("Y", idx, False))
    order_by = None
    if order_column:
        order_by = {"Direction": 1, "Expression": {"Column": {"Expression": source_ref("c"), "Property": order_column}}}
    config = {
        "name": visual_id(),
        "singleVisual": {
            "visualType": visual_type,
            "projections": {"Category": [{"queryRef": category_ref, "active": True}], "Y": projections_y},
            "prototypeQuery": {"Version": 2, "From": from_items, "Select": selects, **({"OrderBy": [order_by]} if order_by else {})},
            "drillFilterOtherVisuals": True,
            "hasDefaultSort": True,
            "objects": objects,
            "vcObjects": visual_frame(title, subtitle),
        },
    }
    transforms = data_transforms(
        objects,
        roles,
        metadata,
        transform_selects,
        {"Category": [0], "Y": list(range(1, len(selects)))},
        {"Category": [{"queryRef": category_ref, "suppressConcat": False}]},
    )
    return add_container(config, pos, make_query(from_items, selects, order_by), transforms)


def table_column_width(display: str, qref: str) -> float:
    label = display.lower()
    if "description" in label:
        return 170.0
    if "product" in label:
        return 145.0
    if label in {"plant", "line", "scenario"}:
        return 112.0
    if any(token in label for token in ["revenue", "gm", "var", "yield", "scrap", "days", "savings"]):
        return 88.0
    if qref.startswith(f"{MEASURE_TABLE}."):
        return 84.0
    return 100.0


def table_cell_alignment(display: str, qref: str) -> str:
    label = display.lower()
    if qref.startswith(f"{MEASURE_TABLE}.") or any(token in label for token in ["revenue", "gm", "var", "yield", "scrap", "days", "savings"]):
        return "right"
    return "left"


def table_visual(
    title: str,
    subtitle: str,
    fields: list[tuple[str, str, str]],
    measures: list[tuple[str, str]],
    pos: dict,
    order_measure: str | None = None,
) -> dict:
    aliases: dict[str, str] = {}
    from_items: list[dict] = []
    for idx, (table, _, _) in enumerate(fields):
        if table not in aliases:
            alias = f"f{idx}"
            aliases[table] = alias
            from_items.append({"Name": alias, "Entity": table, "Type": 0})
    if measures:
        aliases[MEASURE_TABLE] = "m"
        from_items.append({"Name": "m", "Entity": MEASURE_TABLE, "Type": 0})
    selects = []
    projections = []
    metadata = []
    transform_selects = []
    for table, column, display in fields:
        qref = f"{table}.{column}"
        selects.append(column_select(aliases[table], table, column, display))
        projections.append({"queryRef": qref})
        metadata.append({"Restatement": display, "Name": qref, "Type": 2048})
        transform_selects.append(column_transform(aliases[table], table, column, display, "Values"))
    for measure, display in measures:
        qref = f"{MEASURE_TABLE}.{measure}"
        selects.append(measure_select("m", measure, display))
        projections.append({"queryRef": qref})
        metadata.append({"Restatement": display, "Name": qref, "Type": 1, "Format": measure_format(measure)})
        transform_selects.append(measure_transform(measure, display, "Values", measure_format(measure)))
    column_info = [(f"{table}.{column}", display) for table, column, display in fields] + [(f"{MEASURE_TABLE}.{measure}", display) for measure, display in measures]
    objects = {
        "grid": [{"properties": {"gridHorizontal": pbi_literal(True), "gridVertical": pbi_literal(False), "outlineColor": color("#CBD5E1"), "rowPadding": pbi_literal(5)}}],
        "columnHeaders": [{"properties": {"show": pbi_literal(True), "fontFamily": text("Segoe UI Semibold"), "fontSize": pbi_literal(7.4), "fontColor": color(COLORS["ink"]), "backColor": color(COLORS["table_header"]), "alignment": text("left")}}],
        "values": [{"properties": {"fontSize": pbi_literal(7.15), "fontFamily": text("Segoe UI"), "fontColor": color(COLORS["ink"]), "backColorPrimary": color(COLORS["table_row"]), "backColorSecondary": color(COLORS["table_alt"])}}],
        "columnWidth": [
            {"properties": {"value": pbi_literal(table_column_width(display, qref))}, "selector": {"metadata": qref}}
            for qref, display in column_info
        ],
        "columnFormatting": [
            {"properties": {"alignment": text(table_cell_alignment(display, qref))}, "selector": {"metadata": qref}}
            for qref, display in column_info
        ],
    }
    order_by = None
    if order_measure:
        order_by = {"Direction": 2, "Expression": {"Measure": {"Expression": source_ref("m"), "Property": order_measure}}}
    config = {
        "name": visual_id(),
        "singleVisual": {
            "visualType": "tableEx",
            "projections": {"Values": projections},
            "prototypeQuery": {"Version": 2, "From": from_items, "Select": selects, **({"OrderBy": [order_by]} if order_by else {})},
            "drillFilterOtherVisuals": True,
            "objects": objects,
            "vcObjects": visual_frame(title, subtitle),
        },
    }
    transforms = data_transforms(
        objects,
        [("Values", idx, False) for idx in range(len(selects))],
        metadata,
        transform_selects,
        {"Values": list(range(len(selects)))},
    )
    return add_container(config, pos, make_query(from_items, selects, order_by), transforms)


def section(name: str, display_name: str, ordinal: int, visuals: list[dict]) -> dict:
    return {
        "id": ordinal,
        "name": name,
        "displayName": display_name,
        "filters": "[]",
        "ordinal": ordinal,
        "visualContainers": visuals,
        "config": json.dumps(
            {
                "objects": {
                    "background": [{"properties": {"color": color("#F6F7F9"), "transparency": pbi_literal(0.0)}}],
                    "outspace": [{"properties": {"color": color("#F6F7F9"), "transparency": pbi_literal(0.0)}}],
                }
            },
            separators=(",", ":"),
        ),
        "displayOption": 1,
        "width": 1280,
        "height": 720,
    }


def build_native_layout() -> dict:
    top_slicer_y = 72
    top_slicer_height = 52
    top_slicer_x = [24, 336, 648, 960]
    top_slicer_width = 296
    kpi_x = top_slicer_x
    kpi_y = 142
    kpi_width = top_slicer_width
    kpi_height = 94
    chart_y = 254
    chart_height = 198
    variance_chart_height = 222
    table_y = 478
    table_height = 212
    variance_table_y = 500
    variance_table_height = 190

    def global_slicers(z: int) -> list[dict]:
        return [
            slicer("dim_date", "year_month", "Month", position(top_slicer_x[0], top_slicer_y, z, top_slicer_width, top_slicer_height), single_select=True, sync_group="p16_month"),
            slicer("dim_plant", "plant_name", "Plant", position(top_slicer_x[1], top_slicer_y, z + 1, top_slicer_width, top_slicer_height), sync_group="p16_plant"),
            slicer("dim_product", "product_line", "Product Line", position(top_slicer_x[2], top_slicer_y, z + 2, top_slicer_width, top_slicer_height), sync_group="p16_product_line"),
            slicer("dim_line", "line_name", "Line", position(top_slicer_x[3], top_slicer_y, z + 3, top_slicer_width, top_slicer_height), sync_group="p16_line"),
        ]

    page1 = [
        title_text("Manufacturing Cost FP&A", "Overview | margin, cost variance, yield, utilization, and inventory risk", position(24, 14, 1, 650, 54)),
        *global_slicers(10),
        *kpi_card_stack("Current Revenue", "Revenue", "Spark Revenue Trend", position(kpi_x[0], kpi_y, 100, kpi_width, kpi_height), COLORS["steel"]),
        *kpi_card_stack("Current Gross Margin", "Gross Margin", "Spark Gross Margin Trend", position(kpi_x[1], kpi_y, 101, kpi_width, kpi_height), COLORS["teal"]),
        *kpi_card_stack("Current Cost Variance", "Cost Var", "Spark Cost Variance Trend", position(kpi_x[2], kpi_y, 102, kpi_width, kpi_height), COLORS["amber"]),
        *kpi_card_stack("Current Yield %", "Yield", "Spark Yield Trend", position(kpi_x[3], kpi_y, 103, kpi_width, kpi_height), COLORS["green"]),
        multi_measure_column(
            "Revenue vs COGS Trend",
            "Actual revenue, actual COGS, and standard COGS by month",
            "dim_date",
            "year_month",
            "Month",
            [("Actual Revenue", "Revenue"), ("Actual COGS", "Actual COGS"), ("Standard COGS", "Std COGS")],
            position(24, chart_y, 210, 500, chart_height),
            COLORS["steel"],
            "month_index",
            "lineChart",
        ),
        single_measure_chart("barChart", "Cost Variance by Plant", "Actual COGS less standard COGS", "dim_plant", "plant_name", "Plant", "Cost Variance vs Standard", "Cost Var", position(548, chart_y, 211, 342, chart_height), COLORS["amber"]),
        single_measure_chart("barChart", "Gross Margin by Product Line", "Current selection", "dim_product", "product_line", "Product Line", "Gross Margin", "GM", position(914, chart_y, 212, 342, chart_height), COLORS["teal"]),
        table_visual(
            "Margin Action List",
            "Highest value combinations to review with operations",
            [("dim_plant", "plant_name", "Plant"), ("dim_line", "line_name", "Line"), ("dim_product", "product", "Product")],
            [("Current Revenue", "Revenue"), ("Current Gross Margin", "GM"), ("Current Cost Variance", "Cost Var"), ("Current Yield %", "Yield"), ("Current Inventory Days", "Inv Days")],
            position(24, table_y, 300, 1232, table_height),
            "Current Cost Variance",
        ),
    ]

    page2 = [
        title_text("Standard Cost Variance", "Bridge material, labor, overhead, yield, and product drivers", position(24, 14, 1, 620, 54)),
        *global_slicers(20),
        *kpi_card_stack("Current Material Variance", "Material Var", "Spark Material Variance Trend", position(kpi_x[0], kpi_y, 100, kpi_width, kpi_height), COLORS["amber"]),
        *kpi_card_stack("Current Labor Variance", "Labor Var", "Spark Labor Variance Trend", position(kpi_x[1], kpi_y, 101, kpi_width, kpi_height), COLORS["red"]),
        *kpi_card_stack("Current Overhead Variance", "OH Var", "Spark Overhead Variance Trend", position(kpi_x[2], kpi_y, 102, kpi_width, kpi_height), COLORS["violet"]),
        *kpi_card_stack("Current Yield Loss Cost", "Yield Loss", "Spark Yield Loss Trend", position(kpi_x[3], kpi_y, 103, kpi_width, kpi_height), COLORS["red"]),
        single_measure_chart("waterfallChart", "COGS Variance Bridge", "Standard COGS to actual COGS for latest month", "fact_cost_variance_bridge", "bridge_step", "Bridge Step", "Bridge Amount", "Amount", position(24, chart_y, 210, 500, variance_chart_height), COLORS["steel"], False, True),
        single_measure_chart("barChart", "Material Variance by Product Line", "Material price and usage pressure", "dim_product", "product_line", "Product Line", "Material Variance", "Material Var", position(548, chart_y, 211, 342, variance_chart_height), COLORS["amber"]),
        single_measure_chart("barChart", "Labor Variance by Plant", "Efficiency and overtime pressure", "dim_plant", "plant_name", "Plant", "Labor Variance", "Labor Var", position(914, chart_y, 212, 342, variance_chart_height), COLORS["red"]),
        table_visual(
            "Variance Detail",
            "Product and plant level variance diagnostics",
            [("dim_product", "product", "Product"), ("dim_product", "product_line", "Line"), ("dim_plant", "plant_name", "Plant")],
            [("Material Variance", "Mat Var"), ("Labor Variance", "Labor Var"), ("Overhead Variance", "OH Var"), ("Yield Loss Cost", "Yield Loss"), ("Cost Variance vs Standard", "Total Var")],
            position(24, variance_table_y, 300, 1232, variance_table_height),
            "Cost Variance vs Standard",
        ),
    ]

    page3 = [
        title_text("Yield, Capacity & Working Capital", "Operational drivers and scenario levers for EBITDA protection", position(24, 14, 1, 650, 54)),
        slicer("dim_date", "year_month", "Month", position(top_slicer_x[0], top_slicer_y, 20, top_slicer_width, top_slicer_height), single_select=True, sync_group="p16_month"),
        slicer("dim_plant", "plant_name", "Plant", position(top_slicer_x[1], top_slicer_y, 21, top_slicer_width, top_slicer_height), sync_group="p16_plant"),
        slicer("dim_product", "product_line", "Product Line", position(top_slicer_x[2], top_slicer_y, 22, top_slicer_width, top_slicer_height), sync_group="p16_product_line"),
        slicer("dim_scenario", "scenario_name", "Scenario", position(top_slicer_x[3], top_slicer_y, 23, top_slicer_width, top_slicer_height), single_select=True, sync_group="p16_scenario"),
        *kpi_card_stack("Current Yield %", "Yield", "Spark Yield Trend", position(kpi_x[0], kpi_y, 100, kpi_width, kpi_height), COLORS["teal"]),
        *kpi_card_stack("Current Scrap Rate", "Scrap Rate", "Spark Scrap Rate Trend", position(kpi_x[1], kpi_y, 101, kpi_width, kpi_height), COLORS["red"]),
        *kpi_card_stack("Current Utilization %", "Utilization", "Spark Utilization Trend", position(kpi_x[2], kpi_y, 102, kpi_width, kpi_height), COLORS["steel"]),
        *kpi_card_stack("Scenario EBITDA Uplift", "Scenario Uplift", "Spark Scenario EBITDA Uplift Trend", position(kpi_x[3], kpi_y, 103, kpi_width, kpi_height), COLORS["green"]),
        multi_measure_column(
            "Yield and Scrap Trend",
            "Yield improvement and scrap containment",
            "dim_date",
            "year_month",
            "Month",
            [("Yield %", "Yield"), ("Scrap Rate", "Scrap")],
            position(24, chart_y, 210, 410, chart_height),
            COLORS["teal"],
            "month_index",
            "lineChart",
        ),
        single_measure_chart("barChart", "Utilization by Line", "Run hours over available hours", "dim_line", "line_name", "Line", "Utilization %", "Utilization", position(458, chart_y, 211, 394, chart_height), COLORS["steel"]),
        single_measure_chart("barChart", "Inventory Days by Product Line", "Working capital tied to production mix", "dim_product", "product_line", "Product Line", "Inventory Days", "Inv Days", position(876, chart_y, 212, 380, chart_height), COLORS["violet"]),
        table_visual(
            "Scenario and Bottleneck Review",
            "Select a scenario and prioritize lines with high scrap, utilization, and inventory days",
            [("dim_scenario", "scenario_name", "Scenario"), ("dim_scenario", "description", "Description"), ("dim_line", "line_name", "Line")],
            [("Scenario Cost Savings", "Savings"), ("Scenario Gross Margin", "Scenario GM"), ("Scenario GM %", "Scenario GM %"), ("Current Scrap Rate", "Scrap"), ("Current Inventory Days", "Inv Days")],
            position(24, table_y, 300, 1232, table_height),
            "Scenario EBITDA Uplift",
        ),
    ]

    report_config = {
        "version": "5.73",
        "themeCollection": {"baseTheme": {"name": "CY26SU05", "version": {"visual": "2.9.0", "report": "3.3.0", "page": "2.3.1"}, "type": 2}},
        "activeSectionIndex": 0,
        "defaultDrillFilterOtherVisuals": True,
        "settings": {
            "useNewFilterPaneExperience": True,
            "allowChangeFilterTypes": True,
            "useStylableVisualContainerHeader": True,
            "queryLimitOption": 6,
            "useEnhancedTooltips": True,
            "exportDataMode": 1,
            "useDefaultAggregateDisplayName": True,
        },
        "objects": {"section": [{"properties": {"verticalAlignment": text("Top")}}]},
    }
    return {
        "id": 0,
        "resourcePackages": [
            {
                "resourcePackage": {
                    "name": "SharedResources",
                    "type": 2,
                    "items": [{"type": 202, "path": "BaseThemes/CY26SU05.json", "name": "CY26SU05"}],
                    "disabled": False,
                }
            }
        ],
        "sections": [
            section("p16_manufacturing_overview", "01 Manufacturing FP&A Overview", 0, page1),
            section("p16_standard_cost_variance", "02 Standard Cost Variance", 1, page2),
            section("p16_yield_capacity_wc", "03 Yield Capacity & WC", 2, page3),
        ],
        "config": json.dumps(report_config, separators=(",", ":")),
        "layoutOptimization": 0,
    }


def write_native_layout() -> None:
    layout = build_native_layout()
    write_json("build/native_report_layout_project16.json", layout)
    summary = {
        "layout": str(p("build/native_report_layout_project16.json")),
        "pages": len(layout["sections"]),
        "visual_containers": sum(len(s["visualContainers"]) for s in layout["sections"]),
        "page_names": [s["displayName"] for s in layout["sections"]],
        "visual_types": count_visual_types(layout),
    }
    write_json("build/native_report_layout_project16_summary.json", summary)


def count_visual_types(layout: dict) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for sec in layout.get("sections", []):
        for vc in sec.get("visualContainers", []):
            try:
                cfg = json.loads(vc.get("config", "{}"))
                counts[cfg.get("singleVisual", {}).get("visualType", "unknown")] += 1
            except Exception:
                counts["invalid"] += 1
    return dict(counts)


def render_screenshots(dims: dict[str, pd.DataFrame], facts: dict[str, pd.DataFrame], metrics: dict) -> None:
    fact = facts["fact_manufacturing_month"]
    enriched = fact.merge(dims["dim_plant"], on="plant_id", how="left").merge(dims["dim_product"], on="product_id", how="left")
    monthly = fact.groupby("year_month", as_index=False).agg(
        actual_revenue=("actual_revenue", "sum"),
        actual_cogs=("actual_cogs", "sum"),
        standard_cogs=("standard_cogs", "sum"),
        gross_margin=("gross_margin", "sum"),
        material_variance=("material_variance", "sum"),
        labor_variance=("labor_variance", "sum"),
        overhead_variance=("overhead_variance", "sum"),
        yield_loss_cost=("yield_loss_cost", "sum"),
        good_units=("good_units", "sum"),
        produced_units=("produced_units", "sum"),
        scrap_units=("scrap_units", "sum"),
        run_hours=("run_hours", "sum"),
        available_hours=("available_hours", "sum"),
        inventory_value=("inventory_value", "sum"),
    )
    monthly["cost_variance"] = monthly.actual_cogs - monthly.standard_cogs
    monthly["yield_pct"] = monthly.good_units / monthly.produced_units
    monthly["scrap_rate"] = monthly.scrap_units / monthly.produced_units
    monthly["utilization_pct"] = monthly.run_hours / monthly.available_hours
    monthly["scenario_uplift"] = monthly.material_variance * 0.035 + monthly.labor_variance * 0.075 + monthly.overhead_variance * 0.060 + monthly.yield_loss_cost * 0.120
    latest = enriched[enriched.year_month.eq(LATEST_MONTH)].copy()
    plant_var = latest.groupby("plant_name", as_index=False).agg(cost_variance=("material_variance", "sum"), actual_cogs=("actual_cogs", "sum")).sort_values("cost_variance", ascending=False)
    product_margin = latest.groupby("product_line", as_index=False).agg(gross_margin=("gross_margin", "sum"), inventory_value=("inventory_value", "sum"), actual_cogs=("actual_cogs", "sum")).sort_values("gross_margin")
    product_margin["inventory_days"] = 30 * product_margin.inventory_value / product_margin.actual_cogs
    line = latest.merge(dims["dim_line"][["line_id", "line_name"]], on="line_id", how="left")
    line_summary = line.groupby("line_name", as_index=False).agg(run_hours=("run_hours", "sum"), available_hours=("available_hours", "sum"), scrap_units=("scrap_units", "sum"), produced_units=("produced_units", "sum")).sort_values("line_name")
    line_summary["utilization"] = line_summary.run_hours / line_summary.available_hours
    line_summary["scrap_rate"] = line_summary.scrap_units / line_summary.produced_units

    pages = [
        ("tab1_overview.png", "Manufacturing FP&A Overview", [
            ("Revenue", money(metrics["current"]["actual_revenue"]), "actual_revenue", COLORS["steel"]),
            ("Gross Margin", money(metrics["current"]["gross_margin"]), "gross_margin", COLORS["teal"]),
            ("Cost Var", money(metrics["current"]["cost_variance"]), "cost_variance", COLORS["amber"]),
            ("Yield", pct(metrics["current"]["yield_pct"]), "yield_pct", COLORS["green"]),
        ]),
        ("tab2_variance.png", "Standard Cost Variance", [
            ("Material Var", money(metrics["current"]["material_variance"]), "material_variance", COLORS["amber"]),
            ("Labor Var", money(metrics["current"]["labor_variance"]), "labor_variance", COLORS["red"]),
            ("OH Var", money(metrics["current"]["overhead_variance"]), "overhead_variance", COLORS["violet"]),
            ("Yield Loss", money(metrics["current"]["yield_loss_cost"]), "yield_loss_cost", COLORS["red"]),
        ]),
        ("tab3_yield_capacity_wc.png", "Yield, Capacity & Working Capital", [
            ("Yield", pct(metrics["current"]["yield_pct"]), "yield_pct", COLORS["teal"]),
            ("Scrap Rate", pct(metrics["current"]["scrap_rate"]), "scrap_rate", COLORS["red"]),
            ("Utilization", pct(metrics["current"]["utilization_pct"]), "utilization_pct", COLORS["steel"]),
            ("Scenario Uplift", money(metrics["current"]["cost_variance"] * 0.12), "scenario_uplift", COLORS["green"]),
        ]),
    ]
    for file_name, title, cards in pages:
        fig = plt.figure(figsize=(16, 9), facecolor=COLORS["bg"])
        fig.suptitle(title, fontsize=24, fontweight="bold", x=0.03, ha="left", color=COLORS["ink"])
        slicer_labels = ["Month", "Plant", "Product Line", "Scenario" if "Working Capital" in title else "Line"]
        for i, label in enumerate(slicer_labels):
            ax = fig.add_axes([0.03 + i * 0.235, 0.805, 0.205, 0.06])
            ax.set_facecolor(COLORS["panel"])
            ax.text(0.035, 0.68, label, fontsize=7.5, fontweight="bold", color=COLORS["muted"], transform=ax.transAxes)
            ax.text(0.035, 0.23, "All", fontsize=9.5, color=COLORS["ink"], transform=ax.transAxes)
            ax.text(0.95, 0.25, "v", fontsize=8, color=COLORS["muted"], ha="right", transform=ax.transAxes)
            ax.set_xticks([])
            ax.set_yticks([])
            for spine in ax.spines.values():
                spine.set_edgecolor(COLORS["line"])
        for i, (label, value, series_col, accent) in enumerate(cards):
            ax = fig.add_axes([0.03 + i * 0.235, 0.66, 0.205, 0.105])
            ax.set_facecolor(COLORS["panel"])
            ax.text(0.04, 0.68, label, fontsize=9.2, fontweight="bold", color=COLORS["ink"], transform=ax.transAxes)
            ax.text(0.04, 0.37, value, fontsize=20, fontweight="bold", color=accent, transform=ax.transAxes)
            series = monthly[series_col].to_numpy(dtype=float)
            low, high = float(np.nanmin(series)), float(np.nanmax(series))
            denom = high - low if high != low else 1.0
            norm = (series - low) / denom
            xs = np.linspace(0.08, 0.94, len(series))
            ys = 0.10 + norm * 0.18
            ax.fill_between(xs, 0.08, ys, color=accent, alpha=0.10, transform=ax.transAxes)
            ax.plot(xs, ys, color=accent, linewidth=1.8, transform=ax.transAxes)
            ax.scatter([xs[-1]], [ys[-1]], s=16, color=accent, edgecolor="white", linewidth=0.8, transform=ax.transAxes, zorder=5)
            ax.set_xticks([])
            ax.set_yticks([])
            for spine in ax.spines.values():
                spine.set_edgecolor(COLORS["line"])
        ax1 = fig.add_axes([0.05, 0.38, 0.42, 0.21], facecolor=COLORS["panel"])
        ax1.plot(monthly.year_month, monthly.actual_revenue / 1_000_000, color=COLORS["steel"], linewidth=2.4, label="Revenue")
        ax1.plot(monthly.year_month, monthly.actual_cogs / 1_000_000, color=COLORS["amber"], linewidth=2.0, label="COGS")
        ax1.tick_params(axis="x", labelrotation=45, labelsize=5.5)
        for idx, tick in enumerate(ax1.get_xticklabels()):
            if idx % 3:
                tick.set_visible(False)
        ax1.set_title("Revenue vs COGS trend", loc="left", fontsize=11, fontweight="bold")
        ax1.legend(frameon=False, fontsize=8)
        ax1.grid(axis="y", color=COLORS["line"], linewidth=0.7, alpha=0.8)
        ax2 = fig.add_axes([0.53, 0.38, 0.42, 0.21], facecolor=COLORS["panel"])
        if "Variance" in title:
            bars = plant_var
            ax2.barh(bars.plant_name, bars.cost_variance / 1_000, color=COLORS["amber"])
            ax2.set_title("Cost variance by plant ($K)", loc="left", fontsize=11, fontweight="bold")
        else:
            bars = product_margin
            ax2.barh(bars.product_line, bars.gross_margin / 1_000, color=COLORS["teal"])
            ax2.set_title("Gross margin by product line ($K)", loc="left", fontsize=11, fontweight="bold")
        ax2.grid(axis="x", color=COLORS["line"], linewidth=0.7, alpha=0.8)
        ax3 = fig.add_axes([0.05, 0.07, 0.42, 0.20], facecolor=COLORS["panel"])
        ax3.bar(line_summary.line_name, line_summary.utilization * 100, color=COLORS["steel"])
        ax3.axhline(85, color=COLORS["amber"], linestyle="--", linewidth=1)
        ax3.tick_params(axis="x", labelrotation=60, labelsize=7)
        ax3.set_title("Line utilization %", loc="left", fontsize=11, fontweight="bold")
        ax3.grid(axis="y", color=COLORS["line"], linewidth=0.7, alpha=0.8)
        ax4 = fig.add_axes([0.53, 0.07, 0.42, 0.20], facecolor=COLORS["panel"])
        ax4.bar(product_margin.product_line, product_margin.inventory_days, color=COLORS["violet"])
        ax4.tick_params(axis="x", labelrotation=25, labelsize=8)
        ax4.set_title("Inventory days by product line", loc="left", fontsize=11, fontweight="bold")
        ax4.grid(axis="y", color=COLORS["line"], linewidth=0.7, alpha=0.8)
        fig.savefig(p(f"output/screenshots/{file_name}"), dpi=150, bbox_inches="tight")
        plt.close(fig)


def build_html(dims: dict[str, pd.DataFrame], facts: dict[str, pd.DataFrame], exports: dict[str, pd.DataFrame], metrics: dict) -> None:
    current = metrics["current"]
    top_products = exports["latest_product_margin"].head(8).copy()
    watch = exports["latest_line_watchlist"].head(8).copy()
    rows_products = "\n".join(
        f"<tr><td>{r.product}</td><td>{r.product_line}</td><td>{money(r.actual_revenue)}</td><td>{money(r.gross_margin)}</td><td>{pct(r.gross_margin_pct)}</td><td>{money(r.inventory_value)}</td></tr>"
        for r in top_products.itertuples()
    )
    rows_watch = "\n".join(
        f"<tr><td>{r.plant_name}</td><td>{r.line_name}</td><td>{r.product_line}</td><td>{pct(r.yield_pct)}</td><td>{pct(r.scrap_rate)}</td><td>{pct(r.utilization_pct)}</td><td>{r.inventory_days:.1f}</td></tr>"
        for r in watch.itertuples()
    )
    html = f"""
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Manufacturing Cost FP&A</title>
  <style>
    :root {{ --bg:{COLORS['bg']}; --panel:#fff; --ink:{COLORS['ink']}; --muted:{COLORS['muted']}; --line:{COLORS['line']}; --steel:{COLORS['steel']}; --teal:{COLORS['teal']}; --amber:{COLORS['amber']}; --red:{COLORS['red']}; --violet:{COLORS['violet']}; }}
    body {{ margin:0; font-family:Segoe UI, Arial, sans-serif; background:var(--bg); color:var(--ink); }}
    main {{ max-width:1320px; margin:0 auto; padding:28px; }}
    header {{ display:flex; justify-content:space-between; gap:24px; align-items:flex-end; margin-bottom:18px; }}
    h1 {{ margin:0; font-size:30px; }}
    .sub {{ color:var(--muted); margin-top:6px; }}
    .tabs {{ display:flex; gap:8px; margin:18px 0; }}
    .tabs button {{ border:1px solid var(--line); background:#fff; padding:9px 14px; border-radius:6px; cursor:pointer; font-weight:600; }}
    .tabs button.active {{ background:var(--steel); color:#fff; border-color:var(--steel); }}
    .grid {{ display:grid; grid-template-columns:repeat(4,1fr); gap:12px; }}
    .card {{ background:var(--panel); border:1px solid var(--line); border-radius:8px; padding:14px; min-height:82px; box-sizing:border-box; }}
    .label {{ color:var(--muted); font-size:12px; }}
    .value {{ font-size:24px; font-weight:750; margin-top:10px; }}
    .section {{ display:none; }}
    .section.active {{ display:block; }}
    .panel {{ background:var(--panel); border:1px solid var(--line); border-radius:8px; padding:14px; }}
    .two {{ display:grid; grid-template-columns:1fr 1fr; gap:14px; margin-top:14px; }}
    img {{ width:100%; border-radius:6px; border:1px solid var(--line); }}
    table {{ width:100%; border-collapse:collapse; font-size:13px; }}
    th,td {{ padding:9px; border-bottom:1px solid var(--line); text-align:left; }}
    th {{ color:#334155; font-size:12px; }}
    @media (max-width:900px) {{ .grid,.two {{ grid-template-columns:1fr; }} header {{ display:block; }} }}
  </style>
</head>
<body>
<main>
  <header>
    <div>
      <h1>Manufacturing Cost FP&A</h1>
      <div class="sub">Executive-ready BI preview. Final target: Power BI PBIX with 3 native tabs.</div>
    </div>
    <div class="sub">Synthetic fixed-seed data | Latest complete month: {LATEST_MONTH}</div>
  </header>
  <nav class="tabs">
    <button class="active" data-tab="overview">Overview</button>
    <button data-tab="variance">Cost Variance</button>
    <button data-tab="ops">Yield & WC</button>
  </nav>
  <section id="overview" class="section active">
    <div class="grid">
      <div class="card"><div class="label">Revenue</div><div class="value" style="color:var(--steel)">{money(current['actual_revenue'])}</div></div>
      <div class="card"><div class="label">Gross Margin</div><div class="value" style="color:var(--teal)">{money(current['gross_margin'])}</div></div>
      <div class="card"><div class="label">Cost Variance</div><div class="value" style="color:var(--amber)">{money(current['cost_variance'])}</div></div>
      <div class="card"><div class="label">Yield</div><div class="value" style="color:var(--teal)">{pct(current['yield_pct'])}</div></div>
    </div>
    <div class="two"><div class="panel"><img src="screenshots/tab1_overview.png" alt="Overview screenshot"></div><div class="panel"><table><thead><tr><th>Product</th><th>Line</th><th>Revenue</th><th>GM</th><th>GM %</th><th>Inventory</th></tr></thead><tbody>{rows_products}</tbody></table></div></div>
  </section>
  <section id="variance" class="section">
    <div class="grid">
      <div class="card"><div class="label">Material Variance</div><div class="value" style="color:var(--amber)">{money(current['material_variance'])}</div></div>
      <div class="card"><div class="label">Labor Variance</div><div class="value" style="color:var(--red)">{money(current['labor_variance'])}</div></div>
      <div class="card"><div class="label">OH Variance</div><div class="value" style="color:var(--violet)">{money(current['overhead_variance'])}</div></div>
      <div class="card"><div class="label">Yield Loss</div><div class="value" style="color:var(--red)">{money(current['yield_loss_cost'])}</div></div>
    </div>
    <div class="panel" style="margin-top:14px"><img src="screenshots/tab2_variance.png" alt="Variance screenshot"></div>
  </section>
  <section id="ops" class="section">
    <div class="grid">
      <div class="card"><div class="label">Yield</div><div class="value" style="color:var(--teal)">{pct(current['yield_pct'])}</div></div>
      <div class="card"><div class="label">Scrap Rate</div><div class="value" style="color:var(--red)">{pct(current['scrap_rate'])}</div></div>
      <div class="card"><div class="label">Utilization</div><div class="value" style="color:var(--steel)">{pct(current['utilization_pct'])}</div></div>
      <div class="card"><div class="label">Scenario Uplift</div><div class="value" style="color:var(--teal)">{money(current['cost_variance'] * 0.12)}</div></div>
    </div>
    <div class="two"><div class="panel"><img src="screenshots/tab3_yield_capacity_wc.png" alt="Yield capacity screenshot"></div><div class="panel"><table><thead><tr><th>Plant</th><th>Line</th><th>Product Line</th><th>Yield</th><th>Scrap</th><th>Utilization</th><th>Inv Days</th></tr></thead><tbody>{rows_watch}</tbody></table></div></div>
  </section>
</main>
<script>
  document.querySelectorAll('.tabs button').forEach(btn => btn.addEventListener('click', () => {{
    document.querySelectorAll('.tabs button').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
    btn.classList.add('active');
    document.getElementById(btn.dataset.tab).classList.add('active');
  }}));
</script>
</body>
</html>
""".strip()
    write_text("output/dashboard_final.html", html)
    write_text("output/dashboard_complete.html", html)


def write_model_docs(all_tables: dict[str, pd.DataFrame], metrics: dict) -> None:
    dictionary_rows = []
    for table, df in all_tables.items():
        dictionary_rows.append(f"## {table}\n\n| Column | Type | Non-null | Example |\n|---|---|---:|---|")
        for col in df.columns:
            sample = "" if df.empty else str(df[col].dropna().iloc[0]) if len(df[col].dropna()) else ""
            dictionary_rows.append(f"| {col} | {df[col].dtype} | {int(df[col].notna().sum())} | {sample} |")
        dictionary_rows.append("")
    content = "# Data Dictionary\n\n" + "\n".join(dictionary_rows)
    write_text("data/data_dictionary.md", content)
    write_text("model/data_dictionary.md", content)
    write_text(
        "model/relationship_map.md",
        """# Relationship Map

| From table | From column | To table | To column | Cardinality | Filter |
|---|---|---|---|---|---|
| fact_manufacturing_month | year_month | dim_date | year_month | many-to-one | single |
| fact_manufacturing_month | plant_id | dim_plant | plant_id | many-to-one | single |
| fact_manufacturing_month | line_id | dim_line | line_id | many-to-one | single |
| fact_manufacturing_month | product_id | dim_product | product_id | many-to-one | single |
| fact_cost_variance_bridge | year_month | dim_date | year_month | many-to-one | single |

`dim_scenario` is intentionally disconnected and used by scenario measures via `SELECTEDVALUE`.
""",
    )
    write_text(
        "model/metric_definitions.md",
        f"""# Metric Definitions

Latest complete month: `{LATEST_MONTH}`.

| Metric | Definition |
|---|---|
| Actual Revenue | Good units multiplied by realized price. |
| Actual COGS | Actual material, labor, overhead, scrap, and rework cost. |
| Standard COGS | Actual produced units valued at standard material, labor, and overhead rates. |
| Cost Variance vs Standard | Actual COGS minus Standard COGS. Positive is unfavorable. |
| Material Variance | Actual material cost minus standard material cost. |
| Labor Variance | Actual labor cost minus standard labor cost. |
| Overhead Variance | Actual overhead cost minus standard overhead cost. |
| Yield Loss Cost | Scrap cost plus rework cost. |
| Gross Margin | Actual Revenue minus Actual COGS. |
| Gross Margin % | `Gross Margin / Actual Revenue` using `DIVIDE`. |
| Yield % | `Good Units / Produced Units` using `DIVIDE`. |
| Scrap Rate | `Scrap Units / Produced Units` using `DIVIDE`. |
| Utilization % | `Run Hours / Available Hours` using `DIVIDE`. |
| Inventory Days | `Inventory Value / Actual COGS * 30` using `DIVIDE`. |
| Scenario EBITDA Uplift | Scenario gross margin less current gross margin. |

Latest reconciliation: revenue {money(metrics['current']['actual_revenue'])}, actual COGS {money(metrics['current']['actual_cogs'])}, cost variance {money(metrics['current']['cost_variance'])}, gross margin {money(metrics['current']['gross_margin'])}.
""",
    )
    dax = dax_measures()
    write_text("model/dax_measures.md", dax)
    write_text("model/MEASURES.dax", dax.split("```DAX", 1)[1].split("```", 1)[0].strip())
    write_text(
        "model/semantic_model_notes.md",
        """# Semantic Model Notes

- Main grain: monthly plant x line x product in `fact_manufacturing_month`.
- Standard cost variance is decomposed into material, labor, overhead, and yield loss drivers.
- Product/plant/line/date are conformed dimensions for all operational finance visuals.
- `dim_spark_date` is disconnected and used only by KPI mini-sparkline measures so Month slicers do not collapse trends to one point.
- `dim_scenario` is disconnected and drives scenario measures without filtering facts directly.
- Rates and percentages are DAX measures with `DIVIDE`; raw rate columns are not used as KPI totals.
""",
    )
    write_json(
        "model/measure_map.json",
        {
            "measure_table": MEASURE_TABLE,
            "latest_complete_month": LATEST_MONTH,
            "measures": list(MEASURE_FORMATS.keys()),
            "critical_measures": ["Current Revenue", "Current Gross Margin", "Current Cost Variance", "Current Yield %", "Scenario EBITDA Uplift"],
        },
    )


def write_config(metrics: dict) -> None:
    write_json(
        "build/config/dashboard_config.json",
        {
            "title": "Manufacturing Cost FP&A",
            "prompt_version": "BI_A2Z_Master_Prompt_v3",
            "latest_complete_month": LATEST_MONTH,
            "data_source": "synthetic_demo",
            "seed": SEED,
            "audience": "CFO, Plant Finance, Operations, Supply Chain, and Manufacturing leadership",
            "business_goal": "Protect EBITDA by diagnosing standard cost variance, yield loss, capacity pressure, and inventory working capital.",
            "page_count": 3,
            "technical_seed": "Template/04_Profitability_Margin/Packt_Ch10_PVM.pbix",
        },
    )
    write_json(
        "build/config/page_map.json",
        {
            "pages": [
                {
                    "name": "01 Manufacturing FP&A Overview",
                    "purpose": "Monitor margin, standard cost variance, yield, utilization, unit cost, and working capital.",
                    "visuals": ["4 KPI cards with mini sparklines", "Revenue/COGS line trend", "Variance by plant", "Margin by product line", "Margin action list"],
                },
                {
                    "name": "02 Standard Cost Variance",
                    "purpose": "Explain cost variance through material, labor, overhead, and yield loss drivers.",
                    "visuals": ["4 variance KPI cards with mini sparklines", "COGS waterfall", "Material variance by product line", "Labor variance by plant", "Variance detail table"],
                },
                {
                    "name": "03 Yield Capacity & WC",
                    "purpose": "Tie yield, scrap, utilization, capacity gaps, inventory days, and scenario savings to EBITDA protection.",
                    "visuals": ["4 operations KPI cards with mini sparklines", "Yield/scrap line trend", "Utilization by line", "Inventory days", "Scenario and bottleneck table"],
                },
            ]
        },
    )
    write_json(
        "build/config/slicer_map.json",
        {
            "placement": "top_filter_bar",
            "layout": {"x": 24, "y": 72, "slot_width": 296, "slot_height": 52, "gap": 16},
            "global_slicers": [
                {"label": "Month", "field": "dim_date[year_month]", "type": "dropdown", "single_select": True, "sync_group": "p16_month"},
                {"label": "Plant", "field": "dim_plant[plant_name]", "type": "dropdown", "sync_group": "p16_plant"},
                {"label": "Product Line", "field": "dim_product[product_line]", "type": "dropdown", "sync_group": "p16_product_line"},
                {"label": "Line", "field": "dim_line[line_name]", "type": "dropdown", "sync_group": "p16_line"},
            ],
            "scenario_slicer": {"label": "Scenario", "field": "dim_scenario[scenario_name]", "type": "dropdown", "single_select": True, "sync_group": "p16_scenario"},
        },
    )
    write_json(
        "build/config/theme.json",
        {
            "name": "Manufacturing Cost FP&A Light",
            "dataColors": [COLORS["steel"], COLORS["teal"], COLORS["amber"], COLORS["red"], COLORS["violet"], COLORS["slate"], COLORS["green"]],
            "background": COLORS["bg"],
            "foreground": COLORS["ink"],
            "tableAccent": COLORS["steel"],
            "good": COLORS["green"],
            "neutral": COLORS["amber"],
            "bad": COLORS["red"],
        },
    )
    write_json(
        "build/config/visual_map.json",
        {
            "visual_count_target": 51,
            "native_visual_types": ["cardVisual", "slicer", "lineChart", "barChart", "waterfallChart", "tableEx", "textbox"],
            "kpi_pattern": "4 focused cards per page plus native mini line-chart sparklines",
            "latest_month_snapshot": metrics["current"],
        },
    )


def run_command(args: list[str], cwd: Path | None = None, timeout: int = 60) -> dict:
    try:
        proc = subprocess.run(args, cwd=str(cwd or ROOT), text=True, capture_output=True, timeout=timeout, shell=False)
        return {"args": args, "returncode": proc.returncode, "stdout": proc.stdout, "stderr": proc.stderr}
    except Exception as exc:
        return {"args": args, "error": str(exc)}


def get_pbi_info() -> dict:
    result = run_command(["pbi-tools", "info"], timeout=45)
    raw = (result.get("stdout") or "") + "\n" + (result.get("stderr") or "")
    json_start = raw.find("{")
    if json_start >= 0:
        try:
            parsed = json.loads(raw[json_start:])
        except Exception:
            parsed = None
    else:
        parsed = None
    return {"raw": raw, "parsed": parsed, "command": result}


def write_environment_docs() -> None:
    pbi_info = get_pbi_info()
    pbidesktop_exe = Path(r"C:\Program Files\Microsoft Power BI Desktop\bin\PBIDesktop.exe")
    store_probe = run_command(["powershell", "-NoProfile", "-Command", "Get-StartApps | Where-Object { $_.Name -like '*Power BI Desktop*' -or $_.AppID -like '*PowerBI*' } | Select-Object Name,AppID | ConvertTo-Json -Depth 3"], timeout=30)
    dotnet_probe = run_command(["powershell", "-NoProfile", "-Command", "if (Get-Command dotnet -ErrorAction SilentlyContinue) { dotnet --info } else { 'dotnet not found' }"], timeout=30)
    env = {
        "project_root": str(ROOT),
        "expected_final_pbix": str(p("output/dashboard_final.pbix")),
        "pbidesktop_command": shutil.which("PBIDesktop.exe"),
        "pbidesktop_program_files": pbidesktop_exe.exists(),
        "pbi_tools_command": shutil.which("pbi-tools"),
        "dotnet": dotnet_probe,
        "start_apps": store_probe,
        "pbi_tools_info": pbi_info["parsed"],
    }
    write_json("_agent/environment_check.json", env)
    sessions = []
    if pbi_info["parsed"] and pbi_info["parsed"].get("pbiSessions"):
        sessions = pbi_info["parsed"].get("pbiSessions", [])
    session_lines = "\n".join(f"- PID {s.get('ProcessId')} Port {s.get('Port')} PBIX `{s.get('PbixPath')}`" for s in sessions) or "- No running sessions detected."
    write_text(
        "_agent/environment_check.md",
        f"""# Environment Check

Project root: `{ROOT}`
Expected PBIX: `{p('output/dashboard_final.pbix')}`

| Check | Result |
|---|---|
| Power BI Desktop command | `{env['pbidesktop_command']}` |
| Program Files Desktop path exists | `{env['pbidesktop_program_files']}` |
| pbi-tools command | `{env['pbi_tools_command']}` |
| dotnet | `{(dotnet_probe.get('stdout') or dotnet_probe.get('stderr') or '').strip().splitlines()[0] if dotnet_probe else 'unknown'}` |

Running Power BI sessions at intake:

{session_lines}
""",
    )
    write_text(
        "_agent/session_guard.md",
        f"""# Session Guard

Current project path: `{ROOT}`
Expected final PBIX path: `{p('output/dashboard_final.pbix')}`

Power BI windows/sessions detected before Project 16 Desktop work:

{session_lines}

Selected session rule:
- Only use a Power BI Desktop session whose `pbi-tools info` `PbixPath` exactly equals `{p('output/dashboard_final.pbix')}`.
- Existing `dashboard_final` windows from Project 13 are unrelated and must be ignored.
- Do not save through UI automation unless the exact Project 16 session is identified.
""",
    )


def write_docs(metrics: dict, validation: dict) -> None:
    write_text(
        "docs/design_research.md",
        """# Design Research

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
""",
    )
    write_text(
        "_agent/intake_brief.md",
        f"""# Intake Brief

Topic: Manufacturing Cost FP&A.
Project path: `{ROOT}`.
Output target: `output/dashboard_final.pbix`.
Delivery level: executive-ready portfolio demo.
Source: synthetic data with fixed seed `{SEED}` because no production source was supplied.
Audience: CFO, Plant Finance, Operations, Supply Chain, and Manufacturing leadership.
Latest complete month: `{LATEST_MONTH}`.
Page count: 3 tabs per user request.

Assumptions:
- This is a portfolio/demo BI product, so synthetic manufacturing data is acceptable and documented.
- Currency is USD.
- Standard cost variance positive values are unfavorable.
- The dashboard prioritizes EBITDA protection through material, labor, overhead, yield, capacity, and inventory levers.
""",
    )
    write_text(
        "_agent/run_log.md",
        f"""# Run Log

## {TODAY}

- Read BI A-Z Master Prompt v3 and Project 16 README.
- Ran Data Analytics dashboard preflight.
- Reviewed available template library and selected `Packt_Ch10_PVM.pbix` as the technical seed.
- Generated synthetic manufacturing FP&A data with seed `{SEED}`.
- Built model docs, DAX measures, config maps, native Power BI layout JSON, HTML preview, screenshots, and QA docs.
- Project 20 style pass: moved native slicers into a dedicated top filter bar above the KPI row and regenerated preview evidence.
- Project 20 upgrade pass: rebuilt KPI areas as four focused cards per page with native mini sparklines; tightened slicer typography/sync groups; changed trend panels to line visuals; improved chart units and table styling.
- Next stage: copy seed PBIX, apply Project 16 layout, launch exact Project 16 PBIX in Power BI Desktop, push model, save, reopen, and validate.
""",
    )
    write_text(
        "_agent/pbix_authoring_decision.md",
        """# PBIX Authoring Decision

Build route: `SCRIPTED_DESKTOP_PBIX` with a template-compatible PBIX seed.

Decision:
- Use `Template/04_Profitability_Margin/Packt_Ch10_PVM.pbix` as a technical container only.
- Patch native report layout to Project 16 before Desktop authoring.
- Launch the exact Project 16 PBIX through Power BI Desktop.
- Push the Project 16 semantic model into the exact Desktop session through TOM/XMLA.
- Save and reopen the exact PBIX in Desktop.

Why this route:
- It avoids using pbi-tools compile as a full PBIX authoring route.
- It keeps the final file as a Desktop-openable PBIX.
- It gives Project 16 native visuals, native slicers, a real model, and project-specific measures.
""",
    )
    write_text(
        "_agent/failure_matrix.md",
        """# Failure Matrix

| Failure | Mitigation |
|---|---|
| Existing Power BI windows have same title | Use `pbi-tools info` and exact `PbixPath` match before push/save. |
| Seed has old model/report bindings | Replace report layout and push Project 16 model; validate no old fields remain in extraction. |
| Desktop save cannot be verified | Mark PBIX blocked and keep build package/HTML preview as supplemental only. |
| Visual binding errors | Re-extract PBIX and compare layout fields against `model/MEASURES.dax` and prepared CSV schemas. |
| SecurityBindings causes corrupt patched package | Remove stale `SecurityBindings` when applying native layout. |
""",
    )
    write_text(
        "docs/handoff_notes.md",
        f"""# Handoff Notes

Project: Manufacturing Cost FP&A.
Main output target: `output/dashboard_final.pbix`.
Supplemental preview: `output/dashboard_final.html`.

Layout update:
- Slicers are positioned in a dedicated top filter bar on every page.
- Overview and Variance use Month, Plant, Product Line, and Line.
- Yield, Capacity & WC uses Month, Plant, Product Line, and Scenario.
- Each page uses four larger KPI cards with native mini sparklines beneath the value.
- Main trend panels are native line charts, and tables use compact banded rows with numeric alignment.

Latest-month snapshot:
- Revenue: {money(metrics['current']['actual_revenue'])}
- Actual COGS: {money(metrics['current']['actual_cogs'])}
- Cost variance vs standard: {money(metrics['current']['cost_variance'])}
- Gross margin: {money(metrics['current']['gross_margin'])}
- Gross margin %: {pct(metrics['current']['gross_margin_pct'])}
- Yield: {pct(metrics['current']['yield_pct'])}
- Utilization: {pct(metrics['current']['utilization_pct'])}
- Inventory value: {money(metrics['current']['inventory_value'])}

Data is synthetic with seed `{SEED}` and is suitable for portfolio/demo use, not production decisioning.
""",
    )
    write_text(
        "docs/rebuild_guide.md",
        """# Rebuild Guide

1. Run `python build/scripts/00_build_project16.py`.
2. Run `python build/scripts/10_apply_native_report_project16.py` to patch the seed layout into `output/dashboard_final.pbix`.
3. Launch with `powerbi/launch_powerbi.ps1`.
4. After the exact Project 16 PBIX opens, run `build/scripts/08_push_project16_model_to_powerbi_desktop.ps1`.
5. Save the report in Power BI Desktop.
6. Reopen the exact file and validate with `pbi-tools extract` and `pbi-tools export-data`.
""",
    )
    write_text(
        "docs/refresh_guide.md",
        """# Refresh Guide

The prepared CSV files are the refresh boundary.

- Regenerate or replace files in `data/prepared/`.
- Keep table and column names stable.
- Open the exact Project 16 PBIX in Power BI Desktop.
- Re-run `build/scripts/08_push_project16_model_to_powerbi_desktop.ps1`.
- Save and re-run QA.
""",
    )
    write_text(
        "docs/changelog.md",
        f"""# Changelog

## {TODAY}

- Created Project 16 Manufacturing Cost FP&A BI product structure.
- Generated synthetic manufacturing standard-cost, production, inventory, and scenario data.
- Added semantic model docs, DAX measures, native 3-tab Power BI layout JSON, theme, HTML preview, screenshots, runbooks, and QA docs.
- Upgraded slicer placement to a top filter bar across all pages, preserving the light manufacturing FP&A style while borrowing Project 20's compact aligned control pattern.
- Upgraded KPI cards, sparklines, chart units, trend chart types, slicer text fit, and table styling toward the Project 20 standard.
""",
    )
    write_text(
        "docs/issue_log.md",
        """# Issue Log

| Issue | Status | Notes |
|---|---|---|
| No production data supplied | Accepted | Synthetic fixed-seed portfolio data generated and documented. |
| Existing Project 13 Power BI sessions detected | Controlled | Session guard requires exact Project 16 `PbixPath` before push/save. |
| Seed PBIX contains prior PVM sample model | Controlled | Seed is technical container only; Project 16 model and layout replace current content during Desktop build. |
""",
    )
    write_text(
        "qa/qa_checklist.md",
        f"""# QA Checklist

| Area | Status | Evidence |
|---|---|---|
| Data QA | {validation['status']} | `data/validated/validation_summary.json` |
| Metric QA | PASS | `qa/reconciliation.csv` |
| Visual QA | PASS for generated preview; pending Desktop final check | `output/screenshots/` |
| Interaction QA | Designed; pending Desktop slicer click check | `qa/interaction_qa_notes.md` |
| File QA | Pending Desktop save/open-check | `qa/pbix_final_validation.json` |
""",
    )
    write_text(
        "qa/interaction_qa_notes.md",
        """# Interaction QA Notes

Planned PBIX interactions:
- Month, Plant, Product Line, and Line slicers appear in the top filter bar on Overview and Variance pages.
- Month, Plant, Product Line, and Scenario slicers appear in the top filter bar on Yield, Capacity & WC.
- The top slicer slots share the same y-position, width, height, and z-order pattern on each page.
- Native visuals are configured for default cross-filtering.
- Final click testing requires Power BI Desktop after save/reopen.
""",
    )
    write_text(
        "qa/visual_qa_notes.md",
        """# Visual QA Notes

Generated preview screenshots cover all 3 requested tabs.

Native PBIX layout contains:
- 3 page title textboxes.
- 12 top-bar slicers.
- 12 focused KPI cards.
- 12 native mini line-chart sparklines layered inside KPI cards.
- Trend line, bar, waterfall, and detail-table visuals.

Design follows a light manufacturing FP&A theme with consistent spacing, top aligned slicers, Project 20-style focused KPI cards, and restrained color use.
""",
    )
    write_text(
        "qa/performance_qa_notes.md",
        """# Performance QA Notes

The dataset is compact for portfolio use:
- Monthly plant x line x product fact table.
- Imported CSV tables.
- Aggregations are handled by DAX measures over a modest row count.

Expected Desktop performance is interactive on a local machine.
""",
    )
    write_text(
        "qa/regression_qa_notes.md",
        """# Regression QA Notes

No prior Project 16 PBIX existed. Regression scope is limited to:
- Rebuild generator creates the same row counts with seed 160416.
- Variance bridge ties to actual COGS.
- Native layout references only Project 16 table/measure names.
""",
    )


def write_powerbi_scripts() -> None:
    write_text(
        "powerbi/launch_powerbi.ps1",
        rf"""
$ErrorActionPreference = "Stop"
$pbix = "{p('output/dashboard_final.pbix')}"
if (-not (Test-Path $pbix)) {{
  throw "PBIX not found: $pbix"
}}
& pbi-tools launch-pbi -pbixPath $pbix
""",
    )
    write_text(
        "powerbi/notes/authoring_strategy.md",
        """# Authoring Strategy

Use the selected PVM PBIX only as a technical seed. The Project 16 model is pushed through Power BI Desktop TOM/XMLA from prepared CSV files, then the report is saved by Desktop. The native layout is Project 16-specific and contains only manufacturing cost FP&A visuals.
""",
    )
    write_text(
        "powerbi/notes/desktop_ui_runbook.md",
        """# Desktop UI Runbook

1. Confirm existing Project 13 sessions are ignored.
2. Run `powerbi/launch_powerbi.ps1`.
3. Confirm `pbi-tools info` shows a session with `PbixPath` equal to Project 16 `output/dashboard_final.pbix`.
4. Run `build/scripts/08_push_project16_model_to_powerbi_desktop.ps1`.
5. Save in Desktop.
6. Reopen exact PBIX and capture screenshots/validation notes.
""",
    )
    write_text(
        "powerbi/notes/pbix_build_runbook.md",
        """# PBIX Build Runbook

Route: `SCRIPTED_DESKTOP_PBIX`.

Critical final criteria:
- `output/dashboard_final.pbix` exists.
- Exact PBIX opens in Power BI Desktop.
- Model contains Project 16 manufacturing tables and KPI measures.
- Report has 3 native pages and native visuals.
- `pbi-tools extract` and `pbi-tools export-data` pass where available.
""",
    )

    write_text("build/scripts/08_push_project16_model_to_powerbi_desktop.ps1", push_model_ps1())
    write_text("build/scripts/10_apply_native_report_project16.py", apply_layout_py())


def push_model_ps1() -> str:
    measures = dax_measures().split("```DAX", 1)[1].split("```", 1)[0].strip().splitlines()
    add_measures = []
    for line in measures:
        if "=" not in line:
            continue
        name, expr = line.split("=", 1)
        name = name.strip()
        expr = expr.strip().replace('"', '""')
        fmt = MEASURE_FORMATS.get(name, "")
        add_measures.append(f'  Add-KpiMeasure -Table $measureTable -Name "{name}" -Expression "{expr}" -FormatString "{fmt}"')
    add_measures_block = "\n".join(add_measures)
    return rf'''
param(
  [int]$Port = 0,
  [string]$ProjectRoot = "{ROOT}",
  [string]$PbixPath = "{p('output/dashboard_final.pbix')}"
)

$ErrorActionPreference = "Stop"

function Resolve-PowerBIPort {{
  if ($Port -gt 0) {{ return $Port }}
  $infoRaw = & pbi-tools info 2>&1 | Out-String
  $jsonStart = $infoRaw.IndexOf("{{")
  if ($jsonStart -lt 0) {{ throw "Could not find JSON payload in pbi-tools info output." }}
  $info = $infoRaw.Substring($jsonStart) | ConvertFrom-Json
  $resolvedPbix = [System.IO.Path]::GetFullPath($PbixPath)
  $matches = @($info.pbiSessions | Where-Object {{ $_.PbixPath -and ([System.IO.Path]::GetFullPath($_.PbixPath) -ieq $resolvedPbix) }})
  if ($matches.Count -ne 1) {{
    $sessionText = ($info.pbiSessions | ForEach-Object {{ "PID=$($_.ProcessId) Port=$($_.Port) PbixPath=$($_.PbixPath)" }}) -join "`n"
    throw "Expected exactly one Project 16 Power BI session for $resolvedPbix. Found $($matches.Count). Sessions:`n$sessionText"
  }}
  return [int]$matches[0].Port
}}

function Import-PowerBIAssemblies {{
  $bin = "C:\Program Files\Microsoft Power BI Desktop\bin"
  [System.IO.Directory]::SetCurrentDirectory($bin)
  $dlls = @(
    "Microsoft.AnalysisServices.Server.Core.dll",
    "Microsoft.AnalysisServices.Server.Tabular.dll",
    "Microsoft.AnalysisServices.Server.Tabular.Json.dll"
  )
  foreach ($dll in $dlls) {{
    $path = Join-Path $bin $dll
    if (-not (Test-Path $path)) {{ throw "Missing Power BI TOM assembly: $path" }}
    [void][System.Reflection.Assembly]::LoadFrom($path)
  }}
}}

function Escape-MPath([string]$Path) {{
  return $Path.Replace("\", "\\").Replace('"', '""')
}}

function Get-ColumnType([string]$ColumnName) {{
  $intCols = @("date_key", "year", "month_no", "month_index", "is_latest_complete_month", "bridge_order")
  $dateCols = @("month_start_date")
  $doubleCols = @(
    "productivity_index", "labor_rate_usd", "fixed_overhead_rate_usd", "material_price_index",
    "standard_price_usd", "standard_material_cost_usd", "standard_labor_hours", "standard_machine_hours", "complexity_index", "base_monthly_units",
    "monthly_capacity_units", "shift_count", "material_cost_reduction_pct", "labor_efficiency_gain_pct", "overhead_absorption_gain_pct", "scrap_reduction_pct", "volume_delta_pct",
    "budget_units", "produced_units", "good_units", "scrap_units", "rework_units", "capacity_units", "available_hours", "run_hours", "downtime_hours",
    "actual_revenue", "budget_revenue", "standard_material_cost", "standard_labor_cost", "standard_overhead_cost", "standard_cogs",
    "actual_material_cost", "actual_labor_cost", "actual_overhead_cost", "scrap_cost", "rework_cost", "actual_cogs",
    "material_variance", "labor_variance", "overhead_variance", "yield_loss_cost", "gross_margin", "inventory_units", "inventory_value", "slow_moving_inventory_value",
    "bridge_amount"
  )
  if ($intCols -contains $ColumnName) {{ return "Int64" }}
  if ($dateCols -contains $ColumnName) {{ return "DateTime" }}
  if ($doubleCols -contains $ColumnName) {{ return "Double" }}
  return "String"
}}

function New-MExpression {{
  param([string]$CsvPath, [array]$Columns)
  $typedRows = @()
  foreach ($col in $Columns) {{
    $mType = switch ($col.Type) {{
      "String" {{ "type text" }}
      "Int64" {{ "Int64.Type" }}
      "Double" {{ "type number" }}
      "DateTime" {{ "type date" }}
      default {{ "type text" }}
    }}
    $typedRows += "        {{`"$($col.Name)`", $mType}}"
  }}
  $typedBlock = $typedRows -join ",`n"
  $escaped = Escape-MPath $CsvPath
  return @"
let
    Source = Csv.Document(File.Contents("$escaped"), [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]),
    PromotedHeaders = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    TypedColumns = Table.TransformColumnTypes(PromotedHeaders, {{
$typedBlock
    }}, "en-US")
in
    TypedColumns
"@
}}

function Get-CsvColumns {{
  param([string]$CsvPath)
  $reader = [System.IO.StreamReader]::new($CsvPath)
  try {{ $header = $reader.ReadLine() }} finally {{ $reader.Close() }}
  if (-not $header) {{ throw "CSV has no header: $CsvPath" }}
  return $header.Split(",") | ForEach-Object {{ [ordered]@{{ Name = $_.Trim('"'); Type = Get-ColumnType $_.Trim('"') }} }}
}}

function Add-ImportTable {{
  param([Microsoft.AnalysisServices.Tabular.Model]$Model, [string]$Name, [string]$CsvPath)
  $columns = @(Get-CsvColumns -CsvPath $CsvPath)
  $table = New-Object Microsoft.AnalysisServices.Tabular.Table
  $table.Name = $Name
  foreach ($col in $columns) {{
    $column = New-Object Microsoft.AnalysisServices.Tabular.DataColumn
    $column.Name = $col.Name
    $column.SourceColumn = $col.Name
    $column.DataType = [Microsoft.AnalysisServices.Tabular.DataType]::$($col.Type)
    $column.SummarizeBy = [Microsoft.AnalysisServices.Tabular.AggregateFunction]::None
    $table.Columns.Add($column) | Out-Null
  }}
  $source = New-Object Microsoft.AnalysisServices.Tabular.MPartitionSource
  $source.Expression = New-MExpression -CsvPath $CsvPath -Columns $columns
  $partition = New-Object Microsoft.AnalysisServices.Tabular.Partition
  $partition.Name = "$Name-Import"
  $partition.Mode = [Microsoft.AnalysisServices.Tabular.ModeType]::Import
  $partition.Source = $source
  $table.Partitions.Add($partition) | Out-Null
  $Model.Tables.Add($table) | Out-Null
}}

function Add-MeasureTable {{
  param([Microsoft.AnalysisServices.Tabular.Model]$Model)
  $table = New-Object Microsoft.AnalysisServices.Tabular.Table
  $table.Name = "KPI Measures"
  $column = New-Object Microsoft.AnalysisServices.Tabular.DataColumn
  $column.Name = "Measure Group"
  $column.SourceColumn = "Measure Group"
  $column.DataType = [Microsoft.AnalysisServices.Tabular.DataType]::String
  $column.SummarizeBy = [Microsoft.AnalysisServices.Tabular.AggregateFunction]::None
  $column.IsHidden = $true
  $table.Columns.Add($column) | Out-Null
  $source = New-Object Microsoft.AnalysisServices.Tabular.MPartitionSource
  $source.Expression = @"
let
    Source = #table(type table [Measure Group = text], {{"Manufacturing Cost FP&A"}})
in
    Source
"@
  $partition = New-Object Microsoft.AnalysisServices.Tabular.Partition
  $partition.Name = "KPI Measures-Import"
  $partition.Mode = [Microsoft.AnalysisServices.Tabular.ModeType]::Import
  $partition.Source = $source
  $table.Partitions.Add($partition) | Out-Null
  $Model.Tables.Add($table) | Out-Null
  return $table
}}

function Add-Relationship {{
  param([Microsoft.AnalysisServices.Tabular.Model]$Model, [string]$FromTable, [string]$FromColumn, [string]$ToTable, [string]$ToColumn)
  $relationship = New-Object Microsoft.AnalysisServices.Tabular.SingleColumnRelationship
  $relationship.Name = "rel_${{FromTable}}_${{FromColumn}}_${{ToTable}}_${{ToColumn}}"
  $relationship.FromColumn = $Model.Tables[$FromTable].Columns[$FromColumn]
  $relationship.ToColumn = $Model.Tables[$ToTable].Columns[$ToColumn]
  $relationship.CrossFilteringBehavior = [Microsoft.AnalysisServices.Tabular.CrossFilteringBehavior]::OneDirection
  $Model.Relationships.Add($relationship) | Out-Null
}}

function Add-KpiMeasure {{
  param([Microsoft.AnalysisServices.Tabular.Table]$Table, [string]$Name, [string]$Expression, [string]$FormatString = "")
  $measure = New-Object Microsoft.AnalysisServices.Tabular.Measure
  $measure.Name = $Name
  $measure.Expression = $Expression
  if ($FormatString) {{ $measure.FormatString = $FormatString }}
  $Table.Measures.Add($measure) | Out-Null
}}

$portToUse = Resolve-PowerBIPort
Import-PowerBIAssemblies
$prepared = Join-Path $ProjectRoot "data\prepared"
$tableNames = @("dim_date", "dim_spark_date", "dim_plant", "dim_product", "dim_line", "dim_scenario", "fact_manufacturing_month", "fact_cost_variance_bridge")

$server = New-Object Microsoft.AnalysisServices.Tabular.Server
$server.Connect("localhost:$portToUse")
try {{
  if ($server.Databases.Count -lt 1) {{ throw "Connected to Power BI Desktop, but no database was found." }}
  $database = $server.Databases[0]
  $model = $database.Model
  while ($model.Relationships.Count -gt 0) {{ $model.Relationships.Remove($model.Relationships[0]) }}
  while ($model.Tables.Count -gt 0) {{ $model.Tables.Remove($model.Tables[0]) }}

  $model.Culture = "en-US"
  $model.SourceQueryCulture = "en-US"
  $model.DataAccessOptions.LegacyRedirects = $true
  $model.DataAccessOptions.ReturnErrorValuesAsNull = $true

  foreach ($name in $tableNames) {{
    $csvPath = Join-Path $prepared "$name.csv"
    if (-not (Test-Path $csvPath)) {{ throw "Missing prepared CSV: $csvPath" }}
    Add-ImportTable -Model $model -Name $name -CsvPath $csvPath
  }}

  $measureTable = Add-MeasureTable -Model $model
  Add-Relationship -Model $model -FromTable "fact_manufacturing_month" -FromColumn "year_month" -ToTable "dim_date" -ToColumn "year_month"
  Add-Relationship -Model $model -FromTable "fact_manufacturing_month" -FromColumn "plant_id" -ToTable "dim_plant" -ToColumn "plant_id"
  Add-Relationship -Model $model -FromTable "fact_manufacturing_month" -FromColumn "line_id" -ToTable "dim_line" -ToColumn "line_id"
  Add-Relationship -Model $model -FromTable "fact_manufacturing_month" -FromColumn "product_id" -ToTable "dim_product" -ToColumn "product_id"
  Add-Relationship -Model $model -FromTable "fact_cost_variance_bridge" -FromColumn "year_month" -ToTable "dim_date" -ToColumn "year_month"

{add_measures_block}

  $model.SaveChanges()
  $model.RequestRefresh([Microsoft.AnalysisServices.Tabular.RefreshType]::Full)
  $model.SaveChanges()
  $summary = [ordered]@{{
    status = "model_pushed"
    port = $portToUse
    database = $database.Name
    tables = @($model.Tables | ForEach-Object {{ $_.Name }})
    table_count = $model.Tables.Count
    relationship_count = $model.Relationships.Count
    measure_count = ($model.Tables | ForEach-Object {{ $_.Measures.Count }} | Measure-Object -Sum).Sum
    project_root = $ProjectRoot
    pbix_path = $PbixPath
  }}
  $summary | ConvertTo-Json -Depth 5
}}
finally {{
  $server.Disconnect()
}}
'''.strip()


def apply_layout_py() -> str:
    return rf'''
from __future__ import annotations

import json
import os
import shutil
import tempfile
import zipfile
from collections import Counter
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SEED_PBIX = ROOT / "powerbi" / "seed" / "Packt_Ch10_PVM_seed.pbix"
TEMPLATE_SEED = ROOT.parent / "Template" / "04_Profitability_Margin" / "Packt_Ch10_PVM.pbix"
FINAL_PBIX = ROOT / "output" / "dashboard_final.pbix"
LAYOUT_JSON = ROOT / "build" / "native_report_layout_project16.json"
THEME_JSON = ROOT / "build" / "config" / "theme.json"


def clone_zip_info(info: zipfile.ZipInfo) -> zipfile.ZipInfo:
    cloned = zipfile.ZipInfo(info.filename, date_time=info.date_time)
    cloned.comment = info.comment
    cloned.extra = info.extra
    cloned.internal_attr = info.internal_attr
    cloned.external_attr = info.external_attr
    cloned.create_system = info.create_system
    cloned.compress_type = info.compress_type
    return cloned


def count_visual_types(layout: dict) -> dict[str, int]:
    counts = Counter()
    for section in layout.get("sections", []):
        for vc in section.get("visualContainers", []):
            cfg = json.loads(vc.get("config", "{{}}"))
            counts[cfg.get("singleVisual", {{}}).get("visualType", "unknown")] += 1
    return dict(counts)


def apply_layout() -> dict:
    if not TEMPLATE_SEED.exists():
        raise FileNotFoundError(f"Template seed not found: {{TEMPLATE_SEED}}")
    if not LAYOUT_JSON.exists():
        raise FileNotFoundError(f"Layout JSON not found: {{LAYOUT_JSON}}")

    SEED_PBIX.parent.mkdir(parents=True, exist_ok=True)
    FINAL_PBIX.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(TEMPLATE_SEED, SEED_PBIX)

    archive = ROOT / "archive" / "old_versions"
    archive.mkdir(parents=True, exist_ok=True)
    if FINAL_PBIX.exists():
        backup = archive / f"dashboard_final_before_project16_layout_{{datetime.now().strftime('%Y%m%d_%H%M%S')}}.pbix"
        shutil.copy2(FINAL_PBIX, backup)
    else:
        backup = None

    layout = json.loads(LAYOUT_JSON.read_text(encoding="utf-8"))
    theme_cfg = json.loads(THEME_JSON.read_text(encoding="utf-8")) if THEME_JSON.exists() else {{}}

    with zipfile.ZipFile(SEED_PBIX, "r") as zin:
        infos = zin.infolist()
        zip_infos = {{info.filename: clone_zip_info(info) for info in infos}}
        entry_order = [info.filename for info in infos]
        entries = {{info.filename: zin.read(info.filename) for info in infos}}

    if "Report/Layout" not in entries:
        raise KeyError("Report/Layout not found in PBIX package.")

    theme_candidates = [name for name in entries if name.startswith("Report/StaticResources/SharedResources/BaseThemes/") and name.endswith(".json")]
    theme_path = theme_candidates[0] if theme_candidates else None
    entries["Report/Layout"] = json.dumps(layout, separators=(",", ":"), ensure_ascii=False).encode("utf-16le")
    if theme_path:
        try:
            theme = json.loads(entries[theme_path].decode("utf-8"))
        except Exception:
            theme = {{}}
        theme.update({{
            "name": theme_cfg.get("name", "Manufacturing Cost FP&A Light"),
            "dataColors": theme_cfg.get("dataColors", []),
            "background": theme_cfg.get("background", "#F6F7F9"),
            "foreground": theme_cfg.get("foreground", "#111827"),
            "tableAccent": theme_cfg.get("tableAccent", "#2563EB"),
            "good": theme_cfg.get("good", "#16A34A"),
            "neutral": theme_cfg.get("neutral", "#D97706"),
            "bad": theme_cfg.get("bad", "#DC2626"),
        }})
        entries[theme_path] = json.dumps(theme, separators=(",", ":"), ensure_ascii=False).encode("utf-8")

    fd, tmp_name = tempfile.mkstemp(suffix=".pbix")
    os.close(fd)
    tmp = Path(tmp_name)
    try:
        with zipfile.ZipFile(tmp, "w", compression=zipfile.ZIP_DEFLATED) as zout:
            for name in entry_order:
                if name == "SecurityBindings":
                    continue
                zout.writestr(zip_infos[name], entries[name])
        shutil.move(str(tmp), FINAL_PBIX)
    finally:
        if tmp.exists():
            tmp.unlink()

    result = {{
        "status": "PASS",
        "template_seed": str(TEMPLATE_SEED),
        "project_seed_copy": str(SEED_PBIX),
        "final_pbix": str(FINAL_PBIX),
        "layout_json": str(LAYOUT_JSON),
        "backup": str(backup) if backup else None,
        "page_count": len(layout.get("sections", [])),
        "pages": [section.get("displayName") for section in layout.get("sections", [])],
        "visual_count": sum(len(section.get("visualContainers", [])) for section in layout.get("sections", [])),
        "visual_types": count_visual_types(layout),
        "security_bindings_removed": "SecurityBindings" in entries,
        "theme_path": theme_path,
    }}
    (ROOT / "qa" / "native_layout_validation.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


if __name__ == "__main__":
    print(json.dumps(apply_layout(), indent=2))
'''.strip()


def write_reconciliation(metrics: dict, validation: dict, facts: dict[str, pd.DataFrame]) -> None:
    cur = metrics["current"]
    rec = pd.DataFrame(
        [
            ["Actual COGS", cur["actual_cogs"]],
            ["Standard COGS", cur["standard_cogs"]],
            ["Material Variance", cur["material_variance"]],
            ["Labor Variance", cur["labor_variance"]],
            ["Overhead Variance", cur["overhead_variance"]],
            ["Yield Loss Cost", cur["yield_loss_cost"]],
            ["Rebuilt Actual COGS", cur["standard_cogs"] + cur["material_variance"] + cur["labor_variance"] + cur["overhead_variance"] + cur["yield_loss_cost"]],
            ["Tie-out Difference", cur["actual_cogs"] - (cur["standard_cogs"] + cur["material_variance"] + cur["labor_variance"] + cur["overhead_variance"] + cur["yield_loss_cost"])],
        ],
        columns=["metric", "value"],
    )
    write_csv("qa/reconciliation.csv", rec)
    write_json("qa/reconciliation.json", {"metrics": metrics, "validation": validation})
    write_json(
        "qa/pbix_validation.json",
        {
            "status": "PENDING_DESKTOP",
            "reason": "PBIX seed/layout prepared; Desktop model push and save pending.",
            "expected_final_pbix": str(p("output/dashboard_final.pbix")),
        },
    )
    write_json(
        "qa/pbix_final_validation.json",
        {
            "status": "PENDING_DESKTOP",
            "opened_exact_file": False,
            "saved_reopened": False,
            "visual_error_count": None,
        },
    )


def write_readme(metrics: dict) -> None:
    write_text(
        "README.md",
        f"""# Project 16 - Manufacturing Cost FP&A

Executive-ready BI portfolio product for manufacturing standard cost variance, capacity, yield, inventory, and product margin diagnostics.

Main target: `output/dashboard_final.pbix`.
Supplemental preview: `output/dashboard_final.html`.

Tabs:
- Manufacturing FP&A Overview
- Standard Cost Variance
- Yield, Capacity & Working Capital

Synthetic data seed: `{SEED}`.
Latest complete month: `{LATEST_MONTH}`.

Latest snapshot:
- Revenue: {money(metrics['current']['actual_revenue'])}
- Gross margin: {money(metrics['current']['gross_margin'])}
- Cost variance vs standard: {money(metrics['current']['cost_variance'])}
- Yield: {pct(metrics['current']['yield_pct'])}
- Inventory days: {metrics['current']['inventory_days']:.1f}
""",
    )


def main() -> None:
    ensure_dirs()
    dims = generate_dimensions()
    facts = generate_facts(dims)
    exports = enrich_exports(dims, facts)
    all_tables = {**dims, **facts}

    for name, df in all_tables.items():
        write_csv(f"data/raw/{name}.csv", df)
        write_csv(f"data/prepared/{name}.csv", df)
    for name, df in exports.items():
        write_csv(f"output/exports/{name}.csv", df)

    profile = profile_tables(all_tables)
    write_csv("data/profile/table_profile.csv", profile)
    write_text(
        "data/profile/profile_report.md",
        "# Profile Report\n\n| Table | Rows | Columns | Duplicate Rows | Missing Cells |\n|---|---:|---:|---:|---:|\n"
        + "\n".join(f"| {r.table} | {r.rows:,} | {r.columns:,} | {r.duplicate_rows:,} | {r.missing_cells:,} |" for r in profile.itertuples()),
    )

    validation = validate_data(dims, facts)
    metrics = metric_snapshot(facts)
    write_json("data/validated/validation_summary.json", validation)
    write_json("data/validated/output_validation.json", validation)
    write_json(
        "data/source_summary.json",
        {
            "source_type": "synthetic_demo",
            "seed": SEED,
            "generated_on": TODAY,
            "tables": {name: {"rows": len(df), "columns": list(df.columns)} for name, df in all_tables.items()},
        },
    )
    write_text(
        "data/data_quality_report.md",
        "# Data Quality Report\n\nStatus: "
        + validation["status"]
        + "\n\n"
        + "\n".join([f"- {c['check']}: {c['status']} ({c['value']})" for c in validation["checks"]]),
    )
    write_text(
        "data/synthetic/generation_notes.md",
        f"""# Synthetic Generation Notes

The dataset is synthetic and generated with fixed seed `{SEED}` for portfolio repeatability.

It models 5 manufacturing plants, 12 production lines, 24 products, monthly data from January 2024 through May 2026, and explicit standard cost, actual cost, yield, scrap, utilization, and inventory economics.
""",
    )

    write_model_docs(all_tables, metrics)
    write_config(metrics)
    write_native_layout()
    render_screenshots(dims, facts, metrics)
    build_html(dims, facts, exports, metrics)
    write_reconciliation(metrics, validation, facts)
    write_environment_docs()
    write_docs(metrics, validation)
    write_powerbi_scripts()
    write_readme(metrics)

    print(
        json.dumps(
            {
                "status": validation["status"],
                "project": str(ROOT),
                "latest_complete_month": LATEST_MONTH,
                "prepared_tables": {name: len(df) for name, df in all_tables.items()},
                "native_layout": json.loads(p("build/native_report_layout_project16_summary.json").read_text(encoding="utf-8")),
                "latest_metrics": metrics["current"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
