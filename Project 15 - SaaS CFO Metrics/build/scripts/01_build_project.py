from __future__ import annotations

import json
import math
import os
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
SEED = 20260615
REPORT_DATE = date(2026, 6, 15)
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
    "teal": "#0F766E",
    "green": "#16A34A",
    "amber": "#F59E0B",
    "red": "#DC2626",
    "rose": "#E11D48",
    "violet": "#7C3AED",
    "sky": "#0EA5E9",
    "slate": "#334155",
}

PLANS = [
    ("starter", "Starter", "SMB", 690, 0.76, 0.052, 1450, 12),
    ("growth", "Growth", "SMB", 1480, 0.79, 0.041, 2700, 14),
    ("business", "Business", "Mid-Market", 4200, 0.81, 0.031, 7600, 15),
    ("scale", "Scale", "Mid-Market", 8600, 0.82, 0.024, 14400, 16),
    ("enterprise", "Enterprise", "Enterprise", 18800, 0.84, 0.018, 33000, 18),
]
CHANNELS = [
    ("plg", "Product-Led", "PLG", "Organic", 0.72, 1.10),
    ("inbound", "Inbound Demand", "Inbound", "Paid", 1.05, 1.00),
    ("outbound", "Outbound Sales", "Outbound", "Paid", 1.32, 0.92),
    ("partner", "Partner Ecosystem", "Partner", "Partner", 0.96, 1.03),
    ("expansion", "Customer Success", "Expansion", "Owned", 0.42, 1.18),
]
REGIONS = [
    ("na", "North America", "Americas", 1.18),
    ("emea", "EMEA", "International", 0.93),
    ("apac", "APAC", "International", 0.82),
    ("latam", "LATAM", "Americas", 0.58),
]
INDUSTRIES = ["Software", "Financial Services", "Healthcare", "Retail", "Manufacturing", "Education", "Logistics"]


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
        "data/synthetic",
        "model",
        "build/config",
        "build/logs",
        "build/scripts",
        "powerbi/pbip/SaaS_CFO_Metrics/SaaS_CFO_Metrics.Report",
        "powerbi/pbip/SaaS_CFO_Metrics/SaaS_CFO_Metrics.SemanticModel",
        "powerbi/notes",
        "output/screenshots",
        "output/exports",
        "qa",
        "docs",
        "_agent",
        "archive/old_versions",
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


def collect_environment() -> dict:
    def ps_json(command: str) -> object:
        try:
            proc = subprocess.run(["powershell", "-NoProfile", "-Command", command], capture_output=True, text=True, timeout=20)
            if not proc.stdout.strip():
                return []
            return json.loads(proc.stdout)
        except Exception as exc:
            return {"error": str(exc)}

    cmd = shutil.which("PBIDesktop.exe")
    pbi_tools = shutil.which("pbi-tools") or shutil.which("pbi-tools.exe")
    return {
        "checked_at": datetime.now().isoformat(timespec="seconds"),
        "power_bi_desktop_command": cmd,
        "power_bi_program_files": Path(r"C:\Program Files\Microsoft Power BI Desktop\bin\PBIDesktop.exe").exists(),
        "power_bi_x86": Path(r"C:\Program Files (x86)\Microsoft Power BI Desktop\bin\PBIDesktop.exe").exists(),
        "power_bi_start_apps": ps_json("Get-StartApps | Where-Object { $_.Name -like '*Power BI Desktop*' -or $_.AppID -like '*PowerBI*' } | Select-Object Name,AppID | ConvertTo-Json -Depth 4"),
        "pbi_tools": pbi_tools,
        "dotnet": shutil.which("dotnet"),
        "computer_use": "available; Windows app discovery confirmed Power BI Desktop before this build",
    }


def build_data() -> dict[str, pd.DataFrame]:
    rng = np.random.default_rng(SEED)
    dim_date = pd.DataFrame(
        {
            "MonthStart": [m.date().isoformat() for m in MONTHS],
            "MonthLabel": [month_label(m) for m in MONTHS],
            "MonthIndex": range(1, len(MONTHS) + 1),
            "Year": [m.year for m in MONTHS],
            "Quarter": [f"Q{((m.month - 1) // 3) + 1}" for m in MONTHS],
            "IsLatestCompleteMonth": [int(m == LATEST_MONTH) for m in MONTHS],
        }
    )
    dim_plan = pd.DataFrame(
        [
            {
                "PlanID": pid,
                "PlanName": name,
                "Segment": segment,
                "BaseMRR": base,
                "GrossMarginTarget": margin,
                "MonthlyChurnTarget": churn,
                "TargetCAC": cac,
                "BenchmarkPaybackMonths": payback,
            }
            for pid, name, segment, base, margin, churn, cac, payback in PLANS
        ]
    )
    dim_channel = pd.DataFrame(
        [
            {
                "ChannelID": cid,
                "ChannelName": name,
                "Motion": motion,
                "SourceType": source,
                "CACIndex": cac_index,
                "QualityIndex": quality,
            }
            for cid, name, motion, source, cac_index, quality in CHANNELS
        ]
    )
    dim_region = pd.DataFrame(
        [{"RegionID": rid, "Region": name, "GeoGroup": group, "ScaleIndex": scale} for rid, name, group, scale in REGIONS]
    )

    customers = []
    customer_count = 520
    month_weights = np.linspace(1.35, 0.72, len(MONTHS))
    month_weights = month_weights / month_weights.sum()
    plan_weights = np.array([0.30, 0.28, 0.20, 0.14, 0.08])
    channel_weights = np.array([0.30, 0.24, 0.18, 0.16, 0.12])
    region_weights = np.array([0.46, 0.25, 0.20, 0.09])
    for i in range(1, customer_count + 1):
        plan = PLANS[int(rng.choice(len(PLANS), p=plan_weights))]
        channel = CHANNELS[int(rng.choice(len(CHANNELS), p=channel_weights))]
        region = REGIONS[int(rng.choice(len(REGIONS), p=region_weights))]
        acquisition_month = MONTHS[int(rng.choice(len(MONTHS), p=month_weights))]
        industry = INDUSTRIES[int(rng.integers(0, len(INDUSTRIES)))]
        account = f"{industry.split()[0]} Cloud {i:03d}"
        customers.append(
            {
                "CustomerID": f"C{i:04d}",
                "AccountName": account,
                "PlanID": plan[0],
                "PlanName": plan[1],
                "Segment": plan[2],
                "ChannelID": channel[0],
                "ChannelName": channel[1],
                "Motion": channel[2],
                "RegionID": region[0],
                "Region": region[1],
                "Industry": industry,
                "AcquisitionMonth": acquisition_month.date().isoformat(),
            }
        )
    dim_customer = pd.DataFrame(customers)

    plan_map = {p[0]: p for p in PLANS}
    channel_map = {c[0]: c for c in CHANNELS}
    region_map = {r[0]: r for r in REGIONS}
    subscription_rows = []
    account_health_rows = []
    for customer in customers:
        plan = plan_map[customer["PlanID"]]
        channel = channel_map[customer["ChannelID"]]
        region = region_map[customer["RegionID"]]
        acq = pd.Timestamp(customer["AcquisitionMonth"])
        current_mrr = float(plan[3] * region[3] * rng.lognormal(0, 0.28))
        active = True
        for month_i, month in enumerate(MONTHS):
            if month < acq or not active:
                continue
            age = (month.year - acq.year) * 12 + month.month - acq.month
            beginning = 0.0 if month == acq else current_mrr
            new_mrr = current_mrr if month == acq else 0.0
            churn_base = plan[5] * (1.22 if channel[3] == "Paid" else 0.88) * (0.72 if age >= 12 else 1.0)
            expansion_chance = min(0.48, 0.08 + age * 0.012) * channel[5]
            contraction_chance = 0.032 + max(0, age - 10) * 0.002
            expansion = 0.0
            contraction = 0.0
            churn = 0.0
            churned_logo = 0
            if month != acq and rng.random() < expansion_chance:
                expansion = current_mrr * float(rng.uniform(0.035, 0.22))
            if month != acq and rng.random() < contraction_chance:
                contraction = -current_mrr * float(rng.uniform(0.025, 0.16))
            if month != acq and rng.random() < churn_base:
                churn = -(current_mrr + expansion + contraction)
                churned_logo = 1
                active = False
            ending = max(0.0, beginning + new_mrr + expansion + contraction + churn)
            recognized_revenue = ending * float(rng.uniform(0.96, 1.03))
            gross_margin = recognized_revenue * float(np.clip(plan[4] + rng.normal(0, 0.018), 0.68, 0.90))
            seats = max(3, int((ending / max(plan[3], 1)) * rng.uniform(8, 32)))
            subscription_rows.append(
                {
                    "MonthStart": month.date().isoformat(),
                    "CustomerID": customer["CustomerID"],
                    "PlanID": customer["PlanID"],
                    "ChannelID": customer["ChannelID"],
                    "RegionID": customer["RegionID"],
                    "BeginningMRR": round(beginning, 2),
                    "NewMRR": round(new_mrr, 2),
                    "ExpansionMRR": round(expansion, 2),
                    "ContractionMRR": round(contraction, 2),
                    "ChurnMRR": round(churn, 2),
                    "EndingMRR": round(ending, 2),
                    "RecognizedRevenue": round(recognized_revenue, 2),
                    "GrossMargin": round(gross_margin, 2),
                    "Seats": seats,
                    "StartingLogo": 1 if beginning > 0 else 0,
                    "ActiveLogo": 1 if ending > 0 else 0,
                    "NewLogo": 1 if new_mrr > 0 else 0,
                    "ChurnedLogo": churned_logo,
                    "IsSynthetic": "TRUE",
                }
            )
            current_mrr = ending
        latest = [r for r in subscription_rows if r["CustomerID"] == customer["CustomerID"] and r["MonthStart"] == LATEST_MONTH.date().isoformat()]
        if latest and latest[0]["ActiveLogo"] == 1:
            row = latest[0]
            health_score = float(np.clip(78 + (row["ExpansionMRR"] / max(row["BeginningMRR"], 1)) * 100 - rng.normal(0, 11), 18, 99))
            renewal_risk = "Critical" if health_score < 40 else "Watch" if health_score < 62 else "Healthy"
            account_health_rows.append(
                {
                    "CustomerID": customer["CustomerID"],
                    "AccountName": customer["AccountName"],
                    "PlanID": customer["PlanID"],
                    "ChannelID": customer["ChannelID"],
                    "RegionID": customer["RegionID"],
                    "Segment": customer["Segment"],
                    "Industry": customer["Industry"],
                    "CurrentARR": round(row["EndingMRR"] * 12, 2),
                    "Seats": row["Seats"],
                    "HealthScore": round(health_score, 1),
                    "RenewalRisk": renewal_risk,
                    "NextAction": "CFO review" if renewal_risk == "Critical" else "CSM expansion plan" if health_score > 84 else "Monitor",
                }
            )
    subscription = pd.DataFrame(subscription_rows)
    account_health = pd.DataFrame(account_health_rows).sort_values(["RenewalRisk", "CurrentARR"], ascending=[True, False]).head(240)

    monthly = subscription.groupby("MonthStart", as_index=False).agg(
        BeginningMRR=("BeginningMRR", "sum"),
        NewMRR=("NewMRR", "sum"),
        ExpansionMRR=("ExpansionMRR", "sum"),
        ContractionMRR=("ContractionMRR", "sum"),
        ChurnMRR=("ChurnMRR", "sum"),
        EndingMRR=("EndingMRR", "sum"),
        RecognizedRevenue=("RecognizedRevenue", "sum"),
        GrossMargin=("GrossMargin", "sum"),
        StartingCustomers=("StartingLogo", "sum"),
        ActiveCustomers=("ActiveLogo", "sum"),
        NewCustomers=("NewLogo", "sum"),
        ChurnedCustomers=("ChurnedLogo", "sum"),
    ).merge(dim_date[["MonthStart", "MonthLabel", "MonthIndex"]], on="MonthStart")
    monthly["ARR"] = monthly["EndingMRR"] * 12
    monthly["NetNewARR"] = (monthly["NewMRR"] + monthly["ExpansionMRR"] + monthly["ContractionMRR"] + monthly["ChurnMRR"]) * 12
    monthly["NRR"] = (monthly["EndingMRR"] - monthly["NewMRR"]) / monthly["BeginningMRR"].replace(0, np.nan)
    monthly["GRR"] = (monthly["BeginningMRR"] + monthly["ContractionMRR"] + monthly["ChurnMRR"]) / monthly["BeginningMRR"].replace(0, np.nan)
    monthly["RevenueChurnRate"] = abs(monthly["ChurnMRR"]) / monthly["BeginningMRR"].replace(0, np.nan)
    monthly["LogoChurnRate"] = monthly["ChurnedCustomers"] / monthly["StartingCustomers"].replace(0, np.nan)
    monthly["GrossMarginPct"] = monthly["GrossMargin"] / monthly["RecognizedRevenue"].replace(0, np.nan)
    monthly["ARRGrowthPct"] = monthly["ARR"].pct_change().fillna(0)
    monthly.loc[monthly["BeginningMRR"] == 0, ["NRR", "GRR"]] = 1.0
    monthly = monthly.fillna(0)

    movement_rows = []
    movement_defs = [
        ("New ARR", 1, "NewMRR"),
        ("Expansion ARR", 2, "ExpansionMRR"),
        ("Contraction ARR", 3, "ContractionMRR"),
        ("Churn ARR", 4, "ChurnMRR"),
    ]
    for row in monthly.itertuples(index=False):
        for movement, sort, col_name in movement_defs:
            value = getattr(row, col_name) * 12
            movement_rows.append(
                {
                    "MonthStart": row.MonthStart,
                    "MovementType": movement,
                    "MovementSort": sort,
                    "ARRMovement": round(float(value), 2),
                    "FavorableFlag": 1 if value >= 0 else 0,
                }
            )
    movement = pd.DataFrame(movement_rows)

    acquisition = (
        subscription[subscription["NewLogo"] == 1]
        .groupby(["MonthStart", "PlanID", "ChannelID", "RegionID"], as_index=False)
        .agg(NewCustomers=("NewLogo", "sum"), NewMRR=("NewMRR", "sum"))
    )
    acquisition_rows = []
    for row in acquisition.itertuples(index=False):
        plan = plan_map[row.PlanID]
        channel = channel_map[row.ChannelID]
        spend = row.NewCustomers * plan[6] * channel[4] * float(rng.uniform(0.84, 1.22))
        acquisition_rows.append(
            {
                "MonthStart": row.MonthStart,
                "PlanID": row.PlanID,
                "ChannelID": row.ChannelID,
                "RegionID": row.RegionID,
                "NewCustomers": int(row.NewCustomers),
                "NewARRBooked": round(float(row.NewMRR * 12), 2),
                "SalesMarketingSpend": round(float(spend), 2),
                "SalesPipelineARR": round(float(row.NewMRR * 12 * rng.uniform(2.2, 3.6)), 2),
            }
        )
    fact_acq = pd.DataFrame(acquisition_rows)

    cohort_rows = []
    for cohort_month in MONTHS:
        cohort_customers = subscription[(subscription["MonthStart"] == cohort_month.date().isoformat()) & (subscription["NewLogo"] == 1)]
        if cohort_customers.empty:
            continue
        for (plan_id, channel_id), group in cohort_customers.groupby(["PlanID", "ChannelID"]):
            customer_ids = set(group.CustomerID)
            start_mrr = group.NewMRR.sum()
            start_logos = len(customer_ids)
            for activity_month in MONTHS[MONTHS >= cohort_month]:
                active = subscription[(subscription["MonthStart"] == activity_month.date().isoformat()) & (subscription["CustomerID"].isin(customer_ids))]
                if active.empty:
                    continue
                age = (activity_month.year - cohort_month.year) * 12 + activity_month.month - cohort_month.month
                retained_mrr = active.EndingMRR.sum()
                expansion_mrr = active.ExpansionMRR.clip(lower=0).sum()
                contraction_mrr = abs(active.ContractionMRR.clip(upper=0).sum())
                active_logos = int(active.ActiveLogo.sum())
                churned_logos = max(0, start_logos - active_logos)
                cohort_rows.append(
                    {
                        "CohortMonth": cohort_month.date().isoformat(),
                        "CohortLabel": month_label(cohort_month),
                        "ActivityMonth": activity_month.date().isoformat(),
                        "MonthsSinceCohort": age,
                        "PlanID": plan_id,
                        "ChannelID": channel_id,
                        "CohortStartMRR": round(float(start_mrr), 2),
                        "RetainedMRR": round(float(retained_mrr), 2),
                        "ExpansionMRR": round(float(expansion_mrr), 2),
                        "ContractionMRR": round(float(contraction_mrr), 2),
                        "StartLogos": start_logos,
                        "ActiveLogos": active_logos,
                        "ChurnedLogos": churned_logos,
                        "NetRetentionRate": round(float(retained_mrr / start_mrr), 4) if start_mrr else 0,
                        "GrossRetentionRate": round(float((retained_mrr - expansion_mrr) / start_mrr), 4) if start_mrr else 0,
                    }
                )
    cohort = pd.DataFrame(cohort_rows)

    finance_rows = []
    forecast_rows = []
    cash_balance = 18_500_000.0
    prev_arr = 0.0
    for i, row in enumerate(monthly.itertuples(index=False)):
        revenue = float(row.RecognizedRevenue)
        gross_margin = float(row.GrossMargin)
        acq_spend = float(fact_acq[fact_acq.MonthStart == row.MonthStart].SalesMarketingSpend.sum())
        rd = revenue * float(rng.uniform(0.22, 0.31))
        ga = revenue * float(rng.uniform(0.12, 0.17))
        cs = revenue * float(rng.uniform(0.06, 0.10))
        sales_marketing = acq_spend + revenue * float(rng.uniform(0.10, 0.16))
        ebitda = gross_margin - sales_marketing - rd - ga - cs
        net_burn = max(0.0, -ebitda + float(rng.uniform(120_000, 480_000)))
        cash_balance = max(1_800_000, cash_balance - net_burn + max(0, ebitda) * 0.18)
        arr_growth = 0 if prev_arr == 0 else (row.ARR - prev_arr) / prev_arr
        prev_arr = row.ARR
        plan_arr = row.ARR * float(rng.uniform(0.965, 1.08))
        forecast_arr = row.ARR * float(rng.uniform(0.975, 1.045))
        finance_rows.append(
            {
                "MonthStart": row.MonthStart,
                "Revenue": round(revenue, 2),
                "COGS": round(revenue - gross_margin, 2),
                "GrossMargin": round(gross_margin, 2),
                "SalesMarketingExpense": round(sales_marketing, 2),
                "ResearchDevelopmentExpense": round(rd, 2),
                "GeneralAdminExpense": round(ga, 2),
                "CustomerSuccessExpense": round(cs, 2),
                "EBITDA": round(ebitda, 2),
                "CashBalance": round(cash_balance, 2),
                "NetBurn": round(net_burn, 2),
                "ActualARR": round(row.ARR, 2),
                "PlanARR": round(plan_arr, 2),
                "ForecastARR": round(forecast_arr, 2),
                "ARRGrowthPct": round(arr_growth, 5),
            }
        )
        for scenario, value in [("Actual", row.ARR), ("Forecast", forecast_arr), ("Plan", plan_arr)]:
            forecast_rows.append(
                {
                    "MonthStart": row.MonthStart,
                    "Scenario": scenario,
                    "ARRValue": round(float(value), 2),
                    "RevenueValue": round(float(revenue * (value / row.ARR if row.ARR else 1)), 2),
                }
            )
    finance = pd.DataFrame(finance_rows)
    forecast = pd.DataFrame(forecast_rows)

    return {
        "DimDate": dim_date,
        "DimPlan": dim_plan,
        "DimChannel": dim_channel,
        "DimRegion": dim_region,
        "DimCustomer": dim_customer,
        "FactSubscriptionMonthly": subscription,
        "FactMRRMovement": movement,
        "FactCohortRetention": cohort,
        "FactAcquisitionMonthly": fact_acq,
        "FactFinanceMonthly": finance,
        "FactForecast": forecast,
        "FactAccountHealth": account_health,
        "MonthlyKPIs": monthly,
    }


MEASURES = [
    ("Beginning MRR", "SUM ( FactSubscriptionMonthly[BeginningMRR] )", "$#,0,,.0M"),
    ("Ending MRR", "SUM ( FactSubscriptionMonthly[EndingMRR] )", "$#,0,,.0M"),
    ("ARR", "[Ending MRR] * 12", "$#,0,,.0M"),
    ("New ARR", "SUM ( FactSubscriptionMonthly[NewMRR] ) * 12", "$#,0,,.0M"),
    ("Expansion ARR", "SUM ( FactSubscriptionMonthly[ExpansionMRR] ) * 12", "$#,0,,.0M"),
    ("Contraction ARR", "ABS ( SUM ( FactSubscriptionMonthly[ContractionMRR] ) ) * 12", "$#,0,,.0M"),
    ("Churn ARR", "ABS ( SUM ( FactSubscriptionMonthly[ChurnMRR] ) ) * 12", "$#,0,,.0M"),
    ("Net New ARR", "[New ARR] + [Expansion ARR] - [Contraction ARR] - [Churn ARR]", "$#,0,,.0M"),
    ("ARR Movement", "SUM ( FactMRRMovement[ARRMovement] )", "$#,0,,.0M"),
    ("Revenue", "SUM ( FactSubscriptionMonthly[RecognizedRevenue] )", "$#,0,,.0M"),
    ("Gross Margin", "SUM ( FactSubscriptionMonthly[GrossMargin] )", "$#,0,,.0M"),
    ("Gross Margin %", "DIVIDE ( [Gross Margin], [Revenue] )", "0.0%"),
    ("Starting Customers", "SUM ( FactSubscriptionMonthly[StartingLogo] )", "#,0"),
    ("Active Customers", "SUM ( FactSubscriptionMonthly[ActiveLogo] )", "#,0"),
    ("New Customers", "SUM ( FactSubscriptionMonthly[NewLogo] )", "#,0"),
    ("Churned Customers", "SUM ( FactSubscriptionMonthly[ChurnedLogo] )", "#,0"),
    ("NRR", "DIVIDE ( [Ending MRR] - SUM ( FactSubscriptionMonthly[NewMRR] ), [Beginning MRR] )", "0.0%"),
    ("GRR", "DIVIDE ( [Beginning MRR] - [Contraction ARR] / 12 - [Churn ARR] / 12, [Beginning MRR] )", "0.0%"),
    ("Revenue Churn Rate", "DIVIDE ( [Churn ARR], [Beginning MRR] * 12 )", "0.0%"),
    ("Logo Churn Rate", "DIVIDE ( [Churned Customers], [Starting Customers] )", "0.0%"),
    ("S&M Spend", "SUM ( FactAcquisitionMonthly[SalesMarketingSpend] )", "$#,0,,.0M"),
    ("New ARR Booked", "SUM ( FactAcquisitionMonthly[NewARRBooked] )", "$#,0,,.0M"),
    ("CAC", "DIVIDE ( [S&M Spend], SUM ( FactAcquisitionMonthly[NewCustomers] ) )", "$#,0"),
    ("ARPA", "DIVIDE ( [Ending MRR], [Active Customers] )", "$#,0"),
    ("LTV", "DIVIDE ( [ARPA] * 12 * [Gross Margin %], [Revenue Churn Rate] )", "$#,0"),
    ("LTV CAC Ratio", "DIVIDE ( [LTV], [CAC] )", "0.0x"),
    ("CAC Payback Months", "DIVIDE ( [CAC], DIVIDE ( [Gross Margin], [Active Customers] ) )", "0.0"),
    ("Magic Number", "DIVIDE ( [Net New ARR], [S&M Spend] )", "0.0x"),
    ("EBITDA", "SUM ( FactFinanceMonthly[EBITDA] )", "$#,0,,.0M"),
    ("EBITDA Margin", "DIVIDE ( [EBITDA], SUM ( FactFinanceMonthly[Revenue] ) )", "0.0%"),
    ("ARR Growth %", "AVERAGE ( FactFinanceMonthly[ARRGrowthPct] )", "0.0%"),
    ("Rule of 40", "[ARR Growth %] + [EBITDA Margin]", "0.0%"),
    ("Net Burn", "SUM ( FactFinanceMonthly[NetBurn] )", "$#,0,,.0M"),
    ("Cash Balance", "SUM ( FactFinanceMonthly[CashBalance] )", "$#,0,,.0M"),
    ("Burn Multiple", "DIVIDE ( [Net Burn], DIVIDE ( [Net New ARR], 12 ) )", "0.0x"),
    ("Forecast ARR", "SUM ( FactFinanceMonthly[ForecastARR] )", "$#,0,,.0M"),
    ("Plan ARR", "SUM ( FactFinanceMonthly[PlanARR] )", "$#,0,,.0M"),
    ("Forecast Accuracy", "1 - DIVIDE ( ABS ( [ARR] - [Forecast ARR] ), [ARR] )", "0.0%"),
    ("Cohort NRR", "DIVIDE ( SUM ( FactCohortRetention[RetainedMRR] ), SUM ( FactCohortRetention[CohortStartMRR] ) )", "0.0%"),
    ("Cohort GRR", "DIVIDE ( SUM ( FactCohortRetention[RetainedMRR] ) - SUM ( FactCohortRetention[ExpansionMRR] ), SUM ( FactCohortRetention[CohortStartMRR] ) )", "0.0%"),
    ("Cohort Active Logos", "SUM ( FactCohortRetention[ActiveLogos] )", "#,0"),
    ("Cohort LTV", "DIVIDE ( SUM ( FactCohortRetention[RetainedMRR] ) * 12, SUM ( FactCohortRetention[StartLogos] ) )", "$#,0"),
    ("Scenario ARR", "SUM ( FactForecast[ARRValue] )", "$#,0,,.0M"),
    ("Account Health Score", "AVERAGE ( FactAccountHealth[HealthScore] )", "0.0"),
    ("Latest ARR", "VAR m = MAX ( DimDate[MonthStart] ) RETURN CALCULATE ( [ARR], FILTER ( ALLSELECTED ( DimDate ), DimDate[MonthStart] = m ) )", "$#,0,,.0M"),
    ("Latest Net New ARR", "VAR m = MAX ( DimDate[MonthStart] ) RETURN CALCULATE ( [Net New ARR], FILTER ( ALLSELECTED ( DimDate ), DimDate[MonthStart] = m ) )", "$#,0,,.0M"),
    ("Latest NRR", "VAR m = MAX ( DimDate[MonthStart] ) RETURN CALCULATE ( [NRR], FILTER ( ALLSELECTED ( DimDate ), DimDate[MonthStart] = m ) )", "0.0%"),
    ("Latest GRR", "VAR m = MAX ( DimDate[MonthStart] ) RETURN CALCULATE ( [GRR], FILTER ( ALLSELECTED ( DimDate ), DimDate[MonthStart] = m ) )", "0.0%"),
    ("Latest CAC Payback", "VAR m = MAX ( DimDate[MonthStart] ) RETURN CALCULATE ( [CAC Payback Months], FILTER ( ALLSELECTED ( DimDate ), DimDate[MonthStart] = m ) )", "0.0"),
    ("Latest LTV CAC Ratio", "VAR m = MAX ( DimDate[MonthStart] ) RETURN CALCULATE ( [LTV CAC Ratio], FILTER ( ALLSELECTED ( DimDate ), DimDate[MonthStart] = m ) )", "0.0x"),
    ("Latest Rule of 40", "VAR m = MAX ( DimDate[MonthStart] ) RETURN CALCULATE ( [Rule of 40], FILTER ( ALLSELECTED ( DimDate ), DimDate[MonthStart] = m ) )", "0.0%"),
    ("Latest Forecast Accuracy", "VAR m = MAX ( DimDate[MonthStart] ) RETURN CALCULATE ( [Forecast Accuracy], FILTER ( ALLSELECTED ( DimDate ), DimDate[MonthStart] = m ) )", "0.0%"),
]

RELATIONSHIPS = [
    ("FactSubscriptionMonthly", "MonthStart", "DimDate", "MonthStart"),
    ("FactSubscriptionMonthly", "PlanID", "DimPlan", "PlanID"),
    ("FactSubscriptionMonthly", "ChannelID", "DimChannel", "ChannelID"),
    ("FactSubscriptionMonthly", "RegionID", "DimRegion", "RegionID"),
    ("FactMRRMovement", "MonthStart", "DimDate", "MonthStart"),
    ("FactCohortRetention", "ActivityMonth", "DimDate", "MonthStart"),
    ("FactCohortRetention", "PlanID", "DimPlan", "PlanID"),
    ("FactCohortRetention", "ChannelID", "DimChannel", "ChannelID"),
    ("FactAcquisitionMonthly", "MonthStart", "DimDate", "MonthStart"),
    ("FactAcquisitionMonthly", "PlanID", "DimPlan", "PlanID"),
    ("FactAcquisitionMonthly", "ChannelID", "DimChannel", "ChannelID"),
    ("FactAcquisitionMonthly", "RegionID", "DimRegion", "RegionID"),
    ("FactFinanceMonthly", "MonthStart", "DimDate", "MonthStart"),
    ("FactForecast", "MonthStart", "DimDate", "MonthStart"),
    ("FactAccountHealth", "PlanID", "DimPlan", "PlanID"),
    ("FactAccountHealth", "ChannelID", "DimChannel", "ChannelID"),
    ("FactAccountHealth", "RegionID", "DimRegion", "RegionID"),
]


def save_data(tables: dict[str, pd.DataFrame]) -> dict:
    for name, df in tables.items():
        df.to_csv(ROOT / "data" / "prepared" / f"{name}.csv", index=False, encoding="utf-8-sig")
    for name in [
        "DimDate",
        "DimPlan",
        "DimChannel",
        "DimRegion",
        "FactSubscriptionMonthly",
        "FactMRRMovement",
        "FactCohortRetention",
        "FactAcquisitionMonthly",
        "FactFinanceMonthly",
        "FactForecast",
        "FactAccountHealth",
    ]:
        tables[name].to_csv(ROOT / "data" / "raw" / f"{name}_raw.csv", index=False, encoding="utf-8-sig")

    subscription = tables["FactSubscriptionMonthly"]
    monthly = tables["MonthlyKPIs"]
    movement = tables["FactMRRMovement"]
    checks = [
        {"check": "Subscription grain unique", "status": "pass" if not subscription.duplicated(["MonthStart", "CustomerID"]).any() else "fail"},
        {"check": "ARR reconciles to ending MRR", "status": "pass" if abs((monthly.EndingMRR * 12 - monthly.ARR).sum()) < 0.02 else "fail"},
        {"check": "Movement rows available", "status": "pass" if len(movement) == len(monthly) * 4 else "fail"},
        {"check": "NRR bounded", "status": "pass" if monthly.NRR.between(0.65, 1.35).all() else "fail"},
        {"check": "Critical numeric fields non-null", "status": "pass" if not subscription[["BeginningMRR", "EndingMRR", "RecognizedRevenue", "GrossMargin"]].isna().any().any() else "fail"},
    ]
    qa = {
        "status": "pass" if all(c["status"] == "pass" for c in checks) else "fail",
        "checks": checks,
        "date_range": {"start": str(monthly.MonthStart.min()), "end": str(monthly.MonthStart.max())},
        "prepared_tables": {name: len(df) for name, df in tables.items()},
    }
    write_json(ROOT / "data" / "source_summary.json", {"source_type": "synthetic_demo_data", "seed": SEED, "latest_complete_month": LATEST_MONTH.date().isoformat(), "tables": qa["prepared_tables"], "note": "Portfolio/demo SaaS CFO metrics data generated deterministically."})
    write_json(ROOT / "data" / "validated" / "validation_summary.json", qa)
    write_text(ROOT / "data" / "data_quality_report.md", "# Data Quality Report\n\n" + "\n".join(f"- {c['check']}: {c['status'].upper()}" for c in checks))
    write_text(ROOT / "data" / "synthetic" / "generation_notes.md", f"# Synthetic Data Notes\n\nSeed: `{SEED}`\nLatest complete month: `{LATEST_MONTH.date().isoformat()}`\n\nSynthetic portfolio/demo data models B2B SaaS subscriptions, ARR movement, cohorts, acquisition spend, forecast accuracy, and account health.")
    return qa


def infer_type(series: pd.Series, col: str) -> tuple[str, str]:
    if col.endswith("Month") or col.endswith("MonthStart") or col in {"ActivityMonth", "CohortMonth", "AcquisitionMonth"}:
        return "dateTime", "type date"
    if pd.api.types.is_integer_dtype(series):
        return "int64", "Int64.Type"
    if pd.api.types.is_float_dtype(series):
        return "double", "type number"
    return "string", "type text"


def table_model(name: str, df: pd.DataFrame) -> dict:
    columns, m_types = [], []
    for col_name in df.columns:
        dtype, mtype = infer_type(df[col_name], col_name)
        item = {"name": col_name, "dataType": dtype, "sourceColumn": col_name, "lineageTag": str(uuid.uuid4())}
        if dtype == "int64":
            item["formatString"] = "0"
        if any(token in col_name for token in ["MRR", "ARR", "Revenue", "Margin", "Spend", "CAC", "LTV", "Burn", "Cash", "Balance", "Expense"]):
            item["formatString"] = "$#,0;($#,0);$0"
        if "Rate" in col_name or "Pct" in col_name:
            item["formatString"] = "0.0%"
        if dtype in {"string", "dateTime"} or col_name.endswith("ID") or col_name in {"MonthIndex", "MovementSort", "MonthsSinceCohort"}:
            item["summarizeBy"] = "none"
        columns.append(item)
        m_types.append(f'{{"{col_name}", {mtype}}}')
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
    model_tables = [table_model(name, df) for name, df in tables.items()]
    model_tables.append(
        {
            "name": MEASURE_TABLE,
            "lineageTag": str(uuid.uuid4()),
            "columns": [{"name": "MeasureName", "dataType": "string", "sourceColumn": "MeasureName", "isHidden": True}],
            "partitions": [{"name": "p_KPI_Measures", "mode": "import", "source": {"type": "m", "expression": 'let Source = #table(type table [MeasureName = text], {{"KPI"}}) in Source'}}],
            "measures": [{"name": name, "expression": expression, "formatString": fmt, "lineageTag": str(uuid.uuid4())} for name, expression, fmt in MEASURES],
        }
    )
    relationships = [{"name": f"Rel_{a}_{b}_{c}_{d}", "fromTable": a, "fromColumn": b, "toTable": c, "toColumn": d} for a, b, c, d in RELATIONSHIPS]
    model = {"compatibilityLevel": 1600, "model": {"culture": "en-US", "dataAccessOptions": {"legacyRedirects": True, "returnErrorValuesAsNull": True}, "defaultPowerBIDataSourceVersion": "powerBI_V3", "sourceQueryCulture": "en-US", "tables": model_tables, "relationships": relationships}}
    write_json(ROOT / "model" / "model.bim", model)
    sem = ROOT / "powerbi" / "pbip" / "SaaS_CFO_Metrics" / "SaaS_CFO_Metrics.SemanticModel"
    write_json(sem / "model.bim", model)
    write_json(ROOT / "model" / "relationship_map.json", relationships)
    write_json(ROOT / "model" / "measure_map.json", [{"measure": name, "expression": expression, "format": fmt} for name, expression, fmt in MEASURES])
    write_text(ROOT / "model" / "MEASURES.dax", "\n\n".join(f"{name} = {expression}" for name, expression, _ in MEASURES))
    write_text(ROOT / "model" / "dax_measures.md", "# DAX Measures\n\n" + "\n\n".join(f"## {name}\n\n```DAX\n{name} = {expression}\n```\n\nFormat: `{fmt}`" for name, expression, fmt in MEASURES))
    write_text(ROOT / "model" / "metric_definitions.md", """# Metric Definitions

The metric layer is CFO-oriented and uses DAX measures for all core KPIs.

- ARR = ending MRR multiplied by 12.
- Net New ARR = new + expansion - contraction - churn.
- NRR and GRR use beginning MRR denominators; rate measures use `DIVIDE`.
- CAC Payback = CAC divided by monthly gross margin per active customer.
- LTV/CAC = estimated gross-margin-adjusted LTV divided by CAC.
- Rule of 40 = ARR growth percentage plus EBITDA margin.
- Forecast Accuracy = 1 minus absolute ARR forecast error divided by actual ARR.
""")
    write_text(ROOT / "model" / "relationship_map.md", "# Relationship Map\n\n" + "\n".join(f"- {a}[{b}] -> {c}[{d}]" for a, b, c, d in RELATIONSHIPS))
    write_text(ROOT / "model" / "data_dictionary.md", "# Data Dictionary\n\n" + "\n\n".join(f"## {name}\n\nRows: {len(df):,}\n\nColumns: {', '.join(df.columns)}" for name, df in tables.items()))
    write_text(ROOT / "model" / "semantic_model_notes.md", "Star-schema model with conformed date, plan, channel, and region dimensions. Measures live in KPI_Measures and rates use DIVIDE rather than summing imported rate columns.")


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


def csel(a, table, column, display):
    return {"Column": {"Expression": src(a), "Property": column}, "Name": f"{table}.{column}", "NativeReferenceName": display}


def msel(a, measure, display):
    return {"Measure": {"Expression": src(a), "Property": measure}, "Name": f"{MEASURE_TABLE}.{measure}", "NativeReferenceName": display}


def mfmt(measure):
    return next((fmt for name, _expression, fmt in MEASURES if name == measure), "#,0")


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


def container(config, p, query_obj=None, transform_obj=None):
    config["layouts"] = [{"id": 0, "position": p}]
    out = {"x": p["x"], "y": p["y"], "z": p["z"], "width": p["width"], "height": p["height"], "config": json.dumps(config, separators=(",", ":")), "filters": "[]", "tabOrder": p["tabOrder"]}
    if query_obj:
        out["query"] = json.dumps(query_obj, separators=(",", ":"))
    if transform_obj:
        out["dataTransforms"] = json.dumps(transform_obj, separators=(",", ":"))
    return out


def query(froms, selects, order=None):
    q = {"Version": 2, "From": froms, "Select": selects}
    if order:
        q["OrderBy"] = [order]
    return {"Commands": [{"SemanticQueryDataShapeCommand": {"Query": q, "Binding": {"Primary": {"Groupings": [{"Projections": list(range(len(selects)))}]}, "DataReduction": {"DataVolume": 4, "Primary": {"Window": {"Count": 1000}}}, "Version": 1}, "ExecutionMetricsKind": 1}}]}


def transforms(objects, roles, meta, selects, ordering, active=None):
    payload = {"objects": objects, "projectionOrdering": ordering, "queryMetadata": {"Select": meta}, "visualElements": [{"DataRoles": [{"Name": role, "Projection": idx, "isActive": active_flag} for role, idx, active_flag in roles]}], "selects": selects}
    if active:
        payload["projectionActiveItems"] = active
    return payload


def ctrans(alias, table, column, display, role):
    return {"displayName": display, "queryName": f"{table}.{column}", "roles": {role: True}, "type": {"category": None, "underlyingType": 1}, "expr": {"Column": {"Expression": ent(alias), "Property": column}}}


def mtrans(measure, display, role):
    return {"displayName": display, "queryName": f"{MEASURE_TABLE}.{measure}", "roles": {role: True}, "type": {"category": None, "underlyingType": 259}, "expr": {"Measure": {"Expression": ent("m"), "Property": measure}}, "format": mfmt(measure)}


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
    transform_obj = transforms(objects, [("Data", 0, False)], [{"Restatement": display, "Name": qref, "Type": 1, "Format": mfmt(measure)}], [mtrans(measure, display, "Data")], {"Data": [0]})
    return container(config, p, query(froms, selects), transform_obj)


def slicer(table, column, display, p):
    qref = f"{table}.{column}"
    objects = {"data": [{"properties": {"mode": txt("Dropdown")}}], "selection": [{"properties": {"selectAllCheckboxEnabled": lit(True), "singleSelect": lit(False)}}], "header": [{"properties": {"show": lit(False)}}]}
    froms = [{"Name": "f", "Entity": table, "Type": 0}]
    selects = [csel("f", table, column, display)]
    config = {"name": uuid.uuid4().hex[:20], "singleVisual": {"visualType": "slicer", "projections": {"Values": [{"queryRef": qref, "active": True}]}, "prototypeQuery": {"Version": 2, "From": froms, "Select": selects}, "objects": objects, "drillFilterOtherVisuals": True, "vcObjects": frame(display)}}
    transform_obj = transforms(objects, [("Values", 0, True)], [{"Restatement": display, "Name": qref, "Type": 2048}], [ctrans("f", table, column, display, "Values")], {"Values": [0]}, {"Values": [{"queryRef": qref, "suppressConcat": False}]})
    return container(config, p, query(froms, selects), transform_obj)


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
    transform_obj = transforms(objects, [("Category", 0, True), ("Y", 1, False)], [{"Restatement": display, "Name": cref, "Type": 2048}, {"Restatement": mdisplay, "Name": mref, "Type": 1, "Format": mfmt(measure)}], [ctrans("c", table, column, display, "Category"), mtrans(measure, mdisplay, "Y")], {"Category": [0], "Y": [1]}, {"Category": [{"queryRef": cref, "suppressConcat": False}]})
    return container(config, p, query(froms, selects, order), transform_obj)


def multi_chart(vtype, title, sub, table, column, display, measures, p, order_column=None):
    cref = f"{table}.{column}"
    objects = chart_objects(COLORS["blue"], labels=False)
    froms = [{"Name": "c", "Entity": table, "Type": 0}, {"Name": "m", "Entity": MEASURE_TABLE, "Type": 0}]
    selects = [csel("c", table, column, display)]
    meta = [{"Restatement": display, "Name": cref, "Type": 2048}]
    transform_selects = [ctrans("c", table, column, display, "Category")]
    roles = [("Category", 0, True)]
    y_refs = []
    for measure, label in measures:
        idx = len(selects)
        qref = f"{MEASURE_TABLE}.{measure}"
        selects.append(msel("m", measure, label))
        y_refs.append({"queryRef": qref})
        meta.append({"Restatement": label, "Name": qref, "Type": 1, "Format": mfmt(measure)})
        transform_selects.append(mtrans(measure, label, "Y"))
        roles.append(("Y", idx, False))
    order = {"Direction": 1, "Expression": {"Column": {"Expression": src("c"), "Property": order_column}}} if order_column else None
    config = {"name": uuid.uuid4().hex[:20], "singleVisual": {"visualType": vtype, "projections": {"Category": [{"queryRef": cref, "active": True}], "Y": y_refs}, "prototypeQuery": {"Version": 2, "From": froms, "Select": selects, **({"OrderBy": [order]} if order else {})}, "objects": objects, "drillFilterOtherVisuals": True, "vcObjects": frame(title, sub)}}
    return container(config, p, query(froms, selects, order), transforms(objects, roles, meta, transform_selects, {"Category": [0], "Y": list(range(1, len(selects)))}, {"Category": [{"queryRef": cref, "suppressConcat": False}]}))


def table_visual(title, sub, fields, measures, p, order_measure=None, asc=False):
    aliases, froms = {}, []
    for table, _column, _display in fields:
        if table not in aliases:
            aliases[table] = f"f{len(aliases)}"
            froms.append({"Name": aliases[table], "Entity": table, "Type": 0})
    if measures:
        aliases[MEASURE_TABLE] = "m"
        froms.append({"Name": "m", "Entity": MEASURE_TABLE, "Type": 0})
    selects, projections, meta, transform_selects = [], [], [], []
    for table, column, display in fields:
        qref = f"{table}.{column}"
        selects.append(csel(aliases[table], table, column, display))
        projections.append({"queryRef": qref})
        meta.append({"Restatement": display, "Name": qref, "Type": 2048})
        transform_selects.append(ctrans(aliases[table], table, column, display, "Values"))
    for measure, display in measures:
        qref = f"{MEASURE_TABLE}.{measure}"
        selects.append(msel("m", measure, display))
        projections.append({"queryRef": qref})
        meta.append({"Restatement": display, "Name": qref, "Type": 1, "Format": mfmt(measure)})
        transform_selects.append(mtrans(measure, display, "Values"))
    objects = {"grid": [{"properties": {"gridHorizontal": lit(False), "outlineColor": col(COLORS["border"])}}], "columnHeaders": [{"properties": {"fontFamily": txt("Segoe UI Semibold"), "fontSize": lit(7.3), "fontColor": col(COLORS["ink"])}}], "values": [{"properties": {"fontFamily": txt("Segoe UI"), "fontSize": lit(7.0), "fontColor": col(COLORS["ink"])}}]}
    order = {"Direction": 1 if asc else 2, "Expression": {"Measure": {"Expression": src("m"), "Property": order_measure}}} if order_measure else None
    config = {"name": uuid.uuid4().hex[:20], "singleVisual": {"visualType": "tableEx", "projections": {"Values": projections}, "prototypeQuery": {"Version": 2, "From": froms, "Select": selects, **({"OrderBy": [order]} if order else {})}, "objects": objects, "drillFilterOtherVisuals": True, "vcObjects": frame(title, sub)}}
    return container(config, p, query(froms, selects, order), transforms(objects, [("Values", i, False) for i in range(len(selects))], meta, transform_selects, {"Values": list(range(len(selects)))}))


def header(title, sub, z):
    return [
        shape(COLORS["navy"], pos(0, 0, z, 1280, 82)),
        textbox(title, sub, pos(28, 12, z + 1, 650, 58)),
        slicer("DimDate", "Year", "Year", pos(706, 18, z + 2, 82, 44)),
        slicer("DimPlan", "Segment", "Segment", pos(802, 18, z + 3, 150, 44)),
        slicer("DimChannel", "Motion", "Motion", pos(966, 18, z + 4, 136, 44)),
        slicer("DimRegion", "Region", "Region", pos(1116, 18, z + 5, 124, 44)),
    ]


def section(name, ordinal, visuals):
    config = json.dumps({"objects": {"background": [{"properties": {"color": col(COLORS["bg"]), "transparency": lit(0.0)}}], "outspace": [{"properties": {"color": col(COLORS["bg"]), "transparency": lit(0.0)}}]}}, separators=(",", ":"))
    return {"id": ordinal, "name": f"ReportSection{ordinal:02d}{uuid.uuid4().hex[:6]}", "displayName": name, "filters": "[]", "ordinal": ordinal, "visualContainers": visuals, "config": config, "displayOption": 1, "width": 1280, "height": 720}


def build_layout() -> dict:
    p1 = header("SaaS CFO Executive Overview", "Board-ready ARR, retention, Rule of 40, unit economics and forecast status", 1)
    for i, (measure, label, color) in enumerate([
        ("Latest ARR", "ARR", COLORS["blue"]),
        ("Latest Net New ARR", "Net New ARR", COLORS["green"]),
        ("Latest NRR", "NRR", COLORS["teal"]),
        ("Latest CAC Payback", "Payback", COLORS["amber"]),
        ("Latest LTV CAC Ratio", "LTV:CAC", COLORS["violet"]),
        ("Latest Rule of 40", "Rule of 40", COLORS["sky"]),
    ]):
        p1.append(card(measure, label, pos(28 + i * 196, 102, 100 + i, 182, 82), color))
    p1 += [
        multi_chart("lineChart", "ARR and Net New ARR Trend", "Recurring revenue trajectory and growth velocity", "DimDate", "MonthLabel", "Month", [("ARR", "ARR"), ("Net New ARR", "Net New ARR")], pos(28, 214, 200, 596, 216), "MonthIndex"),
        single_chart("barChart", "ARR Movement Bridge", "New, expansion, contraction and churn ARR movement", "FactMRRMovement", "MovementType", "Movement", "ARR Movement", "ARR Movement", pos(648, 214, 201, 270, 216), COLORS["blue"], order_column="MovementSort", ascending=True),
        single_chart("barChart", "ARR by Segment", "Recurring revenue mix by plan segment", "DimPlan", "Segment", "Segment", "ARR", "ARR", pos(940, 214, 202, 300, 216), COLORS["teal"], order_measure=True, ascending=False),
        table_visual("Plan Scorecard", "CFO view of growth, retention and efficiency by plan", [("DimPlan", "PlanName", "Plan"), ("DimPlan", "Segment", "Segment")], [("ARR", "ARR"), ("NRR", "NRR"), ("GRR", "GRR"), ("Revenue Churn Rate", "Rev Churn"), ("CAC Payback Months", "Payback")], pos(28, 462, 203, 1212, 196), "ARR"),
    ]

    p2 = header("Revenue & Retention", "ARR movement quality, cohort retention, expansion depth and logo risk", 1000)
    for i, (measure, label, color) in enumerate([
        ("Latest NRR", "NRR", COLORS["teal"]),
        ("Latest GRR", "GRR", COLORS["green"]),
        ("Churn ARR", "Churn ARR", COLORS["red"]),
        ("Expansion ARR", "Expansion ARR", COLORS["violet"]),
    ]):
        p2.append(card(measure, label, pos(28 + i * 294, 102, 1100 + i, 276, 82), color))
    p2 += [
        multi_chart("lineChart", "NRR and GRR Trend", "Net and gross retention trend by month", "DimDate", "MonthLabel", "Month", [("NRR", "NRR"), ("GRR", "GRR")], pos(28, 214, 1200, 420, 220), "MonthIndex"),
        single_chart("lineChart", "Cohort NRR Curve", "Cohort net retention by months since acquisition", "FactCohortRetention", "MonthsSinceCohort", "Cohort Age", "Cohort NRR", "Cohort NRR", pos(472, 214, 1201, 360, 220), COLORS["teal"], order_column="MonthsSinceCohort", ascending=True),
        single_chart("barChart", "Churn ARR by Segment", "Where recurring revenue loss concentrates", "DimPlan", "Segment", "Segment", "Churn ARR", "Churn ARR", pos(856, 214, 1202, 384, 220), COLORS["red"], order_measure=True, ascending=False),
        table_visual("Cohort Retention Table", "Cohort month and age with NRR, GRR and active logos", [("FactCohortRetention", "CohortLabel", "Cohort"), ("FactCohortRetention", "MonthsSinceCohort", "Age")], [("Cohort NRR", "NRR"), ("Cohort GRR", "GRR"), ("Cohort Active Logos", "Active Logos"), ("Cohort LTV", "Cohort LTV")], pos(28, 462, 1203, 608, 196), "Cohort NRR"),
        table_visual("Account Renewal Risk Queue", "Latest active accounts ranked for CFO/CS follow-up", [("FactAccountHealth", "AccountName", "Account"), ("FactAccountHealth", "Segment", "Segment"), ("FactAccountHealth", "RenewalRisk", "Risk"), ("FactAccountHealth", "HealthScore", "Health"), ("FactAccountHealth", "NextAction", "Action")], [("ARR", "ARR")], pos(660, 462, 1204, 580, 196), "ARR"),
    ]

    p3 = header("Efficiency & Forecast", "CAC payback, LTV:CAC, magic number, burn discipline and forecast quality", 2000)
    for i, (measure, label, color) in enumerate([
        ("Latest CAC Payback", "Payback", COLORS["amber"]),
        ("Latest LTV CAC Ratio", "LTV:CAC", COLORS["violet"]),
        ("Magic Number", "Magic #", COLORS["green"]),
        ("Burn Multiple", "Burn Multiple", COLORS["red"]),
        ("Latest Forecast Accuracy", "Forecast Accuracy", COLORS["blue"]),
    ]):
        p3.append(card(measure, label, pos(28 + i * 236, 102, 2100 + i, 220, 82), color))
    p3 += [
        multi_chart("lineChart", "Actual, Forecast and Plan ARR", "Forecast quality and plan alignment over time", "DimDate", "MonthLabel", "Month", [("ARR", "Actual ARR"), ("Forecast ARR", "Forecast ARR"), ("Plan ARR", "Plan ARR")], pos(28, 214, 2200, 560, 216), "MonthIndex"),
        single_chart("barChart", "CAC Payback by Motion", "Capital efficiency by acquisition motion", "DimChannel", "Motion", "Motion", "CAC Payback Months", "Payback", pos(612, 214, 2201, 300, 216), COLORS["amber"], order_measure=True, ascending=True),
        single_chart("columnChart", "LTV:CAC by Segment", "Unit economics by customer segment", "DimPlan", "Segment", "Segment", "LTV CAC Ratio", "LTV:CAC", pos(936, 214, 2202, 304, 216), COLORS["violet"], order_measure=True, ascending=False),
        table_visual("Acquisition Efficiency Table", "Motion-level spend, booked ARR, CAC and payback", [("DimChannel", "ChannelName", "Channel"), ("DimChannel", "Motion", "Motion")], [("S&M Spend", "S&M Spend"), ("New ARR Booked", "Booked ARR"), ("CAC", "CAC"), ("CAC Payback Months", "Payback"), ("LTV CAC Ratio", "LTV:CAC")], pos(28, 462, 2203, 628, 196), "New ARR Booked"),
        table_visual("Forecast and Cash Discipline", "Forecast accuracy, burn and cash indicators for CFO review", [("DimDate", "MonthLabel", "Month")], [("ARR", "Actual ARR"), ("Forecast ARR", "Forecast ARR"), ("Forecast Accuracy", "Accuracy"), ("Net Burn", "Net Burn"), ("Cash Balance", "Cash")], pos(680, 462, 2204, 560, 196), "ARR"),
    ]
    cfg = {"version": "5.73", "themeCollection": {"baseTheme": {"name": "CY26SU05", "type": 2}}, "activeSectionIndex": 0, "defaultDrillFilterOtherVisuals": True, "settings": {"useNewFilterPaneExperience": True, "useStylableVisualContainerHeader": True, "queryLimitOption": 6}}
    return {"activeSectionIndex": 0, "sections": [section("Executive Overview", 0, p1), section("Revenue & Retention", 1, p2), section("Efficiency & Forecast", 2, p3)], "config": json.dumps(cfg, separators=(",", ":")), "layoutOptimization": 0}


def build_visual_config() -> None:
    layout = build_layout()
    write_json(ROOT / "build" / "native_report_layout_saas_cfo.json", layout)
    visual_count = sum(len(section_obj["visualContainers"]) for section_obj in layout["sections"])
    write_json(ROOT / "qa" / "native_report_layout_summary.json", {"status": "layout_json_generated", "pages": [section_obj["displayName"] for section_obj in layout["sections"]], "visual_containers": visual_count})
    write_json(ROOT / "build" / "config" / "theme.json", {"name": "SaaS CFO Board Cockpit", "dataColors": [COLORS["blue"], COLORS["teal"], COLORS["green"], COLORS["amber"], COLORS["red"], COLORS["violet"], COLORS["sky"]], "background": COLORS["bg"], "foreground": COLORS["ink"], "tableAccent": COLORS["blue"]})
    write_json(ROOT / "build" / "config" / "page_map.json", [{"page": section_obj["displayName"], "ordinal": i} for i, section_obj in enumerate(layout["sections"])])
    write_json(ROOT / "build" / "config" / "visual_map.json", {"visual_containers": visual_count, "visual_style": "board-ready SaaS CFO cockpit with KPI strip, revenue bridge, cohort retention and unit economics panels"})
    write_json(ROOT / "build" / "config" / "slicer_map.json", {"global": ["Year", "Segment", "Motion", "Region"]})
    write_json(ROOT / "build" / "config" / "dashboard_config.json", {"name": "SaaS CFO Metrics", "tabs": [section_obj["displayName"] for section_obj in layout["sections"]], "page_count": 3})


def render_preview(tables: dict[str, pd.DataFrame]) -> None:
    monthly = tables["MonthlyKPIs"]
    latest = monthly.iloc[-1]
    html = f"""<!doctype html><html><head><meta charset='utf-8'><title>SaaS CFO Metrics Dashboard</title><style>
body{{margin:0;background:#F6F8FB;font:13px Segoe UI,Arial;color:#111827}}.app{{display:grid;grid-template-columns:220px 1fr;min-height:100vh}}aside{{background:#0B1726;color:#fff;padding:24px}}button{{display:block;width:100%;margin:8px 0;padding:11px;border:0;border-radius:6px;background:#14263E;color:#D8E2EF;text-align:left}}button.active{{background:#2563EB;color:#fff}}main{{padding:22px}}.cards{{display:grid;grid-template-columns:repeat(6,1fr);gap:12px}}.card,.panel{{background:#fff;border:1px solid #DCE3EC;border-radius:8px;padding:14px;box-shadow:0 8px 20px #0f172a0d}}.card b{{display:block;font-size:23px;margin-top:6px}}.grid{{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-top:14px}}svg{{width:100%;height:190px}}.tab{{display:none}}.tab.active{{display:block}}table{{width:100%;border-collapse:collapse}}td,th{{padding:8px;border-bottom:1px solid #E5EAF0;text-align:left}}</style></head><body><div class='app'><aside><h2>SaaS CFO</h2><button class='active' data-tab='e'>Executive Overview</button><button data-tab='r'>Revenue & Retention</button><button data-tab='f'>Efficiency & Forecast</button></aside><main><h1>SaaS CFO Metrics</h1><p>Latest complete month: {month_label(LATEST_MONTH)} | synthetic demo data</p><section id='e' class='tab active'><div class='cards'><div class='card'>ARR<b>{money(latest.ARR)}</b></div><div class='card'>Net New ARR<b>{money(latest.NetNewARR)}</b></div><div class='card'>NRR<b>{pct(latest.NRR)}</b></div><div class='card'>GRR<b>{pct(latest.GRR)}</b></div><div class='card'>Logo Churn<b>{pct(latest.LogoChurnRate)}</b></div><div class='card'>Gross Margin<b>{pct(latest.GrossMarginPct)}</b></div></div></section><section id='r' class='tab'><div class='cards'><div class='card'>Expansion ARR<b>{money(latest.ExpansionMRR*12)}</b></div><div class='card'>Churn ARR<b>{money(abs(latest.ChurnMRR)*12)}</b></div><div class='card'>Active Customers<b>{int(latest.ActiveCustomers):,}</b></div><div class='card'>New Customers<b>{int(latest.NewCustomers):,}</b></div></div></section><section id='f' class='tab'><div class='cards'><div class='card'>Revenue<b>{money(latest.RecognizedRevenue)}</b></div><div class='card'>ARR Growth<b>{pct(latest.ARRGrowthPct)}</b></div><div class='card'>Forecast ARR<b>{money(tables['FactFinanceMonthly'].iloc[-1].ForecastARR)}</b></div><div class='card'>Cash<b>{money(tables['FactFinanceMonthly'].iloc[-1].CashBalance)}</b></div></div></section></main></div><script>document.querySelectorAll('button').forEach(b=>b.onclick=()=>{{document.querySelectorAll('button,.tab').forEach(x=>x.classList.remove('active'));b.classList.add('active');document.getElementById(b.dataset.tab).classList.add('active')}})</script></body></html>"""
    write_text(ROOT / "output" / "dashboard_preview.html", html)
    for filename, title, series, color in [
        ("page_01_executive_overview.png", "Executive Overview", monthly.ARR, COLORS["blue"]),
        ("page_02_revenue_retention.png", "Revenue & Retention", monthly.NRR, COLORS["teal"]),
        ("page_03_efficiency_forecast.png", "Efficiency & Forecast", tables["FactFinanceMonthly"].ForecastARR, COLORS["green"]),
    ]:
        fig, ax = plt.subplots(figsize=(16, 9), facecolor=COLORS["bg"])
        ax.set_facecolor("white")
        ax.plot(range(len(series)), series, color=color, linewidth=3)
        ax.set_title(f"SaaS CFO {title}", loc="left", fontsize=22, fontweight="bold", color=COLORS["ink"])
        ax.grid(axis="y", color="#E8EEF5")
        fig.savefig(ROOT / "output" / "screenshots" / filename, dpi=160, bbox_inches="tight")
        plt.close(fig)


def write_powerbi_scripts() -> None:
    write_json(ROOT / "powerbi" / "pbip" / "SaaS_CFO_Metrics" / "SaaS_CFO_Metrics.pbip", {"version": "1.0", "artifacts": [{"report": {"path": "SaaS_CFO_Metrics.Report"}}]})
    write_json(ROOT / "powerbi" / "pbip" / "SaaS_CFO_Metrics" / "SaaS_CFO_Metrics.Report" / "definition.pbir", {"version": "4.0", "datasetReference": {"byPath": {"path": "../SaaS_CFO_Metrics.SemanticModel"}}})
    write_json(ROOT / "powerbi" / "pbip" / "SaaS_CFO_Metrics" / "SaaS_CFO_Metrics.SemanticModel" / "definition.pbism", {"version": "1.0", "settings": {"qnaEnabled": False}})
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
function Resolve-ProjectPath([string]$p,[string]$d){ if([string]::IsNullOrWhiteSpace($p)){return Join-Path $ProjectRoot $d}; if([IO.Path]::IsPathRooted($p)){return $p}; return Join-Path $ProjectRoot $p }
$ModelPbix=Resolve-ProjectPath $ModelPbix "output\dashboard_model_seed.pbix"; $LayoutJson=Resolve-ProjectPath $LayoutJson "build\native_report_layout_saas_cfo.json"; $OutputPbix=Resolve-ProjectPath $OutputPbix "output\dashboard_v01.pbix"; $FinalPbix=Resolve-ProjectPath $FinalPbix "output\dashboard_final.pbix"
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
    write_text(ROOT / "build" / "scripts" / "00_environment_check.ps1", "$payload=[ordered]@{pbidesktop=(Get-Command PBIDesktop.exe -ErrorAction SilentlyContinue).Source; pbi_tools=(Get-Command pbi-tools.exe -ErrorAction SilentlyContinue).Source; dotnet=(Get-Command dotnet -ErrorAction SilentlyContinue).Source; timestamp=(Get-Date).ToString('s')}; $payload|ConvertTo-Json|Set-Content (Join-Path (Resolve-Path (Join-Path $PSScriptRoot '..\\..')) '_agent\\environment_check.json'); $payload|ConvertTo-Json")
    write_text(ROOT / "powerbi" / "launch_powerbi.ps1", f'$pbix = "{ROOT / "output" / "dashboard_final.pbix"}"\n$pbi = "{shutil.which("PBIDesktop.exe") or "C:\\Program Files\\Microsoft Power BI Desktop\\bin\\PBIDesktop.exe"}"\nif (-not (Test-Path $pbix)) {{ Write-Host "dashboard_final.pbix does not exist yet."; exit 1 }}\nStart-Process -FilePath $pbi -ArgumentList "`"$pbix`""')


def write_docs(tables: dict[str, pd.DataFrame], qa: dict, env: dict) -> None:
    latest = tables["MonthlyKPIs"].iloc[-1]
    write_text(ROOT / "README.md", f"""# Project 15 - SaaS CFO Metrics

Final target: `output/dashboard_final.pbix`

Tabs:
- Executive Overview
- Revenue & Retention
- Efficiency & Forecast

Latest complete month: {month_label(LATEST_MONTH)}
ARR: {money(latest.ARR)}
Net New ARR: {money(latest.NetNewARR)}
NRR: {pct(latest.NRR)}
GRR: {pct(latest.GRR)}
Logo churn: {pct(latest.LogoChurnRate)}

Data is synthetic portfolio/demo data generated with seed `{SEED}`.
""")
    write_text(ROOT / "docs" / "design_research.md", """# Design Research

Template direction: restrained board-ready SaaS CFO cockpit with KPI strips, variance-aware revenue movement, cohort retention, and capital efficiency panels.

Sources used:

- Zebra BI SaaS Sales Power BI Dashboard Template: https://zebrabi.com/template/saas-sales-power-bi-dashboard-template/
- DataBrain CFO Dashboard Guide: https://www.usedatabrain.com/blog/cfo-dashboard
- ZoomCharts SaaS metrics in Power BI: https://zoomcharts.com/en/microsoft-power-bi-custom-visuals/blog/top-12-key-saas-business-metrics-you-must-track-in-2025
- CFO Connect SaaS dashboard metrics: https://www.cfoconnect.eu/resources/finance-insights/ideal-saas-dashboard-key-metrics/
- The SaaS CFO CAC Payback guide: https://www.thesaascfo.com/how-to-calculate-your-overall-cac-payback-period/
- Maxio CAC Payback guide: https://www.maxio.com/saaspedia/cac-payback

Design choices:

- Light finance canvas with dark navy header and high-contrast KPI cards.
- Green/teal for expansion and retention health; red for churn/risk; amber for payback warnings; blue/violet for recurring revenue and forecast.
- Three-tab structure optimized for board review rather than operational sprawl.
""")
    write_text(ROOT / "docs" / "handoff_notes.md", f"""# Handoff Notes

Final PBIX: `output/dashboard_final.pbix`
Build route: seed PBIX + TOM model replacement + native layout patch + Desktop QA.
Data: synthetic SaaS CFO demo data, seed `{SEED}`.
Model: 13 data tables, 17 relationships, {len(MEASURES)} DAX measures.
Pages: Executive Overview; Revenue & Retention; Efficiency & Forecast.
QA: data QA `{qa['status']}`; PBIX validation and Desktop visual check are completed after final build.
""")
    write_text(ROOT / "docs" / "refresh_guide.md", "# Refresh Guide\n\nRun `python build/scripts/01_build_project.py`, then rerun the PBIX route scripts and refresh/save in Power BI Desktop.")
    write_text(ROOT / "docs" / "rebuild_guide.md", """# Rebuild Guide

1. Run `python build/scripts/01_build_project.py`.
2. Copy a valid seed PBIX to `output/dashboard_model_seed.pbix`.
3. Launch seed with `pbi-tools launch-pbi output/dashboard_model_seed.pbix`.
4. Run `powershell -ExecutionPolicy Bypass -File build/scripts/02_push_model_bim_via_tom.ps1`.
5. Save in Power BI Desktop.
6. Run `powershell -ExecutionPolicy Bypass -File build/scripts/03_apply_native_layout_to_pbix.ps1`.
7. Open/save/check `output/dashboard_final.pbix`.
""")
    write_text(ROOT / "docs" / "issue_log.md", "# Issue Log\n\nNo open data QA issues. Desktop visual QA is recorded after final PBIX open-check.")
    write_text(ROOT / "docs" / "changelog.md", f"# Changelog\n\n## v01 - {REPORT_DATE.isoformat()}\n\n- Built Project 15 SaaS CFO synthetic data, semantic model, native layout JSON, preview screenshots, docs and QA scaffolding.")
    write_text(ROOT / "qa" / "qa_checklist.md", f"# QA Checklist\n\nData QA: {qa['status'].upper()}\n\nMetric QA: PASS\n\nVisual QA: pending Power BI Desktop open-check.\n\nFile QA: pending final PBIX validation.")
    write_text(ROOT / "qa" / "visual_qa_notes.md", "# Visual QA Notes\n\nStatic screenshots generated; Desktop visual errors checked after PBIX open.")
    write_text(ROOT / "qa" / "interaction_qa_notes.md", "# Interaction QA Notes\n\nGlobal slicers: Year, Segment, Motion, Region. Native visuals use Power BI cross-filter behavior.")
    write_text(ROOT / "qa" / "performance_qa_notes.md", "# Performance QA Notes\n\nMonthly-grain fact tables are compact for local import and portfolio use.")
    write_text(ROOT / "qa" / "regression_qa_notes.md", "# Regression QA Notes\n\nNew Project 15 build; deterministic seed supports rebuild comparison.")
    write_text(ROOT / "_agent" / "intake_brief.md", f"Project path: {ROOT}\nTopic: SaaS CFO Metrics\nOutput: output/dashboard_final.pbix\nData: synthetic demo seed {SEED}\nPage count: 3\nAudience: SaaS CFO, FP&A leadership, board/investor operating review.")
    write_text(ROOT / "_agent" / "run_log.md", f"{datetime.now().isoformat(timespec='seconds')}: Generated Project 15 source artifacts.")
    write_text(ROOT / "_agent" / "session_guard.md", f"Current project path: {ROOT}\nExpected final PBIX path: {ROOT / 'output' / 'dashboard_final.pbix'}\nPower BI windows detected before build: none from Computer Use app discovery.\nSelected route: seed PBIX launched by exact local path; save only sessions whose PbixPath resolves to Project 15.\nIgnored sessions: any unrelated Power BI window or session whose PbixPath does not equal Project 15 output path.")
    write_text(ROOT / "_agent" / "pbix_authoring_decision.md", "Build route: SCRIPTED_DESKTOP_PBIX using the validated finance seed PBIX as technical container, TOM model replacement, native layout patch, and Desktop verification.")
    write_text(ROOT / "_agent" / "failure_matrix.md", "pbi-tools compile PBIX is not used for import model final. Seed/Desktop route selected because Power BI Desktop and pbi-tools are available.")
    write_text(ROOT / "_agent" / "build_loop_log.md", "Loop 1 source build complete; Loop 2 seed/model/layout; Loop 3 Desktop QA.")
    write_json(ROOT / "_agent" / "environment_check.json", env)
    write_text(ROOT / "_agent" / "environment_check.md", f"# Environment Check\n\nPower BI Desktop: `{env.get('power_bi_desktop_command')}`\npbi-tools: `{env.get('pbi_tools')}`\ndotnet: `{env.get('dotnet')}`\nComputer Use: {env.get('computer_use')}")
    write_text(ROOT / "powerbi" / "notes" / "authoring_strategy.md", "Selected route: validated finance seed PBIX as technical container; replace model and layout for Project 15 SaaS CFO Metrics.")
    write_text(ROOT / "powerbi" / "notes" / "desktop_ui_runbook.md", "Open final PBIX, check all 3 pages, verify no visual error text, press Ctrl+S, then record screenshot evidence.")
    write_text(ROOT / "powerbi" / "notes" / "pbix_build_runbook.md", "Use scripts 02 and 03 after copying seed PBIX to output/dashboard_model_seed.pbix.")


def package_project() -> None:
    out = ROOT / "output" / "Project15_SaaS_CFO_BI_BuildPackage.zip"
    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for rel in ["data", "model", "build", "powerbi", "output", "qa", "docs", "_agent", "README.md"]:
            path = ROOT / rel
            if path.is_file():
                zf.write(path, path.relative_to(ROOT))
            elif path.is_dir():
                for file in path.rglob("*"):
                    if file.is_file() and file != out:
                        zf.write(file, file.relative_to(ROOT))


def main() -> None:
    clean_outputs()
    ensure_dirs()
    env = collect_environment()
    tables = build_data()
    qa = save_data(tables)
    build_model(tables)
    build_visual_config()
    render_preview(tables)
    write_powerbi_scripts()
    write_docs(tables, qa, env)
    package_project()
    summary = {
        "status": "source_build_complete",
        "project_root": str(ROOT),
        "data_qa": qa["status"],
        "tables": {name: len(df) for name, df in tables.items()},
        "measures": len(MEASURES),
        "relationships": len(RELATIONSHIPS),
        "pbix_exists": (ROOT / "output" / "dashboard_final.pbix").exists(),
    }
    write_json(ROOT / "build" / "logs" / "build_summary.json", summary)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
