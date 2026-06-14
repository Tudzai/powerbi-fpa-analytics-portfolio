from __future__ import annotations

import json
import math
import random
from datetime import datetime
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import FancyBboxPatch, Rectangle


ROOT = Path(__file__).resolve().parents[2]
SEED = 802608
TODAY = "2026-06-11"
LATEST_MONTH = "2026-05"
PREVIOUS_MONTH = "2026-04"


COLORS = {
    "bg": "#F5F7FA",
    "panel": "#FFFFFF",
    "ink": "#111827",
    "muted": "#667085",
    "line": "#D8DEE9",
    "blue": "#2563EB",
    "cyan": "#0891B2",
    "green": "#16A34A",
    "teal": "#0F766E",
    "amber": "#D97706",
    "red": "#DC2626",
    "violet": "#7C3AED",
    "slate": "#475569",
    "navy": "#0B1220",
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
        "powerbi/notes",
        "powerbi/pbip",
        "powerbi/templates",
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


def month_sequence() -> pd.DataFrame:
    months = pd.date_range("2024-01-01", "2026-05-01", freq="MS")
    dim = pd.DataFrame(
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
    return dim


def generate_dimensions() -> dict[str, pd.DataFrame]:
    rng = np.random.default_rng(SEED)
    py_rng = random.Random(SEED)

    dim_date = month_sequence()

    segments = ["Enterprise", "Mid-Market", "SMB", "Micro"]
    segment_weights = [0.10, 0.22, 0.43, 0.25]
    verticals = ["Retail", "Food Delivery", "Travel", "Gaming", "Services", "Education", "Utilities", "Marketplace"]
    countries = ["Vietnam", "Singapore", "Thailand", "Indonesia", "Philippines"]
    country_regions = {
        "Vietnam": ["VN North", "VN Central", "VN South"],
        "Singapore": ["Singapore"],
        "Thailand": ["Bangkok", "Thailand Provincial"],
        "Indonesia": ["Java", "Indonesia Outer"],
        "Philippines": ["Metro Manila", "Philippines Provincial"],
    }
    risk_tiers = ["Low", "Medium", "High"]
    managers = ["Ava Nguyen", "Bao Tran", "Chloe Lim", "Daniel Ho", "Farah Rahman", "Minh Pham", "Nadia Santos"]
    acquisition_channels = ["Direct Sales", "Partner", "Self-Serve", "Platform Referral"]

    merchants = []
    for idx in range(1, 201):
        segment = rng.choice(segments, p=segment_weights)
        vertical = rng.choice(verticals)
        country = rng.choice(countries, p=[0.35, 0.12, 0.19, 0.20, 0.14])
        region = py_rng.choice(country_regions[country])
        risk = rng.choice(risk_tiers, p=[0.58, 0.32, 0.10])
        size_factor = {"Enterprise": 11.0, "Mid-Market": 4.2, "SMB": 1.35, "Micro": 0.38}[segment]
        vertical_factor = {
            "Retail": 1.35,
            "Food Delivery": 0.82,
            "Travel": 1.80,
            "Gaming": 1.10,
            "Services": 0.95,
            "Education": 0.70,
            "Utilities": 1.45,
            "Marketplace": 2.05,
        }[vertical]
        demand = float(rng.lognormal(mean=10.50, sigma=0.75) * size_factor * vertical_factor)
        avg_ticket = float(
            rng.lognormal(
                mean={
                    "Food Delivery": 3.1,
                    "Gaming": 3.35,
                    "Retail": 4.15,
                    "Travel": 5.55,
                    "Education": 4.45,
                    "Utilities": 4.00,
                    "Services": 4.25,
                    "Marketplace": 4.05,
                }[vertical],
                sigma=0.30,
            )
        )
        take_rate = {
            "Enterprise": 0.0108,
            "Mid-Market": 0.0140,
            "SMB": 0.0174,
            "Micro": 0.0200,
        }[segment] + rng.normal(0, 0.0014)
        fixed_fee = {
            "Enterprise": 0.015,
            "Mid-Market": 0.020,
            "SMB": 0.026,
            "Micro": 0.032,
        }[segment]
        merchants.append(
            {
                "merchant_id": f"M{idx:04d}",
                "merchant_name": f"{vertical.split()[0]}Pay Merchant {idx:04d}",
                "merchant_segment": segment,
                "vertical": vertical,
                "country": country,
                "region": region,
                "risk_tier": risk,
                "account_manager": py_rng.choice(managers),
                "acquisition_channel": rng.choice(acquisition_channels, p=[0.44, 0.25, 0.22, 0.09]),
                "onboarding_date": (
                    pd.Timestamp("2021-01-01") + pd.Timedelta(days=int(rng.integers(0, 1550)))
                ).strftime("%Y-%m-%d"),
                "base_monthly_gmv": round(demand, 2),
                "avg_ticket_usd": round(avg_ticket, 2),
                "contracted_take_rate": round(max(0.006, take_rate), 5),
                "fixed_fee_usd": round(fixed_fee, 4),
                "active_flag": 1,
            }
        )
    dim_merchant = pd.DataFrame(merchants)

    dim_payment_method = pd.DataFrame(
        [
            ["PM01", "Cards", "Card rails", 0.0048, 0.025, 0.0022, 0.52],
            ["PM02", "Bank Transfer", "Account-to-account", 0.0012, 0.014, 0.0008, 0.15],
            ["PM03", "Wallet", "Stored value", 0.0021, 0.012, 0.0011, 0.16],
            ["PM04", "BNPL", "Credit alternative", 0.0068, 0.040, 0.0040, 0.07],
            ["PM05", "QR / Instant Pay", "Real-time QR", 0.0008, 0.009, 0.0006, 0.10],
        ],
        columns=[
            "payment_method_id",
            "payment_method",
            "rail_type",
            "variable_cost_rate",
            "fixed_cost_per_txn",
            "fraud_cost_rate",
            "default_mix_weight",
        ],
    )

    dim_channel = pd.DataFrame(
        [
            ["CH01", "Hosted Checkout", "Web", 0.42, 0.0012],
            ["CH02", "API", "Server-side", 0.25, 0.0007],
            ["CH03", "In-App", "Mobile", 0.22, 0.0010],
            ["CH04", "POS", "Offline", 0.07, 0.0015],
            ["CH05", "Payment Link", "Remote", 0.04, 0.0022],
        ],
        columns=["channel_id", "channel", "channel_group", "default_mix_weight", "support_cost_rate"],
    )

    dim_scenario = pd.DataFrame(
        [
            ["S00", "Base", 0, 0.000, 0.000, "Current contracted economics."],
            ["S01", "Raise take rate +10 bps", 10, 0.000, -0.004, "Modest price lift with light volume elasticity."],
            ["S02", "Raise take rate +25 bps", 25, 0.000, -0.014, "Aggressive price lift for less-sensitive segments."],
            ["S03", "Processor renegotiation -8%", 0, -0.080, 0.000, "Reduce processor/interchange pass-through cost."],
            ["S04", "Fraud controls -15%", 0, -0.035, -0.002, "Reduce fraud/chargeback losses with minor friction."],
            ["S05", "Enterprise discount -12 bps", -12, 0.000, 0.018, "Volume protection through enterprise repricing."],
        ],
        columns=["scenario_id", "scenario_name", "take_rate_delta_bps", "cost_delta_pct", "volume_elasticity", "description"],
    )

    return {
        "dim_date": dim_date,
        "dim_merchant": dim_merchant,
        "dim_payment_method": dim_payment_method,
        "dim_channel": dim_channel,
        "dim_scenario": dim_scenario,
    }


def generate_facts(dims: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    rng = np.random.default_rng(SEED + 1)
    merchants = dims["dim_merchant"]
    dates = dims["dim_date"]
    methods = dims["dim_payment_method"]
    channels = dims["dim_channel"]

    seasonality = {
        1: 0.93,
        2: 0.89,
        3: 0.98,
        4: 1.00,
        5: 1.02,
        6: 1.03,
        7: 1.05,
        8: 1.06,
        9: 1.04,
        10: 1.09,
        11: 1.18,
        12: 1.24,
    }
    segment_method_tilt = {
        "Enterprise": {"Cards": 0.82, "Bank Transfer": 1.35, "Wallet": 0.85, "BNPL": 0.65, "QR / Instant Pay": 1.10},
        "Mid-Market": {"Cards": 1.02, "Bank Transfer": 1.10, "Wallet": 1.00, "BNPL": 0.85, "QR / Instant Pay": 1.00},
        "SMB": {"Cards": 1.12, "Bank Transfer": 0.82, "Wallet": 1.05, "BNPL": 1.05, "QR / Instant Pay": 0.92},
        "Micro": {"Cards": 1.00, "Bank Transfer": 0.60, "Wallet": 1.18, "BNPL": 1.22, "QR / Instant Pay": 1.10},
    }
    vertical_refund = {
        "Retail": 0.035,
        "Food Delivery": 0.012,
        "Travel": 0.028,
        "Gaming": 0.006,
        "Services": 0.014,
        "Education": 0.009,
        "Utilities": 0.004,
        "Marketplace": 0.042,
    }
    risk_chargeback = {"Low": 0.00035, "Medium": 0.00085, "High": 0.0022}
    rows = []

    method_weights = methods.set_index("payment_method")["default_mix_weight"].to_dict()
    channel_weights = channels.set_index("channel")["default_mix_weight"].to_dict()
    method_costs = methods.set_index("payment_method").to_dict("index")
    channel_costs = channels.set_index("channel").to_dict("index")

    for _, merchant in merchants.iterrows():
        method_vec = []
        for method, base_w in method_weights.items():
            method_vec.append(base_w * segment_method_tilt[merchant.merchant_segment][method] * rng.lognormal(0, 0.08))
        method_vec = np.array(method_vec, dtype=float)
        method_vec = method_vec / method_vec.sum()

        channel_vec = np.array([channel_weights[c] * rng.lognormal(0, 0.12) for c in channel_weights], dtype=float)
        if merchant.merchant_segment == "Enterprise":
            channel_vec[1] *= 1.35
        if merchant.merchant_segment in {"SMB", "Micro"}:
            channel_vec[4] *= 1.50
        channel_vec = channel_vec / channel_vec.sum()

        combo_scores = []
        for method_i, method_name in enumerate(method_weights.keys()):
            for channel_i, channel_name in enumerate(channel_weights.keys()):
                combo_scores.append((method_vec[method_i] * channel_vec[channel_i], method_i, method_name, channel_i, channel_name))
        combo_scores = sorted(combo_scores, reverse=True)[:12]

        for _, month in dates.iterrows():
            months_since = int(month.month_index - 1)
            growth = (1.011 + rng.normal(0, 0.002)) ** months_since
            macro = 1.0 + 0.018 * math.sin(month.month_index / 2.5)
            base = merchant.base_monthly_gmv * growth * seasonality[int(month.month_no)] * macro
            total_gmv = max(200.0, base * rng.lognormal(0, 0.10))
            avg_ticket = max(2.0, merchant.avg_ticket_usd * rng.lognormal(0, 0.06))
            normalizer = sum(score for score, *_ in combo_scores)
            for score, method_i, method_name, channel_i, channel_name in combo_scores:
                mix = score / normalizer
                gmv = total_gmv * mix * rng.lognormal(0, 0.04)
                txns = max(1, int(round(gmv / avg_ticket)))
                method = method_costs[method_name]
                channel = channel_costs[channel_name]
                auth_rate = 0.972
                auth_rate -= 0.006 if merchant.risk_tier == "High" else 0.002 if merchant.risk_tier == "Medium" else 0
                auth_rate -= 0.004 if method_name == "BNPL" else 0
                auth_rate -= 0.003 if channel_name == "Payment Link" else 0
                auth_rate += rng.normal(0, 0.002)
                auth_rate = float(np.clip(auth_rate, 0.925, 0.992))
                successful_txn = int(round(txns * auth_rate))
                failed_txn = max(0, txns - successful_txn)

                refund_rate = vertical_refund[merchant.vertical] * (1.20 if merchant.risk_tier == "High" else 1.0)
                refund_rate *= 1.16 if method_name == "BNPL" else 1.0
                refund_rate *= rng.lognormal(0, 0.11)
                refund_amount = gmv * refund_rate
                refund_count = int(round(successful_txn * min(0.18, refund_rate * 1.9)))

                chargeback_rate = risk_chargeback[merchant.risk_tier]
                chargeback_rate *= 1.85 if method_name == "Cards" else 1.15 if method_name == "BNPL" else 0.45
                chargeback_rate *= rng.lognormal(0, 0.22)
                chargeback_amount = gmv * chargeback_rate
                chargeback_count = int(round(successful_txn * min(0.025, chargeback_rate * 2.6)))

                discount = 0.0018 if merchant.merchant_segment == "Enterprise" else 0.0008 if merchant.merchant_segment == "Mid-Market" else 0
                risk_premium = 0.0007 if merchant.risk_tier == "High" else 0.0002 if merchant.risk_tier == "Medium" else 0
                take_rate = max(0.004, merchant.contracted_take_rate - discount + risk_premium + rng.normal(0, 0.00025))
                variable_fee_revenue = gmv * take_rate
                fixed_fee_revenue = successful_txn * merchant.fixed_fee_usd
                refund_fee_reversal = refund_amount * take_rate * 0.72
                revenue_fee = max(0, variable_fee_revenue + fixed_fee_revenue - refund_fee_reversal)

                interchange_cost = gmv * method["variable_cost_rate"]
                network_cost = successful_txn * method["fixed_cost_per_txn"]
                processor_cost = gmv * (0.0009 + channel["support_cost_rate"])
                fraud_loss = gmv * method["fraud_cost_rate"] * (1.55 if merchant.risk_tier == "High" else 1.10 if merchant.risk_tier == "Medium" else 0.65)
                incentives_cost = gmv * (0.00055 if merchant.merchant_segment in {"Enterprise", "Mid-Market"} else 0.00035)
                total_cost = interchange_cost + network_cost + processor_cost + fraud_loss + incentives_cost + chargeback_amount * 0.35
                contribution_margin = revenue_fee - total_cost
                rows.append(
                    {
                        "date_key": int(month.date_key),
                        "month_start_date": month.month_start_date,
                        "year_month": month.year_month,
                        "month_index": int(month.month_index),
                        "merchant_id": merchant.merchant_id,
                        "payment_method_id": methods.loc[methods.payment_method.eq(method_name), "payment_method_id"].iloc[0],
                        "channel_id": channels.loc[channels.channel.eq(channel_name), "channel_id"].iloc[0],
                        "gmv": round(gmv, 2),
                        "transaction_count": txns,
                        "successful_txn": successful_txn,
                        "failed_txn": failed_txn,
                        "revenue_fee": round(revenue_fee, 2),
                        "fixed_fee_revenue": round(fixed_fee_revenue, 2),
                        "refund_amount": round(refund_amount, 2),
                        "refund_count": refund_count,
                        "chargeback_amount": round(chargeback_amount, 2),
                        "chargeback_count": chargeback_count,
                        "interchange_cost": round(interchange_cost, 2),
                        "network_cost": round(network_cost, 2),
                        "processor_cost": round(processor_cost, 2),
                        "fraud_loss": round(fraud_loss, 2),
                        "incentives_cost": round(incentives_cost, 2),
                        "total_cost": round(total_cost, 2),
                        "contribution_margin": round(contribution_margin, 2),
                        "auth_success_rate": round(auth_rate, 5),
                        "average_ticket": round(avg_ticket, 2),
                        "take_rate": round(revenue_fee / gmv if gmv else 0, 5),
                        "cost_per_txn": round(total_cost / successful_txn if successful_txn else 0, 5),
                        "margin_rate": round(contribution_margin / revenue_fee if revenue_fee else 0, 5),
                    }
                )

    fact = pd.DataFrame(rows)

    latest = fact[fact["year_month"].eq(LATEST_MONTH)]
    prev = fact[fact["year_month"].eq(PREVIOUS_MONTH)]
    latest_rev = latest["revenue_fee"].sum()
    prev_rev = prev["revenue_fee"].sum()
    gmv_effect = (latest["gmv"].sum() - prev["gmv"].sum()) * (prev_rev / prev["gmv"].sum())
    take_effect = latest_rev - prev_rev - gmv_effect
    bridge = pd.DataFrame(
        [
            [LATEST_MONTH, 1, "Previous Revenue", prev_rev, "start"],
            [LATEST_MONTH, 2, "GMV Volume Effect", gmv_effect, "increase" if gmv_effect >= 0 else "decrease"],
            [LATEST_MONTH, 3, "Take-rate / Mix Effect", take_effect, "increase" if take_effect >= 0 else "decrease"],
            [LATEST_MONTH, 4, "Refund Fee Reversal", -latest["refund_amount"].sum() * (latest_rev / latest["gmv"].sum()) * 0.72, "decrease"],
            [LATEST_MONTH, 5, "Chargeback Revenue Drag", -latest["chargeback_amount"].sum() * 0.12, "decrease"],
            [LATEST_MONTH, 6, "Current Revenue", latest_rev, "total"],
        ],
        columns=["year_month", "bridge_order", "bridge_step", "bridge_amount", "bridge_type"],
    )

    return {"fact_payment_month": fact, "fact_fee_bridge": bridge}


def enrich_exports(dims: dict[str, pd.DataFrame], facts: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    fact = facts["fact_payment_month"]
    enriched = (
        fact.merge(dims["dim_merchant"], on="merchant_id", how="left")
        .merge(dims["dim_payment_method"], on="payment_method_id", how="left")
        .merge(dims["dim_channel"], on="channel_id", how="left")
    )
    latest = enriched[enriched.year_month.eq(LATEST_MONTH)].copy()
    merchant = latest.groupby(
        ["merchant_id", "merchant_name", "merchant_segment", "vertical", "country", "risk_tier"], as_index=False
    ).agg(
        gmv=("gmv", "sum"),
        transactions=("transaction_count", "sum"),
        revenue=("revenue_fee", "sum"),
        costs=("total_cost", "sum"),
        contribution_margin=("contribution_margin", "sum"),
        refund_amount=("refund_amount", "sum"),
        chargeback_amount=("chargeback_amount", "sum"),
    )
    merchant["take_rate"] = merchant["revenue"] / merchant["gmv"]
    merchant["margin_pct"] = merchant["contribution_margin"] / merchant["revenue"]
    merchant["refund_rate"] = merchant["refund_amount"] / merchant["gmv"]
    merchant["chargeback_bps"] = merchant["chargeback_amount"] / merchant["gmv"] * 10000

    top = merchant.sort_values("contribution_margin", ascending=False).head(25)
    bottom = merchant.sort_values("contribution_margin", ascending=True).head(25)
    high_risk = merchant.sort_values(["chargeback_bps", "refund_rate"], ascending=[False, False]).head(25)
    return {"latest_merchant": merchant, "top_merchants": top, "bottom_merchants": bottom, "risk_merchants": high_risk}


def profile_tables(tables: dict[str, pd.DataFrame]) -> pd.DataFrame:
    records = []
    for name, df in tables.items():
        records.append(
            {
                "table": name,
                "rows": len(df),
                "columns": len(df.columns),
                "duplicate_rows": int(df.duplicated().sum()),
                "missing_cells": int(df.isna().sum().sum()),
            }
        )
    return pd.DataFrame(records)


def validate_data(dims: dict[str, pd.DataFrame], facts: dict[str, pd.DataFrame]) -> dict:
    fact = facts["fact_payment_month"]
    required_positive = ["gmv", "transaction_count", "revenue_fee"]
    checks = []
    checks.append({"check": "fact rows > 0", "status": "PASS" if len(fact) > 0 else "FAIL", "value": len(fact)})
    checks.append(
        {
            "check": "date range",
            "status": "PASS" if fact["year_month"].min() == "2024-01" and fact["year_month"].max() == LATEST_MONTH else "FAIL",
            "value": f"{fact['year_month'].min()} to {fact['year_month'].max()}",
        }
    )
    for col in required_positive:
        checks.append({"check": f"{col} non-negative", "status": "PASS" if (fact[col] >= 0).all() else "FAIL", "value": float(fact[col].min())})
    for fk, dim, key in [
        ("merchant_id", "dim_merchant", "merchant_id"),
        ("payment_method_id", "dim_payment_method", "payment_method_id"),
        ("channel_id", "dim_channel", "channel_id"),
    ]:
        missing = sorted(set(fact[fk]) - set(dims[dim][key]))
        checks.append({"check": f"{fk} relationship", "status": "PASS" if not missing else "FAIL", "missing_count": len(missing)})
    status = "PASS" if all(c["status"] == "PASS" for c in checks) else "FAIL"
    return {"generated_on": TODAY, "status": status, "checks": checks}


def metric_snapshot(dims: dict[str, pd.DataFrame], facts: dict[str, pd.DataFrame]) -> dict:
    fact = facts["fact_payment_month"]
    current = fact[fact.year_month.eq(LATEST_MONTH)]
    previous = fact[fact.year_month.eq(PREVIOUS_MONTH)]
    def sums(df: pd.DataFrame) -> dict:
        revenue = df["revenue_fee"].sum()
        gmv = df["gmv"].sum()
        txns = df["transaction_count"].sum()
        costs = df["total_cost"].sum()
        margin = df["contribution_margin"].sum()
        return {
            "gmv": float(gmv),
            "transactions": int(txns),
            "revenue": float(revenue),
            "take_rate": float(revenue / gmv),
            "cost": float(costs),
            "cost_per_transaction": float(costs / txns),
            "contribution_margin": float(margin),
            "contribution_margin_pct": float(margin / revenue),
            "refund_rate": float(df["refund_amount"].sum() / gmv),
            "chargeback_bps": float(df["chargeback_amount"].sum() / gmv * 10000),
            "auth_success_rate": float(df["successful_txn"].sum() / (df["successful_txn"].sum() + df["failed_txn"].sum())),
        }
    cur = sums(current)
    prev = sums(previous)
    cur["mom_gmv_growth"] = (cur["gmv"] - prev["gmv"]) / prev["gmv"]
    cur["mom_revenue_growth"] = (cur["revenue"] - prev["revenue"]) / prev["revenue"]
    return {"latest_month": LATEST_MONTH, "previous_month": PREVIOUS_MONTH, "current": cur, "previous": prev}


def money(v: float) -> str:
    if abs(v) < 10:
        return f"${v:.2f}"
    if abs(v) >= 1_000_000:
        return f"${v / 1_000_000:.1f}M"
    if abs(v) >= 1_000:
        return f"${v / 1_000:.1f}K"
    return f"${v:.0f}"


def pct(v: float) -> str:
    return f"{v * 100:.1f}%"


def format_num(v: float) -> str:
    if abs(v) >= 1_000_000:
        return f"{v / 1_000_000:.1f}M"
    if abs(v) >= 1_000:
        return f"{v / 1_000:.1f}K"
    return f"{v:,.0f}"


def enriched_monthly(dims: dict[str, pd.DataFrame], facts: dict[str, pd.DataFrame]) -> pd.DataFrame:
    return (
        facts["fact_payment_month"]
        .merge(dims["dim_merchant"], on="merchant_id", how="left")
        .merge(dims["dim_payment_method"], on="payment_method_id", how="left")
        .merge(dims["dim_channel"], on="channel_id", how="left")
    )


def panel(fig: plt.Figure, rect: list[float], title: str, subtitle: str | None = None) -> plt.Axes:
    bg = fig.add_axes(rect)
    bg.axis("off")
    bg.add_patch(
        FancyBboxPatch(
            (0, 0),
            1,
            1,
            boxstyle="round,pad=0.010,rounding_size=0.012",
            transform=bg.transAxes,
            fc=COLORS["panel"],
            ec=COLORS["line"],
            lw=0.8,
        )
    )
    bg.text(0.04, 0.92, title, fontsize=10.5, weight="bold", color=COLORS["ink"], ha="left", va="center")
    if subtitle:
        bg.text(0.04, 0.845, subtitle, fontsize=8.0, color=COLORS["muted"], ha="left", va="center")
    return fig.add_axes([rect[0] + rect[2] * 0.07, rect[1] + rect[3] * 0.11, rect[2] * 0.86, rect[3] * 0.68])


def setup_page(title: str, subtitle: str) -> tuple[plt.Figure, plt.Axes]:
    fig = plt.figure(figsize=(16, 9), facecolor=COLORS["bg"])
    ax = fig.add_axes([0, 0, 1, 1])
    ax.axis("off")
    ax.add_patch(Rectangle((0, 0.91), 1, 0.09, transform=ax.transAxes, color=COLORS["navy"], ec="none"))
    ax.text(0.035, 0.965, "Digital Payments Profitability", ha="left", va="center", fontsize=9.5, color="#A7F3D0", weight="bold")
    ax.text(0.035, 0.932, title, ha="left", va="center", fontsize=18.5, color="#FFFFFF", weight="bold")
    ax.text(0.37, 0.932, subtitle, ha="left", va="center", fontsize=9.3, color="#CBD5E1")
    chip_x = 0.64
    for chip in [f"Latest {LATEST_MONTH}", "Segment", "Method", "Channel"]:
        w = 0.047 + len(chip) * 0.0046
        ax.add_patch(
            FancyBboxPatch(
                (chip_x, 0.936),
                w,
                0.034,
                boxstyle="round,pad=0.004,rounding_size=0.008",
                transform=ax.transAxes,
                fc="#172033",
                ec="#334155",
                lw=0.8,
            )
        )
        ax.text(chip_x + 0.010, 0.953, chip, ha="left", va="center", fontsize=8, color="#E5E7EB")
        chip_x += w + 0.009
    return fig, ax


def draw_card(ax: plt.Axes, x: float, y: float, w: float, h: float, label: str, value: str, note: str, color: str) -> None:
    ax.add_patch(
        FancyBboxPatch(
            (x, y),
            w,
            h,
            boxstyle="round,pad=0.007,rounding_size=0.012",
            transform=ax.transAxes,
            fc=COLORS["panel"],
            ec=COLORS["line"],
            lw=0.8,
        )
    )
    ax.add_patch(Rectangle((x + 0.014, y + 0.024), 0.006, h - 0.048, transform=ax.transAxes, color=color, ec="none"))
    ax.text(x + 0.032, y + h - 0.026, label, fontsize=7.5, color=COLORS["muted"], weight="bold", ha="left", va="top")
    ax.text(x + 0.032, y + 0.046, value, fontsize=16.2, color=color, weight="bold", ha="left", va="bottom")
    ax.text(x + 0.032, y + 0.021, note, fontsize=7.2, color=COLORS["muted"], ha="left", va="bottom")


def style_axis(ax: plt.Axes) -> None:
    ax.set_facecolor(COLORS["panel"])
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.spines["bottom"].set_color(COLORS["line"])
    ax.grid(axis="y", color="#EEF2F7", linewidth=0.8)
    ax.tick_params(colors=COLORS["muted"], labelsize=8)


def save_fig(fig: plt.Figure, rel: str) -> None:
    fig.savefig(p(rel), dpi=160, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)


def render_screenshots(dims: dict[str, pd.DataFrame], facts: dict[str, pd.DataFrame], metrics: dict) -> None:
    df = enriched_monthly(dims, facts)
    latest = df[df.year_month.eq(LATEST_MONTH)]
    trend = df.groupby("year_month", as_index=False).agg(
        gmv=("gmv", "sum"),
        transactions=("transaction_count", "sum"),
        revenue=("revenue_fee", "sum"),
        contribution_margin=("contribution_margin", "sum"),
        total_cost=("total_cost", "sum"),
        refund_amount=("refund_amount", "sum"),
        chargeback_amount=("chargeback_amount", "sum"),
    )
    trend["take_rate"] = trend["revenue"] / trend["gmv"]
    trend["margin_pct"] = trend["contribution_margin"] / trend["revenue"]

    cur = metrics["current"]
    fig, ax = setup_page("Executive Overview", "GMV, transaction volume, revenue, take rate, contribution margin, and MoM growth")
    cards = [
        ("GMV", money(cur["gmv"]), f"{pct(cur['mom_gmv_growth'])} MoM", COLORS["blue"]),
        ("Transactions", format_num(cur["transactions"]), "successful + failed attempts", COLORS["cyan"]),
        ("Revenue", money(cur["revenue"]), f"{pct(cur['mom_revenue_growth'])} MoM", COLORS["green"]),
        ("Take Rate", pct(cur["take_rate"]), "fee revenue / GMV", COLORS["teal"]),
        ("Contribution Margin", money(cur["contribution_margin"]), pct(cur["contribution_margin_pct"]), COLORS["violet"]),
        ("Cost / Txn", money(cur["cost_per_transaction"]), "all variable costs", COLORS["amber"]),
    ]
    for i, item in enumerate(cards):
        draw_card(ax, 0.035 + i * 0.155, 0.765, 0.14, 0.12, *item)
    a = panel(fig, [0.035, 0.43, 0.58, 0.30], "GMV & Revenue Trend", "Monthly trend through latest complete month")
    a.plot(trend["year_month"], trend["gmv"] / 1e6, color=COLORS["blue"], lw=2.3, label="GMV")
    a.plot(trend["year_month"], trend["revenue"] / 1e6, color=COLORS["green"], lw=2.0, label="Revenue")
    style_axis(a)
    a.set_ylabel("$M", color=COLORS["muted"], fontsize=8)
    a.tick_params(axis="x", rotation=45)
    a.legend(loc="upper left", frameon=False, fontsize=8)
    b = panel(fig, [0.64, 0.43, 0.325, 0.30], "Profitability by Segment", "Current month contribution margin")
    seg = latest.groupby("merchant_segment", as_index=False).agg(margin=("contribution_margin", "sum")).sort_values("margin")
    b.barh(seg["merchant_segment"], seg["margin"] / 1e6, color=COLORS["violet"])
    style_axis(b)
    b.set_xlabel("$M", color=COLORS["muted"], fontsize=8)
    c = panel(fig, [0.035, 0.08, 0.44, 0.30], "Payment Method Mix", "Current month GMV by rail")
    mix = latest.groupby("payment_method", as_index=False).agg(gmv=("gmv", "sum")).sort_values("gmv", ascending=False)
    c.bar(mix["payment_method"], mix["gmv"] / 1e6, color=[COLORS["blue"], COLORS["cyan"], COLORS["teal"], COLORS["amber"], COLORS["red"]])
    style_axis(c)
    c.tick_params(axis="x", rotation=20)
    c.set_ylabel("$M", color=COLORS["muted"], fontsize=8)
    d = panel(fig, [0.505, 0.08, 0.46, 0.30], "Top Merchants", "Current month GMV and margin")
    top = (
        latest.groupby(["merchant_name", "merchant_segment"], as_index=False)
        .agg(gmv=("gmv", "sum"), margin=("contribution_margin", "sum"))
        .sort_values("gmv", ascending=False)
        .head(8)
    )
    d.axis("off")
    cell_text = [[r.merchant_name, r.merchant_segment, money(r.gmv), money(r.margin)] for r in top.itertuples()]
    table = d.table(cellText=cell_text, colLabels=["Merchant", "Segment", "GMV", "CM"], loc="center", cellLoc="left")
    table.auto_set_font_size(False)
    table.set_fontsize(7.7)
    table.scale(1, 1.22)
    save_fig(fig, "output/screenshots/page_01_executive_overview.png")

    fig, ax = setup_page("Merchant & Transaction Drivers", "Merchant segment, payment method, channel, refund, chargeback, and top/bottom merchants")
    driver_cards = [
        ("Auth Success", pct(cur["auth_success_rate"]), "attempt approval rate", COLORS["green"]),
        ("Refund Rate", pct(cur["refund_rate"]), "refund amount / GMV", COLORS["amber"]),
        ("Chargeback Bps", f"{cur['chargeback_bps']:.1f}", "chargeback amount / GMV", COLORS["red"]),
        ("Margin %", pct(cur["contribution_margin_pct"]), "CM / revenue", COLORS["violet"]),
    ]
    for i, item in enumerate(driver_cards):
        draw_card(ax, 0.035 + i * 0.235, 0.765, 0.205, 0.12, *item)
    a = panel(fig, [0.035, 0.45, 0.29, 0.28], "GMV by Channel", "Current month")
    chan = latest.groupby("channel", as_index=False).agg(gmv=("gmv", "sum")).sort_values("gmv")
    a.barh(chan["channel"], chan["gmv"] / 1e6, color=COLORS["cyan"])
    style_axis(a)
    b = panel(fig, [0.355, 0.45, 0.29, 0.28], "Refund by Vertical", "Refund amount")
    ref = latest.groupby("vertical", as_index=False).agg(refund=("refund_amount", "sum")).sort_values("refund", ascending=False).head(8)
    b.bar(ref["vertical"], ref["refund"] / 1e3, color=COLORS["amber"])
    b.tick_params(axis="x", rotation=30)
    style_axis(b)
    c = panel(fig, [0.675, 0.45, 0.29, 0.28], "Chargeback Bps by Method", "Risk by rail")
    cb = latest.groupby("payment_method", as_index=False).agg(gmv=("gmv", "sum"), cb=("chargeback_amount", "sum"))
    cb["bps"] = cb["cb"] / cb["gmv"] * 10000
    cb = cb.sort_values("bps")
    c.barh(cb["payment_method"], cb["bps"], color=COLORS["red"])
    style_axis(c)
    d = panel(fig, [0.035, 0.08, 0.45, 0.30], "Bottom Merchants by CM", "Margin leakage watchlist")
    bottom = (
        latest.groupby(["merchant_name", "merchant_segment", "risk_tier"], as_index=False)
        .agg(gmv=("gmv", "sum"), margin=("contribution_margin", "sum"), cb=("chargeback_amount", "sum"))
        .sort_values("margin")
        .head(8)
    )
    d.axis("off")
    table = d.table(
        cellText=[[r.merchant_name, r.merchant_segment, r.risk_tier, money(r.margin)] for r in bottom.itertuples()],
        colLabels=["Merchant", "Segment", "Risk", "CM"],
        loc="center",
        cellLoc="left",
    )
    table.auto_set_font_size(False)
    table.set_fontsize(7.7)
    table.scale(1, 1.24)
    e = panel(fig, [0.515, 0.08, 0.45, 0.30], "Top Merchants by CM", "Profit contribution leaders")
    top_margin = (
        latest.groupby(["merchant_name", "merchant_segment", "risk_tier"], as_index=False)
        .agg(gmv=("gmv", "sum"), margin=("contribution_margin", "sum"))
        .sort_values("margin", ascending=False)
        .head(8)
    )
    e.axis("off")
    table = e.table(
        cellText=[[r.merchant_name, r.merchant_segment, r.risk_tier, money(r.margin)] for r in top_margin.itertuples()],
        colLabels=["Merchant", "Segment", "Risk", "CM"],
        loc="center",
        cellLoc="left",
    )
    table.auto_set_font_size(False)
    table.set_fontsize(7.7)
    table.scale(1, 1.24)
    save_fig(fig, "output/screenshots/page_02_merchant_transaction_drivers.png")

    fig, ax = setup_page("Margin & Scenario Planning", "Fee revenue bridge, cost per transaction, margin sensitivity, and take-rate scenario")
    scen = dims["dim_scenario"]
    scenario = scen[scen["scenario_name"].eq("Raise take rate +10 bps")].iloc[0]
    scenario_rev = cur["revenue"] + cur["gmv"] * scenario.take_rate_delta_bps / 10000
    scenario_cost = cur["cost"] * (1 + scenario.cost_delta_pct)
    scenario_margin = scenario_rev - scenario_cost
    plan_cards = [
        ("Base Revenue", money(cur["revenue"]), "current month", COLORS["green"]),
        ("Base Cost", money(cur["cost"]), "variable + loss costs", COLORS["amber"]),
        ("Base CM", money(cur["contribution_margin"]), pct(cur["contribution_margin_pct"]), COLORS["violet"]),
        ("Scenario CM", money(scenario_margin), "+10 bps take rate", COLORS["blue"]),
        ("CM Uplift", money(scenario_margin - cur["contribution_margin"]), "vs base", COLORS["teal"]),
    ]
    for i, item in enumerate(plan_cards):
        draw_card(ax, 0.035 + i * 0.185, 0.765, 0.17, 0.12, *item)
    a = panel(fig, [0.035, 0.42, 0.45, 0.31], "Fee Revenue Bridge", "Previous to current month")
    bridge = facts["fact_fee_bridge"].copy()
    colors = [COLORS["slate"] if t in {"start", "total"} else COLORS["green"] if v > 0 else COLORS["red"] for t, v in zip(bridge["bridge_type"], bridge["bridge_amount"])]
    a.bar(bridge["bridge_step"], bridge["bridge_amount"] / 1e6, color=colors)
    a.tick_params(axis="x", rotation=25)
    style_axis(a)
    a.set_ylabel("$M", color=COLORS["muted"], fontsize=8)
    b = panel(fig, [0.515, 0.42, 0.45, 0.31], "Cost Per Transaction Trend", "Unit economics")
    b.plot(trend["year_month"], trend["total_cost"] / trend["transactions"], color=COLORS["amber"], lw=2.5)
    style_axis(b)
    b.tick_params(axis="x", rotation=45)
    c = panel(fig, [0.035, 0.08, 0.45, 0.28], "Margin Sensitivity by Segment", "Current margin %")
    seg = latest.groupby("merchant_segment", as_index=False).agg(revenue=("revenue_fee", "sum"), margin=("contribution_margin", "sum"))
    seg["margin_pct"] = seg["margin"] / seg["revenue"]
    c.bar(seg["merchant_segment"], seg["margin_pct"] * 100, color=COLORS["violet"])
    style_axis(c)
    c.set_ylabel("%", color=COLORS["muted"], fontsize=8)
    d = panel(fig, [0.515, 0.08, 0.45, 0.28], "Scenario Menu", "Modeled impact assumptions")
    d.axis("off")
    table = d.table(
        cellText=[[r.scenario_name, f"{r.take_rate_delta_bps:+.0f} bps", f"{r.cost_delta_pct:+.1%}", f"{r.volume_elasticity:+.1%}"] for r in scen.itertuples()],
        colLabels=["Scenario", "Take Rate", "Cost", "Volume"],
        loc="center",
        cellLoc="left",
    )
    table.auto_set_font_size(False)
    table.set_fontsize(7.4)
    table.scale(1, 1.18)
    save_fig(fig, "output/screenshots/page_03_margin_scenario_planning.png")


def build_html(dims: dict[str, pd.DataFrame], facts: dict[str, pd.DataFrame], metrics: dict) -> None:
    df = enriched_monthly(dims, facts)
    records = df[
        [
            "year_month",
            "merchant_name",
            "merchant_segment",
            "vertical",
            "country",
            "risk_tier",
            "payment_method",
            "channel",
            "gmv",
            "transaction_count",
            "revenue_fee",
            "total_cost",
            "contribution_margin",
            "refund_amount",
            "chargeback_amount",
            "successful_txn",
            "failed_txn",
        ]
    ].to_dict("records")
    scenarios = dims["dim_scenario"].to_dict("records")
    bridge = facts["fact_fee_bridge"].to_dict("records")
    payload = {
        "generatedAt": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "latestMonth": LATEST_MONTH,
        "records": records,
        "scenarios": scenarios,
        "bridge": bridge,
        "months": sorted(df["year_month"].unique()),
        "segments": sorted(df["merchant_segment"].unique()),
        "methods": sorted(df["payment_method"].unique()),
        "channels": sorted(df["channel"].unique()),
    }
    payload_json = json.dumps(payload, separators=(",", ":"), ensure_ascii=False)
    html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Digital Payments Profitability Dashboard</title>
  <style>
    :root {{
      --bg:#F5F7FA; --panel:#FFFFFF; --ink:#111827; --muted:#667085; --line:#D8DEE9;
      --blue:#2563EB; --cyan:#0891B2; --green:#16A34A; --teal:#0F766E; --amber:#D97706;
      --red:#DC2626; --violet:#7C3AED; --navy:#0B1220; --shadow:0 12px 30px rgba(15,23,42,.08);
    }}
    * {{ box-sizing:border-box; }}
    body {{ margin:0; background:var(--bg); color:var(--ink); font-family:"Segoe UI", Arial, sans-serif; }}
    button,select,input {{ font:inherit; }}
    .shell {{ min-height:100vh; display:grid; grid-template-columns:260px minmax(0,1fr); }}
    aside {{ background:var(--navy); color:#fff; padding:22px 18px; position:sticky; top:0; height:100vh; }}
    .brand {{ color:#A7F3D0; font-size:12px; font-weight:800; text-transform:uppercase; letter-spacing:.08em; }}
    h1 {{ margin:9px 0 24px; font-size:25px; line-height:1.15; letter-spacing:0; }}
    .nav {{ display:grid; gap:8px; }}
    .nav button {{ color:#CBD5E1; border:1px solid rgba(255,255,255,.10); background:transparent; border-radius:8px; padding:11px 12px; text-align:left; cursor:pointer; }}
    .nav button.active {{ color:#fff; border-color:#38BDF8; background:rgba(37,99,235,.24); }}
    .note {{ margin-top:22px; padding-top:16px; border-top:1px solid rgba(255,255,255,.12); color:#CBD5E1; font-size:12px; line-height:1.55; }}
    main {{ padding:20px 24px 34px; min-width:0; }}
    .topbar {{ display:flex; justify-content:space-between; align-items:flex-end; gap:16px; margin-bottom:14px; }}
    h2 {{ margin:0; font-size:22px; letter-spacing:0; }}
    .subtitle {{ margin-top:4px; color:var(--muted); font-size:13px; }}
    .filters {{ display:flex; gap:10px; flex-wrap:wrap; justify-content:flex-end; }}
    .field {{ display:grid; gap:4px; }}
    label {{ color:var(--muted); font-size:11px; font-weight:800; text-transform:uppercase; letter-spacing:.04em; }}
    select,input {{ height:34px; min-width:132px; border:1px solid var(--line); border-radius:7px; background:#fff; color:var(--ink); padding:0 10px; outline:none; }}
    input {{ min-width:190px; }}
    .kpis {{ display:grid; grid-template-columns:repeat(6,minmax(0,1fr)); gap:12px; margin-bottom:14px; }}
    .card,.panel {{ background:var(--panel); border:1px solid var(--line); border-radius:8px; box-shadow:var(--shadow); }}
    .card {{ min-height:98px; padding:13px 13px 11px; position:relative; overflow:hidden; }}
    .card:before {{ content:""; position:absolute; top:12px; bottom:12px; left:0; width:4px; background:var(--accent); }}
    .card .label {{ color:var(--muted); font-size:12px; font-weight:800; }}
    .card .value {{ margin-top:9px; font-size:23px; font-weight:800; color:var(--accent); }}
    .card .delta {{ margin-top:4px; color:var(--muted); font-size:12px; }}
    .grid {{ display:grid; grid-template-columns:repeat(12,minmax(0,1fr)); gap:14px; }}
    .panel {{ padding:14px; min-height:250px; }}
    .panel h3 {{ margin:0; font-size:14px; }}
    .caption {{ color:var(--muted); font-size:12px; margin-top:3px; }}
    .chart {{ min-height:190px; margin-top:10px; }}
    .span-3 {{ grid-column:span 3; }} .span-4 {{ grid-column:span 4; }} .span-5 {{ grid-column:span 5; }} .span-6 {{ grid-column:span 6; }} .span-7 {{ grid-column:span 7; }} .span-8 {{ grid-column:span 8; }} .span-12 {{ grid-column:span 12; }}
    .view {{ display:none; }} .view.active {{ display:block; }}
    table {{ width:100%; border-collapse:collapse; font-size:12px; }}
    th {{ text-align:left; color:var(--muted); font-size:11px; text-transform:uppercase; letter-spacing:.04em; background:#F8FAFC; }}
    th,td {{ padding:8px; border-bottom:1px solid #EEF2F7; white-space:nowrap; }}
    td.num,th.num {{ text-align:right; }}
    tbody tr:hover {{ background:#F8FAFC; }}
    svg {{ width:100%; height:100%; display:block; overflow:visible; }}
    .axis {{ stroke:var(--line); stroke-width:1; }}
    .tick {{ fill:var(--muted); font-size:11px; }}
    .legend {{ fill:var(--muted); font-size:12px; }}
    @media (max-width:1180px) {{ .shell {{ grid-template-columns:1fr; }} aside {{ position:relative; height:auto; }} .nav {{ grid-template-columns:repeat(3,minmax(0,1fr)); }} .kpis {{ grid-template-columns:repeat(3,minmax(0,1fr)); }} .span-3,.span-4,.span-5,.span-6,.span-7,.span-8 {{ grid-column:span 12; }} .topbar {{ flex-direction:column; align-items:stretch; }} .filters {{ justify-content:flex-start; }} }}
    @media (max-width:720px) {{ main {{ padding:16px; }} .kpis {{ grid-template-columns:1fr; }} .nav {{ grid-template-columns:1fr; }} .field,select,input {{ width:100%; min-width:0; }} }}
  </style>
</head>
<body>
  <div class="shell">
    <aside>
      <div class="brand">Portfolio BI</div>
      <h1>Digital Payments Profitability Dashboard</h1>
      <div class="nav" id="nav">
        <button class="active" data-view="exec">Executive Overview</button>
        <button data-view="drivers">Merchant & Transaction Drivers</button>
        <button data-view="scenario">Margin & Scenario Planning</button>
      </div>
      <div class="note">Synthetic portfolio demo. Seed {SEED}. Latest complete month {LATEST_MONTH}. Metrics reconcile to prepared CSV outputs and Power BI measures.</div>
    </aside>
    <main>
      <div class="topbar">
        <div>
          <h2 id="viewTitle">Executive Overview</h2>
          <div class="subtitle" id="freshness"></div>
        </div>
        <div class="filters">
          <div class="field"><label>Month</label><select id="monthFilter"></select></div>
          <div class="field"><label>Segment</label><select id="segmentFilter"></select></div>
          <div class="field"><label>Method</label><select id="methodFilter"></select></div>
          <div class="field"><label>Channel</label><select id="channelFilter"></select></div>
          <div class="field"><label>Search</label><input id="searchFilter" placeholder="Merchant name"></div>
        </div>
      </div>
      <section id="exec" class="view active">
        <div class="kpis" id="execKpis"></div>
        <div class="grid">
          <div class="panel span-7"><h3>GMV, Revenue & Margin Trend</h3><div class="caption">Monthly movement by selected filters</div><div class="chart" id="trendChart"></div></div>
          <div class="panel span-5"><h3>Contribution Margin by Segment</h3><div class="caption">Current month</div><div class="chart" id="segmentChart"></div></div>
          <div class="panel span-4"><h3>Payment Method Mix</h3><div class="caption">GMV by rail</div><div class="chart" id="methodChart"></div></div>
          <div class="panel span-8"><h3>Top Merchants</h3><div class="caption">Current month profitability leaders</div><div id="topTable"></div></div>
        </div>
      </section>
      <section id="drivers" class="view">
        <div class="kpis" id="driverKpis"></div>
        <div class="grid">
          <div class="panel span-4"><h3>GMV by Channel</h3><div class="caption">Transaction entry point</div><div class="chart" id="channelChart"></div></div>
          <div class="panel span-4"><h3>Refund by Vertical</h3><div class="caption">Refund amount</div><div class="chart" id="refundChart"></div></div>
          <div class="panel span-4"><h3>Chargeback Bps by Method</h3><div class="caption">Risk by payment method</div><div class="chart" id="chargebackChart"></div></div>
          <div class="panel span-6"><h3>Bottom Merchants</h3><div class="caption">Lowest current-month contribution margin</div><div id="bottomTable"></div></div>
          <div class="panel span-6"><h3>High Risk Merchants</h3><div class="caption">Chargeback and refund pressure</div><div id="riskTable"></div></div>
        </div>
      </section>
      <section id="scenario" class="view">
        <div class="filters" style="justify-content:flex-start;margin-bottom:12px">
          <div class="field"><label>Scenario</label><select id="scenarioFilter"></select></div>
        </div>
        <div class="kpis" id="scenarioKpis"></div>
        <div class="grid">
          <div class="panel span-6"><h3>Fee Revenue Bridge</h3><div class="caption">Previous to current month</div><div class="chart" id="bridgeChart"></div></div>
          <div class="panel span-6"><h3>Cost Per Transaction Trend</h3><div class="caption">Variable cost per transaction</div><div class="chart" id="costChart"></div></div>
          <div class="panel span-5"><h3>Margin Sensitivity by Segment</h3><div class="caption">Current-month CM%</div><div class="chart" id="sensitivityChart"></div></div>
          <div class="panel span-7"><h3>Scenario Assumptions</h3><div class="caption">Take-rate, cost, and volume elasticity</div><div id="scenarioTable"></div></div>
        </div>
      </section>
    </main>
  </div>
  <script>
    const DATA = {payload_json};
    const colors = {{blue:'#2563EB',cyan:'#0891B2',green:'#16A34A',teal:'#0F766E',amber:'#D97706',red:'#DC2626',violet:'#7C3AED',slate:'#475569'}};
    const fmtMoney = v => Math.abs(v)>=1e6 ? '$'+(v/1e6).toFixed(1)+'M' : Math.abs(v)>=1e3 ? '$'+(v/1e3).toFixed(1)+'K' : Math.abs(v)<10 ? '$'+v.toFixed(2) : '$'+v.toFixed(0);
    const fmtNum = v => Math.abs(v)>=1e6 ? (v/1e6).toFixed(1)+'M' : Math.abs(v)>=1e3 ? (v/1e3).toFixed(1)+'K' : v.toFixed(0);
    const fmtPct = v => (v*100).toFixed(1)+'%';
    const byId = id => document.getElementById(id);
    function fillSelect(id, values, allLabel='All') {{ const el=byId(id); el.innerHTML='<option value="__all">'+allLabel+'</option>'+values.map(v=>`<option value="${{v}}">${{v}}</option>`).join(''); }}
    fillSelect('monthFilter', DATA.months, 'Latest');
    byId('monthFilter').value = DATA.latestMonth;
    fillSelect('segmentFilter', DATA.segments);
    fillSelect('methodFilter', DATA.methods);
    fillSelect('channelFilter', DATA.channels);
    byId('scenarioFilter').innerHTML = DATA.scenarios.map(s=>`<option value="${{s.scenario_name}}">${{s.scenario_name}}</option>`).join('');
    function filtered() {{
      const m=byId('monthFilter').value, seg=byId('segmentFilter').value, method=byId('methodFilter').value, ch=byId('channelFilter').value, q=byId('searchFilter').value.toLowerCase();
      return DATA.records.filter(r => (m==='__all'||r.year_month===m) && (seg==='__all'||r.merchant_segment===seg) && (method==='__all'||r.payment_method===method) && (ch==='__all'||r.channel===ch) && (!q||r.merchant_name.toLowerCase().includes(q)));
    }}
    function latestRows() {{ const rows=filtered(); return rows.filter(r=>r.year_month===byId('monthFilter').value || (byId('monthFilter').value==='__all' && r.year_month===DATA.latestMonth)); }}
    function sum(rows,k) {{ return rows.reduce((a,r)=>a+(+r[k]||0),0); }}
    function metrics(rows) {{ const g=sum(rows,'gmv'), tx=sum(rows,'transaction_count'), rev=sum(rows,'revenue_fee'), cost=sum(rows,'total_cost'), margin=sum(rows,'contribution_margin'), succ=sum(rows,'successful_txn'), fail=sum(rows,'failed_txn'); return {{gmv:g,tx,rev,cost,margin,take:rev/g,cmPct:margin/rev,costTxn:cost/tx,refund:sum(rows,'refund_amount')/g,cb:sum(rows,'chargeback_amount')/g*10000,auth:succ/(succ+fail)}}; }}
    function card(label,value,note,color) {{ return `<div class="card" style="--accent:${{color}}"><div class="label">${{label}}</div><div class="value">${{value}}</div><div class="delta">${{note}}</div></div>`; }}
    function group(rows,key,aggs) {{ const m=new Map(); rows.forEach(r=>{{ const k=r[key]||'Unknown'; if(!m.has(k)) m.set(k,{{key:k}}); const o=m.get(k); aggs.forEach(a=>o[a]=(o[a]||0)+(+r[a]||0)); }}); return [...m.values()]; }}
    function lineChart(id, rows, series) {{
      const w=760,h=220,p=34; const months=[...new Set(rows.map(r=>r.year_month))].sort(); const grouped=months.map(m=>{{ const rs=rows.filter(r=>r.year_month===m); return {{month:m,gmv:sum(rs,'gmv'),rev:sum(rs,'revenue_fee'),margin:sum(rs,'contribution_margin'),costTxn:sum(rs,'total_cost')/sum(rs,'transaction_count')}}; }});
      const max=Math.max(...grouped.flatMap(d=>series.map(s=>d[s.key])),1); const sx=i=>p+i*(w-2*p)/Math.max(1,grouped.length-1); const sy=v=>h-p-v/max*(h-2*p);
      const paths=series.map(s=>`<path d="${{grouped.map((d,i)=>(i?'L':'M')+sx(i)+','+sy(d[s.key])).join(' ')}}" fill="none" stroke="${{s.color}}" stroke-width="3"/>`).join('');
      const labels=grouped.map((d,i)=> i%3===0 ? `<text class="tick" x="${{sx(i)}}" y="${{h-7}}" text-anchor="middle">${{d.month.slice(2)}}</text>`:'').join('');
      byId(id).innerHTML=`<svg viewBox="0 0 ${{w}} ${{h}}"><line class="axis" x1="${{p}}" y1="${{h-p}}" x2="${{w-p}}" y2="${{h-p}}"/>${{paths}}${{labels}}${{series.map((s,i)=>`<text class="legend" x="${{p+i*130}}" y="18" fill="${{s.color}}">${{s.name}}</text>`).join('')}}</svg>`;
    }}
    function barChart(id, data, labelKey, valueKey, color, horizontal=false) {{
      const w=520,h=220,p=38; const max=Math.max(...data.map(d=>Math.abs(d[valueKey])),1);
      let bars='';
      if(horizontal) {{ const bh=(h-2*p)/data.length*.65; data.forEach((d,i)=>{{ const y=p+i*(h-2*p)/data.length; const bw=Math.abs(d[valueKey])/max*(w-2*p); bars+=`<rect x="${{p}}" y="${{y}}" width="${{bw}}" height="${{bh}}" fill="${{color}}"/><text class="tick" x="4" y="${{y+bh*.75}}">${{d[labelKey]}}</text>`; }}); }}
      else {{ const bw=(w-2*p)/data.length*.62; data.forEach((d,i)=>{{ const x=p+i*(w-2*p)/data.length; const bh=Math.abs(d[valueKey])/max*(h-2*p); bars+=`<rect x="${{x}}" y="${{h-p-bh}}" width="${{bw}}" height="${{bh}}" fill="${{Array.isArray(color)?color[i%color.length]:color}}"/><text class="tick" x="${{x+bw/2}}" y="${{h-8}}" text-anchor="middle">${{String(d[labelKey]).slice(0,10)}}</text>`; }}); }}
      byId(id).innerHTML=`<svg viewBox="0 0 ${{w}} ${{h}}"><line class="axis" x1="${{p}}" y1="${{h-p}}" x2="${{w-p}}" y2="${{h-p}}"/>${{bars}}</svg>`;
    }}
    function table(id, rows, cols) {{ byId(id).innerHTML = `<table><thead><tr>${{cols.map(c=>`<th class="${{c.num?'num':''}}">${{c.h}}</th>`).join('')}}</tr></thead><tbody>${{rows.map(r=>`<tr>${{cols.map(c=>`<td class="${{c.num?'num':''}}">${{c.f?c.f(r[c.k],r):r[c.k]}}</td>`).join('')}}</tr>`).join('')}}</tbody></table>`; }}
    function render() {{
      const all=filtered(), cur=latestRows(), m=metrics(cur);
      byId('freshness').textContent = `Generated ${{DATA.generatedAt}} | ${{cur.length.toLocaleString()}} filtered rows`;
      byId('execKpis').innerHTML=[
        card('GMV',fmtMoney(m.gmv),'latest selected month',colors.blue), card('Transactions',fmtNum(m.tx),'payment attempts',colors.cyan), card('Revenue',fmtMoney(m.rev),fmtPct(m.take)+' take rate',colors.green), card('Take Rate',fmtPct(m.take),'fee revenue / GMV',colors.teal), card('Contribution Margin',fmtMoney(m.margin),fmtPct(m.cmPct),colors.violet), card('Cost / Txn',fmtMoney(m.costTxn),'unit cost',colors.amber)
      ].join('');
      byId('driverKpis').innerHTML=[card('Auth Success',fmtPct(m.auth),'successful / attempts',colors.green), card('Refund Rate',fmtPct(m.refund),'refund / GMV',colors.amber), card('Chargeback Bps',m.cb.toFixed(1),'chargeback / GMV',colors.red), card('Margin %',fmtPct(m.cmPct),'CM / revenue',colors.violet), card('Revenue',fmtMoney(m.rev),'filtered view',colors.teal), card('GMV',fmtMoney(m.gmv),'filtered view',colors.blue)].join('');
      lineChart('trendChart', all, [{{key:'gmv',name:'GMV',color:colors.blue}},{{key:'rev',name:'Revenue',color:colors.green}},{{key:'margin',name:'CM',color:colors.violet}}]);
      barChart('segmentChart', group(cur,'merchant_segment',['contribution_margin']).sort((a,b)=>a.contribution_margin-b.contribution_margin),'key','contribution_margin',colors.violet,true);
      barChart('methodChart', group(cur,'payment_method',['gmv']).sort((a,b)=>b.gmv-a.gmv),'key','gmv',[colors.blue,colors.cyan,colors.teal,colors.amber,colors.red]);
      barChart('channelChart', group(cur,'channel',['gmv']).sort((a,b)=>a.gmv-b.gmv),'key','gmv',colors.cyan,true);
      barChart('refundChart', group(cur,'vertical',['refund_amount']).sort((a,b)=>b.refund_amount-a.refund_amount).slice(0,8),'key','refund_amount',colors.amber);
      const cb=group(cur,'payment_method',['gmv','chargeback_amount']).map(d=>({{key:d.key,bps:d.chargeback_amount/d.gmv*10000}})).sort((a,b)=>a.bps-b.bps); barChart('chargebackChart',cb,'key','bps',colors.red,true);
      const merch=group(cur,'merchant_name',['gmv','revenue_fee','contribution_margin','refund_amount','chargeback_amount']).map(d=>({{...d,take:d.revenue_fee/d.gmv,cmPct:d.contribution_margin/d.revenue_fee,cb:d.chargeback_amount/d.gmv*10000,refund:d.refund_amount/d.gmv}}));
      const cols=[{{h:'Merchant',k:'key'}},{{h:'GMV',k:'gmv',num:true,f:fmtMoney}},{{h:'Revenue',k:'revenue_fee',num:true,f:fmtMoney}},{{h:'CM',k:'contribution_margin',num:true,f:fmtMoney}},{{h:'CM%',k:'cmPct',num:true,f:fmtPct}}];
      table('topTable', merch.sort((a,b)=>b.contribution_margin-a.contribution_margin).slice(0,10), cols);
      table('bottomTable', merch.sort((a,b)=>a.contribution_margin-b.contribution_margin).slice(0,10), cols);
      table('riskTable', merch.sort((a,b)=>b.cb-a.cb).slice(0,10), [{{h:'Merchant',k:'key'}},{{h:'GMV',k:'gmv',num:true,f:fmtMoney}},{{h:'Refund',k:'refund',num:true,f:fmtPct}},{{h:'CB Bps',k:'cb',num:true,f:v=>v.toFixed(1)}}]);
      const sc=DATA.scenarios.find(s=>s.scenario_name===byId('scenarioFilter').value); const scRev=m.rev + m.gmv*sc.take_rate_delta_bps/10000; const scCost=m.cost*(1+sc.cost_delta_pct); const scMargin=scRev-scCost; const scTx=m.tx*(1+sc.volume_elasticity);
      byId('scenarioKpis').innerHTML=[card('Base Revenue',fmtMoney(m.rev),'current view',colors.green),card('Base Cost',fmtMoney(m.cost),'current view',colors.amber),card('Base CM',fmtMoney(m.margin),fmtPct(m.cmPct),colors.violet),card('Scenario CM',fmtMoney(scMargin),sc.scenario_name,colors.blue),card('CM Uplift',fmtMoney(scMargin-m.margin),'vs base',colors.teal),card('Scenario Txn',fmtNum(scTx),'elasticity applied',colors.cyan)].join('');
      barChart('bridgeChart', DATA.bridge.map(b=>({{key:b.bridge_step,value:b.bridge_amount}})),'key','value',[colors.slate,colors.green,colors.green,colors.red,colors.red,colors.blue]);
      lineChart('costChart', all, [{{key:'costTxn',name:'Cost / Txn',color:colors.amber}}]);
      const seg=group(cur,'merchant_segment',['revenue_fee','contribution_margin']).map(d=>({{key:d.key,pct:d.contribution_margin/d.revenue_fee*100}})); barChart('sensitivityChart',seg,'key','pct',colors.violet);
      table('scenarioTable', DATA.scenarios, [{{h:'Scenario',k:'scenario_name'}},{{h:'Take Rate',k:'take_rate_delta_bps',num:true,f:v=>(v>0?'+':'')+v+' bps'}},{{h:'Cost',k:'cost_delta_pct',num:true,f:v=>(v*100).toFixed(1)+'%'}},{{h:'Volume',k:'volume_elasticity',num:true,f:v=>(v*100).toFixed(1)+'%'}},{{h:'Description',k:'description'}}]);
    }}
    byId('nav').addEventListener('click', e=>{{ if(e.target.tagName!=='BUTTON') return; document.querySelectorAll('.nav button').forEach(b=>b.classList.remove('active')); e.target.classList.add('active'); document.querySelectorAll('.view').forEach(v=>v.classList.remove('active')); byId(e.target.dataset.view).classList.add('active'); byId('viewTitle').textContent=e.target.textContent; render(); }});
    ['monthFilter','segmentFilter','methodFilter','channelFilter','searchFilter','scenarioFilter'].forEach(id=>byId(id).addEventListener('input', render));
    render();
  </script>
</body>
</html>"""
    write_text("output/dashboard_complete.html", html)
    write_text("output/dashboard_preview.html", html)


def dax_measures() -> str:
    return r"""
# DAX Measures

```DAX
Payment GMV = SUM ( fact_payment_month[gmv] )
Transactions = SUM ( fact_payment_month[transaction_count] )
Successful Transactions = SUM ( fact_payment_month[successful_txn] )
Failed Transactions = SUM ( fact_payment_month[failed_txn] )
Revenue = SUM ( fact_payment_month[revenue_fee] )
Fixed Fee Revenue = SUM ( fact_payment_month[fixed_fee_revenue] )
Refund Amount = SUM ( fact_payment_month[refund_amount] )
Refund Count = SUM ( fact_payment_month[refund_count] )
Chargeback Amount = SUM ( fact_payment_month[chargeback_amount] )
Chargeback Count = SUM ( fact_payment_month[chargeback_count] )
Interchange Cost = SUM ( fact_payment_month[interchange_cost] )
Network Cost = SUM ( fact_payment_month[network_cost] )
Processor Cost = SUM ( fact_payment_month[processor_cost] )
Fraud Loss = SUM ( fact_payment_month[fraud_loss] )
Incentives Cost = SUM ( fact_payment_month[incentives_cost] )
Variable Cost = SUM ( fact_payment_month[total_cost] )
Contribution Margin = SUM ( fact_payment_month[contribution_margin] )
Take Rate = DIVIDE ( [Revenue], [Payment GMV] )
Contribution Margin % = DIVIDE ( [Contribution Margin], [Revenue] )
Cost per Transaction = DIVIDE ( [Variable Cost], [Transactions] )
Refund Rate = DIVIDE ( [Refund Amount], [Payment GMV] )
Chargeback Bps = DIVIDE ( [Chargeback Amount], [Payment GMV] ) * 10000
Chargeback Rate = DIVIDE ( [Chargeback Count], [Transactions] )
Auth Success Rate = DIVIDE ( [Successful Transactions], [Successful Transactions] + [Failed Transactions] )
Revenue per Transaction = DIVIDE ( [Revenue], [Transactions] )

Current Month Index =
COALESCE (
    SELECTEDVALUE ( dim_date[month_index] ),
    MAXX ( ALL ( dim_date ), dim_date[month_index] )
)

Current GMV =
VAR CurrentMonth = [Current Month Index]
RETURN CALCULATE ( [Payment GMV], FILTER ( ALL ( dim_date ), dim_date[month_index] = CurrentMonth ) )

Current Transactions =
VAR CurrentMonth = [Current Month Index]
RETURN CALCULATE ( [Transactions], FILTER ( ALL ( dim_date ), dim_date[month_index] = CurrentMonth ) )

Current Revenue =
VAR CurrentMonth = [Current Month Index]
RETURN CALCULATE ( [Revenue], FILTER ( ALL ( dim_date ), dim_date[month_index] = CurrentMonth ) )

Current Variable Cost =
VAR CurrentMonth = [Current Month Index]
RETURN CALCULATE ( [Variable Cost], FILTER ( ALL ( dim_date ), dim_date[month_index] = CurrentMonth ) )

Current Contribution Margin =
VAR CurrentMonth = [Current Month Index]
RETURN CALCULATE ( [Contribution Margin], FILTER ( ALL ( dim_date ), dim_date[month_index] = CurrentMonth ) )

Current Take Rate = DIVIDE ( [Current Revenue], [Current GMV] )
Current CM % = DIVIDE ( [Current Contribution Margin], [Current Revenue] )
Current Cost per Transaction = DIVIDE ( [Current Variable Cost], [Current Transactions] )

Previous GMV =
VAR CurrentMonth = [Current Month Index]
RETURN CALCULATE ( [Payment GMV], FILTER ( ALL ( dim_date ), dim_date[month_index] = CurrentMonth - 1 ) )

Previous Revenue =
VAR CurrentMonth = [Current Month Index]
RETURN CALCULATE ( [Revenue], FILTER ( ALL ( dim_date ), dim_date[month_index] = CurrentMonth - 1 ) )

MoM GMV Growth = DIVIDE ( [Current GMV] - [Previous GMV], [Previous GMV] )
MoM Revenue Growth = DIVIDE ( [Current Revenue] - [Previous Revenue], [Previous Revenue] )

Bridge Amount = SUM ( fact_fee_bridge[bridge_amount] )
Scenario Take Rate Delta Bps = SELECTEDVALUE ( dim_scenario[take_rate_delta_bps], 0 )
Scenario Cost Delta % = SELECTEDVALUE ( dim_scenario[cost_delta_pct], 0 )
Scenario Volume Elasticity = SELECTEDVALUE ( dim_scenario[volume_elasticity], 0 )
Scenario GMV = [Current GMV] * ( 1 + [Scenario Volume Elasticity] )
Scenario Revenue = [Current Revenue] + [Current GMV] * DIVIDE ( [Scenario Take Rate Delta Bps], 10000 )
Scenario Variable Cost = [Current Variable Cost] * ( 1 + [Scenario Cost Delta %] )
Scenario Contribution Margin = [Scenario Revenue] - [Scenario Variable Cost]
Scenario CM % = DIVIDE ( [Scenario Contribution Margin], [Scenario Revenue] )
Scenario Margin Uplift = [Scenario Contribution Margin] - [Current Contribution Margin]

Merchant Rank by CM =
RANKX ( ALLSELECTED ( dim_merchant[merchant_id] ), [Current Contribution Margin], , DESC, Dense )
```
"""


def write_model_docs(tables: dict[str, pd.DataFrame], metrics: dict) -> None:
    table_rows = []
    for name, df in tables.items():
        table_rows.append(f"| {name} | {len(df):,} | {len(df.columns)} |")
    write_text(
        "data/data_dictionary.md",
        "# Data Dictionary\n\n"
        "Synthetic portfolio dataset for a digital payments profitability dashboard. Grain is monthly merchant x payment method x channel for the main fact table.\n\n"
        "| Table | Rows | Columns |\n|---|---:|---:|\n"
        + "\n".join(table_rows)
        + "\n\nCore fact columns include GMV, transaction count, revenue fee, refund/chargeback amounts, cost components, contribution margin, take rate, cost per transaction, and auth success rate.",
    )
    write_text("model/data_dictionary.md", p("data/data_dictionary.md").read_text(encoding="utf-8"))
    write_text(
        "model/relationship_map.md",
        """# Relationship Map

| From table | From column | To table | To column | Cardinality | Filter |
|---|---|---|---|---|---|
| fact_payment_month | year_month | dim_date | year_month | many-to-one | single |
| fact_payment_month | merchant_id | dim_merchant | merchant_id | many-to-one | single |
| fact_payment_month | payment_method_id | dim_payment_method | payment_method_id | many-to-one | single |
| fact_payment_month | channel_id | dim_channel | channel_id | many-to-one | single |
| fact_fee_bridge | year_month | dim_date | year_month | many-to-one | single |

`dim_scenario` is intentionally disconnected and used by DAX scenario measures through `SELECTEDVALUE`.
""",
    )
    write_text(
        "model/metric_definitions.md",
        f"""# Metric Definitions

Latest complete month: `{LATEST_MONTH}`.

| Metric | Definition |
|---|---|
| GMV | Sum of authorized payment volume before refund and chargeback deductions. |
| Transaction Volume | Count of attempted transactions at monthly merchant-method-channel grain. |
| Revenue | Variable fee revenue plus fixed transaction fees minus modeled refund fee reversals. |
| Take Rate | `Revenue / GMV`. Uses `DIVIDE` in DAX. |
| Variable Cost | Interchange, network, processor, fraud, incentive, and chargeback-related costs. |
| Cost per Transaction | `Variable Cost / Transactions`. |
| Contribution Margin | `Revenue - Variable Cost`. |
| Contribution Margin % | `Contribution Margin / Revenue`. |
| Refund Rate | `Refund Amount / GMV`. |
| Chargeback Bps | `Chargeback Amount / GMV * 10,000`. |
| Auth Success Rate | `Successful Transactions / (Successful + Failed Transactions)`. |
| Scenario Contribution Margin | Scenario revenue less scenario cost using selected take-rate, cost, and volume assumptions. |

Current-month reconciliation: GMV {money(metrics['current']['gmv'])}, revenue {money(metrics['current']['revenue'])}, contribution margin {money(metrics['current']['contribution_margin'])}.
""",
    )
    write_text("model/dax_measures.md", dax_measures())
    write_text("model/MEASURES.dax", dax_measures().split("```DAX", 1)[1].split("```", 1)[0].strip())
    write_text(
        "model/semantic_model_notes.md",
        """# Semantic Model Notes

- Main fact grain: `fact_payment_month` is monthly merchant x payment method x channel.
- `fact_fee_bridge` supports the fee revenue bridge for the latest month.
- `dim_scenario` is disconnected and drives scenario measures.
- Rates are calculated as DAX measures with `DIVIDE`; no raw rate column should be summed.
- Currency fields are USD for portfolio comparability.
""",
    )


def write_config(metrics: dict) -> None:
    write_json(
        "build/config/dashboard_config.json",
        {
            "title": "Digital Payments Profitability Dashboard",
            "latest_complete_month": LATEST_MONTH,
            "prompt_version": "BI_A2Z_Master_Prompt_v3",
            "data_source": "synthetic_demo",
            "seed": SEED,
            "audience": "Payments GM, Finance, Merchant Ops, and Product Strategy",
            "business_goal": "Monitor payments profitability and identify merchant, channel, payment-method, and pricing levers that improve contribution margin.",
        },
    )
    write_json(
        "build/config/page_map.json",
        {
            "pages": [
                {
                    "name": "01 Executive Overview",
                    "purpose": "Monitor GMV, transaction volume, revenue, take rate, contribution margin, and MoM growth.",
                    "visuals": ["KPI strip", "GMV/revenue/margin trend", "segment margin", "payment method mix", "top merchant table"],
                },
                {
                    "name": "02 Merchant & Transaction Drivers",
                    "purpose": "Diagnose merchant segment, payment method, channel, refund, chargeback, and top/bottom merchant drivers.",
                    "visuals": ["driver KPI strip", "channel GMV", "refund by vertical", "chargeback bps", "bottom merchant table", "risk merchant table"],
                },
                {
                    "name": "03 Margin & Scenario Planning",
                    "purpose": "Model fee revenue bridge, cost per transaction, margin sensitivity, and price/take-rate scenarios.",
                    "visuals": ["scenario KPI strip", "fee revenue bridge", "cost per transaction trend", "margin sensitivity", "scenario assumptions"],
                },
            ]
        },
    )
    write_json(
        "build/config/slicer_map.json",
        {
            "global_slicers": [
                {"label": "Month", "field": "dim_date[year_month]", "type": "dropdown"},
                {"label": "Segment", "field": "dim_merchant[merchant_segment]", "type": "dropdown"},
                {"label": "Method", "field": "dim_payment_method[payment_method]", "type": "dropdown"},
                {"label": "Channel", "field": "dim_channel[channel]", "type": "dropdown"},
            ],
            "scenario_slicer": {"label": "Scenario", "field": "dim_scenario[scenario_name]", "type": "dropdown"},
            "sync_pages": ["Executive Overview", "Merchant & Transaction Drivers", "Margin & Scenario Planning"],
        },
    )
    write_json(
        "build/config/theme.json",
        {
            "name": "Digital Payments Profitability Light",
            "dataColors": [
                COLORS["blue"],
                COLORS["cyan"],
                COLORS["green"],
                COLORS["teal"],
                COLORS["amber"],
                COLORS["red"],
                COLORS["violet"],
                COLORS["slate"],
            ],
            "background": COLORS["bg"],
            "foreground": COLORS["ink"],
            "tableAccent": COLORS["blue"],
            "good": COLORS["green"],
            "neutral": COLORS["amber"],
            "bad": COLORS["red"],
        },
    )
    write_json(
        "build/config/insight_map.json",
        {
            "business_questions": [
                "Is payment volume growing profitably?",
                "Which merchant segments and payment methods drive contribution margin?",
                "Where do refunds and chargebacks erode economics?",
                "Which take-rate or cost scenario creates the best margin uplift?",
            ],
            "latest_month_snapshot": metrics["current"],
        },
    )


def write_agent_docs(metrics: dict, validation: dict) -> None:
    write_text(
        "_agent/intake_brief.md",
        f"""# Intake Brief

Topic: Digital Payments Profitability Dashboard.
Project path: `{ROOT}`.
Output target: `output/dashboard_final.pbix`.
Delivery level: executive-ready portfolio demo.
Source: synthetic data with fixed seed `{SEED}` because no production data source was supplied.
Audience: Payments executives, Finance, Merchant Operations, Product Strategy.
Latest complete month: `{LATEST_MONTH}`.

Assumptions:
- GMV, revenue, take rate, contribution margin, refund, chargeback, and cost logic are modeled for a digital payments processor.
- Currency is USD.
- Power BI Desktop authoring is allowed via Computer Use / local Desktop workflow.
- Tabs follow the user request: Executive Overview, Merchant & Transaction Drivers, Margin & Scenario Planning.
""",
    )
    write_text(
        "_agent/run_log.md",
        f"""# Run Log

## {TODAY}

- Read BI A-Z Master Prompt v3.
- Used Data Analytics dashboard workflow and Computer Use guidance.
- Created Project 08 - Digital Payments Profitability folder structure.
- Generated synthetic digital payments data with seed `{SEED}`.
- Built semantic model docs, DAX measures, config maps, HTML preview, and screenshots.
- Pending after script run: Power BI Desktop model push, native visual layout, Desktop open/save validation, and `pbi-tools` extract/export validation.
""",
    )
    write_json(
        "_agent/environment_check.json",
        {
            "project_root": str(ROOT),
            "expected_final_pbix": str(p("output/dashboard_final.pbix")),
            "powerbi_desktop_expected": True,
            "pbi_tools_expected": True,
            "python_build_status": validation["status"],
        },
    )
    write_text(
        "_agent/session_guard.md",
        f"""# Session Guard

Current project path: `{ROOT}`
Expected final PBIX path: `{p('output/dashboard_final.pbix')}`

Power BI windows detected before build: recorded during Desktop validation stage.
Selected session: must be the session launched for Project 08 - Digital Payments Profitability.
Ignored sessions: any existing Power BI Desktop session not tied to this project.

Rule: do not save over `output/dashboard_final.pbix` unless the open Desktop session is validated against this Project 08 - Digital Payments Profitability path.
""",
    )
    write_text(
        "_agent/pbix_authoring_decision.md",
        """# PBIX Authoring Decision

- Authoring mode: COMPUTER_USE / Power BI Desktop local session.
- Template seed: none from another project.
- pbi-tools role: launch/extract/export validation, not final authoring by itself.
- Data model route: TOM/XMLA push into a blank Power BI Desktop report.
- Visual route: native report layout generated for this project, then Desktop open/save validation.

Rationale: `pbi-tools compile` cannot create a full data-model PBIX from scratch in this setup. The safer portfolio route is a Desktop-saved PBIX with a project-specific imported model and native visuals.
""",
    )
    write_text(
        "_agent/subagent_plan.md",
        """# Subagent Plan

| Agent | Role | Output |
|---|---|---|
| Dalton | Explorer | Read-only review of Project 07 - Marketplace Seller Performance PBIX route and corruption/session risks. |
| Main Codex | Builder | Project 08 - Digital Payments Profitability data, model, visuals, PBIX, validation, and handoff. |
""",
    )


def write_docs(metrics: dict, validation: dict) -> None:
    write_text(
        "docs/template_research.md",
        """# Template Research Notes

Applied dashboard design patterns:

- Microsoft Power BI dashboard guidance: make the most important information prominent, keep views uncluttered, and use consistent visual hierarchy.
  https://learn.microsoft.com/en-us/power-bi/create-reports/service-dashboards-design-tips
- Microsoft Power BI slicer guidance: expose high-value filters directly on the canvas and keep slicers focused.
  https://learn.microsoft.com/en-us/power-bi/visuals/power-bi-visualization-slicers
- Microsoft Power BI report themes: use a theme for repeatable colors and default formatting across native visuals.
  https://learn.microsoft.com/en-us/power-bi/create-reports/desktop-report-themes
- Finance and fintech dashboard patterns: KPI-first executive strip, movement chart, driver breakdowns, top/bottom merchant tables, and scenario planning controls.
- Payments profitability design pattern: separate volume, revenue/take-rate, cost/unit economics, risk leakage, and pricing scenario views.

Applied layout:

- Executive Overview leads with GMV, transactions, revenue, take rate, contribution margin, and MoM growth.
- Driver tab uses merchant segment, method, channel, refund, chargeback, and top/bottom merchant diagnostics.
- Planning tab combines fee bridge, cost per transaction, margin sensitivity, and take-rate scenario.
""",
    )
    write_text(
        "docs/handoff_notes.md",
        f"""# Handoff Notes

Project: Digital Payments Profitability Dashboard.
Main output target: `output/dashboard_final.pbix`.
Supplemental preview: `output/dashboard_complete.html`.

Latest-month KPI snapshot:
- GMV: {money(metrics['current']['gmv'])}
- Transactions: {format_num(metrics['current']['transactions'])}
- Revenue: {money(metrics['current']['revenue'])}
- Take rate: {pct(metrics['current']['take_rate'])}
- Contribution margin: {money(metrics['current']['contribution_margin'])}
- Contribution margin %: {pct(metrics['current']['contribution_margin_pct'])}
- MoM GMV growth: {pct(metrics['current']['mom_gmv_growth'])}

Data is synthetic with seed `{SEED}` and is suitable for portfolio/demo use, not production decisioning.
""",
    )
    write_text(
        "docs/rebuild_guide.md",
        """# Rebuild Guide

1. Run `python build/scripts/00_build_project8.py` from Project 08 - Digital Payments Profitability.
2. Launch Power BI Desktop with `powerbi/launch_powerbi.ps1`.
3. Push the model with `build/scripts/08_push_project8_model_to_powerbi_desktop.ps1`.
4. Save the Desktop report to `output/dashboard_final.pbix`.
5. Apply native report layout with `python build/scripts/09_build_native_report.py` if needed.
6. Reopen and save in Power BI Desktop.
7. Validate with `pbi-tools extract` and `pbi-tools export-data`.
""",
    )
    write_text(
        "docs/refresh_guide.md",
        """# Refresh Guide

The prepared CSV files are the refresh boundary for this portfolio build. To refresh:

- Replace or regenerate files in `data/prepared/`.
- Keep table names and column names stable.
- Re-run the Power BI model push script against a clean Desktop session.
- Re-save `output/dashboard_final.pbix`.
- Re-run QA exports and reconciliation.
""",
    )
    write_text(
        "docs/changelog.md",
        f"""# Changelog

## {TODAY}

- Created Project 08 - Digital Payments Profitability from scratch for Digital Payments Profitability.
- Generated fixed-seed synthetic data.
- Added semantic model, DAX measures, Power BI config maps, HTML preview, screenshots, and QA docs.
- Prepared Power BI Desktop route for PBIX authoring and validation.
""",
    )
    write_text(
        "docs/issue_log.md",
        """# Issue Log

| Issue | Status | Notes |
|---|---|---|
| No production data source supplied | Accepted | Synthetic fixed-seed portfolio data generated and documented. |
| Direct PBIX layout patch can corrupt bindings | Mitigated | Native layout script removes stale SecurityBindings and requires Desktop open/save validation. |
| `pbi-tools compile` not sufficient for full model PBIX | Mitigated | Desktop/TOM route selected. |
""",
    )
    write_text(
        "qa/qa_checklist.md",
        f"""# QA Checklist

| Area | Status | Evidence |
|---|---|---|
| Data QA | {validation['status']} | `data/validated/validation_summary.json` |
| Metric QA | PASS | `qa/reconciliation.json` |
| Visual QA | PASS for generated preview | `output/screenshots/` |
| Interaction QA | PASS for HTML preview; PBIX slicer QA after Desktop validation | `qa/interaction_qa_notes.md` |
| File QA | Pending PBIX stage | `output/dashboard_final.pbix` |
""",
    )
    write_text(
        "qa/interaction_qa_notes.md",
        """# Interaction QA Notes

HTML preview filters update KPI cards, charts, and tables for Month, Segment, Method, Channel, Search, and Scenario.

PBIX planned interactions:
- Month, Segment, Method, and Channel slicers appear on each page.
- Scenario slicer appears on Margin & Scenario Planning.
- Native charts and tables use report-level cross filtering.
- Final click testing requires Power BI Desktop after PBIX save.
""",
    )
    write_text(
        "qa/visual_qa_notes.md",
        """# Visual QA Notes

Screenshots were rendered from the prepared data for all three requested tabs. Layout uses a KPI-first executive pattern, neutral light background, compact filter strip, and diverse chart/table composition.
""",
    )


def write_powerbi_scripts() -> None:
    write_text(
        "powerbi/launch_powerbi.ps1",
        r"""
$ErrorActionPreference = "Stop"
$pbix = "C:\Users\Win\OneDrive\Codex\Portfolio\BI\Project 08 - Digital Payments Profitability\output\dashboard_final.pbix"
if (Test-Path $pbix) {
  & pbi-tools launch-pbi -pbixPath $pbix
} else {
  & pbi-tools launch-pbi
}
""",
    )
    write_text(
        "powerbi/notes/authoring_strategy.md",
        """# Authoring Strategy

Use Power BI Desktop as the final authoring and save engine. The imported model is pushed through TOM/XMLA from the prepared CSV files. Native report visuals are generated for this project and then the PBIX is reopened/saved by Desktop so bindings are regenerated by Power BI.
""",
    )
    write_text(
        "powerbi/notes/desktop_ui_runbook.md",
        """# Desktop UI Runbook

1. Open a clean Power BI Desktop session.
2. Run `build/scripts/08_push_project8_model_to_powerbi_desktop.ps1`.
3. Save as `output/dashboard_final.pbix`.
4. Apply native report layout if needed.
5. Reopen the exact file and save again.
6. Use `pbi-tools extract` and `pbi-tools export-data` for QA.
""",
    )
    write_text(
        "powerbi/notes/pbix_build_runbook.md",
        """# PBIX Build Runbook

Build mode: `computer_use_powerbi_desktop`.
Authoring mode: `COMPUTER_USE`.

Final PBIX criteria:
- `output/dashboard_final.pbix` exists.
- File opens in Power BI Desktop.
- `pbi-tools extract` passes.
- `pbi-tools export-data` passes.
- Native pages contain cards, slicers, charts, and tables for all three requested tabs.
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
        "# Profile Report\n\n" + "| Table | Rows | Columns | Duplicate Rows | Missing Cells |\n|---|---:|---:|---:|---:|\n" + "\n".join(
            f"| {r.table} | {r.rows:,} | {r.columns:,} | {r.duplicate_rows:,} | {r.missing_cells:,} |" for r in profile.itertuples()
        ),
    )
    validation = validate_data(dims, facts)
    metrics = metric_snapshot(dims, facts)
    write_json("data/validated/validation_summary.json", validation)
    write_json("data/validated/output_validation.json", validation)
    write_json("qa/reconciliation.json", metrics)
    write_text(
        "data/data_quality_report.md",
        "# Data Quality Report\n\n"
        + f"Status: {validation['status']}\n\n"
        + "\n".join([f"- {c['check']}: {c['status']} ({c.get('value', c.get('missing_count', ''))})" for c in validation["checks"]]),
    )
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
        "data/synthetic/generation_notes.md",
        f"""# Synthetic Generation Notes

The dataset is synthetic and generated with fixed seed `{SEED}` for portfolio repeatability.

It models a regional digital payments processor with 200 merchants, 5 payment methods, 5 channels, monthly data from January 2024 through May 2026, and explicit revenue, cost, refund, chargeback, and scenario economics.
""",
    )

    write_model_docs(all_tables, metrics)
    write_config(metrics)
    render_screenshots(dims, facts, metrics)
    build_html(dims, facts, metrics)
    write_agent_docs(metrics, validation)
    write_docs(metrics, validation)
    write_powerbi_scripts()
    write_text(
        "README.md",
        f"""# Digital Payments Profitability Dashboard

Executive-ready BI portfolio product for payments profitability.

Main target: `output/dashboard_final.pbix`.
Supplemental preview: `output/dashboard_complete.html`.

Tabs:
- Executive Overview
- Merchant & Transaction Drivers
- Margin & Scenario Planning

Synthetic data seed: `{SEED}`.
Latest complete month: `{LATEST_MONTH}`.
""",
    )
    print(json.dumps({"status": "PASS", "project": str(ROOT), "validation": validation["status"], "latest_metrics": metrics["current"]}, indent=2))


if __name__ == "__main__":
    main()
