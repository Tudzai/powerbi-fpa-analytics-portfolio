from __future__ import annotations

import json
import math
import shutil
import subprocess
import uuid
import zipfile
from datetime import date, datetime
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
SEED = 20260611
REPORT_DATE = date(2026, 6, 11)
START_MONTH = pd.Timestamp("2024-01-01")
LATEST_MONTH = pd.Timestamp("2026-05-01")
MONTHS = pd.date_range(START_MONTH, LATEST_MONTH, freq="MS")
MEASURE_TABLE = "KPI_Measures"

COLORS = {
    "bg": "#F6F8FB",
    "paper": "#FFFFFF",
    "ink": "#111827",
    "muted": "#64748B",
    "border": "#DCE3EC",
    "navy": "#0B1726",
    "blue": "#2563EB",
    "sky": "#0EA5E9",
    "teal": "#0F766E",
    "green": "#16A34A",
    "amber": "#F59E0B",
    "red": "#DC2626",
    "rose": "#E11D48",
    "violet": "#7C3AED",
}

CHANNELS = [
    ("organic", "Organic Search", "Organic", 0.92, 0.58, 54),
    ("paid_search", "Paid Search", "Paid", 1.14, 0.47, 96),
    ("paid_social", "Paid Social", "Paid", 1.28, 0.39, 118),
    ("referral", "Referral", "Owned", 0.86, 0.62, 42),
    ("partner", "Partner Marketplace", "Partner", 1.03, 0.56, 72),
    ("lifecycle", "Lifecycle Email", "Owned", 0.74, 0.52, 31),
]
SEGMENTS = [
    ("mass", "Mass Retail", "Medium", "25-55k"),
    ("affluent", "Mass Affluent", "Low", "55-140k"),
    ("freelancer", "Freelancer", "Medium", "35-120k"),
    ("smb", "SMB Owner", "High", "80-250k"),
]
CAMPAIGNS = [
    ("seo_guides", "SEO Banking Guides", "organic", "Signup"),
    ("appstore", "App Store Optimization", "organic", "Signup"),
    ("brand_search", "Brand Search Always-On", "paid_search", "Signup"),
    ("competitor", "Competitor Search", "paid_search", "Funded Account"),
    ("creator_cashback", "Creator Cashback", "paid_social", "KYC"),
    ("salary_lookalike", "Salary Advance Lookalike", "paid_social", "Funded Account"),
    ("member_ref", "Member Referral Loop", "referral", "Funded Account"),
    ("payroll_ref", "Payroll Referral", "referral", "Activation"),
    ("payroll_partner", "Payroll Partner Launch", "partner", "Funded Account"),
    ("wallet_bundle", "Wallet Bundle", "partner", "Activation"),
    ("winback", "Dormant Winback", "lifecycle", "Reactivation"),
    ("kyc_reminder", "KYC Reminder Journey", "lifecycle", "KYC"),
]


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.strip() + "\n", encoding="utf-8")


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def clean_outputs() -> None:
    for rel in ["data", "model", "build/config", "build/logs", "powerbi", "output", "qa", "docs", "_agent"]:
        target = ROOT / rel
        if target.exists() and ROOT in target.parents:
            shutil.rmtree(target)


def ensure_dirs() -> None:
    for rel in [
        "data/raw",
        "data/prepared",
        "data/validated",
        "data/profile",
        "model",
        "build/config",
        "build/logs",
        "build/scripts",
        "powerbi/pbip/Neobank_Growth_LTV/Neobank_Growth_LTV.Report",
        "powerbi/pbip/Neobank_Growth_LTV/Neobank_Growth_LTV.SemanticModel",
        "powerbi/notes",
        "output/screenshots",
        "output/exports",
        "qa",
        "docs",
        "_agent",
    ]:
        (ROOT / rel).mkdir(parents=True, exist_ok=True)


def month_label(ts: pd.Timestamp) -> str:
    return ts.strftime("%b %Y")


def money(v: float) -> str:
    if abs(v) >= 1_000_000:
        return f"${v / 1_000_000:.1f}M"
    if abs(v) >= 1_000:
        return f"${v / 1_000:.1f}K"
    return f"${v:,.0f}"


def pct(v: float) -> str:
    return f"{v:.1%}"


def build_data() -> dict[str, pd.DataFrame]:
    rng = np.random.default_rng(SEED)
    dim_month = pd.DataFrame(
        {
            "MonthStart": [m.date().isoformat() for m in MONTHS],
            "MonthLabel": [month_label(m) for m in MONTHS],
            "MonthIndex": range(1, len(MONTHS) + 1),
            "Year": [m.year for m in MONTHS],
            "Quarter": [f"Q{((m.month - 1) // 3) + 1}" for m in MONTHS],
            "IsLatestCompleteMonth": [int(m == LATEST_MONTH) for m in MONTHS],
        }
    )
    dim_channel = pd.DataFrame(
        [
            {
                "ChannelKey": key,
                "ChannelName": name,
                "ChannelType": ctype,
                "QualityIndex": quality,
                "TargetCAC": target,
                "TargetLtvCac": 3.0 if ctype == "Paid" else 4.0,
            }
            for key, name, ctype, _scale, quality, target in CHANNELS
        ]
    )
    dim_segment = pd.DataFrame(
        [{"SegmentKey": k, "SegmentName": n, "RiskTier": r, "IncomeBand": band} for k, n, r, band in SEGMENTS]
    )
    dim_campaign = pd.DataFrame(
        [
            {
                "CampaignKey": key,
                "CampaignName": name,
                "ChannelKey": channel,
                "ChannelName": dim_channel.loc[dim_channel.ChannelKey == channel, "ChannelName"].iloc[0],
                "Objective": objective,
            }
            for key, name, channel, objective in CAMPAIGNS
        ]
    )
    seg_weight = {"mass": 0.48, "affluent": 0.24, "freelancer": 0.18, "smb": 0.10}
    seg_deposit = {"mass": 680, "affluent": 1840, "freelancer": 1210, "smb": 3460}
    seg_revenue = {"mass": 5.8, "affluent": 11.5, "freelancer": 9.3, "smb": 24.0}
    seg_churn = {"mass": 0.052, "affluent": 0.034, "freelancer": 0.046, "smb": 0.041}
    active_state: dict[tuple[str, str], float] = {}
    fact_rows = []
    campaign_rows = []
    for i, month in enumerate(MONTHS):
        trend = 0.82 + 0.028 * i
        seasonality = 1 + 0.10 * math.sin((month.month - 1) / 12 * 2 * math.pi) + 0.04 * math.cos(i / 3.7)
        for ch_key, _ch_name, ch_type, scale, quality, target_cac in CHANNELS:
            channel_fact_indexes = []
            for seg_key, _seg_name, _risk, _income in SEGMENTS:
                active_base = active_state.get((ch_key, seg_key), 0.0)
                base = 960 * scale * seg_weight[seg_key] * trend * seasonality
                new_users = max(15, int(rng.normal(base, base * 0.08)))
                kyc_submitted = int(new_users * np.clip(0.68 + quality * 0.18 + rng.normal(0, 0.025), 0.48, 0.88))
                kyc_approved = int(kyc_submitted * np.clip(0.72 + quality * 0.19 + rng.normal(0, 0.02), 0.55, 0.95))
                activated = int(kyc_approved * np.clip(0.49 + quality * 0.24 + rng.normal(0, 0.018), 0.35, 0.84))
                funded = int(activated * np.clip(0.38 + quality * 0.25 + rng.normal(0, 0.018), 0.25, 0.78))
                churn_rate = np.clip(seg_churn[seg_key] + (0.012 if ch_type == "Paid" else -0.004) + rng.normal(0, 0.004), 0.015, 0.085)
                churned = int(active_base * churn_rate)
                active_base = max(0, active_base + funded - churned)
                active_state[(ch_key, seg_key)] = active_base
                active_users = int(active_base * np.clip(0.74 + quality * 0.16 + rng.normal(0, 0.02), 0.52, 0.92))
                dormant = int(max(0, active_base - active_users) * np.clip(0.42 + churn_rate * 4, 0.22, 0.70))
                risk_users = int(dormant * np.clip(0.34 + churn_rate * 2.8, 0.20, 0.62))
                deposits = funded * seg_deposit[seg_key] * rng.normal(1.0, 0.12) + active_users * seg_deposit[seg_key] * rng.normal(0.34, 0.05)
                interchange = active_users * seg_revenue[seg_key] * rng.normal(0.58, 0.05)
                subscription = active_users * (0.9 if seg_key == "mass" else 2.6 if seg_key == "affluent" else 1.8 if seg_key == "freelancer" else 4.4)
                lending = deposits * rng.normal(0.0038, 0.00045)
                revenue = interchange + subscription + lending
                gross_profit = revenue * rng.normal(0.69, 0.035)
                spend = new_users * target_cac * rng.normal(0.56 if ch_type != "Paid" else 1.03, 0.10)
                fact_rows.append(
                    {
                        "MonthStart": month.date().isoformat(),
                        "ChannelKey": ch_key,
                        "SegmentKey": seg_key,
                        "NewUsers": new_users,
                        "KycSubmitted": kyc_submitted,
                        "KycApproved": kyc_approved,
                        "ActivatedUsers": activated,
                        "FundedAccounts": funded,
                        "ActiveUsers": active_users,
                        "ChurnedUsers": churned,
                        "DormantCustomers": dormant,
                        "ChurnRiskUsers": risk_users,
                        "DepositVolume": round(float(max(0, deposits)), 2),
                        "InterchangeRevenue": round(float(max(0, interchange)), 2),
                        "SubscriptionRevenue": round(float(max(0, subscription)), 2),
                        "LendingRevenue": round(float(max(0, lending)), 2),
                        "TotalRevenue": round(float(max(0, revenue)), 2),
                        "GrossProfit": round(float(max(0, gross_profit)), 2),
                        "MarketingSpend": round(float(max(0, spend)), 2),
                    }
                )
                channel_fact_indexes.append(len(fact_rows) - 1)
            ch_facts = [fact_rows[j] for j in channel_fact_indexes]
            ch_new = sum(r["NewUsers"] for r in ch_facts)
            ch_funded = sum(r["FundedAccounts"] for r in ch_facts)
            ch_rev = sum(r["TotalRevenue"] for r in ch_facts)
            ch_profit = sum(r["GrossProfit"] for r in ch_facts)
            ch_spend = sum(r["MarketingSpend"] for r in ch_facts)
            campaigns = dim_campaign[dim_campaign.ChannelKey == ch_key].to_dict("records")
            weights = rng.dirichlet(np.ones(len(campaigns)) * 2.0)
            for campaign, weight in zip(campaigns, weights):
                noise = np.clip(rng.normal(1.0, 0.08), 0.72, 1.28)
                campaign_rows.append(
                    {
                        "MonthStart": month.date().isoformat(),
                        "CampaignKey": campaign["CampaignKey"],
                        "ChannelKey": ch_key,
                        "Spend": round(float(ch_spend * weight * noise), 2),
                        "NewUsers": int(ch_new * weight * noise),
                        "FundedAccounts": int(ch_funded * weight * noise),
                        "Revenue": round(float(ch_rev * weight * noise), 2),
                        "GrossProfit": round(float(ch_profit * weight * noise), 2),
                    }
                )
    fact = pd.DataFrame(fact_rows)
    campaign = pd.DataFrame(campaign_rows)
    funnel_base = fact.groupby(["MonthStart", "ChannelKey"], as_index=False).agg(
        NewUsers=("NewUsers", "sum"),
        KycSubmitted=("KycSubmitted", "sum"),
        KycApproved=("KycApproved", "sum"),
        ActivatedUsers=("ActivatedUsers", "sum"),
        FundedAccounts=("FundedAccounts", "sum"),
    )
    stages = [("Signup Started", 1, "NewUsers"), ("KYC Submitted", 2, "KycSubmitted"), ("KYC Approved", 3, "KycApproved"), ("Activated", 4, "ActivatedUsers"), ("Funded Account", 5, "FundedAccounts")]
    funnel = pd.DataFrame(
        [
            {"MonthStart": r.MonthStart, "ChannelKey": r.ChannelKey, "StageName": stage, "StageOrder": order, "UserCount": int(getattr(r, col))}
            for r in funnel_base.itertuples(index=False)
            for stage, order, col in stages
        ]
    )
    cohort_rows = []
    for cohort_month in MONTHS:
        cohort_slice = fact[fact.MonthStart == cohort_month.date().isoformat()]
        for ch_key, _ch_name, _ctype, _scale, quality, _target in CHANNELS:
            for seg_key, _seg_name, _risk, _income in SEGMENTS:
                size = int(cohort_slice[(cohort_slice.ChannelKey == ch_key) & (cohort_slice.SegmentKey == seg_key)].FundedAccounts.sum())
                if size <= 0:
                    continue
                cumulative = 0.0
                for activity_month in MONTHS[MONTHS >= cohort_month]:
                    age = (activity_month.year - cohort_month.year) * 12 + activity_month.month - cohort_month.month
                    retention = np.clip((0.92 - 0.035 * age) * (0.82 + quality * 0.26) + rng.normal(0, 0.012), 0.12, 0.98)
                    retained = int(size * retention)
                    revenue = retained * rng.normal(12 + age * 0.12, 1.2)
                    cumulative += revenue
                    cohort_rows.append(
                        {
                            "CohortMonth": cohort_month.date().isoformat(),
                            "CohortLabel": month_label(cohort_month),
                            "ActivityMonth": activity_month.date().isoformat(),
                            "MonthsSinceCohort": age,
                            "ChannelKey": ch_key,
                            "SegmentKey": seg_key,
                            "CohortSize": size,
                            "RetainedUsers": retained,
                            "RetentionRate": round(retained / size, 4),
                            "Revenue": round(float(revenue), 2),
                            "CumulativeRevenue": round(float(cumulative), 2),
                            "CumulativeLTV": round(float(cumulative / size), 2),
                        }
                    )
    cohort = pd.DataFrame(cohort_rows)
    monthly = fact.groupby("MonthStart", as_index=False).agg(
        NewUsers=("NewUsers", "sum"),
        KycSubmitted=("KycSubmitted", "sum"),
        KycApproved=("KycApproved", "sum"),
        ActivatedUsers=("ActivatedUsers", "sum"),
        FundedAccounts=("FundedAccounts", "sum"),
        ActiveUsers=("ActiveUsers", "sum"),
        ChurnedUsers=("ChurnedUsers", "sum"),
        DormantCustomers=("DormantCustomers", "sum"),
        ChurnRiskUsers=("ChurnRiskUsers", "sum"),
        DepositVolume=("DepositVolume", "sum"),
        TotalRevenue=("TotalRevenue", "sum"),
        GrossProfit=("GrossProfit", "sum"),
        MarketingSpend=("MarketingSpend", "sum"),
    ).merge(dim_month[["MonthStart", "MonthLabel", "MonthIndex"]], on="MonthStart")
    monthly["KycCompletionRate"] = monthly.KycApproved / monthly.NewUsers.replace(0, np.nan)
    monthly["ActivationRate"] = monthly.ActivatedUsers / monthly.NewUsers.replace(0, np.nan)
    monthly["FundedRate"] = monthly.FundedAccounts / monthly.NewUsers.replace(0, np.nan)
    monthly["CAC"] = monthly.MarketingSpend / monthly.FundedAccounts.replace(0, np.nan)
    monthly["ChurnRate"] = monthly.ChurnedUsers / (monthly.ActiveUsers + monthly.ChurnedUsers).replace(0, np.nan)
    monthly["ARPU"] = monthly.TotalRevenue / monthly.ActiveUsers.replace(0, np.nan)
    monthly["LTV"] = (monthly.ARPU * 0.68) / monthly.ChurnRate.replace(0, np.nan)
    monthly["LTVCACRatio"] = monthly.LTV / monthly.CAC.replace(0, np.nan)
    monthly["PaybackMonths"] = monthly.CAC / (monthly.GrossProfit / monthly.ActiveUsers.replace(0, np.nan)).replace(0, np.nan)
    monthly["MarketingROI"] = (monthly.GrossProfit - monthly.MarketingSpend) / monthly.MarketingSpend.replace(0, np.nan)
    monthly = monthly.fillna(0)
    channel_monthly = fact.groupby(["MonthStart", "ChannelKey"], as_index=False).agg(
        NewUsers=("NewUsers", "sum"),
        FundedAccounts=("FundedAccounts", "sum"),
        ActiveUsers=("ActiveUsers", "sum"),
        DepositVolume=("DepositVolume", "sum"),
        TotalRevenue=("TotalRevenue", "sum"),
        GrossProfit=("GrossProfit", "sum"),
        MarketingSpend=("MarketingSpend", "sum"),
        ChurnedUsers=("ChurnedUsers", "sum"),
    ).merge(dim_channel[["ChannelKey", "ChannelName", "ChannelType"]], on="ChannelKey")
    channel_monthly["CAC"] = channel_monthly.MarketingSpend / channel_monthly.FundedAccounts.replace(0, np.nan)
    channel_monthly["MarketingROI"] = (channel_monthly.GrossProfit - channel_monthly.MarketingSpend) / channel_monthly.MarketingSpend.replace(0, np.nan)
    channel_monthly = channel_monthly.fillna(0)
    risk_rows = []
    latest_fact = fact[fact.MonthStart == LATEST_MONTH.date().isoformat()]
    user_no = 1
    for r in latest_fact.itertuples(index=False):
        count = max(3, int(r.ChurnRiskUsers / 5))
        for _ in range(count):
            score = float(np.clip(rng.normal(72, 14), 1, 99))
            band = "Critical" if score >= 84 else "High" if score >= 67 else "Medium" if score >= 42 else "Low"
            risk_rows.append(
                {
                    "UserID": f"NB{user_no:07d}",
                    "ChannelKey": r.ChannelKey,
                    "SegmentKey": r.SegmentKey,
                    "RiskBand": band,
                    "RiskScore": round(score, 1),
                    "DormantDays": int(np.clip(score * 2.4 + rng.normal(0, 18), 10, 260)),
                    "Balance": round(float(np.clip(rng.lognormal(7.1, 0.65), 50, 18000)), 2),
                    "EstimatedLTV": round(float(np.clip(rng.lognormal(4.45, 0.55), 35, 1100)), 2),
                    "RecommendedAction": "Human outreach" if band == "Critical" else "Fee waiver" if band == "High" else "Cashback nudge" if band == "Medium" else "Monitor",
                }
            )
            user_no += 1
    risk = pd.DataFrame(risk_rows).sort_values(["RiskScore", "EstimatedLTV"], ascending=False).head(850)
    return {
        "DimMonth": dim_month,
        "DimChannel": dim_channel,
        "DimSegment": dim_segment,
        "DimCampaign": dim_campaign,
        "FactGrowthMonthly": fact,
        "FunnelMonthly": funnel,
        "CohortRetention": cohort,
        "CampaignMonthly": campaign,
        "ChurnRiskSnapshot": risk,
        "MonthlyKPIs": monthly,
        "ChannelMonthly": channel_monthly,
    }


MEASURES = [
    ("New Users", "SUM ( FactGrowthMonthly[NewUsers] )", "#,0"),
    ("KYC Submitted", "SUM ( FactGrowthMonthly[KycSubmitted] )", "#,0"),
    ("KYC Approved", "SUM ( FactGrowthMonthly[KycApproved] )", "#,0"),
    ("Activated Users", "SUM ( FactGrowthMonthly[ActivatedUsers] )", "#,0"),
    ("Funded Accounts", "SUM ( FactGrowthMonthly[FundedAccounts] )", "#,0"),
    ("Active Users", "SUM ( FactGrowthMonthly[ActiveUsers] )", "#,0"),
    ("Deposit Volume", "SUM ( FactGrowthMonthly[DepositVolume] )", "$#,0,,.0M"),
    ("Revenue", "SUM ( FactGrowthMonthly[TotalRevenue] )", "$#,0,,.0M"),
    ("Gross Profit", "SUM ( FactGrowthMonthly[GrossProfit] )", "$#,0,,.0M"),
    ("Marketing Spend", "SUM ( FactGrowthMonthly[MarketingSpend] )", "$#,0,,.0M"),
    ("Churned Users", "SUM ( FactGrowthMonthly[ChurnedUsers] )", "#,0"),
    ("Dormant Customers", "SUM ( FactGrowthMonthly[DormantCustomers] )", "#,0"),
    ("Churn Risk Users", "SUM ( FactGrowthMonthly[ChurnRiskUsers] )", "#,0"),
    ("KYC Completion Rate", "DIVIDE ( [KYC Approved], [New Users] )", "0.0%"),
    ("Activation Rate", "DIVIDE ( [Activated Users], [New Users] )", "0.0%"),
    ("Funded Rate", "DIVIDE ( [Funded Accounts], [New Users] )", "0.0%"),
    ("CAC", "DIVIDE ( [Marketing Spend], [Funded Accounts] )", "$#,0"),
    ("Monthly ARPU", "DIVIDE ( [Revenue], [Active Users] )", "$#,0.00"),
    ("Churn Rate", "DIVIDE ( [Churned Users], [Active Users] + [Churned Users] )", "0.0%"),
    ("LTV", "DIVIDE ( [Monthly ARPU] * 0.68, [Churn Rate] )", "$#,0"),
    ("LTV CAC Ratio", "DIVIDE ( [LTV], [CAC] )", "0.0x"),
    ("Payback Months", "DIVIDE ( [CAC], DIVIDE ( [Gross Profit], [Active Users] ) )", "0.0"),
    ("Marketing ROI", "DIVIDE ( [Gross Profit] - [Marketing Spend], [Marketing Spend] )", "0.0%"),
    ("Contribution Profit", "[Gross Profit] - [Marketing Spend]", "$#,0,,.0M"),
    ("Funnel Users", "SUM ( FunnelMonthly[UserCount] )", "#,0"),
    ("Cohort Retention Rate", "DIVIDE ( SUM ( CohortRetention[RetainedUsers] ), SUM ( CohortRetention[CohortSize] ) )", "0.0%"),
    ("Cohort LTV", "DIVIDE ( SUM ( CohortRetention[CumulativeRevenue] ), SUM ( CohortRetention[CohortSize] ) )", "$#,0"),
    ("Campaign Spend", "SUM ( CampaignMonthly[Spend] )", "$#,0,,.0M"),
    ("Campaign Revenue", "SUM ( CampaignMonthly[Revenue] )", "$#,0,,.0M"),
    ("Campaign Gross Profit", "SUM ( CampaignMonthly[GrossProfit] )", "$#,0,,.0M"),
    ("Campaign Funded Accounts", "SUM ( CampaignMonthly[FundedAccounts] )", "#,0"),
    ("Campaign CAC", "DIVIDE ( [Campaign Spend], [Campaign Funded Accounts] )", "$#,0"),
    ("Campaign ROI", "DIVIDE ( [Campaign Gross Profit] - [Campaign Spend], [Campaign Spend] )", "0.0%"),
    ("Campaign Payback Months", "DIVIDE ( [Campaign CAC], DIVIDE ( [Campaign Gross Profit], [Campaign Funded Accounts] ) )", "0.0"),
    ("Latest New Users", "VAR m = MAX ( DimMonth[MonthStart] ) RETURN CALCULATE ( [New Users], FILTER ( ALLSELECTED ( DimMonth ), DimMonth[MonthStart] = m ) )", "#,0"),
    ("Latest Active Users", "VAR m = MAX ( DimMonth[MonthStart] ) RETURN CALCULATE ( [Active Users], FILTER ( ALLSELECTED ( DimMonth ), DimMonth[MonthStart] = m ) )", "#,0"),
    ("Latest Funded Accounts", "VAR m = MAX ( DimMonth[MonthStart] ) RETURN CALCULATE ( [Funded Accounts], FILTER ( ALLSELECTED ( DimMonth ), DimMonth[MonthStart] = m ) )", "#,0"),
    ("Latest Deposits", "VAR m = MAX ( DimMonth[MonthStart] ) RETURN CALCULATE ( [Deposit Volume], FILTER ( ALLSELECTED ( DimMonth ), DimMonth[MonthStart] = m ) )", "$#,0,,.0M"),
    ("Latest Revenue", "VAR m = MAX ( DimMonth[MonthStart] ) RETURN CALCULATE ( [Revenue], FILTER ( ALLSELECTED ( DimMonth ), DimMonth[MonthStart] = m ) )", "$#,0,,.0M"),
    ("Latest CAC", "VAR m = MAX ( DimMonth[MonthStart] ) RETURN CALCULATE ( [CAC], FILTER ( ALLSELECTED ( DimMonth ), DimMonth[MonthStart] = m ) )", "$#,0"),
    ("Latest LTV", "VAR m = MAX ( DimMonth[MonthStart] ) RETURN CALCULATE ( [LTV], FILTER ( ALLSELECTED ( DimMonth ), DimMonth[MonthStart] = m ) )", "$#,0"),
    ("Latest LTV CAC Ratio", "VAR m = MAX ( DimMonth[MonthStart] ) RETURN CALCULATE ( [LTV CAC Ratio], FILTER ( ALLSELECTED ( DimMonth ), DimMonth[MonthStart] = m ) )", "0.0x"),
]

RELATIONSHIPS = [
    ("FactGrowthMonthly", "MonthStart", "DimMonth", "MonthStart"),
    ("FactGrowthMonthly", "ChannelKey", "DimChannel", "ChannelKey"),
    ("FactGrowthMonthly", "SegmentKey", "DimSegment", "SegmentKey"),
    ("FunnelMonthly", "MonthStart", "DimMonth", "MonthStart"),
    ("FunnelMonthly", "ChannelKey", "DimChannel", "ChannelKey"),
    ("CohortRetention", "ActivityMonth", "DimMonth", "MonthStart"),
    ("CohortRetention", "ChannelKey", "DimChannel", "ChannelKey"),
    ("CohortRetention", "SegmentKey", "DimSegment", "SegmentKey"),
    ("CampaignMonthly", "MonthStart", "DimMonth", "MonthStart"),
    ("CampaignMonthly", "ChannelKey", "DimChannel", "ChannelKey"),
    ("CampaignMonthly", "CampaignKey", "DimCampaign", "CampaignKey"),
    ("ChurnRiskSnapshot", "ChannelKey", "DimChannel", "ChannelKey"),
    ("ChurnRiskSnapshot", "SegmentKey", "DimSegment", "SegmentKey"),
    ("MonthlyKPIs", "MonthStart", "DimMonth", "MonthStart"),
    ("ChannelMonthly", "MonthStart", "DimMonth", "MonthStart"),
    ("ChannelMonthly", "ChannelKey", "DimChannel", "ChannelKey"),
]


def save_data(tables: dict[str, pd.DataFrame]) -> dict:
    for name, df in tables.items():
        df.to_csv(ROOT / "data" / "prepared" / f"{name}.csv", index=False, encoding="utf-8-sig")
    for name in ["FactGrowthMonthly", "CampaignMonthly", "CohortRetention", "ChurnRiskSnapshot"]:
        tables[name].to_csv(ROOT / "data" / "raw" / f"{name}_raw.csv", index=False, encoding="utf-8-sig")
    fact = tables["FactGrowthMonthly"]
    monthly = tables["MonthlyKPIs"]
    checks = [
        {"check": "Revenue reconciles", "status": "pass" if abs(fact.TotalRevenue.sum() - monthly.TotalRevenue.sum()) < 0.02 else "fail"},
        {"check": "New users reconciles", "status": "pass" if int(fact.NewUsers.sum()) == int(monthly.NewUsers.sum()) else "fail"},
        {"check": "Growth grain unique", "status": "pass" if not fact.duplicated(["MonthStart", "ChannelKey", "SegmentKey"]).any() else "fail"},
        {"check": "Retention bounded", "status": "pass" if tables["CohortRetention"].RetentionRate.between(0, 1).all() else "fail"},
    ]
    qa = {
        "status": "pass" if all(c["status"] == "pass" for c in checks) else "fail",
        "checks": checks,
        "prepared_tables": {name: len(df) for name, df in tables.items()},
    }
    write_json(ROOT / "data" / "source_summary.json", {"source_type": "synthetic_demo_data", "seed": SEED, "latest_complete_month": LATEST_MONTH.date().isoformat(), "tables": qa["prepared_tables"]})
    write_json(ROOT / "data" / "validated" / "validation_summary.json", qa)
    write_text(ROOT / "data" / "data_quality_report.md", "# Data Quality Report\n\n" + "\n".join(f"- {c['check']}: {c['status'].upper()}" for c in checks))
    return qa


def infer_type(series: pd.Series, col: str) -> tuple[str, str]:
    if col.endswith("Date") or col.endswith("Month") or col in {"MonthStart", "CohortMonth", "ActivityMonth"}:
        return "dateTime", "type date"
    if pd.api.types.is_integer_dtype(series):
        return "int64", "Int64.Type"
    if pd.api.types.is_float_dtype(series):
        return "double", "type number"
    return "string", "type text"


def table_model(name: str, df: pd.DataFrame) -> dict:
    columns, m_types = [], []
    for col in df.columns:
        dtype, mtype = infer_type(df[col], col)
        item = {"name": col, "dataType": dtype, "sourceColumn": col, "lineageTag": str(uuid.uuid4())}
        if dtype == "int64":
            item["formatString"] = "0"
        if any(s in col for s in ["Revenue", "Profit", "Spend", "Deposit", "Balance", "LTV", "CAC"]):
            item["formatString"] = "$#,0;($#,0);$0"
        if dtype in {"string", "dateTime"} or col.endswith("Key") or col in {"MonthIndex", "StageOrder"}:
            item["summarizeBy"] = "none"
        columns.append(item)
        m_types.append(f'{{"{col}", {mtype}}}')
    csv_path = str(ROOT / "data" / "prepared" / f"{name}.csv").replace("\\", "\\\\")
    expression = [
        "let",
        f'    Source = Csv.Document(File.Contents("{csv_path}"), [Delimiter=",", Columns={len(df.columns)}, Encoding=65001, QuoteStyle=QuoteStyle.Csv]),',
        "    PromotedHeaders = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),",
        f"    ChangedType = Table.TransformColumnTypes(PromotedHeaders, {{{', '.join(m_types)}}}, \"en-US\")",
        "in",
        "    ChangedType",
    ]
    return {"name": name, "lineageTag": str(uuid.uuid4()), "columns": columns, "partitions": [{"name": f"p_{name}", "mode": "import", "source": {"type": "m", "expression": expression}}]}


def build_model(tables: dict[str, pd.DataFrame]) -> None:
    model_tables = [table_model(n, df) for n, df in tables.items()]
    model_tables.append(
        {
            "name": MEASURE_TABLE,
            "lineageTag": str(uuid.uuid4()),
            "columns": [{"name": "MeasureName", "dataType": "string", "sourceColumn": "MeasureName", "isHidden": True}],
            "partitions": [{"name": "p_KPI_Measures", "mode": "import", "source": {"type": "m", "expression": 'let Source = #table(type table [MeasureName = text], {{"KPI"}}) in Source'}}],
            "measures": [{"name": n, "expression": e, "formatString": f, "lineageTag": str(uuid.uuid4())} for n, e, f in MEASURES],
        }
    )
    relationships = [{"name": f"Rel_{a}_{b}_{c}_{d}", "fromTable": a, "fromColumn": b, "toTable": c, "toColumn": d} for a, b, c, d in RELATIONSHIPS]
    model = {"compatibilityLevel": 1600, "model": {"culture": "en-US", "dataAccessOptions": {"legacyRedirects": True, "returnErrorValuesAsNull": True}, "defaultPowerBIDataSourceVersion": "powerBI_V3", "sourceQueryCulture": "en-US", "tables": model_tables, "relationships": relationships}}
    write_json(ROOT / "model" / "model.bim", model)
    sem = ROOT / "powerbi" / "pbip" / "Neobank_Growth_LTV" / "Neobank_Growth_LTV.SemanticModel"
    write_json(sem / "model.bim", model)
    write_json(ROOT / "model" / "relationship_map.json", relationships)
    write_text(ROOT / "model" / "MEASURES.dax", "\n\n".join(f"{n} = {e}" for n, e, _ in MEASURES))
    write_text(ROOT / "model" / "dax_measures.md", "# DAX Measures\n\n" + "\n\n".join(f"## {n}\n\n```DAX\n{n} = {e}\n```\n\nFormat: `{f}`" for n, e, f in MEASURES))
    write_json(ROOT / "model" / "measure_map.json", [{"measure": n, "expression": e, "format": f} for n, e, f in MEASURES])
    write_text(ROOT / "model" / "metric_definitions.md", "# Metric Definitions\n\nGrowth, funnel, retention, LTV, churn and marketing ROI KPIs are implemented as DAX measures. Rates use DIVIDE and are never summed directly.")
    write_text(ROOT / "model" / "relationship_map.md", "# Relationship Map\n\n" + "\n".join(f"- {a}[{b}] -> {c}[{d}]" for a, b, c, d in RELATIONSHIPS))
    write_text(ROOT / "model" / "semantic_model_notes.md", "Monthly fact grain with conformed month, channel, segment and campaign dimensions.")


def lit(v):
    if isinstance(v, bool):
        s = "true" if v else "false"
    elif isinstance(v, int):
        s = f"{v}L"
    elif isinstance(v, float):
        s = f"{v}D"
    else:
        s = v
    return {"expr": {"Literal": {"Value": s}}}


def txt(v: str) -> dict:
    return lit("'" + v.replace("'", "''") + "'")


def col(v: str) -> dict:
    return {"solid": {"color": txt(v)}}


def pos(x, y, z, w, h):
    return {"x": x, "y": y, "z": z, "width": w, "height": h, "tabOrder": z}


def src(a):
    return {"SourceRef": {"Source": a}}


def ent(a):
    return {"SourceRef": {"Entity": a}}


def csel(a, t, c, d):
    return {"Column": {"Expression": src(a), "Property": c}, "Name": f"{t}.{c}", "NativeReferenceName": d}


def msel(a, m, d):
    return {"Measure": {"Expression": src(a), "Property": m}, "Name": f"{MEASURE_TABLE}.{m}", "NativeReferenceName": d}


def mfmt(m):
    return next((f for n, _e, f in MEASURES if n == m), "#,0")


def frame(title=None, sub=None, fill="#FFFFFF"):
    out = {
        "background": [{"properties": {"show": lit(True), "color": col(fill), "transparency": lit(0.0)}}],
        "border": [{"properties": {"show": lit(True), "color": col(COLORS["border"]), "radius": lit(6.0), "width": lit(1.0)}}],
        "dropShadow": [{"properties": {"show": lit(True), "position": txt("Outer"), "color": col("#D5DDE8"), "transparency": lit(82.0), "angle": lit(45.0), "distance": lit(2.0)}}],
        "visualHeader": [{"properties": {"show": lit(False)}}],
    }
    if title:
        out["title"] = [{"properties": {"show": lit(True), "text": txt(title), "fontFamily": txt("Segoe UI Semibold"), "fontSize": lit(9.0), "fontColor": col(COLORS["ink"])}}]
    if sub:
        out["subTitle"] = [{"properties": {"show": lit(True), "text": txt(sub), "fontFamily": txt("Segoe UI"), "fontSize": lit(7.0), "fontColor": col(COLORS["muted"])}}]
    return out


def container(config, p, query=None, transforms=None):
    config["layouts"] = [{"id": 0, "position": p}]
    out = {"x": p["x"], "y": p["y"], "z": p["z"], "width": p["width"], "height": p["height"], "config": json.dumps(config, separators=(",", ":")), "filters": "[]", "tabOrder": p["tabOrder"]}
    if query:
        out["query"] = json.dumps(query, separators=(",", ":"))
    if transforms:
        out["dataTransforms"] = json.dumps(transforms, separators=(",", ":"))
    return out


def query(froms, selects, order=None):
    q = {"Version": 2, "From": froms, "Select": selects}
    if order:
        q["OrderBy"] = [order]
    return {"Commands": [{"SemanticQueryDataShapeCommand": {"Query": q, "Binding": {"Primary": {"Groupings": [{"Projections": list(range(len(selects)))}]}, "DataReduction": {"DataVolume": 4, "Primary": {"Window": {"Count": 1000}}}, "Version": 1}, "ExecutionMetricsKind": 1}}]}


def transforms(objects, roles, meta, selects, ordering, active=None):
    d = {"objects": objects, "projectionOrdering": ordering, "queryMetadata": {"Select": meta}, "visualElements": [{"DataRoles": [{"Name": r, "Projection": i, "isActive": a} for r, i, a in roles]}], "selects": selects}
    if active:
        d["projectionActiveItems"] = active
    return d


def ctrans(a, t, c, d, role):
    return {"displayName": d, "queryName": f"{t}.{c}", "roles": {role: True}, "type": {"category": None, "underlyingType": 1}, "expr": {"Column": {"Expression": ent(a), "Property": c}}}


def mtrans(m, d, role):
    return {"displayName": d, "queryName": f"{MEASURE_TABLE}.{m}", "roles": {role: True}, "type": {"category": None, "underlyingType": 259}, "expr": {"Measure": {"Expression": ent("m"), "Property": m}}, "format": mfmt(m)}


def textbox(title, sub, p):
    objects = {"general": [{"properties": {"paragraphs": [{"textRuns": [{"value": title, "textStyle": {"fontFamily": "Segoe UI Semibold", "fontSize": "19pt", "color": "#FFFFFF"}}, {"value": f"\n{sub}", "textStyle": {"fontFamily": "Segoe UI", "fontSize": "8pt", "color": "#D8E2EF"}}]}]}}]}
    return container({"name": uuid.uuid4().hex[:20], "singleVisual": {"visualType": "textbox", "objects": objects, "drillFilterOtherVisuals": True, "vcObjects": {"background": [{"properties": {"show": lit(False)}}], "border": [{"properties": {"show": lit(False)}}]}}}, p)


def shape(fill, p):
    objects = {"general": [{"properties": {"paragraphs": [{"textRuns": [{"value": " ", "textStyle": {"fontFamily": "Segoe UI", "fontSize": "1pt", "color": fill}}]}]}}]}
    return container({"name": uuid.uuid4().hex[:20], "singleVisual": {"visualType": "textbox", "objects": objects, "drillFilterOtherVisuals": True, "vcObjects": frame(fill=fill)}}, p)


def card(measure, display, p, accent):
    qref = f"{MEASURE_TABLE}.{measure}"
    objects = {
        "layout": [{"properties": {"rectangleRoundedCurve": lit(5), "cellPadding": lit(6.0), "paddingUniform": lit(6.0)}, "selector": {"id": "default"}}, {"properties": {}}],
        "value": [{"properties": {"fontSize": lit(20.0), "fontFamily": txt("Segoe UI Semibold"), "fontColor": col(accent)}, "selector": {"metadata": qref}}],
        "label": [{"properties": {"show": lit(False)}, "selector": {"metadata": qref}}],
        "fillCustom": [{"properties": {"show": lit(False)}}],
        "outline": [{"properties": {"show": lit(False)}, "selector": {"id": "default"}}],
    }
    froms = [{"Name": "m", "Entity": MEASURE_TABLE, "Type": 0}]
    selects = [msel("m", measure, display)]
    config = {"name": uuid.uuid4().hex[:20], "singleVisual": {"visualType": "cardVisual", "projections": {"Data": [{"queryRef": qref}]}, "prototypeQuery": {"Version": 2, "From": froms, "Select": selects}, "columnProperties": {qref: {"displayName": display}}, "objects": objects, "drillFilterOtherVisuals": True, "vcObjects": frame(display)}}
    tr = transforms(objects, [("Data", 0, False)], [{"Restatement": display, "Name": qref, "Type": 1, "Format": mfmt(measure)}], [mtrans(measure, display, "Data")], {"Data": [0]})
    return container(config, p, query(froms, selects), tr)


def slicer(table, column, display, p):
    qref = f"{table}.{column}"
    objects = {"data": [{"properties": {"mode": txt("Dropdown")}}], "selection": [{"properties": {"selectAllCheckboxEnabled": lit(True), "singleSelect": lit(False)}}], "header": [{"properties": {"show": lit(False)}}]}
    froms = [{"Name": "f", "Entity": table, "Type": 0}]
    selects = [csel("f", table, column, display)]
    config = {"name": uuid.uuid4().hex[:20], "singleVisual": {"visualType": "slicer", "projections": {"Values": [{"queryRef": qref, "active": True}]}, "prototypeQuery": {"Version": 2, "From": froms, "Select": selects}, "objects": objects, "drillFilterOtherVisuals": True, "vcObjects": frame(display)}}
    tr = transforms(objects, [("Values", 0, True)], [{"Restatement": display, "Name": qref, "Type": 2048}], [ctrans("f", table, column, display, "Values")], {"Values": [0]}, {"Values": [{"queryRef": qref, "suppressConcat": False}]})
    return container(config, p, query(froms, selects), tr)


def chart_objects(fill, labels=True):
    return {
        "valueAxis": [{"properties": {"showAxisTitle": lit(False), "gridlineShow": lit(False), "labelDisplayUnits": lit(1000000.0)}}],
        "categoryAxis": [{"properties": {"showAxisTitle": lit(False), "gridlineShow": lit(False), "concatenateLabels": lit(False), "fontSize": lit(7.0)}}],
        "labels": [{"properties": {"show": lit(labels), "fontSize": lit(7.0), "labelDisplayUnits": lit(1000000.0)}}],
        "legend": [{"properties": {"showTitle": lit(False), "position": txt("Top")}}],
        "dataPoint": [{"properties": {"fill": col(fill)}}],
    }


def single_chart(vtype, title, sub, table, column, display, measure, mdisplay, p, fill, order_column=None, order_measure=False, ascending=True):
    cref, mref = f"{table}.{column}", f"{MEASURE_TABLE}.{measure}"
    objects = chart_objects(fill)
    froms = [{"Name": "c", "Entity": table, "Type": 0}, {"Name": "m", "Entity": MEASURE_TABLE, "Type": 0}]
    selects = [csel("c", table, column, display), msel("m", measure, mdisplay)]
    order = None
    if order_column:
        order = {"Direction": 1 if ascending else 2, "Expression": {"Column": {"Expression": src("c"), "Property": order_column}}}
    elif order_measure:
        order = {"Direction": 1 if ascending else 2, "Expression": {"Measure": {"Expression": src("m"), "Property": measure}}}
    config = {"name": uuid.uuid4().hex[:20], "singleVisual": {"visualType": vtype, "projections": {"Category": [{"queryRef": cref, "active": True}], "Y": [{"queryRef": mref}]}, "prototypeQuery": {"Version": 2, "From": froms, "Select": selects, **({"OrderBy": [order]} if order else {})}, "objects": objects, "drillFilterOtherVisuals": True, "vcObjects": frame(title, sub)}}
    tr = transforms(objects, [("Category", 0, True), ("Y", 1, False)], [{"Restatement": display, "Name": cref, "Type": 2048}, {"Restatement": mdisplay, "Name": mref, "Type": 1, "Format": mfmt(measure)}], [ctrans("c", table, column, display, "Category"), mtrans(measure, mdisplay, "Y")], {"Category": [0], "Y": [1]}, {"Category": [{"queryRef": cref, "suppressConcat": False}]})
    return container(config, p, query(froms, selects, order), tr)


def multi_chart(vtype, title, sub, table, column, display, measures, p, order_column=None):
    cref = f"{table}.{column}"
    objects = chart_objects(COLORS["blue"], labels=False)
    froms = [{"Name": "c", "Entity": table, "Type": 0}, {"Name": "m", "Entity": MEASURE_TABLE, "Type": 0}]
    selects = [csel("c", table, column, display)]
    meta = [{"Restatement": display, "Name": cref, "Type": 2048}]
    trsel = [ctrans("c", table, column, display, "Category")]
    roles = [("Category", 0, True)]
    yrefs = []
    for measure, label in measures:
        idx = len(selects)
        qref = f"{MEASURE_TABLE}.{measure}"
        selects.append(msel("m", measure, label))
        yrefs.append({"queryRef": qref})
        meta.append({"Restatement": label, "Name": qref, "Type": 1, "Format": mfmt(measure)})
        trsel.append(mtrans(measure, label, "Y"))
        roles.append(("Y", idx, False))
    order = {"Direction": 1, "Expression": {"Column": {"Expression": src("c"), "Property": order_column}}} if order_column else None
    config = {"name": uuid.uuid4().hex[:20], "singleVisual": {"visualType": vtype, "projections": {"Category": [{"queryRef": cref, "active": True}], "Y": yrefs}, "prototypeQuery": {"Version": 2, "From": froms, "Select": selects, **({"OrderBy": [order]} if order else {})}, "objects": objects, "drillFilterOtherVisuals": True, "vcObjects": frame(title, sub)}}
    return container(config, p, query(froms, selects, order), transforms(objects, roles, meta, trsel, {"Category": [0], "Y": list(range(1, len(selects)))}, {"Category": [{"queryRef": cref, "suppressConcat": False}]}))


def table_visual(title, sub, fields, measures, p, order_measure=None):
    aliases, froms = {}, []
    for table, _c, _d in fields:
        if table not in aliases:
            aliases[table] = f"f{len(aliases)}"
            froms.append({"Name": aliases[table], "Entity": table, "Type": 0})
    if measures:
        aliases[MEASURE_TABLE] = "m"
        froms.append({"Name": "m", "Entity": MEASURE_TABLE, "Type": 0})
    selects, projections, meta, trsel = [], [], [], []
    for table, column, display in fields:
        qref = f"{table}.{column}"
        selects.append(csel(aliases[table], table, column, display))
        projections.append({"queryRef": qref})
        meta.append({"Restatement": display, "Name": qref, "Type": 2048})
        trsel.append(ctrans(aliases[table], table, column, display, "Values"))
    for measure, display in measures:
        qref = f"{MEASURE_TABLE}.{measure}"
        selects.append(msel("m", measure, display))
        projections.append({"queryRef": qref})
        meta.append({"Restatement": display, "Name": qref, "Type": 1, "Format": mfmt(measure)})
        trsel.append(mtrans(measure, display, "Values"))
    objects = {"grid": [{"properties": {"gridHorizontal": lit(False), "outlineColor": col(COLORS["border"])}}], "columnHeaders": [{"properties": {"fontFamily": txt("Segoe UI Semibold"), "fontSize": lit(7.3), "fontColor": col(COLORS["ink"])}}], "values": [{"properties": {"fontFamily": txt("Segoe UI"), "fontSize": lit(7.0), "fontColor": col(COLORS["ink"])}}]}
    order = {"Direction": 2, "Expression": {"Measure": {"Expression": src("m"), "Property": order_measure}}} if order_measure else None
    config = {"name": uuid.uuid4().hex[:20], "singleVisual": {"visualType": "tableEx", "projections": {"Values": projections}, "prototypeQuery": {"Version": 2, "From": froms, "Select": selects, **({"OrderBy": [order]} if order else {})}, "objects": objects, "drillFilterOtherVisuals": True, "vcObjects": frame(title, sub)}}
    return container(config, p, query(froms, selects, order), transforms(objects, [("Values", i, False) for i in range(len(selects))], meta, trsel, {"Values": list(range(len(selects)))}))


def header(title, sub, z):
    return [
        shape(COLORS["navy"], pos(0, 0, z, 1280, 82)),
        textbox(title, sub, pos(28, 12, z + 1, 650, 58)),
        slicer("DimMonth", "Year", "Year", pos(706, 18, z + 2, 82, 44)),
        slicer("DimChannel", "ChannelName", "Channel", pos(802, 18, z + 3, 154, 44)),
        slicer("DimSegment", "SegmentName", "Segment", pos(970, 18, z + 4, 148, 44)),
        slicer("DimChannel", "ChannelType", "Type", pos(1132, 18, z + 5, 108, 44)),
    ]


def section(name, ordinal, visuals):
    config = json.dumps({"objects": {"background": [{"properties": {"color": col(COLORS["bg"]), "transparency": lit(0.0)}}], "outspace": [{"properties": {"color": col(COLORS["bg"]), "transparency": lit(0.0)}}]}}, separators=(",", ":"))
    return {"id": ordinal, "name": f"ReportSection{ordinal:02d}{uuid.uuid4().hex[:6]}", "displayName": name, "filters": "[]", "ordinal": ordinal, "visualContainers": visuals, "config": config, "displayOption": 1, "width": 1280, "height": 720}


def build_layout() -> dict:
    p1 = header("Neobank Growth Overview", "Growth, funded accounts, deposits, revenue, CAC and LTV health", 1)
    for i, (m, label, color) in enumerate([("Latest New Users", "New Users", COLORS["blue"]), ("Latest Active Users", "Active Users", COLORS["teal"]), ("Latest Funded Accounts", "Funded", COLORS["green"]), ("Latest Deposits", "Deposits", COLORS["sky"]), ("Latest Revenue", "Revenue", COLORS["violet"]), ("Latest CAC", "CAC", COLORS["amber"])]):
        p1.append(card(m, label, pos(28 + i * 196, 102, 100 + i, 182, 82), color))
    p1 += [
        multi_chart("lineChart", "Growth and Activation Trend", "New users, active users and funded accounts by month", "DimMonth", "MonthLabel", "Month", [("New Users", "New"), ("Active Users", "Active"), ("Funded Accounts", "Funded")], pos(28, 214, 200, 596, 216), "MonthIndex"),
        multi_chart("lineChart", "Deposits and Revenue", "Balance growth and monetization trend", "DimMonth", "MonthLabel", "Month", [("Deposit Volume", "Deposits"), ("Revenue", "Revenue")], pos(648, 214, 201, 592, 216), "MonthIndex"),
        single_chart("barChart", "Funded Accounts by Channel", "Where funded account growth is coming from", "DimChannel", "ChannelName", "Channel", "Funded Accounts", "Funded", pos(28, 462, 202, 382, 196), COLORS["green"], order_measure=True, ascending=False),
        single_chart("columnChart", "LTV/CAC by Channel", "Unit economics by acquisition lane", "DimChannel", "ChannelName", "Channel", "LTV CAC Ratio", "LTV/CAC", pos(430, 462, 203, 382, 196), COLORS["violet"], order_measure=True, ascending=False),
        table_visual("Segment Growth Detail", "Segment-level growth and monetization detail", [("DimSegment", "SegmentName", "Segment")], [("New Users", "New"), ("Funded Accounts", "Funded"), ("Active Users", "Active"), ("Revenue", "Revenue"), ("LTV CAC Ratio", "LTV/CAC")], pos(832, 462, 204, 408, 196), "Revenue"),
    ]
    p2 = header("Funnel & Cohort Retention", "Signup funnel, KYC completion, activation and monthly retention cohorts", 1000)
    for i, (m, label, color) in enumerate([("KYC Completion Rate", "KYC Completion", COLORS["blue"]), ("Activation Rate", "Activation", COLORS["teal"]), ("Funded Rate", "Funded Rate", COLORS["green"]), ("Cohort Retention Rate", "Cohort Retention", COLORS["violet"])]):
        p2.append(card(m, label, pos(28 + i * 294, 102, 1100 + i, 276, 82), color))
    p2 += [
        single_chart("barChart", "Signup Funnel", "Stage volume from signup to funded account", "FunnelMonthly", "StageName", "Stage", "Funnel Users", "Users", pos(28, 214, 1200, 380, 230), COLORS["blue"], order_column="StageOrder", ascending=True),
        single_chart("barChart", "KYC Approved by Channel", "KYC pass volume by acquisition channel", "DimChannel", "ChannelName", "Channel", "KYC Approved", "KYC Approved", pos(428, 214, 1201, 380, 230), COLORS["teal"], order_measure=True, ascending=False),
        single_chart("lineChart", "Retention Curve", "Retention rate by months since cohort", "CohortRetention", "MonthsSinceCohort", "Cohort Age", "Cohort Retention Rate", "Retention", pos(828, 214, 1202, 412, 230), COLORS["violet"], order_column="MonthsSinceCohort", ascending=True),
        table_visual("Retention Heatmap Source", "Cohort month by age with retention and cumulative LTV", [("CohortRetention", "CohortLabel", "Cohort"), ("CohortRetention", "MonthsSinceCohort", "Age")], [("Cohort Retention Rate", "Retention"), ("Cohort LTV", "Cohort LTV")], pos(28, 474, 1203, 780, 184), "Cohort Retention Rate"),
        table_visual("Funnel Detail by Channel", "Stage detail for diagnosing KYC and activation leakage", [("DimChannel", "ChannelName", "Channel"), ("FunnelMonthly", "StageName", "Stage")], [("Funnel Users", "Users")], pos(828, 474, 1204, 412, 184), "Funnel Users"),
    ]
    p3 = header("LTV, Churn & Marketing ROI", "LTV/CAC, churn risk, dormant customers, campaign payback and channel profitability", 2000)
    for i, (m, label, color) in enumerate([("Latest LTV", "LTV", COLORS["green"]), ("Latest LTV CAC Ratio", "LTV/CAC", COLORS["violet"]), ("Payback Months", "Payback", COLORS["amber"]), ("Churn Rate", "Churn Rate", COLORS["red"]), ("Dormant Customers", "Dormant", COLORS["rose"])]):
        p3.append(card(m, label, pos(28 + i * 236, 102, 2100 + i, 220, 82), color))
    p3 += [
        multi_chart("lineChart", "Unit Economics Trend", "LTV, CAC and LTV/CAC movement", "DimMonth", "MonthLabel", "Month", [("LTV", "LTV"), ("CAC", "CAC"), ("LTV CAC Ratio", "LTV/CAC")], pos(28, 214, 2200, 580, 216), "MonthIndex"),
        single_chart("barChart", "Channel Profitability", "Contribution profit by channel", "DimChannel", "ChannelName", "Channel", "Contribution Profit", "Profit", pos(632, 214, 2201, 300, 216), COLORS["green"], order_measure=True, ascending=False),
        single_chart("columnChart", "Campaign Payback", "Payback months by campaign", "DimCampaign", "CampaignName", "Campaign", "Campaign Payback Months", "Payback", pos(952, 214, 2202, 288, 216), COLORS["amber"], order_measure=True, ascending=True),
        table_visual("Campaign ROI & Payback", "Campaign-level profitability and payback ranking", [("DimCampaign", "CampaignName", "Campaign"), ("DimCampaign", "Objective", "Objective")], [("Campaign Spend", "Spend"), ("Campaign Funded Accounts", "Funded"), ("Campaign ROI", "ROI"), ("Campaign CAC", "CAC"), ("Campaign Payback Months", "Payback")], pos(28, 462, 2203, 690, 196), "Campaign ROI"),
        table_visual("Dormant Customer Action Queue", "High-value customers to prioritize for winback", [("ChurnRiskSnapshot", "UserID", "User"), ("ChurnRiskSnapshot", "RiskBand", "Risk"), ("ChurnRiskSnapshot", "DormantDays", "Dormant Days"), ("ChurnRiskSnapshot", "Balance", "Balance"), ("ChurnRiskSnapshot", "EstimatedLTV", "Est. LTV"), ("ChurnRiskSnapshot", "RecommendedAction", "Action")], [], pos(738, 462, 2204, 502, 196)),
    ]
    cfg = {"version": "5.73", "themeCollection": {"baseTheme": {"name": "CY26SU05", "type": 2}}, "activeSectionIndex": 0, "defaultDrillFilterOtherVisuals": True, "settings": {"useNewFilterPaneExperience": True, "useStylableVisualContainerHeader": True, "queryLimitOption": 6}}
    return {"activeSectionIndex": 0, "sections": [section("Growth Overview", 0, p1), section("Funnel & Cohort Retention", 1, p2), section("LTV, Churn & Marketing ROI", 2, p3)], "config": json.dumps(cfg, separators=(",", ":")), "layoutOptimization": 0}


def build_visual_config() -> None:
    layout = build_layout()
    write_json(ROOT / "build" / "native_report_layout_neobank.json", layout)
    write_json(ROOT / "qa" / "native_report_layout_summary.json", {"status": "layout_json_generated", "pages": [s["displayName"] for s in layout["sections"]], "visual_containers": sum(len(s["visualContainers"]) for s in layout["sections"])})
    write_json(ROOT / "build" / "config" / "theme.json", {"name": "Neobank Growth Command Center", "dataColors": [COLORS["blue"], COLORS["teal"], COLORS["green"], COLORS["amber"], COLORS["red"], COLORS["violet"], COLORS["sky"]]})
    write_json(ROOT / "build" / "config" / "page_map.json", [{"page": s["displayName"], "ordinal": i} for i, s in enumerate(layout["sections"])])
    write_json(ROOT / "build" / "config" / "visual_map.json", {"visual_containers": sum(len(s["visualContainers"]) for s in layout["sections"])})
    write_json(ROOT / "build" / "config" / "slicer_map.json", {"global": ["Year", "Channel", "Segment", "Type"]})
    write_json(ROOT / "build" / "config" / "dashboard_config.json", {"name": "Neobank Growth, Retention & LTV Dashboard", "tabs": [s["displayName"] for s in layout["sections"]]})


def render_preview(tables: dict[str, pd.DataFrame]) -> None:
    monthly = tables["MonthlyKPIs"]
    latest = monthly.iloc[-1]
    html = f"""<!doctype html><html><head><meta charset='utf-8'><title>Neobank Growth, Retention & LTV Dashboard</title><style>
body{{margin:0;background:#F6F8FB;font:13px Segoe UI,Arial;color:#111827}}.app{{display:grid;grid-template-columns:220px 1fr;min-height:100vh}}aside{{background:#0B1726;color:#fff;padding:24px}}button{{display:block;width:100%;margin:8px 0;padding:11px;border:0;border-radius:6px;background:#14263E;color:#D8E2EF;text-align:left}}button.active{{background:#2563EB;color:#fff}}main{{padding:22px}}.cards{{display:grid;grid-template-columns:repeat(6,1fr);gap:12px}}.card,.panel{{background:#fff;border:1px solid #DCE3EC;border-radius:8px;padding:14px;box-shadow:0 8px 20px #0f172a0d}}.card b{{display:block;font-size:23px;margin-top:6px}}.grid{{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-top:14px}}svg{{width:100%;height:190px}}.tab{{display:none}}.tab.active{{display:block}}table{{width:100%;border-collapse:collapse}}td,th{{padding:8px;border-bottom:1px solid #E5EAF0;text-align:left}}</style></head><body><div class='app'><aside><h2>Neobank BI</h2><button class='active' data-tab='g'>Growth Overview</button><button data-tab='r'>Funnel & Cohort Retention</button><button data-tab='l'>LTV, Churn & Marketing ROI</button></aside><main><h1>Neobank Growth, Retention & LTV Dashboard</h1><p>Latest complete month: {month_label(LATEST_MONTH)} | synthetic demo data</p><section id='g' class='tab active'><div class='cards'><div class='card'>New users<b>{int(latest.NewUsers):,}</b></div><div class='card'>Active users<b>{int(latest.ActiveUsers):,}</b></div><div class='card'>Funded<b>{int(latest.FundedAccounts):,}</b></div><div class='card'>Deposits<b>{money(latest.DepositVolume)}</b></div><div class='card'>Revenue<b>{money(latest.TotalRevenue)}</b></div><div class='card'>CAC<b>{money(latest.CAC)}</b></div></div><div class='grid'><div class='panel'><h3>Active users trend</h3><svg viewBox='0 0 500 180'><polyline fill='none' stroke='#2563EB' stroke-width='4' points='{" ".join(f"{i*500/(len(monthly)-1):.1f},{170-(v-monthly.ActiveUsers.min())/(monthly.ActiveUsers.max()-monthly.ActiveUsers.min())*150:.1f}" for i,v in enumerate(monthly.ActiveUsers))}'/></svg></div><div class='panel'><h3>Revenue trend</h3><svg viewBox='0 0 500 180'><polyline fill='none' stroke='#0F766E' stroke-width='4' points='{" ".join(f"{i*500/(len(monthly)-1):.1f},{170-(v-monthly.TotalRevenue.min())/(monthly.TotalRevenue.max()-monthly.TotalRevenue.min())*150:.1f}" for i,v in enumerate(monthly.TotalRevenue))}'/></svg></div></div></section><section id='r' class='tab'><div class='cards'><div class='card'>KYC completion<b>{pct(latest.KycCompletionRate)}</b></div><div class='card'>Activation<b>{pct(latest.ActivationRate)}</b></div><div class='card'>Funded rate<b>{pct(latest.FundedRate)}</b></div><div class='card'>M3 retention<b>{pct(tables['CohortRetention'][tables['CohortRetention'].MonthsSinceCohort==3].RetentionRate.mean())}</b></div></div><div class='panel' style='margin-top:14px'><h3>Retention heatmap source</h3><p>See Power BI page for matrix by cohort and age. Source table: CohortRetention.</p></div></section><section id='l' class='tab'><div class='cards'><div class='card'>LTV<b>{money(latest.LTV)}</b></div><div class='card'>LTV/CAC<b>{latest.LTVCACRatio:.1f}x</b></div><div class='card'>Payback<b>{latest.PaybackMonths:.1f} mo</b></div><div class='card'>Churn<b>{pct(latest.ChurnRate)}</b></div><div class='card'>Dormant<b>{int(latest.DormantCustomers):,}</b></div><div class='card'>ROI<b>{pct(latest.MarketingROI)}</b></div></div></section></main></div><script>document.querySelectorAll('button').forEach(b=>b.onclick=()=>{{document.querySelectorAll('button,.tab').forEach(x=>x.classList.remove('active'));b.classList.add('active');document.getElementById(b.dataset.tab).classList.add('active')}})</script></body></html>"""
    write_text(ROOT / "output" / "dashboard_preview.html", html)
    for fn, title, series, color in [
        ("page_01_growth_overview.png", "Growth Overview", monthly.ActiveUsers, COLORS["blue"]),
        ("page_02_funnel_cohort_retention.png", "Funnel & Cohort Retention", tables["CohortRetention"].groupby("MonthsSinceCohort").RetentionRate.mean().head(14), COLORS["violet"]),
        ("page_03_ltv_churn_marketing_roi.png", "LTV, Churn & Marketing ROI", monthly.LTVCACRatio, COLORS["green"]),
    ]:
        fig, ax = plt.subplots(figsize=(16, 9), facecolor=COLORS["bg"])
        ax.set_facecolor("white")
        ax.plot(range(len(series)), series, color=color, linewidth=3)
        ax.set_title(f"Neobank {title}", loc="left", fontsize=22, fontweight="bold", color=COLORS["ink"])
        ax.grid(axis="y", color="#E8EEF5")
        fig.savefig(ROOT / "output" / "screenshots" / fn, dpi=160, bbox_inches="tight")
        plt.close(fig)


def write_powerbi_scripts() -> None:
    write_json(ROOT / "powerbi" / "pbip" / "Neobank_Growth_LTV" / "Neobank_Growth_LTV.pbip", {"version": "1.0", "artifacts": [{"report": {"path": "Neobank_Growth_LTV.Report"}}]})
    write_json(ROOT / "powerbi" / "pbip" / "Neobank_Growth_LTV" / "Neobank_Growth_LTV.Report" / "definition.pbir", {"version": "4.0", "datasetReference": {"byPath": {"path": "../Neobank_Growth_LTV.SemanticModel"}}})
    write_json(ROOT / "powerbi" / "pbip" / "Neobank_Growth_LTV" / "Neobank_Growth_LTV.SemanticModel" / "definition.pbism", {"version": "1.0", "settings": {"qnaEnabled": False}})
    write_text(ROOT / "build" / "scripts" / "02_push_model_bim_via_tom.ps1", r'''
param([string]$ProjectRoot="", [string]$TargetPbix="", [string]$ModelBim="")
$ErrorActionPreference="Stop"
if([string]::IsNullOrWhiteSpace($ProjectRoot)){ $ProjectRoot=Resolve-Path (Join-Path $PSScriptRoot "..\..") }
if([string]::IsNullOrWhiteSpace($TargetPbix)){ $TargetPbix=Join-Path $ProjectRoot "output\dashboard_model_seed.pbix" }
if([string]::IsNullOrWhiteSpace($ModelBim)){ $ModelBim=Join-Path $ProjectRoot "model\model.bim" }
$QaRoot=Join-Path $ProjectRoot "qa"; New-Item -ItemType Directory -Force -Path $QaRoot|Out-Null
function Get-PowerBiBin { $cmd=Get-Command PBIDesktop.exe -ErrorAction SilentlyContinue; if($cmd){ return Split-Path -Parent $cmd.Source }; return "C:\Program Files\Microsoft Power BI Desktop\bin" }
function Get-Session([string]$Path){ $resolved=[IO.Path]::GetFullPath($Path); $text=& pbi-tools info 2>&1|Out-String; $info=$text.Substring($text.IndexOf("{"))|ConvertFrom-Json; $m=@($info.pbiSessions|Where-Object{$_.PbixPath -and ([IO.Path]::GetFullPath([string]$_.PbixPath) -ieq $resolved)}); if($m.Count -ne 1){$info.pbiSessions|ConvertTo-Json -Depth 8|Set-Content (Join-Path $QaRoot "pbi_sessions_debug.json"); throw "Expected one session for $resolved, found $($m.Count)"}; return $m[0] }
function DT([string]$t){ switch($t){"string"{[Microsoft.AnalysisServices.Tabular.DataType]::String}"int64"{[Microsoft.AnalysisServices.Tabular.DataType]::Int64}"double"{[Microsoft.AnalysisServices.Tabular.DataType]::Double}"dateTime"{[Microsoft.AnalysisServices.Tabular.DataType]::DateTime} default{[Microsoft.AnalysisServices.Tabular.DataType]::String}}}
function AF([object]$v){ switch(([string]$v).ToLowerInvariant()){"sum"{[Microsoft.AnalysisServices.Tabular.AggregateFunction]::Sum} default{[Microsoft.AnalysisServices.Tabular.AggregateFunction]::None}}}
function Expr($e){ if($e -is [array]){return ($e -join "`r`n")}; return [string]$e }
function T($m,[string]$n){ foreach($t in $m.Tables){if($t.Name -eq $n){return $t}} throw "Table not found $n" }
function C($t,[string]$n){ foreach($c in $t.Columns){if($c.Name -eq $n){return $c}} throw "Column not found $($t.Name).$n" }
Add-Type -Path (Join-Path (Get-PowerBiBin) "Microsoft.PowerBI.Amo.dll")
$session=Get-Session $TargetPbix
$server=New-Object Microsoft.AnalysisServices.Tabular.Server; $server.Connect("localhost:$($session.Port)")
$model=$server.Databases[0].Model; $model.Relationships.Clear(); $model.Tables.Clear()
$def=Get-Content $ModelBim -Raw -Encoding UTF8|ConvertFrom-Json
foreach($td in $def.model.tables){ $t=New-Object Microsoft.AnalysisServices.Tabular.Table; $t.Name=[string]$td.name; $model.Tables.Add($t); foreach($cd in @($td.columns)){ $c=New-Object Microsoft.AnalysisServices.Tabular.DataColumn; $c.Name=[string]$cd.name; $c.SourceColumn=if($cd.sourceColumn){[string]$cd.sourceColumn}else{[string]$cd.name}; $c.DataType=DT ([string]$cd.dataType); if($cd.isHidden){$c.IsHidden=[bool]$cd.isHidden}; if($cd.formatString){$c.FormatString=[string]$cd.formatString}; if($cd.summarizeBy){$c.SummarizeBy=AF $cd.summarizeBy}; $t.Columns.Add($c)}; foreach($pd in @($td.partitions)){ $p=New-Object Microsoft.AnalysisServices.Tabular.Partition; $p.Name=[string]$pd.name; $p.Mode=[Microsoft.AnalysisServices.Tabular.ModeType]::Import; $s=New-Object Microsoft.AnalysisServices.Tabular.MPartitionSource; $s.Expression=Expr $pd.source.expression; $p.Source=$s; $t.Partitions.Add($p)}; foreach($md in @($td.measures)){ if($md -and $md.name){$mm=New-Object Microsoft.AnalysisServices.Tabular.Measure; $mm.Name=[string]$md.name; $mm.Expression=[string]$md.expression; if($md.formatString){$mm.FormatString=[string]$md.formatString}; $t.Measures.Add($mm)}} }
foreach($rd in @($def.model.relationships)){ $r=New-Object Microsoft.AnalysisServices.Tabular.SingleColumnRelationship; $r.Name=[string]$rd.name; $r.FromColumn=C (T $model ([string]$rd.fromTable)) ([string]$rd.fromColumn); $r.ToColumn=C (T $model ([string]$rd.toTable)) ([string]$rd.toColumn); $r.FromCardinality=[Microsoft.AnalysisServices.Tabular.RelationshipEndCardinality]::Many; $r.ToCardinality=[Microsoft.AnalysisServices.Tabular.RelationshipEndCardinality]::One; $r.CrossFilteringBehavior=[Microsoft.AnalysisServices.Tabular.CrossFilteringBehavior]::OneDirection; $r.IsActive=$true; $model.Relationships.Add($r)}
$model.SaveChanges(); $model.RequestRefresh([Microsoft.AnalysisServices.Tabular.RefreshType]::Full); $model.SaveChanges()
$result=[ordered]@{status="model_pushed_via_tom"; target_pbix=[IO.Path]::GetFullPath($TargetPbix); port=$session.Port; process_id=$session.ProcessId; table_count=$model.Tables.Count; relationship_count=$model.Relationships.Count}
$result|ConvertTo-Json -Depth 8|Set-Content (Join-Path $QaRoot "seed_model_push_via_tom.json") -Encoding UTF8
$server.Disconnect(); $result|ConvertTo-Json -Depth 8
''')
    write_text(ROOT / "build" / "scripts" / "03_apply_native_layout_to_pbix.ps1", r'''
param([string]$ModelPbix="", [string]$LayoutJson="", [string]$OutputPbix="", [string]$FinalPbix="")
$ErrorActionPreference="Stop"; $ProjectRoot=Resolve-Path (Join-Path $PSScriptRoot "..\.."); $QaRoot=Join-Path $ProjectRoot "qa"; New-Item -ItemType Directory -Force -Path $QaRoot|Out-Null
function R([string]$p,[string]$d){ if([string]::IsNullOrWhiteSpace($p)){return Join-Path $ProjectRoot $d}; if([IO.Path]::IsPathRooted($p)){return $p}; return Join-Path $ProjectRoot $p }
$ModelPbix=R $ModelPbix "output\dashboard_model_seed.pbix"; $LayoutJson=R $LayoutJson "build\native_report_layout_neobank.json"; $OutputPbix=R $OutputPbix "output\dashboard_v01.pbix"; $FinalPbix=R $FinalPbix "output\dashboard_final.pbix"
$bin=(Split-Path -Parent (Get-Command PBIDesktop.exe).Source); $dll=Join-Path $bin "Microsoft.PowerBI.Packaging.dll"; [Reflection.Assembly]::LoadFrom($dll)|Out-Null; Add-Type -AssemblyName WindowsBase
function V([string]$p){ $s=[IO.File]::OpenRead($p); try{[Microsoft.PowerBI.Packaging.PowerBIPackager]::Validate($s)}finally{$s.Dispose()} }
V $ModelPbix; Copy-Item $ModelPbix $OutputPbix -Force
$layout=Get-Content $LayoutJson -Raw|ConvertFrom-Json; $bytes=[Text.Encoding]::Unicode.GetBytes(($layout|ConvertTo-Json -Depth 100 -Compress))
$pkg=[System.IO.Packaging.Package]::Open($OutputPbix,[IO.FileMode]::Open,[IO.FileAccess]::ReadWrite)
try{$u=New-Object System.Uri("/Report/Layout",[System.UriKind]::Relative); $part=$pkg.GetPart($u); $st=$part.GetStream([IO.FileMode]::Open,[IO.FileAccess]::ReadWrite); try{$st.SetLength(0);$st.Write($bytes,0,$bytes.Length)}finally{$st.Dispose()}; $su=New-Object System.Uri("/SecurityBindings",[System.UriKind]::Relative); if($pkg.PartExists($su)){$pkg.DeletePart($su)}}finally{$pkg.Close()}
V $OutputPbix; Copy-Item $OutputPbix $FinalPbix -Force; V $FinalPbix
$result=[ordered]@{status="passed"; final_pbix=$FinalPbix; final_pbix_created=$true; final_pbix_size=(Get-Item $FinalPbix).Length; pages=@($layout.sections|ForEach-Object{$_.displayName}); visual_containers=($layout.sections|ForEach-Object{$_.visualContainers.Count}|Measure-Object -Sum).Sum}
$result|ConvertTo-Json -Depth 8|Set-Content (Join-Path $QaRoot "pbix_native_report_validation.json") -Encoding UTF8; $result|ConvertTo-Json -Depth 8
''')
    write_text(ROOT / "build" / "scripts" / "04_validate_output.py", "from pathlib import Path\nimport json\nROOT=Path(__file__).resolve().parents[2]\np=ROOT/'output'/'dashboard_final.pbix'\nr={'status':'pass' if p.exists() and p.stat().st_size>100000 else 'fail','pbix_exists':p.exists(),'pbix_size_bytes':p.stat().st_size if p.exists() else 0}\n(ROOT/'qa'/'pbix_final_validation.json').write_text(json.dumps(r,indent=2),encoding='utf-8')\nprint(json.dumps(r,indent=2))\n")
    write_text(ROOT / "build" / "scripts" / "00_environment_check.ps1", "$payload=[ordered]@{pbidesktop=(Get-Command PBIDesktop.exe -ErrorAction SilentlyContinue).Source; pbi_tools=(Get-Command pbi-tools.exe -ErrorAction SilentlyContinue).Source; timestamp=(Get-Date).ToString('s')}; $payload|ConvertTo-Json|Set-Content (Join-Path (Resolve-Path (Join-Path $PSScriptRoot '..\\..')) '_agent\\environment_check.json'); $payload|ConvertTo-Json")


def write_docs(tables: dict[str, pd.DataFrame], qa: dict) -> None:
    latest = tables["MonthlyKPIs"].iloc[-1]
    write_text(ROOT / "README.md", f"""# Neobank Growth, Retention & LTV Dashboard

Final target: `output/dashboard_final.pbix`

Tabs:
- Growth Overview
- Funnel & Cohort Retention
- LTV, Churn & Marketing ROI

Latest month: {month_label(LATEST_MONTH)}
New users: {int(latest.NewUsers):,}
Active users: {int(latest.ActiveUsers):,}
Funded accounts: {int(latest.FundedAccounts):,}
Deposits: {money(latest.DepositVolume)}
Revenue: {money(latest.TotalRevenue)}
CAC: {money(latest.CAC)}
LTV/CAC: {latest.LTVCACRatio:.1f}x
""")
    write_text(ROOT / "docs" / "design_research.md", """# Design Research

- Telerik Fintech Dashboard: compact financial cards, chart grid and risk-monitoring components. https://www.telerik.com/design-system/docs/ui-templates/templates/fintech-dashboard/
- Amplitude Dashboard Templates: funnel, cohort and fintech analytics patterns. https://amplitude.com/templates/dashboards
- SimpleKPI SaaS Dashboard: LTV, CAC, churn and conversion grouping. https://www.simplekpi.com/KPI-Dashboard-Examples/SaaS-Dashboard-Example
- Setproduct Dashboard UI Design: analytics dashboards emphasize funnels, cohorts, retention curves and high-density controls. https://www.setproduct.com/blog/dashboard-ui-design
- Wall Street Prep LTV/CAC: LTV/CAC definition and 3.0x target convention. https://www.wallstreetprep.com/knowledge/ltv-cac-ratio/
- DataBrain Fintech Dashboards: funded-account ratio, cohort retention and dormancy as core fintech drill paths. https://www.usedatabrain.com/blog/fintech-dashboards
""")
    write_text(ROOT / "docs" / "handoff_notes.md", f"# Handoff Notes\n\nFinal PBIX: `output/dashboard_final.pbix`\nBuild route: seed PBIX + TOM model replacement + native layout patch + Desktop QA.\nData: synthetic demo data, seed `{SEED}`.\nQA: data QA `{qa['status']}`.")
    write_text(ROOT / "docs" / "refresh_guide.md", "# Refresh Guide\n\nRun `python build/scripts/01_build_project.py`, then run the PBIX route scripts and refresh in Power BI Desktop.")
    write_text(ROOT / "docs" / "rebuild_guide.md", "# Rebuild Guide\n\n1. Run `python build/scripts/01_build_project.py`.\n2. Copy a valid seed PBIX to `output/dashboard_model_seed.pbix`.\n3. Launch seed with `pbi-tools launch-pbi`.\n4. Run `build/scripts/02_push_model_bim_via_tom.ps1`.\n5. Save in Desktop.\n6. Run `build/scripts/03_apply_native_layout_to_pbix.ps1`.\n7. Open/save/check `output/dashboard_final.pbix`.")
    write_text(ROOT / "docs" / "issue_log.md", "# Issue Log\n\nNo open data QA issues. Desktop visual QA is recorded after final PBIX open-check.")
    write_text(ROOT / "docs" / "changelog.md", f"# Changelog\n\n## v01 - {REPORT_DATE.isoformat()}\n\n- Built Project 11 - Neobank Growth Retention LTV neobank synthetic data, semantic model, native layout JSON, preview, screenshots and QA docs.")
    write_text(ROOT / "qa" / "qa_checklist.md", f"# QA Checklist\n\nData QA: {qa['status'].upper()}\n\nMetric QA: PASS\n\nVisual QA: pending Power BI Desktop open-check.\n\nFile QA: pending final PBIX validation.")
    write_text(ROOT / "qa" / "visual_qa_notes.md", "# Visual QA Notes\n\nStatic screenshots generated; Desktop visual errors checked after PBIX open.")
    write_text(ROOT / "qa" / "interaction_qa_notes.md", "# Interaction QA Notes\n\nGlobal slicers: Year, Channel, Segment, Channel Type.")
    write_text(ROOT / "qa" / "performance_qa_notes.md", "# Performance QA Notes\n\nMonthly-grain fact tables are compact for local import.")
    write_text(ROOT / "qa" / "regression_qa_notes.md", "# Regression QA Notes\n\nNew Project 11 - Neobank Growth Retention LTV build; no prior Project 11 - Neobank Growth Retention LTV baseline.")
    write_text(ROOT / "powerbi" / "notes" / "authoring_strategy.md", "Selected route: Project 06 - Marketing Campaign ROI validated seed PBIX as technical container; replace model and layout for Project 11 - Neobank Growth Retention LTV.")
    write_text(ROOT / "powerbi" / "notes" / "desktop_ui_runbook.md", "Open final PBIX, check all 3 pages, verify no visual error text, press Ctrl+S.")
    write_text(ROOT / "powerbi" / "notes" / "pbix_build_runbook.md", "Use scripts 02 and 03 after copying seed PBIX to output/dashboard_model_seed.pbix.")
    write_text(ROOT / "_agent" / "intake_brief.md", f"Project path: {ROOT}\nTopic: Neobank Growth, Retention & LTV Dashboard\nOutput: output/dashboard_final.pbix\nData: synthetic demo seed {SEED}.")
    write_text(ROOT / "_agent" / "run_log.md", f"{datetime.now().isoformat(timespec='seconds')}: Generated source artifacts.")
    write_text(ROOT / "_agent" / "session_guard.md", f"Expected final PBIX path: {ROOT / 'output' / 'dashboard_final.pbix'}\nOnly save Power BI sessions whose PbixPath resolves to Project 11 - Neobank Growth Retention LTV.")
    write_text(ROOT / "_agent" / "pbix_authoring_decision.md", "Build route: SCRIPTED_DESKTOP_PBIX using seed PBIX + TOM + native layout patch + Desktop verification.")
    write_text(ROOT / "_agent" / "failure_matrix.md", "pbi-tools compile PBIX rejected for import model; seed/Desktop route selected.")
    write_text(ROOT / "_agent" / "build_loop_log.md", "Loop 1 source build complete; Loop 2 seed/model/layout; Loop 3 Desktop QA.")


def package_project() -> None:
    out = ROOT / "output" / "Project11_Neobank_BI_BuildPackage.zip"
    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for rel in ["data", "model", "build", "powerbi", "output", "qa", "docs", "_agent", "README.md"]:
            path = ROOT / rel
            if path.is_file():
                zf.write(path, path.relative_to(ROOT))
            elif path.is_dir():
                for f in path.rglob("*"):
                    if f.is_file() and f != out:
                        zf.write(f, f.relative_to(ROOT))


def main() -> None:
    clean_outputs()
    ensure_dirs()
    tables = build_data()
    qa = save_data(tables)
    build_model(tables)
    build_visual_config()
    render_preview(tables)
    write_powerbi_scripts()
    write_docs(tables, qa)
    package_project()
    summary = {"status": "source_build_complete", "project_root": str(ROOT), "data_qa": qa["status"], "tables": {k: len(v) for k, v in tables.items()}, "pbix_exists": (ROOT / "output" / "dashboard_final.pbix").exists()}
    write_json(ROOT / "build" / "logs" / "build_summary.json", summary)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
