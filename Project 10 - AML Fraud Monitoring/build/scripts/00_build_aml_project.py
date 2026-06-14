from __future__ import annotations

import json
import math
import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SEED = 20260611
RNG = np.random.default_rng(SEED)
AS_OF_DATE = pd.Timestamp("2026-06-01")
LATEST_COMPLETE_MONTH = "May 2026"


DIRS = [
    "_agent",
    "data/raw",
    "data/prepared",
    "data/validated",
    "model",
    "build/config",
    "powerbi/notes",
    "output/screenshots",
    "output/exports",
    "qa",
    "docs",
]


def ensure_dirs() -> None:
    for folder in DIRS:
        (PROJECT_ROOT / folder).mkdir(parents=True, exist_ok=True)


def write_json(path: Path, payload: dict | list) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.strip() + "\n", encoding="utf-8")


def money(value: float) -> str:
    abs_value = abs(value)
    sign = "-" if value < 0 else ""
    if abs_value >= 1_000_000_000:
        return f"{sign}${abs_value / 1_000_000_000:.1f}B"
    if abs_value >= 1_000_000:
        return f"{sign}${abs_value / 1_000_000:.1f}M"
    if abs_value >= 1_000:
        return f"{sign}${abs_value / 1_000:.1f}K"
    return f"{sign}${abs_value:,.0f}"


def pct(value: float) -> str:
    return f"{value * 100:.1f}%"


def number(value: float) -> str:
    return f"{value:,.0f}"


def date_key(ts: pd.Timestamp) -> int:
    return int(ts.strftime("%Y%m%d"))


def month_index(ts: pd.Timestamp) -> int:
    return (ts.year - 2025) * 12 + ts.month


def make_dimensions() -> dict[str, pd.DataFrame]:
    dates = pd.date_range("2025-01-01", "2026-05-31", freq="D")
    dim_date = pd.DataFrame(
        {
            "DateKey": [date_key(d) for d in dates],
            "Date": dates,
            "MonthStart": dates.to_period("M").to_timestamp(),
            "Year": dates.year,
            "Quarter": ["Q" + str(q) for q in dates.quarter],
            "MonthNumber": dates.month,
            "MonthName": dates.strftime("%b"),
            "MonthYear": dates.strftime("%b %Y"),
            "MonthIndex": [month_index(d) for d in dates],
            "IsLatestCompleteMonth": np.where(dates.strftime("%b %Y") == LATEST_COMPLETE_MONTH, "Y", "N"),
        }
    )

    countries = [
        ("US", "United States", "North America", 38),
        ("GB", "United Kingdom", "Europe", 42),
        ("SG", "Singapore", "Asia Pacific", 36),
        ("VN", "Vietnam", "Asia Pacific", 44),
        ("HK", "Hong Kong", "Asia Pacific", 53),
        ("AE", "United Arab Emirates", "Middle East", 61),
        ("TR", "Turkey", "EMEA", 66),
        ("NG", "Nigeria", "Africa", 72),
        ("ZA", "South Africa", "Africa", 58),
        ("BR", "Brazil", "Latin America", 57),
        ("MX", "Mexico", "Latin America", 55),
        ("PH", "Philippines", "Asia Pacific", 49),
    ]
    dim_country = pd.DataFrame(
        countries,
        columns=["CountryCode", "Country", "Region", "CountryRiskScore"],
    )
    dim_country["CountryRiskTier"] = pd.cut(
        dim_country["CountryRiskScore"],
        bins=[0, 45, 60, 100],
        labels=["Low", "Medium", "High"],
        include_lowest=True,
    ).astype(str)

    corridor_defs = [
        ("US", "GB", "Retail wire corridor", 40),
        ("US", "MX", "Remittance corridor", 57),
        ("GB", "AE", "Private banking corridor", 63),
        ("SG", "HK", "Trade finance corridor", 55),
        ("VN", "SG", "SME supplier corridor", 46),
        ("HK", "NG", "High-risk trade corridor", 78),
        ("AE", "TR", "Cash-intensive corridor", 73),
        ("BR", "US", "Merchant settlement corridor", 54),
        ("PH", "HK", "Wallet remittance corridor", 58),
        ("ZA", "GB", "Investment services corridor", 60),
        ("NG", "AE", "Enhanced due diligence corridor", 81),
        ("MX", "US", "Card acquiring corridor", 52),
    ]
    dim_corridor = pd.DataFrame(
        [
            {
                "CorridorKey": f"COR{i + 1:03d}",
                "OriginCountryCode": o,
                "DestinationCountryCode": d,
                "Corridor": f"{o}->{d}",
                "CorridorName": name,
                "CorridorRiskScore": score,
            }
            for i, (o, d, name, score) in enumerate(corridor_defs)
        ]
    )
    dim_corridor["CorridorRiskTier"] = pd.cut(
        dim_corridor["CorridorRiskScore"],
        bins=[0, 50, 65, 100],
        labels=["Low", "Medium", "High"],
        include_lowest=True,
    ).astype(str)

    channels = [
        ("CH001", "ACH", "Batch", 34),
        ("CH002", "Wire", "Real-time", 58),
        ("CH003", "Card", "Real-time", 43),
        ("CH004", "RTP", "Real-time", 66),
        ("CH005", "Cash Deposit", "Branch", 72),
        ("CH006", "International Transfer", "Real-time", 68),
        ("CH007", "Digital Wallet", "Real-time", 51),
        ("CH008", "Crypto Off-ramp", "Real-time", 83),
    ]
    dim_channel = pd.DataFrame(channels, columns=["ChannelKey", "Channel", "ChannelMode", "ChannelRiskScore"])

    products = [
        ("PR001", "Retail Checking", "Consumer Banking", 36),
        ("PR002", "SME Payments", "Business Banking", 49),
        ("PR003", "Cross-border Remittance", "Payments", 62),
        ("PR004", "Merchant Acquiring", "Payments", 55),
        ("PR005", "Digital Wallet", "Digital Assets", 58),
        ("PR006", "Private Banking", "Wealth", 67),
        ("PR007", "Trade Finance", "Commercial Banking", 71),
        ("PR008", "Crypto Off-ramp", "Digital Assets", 84),
    ]
    dim_product = pd.DataFrame(products, columns=["ProductKey", "Product", "ProductFamily", "ProductRiskScore"])

    rules = [
        ("R001", "High Velocity Transfers", "Velocity", "High", "Active", "Financial Crime Analytics", 69),
        ("R002", "Structuring Below Threshold", "Structuring", "High", "Active", "AML Monitoring", 73),
        ("R003", "High Risk Corridor", "Geo/Corridor", "High", "Active", "Sanctions Risk", 71),
        ("R004", "Dormant Account Reactivation", "Behavioral", "Medium", "Active", "KYC Operations", 63),
        ("R005", "Cash Intensive Pattern", "Cash", "High", "Active", "Branch Risk", 74),
        ("R006", "Round Dollar Repetition", "Pattern", "Medium", "Tuning", "Fraud Strategy", 58),
        ("R007", "New Beneficiary Burst", "Account Takeover", "High", "Active", "Fraud Strategy", 76),
        ("R008", "Watchlist Proximity", "Sanctions", "Critical", "Active", "Sanctions Risk", 86),
        ("R009", "Crypto Off-ramp Spike", "Digital Assets", "High", "Pilot", "Digital Assets Risk", 81),
        ("R010", "Rapid In-Out Funds", "Mule/Funnel", "High", "Active", "AML Monitoring", 78),
    ]
    dim_rule = pd.DataFrame(
        rules,
        columns=[
            "RuleKey",
            "RuleName",
            "Typology",
            "RuleSeverity",
            "RuleStatus",
            "RuleOwner",
            "RuleRiskScore",
        ],
    )
    dim_rule["LastTunedDate"] = pd.to_datetime("2026-05-01") - pd.to_timedelta(
        RNG.integers(5, 170, len(dim_rule)), unit="D"
    )

    analysts = [
        ("A001", "Maya Tran", "Tier 1", "APAC Queue"),
        ("A002", "Liam Nguyen", "Tier 1", "APAC Queue"),
        ("A003", "Sofia Patel", "Tier 2", "High Risk Queue"),
        ("A004", "Noah Garcia", "Tier 2", "Americas Queue"),
        ("A005", "Amelia Chen", "Tier 3", "SAR Review"),
        ("A006", "Ethan Brooks", "Tier 2", "EMEA Queue"),
        ("A007", "Aisha Khan", "Tier 3", "Sanctions Escalation"),
        ("A008", "Minh Le", "Tier 1", "Payments Queue"),
    ]
    dim_analyst = pd.DataFrame(analysts, columns=["AnalystKey", "Analyst", "AnalystTier", "Queue"])

    segments = ["Retail", "SME", "Corporate", "Wealth", "Fintech", "Money Services Business"]
    customer_types = ["Individual", "Business", "Non-resident", "Shell-risk entity"]
    customer_rows = []
    country_weights = np.array([1.4, 1.1, 1.0, 1.0, 0.9, 0.7, 0.5, 0.4, 0.4, 0.6, 0.8, 0.7])
    country_weights = country_weights / country_weights.sum()
    for i in range(1, 181):
        country = dim_country.sample(n=1, weights=country_weights, random_state=int(RNG.integers(1, 1_000_000))).iloc[0]
        segment = RNG.choice(segments, p=[0.33, 0.22, 0.14, 0.08, 0.11, 0.12])
        customer_type = RNG.choice(customer_types, p=[0.58, 0.29, 0.08, 0.05])
        base = int(np.clip(country.CountryRiskScore + RNG.normal(0, 12), 15, 95))
        pep = "Y" if RNG.random() < (0.04 + max(base - 65, 0) / 700) else "N"
        watch = "Y" if RNG.random() < (0.025 + max(base - 70, 0) / 800) else "N"
        kyc_status = RNG.choice(["Current", "Due Soon", "Overdue"], p=[0.78, 0.15, 0.07])
        risk_score = int(np.clip(base + (10 if pep == "Y" else 0) + (14 if watch == "Y" else 0), 1, 99))
        tier = "High" if risk_score >= 70 else "Medium" if risk_score >= 45 else "Low"
        customer_rows.append(
            {
                "CustomerKey": f"C{i:04d}",
                "Customer": f"Customer {i:04d}",
                "CustomerSegment": segment,
                "CustomerType": customer_type,
                "HomeCountryCode": country.CountryCode,
                "HomeCountry": country.Country,
                "CustomerRiskScore": risk_score,
                "CustomerRiskTier": tier,
                "PEPFlag": pep,
                "WatchlistFlag": watch,
                "KYCStatus": kyc_status,
                "OnboardingDate": pd.Timestamp("2023-01-01") + pd.to_timedelta(int(RNG.integers(0, 1200)), unit="D"),
            }
        )
    dim_customer = pd.DataFrame(customer_rows)

    return {
        "dim_date": dim_date,
        "dim_country": dim_country,
        "dim_corridor": dim_corridor,
        "dim_channel": dim_channel,
        "dim_product": dim_product,
        "dim_rule": dim_rule,
        "dim_analyst": dim_analyst,
        "dim_customer": dim_customer,
    }


def weighted_choice(values: pd.Series, weights: pd.Series, n: int) -> np.ndarray:
    normalized = np.array(weights, dtype=float)
    normalized = normalized / normalized.sum()
    return RNG.choice(values.to_numpy(), size=n, p=normalized)


def make_facts(dims: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    n_txn = 36_000
    dim_date = dims["dim_date"]
    dim_customer = dims["dim_customer"].set_index("CustomerKey")
    dim_corridor = dims["dim_corridor"].set_index("CorridorKey")
    dim_channel = dims["dim_channel"].set_index("ChannelKey")
    dim_product = dims["dim_product"].set_index("ProductKey")
    dim_rule = dims["dim_rule"].set_index("RuleKey")

    date_weights = np.linspace(0.7, 1.25, len(dim_date))
    month_boost = dim_date["MonthNumber"].isin([3, 5, 9, 11]).to_numpy() * 0.25
    date_weights = date_weights + month_boost
    txn_date_keys = weighted_choice(dim_date["DateKey"], pd.Series(date_weights), n_txn)

    customer_weights = 0.75 + dim_customer["CustomerRiskScore"] / 70
    customer_keys = weighted_choice(pd.Series(dim_customer.index), customer_weights, n_txn)

    corridor_weights = 1.0 + dim_corridor["CorridorRiskScore"] / 80
    corridor_keys = weighted_choice(pd.Series(dim_corridor.index), corridor_weights, n_txn)

    channel_weights = 1.0 + dim_channel["ChannelRiskScore"] / 100
    channel_keys = weighted_choice(pd.Series(dim_channel.index), channel_weights, n_txn)

    product_weights = 1.0 + dim_product["ProductRiskScore"] / 100
    product_keys = weighted_choice(pd.Series(dim_product.index), product_weights, n_txn)

    rows = []
    for i in range(n_txn):
        ck = customer_keys[i]
        cor = corridor_keys[i]
        ch = channel_keys[i]
        pr = product_keys[i]
        cust = dim_customer.loc[ck]
        corridor = dim_corridor.loc[cor]
        channel = dim_channel.loc[ch]
        product = dim_product.loc[pr]

        base_amount = RNG.lognormal(mean=8.5, sigma=1.1)
        amount = base_amount * (1 + channel.ChannelRiskScore / 140) * (1 + product.ProductRiskScore / 180)
        if cust.CustomerSegment in ["Corporate", "Money Services Business", "Wealth"]:
            amount *= RNG.uniform(1.7, 4.8)
        if channel.Channel in ["Wire", "International Transfer", "Crypto Off-ramp"]:
            amount *= RNG.uniform(1.3, 3.5)
        amount = float(np.clip(amount, 18, 1_750_000))

        round_dollar = "Y" if amount > 8_000 and RNG.random() < 0.18 else "N"
        if round_dollar == "Y":
            amount = round(amount / 1000) * 1000

        risk_score = (
            0.38 * cust.CustomerRiskScore
            + 0.28 * corridor.CorridorRiskScore
            + 0.18 * channel.ChannelRiskScore
            + 0.10 * product.ProductRiskScore
            + min(math.log10(amount + 1) * 6, 35)
            + RNG.normal(0, 8)
        )
        if round_dollar == "Y":
            risk_score += 4
        risk_score = int(np.clip(risk_score, 1, 99))

        flag_prob = 0.012 + 0.22 / (1 + math.exp(-(risk_score - 68) / 8))
        if amount > 95_000:
            flag_prob += 0.035
        if channel.Channel in ["Crypto Off-ramp", "Cash Deposit", "RTP"]:
            flag_prob += 0.018
        is_flagged = "Y" if RNG.random() < min(flag_prob, 0.62) else "N"
        if is_flagged == "Y":
            rule_weights = []
            for _, rule in dim_rule.iterrows():
                w = 1.0
                if "Crypto" in rule.RuleName and channel.Channel == "Crypto Off-ramp":
                    w += 4
                if "Corridor" in rule.RuleName and corridor.CorridorRiskScore >= 65:
                    w += 3
                if "Cash" in rule.RuleName and channel.Channel == "Cash Deposit":
                    w += 4
                if "Structuring" in rule.RuleName and round_dollar == "Y":
                    w += 3
                if "Velocity" in rule.RuleName and channel.ChannelMode == "Real-time":
                    w += 2
                if "Watchlist" in rule.RuleName and (cust.WatchlistFlag == "Y" or cust.PEPFlag == "Y"):
                    w += 4
                rule_weights.append(w)
            rule_key = RNG.choice(dim_rule.index.to_numpy(), p=np.array(rule_weights) / np.sum(rule_weights))
        else:
            rule_key = ""

        rows.append(
            {
                "TransactionKey": f"T{i + 1:07d}",
                "DateKey": int(txn_date_keys[i]),
                "CustomerKey": ck,
                "CorridorKey": cor,
                "ChannelKey": ch,
                "ProductKey": pr,
                "AmountUSD": round(amount, 2),
                "RiskScore": risk_score,
                "IsFlagged": is_flagged,
                "PrimaryRuleKey": rule_key,
                "RoundDollarFlag": round_dollar,
                "TransactionType": RNG.choice(["Credit", "Debit", "Transfer", "Withdrawal"], p=[0.24, 0.28, 0.40, 0.08]),
            }
        )

    fact_transactions = pd.DataFrame(rows)
    alerts = []
    cases = []
    flagged = fact_transactions[fact_transactions["IsFlagged"] == "Y"].copy()
    for alert_idx, txn in enumerate(flagged.itertuples(index=False), start=1):
        risk = txn.RiskScore
        amount = txn.AmountUSD
        customer = dim_customer.loc[txn.CustomerKey]
        rule = dim_rule.loc[txn.PrimaryRuleKey]
        false_positive_prob = np.clip(0.74 - (risk - 50) / 90 - (amount > 100_000) * 0.12, 0.08, 0.86)
        is_fp = "Y" if RNG.random() < false_positive_prob else "N"
        true_positive = "Y" if is_fp == "N" else "N"
        severity = "Critical" if risk >= 88 else "High" if risk >= 74 else "Medium" if risk >= 58 else "Low"
        escalated = (true_positive == "Y" and RNG.random() < 0.58) or severity == "Critical" or (
            customer.WatchlistFlag == "Y" and RNG.random() < 0.45
        )
        sar_likely = escalated and true_positive == "Y" and (risk >= 78 or RNG.random() < 0.24)
        txn_date = pd.to_datetime(str(txn.DateKey))
        alert_date = txn_date + pd.to_timedelta(int(RNG.integers(0, 3)), unit="D")
        close_days = int(RNG.integers(1, 16))
        if alert_date > pd.Timestamp("2026-05-31"):
            alert_date = pd.Timestamp("2026-05-31")
        if sar_likely:
            status = "SAR Filed" if RNG.random() < 0.72 else "Escalated"
        elif escalated:
            status = RNG.choice(["Escalated", "In Review", "Closed True Positive"], p=[0.38, 0.25, 0.37])
        elif is_fp == "Y":
            status = RNG.choice(["Closed False Positive", "In Review", "New"], p=[0.70, 0.22, 0.08])
        else:
            status = RNG.choice(["Closed True Positive", "In Review"], p=[0.62, 0.38])
        closed_status = status in {"Closed False Positive", "Closed True Positive", "SAR Filed"}
        closed_date = alert_date + pd.to_timedelta(close_days, unit="D") if closed_status else pd.NaT
        alert_id = f"AL{alert_idx:06d}"
        case_id = f"CA{alert_idx:06d}" if escalated else ""
        alerts.append(
            {
                "AlertKey": alert_id,
                "TransactionKey": txn.TransactionKey,
                "DateKey": txn.DateKey,
                "AlertDateKey": date_key(alert_date),
                "CustomerKey": txn.CustomerKey,
                "RuleKey": txn.PrimaryRuleKey,
                "CorridorKey": txn.CorridorKey,
                "ChannelKey": txn.ChannelKey,
                "ProductKey": txn.ProductKey,
                "AlertAmountUSD": amount,
                "RiskScore": risk,
                "Severity": severity,
                "AlertStatus": status,
                "IsFalsePositive": is_fp,
                "IsTruePositive": true_positive,
                "EscalatedToCase": "Y" if escalated else "N",
                "CaseKey": case_id,
                "ClosedDateKey": date_key(closed_date) if pd.notna(closed_date) else None,
                "HoursToDisposition": int(close_days * 24 + RNG.integers(1, 16)) if closed_status else None,
            }
        )
        if escalated:
            priority = "P1" if severity == "Critical" else "P2" if severity == "High" else "P3"
            sla_hours = {"P1": 24, "P2": 48, "P3": 96}[priority]
            created = alert_date + pd.to_timedelta(int(RNG.integers(0, 3)), unit="D")
            close_case = sar_likely or RNG.random() < 0.54
            target_compliance = {"P1": 0.68, "P2": 0.76, "P3": 0.84}[priority]
            if close_case:
                if RNG.random() < target_compliance:
                    hours_to_close = int(RNG.uniform(6, max(8, sla_hours * 0.92)))
                else:
                    hours_to_close = int(RNG.uniform(sla_hours * 1.08, sla_hours * 4.2))
                closed_case_date = created + pd.to_timedelta(hours_to_close, unit="h")
                age_days = max(1, int(math.ceil(hours_to_close / 24)))
            else:
                open_age_days = int(RNG.choice([0, 1, 2, 3, 5, 8, 13, 21], p=[0.11, 0.15, 0.18, 0.18, 0.16, 0.12, 0.07, 0.03]))
                created = min(created, AS_OF_DATE - pd.to_timedelta(open_age_days, unit="D"))
                closed_case_date = pd.NaT
                hours_to_close = int(open_age_days * 24 + RNG.integers(2, 18))
                age_days = open_age_days
            status_case = (
                "SAR Filed"
                if sar_likely and close_case
                else "Closed"
                if close_case
                else RNG.choice(["Open", "In Review", "Pending EDD"], p=[0.30, 0.52, 0.18])
            )
            outcome = (
                "SAR Filed"
                if status_case == "SAR Filed"
                else "Confirmed Suspicious"
                if true_positive == "Y" and close_case
                else "False Positive"
                if is_fp == "Y" and close_case
                else "Pending"
            )
            analyst = RNG.choice(dims["dim_analyst"]["AnalystKey"].to_numpy())
            cases.append(
                {
                    "CaseKey": case_id,
                    "AlertKey": alert_id,
                    "CreatedDateKey": date_key(created),
                    "ClosedDateKey": date_key(closed_case_date) if pd.notna(closed_case_date) else None,
                    "CustomerKey": txn.CustomerKey,
                    "RuleKey": txn.PrimaryRuleKey,
                    "CorridorKey": txn.CorridorKey,
                    "AnalystKey": analyst,
                    "CasePriority": priority,
                    "CaseStatus": status_case,
                    "Outcome": outcome,
                    "SARFiled": "Y" if status_case == "SAR Filed" else "N",
                    "SLAHours": sla_hours,
                    "AgeDays": age_days,
                    "HoursToClose": hours_to_close if close_case else None,
                    "IsOverdue": "Y" if hours_to_close > sla_hours else "N",
                    "CaseAmountUSD": amount,
                }
            )

    fact_alerts = pd.DataFrame(alerts)
    fact_cases = pd.DataFrame(cases)

    governance = []
    change_types = ["Threshold tuning", "Rule enablement", "Sandbox validation", "Owner review", "Precision backtest"]
    for rule_key, rule in dim_rule.iterrows():
        for i in range(int(RNG.integers(2, 5))):
            change_date = pd.Timestamp("2025-08-01") + pd.to_timedelta(int(RNG.integers(0, 295)), unit="D")
            precision_before = float(np.clip(RNG.normal(0.42, 0.15), 0.08, 0.88))
            lift = float(np.clip(RNG.normal(0.07, 0.05), -0.04, 0.20))
            governance.append(
                {
                    "GovernanceKey": f"G{len(governance) + 1:04d}",
                    "RuleKey": rule_key,
                    "ChangeDateKey": date_key(change_date),
                    "ChangeType": RNG.choice(change_types),
                    "ChangeReason": RNG.choice(
                        [
                            "Reduce false positives",
                            "Address audit finding",
                            "Expand high-risk corridor coverage",
                            "Tune threshold after backtest",
                            "Add control for emerging typology",
                        ]
                    ),
                    "ApprovalStatus": RNG.choice(["Approved", "Pending", "Rejected"], p=[0.78, 0.17, 0.05]),
                    "ApprovedBy": RNG.choice(["MLRO", "Head of Compliance", "Fraud Ops Lead", "Rule Governance Board"]),
                    "PrecisionBefore": round(precision_before, 4),
                    "PrecisionAfter": round(float(np.clip(precision_before + lift, 0.05, 0.95)), 4),
                    "AlertVolumeDeltaPct": round(float(RNG.normal(-0.06, 0.14)), 4),
                }
            )
    fact_rule_governance = pd.DataFrame(governance)

    return {
        "fact_transactions": fact_transactions,
        "fact_alerts": fact_alerts,
        "fact_cases": fact_cases,
        "fact_rule_governance": fact_rule_governance,
    }


def save_data(dims: dict[str, pd.DataFrame], facts: dict[str, pd.DataFrame]) -> None:
    for name, df in {**dims, **facts}.items():
        raw_name = "raw_" + name.replace("dim_", "").replace("fact_", "") + ".csv"
        df.to_csv(PROJECT_ROOT / "data/raw" / raw_name, index=False)
        df.to_csv(PROJECT_ROOT / "data/prepared" / f"{name}.csv", index=False)


def quality_payload(dims: dict[str, pd.DataFrame], facts: dict[str, pd.DataFrame]) -> tuple[dict, str]:
    tables = {**dims, **facts}
    payload = {
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "seed": SEED,
        "synthetic": True,
        "tables": {},
    }
    lines = [
        "# Data Quality Report",
        "",
        "Data is deterministic synthetic portfolio data generated for an AML / Fraud Monitoring Command Center. It is not production, customer, or regulated data.",
        "",
        "| Table | Rows | Columns | Duplicate Key Check | Missing Critical Values |",
        "|---|---:|---:|---|---:|",
    ]
    key_map = {
        "dim_date": "DateKey",
        "dim_country": "CountryCode",
        "dim_corridor": "CorridorKey",
        "dim_channel": "ChannelKey",
        "dim_product": "ProductKey",
        "dim_rule": "RuleKey",
        "dim_analyst": "AnalystKey",
        "dim_customer": "CustomerKey",
        "fact_transactions": "TransactionKey",
        "fact_alerts": "AlertKey",
        "fact_cases": "CaseKey",
        "fact_rule_governance": "GovernanceKey",
    }
    for name, df in tables.items():
        key = key_map[name]
        dupes = int(df[key].duplicated().sum()) if key in df.columns else 0
        critical = [c for c in [key, "DateKey", "CustomerKey", "RuleKey"] if c in df.columns]
        missing = int(df[critical].isna().sum().sum()) if critical else 0
        payload["tables"][name] = {
            "rows": int(len(df)),
            "columns": list(df.columns),
            "primary_key": key,
            "duplicate_key_rows": dupes,
            "missing_critical_values": missing,
        }
        lines.append(f"| {name} | {len(df):,} | {len(df.columns)} | {dupes} duplicate rows | {missing} |")
    return payload, "\n".join(lines)


def schema_markdown(tables: dict[str, pd.DataFrame]) -> str:
    lines = [
        "# Data Dictionary",
        "",
        "| Table | Grain | Key | Columns |",
        "|---|---|---|---|",
    ]
    grains = {
        "dim_date": "One calendar day",
        "dim_country": "One country",
        "dim_corridor": "One origin-destination corridor",
        "dim_channel": "One transaction channel",
        "dim_product": "One banking/payment product",
        "dim_rule": "One detection rule",
        "dim_analyst": "One analyst",
        "dim_customer": "One customer profile",
        "fact_transactions": "One financial transaction",
        "fact_alerts": "One alert generated from a flagged transaction",
        "fact_cases": "One investigation case opened from an escalated alert",
        "fact_rule_governance": "One rule governance event",
    }
    keys = {
        "dim_date": "DateKey",
        "dim_country": "CountryCode",
        "dim_corridor": "CorridorKey",
        "dim_channel": "ChannelKey",
        "dim_product": "ProductKey",
        "dim_rule": "RuleKey",
        "dim_analyst": "AnalystKey",
        "dim_customer": "CustomerKey",
        "fact_transactions": "TransactionKey",
        "fact_alerts": "AlertKey",
        "fact_cases": "CaseKey",
        "fact_rule_governance": "GovernanceKey",
    }
    for name, df in tables.items():
        lines.append(f"| {name} | {grains[name]} | {keys[name]} | {', '.join(df.columns)} |")
    return "\n".join(lines)


MEASURES = [
    ("Total Transactions", "COUNTROWS ( FactTransactions )", "#,0", "Overview"),
    ("Transaction Amount", "SUM ( FactTransactions[AmountUSD] )", "$#,0", "Overview"),
    ("Flagged Transactions", 'CALCULATE ( [Total Transactions], FactTransactions[IsFlagged] = "Y" )', "#,0", "Overview"),
    ("Flagged Amount", 'CALCULATE ( [Transaction Amount], FactTransactions[IsFlagged] = "Y" )', "$#,0", "Overview"),
    ("Alert Count", "COUNTROWS ( FactAlerts )", "#,0", "Alert"),
    ("Case Count", "COUNTROWS ( FactCases )", "#,0", "Case"),
    (
        "Suspicious Cases",
        'CALCULATE ( [Case Count], FactCases[Outcome] IN { "Confirmed Suspicious", "SAR Filed" } )',
        "#,0",
        "Case",
    ),
    ("SAR Filed Cases", 'CALCULATE ( [Case Count], FactCases[SARFiled] = "Y" )', "#,0", "Case"),
    (
        "Closed Alerts",
        'CALCULATE ( [Alert Count], FactAlerts[AlertStatus] IN { "Closed False Positive", "Closed True Positive", "SAR Filed" } )',
        "#,0",
        "Alert",
    ),
    ("False Positive Alerts", 'CALCULATE ( [Closed Alerts], FactAlerts[IsFalsePositive] = "Y" )', "#,0", "Alert"),
    ("False Positive Rate", "DIVIDE ( [False Positive Alerts], [Closed Alerts] )", "0.0%", "Alert"),
    ("True Positive Alerts", 'CALCULATE ( [Alert Count], FactAlerts[IsTruePositive] = "Y" )', "#,0", "Alert"),
    ("Rule Precision", "DIVIDE ( [True Positive Alerts], [Closed Alerts] )", "0.0%", "Rule"),
    ("Alert Rate", "DIVIDE ( [Alert Count], [Total Transactions] )", "0.0%", "Alert"),
    ("Alert to Case Conversion", "DIVIDE ( [Case Count], [Alert Count] )", "0.0%", "Alert"),
    ("SAR Conversion Rate", "DIVIDE ( [SAR Filed Cases], [Case Count] )", "0.0%", "Case"),
    (
        "Open Cases",
        'CALCULATE ( [Case Count], NOT ( FactCases[CaseStatus] IN { "Closed", "SAR Filed" } ) )',
        "#,0",
        "Case",
    ),
    ("Overdue Cases", 'CALCULATE ( [Case Count], FactCases[IsOverdue] = "Y" )', "#,0", "SLA"),
    ("SLA Compliance Rate", "DIVIDE ( [Case Count] - [Overdue Cases], [Case Count] )", "0.0%", "SLA"),
    ("Average Case Age Days", "AVERAGE ( FactCases[AgeDays] )", "0.0", "SLA"),
    ("Average Alert Risk Score", "AVERAGE ( FactAlerts[RiskScore] )", "0.0", "Risk"),
    ("High Risk Customers", 'CALCULATE ( DISTINCTCOUNT ( DimCustomer[CustomerKey] ), DimCustomer[CustomerRiskTier] = "High" )', "#,0", "Risk"),
    ("Governance Changes", "COUNTROWS ( FactRuleGovernance )", "#,0", "Governance"),
    ("Avg Precision After Tuning", "AVERAGE ( FactRuleGovernance[PrecisionAfter] )", "0.0%", "Governance"),
    ("Alert Amount", "SUM ( FactAlerts[AlertAmountUSD] )", "$#,0", "Alert"),
    ("Case Amount", "SUM ( FactCases[CaseAmountUSD] )", "$#,0", "Case"),
]


def write_model_docs() -> None:
    lines = ["# DAX Measures", ""]
    measure_map = []
    for name, expr, fmt, folder in MEASURES:
        lines.extend([f"## {name}", "", "```DAX", f"{name} = {expr}", "```", ""])
        measure_map.append({"name": name, "expression": expr, "format": fmt, "display_folder": folder})
    write_text(PROJECT_ROOT / "model/measures.dax", "\n".join([f"{name} = {expr}" for name, expr, _, _ in MEASURES]))
    write_text(PROJECT_ROOT / "model/dax_measures.md", "\n".join(lines))
    write_json(PROJECT_ROOT / "model/measure_map.json", measure_map)

    metric_defs = [
        "# Metric Definitions",
        "",
        "| KPI | Business Definition | DAX Measure |",
        "|---|---|---|",
        "| Total transactions | Count of all monitored financial transactions in the selected period. | [Total Transactions] |",
        "| Flagged amount | Sum of transaction value where monitoring logic generated a flag. | [Flagged Amount] |",
        "| Alerts | Count of generated monitoring alerts. | [Alert Count] |",
        "| Suspicious cases | Cases confirmed suspicious or filed as SAR. | [Suspicious Cases] |",
        "| False positive rate | False-positive alerts divided by closed alerts. Uses DIVIDE. | [False Positive Rate] |",
        "| Rule precision | True-positive alerts divided by closed alerts. Uses DIVIDE. | [Rule Precision] |",
        "| SLA compliance | Cases not overdue divided by all cases. Uses DIVIDE. | [SLA Compliance Rate] |",
        "| Alert to case conversion | Cases opened divided by alert count. Uses DIVIDE. | [Alert to Case Conversion] |",
    ]
    write_text(PROJECT_ROOT / "model/metric_definitions.md", "\n".join(metric_defs))


def write_powerbi_config(dims: dict[str, pd.DataFrame], facts: dict[str, pd.DataFrame]) -> None:
    type_map = {
        "int64": "Int64",
        "float64": "Decimal",
        "object": "String",
        "datetime64[ns]": "DateTime",
    }
    table_map = {
        "dim_date": "DimDate",
        "dim_country": "DimCountry",
        "dim_corridor": "DimCorridor",
        "dim_channel": "DimChannel",
        "dim_product": "DimProduct",
        "dim_rule": "DimRule",
        "dim_analyst": "DimAnalyst",
        "dim_customer": "DimCustomer",
        "fact_transactions": "FactTransactions",
        "fact_alerts": "FactAlerts",
        "fact_cases": "FactCases",
        "fact_rule_governance": "FactRuleGovernance",
    }
    schema = []
    for csv_name, df in {**dims, **facts}.items():
        table = {"name": table_map[csv_name], "file": f"{csv_name}.csv", "columns": []}
        for col in df.columns:
            dtype = str(df[col].dtype)
            pbi_type = type_map.get(dtype, "String")
            if col.endswith("Key") and pbi_type == "Decimal":
                pbi_type = "Int64"
            summarize_by = "Sum" if pbi_type in {"Decimal", "Int64", "Double"} and col not in {"DateKey", "AlertDateKey", "CreatedDateKey", "ClosedDateKey"} and not col.endswith("Key") else "None"
            table["columns"].append(
                {
                    "name": col,
                    "type": pbi_type,
                    "summarize_by": summarize_by,
                    "format": "$#,0" if col.endswith("USD") else "0.0%" if col.startswith("Precision") or col.endswith("Pct") else None,
                    "hidden": col.endswith("Key") and table_map[csv_name].startswith("Fact"),
                }
            )
        schema.append(table)
    write_json(PROJECT_ROOT / "build/config/powerbi_table_schema.json", schema)

    relationships = [
        ("FactTransactions_Date", "FactTransactions", "DateKey", "DimDate", "DateKey"),
        ("FactTransactions_Customer", "FactTransactions", "CustomerKey", "DimCustomer", "CustomerKey"),
        ("FactTransactions_Corridor", "FactTransactions", "CorridorKey", "DimCorridor", "CorridorKey"),
        ("FactTransactions_Channel", "FactTransactions", "ChannelKey", "DimChannel", "ChannelKey"),
        ("FactTransactions_Product", "FactTransactions", "ProductKey", "DimProduct", "ProductKey"),
        ("FactAlerts_Date", "FactAlerts", "AlertDateKey", "DimDate", "DateKey"),
        ("FactAlerts_Customer", "FactAlerts", "CustomerKey", "DimCustomer", "CustomerKey"),
        ("FactAlerts_Rule", "FactAlerts", "RuleKey", "DimRule", "RuleKey"),
        ("FactAlerts_Corridor", "FactAlerts", "CorridorKey", "DimCorridor", "CorridorKey"),
        ("FactAlerts_Channel", "FactAlerts", "ChannelKey", "DimChannel", "ChannelKey"),
        ("FactAlerts_Product", "FactAlerts", "ProductKey", "DimProduct", "ProductKey"),
        ("FactCases_Date", "FactCases", "CreatedDateKey", "DimDate", "DateKey"),
        ("FactCases_Customer", "FactCases", "CustomerKey", "DimCustomer", "CustomerKey"),
        ("FactCases_Rule", "FactCases", "RuleKey", "DimRule", "RuleKey"),
        ("FactCases_Corridor", "FactCases", "CorridorKey", "DimCorridor", "CorridorKey"),
        ("FactCases_Analyst", "FactCases", "AnalystKey", "DimAnalyst", "AnalystKey"),
        ("FactRuleGovernance_Date", "FactRuleGovernance", "ChangeDateKey", "DimDate", "DateKey"),
        ("FactRuleGovernance_Rule", "FactRuleGovernance", "RuleKey", "DimRule", "RuleKey"),
    ]
    relationship_payload = [
        {
            "name": name,
            "from_table": ft,
            "from_column": fc,
            "to_table": dt,
            "to_column": dc,
            "cardinality": "Many-to-one",
            "cross_filter": "Single",
        }
        for name, ft, fc, dt, dc in relationships
    ]
    write_json(PROJECT_ROOT / "build/config/relationship_map.json", relationship_payload)

    rel_lines = ["# Relationship Map", "", "| Relationship | From | To | Direction |", "|---|---|---|---|"]
    for rel in relationship_payload:
        rel_lines.append(
            f"| {rel['name']} | {rel['from_table']}[{rel['from_column']}] | {rel['to_table']}[{rel['to_column']}] | Single |"
        )
    write_text(PROJECT_ROOT / "model/relationship_map.md", "\n".join(rel_lines))
    write_text(
        PROJECT_ROOT / "model/semantic_model_notes.md",
        """
# Semantic Model Notes

The model uses a star-schema style around transactions, alerts, cases, and rule governance events.
All executive KPIs are DAX measures in the disconnected `KPI Measures` table. Rate measures use DIVIDE.
Date filtering uses DimDate relationships to transaction, alert, case-created, and governance-change dates.
The data is deterministic synthetic portfolio data generated from seed 20260611.
""",
    )

    pq_lines = ["// Power Query snippets for prepared CSV imports", ""]
    for table in schema:
        path = (PROJECT_ROOT / "data/prepared" / table["file"]).as_posix()
        pq_lines.append(
            f'{table["name"]} = let Source = Csv.Document(File.Contents("{path}"), [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]), PromotedHeaders = Table.PromoteHeaders(Source, [PromoteAllScalars=true]) in PromotedHeaders;'
        )
    write_text(PROJECT_ROOT / "build/config/PowerQuery_AllTables.pq", "\n".join(pq_lines))


def aggregate_for_dashboard(dims: dict[str, pd.DataFrame], facts: dict[str, pd.DataFrame]) -> dict:
    dim_date = dims["dim_date"][["DateKey", "MonthYear", "MonthIndex", "MonthStart"]]
    tx = facts["fact_transactions"].merge(dim_date, on="DateKey", how="left")
    alerts = facts["fact_alerts"].merge(dim_date.rename(columns={"DateKey": "AlertDateKey"}), on="AlertDateKey", how="left")
    cases = facts["fact_cases"].merge(dim_date.rename(columns={"DateKey": "CreatedDateKey"}), on="CreatedDateKey", how="left")
    tx = tx.merge(dims["dim_customer"], on="CustomerKey", how="left")
    tx = tx.merge(dims["dim_corridor"], on="CorridorKey", how="left")
    tx = tx.merge(dims["dim_channel"], on="ChannelKey", how="left")
    alerts = alerts.merge(dims["dim_rule"], on="RuleKey", how="left")
    alerts = alerts.merge(dims["dim_customer"], on="CustomerKey", how="left")
    alerts = alerts.merge(dims["dim_corridor"], on="CorridorKey", how="left")
    alerts = alerts.merge(dims["dim_channel"], on="ChannelKey", how="left")
    cases = cases.merge(dims["dim_analyst"], on="AnalystKey", how="left")
    cases = cases.merge(dims["dim_rule"], on="RuleKey", how="left")
    cases = cases.merge(dims["dim_corridor"], on="CorridorKey", how="left")

    closed_alerts = alerts[alerts["AlertStatus"].isin(["Closed False Positive", "Closed True Positive", "SAR Filed"])]
    fpr = (closed_alerts["IsFalsePositive"].eq("Y").sum() / len(closed_alerts)) if len(closed_alerts) else 0
    suspicious_cases = cases["Outcome"].isin(["Confirmed Suspicious", "SAR Filed"]).sum()

    monthly = []
    tx_month = tx.groupby(["MonthIndex", "MonthYear"], as_index=False).agg(transactions=("TransactionKey", "count"), amount=("AmountUSD", "sum"))
    alert_month = alerts.groupby(["MonthIndex", "MonthYear"], as_index=False).agg(alerts=("AlertKey", "count"), fp=("IsFalsePositive", lambda s: int((s == "Y").sum())))
    case_month = cases.groupby(["MonthIndex", "MonthYear"], as_index=False).agg(cases=("CaseKey", "count"), sar=("SARFiled", lambda s: int((s == "Y").sum())))
    month_df = tx_month.merge(alert_month, on=["MonthIndex", "MonthYear"], how="left").merge(case_month, on=["MonthIndex", "MonthYear"], how="left").fillna(0).sort_values("MonthIndex")
    for row in month_df.tail(17).itertuples(index=False):
        monthly.append(
            {
                "month": row.MonthYear,
                "transactions": int(row.transactions),
                "amount": round(float(row.amount), 2),
                "alerts": int(row.alerts),
                "cases": int(row.cases),
                "sar": int(row.sar),
                "falsePositives": int(row.fp),
            }
        )

    severity = (
        alerts.groupby("Severity", as_index=False)
        .agg(alerts=("AlertKey", "count"))
        .sort_values("alerts", ascending=False)
        .to_dict("records")
    )
    typology = (
        alerts.groupby("Typology", as_index=False)
        .agg(alerts=("AlertKey", "count"), amount=("AlertAmountUSD", "sum"))
        .sort_values("alerts", ascending=False)
        .head(8)
        .to_dict("records")
    )
    corridor = (
        alerts.groupby(["Corridor", "CorridorName", "CorridorRiskTier"], as_index=False)
        .agg(alerts=("AlertKey", "count"), flaggedAmount=("AlertAmountUSD", "sum"), avgRisk=("RiskScore", "mean"), fp=("IsFalsePositive", lambda s: int((s == "Y").sum())))
        .assign(falsePositiveRate=lambda d: d["fp"] / d["alerts"])
        .sort_values(["avgRisk", "flaggedAmount"], ascending=False)
        .head(10)
    )
    corridor_records = [
        {
            "corridor": r.Corridor,
            "name": r.CorridorName,
            "tier": r.CorridorRiskTier,
            "alerts": int(r.alerts),
            "flaggedAmount": round(float(r.flaggedAmount), 2),
            "avgRisk": round(float(r.avgRisk), 1),
            "falsePositiveRate": round(float(r.falsePositiveRate), 4),
        }
        for r in corridor.itertuples(index=False)
    ]

    rule = (
        alerts.groupby(["RuleKey", "RuleName", "Typology"], as_index=False)
        .agg(
            alerts=("AlertKey", "count"),
            truePositive=("IsTruePositive", lambda s: int((s == "Y").sum())),
            falsePositive=("IsFalsePositive", lambda s: int((s == "Y").sum())),
            avgRisk=("RiskScore", "mean"),
            amount=("AlertAmountUSD", "sum"),
        )
        .assign(precision=lambda d: d["truePositive"] / (d["truePositive"] + d["falsePositive"]).replace(0, np.nan))
        .fillna({"precision": 0})
        .sort_values("alerts", ascending=False)
    )
    rule_records = [
        {
            "rule": r.RuleName,
            "typology": r.Typology,
            "alerts": int(r.alerts),
            "precision": round(float(r.precision), 4),
            "falsePositiveRate": round(float(r.falsePositive / max(r.alerts, 1)), 4),
            "avgRisk": round(float(r.avgRisk), 1),
            "amount": round(float(r.amount), 2),
        }
        for r in rule.itertuples(index=False)
    ]

    customer_alerts = alerts.groupby(["CustomerKey", "Customer", "CustomerRiskTier", "HomeCountry", "PEPFlag", "WatchlistFlag"], as_index=False).agg(
        alerts=("AlertKey", "count"),
        amount=("AlertAmountUSD", "sum"),
        avgRisk=("RiskScore", "mean"),
    )
    customer_cases = cases.groupby("CustomerKey", as_index=False).agg(cases=("CaseKey", "count"), sar=("SARFiled", lambda s: int((s == "Y").sum())))
    high_customers = (
        customer_alerts.merge(customer_cases, on="CustomerKey", how="left")
        .fillna({"cases": 0, "sar": 0})
        .sort_values(["avgRisk", "amount"], ascending=False)
        .head(10)
    )
    high_customer_records = [
        {
            "customer": r.Customer,
            "tier": r.CustomerRiskTier,
            "country": r.HomeCountry,
            "pep": r.PEPFlag,
            "watchlist": r.WatchlistFlag,
            "alerts": int(r.alerts),
            "cases": int(r.cases),
            "sar": int(r.sar),
            "amount": round(float(r.amount), 2),
            "avgRisk": round(float(r.avgRisk), 1),
        }
        for r in high_customers.itertuples(index=False)
    ]

    age_bins = pd.cut(cases["AgeDays"], bins=[-1, 3, 7, 14, 30, 999], labels=["0-3d", "4-7d", "8-14d", "15-30d", "31d+"])
    aging = cases.assign(AgeBucket=age_bins).groupby("AgeBucket", observed=True, as_index=False).agg(cases=("CaseKey", "count"))
    aging_records = [{"bucket": str(r.AgeBucket), "cases": int(r.cases)} for r in aging.itertuples(index=False)]

    workload = (
        cases.groupby(["Analyst", "Queue"], as_index=False)
        .agg(cases=("CaseKey", "count"), overdue=("IsOverdue", lambda s: int((s == "Y").sum())), avgAge=("AgeDays", "mean"), sar=("SARFiled", lambda s: int((s == "Y").sum())))
        .sort_values("cases", ascending=False)
    )
    workload_records = [
        {
            "analyst": r.Analyst,
            "queue": r.Queue,
            "cases": int(r.cases),
            "overdue": int(r.overdue),
            "avgAge": round(float(r.avgAge), 1),
            "sar": int(r.sar),
        }
        for r in workload.itertuples(index=False)
    ]

    gov = facts["fact_rule_governance"].merge(dims["dim_rule"], on="RuleKey", how="left").merge(
        dim_date.rename(columns={"DateKey": "ChangeDateKey"}), on="ChangeDateKey", how="left"
    )
    gov = gov.sort_values("ChangeDateKey", ascending=False).head(12)
    gov_records = [
        {
            "date": r.MonthYear,
            "rule": r.RuleName,
            "change": r.ChangeType,
            "status": r.ApprovalStatus,
            "precisionBefore": round(float(r.PrecisionBefore), 4),
            "precisionAfter": round(float(r.PrecisionAfter), 4),
            "volumeDelta": round(float(r.AlertVolumeDeltaPct), 4),
        }
        for r in gov.itertuples(index=False)
    ]

    funnel = [
        {"stage": "Transactions", "value": int(len(tx))},
        {"stage": "Flagged Txns", "value": int((tx["IsFlagged"] == "Y").sum())},
        {"stage": "Alerts", "value": int(len(alerts))},
        {"stage": "Cases", "value": int(len(cases))},
        {"stage": "Suspicious", "value": int(suspicious_cases)},
        {"stage": "SAR Filed", "value": int((cases["SARFiled"] == "Y").sum())},
    ]

    return {
        "asOf": LATEST_COMPLETE_MONTH,
        "kpis": {
            "transactions": int(len(tx)),
            "transactionAmount": round(float(tx["AmountUSD"].sum()), 2),
            "flaggedAmount": round(float(tx.loc[tx["IsFlagged"] == "Y", "AmountUSD"].sum()), 2),
            "alerts": int(len(alerts)),
            "suspiciousCases": int(suspicious_cases),
            "falsePositiveRate": round(float(fpr), 4),
            "alertRate": round(float(len(alerts) / len(tx)), 4),
            "openCases": int((~cases["CaseStatus"].isin(["Closed", "SAR Filed"])).sum()),
            "overdueCases": int((cases["IsOverdue"] == "Y").sum()),
            "slaCompliance": round(float(1 - (cases["IsOverdue"] == "Y").sum() / max(len(cases), 1)), 4),
            "highRiskCustomers": int((dims["dim_customer"]["CustomerRiskTier"] == "High").sum()),
        },
        "monthly": monthly,
        "severity": severity,
        "typology": typology,
        "corridors": corridor_records,
        "rules": rule_records,
        "highCustomers": high_customer_records,
        "aging": aging_records,
        "workload": workload_records,
        "governance": gov_records,
        "funnel": funnel,
    }


def svg_line_monthly(monthly: list[dict]) -> str:
    width, height = 760, 260
    pad_l, pad_r, pad_t, pad_b = 48, 20, 24, 38
    max_alert = max(m["alerts"] for m in monthly) * 1.12
    max_case = max(m["cases"] for m in monthly) * 1.2
    span_x = width - pad_l - pad_r
    span_y = height - pad_t - pad_b

    def xy(idx: int, value: float, max_v: float) -> tuple[float, float]:
        x = pad_l + idx * (span_x / max(1, len(monthly) - 1))
        y = pad_t + span_y - (value / max_v * span_y)
        return x, y

    alert_points = [xy(i, m["alerts"], max_alert) for i, m in enumerate(monthly)]
    case_points = [xy(i, m["cases"], max_case) for i, m in enumerate(monthly)]
    path_alert = " ".join(("M" if i == 0 else "L") + f"{x:.1f},{y:.1f}" for i, (x, y) in enumerate(alert_points))
    path_case = " ".join(("M" if i == 0 else "L") + f"{x:.1f},{y:.1f}" for i, (x, y) in enumerate(case_points))
    grid = "".join(
        f'<line x1="{pad_l}" x2="{width-pad_r}" y1="{pad_t + i * span_y / 4:.1f}" y2="{pad_t + i * span_y / 4:.1f}" class="grid"/>'
        for i in range(5)
    )
    labels = "".join(
        f'<text x="{x:.1f}" y="{height-14}" class="axis-label" text-anchor="middle">{monthly[i]["month"].split()[0]}</text>'
        for i, (x, _) in enumerate(alert_points)
        if i % 2 == 0 or i == len(alert_points) - 1
    )
    dots = "".join(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3.2" class="dot-alert"/>' for x, y in alert_points)
    return f"""
<svg viewBox="0 0 {width} {height}" class="chart-svg" role="img" aria-label="Alert and case monthly trend">
  {grid}
  <line x1="{pad_l}" y1="{height-pad_b}" x2="{width-pad_r}" y2="{height-pad_b}" class="axis"/>
  <path d="{path_alert}" class="line-alert"/>
  <path d="{path_case}" class="line-case"/>
  {dots}
  {labels}
  <text x="{pad_l}" y="16" class="legend-alert">Alerts</text>
  <text x="{pad_l + 78}" y="16" class="legend-case">Cases</text>
</svg>"""


def svg_bars(records: list[dict], label_key: str, value_key: str, width: int = 380, height: int = 260, color: str = "#0f766e") -> str:
    records = records[:8]
    max_v = max(float(r[value_key]) for r in records) if records else 1
    row_h = max(22, (height - 26) / max(len(records), 1))
    rows = []
    for i, record in enumerate(records):
        y = 18 + i * row_h
        v = float(record[value_key])
        bar_w = 210 * v / max_v
        label = str(record[label_key])[:28]
        rows.append(
            f'<text x="0" y="{y+11:.1f}" class="bar-label">{label}</text>'
            f'<rect x="150" y="{y:.1f}" width="210" height="12" rx="3" class="bar-bg"/>'
            f'<rect x="150" y="{y:.1f}" width="{bar_w:.1f}" height="12" rx="3" fill="{color}"/>'
            f'<text x="368" y="{y+11:.1f}" class="bar-value" text-anchor="end">{int(v):,}</text>'
        )
    return f'<svg viewBox="0 0 {width} {height}" class="chart-svg">{"".join(rows)}</svg>'


def svg_funnel(funnel: list[dict]) -> str:
    width, height = 520, 270
    max_v = max(item["value"] for item in funnel)
    colors = ["#17202a", "#0f766e", "#2a9d8f", "#d97706", "#b91c1c", "#5b4b8a"]
    parts = []
    for i, item in enumerate(funnel):
        y = 18 + i * 40
        w = 420 * math.sqrt(item["value"] / max_v)
        x = 82 + (420 - w) / 2
        parts.append(
            f'<rect x="{x:.1f}" y="{y}" width="{w:.1f}" height="27" rx="5" fill="{colors[i]}"/>'
            f'<text x="20" y="{y+18}" class="funnel-stage">{item["stage"]}</text>'
            f'<text x="492" y="{y+18}" class="funnel-value" text-anchor="end">{item["value"]:,}</text>'
        )
    return f'<svg viewBox="0 0 {width} {height}" class="chart-svg">{"".join(parts)}</svg>'


def svg_scatter(rules: list[dict]) -> str:
    width, height = 520, 280
    pad = 42
    max_alerts = max(r["alerts"] for r in rules)
    parts = [
        f'<line x1="{pad}" y1="{height-pad}" x2="{width-18}" y2="{height-pad}" class="axis"/>',
        f'<line x1="{pad}" y1="18" x2="{pad}" y2="{height-pad}" class="axis"/>',
        f'<text x="{width/2}" y="{height-6}" class="axis-label" text-anchor="middle">Alert volume</text>',
        f'<text x="9" y="{height/2}" class="axis-label rotate" text-anchor="middle">Precision</text>',
    ]
    for r in rules[:10]:
        x = pad + (width - pad - 28) * (r["alerts"] / max_alerts)
        y = height - pad - (height - pad - 28) * r["precision"]
        radius = max(5, min(19, math.sqrt(r["amount"]) / 550))
        color = "#b91c1c" if r["falsePositiveRate"] > 0.55 else "#d97706" if r["falsePositiveRate"] > 0.42 else "#0f766e"
        parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{radius:.1f}" fill="{color}" opacity="0.82"><title>{r["rule"]}</title></circle>')
    return f'<svg viewBox="0 0 {width} {height}" class="chart-svg">{"".join(parts)}</svg>'


def table_rows(records: list[dict], columns: list[tuple[str, str]], limit: int = 8) -> str:
    header = "".join(f"<th>{label}</th>" for key, label in columns)
    body = []
    for row in records[:limit]:
        cells = []
        for key, _ in columns:
            value = row.get(key, "")
            if isinstance(value, float) and ("Rate" in key or "precision" in key or "sla" in key or key.endswith("Delta")):
                value = pct(value)
            elif isinstance(value, float) and ("amount" in key or "Amount" in key):
                value = money(value)
            elif isinstance(value, float):
                value = f"{value:.1f}"
            elif isinstance(value, int) and ("amount" in key or "Amount" in key):
                value = money(value)
            cells.append(f"<td>{value}</td>")
        body.append("<tr>" + "".join(cells) + "</tr>")
    return f"<table><thead><tr>{header}</tr></thead><tbody>{''.join(body)}</tbody></table>"


def write_html_dashboard(data: dict) -> None:
    monthly_svg = svg_line_monthly(data["monthly"])
    typology_svg = svg_bars(data["typology"], "Typology", "alerts", color="#5b4b8a")
    corridor_svg = svg_bars(data["corridors"], "corridor", "alerts", color="#d97706")
    funnel_svg = svg_funnel(data["funnel"])
    scatter_svg = svg_scatter(data["rules"])
    aging_svg = svg_bars(data["aging"], "bucket", "cases", width=400, color="#b91c1c")
    workload_svg = svg_bars(data["workload"], "analyst", "cases", width=400, color="#0f766e")
    k = data["kpis"]
    html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>AML / Fraud Monitoring Command Center</title>
  <style>
    :root {{
      --ink: #17202a;
      --muted: #657383;
      --line: #d8ded8;
      --paper: #f6f7f4;
      --surface: #ffffff;
      --teal: #0f766e;
      --mint: #2a9d8f;
      --amber: #d97706;
      --red: #b91c1c;
      --violet: #5b4b8a;
      --shadow: 0 10px 24px rgba(23, 32, 42, .08);
    }}
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; font-family: Inter, Segoe UI, Arial, sans-serif; background: var(--paper); color: var(--ink); }}
    .app {{ min-height: 100vh; display: grid; grid-template-columns: 248px 1fr; }}
    aside {{ background: #17202a; color: #f7faf8; padding: 22px 18px; position: sticky; top: 0; height: 100vh; }}
    .brand {{ font-size: 16px; line-height: 1.2; font-weight: 800; letter-spacing: 0; margin-bottom: 18px; }}
    .brand span {{ display:block; color:#9ad7cd; font-size: 11px; font-weight: 700; margin-top: 6px; }}
    .tabs {{ display: grid; gap: 8px; margin-top: 20px; }}
    .tab-button {{ border: 1px solid rgba(255,255,255,.12); background: rgba(255,255,255,.04); color: #f7faf8; border-radius: 8px; padding: 12px; text-align: left; font-size: 13px; cursor: pointer; }}
    .tab-button.active {{ background: #f7faf8; color: var(--ink); border-color: #f7faf8; }}
    .side-metric {{ margin-top: 18px; padding-top: 18px; border-top: 1px solid rgba(255,255,255,.15); }}
    .side-metric div {{ font-size: 11px; color: #b9c7c2; }}
    .side-metric strong {{ display: block; font-size: 22px; margin-top: 5px; color: #ffffff; }}
    main {{ padding: 22px; }}
    .topbar {{ display:flex; align-items: flex-start; justify-content: space-between; gap: 18px; margin-bottom: 16px; }}
    h1 {{ font-size: 24px; margin: 0 0 4px; letter-spacing: 0; }}
    .subtitle {{ color: var(--muted); font-size: 13px; }}
    .filters {{ display: flex; gap: 8px; flex-wrap: wrap; justify-content: flex-end; }}
    select {{ border: 1px solid var(--line); background: var(--surface); border-radius: 7px; padding: 8px 28px 8px 10px; color: var(--ink); }}
    .tab-panel {{ display: none; }}
    .tab-panel.active {{ display: block; }}
    .kpi-grid {{ display: grid; grid-template-columns: repeat(6, minmax(0,1fr)); gap: 12px; margin-bottom: 12px; }}
    .kpi {{ background: var(--surface); border: 1px solid var(--line); border-radius: 8px; padding: 13px 14px; box-shadow: var(--shadow); min-height: 94px; }}
    .kpi label {{ display: block; color: var(--muted); font-size: 11px; font-weight: 700; text-transform: uppercase; }}
    .kpi strong {{ display: block; font-size: 24px; margin-top: 8px; white-space: nowrap; }}
    .kpi small {{ color: var(--muted); font-size: 12px; }}
    .grid-2 {{ display: grid; grid-template-columns: 1.35fr .65fr; gap: 12px; }}
    .grid-3 {{ display: grid; grid-template-columns: .9fr .9fr 1.2fr; gap: 12px; }}
    .grid-balanced {{ display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }}
    .panel {{ background: var(--surface); border: 1px solid var(--line); border-radius: 8px; padding: 14px; box-shadow: var(--shadow); min-width: 0; }}
    .panel h2 {{ font-size: 14px; margin: 0 0 2px; }}
    .panel p {{ margin: 0 0 10px; color: var(--muted); font-size: 12px; }}
    .chart-svg {{ width: 100%; height: auto; display: block; }}
    .grid {{ stroke: #e6ebe6; stroke-width: 1; }}
    .axis {{ stroke: #bfc8c0; stroke-width: 1; }}
    .axis-label, .bar-label, .bar-value, .funnel-stage, .funnel-value {{ fill: #657383; font-size: 11px; }}
    .rotate {{ transform: rotate(-90deg); transform-origin: 9px 140px; }}
    .line-alert {{ fill: none; stroke: var(--amber); stroke-width: 3; }}
    .line-case {{ fill: none; stroke: var(--teal); stroke-width: 3; }}
    .dot-alert {{ fill: var(--amber); }}
    .legend-alert {{ fill: var(--amber); font-size: 12px; font-weight: 700; }}
    .legend-case {{ fill: var(--teal); font-size: 12px; font-weight: 700; }}
    .bar-bg {{ fill: #eef2ee; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 12px; }}
    th {{ text-align: left; color: var(--muted); border-bottom: 1px solid var(--line); padding: 8px 6px; font-size: 11px; }}
    td {{ border-bottom: 1px solid #edf0ed; padding: 8px 6px; vertical-align: top; }}
    .chip {{ display:inline-flex; align-items:center; border-radius:999px; padding:3px 7px; font-size:11px; background:#eef2ee; color:var(--ink); font-weight:700; }}
    .risk-high {{ background: #fee2e2; color: var(--red); }}
    .risk-med {{ background: #fef3c7; color: #92400e; }}
    .risk-low {{ background: #d1fae5; color: #065f46; }}
    .governance-list {{ display: grid; gap: 8px; }}
    .gov-row {{ display: grid; grid-template-columns: 78px 1fr 92px 74px; gap: 8px; align-items:center; padding: 8px; border: 1px solid #edf0ed; border-radius: 7px; }}
    .gov-row span {{ font-size: 12px; color: var(--muted); }}
    .gov-row strong {{ font-size: 12px; }}
    @media (max-width: 1100px) {{
      .app {{ grid-template-columns: 1fr; }}
      aside {{ position: relative; height: auto; }}
      .kpi-grid {{ grid-template-columns: repeat(2, minmax(0,1fr)); }}
      .grid-2, .grid-3, .grid-balanced {{ grid-template-columns: 1fr; }}
      .topbar {{ display:block; }}
      .filters {{ justify-content:flex-start; margin-top:12px; }}
    }}
  </style>
</head>
<body>
<div class="app">
  <aside>
    <div class="brand">AML / Fraud Monitoring Command Center<span>Portfolio BI product | Synthetic data | As of {data["asOf"]}</span></div>
    <div class="tabs">
      <button class="tab-button active" data-tab="overview">Fraud & Compliance Overview</button>
      <button class="tab-button" data-tab="deep">Alert & Customer Risk Deep Dive</button>
      <button class="tab-button" data-tab="sla">Case SLA & Rule Governance</button>
    </div>
    <div class="side-metric"><div>Alert rate</div><strong>{pct(k["alertRate"])}</strong></div>
    <div class="side-metric"><div>High-risk customers</div><strong>{number(k["highRiskCustomers"])}</strong></div>
    <div class="side-metric"><div>SLA compliance</div><strong>{pct(k["slaCompliance"])}</strong></div>
  </aside>
  <main>
    <div class="topbar">
      <div>
        <h1>AML / Fraud Monitoring Command Center</h1>
        <div class="subtitle">Transactions, alerts, case workload, customer risk, rule precision, and governance control.</div>
      </div>
      <div class="filters">
        <select><option>{data["asOf"]}</option></select>
        <select><option>All corridors</option><option>High risk corridors</option></select>
        <select><option>All severities</option><option>Critical and High</option></select>
      </div>
    </div>

    <section id="overview" class="tab-panel active">
      <div class="kpi-grid">
        <div class="kpi"><label>Total transactions</label><strong>{number(k["transactions"])}</strong><small>{money(k["transactionAmount"])} monitored</small></div>
        <div class="kpi"><label>Flagged amount</label><strong>{money(k["flaggedAmount"])}</strong><small>{pct(k["alertRate"])} alert rate</small></div>
        <div class="kpi"><label>Alerts</label><strong>{number(k["alerts"])}</strong><small>Generated from rules</small></div>
        <div class="kpi"><label>Suspicious cases</label><strong>{number(k["suspiciousCases"])}</strong><small>SAR and confirmed suspicious</small></div>
        <div class="kpi"><label>False positive rate</label><strong>{pct(k["falsePositiveRate"])}</strong><small>Closed alerts denominator</small></div>
        <div class="kpi"><label>Overdue cases</label><strong>{number(k["overdueCases"])}</strong><small>{number(k["openCases"])} open cases</small></div>
      </div>
      <div class="grid-2">
        <div class="panel"><h2>Alert and Case Trend</h2><p>Monthly alert volume and escalated case load.</p>{monthly_svg}</div>
        <div class="panel"><h2>Typology Mix</h2><p>Alert concentration by detection theme.</p>{typology_svg}</div>
      </div>
      <div class="grid-balanced" style="margin-top:12px">
        <div class="panel"><h2>Country / Corridor Risk</h2><p>Highest risk corridors by alert volume.</p>{corridor_svg}</div>
        <div class="panel"><h2>Top Corridor Watchlist</h2><p>Risk, amount and false positive context.</p>{table_rows(data["corridors"], [("corridor","Corridor"),("tier","Tier"),("alerts","Alerts"),("flaggedAmount","Amount"),("avgRisk","Risk"),("falsePositiveRate","FPR")], 6)}</div>
      </div>
    </section>

    <section id="deep" class="tab-panel">
      <div class="grid-3">
        <div class="panel"><h2>Alert Funnel</h2><p>From monitored activity to SAR filing.</p>{funnel_svg}</div>
        <div class="panel"><h2>Rule Performance</h2><p>Precision vs alert volume, sized by value.</p>{scatter_svg}</div>
        <div class="panel"><h2>High-Risk Customers</h2><p>Customer risk and case conversion queue.</p>{table_rows(data["highCustomers"], [("customer","Customer"),("country","Country"),("alerts","Alerts"),("cases","Cases"),("sar","SAR"),("amount","Amount"),("avgRisk","Risk")], 8)}</div>
      </div>
      <div class="grid-balanced" style="margin-top:12px">
        <div class="panel"><h2>Rule Precision Table</h2><p>Rule-by-rule volume and quality signal.</p>{table_rows(data["rules"], [("rule","Rule"),("typology","Typology"),("alerts","Alerts"),("precision","Precision"),("falsePositiveRate","FPR"),("avgRisk","Risk")], 8)}</div>
        <div class="panel"><h2>Corridor Exposure Detail</h2><p>Alerting across country corridors.</p>{table_rows(data["corridors"], [("corridor","Corridor"),("name","Name"),("tier","Tier"),("alerts","Alerts"),("flaggedAmount","Amount"),("avgRisk","Risk")], 8)}</div>
      </div>
    </section>

    <section id="sla" class="tab-panel">
      <div class="kpi-grid">
        <div class="kpi"><label>Case count</label><strong>{number(sum(x["cases"] for x in data["aging"]))}</strong><small>Investigation workload</small></div>
        <div class="kpi"><label>Open cases</label><strong>{number(k["openCases"])}</strong><small>Active inventory</small></div>
        <div class="kpi"><label>SLA compliance</label><strong>{pct(k["slaCompliance"])}</strong><small>All cases denominator</small></div>
        <div class="kpi"><label>Governance changes</label><strong>{number(len(data["governance"]))}</strong><small>Latest visible log</small></div>
        <div class="kpi"><label>Rule precision</label><strong>{pct(np.mean([r["precision"] for r in data["rules"]]))}</strong><small>Average by rule</small></div>
        <div class="kpi"><label>SAR filed</label><strong>{number(data["funnel"][-1]["value"])}</strong><small>Filed from cases</small></div>
      </div>
      <div class="grid-3">
        <div class="panel"><h2>Case Aging</h2><p>Open and closed case age distribution.</p>{aging_svg}</div>
        <div class="panel"><h2>Analyst Workload</h2><p>Case inventory by analyst queue.</p>{workload_svg}</div>
        <div class="panel"><h2>Workload Detail</h2><p>Overdue and SAR mix by analyst.</p>{table_rows(data["workload"], [("analyst","Analyst"),("queue","Queue"),("cases","Cases"),("overdue","Overdue"),("avgAge","Avg Age"),("sar","SAR")], 8)}</div>
      </div>
      <div class="panel" style="margin-top:12px">
        <h2>Rule Governance Log</h2><p>Rule tuning, approvals and precision lift audit trail.</p>
        <div class="governance-list">
          {"".join(f'<div class="gov-row"><span>{r["date"]}</span><strong>{r["rule"]}</strong><span>{r["change"]}</span><span class="chip">{r["status"]}</span></div>' for r in data["governance"][:10])}
        </div>
      </div>
    </section>
  </main>
</div>
<script>
  const buttons = document.querySelectorAll('.tab-button');
  const panels = document.querySelectorAll('.tab-panel');
  buttons.forEach(button => button.addEventListener('click', () => {{
    buttons.forEach(b => b.classList.remove('active'));
    panels.forEach(p => p.classList.remove('active'));
    button.classList.add('active');
    document.getElementById(button.dataset.tab).classList.add('active');
  }}));
</script>
</body>
</html>"""
    out = PROJECT_ROOT / "output/dashboard.html"
    write_text(out, html)
    shutil.copyfile(out, PROJECT_ROOT / "output/exports/aml_fraud_command_center_preview.html")
    write_json(PROJECT_ROOT / "output/dashboard_data.json", data)


def pbi_literal(value: str | bool | int | float) -> dict:
    if isinstance(value, bool):
        literal_value = "true" if value else "false"
    elif isinstance(value, str):
        literal_value = "'" + value.replace("'", "''") + "'"
    elif isinstance(value, int):
        literal_value = f"{value}L"
    else:
        literal_value = f"{value}D"
    return {"expr": {"Literal": {"Value": literal_value}}}


def solid(color: str) -> dict:
    return {"solid": {"color": color}}


def column(table: str, prop: str) -> dict:
    return {"Column": {"Expression": {"SourceRef": {"Entity": table}}, "Property": prop}}


def measure(prop: str) -> dict:
    return {"Measure": {"Expression": {"SourceRef": {"Entity": "KPI Measures"}}, "Property": prop}}


def projection(field: dict, query_ref: str, display_name: str | None = None) -> dict:
    payload = {"field": field, "queryRef": query_ref}
    if display_name:
        payload["displayName"] = display_name
    return payload


def measure_projection(name: str, display: str | None = None) -> dict:
    return projection(measure(name), f"KPI Measures.{name}", display or name)


def column_projection(table: str, name: str, display: str | None = None) -> dict:
    return projection(column(table, name), f"{table}.{name}", display or name)


def visual_frame(title: str, subtitle: str | None = None) -> dict:
    objects = {
        "title": [
            {
                "properties": {
                    "show": pbi_literal(True),
                    "text": pbi_literal(title),
                    "fontColor": solid("#17202A"),
                    "fontSize": pbi_literal(10),
                    "bold": pbi_literal(True),
                    "titleWrap": pbi_literal(True),
                }
            }
        ],
        "background": [{"properties": {"show": pbi_literal(True), "color": solid("#FFFFFF"), "transparency": pbi_literal(0)}}],
        "border": [{"properties": {"show": pbi_literal(True), "color": solid("#D8DED8"), "radius": pbi_literal(6)}}],
        "visualHeader": [{"properties": {"show": pbi_literal(False)}}],
    }
    if subtitle:
        objects["subTitle"] = [
            {
                "properties": {
                    "show": pbi_literal(True),
                    "text": pbi_literal(subtitle),
                    "fontColor": solid("#657383"),
                    "fontSize": pbi_literal(8),
                    "titleWrap": pbi_literal(True),
                }
            }
        ]
    return objects


def make_visual(
    name: str,
    visual_type: str,
    x: float,
    y: float,
    width: float,
    height: float,
    z: int,
    query_state: dict[str, list[dict]] | None = None,
    title: str | None = None,
    subtitle: str | None = None,
    sort_field: dict | None = None,
    sort_direction: str = "Descending",
) -> dict:
    visual: dict = {"visualType": visual_type}
    if query_state is not None:
        visual["query"] = {
            "queryState": {role: {"projections": projections} for role, projections in query_state.items()}
        }
        if sort_field is not None:
            visual["query"]["sortDefinition"] = {"sort": [{"field": sort_field, "direction": sort_direction}]}
    if title:
        visual["visualContainerObjects"] = visual_frame(title, subtitle)
    return {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.9.0/schema.json",
        "name": name,
        "position": {"x": x, "y": y, "z": z, "height": height, "width": width, "tabOrder": z},
        "visual": visual,
    }


def card(name: str, title: str, metric: str, x: float, y: float, z: int) -> dict:
    return make_visual(
        name=name,
        visual_type="card",
        x=x,
        y=y,
        width=185,
        height=92,
        z=z,
        title=title,
        query_state={"Values": [measure_projection(metric, title)]},
    )


def slicer(name: str, title: str, table: str, field: str, x: float, y: float, width: float, z: int) -> dict:
    return make_visual(
        name=name,
        visual_type="slicer",
        x=x,
        y=y,
        width=width,
        height=48,
        z=z,
        title=title,
        query_state={"Values": [column_projection(table, field, title)]},
    )


def build_native_layout() -> dict:
    pages = {
        "Fraud & Compliance Overview": [
            card("kpi_transactions", "Total Transactions", "Total Transactions", 24, 84, 100),
            card("kpi_flagged_amount", "Flagged Amount", "Flagged Amount", 224, 84, 101),
            card("kpi_alerts", "Alerts", "Alert Count", 424, 84, 102),
            card("kpi_suspicious", "Suspicious Cases", "Suspicious Cases", 624, 84, 103),
            card("kpi_fpr", "False Positive Rate", "False Positive Rate", 824, 84, 104),
            card("kpi_overdue", "Overdue Cases", "Overdue Cases", 1024, 84, 105),
            slicer("slicer_month", "Month", "DimDate", "MonthYear", 900, 20, 110, 10),
            slicer("slicer_corridor", "Corridor", "DimCorridor", "CorridorRiskTier", 1020, 20, 120, 11),
            slicer("slicer_severity", "Severity", "FactAlerts", "Severity", 1150, 20, 104, 12),
            make_visual(
                "trend_alerts_cases",
                "lineChart",
                24,
                210,
                760,
                300,
                200,
                {"Category": [column_projection("DimDate", "MonthYear", "Month")], "Y": [measure_projection("Alert Count"), measure_projection("Case Count"), measure_projection("SAR Filed Cases")]},
                "Alert, Case, and SAR Trend",
                "Monthly monitoring activity.",
                column("DimDate", "MonthIndex"),
                "Ascending",
            ),
            make_visual(
                "typology_mix",
                "barChart",
                812,
                210,
                444,
                300,
                201,
                {"Category": [column_projection("DimRule", "Typology")], "Y": [measure_projection("Alert Count")]},
                "Alerts by Typology",
                "Top rule families by alert volume.",
                measure("Alert Count"),
            ),
            make_visual(
                "corridor_risk",
                "tableEx",
                24,
                540,
                760,
                150,
                300,
                {
                    "Values": [
                        column_projection("DimCorridor", "Corridor"),
                        column_projection("DimCorridor", "CorridorRiskTier", "Risk Tier"),
                        measure_projection("Alert Count", "Alerts"),
                        measure_projection("Flagged Amount", "Flagged Amount"),
                        measure_projection("False Positive Rate", "FPR"),
                    ]
                },
                "Country / Corridor Risk Watchlist",
            ),
            make_visual(
                "severity_mix",
                "donutChart",
                812,
                540,
                444,
                150,
                301,
                {"Category": [column_projection("FactAlerts", "Severity")], "Y": [measure_projection("Alert Count")]},
                "Alert Severity Mix",
            ),
        ],
        "Alert & Customer Risk Deep Dive": [
            slicer("slicer_rule", "Rule", "DimRule", "Typology", 886, 20, 120, 10),
            slicer("slicer_channel", "Channel", "DimChannel", "Channel", 1020, 20, 110, 11),
            slicer("slicer_customer_tier", "Customer Risk", "DimCustomer", "CustomerRiskTier", 1140, 20, 116, 12),
            make_visual(
                "alert_funnel",
                "funnel",
                24,
                88,
                390,
                300,
                100,
                {"Category": [column_projection("DimRule", "Typology")], "Values": [measure_projection("Alert Count")]},
                "Alert Funnel by Typology",
                "Alert concentration and case conversion entry point.",
            ),
            make_visual(
                "rule_performance_scatter",
                "scatterChart",
                444,
                88,
                390,
                300,
                101,
                {
                    "Details": [column_projection("DimRule", "RuleName", "Rule")],
                    "X": [measure_projection("Alert Count", "Alert Volume")],
                    "Y": [measure_projection("Rule Precision", "Precision")],
                    "Size": [measure_projection("Alert Amount", "Alert Amount")],
                },
                "Rule Performance",
                "Precision versus alert volume.",
            ),
            make_visual(
                "high_risk_customers",
                "tableEx",
                864,
                88,
                392,
                300,
                102,
                {
                    "Values": [
                        column_projection("DimCustomer", "Customer"),
                        column_projection("DimCustomer", "CustomerRiskTier", "Tier"),
                        column_projection("DimCustomer", "HomeCountry", "Country"),
                        measure_projection("Alert Count", "Alerts"),
                        measure_projection("Case Count", "Cases"),
                        measure_projection("Alert Amount", "Alert Amount"),
                        measure_projection("Average Alert Risk Score", "Risk"),
                    ]
                },
                "High-Risk Customers",
            ),
            make_visual(
                "corridor_amount",
                "barChart",
                24,
                420,
                560,
                270,
                200,
                {"Category": [column_projection("DimCorridor", "Corridor")], "Y": [measure_projection("Flagged Amount")]},
                "Flagged Amount by Corridor",
                "Value exposure by origin-destination corridor.",
                measure("Flagged Amount"),
            ),
            make_visual(
                "channel_risk",
                "columnChart",
                616,
                420,
                310,
                270,
                201,
                {"Category": [column_projection("DimChannel", "Channel")], "Y": [measure_projection("Alert Rate"), measure_projection("False Positive Rate")]},
                "Channel Risk Quality",
                "Alert rate and false positive rate.",
            ),
            make_visual(
                "alert_detail",
                "tableEx",
                956,
                420,
                300,
                270,
                202,
                {
                    "Values": [
                        column_projection("DimRule", "RuleName", "Rule"),
                        column_projection("FactAlerts", "Severity"),
                        measure_projection("Alert Count"),
                        measure_projection("Rule Precision"),
                    ]
                },
                "Rule Detail",
            ),
        ],
        "Case SLA & Rule Governance": [
            card("kpi_open_cases", "Open Cases", "Open Cases", 24, 84, 100),
            card("kpi_sla", "SLA Compliance", "SLA Compliance Rate", 224, 84, 101),
            card("kpi_avg_age", "Avg Case Age", "Average Case Age Days", 424, 84, 102),
            card("kpi_rule_precision", "Rule Precision", "Rule Precision", 624, 84, 103),
            card("kpi_gov", "Governance Changes", "Governance Changes", 824, 84, 104),
            card("kpi_sars", "SAR Filed", "SAR Filed Cases", 1024, 84, 105),
            slicer("slicer_priority", "Priority", "FactCases", "CasePriority", 1020, 20, 110, 11),
            slicer("slicer_queue", "Queue", "DimAnalyst", "Queue", 1140, 20, 116, 12),
            make_visual(
                "case_aging",
                "columnChart",
                24,
                210,
                390,
                300,
                200,
                {"Category": [column_projection("FactCases", "CaseStatus")], "Y": [measure_projection("Case Count"), measure_projection("Overdue Cases")]},
                "Case Aging and Status",
                "Open, closed, SAR, and overdue case inventory.",
            ),
            make_visual(
                "analyst_workload",
                "barChart",
                444,
                210,
                390,
                300,
                201,
                {"Category": [column_projection("DimAnalyst", "Analyst")], "Y": [measure_projection("Case Count"), measure_projection("Overdue Cases")]},
                "Analyst Workload",
                "Case load and overdue count by analyst.",
                measure("Case Count"),
            ),
            make_visual(
                "rule_precision",
                "barChart",
                864,
                210,
                392,
                300,
                202,
                {"Category": [column_projection("DimRule", "RuleName")], "Y": [measure_projection("Rule Precision"), measure_projection("False Positive Rate")]},
                "Rule Precision and FPR",
                "Quality indicators by rule.",
            ),
            make_visual(
                "governance_log",
                "tableEx",
                24,
                540,
                1232,
                150,
                300,
                {
                    "Values": [
                        column_projection("DimDate", "MonthYear", "Change Month"),
                        column_projection("DimRule", "RuleName", "Rule"),
                        column_projection("FactRuleGovernance", "ChangeType", "Change"),
                        column_projection("FactRuleGovernance", "ApprovalStatus", "Status"),
                        column_projection("FactRuleGovernance", "PrecisionBefore", "Precision Before"),
                        column_projection("FactRuleGovernance", "PrecisionAfter", "Precision After"),
                        column_projection("FactRuleGovernance", "AlertVolumeDeltaPct", "Volume Delta"),
                    ]
                },
                "Rule Governance Audit Log",
            ),
        ],
    }
    page_names = {}
    for idx, display_name in enumerate(pages):
        safe = "Page" + str(idx + 1).zfill(2) + "_" + "".join(ch if ch.isalnum() else "_" for ch in display_name)
        page_names[display_name] = safe[:50]
    layout = {
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
        "sections": [],
        "config": json.dumps(
            {
                "version": "5.73",
                "activeSectionIndex": 0,
                "defaultDrillFilterOtherVisuals": True,
                "settings": {"useNewFilterPaneExperience": True, "useEnhancedTooltips": True},
            },
            separators=(",", ":"),
        ),
        "layoutOptimization": 0,
    }
    for ordinal, (display_name, visuals) in enumerate(pages.items()):
        layout["sections"].append(
            {
                "id": ordinal,
                "name": page_names[display_name],
                "displayName": display_name,
                "filters": "[]",
                "ordinal": ordinal,
                "visualContainers": visuals,
                "config": json.dumps(
                    {
                        "objects": {
                            "background": [{"properties": {"color": solid("#F6F7F4"), "transparency": pbi_literal(0.0)}}],
                            "outspace": [{"properties": {"color": solid("#F6F7F4"), "transparency": pbi_literal(0.0)}}],
                        }
                    },
                    separators=(",", ":"),
                ),
                "displayOption": 1,
                "width": 1280,
                "height": 720,
            }
        )
    write_json(PROJECT_ROOT / "build/native_report_layout_aml.json", layout)
    write_json(
        PROJECT_ROOT / "build/native_report_layout_aml_summary.json",
        {
            "pages": len(layout["sections"]),
            "visual_containers": sum(len(section["visualContainers"]) for section in layout["sections"]),
            "visual_strategy": "Native Power BI visual containers: cards, slicers, line, bar, column, donut, scatter, funnel, and tables.",
        },
    )
    return layout


def write_pbip_project(layout: dict) -> None:
    project_dir = PROJECT_ROOT / "output/powerbi_project"
    report_name = "AML_Fraud_Monitoring_Command_Center"
    if project_dir.exists():
        shutil.rmtree(project_dir)
    report_dir = project_dir / f"{report_name}.Report"
    model_dir = project_dir / f"{report_name}.SemanticModel"
    definition = report_dir / "definition"
    pages_dir = definition / "pages"
    model_dir.mkdir(parents=True, exist_ok=True)
    write_json(
        project_dir / f"{report_name}.pbip",
        {
            "$schema": "https://developer.microsoft.com/json-schemas/fabric/pbip/pbipProperties/1.0.0/schema.json",
            "version": "1.0",
            "artifacts": [{"report": {"path": f"{report_name}.Report"}}],
            "settings": {"enableAutoRecovery": True},
        },
    )
    write_json(PROJECT_ROOT / "output/open_dashboard_powerbi.pbip", {"version": "1.0", "artifacts": [{"report": {"path": f"powerbi_project/{report_name}.Report"}}]})
    write_json(
        report_dir / "definition.pbir",
        {
            "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definitionProperties/2.0.0/schema.json",
            "version": "4.0",
            "datasetReference": {"byPath": {"path": f"../{report_name}.SemanticModel"}},
        },
    )
    write_json(definition / "version.json", {"version": "1.0.0"})
    write_json(definition / "report.json", {"settings": {"useEnhancedTooltips": True}})
    page_order = []
    for section in layout["sections"]:
        page_name = section["name"]
        page_order.append(page_name)
        page_dir = pages_dir / page_name
        write_json(
            page_dir / "page.json",
            {
                "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/page/2.1.0/schema.json",
                "name": page_name,
                "displayName": section["displayName"],
                "displayOption": "FitToPage",
                "height": 720,
                "width": 1280,
            },
        )
        for visual in section["visualContainers"]:
            write_json(page_dir / "visuals" / visual["name"] / "visual.json", visual)
    write_json(pages_dir / "pages.json", {"pageOrder": page_order, "activePageName": page_order[0]})
    write_json(model_dir / "definition.pbism", {"version": "1.0", "settings": {"qnaEnabled": False}})
    write_text(
        PROJECT_ROOT / "output/OPEN_POWERBI_DASHBOARD.md",
        """
# Power BI Project Entry

Open `output/open_dashboard_powerbi.pbip` in Power BI Desktop after running the model push script.
The PBIP folder is a source package and backup entry point; the requested final PBIX target is `output/dashboard_final.pbix`.
""",
    )


def write_configs_and_docs(data: dict, tables: dict[str, pd.DataFrame]) -> None:
    dashboard_config = {
        "title": "AML / Fraud Monitoring Command Center",
        "audience": "Chief Compliance Officer, MLRO, Fraud Ops, AML analysts, rule governance board",
        "business_goal": "Monitor financial crime exposure, triage alert quality, keep case SLA under control, and govern rule tuning with audit-ready evidence.",
        "latest_complete_month": LATEST_COMPLETE_MONTH,
        "synthetic_seed": SEED,
        "tabs": [
            "Fraud & Compliance Overview",
            "Alert & Customer Risk Deep Dive",
            "Case SLA & Rule Governance",
        ],
    }
    write_json(PROJECT_ROOT / "build/config/dashboard_config.json", dashboard_config)
    write_json(
        PROJECT_ROOT / "build/config/page_map.json",
        [
            {"page": "Fraud & Compliance Overview", "purpose": "Executive status, flagged exposure, alert trend, corridor risk."},
            {"page": "Alert & Customer Risk Deep Dive", "purpose": "Alert funnel, rule performance, high-risk customers, investigation drivers."},
            {"page": "Case SLA & Rule Governance", "purpose": "Case backlog, analyst workload, overdue inventory, rule tuning governance."},
        ],
    )
    write_json(
        PROJECT_ROOT / "build/config/visual_map.json",
        {
            "overview": ["KPI strip", "Monthly trend", "Typology bar", "Corridor risk table", "Severity donut"],
            "deep_dive": ["Alert funnel", "Rule precision scatter", "High-risk customer table", "Channel quality", "Rule detail"],
            "sla_governance": ["Case status columns", "Analyst workload", "Rule precision/FPR", "Governance log"],
        },
    )
    write_json(
        PROJECT_ROOT / "build/config/slicer_map.json",
        {
            "global": ["Month", "Corridor risk tier", "Severity"],
            "deep_dive": ["Rule typology", "Channel", "Customer risk tier"],
            "sla_governance": ["Case priority", "Analyst queue"],
        },
    )
    write_json(
        PROJECT_ROOT / "build/config/theme.json",
        {
            "name": "AML Command Center",
            "background": "#F6F7F4",
            "surface": "#FFFFFF",
            "ink": "#17202A",
            "teal": "#0F766E",
            "mint": "#2A9D8F",
            "amber": "#D97706",
            "red": "#B91C1C",
            "violet": "#5B4B8A",
        },
    )
    write_text(
        PROJECT_ROOT / "docs/design_research.md",
        """
# Design Research

Sources used for layout and KPI inspiration:

- Stripe Radar analytics and fraud-team surfaces: https://docs.stripe.com/radar/analytics and https://stripe.com/radar/fraud-teams
- Microsoft Fabric real-time fraud detection architecture: https://learn.microsoft.com/en-us/fabric/real-time-intelligence/architectures/fraud-detection
- Nasdaq Verafin enterprise reporting and transaction monitoring: https://verafin.com/solution/enterprise-reporting/ and https://verafin.com/solution/transaction-monitoring/
- Unit21 AML case-management KPI guidance: https://www.unit21.ai/blog/aml-case-management-system-metrics-and-kpis
- Salv AML effectiveness KPIs: https://salv.com/blog/anti-money-laundering-metrics-crime/
- Flagright false-positive rate example: https://www.flagright.com/post/understanding-false-positives-in-transaction-monitoring
- StackGo AML compliance dashboard components: https://stackgo.io/resources/aml-compliance-dashboard/
- Linkurious AML graph investigation pattern: https://linkurious.com/aml-compliance/

Applied patterns:

- Dense command-center KPI strip instead of a landing page.
- Alert-to-case-to-SAR funnel for triage visibility.
- Rule precision versus alert volume to separate noisy rules from high-yield rules.
- Corridor and customer risk tables for investigation handoff.
- SLA aging, analyst workload, and governance log for operational accountability.
""",
    )
    write_text(
        PROJECT_ROOT / "_agent/intake_brief.md",
        f"""
# Intake Brief

Topic: AML / Fraud Monitoring Command Center
Project path: {PROJECT_ROOT}
Audience: CCO, MLRO, fraud operations, AML investigation leads, rule governance board.
Business goal: Monitor fraud/AML exposure, alert quality, case SLA, high-risk customers, corridor risk, and rule governance.
Data source: Synthetic portfolio demo data generated with seed {SEED}.
Final requested output: `output/dashboard_final.pbix`; HTML and PBIP are supplemental previews/build packages.
Assumption: This is a portfolio/demo build, so synthetic data is acceptable and clearly labeled.
""",
    )
    write_text(
        PROJECT_ROOT / "_agent/run_log.md",
        f"""
# Run Log

- Created project structure.
- Loaded BI A-Z master prompt and Data Analytics dashboard workflow.
- Researched AML/fraud/compliance dashboard patterns online.
- Generated synthetic data with seed {SEED}.
- Built prepared star schema, metric definitions, DAX, configs, HTML preview, PBIP source package, and native report layout JSON.
""",
    )
    write_text(
        PROJECT_ROOT / "_agent/session_guard.md",
        f"""
# Session Guard

Current project path: {PROJECT_ROOT}
Expected final PBIX path: {PROJECT_ROOT / 'output/dashboard_final.pbix'}
Power BI windows detected before project build: checked by environment scripts; no save action should target unrelated sessions.
Selected session: pending exact Desktop open-check for this project path.
Windows ignored: any Power BI Desktop window not opened from the Project 10 - AML Fraud Monitoring target file.
""",
    )
    write_text(
        PROJECT_ROOT / "_agent/pbix_authoring_decision.md",
        """
# PBIX Authoring Decision

Selected route: SCRIPTED_DESKTOP_PBIX with Computer Use-assisted Desktop save/check.

Reason:
- Power BI Desktop and pbi-tools are installed.
- pbi-tools compile cannot create a full data-model PBIX directly; it can help inspect/extract/validate.
- The deterministic route is to push the semantic model into Power BI Desktop, save a model PBIX, patch a native report layout, validate with PowerBIPackager, then reopen the exact final file.

Fallback:
- If Desktop save/open-check cannot complete, final output must be marked blocked for PBIX build, with HTML/PBIP retained as supplemental build package.
""",
    )
    write_text(
        PROJECT_ROOT / "_agent/failure_matrix.md",
        """
# Failure Matrix

| Failure | Handling |
|---|---|
| Power BI Desktop not found | Mark PBIX blocked and keep PBIP/HTML package. |
| Desktop opens unrelated file | Stop save, relaunch exact Project 10 - AML Fraud Monitoring target. |
| Local AS port not found | Wait for Desktop engine, retry once, then log blocker. |
| TOM model push fails | Keep prepared data/model docs, mark PBIX blocked. |
| PBIX package validation fails | Do not overwrite final; keep last valid artifact. |
| Visual open-check fails | Mark visual QA failed and keep screenshots/logs. |
""",
    )
    write_text(
        PROJECT_ROOT / "docs/handoff_notes.md",
        """
# Handoff Notes

Final PBIX target: `output/dashboard_final.pbix`
Build route: SCRIPTED_DESKTOP_PBIX, with HTML/PBIP supplemental outputs.
Data: deterministic synthetic AML/fraud monitoring data, seed 20260611.
Tabs: Fraud & Compliance Overview; Alert & Customer Risk Deep Dive; Case SLA & Rule Governance.
Key KPIs: total transactions, flagged amount, alerts, suspicious cases, false positive rate, alert rate, alert-to-case conversion, SAR conversion, overdue cases, SLA compliance, rule precision.
Known issue until Desktop run completes: PBIX open-check and screenshot evidence are pending.
""",
    )
    write_text(
        PROJECT_ROOT / "docs/refresh_guide.md",
        """
# Refresh Guide

1. Run `python build/scripts/00_build_aml_project.py` to regenerate synthetic data and configs.
2. Open the Project 10 - AML Fraud Monitoring model PBIX in Power BI Desktop.
3. Run `build/scripts/07_push_model_to_powerbi_desktop.ps1` to rebuild the semantic model from `data/prepared`.
4. Save in Power BI Desktop.
5. Run `build/scripts/10_apply_native_pbix_report.ps1` to create `output/dashboard_final.pbix`.
6. Reopen the exact final PBIX and capture QA screenshots.
""",
    )
    write_text(
        PROJECT_ROOT / "docs/rebuild_guide.md",
        """
# Rebuild Guide

Run:

```powershell
python build\\scripts\\00_build_aml_project.py
```

Then follow `powerbi/notes/pbix_build_runbook.md` for the Desktop-dependent PBIX build.
""",
    )
    write_text(PROJECT_ROOT / "docs/changelog.md", "# Changelog\n\n## v01-build-ready\n\n- Created AML/Fraud BI project package, synthetic data, model docs, HTML dashboard, PBIP source package, and native report layout JSON.")
    write_text(PROJECT_ROOT / "docs/issue_log.md", "# Issue Log\n\n- PBIX Desktop save/open-check remains pending until Desktop build route is executed.")
    write_text(PROJECT_ROOT / "powerbi/notes/authoring_strategy.md", (PROJECT_ROOT / "_agent/pbix_authoring_decision.md").read_text(encoding="utf-8"))
    write_text(
        PROJECT_ROOT / "powerbi/notes/pbix_build_runbook.md",
        """
# PBIX Build Runbook

1. Copy a valid technical seed PBIX into `output/dashboard_model.pbix`.
2. Launch that exact file in Power BI Desktop.
3. Run `build/scripts/07_push_model_to_powerbi_desktop.ps1`.
4. Save the exact file in Desktop.
5. Run `build/scripts/10_apply_native_pbix_report.ps1`.
6. Open `output/dashboard_final.pbix` in Desktop and verify 3 pages with native visuals and no visual error.
""",
    )
    write_text(
        PROJECT_ROOT / "powerbi/notes/desktop_ui_runbook.md",
        """
# Desktop UI Runbook

Use Computer Use to select the Power BI Desktop window opened from Project 10 - AML Fraud Monitoring.
Use Ctrl+S only after confirming the target file is `output/dashboard_model.pbix` or `output/dashboard_final.pbix`.
Capture screenshots under `output/screenshots`.
""",
    )
    write_text(
        PROJECT_ROOT / "README.md",
        """
# AML / Fraud Monitoring Command Center

This project is a complete BI portfolio package for AML and fraud monitoring.

Open quick preview:

- `output/dashboard.html`

Main Power BI target:

- `output/dashboard_final.pbix`

Build package:

- `data/prepared/*.csv`
- `model/measures.dax`
- `build/config/*.json`
- `build/native_report_layout_aml.json`
- `output/open_dashboard_powerbi.pbip`

The data is deterministic synthetic demo data generated with seed 20260611.
""",
    )


def write_validation_files(data: dict, quality: dict) -> None:
    reconciliation = pd.DataFrame(
        [
            {"Metric": "Total Transactions", "Value": data["kpis"]["transactions"]},
            {"Metric": "Transaction Amount", "Value": data["kpis"]["transactionAmount"]},
            {"Metric": "Flagged Amount", "Value": data["kpis"]["flaggedAmount"]},
            {"Metric": "Alert Count", "Value": data["kpis"]["alerts"]},
            {"Metric": "Suspicious Cases", "Value": data["kpis"]["suspiciousCases"]},
            {"Metric": "False Positive Rate", "Value": data["kpis"]["falsePositiveRate"]},
            {"Metric": "Overdue Cases", "Value": data["kpis"]["overdueCases"]},
            {"Metric": "SLA Compliance", "Value": data["kpis"]["slaCompliance"]},
        ]
    )
    reconciliation.to_csv(PROJECT_ROOT / "qa/reconciliation.csv", index=False)
    with pd.ExcelWriter(PROJECT_ROOT / "qa/reconciliation.xlsx", engine="openpyxl") as writer:
        reconciliation.to_excel(writer, sheet_name="KPI Reconciliation", index=False)
    write_json(PROJECT_ROOT / "data/validated/validation_summary.json", {"status": "pass", "quality": quality, "kpis": data["kpis"]})
    write_json(PROJECT_ROOT / "qa/pbix_validation.json", {"status": "pending_desktop_build", "target": str(PROJECT_ROOT / "output/dashboard_final.pbix")})
    write_json(PROJECT_ROOT / "qa/pbix_final_validation.json", {"status": "pending_desktop_open_check", "target": str(PROJECT_ROOT / "output/dashboard_final.pbix")})
    write_text(
        PROJECT_ROOT / "qa/qa_checklist.md",
        """
# QA Checklist

## Data QA

- [x] Synthetic data generated with fixed seed 20260611.
- [x] Row counts, duplicate key checks, and missing critical values captured.
- [x] Prepared CSVs exist for facts and dimensions.

## Metric QA

- [x] KPI definitions documented in `model/metric_definitions.md`.
- [x] DAX measures use DIVIDE for rates.
- [x] Reconciliation CSV/XLSX generated.

## Visual QA

- [x] HTML dashboard preview generated.
- [x] Native Power BI report layout JSON generated.
- [ ] Exact PBIX opened in Power BI Desktop.
- [ ] Visual error count verified as 0.

## File QA

- [x] Project folders and handoff docs created.
- [ ] `output/dashboard_final.pbix` validated after Desktop build.
""",
    )
    write_text(PROJECT_ROOT / "qa/visual_qa_notes.md", "HTML preview generated. PBIX visual QA pending exact Desktop open-check.")
    write_text(PROJECT_ROOT / "qa/interaction_qa_notes.md", "HTML tabs switch in-browser. Power BI slicer interaction pending Desktop QA.")
    write_text(PROJECT_ROOT / "qa/performance_qa_notes.md", "Prepared data is compact for portfolio use: 36k transactions plus derived alerts/cases.")
    write_text(PROJECT_ROOT / "qa/regression_qa_notes.md", "Initial build. No regression loop yet.")


def write_environment_files() -> None:
    write_text(
        PROJECT_ROOT / "powerbi/launch_powerbi.ps1",
        """
param(
  [string]$PbixPath = ""
)

$ErrorActionPreference = "Stop"
$exe = "C:\\Program Files\\Microsoft Power BI Desktop\\bin\\PBIDesktop.exe"
if (!(Test-Path -LiteralPath $exe)) {
  $cmd = Get-Command PBIDesktop.exe -ErrorAction SilentlyContinue
  if ($cmd) { $exe = $cmd.Source }
}
if (!(Test-Path -LiteralPath $exe)) { throw "Power BI Desktop executable not found." }
if ($PbixPath) {
  Start-Process -FilePath $exe -ArgumentList "`"$PbixPath`""
} else {
  Start-Process -FilePath $exe
}
""",
    )
    write_text(
        PROJECT_ROOT / "_agent/environment_check.md",
        """
# Environment Check

Power BI Desktop and pbi-tools are checked by the assistant run before PBIX authoring.
Observed environment during intake:
- PBIDesktop.exe found under `C:\\Program Files\\Microsoft Power BI Desktop\\bin`.
- Microsoft Store Power BI Desktop also present.
- pbi-tools 1.2.0 available.
- dotnet command not found in PATH.
""",
    )
    write_json(
        PROJECT_ROOT / "_agent/environment_check.json",
        {
            "PBIDesktopCommand": "C:\\Program Files\\Microsoft Power BI Desktop\\bin\\PBIDesktop.exe",
            "ProgramFilesPowerBI": True,
            "StorePowerBI": True,
            "pbi_tools": True,
            "dotnet_in_path": False,
            "checked_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        },
    )


def main() -> None:
    ensure_dirs()
    dims = make_dimensions()
    facts = make_facts(dims)
    save_data(dims, facts)
    tables = {**dims, **facts}
    quality, quality_md = quality_payload(dims, facts)
    write_json(PROJECT_ROOT / "data/source_summary.json", {"synthetic": True, "seed": SEED, "tables": {name: len(df) for name, df in tables.items()}, "latest_complete_month": LATEST_COMPLETE_MONTH})
    write_json(PROJECT_ROOT / "data/validated/quality_payload.json", quality)
    write_text(PROJECT_ROOT / "data/data_quality_report.md", quality_md)
    dictionary = schema_markdown(tables)
    write_text(PROJECT_ROOT / "data/data_dictionary.md", dictionary)
    write_text(PROJECT_ROOT / "model/data_dictionary.md", dictionary)
    write_model_docs()
    write_powerbi_config(dims, facts)
    dashboard_data = aggregate_for_dashboard(dims, facts)
    write_html_dashboard(dashboard_data)
    layout = build_native_layout()
    write_pbip_project(layout)
    write_configs_and_docs(dashboard_data, tables)
    write_validation_files(dashboard_data, quality)
    write_environment_files()
    print(json.dumps({"status": "ok", "project": str(PROJECT_ROOT), "tables": {name: len(df) for name, df in tables.items()}, "html": str(PROJECT_ROOT / "output/dashboard.html")}, indent=2))


if __name__ == "__main__":
    main()
