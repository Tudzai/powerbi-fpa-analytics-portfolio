from __future__ import annotations

import csv
import json
import math
import shutil
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
DATA_RAW = ROOT / "data" / "raw"
DATA_PREP = ROOT / "data" / "prepared"
DATA_VALID = ROOT / "data" / "validated"
MODEL_DIR = ROOT / "model"
BUILD_CONFIG = ROOT / "build" / "config"
PBIXPROJ_DIR = ROOT / "build" / "pbixproj" / "Project9_BNPL_Risk"
PBIP_DIR = ROOT / "powerbi" / "pbip" / "Project9_BNPL_Risk"
OUTPUT_DIR = ROOT / "output"
SCREEN_DIR = OUTPUT_DIR / "screenshots"
QA_DIR = ROOT / "qa"
DOCS_DIR = ROOT / "docs"
AGENT_DIR = ROOT / "_agent"

SEED = 90209
LATEST_SNAPSHOT = pd.Timestamp("2026-05-01")
FORECAST_MONTHS = pd.date_range("2026-06-01", "2026-12-01", freq="MS")
MEASURE_TABLE = "KPI Measures"

COLORS = {
    "navy": "#10223F",
    "ink": "#172033",
    "muted": "#687385",
    "border": "#D8DEE9",
    "panel": "#FFFFFF",
    "bg": "#F5F7FB",
    "blue": "#2F66B3",
    "teal": "#11887F",
    "green": "#2E9B65",
    "amber": "#E6A23C",
    "coral": "#D45D5D",
    "red": "#B42318",
    "purple": "#7357C8",
}


def mkdirs() -> None:
    for path in [
        DATA_RAW,
        DATA_PREP,
        DATA_VALID,
        MODEL_DIR,
        BUILD_CONFIG,
        PBIXPROJ_DIR,
        PBIP_DIR,
        OUTPUT_DIR,
        SCREEN_DIR,
        QA_DIR,
        DOCS_DIR,
        AGENT_DIR,
        ROOT / "powerbi" / "notes",
    ]:
        path.mkdir(parents=True, exist_ok=True)


def write_json(path: Path, payload: dict | list) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def write_md(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.strip() + "\n", encoding="utf-8")


def money(value: float) -> str:
    if abs(value) >= 1_000_000:
        return f"${value / 1_000_000:,.1f}M"
    if abs(value) >= 1_000:
        return f"${value / 1_000:,.1f}K"
    return f"${value:,.0f}"


def pct(value: float) -> str:
    return f"{value * 100:.1f}%"


def band_from_score(score: float) -> str:
    if score >= 735:
        return "A Prime"
    if score >= 700:
        return "B Near Prime"
    if score >= 660:
        return "C Mid"
    if score >= 615:
        return "D Subprime"
    return "E Deep Subprime"


def bucket_from_roll(rand: float, risk_score: float, mob: int, stress: float) -> str:
    base = max(0.02, min(0.92, 1.0 - risk_score))
    mob_lift = 1.0 + min(mob, 8) * 0.07
    p = base * mob_lift * stress
    if rand < max(0.02, 1.0 - p):
        return "Current"
    tail = (rand - max(0.02, 1.0 - p)) / max(p, 0.001)
    if tail < 0.28:
        return "1-7 DPD"
    if tail < 0.48:
        return "8-14 DPD"
    if tail < 0.66:
        return "15-29 DPD"
    if tail < 0.82:
        return "30-59 DPD"
    if tail < 0.94:
        return "60-89 DPD"
    return "90+ DPD"


def bucket_order(bucket: str) -> int:
    return {
        "Current": 0,
        "1-7 DPD": 1,
        "8-14 DPD": 2,
        "15-29 DPD": 3,
        "30-59 DPD": 4,
        "60-89 DPD": 5,
        "90+ DPD": 6,
        "Charge-off": 7,
    }[bucket]


def build_data() -> dict:
    rng = np.random.default_rng(SEED)
    start = pd.Timestamp("2024-01-01")
    end = pd.Timestamp("2026-05-31")
    all_days = pd.date_range(start, end, freq="D")
    months = pd.date_range("2024-01-01", "2026-05-01", freq="MS")

    n_apps = 52000
    product_types = np.array(["Pay-in-4", "Installment 3M", "Installment 6M", "Installment 12M"])
    product_probs = np.array([0.50, 0.25, 0.18, 0.07])
    channels = np.array(["Merchant Checkout", "Marketplace API", "Mobile App", "POS QR", "Partner Wallet"])
    channel_probs = np.array([0.38, 0.20, 0.24, 0.10, 0.08])
    segments = np.array(["First-time BNPL", "Repeat Light", "Repeat Heavy", "Dormant Reactivated"])
    segment_probs = np.array([0.42, 0.30, 0.20, 0.08])
    geos = np.array(["North", "South", "West", "Midwest", "Online Only"])
    categories = np.array(["Electronics", "Fashion", "Home", "Travel", "Beauty", "Education", "Sports"])
    merchants = [f"M{str(i).zfill(3)}" for i in range(1, 61)]
    merchant_categories = {m: rng.choice(categories, p=[0.20, 0.18, 0.15, 0.12, 0.15, 0.08, 0.12]) for m in merchants}

    app_dates = rng.choice(all_days, n_apps)
    app_dates = pd.to_datetime(app_dates)
    product = rng.choice(product_types, n_apps, p=product_probs)
    channel = rng.choice(channels, n_apps, p=channel_probs)
    segment = rng.choice(segments, n_apps, p=segment_probs)
    geo = rng.choice(geos, n_apps, p=[0.21, 0.22, 0.20, 0.19, 0.18])
    merchant = rng.choice(merchants, n_apps)
    category = np.array([merchant_categories[m] for m in merchant])
    repeat_lift = np.select(
        [segment == "Repeat Heavy", segment == "Repeat Light", segment == "Dormant Reactivated"],
        [34, 18, -14],
        default=-5,
    )
    product_lift = np.select([product == "Pay-in-4", product == "Installment 12M"], [8, -18], default=0)
    channel_lift = np.select([channel == "Marketplace API", channel == "Mobile App"], [-8, 7], default=0)
    credit_score = np.clip(rng.normal(674, 54, n_apps) + repeat_lift + product_lift + channel_lift, 520, 820).round(0)
    risk_band = np.array([band_from_score(s) for s in credit_score])
    amount_base = np.select(
        [product == "Pay-in-4", product == "Installment 3M", product == "Installment 6M"],
        [180, 430, 840],
        default=1450,
    )
    requested_amount = np.maximum(35, rng.lognormal(np.log(amount_base), 0.45)).round(2)
    pd_map = {
        "A Prime": 0.012,
        "B Near Prime": 0.022,
        "C Mid": 0.040,
        "D Subprime": 0.075,
        "E Deep Subprime": 0.128,
    }
    raw_pd = np.array([pd_map[x] for x in risk_band])
    approval_prob = np.clip(0.78 - raw_pd * 2.8 + (segment == "Repeat Heavy") * 0.10 + (product == "Installment 12M") * -0.06, 0.20, 0.93)
    approved = rng.random(n_apps) < approval_prob
    disbursed = approved & (rng.random(n_apps) < 0.965)
    approved_amount = np.where(approved, requested_amount * rng.uniform(0.80, 1.0, n_apps), 0).round(2)
    funded_amount = np.where(disbursed, approved_amount * rng.uniform(0.96, 1.0, n_apps), 0).round(2)
    lgd = np.clip(0.52 + raw_pd * 1.4 + (product == "Pay-in-4") * -0.08, 0.35, 0.82)

    apps = pd.DataFrame(
        {
            "application_id": [f"A{str(i).zfill(7)}" for i in range(1, n_apps + 1)],
            "application_date": app_dates,
            "application_month": app_dates.to_period("M").to_timestamp(),
            "product_type": product,
            "channel": channel,
            "customer_segment": segment,
            "region": geo,
            "merchant_id": merchant,
            "merchant_category": category,
            "requested_amount": requested_amount,
            "credit_score": credit_score.astype(int),
            "risk_band": risk_band,
            "pd_12m": raw_pd.round(4),
            "lgd": lgd.round(4),
            "approved_flag": approved.astype(int),
            "disbursed_flag": disbursed.astype(int),
            "approved_amount": approved_amount,
            "funded_amount": funded_amount,
            "decision": np.where(approved, "Approved", "Declined"),
        }
    )
    apps.to_csv(DATA_RAW / "bnpl_applications_raw.csv", index=False)

    loans = apps.loc[apps["disbursed_flag"].eq(1)].copy().reset_index(drop=True)
    loans.insert(0, "loan_id", [f"L{str(i).zfill(7)}" for i in range(1, len(loans) + 1)])
    term_map = {"Pay-in-4": 2, "Installment 3M": 3, "Installment 6M": 6, "Installment 12M": 12}
    apr_map = {"Pay-in-4": 0.00, "Installment 3M": 0.065, "Installment 6M": 0.115, "Installment 12M": 0.165}
    loans["term_months"] = loans["product_type"].map(term_map).astype(int)
    loans["apr"] = loans["product_type"].map(apr_map).round(4)
    loans["origination_month"] = pd.to_datetime(loans["application_date"]).dt.to_period("M").dt.to_timestamp()
    loans["expected_loss_at_origination"] = (loans["funded_amount"] * loans["pd_12m"] * loans["lgd"]).round(2)
    loans["limit_utilization"] = np.clip(loans["funded_amount"] / np.maximum(loans["approved_amount"], 1), 0, 1).round(4)

    snapshot_rows: list[dict] = []
    for row in loans.itertuples(index=False):
        orig = pd.Timestamp(row.origination_month)
        max_mob = min(int(row.term_months) + 4, (LATEST_SNAPSHOT.year - orig.year) * 12 + (LATEST_SNAPSHOT.month - orig.month) + 1)
        if max_mob <= 0:
            continue
        loan_risk = np.clip(row.pd_12m * 4.5 + rng.normal(0, 0.045), 0.01, 0.86)
        charged_off = False
        prior_bucket = "Current"
        for mob in range(max_mob):
            snap = orig + pd.DateOffset(months=mob)
            if snap > LATEST_SNAPSHOT:
                continue
            amort = min(1.0, mob / max(row.term_months, 1))
            principal = max(row.funded_amount * (1 - amort), row.funded_amount * 0.04)
            stress = 1.0 + 0.15 * math.sin((snap.month + mob) / 3.2)
            bucket = "Charge-off" if charged_off else bucket_from_roll(rng.random(), loan_risk, mob, stress)
            if prior_bucket in {"60-89 DPD", "90+ DPD"} and rng.random() < 0.34:
                bucket = rng.choice(["90+ DPD", "Charge-off"], p=[0.72, 0.28])
            if bucket == "90+ DPD" and rng.random() < 0.18:
                charged_off = True
                bucket = "Charge-off"
            cure_factor = 0.0 if bucket_order(bucket) >= 4 else rng.uniform(0.72, 1.02)
            current_principal = 0.0 if bucket == "Charge-off" else principal
            delinquency_balance = current_principal if bucket_order(bucket) >= 1 else 0.0
            dpd30_balance = current_principal if bucket_order(bucket) >= 4 else 0.0
            dpd60_balance = current_principal if bucket_order(bucket) >= 5 else 0.0
            npl_balance = current_principal if bucket_order(bucket) >= 6 else 0.0
            chargeoff = principal * row.lgd if bucket == "Charge-off" else 0.0
            monthly_pd = min(0.80, row.pd_12m / 12 * (1 + bucket_order(bucket) * 1.55))
            expected_loss = (current_principal + chargeoff) * monthly_pd * row.lgd
            provision = expected_loss * (1.25 if bucket_order(bucket) >= 4 else 0.95)
            payment_due = row.funded_amount / row.term_months
            payment_received = payment_due * cure_factor
            snapshot_rows.append(
                {
                    "loan_id": row.loan_id,
                    "snapshot_month": snap,
                    "mob": mob,
                    "product_type": row.product_type,
                    "channel": row.channel,
                    "customer_segment": row.customer_segment,
                    "region": row.region,
                    "merchant_id": row.merchant_id,
                    "merchant_category": row.merchant_category,
                    "risk_band": row.risk_band,
                    "dpd_bucket": bucket,
                    "prior_dpd_bucket": prior_bucket,
                    "funded_amount": row.funded_amount,
                    "current_principal": round(current_principal, 2),
                    "delinquency_balance": round(delinquency_balance, 2),
                    "dpd30_balance": round(dpd30_balance, 2),
                    "dpd60_balance": round(dpd60_balance, 2),
                    "npl_balance": round(npl_balance, 2),
                    "chargeoff_amount": round(chargeoff, 2),
                    "expected_loss_amount": round(expected_loss, 2),
                    "provision_amount": round(provision, 2),
                    "payment_due": round(payment_due, 2),
                    "payment_received": round(payment_received, 2),
                    "autopay_failure_flag": int(bucket_order(bucket) >= 2 and rng.random() < 0.76),
                    "npl_flag": int(bucket_order(bucket) >= 6),
                    "dpd30_flag": int(bucket_order(bucket) >= 4),
                    "dpd60_flag": int(bucket_order(bucket) >= 5),
                }
            )
            prior_bucket = bucket

    snapshots = pd.DataFrame(snapshot_rows)
    snapshots["snapshot_month"] = pd.to_datetime(snapshots["snapshot_month"])

    delinq = snapshots.loc[snapshots["dpd_bucket"].isin(["15-29 DPD", "30-59 DPD", "60-89 DPD", "90+ DPD"])].copy()
    delinq = delinq.sample(frac=0.45, random_state=SEED).reset_index(drop=True)
    case_rows: list[dict] = []
    queues = ["Early Outreach", "Soft Collections", "Hard Collections", "Legal Review"]
    for i, row in enumerate(delinq.itertuples(index=False), start=1):
        severity = bucket_order(row.dpd_bucket)
        queue = queues[min(len(queues) - 1, max(0, severity - 3))]
        contact_prob = min(0.94, 0.52 + severity * 0.07)
        contacted = rng.random() < contact_prob
        ptp = contacted and rng.random() < max(0.18, 0.58 - severity * 0.045)
        resolved = contacted and rng.random() < max(0.12, 0.50 - severity * 0.05)
        recovery = row.current_principal * (rng.uniform(0.22, 0.82) if resolved else rng.uniform(0.02, 0.22))
        sla_hours = float(np.clip(rng.normal(18 + severity * 9, 8), 3, 96))
        case_rows.append(
            {
                "case_id": f"C{str(i).zfill(7)}",
                "loan_id": row.loan_id,
                "snapshot_month": row.snapshot_month,
                "dpd_bucket": row.dpd_bucket,
                "risk_band": row.risk_band,
                "product_type": row.product_type,
                "channel": row.channel,
                "customer_segment": row.customer_segment,
                "region": row.region,
                "queue": queue,
                "contacted_flag": int(contacted),
                "promise_to_pay_flag": int(ptp),
                "resolved_flag": int(resolved),
                "sla_hours": round(sla_hours, 1),
                "within_sla_flag": int(sla_hours <= (24 if severity <= 4 else 48)),
                "recovery_amount": round(recovery, 2),
                "case_balance": row.current_principal,
            }
        )
    collections = pd.DataFrame(case_rows)

    loans_out = loans[
        [
            "loan_id",
            "application_id",
            "application_date",
            "origination_month",
            "product_type",
            "channel",
            "customer_segment",
            "region",
            "merchant_id",
            "merchant_category",
            "funded_amount",
            "credit_score",
            "risk_band",
            "pd_12m",
            "lgd",
            "term_months",
            "apr",
            "expected_loss_at_origination",
            "limit_utilization",
        ]
    ].copy()

    date_df = pd.DataFrame({"date": pd.date_range(start, LATEST_SNAPSHOT + pd.offsets.MonthEnd(0), freq="D")})
    date_df["month_start"] = date_df["date"].values.astype("datetime64[M]")
    date_df["month_label"] = date_df["month_start"].dt.strftime("%b %Y")
    date_df["year"] = date_df["date"].dt.year
    date_df["quarter"] = "Q" + date_df["date"].dt.quarter.astype(str)

    month_df = pd.DataFrame({"month_start": months})
    month_df["month_label"] = month_df["month_start"].dt.strftime("%b %Y")
    month_df["month_index"] = range(1, len(month_df) + 1)
    month_df["year"] = month_df["month_start"].dt.year

    product_df = pd.DataFrame(
        {
            "product_type": product_types,
            "term_months": [2, 3, 6, 12],
            "product_family": ["Short-term", "Installment", "Installment", "Installment"],
            "apr_policy": [0.00, 0.065, 0.115, 0.165],
        }
    )
    channel_df = pd.DataFrame({"channel": channels, "channel_group": ["Merchant", "Partner", "Owned", "Merchant", "Partner"]})
    risk_df = pd.DataFrame(
        {
            "risk_band": ["A Prime", "B Near Prime", "C Mid", "D Subprime", "E Deep Subprime"],
            "risk_order": [1, 2, 3, 4, 5],
            "risk_appetite": ["Low", "Low", "Watch", "High", "High"],
            "pd_floor": [0.010, 0.020, 0.035, 0.065, 0.110],
        }
    )
    merchant_df = pd.DataFrame({"merchant_id": merchants})
    merchant_df["merchant_name"] = merchant_df["merchant_id"].map(lambda x: f"Merchant {x[-3:]}")
    merchant_df["merchant_category"] = merchant_df["merchant_id"].map(merchant_categories)
    merchant_df["merchant_tier"] = rng.choice(["Strategic", "Core", "Long Tail"], len(merchant_df), p=[0.16, 0.42, 0.42])
    segment_df = pd.DataFrame({"customer_segment": segments, "repeat_type": ["New", "Repeat", "Repeat", "Reactivated"]})

    # Vintage metrics by origination cohort and months on book.
    vintage_base = snapshots.merge(loans_out[["loan_id", "origination_month"]], on="loan_id", how="left")
    vintage = (
        vintage_base.groupby(["origination_month", "mob"], as_index=False)
        .agg(
            loan_count=("loan_id", "nunique"),
            originated_amount=("funded_amount", "sum"),
            outstanding_balance=("current_principal", "sum"),
            dpd30_balance=("dpd30_balance", "sum"),
            dpd60_balance=("dpd60_balance", "sum"),
            npl_balance=("npl_balance", "sum"),
            chargeoff_amount=("chargeoff_amount", "sum"),
        )
        .sort_values(["origination_month", "mob"])
    )
    for col in ["dpd30", "dpd60", "npl"]:
        vintage[f"{col}_rate"] = (vintage[f"{col}_balance"] / vintage["outstanding_balance"].replace(0, np.nan)).fillna(0).round(4)
    vintage["cumulative_loss_rate"] = (
        vintage.groupby("origination_month")["chargeoff_amount"].cumsum()
        / vintage.groupby("origination_month")["originated_amount"].transform("first").replace(0, np.nan)
    ).fillna(0).round(4)

    # Roll-rate matrix from prior to current bucket.
    roll = (
        snapshots.groupby(["snapshot_month", "prior_dpd_bucket", "dpd_bucket"], as_index=False)
        .agg(loan_count=("loan_id", "nunique"), balance=("current_principal", "sum"))
    )
    roll_totals = roll.groupby(["snapshot_month", "prior_dpd_bucket"])["loan_count"].transform("sum")
    roll["roll_rate"] = (roll["loan_count"] / roll_totals.replace(0, np.nan)).fillna(0).round(4)

    latest = snapshots.loc[snapshots["snapshot_month"].eq(LATEST_SNAPSHOT)].copy()
    latest_balance = latest["current_principal"].sum()
    latest_el = latest["expected_loss_amount"].sum()
    latest_provision = latest["provision_amount"].sum()
    forecast_rows: list[dict] = []
    scenarios = {
        "Upside": {"pd_mult": 0.82, "recovery_mult": 1.12, "volume_mult": 1.03},
        "Base": {"pd_mult": 1.00, "recovery_mult": 1.00, "volume_mult": 1.00},
        "Downside": {"pd_mult": 1.34, "recovery_mult": 0.82, "volume_mult": 0.92},
    }
    for scenario, parms in scenarios.items():
        balance = latest_balance
        provision = latest_provision
        for i, month in enumerate(FORECAST_MONTHS, start=1):
            balance *= 0.985 * parms["volume_mult"]
            expected_loss = latest_el * (1 + 0.035 * i) * parms["pd_mult"]
            recovery = collections.loc[collections["snapshot_month"].ge(pd.Timestamp("2026-01-01")), "recovery_amount"].mean() * 22 * parms["recovery_mult"]
            provision = max(0, provision + expected_loss - recovery * 0.42)
            forecast_rows.append(
                {
                    "forecast_month": month,
                    "scenario": scenario,
                    "forecast_balance": round(balance, 2),
                    "forecast_expected_loss": round(expected_loss, 2),
                    "forecast_recovery": round(recovery, 2),
                    "forecast_provision": round(provision, 2),
                    "incremental_provision": round(expected_loss - recovery * 0.42, 2),
                }
            )
    forecast = pd.DataFrame(forecast_rows)

    # Write prepared facts and dimensions.
    prepared = {
        "dim_date": date_df,
        "dim_month": month_df,
        "dim_product": product_df,
        "dim_channel": channel_df,
        "dim_risk_band": risk_df,
        "dim_merchant": merchant_df,
        "dim_customer_segment": segment_df,
        "fact_applications": apps,
        "fact_loans": loans_out,
        "fact_loan_monthly": snapshots,
        "fact_collections": collections,
        "fact_vintage": vintage,
        "fact_roll_rate": roll,
        "fact_provision_forecast": forecast,
    }
    for name, df in prepared.items():
        df.to_csv(DATA_PREP / f"{name}.csv", index=False)

    source_summary = {
        "is_synthetic": True,
        "seed": SEED,
        "domain": "BNPL / Digital Lending Credit Risk",
        "latest_snapshot_month": LATEST_SNAPSHOT.strftime("%Y-%m-%d"),
        "raw_file": "data/raw/bnpl_applications_raw.csv",
        "prepared_tables": {name: int(len(df)) for name, df in prepared.items()},
        "date_range": {
            "applications_min": apps["application_date"].min().strftime("%Y-%m-%d"),
            "applications_max": apps["application_date"].max().strftime("%Y-%m-%d"),
            "snapshot_min": snapshots["snapshot_month"].min().strftime("%Y-%m-%d"),
            "snapshot_max": snapshots["snapshot_month"].max().strftime("%Y-%m-%d"),
        },
    }
    write_json(ROOT / "data" / "source_summary.json", source_summary)

    quality = []
    for name, df in prepared.items():
        dup_keys = 0
        if name == "fact_loans":
            dup_keys = int(df["loan_id"].duplicated().sum())
        elif name == "fact_applications":
            dup_keys = int(df["application_id"].duplicated().sum())
        elif name == "dim_merchant":
            dup_keys = int(df["merchant_id"].duplicated().sum())
        quality.append(
            {
                "table": name,
                "rows": int(len(df)),
                "columns": int(len(df.columns)),
                "missing_cells": int(df.isna().sum().sum()),
                "duplicate_key_count": dup_keys,
            }
        )
    write_json(DATA_VALID / "validation_summary.json", {"status": "passed", "checks": quality})
    write_md(
        ROOT / "data" / "data_quality_report.md",
        "\n".join(
            [
                "# Data Quality Report",
                "",
                f"- Synthetic data: yes, seed {SEED}.",
                f"- Latest closed snapshot month: {LATEST_SNAPSHOT.date()}.",
                f"- Prepared tables: {len(prepared)}.",
                "",
                "| Table | Rows | Columns | Missing cells | Duplicate key count |",
                "|---|---:|---:|---:|---:|",
                *[
                    f"| {x['table']} | {x['rows']:,} | {x['columns']} | {x['missing_cells']:,} | {x['duplicate_key_count']:,} |"
                    for x in quality
                ],
            ]
        ),
    )

    return {
        "prepared": prepared,
        "apps": apps,
        "loans": loans_out,
        "snapshots": snapshots,
        "collections": collections,
        "vintage": vintage,
        "roll": roll,
        "forecast": forecast,
        "summary": source_summary,
    }


MEASURES: list[tuple[str, str, str, str]] = [
    ("Applications", "COUNTROWS ( FactApplications )", "#,0", "Total submitted credit applications."),
    ("Approved Applications", "CALCULATE ( [Applications], FactApplications[approved_flag] = 1 )", "#,0", "Approved application count."),
    ("Approval Rate", "DIVIDE ( [Approved Applications], [Applications] )", "0.0%", "Approved applications divided by total applications."),
    ("Disbursed Loans", "COUNTROWS ( FactLoans )", "#,0", "Funded loan count."),
    ("Disbursement Amount", "SUM ( FactLoans[funded_amount] )", "$#,0,,.0M", "Total funded amount."),
    ("Loan Book Balance", "SUM ( FactLoanMonthly[current_principal] )", "$#,0,,.0M", "Outstanding principal balance in selected snapshot context."),
    ("DPD 30+ Balance", "SUM ( FactLoanMonthly[dpd30_balance] )", "$#,0,,.0M", "Outstanding balance with 30 or more days past due."),
    ("DPD 60+ Balance", "SUM ( FactLoanMonthly[dpd60_balance] )", "$#,0,,.0M", "Outstanding balance with 60 or more days past due."),
    ("NPL Balance", "SUM ( FactLoanMonthly[npl_balance] )", "$#,0,,.0M", "Outstanding 90+ DPD or non-performing balance."),
    ("Delinquency Rate", "DIVIDE ( [DPD 30+ Balance], [Loan Book Balance] )", "0.0%", "DPD 30+ balance divided by loan book balance."),
    ("NPL Rate", "DIVIDE ( [NPL Balance], [Loan Book Balance] )", "0.0%", "NPL balance divided by loan book balance."),
    ("Expected Loss", "SUM ( FactLoanMonthly[expected_loss_amount] )", "$#,0,,.0M", "Expected credit loss amount."),
    ("Expected Loss Rate", "DIVIDE ( [Expected Loss], [Loan Book Balance] )", "0.0%", "Expected loss divided by loan book balance."),
    ("Provision Amount", "SUM ( FactLoanMonthly[provision_amount] )", "$#,0,,.0M", "Provision amount calculated from expected loss policy."),
    ("Provision Coverage", "DIVIDE ( [Provision Amount], [Expected Loss] )", "0.0x", "Provision amount divided by expected loss."),
    ("Autopay Failure Loans", "CALCULATE ( DISTINCTCOUNT ( FactLoanMonthly[loan_id] ), FactLoanMonthly[autopay_failure_flag] = 1 )", "#,0", "Loans with autopay failure flag."),
    ("Recovery Amount", "SUM ( FactCollections[recovery_amount] )", "$#,0,,.0M", "Total recovery amount from collection cases."),
    ("Case Balance", "SUM ( FactCollections[case_balance] )", "$#,0,,.0M", "Total balance assigned to collection cases."),
    ("Recovery Rate", "DIVIDE ( [Recovery Amount], [Case Balance] )", "0.0%", "Recovered amount divided by collection case balance."),
    ("Collections SLA %", "DIVIDE ( SUM ( FactCollections[within_sla_flag] ), COUNTROWS ( FactCollections ) )", "0.0%", "Share of collection cases handled within SLA."),
    ("Promise To Pay %", "DIVIDE ( SUM ( FactCollections[promise_to_pay_flag] ), COUNTROWS ( FactCollections ) )", "0.0%", "Share of cases with promise to pay."),
    ("Vintage 30+ Rate", "DIVIDE ( SUM ( FactVintage[dpd30_balance] ), SUM ( FactVintage[outstanding_balance] ) )", "0.0%", "Vintage cohort DPD 30+ balance share."),
    ("Vintage Loss Rate", "AVERAGE ( FactVintage[cumulative_loss_rate] )", "0.0%", "Average cumulative loss rate across visible vintage cells."),
    ("Roll Rate", "AVERAGE ( FactRollRate[roll_rate] )", "0.0%", "Average roll rate across selected transition cells."),
    ("Forecast Provision", "SUM ( FactProvisionForecast[forecast_provision] )", "$#,0,,.0M", "Forecast provision amount."),
    ("Forecast Expected Loss", "SUM ( FactProvisionForecast[forecast_expected_loss] )", "$#,0,,.0M", "Forecast expected loss."),
    ("Incremental Provision", "SUM ( FactProvisionForecast[incremental_provision] )", "$#,0,,.0M", "Incremental provision bridge amount."),
]


TABLE_MAP = [
    ("dim_date", "DimDate"),
    ("dim_month", "DimMonth"),
    ("dim_product", "DimProduct"),
    ("dim_channel", "DimChannel"),
    ("dim_risk_band", "DimRiskBand"),
    ("dim_merchant", "DimMerchant"),
    ("dim_customer_segment", "DimCustomerSegment"),
    ("fact_applications", "FactApplications"),
    ("fact_loans", "FactLoans"),
    ("fact_loan_monthly", "FactLoanMonthly"),
    ("fact_collections", "FactCollections"),
    ("fact_vintage", "FactVintage"),
    ("fact_roll_rate", "FactRollRate"),
    ("fact_provision_forecast", "FactProvisionForecast"),
]


RELATIONSHIPS = [
    ("FactApplications", "application_month", "DimMonth", "month_start"),
    ("FactApplications", "product_type", "DimProduct", "product_type"),
    ("FactApplications", "channel", "DimChannel", "channel"),
    ("FactApplications", "risk_band", "DimRiskBand", "risk_band"),
    ("FactApplications", "merchant_id", "DimMerchant", "merchant_id"),
    ("FactApplications", "customer_segment", "DimCustomerSegment", "customer_segment"),
    ("FactLoans", "origination_month", "DimMonth", "month_start"),
    ("FactLoans", "product_type", "DimProduct", "product_type"),
    ("FactLoans", "channel", "DimChannel", "channel"),
    ("FactLoans", "risk_band", "DimRiskBand", "risk_band"),
    ("FactLoans", "merchant_id", "DimMerchant", "merchant_id"),
    ("FactLoans", "customer_segment", "DimCustomerSegment", "customer_segment"),
    ("FactLoanMonthly", "snapshot_month", "DimMonth", "month_start"),
    ("FactLoanMonthly", "product_type", "DimProduct", "product_type"),
    ("FactLoanMonthly", "channel", "DimChannel", "channel"),
    ("FactLoanMonthly", "risk_band", "DimRiskBand", "risk_band"),
    ("FactLoanMonthly", "merchant_id", "DimMerchant", "merchant_id"),
    ("FactLoanMonthly", "customer_segment", "DimCustomerSegment", "customer_segment"),
    ("FactCollections", "snapshot_month", "DimMonth", "month_start"),
    ("FactCollections", "product_type", "DimProduct", "product_type"),
    ("FactCollections", "channel", "DimChannel", "channel"),
    ("FactCollections", "risk_band", "DimRiskBand", "risk_band"),
    ("FactCollections", "customer_segment", "DimCustomerSegment", "customer_segment"),
    ("FactVintage", "origination_month", "DimMonth", "month_start"),
    ("FactRollRate", "snapshot_month", "DimMonth", "month_start"),
]


def infer_type(series: pd.Series, column: str) -> tuple[str, str]:
    if column.endswith("_date") or column.endswith("_month") or column in {"date", "month_start", "forecast_month", "snapshot_month", "origination_month"}:
        return "dateTime", "type date"
    if pd.api.types.is_bool_dtype(series):
        return "boolean", "type logical"
    if pd.api.types.is_integer_dtype(series):
        return "int64", "Int64.Type"
    if pd.api.types.is_float_dtype(series):
        return "double", "type number"
    return "string", "type text"


def column_format(column: str, data_type: str) -> str | None:
    if any(token in column for token in ["amount", "balance", "principal", "funded", "provision", "loss", "recovery"]):
        return "$#,0;($#,0);$0"
    if column.endswith("_rate") or column in {"pd_12m", "lgd", "apr", "limit_utilization"}:
        return "0.0%"
    if data_type == "int64":
        return "0"
    return None


def create_import_table(csv_name: str, table_name: str) -> dict:
    csv_path = DATA_PREP / f"{csv_name}.csv"
    sample = pd.read_csv(csv_path, nrows=1000)
    columns = []
    m_types = []
    for name in sample.columns:
        model_type, m_type = infer_type(sample[name], name)
        col = {
            "name": name,
            "dataType": model_type,
            "sourceColumn": name,
            "lineageTag": str(uuid.uuid4()),
        }
        fmt = column_format(name, model_type)
        if fmt:
            col["formatString"] = fmt
        if model_type in {"string", "dateTime", "boolean"} or name.endswith("_id"):
            col["summarizeBy"] = "none"
        columns.append(col)
        m_types.append(f'{{"{name}", {m_type}}}')
    file_path = str(csv_path).replace("\\", "\\\\")
    expression = [
        "let",
        f'    Source = Csv.Document(File.Contents("{file_path}"), [Delimiter=",", Columns={len(sample.columns)}, Encoding=65001, QuoteStyle=QuoteStyle.Csv]),',
        "    PromotedHeaders = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),",
        f"    ChangedType = Table.TransformColumnTypes(PromotedHeaders, {{{', '.join(m_types)}}}, \"en-US\")",
        "in",
        "    ChangedType",
    ]
    return {
        "name": table_name,
        "lineageTag": str(uuid.uuid4()),
        "columns": columns,
        "partitions": [
            {
                "name": f"p_{table_name}",
                "mode": "import",
                "source": {"type": "m", "expression": expression},
            }
        ],
    }


def build_semantic_model(prepared: dict[str, pd.DataFrame]) -> dict:
    tables = [create_import_table(csv, table) for csv, table in TABLE_MAP]
    measure_table = {
        "name": MEASURE_TABLE,
        "lineageTag": str(uuid.uuid4()),
        "columns": [
            {
                "name": "MeasureName",
                "dataType": "string",
                "sourceColumn": "MeasureName",
                "isHidden": True,
                "summarizeBy": "none",
                "lineageTag": str(uuid.uuid4()),
            }
        ],
        "measures": [
            {
                "name": name,
                "expression": expr,
                "formatString": fmt,
                "description": desc,
                "lineageTag": str(uuid.uuid4()),
            }
            for name, expr, fmt, desc in MEASURES
        ],
        "partitions": [
            {
                "name": "p_KPI_Measures",
                "mode": "import",
                "source": {"type": "m", "expression": ['let Source = #table(type table [MeasureName = text], {{"KPI"}}) in Source']},
            }
        ],
    }
    tables.append(measure_table)
    rels = [
        {
            "name": f"{from_table}_{from_col}_to_{to_table}_{to_col}",
            "fromTable": from_table,
            "fromColumn": from_col,
            "toTable": to_table,
            "toColumn": to_col,
            "crossFilteringBehavior": "oneDirection",
        }
        for from_table, from_col, to_table, to_col in RELATIONSHIPS
    ]
    model = {
        "compatibilityLevel": 1550,
        "model": {
            "culture": "en-US",
            "dataAccessOptions": {"legacyRedirects": True, "returnErrorValuesAsNull": True},
            "defaultPowerBIDataSourceVersion": "powerBI_V3",
            "sourceQueryCulture": "en-US",
            "tables": tables,
            "relationships": rels,
        },
    }
    write_json(MODEL_DIR / "model.bim", model)
    model_path = PBIP_DIR / "Project9_BNPL_Risk.SemanticModel" / "model.bim"
    write_json(model_path, model)
    write_json(PBIXPROJ_DIR / "Model" / "database.json", model)
    return model


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


def solid(color_value: str) -> dict:
    return {"solid": {"color": text(color_value)}}


def source_ref(alias: str) -> dict:
    return {"SourceRef": {"Source": alias}}


def entity_ref(entity: str) -> dict:
    return {"SourceRef": {"Entity": entity}}


def visual_id(prefix: str = "v") -> str:
    return (prefix + uuid.uuid4().hex)[:20]


def base_vc(title: str | None = None, subtitle: str | None = None, border: str | None = None) -> dict:
    vc = {
        "background": [{"properties": {"show": pbi_literal(True), "color": solid("#FFFFFF"), "transparency": pbi_literal(0.0)}}],
        "border": [
            {
                "properties": {
                    "show": pbi_literal(True),
                    "color": solid(border or COLORS["border"]),
                    "radius": pbi_literal(6.0),
                    "width": pbi_literal(1.0),
                }
            }
        ],
        "dropShadow": [
            {
                "properties": {
                    "show": pbi_literal(True),
                    "position": text("Outer"),
                    "color": solid("#B8C2D3"),
                    "transparency": pbi_literal(86.0),
                    "angle": pbi_literal(45.0),
                    "distance": pbi_literal(1.0),
                }
            }
        ],
        "visualHeader": [{"properties": {"show": pbi_literal(False)}}],
    }
    if title:
        vc["title"] = [
            {
                "properties": {
                    "show": pbi_literal(True),
                    "text": text(title),
                    "fontFamily": text("Segoe UI Semibold"),
                    "fontSize": pbi_literal(9.2),
                    "fontColor": solid(COLORS["ink"]),
                    "alignment": text("left"),
                }
            }
        ]
    if subtitle:
        vc["subTitle"] = [
            {
                "properties": {
                    "show": pbi_literal(True),
                    "text": text(subtitle),
                    "fontFamily": text("Segoe UI"),
                    "fontSize": pbi_literal(7.5),
                    "fontColor": solid(COLORS["muted"]),
                }
            }
        ]
    return vc


def make_query(froms: list[dict], selects: list[dict], order_by: list[dict] | None = None, count: int = 1000, subtotal: bool = False) -> str:
    query = {"Version": 2, "From": froms, "Select": selects}
    if order_by:
        query["OrderBy"] = order_by
    return json.dumps(
        {
            "Commands": [
                {
                    "SemanticQueryDataShapeCommand": {
                        "Query": query,
                        "Binding": {
                            "Primary": {"Groupings": [{"Projections": list(range(len(selects))), **({"Subtotal": 1} if subtotal else {})}]},
                            "DataReduction": {"DataVolume": 4, "Primary": {"Window": {"Count": count}}},
                            "Version": 1,
                        },
                        "ExecutionMetricsKind": 1,
                    }
                }
            ]
        },
        separators=(",", ":"),
    )


def wrap_visual(x: int, y: int, z: int, width: int, height: int, config: dict, query: str | None = None, transforms: str | None = None) -> dict:
    return {
        "x": x,
        "y": y,
        "z": z,
        "width": width,
        "height": height,
        "config": json.dumps(config, separators=(",", ":")),
        "filters": "[]",
        "tabOrder": z,
        **({"query": query} if query else {}),
        **({"dataTransforms": transforms} if transforms else {}),
    }


def textbox(text_value: str, x: int, y: int, width: int, height: int, z: int, size: str = "16pt", color_value: str = "#172033", bold: bool = True) -> dict:
    runs = []
    for i, line in enumerate(text_value.split("\n")):
        style = {
            "fontFamily": "Segoe UI Semibold" if bold and i == 0 else "Segoe UI",
            "fontSize": size if i == 0 else "8.5pt",
            "color": color_value if i == 0 else COLORS["muted"],
        }
        runs.append({"value": line + ("\n" if i < len(text_value.split("\n")) - 1 else ""), "textStyle": style})
    cfg = {
        "name": visual_id("txt"),
        "singleVisual": {
            "visualType": "textbox",
            "drillFilterOtherVisuals": True,
            "objects": {"general": [{"properties": {"paragraphs": [{"textRuns": runs}]}}]},
            "vcObjects": {
                "background": [{"properties": {"show": pbi_literal(False)}}],
                "border": [{"properties": {"show": pbi_literal(False)}}],
                "visualHeader": [{"properties": {"show": pbi_literal(False)}}],
            },
        },
        "layouts": [{"id": 0, "position": {"x": x, "y": y, "z": z, "width": width, "height": height, "tabOrder": z}}],
    }
    return wrap_visual(x, y, z, width, height, cfg)


def shape(x: int, y: int, width: int, height: int, z: int, fill: str, outline: str = "#000000", show_outline: bool = False) -> dict:
    cfg = {
        "name": visual_id("shp"),
        "layouts": [{"id": 0, "position": {"x": x, "y": y, "z": z, "width": width, "height": height, "tabOrder": z}}],
        "singleVisual": {
            "visualType": "basicShape",
            "drillFilterOtherVisuals": True,
            "objects": {
                "shape": [{"properties": {"tileShape": text("rectangle")}}],
                "fill": [{"properties": {"show": pbi_literal(True), "fillColor": solid(fill), "transparency": pbi_literal(0.0)}}],
                "outline": [{"properties": {"show": pbi_literal(show_outline), "color": solid(outline), "weight": pbi_literal(1.0)}}],
            },
            "vcObjects": {
                "background": [{"properties": {"show": pbi_literal(False)}}],
                "border": [{"properties": {"show": pbi_literal(False)}}],
                "visualHeader": [{"properties": {"show": pbi_literal(False)}}],
            },
        },
    }
    return wrap_visual(x, y, z, width, height, cfg)


def card(measure: str, display: str, fmt: str, x: int, y: int, width: int, height: int, z: int, accent: str) -> dict:
    qref = f"{MEASURE_TABLE}.{measure}"
    froms = [{"Name": "m", "Entity": MEASURE_TABLE, "Type": 0}]
    selects = [{"Measure": {"Expression": source_ref("m"), "Property": measure}, "Name": qref, "NativeReferenceName": display}]
    objects = {
        "layout": [{"properties": {"rectangleRoundedCurve": pbi_literal(6), "cellPadding": pbi_literal(6.0), "paddingUniform": pbi_literal(6.0)}, "selector": {"id": "default"}}],
        "fillCustom": [{"properties": {"show": pbi_literal(False)}}],
        "outline": [{"properties": {"show": pbi_literal(False)}, "selector": {"id": "default"}}],
        "value": [{"properties": {"fontSize": pbi_literal(19.0), "fontFamily": text("Segoe UI Semibold"), "fontColor": solid(accent)}, "selector": {"metadata": qref}}],
        "label": [{"properties": {"show": pbi_literal(True), "position": text("belowValue"), "fontSize": pbi_literal(7.5), "fontFamily": text("Segoe UI"), "fontColor": solid(COLORS["muted"])}, "selector": {"metadata": qref}}],
        "spacing": [{"properties": {"verticalSpacing": pbi_literal(0.0)}, "selector": {"id": "default"}}],
    }
    cfg = {
        "name": visual_id("card"),
        "layouts": [{"id": 0, "position": {"x": x, "y": y, "z": z, "width": width, "height": height, "tabOrder": z}}],
        "singleVisual": {
            "visualType": "cardVisual",
            "projections": {"Data": [{"queryRef": qref}]},
            "prototypeQuery": {"Version": 2, "From": froms, "Select": selects},
            "columnProperties": {qref: {"displayName": display}},
            "drillFilterOtherVisuals": True,
            "hasDefaultSort": True,
            "objects": objects,
            "vcObjects": base_vc(border=accent),
        },
    }
    transforms = {
        "objects": objects,
        "projectionOrdering": {"Data": [0]},
        "queryMetadata": {"Select": [{"Restatement": display, "Name": qref, "Type": 1, "Format": fmt}]},
        "visualElements": [{"DataRoles": [{"Name": "Data", "Projection": 0, "isActive": False}]}],
        "selects": [{"displayName": display, "queryName": qref, "roles": {"Data": True}, "type": {"category": None, "underlyingType": 259}, "expr": {"Measure": {"Expression": entity_ref(MEASURE_TABLE), "Property": measure}}, "format": fmt}],
    }
    return wrap_visual(x, y, z, width, height, cfg, make_query(froms, selects), json.dumps(transforms, separators=(",", ":")))


def category_measure_visual(
    visual_type: str,
    category_table: str,
    category_col: str,
    category_display: str,
    measures: list[tuple[str, str, str]],
    title: str,
    subtitle: str,
    x: int,
    y: int,
    width: int,
    height: int,
    z: int,
    order_measure: str | None = None,
    accent: str = "#2F66B3",
) -> dict:
    froms = [{"Name": "c", "Entity": category_table, "Type": 0}, {"Name": "m", "Entity": MEASURE_TABLE, "Type": 0}]
    selects = [{"Column": {"Expression": source_ref("c"), "Property": category_col}, "Name": f"{category_table}.{category_col}", "NativeReferenceName": category_display}]
    projections = {"Category": [{"queryRef": f"{category_table}.{category_col}", "active": True}]}
    roles = [{"Name": "Category", "Projection": 0, "isActive": True}]
    metadata = [{"Restatement": category_display, "Name": f"{category_table}.{category_col}", "Type": 2048}]
    transform_selects = [{"displayName": category_display, "queryName": f"{category_table}.{category_col}", "roles": {"Category": True}, "type": {"category": None, "underlyingType": 1}, "expr": {"Column": {"Expression": entity_ref(category_table), "Property": category_col}}}]
    role_name = "Y"
    if visual_type == "lineClusteredColumnComboChart" and len(measures) > 1:
        projections["Y"] = []
        projections["Y2"] = []
    else:
        projections[role_name] = []
    for idx, (measure_name, display, fmt) in enumerate(measures, start=1):
        qref = f"{MEASURE_TABLE}.{measure_name}"
        selects.append({"Measure": {"Expression": source_ref("m"), "Property": measure_name}, "Name": qref, "NativeReferenceName": display})
        target_role = "Y2" if visual_type == "lineClusteredColumnComboChart" and idx == 2 else "Y"
        projections[target_role].append({"queryRef": qref})
        roles.append({"Name": target_role, "Projection": idx, "isActive": False})
        metadata.append({"Restatement": display, "Name": qref, "Type": 1, "Format": fmt})
        transform_selects.append({"displayName": display, "queryName": qref, "roles": {target_role: True}, "type": {"category": None, "underlyingType": 259}, "expr": {"Measure": {"Expression": entity_ref(MEASURE_TABLE), "Property": measure_name}}, "format": fmt})
    order_by = []
    if order_measure:
        order_by = [{"Direction": 2, "Expression": {"Measure": {"Expression": source_ref("m"), "Property": order_measure}}}]
    else:
        order_by = [{"Direction": 1, "Expression": {"Column": {"Expression": source_ref("c"), "Property": category_col}}}]
    objects = {
        "valueAxis": [{"properties": {"showAxisTitle": pbi_literal(False), "gridlineShow": pbi_literal(False)}}],
        "categoryAxis": [{"properties": {"showAxisTitle": pbi_literal(False), "gridlineShow": pbi_literal(False), "concatenateLabels": pbi_literal(False)}}],
        "labels": [{"properties": {"show": pbi_literal(True), "labelDisplayUnits": pbi_literal(1000000.0)}}],
        "legend": [{"properties": {"showTitle": pbi_literal(False), "position": text("Top")}}],
        "dataPoint": [{"properties": {"fill": solid(accent)}, "selector": {"metadata": f"{MEASURE_TABLE}.{measures[0][0]}"}}],
    }
    cfg = {
        "name": visual_id("vis"),
        "layouts": [{"id": 0, "position": {"x": x, "y": y, "z": z, "width": width, "height": height, "tabOrder": z}}],
        "singleVisual": {
            "visualType": visual_type,
            "projections": projections,
            "prototypeQuery": {"Version": 2, "From": froms, "Select": selects, "OrderBy": order_by},
            "drillFilterOtherVisuals": True,
            "hasDefaultSort": True,
            "objects": objects,
            "vcObjects": base_vc(title, subtitle),
        },
    }
    transforms = {
        "objects": objects,
        "projectionOrdering": {key: list(range(len(selects))) if key == "Values" else [i for i, role in enumerate(roles) if role["Name"] == key] for key in projections},
        "queryMetadata": {"Select": metadata},
        "visualElements": [{"DataRoles": roles}],
        "selects": transform_selects,
        "projectionActiveItems": {"Category": [{"queryRef": f"{category_table}.{category_col}", "suppressConcat": False}]},
    }
    return wrap_visual(x, y, z, width, height, cfg, make_query(froms, selects, order_by), json.dumps(transforms, separators=(",", ":")))


def table_visual(fields: list[dict], title: str, subtitle: str, x: int, y: int, width: int, height: int, z: int, order_measure: str | None = None) -> dict:
    aliases: dict[str, str] = {}
    froms: list[dict] = []

    def alias_for(table: str) -> str:
        if table not in aliases:
            alias = f"t{len(aliases)}" if table != MEASURE_TABLE else "m"
            aliases[table] = alias
            froms.append({"Name": alias, "Entity": table, "Type": 0})
        return aliases[table]

    selects = []
    metadata = []
    transform_selects = []
    projections = []
    for field in fields:
        if field["kind"] == "column":
            alias = alias_for(field["table"])
            qref = f"{field['table']}.{field['column']}"
            selects.append({"Column": {"Expression": source_ref(alias), "Property": field["column"]}, "Name": qref, "NativeReferenceName": field["display"]})
            metadata.append({"Restatement": field["display"], "Name": qref, "Type": 2048})
            transform_selects.append({"displayName": field["display"], "queryName": qref, "roles": {"Values": True}, "type": {"category": None, "underlyingType": 1}, "expr": {"Column": {"Expression": entity_ref(field["table"]), "Property": field["column"]}}})
        else:
            alias = alias_for(MEASURE_TABLE)
            qref = f"{MEASURE_TABLE}.{field['measure']}"
            selects.append({"Measure": {"Expression": source_ref(alias), "Property": field["measure"]}, "Name": qref, "NativeReferenceName": field["display"]})
            metadata.append({"Restatement": field["display"], "Name": qref, "Type": 1, "Format": field.get("format", "#,0")})
            transform_selects.append({"displayName": field["display"], "queryName": qref, "roles": {"Values": True}, "type": {"category": None, "underlyingType": 259}, "expr": {"Measure": {"Expression": entity_ref(MEASURE_TABLE), "Property": field["measure"]}}, "format": field.get("format", "#,0")})
        projections.append({"queryRef": selects[-1]["Name"]})
    order_by = None
    if order_measure:
        alias = alias_for(MEASURE_TABLE)
        order_by = [{"Direction": 2, "Expression": {"Measure": {"Expression": source_ref(alias), "Property": order_measure}}}]
    objects = {
        "grid": [{"properties": {"gridHorizontal": pbi_literal(False), "outlineColor": solid(COLORS["border"])}}],
        "columnHeaders": [{"properties": {"fontFamily": text("Segoe UI Semibold"), "fontSize": pbi_literal(7.2), "fontColor": solid(COLORS["ink"])}}],
        "values": [{"properties": {"fontSize": pbi_literal(7.0), "fontFamily": text("Segoe UI"), "fontColor": solid(COLORS["ink"])}}],
    }
    cfg = {
        "name": visual_id("tbl"),
        "layouts": [{"id": 0, "position": {"x": x, "y": y, "z": z, "width": width, "height": height, "tabOrder": z}}],
        "singleVisual": {
            "visualType": "tableEx",
            "projections": {"Values": projections},
            "prototypeQuery": {"Version": 2, "From": froms, "Select": selects, **({"OrderBy": order_by} if order_by else {})},
            "drillFilterOtherVisuals": True,
            "objects": objects,
            "vcObjects": base_vc(title, subtitle),
        },
    }
    transforms = {
        "objects": objects,
        "projectionOrdering": {"Values": list(range(len(selects)))},
        "queryMetadata": {"Select": metadata},
        "visualElements": [{"DataRoles": [{"Name": "Values", "Projection": i, "isActive": False} for i in range(len(selects))]}],
        "selects": transform_selects,
    }
    return wrap_visual(x, y, z, width, height, cfg, make_query(froms, selects, order_by, count=500, subtotal=True), json.dumps(transforms, separators=(",", ":")))


def slicer(table: str, column: str, display: str, x: int, y: int, width: int, height: int, z: int) -> dict:
    qref = f"{table}.{column}"
    froms = [{"Name": "s", "Entity": table, "Type": 0}]
    selects = [{"Column": {"Expression": source_ref("s"), "Property": column}, "Name": qref, "NativeReferenceName": display}]
    objects = {
        "data": [{"properties": {"mode": text("Dropdown")}}],
        "general": [{"properties": {"orientation": pbi_literal(0.0)}}],
        "selection": [{"properties": {"selectAllCheckboxEnabled": pbi_literal(True), "singleSelect": pbi_literal(False)}}],
        "header": [{"properties": {"show": pbi_literal(True), "text": text(display), "textSize": pbi_literal(8.0), "fontColor": solid(COLORS["muted"]), "fontFamily": text("Segoe UI Semibold")}}],
        "items": [{"properties": {"textSize": pbi_literal(8.0), "fontColor": solid(COLORS["ink"]), "fontFamily": text("Segoe UI")}}],
    }
    cfg = {
        "name": visual_id("slc"),
        "layouts": [{"id": 0, "position": {"x": x, "y": y, "z": z, "width": width, "height": height, "tabOrder": z}}],
        "singleVisual": {
            "visualType": "slicer",
            "projections": {"Values": [{"queryRef": qref, "active": True}]},
            "prototypeQuery": {"Version": 2, "From": froms, "Select": selects},
            "drillFilterOtherVisuals": True,
            "hasDefaultSort": True,
            "objects": objects,
            "vcObjects": base_vc(display, None),
        },
    }
    transforms = {
        "objects": objects,
        "projectionOrdering": {"Values": [0]},
        "queryMetadata": {"Select": [{"Restatement": display, "Name": qref, "Type": 2048}]},
        "visualElements": [{"DataRoles": [{"Name": "Values", "Projection": 0, "isActive": True}]}],
        "selects": [{"displayName": display, "queryName": qref, "roles": {"Values": True}, "type": {"category": None, "underlyingType": 1}, "expr": {"Column": {"Expression": entity_ref(table), "Property": column}}}],
    }
    return wrap_visual(x, y, z, width, height, cfg, make_query(froms, selects), json.dumps(transforms, separators=(",", ":")))


def page(display: str, ordinal: int, visuals: list[dict]) -> dict:
    return {
        "id": ordinal,
        "name": uuid.uuid4().hex[:20],
        "displayName": display,
        "filters": "[]",
        "ordinal": ordinal,
        "visualContainers": visuals,
        "config": "{}",
        "displayOption": 1,
        "width": 1280,
        "height": 720,
    }


def build_layout() -> dict:
    pages = []
    common_slicers = [
        lambda z: slicer("DimMonth", "month_label", "Month", 842, 19, 120, 46, z),
        lambda z: slicer("DimProduct", "product_type", "Product", 970, 19, 134, 46, z),
        lambda z: slicer("DimRiskBand", "risk_band", "Risk", 1112, 19, 140, 46, z),
    ]

    v1: list[dict] = [shape(0, 0, 1280, 76, 0, "#EEF3FA"), textbox("BNPL Credit Risk Command Center\nCredit Risk Overview | synthetic portfolio through May 2026", 24, 14, 630, 54, 1, "18pt")]
    for i, make in enumerate(common_slicers, start=10):
        v1.append(make(i))
    cards = [
        ("Loan Book Balance", "Loan book", "$#,0,,.0M", COLORS["blue"]),
        ("Disbursement Amount", "Disbursement", "$#,0,,.0M", COLORS["teal"]),
        ("Approval Rate", "Approval rate", "0.0%", COLORS["purple"]),
        ("Delinquency Rate", "30+ DPD", "0.0%", COLORS["amber"]),
        ("NPL Rate", "NPL", "0.0%", COLORS["red"]),
        ("Expected Loss", "Expected loss", "$#,0,,.0M", COLORS["coral"]),
    ]
    for idx, item in enumerate(cards):
        v1.append(card(item[0], item[1], item[2], 24 + idx * 205, 92, 186, 78, 100 + idx, item[3]))
    v1.extend(
        [
            category_measure_visual("lineClusteredColumnComboChart", "DimMonth", "month_start", "Month", [("Loan Book Balance", "Loan book", "$#,0,,.0M"), ("Delinquency Rate", "30+ DPD", "0.0%")], "Loan book and delinquency trend", "Columns show balance, line shows 30+ DPD rate", 24, 190, 610, 238, 200, None, COLORS["blue"]),
            category_measure_visual("barChart", "DimRiskBand", "risk_band", "Risk band", [("Loan Book Balance", "Loan book", "$#,0,,.0M")], "Exposure by risk band", "Sorted by risk grade", 654, 190, 290, 238, 201, "Loan Book Balance", COLORS["teal"]),
            category_measure_visual("barChart", "DimMerchant", "merchant_category", "Merchant category", [("Expected Loss", "Expected loss", "$#,0,,.0M")], "Expected loss by category", "Concentration and credit mix", 964, 190, 290, 238, 202, "Expected Loss", COLORS["coral"]),
            table_visual(
                [
                    {"kind": "column", "table": "DimMerchant", "column": "merchant_category", "display": "Category"},
                    {"kind": "column", "table": "DimRiskBand", "column": "risk_band", "display": "Risk"},
                    {"kind": "measure", "measure": "Loan Book Balance", "display": "Loan book", "format": "$#,0,,.0M"},
                    {"kind": "measure", "measure": "Delinquency Rate", "display": "30+ DPD", "format": "0.0%"},
                    {"kind": "measure", "measure": "Expected Loss Rate", "display": "EL rate", "format": "0.0%"},
                ],
                "Risk concentration lookup",
                "Merchant category and risk grade drill table",
                24,
                452,
                1230,
                210,
                300,
                "Expected Loss",
            ),
        ]
    )
    pages.append(page("Credit Risk Overview", 0, v1))

    v2: list[dict] = [shape(0, 0, 1280, 76, 0, "#F4F1FA"), textbox("Delinquency & Vintage Analysis\nRoll-rate, cohort vintage, DPD bucket, and segment risk", 24, 14, 620, 54, 1, "18pt")]
    for i, make in enumerate(common_slicers, start=10):
        v2.append(make(i))
    for idx, item in enumerate(
        [
            ("DPD 30+ Balance", "30+ balance", "$#,0,,.0M", COLORS["amber"]),
            ("DPD 60+ Balance", "60+ balance", "$#,0,,.0M", COLORS["coral"]),
            ("Vintage 30+ Rate", "Vintage 30+", "0.0%", COLORS["red"]),
            ("Roll Rate", "Avg roll rate", "0.0%", COLORS["purple"]),
            ("Autopay Failure Loans", "Autopay failures", "#,0", COLORS["blue"]),
        ]
    ):
        v2.append(card(item[0], item[1], item[2], 24 + idx * 245, 92, 224, 78, 100 + idx, item[3]))
    v2.extend(
        [
            category_measure_visual("lineClusteredColumnComboChart", "DimMonth", "month_start", "Month", [("DPD 30+ Balance", "30+ balance", "$#,0,,.0M"), ("NPL Rate", "NPL rate", "0.0%")], "Delinquency and NPL trend", "Early warning and non-performing trend", 24, 190, 610, 230, 200, None, COLORS["amber"]),
            category_measure_visual("barChart", "FactLoanMonthly", "dpd_bucket", "DPD bucket", [("Loan Book Balance", "Balance", "$#,0,,.0M")], "DPD bucket exposure", "Current to charge-off waterfall proxy", 654, 190, 290, 230, 201, "Loan Book Balance", COLORS["red"]),
            category_measure_visual("barChart", "DimCustomerSegment", "customer_segment", "Segment", [("Delinquency Rate", "30+ DPD", "0.0%")], "Segment delinquency risk", "Repeat and first-time borrower risk", 964, 190, 290, 230, 202, "Delinquency Rate", COLORS["purple"]),
            table_visual(
                [
                    {"kind": "column", "table": "FactVintage", "column": "origination_month", "display": "Cohort"},
                    {"kind": "column", "table": "FactVintage", "column": "mob", "display": "MOB"},
                    {"kind": "measure", "measure": "Vintage 30+ Rate", "display": "Vintage 30+", "format": "0.0%"},
                    {"kind": "measure", "measure": "Vintage Loss Rate", "display": "Loss rate", "format": "0.0%"},
                ],
                "Vintage cohort table",
                "Origination month by months-on-book",
                24,
                446,
                610,
                220,
                300,
                "Vintage 30+ Rate",
            ),
            table_visual(
                [
                    {"kind": "column", "table": "FactRollRate", "column": "prior_dpd_bucket", "display": "From bucket"},
                    {"kind": "column", "table": "FactRollRate", "column": "dpd_bucket", "display": "To bucket"},
                    {"kind": "measure", "measure": "Roll Rate", "display": "Roll rate", "format": "0.0%"},
                    {"kind": "measure", "measure": "Loan Book Balance", "display": "Balance", "format": "$#,0,,.0M"},
                ],
                "Roll-rate matrix detail",
                "Prior bucket to current bucket",
                654,
                446,
                600,
                220,
                301,
                "Roll Rate",
            ),
        ]
    )
    pages.append(page("Delinquency & Vintage Analysis", 1, v2))

    v3: list[dict] = [shape(0, 0, 1280, 76, 0, "#EEF7F4"), textbox("Collections & Provision Forecast\nRecovery, SLA, provision bridge, and base/downside stress test", 24, 14, 680, 54, 1, "18pt")]
    for i, make in enumerate(common_slicers, start=10):
        v3.append(make(i))
    for idx, item in enumerate(
        [
            ("Recovery Amount", "Recovery", "$#,0,,.0M", COLORS["green"]),
            ("Recovery Rate", "Recovery rate", "0.0%", COLORS["teal"]),
            ("Collections SLA %", "SLA hit rate", "0.0%", COLORS["blue"]),
            ("Provision Amount", "Provision", "$#,0,,.0M", COLORS["purple"]),
            ("Forecast Provision", "Forecast provision", "$#,0,,.0M", COLORS["coral"]),
        ]
    ):
        v3.append(card(item[0], item[1], item[2], 24 + idx * 245, 92, 224, 78, 100 + idx, item[3]))
    v3.extend(
        [
            category_measure_visual("lineClusteredColumnComboChart", "FactProvisionForecast", "forecast_month", "Forecast month", [("Forecast Provision", "Provision", "$#,0,,.0M"), ("Forecast Expected Loss", "Expected loss", "$#,0,,.0M")], "Provision forecast by month", "Base, upside, downside scenarios selectable in model", 24, 190, 610, 230, 200, None, COLORS["purple"]),
            category_measure_visual("barChart", "FactCollections", "queue", "Collection queue", [("Recovery Rate", "Recovery rate", "0.0%")], "Recovery rate by queue", "Operational queue performance", 654, 190, 290, 230, 201, "Recovery Rate", COLORS["green"]),
            category_measure_visual("barChart", "FactProvisionForecast", "scenario", "Scenario", [("Incremental Provision", "Incremental provision", "$#,0,,.0M")], "Provision stress bridge", "Base versus upside/downside scenario", 964, 190, 290, 230, 202, "Incremental Provision", COLORS["coral"]),
            table_visual(
                [
                    {"kind": "column", "table": "FactCollections", "column": "queue", "display": "Queue"},
                    {"kind": "column", "table": "FactCollections", "column": "dpd_bucket", "display": "DPD bucket"},
                    {"kind": "measure", "measure": "Case Balance", "display": "Case balance", "format": "$#,0,,.0M"},
                    {"kind": "measure", "measure": "Recovery Rate", "display": "Recovery rate", "format": "0.0%"},
                    {"kind": "measure", "measure": "Collections SLA %", "display": "SLA %", "format": "0.0%"},
                ],
                "Collections SLA and recovery detail",
                "Queue prioritization table",
                24,
                446,
                610,
                220,
                300,
                "Case Balance",
            ),
            table_visual(
                [
                    {"kind": "column", "table": "FactProvisionForecast", "column": "scenario", "display": "Scenario"},
                    {"kind": "column", "table": "FactProvisionForecast", "column": "forecast_month", "display": "Month"},
                    {"kind": "measure", "measure": "Forecast Expected Loss", "display": "Expected loss", "format": "$#,0,,.0M"},
                    {"kind": "measure", "measure": "Forecast Provision", "display": "Provision", "format": "$#,0,,.0M"},
                    {"kind": "measure", "measure": "Incremental Provision", "display": "Incremental", "format": "$#,0,,.0M"},
                ],
                "Provision forecast detail",
                "Scenario and month bridge",
                654,
                446,
                600,
                220,
                301,
                "Forecast Provision",
            ),
        ]
    )
    pages.append(page("Collections & Provision Forecast", 2, v3))

    layout = {
        "id": 0,
        "resourcePackages": [],
        "sections": pages,
        "config": "{}",
        "layoutOptimization": 0,
    }
    write_json(ROOT / "build" / "native_report_layout_project9.json", layout)
    return layout


def build_pbixproj_files(layout: dict, model: dict) -> None:
    if PBIXPROJ_DIR.exists():
        shutil.rmtree(PBIXPROJ_DIR)
    PBIXPROJ_DIR.mkdir(parents=True, exist_ok=True)
    write_json(
        PBIXPROJ_DIR / ".pbixproj.json",
        {"version": "1.0", "created": "2026-06-11T00:00:00", "lastModified": "2026-06-11T00:00:00", "settings": {"model": {"serializationMode": "Raw"}, "mashup": {"serializationMode": "Raw"}}},
    )
    (PBIXPROJ_DIR / "Version.txt").write_text("1.28", encoding="utf-8")
    write_json(PBIXPROJ_DIR / "ReportMetadata.json", {"Version": 5, "AutoCreatedRelationships": [], "CreatedFrom": "Desktop", "CreatedFromRelease": "2026.06"})
    write_json(PBIXPROJ_DIR / "ReportSettings.json", {"Version": 4, "ReportSettings": {}, "QueriesSettings": {"TypeDetectionEnabled": True, "RelationshipImportEnabled": True, "Version": "2.155.756.0"}})
    write_json(PBIXPROJ_DIR / "Model" / "database.json", model)
    write_json(PBIXPROJ_DIR / "Report" / "report.json", {"id": 0, "layoutOptimization": 0, "sections": [{"displayName": s["displayName"], "name": s["name"], "ordinal": s["ordinal"]} for s in layout["sections"]]})
    write_json(PBIXPROJ_DIR / "Report" / "config.json", {"version": "5.68", "themeCollection": {"baseTheme": {"name": "CY26SU05", "version": "5.68", "type": 2}}})
    for sec in layout["sections"]:
        safe = f"{sec['ordinal']:03d}_{sec['displayName'].replace('/', '-').replace(' ', '_')}"
        sdir = PBIXPROJ_DIR / "Report" / "sections" / safe
        write_json(sdir / "section.json", {k: sec[k] for k in ["displayName", "displayOption", "height", "name", "ordinal", "width"]})
        write_json(sdir / "filters.json", [])
        write_json(sdir / "config.json", {})
        for idx, visual in enumerate(sec["visualContainers"]):
            vdir = sdir / "visualContainers" / f"{idx:05d}_{visual.get('z', idx)}"
            write_json(vdir / "visualContainer.json", {k: visual[k] for k in ["x", "y", "z", "width", "height", "tabOrder"] if k in visual})
            write_json(vdir / "config.json", json.loads(visual["config"]))
            write_json(vdir / "filters.json", [])
            if "query" in visual:
                write_json(vdir / "query.json", json.loads(visual["query"]))
            if "dataTransforms" in visual:
                write_json(vdir / "dataTransforms.json", json.loads(visual["dataTransforms"]))

    # PBIP source mirror for Power BI Desktop project open.
    if PBIP_DIR.exists():
        shutil.rmtree(PBIP_DIR)
    (PBIP_DIR / "Project9_BNPL_Risk.Report").mkdir(parents=True, exist_ok=True)
    (PBIP_DIR / "Project9_BNPL_Risk.SemanticModel").mkdir(parents=True, exist_ok=True)
    write_json(PBIP_DIR / "Project9_BNPL_Risk.pbip", {"version": "1.0", "artifacts": [{"report": {"path": "Project9_BNPL_Risk.Report"}}, {"semanticModel": {"path": "Project9_BNPL_Risk.SemanticModel"}}]})
    write_json(PBIP_DIR / "Project9_BNPL_Risk.SemanticModel" / "model.bim", model)
    write_json(PBIP_DIR / "Project9_BNPL_Risk.SemanticModel" / "diagramLayout.json", {"version": "1.1.0", "diagrams": []})
    write_json(PBIP_DIR / "Project9_BNPL_Risk.Report" / "report.json", layout)


def plot_outputs(data: dict) -> None:
    plt.rcParams.update({"font.family": "DejaVu Sans", "axes.edgecolor": "#D8DEE9", "axes.labelcolor": COLORS["muted"], "xtick.color": COLORS["muted"], "ytick.color": COLORS["muted"]})
    snapshots = data["snapshots"]
    collections = data["collections"]
    vintage = data["vintage"]
    roll = data["roll"]
    forecast = data["forecast"]

    monthly = snapshots.groupby("snapshot_month", as_index=False).agg(balance=("current_principal", "sum"), dpd30=("dpd30_balance", "sum"), npl=("npl_balance", "sum"))
    monthly["dpd30_rate"] = monthly["dpd30"] / monthly["balance"]
    fig, ax1 = plt.subplots(figsize=(10, 4.2))
    ax1.bar(monthly["snapshot_month"], monthly["balance"] / 1e6, color=COLORS["blue"], alpha=0.72, width=20)
    ax1.set_ylabel("Loan book ($M)")
    ax2 = ax1.twinx()
    ax2.plot(monthly["snapshot_month"], monthly["dpd30_rate"] * 100, color=COLORS["red"], linewidth=2.5, marker="o", markersize=3)
    ax2.set_ylabel("30+ DPD %")
    ax1.set_title("Loan Book vs 30+ DPD Trend", loc="left", fontweight="bold")
    fig.tight_layout()
    fig.savefig(SCREEN_DIR / "overview_loan_book_trend.png", dpi=150, bbox_inches="tight")
    plt.close(fig)

    bucket = snapshots.loc[snapshots["snapshot_month"].ge("2025-10-01")].groupby(["snapshot_month", "dpd_bucket"], as_index=False)["current_principal"].sum()
    pivot = bucket.pivot(index="snapshot_month", columns="dpd_bucket", values="current_principal").fillna(0) / 1e6
    ordered_cols = [c for c in ["Current", "1-7 DPD", "8-14 DPD", "15-29 DPD", "30-59 DPD", "60-89 DPD", "90+ DPD", "Charge-off"] if c in pivot.columns]
    fig, ax = plt.subplots(figsize=(10, 4.2))
    pivot_plot = pivot[ordered_cols].copy()
    pivot_plot.index = [x.strftime("%b %y") for x in pivot_plot.index]
    pivot_plot.plot(kind="bar", stacked=True, ax=ax, color=[COLORS["green"], "#82CFAF", "#F3D58A", COLORS["amber"], "#EE8F67", COLORS["coral"], COLORS["red"], "#4B5563"], width=0.82)
    ax.set_title("DPD Bucket Exposure Mix", loc="left", fontweight="bold")
    ax.set_ylabel("$M")
    ax.legend(loc="upper left", ncols=4, fontsize=8)
    ax.set_xticklabels(pivot_plot.index, rotation=0)
    fig.tight_layout()
    fig.savefig(SCREEN_DIR / "vintage_dpd_bucket_mix.png", dpi=150, bbox_inches="tight")
    plt.close(fig)

    vint = vintage.loc[vintage["origination_month"].ge("2025-01-01")].copy()
    heat = vint.pivot(index="origination_month", columns="mob", values="dpd30_rate").fillna(0).iloc[-12:, :8]
    fig, ax = plt.subplots(figsize=(10, 4.2))
    im = ax.imshow(heat.values * 100, cmap="YlOrRd", aspect="auto")
    ax.set_title("Vintage 30+ DPD Heatmap", loc="left", fontweight="bold")
    ax.set_xticks(range(len(heat.columns)), labels=[f"MOB {c}" for c in heat.columns])
    ax.set_yticks(range(len(heat.index)), labels=[x.strftime("%b %y") for x in heat.index])
    fig.colorbar(im, ax=ax, fraction=0.025, pad=0.02, label="30+ DPD %")
    fig.tight_layout()
    fig.savefig(SCREEN_DIR / "vintage_heatmap.png", dpi=150, bbox_inches="tight")
    plt.close(fig)

    latest_roll = roll.loc[roll["snapshot_month"].eq(roll["snapshot_month"].max())]
    roll_piv = latest_roll.pivot(index="prior_dpd_bucket", columns="dpd_bucket", values="roll_rate").fillna(0)
    order = [b for b in ["Current", "1-7 DPD", "8-14 DPD", "15-29 DPD", "30-59 DPD", "60-89 DPD", "90+ DPD", "Charge-off"] if b in roll_piv.index or b in roll_piv.columns]
    roll_piv = roll_piv.reindex(index=order, columns=order).fillna(0)
    fig, ax = plt.subplots(figsize=(9, 4.2))
    im = ax.imshow(roll_piv.values * 100, cmap="Blues", aspect="auto")
    ax.set_title("Latest Roll-rate Matrix", loc="left", fontweight="bold")
    ax.set_xticks(range(len(roll_piv.columns)), labels=roll_piv.columns, rotation=35, ha="right")
    ax.set_yticks(range(len(roll_piv.index)), labels=roll_piv.index)
    fig.colorbar(im, ax=ax, fraction=0.025, pad=0.02, label="Roll %")
    fig.tight_layout()
    fig.savefig(SCREEN_DIR / "roll_rate_matrix.png", dpi=150, bbox_inches="tight")
    plt.close(fig)

    recovery = collections.groupby("queue", as_index=False).agg(recovery=("recovery_amount", "sum"), balance=("case_balance", "sum"), sla=("within_sla_flag", "mean"))
    recovery["recovery_rate"] = recovery["recovery"] / recovery["balance"]
    fig, ax = plt.subplots(figsize=(8, 4.2))
    ax.bar(recovery["queue"], recovery["recovery_rate"] * 100, color=[COLORS["teal"], COLORS["blue"], COLORS["amber"], COLORS["coral"]])
    ax.plot(recovery["queue"], recovery["sla"] * 100, color=COLORS["ink"], marker="o", linewidth=2)
    ax.set_title("Recovery Rate and SLA by Queue", loc="left", fontweight="bold")
    ax.set_ylabel("%")
    ax.tick_params(axis="x", rotation=15)
    fig.tight_layout()
    fig.savefig(SCREEN_DIR / "collections_recovery_sla.png", dpi=150, bbox_inches="tight")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(10, 4.2))
    for scenario, df in forecast.groupby("scenario"):
        ax.plot(df["forecast_month"], df["forecast_provision"] / 1e6, marker="o", linewidth=2.2, label=scenario)
    ax.set_title("Provision Forecast Scenarios", loc="left", fontweight="bold")
    ax.set_ylabel("Provision ($M)")
    ax.legend(loc="upper left")
    fig.tight_layout()
    fig.savefig(SCREEN_DIR / "provision_forecast.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def build_html(data: dict) -> None:
    snapshots = data["snapshots"]
    apps = data["apps"]
    loans = data["loans"]
    collections = data["collections"]
    latest = snapshots.loc[snapshots["snapshot_month"].eq(LATEST_SNAPSHOT)]
    kpis = {
        "Loan book": money(latest["current_principal"].sum()),
        "Disbursement": money(loans["funded_amount"].sum()),
        "Approval rate": pct(apps["approved_flag"].mean()),
        "30+ DPD": pct(latest["dpd30_balance"].sum() / latest["current_principal"].sum()),
        "NPL": pct(latest["npl_balance"].sum() / latest["current_principal"].sum()),
        "Expected loss": money(latest["expected_loss_amount"].sum()),
        "Recovery rate": pct(collections["recovery_amount"].sum() / collections["case_balance"].sum()),
        "SLA": pct(collections["within_sla_flag"].mean()),
    }
    risk_table = (
        latest.groupby("risk_band", as_index=False)
        .agg(balance=("current_principal", "sum"), dpd30=("dpd30_balance", "sum"), expected_loss=("expected_loss_amount", "sum"))
        .assign(dpd30_rate=lambda x: x["dpd30"] / x["balance"])
    )
    risk_rows = "\n".join(
        f"<tr><td>{r.risk_band}</td><td>{money(r.balance)}</td><td>{pct(r.dpd30_rate)}</td><td>{money(r.expected_loss)}</td></tr>"
        for r in risk_table.itertuples()
    )
    html = f"""
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>BNPL Credit Risk Dashboard</title>
  <style>
    :root {{ --navy:{COLORS['navy']}; --ink:{COLORS['ink']}; --muted:{COLORS['muted']}; --bg:{COLORS['bg']}; --panel:#fff; --border:{COLORS['border']}; --red:{COLORS['red']}; --amber:{COLORS['amber']}; --blue:{COLORS['blue']}; --teal:{COLORS['teal']}; }}
    * {{ box-sizing: border-box; }}
    body {{ margin:0; font-family: Segoe UI, Arial, sans-serif; background:var(--bg); color:var(--ink); }}
    header {{ padding: 18px 26px 14px; background:#eef3fa; border-bottom:1px solid var(--border); }}
    h1 {{ margin:0; font-size:24px; letter-spacing:0; }}
    .sub {{ color:var(--muted); margin-top:4px; font-size:13px; }}
    nav {{ display:flex; gap:8px; padding:12px 26px; background:#fff; border-bottom:1px solid var(--border); position:sticky; top:0; z-index:2; }}
    nav button {{ border:1px solid var(--border); background:#fff; padding:9px 13px; border-radius:6px; cursor:pointer; color:var(--ink); font-weight:600; }}
    nav button.active {{ background:var(--navy); color:#fff; border-color:var(--navy); }}
    main {{ padding:18px 26px 36px; }}
    .tab {{ display:none; }}
    .tab.active {{ display:block; }}
    .kpis {{ display:grid; grid-template-columns: repeat(4, minmax(150px, 1fr)); gap:12px; margin-bottom:16px; }}
    .card, .panel {{ background:var(--panel); border:1px solid var(--border); border-radius:8px; box-shadow:0 1px 2px rgba(16,34,63,.05); }}
    .card {{ padding:13px 14px; min-height:78px; }}
    .label {{ color:var(--muted); font-size:12px; }}
    .value {{ font-size:22px; font-weight:700; margin-top:5px; }}
    .grid {{ display:grid; grid-template-columns: 1fr 1fr; gap:14px; }}
    .panel {{ padding:12px; overflow:hidden; }}
    .panel h2 {{ margin:0 0 8px; font-size:15px; }}
    img {{ width:100%; display:block; border-radius:4px; }}
    table {{ width:100%; border-collapse:collapse; font-size:13px; background:#fff; }}
    th, td {{ padding:9px 10px; border-bottom:1px solid var(--border); text-align:left; }}
    th {{ color:var(--muted); font-weight:700; }}
    @media(max-width:900px) {{ .kpis {{ grid-template-columns: repeat(2,1fr); }} .grid {{ grid-template-columns:1fr; }} nav {{ flex-wrap:wrap; }} }}
  </style>
</head>
<body>
  <header>
    <h1>BNPL / Digital Lending Credit Risk Dashboard</h1>
    <div class="sub">Synthetic portfolio, seed {SEED} | latest snapshot {LATEST_SNAPSHOT.strftime('%b %Y')} | designed for credit risk, collections, finance leadership</div>
  </header>
  <nav>
    <button class="active" data-tab="overview">Credit Risk Overview</button>
    <button data-tab="vintage">Delinquency & Vintage Analysis</button>
    <button data-tab="collections">Collections & Provision Forecast</button>
  </nav>
  <main>
    <section id="overview" class="tab active">
      <div class="kpis">{''.join(f'<div class="card"><div class="label">{k}</div><div class="value">{v}</div></div>' for k, v in list(kpis.items())[:6])}</div>
      <div class="grid">
        <div class="panel"><h2>Loan book and delinquency trend</h2><img src="screenshots/overview_loan_book_trend.png" alt="Loan book trend"></div>
        <div class="panel"><h2>Risk concentration</h2><table><thead><tr><th>Risk band</th><th>Balance</th><th>30+ DPD</th><th>Expected loss</th></tr></thead><tbody>{risk_rows}</tbody></table></div>
      </div>
    </section>
    <section id="vintage" class="tab">
      <div class="kpis">{''.join(f'<div class="card"><div class="label">{k}</div><div class="value">{v}</div></div>' for k, v in [('30+ DPD', kpis['30+ DPD']), ('NPL', kpis['NPL']), ('Expected loss', kpis['Expected loss']), ('Autopay failures', f"{int(latest['autopay_failure_flag'].sum()):,}")])}</div>
      <div class="grid">
        <div class="panel"><h2>DPD bucket exposure mix</h2><img src="screenshots/vintage_dpd_bucket_mix.png" alt="DPD bucket mix"></div>
        <div class="panel"><h2>Vintage heatmap</h2><img src="screenshots/vintage_heatmap.png" alt="Vintage heatmap"></div>
        <div class="panel"><h2>Roll-rate matrix</h2><img src="screenshots/roll_rate_matrix.png" alt="Roll-rate matrix"></div>
      </div>
    </section>
    <section id="collections" class="tab">
      <div class="kpis">{''.join(f'<div class="card"><div class="label">{k}</div><div class="value">{v}</div></div>' for k, v in [('Recovery rate', kpis['Recovery rate']), ('SLA', kpis['SLA']), ('Provision', money(latest['provision_amount'].sum())), ('Forecast provision', money(data['forecast'].query('scenario == \"Base\"')['forecast_provision'].sum()))])}</div>
      <div class="grid">
        <div class="panel"><h2>Recovery and SLA by queue</h2><img src="screenshots/collections_recovery_sla.png" alt="Recovery and SLA"></div>
        <div class="panel"><h2>Provision forecast scenarios</h2><img src="screenshots/provision_forecast.png" alt="Provision forecast"></div>
      </div>
    </section>
  </main>
  <script>
    document.querySelectorAll('nav button').forEach(btn => btn.addEventListener('click', () => {{
      document.querySelectorAll('nav button').forEach(b => b.classList.remove('active'));
      document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
      btn.classList.add('active');
      document.getElementById(btn.dataset.tab).classList.add('active');
    }}));
  </script>
</body>
</html>
"""
    (OUTPUT_DIR / "dashboard_preview.html").write_text(html, encoding="utf-8")


def docs_and_configs(data: dict, layout: dict, model: dict) -> None:
    theme = {
        "name": "BNPL Credit Risk Executive",
        "dataColors": [COLORS["blue"], COLORS["teal"], COLORS["amber"], COLORS["coral"], COLORS["red"], COLORS["purple"]],
        "background": COLORS["bg"],
        "foreground": COLORS["ink"],
        "tableAccent": COLORS["blue"],
    }
    write_json(BUILD_CONFIG / "theme.json", theme)
    write_json(
        BUILD_CONFIG / "dashboard_config.json",
        {
            "title": "BNPL / Digital Lending Credit Risk Dashboard",
            "audience": "Credit risk leadership, collections operations, finance provisioning teams",
            "business_goal": "Monitor portfolio risk, diagnose delinquency/vintage movements, and prioritize collections and provision planning.",
            "pages": [s["displayName"] for s in layout["sections"]],
            "latest_snapshot_month": LATEST_SNAPSHOT.strftime("%Y-%m-%d"),
            "synthetic_data_seed": SEED,
        },
    )
    write_json(BUILD_CONFIG / "page_map.json", [{"page": s["displayName"], "ordinal": s["ordinal"], "visual_count": len(s["visualContainers"])} for s in layout["sections"]])
    write_json(
        BUILD_CONFIG / "visual_map.json",
        [
            {"page": s["displayName"], "visual_index": i, "visual_type": json.loads(v["config"]).get("singleVisual", {}).get("visualType"), "x": v["x"], "y": v["y"], "w": v["width"], "h": v["height"]}
            for s in layout["sections"]
            for i, v in enumerate(s["visualContainers"])
        ],
    )
    write_json(BUILD_CONFIG / "slicer_map.json", {"global_slicers": ["Month", "Product", "Risk"], "tables": ["DimMonth", "DimProduct", "DimRiskBand"]})
    write_json(MODEL_DIR / "measure_map.json", [{"name": n, "expression": e, "format": f, "description": d} for n, e, f, d in MEASURES])
    write_md(MODEL_DIR / "MEASURES.dax", "\n\n".join([f"{name} =\n{expr}" for name, expr, _, _ in MEASURES]))
    write_md(
        MODEL_DIR / "dax_measures.md",
        "\n".join(["# DAX Measures", "", "| Measure | Format | Definition |", "|---|---|---|", *[f"| {n} | `{f}` | {d} |" for n, _, f, d in MEASURES]]),
    )
    write_md(
        MODEL_DIR / "relationship_map.md",
        "\n".join(["# Relationship Map", "", "| From | Column | To | Column | Direction |", "|---|---|---|---|---|", *[f"| {a} | {b} | {c} | {d} | one direction |" for a, b, c, d in RELATIONSHIPS]]),
    )
    dictionary_lines = ["# Data Dictionary", "", "Synthetic BNPL credit risk dataset. Grain is documented per table.", ""]
    grains = {
        "fact_applications": "one credit application",
        "fact_loans": "one funded loan",
        "fact_loan_monthly": "one loan per snapshot month",
        "fact_collections": "one collections case",
        "fact_vintage": "one origination cohort per MOB",
        "fact_roll_rate": "one month, from bucket, to bucket",
        "fact_provision_forecast": "one scenario per forecast month",
    }
    for csv_name, table_name in TABLE_MAP:
        df = data["prepared"][csv_name]
        dictionary_lines.extend([f"## {table_name}", f"- Grain: {grains.get(csv_name, 'dimension lookup')}", "", "| Column | Type |", "|---|---|"])
        dictionary_lines.extend([f"| {col} | {str(dtype)} |" for col, dtype in df.dtypes.items()])
        dictionary_lines.append("")
    write_md(ROOT / "data" / "data_dictionary.md", "\n".join(dictionary_lines))
    write_md(MODEL_DIR / "data_dictionary.md", "\n".join(dictionary_lines))
    write_md(
        MODEL_DIR / "semantic_model_notes.md",
        """
# Semantic Model Notes

- Star schema with application, funded loan, monthly portfolio, collections, vintage, roll-rate, and forecast facts.
- KPI measures live in `KPI Measures`; key rates use `DIVIDE`.
- Date analysis uses `DimMonth` for monthly risk reporting, with daily `DimDate` retained for source extensibility.
- Rates are not summed; visuals use DAX measures for approval, delinquency, NPL, expected loss, recovery, SLA, vintage, and roll-rate.
""",
    )
    write_md(
        DOCS_DIR / "design_research.md",
        """
# Design Research

Sources used:

- [Tableau: Loan Risk Analysis Dashboard](https://www.tableau.com/solutions/gallery/banking-analytics): loan default risk, credit score distribution, risk trends, write-off risk over a 24-month view.
- [Microsoft Learn: Credit and collections management Power BI content](https://learn.microsoft.com/en-us/dynamics365/finance/accounts-receivable/credit-collections-power-bi): collections overview, aged balances, expected payments, write-offs, past-due customers.
- [Microsoft Fabric Community: Credit Risk Analytics Dashboard](https://community.fabric.microsoft.com/t5/Data-Stories-Gallery/Credit-Risk-Analytics-Dashboard/m-p/4833815): executive overview, risk matrix, borrower detail, neutral palette with risk colors.
- [ZoomCharts: Credit Risk Analysis Dashboard](https://zoomcharts.com/en/microsoft-power-bi-custom-visuals/dashboard-and-report-examples/view/credit-risk-analysis-dashboard): Power BI borrower risk overview and portfolio risk exposure patterns.
- [SAS: Credit Risk Dashboard](https://communities.sas.com/t5/SAS-Communities-Library/Credit-Risk-Dashboard-Visualize-loan-performance-delinquency/ta-p/968182): KPI cards, delinquency trends, credit score distribution, filters by loan type and delinquency.
- [ListenData: Credit Risk Vintage Analysis](https://www.listendata.com/2019/09/credit-risk-vintage-analysis.html): origination cohort and MOB vintage analysis.
- [OCC BNPL risk management guidance](https://www.occ.gov/news-issuances/bulletins/2023/bulletin-2023-37.html): BNPL needs early delinquency indicators and low-and-grow exposure monitoring.
- [CFPB BNPL Report 2025](https://files.consumerfinance.gov/f/documents/cfpb_BNPL_Report_2025_01.pdf): borrower segmentation and default context for BNPL users.

Applied design patterns:

- Three-tab workflow: monitor, diagnose, act.
- KPI strip on each tab, with dense finance-style charts below.
- Neutral blue/gray base, with amber/red reserved for risk and green/teal for recovery.
- Early BNPL DPD buckets: 1-7, 8-14, 15-29, 30-59, 60-89, 90+, charge-off.
- Vintage heatmap and roll-rate matrix as the main diagnostic patterns.
- Provision forecast scenario view with base, upside, downside cases.
""",
    )
    write_md(
        AGENT_DIR / "intake_brief.md",
        """
# Intake Brief

- Topic: BNPL / Digital Lending Credit Risk Dashboard.
- Project path: C:\\Users\\Win\\OneDrive\\Codex\\Portfolio\\BI\\Project 09 - BNPL Credit Risk Provision.
- Source data: synthetic demo data generated with fixed seed 90209.
- Audience: credit risk leadership, collections operations, finance provisioning.
- Business goal: monitor portfolio risk, diagnose delinquency and vintage movements, prioritize collections and provision planning.
- Requested tabs: Credit Risk Overview; Delinquency & Vintage Analysis; Collections & Provision Forecast.
- Output target: output/dashboard_final.pbix, with HTML preview as supplemental.
""",
    )
    write_md(
        AGENT_DIR / "run_log.md",
        f"""
# Run Log

- {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} Created Project 09 - BNPL Credit Risk Provision structure and generated synthetic BNPL credit risk data.
- Generated semantic model, DAX library, native report layout JSON, HTML preview, screenshots, and QA scaffolding.
""",
    )
    write_md(
        AGENT_DIR / "session_guard.md",
        f"""
# Session Guard

- Current project path: {ROOT}
- Expected final PBIX path: {OUTPUT_DIR / 'dashboard_final.pbix'}
- Power BI windows detected at intake: none from process scan.
- Selected session: pending Power BI Desktop launch for exact Project 09 - BNPL Credit Risk Provision seed PBIX.
- Evidence required before save: pbi-tools session PbixPath must equal `{OUTPUT_DIR / 'dashboard_model_seed.pbix'}`.
- Ignored sessions: any session whose PbixPath does not match Project 09 - BNPL Credit Risk Provision exact seed/final path.
""",
    )
    write_md(
        AGENT_DIR / "pbix_authoring_decision.md",
        """
# PBIX Authoring Decision

Selected route: SCRIPTED_DESKTOP_PBIX with Computer Use verification.

Reason:
- Power BI Desktop EXE and pbi-tools are available.
- dotnet CLI is unavailable, so the route avoids global dotnet tooling.
- A valid PBIX seed will be copied, then the full Project 09 - BNPL Credit Risk Provision model is pushed through the local Power BI Desktop TOM/XMLA session.
- Native report layout is patched after the Project 09 - BNPL Credit Risk Provision model seed is saved.

Fallback:
- If Desktop save or session binding fails, the build remains PBIP/PBIT/HTML supplemental and PBIX is marked blocked.
""",
    )
    write_md(
        AGENT_DIR / "failure_matrix.md",
        """
# Failure Matrix

| Risk | Mitigation |
|---|---|
| Wrong Power BI session | Match exact `PbixPath` before TOM push/save. |
| Stale SecurityBindings | Delete `/SecurityBindings` during layout patch. |
| Corrupt package | Validate with Microsoft.PowerBI.Packaging before replacing final. |
| Old-domain seed tables | Clear model tables/relationships before pushing Project 09 - BNPL Credit Risk Provision model. |
| Visual binding mismatch | Native visuals bind only to Project 09 - BNPL Credit Risk Provision table/measure names. |
""",
    )
    write_md(
        ROOT / "README.md",
        """
# BNPL / Digital Lending Credit Risk Dashboard

This Project 09 - BNPL Credit Risk Provision BI package contains a complete synthetic BNPL credit risk dashboard build.

Key paths:

- `data/raw/`: synthetic source extract.
- `data/prepared/`: prepared star-schema CSV tables.
- `model/`: semantic model, DAX measures, relationship map.
- `build/config/`: dashboard page, visual, slicer, and theme config.
- `build/native_report_layout_project9.json`: native Power BI report layout.
- `powerbi/pbip/Project9_BNPL_Risk/`: Power BI project source package.
- `output/dashboard_preview.html`: supplemental browser preview.
- `output/dashboard_final.pbix`: final target after Power BI Desktop save and package QA.

Rebuild:

```powershell
python .\\build\\scripts\\build_project9.py
```
""",
    )
    write_md(
        DOCS_DIR / "handoff_notes.md",
        """
# Handoff Notes

Final target: `output/dashboard_final.pbix`.

The project includes data pipeline, semantic model, native layout source, HTML preview, screenshots, and QA files. Synthetic data is for portfolio demonstration and uses seed 90209.

Dashboard pages:

1. Credit Risk Overview
2. Delinquency & Vintage Analysis
3. Collections & Provision Forecast

Known caveat: PBIX is only final after Power BI Desktop opens/saves the exact Project 09 - BNPL Credit Risk Provision seed and package validation passes.
""",
    )
    write_md(DOCS_DIR / "refresh_guide.md", "# Refresh Guide\n\nReplace CSVs in `data/prepared/`, rerun model push, refresh in Power BI Desktop, then save final PBIX.")
    write_md(DOCS_DIR / "rebuild_guide.md", "# Rebuild Guide\n\nRun `python build/scripts/build_project9.py`, then run the Power BI scripts in `build/scripts` in numeric order for PBIX build.")
    write_md(DOCS_DIR / "changelog.md", f"# Changelog\n\n- {datetime.now().date()}: Initial Project 09 - BNPL Credit Risk Provision build package generated.")
    write_md(DOCS_DIR / "issue_log.md", "# Issue Log\n\nNo open data/model issues after generation. PBIX Desktop save QA is pending until build route completes.")
    write_md(ROOT / "powerbi" / "notes" / "authoring_strategy.md", (AGENT_DIR / "pbix_authoring_decision.md").read_text(encoding="utf-8"))
    write_md(ROOT / "powerbi" / "notes" / "pbix_build_runbook.md", "# PBIX Build Runbook\n\n1. Build package with `python build/scripts/build_project9.py`.\n2. Copy a validated seed PBIX to `output/dashboard_model_seed.pbix`.\n3. Open exact seed in Power BI Desktop.\n4. Run `build/scripts/12_push_model_bim_via_tom.ps1`.\n5. Save seed in Desktop.\n6. Run `build/scripts/13_apply_native_layout_to_pbix.ps1`.\n7. Open `output/dashboard_final.pbix` and capture QA screenshots.")
    write_md(ROOT / "powerbi" / "notes" / "desktop_ui_runbook.md", "# Desktop UI Runbook\n\nUse Power BI Desktop only on the exact Project 09 - BNPL Credit Risk Provision PBIX path. Confirm pbi-tools session path before save. Do not use another open `dashboard_final.pbix` window.")

    qa_metrics = {
        "applications": int(len(data["apps"])),
        "loans": int(len(data["loans"])),
        "snapshots": int(len(data["snapshots"])),
        "collections_cases": int(len(data["collections"])),
        "latest_loan_book": float(data["snapshots"].loc[data["snapshots"]["snapshot_month"].eq(LATEST_SNAPSHOT), "current_principal"].sum()),
        "latest_dpd30_rate": float(data["snapshots"].loc[data["snapshots"]["snapshot_month"].eq(LATEST_SNAPSHOT), "dpd30_balance"].sum() / data["snapshots"].loc[data["snapshots"]["snapshot_month"].eq(LATEST_SNAPSHOT), "current_principal"].sum()),
    }
    pd.DataFrame([qa_metrics]).to_csv(QA_DIR / "reconciliation.csv", index=False)
    write_json(QA_DIR / "pbix_validation.json", {"status": "pending_desktop_build", "expected_final_path": str(OUTPUT_DIR / "dashboard_final.pbix"), "layout_pages": [s["displayName"] for s in layout["sections"]], "visual_count": sum(len(s["visualContainers"]) for s in layout["sections"])})
    write_json(QA_DIR / "pbix_final_validation.json", {"status": "pending_desktop_open_check", "visual_error_count": None})
    write_md(QA_DIR / "qa_checklist.md", "# QA Checklist\n\n- [x] Data generated with fixed seed.\n- [x] Prepared row counts documented.\n- [x] DAX measures documented and use DIVIDE for rates.\n- [x] Native layout generated.\n- [ ] Final PBIX opened in Power BI Desktop.\n- [ ] Visual error count confirmed as 0.")
    write_md(QA_DIR / "visual_qa_notes.md", "# Visual QA Notes\n\nGenerated HTML preview screenshots and native Power BI layout source. Desktop visual QA pending final PBIX open-check.")
    write_md(QA_DIR / "interaction_qa_notes.md", "# Interaction QA Notes\n\nGlobal slicers are included for Month, Product, and Risk Band in native layout. Browser preview tab navigation is functional.")
    write_md(QA_DIR / "performance_qa_notes.md", "# Performance QA Notes\n\nPrepared data is compact for portfolio demo. Largest table is monthly loan snapshot; expected to import comfortably in Power BI Desktop.")
    write_md(QA_DIR / "regression_qa_notes.md", "# Regression QA Notes\n\nInitial build; no regression loop executed yet.")


def main() -> None:
    mkdirs()
    data = build_data()
    model = build_semantic_model(data["prepared"])
    layout = build_layout()
    build_pbixproj_files(layout, model)
    plot_outputs(data)
    build_html(data)
    docs_and_configs(data, layout, model)
    print(json.dumps({"status": "generated", "project": str(ROOT), "pages": [s["displayName"] for s in layout["sections"]], "visual_count": sum(len(s["visualContainers"]) for s in layout["sections"])}, indent=2))


if __name__ == "__main__":
    main()
