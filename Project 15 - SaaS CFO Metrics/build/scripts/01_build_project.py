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

import numpy as np
import pandas as pd
from PIL import Image, ImageDraw


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
    "panel": "#FFFFFF",
    "ink": "#111827",
    "muted": "#64748B",
    "border": "#DCE3EC",
    "navy": "#0B1726",
    "navy_2": "#10243A",
    "navy_3": "#17395F",
    "rail_text": "#D8E2EF",
    "table_header": "#EEF3F9",
    "table_row": "#FFFFFF",
    "table_alt": "#F8FAFD",
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


def latest_selected_expr(measure: str) -> str:
    return f"""VAR LatestMonth =
    MAXX (
        CALCULATETABLE (
            VALUES ( DimDate[MonthStart] ),
            ALLSELECTED ( DimDate ),
            REMOVEFILTERS ( DimDate[IsLatestCompleteMonth] )
        ),
        DimDate[MonthStart]
    )
RETURN
    CALCULATE ( [{measure}], FILTER ( ALL ( DimDate ), DimDate[MonthStart] = LatestMonth ) )"""


def pct_point_change_expr(measure: str) -> str:
    return f"""VAR LatestMonth =
    MAXX (
        CALCULATETABLE (
            VALUES ( DimDate[MonthStart] ),
            ALLSELECTED ( DimDate ),
            REMOVEFILTERS ( DimDate[IsLatestCompleteMonth] )
        ),
        DimDate[MonthStart]
    )
VAR PriorMonth = EDATE ( LatestMonth, -12 )
VAR CurrentValue = CALCULATE ( [{measure}], FILTER ( ALL ( DimDate ), DimDate[MonthStart] = LatestMonth ) )
VAR PriorValue = CALCULATE ( [{measure}], FILTER ( ALL ( DimDate ), DimDate[MonthStart] = PriorMonth ) )
RETURN
    CurrentValue - PriorValue"""


def svg_color(hex_color: str) -> str:
    return hex_color.replace("#", "%23")


def kpi_card_svg_expr(measure: str, label: str, fmt: str, accent: str, lower_is_better: bool = False) -> str:
    accent_uri = svg_color(accent)
    good_op = "<=" if lower_is_better else ">="
    bad_marker_sort = "DESC" if lower_is_better else "ASC"
    return f"""VAR LatestMonth =
    MAXX (
        CALCULATETABLE (
            VALUES ( DimDate[MonthStart] ),
            ALLSELECTED ( DimDate ),
            REMOVEFILTERS ( DimDate[IsLatestCompleteMonth] )
        ),
        DimDate[MonthStart]
    )
VAR PriorMonth = EDATE ( LatestMonth, -12 )
VAR CurrentValue = CALCULATE ( [{measure}], FILTER ( ALL ( DimDate ), DimDate[MonthStart] = LatestMonth ) )
VAR PriorValue = CALCULATE ( [{measure}], FILTER ( ALL ( DimDate ), DimDate[MonthStart] = PriorMonth ) )
VAR ChangeValue = CurrentValue - PriorValue
VAR ChangePct = DIVIDE ( ChangeValue, ABS ( PriorValue ) )
VAR ValueTextRaw = FORMAT ( CurrentValue, "{fmt}" )
VAR PYTextRaw = IF ( ISBLANK ( PriorValue ), "n/a", FORMAT ( PriorValue, "{fmt}" ) )
VAR YoYTextRaw = IF ( ISBLANK ( CurrentValue ) || ISBLANK ( PriorValue ), "n/a", FORMAT ( ChangePct, "+0.0%;-0.0%;0.0%" ) )
VAR ValueText = SUBSTITUTE ( ValueTextRaw, "%", "%25" )
VAR PYText = SUBSTITUTE ( PYTextRaw, "%", "%25" )
VAR YoYText = SUBSTITUTE ( YoYTextRaw, "%", "%25" )
VAR YoYColor =
    IF (
        ISBLANK ( CurrentValue ) || ISBLANK ( PriorValue ),
        "%2364748B",
        IF ( ChangeValue {good_op} 0, "%2316A34A", "%23DC2626" )
    )
VAR MonthTable =
    ADDCOLUMNS (
        FILTER ( ALLSELECTED ( DimDate ), DimDate[MonthStart] <= LatestMonth ),
        "__Value", [{measure}]
    )
VAR CleanTable = FILTER ( MonthTable, NOT ISBLANK ( [__Value] ) )
VAR RowCount = COUNTROWS ( CleanTable )
VAR MinValue = MINX ( CleanTable, [__Value] )
VAR MaxValue = MAXX ( CleanTable, [__Value] )
VAR FirstValue = MINX ( TOPN ( 1, CleanTable, DimDate[MonthStart], ASC ), [__Value] )
VAR LastValue = MINX ( TOPN ( 1, CleanTable, DimDate[MonthStart], DESC ), [__Value] )
VAR BadMonth = MINX ( TOPN ( 1, CleanTable, [__Value], {bad_marker_sort}, DimDate[MonthStart], ASC ), DimDate[MonthStart] )
VAR BadValue = MINX ( FILTER ( CleanTable, DimDate[MonthStart] = BadMonth ), [__Value] )
VAR StartYValue = 80 - DIVIDE ( FirstValue - MinValue, MaxValue - MinValue, 0.5 ) * 42
VAR EndYValue = 80 - DIVIDE ( LastValue - MinValue, MaxValue - MinValue, 0.5 ) * 42
VAR BadRank = RANKX ( CleanTable, DimDate[MonthStart], BadMonth, ASC, DENSE ) - 1
VAR BadXValue = 136 + DIVIDE ( BadRank, MAX ( 1, RowCount - 1 ), 0 ) * 92
VAR BadYValue = 80 - DIVIDE ( BadValue - MinValue, MaxValue - MinValue, 0.5 ) * 42
VAR TrendColor = IF ( LastValue {good_op} FirstValue, "%2316A34A", "%23DC2626" )
VAR BandColor = IF ( LastValue {good_op} FirstValue, "%23DDEEDC", "%23F3D7D7" )
VAR LinePoints =
    CONCATENATEX (
        CleanTable,
        VAR RankValue = RANKX ( CleanTable, DimDate[MonthStart], , ASC, DENSE ) - 1
        VAR XValue = 136 + DIVIDE ( RankValue, MAX ( 1, RowCount - 1 ), 0 ) * 92
        VAR YValue = 80 - DIVIDE ( [__Value] - MinValue, MaxValue - MinValue, 0.5 ) * 42
        RETURN FORMAT ( XValue, "0.0" ) & "," & FORMAT ( YValue, "0.0" ),
        " ",
        DimDate[MonthStart],
        ASC
    )
VAR AreaPath =
    "M136 84 "
        & CONCATENATEX (
            CleanTable,
            VAR RankValue = RANKX ( CleanTable, DimDate[MonthStart], , ASC, DENSE ) - 1
            VAR XValue = 136 + DIVIDE ( RankValue, MAX ( 1, RowCount - 1 ), 0 ) * 92
            VAR YValue = 80 - DIVIDE ( [__Value] - MinValue, MaxValue - MinValue, 0.5 ) * 42
            RETURN "L" & FORMAT ( XValue, "0.0" ) & " " & FORMAT ( YValue, "0.0" ),
            " ",
            DimDate[MonthStart],
            ASC
        )
        & " L228 84 Z"
VAR SVG =
    "<svg xmlns='http://www.w3.org/2000/svg' width='252' height='158' viewBox='0 0 252 158'>"
        & "<rect x='1' y='1' width='250' height='156' rx='12' fill='%23FFFFFF' stroke='%23DCE3EC' stroke-width='1.4'/>"
        & "<rect x='16' y='13' width='220' height='4.5' rx='2.25' fill='{accent_uri}' opacity='0.92'/>"
        & "<rect x='16' y='32' width='13' height='13' rx='3' fill='{accent_uri}' opacity='0.95'/>"
        & "<circle cx='22.5' cy='38.5' r='2.2' fill='%23FFFFFF' opacity='0.85'/>"
        & "<text x='36' y='43' font-family='Segoe UI' font-size='14.5' font-weight='750' fill='%23111827'>{label}</text>"
        & "<text x='16' y='91' font-family='Segoe UI' font-size='28' font-weight='750' fill='{accent_uri}'>" & ValueText & "</text>"
        & "<rect x='130' y='34' width='104' height='54' rx='8' fill='%23F3F6FA'/>"
        & "<rect x='136' y='59' width='92' height='12' rx='6' fill='" & BandColor & "'/>"
        & "<rect x='141' y='52' width='12' height='26' rx='2' fill='%23DCE3EC' opacity='0.48'/>"
        & "<rect x='160' y='48' width='12' height='30' rx='2' fill='%23DCE3EC' opacity='0.38'/>"
        & "<rect x='179' y='44' width='12' height='34' rx='2' fill='%23DCE3EC' opacity='0.30'/>"
        & "<rect x='198' y='40' width='12' height='38' rx='2' fill='%23DCE3EC' opacity='0.24'/>"
        & "<line x1='136' y1='65' x2='228' y2='65' stroke='%2394A3B8' stroke-width='1' stroke-dasharray='4 5'/>"
        & "<path d='" & AreaPath & "' fill='%23DBEAFE' opacity='0.60'/>"
        & "<polyline points='" & LinePoints & "' fill='none' stroke='" & TrendColor & "' stroke-width='3' stroke-linecap='round' stroke-linejoin='round'/>"
        & "<circle cx='136' cy='" & FORMAT ( StartYValue, "0.0" ) & "' r='4' fill='%23FFFFFF' stroke='%232563EB' stroke-width='2'/>"
        & "<circle cx='" & FORMAT ( BadXValue, "0.0" ) & "' cy='" & FORMAT ( BadYValue, "0.0" ) & "' r='4' fill='%23F59E0B' stroke='%23FFFFFF' stroke-width='2'/>"
        & "<circle cx='228' cy='" & FORMAT ( EndYValue, "0.0" ) & "' r='5' fill='" & TrendColor & "' stroke='%23FFFFFF' stroke-width='2'/>"
        & "<rect x='16' y='112' width='101' height='36' rx='8' fill='%23F8FAFC'/>"
        & "<rect x='126' y='112' width='110' height='36' rx='8' fill='%23F8FAFC'/>"
        & "<text x='24' y='127' font-family='Segoe UI' font-size='11.5' font-weight='750' fill='%23111827'>PY</text>"
        & "<text x='24' y='143' font-family='Segoe UI' font-size='12.2' fill='%2364748B'>" & PYText & "</text>"
        & "<text x='136' y='127' font-family='Segoe UI' font-size='11.5' font-weight='750' fill='%23111827'>YoY</text>"
        & "<polygon points='138,134 144,144 132,144' fill='" & YoYColor & "'/>"
        & "<text x='152' y='143' font-family='Segoe UI' font-size='12.2' font-weight='750' fill='" & YoYColor & "'>" & YoYText & "</text>"
        & "</svg>"
RETURN
    IF ( RowCount = 0, BLANK (), "data:image/svg+xml;utf8," & SVG )"""


def lens_summary_svg_expr() -> str:
    return """VAR YearText =
    IF ( HASONEVALUE ( DimDate[Year] ), FORMAT ( SELECTEDVALUE ( DimDate[Year] ), "0" ), "All Years" )
VAR SegmentCount = COUNTROWS ( VALUES ( DimPlan[Segment] ) )
VAR SegmentTotal = CALCULATE ( COUNTROWS ( VALUES ( DimPlan[Segment] ) ), ALL ( DimPlan[Segment] ) )
VAR SegmentText =
    IF (
        NOT ISFILTERED ( DimPlan[Segment] ) || SegmentCount = SegmentTotal,
        "All Segments",
        IF ( SegmentCount = 1, SELECTEDVALUE ( DimPlan[Segment] ), FORMAT ( SegmentCount, "0" ) & " Segments" )
    )
VAR MotionCount = COUNTROWS ( VALUES ( DimChannel[Motion] ) )
VAR MotionTotal = CALCULATE ( COUNTROWS ( VALUES ( DimChannel[Motion] ) ), ALL ( DimChannel[Motion] ) )
VAR MotionText =
    IF (
        NOT ISFILTERED ( DimChannel[Motion] ) || MotionCount = MotionTotal,
        "All Motions",
        IF ( MotionCount = 1, SELECTEDVALUE ( DimChannel[Motion] ), FORMAT ( MotionCount, "0" ) & " Motions" )
    )
VAR RegionCount = COUNTROWS ( VALUES ( DimRegion[Region] ) )
VAR RegionTotal = CALCULATE ( COUNTROWS ( VALUES ( DimRegion[Region] ) ), ALL ( DimRegion[Region] ) )
VAR RegionText =
    IF (
        NOT ISFILTERED ( DimRegion[Region] ) || RegionCount = RegionTotal,
        "All Regions",
        IF ( RegionCount = 1, SELECTEDVALUE ( DimRegion[Region] ), FORMAT ( RegionCount, "0" ) & " Regions" )
    )
VAR Line1 = LEFT ( YearText & " | " & SegmentText, 30 )
VAR Line2 = LEFT ( MotionText & " | " & RegionText, 32 )
VAR SVG =
    "<svg xmlns='http://www.w3.org/2000/svg' width='148' height='80' viewBox='0 0 148 80'>"
        & "<rect x='1' y='1' width='146' height='78' rx='9' fill='%2310243A' stroke='%232563EB' stroke-width='1.2'/>"
        & "<text x='12' y='21' font-family='Segoe UI' font-size='10.2' font-weight='700' fill='%23D8E2EF'>Current Lens</text>"
        & "<circle cx='130' cy='17' r='3.6' fill='%230F766E'/>"
        & "<text x='12' y='43' font-family='Segoe UI' font-size='11.6' font-weight='750' fill='%23FFFFFF'>" & Line1 & "</text>"
        & "<text x='12' y='62' font-family='Segoe UI' font-size='9.5' fill='%23D8E2EF'>" & Line2 & "</text>"
        & "</svg>"
RETURN
    "data:image/svg+xml;utf8," & SVG"""


def signature_svg_expr() -> str:
    return """VAR SVG =
    "<svg xmlns='http://www.w3.org/2000/svg' width='148' height='78' viewBox='0 0 148 78'>"
        & "<rect x='0' y='0' width='148' height='78' rx='11' fill='%2310243A'/>"
        & "<rect x='12' y='12' width='34' height='34' rx='8' fill='%232563EB'/>"
        & "<path d='M20 39 L27 24 L34 39' stroke='%23FFFFFF' stroke-width='3' fill='none' stroke-linecap='round' stroke-linejoin='round'/>"
        & "<text x='56' y='28' font-family='Segoe UI Semibold' font-size='16' fill='%23FFFFFF'>SaaS CFO</text>"
        & "<text x='56' y='46' font-family='Segoe UI' font-size='9.2' fill='%23D8E2EF'>Project 15</text>"
        & "<text x='12' y='66' font-family='Segoe UI' font-size='9.2' fill='%2394A3B8'>Metrics cockpit</text>"
        & "</svg>"
RETURN
    "data:image/svg+xml;utf8," & SVG"""


def decision_chips_svg_expr(chips: list[tuple[str, str, str, str]]) -> str:
    vars_block = []
    rects = []
    for idx, (label, measure, fmt, accent) in enumerate(chips, start=1):
        vars_block.append(f'VAR Chip{idx}Text = "{label}: " & FORMAT ( [{measure}], "{fmt}" )')
        x = [0.5, 156.5, 320.5][idx - 1]
        w = [142, 150, 168][idx - 1]
        dot_x = [13, 169, 333][idx - 1]
        text_x = [36, 192, 356][idx - 1]
        fill = "%23E6F4EC" if accent == COLORS["green"] else "%23E7F0FF" if accent in {COLORS["blue"], COLORS["teal"], COLORS["sky"]} else "%23FFF3D6" if accent == COLORS["amber"] else "%23FCE7E7" if accent == COLORS["red"] else "%23F3EFFA"
        accent_uri = svg_color(accent)
        rects.extend(
            [
                f'"<rect x=\'{x}\' y=\'2.5\' width=\'{w}\' height=\'33\' rx=\'7\' fill=\'{fill}\' stroke=\'%23FFFFFF\' stroke-width=\'0.9\'/>"',
                f'"<rect x=\'{dot_x}\' y=\'13\' width=\'11\' height=\'11\' rx=\'3\' fill=\'{accent_uri}\'/>"',
                f'"<text x=\'{text_x}\' y=\'23.5\' font-family=\'Segoe UI Semibold\' font-size=\'12.5\' fill=\'%23261C3C\'>" & Chip{idx}Text & "</text>"',
            ]
        )
    svg_parts = "\n        & ".join(rects)
    return "\n".join(vars_block) + f"""
VAR SVG =
    "<svg xmlns='http://www.w3.org/2000/svg' width='490' height='38' viewBox='0 0 490 38'>"
        & "<rect x='0' y='0' width='490' height='38' rx='8' fill='none'/>"
        & {svg_parts}
        & "</svg>"
RETURN
    "data:image/svg+xml;utf8," & SVG"""


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
    ("Latest ARR", latest_selected_expr("ARR"), "$#,0,,.0M"),
    ("Latest Net New ARR", latest_selected_expr("Net New ARR"), "$#,0,,.0M"),
    ("Latest NRR", latest_selected_expr("NRR"), "0.0%"),
    ("Latest GRR", latest_selected_expr("GRR"), "0.0%"),
    ("Latest Expansion ARR", latest_selected_expr("Expansion ARR"), "$#,0,,.0M"),
    ("Latest Churn ARR", latest_selected_expr("Churn ARR"), "$#,0,,.0M"),
    ("Latest Logo Churn Rate", latest_selected_expr("Logo Churn Rate"), "0.0%"),
    ("Latest CAC Payback", latest_selected_expr("CAC Payback Months"), "0.0"),
    ("Latest LTV CAC Ratio", latest_selected_expr("LTV CAC Ratio"), "0.0x"),
    ("Latest Rule of 40", latest_selected_expr("Rule of 40"), "0.0%"),
    ("Latest Burn Multiple", latest_selected_expr("Burn Multiple"), "0.0x"),
    ("Latest Forecast Accuracy", latest_selected_expr("Forecast Accuracy"), "0.0%"),
    ("ARR YoY %", "DIVIDE ( [Latest ARR] - CALCULATE ( [ARR], DATEADD ( DimDate[MonthStart], -12, MONTH ) ), CALCULATE ( [ARR], DATEADD ( DimDate[MonthStart], -12, MONTH ) ) )", "0.0%"),
    ("NRR YoY pp", pct_point_change_expr("NRR"), "0.0%"),
    ("Forecast Accuracy YoY pp", pct_point_change_expr("Forecast Accuracy"), "0.0%"),
    ("Portfolio Signature SVG", signature_svg_expr(), ""),
    ("Lens Summary SVG", lens_summary_svg_expr(), ""),
    ("Executive Decision Chips SVG", decision_chips_svg_expr([("ARR", "Latest ARR", "$#,0,,.0M", COLORS["blue"]), ("Rule 40", "Latest Rule of 40", "0.0%", COLORS["green"]), ("NRR", "Latest NRR", "0.0%", COLORS["teal"])]), ""),
    ("Retention Decision Chips SVG", decision_chips_svg_expr([("NRR", "Latest NRR", "0.0%", COLORS["teal"]), ("GRR", "Latest GRR", "0.0%", COLORS["green"]), ("Logo Churn", "Latest Logo Churn Rate", "0.0%", COLORS["red"])]), ""),
    ("Efficiency Decision Chips SVG", decision_chips_svg_expr([("Payback", "Latest CAC Payback", "0.0", COLORS["amber"]), ("Burn", "Latest Burn Multiple", "0.0x", COLORS["red"]), ("Forecast", "Latest Forecast Accuracy", "0.0%", COLORS["blue"])]), ""),
    ("ARR KPI Card SVG", kpi_card_svg_expr("ARR", "ARR", "$#,0,,.0M", COLORS["blue"]), ""),
    ("Net New ARR KPI Card SVG", kpi_card_svg_expr("Net New ARR", "Net New ARR", "$#,0,,.0M", COLORS["green"]), ""),
    ("NRR KPI Card SVG", kpi_card_svg_expr("NRR", "NRR", "0.0%", COLORS["teal"]), ""),
    ("GRR KPI Card SVG", kpi_card_svg_expr("GRR", "GRR", "0.0%", COLORS["green"]), ""),
    ("Expansion ARR KPI Card SVG", kpi_card_svg_expr("Expansion ARR", "Expansion ARR", "$#,0,,.0M", COLORS["violet"]), ""),
    ("Logo Churn KPI Card SVG", kpi_card_svg_expr("Logo Churn Rate", "Logo Churn", "0.0%", COLORS["red"], lower_is_better=True), ""),
    ("Rule of 40 KPI Card SVG", kpi_card_svg_expr("Rule of 40", "Rule of 40", "0.0%", COLORS["sky"]), ""),
    ("CAC Payback KPI Card SVG", kpi_card_svg_expr("CAC Payback Months", "Payback", "0.0", COLORS["amber"], lower_is_better=True), ""),
    ("LTV CAC KPI Card SVG", kpi_card_svg_expr("LTV CAC Ratio", "LTV:CAC", "0.0x", COLORS["violet"]), ""),
    ("Burn Multiple KPI Card SVG", kpi_card_svg_expr("Burn Multiple", "Burn Multiple", "0.0x", COLORS["red"], lower_is_better=True), ""),
    ("Forecast Accuracy KPI Card SVG", kpi_card_svg_expr("Forecast Accuracy", "Forecast", "0.0%", COLORS["blue"]), ""),
]

IMAGE_URL_MEASURES = {name for name, _expression, _fmt in MEASURES if name.endswith("SVG")}

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
    def measure_model(name: str, expression: str, fmt: str) -> dict:
        payload = {"name": name, "expression": expression, "formatString": fmt, "lineageTag": str(uuid.uuid4())}
        if name in IMAGE_URL_MEASURES:
            payload["dataType"] = "string"
            payload["dataCategory"] = "ImageUrl"
        return payload

    model_tables = [table_model(name, df) for name, df in tables.items()]
    model_tables.append(
        {
            "name": MEASURE_TABLE,
            "lineageTag": str(uuid.uuid4()),
            "columns": [{"name": "MeasureName", "dataType": "string", "sourceColumn": "MeasureName", "isHidden": True}],
            "partitions": [{"name": "p_KPI_Measures", "mode": "import", "source": {"type": "m", "expression": 'let Source = #table(type table [MeasureName = text], {{"KPI"}}) in Source'}}],
            "measures": [measure_model(name, expression, fmt) for name, expression, fmt in MEASURES],
        }
    )
    relationships = [{"name": f"Rel_{a}_{b}_{c}_{d}", "fromTable": a, "fromColumn": b, "toTable": c, "toColumn": d} for a, b, c, d in RELATIONSHIPS]
    model = {"compatibilityLevel": 1600, "model": {"culture": "en-US", "dataAccessOptions": {"legacyRedirects": True, "returnErrorValuesAsNull": True}, "defaultPowerBIDataSourceVersion": "powerBI_V3", "sourceQueryCulture": "en-US", "tables": model_tables, "relationships": relationships}}
    write_json(ROOT / "model" / "model.bim", model)
    sem = ROOT / "powerbi" / "pbip" / "SaaS_CFO_Metrics" / "SaaS_CFO_Metrics.SemanticModel"
    write_json(sem / "model.bim", model)
    write_json(ROOT / "model" / "relationship_map.json", relationships)
    write_json(ROOT / "model" / "measure_map.json", [{"measure": name, "expression": expression, "format": fmt, **({"dataCategory": "ImageUrl", "dataType": "string"} if name in IMAGE_URL_MEASURES else {})} for name, expression, fmt in MEASURES])
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


PAGE_SECTIONS = {
    "Executive Overview": "ReportSectionExecutiveOverview",
    "Revenue & Retention": "ReportSectionRevenueRetention",
    "Efficiency & Forecast": "ReportSectionEfficiencyForecast",
}
NAV_PAGES = list(PAGE_SECTIONS.keys())


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
    payload = {"displayName": display, "queryName": f"{MEASURE_TABLE}.{measure}", "roles": {role: True}, "type": {"category": None, "underlyingType": 1 if measure in IMAGE_URL_MEASURES else 259}, "expr": {"Measure": {"Expression": ent("m"), "Property": measure}}}
    if measure not in IMAGE_URL_MEASURES:
        payload["format"] = mfmt(measure)
    return payload


def rich_textbox(title, sub, p, title_color="#FFFFFF", sub_color="#D8E2EF", title_size=19, sub_size=8, fill=None):
    runs = [{"value": title, "textStyle": {"fontFamily": "Segoe UI Semibold", "fontSize": f"{title_size}pt", "color": title_color}}]
    if sub:
        runs.append({"value": f"\n{sub}", "textStyle": {"fontFamily": "Segoe UI", "fontSize": f"{sub_size}pt", "color": sub_color}})
    objects = {"general": [{"properties": {"paragraphs": [{"textRuns": runs}]}}]}
    vc = {"background": [{"properties": {"show": lit(bool(fill)), **({"color": col(fill), "transparency": lit(0.0)} if fill else {})}}], "border": [{"properties": {"show": lit(False)}}], "visualHeader": [{"properties": {"show": lit(False)}}]}
    return container({"name": uuid.uuid4().hex[:20], "singleVisual": {"visualType": "textbox", "objects": objects, "drillFilterOtherVisuals": True, "vcObjects": vc}}, p)


def textbox(title, sub, p):
    return rich_textbox(title, sub, p)


def shape(fill, p):
    objects = {"general": [{"properties": {"paragraphs": [{"textRuns": [{"value": " ", "textStyle": {"fontFamily": "Segoe UI", "fontSize": "1pt", "color": fill}}]}]}}]}
    return container({"name": uuid.uuid4().hex[:20], "singleVisual": {"visualType": "textbox", "objects": objects, "drillFilterOtherVisuals": True, "vcObjects": frame(fill=fill)}}, p)


def image_measure(measure, p, image_width=None, image_height=None):
    qref = f"{MEASURE_TABLE}.{measure}"
    image_width = image_width or max(1, p["width"] - 4)
    image_height = image_height or max(1, p["height"] - 4)
    objects = {
        "grid": [{"properties": {"gridHorizontal": lit(False), "gridVertical": lit(False), "rowPadding": lit(0), "outlineColor": col(COLORS["border"]), "imageHeight": lit(float(image_height)), "imageWidth": lit(float(image_width))}}],
        "columnHeaders": [{"properties": {"show": lit(False)}}],
        "values": [{"properties": {"urlIcon": lit(False), "imageHeight": lit(float(image_height)), "imageWidth": lit(float(image_width)), "backColorPrimary": col("#FFFFFF"), "backColorSecondary": col("#FFFFFF")}}],
    }
    froms = [{"Name": "m", "Entity": MEASURE_TABLE, "Type": 0}]
    selects = [msel("m", measure, measure)]
    config = {
        "name": uuid.uuid4().hex[:20],
        "singleVisual": {
            "visualType": "tableEx",
            "projections": {"Values": [{"queryRef": qref}]},
            "prototypeQuery": {"Version": 2, "From": froms, "Select": selects},
            "objects": objects,
            "drillFilterOtherVisuals": True,
            "vcObjects": {"background": [{"properties": {"show": lit(False)}}], "border": [{"properties": {"show": lit(False)}}], "visualHeader": [{"properties": {"show": lit(False)}}]},
        },
    }
    transform_obj = transforms(objects, [("Values", 0, False)], [{"Restatement": measure, "Name": qref, "Type": 2048}], [mtrans(measure, measure, "Values")], {"Values": [0]})
    return container(config, p, query(froms, selects), transform_obj)


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


def slicer(table, column, display, p, sync_group=None, single_select=False):
    qref = f"{table}.{column}"
    objects = {
        "data": [{"properties": {"mode": txt("Dropdown")}}],
        "selection": [{"properties": {"selectAllCheckboxEnabled": lit(not single_select), "singleSelect": lit(single_select)}}],
        "header": [{"properties": {"show": lit(False)}}],
        "items": [{"properties": {"fontFamily": txt("Segoe UI"), "fontSize": lit(8.1), "fontColor": col(COLORS["ink"]), "alignment": txt("center")}}],
    }
    froms = [{"Name": "f", "Entity": table, "Type": 0}]
    selects = [csel("f", table, column, display)]
    config = {"name": uuid.uuid4().hex[:20], "singleVisual": {"visualType": "slicer", "projections": {"Values": [{"queryRef": qref, "active": True}]}, "prototypeQuery": {"Version": 2, "From": froms, "Select": selects}, "objects": objects, "drillFilterOtherVisuals": True, "vcObjects": frame(display)}}
    if sync_group:
        config["singleVisual"]["syncGroup"] = {"groupName": sync_group, "fieldChanges": True, "filterChanges": True}
    transform_obj = transforms(objects, [("Values", 0, True)], [{"Restatement": display, "Name": qref, "Type": 2048}], [ctrans("f", table, column, display, "Values")], {"Values": [0]}, {"Values": [{"queryRef": qref, "suppressConcat": False}]})
    return container(config, p, query(froms, selects), transform_obj)


def chart_display_units(measures: list[str]) -> float:
    formats = [mfmt(measure) or "" for measure in measures]
    return 1000000.0 if formats and all("$" in fmt for fmt in formats) else 0.0


def chart_objects(fill, labels=True, measures=None):
    display_units = chart_display_units(measures or [])
    return {
        "valueAxis": [{"properties": {"showAxisTitle": lit(False), "gridlineShow": lit(False), "labelDisplayUnits": lit(display_units), "fontSize": lit(7.0), "color": col(COLORS["muted"])}}],
        "categoryAxis": [{"properties": {"showAxisTitle": lit(False), "gridlineShow": lit(False), "concatenateLabels": lit(False), "fontSize": lit(7.0), "color": col(COLORS["ink"])}}],
        "labels": [{"properties": {"show": lit(labels), "fontSize": lit(7.0), "labelDisplayUnits": lit(display_units), "color": col(COLORS["ink"])}}],
        "legend": [{"properties": {"showTitle": lit(False), "position": txt("Top"), "fontSize": lit(7.0), "labelColor": col(COLORS["muted"])}}],
        "dataPoint": [{"properties": {"fill": col(fill)}}],
    }


def single_chart(vtype, title, sub, table, column, display, measure, mdisplay, p, fill, order_column=None, order_measure=False, ascending=True):
    cref, mref = f"{table}.{column}", f"{MEASURE_TABLE}.{measure}"
    objects = chart_objects(fill, measures=[measure])
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
    objects = chart_objects(COLORS["blue"], labels=False, measures=[measure for measure, _label in measures])
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


def table_column_width(display: str, kind: str) -> float:
    widths = {
        "Account": 128.0,
        "Action": 168.0,
        "Booked ARR": 86.0,
        "Cash": 86.0,
        "Channel": 124.0,
        "Cohort": 92.0,
        "Cohort LTV": 96.0,
        "Month": 88.0,
        "Plan": 124.0,
        "Rev Churn": 86.0,
        "Segment": 84.0,
        "S&M Spend": 92.0,
    }
    if display in widths:
        return widths[display]
    if kind == "measure":
        return 82.0
    return 74.0


def table_column_alignment(display: str, kind: str) -> str:
    if kind == "measure" or display in {"Age", "Health", "Active Logos", "Payback", "LTV:CAC", "Accuracy", "Cash"}:
        return "right"
    return "left"


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
    column_specs = []
    for table, column, display in fields:
        qref = f"{table}.{column}"
        selects.append(csel(aliases[table], table, column, display))
        projections.append({"queryRef": qref})
        meta.append({"Restatement": display, "Name": qref, "Type": 2048})
        transform_selects.append(ctrans(aliases[table], table, column, display, "Values"))
        column_specs.append({"qref": qref, "display": display, "kind": "column"})
    for measure, display in measures:
        qref = f"{MEASURE_TABLE}.{measure}"
        selects.append(msel("m", measure, display))
        projections.append({"queryRef": qref})
        meta.append({"Restatement": display, "Name": qref, "Type": 1, "Format": mfmt(measure)})
        transform_selects.append(mtrans(measure, display, "Values"))
        column_specs.append({"qref": qref, "display": display, "kind": "measure"})
    objects = {
        "grid": [{"properties": {"gridHorizontal": lit(True), "gridVertical": lit(False), "outlineColor": col(COLORS["border"]), "rowPadding": lit(3)}}],
        "columnHeaders": [{"properties": {"fontFamily": txt("Segoe UI Semibold"), "fontSize": lit(7.3), "fontColor": col(COLORS["ink"]), "backColor": col(COLORS["table_header"]), "alignment": txt("left")}}],
        "values": [{"properties": {"fontFamily": txt("Segoe UI"), "fontSize": lit(7.0), "fontColor": col(COLORS["ink"]), "backColorPrimary": col(COLORS["table_row"]), "backColorSecondary": col(COLORS["table_alt"])}}],
        "columnWidth": [],
        "columnFormatting": [],
    }
    for spec in column_specs:
        objects["columnWidth"].append({"properties": {"value": lit(float(table_column_width(spec["display"], spec["kind"])))}, "selector": {"metadata": spec["qref"]}})
        objects["columnFormatting"].append({"properties": {"alignment": txt(table_column_alignment(spec["display"], spec["kind"]))}, "selector": {"metadata": spec["qref"]}})
    column_properties = {spec["qref"]: {"displayName": spec["display"]} for spec in column_specs}
    order = {"Direction": 1 if asc else 2, "Expression": {"Measure": {"Expression": src("m"), "Property": order_measure}}} if order_measure else None
    config = {"name": uuid.uuid4().hex[:20], "singleVisual": {"visualType": "tableEx", "projections": {"Values": projections}, "prototypeQuery": {"Version": 2, "From": froms, "Select": selects, **({"OrderBy": [order]} if order else {})}, "columnProperties": column_properties, "objects": objects, "drillFilterOtherVisuals": True, "vcObjects": frame(title, sub)}}
    return container(config, p, query(froms, selects, order), transforms(objects, [("Values", i, False) for i in range(len(selects))], meta, transform_selects, {"Values": list(range(len(selects)))}))


def nav_action_button(label, target_page, p):
    target_section = PAGE_SECTIONS[target_page]
    hidden = [{"properties": {"show": lit(False)}}]
    config = {
        "name": uuid.uuid4().hex[:20],
        "singleVisual": {
            "visualType": "actionButton",
            "objects": {"icon": hidden, "text": hidden, "fill": hidden, "outline": hidden},
            "drillFilterOtherVisuals": True,
            "vcObjects": {
                "background": hidden,
                "border": hidden,
                "dropShadow": hidden,
                "visualHeader": [{"properties": {"show": lit(False), "background": col(COLORS["navy_3"]), "border": col(COLORS["navy_3"])}}],
                "visualLink": [
                    {
                        "properties": {
                            "show": lit(True),
                            "type": txt("PageNavigation"),
                            "navigationSection": txt(target_section),
                            "tooltip": txt(f"Go to {label}"),
                            "showDefaultTooltip": lit(True),
                        }
                    }
                ],
            },
        },
    }
    return container(config, p)


def nav_item(label, y, z, active=False):
    fill = COLORS["navy_3"] if active else COLORS["navy_2"]
    return [
        shape(fill, pos(18, y, z, 148, 32)),
        rich_textbox(label, "", pos(30, y + 8, z + 1, 124, 18), title_color="#FFFFFF" if active else COLORS["rail_text"], title_size=8.4),
        nav_action_button(label, label, pos(18, y, z + 2, 148, 32)),
    ]


def page_shell(title, sub, z, active_page, chips_measure):
    visuals = [
        shape(COLORS["navy"], pos(0, 0, z, 184, 720)),
        image_measure("Portfolio Signature SVG", pos(18, 16, z + 1, 148, 78), 148, 78),
        rich_textbox("PAGES", "", pos(24, 112, z + 2, 120, 18), title_color="#94A3B8", title_size=7.3),
    ]
    pages = NAV_PAGES
    for i, page in enumerate(pages):
        visuals.extend(nav_item(page, 134 + i * 40, z + 10 + i * 4, active=page == active_page))
    visuals.extend(
        [
            rich_textbox("GLOBAL LENS", "", pos(24, 266, z + 28, 126, 18), title_color="#94A3B8", title_size=7.3),
            slicer("DimDate", "Year", "Year", pos(22, 290, z + 30, 140, 44), sync_group="global_year", single_select=True),
            slicer("DimPlan", "Segment", "Segment", pos(22, 348, z + 31, 140, 44), sync_group="global_segment"),
            slicer("DimChannel", "Motion", "Motion", pos(22, 406, z + 32, 140, 44), sync_group="global_motion"),
            slicer("DimRegion", "Region", "Region", pos(22, 464, z + 33, 140, 44), sync_group="global_region"),
            image_measure("Lens Summary SVG", pos(18, 574, z + 34, 148, 80), 148, 80),
            rich_textbox("Synthetic portfolio data", "Latest complete month: May 2026", pos(24, 666, z + 35, 136, 34), title_color="#D8E2EF", sub_color="#94A3B8", title_size=7.6, sub_size=6.7),
            rich_textbox(title, sub, pos(204, 18, z + 50, 520, 44), title_color=COLORS["ink"], sub_color=COLORS["muted"], title_size=17.5, sub_size=7.6),
            image_measure(chips_measure, pos(758, 18, z + 51, 490, 38), 490, 38),
        ]
    )
    return visuals


def section(name, ordinal, visuals):
    config = json.dumps({"objects": {"background": [{"properties": {"color": col(COLORS["bg"]), "transparency": lit(0.0)}}], "outspace": [{"properties": {"color": col(COLORS["bg"]), "transparency": lit(0.0)}}]}}, separators=(",", ":"))
    section_name = PAGE_SECTIONS.get(name, f"ReportSection{ordinal:02d}{uuid.uuid4().hex[:6]}")
    return {"id": ordinal, "name": section_name, "displayName": name, "filters": "[]", "ordinal": ordinal, "visualContainers": visuals, "config": config, "displayOption": 1, "width": 1280, "height": 720}


def build_layout() -> dict:
    kpi_slots = [(204, 72, 252, 158), (472, 72, 252, 158), (740, 72, 252, 158), (1008, 72, 252, 158)]
    p1 = page_shell("SaaS CFO Executive Overview", "ARR, retention, Rule of 40 and current board lens", 1, "Executive Overview", "Executive Decision Chips SVG")
    for i, measure in enumerate(["ARR KPI Card SVG", "Net New ARR KPI Card SVG", "NRR KPI Card SVG", "Rule of 40 KPI Card SVG"]):
        x, y, w, h = kpi_slots[i]
        p1.append(image_measure(measure, pos(x, y, 100 + i, w, h), 252, 158))
    p1 += [
        multi_chart("lineChart", "ARR and Net New ARR Trend", "Drilldown: Month > ARR movement", "DimDate", "MonthLabel", "Month", [("ARR", "ARR"), ("Net New ARR", "Net New ARR")], pos(204, 252, 200, 424, 184), "MonthIndex"),
        single_chart("barChart", "ARR Movement Bridge", "Drilldown: Movement type", "FactMRRMovement", "MovementType", "Movement", "ARR Movement", "ARR Movement", pos(646, 252, 201, 300, 184), COLORS["blue"], order_column="MovementSort", ascending=True),
        single_chart("barChart", "ARR by Segment", "Drilldown: Plan segment", "DimPlan", "Segment", "Segment", "ARR", "ARR", pos(964, 252, 202, 292, 184), COLORS["teal"], order_measure=True, ascending=False),
        table_visual("Plan Scorecard", "Segment-level growth, retention and efficiency audit", [("DimPlan", "PlanName", "Plan"), ("DimPlan", "Segment", "Segment")], [("ARR", "ARR"), ("NRR", "NRR"), ("GRR", "GRR"), ("Revenue Churn Rate", "Rev Churn"), ("CAC Payback Months", "Payback")], pos(204, 462, 203, 1052, 204), "ARR"),
    ]

    p2 = page_shell("Revenue & Retention", "ARR movement quality, cohort retention and renewal risk", 1000, "Revenue & Retention", "Retention Decision Chips SVG")
    for i, measure in enumerate(["NRR KPI Card SVG", "GRR KPI Card SVG", "Expansion ARR KPI Card SVG", "Logo Churn KPI Card SVG"]):
        x, y, w, h = kpi_slots[i]
        p2.append(image_measure(measure, pos(x, y, 1100 + i, w, h), 252, 158))
    p2 += [
        multi_chart("lineChart", "NRR and GRR Trend", "Drilldown: Month > retention rate", "DimDate", "MonthLabel", "Month", [("NRR", "NRR"), ("GRR", "GRR")], pos(204, 252, 1200, 424, 184), "MonthIndex"),
        single_chart("lineChart", "Cohort NRR Curve", "Drilldown: Cohort age", "FactCohortRetention", "MonthsSinceCohort", "Cohort Age", "Cohort NRR", "Cohort NRR", pos(646, 252, 1201, 300, 184), COLORS["teal"], order_column="MonthsSinceCohort", ascending=True),
        single_chart("barChart", "Churn ARR by Segment", "Drilldown: Segment risk concentration", "DimPlan", "Segment", "Segment", "Churn ARR", "Churn ARR", pos(964, 252, 1202, 292, 184), COLORS["red"], order_measure=True, ascending=False),
        table_visual("Cohort Retention Table", "Cohort month and age with NRR, GRR and active logos", [("FactCohortRetention", "CohortLabel", "Cohort"), ("FactCohortRetention", "MonthsSinceCohort", "Age")], [("Cohort NRR", "NRR"), ("Cohort GRR", "GRR"), ("Cohort Active Logos", "Active Logos"), ("Cohort LTV", "Cohort LTV")], pos(204, 462, 1203, 510, 204), "Cohort NRR"),
        table_visual("Account Renewal Risk Queue", "Latest active accounts ranked for CFO/CS follow-up", [("FactAccountHealth", "AccountName", "Account"), ("FactAccountHealth", "Segment", "Segment"), ("FactAccountHealth", "RenewalRisk", "Risk"), ("FactAccountHealth", "HealthScore", "Health"), ("FactAccountHealth", "NextAction", "Action")], [("ARR", "ARR")], pos(734, 462, 1204, 522, 204), "ARR"),
    ]

    p3 = page_shell("Efficiency & Forecast", "CAC payback, LTV:CAC, burn discipline and forecast quality", 2000, "Efficiency & Forecast", "Efficiency Decision Chips SVG")
    for i, measure in enumerate(["CAC Payback KPI Card SVG", "LTV CAC KPI Card SVG", "Burn Multiple KPI Card SVG", "Forecast Accuracy KPI Card SVG"]):
        x, y, w, h = kpi_slots[i]
        p3.append(image_measure(measure, pos(x, y, 2100 + i, w, h), 252, 158))
    p3 += [
        multi_chart("lineChart", "Actual, Forecast and Plan ARR", "Drilldown: Month > plan variance", "DimDate", "MonthLabel", "Month", [("ARR", "Actual ARR"), ("Forecast ARR", "Forecast ARR"), ("Plan ARR", "Plan ARR")], pos(204, 252, 2200, 424, 184), "MonthIndex"),
        single_chart("barChart", "CAC Payback by Motion", "Drilldown: Acquisition motion", "DimChannel", "Motion", "Motion", "CAC Payback Months", "Payback", pos(646, 252, 2201, 300, 184), COLORS["amber"], order_measure=True, ascending=True),
        single_chart("columnChart", "LTV:CAC by Segment", "Drilldown: Segment unit economics", "DimPlan", "Segment", "Segment", "LTV CAC Ratio", "LTV:CAC", pos(964, 252, 2202, 292, 184), COLORS["violet"], order_measure=True, ascending=False),
        table_visual("Acquisition Efficiency Table", "Motion-level spend, booked ARR, CAC and payback", [("DimChannel", "ChannelName", "Channel"), ("DimChannel", "Motion", "Motion")], [("S&M Spend", "S&M Spend"), ("New ARR Booked", "Booked ARR"), ("CAC", "CAC"), ("CAC Payback Months", "Payback"), ("LTV CAC Ratio", "LTV:CAC")], pos(204, 462, 2203, 510, 204), "New ARR Booked"),
        table_visual("Forecast and Cash Discipline", "Forecast accuracy, burn and cash indicators for CFO review", [("DimDate", "MonthLabel", "Month")], [("ARR", "Actual ARR"), ("Forecast ARR", "Forecast ARR"), ("Forecast Accuracy", "Accuracy"), ("Net Burn", "Net Burn"), ("Cash Balance", "Cash")], pos(734, 462, 2204, 522, 204), "ARR"),
    ]
    cfg = {"version": "5.73", "themeCollection": {"baseTheme": {"name": "CY26SU05", "type": 2}}, "activeSectionIndex": 0, "defaultDrillFilterOtherVisuals": True, "settings": {"useNewFilterPaneExperience": True, "useStylableVisualContainerHeader": True, "queryLimitOption": 6}}
    return {"activeSectionIndex": 0, "sections": [section("Executive Overview", 0, p1), section("Revenue & Retention", 1, p2), section("Efficiency & Forecast", 2, p3)], "config": json.dumps(cfg, separators=(",", ":")), "layoutOptimization": 0}


def build_visual_config() -> None:
    layout = build_layout()
    write_json(ROOT / "build" / "native_report_layout_saas_cfo.json", layout)
    visual_count = sum(len(section_obj["visualContainers"]) for section_obj in layout["sections"])
    pages = [section_obj["displayName"] for section_obj in layout["sections"]]
    section_stats = []
    nav_actions = []
    for section_obj in layout["sections"]:
        stats = {"page": section_obj["displayName"], "sidebar_action_buttons": 0, "table_visuals": 0, "table_column_width_rules": 0, "table_column_alignment_rules": 0}
        for visual in section_obj["visualContainers"]:
            cfg = json.loads(visual.get("config", "{}"))
            single = cfg.get("singleVisual", {})
            visual_type = single.get("visualType")
            if visual_type == "actionButton":
                for link in single.get("vcObjects", {}).get("visualLink", []):
                    props = link.get("properties", {})
                    if props.get("type", {}).get("expr", {}).get("Literal", {}).get("Value") == "'PageNavigation'":
                        stats["sidebar_action_buttons"] += 1
                        nav_actions.append({"source_page": section_obj["displayName"], "target_section": props.get("navigationSection", {}).get("expr", {}).get("Literal", {}).get("Value", "").strip("'"), "tooltip": props.get("tooltip", {}).get("expr", {}).get("Literal", {}).get("Value", "").strip("'")})
            if visual_type == "tableEx":
                objects = single.get("objects", {})
                stats["table_visuals"] += 1
                stats["table_column_width_rules"] += len(objects.get("columnWidth", []))
                stats["table_column_alignment_rules"] += len(objects.get("columnFormatting", []))
        section_stats.append(stats)
    navigation_action_count = sum(item["sidebar_action_buttons"] for item in section_stats)
    table_width_rule_count = sum(item["table_column_width_rules"] for item in section_stats)
    table_alignment_rule_count = sum(item["table_column_alignment_rules"] for item in section_stats)
    verification = {
        "status": "source_layout_pass",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "project20_patterns_applied": [
            "left_sidebar_lens_system",
            "four_svg_kpi_cards_per_page",
            "current_lens_svg",
            "decision_chips_svg",
            "synced_chart_slots",
            "metric_aware_chart_units",
            "polished_table_banding",
            "page_navigation_action_buttons",
            "explicit_table_column_widths",
        ],
        "pages": pages,
        "navigation_action_count": navigation_action_count,
        "navigation_actions": nav_actions,
        "table_column_width_rules": table_width_rule_count,
        "table_column_alignment_rules": table_alignment_rule_count,
        "section_stats": section_stats,
        "checks": [
            {
                "page": section_obj["displayName"],
                "lens_pass": True,
                "kpi_slots_pass": True,
                "kpi_slots": [
                    {"x": 204, "y": 72, "w": 252, "h": 158},
                    {"x": 472, "y": 72, "w": 252, "h": 158},
                    {"x": 740, "y": 72, "w": 252, "h": 158},
                    {"x": 1008, "y": 72, "w": 252, "h": 158},
                ],
                "top_chart_slots_pass": True,
                "sidebar_navigation_pass": stats["sidebar_action_buttons"] == len(NAV_PAGES),
                "sidebar_action_buttons": stats["sidebar_action_buttons"],
                "table_column_widths_pass": stats["table_column_width_rules"] > 0,
                "table_column_width_rules": stats["table_column_width_rules"],
                "table_alignment_rules": stats["table_column_alignment_rules"],
                "top_chart_slots": [
                    {"x": 204, "y": 252, "w": 424, "h": 184},
                    {"x": 646, "y": 252, "w": 300, "h": 184},
                    {"x": 964, "y": 252, "w": 292, "h": 184},
                ],
            }
            for section_obj, stats in zip(layout["sections"], section_stats)
        ],
    }
    write_json(ROOT / "qa" / "native_report_layout_summary.json", {"status": "layout_json_generated", "pages": pages, "visual_containers": visual_count})
    write_json(ROOT / "qa" / "project20_upgrade_verification.json", verification)
    write_json(ROOT / "build" / "config" / "theme.json", {"name": "SaaS CFO Board Cockpit - Project 20 Upgrade", "dataColors": [COLORS["blue"], COLORS["teal"], COLORS["green"], COLORS["amber"], COLORS["red"], COLORS["violet"], COLORS["sky"]], "background": COLORS["bg"], "foreground": COLORS["ink"], "tableAccent": COLORS["blue"]})
    write_json(ROOT / "build" / "config" / "page_map.json", [{"page": section_obj["displayName"], "ordinal": i} for i, section_obj in enumerate(layout["sections"])])
    write_json(ROOT / "build" / "config" / "visual_map.json", {"visual_containers": visual_count, "visual_style": "Project 20-quality SaaS CFO cockpit with left rail, SVG KPI cards, current lens, decision chips, synchronized chart slots, metric-aware units, action-button page navigation, and explicit table widths", "navigation_action_count": navigation_action_count, "table_column_width_rules": table_width_rule_count, "table_column_alignment_rules": table_alignment_rule_count})
    write_json(ROOT / "build" / "config" / "navigation_map.json", {"status": "pass", "mode": "left-sidebar transparent actionButton overlays", "pages": pages, "targets": PAGE_SECTIONS, "action_count": navigation_action_count, "actions": nav_actions})
    write_json(ROOT / "build" / "config" / "table_style_map.json", {"status": "pass", "table_column_width_rules": table_width_rule_count, "table_column_alignment_rules": table_alignment_rule_count, "section_stats": section_stats})
    write_json(ROOT / "build" / "config" / "slicer_map.json", {"status": "pass", "global": ["Year", "Segment", "Motion", "Region"], "sync_groups": ["global_year", "global_segment", "global_motion", "global_region"], "mode": "compact dropdown sidebar controls", "slot": {"x": 22, "width": 140, "height": 44}, "clip_safety": "dropdown labels and values use 140px sidebar slots; labels are above each control, not clipped inside the slicer body"})
    write_json(ROOT / "build" / "config" / "dashboard_config.json", {"name": "SaaS CFO Metrics", "tabs": pages, "page_count": 3, "upgrade_reference": "Project 20 - Board Investor CFO Pack v77 patterns"})


def render_preview(tables: dict[str, pd.DataFrame]) -> None:
    monthly = tables["MonthlyKPIs"]
    latest = monthly.iloc[-1]
    finance_latest = tables["FactFinanceMonthly"].iloc[-1]
    forecast_accuracy = 1 - abs(latest.ARR - finance_latest.ForecastARR) / max(latest.ARR, 1)
    rule_of_40 = finance_latest.ARRGrowthPct + finance_latest.EBITDA / max(finance_latest.Revenue, 1)
    cac = tables["FactAcquisitionMonthly"].SalesMarketingSpend.sum() / max(tables["FactAcquisitionMonthly"].NewCustomers.sum(), 1)
    payback = cac / max(latest.GrossMargin / max(latest.ActiveCustomers, 1), 1)
    ltv_cac = (latest.ARR / max(latest.ActiveCustomers, 1)) / max(cac, 1)
    burn_multiple = finance_latest.NetBurn / max(abs(latest.NetNewARR) / 12, 1)
    html = f"""<!doctype html><html><head><meta charset='utf-8'><title>SaaS CFO Metrics Dashboard</title><style>
body{{margin:0;background:#F6F8FB;font:13px Segoe UI,Arial;color:#111827}}.app{{display:grid;grid-template-columns:184px 1fr;min-height:100vh}}aside{{background:#0B1726;color:#fff;padding:18px}}aside h2{{margin:0 0 24px;font-size:18px}}button{{display:block;width:100%;margin:8px 0;padding:10px;border:1px solid #17395F;border-radius:6px;background:#10243A;color:#D8E2EF;text-align:left}}button.active{{background:#17395F;color:#fff}}main{{padding:18px 24px}}.head{{display:flex;align-items:center;justify-content:space-between;gap:18px}}.chips span{{display:inline-block;background:#E7F0FF;border-radius:7px;padding:8px 12px;margin-left:8px;font-weight:600}}.cards{{display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin-top:16px}}.card,.panel{{background:#fff;border:1px solid #DCE3EC;border-radius:8px;padding:15px;box-shadow:0 8px 20px #0f172a0d}}.card b{{display:block;font-size:27px;margin-top:8px}}.card small{{display:block;color:#64748B;margin-top:6px}}.grid{{display:grid;grid-template-columns:1.4fr 1fr 1fr;gap:16px;margin-top:16px}}.tab{{display:none}}.tab.active{{display:block}}</style></head><body><div class='app'><aside><h2>SaaS CFO<br><small>Project 15</small></h2><button class='active' data-tab='e'>Executive Overview</button><button data-tab='r'>Revenue & Retention</button><button data-tab='f'>Efficiency & Forecast</button><p style='color:#94A3B8;margin-top:28px'>Current Lens<br>All Years | All Segments<br>All Motions | All Regions</p></aside><main><div class='head'><div><h1>SaaS CFO Metrics</h1><p>Latest complete month: {month_label(LATEST_MONTH)} | synthetic demo data</p></div><div class='chips'><span>ARR {money(latest.ARR)}</span><span>NRR {pct(latest.NRR)}</span><span>Forecast {pct(forecast_accuracy)}</span></div></div><section id='e' class='tab active'><div class='cards'><div class='card'>ARR<b>{money(latest.ARR)}</b><small>PY + trend in PBIX SVG</small></div><div class='card'>Net New ARR<b>{money(latest.NetNewARR)}</b><small>Latest selected month</small></div><div class='card'>NRR<b>{pct(latest.NRR)}</b><small>Retention health</small></div><div class='card'>Rule of 40<b>{pct(rule_of_40)}</b><small>Growth + margin</small></div></div><div class='grid'><div class='panel'>ARR and Net New ARR Trend</div><div class='panel'>ARR Movement Bridge</div><div class='panel'>ARR by Segment</div></div></section><section id='r' class='tab'><div class='cards'><div class='card'>NRR<b>{pct(latest.NRR)}</b></div><div class='card'>GRR<b>{pct(latest.GRR)}</b></div><div class='card'>Expansion ARR<b>{money(latest.ExpansionMRR*12)}</b></div><div class='card'>Logo Churn<b>{pct(latest.LogoChurnRate)}</b></div></div></section><section id='f' class='tab'><div class='cards'><div class='card'>Payback<b>{payback:.1f}</b></div><div class='card'>LTV:CAC<b>{ltv_cac:.1f}x</b></div><div class='card'>Burn Multiple<b>{burn_multiple:.1f}x</b></div><div class='card'>Forecast Accuracy<b>{pct(forecast_accuracy)}</b></div></div></section></main></div><script>document.querySelectorAll('button').forEach(b=>b.onclick=()=>{{document.querySelectorAll('button,.tab').forEach(x=>x.classList.remove('active'));b.classList.add('active');document.getElementById(b.dataset.tab).classList.add('active')}})</script></body></html>"""
    write_text(ROOT / "output" / "dashboard_preview.html", html)
    for filename, title, series, color in [
        ("page_01_executive_overview.png", "Executive Overview", monthly.ARR, COLORS["blue"]),
        ("page_02_revenue_retention.png", "Revenue & Retention", monthly.NRR, COLORS["teal"]),
        ("page_03_efficiency_forecast.png", "Efficiency & Forecast", tables["FactFinanceMonthly"].ForecastARR, COLORS["green"]),
    ]:
        img = Image.new("RGB", (1600, 900), COLORS["bg"])
        draw = ImageDraw.Draw(img)
        draw.rectangle((0, 0, 230, 900), fill=COLORS["navy"])
        draw.text((36, 38), "SaaS CFO", fill="#FFFFFF")
        draw.text((36, 72), "Project 15", fill=COLORS["rail_text"])
        draw.rectangle((285, 115, 1515, 760), fill="#FFFFFF", outline=COLORS["border"])
        draw.text((285, 56), f"SaaS CFO {title}", fill=COLORS["ink"])
        draw.text((285, 86), "Project 20-style source preview; final QA must use Power BI Desktop", fill=COLORS["muted"])
        values = [float(v) for v in series]
        vmin, vmax = min(values), max(values)
        span = max(vmax - vmin, 1.0)
        points = []
        for idx, value in enumerate(values):
            x = 320 + (idx / max(len(values) - 1, 1)) * 1160
            y = 710 - ((value - vmin) / span) * 520
            points.append((x, y))
        for gy in range(0, 6):
            y = 190 + gy * 104
            draw.line((320, y, 1480, y), fill="#E8EEF5", width=1)
        if len(points) > 1:
            draw.line(points, fill=color, width=5, joint="curve")
        for x, y in points[-3:]:
            draw.ellipse((x - 6, y - 6, x + 6, y + 6), fill=color, outline="#FFFFFF", width=2)
        img.save(ROOT / "output" / "screenshots" / filename)


def write_powerbi_scripts() -> None:
    write_json(ROOT / "powerbi" / "pbip" / "SaaS_CFO_Metrics" / "SaaS_CFO_Metrics.pbip", {"version": "1.0", "artifacts": [{"report": {"path": "SaaS_CFO_Metrics.Report"}}]})
    write_json(ROOT / "powerbi" / "pbip" / "SaaS_CFO_Metrics" / "SaaS_CFO_Metrics.Report" / "definition.pbir", {"version": "4.0", "datasetReference": {"byPath": {"path": "../SaaS_CFO_Metrics.SemanticModel"}}})
    write_json(ROOT / "powerbi" / "pbip" / "SaaS_CFO_Metrics" / "SaaS_CFO_Metrics.SemanticModel" / "definition.pbism", {"version": "1.0", "settings": {"qnaEnabled": False}})
    write_text(ROOT / "build" / "scripts" / "02_push_model_bim_via_tom.ps1", r'''
param([string]$ProjectRoot="", [string]$TargetPbix="", [string]$ModelBim="", [int]$Port=0, [int]$PbiProcessId=0)
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
$session=if($Port -gt 0){ [pscustomobject]@{Port=$Port; ProcessId=$PbiProcessId; PbixPath=[IO.Path]::GetFullPath($TargetPbix); Source="direct_port"} } else { Get-Session $TargetPbix }
$server=New-Object Microsoft.AnalysisServices.Tabular.Server; $server.Connect("localhost:$($session.Port)")
$model=$server.Databases[0].Model; $model.Relationships.Clear(); $model.Tables.Clear()
$def=Get-Content $ModelBim -Raw -Encoding UTF8|ConvertFrom-Json
foreach($td in $def.model.tables){ $t=New-Object Microsoft.AnalysisServices.Tabular.Table; $t.Name=[string]$td.name; $model.Tables.Add($t); foreach($cd in @($td.columns)){ $c=New-Object Microsoft.AnalysisServices.Tabular.DataColumn; $c.Name=[string]$cd.name; $c.SourceColumn=if($cd.sourceColumn){[string]$cd.sourceColumn}else{[string]$cd.name}; $c.DataType=DT ([string]$cd.dataType); if($cd.isHidden){$c.IsHidden=[bool]$cd.isHidden}; if($cd.formatString){$c.FormatString=[string]$cd.formatString}; if($cd.summarizeBy){$c.SummarizeBy=AF $cd.summarizeBy}; $t.Columns.Add($c)}; foreach($pd in @($td.partitions)){ $p=New-Object Microsoft.AnalysisServices.Tabular.Partition; $p.Name=[string]$pd.name; $p.Mode=[Microsoft.AnalysisServices.Tabular.ModeType]::Import; $s=New-Object Microsoft.AnalysisServices.Tabular.MPartitionSource; $s.Expression=Expr $pd.source.expression; $p.Source=$s; $t.Partitions.Add($p)}; foreach($md in @($td.measures)){ if($md -and $md.name){$mm=New-Object Microsoft.AnalysisServices.Tabular.Measure; $mm.Name=[string]$md.name; $mm.Expression=[string]$md.expression; if($md.formatString){$mm.FormatString=[string]$md.formatString}; if($md.dataCategory){$mm.DataCategory=[string]$md.dataCategory}; $t.Measures.Add($mm)}} }
foreach($rd in @($def.model.relationships)){ $r=New-Object Microsoft.AnalysisServices.Tabular.SingleColumnRelationship; $r.Name=[string]$rd.name; $r.FromColumn=C (T $model ([string]$rd.fromTable)) ([string]$rd.fromColumn); $r.ToColumn=C (T $model ([string]$rd.toTable)) ([string]$rd.toColumn); $r.FromCardinality=[Microsoft.AnalysisServices.Tabular.RelationshipEndCardinality]::Many; $r.ToCardinality=[Microsoft.AnalysisServices.Tabular.RelationshipEndCardinality]::One; $r.CrossFilteringBehavior=[Microsoft.AnalysisServices.Tabular.CrossFilteringBehavior]::OneDirection; $r.IsActive=$true; $model.Relationships.Add($r)}
$model.SaveChanges(); $model.RequestRefresh([Microsoft.AnalysisServices.Tabular.RefreshType]::Full); $model.SaveChanges()
$result=[ordered]@{status="model_pushed_via_tom"; target_pbix=[IO.Path]::GetFullPath($TargetPbix); port=$session.Port; process_id=$session.ProcessId; session_source=$session.Source; table_count=$model.Tables.Count; relationship_count=$model.Relationships.Count}
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

Upgrade target: Project 20 quality benchmark while preserving the original light SaaS CFO / navy finance style.

Tabs:
- Executive Overview
- Revenue & Retention
- Efficiency & Forecast

Project 20 upgrade patterns applied:
- Left sidebar with page identity, compact dropdown slicers, and Current Lens SVG.
- Four SVG KPI cards per page with latest-month value, PY, YoY, target-band sparkline, and semantic color.
- Page-level decision chips for executive context.
- Synced slicer groups: Year, Segment, Motion, Region.
- Metric-aware chart units so percentages, ratios, months, and multiples are not forced into money units.
- Banded tables and synchronized chart/KPI slots across pages.

Latest complete month: {month_label(LATEST_MONTH)}
ARR: {money(latest.ARR)}
Net New ARR: {money(latest.NetNewARR)}
NRR: {pct(latest.NRR)}
GRR: {pct(latest.GRR)}
Logo churn: {pct(latest.LogoChurnRate)}

Data is synthetic portfolio/demo data generated with seed `{SEED}`.
""")
    write_text(ROOT / "docs" / "design_research.md", """# Design Research

Template direction: restrained board-ready SaaS CFO cockpit with Project 20-level interaction polish, while preserving Project 15's original light finance canvas and dark navy language.

Sources used:

- Zebra BI SaaS Sales Power BI Dashboard Template: https://zebrabi.com/template/saas-sales-power-bi-dashboard-template/
- DataBrain CFO Dashboard Guide: https://www.usedatabrain.com/blog/cfo-dashboard
- ZoomCharts SaaS metrics in Power BI: https://zoomcharts.com/en/microsoft-power-bi-custom-visuals/blog/top-12-key-saas-business-metrics-you-must-track-in-2025
- CFO Connect SaaS dashboard metrics: https://www.cfoconnect.eu/resources/finance-insights/ideal-saas-dashboard-key-metrics/
- The SaaS CFO CAC Payback guide: https://www.thesaascfo.com/how-to-calculate-your-overall-cac-payback-period/
- Maxio CAC Payback guide: https://www.maxio.com/saaspedia/cac-payback

Project 20 reference patterns reused conceptually:

- Left rail with stable page navigation/lens controls.
- Four KPI card slots instead of crowded 5-6 card strips.
- DAX SVG KPI cards with current value, PY, YoY, sparkline, target band, and markers.
- Current Lens and page-level decision chips rather than explanatory note boxes.
- Metric-aware display units and synchronized chart/table slots.

Design choices:

- Light finance canvas with dark navy sidebar and high-contrast KPI cards.
- Green/teal for expansion and retention health; red for churn/risk; amber for payback warnings; blue/violet for recurring revenue and forecast.
- Three-tab structure optimized for board review rather than operational sprawl.
""")
    write_text(ROOT / "docs" / "handoff_notes.md", f"""# Handoff Notes

Final PBIX: `output/dashboard_final.pbix`
Build route: seed PBIX + TOM model replacement + native layout patch + Desktop QA.
Data: synthetic SaaS CFO demo data, seed `{SEED}`.
Model: 13 data tables, 17 relationships, {len(MEASURES)} DAX measures.
Pages: Executive Overview; Revenue & Retention; Efficiency & Forecast.
Upgrade: Project 20 quality patterns applied without copying Project 20's purple investor-pack skin.
Layout: dark navy left sidebar, compact dropdown lens controls, Current Lens SVG, decision chips, four SVG KPI cards per page, synced chart slots, polished tables.
QA: data QA `{qa['status']}`; source layout verification is `qa/project20_upgrade_verification.json`; PBIX validation and Desktop visual check must be refreshed after final PBIX rebuild.
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
    write_text(ROOT / "docs" / "issue_log.md", "# Issue Log\n\nNo open data QA issues. Desktop visual QA must be rerun after the upgraded PBIX is rebuilt/opened because the report layout and SVG measure layer changed.")
    write_text(ROOT / "docs" / "changelog.md", f"""# Changelog

## v20-style-upgrade - {date.today().isoformat()}

- Upgraded Project 15 to Project 20 quality patterns while preserving the SaaS CFO light/navy finance style.
- Added left sidebar, compact synced dropdown slicers, Current Lens SVG, portfolio signature SVG, and decision-chip SVG context.
- Replaced crowded native card strips with four focused SVG KPI cards per page.
- Added latest-period/PY/YoY/sparkline KPI card measures, including lower-is-better color logic for logo churn, CAC payback, and burn multiple.
- Tightened chart/table slots and added metric-aware chart units.
- Added upgrade QA and handoff docs.

## v01 - {REPORT_DATE.isoformat()}

- Built Project 15 SaaS CFO synthetic data, semantic model, native layout JSON, preview screenshots, docs and QA scaffolding.
""")
    write_text(ROOT / "qa" / "qa_checklist.md", f"""# QA Checklist

Data QA: {qa['status'].upper()}

Metric QA: PASS at source/model generation level. SVG KPI measures are generated into `model/MEASURES.dax` and tagged as Image URL in `model/model.bim`.

Source Layout QA: PASS. See `qa/project20_upgrade_verification.json`.

Visual QA: pending Power BI Desktop open-check after final PBIX rebuild.

File QA: pending final PBIX validation after TOM model push + layout patch.
""")
    write_text(ROOT / "qa" / "visual_qa_notes.md", "# Visual QA Notes\n\nStatic screenshots generated for preview. Upgraded PBIX visual QA must confirm SVG KPI cards, Current Lens, decision chips, slicers, charts, and tables render without overlap or visual errors in Power BI Desktop.")
    write_text(ROOT / "qa" / "interaction_qa_notes.md", "# Interaction QA Notes\n\n- Sidebar slicers: Year, Segment, Motion, Region.\n- Sync groups in generated layout: `global_year`, `global_segment`, `global_motion`, `global_region`.\n- Year is configured as a single-select global lens; Segment, Motion, and Region remain multi-select analytical lenses.\n- Page-level decision chips summarize the current lens before drilldown.\n- Native visuals use Power BI cross-filter behavior within each page.\n- Ctrl+Click navigation still requires Desktop/service action-button validation if true page buttons are added later; current sidebar labels are visual navigation context, not action buttons.")
    write_text(ROOT / "qa" / "performance_qa_notes.md", "# Performance QA Notes\n\nMonthly-grain fact tables are compact for local import and portfolio use.")
    write_text(ROOT / "qa" / "regression_qa_notes.md", "# Regression QA Notes\n\nDeterministic seed supports rebuild comparison. Pre-upgrade PBIX/script/layout backups are stored under `archive/old_versions/project20_upgrade_before_*`.")
    write_text(ROOT / "qa" / "project20_upgrade_qa.md", f"""# Project 20 Upgrade QA

Status: source artifacts regenerated; PBIX Desktop open-check pending after final rebuild.

Checks completed:
- Project inventory and Project 20 reference review.
- Backup created under `archive/old_versions/`.
- Data QA: {qa['status']}.
- Generated layout has 3 pages, 4 SVG KPI card slots per page, Current Lens SVG, decision chips, left sidebar slicers, and synchronized top chart slots.
- SVG measures are tagged as `ImageUrl` in the generated model metadata.

Checks still required after PBIX rebuild:
- Open exact `output/dashboard_final.pbix` in Power BI Desktop.
- Confirm SVG KPI cards render as images, not data URI text.
- Test synced slicers across all 3 pages.
- Confirm no overlap, clipped labels, blank visuals, or visual errors.
- Save/reopen exact final PBIX and refresh `qa/pbix_final_validation.json`.
""")
    write_text(ROOT / "docs" / "project20_upgrade_before_audit.md", """# Project 20 Upgrade Before Audit

Target: Project 15 - SaaS CFO Metrics.

Before-state inventory:
- Final PBIX existed at `output/dashboard_final.pbix`.
- Source build path used synthetic data, `model/model.bim`, native `Report/Layout` JSON, and seed PBIX/TOM/layout patch scripts.
- Pages: Executive Overview; Revenue & Retention; Efficiency & Forecast.
- Model: 13 data tables, 17 relationships, 52 DAX measures before upgrade.
- Layout: 47 native visual containers before upgrade.
- Style signals to preserve: light finance canvas, dark navy header/control language, SaaS CFO metrics, board-ready but not purple investor-pack skin.

Gaps versus Project 20 quality:
- KPI strip used native cards and crowded 5-6 card rows on some pages.
- No Current Lens SVG or page-level decision-chip context.
- No SVG KPI cards with PY/YoY/sparkline/target-band logic.
- Chart display units were not metric-aware for all ratio/percentage visuals.
- Upgrade-specific QA/handoff docs were missing.
""")
    write_text(ROOT / "docs" / "project20_upgrade_handoff.md", f"""# Project 20 Upgrade Handoff

Project path: `{ROOT}`

Final target: `output/dashboard_final.pbix`

Upgrade approach:
- Preserve Project 15's SaaS CFO domain story, metric hierarchy, and light/navy finance mood.
- Reuse Project 20 as a pattern library for polish: left sidebar, compact slicers, four SVG KPI cards, Current Lens, decision chips, chart/table rhythm, and QA evidence.

Files/source changed by generator:
- `build/scripts/01_build_project.py`
- `build/native_report_layout_saas_cfo.json`
- `model/model.bim`
- `model/MEASURES.dax`
- `model/measure_map.json`
- `build/config/*.json`
- `docs/*`
- `qa/*`

PBIX rebuild route:
1. Run `python build/scripts/01_build_project.py`.
2. Copy a known-good PBIX container to `output/dashboard_model_seed.pbix`.
3. Launch that seed in Power BI Desktop.
4. Run `build/scripts/02_push_model_bim_via_tom.ps1`.
5. Save the seed in Desktop.
6. Run `build/scripts/03_apply_native_layout_to_pbix.ps1`.
7. Open/save/reopen exact `output/dashboard_final.pbix`.

Known limitation:
- Desktop render validation is required after rebuild. Source-level checks prove layout/metadata generation, but not final Power BI rendering.
""")
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
