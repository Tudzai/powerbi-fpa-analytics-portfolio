from __future__ import annotations

import csv
import json
import math
import shutil
import textwrap
import uuid
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SEED = 20260611
REPORT_DATE = date(2026, 6, 11)
START_MONTH = pd.Timestamp("2024-01-01")
LATEST_MONTH = pd.Timestamp("2026-05-01")
MONTHS = pd.date_range(START_MONTH, LATEST_MONTH, freq="MS")
MEASURE_TABLE = "KPI Measures"

RAW_DIR = PROJECT_ROOT / "data" / "raw"
PREPARED_DIR = PROJECT_ROOT / "data" / "prepared"
VALIDATED_DIR = PROJECT_ROOT / "data" / "validated"
MODEL_DIR = PROJECT_ROOT / "model"
BUILD_DIR = PROJECT_ROOT / "build"
CONFIG_DIR = BUILD_DIR / "config"
SCRIPT_DIR = BUILD_DIR / "scripts"
POWERBI_DIR = PROJECT_ROOT / "powerbi"
OUTPUT_DIR = PROJECT_ROOT / "output"
SCREENSHOT_DIR = OUTPUT_DIR / "screenshots"
QA_DIR = PROJECT_ROOT / "qa"
DOCS_DIR = PROJECT_ROOT / "docs"
AGENT_DIR = PROJECT_ROOT / "_agent"

PAGE_BG = "#F5F7FA"
HEADER_BG = "#102033"
PANEL_BG = "#FFFFFF"
PANEL_BORDER = "#D6DEE8"
TEXT_DARK = "#172033"
TEXT_MUTED = "#667085"
TEXT_LIGHT = "#F8FAFC"
TEXT_LIGHT_MUTED = "#C9D6E4"
BLUE = "#2563EB"
TEAL = "#0F8B8D"
GREEN = "#16A34A"
AMBER = "#D97706"
RED = "#DC2626"
INDIGO = "#4F46E5"
SLATE = "#475467"


def ensure_dirs() -> None:
    for folder in [
        RAW_DIR,
        PREPARED_DIR,
        VALIDATED_DIR,
        MODEL_DIR,
        BUILD_DIR,
        CONFIG_DIR,
        SCRIPT_DIR,
        POWERBI_DIR / "notes",
        POWERBI_DIR / "pbip",
        OUTPUT_DIR / "exports",
        SCREENSHOT_DIR,
        QA_DIR,
        DOCS_DIR,
        AGENT_DIR,
    ]:
        folder.mkdir(parents=True, exist_ok=True)


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.strip() + "\n", encoding="utf-8")


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def write_csv(path: Path, df: pd.DataFrame) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False, encoding="utf-8-sig")


def month_key(ts: pd.Timestamp) -> int:
    return ts.year * 100 + ts.month


def month_label(ts: pd.Timestamp) -> str:
    return ts.strftime("%b %Y")


def clean_name(value: str) -> str:
    return "".join(ch for ch in value if ch.isalnum() or ch in (" ", "-", "_")).strip()


def money_short(value: float) -> str:
    sign = "-" if value < 0 else ""
    value = abs(float(value))
    if value >= 1_000_000_000:
        return f"{sign}${value / 1_000_000_000:.2f}B"
    if value >= 1_000_000:
        return f"{sign}${value / 1_000_000:.1f}M"
    if value >= 1_000:
        return f"{sign}${value / 1_000:.1f}K"
    return f"{sign}${value:,.0f}"


def number_short(value: float) -> str:
    value = float(value)
    if abs(value) >= 1_000_000:
        return f"{value / 1_000_000:.1f}M"
    if abs(value) >= 1_000:
        return f"{value / 1_000:.1f}K"
    return f"{value:,.0f}"


def pct(value: float) -> str:
    return f"{float(value):.1%}"


def build_synthetic_data() -> dict[str, pd.DataFrame]:
    rng = np.random.default_rng(SEED)
    n_clients = 860
    segments = np.array(["Digital Starter", "Mass Affluent", "HNW", "UHNW", "Retirement"])
    segment_p = np.array([0.28, 0.34, 0.22, 0.06, 0.10])
    risk_profiles = np.array(["Conservative", "Balanced", "Growth", "Aggressive"])
    risk_p = np.array([0.22, 0.39, 0.28, 0.11])
    regions = np.array(["North America", "Europe", "APAC", "LATAM"])
    region_p = np.array([0.48, 0.22, 0.23, 0.07])
    channels = np.array(["Organic App", "Advisor Referral", "Paid Search", "Employer Plan", "Partner API"])
    channel_p = np.array([0.30, 0.26, 0.18, 0.14, 0.12])
    advisors = np.array(["Avery Chen", "Mina Patel", "Jon Bell", "Sofia Garcia", "Noah Miller", "Lin Nguyen"])
    model_by_risk = {
        "Conservative": "Income Shield",
        "Balanced": "Balanced Core",
        "Growth": "Growth Builder",
        "Aggressive": "Equity Edge",
    }
    benchmarks = {
        "Income Shield": "40/60 Global Blend",
        "Balanced Core": "60/40 Global Blend",
        "Growth Builder": "80/20 Global Blend",
        "Equity Edge": "Global Equity 90",
    }
    target_alloc = {
        "Income Shield": {"Equity": 0.35, "Fixed Income": 0.50, "Alternatives": 0.07, "Cash": 0.07, "Crypto": 0.01},
        "Balanced Core": {"Equity": 0.58, "Fixed Income": 0.30, "Alternatives": 0.07, "Cash": 0.04, "Crypto": 0.01},
        "Growth Builder": {"Equity": 0.76, "Fixed Income": 0.15, "Alternatives": 0.06, "Cash": 0.02, "Crypto": 0.01},
        "Equity Edge": {"Equity": 0.88, "Fixed Income": 0.04, "Alternatives": 0.04, "Cash": 0.01, "Crypto": 0.03},
    }
    target_risk = {"Conservative": 25, "Balanced": 48, "Growth": 68, "Aggressive": 84}
    fee_bps = {"Digital Starter": 29, "Mass Affluent": 42, "HNW": 58, "UHNW": 74, "Retirement": 38}
    segment_aum_mu = {"Digital Starter": 11.0, "Mass Affluent": 12.6, "HNW": 14.1, "UHNW": 15.3, "Retirement": 13.2}
    first_names = [
        "Alex", "Taylor", "Morgan", "Jordan", "Riley", "Casey", "Jamie", "Cameron", "Quinn", "Drew",
        "Harper", "Rowan", "Skyler", "Reese", "Emerson", "Parker", "Ari", "Sam", "Nico", "Lena",
    ]
    last_names = [
        "Stone", "Lee", "Martin", "Young", "Wong", "Rivera", "Cole", "Adams", "Price", "Brooks",
        "Tran", "Kim", "Singh", "Carter", "Morris", "Bennett", "Hughes", "Cooper", "Nguyen", "Patel",
    ]

    join_weights = np.linspace(0.6, 1.25, len(MONTHS))
    join_weights = join_weights / join_weights.sum()
    join_months = rng.choice(MONTHS, size=n_clients, p=join_weights)

    client_rows = []
    client_state: dict[str, dict[str, object]] = {}
    for idx in range(n_clients):
        seg = str(rng.choice(segments, p=segment_p))
        risk = str(rng.choice(risk_profiles, p=risk_p))
        model = model_by_risk[risk]
        base_aum = float(rng.lognormal(segment_aum_mu[seg], 0.58))
        base_aum = float(np.clip(base_aum, 18_000, 16_000_000))
        join_month = pd.Timestamp(join_months[idx])
        client_id = f"CL{idx + 1:05d}"
        client_name = f"{rng.choice(first_names)} {rng.choice(last_names)}"
        advisor = str(rng.choice(advisors))
        region = str(rng.choice(regions, p=region_p))
        channel = str(rng.choice(channels, p=channel_p))
        suitability = int(np.clip(rng.normal(86, 8), 55, 99))
        client_rows.append(
            {
                "ClientID": client_id,
                "ClientName": client_name,
                "ClientSegment": seg,
                "RiskProfile": risk,
                "Region": region,
                "AdvisorName": advisor,
                "OnboardingChannel": channel,
                "JoinMonth": join_month.date().isoformat(),
                "SuitabilityScore": suitability,
                "ModelPortfolio": model,
                "TargetRiskScore": target_risk[risk],
                "FeeBps": fee_bps[seg],
            }
        )
        client_state[client_id] = {
            "aum": base_aum,
            "join_month": join_month,
            "risk_score": float(np.clip(rng.normal(target_risk[risk], 9), 8, 98)),
            "churned": False,
            "last_outflow_pressure": 0.0,
        }

    dim_client = pd.DataFrame(client_rows)
    dim_portfolio = pd.DataFrame(
        [
            {
                "ModelPortfolio": model,
                "RiskProfile": risk,
                "Benchmark": benchmarks[model],
                "TargetEquityPct": alloc["Equity"],
                "TargetFixedIncomePct": alloc["Fixed Income"],
                "TargetAlternativesPct": alloc["Alternatives"],
                "TargetCashPct": alloc["Cash"],
                "TargetCryptoPct": alloc["Crypto"],
            }
            for risk, model in model_by_risk.items()
            for alloc in [target_alloc[model]]
        ]
    )
    dim_date = pd.DataFrame(
        [
            {
                "MonthStart": ts.date().isoformat(),
                "MonthKey": month_key(ts),
                "MonthLabel": month_label(ts),
                "MonthIndex": i + 1,
                "Year": ts.year,
                "Quarter": f"Q{((ts.month - 1) // 3) + 1}",
                "YearQuarter": f"{ts.year} Q{((ts.month - 1) // 3) + 1}",
            }
            for i, ts in enumerate(MONTHS)
        ]
    )

    market_base = []
    for i, ts in enumerate(MONTHS):
        cycle = 0.005 + 0.012 * math.sin(i / 3.2) + 0.006 * math.cos(i / 5.5)
        shock = rng.normal(0, 0.018)
        market_base.append(
            {
                "MonthStart": ts,
                "Equity": cycle + shock + rng.normal(0.004, 0.011),
                "Fixed Income": 0.002 + 0.25 * cycle + rng.normal(0, 0.005),
                "Alternatives": 0.004 + 0.55 * cycle + rng.normal(0, 0.008),
                "Cash": 0.0025 + rng.normal(0, 0.0005),
                "Crypto": 0.012 + 1.85 * cycle + rng.normal(0, 0.065),
            }
        )
    market_returns = pd.DataFrame(market_base)

    fact_rows = []
    alloc_rows = []
    action_rows = []
    for month_idx, ts in enumerate(MONTHS):
        market = market_returns.loc[market_returns["MonthStart"].eq(ts)].iloc[0].to_dict()
        for client in dim_client.itertuples(index=False):
            state = client_state[client.ClientID]
            if ts < state["join_month"] or state["churned"]:
                continue
            begin_aum = float(state["aum"])
            tenure = (ts.year - state["join_month"].year) * 12 + ts.month - state["join_month"].month
            seg_mult = {"Digital Starter": 0.36, "Mass Affluent": 0.52, "HNW": 0.66, "UHNW": 0.88, "Retirement": 0.44}[client.ClientSegment]
            channel_inflow = {
                "Organic App": 0.90,
                "Advisor Referral": 1.18,
                "Paid Search": 0.82,
                "Employer Plan": 1.08,
                "Partner API": 1.12,
            }[client.OnboardingChannel]
            season = 1 + 0.25 * math.sin((ts.month - 1) / 12 * 2 * math.pi)
            inflow_rate = max(0, rng.normal(0.012 * seg_mult * channel_inflow * season, 0.016))
            if tenure <= 1:
                inflow_rate += rng.uniform(0.08, 0.28)
            outflow_rate = max(0, rng.normal(0.007 + 0.0015 * tenure, 0.011))
            if client.ClientSegment == "Digital Starter":
                outflow_rate *= 1.25
            if rng.random() < 0.035:
                outflow_rate += rng.uniform(0.08, 0.24)
            inflow = begin_aum * inflow_rate
            outflow = min(begin_aum * 0.82, begin_aum * outflow_rate)
            net_new_money = inflow - outflow

            alloc = target_alloc[client.ModelPortfolio].copy()
            drift_noise = rng.normal(0, 0.018, len(alloc))
            weights = np.array(list(alloc.values())) + drift_noise
            weights = np.clip(weights, 0.005, 0.94)
            weights = weights / weights.sum()
            weighted_return = 0.0
            drift_abs = 0.0
            for asset_class, weight in zip(alloc.keys(), weights):
                benchmark_pct = alloc[asset_class]
                weighted_return += weight * float(market[asset_class])
                drift_abs += abs(float(weight) - benchmark_pct)
            return_pct = float(np.clip(weighted_return + rng.normal(0, 0.006), -0.16, 0.18))
            benchmark_return_pct = float(
                np.clip(sum(alloc[asset] * float(market[asset]) for asset in alloc.keys()), -0.14, 0.15)
            )
            market_effect = (begin_aum + 0.5 * net_new_money) * return_pct
            end_aum = max(2_500, begin_aum + inflow - outflow + market_effect)
            risk_score = float(np.clip(float(state["risk_score"]) + rng.normal(0, 2.4) + 18 * (return_pct - benchmark_return_pct), 1, 99))
            state["risk_score"] = risk_score
            risk_mismatch = int(abs(risk_score - float(client.TargetRiskScore)) >= 18 or client.SuitabilityScore < 72)
            rebalance_needed = int(drift_abs >= 0.12 or risk_mismatch == 1)
            underperformance = max(0.0, benchmark_return_pct - return_pct)
            churn_risk_score = float(
                np.clip(0.18 + 1.85 * (outflow / max(begin_aum, 1)) + 0.85 * underperformance + 0.22 * risk_mismatch + rng.normal(0, 0.07), 0, 0.98)
            )
            outflow_risk_score = float(np.clip(0.16 + 2.15 * (outflow / max(begin_aum, 1)) + 0.28 * churn_risk_score + rng.normal(0, 0.06), 0, 0.99))
            active = int(end_aum >= 10_000)
            advisory_revenue = end_aum * float(client.FeeBps) / 10000 / 12
            status = "Active"
            if end_aum < 10_000 or outflow > begin_aum * 0.72:
                status = "At Risk"
            if churn_risk_score > 0.90 and outflow > begin_aum * 0.50 and rng.random() < 0.18:
                status = "Churned"
                state["churned"] = True
            fact_rows.append(
                {
                    "MonthStart": ts.date().isoformat(),
                    "ClientID": client.ClientID,
                    "ModelPortfolio": client.ModelPortfolio,
                    "BeginningAUM": round(begin_aum, 2),
                    "Inflows": round(inflow, 2),
                    "Outflows": round(outflow, 2),
                    "NetNewMoney": round(net_new_money, 2),
                    "MarketEffect": round(market_effect, 2),
                    "EndingAUM": round(end_aum, 2),
                    "AdvisoryRevenue": round(advisory_revenue, 2),
                    "PortfolioReturnPct": round(return_pct, 6),
                    "BenchmarkReturnPct": round(benchmark_return_pct, 6),
                    "RiskScore": round(risk_score, 2),
                    "TargetRiskScore": client.TargetRiskScore,
                    "RiskMismatchFlag": risk_mismatch,
                    "RebalanceNeededFlag": rebalance_needed,
                    "ChurnRiskScore": round(churn_risk_score, 4),
                    "OutflowRiskScore": round(outflow_risk_score, 4),
                    "ActiveClientFlag": active,
                    "ClientStatus": status,
                }
            )
            for asset_class, weight in zip(alloc.keys(), weights):
                alloc_rows.append(
                    {
                        "MonthStart": ts.date().isoformat(),
                        "ClientID": client.ClientID,
                        "ModelPortfolio": client.ModelPortfolio,
                        "AssetClass": asset_class,
                        "AllocationPct": round(float(weight), 6),
                        "BenchmarkPct": round(float(alloc[asset_class]), 6),
                        "DriftPct": round(float(weight) - float(alloc[asset_class]), 6),
                        "AllocationAmount": round(end_aum * float(weight), 2),
                    }
                )
            if ts == LATEST_MONTH and (risk_mismatch or rebalance_needed or churn_risk_score >= 0.62 or outflow_risk_score >= 0.60):
                if churn_risk_score >= 0.74:
                    action_type = "Advisor outreach"
                    priority = "High"
                    reason = "Churn risk"
                elif rebalance_needed:
                    action_type = "Rebalance proposal"
                    priority = "Medium"
                    reason = "Allocation drift"
                elif risk_mismatch:
                    action_type = "Suitability review"
                    priority = "Medium"
                    reason = "Risk mismatch"
                else:
                    action_type = "Cashflow check-in"
                    priority = "Low"
                    reason = "Outflow watch"
                action_rows.append(
                    {
                        "ActionID": f"ACT-{len(action_rows) + 1:05d}",
                        "MonthStart": ts.date().isoformat(),
                        "ClientID": client.ClientID,
                        "ActionType": action_type,
                        "Priority": priority,
                        "RiskReason": reason,
                        "Status": str(rng.choice(["Open", "In Progress", "Scheduled"], p=[0.46, 0.34, 0.20])),
                        "ExpectedRetainedAUM": round(end_aum * rng.uniform(0.18, 0.42), 2),
                    }
                )
            state["aum"] = end_aum

    fact_aum = pd.DataFrame(fact_rows)
    fact_allocation = pd.DataFrame(alloc_rows)
    fact_actions = pd.DataFrame(action_rows)
    if fact_actions.empty:
        fact_actions = pd.DataFrame(
            columns=[
                "ActionID",
                "MonthStart",
                "ClientID",
                "ActionType",
                "Priority",
                "RiskReason",
                "Status",
                "ExpectedRetainedAUM",
            ]
        )

    return {
        "DimDate": dim_date,
        "DimClient": dim_client,
        "DimPortfolio": dim_portfolio,
        "FactAUMMonthly": fact_aum,
        "FactAllocationMonthly": fact_allocation,
        "FactRetentionActions": fact_actions,
    }


def prepare_aggregates(tables: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    fact = tables["FactAUMMonthly"].copy()
    clients = tables["DimClient"].copy()
    portfolios = tables["DimPortfolio"].copy()
    alloc = tables["FactAllocationMonthly"].copy()
    actions = tables["FactRetentionActions"].copy()
    fact["MonthStart"] = pd.to_datetime(fact["MonthStart"])
    alloc["MonthStart"] = pd.to_datetime(alloc["MonthStart"])
    fact_client = fact.merge(clients, on="ClientID", how="left", suffixes=("", "_Client"))
    fact_client = fact_client.merge(
        portfolios[["ModelPortfolio", "Benchmark"]],
        on="ModelPortfolio",
        how="left",
    )
    latest = fact_client[fact_client["MonthStart"].eq(LATEST_MONTH)].copy()

    def weighted_return(df: pd.DataFrame, col: str) -> float:
        denom = df["EndingAUM"].sum()
        return 0.0 if denom == 0 else float((df["EndingAUM"] * df[col]).sum() / denom)

    monthly_rows = []
    for month, df in fact_client.groupby("MonthStart"):
        total_aum = df["EndingAUM"].sum()
        beginning = df["BeginningAUM"].sum()
        top10 = df.nlargest(10, "EndingAUM")["EndingAUM"].sum()
        monthly_rows.append(
            {
                "MonthStart": month.date().isoformat(),
                "MonthLabel": month_label(month),
                "MonthIndex": int(((month.year - START_MONTH.year) * 12 + month.month - START_MONTH.month) + 1),
                "Year": int(month.year),
                "TotalAUM": round(total_aum, 2),
                "BeginningAUM": round(beginning, 2),
                "Inflows": round(df["Inflows"].sum(), 2),
                "Outflows": round(df["Outflows"].sum(), 2),
                "NetNewMoney": round(df["NetNewMoney"].sum(), 2),
                "MarketEffect": round(df["MarketEffect"].sum(), 2),
                "AdvisoryRevenue": round(df["AdvisoryRevenue"].sum(), 2),
                "ActiveClients": int(df.loc[df["ActiveClientFlag"].eq(1), "ClientID"].nunique()),
                "PortfolioReturnPct": round(weighted_return(df, "PortfolioReturnPct"), 6),
                "BenchmarkReturnPct": round(weighted_return(df, "BenchmarkReturnPct"), 6),
                "RiskMismatchClients": int(df.loc[df["RiskMismatchFlag"].eq(1), "ClientID"].nunique()),
                "RebalanceNeededClients": int(df.loc[df["RebalanceNeededFlag"].eq(1), "ClientID"].nunique()),
                "HighChurnRiskClients": int(df.loc[df["ChurnRiskScore"].ge(0.70), "ClientID"].nunique()),
                "HighOutflowRiskClients": int(df.loc[df["OutflowRiskScore"].ge(0.65), "ClientID"].nunique()),
                "ChurnRiskAUM": round(df.loc[df["ChurnRiskScore"].ge(0.70), "EndingAUM"].sum(), 2),
                "Top10AUMShare": round(0.0 if total_aum == 0 else top10 / total_aum, 6),
            }
        )
    monthly_kpis = pd.DataFrame(monthly_rows)

    segment_rows = []
    for segment, df in latest.groupby("ClientSegment"):
        segment_rows.append(
            {
                "ClientSegment": segment,
                "TotalAUM": round(df["EndingAUM"].sum(), 2),
                "NetNewMoney": round(df["NetNewMoney"].sum(), 2),
                "AdvisoryRevenue": round(df["AdvisoryRevenue"].sum(), 2),
                "ActiveClients": int(df.loc[df["ActiveClientFlag"].eq(1), "ClientID"].nunique()),
                "PortfolioReturnPct": round(weighted_return(df, "PortfolioReturnPct"), 6),
                "BenchmarkReturnPct": round(weighted_return(df, "BenchmarkReturnPct"), 6),
                "RiskMismatchClients": int(df.loc[df["RiskMismatchFlag"].eq(1), "ClientID"].nunique()),
                "ChurnRiskAUM": round(df.loc[df["ChurnRiskScore"].ge(0.70), "EndingAUM"].sum(), 2),
            }
        )
    segment_summary = pd.DataFrame(segment_rows).sort_values("TotalAUM", ascending=False)

    risk_rows = []
    for risk, df in latest.groupby("RiskProfile"):
        risk_rows.append(
            {
                "RiskProfile": risk,
                "TotalAUM": round(df["EndingAUM"].sum(), 2),
                "ActiveClients": int(df["ClientID"].nunique()),
                "PortfolioReturnPct": round(weighted_return(df, "PortfolioReturnPct"), 6),
                "BenchmarkReturnPct": round(weighted_return(df, "BenchmarkReturnPct"), 6),
                "RiskMismatchClients": int(df.loc[df["RiskMismatchFlag"].eq(1), "ClientID"].nunique()),
                "RebalanceNeededClients": int(df.loc[df["RebalanceNeededFlag"].eq(1), "ClientID"].nunique()),
            }
        )
    risk_summary = pd.DataFrame(risk_rows)

    portfolio_rows = []
    for model, df in latest.groupby("ModelPortfolio"):
        portfolio_rows.append(
            {
                "ModelPortfolio": model,
                "Benchmark": df["Benchmark"].iloc[0],
                "TotalAUM": round(df["EndingAUM"].sum(), 2),
                "NetNewMoney": round(df["NetNewMoney"].sum(), 2),
                "PortfolioReturnPct": round(weighted_return(df, "PortfolioReturnPct"), 6),
                "BenchmarkReturnPct": round(weighted_return(df, "BenchmarkReturnPct"), 6),
                "AlphaPct": round(weighted_return(df, "PortfolioReturnPct") - weighted_return(df, "BenchmarkReturnPct"), 6),
            }
        )
    portfolio_summary = pd.DataFrame(portfolio_rows).sort_values("TotalAUM", ascending=False)

    latest_alloc = alloc[alloc["MonthStart"].eq(LATEST_MONTH)].copy()
    alloc_summary = (
        latest_alloc.groupby("AssetClass", as_index=False)
        .agg(AllocationAmount=("AllocationAmount", "sum"), BenchmarkPct=("BenchmarkPct", "mean"))
        .sort_values("AllocationAmount", ascending=False)
    )
    total_alloc = alloc_summary["AllocationAmount"].sum()
    alloc_summary["AllocationPct"] = np.where(total_alloc == 0, 0, alloc_summary["AllocationAmount"] / total_alloc)
    alloc_summary = alloc_summary[["AssetClass", "AllocationAmount", "AllocationPct", "BenchmarkPct"]]

    top_clients = latest.sort_values("EndingAUM", ascending=False).head(20)[
        [
            "ClientID",
            "ClientName",
            "ClientSegment",
            "RiskProfile",
            "Region",
            "AdvisorName",
            "ModelPortfolio",
            "EndingAUM",
            "NetNewMoney",
            "PortfolioReturnPct",
            "ChurnRiskScore",
            "RiskMismatchFlag",
            "RebalanceNeededFlag",
        ]
    ].copy()

    action_detail = actions.merge(clients[["ClientID", "ClientName", "ClientSegment", "RiskProfile", "Region", "AdvisorName"]], on="ClientID", how="left")
    if not action_detail.empty:
        latest_for_actions = latest[["ClientID", "EndingAUM", "ChurnRiskScore", "OutflowRiskScore"]]
        action_detail = action_detail.merge(latest_for_actions, on="ClientID", how="left")
        action_detail = action_detail.sort_values(["Priority", "ExpectedRetainedAUM"], ascending=[True, False])

    return {
        "MonthlyKPIs": monthly_kpis,
        "SegmentSummaryLatest": segment_summary,
        "RiskProfileSummaryLatest": risk_summary,
        "PortfolioSummaryLatest": portfolio_summary,
        "AllocationLatest": alloc_summary,
        "TopClientsLatest": top_clients,
        "RetentionActionsLatest": action_detail,
    }


def data_quality_report(tables: dict[str, pd.DataFrame], aggregates: dict[str, pd.DataFrame]) -> dict:
    checks = {}
    for name, df in {**tables, **aggregates}.items():
        checks[name] = {
            "rows": int(len(df)),
            "columns": int(len(df.columns)),
            "duplicate_rows": int(df.duplicated().sum()),
            "missing_values": {col: int(df[col].isna().sum()) for col in df.columns if int(df[col].isna().sum()) > 0},
        }
        date_cols = [
            col
            for col in df.columns
            if col.lower() in {"monthstart", "joinmonth"} or col.lower().endswith("date")
        ]
        for col in date_cols:
            try:
                dates = pd.to_datetime(df[col], errors="coerce")
                if dates.notna().any():
                    checks[name][f"{col}_range"] = {
                        "min": dates.min().date().isoformat(),
                        "max": dates.max().date().isoformat(),
                    }
            except Exception:
                pass
    fact = tables["FactAUMMonthly"]
    monthly = aggregates["MonthlyKPIs"]
    latest = monthly.iloc[-1]
    reconciliation = {
        "latest_month": str(latest["MonthStart"]),
        "latest_fact_aum_sum": round(float(fact.loc[fact["MonthStart"].eq(latest["MonthStart"]), "EndingAUM"].sum()), 2),
        "latest_monthly_kpi_aum": round(float(latest["TotalAUM"]), 2),
        "aum_reconciles": bool(
            abs(float(fact.loc[fact["MonthStart"].eq(latest["MonthStart"]), "EndingAUM"].sum()) - float(latest["TotalAUM"])) < 0.01
        ),
        "nnm_formula_pass": bool(
            np.allclose(
                fact["NetNewMoney"].round(2),
                (fact["Inflows"] - fact["Outflows"]).round(2),
                atol=0.02,
            )
        ),
        "ending_aum_nonnegative": bool((fact["EndingAUM"] >= 0).all()),
    }
    return {
        "generated_at": REPORT_DATE.isoformat(),
        "synthetic": True,
        "seed": SEED,
        "latest_complete_month": LATEST_MONTH.date().isoformat(),
        "checks": checks,
        "reconciliation": reconciliation,
        "status": "passed" if all([reconciliation["aum_reconciles"], reconciliation["nnm_formula_pass"], reconciliation["ending_aum_nonnegative"]]) else "review",
    }


MEASURES = [
    ("Latest Month", "MAX ( DimDate[MonthStart] )", "yyyy-mm-dd"),
    ("Total AUM", "SUM ( FactAUMMonthly[EndingAUM] )", "$#,0,,.0M"),
    ("Beginning AUM", "SUM ( FactAUMMonthly[BeginningAUM] )", "$#,0,,.0M"),
    ("Inflows", "SUM ( FactAUMMonthly[Inflows] )", "$#,0,,.0M"),
    ("Outflows", "SUM ( FactAUMMonthly[Outflows] )", "$#,0,,.0M"),
    ("Net New Money", "SUM ( FactAUMMonthly[NetNewMoney] )", "$#,0,,.0M"),
    ("Market Effect", "SUM ( FactAUMMonthly[MarketEffect] )", "$#,0,,.0M"),
    ("Advisory Revenue", "SUM ( FactAUMMonthly[AdvisoryRevenue] )", "$#,0,.0K"),
    ("Allocation Amount", "SUM ( FactAllocationMonthly[AllocationAmount] )", "$#,0,,.0M"),
    ("Active Clients", "CALCULATE ( DISTINCTCOUNT ( FactAUMMonthly[ClientID] ), FactAUMMonthly[ActiveClientFlag] = 1 )", "#,0"),
    ("Net Flow Rate", "DIVIDE ( [Net New Money], [Beginning AUM] )", "0.0%"),
    (
        "Portfolio Return %",
        "DIVIDE ( SUMX ( FactAUMMonthly, FactAUMMonthly[EndingAUM] * FactAUMMonthly[PortfolioReturnPct] ), [Total AUM] )",
        "0.0%",
    ),
    (
        "Benchmark Return %",
        "DIVIDE ( SUMX ( FactAUMMonthly, FactAUMMonthly[EndingAUM] * FactAUMMonthly[BenchmarkReturnPct] ), [Total AUM] )",
        "0.0%",
    ),
    ("Alpha %", "[Portfolio Return %] - [Benchmark Return %]", "0.0%"),
    (
        "Risk Mismatch Clients",
        "CALCULATE ( DISTINCTCOUNT ( FactAUMMonthly[ClientID] ), FactAUMMonthly[RiskMismatchFlag] = 1 )",
        "#,0",
    ),
    (
        "Risk Mismatch Rate",
        "DIVIDE ( [Risk Mismatch Clients], [Active Clients] )",
        "0.0%",
    ),
    (
        "Rebalance Needed Clients",
        "CALCULATE ( DISTINCTCOUNT ( FactAUMMonthly[ClientID] ), FactAUMMonthly[RebalanceNeededFlag] = 1 )",
        "#,0",
    ),
    (
        "Rebalance Needed Rate",
        "DIVIDE ( [Rebalance Needed Clients], [Active Clients] )",
        "0.0%",
    ),
    (
        "High Churn Risk Clients",
        "CALCULATE ( DISTINCTCOUNT ( FactAUMMonthly[ClientID] ), FactAUMMonthly[ChurnRiskScore] >= 0.70 )",
        "#,0",
    ),
    (
        "High Outflow Risk Clients",
        "CALCULATE ( DISTINCTCOUNT ( FactAUMMonthly[ClientID] ), FactAUMMonthly[OutflowRiskScore] >= 0.65 )",
        "#,0",
    ),
    (
        "Churn Risk AUM",
        "SUMX ( FILTER ( FactAUMMonthly, FactAUMMonthly[ChurnRiskScore] >= 0.70 ), FactAUMMonthly[EndingAUM] )",
        "$#,0,,.0M",
    ),
    ("Churn Risk AUM Rate", "DIVIDE ( [Churn Risk AUM], [Total AUM] )", "0.0%"),
    (
        "Top 10 Client AUM Share",
        "VAR t = TOPN ( 10, SUMMARIZE ( DimClient, DimClient[ClientID], \"AUMValue\", [Total AUM] ), [AUMValue], DESC ) RETURN DIVIDE ( SUMX ( t, [AUMValue] ), [Total AUM] )",
        "0.0%",
    ),
    ("Retention Action AUM", "SUM ( FactRetentionActions[ExpectedRetainedAUM] )", "$#,0,,.0M"),
    (
        "Open Retention Actions",
        "COUNTROWS ( FactRetentionActions )",
        "#,0",
    ),
]


def write_model_docs(tables: dict[str, pd.DataFrame]) -> None:
    dictionary_rows = []
    for table_name, df in tables.items():
        grain = {
            "DimDate": "one row per reporting month",
            "DimClient": "one row per client",
            "DimPortfolio": "one row per robo-advisor model portfolio",
            "FactAUMMonthly": "one row per active client and model portfolio per reporting month",
            "FactAllocationMonthly": "one row per active client, model portfolio, month, and asset class",
            "FactRetentionActions": "one row per recommended retention action in the latest month",
        }.get(table_name, "derived aggregate")
        for col in df.columns:
            dictionary_rows.append(
                {
                    "Table": table_name,
                    "Column": col,
                    "DataType": str(df[col].dtype),
                    "Grain": grain,
                    "Nullable": bool(df[col].isna().any()),
                    "Example": "" if df.empty else str(df[col].iloc[0]),
                }
            )
    data_dictionary = pd.DataFrame(dictionary_rows)
    write_csv(MODEL_DIR / "data_dictionary.csv", data_dictionary)

    measure_map = [
        {"Measure": name, "DAX": dax, "Format": fmt, "BusinessRole": classify_measure(name)}
        for name, dax, fmt in MEASURES
    ]
    write_json(MODEL_DIR / "measure_map.json", measure_map)
    write_text(
        MODEL_DIR / "measures.dax",
        "\n\n".join([f"{name} =\n{dax}\n-- Format: {fmt}" for name, dax, fmt in MEASURES]),
    )
    relationships = [
        ("FactAUMMonthly", "MonthStart", "DimDate", "MonthStart", "many-to-one"),
        ("FactAllocationMonthly", "MonthStart", "DimDate", "MonthStart", "many-to-one"),
        ("FactRetentionActions", "MonthStart", "DimDate", "MonthStart", "many-to-one"),
        ("FactAUMMonthly", "ClientID", "DimClient", "ClientID", "many-to-one"),
        ("FactAllocationMonthly", "ClientID", "DimClient", "ClientID", "many-to-one"),
        ("FactRetentionActions", "ClientID", "DimClient", "ClientID", "many-to-one"),
        ("FactAUMMonthly", "ModelPortfolio", "DimPortfolio", "ModelPortfolio", "many-to-one"),
        ("FactAllocationMonthly", "ModelPortfolio", "DimPortfolio", "ModelPortfolio", "many-to-one"),
    ]
    write_json(
        MODEL_DIR / "relationships.json",
        [
            {
                "from_table": src,
                "from_column": src_col,
                "to_table": dst,
                "to_column": dst_col,
                "cardinality": card,
                "cross_filter": "single",
            }
            for src, src_col, dst, dst_col, card in relationships
        ],
    )
    write_text(
        MODEL_DIR / "relationship_map.md",
        "# Relationship Map\n\n"
        + "\n".join([f"- `{src}[{src_col}]` -> `{dst}[{dst_col}]` ({card}, single direction)" for src, src_col, dst, dst_col, card in relationships]),
    )


def classify_measure(name: str) -> str:
    lowered = name.lower()
    if "risk" in lowered or "rebalance" in lowered:
        return "guardrail"
    if "return" in lowered or "alpha" in lowered:
        return "performance"
    if "revenue" in lowered or "aum" in lowered or "money" in lowered or "flow" in lowered:
        return "growth"
    return "diagnostic"


def build_html_dashboard(aggregates: dict[str, pd.DataFrame]) -> str:
    monthly = aggregates["MonthlyKPIs"].copy()
    segment = aggregates["SegmentSummaryLatest"].copy()
    portfolio = aggregates["PortfolioSummaryLatest"].copy()
    allocation = aggregates["AllocationLatest"].copy()
    risk = aggregates["RiskProfileSummaryLatest"].copy()
    top_clients = aggregates["TopClientsLatest"].head(12).copy()
    actions = aggregates["RetentionActionsLatest"].head(80).copy()
    latest = monthly.iloc[-1].to_dict()

    payload = {
        "monthly": monthly.to_dict(orient="records"),
        "segment": segment.to_dict(orient="records"),
        "portfolio": portfolio.to_dict(orient="records"),
        "allocation": allocation.to_dict(orient="records"),
        "risk": risk.to_dict(orient="records"),
        "topClients": top_clients.to_dict(orient="records"),
        "actions": actions.to_dict(orient="records"),
        "latest": latest,
        "meta": {
            "reportDate": REPORT_DATE.isoformat(),
            "latestMonth": LATEST_MONTH.date().isoformat(),
            "seed": SEED,
            "source": "Deterministic synthetic WealthTech/Robo-Advisor portfolio dataset.",
        },
    }
    payload_json = json.dumps(payload, ensure_ascii=False)
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>WealthTech / Robo-Advisor AUM Dashboard</title>
<style>
:root {{
  --bg: #f5f7fa;
  --panel: #ffffff;
  --ink: #172033;
  --muted: #667085;
  --line: #d6dee8;
  --navy: #102033;
  --blue: #2563eb;
  --teal: #0f8b8d;
  --green: #16a34a;
  --amber: #d97706;
  --red: #dc2626;
  --indigo: #4f46e5;
}}
* {{ box-sizing: border-box; }}
body {{
  margin: 0;
  background: var(--bg);
  color: var(--ink);
  font-family: "Segoe UI", Arial, sans-serif;
  letter-spacing: 0;
}}
.app {{ min-height: 100vh; display: grid; grid-template-columns: 248px 1fr; }}
.side {{
  background: var(--navy);
  color: #f8fafc;
  padding: 22px 18px;
  position: sticky;
  top: 0;
  height: 100vh;
}}
.brand {{ display: grid; gap: 10px; margin-bottom: 24px; }}
.mark {{
  width: 42px; height: 42px; border-radius: 8px;
  background: linear-gradient(135deg, #0f8b8d, #2563eb);
  display: grid; place-items: center; font-weight: 800;
}}
h1 {{ font-size: 18px; line-height: 1.15; margin: 0; }}
.side small {{ color: #c9d6e4; line-height: 1.45; }}
.tab {{
  width: 100%;
  border: 1px solid rgba(255,255,255,.12);
  color: #dbe7f3;
  background: rgba(255,255,255,.04);
  padding: 11px 12px;
  border-radius: 7px;
  margin-bottom: 8px;
  text-align: left;
  cursor: pointer;
  font-weight: 600;
}}
.tab.active {{ background: #f8fafc; color: var(--navy); border-color: #f8fafc; }}
.filters {{ margin-top: 18px; display: grid; gap: 10px; }}
label {{ color: #c9d6e4; font-size: 11px; font-weight: 700; text-transform: uppercase; }}
select {{
  width: 100%; border: 1px solid rgba(255,255,255,.18); border-radius: 7px;
  background: rgba(255,255,255,.08); color: #f8fafc; padding: 9px 10px;
}}
select option {{ color: #172033; }}
.main {{ padding: 22px; min-width: 0; }}
.topbar {{ display:flex; justify-content:space-between; align-items:flex-start; gap: 16px; margin-bottom: 18px; }}
.topbar h2 {{ margin: 0 0 5px; font-size: 25px; }}
.topbar p {{ margin: 0; color: var(--muted); }}
.freshness {{ color: var(--muted); font-size: 12px; text-align:right; }}
.grid {{ display: grid; gap: 14px; }}
.kpis {{ grid-template-columns: repeat(6, minmax(136px, 1fr)); }}
.cards4 {{ grid-template-columns: repeat(4, minmax(170px, 1fr)); }}
.panel {{
  background: var(--panel); border: 1px solid var(--line); border-radius: 8px;
  box-shadow: 0 2px 8px rgba(16, 32, 51, .05);
  min-width: 0;
}}
.card {{ padding: 14px 14px 12px; min-height: 90px; }}
.card .label {{ font-size: 11px; color: var(--muted); font-weight: 800; text-transform: uppercase; }}
.card .value {{ font-size: 22px; font-weight: 800; margin-top: 8px; white-space: nowrap; }}
.card .delta {{ font-size: 12px; color: var(--muted); margin-top: 6px; }}
.blue {{ color: var(--blue); }} .teal {{ color: var(--teal); }} .green {{ color: var(--green); }}
.amber {{ color: var(--amber); }} .red {{ color: var(--red); }} .indigo {{ color: var(--indigo); }}
.layout-2 {{ grid-template-columns: minmax(0, 1.2fr) minmax(340px, .8fr); margin-top: 14px; }}
.layout-3 {{ grid-template-columns: minmax(0, .9fr) minmax(0, .9fr) minmax(330px, .7fr); margin-top: 14px; }}
.chart {{ padding: 14px; min-height: 280px; }}
.chart h3 {{ margin: 0 0 2px; font-size: 14px; }}
.chart p {{ margin: 0 0 10px; font-size: 12px; color: var(--muted); }}
svg {{ width: 100%; height: 220px; display:block; overflow: visible; }}
.legend {{ display:flex; gap: 14px; flex-wrap: wrap; color: var(--muted); font-size: 12px; margin-top: 8px; }}
.legend span::before {{ content: ""; display:inline-block; width:10px; height:10px; border-radius:2px; margin-right:5px; background: var(--c); }}
table {{ width: 100%; border-collapse: collapse; font-size: 12px; }}
th, td {{ padding: 9px 10px; border-bottom: 1px solid #edf1f5; text-align: left; white-space: nowrap; }}
th {{ color: var(--muted); font-size: 11px; text-transform: uppercase; }}
td.num, th.num {{ text-align: right; }}
.table-wrap {{ overflow:auto; max-height: 310px; }}
.pill {{ display:inline-flex; padding: 3px 7px; border-radius: 999px; font-weight: 700; font-size: 11px; background:#eef2f7; color:#344054; }}
.pill.High {{ color:#991b1b; background:#fee2e2; }}
.pill.Medium {{ color:#92400e; background:#fef3c7; }}
.pill.Low {{ color:#065f46; background:#d1fae5; }}
.tabpage {{ display:none; }} .tabpage.active {{ display:block; }}
.method {{ margin-top: 14px; padding: 12px 14px; font-size: 12px; color: var(--muted); }}
@media (max-width: 1100px) {{
  .app {{ grid-template-columns: 1fr; }}
  .side {{ position: static; height: auto; }}
  .kpis, .cards4, .layout-2, .layout-3 {{ grid-template-columns: 1fr 1fr; }}
}}
@media (max-width: 680px) {{
  .main {{ padding: 14px; }}
  .kpis, .cards4, .layout-2, .layout-3 {{ grid-template-columns: 1fr; }}
  .topbar {{ display:block; }}
  .freshness {{ text-align:left; margin-top:8px; }}
}}
</style>
</head>
<body>
<div class="app">
  <aside class="side">
    <div class="brand">
      <div class="mark">WT</div>
      <div>
        <h1>WealthTech AUM Dashboard</h1>
        <small>Robo-advisor growth, portfolio quality, suitability, and retention actions.</small>
      </div>
    </div>
    <button class="tab active" data-tab="overview">AUM & Revenue Overview</button>
    <button class="tab" data-tab="segments">Portfolio & Client Segments</button>
    <button class="tab" data-tab="risk">Risk, Suitability & Retention</button>
    <div class="filters">
      <label for="segmentFilter">Client Segment</label>
      <select id="segmentFilter"></select>
      <label for="riskFilter">Risk Profile</label>
      <select id="riskFilter"></select>
      <label for="regionFilter">Region</label>
      <select id="regionFilter"></select>
    </div>
  </aside>
  <main class="main">
    <div class="topbar">
      <div>
        <h2 id="pageTitle">AUM & Revenue Overview</h2>
        <p id="pageSubtitle">Executive view of AUM, net new money, flows, revenue, and active clients.</p>
      </div>
      <div class="freshness">Synthetic portfolio demo<br>Latest complete month: May 2026</div>
    </div>

    <section id="overview" class="tabpage active">
      <div class="grid kpis" id="overviewKpis"></div>
      <div class="grid layout-2">
        <div class="panel chart">
          <h3>AUM Growth Trend</h3><p>Monthly ending AUM; advisory revenue is carried in the KPI ribbon.</p>
          <svg id="aumTrend"></svg><div class="legend"><span style="--c:var(--blue)">AUM</span></div>
        </div>
        <div class="panel chart">
          <h3>Flow Composition</h3><p>Inflows and outflows explain net new money.</p>
          <svg id="flowBars"></svg><div class="legend"><span style="--c:var(--green)">Inflows</span><span style="--c:var(--red)">Outflows</span></div>
        </div>
      </div>
      <div class="grid layout-2">
        <div class="panel chart">
          <h3>AUM by Client Segment</h3><p>Client mix and monetization base.</p>
          <svg id="segmentBars"></svg>
        </div>
        <div class="panel chart">
          <h3>Top Client Concentration</h3><p>Largest relationships and retention exposure.</p>
          <div class="table-wrap"><table id="topClientTable"></table></div>
        </div>
      </div>
    </section>

    <section id="segments" class="tabpage">
      <div class="grid cards4" id="segmentKpis"></div>
      <div class="grid layout-3">
        <div class="panel chart">
          <h3>Return vs Benchmark</h3><p>Weighted portfolio return versus assigned benchmark.</p>
          <svg id="returnTrend"></svg><div class="legend"><span style="--c:var(--blue)">Portfolio</span><span style="--c:var(--amber)">Benchmark</span></div>
        </div>
        <div class="panel chart">
          <h3>Asset Allocation</h3><p>Latest AUM by asset class.</p>
          <svg id="allocationDonut"></svg>
        </div>
        <div class="panel chart">
          <h3>AUM by Risk Profile</h3><p>Risk bands drive allocation and suitability monitoring.</p>
          <svg id="riskBars"></svg>
        </div>
      </div>
      <div class="panel chart">
        <h3>Portfolio Model Detail</h3><p>Model-level AUM, alpha, and benchmark comparison.</p>
        <div class="table-wrap"><table id="portfolioTable"></table></div>
      </div>
    </section>

    <section id="risk" class="tabpage">
      <div class="grid kpis" id="riskKpis"></div>
      <div class="grid layout-3">
        <div class="panel chart">
          <h3>Risk Mismatch Trend</h3><p>Suitability drift and profile mismatch by month.</p>
          <svg id="riskMismatchTrend"></svg>
        </div>
        <div class="panel chart">
          <h3>Churn Risk AUM by Segment</h3><p>AUM exposed to churn-risk threshold.</p>
          <svg id="churnSegmentBars"></svg>
        </div>
        <div class="panel chart">
          <h3>Retention Action Mix</h3><p>Next-best action queue for advisors.</p>
          <svg id="actionBars"></svg>
        </div>
      </div>
      <div class="panel chart">
        <h3>Retention Action Queue</h3><p>High-value clients needing outreach, suitability review, or rebalancing.</p>
        <div class="table-wrap"><table id="actionsTable"></table></div>
      </div>
    </section>

    <div class="panel method">
      Source: deterministic synthetic dataset, seed {SEED}. Definitions and DAX are in <code>model/</code>; validation is in <code>qa/</code>.
      Design references include Tableau AUM accelerators, financial dashboard galleries, and wealth-management analytics patterns documented in <code>docs/design_research_notes.md</code>.
    </div>
  </main>
</div>
<script>
const DATA = {payload_json};
const colors = {{ blue:'#2563eb', teal:'#0f8b8d', green:'#16a34a', amber:'#d97706', red:'#dc2626', indigo:'#4f46e5', muted:'#667085', line:'#d6dee8' }};
const fmtMoney = v => {{
  v = Number(v || 0); const s = v < 0 ? '-' : ''; v = Math.abs(v);
  if (v >= 1e9) return `${{s}}$${{(v/1e9).toFixed(2)}}B`;
  if (v >= 1e6) return `${{s}}$${{(v/1e6).toFixed(1)}}M`;
  if (v >= 1e3) return `${{s}}$${{(v/1e3).toFixed(1)}}K`;
  return `${{s}}$${{v.toFixed(0)}}`;
}};
const fmtNum = v => Number(v || 0).toLocaleString();
const fmtPct = v => `${{(Number(v || 0)*100).toFixed(1)}}%`;
const card = (label, value, delta, cls='blue') => `<div class="panel card"><div class="label">${{label}}</div><div class="value ${{cls}}">${{value}}</div><div class="delta">${{delta}}</div></div>`;
function setOptions(id, values) {{
  const el = document.getElementById(id); el.innerHTML = '<option value="All">All</option>' + values.map(v => `<option>${{v}}</option>`).join('');
}}
function lineChart(id, rows, series, opts={{}}) {{
  const svg = document.getElementById(id), w = svg.clientWidth || 700, h = 220, pad = {{l:46,r:16,t:12,b:34}};
  const vals = rows.flatMap(r => series.map(s => Number(r[s.key] || 0)));
  const min = opts.zero ? 0 : Math.min(...vals), max = Math.max(...vals);
  const y = v => h-pad.b - ((Number(v)-min) / Math.max(1, max-min)) * (h-pad.t-pad.b);
  const x = i => pad.l + i * ((w-pad.l-pad.r) / Math.max(1, rows.length-1));
  let out = `<line x1="${{pad.l}}" y1="${{h-pad.b}}" x2="${{w-pad.r}}" y2="${{h-pad.b}}" stroke="${{colors.line}}"/>`;
  series.forEach(s => {{
    const points = rows.map((r,i)=>`${{x(i)}},${{y(r[s.key])}}`).join(' ');
    out += `<polyline fill="none" stroke="${{s.color}}" stroke-width="2.5" points="${{points}}"/>`;
  }});
  rows.forEach((r,i)=> {{ if (i % 4 === 0 || i === rows.length-1) out += `<text x="${{x(i)}}" y="${{h-12}}" text-anchor="middle" font-size="10" fill="${{colors.muted}}">${{r.MonthLabel.split(' ')[0]}}</text>`; }});
  out += `<text x="4" y="18" font-size="10" fill="${{colors.muted}}">${{opts.formatMax ? opts.formatMax(max) : max.toFixed(0)}}</text>`;
  svg.setAttribute('viewBox', `0 0 ${{w}} ${{h}}`); svg.innerHTML = out;
}}
function barChart(id, rows, labelKey, valueKey, color, formatter=fmtMoney) {{
  const svg = document.getElementById(id), w = svg.clientWidth || 500, h = 220, pad = {{l:118,r:18,t:10,b:22}};
  const data = rows.slice(0, 8), max = Math.max(...data.map(r => Math.abs(Number(r[valueKey] || 0))), 1);
  const bh = (h-pad.t-pad.b) / data.length - 8;
  let out = '';
  data.forEach((r,i)=> {{
    const y = pad.t + i * ((h-pad.t-pad.b) / data.length);
    const bw = Math.abs(Number(r[valueKey] || 0)) / max * (w-pad.l-pad.r);
    out += `<text x="0" y="${{y+bh*.65}}" font-size="10" fill="${{colors.muted}}">${{String(r[labelKey]).slice(0,18)}}</text>`;
    out += `<rect x="${{pad.l}}" y="${{y}}" width="${{bw}}" height="${{bh}}" rx="4" fill="${{color}}"/>`;
    out += `<text x="${{pad.l+bw+5}}" y="${{y+bh*.65}}" font-size="10" fill="${{colors.muted}}">${{formatter(r[valueKey])}}</text>`;
  }});
  svg.setAttribute('viewBox', `0 0 ${{w}} ${{h}}`); svg.innerHTML = out;
}}
function groupedFlow(id, rows) {{
  const svg = document.getElementById(id), w = svg.clientWidth || 500, h = 220, pad = {{l:34,r:14,t:10,b:30}};
  const vals = rows.flatMap(r => [Number(r.Inflows), Number(r.Outflows)]);
  const max = Math.max(...vals, 1); const bw = (w-pad.l-pad.r)/rows.length * .34;
  let out = `<line x1="${{pad.l}}" y1="${{h-pad.b}}" x2="${{w-pad.r}}" y2="${{h-pad.b}}" stroke="${{colors.line}}"/>`;
  rows.forEach((r,i)=> {{
    const x0 = pad.l + i*((w-pad.l-pad.r)/rows.length)+2;
    const h1 = Number(r.Inflows)/max*(h-pad.t-pad.b); const h2 = Number(r.Outflows)/max*(h-pad.t-pad.b);
    out += `<rect x="${{x0}}" y="${{h-pad.b-h1}}" width="${{bw}}" height="${{h1}}" fill="${{colors.green}}" rx="3"/>`;
    out += `<rect x="${{x0+bw+2}}" y="${{h-pad.b-h2}}" width="${{bw}}" height="${{h2}}" fill="${{colors.red}}" rx="3"/>`;
    if (i % 5 === 0) out += `<text x="${{x0}}" y="${{h-10}}" font-size="9" fill="${{colors.muted}}">${{r.MonthLabel.split(' ')[0]}}</text>`;
  }});
  svg.setAttribute('viewBox', `0 0 ${{w}} ${{h}}`); svg.innerHTML = out;
}}
function donut(id, rows) {{
  const svg = document.getElementById(id), w = svg.clientWidth || 360, h = 220, cx=105, cy=108, r=74, sw=24;
  const total = rows.reduce((a,r)=>a+Number(r.AllocationAmount||0),0); let a0=-Math.PI/2;
  const palette=[colors.blue, colors.teal, colors.green, colors.amber, colors.indigo];
  function arc(a1,a2) {{
    const x1=cx+r*Math.cos(a1), y1=cy+r*Math.sin(a1), x2=cx+r*Math.cos(a2), y2=cy+r*Math.sin(a2);
    const large = a2-a1 > Math.PI ? 1 : 0; return `M ${{x1}} ${{y1}} A ${{r}} ${{r}} 0 ${{large}} 1 ${{x2}} ${{y2}}`;
  }}
  let out = '';
  rows.forEach((row,i)=> {{ const a1=a0, a2=a0 + Number(row.AllocationAmount||0)/total*Math.PI*2; out += `<path d="${{arc(a1,a2)}}" fill="none" stroke="${{palette[i%palette.length]}}" stroke-width="${{sw}}" />`; a0=a2; }});
  out += `<text x="${{cx}}" y="${{cy-4}}" text-anchor="middle" font-size="18" font-weight="800" fill="#172033">${{fmtMoney(total)}}</text><text x="${{cx}}" y="${{cy+16}}" text-anchor="middle" font-size="11" fill="${{colors.muted}}">allocated</text>`;
  rows.forEach((row,i)=> {{ out += `<rect x="210" y="${{32+i*28}}" width="10" height="10" rx="2" fill="${{palette[i%palette.length]}}"/><text x="226" y="${{41+i*28}}" font-size="11" fill="${{colors.muted}}">${{row.AssetClass}} ${{fmtPct(row.AllocationPct)}}</text>`; }});
  svg.setAttribute('viewBox', `0 0 ${{w}} ${{h}}`); svg.innerHTML = out;
}}
function table(id, headers, rows) {{
  document.getElementById(id).innerHTML = `<thead><tr>${{headers.map(h=>`<th class="${{h.cls||''}}">${{h.label}}</th>`).join('')}}</tr></thead><tbody>` +
    rows.map(r => `<tr>${{headers.map(h=>`<td class="${{h.cls||''}}">${{h.render ? h.render(r[h.key], r) : (r[h.key] ?? '')}}</td>`).join('')}}</tr>`).join('') + '</tbody>';
}}
function render() {{
  const latest = DATA.latest, monthly = DATA.monthly.slice(-18);
  document.getElementById('overviewKpis').innerHTML = [
    card('Total AUM', fmtMoney(latest.TotalAUM), 'Ending AUM, May 2026', 'blue'),
    card('Net New Money', fmtMoney(latest.NetNewMoney), `Flow rate ${{fmtPct(latest.NetNewMoney/latest.BeginningAUM)}}`, 'teal'),
    card('Inflows', fmtMoney(latest.Inflows), 'Gross client deposits', 'green'),
    card('Outflows', fmtMoney(latest.Outflows), 'Withdrawals/transfers', 'red'),
    card('Advisory Revenue', fmtMoney(latest.AdvisoryRevenue), 'Monthly recurring fees', 'indigo'),
    card('Active Clients', fmtNum(latest.ActiveClients), 'Funded accounts', 'amber')
  ].join('');
  lineChart('aumTrend', monthly, [{{key:'TotalAUM', color:colors.blue}}], {{zero:true, formatMax:fmtMoney}});
  groupedFlow('flowBars', monthly.slice(-14));
  barChart('segmentBars', DATA.segment, 'ClientSegment', 'TotalAUM', colors.blue, fmtMoney);
  table('topClientTable', [
    {{label:'Client', key:'ClientName'}}, {{label:'Segment', key:'ClientSegment'}}, {{label:'AUM', key:'EndingAUM', cls:'num', render:fmtMoney}},
    {{label:'Return', key:'PortfolioReturnPct', cls:'num', render:fmtPct}}
  ], DATA.topClients);
  document.getElementById('segmentKpis').innerHTML = [
    card('Portfolio Return', fmtPct(latest.PortfolioReturnPct), 'Weighted client return', 'blue'),
    card('Benchmark Return', fmtPct(latest.BenchmarkReturnPct), 'Assigned benchmarks', 'amber'),
    card('Alpha', fmtPct(latest.PortfolioReturnPct-latest.BenchmarkReturnPct), 'Return spread', latest.PortfolioReturnPct >= latest.BenchmarkReturnPct ? 'green':'red'),
    card('Top 10 AUM Share', fmtPct(latest.Top10AUMShare), 'Concentration guardrail', 'indigo')
  ].join('');
  lineChart('returnTrend', monthly, [{{key:'PortfolioReturnPct', color:colors.blue}}, {{key:'BenchmarkReturnPct', color:colors.amber}}], {{formatMax:fmtPct}});
  donut('allocationDonut', DATA.allocation);
  barChart('riskBars', DATA.risk, 'RiskProfile', 'TotalAUM', colors.teal, fmtMoney);
  table('portfolioTable', [
    {{label:'Model', key:'ModelPortfolio'}}, {{label:'Benchmark', key:'Benchmark'}}, {{label:'AUM', key:'TotalAUM', cls:'num', render:fmtMoney}},
    {{label:'NNM', key:'NetNewMoney', cls:'num', render:fmtMoney}}, {{label:'Return', key:'PortfolioReturnPct', cls:'num', render:fmtPct}},
    {{label:'Benchmark', key:'BenchmarkReturnPct', cls:'num', render:fmtPct}}, {{label:'Alpha', key:'AlphaPct', cls:'num', render:fmtPct}}
  ], DATA.portfolio);
  document.getElementById('riskKpis').innerHTML = [
    card('Risk Mismatch', fmtNum(latest.RiskMismatchClients), `${{fmtPct(latest.RiskMismatchClients/latest.ActiveClients)}} of active clients`, 'red'),
    card('Rebalance Needed', fmtNum(latest.RebalanceNeededClients), `${{fmtPct(latest.RebalanceNeededClients/latest.ActiveClients)}} of active clients`, 'amber'),
    card('Churn Risk AUM', fmtMoney(latest.ChurnRiskAUM), `${{fmtPct(latest.ChurnRiskAUM/latest.TotalAUM)}} of AUM`, 'red'),
    card('High Churn Clients', fmtNum(latest.HighChurnRiskClients), 'Risk score >= 0.70', 'red'),
    card('High Outflow Risk', fmtNum(latest.HighOutflowRiskClients), 'Outflow score >= 0.65', 'amber'),
    card('Action AUM', fmtMoney(DATA.actions.reduce((a,r)=>a+Number(r.ExpectedRetainedAUM||0),0)), 'Expected retained AUM', 'green')
  ].join('');
  lineChart('riskMismatchTrend', monthly, [{{key:'RiskMismatchClients', color:colors.red}}, {{key:'RebalanceNeededClients', color:colors.amber}}], {{zero:true, formatMax:fmtNum}});
  barChart('churnSegmentBars', DATA.segment, 'ClientSegment', 'ChurnRiskAUM', colors.red, fmtMoney);
  const mix = Object.values(DATA.actions.reduce((a,r)=>{{ a[r.ActionType] = a[r.ActionType] || {{ActionType:r.ActionType, Count:0}}; a[r.ActionType].Count++; return a; }}, {{}}));
  barChart('actionBars', mix, 'ActionType', 'Count', colors.green, fmtNum);
  table('actionsTable', [
    {{label:'Priority', key:'Priority', render:v=>`<span class="pill ${{v}}">${{v}}</span>`}}, {{label:'Client', key:'ClientName'}}, {{label:'Segment', key:'ClientSegment'}},
    {{label:'Action', key:'ActionType'}}, {{label:'Reason', key:'RiskReason'}}, {{label:'Status', key:'Status'}},
    {{label:'Retained AUM', key:'ExpectedRetainedAUM', cls:'num', render:fmtMoney}}, {{label:'Churn', key:'ChurnRiskScore', cls:'num', render:v=>Number(v||0).toFixed(2)}}
  ], DATA.actions);
}}
document.querySelectorAll('.tab').forEach(btn => btn.addEventListener('click', () => {{
  document.querySelectorAll('.tab,.tabpage').forEach(el => el.classList.remove('active'));
  btn.classList.add('active'); document.getElementById(btn.dataset.tab).classList.add('active');
  const titles = {{
    overview: ['AUM & Revenue Overview','Executive view of AUM, net new money, flows, revenue, and active clients.'],
    segments: ['Portfolio & Client Segments','Performance versus benchmark, allocation, concentration, and client mix.'],
    risk: ['Risk, Suitability & Retention','Mismatch, rebalance needs, churn risk, and advisor action queue.']
  }};
  document.getElementById('pageTitle').textContent = titles[btn.dataset.tab][0];
  document.getElementById('pageSubtitle').textContent = titles[btn.dataset.tab][1];
  setTimeout(render, 30);
}}));
setOptions('segmentFilter', [...new Set(DATA.segment.map(r=>r.ClientSegment))]);
setOptions('riskFilter', [...new Set(DATA.risk.map(r=>r.RiskProfile))]);
setOptions('regionFilter', ['North America','Europe','APAC','LATAM']);
render();
</script>
</body>
</html>"""


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


def visual_id() -> str:
    return uuid.uuid4().hex[:20]


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


MEASURE_FORMATS = {name: fmt for name, _, fmt in MEASURES}


def measure_transform(measure: str, display: str, role: str) -> dict:
    return {
        "displayName": display,
        "queryName": f"{MEASURE_TABLE}.{measure}",
        "roles": {role: True},
        "type": {"category": None, "underlyingType": 259},
        "expr": {"Measure": {"Expression": entity_ref("m"), "Property": measure}},
        "format": MEASURE_FORMATS.get(measure, "#,0"),
        "sort": 2,
        "sortOrder": 0,
    }


def make_query(from_items: list[dict], selects: list[dict], order_by: dict | None = None) -> str:
    query = {"Version": 2, "From": from_items, "Select": selects}
    if order_by:
        query["OrderBy"] = [order_by]
    return json.dumps(
        {
            "Commands": [
                {
                    "SemanticQueryDataShapeCommand": {
                        "Query": query,
                        "Binding": {
                            "Primary": {"Groupings": [{"Projections": list(range(len(selects)))}]},
                            "DataReduction": {"DataVolume": 4, "Primary": {"Window": {"Count": 1000}}},
                            "Version": 1,
                        },
                        "ExecutionMetricsKind": 1,
                    }
                }
            ]
        },
        separators=(",", ":"),
    )


def data_transforms(objects: dict, roles: list[tuple[str, int, bool]], metadata: list[dict], selects: list[dict], projection_ordering: dict, active_items: dict | None = None) -> str:
    payload = {
        "objects": objects,
        "projectionOrdering": projection_ordering,
        "queryMetadata": {"Select": metadata},
        "visualElements": [{"DataRoles": [{"Name": role, "Projection": idx, "isActive": active} for role, idx, active in roles]}],
        "selects": selects,
    }
    if active_items:
        payload["projectionActiveItems"] = active_items
    return json.dumps(payload, separators=(",", ":"))


def visual_frame(title: str | None = None, subtitle: str | None = None, *, fill: str = PANEL_BG, border_fill: str = PANEL_BORDER, radius: float = 8.0) -> dict:
    frame = {
        "background": [{"properties": {"show": pbi_literal(True), "color": color(fill), "transparency": pbi_literal(0.0)}}],
        "border": [{"properties": {"show": pbi_literal(True), "color": color(border_fill), "radius": pbi_literal(radius), "width": pbi_literal(1.0)}}],
        "dropShadow": [{"properties": {"show": pbi_literal(True), "position": text("Outer"), "color": color("#0F172A"), "transparency": pbi_literal(88.0), "angle": pbi_literal(45.0), "distance": pbi_literal(2.0)}}],
        "visualHeader": [{"properties": {"show": pbi_literal(False)}}],
    }
    if title:
        frame["title"] = [{"properties": {"show": pbi_literal(True), "text": text(title), "fontFamily": text("Segoe UI Semibold"), "fontSize": pbi_literal(9.0), "fontColor": color(TEXT_DARK), "alignment": text("left")}}]
    if subtitle:
        frame["subTitle"] = [{"properties": {"show": pbi_literal(True), "text": text(subtitle), "fontFamily": text("Segoe UI"), "fontSize": pbi_literal(7.0), "fontColor": color(TEXT_MUTED)}}]
    return frame


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
                                {"value": title, "textStyle": {"fontFamily": "Segoe UI Semibold", "fontSize": "20pt", "color": TEXT_LIGHT}},
                                {"value": f"\n{subtitle}", "textStyle": {"fontFamily": "Segoe UI", "fontSize": "8pt", "color": TEXT_LIGHT_MUTED}},
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


def shape_box(pos: dict, fill: str) -> dict:
    objects = {"general": [{"properties": {"paragraphs": [{"textRuns": [{"value": " ", "textStyle": {"fontFamily": "Segoe UI", "fontSize": "1pt", "color": fill}}]}]}}]}
    config = {
        "name": visual_id(),
        "singleVisual": {
            "visualType": "textbox",
            "drillFilterOtherVisuals": True,
            "objects": objects,
            "vcObjects": {
                "background": [{"properties": {"show": pbi_literal(True), "color": color(fill), "transparency": pbi_literal(0.0)}}],
                "border": [{"properties": {"show": pbi_literal(False)}}],
                "visualHeader": [{"properties": {"show": pbi_literal(False)}}],
            },
        },
    }
    return add_container(config, pos)


def card_visual(measure: str, display: str, pos: dict, value_color: str = BLUE) -> dict:
    qref = f"{MEASURE_TABLE}.{measure}"
    objects = {
        "value": [{"properties": {"fontSize": pbi_literal(21.0), "fontFamily": text("Segoe UI Semibold"), "fontColor": color(value_color)}, "selector": {"metadata": qref}}],
        "label": [{"properties": {"show": pbi_literal(False)}}],
        "divider": [{"properties": {"show": pbi_literal(False)}, "selector": {"metadata": qref}}],
    }
    from_items = [{"Name": "m", "Entity": MEASURE_TABLE, "Type": 0}]
    selects = [measure_select("m", measure, display)]
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
            "vcObjects": visual_frame(display),
        },
    }
    transforms = data_transforms(
        objects,
        [("Data", 0, False)],
        [{"Restatement": display, "Name": qref, "Type": 1, "Format": MEASURE_FORMATS.get(measure, "#,0")}],
        [measure_transform(measure, display, "Data")],
        {"Data": [0]},
    )
    return add_container(config, pos, make_query(from_items, selects), transforms)


def slicer(table: str, column: str, display: str, pos: dict) -> dict:
    qref = f"{table}.{column}"
    objects = {
        "data": [{"properties": {"mode": text("Dropdown")}}],
        "selection": [{"properties": {"selectAllCheckboxEnabled": pbi_literal(True), "singleSelect": pbi_literal(False)}}],
        "header": [{"properties": {"show": pbi_literal(False), "text": text(display)}}],
        "items": [{"properties": {"textSize": pbi_literal(7.5), "fontColor": color(TEXT_DARK)}}],
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
            "vcObjects": visual_frame(display),
        },
    }
    transforms = data_transforms(
        objects,
        [("Values", 0, True)],
        [{"Restatement": display, "Name": qref, "Type": 2048}],
        [column_transform("f", table, column, display, "Values")],
        {"Values": [0]},
    )
    return add_container(config, pos, make_query(from_items, selects), transforms)


def chart_objects(fill: str = BLUE, show_labels: bool = False) -> dict:
    return {
        "valueAxis": [{"properties": {"showAxisTitle": pbi_literal(False), "gridlineShow": pbi_literal(False), "labelDisplayUnits": pbi_literal(1000.0)}}],
        "categoryAxis": [{"properties": {"showAxisTitle": pbi_literal(False), "gridlineShow": pbi_literal(False), "concatenateLabels": pbi_literal(False), "fontSize": pbi_literal(7.0)}}],
        "labels": [{"properties": {"show": pbi_literal(show_labels), "fontSize": pbi_literal(7.0), "fontColor": color(SLATE)}}],
        "legend": [{"properties": {"showTitle": pbi_literal(False), "position": text("Top")}}],
        "dataPoint": [{"properties": {"fill": color(fill)}}],
    }


def single_measure_chart(visual_type: str, title: str, subtitle: str, category_table: str, category_column: str, category_display: str, measure: str, measure_display: str, pos: dict, fill: str = BLUE, order_column: str | None = None, order_measure: bool = False, ascending: bool = True) -> dict:
    category_ref = f"{category_table}.{category_column}"
    measure_ref = f"{MEASURE_TABLE}.{measure}"
    objects = chart_objects(fill=fill, show_labels=False)
    from_items = [{"Name": "c", "Entity": category_table, "Type": 0}, {"Name": "m", "Entity": MEASURE_TABLE, "Type": 0}]
    selects = [column_select("c", category_table, category_column, category_display), measure_select("m", measure, measure_display)]
    order_by = None
    if order_column:
        order_by = {"Direction": 1 if ascending else 2, "Expression": {"Column": {"Expression": source_ref("c"), "Property": order_column}}}
    elif order_measure:
        order_by = {"Direction": 1 if ascending else 2, "Expression": {"Measure": {"Expression": source_ref("m"), "Property": measure}}}
    config = {
        "name": visual_id(),
        "singleVisual": {
            "visualType": visual_type,
            "projections": {"Category": [{"queryRef": category_ref, "active": True}], "Y": [{"queryRef": measure_ref}]},
            "prototypeQuery": {"Version": 2, "From": from_items, "Select": selects, **({"OrderBy": [order_by]} if order_by else {})},
            "drillFilterOtherVisuals": True,
            "hasDefaultSort": True,
            "objects": objects,
            "vcObjects": visual_frame(title, subtitle),
        },
    }
    transforms = data_transforms(
        objects,
        [("Category", 0, True), ("Y", 1, False)],
        [{"Restatement": category_display, "Name": category_ref, "Type": 2048}, {"Restatement": measure_display, "Name": measure_ref, "Type": 1, "Format": MEASURE_FORMATS.get(measure, "#,0")}],
        [column_transform("c", category_table, category_column, category_display, "Category"), measure_transform(measure, measure_display, "Y")],
        {"Category": [0], "Y": [1]},
        {"Category": [{"queryRef": category_ref, "suppressConcat": False}]},
    )
    return add_container(config, pos, make_query(from_items, selects, order_by), transforms)


def multi_measure_chart(visual_type: str, title: str, subtitle: str, category_table: str, category_column: str, category_display: str, measures: list[tuple[str, str]], pos: dict, order_column: str | None = None) -> dict:
    category_ref = f"{category_table}.{category_column}"
    objects = chart_objects(fill=BLUE, show_labels=False)
    from_items = [{"Name": "c", "Entity": category_table, "Type": 0}, {"Name": "m", "Entity": MEASURE_TABLE, "Type": 0}]
    selects = [column_select("c", category_table, category_column, category_display)]
    projections_y, metadata, transform_selects, roles = [], [{"Restatement": category_display, "Name": category_ref, "Type": 2048}], [column_transform("c", category_table, category_column, category_display, "Category")], [("Category", 0, True)]
    for measure, display in measures:
        idx = len(selects)
        qref = f"{MEASURE_TABLE}.{measure}"
        selects.append(measure_select("m", measure, display))
        projections_y.append({"queryRef": qref})
        metadata.append({"Restatement": display, "Name": qref, "Type": 1, "Format": MEASURE_FORMATS.get(measure, "#,0")})
        transform_selects.append(measure_transform(measure, display, "Y"))
        roles.append(("Y", idx, False))
    order_by = {"Direction": 1, "Expression": {"Column": {"Expression": source_ref("c"), "Property": order_column}}} if order_column else None
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


def table_visual(title: str, subtitle: str, fields: list[tuple[str, str, str]], measures: list[tuple[str, str]], pos: dict, order_measure: str | None = None) -> dict:
    aliases, from_items = {}, []
    for table, _, _ in fields:
        if table not in aliases:
            alias = f"f{len(aliases)}"
            aliases[table] = alias
            from_items.append({"Name": alias, "Entity": table, "Type": 0})
    if measures:
        aliases[MEASURE_TABLE] = "m"
        from_items.append({"Name": "m", "Entity": MEASURE_TABLE, "Type": 0})
    selects, projections, metadata, transform_selects = [], [], [], []
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
        metadata.append({"Restatement": display, "Name": qref, "Type": 1, "Format": MEASURE_FORMATS.get(measure, "#,0")})
        transform_selects.append(measure_transform(measure, display, "Values"))
    objects = {
        "grid": [{"properties": {"gridHorizontal": pbi_literal(False), "outlineColor": color(PANEL_BORDER)}}],
        "columnHeaders": [{"properties": {"fontFamily": text("Segoe UI Semibold"), "fontSize": pbi_literal(7.5), "fontColor": color(TEXT_DARK)}}],
        "values": [{"properties": {"fontSize": pbi_literal(7.2), "fontFamily": text("Segoe UI")}}],
    }
    order_by = {"Direction": 2, "Expression": {"Measure": {"Expression": source_ref("m"), "Property": order_measure}}} if order_measure else None
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
    transforms = data_transforms(objects, [("Values", idx, False) for idx in range(len(selects))], metadata, transform_selects, {"Values": list(range(len(selects)))})
    return add_container(config, pos, make_query(from_items, selects, order_by), transforms)


def section(name: str, display_name: str, ordinal: int, visuals: list[dict]) -> dict:
    return {
        "id": ordinal,
        "name": name,
        "displayName": display_name,
        "filters": "[]",
        "ordinal": ordinal,
        "visualContainers": visuals,
        "config": json.dumps({"objects": {"background": [{"properties": {"color": color(PAGE_BG), "transparency": pbi_literal(0.0)}}], "outspace": [{"properties": {"color": color(PAGE_BG), "transparency": pbi_literal(0.0)}}]}}, separators=(",", ":")),
        "displayOption": 1,
        "width": 1280,
        "height": 720,
    }


def page_header(title: str, subtitle: str, slicer_z: int) -> list[dict]:
    return [
        shape_box(position(0, 0, 0, 1280, 84), HEADER_BG),
        title_text(title, subtitle, position(28, 14, 1, 620, 56)),
        slicer("DimDate", "Year", "Year", position(704, 20, slicer_z, 86, 46)),
        slicer("DimClient", "ClientSegment", "Segment", position(804, 20, slicer_z + 1, 130, 46)),
        slicer("DimClient", "Region", "Region", position(948, 20, slicer_z + 2, 116, 46)),
        slicer("DimPortfolio", "ModelPortfolio", "Model", position(1078, 20, slicer_z + 3, 116, 46)),
    ]


def build_native_layout() -> dict:
    page1 = [
        *page_header("AUM & Revenue Overview", "AUM, net new money, inflow/outflow, advisory revenue, and active clients", 10),
        card_visual("Total AUM", "Total AUM", position(28, 106, 100, 184, 96), BLUE),
        card_visual("Net New Money", "Net New Money", position(224, 106, 101, 184, 96), TEAL),
        card_visual("Inflows", "Inflows", position(420, 106, 102, 184, 96), GREEN),
        card_visual("Outflows", "Outflows", position(616, 106, 103, 184, 96), RED),
        card_visual("Advisory Revenue", "Advisory Revenue", position(812, 106, 104, 184, 96), INDIGO),
        card_visual("Active Clients", "Active Clients", position(1008, 106, 105, 184, 96), AMBER),
        single_measure_chart("lineChart", "AUM Growth Trend", "Monthly ending AUM", "DimDate", "MonthLabel", "Month", "Total AUM", "AUM", position(28, 226, 200, 586, 210), BLUE, order_measure=False),
        multi_measure_chart("columnChart", "Flow Composition", "Inflows, outflows, and net new money", "DimDate", "MonthLabel", "Month", [("Inflows", "Inflows"), ("Outflows", "Outflows"), ("Net New Money", "NNM")], position(638, 226, 201, 556, 210), "MonthIndex"),
        single_measure_chart("barChart", "AUM by Client Segment", "Client mix and growth base", "DimClient", "ClientSegment", "Segment", "Total AUM", "AUM", position(28, 464, 202, 498, 190), BLUE, order_measure=True, ascending=False),
        table_visual("Top Client Detail", "Largest relationships and flow exposure", [("DimClient", "ClientName", "Client"), ("DimClient", "ClientSegment", "Segment"), ("DimClient", "RiskProfile", "Risk"), ("DimClient", "AdvisorName", "Advisor")], [("Total AUM", "AUM"), ("Net New Money", "NNM")], position(550, 464, 203, 644, 190), "Total AUM"),
    ]
    page2 = [
        *page_header("Portfolio & Client Segments", "Return vs benchmark, allocation, risk profile, client segment, and concentration", 20),
        card_visual("Portfolio Return %", "Portfolio Return", position(28, 106, 100, 220, 96), BLUE),
        card_visual("Benchmark Return %", "Benchmark Return", position(264, 106, 101, 220, 96), AMBER),
        card_visual("Alpha %", "Alpha", position(500, 106, 102, 220, 96), GREEN),
        card_visual("Top 10 Client AUM Share", "Top 10 AUM Share", position(736, 106, 103, 220, 96), INDIGO),
        card_visual("Advisory Revenue", "Revenue", position(972, 106, 104, 222, 96), TEAL),
        multi_measure_chart("lineChart", "Return vs Benchmark", "Weighted return and assigned benchmark by month", "DimDate", "MonthLabel", "Month", [("Portfolio Return %", "Portfolio"), ("Benchmark Return %", "Benchmark")], position(28, 232, 200, 526, 210), "MonthIndex"),
        single_measure_chart("donutChart", "Allocation by Asset Class", "Latest allocation amount by asset class", "FactAllocationMonthly", "AssetClass", "Asset Class", "Allocation Amount", "Allocation", position(578, 232, 201, 300, 210), BLUE, order_measure=True, ascending=False),
        single_measure_chart("barChart", "AUM by Risk Profile", "Risk profile scale and suitability footprint", "DimClient", "RiskProfile", "Risk Profile", "Total AUM", "AUM", position(902, 232, 202, 292, 210), TEAL, order_measure=True, ascending=False),
        table_visual("Portfolio Model Detail", "Model-level AUM, performance, and concentration", [("DimPortfolio", "ModelPortfolio", "Model"), ("DimPortfolio", "Benchmark", "Benchmark"), ("DimPortfolio", "RiskProfile", "Risk")], [("Total AUM", "AUM"), ("Portfolio Return %", "Return"), ("Benchmark Return %", "Benchmark"), ("Alpha %", "Alpha")], position(28, 474, 203, 1166, 180), "Total AUM"),
    ]
    page3 = [
        *page_header("Risk, Suitability & Retention", "Risk mismatch, rebalancing needs, churn, outflow risk, and retention actions", 30),
        card_visual("Risk Mismatch Clients", "Risk Mismatch", position(28, 106, 100, 184, 96), RED),
        card_visual("Rebalance Needed Clients", "Rebalance Needed", position(224, 106, 101, 184, 96), AMBER),
        card_visual("Churn Risk AUM", "Churn Risk AUM", position(420, 106, 102, 184, 96), RED),
        card_visual("High Churn Risk Clients", "High Churn Clients", position(616, 106, 103, 184, 96), RED),
        card_visual("High Outflow Risk Clients", "Outflow Risk", position(812, 106, 104, 184, 96), AMBER),
        card_visual("Retention Action AUM", "Action AUM", position(1008, 106, 105, 184, 96), GREEN),
        multi_measure_chart("lineChart", "Suitability and Rebalance Trend", "Clients requiring review by month", "DimDate", "MonthLabel", "Month", [("Risk Mismatch Clients", "Risk Mismatch"), ("Rebalance Needed Clients", "Rebalance")], position(28, 226, 200, 500, 210), "MonthIndex"),
        single_measure_chart("barChart", "Churn Risk AUM by Segment", "AUM over churn-risk threshold", "DimClient", "ClientSegment", "Segment", "Churn Risk AUM", "Churn Risk AUM", position(552, 226, 201, 326, 210), RED, order_measure=True, ascending=False),
        single_measure_chart("barChart", "Retention Actions by Type", "Recommended next-best actions", "FactRetentionActions", "ActionType", "Action", "Open Retention Actions", "Actions", position(902, 226, 202, 292, 210), GREEN, order_measure=True, ascending=False),
        table_visual("Retention Action Queue", "Advisor follow-up list with expected retained AUM", [("FactRetentionActions", "Priority", "Priority"), ("DimClient", "ClientName", "Client"), ("DimClient", "ClientSegment", "Segment"), ("FactRetentionActions", "ActionType", "Action"), ("FactRetentionActions", "RiskReason", "Reason"), ("FactRetentionActions", "Status", "Status")], [("Retention Action AUM", "Retained AUM")], position(28, 464, 203, 1166, 190), "Retention Action AUM"),
    ]
    report_config = {
        "version": "5.73",
        "themeCollection": {"baseTheme": {"name": "CY26SU05", "version": {"visual": "2.9.0", "report": "3.3.0", "page": "2.3.1"}, "type": 2}},
        "activeSectionIndex": 0,
        "defaultDrillFilterOtherVisuals": True,
        "settings": {"useNewFilterPaneExperience": True, "allowChangeFilterTypes": True, "useStylableVisualContainerHeader": True, "queryLimitOption": 6, "useEnhancedTooltips": True, "exportDataMode": 1, "useDefaultAggregateDisplayName": True},
        "objects": {"section": [{"properties": {"verticalAlignment": {"expr": {"Literal": {"Value": "'Top'"}}}}}]},
    }
    return {
        "activeSectionIndex": 0,
        "sections": [
            section("ReportSectionAUMRevenue", "AUM & Revenue Overview", 0, page1),
            section("ReportSectionSegments", "Portfolio & Client Segments", 1, page2),
            section("ReportSectionRiskRetention", "Risk, Suitability & Retention", 2, page3),
        ],
        "config": json.dumps(report_config, separators=(",", ":")),
        "layoutOptimization": 0,
    }


def write_powerbi_scripts() -> None:
    launch = r'''
$ErrorActionPreference = "Stop"
$ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$AgentDir = Join-Path $ProjectRoot "_agent"
New-Item -ItemType Directory -Force -Path $AgentDir | Out-Null
$cmd = Get-Command PBIDesktop.exe -ErrorAction SilentlyContinue
if (-not $cmd) { throw "PBIDesktop.exe not found." }
Start-Process -FilePath $cmd.Source
Start-Sleep -Seconds 15
$process = Get-Process PBIDesktop -ErrorAction SilentlyContinue | Select-Object ProcessName, Id, MainWindowTitle
$process | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $AgentDir "powerbi_windows_after_launch.json") -Encoding UTF8
$process | ConvertTo-Json -Depth 4
'''
    write_text(POWERBI_DIR / "launch_powerbi.ps1", launch)

    environment = r'''
$ErrorActionPreference = "Continue"
$ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..")
$AgentDir = Join-Path $ProjectRoot "_agent"
New-Item -ItemType Directory -Force -Path $AgentDir | Out-Null
$result = [ordered]@{
  Timestamp = (Get-Date).ToString("s")
  ProjectRoot = $ProjectRoot.Path
  PBIDesktop = (Get-Command PBIDesktop.exe -ErrorAction SilentlyContinue).Source
  PowerBIStore = (Get-AppxPackage -Name Microsoft.MicrosoftPowerBIDesktop -ErrorAction SilentlyContinue).InstallLocation
  PbiTools = (Get-Command pbi-tools.exe -ErrorAction SilentlyContinue).Source
  PbiToolsInfo = ((pbi-tools info 2>&1) -join "`n")
  Python = (Get-Command python.exe -ErrorAction SilentlyContinue).Source
  ExistingPowerBIWindows = @(Get-Process PBIDesktop -ErrorAction SilentlyContinue | Select-Object ProcessName,Id,MainWindowTitle)
}
$result | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $AgentDir "environment_check.json") -Encoding UTF8
$md = "# Environment Check`n`n- Project: $($result.ProjectRoot)`n- PBIDesktop: $($result.PBIDesktop)`n- Power BI Store: $($result.PowerBIStore)`n- pbi-tools: $($result.PbiTools)`n- Python: $($result.Python)`n`n## Existing Power BI Windows`n`n````json`n$($result.ExistingPowerBIWindows | ConvertTo-Json -Depth 6)`n````"
$md | Set-Content -LiteralPath (Join-Path $AgentDir "environment_check.md") -Encoding UTF8
$result | ConvertTo-Json -Depth 8
'''
    write_text(SCRIPT_DIR / "00_environment_check.ps1", environment)

    push = r'''
param(
  [string]$ProjectRoot = "",
  [int]$TargetProcessId = 0
)

$ErrorActionPreference = "Stop"
if ([string]::IsNullOrWhiteSpace($ProjectRoot)) {
  $ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..")
}
$PreparedRoot = Join-Path $ProjectRoot "data\prepared"
$QaRoot = Join-Path $ProjectRoot "qa"
New-Item -ItemType Directory -Force -Path $QaRoot | Out-Null

function Get-PowerBiBin {
  $cmd = Get-Command PBIDesktop.exe -ErrorAction SilentlyContinue
  if ($cmd) { return Split-Path -Parent $cmd.Source }
  throw "Power BI Desktop EXE bin folder not found."
}

function Get-PowerBiSession([int]$TargetProcessId = 0) {
  $infoText = pbi-tools info 2>&1 | Out-String
  $jsonStart = $infoText.IndexOf("{")
  if ($jsonStart -lt 0) { throw "pbi-tools info did not return a JSON payload." }
  $info = $infoText.Substring($jsonStart) | ConvertFrom-Json
  if (-not $info.pbiSessions -or $info.pbiSessions.Count -eq 0) {
    throw "No active Power BI Desktop local Analysis Services session found. Launch Power BI Desktop first."
  }
  $sessions = @($info.pbiSessions)
  if ($TargetProcessId -gt 0) {
    $target = @($sessions | Where-Object { $_.ProcessId -eq $TargetProcessId })
    if ($target.Count -eq 0) { throw "No active Power BI Desktop session found for TargetProcessId $TargetProcessId." }
    return $target[0]
  }
  $blank = @($sessions | Where-Object { -not $_.PbixPath } | Sort-Object ProcessId -Descending | Select-Object -First 1)
  if ($blank.Count -gt 0) { return $blank[0] }
  return @($sessions | Sort-Object ProcessId -Descending | Select-Object -First 1)[0]
}

function Get-ColumnType([string]$ColumnName) {
  $lower = $ColumnName.ToLowerInvariant()
  if ($lower -match "(monthstart|joinmonth|date)$") { return [Microsoft.AnalysisServices.Tabular.DataType]::DateTime }
  if ($lower -match "(monthkey|monthindex|year|flag|clients|count)$") { return [Microsoft.AnalysisServices.Tabular.DataType]::Int64 }
  if ($lower -match "(aum|inflow|outflow|money|effect|revenue|return|pct|score|bps|rate|share|amount|risk)") { return [Microsoft.AnalysisServices.Tabular.DataType]::Double }
  return [Microsoft.AnalysisServices.Tabular.DataType]::String
}

function Get-MType([string]$ColumnName) {
  $type = Get-ColumnType $ColumnName
  if ($type -eq [Microsoft.AnalysisServices.Tabular.DataType]::DateTime) { return "type date" }
  if ($type -eq [Microsoft.AnalysisServices.Tabular.DataType]::Int64) { return "Int64.Type" }
  if ($type -eq [Microsoft.AnalysisServices.Tabular.DataType]::Double) { return "type number" }
  return "type text"
}

function New-MExpression([string]$FileName, [object[]]$ColumnNames) {
  $path = Join-Path $PreparedRoot $FileName
  $escaped = $path.Replace("\", "\\")
  $typePairs = @($ColumnNames | ForEach-Object {
    $name = [string]$_
    $escapedName = $name -replace '"', '""'
    "{`"$escapedName`", $(Get-MType $name)}"
  }) -join ",`n        "
  return @"
let
    Source = Csv.Document(File.Contents("$escaped"), [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]),
    PromotedHeaders = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    TypedColumns = Table.TransformColumnTypes(PromotedHeaders, {
        $typePairs
    }, "en-US")
in
    TypedColumns
"@
}

function Get-SummarizeBy([string]$TableName, [string]$ColumnName) {
  $type = Get-ColumnType $ColumnName
  if ($type -in @([Microsoft.AnalysisServices.Tabular.DataType]::Double, [Microsoft.AnalysisServices.Tabular.DataType]::Int64) -and $TableName.StartsWith("Fact")) {
    if ($ColumnName.ToLowerInvariant() -notmatch "(id|key|flag|pct|score|bps|rate)$") {
      return [Microsoft.AnalysisServices.Tabular.AggregateFunction]::Sum
    }
  }
  return [Microsoft.AnalysisServices.Tabular.AggregateFunction]::None
}

function Add-ImportTable([Microsoft.AnalysisServices.Tabular.Model]$Model, [string]$Name, [string]$FileName) {
  $path = Join-Path $PreparedRoot $FileName
  if (!(Test-Path -LiteralPath $path)) { throw "Prepared CSV missing: $path" }
  $first = Import-Csv -LiteralPath $path | Select-Object -First 1
  if (-not $first) { throw "Prepared CSV has no rows: $path" }
  $table = New-Object Microsoft.AnalysisServices.Tabular.Table
  $table.Name = $Name
  $Model.Tables.Add($table)
  foreach ($columnName in $first.PSObject.Properties.Name) {
    $column = New-Object Microsoft.AnalysisServices.Tabular.DataColumn
    $column.Name = $columnName
    $column.SourceColumn = $columnName
    $column.DataType = Get-ColumnType $columnName
    $column.SummarizeBy = Get-SummarizeBy $Name $columnName
    if ($columnName.ToLowerInvariant() -match "(clientid|actionid)$") { $column.SummarizeBy = [Microsoft.AnalysisServices.Tabular.AggregateFunction]::None }
    $table.Columns.Add($column)
  }
  $partition = New-Object Microsoft.AnalysisServices.Tabular.Partition
  $partition.Name = "${Name}-Import"
  $partition.Mode = [Microsoft.AnalysisServices.Tabular.ModeType]::Import
  $source = New-Object Microsoft.AnalysisServices.Tabular.MPartitionSource
  $source.Expression = New-MExpression $FileName $first.PSObject.Properties.Name
  $partition.Source = $source
  $table.Partitions.Add($partition)
}

function Add-Relationship($Model, $Name, $FactTable, $FactColumn, $DimTable, $DimColumn) {
  if (-not $Model.Tables.Contains($FactTable) -or -not $Model.Tables.Contains($DimTable)) { return }
  $rel = New-Object Microsoft.AnalysisServices.Tabular.SingleColumnRelationship
  $rel.Name = $Name
  $rel.FromColumn = $Model.Tables[$FactTable].Columns[$FactColumn]
  $rel.ToColumn = $Model.Tables[$DimTable].Columns[$DimColumn]
  $rel.FromCardinality = [Microsoft.AnalysisServices.Tabular.RelationshipEndCardinality]::Many
  $rel.ToCardinality = [Microsoft.AnalysisServices.Tabular.RelationshipEndCardinality]::One
  $rel.CrossFilteringBehavior = [Microsoft.AnalysisServices.Tabular.CrossFilteringBehavior]::OneDirection
  $rel.IsActive = $true
  $Model.Relationships.Add($rel)
}

function Add-Measure($Table, $Name, $Expression, $FormatString = $null) {
  $measure = New-Object Microsoft.AnalysisServices.Tabular.Measure
  $measure.Name = $Name
  $measure.Expression = $Expression
  if ($FormatString) { $measure.FormatString = $FormatString }
  $Table.Measures.Add($measure)
}

$powerBiBin = Get-PowerBiBin
Add-Type -Path (Join-Path $powerBiBin "Microsoft.PowerBI.Amo.dll")
$session = Get-PowerBiSession -TargetProcessId $TargetProcessId
$server = New-Object Microsoft.AnalysisServices.Tabular.Server
$server.Connect("localhost:$($session.Port)")
$database = $server.Databases[0]
$model = $database.Model
$model.Relationships.Clear()
$model.Tables.Clear()

$tableSpecs = @(
  @{Name="DimDate"; File="dim_date.csv"},
  @{Name="DimClient"; File="dim_client.csv"},
  @{Name="DimPortfolio"; File="dim_portfolio.csv"},
  @{Name="FactAUMMonthly"; File="fact_aum_monthly.csv"},
  @{Name="FactAllocationMonthly"; File="fact_allocation_monthly.csv"},
  @{Name="FactRetentionActions"; File="fact_retention_actions.csv"}
)
foreach ($spec in $tableSpecs) { Add-ImportTable $model $spec.Name $spec.File }

Add-Relationship $model "AUM_Date" "FactAUMMonthly" "MonthStart" "DimDate" "MonthStart"
Add-Relationship $model "Allocation_Date" "FactAllocationMonthly" "MonthStart" "DimDate" "MonthStart"
Add-Relationship $model "Actions_Date" "FactRetentionActions" "MonthStart" "DimDate" "MonthStart"
Add-Relationship $model "AUM_Client" "FactAUMMonthly" "ClientID" "DimClient" "ClientID"
Add-Relationship $model "Allocation_Client" "FactAllocationMonthly" "ClientID" "DimClient" "ClientID"
Add-Relationship $model "Actions_Client" "FactRetentionActions" "ClientID" "DimClient" "ClientID"
Add-Relationship $model "AUM_Portfolio" "FactAUMMonthly" "ModelPortfolio" "DimPortfolio" "ModelPortfolio"
Add-Relationship $model "Allocation_Portfolio" "FactAllocationMonthly" "ModelPortfolio" "DimPortfolio" "ModelPortfolio"

$kpi = New-Object Microsoft.AnalysisServices.Tabular.Table
$kpi.Name = "KPI Measures"
$model.Tables.Add($kpi)
$kpiCol = New-Object Microsoft.AnalysisServices.Tabular.DataColumn
$kpiCol.Name = "MeasureKey"
$kpiCol.SourceColumn = "MeasureKey"
$kpiCol.DataType = [Microsoft.AnalysisServices.Tabular.DataType]::String
$kpiCol.IsHidden = $true
$kpi.Columns.Add($kpiCol)
$kpiPartition = New-Object Microsoft.AnalysisServices.Tabular.Partition
$kpiPartition.Name = "KPI Measures-Import"
$kpiPartition.Mode = [Microsoft.AnalysisServices.Tabular.ModeType]::Import
$kpiSource = New-Object Microsoft.AnalysisServices.Tabular.MPartitionSource
$kpiSource.Expression = "let Source = #table(type table [MeasureKey = text], {{""KPI""}}) in Source"
$kpiPartition.Source = $kpiSource
$kpi.Partitions.Add($kpiPartition)
'''
    for name, dax, fmt in MEASURES:
        escaped_name = name.replace('"', '""')
        escaped_dax = dax.replace('"', '""')
        escaped_fmt = fmt.replace("'", "''")
        push += f'\nAdd-Measure $kpi "{escaped_name}" "{escaped_dax}" \'{escaped_fmt}\''
    push += r'''

$model.SaveChanges()
$model.RequestRefresh([Microsoft.AnalysisServices.Tabular.RefreshType]::Full)
$model.SaveChanges()

$result = [ordered]@{
  timestamp = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss zzz")
  status = "model_pushed_to_powerbi_desktop_local_session"
  power_bi_port = $session.Port
  process_id = $session.ProcessId
  tables = $model.Tables.Count
  relationships = $model.Relationships.Count
  measures = $kpi.Measures.Count
  output_model_pbix = "not_created_requires_desktop_save"
  expected_save_path = (Join-Path $ProjectRoot "output\dashboard_model.pbix")
}
$result | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $QaRoot "scripted_model_push.json") -Encoding UTF8
$server.Disconnect()
$result | ConvertTo-Json -Depth 8
'''
    write_text(SCRIPT_DIR / "07_push_model_to_powerbi_desktop.ps1", push)

    patch = r'''
param(
  [string]$ModelPbix = "",
  [string]$LayoutJson = "",
  [string]$OutputPbix = "",
  [string]$FinalPbix = ""
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..")
$OutputRoot = Join-Path $ProjectRoot "output"
$QaRoot = Join-Path $ProjectRoot "qa"
New-Item -ItemType Directory -Force -Path $OutputRoot, $QaRoot | Out-Null

function Resolve-ProjectPath([string]$PathValue, [string]$DefaultRelative) {
  if ([string]::IsNullOrWhiteSpace($PathValue)) { return Join-Path $ProjectRoot $DefaultRelative }
  if ([IO.Path]::IsPathRooted($PathValue)) { return $PathValue }
  return Join-Path $ProjectRoot $PathValue
}
function Get-PowerBiBin {
  $cmd = Get-Command PBIDesktop.exe -ErrorAction SilentlyContinue
  if ($cmd) { return Split-Path -Parent $cmd.Source }
  throw "Power BI Desktop bin folder not found."
}
function Write-Validation([hashtable]$Payload, [int]$ExitCode = 0) {
  $Payload.timestamp = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss zzz")
  $Payload | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath (Join-Path $QaRoot "pbix_native_report_validation.json") -Encoding UTF8
  Write-Output ($Payload | ConvertTo-Json -Depth 10)
  if ($ExitCode -ne 0) { exit $ExitCode }
}

$ModelPbix = Resolve-ProjectPath $ModelPbix "output\dashboard_model.pbix"
$LayoutJson = Resolve-ProjectPath $LayoutJson "build\native_report_layout_wealthtech.json"
$OutputPbix = Resolve-ProjectPath $OutputPbix "output\dashboard_v01.pbix"
$FinalPbix = Resolve-ProjectPath $FinalPbix "output\dashboard_final.pbix"
if (!(Test-Path -LiteralPath $ModelPbix)) {
  Write-Validation @{ status="failed_precondition_missing_model_pbix"; source_model_pbix=$ModelPbix; layout_json=$LayoutJson; final_pbix_created=$false; reason="No output/dashboard_model.pbix exists. Push the model into Power BI Desktop and save that session first." } 2
}
if (!(Test-Path -LiteralPath $LayoutJson)) {
  Write-Validation @{ status="failed_precondition_missing_layout_json"; source_model_pbix=$ModelPbix; layout_json=$LayoutJson; final_pbix_created=$false; reason="Native report layout JSON is missing. Run build/scripts/01_build_project.py first." } 2
}
try {
  $PowerBiBin = Get-PowerBiBin
  $PackagingDll = Join-Path $PowerBiBin "Microsoft.PowerBI.Packaging.dll"
  [Reflection.Assembly]::LoadFrom($PackagingDll) | Out-Null
  Add-Type -AssemblyName WindowsBase
  function Validate-Pbix([string]$Path) {
    $stream = [IO.File]::OpenRead($Path)
    try { [Microsoft.PowerBI.Packaging.PowerBIPackager]::Validate($stream) }
    finally { $stream.Dispose() }
  }
  Validate-Pbix $ModelPbix
  Copy-Item -LiteralPath $ModelPbix -Destination $OutputPbix -Force
  $layout = Get-Content -LiteralPath $LayoutJson -Raw | ConvertFrom-Json
  $layoutText = $layout | ConvertTo-Json -Depth 100 -Compress
  $layoutBytes = [Text.Encoding]::Unicode.GetBytes($layoutText)
  $package = [System.IO.Packaging.Package]::Open($OutputPbix, [IO.FileMode]::Open, [IO.FileAccess]::ReadWrite)
  try {
    $layoutUri = New-Object System.Uri("/Report/Layout", [System.UriKind]::Relative)
    if (-not $package.PartExists($layoutUri)) { throw "The source model PBIX does not contain /Report/Layout." }
    $layoutPart = $package.GetPart($layoutUri)
    $stream = $layoutPart.GetStream([IO.FileMode]::Open, [IO.FileAccess]::ReadWrite)
    try {
      $stream.SetLength(0)
      $stream.Position = 0
      $stream.Write($layoutBytes, 0, $layoutBytes.Length)
    }
    finally { $stream.Dispose() }
    $securityUri = New-Object System.Uri("/SecurityBindings", [System.UriKind]::Relative)
    if ($package.PartExists($securityUri)) { $package.DeletePart($securityUri) }
  }
  finally { $package.Close() }
  Validate-Pbix $OutputPbix
  Copy-Item -LiteralPath $OutputPbix -Destination $FinalPbix -Force
  Validate-Pbix $FinalPbix
  Write-Validation @{ status="passed"; source_model_pbix=$ModelPbix; layout_json=$LayoutJson; output_pbix=$OutputPbix; final_pbix=$FinalPbix; final_pbix_created=$true; final_pbix_size=(Get-Item -LiteralPath $FinalPbix).Length; pages=@($layout.sections | ForEach-Object { $_.displayName }); visual_containers=($layout.sections | ForEach-Object { $_.visualContainers.Count } | Measure-Object -Sum).Sum; validation="PowerBIPackager.Validate passed for output and final PBIX after native report layout patch." }
}
catch {
  Write-Validation @{ status="failed_exception"; source_model_pbix=$ModelPbix; layout_json=$LayoutJson; final_pbix=$FinalPbix; final_pbix_created=(Test-Path -LiteralPath $FinalPbix); reason=$_.Exception.Message } 1
}
'''
    write_text(SCRIPT_DIR / "10_apply_native_pbix_report.ps1", patch)


def write_docs(tables: dict[str, pd.DataFrame], aggregates: dict[str, pd.DataFrame], dq: dict) -> None:
    latest = aggregates["MonthlyKPIs"].iloc[-1]
    write_text(
        AGENT_DIR / "intake_brief.md",
        f"""
# Intake Brief

- Topic: WealthTech / Robo-Advisor AUM Dashboard.
- Project path: `{PROJECT_ROOT}`.
- Audience: wealth management executives, robo-advisor product leaders, advisor operations, and risk/compliance partners.
- Business goal: monitor AUM growth, revenue quality, portfolio/client mix, suitability risk, and retention actions.
- Data source: synthetic deterministic demo data, seed `{SEED}`, latest complete month `{LATEST_MONTH.date().isoformat()}`.
- Requested tabs: AUM & Revenue Overview; Portfolio & Client Segments; Risk, Suitability & Retention.
- Assumption: portfolio/demo build, so synthetic data is acceptable and clearly marked in all docs.
""",
    )
    write_text(
        AGENT_DIR / "run_log.md",
        f"""
# Run Log

- {REPORT_DATE.isoformat()}: Initialized Project 12 - WealthTech AUM Client Retention scaffold.
- Generated deterministic WealthTech synthetic data with seed `{SEED}`.
- Prepared star-schema CSVs, aggregate extracts, semantic model docs, DAX catalog, HTML preview, native Power BI layout JSON, and QA reports.
- Native PBIX route: push model into Power BI Desktop via XMLA/TOM, save `output/dashboard_model.pbix`, then patch `/Report/Layout` and validate final package.
""",
    )
    write_text(
        AGENT_DIR / "session_guard.md",
        f"""
# Session Guard

- Current project path: `{PROJECT_ROOT}`.
- Expected final PBIX path: `{OUTPUT_DIR / "dashboard_final.pbix"}`.
- Expected model-save path: `{OUTPUT_DIR / "dashboard_model.pbix"}`.
- Power BI windows detected before automation: recorded by `build/scripts/00_environment_check.ps1`.
- Selected session rule: use latest Power BI Desktop session only after `pbi-tools info` confirms a local Analysis Services port, then record process id and port in `qa/scripted_model_push.json`.
- Ignored sessions: any window/session whose saved path or process evidence does not match this project.
""",
    )
    write_text(
        DOCS_DIR / "design_research_notes.md",
        """
# Design Research Notes

Public references used for layout and KPI framing:

- Tableau Exchange Assets under Management accelerators: AUM, net new money, revenue, flows, business lines, client type, top clients, and client-level drilldown.
- Tableau wealth-management analytics: advisor-facing dashboards should protect and grow investments, personalize client experiences, and manage risk/compliance.
- Tableau financial services churn/AUM demo: combine client KPIs, churn predictions, and recommended engagement actions in one view.
- Qlik financial dashboard guide: lead with finance KPIs, then trends, variance drivers, and exploratory breakdowns.
- ZoomCharts Power BI financial template gallery: overview-first navigation with deeper pages, KPI cards, combo charts, waterfall/donut/table patterns.
- Masttro family-office dashboard article: wealth dashboards should cover allocation, performance reporting, rebalancing, cash/liquidity, compliance, and decision actions.
- Sub-agent research also suggested BlackRock Advisor Center 360, Morningstar Portfolio Snapshot, Betterment Advisor Dashboard, and J.P. Morgan Guide to the Markets for sober institutional visual language.

Applied decisions:

- Light institutional base with navy navigation, white panels, thin borders, blue/teal growth accents, green only for positive performance, red only for risk/outflow.
- Three requested tabs, each with KPI ribbon, trend view, diagnostic visual, and action/detail table.
- Robo-advisor-specific action layer: suitability mismatch, rebalance needs, churn/outflow risk, and expected retained AUM.
""",
    )
    write_text(
        DOCS_DIR / "dashboard_spec.md",
        f"""
# Dashboard Specification

## Pages

1. AUM & Revenue Overview
   - Purpose: monitor growth, net new money, flows, advisory revenue, and active clients.
   - Visuals: KPI ribbon, AUM/revenue trend, flow composition, segment AUM, top-client concentration table.
2. Portfolio & Client Segments
   - Purpose: compare return versus benchmark and diagnose allocation, risk profile, segment mix, and concentration.
   - Visuals: return/benchmark trend, allocation donut, AUM by risk profile, portfolio model detail.
3. Risk, Suitability & Retention
   - Purpose: surface mismatch, rebalancing, churn/outflow risk, and advisor follow-up actions.
   - Visuals: KPI ribbon, mismatch/rebalance trend, churn-risk AUM by segment, action mix, retention action queue.

## Latest KPI Snapshot

- Total AUM: {money_short(latest["TotalAUM"])}
- Net New Money: {money_short(latest["NetNewMoney"])}
- Advisory Revenue: {money_short(latest["AdvisoryRevenue"])}
- Active Clients: {int(latest["ActiveClients"]):,}
- Portfolio Return: {pct(latest["PortfolioReturnPct"])}
- Benchmark Return: {pct(latest["BenchmarkReturnPct"])}
- Risk Mismatch Clients: {int(latest["RiskMismatchClients"]):,}
- Rebalance Needed Clients: {int(latest["RebalanceNeededClients"]):,}
- Churn Risk AUM: {money_short(latest["ChurnRiskAUM"])}
""",
    )
    write_text(
        DOCS_DIR / "rebuild_guide.md",
        f"""
# Rebuild Guide

```powershell
$py = 'C:\\Users\\Win\\.cache\\codex-runtimes\\codex-primary-runtime\\dependencies\\python\\python.exe'
& $py 'build\\scripts\\01_build_project.py'
.\\build\\scripts\\00_environment_check.ps1
.\\powerbi\\launch_powerbi.ps1
.\\build\\scripts\\07_push_model_to_powerbi_desktop.ps1
```

After the model push, save the active Power BI Desktop report as:

```text
{OUTPUT_DIR / "dashboard_model.pbix"}
```

Then patch the native report layout and validate the final package:

```powershell
.\\build\\scripts\\10_apply_native_pbix_report.ps1
```

The portable HTML preview is:

```text
{OUTPUT_DIR / "dashboard_preview.html"}
```
""",
    )
    write_text(
        DOCS_DIR / "qa_summary.md",
        f"""
# QA Summary

- Data quality status: `{dq["status"]}`.
- Synthetic data seed: `{SEED}`.
- Latest complete month: `{LATEST_MONTH.date().isoformat()}`.
- Row counts:
  - DimDate: {len(tables["DimDate"]):,}
  - DimClient: {len(tables["DimClient"]):,}
  - DimPortfolio: {len(tables["DimPortfolio"]):,}
  - FactAUMMonthly: {len(tables["FactAUMMonthly"]):,}
  - FactAllocationMonthly: {len(tables["FactAllocationMonthly"]):,}
  - FactRetentionActions: {len(tables["FactRetentionActions"]):,}
- Reconciliation:
  - Latest fact AUM equals monthly KPI AUM: `{dq["reconciliation"]["aum_reconciles"]}`.
  - Net new money formula passes: `{dq["reconciliation"]["nnm_formula_pass"]}`.
  - Ending AUM nonnegative: `{dq["reconciliation"]["ending_aum_nonnegative"]}`.

PBIX QA is written to `qa/pbix_native_report_validation.json` after `10_apply_native_pbix_report.ps1` runs.
""",
    )
    write_text(
        POWERBI_DIR / "notes" / "desktop_ui_runbook.md",
        f"""
# Desktop UI Runbook

1. Run `powerbi/launch_powerbi.ps1` and wait for a blank Power BI Desktop window.
2. Run `build/scripts/07_push_model_to_powerbi_desktop.ps1`.
3. Verify `qa/scripted_model_push.json` records the selected process id and local port.
4. Save the active Desktop file as `{OUTPUT_DIR / "dashboard_model.pbix"}`.
5. Run `build/scripts/10_apply_native_pbix_report.ps1` to create `{OUTPUT_DIR / "dashboard_final.pbix"}`.
6. Reopen the final PBIX and confirm pages render without visual errors.
""",
    )


def main() -> None:
    ensure_dirs()
    tables = build_synthetic_data()

    raw_names = {
        "DimClient": "clients_raw.csv",
        "DimPortfolio": "portfolios_raw.csv",
        "FactAUMMonthly": "aum_monthly_raw.csv",
        "FactAllocationMonthly": "allocation_monthly_raw.csv",
        "FactRetentionActions": "retention_actions_raw.csv",
    }
    for name, file_name in raw_names.items():
        write_csv(RAW_DIR / file_name, tables[name])

    prepared_names = {
        "DimDate": "dim_date.csv",
        "DimClient": "dim_client.csv",
        "DimPortfolio": "dim_portfolio.csv",
        "FactAUMMonthly": "fact_aum_monthly.csv",
        "FactAllocationMonthly": "fact_allocation_monthly.csv",
        "FactRetentionActions": "fact_retention_actions.csv",
    }
    for name, file_name in prepared_names.items():
        write_csv(PREPARED_DIR / file_name, tables[name])

    aggregates = prepare_aggregates(tables)
    aggregate_names = {
        "MonthlyKPIs": "monthly_kpis.csv",
        "SegmentSummaryLatest": "segment_summary_latest.csv",
        "RiskProfileSummaryLatest": "risk_profile_summary_latest.csv",
        "PortfolioSummaryLatest": "portfolio_summary_latest.csv",
        "AllocationLatest": "allocation_latest.csv",
        "TopClientsLatest": "top_clients_latest.csv",
        "RetentionActionsLatest": "retention_actions_latest.csv",
    }
    for name, file_name in aggregate_names.items():
        write_csv(VALIDATED_DIR / file_name, aggregates[name])
        write_csv(PREPARED_DIR / file_name, aggregates[name])

    dq = data_quality_report(tables, aggregates)
    write_json(VALIDATED_DIR / "data_quality_report.json", dq)
    write_json(QA_DIR / "prepared_data_validation.json", dq)
    write_json(PROJECT_ROOT / "data" / "source_summary.json", {"synthetic": True, "seed": SEED, "latest_complete_month": LATEST_MONTH.date().isoformat(), "raw_tables": raw_names, "prepared_tables": prepared_names})
    write_model_docs(tables)
    write_json(CONFIG_DIR / "theme.json", {"name": "WealthTech Institutional Light", "colors": {"page": PAGE_BG, "header": HEADER_BG, "panel": PANEL_BG, "blue": BLUE, "teal": TEAL, "green": GREEN, "amber": AMBER, "red": RED, "indigo": INDIGO}})
    write_json(CONFIG_DIR / "page_map.json", {"pages": ["AUM & Revenue Overview", "Portfolio & Client Segments", "Risk, Suitability & Retention"]})
    write_json(CONFIG_DIR / "visual_map.json", {"kpi_cards": 17, "charts": ["lineChart", "columnChart", "barChart", "donutChart", "tableEx"], "slicers": ["Year", "Client Segment", "Region", "Model Portfolio"]})

    html = build_html_dashboard(aggregates)
    write_text(OUTPUT_DIR / "dashboard_preview.html", html)
    write_text(OUTPUT_DIR / "exports" / "wealthtech_aum_dashboard.html", html)

    layout = build_native_layout()
    write_json(BUILD_DIR / "native_report_layout_wealthtech.json", layout)
    write_json(
        QA_DIR / "native_report_layout_summary.json",
        {
            "generated_at": REPORT_DATE.isoformat(),
            "status": "layout_json_generated",
            "layout_json": str(BUILD_DIR / "native_report_layout_wealthtech.json"),
            "pages": [section["displayName"] for section in layout["sections"]],
            "visual_containers": sum(len(section["visualContainers"]) for section in layout["sections"]),
            "target_model_pbix": str(OUTPUT_DIR / "dashboard_model.pbix"),
            "target_final_pbix": str(OUTPUT_DIR / "dashboard_final.pbix"),
        },
    )
    write_powerbi_scripts()
    write_docs(tables, aggregates, dq)
    write_json(QA_DIR / "build_summary.json", {"status": "built", "project_root": str(PROJECT_ROOT), "html_preview": str(OUTPUT_DIR / "dashboard_preview.html"), "layout_json": str(BUILD_DIR / "native_report_layout_wealthtech.json"), "data_quality": dq["status"]})
    print(json.dumps({"status": "built", "project_root": str(PROJECT_ROOT), "data_quality": dq["status"], "html_preview": str(OUTPUT_DIR / "dashboard_preview.html")}, indent=2))


if __name__ == "__main__":
    main()
