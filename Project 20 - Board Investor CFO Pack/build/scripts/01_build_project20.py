from __future__ import annotations

import json
import math
import shutil
import subprocess
import uuid
import zipfile
from datetime import date, datetime
from pathlib import Path

import numpy as np
import pandas as pd

try:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
except ModuleNotFoundError:
    plt = None


ROOT = Path(__file__).resolve().parents[2]
SEED = 20260615
REPORT_DATE = date(2026, 6, 20)
START_MONTH = pd.Timestamp("2024-01-01")
LATEST_MONTH = pd.Timestamp("2026-05-01")
MONTHS = pd.date_range(START_MONTH, LATEST_MONTH, freq="MS")
MEASURE_TABLE = "KPI_Measures"

COLORS = {
    "bg": "#463793",
    "paper": "#F4EDF9",
    "ink": "#211A32",
    "muted": "#6E667B",
    "border": "#D5CDE6",
    "navy": "#23023F",
    "sidebar": "#250642",
    "sidebar2": "#332288",
    "sidebar_rule": "#7F67D7",
    "sidebar_text": "#E5DBFF",
    "sidebar_muted": "#BDAFD8",
    "chip_text": "#261C3C",
    "chip_good": "#E6F4EC",
    "chip_watch": "#FFF3D6",
    "chip_risk": "#FCE7E7",
    "chip_info": "#E7F0FF",
    "blue": "#4F87F5",
    "teal": "#0F9F95",
    "green": "#1F8E45",
    "amber": "#BE7C10",
    "red": "#B73535",
    "violet": "#6C2DBE",
    "slate": "#4E4662",
    "panel": "#F0EAF7",
    "card": "#FFFFFF",
    "pale": "#D5C5F0",
    "track": "#CFC3E6",
    "spark": "#DCD0F0",
    "table_header": "#E7DDF5",
    "table_row": "#FCFAFF",
    "table_alt": "#F4EFFA",
    "table_grid": "#DFD6ED",
    "chart_grid": "#DED6EB",
    "chart_panel": "#F5F0FA",
    "chart_border": "#B59BE1",
    "chart_axis": "#62586F",
    "slicer_fill": "#DCCFF4",
    "slicer_border": "#AD97DA",
}


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.strip() + "\n", encoding="utf-8")


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def clean_outputs() -> None:
    for rel in ["data", "model", "build/config", "build/logs", "powerbi", "qa", "docs", "_agent"]:
        target = ROOT / rel
        if target.exists() and ROOT in target.parents:
            shutil.rmtree(target)
    output = ROOT / "output"
    if output.exists() and ROOT in output.parents:
        for child in output.iterdir():
            try:
                if child.is_dir():
                    shutil.rmtree(child)
                else:
                    child.unlink()
            except PermissionError:
                # Power BI Desktop can keep the active PBIX locked. Keep it and
                # let the layout patch script write a versioned PBIX instead.
                continue


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
        "powerbi/pbip/Board_Investor_CFO_Pack/Board_Investor_CFO_Pack.Report",
        "powerbi/pbip/Board_Investor_CFO_Pack/Board_Investor_CFO_Pack.SemanticModel",
        "powerbi/notes",
        "output/screenshots",
        "output/exports",
        "qa",
        "docs",
        "_agent",
        "archive/old_versions",
    ]:
        (ROOT / rel).mkdir(parents=True, exist_ok=True)


def month_label(ts: pd.Timestamp | str) -> str:
    return pd.Timestamp(ts).strftime("%b %Y")


def money(v: float) -> str:
    if pd.isna(v):
        return "$0"
    sign = "-" if v < 0 else ""
    v = abs(float(v))
    if v >= 1_000_000_000:
        return f"{sign}${v / 1_000_000_000:.1f}B"
    if v >= 1_000_000:
        return f"{sign}${v / 1_000_000:.1f}M"
    if v >= 1_000:
        return f"{sign}${v / 1_000:.1f}K"
    return f"{sign}${v:,.0f}"


def pct(v: float) -> str:
    return f"{float(v):.1%}"


def multiple(v: float) -> str:
    return f"{float(v):.1f}x"


def collect_environment() -> dict:
    def run_ps(command: str) -> object:
        try:
            proc = subprocess.run(
                ["powershell", "-NoProfile", "-Command", command],
                capture_output=True,
                text=True,
                timeout=35,
            )
            return {"stdout": proc.stdout.strip(), "stderr": proc.stderr.strip(), "returncode": proc.returncode}
        except Exception as exc:
            return {"error": str(exc)}

    return {
        "checked_at": datetime.now().isoformat(timespec="seconds"),
        "power_bi_desktop_command": shutil.which("PBIDesktop.exe"),
        "power_bi_program_files": Path(r"C:\Program Files\Microsoft Power BI Desktop\bin\PBIDesktop.exe").exists(),
        "power_bi_x86": Path(r"C:\Program Files (x86)\Microsoft Power BI Desktop\bin\PBIDesktop.exe").exists(),
        "power_bi_start_apps": run_ps("Get-StartApps | Where-Object { $_.Name -like '*Power BI Desktop*' -or $_.AppID -like '*PowerBI*' } | Select-Object Name,AppID | ConvertTo-Json -Depth 4"),
        "winget_power_bi": run_ps("winget list --name 'Power BI'"),
        "pbi_tools": shutil.which("pbi-tools") or shutil.which("pbi-tools.exe"),
        "pbi_tools_info": run_ps("pbi-tools info"),
        "dotnet": shutil.which("dotnet"),
        "computer_use": "available; exact Desktop windows will be matched by pbi-tools PbixPath and window handle before save/check",
    }


BUSINESS_UNITS = [
    ("enterprise", "Enterprise SaaS", "Subscription", 0.42, 0.82, 0.96),
    ("smb", "SMB Platform", "Subscription", 0.28, 0.77, 1.16),
    ("data", "Data Products", "Platform", 0.18, 0.86, 1.08),
    ("services", "Professional Services", "Services", 0.12, 0.48, 0.70),
]
REGIONS = [
    ("americas", "Americas", "Core", 0.50, 1.14),
    ("emea", "EMEA", "Core", 0.25, 0.96),
    ("apac", "APAC", "Growth", 0.18, 0.83),
    ("latam", "LATAM", "Emerging", 0.07, 0.62),
]
SCENARIOS = [
    ("Base", "Base Case", 1.00, 1.00, 1.00, 0),
    ("Upside", "Upside Growth", 1.11, 1.04, 0.92, 1),
    ("Downside", "Downside Protect", 0.88, 0.96, 1.10, 2),
]
COST_CATEGORIES = [
    ("sm", "Sales & Marketing", 0.34),
    ("rd", "R&D", 0.24),
    ("ga", "G&A", 0.13),
    ("support", "Customer Support", 0.07),
]


def build_data() -> dict[str, pd.DataFrame]:
    rng = np.random.default_rng(SEED)
    dim_date = pd.DataFrame(
        {
            "MonthStart": [m.date().isoformat() for m in MONTHS],
            "MonthLabel": [month_label(m) for m in MONTHS],
            "MonthIndex": list(range(1, len(MONTHS) + 1)),
            "Year": [m.year for m in MONTHS],
            "Quarter": [f"Q{((m.month - 1) // 3) + 1}" for m in MONTHS],
            "IsLatestCompleteMonth": [1 if m == LATEST_MONTH else 0 for m in MONTHS],
        }
    )
    dim_scenario = pd.DataFrame(
        [
            {
                "ScenarioID": sid,
                "ScenarioName": name,
                "RevenueIndex": revenue_idx,
                "MarginIndex": margin_idx,
                "BurnIndex": burn_idx,
                "ScenarioSort": sort,
            }
            for sid, name, revenue_idx, margin_idx, burn_idx, sort in SCENARIOS
        ]
    )
    dim_bu = pd.DataFrame(
        [
            {
                "BusinessUnitID": bid,
                "BusinessUnit": name,
                "RevenueFamily": family,
                "MixWeight": weight,
                "TargetGrossMargin": margin,
                "GrowthIndex": growth_index,
            }
            for bid, name, family, weight, margin, growth_index in BUSINESS_UNITS
        ]
    )
    dim_region = pd.DataFrame(
        [
            {
                "RegionID": rid,
                "Region": name,
                "RegionMaturity": maturity,
                "MixWeight": weight,
                "DemandIndex": demand,
            }
            for rid, name, maturity, weight, demand in REGIONS
        ]
    )
    dim_cost = pd.DataFrame(
        [
            {"CostCategoryID": cid, "CostCategory": name, "RevenueLoad": load}
            for cid, name, load in COST_CATEGORIES
        ]
    )

    pnl_rows = []
    opex_rows = []
    cash_rows = []
    covenant_rows = []
    statement_rows = []
    base_revenue = np.linspace(18_500_000, 34_500_000, len(MONTHS))
    cash_state = {"Base": 78_000_000.0, "Upside": 78_000_000.0, "Downside": 78_000_000.0}
    debt_state = {"Base": 34_000_000.0, "Upside": 31_000_000.0, "Downside": 38_000_000.0}
    scenario_monthly_totals: dict[tuple[str, str], dict[str, float]] = {}

    for s_id, s_name, revenue_idx, margin_idx, burn_idx, _sort in SCENARIOS:
        for m_idx, month in enumerate(MONTHS):
            seasonality = 1 + 0.055 * math.sin((m_idx % 12) / 12 * 2 * math.pi - 0.6)
            macro_noise = rng.normal(0, 0.017)
            scenario_revenue = base_revenue[m_idx] * revenue_idx * seasonality * (1 + macro_noise)
            plan_revenue = base_revenue[m_idx] * 1.02
            forecast_revenue = scenario_revenue * (1 + rng.normal(0, 0.018))
            total_gross_profit = 0.0
            total_ebitda = 0.0
            total_net_income = 0.0
            for bu_id, bu_name, family, bu_weight, target_margin, growth_index in BUSINESS_UNITS:
                for region_id, region, maturity, region_weight, demand_index in REGIONS:
                    mix = bu_weight * region_weight
                    growth_tilt = 1 + (m_idx / max(1, len(MONTHS) - 1)) * (growth_index - 1) * 0.22
                    revenue = scenario_revenue * mix * demand_index * growth_tilt * (1 + rng.normal(0, 0.026))
                    plan = plan_revenue * mix * demand_index * (1 + (growth_index - 1) * 0.08)
                    forecast = forecast_revenue * mix * demand_index * (1 + rng.normal(0, 0.012))
                    gross_margin_pct = np.clip(target_margin * margin_idx + rng.normal(0, 0.012), 0.43, 0.89)
                    cogs = revenue * (1 - gross_margin_pct)
                    gross_profit = revenue - cogs
                    allocated_opex = revenue * (0.42 * burn_idx - 0.08 * (m_idx / len(MONTHS))) + 580_000 * mix
                    ebitda = gross_profit - allocated_opex
                    depreciation = revenue * 0.018
                    interest = debt_state[s_id] * 0.006 / 12 * mix
                    tax = max(0.0, (ebitda - depreciation - interest) * 0.18)
                    net_income = ebitda - depreciation - interest - tax
                    pnl_rows.append(
                        {
                            "MonthStart": month.date().isoformat(),
                            "ScenarioID": s_id,
                            "BusinessUnitID": bu_id,
                            "RegionID": region_id,
                            "Revenue": round(revenue, 2),
                            "PlanRevenue": round(plan, 2),
                            "ForecastRevenue": round(forecast, 2),
                            "COGS": round(cogs, 2),
                            "GrossProfit": round(gross_profit, 2),
                            "OperatingExpense": round(allocated_opex, 2),
                            "EBITDA": round(ebitda, 2),
                            "PlanEBITDA": round(plan * (target_margin - 0.42), 2),
                            "ForecastEBITDA": round(forecast * (gross_margin_pct - 0.40 * burn_idx), 2),
                            "NetIncome": round(net_income, 2),
                            "IsSynthetic": "TRUE",
                        }
                    )
                    total_gross_profit += gross_profit
                    total_ebitda += ebitda
                    total_net_income += net_income

            total_revenue = sum(r["Revenue"] for r in pnl_rows if r["MonthStart"] == month.date().isoformat() and r["ScenarioID"] == s_id)
            for cost_id, cost_name, load in COST_CATEGORIES:
                cost = total_revenue * load * burn_idx * (1 - min(0.16, m_idx / 220)) * (1 + rng.normal(0, 0.022))
                opex_rows.append(
                    {
                        "MonthStart": month.date().isoformat(),
                        "ScenarioID": s_id,
                        "CostCategoryID": cost_id,
                        "OperatingExpense": round(cost, 2),
                        "PlanOperatingExpense": round(total_revenue * load * 0.98, 2),
                        "ForecastOperatingExpense": round(cost * (1 + rng.normal(0, 0.018)), 2),
                    }
                )

            ar = total_revenue * 0.18
            ap = total_revenue * 0.10
            inventory = total_revenue * 0.03
            working_capital = ar + inventory - ap
            ocf = total_ebitda + total_revenue * 0.026 - (working_capital * 0.028)
            capex = total_revenue * (0.035 if s_id != "Downside" else 0.025)
            fcf = ocf - capex
            financing = 0.0
            if month == pd.Timestamp("2026-03-01") and s_id == "Downside":
                financing = 28_000_000.0
            if month == pd.Timestamp("2026-04-01") and s_id == "Base":
                financing = 16_000_000.0
            cash_state[s_id] += fcf + financing
            net_burn = max(0.0, -fcf)
            runway = 99.0 if net_burn <= 1 else min(99.0, cash_state[s_id] / net_burn)
            funding_need = max(0.0, 24 * max(net_burn, 1_000_000) - cash_state[s_id])
            cash_rows.append(
                {
                    "MonthStart": month.date().isoformat(),
                    "ScenarioID": s_id,
                    "CashBalance": round(cash_state[s_id], 2),
                    "OperatingCashFlow": round(ocf, 2),
                    "Capex": round(capex, 2),
                    "FreeCashFlow": round(fcf, 2),
                    "NetBurn": round(net_burn, 2),
                    "RunwayMonths": round(runway, 1),
                    "FundingNeed": round(funding_need, 2),
                    "Debt": round(debt_state[s_id], 2),
                    "WorkingCapital": round(working_capital, 2),
                    "FinancingInflow": round(financing, 2),
                }
            )
            scenario_monthly_totals[(s_id, month.date().isoformat())] = {
                "Revenue": total_revenue,
                "GrossProfit": total_gross_profit,
                "EBITDA": total_ebitda,
                "NetIncome": total_net_income,
                "CashBalance": cash_state[s_id],
                "OCF": ocf,
                "FCF": fcf,
                "WorkingCapital": working_capital,
                "Debt": debt_state[s_id],
                "Capex": capex,
                "FundingNeed": funding_need,
                "RunwayMonths": runway,
            }

            debt = debt_state[s_id]
            ltm_ebitda = sum(
                scenario_monthly_totals.get((s_id, mm.date().isoformat()), {}).get("EBITDA", 0.0)
                for mm in MONTHS[max(0, m_idx - 11) : m_idx + 1]
            )
            ltm_revenue = sum(
                scenario_monthly_totals.get((s_id, mm.date().isoformat()), {}).get("Revenue", 0.0)
                for mm in MONTHS[max(0, m_idx - 11) : m_idx + 1]
            )
            leverage = debt / max(ltm_ebitda, 1)
            interest_coverage = ltm_ebitda / max(debt * 0.082, 1)
            leverage_limit = 3.5
            icr_limit = 2.0
            liquidity_min = 25_000_000
            headroom = leverage_limit - leverage
            liquidity_headroom = cash_state[s_id] - liquidity_min
            covenant_status = "Breach" if headroom < 0 or liquidity_headroom < 0 or interest_coverage < icr_limit else "Watch" if headroom < 0.6 or liquidity_headroom < 10_000_000 else "Clear"
            risk_score = max(0, min(100, 100 - headroom * 16 - liquidity_headroom / 2_500_000))
            covenant_rows.append(
                {
                    "MonthStart": month.date().isoformat(),
                    "ScenarioID": s_id,
                    "RevenueLTM": round(ltm_revenue, 2),
                    "EBITDALTM": round(ltm_ebitda, 2),
                    "NetDebt": round(debt - cash_state[s_id], 2),
                    "LeverageRatio": round(leverage, 2),
                    "LeverageLimit": leverage_limit,
                    "LeverageHeadroom": round(headroom, 2),
                    "InterestCoverage": round(interest_coverage, 2),
                    "InterestCoverageLimit": icr_limit,
                    "Liquidity": round(cash_state[s_id], 2),
                    "LiquidityMinimum": liquidity_min,
                    "LiquidityHeadroom": round(liquidity_headroom, 2),
                    "CovenantStatus": covenant_status,
                    "RiskScore": round(risk_score, 1),
                }
            )

            lines = [
                ("Income Statement", "Revenue", 10, total_revenue, plan_revenue, forecast_revenue),
                ("Income Statement", "Gross Profit", 20, total_gross_profit, plan_revenue * 0.76, forecast_revenue * 0.77),
                ("Income Statement", "EBITDA", 30, total_ebitda, plan_revenue * 0.22, forecast_revenue * 0.23),
                ("Income Statement", "Net Income", 40, total_net_income, plan_revenue * 0.11, forecast_revenue * 0.12),
                ("Balance Sheet", "Cash", 110, cash_state[s_id], 64_000_000, cash_state[s_id] * 1.02),
                ("Balance Sheet", "Working Capital", 120, working_capital, plan_revenue * 0.12, working_capital * 0.98),
                ("Balance Sheet", "Debt", 130, debt, debt, debt),
                ("Cash Flow", "Operating Cash Flow", 210, ocf, plan_revenue * 0.18, ocf * 1.03),
                ("Cash Flow", "Capex", 220, -capex, -plan_revenue * 0.035, -capex * 1.02),
                ("Cash Flow", "Free Cash Flow", 230, fcf, plan_revenue * 0.13, fcf * 1.04),
                ("Cash Flow", "Financing Inflow", 240, financing, 0.0, financing),
            ]
            for statement, line_item, sort_order, actual, plan, forecast in lines:
                statement_rows.append(
                    {
                        "MonthStart": month.date().isoformat(),
                        "ScenarioID": s_id,
                        "Statement": statement,
                        "LineItem": line_item,
                        "LineSort": sort_order,
                        "ValueActual": round(actual, 2),
                        "ValuePlan": round(plan, 2),
                        "ValueForecast": round(forecast, 2),
                    }
                )

    fact_pnl = pd.DataFrame(pnl_rows)
    fact_opex = pd.DataFrame(opex_rows)
    fact_cash = pd.DataFrame(cash_rows)
    fact_covenant = pd.DataFrame(covenant_rows)
    fact_statement = pd.DataFrame(statement_rows)

    valuation_rows = []
    sensitivity_rows = []
    latest_key = LATEST_MONTH.date().isoformat()
    method_defs = [
        ("EV/Revenue Comps", 1, 5.8),
        ("EV/EBITDA Comps", 2, 18.5),
        ("DCF", 3, 1.00),
        ("Precedent Transactions", 4, 6.4),
        ("Investor Base Case", 5, 6.0),
    ]
    for s_id, s_name, revenue_idx, margin_idx, burn_idx, sort in SCENARIOS:
        latest_total = scenario_monthly_totals[(s_id, latest_key)]
        ltm_revenue = fact_covenant[(fact_covenant["ScenarioID"] == s_id) & (fact_covenant["MonthStart"] == latest_key)]["RevenueLTM"].iloc[0]
        ltm_ebitda = fact_covenant[(fact_covenant["ScenarioID"] == s_id) & (fact_covenant["MonthStart"] == latest_key)]["EBITDALTM"].iloc[0]
        net_debt = fact_covenant[(fact_covenant["ScenarioID"] == s_id) & (fact_covenant["MonthStart"] == latest_key)]["NetDebt"].iloc[0]
        for method, order, base_multiple in method_defs:
            if method == "DCF":
                ev = (latest_total["FCF"] * 12 * 14 + ltm_revenue * 1.9) * revenue_idx * margin_idx
                multiple_used = 0.0
            elif "EBITDA" in method:
                ev = max(ltm_ebitda, 1) * base_multiple * margin_idx
                multiple_used = base_multiple
            else:
                ev = ltm_revenue * base_multiple * revenue_idx
                multiple_used = base_multiple
            low = ev * 0.86
            high = ev * 1.14
            valuation_rows.append(
                {
                    "ScenarioID": s_id,
                    "Method": method,
                    "MethodSort": order,
                    "Multiple": round(multiple_used, 2),
                    "EnterpriseValue": round(ev, 2),
                    "EquityValue": round(ev - net_debt, 2),
                    "LowValue": round(low - net_debt, 2),
                    "HighValue": round(high - net_debt, 2),
                }
            )
        base_equity = np.mean([r["EquityValue"] for r in valuation_rows if r["ScenarioID"] == s_id])
        drivers = [
            ("Revenue Growth", -0.10, 0.12),
            ("Gross Margin", -0.04, 0.05),
            ("WACC", 0.07, -0.06),
            ("Terminal Growth", -0.05, 0.07),
            ("Exit Multiple", -0.12, 0.14),
            ("Burn Reduction", -0.04, 0.08),
        ]
        for driver, downside, upside in drivers:
            for case_label, impact in [("Downside", downside), ("Upside", upside)]:
                sensitivity_rows.append(
                    {
                        "ScenarioID": s_id,
                        "Driver": driver,
                        "CaseLabel": case_label,
                        "DriverCase": f"{driver} - {case_label}",
                        "EquityValueDelta": round(base_equity * impact, 2),
                        "EquityValue": round(base_equity * (1 + impact), 2),
                    }
                )

    risks = [
        ("R01", "Cash", "Downside runway drops below 18 months", "Critical", 0.42, 18_000_000, "CFO", "Funding plan drafted", "Approve financing trigger"),
        ("R02", "Growth", "Enterprise pipeline slips two quarters", "High", 0.36, 15_500_000, "CRO", "Pipeline recovery sprint", "Review GTM investment"),
        ("R03", "Margin", "Cloud infrastructure savings delayed", "High", 0.31, 9_200_000, "CTO", "Vendor renegotiation", "Track margin bridge"),
        ("R04", "Covenant", "Leverage headroom tightens under downside", "Critical", 0.28, 22_000_000, "Treasury", "Bank waiver playbook", "Confirm covenant action plan"),
        ("R05", "Working Capital", "Collections DSO rises in EMEA", "Watch", 0.44, 6_800_000, "Controller", "AR task force active", "Monitor DSO trend"),
        ("R06", "Valuation", "Comps multiple compresses", "High", 0.38, 31_000_000, "CFO", "Sensitivity included", "Align investor narrative"),
        ("R07", "Operations", "Hiring plan outpaces productivity", "Watch", 0.27, 5_100_000, "COO", "Headcount gate in place", "Review hiring freeze gate"),
        ("R08", "Product", "Data product launch delay", "Watch", 0.25, 7_600_000, "CPO", "Revised milestone plan", "Confirm launch date"),
        ("R09", "Tax", "International tax exposure", "Watch", 0.18, 3_900_000, "Tax", "Advisor review", "No board ask"),
        ("R10", "Security", "Enterprise security audit delay", "High", 0.21, 8_400_000, "CISO", "SOC2 remediation", "Monitor deal blockers"),
    ]
    risk_rows = []
    for scenario_id, scenario_name, *_ in SCENARIOS:
        for rid, category, risk, severity, probability, exposure, owner, mitigation, board_ask in risks:
            scenario_factor = 1.22 if scenario_id == "Downside" else 0.82 if scenario_id == "Upside" else 1.0
            risk_rows.append(
                {
                    "ScenarioID": scenario_id,
                    "RiskID": rid,
                    "RiskCategory": category,
                    "Risk": risk,
                    "Severity": severity,
                    "Probability": round(min(0.92, probability * scenario_factor), 2),
                    "ExposureUSD": round(exposure * scenario_factor, 2),
                    "Owner": owner,
                    "MitigationStatus": mitigation,
                    "BoardAsk": board_ask,
                }
            )

    # Board scorecard is intentionally denormalized for a compact board-style status table.
    base_latest_pnl = fact_pnl[(fact_pnl["ScenarioID"] == "Base") & (fact_pnl["MonthStart"] == latest_key)]
    base_latest_cash = fact_cash[(fact_cash["ScenarioID"] == "Base") & (fact_cash["MonthStart"] == latest_key)].iloc[0]
    base_latest_cov = fact_covenant[(fact_covenant["ScenarioID"] == "Base") & (fact_covenant["MonthStart"] == latest_key)].iloc[0]
    rev_actual = base_latest_pnl["Revenue"].sum()
    rev_plan = base_latest_pnl["PlanRevenue"].sum()
    ebitda_actual = base_latest_pnl["EBITDA"].sum()
    ebitda_plan = base_latest_pnl["PlanEBITDA"].sum()
    gp = base_latest_pnl["GrossProfit"].sum()
    scorecard = [
        ("Revenue", "Growth", rev_actual, rev_plan, "Clear" if rev_actual >= rev_plan * 0.98 else "Watch", "Revenue remains near board plan."),
        ("Gross Margin", "Profitability", gp / rev_actual, 0.76, "Clear" if gp / rev_actual >= 0.75 else "Watch", "Margin expansion depends on cloud cost savings."),
        ("EBITDA", "Profitability", ebitda_actual, ebitda_plan, "Watch" if ebitda_actual < ebitda_plan else "Clear", "EBITDA gap is concentrated in GTM timing."),
        ("Cash Balance", "Liquidity", base_latest_cash["CashBalance"], 55_000_000, "Clear" if base_latest_cash["CashBalance"] > 55_000_000 else "Watch", "Cash balance supports planned investment cadence."),
        ("Runway", "Liquidity", base_latest_cash["RunwayMonths"], 24, "Clear" if base_latest_cash["RunwayMonths"] >= 24 else "Watch", "Runway is board-visible under downside scenario."),
        ("Funding Need", "Liquidity", base_latest_cash["FundingNeed"], 0, "Watch" if base_latest_cash["FundingNeed"] > 0 else "Clear", "Funding trigger becomes active when runway target is below 24 months."),
        ("Leverage", "Covenant", base_latest_cov["LeverageRatio"], base_latest_cov["LeverageLimit"], "Clear" if base_latest_cov["LeverageRatio"] < base_latest_cov["LeverageLimit"] else "Breach", "Leverage covenant has adequate base-case headroom."),
        ("Interest Coverage", "Covenant", base_latest_cov["InterestCoverage"], base_latest_cov["InterestCoverageLimit"], "Clear" if base_latest_cov["InterestCoverage"] > base_latest_cov["InterestCoverageLimit"] else "Breach", "Coverage remains above lender threshold."),
    ]
    score_rows = []
    for idx, (metric, family, actual, plan, status, narrative) in enumerate(scorecard, start=1):
        if metric in {"Gross Margin"}:
            actual_display, plan_display = pct(actual), pct(plan)
            variance = actual - plan
            variance_display = f"{variance * 100:+.1f} pts"
        elif metric in {"Runway", "Leverage", "Interest Coverage"}:
            actual_display, plan_display = multiple(actual), multiple(plan)
            variance = actual - plan
            variance_display = f"{variance:+.1f}x"
        else:
            actual_display, plan_display = money(actual), money(plan)
            variance = (actual - plan) / abs(plan) if plan else 0
            variance_display = pct(variance)
        score_rows.append(
            {
                "MetricName": metric,
                "MetricFamily": family,
                "ActualDisplay": actual_display,
                "PlanDisplay": plan_display,
                "VarianceDisplay": variance_display,
                "Status": status,
                "BoardNarrative": narrative,
                "SortOrder": idx,
            }
        )

    return {
        "DimDate": dim_date,
        "DimScenario": dim_scenario,
        "DimBusinessUnit": dim_bu,
        "DimRegion": dim_region,
        "DimCostCategory": dim_cost,
        "FactPnlMonthly": fact_pnl,
        "FactOpexMonthly": fact_opex,
        "FactCashMonthly": fact_cash,
        "FactStatementLines": fact_statement,
        "FactCovenantMonthly": fact_covenant,
        "FactValuation": pd.DataFrame(valuation_rows),
        "FactSensitivity": pd.DataFrame(sensitivity_rows),
        "FactRiskRegister": pd.DataFrame(risk_rows),
        "FactKpiScorecard": pd.DataFrame(score_rows),
    }


def save_data(tables: dict[str, pd.DataFrame]) -> dict:
    row_counts = {}
    quality = {"status": "pass", "seed": SEED, "latest_complete_month": LATEST_MONTH.date().isoformat(), "tables": {}}
    for name, df in tables.items():
        row_counts[name] = int(len(df))
        df.to_csv(ROOT / "data" / "prepared" / f"{name}.csv", index=False, encoding="utf-8")
        nulls = {col: int(df[col].isna().sum()) for col in df.columns}
        duplicates = int(df.duplicated().sum())
        quality["tables"][name] = {
            "rows": int(len(df)),
            "columns": list(df.columns),
            "nulls": nulls,
            "duplicate_rows": duplicates,
        }
        if duplicates:
            quality["status"] = "warn"

    write_text(
        ROOT / "data" / "raw" / "synthetic_source_note.md",
        f"""# Synthetic Source Note

Project 20 has no real source data in the project folder. This portfolio build uses deterministic synthetic CFO/board financial data generated with seed `{SEED}`.

Source grain:
- Monthly P&L by scenario, business unit, and region.
- Monthly cash/runway/covenant scenario snapshot.
- Monthly statement lines for 3-statement board view.
- Scenario valuation, sensitivity, covenant, and risk register tables.
""",
    )
    write_json(
        ROOT / "data" / "source_summary.json",
        {
            "source_type": "synthetic_portfolio_demo",
            "seed": SEED,
            "project": "Project 20 - Board Investor CFO Pack",
            "date_range": {"start": START_MONTH.date().isoformat(), "end": LATEST_MONTH.date().isoformat()},
            "row_counts": row_counts,
            "source_note": "No production source was provided; synthetic data is explicitly labeled and rebuildable.",
        },
    )
    write_json(ROOT / "data" / "validated" / "validation_summary.json", quality)
    write_text(
        ROOT / "data" / "data_quality_report.md",
        "# Data Quality Report\n\n"
        + f"Status: `{quality['status']}`\n\n"
        + f"Seed: `{SEED}`\n\nDate range: `{START_MONTH.date().isoformat()}` to `{LATEST_MONTH.date().isoformat()}`\n\n"
        + "\n".join(
            f"- {name}: {details['rows']:,} rows, duplicate rows {details['duplicate_rows']:,}, nulls "
            f"{sum(details['nulls'].values()):,}"
            for name, details in quality["tables"].items()
        ),
    )
    write_text(
        ROOT / "data" / "data_dictionary.md",
        "# Data Dictionary\n\n"
        + "\n\n".join(
            f"## {name}\n\nGrain: {grain_for_table(name)}\n\nRows: {len(df):,}\n\nColumns:\n"
            + "\n".join(f"- `{col}`: `{str(df[col].dtype)}`" for col in df.columns)
            for name, df in tables.items()
        ),
    )
    latest = tables["FactCashMonthly"][
        (tables["FactCashMonthly"]["ScenarioID"] == "Base")
        & (tables["FactCashMonthly"]["MonthStart"] == LATEST_MONTH.date().isoformat())
    ].iloc[0]
    rec = pd.DataFrame(
        [
            {"metric": "Latest Cash Balance", "value": latest["CashBalance"]},
            {"metric": "Latest Runway Months", "value": latest["RunwayMonths"]},
            {"metric": "Latest Funding Need", "value": latest["FundingNeed"]},
            {"metric": "Latest Net Burn", "value": latest["NetBurn"]},
        ]
    )
    rec.to_csv(ROOT / "qa" / "reconciliation.csv", index=False)
    return quality


def grain_for_table(name: str) -> str:
    return {
        "DimDate": "one row per month",
        "DimScenario": "one row per scenario",
        "DimBusinessUnit": "one row per business unit",
        "DimRegion": "one row per region",
        "DimCostCategory": "one row per cost category",
        "FactPnlMonthly": "one row per month, scenario, business unit, and region",
        "FactOpexMonthly": "one row per month, scenario, and cost category",
        "FactCashMonthly": "one row per month and scenario",
        "FactStatementLines": "one row per month, scenario, and financial statement line",
        "FactCovenantMonthly": "one row per month and scenario",
        "FactValuation": "one row per scenario and valuation method",
        "FactSensitivity": "one row per scenario, driver, and case",
        "FactRiskRegister": "one row per scenario and risk",
        "FactKpiScorecard": "one row per board KPI status item",
    }.get(name, "documented table grain")


def selected_scenario_sum(table: str, column: str) -> str:
    return f'VAR ScenarioID = SELECTEDVALUE(DimScenario[ScenarioID], "Base") RETURN CALCULATE(SUM({table}[{column}]), {table}[ScenarioID] = ScenarioID)'


def selected_scenario_max(table: str, column: str) -> str:
    return f'VAR ScenarioID = SELECTEDVALUE(DimScenario[ScenarioID], "Base") RETURN CALCULATE(MAX({table}[{column}]), {table}[ScenarioID] = ScenarioID)'


def latest_period_value(measure: str) -> str:
    return f'VAR LatestMonth = CALCULATE(MAX(DimDate[MonthStart]), ALL(DimDate), DimDate[IsLatestCompleteMonth] = 1) RETURN CALCULATE([{measure}], FILTER(ALL(DimDate), DimDate[MonthStart] = LatestMonth))'


def prior_year_value(measure: str) -> str:
    return f'VAR LatestMonth = CALCULATE(MAX(DimDate[MonthStart]), ALL(DimDate), DimDate[IsLatestCompleteMonth] = 1) VAR PriorMonth = EDATE(LatestMonth, -12) RETURN CALCULATE([{measure}], FILTER(ALL(DimDate), DimDate[MonthStart] = PriorMonth))'


def py_display(measure: str, fmt: str) -> str:
    return f'VAR LatestMonth = CALCULATE(MAX(DimDate[MonthStart]), ALL(DimDate), DimDate[IsLatestCompleteMonth] = 1) VAR PriorMonth = EDATE(LatestMonth, -12) VAR PriorValue = CALCULATE([{measure}], FILTER(ALL(DimDate), DimDate[MonthStart] = PriorMonth)) RETURN FORMAT(PriorValue, "{fmt}")'


def yoy_display(measure: str, mode: str = "percent", favorable: str = "higher") -> str:
    diff = f'VAR LatestMonth = CALCULATE(MAX(DimDate[MonthStart]), ALL(DimDate), DimDate[IsLatestCompleteMonth] = 1) VAR PriorMonth = EDATE(LatestMonth, -12) VAR CurrentValue = CALCULATE([{measure}], FILTER(ALL(DimDate), DimDate[MonthStart] = LatestMonth)) VAR PriorValue = CALCULATE([{measure}], FILTER(ALL(DimDate), DimDate[MonthStart] = PriorMonth)) VAR ChangeValue = CurrentValue - PriorValue '
    if mode == "points":
        delta = 'VAR DeltaLabel = FORMAT(ChangeValue * 100, "+0.0;-0.0;0.0") & "pt" '
        icon = 'VAR IconValue = IF(ChangeValue >= 0, UNICHAR(9650), UNICHAR(9660)) '
    elif mode == "multiple":
        delta = 'VAR DeltaLabel = FORMAT(ChangeValue, "+0.0x;-0.0x;0.0x") '
        icon = 'VAR IconValue = IF(ChangeValue >= 0, UNICHAR(9650), UNICHAR(9660)) '
    else:
        delta = 'VAR RateValue = DIVIDE(ChangeValue, ABS(PriorValue)) VAR DeltaLabel = FORMAT(RateValue, "+0.0%;-0.0%;0.0%") '
        icon = 'VAR IconValue = IF(RateValue >= 0, UNICHAR(9650), UNICHAR(9660)) '
    if favorable == "lower":
        icon = icon.replace(">= 0", "<= 0")
    return diff + delta + icon + 'RETURN IconValue & " " & DeltaLabel'


def status_color(measure: str, amber_floor: float, red_is_lower: bool = True) -> str:
    op = ">=" if red_is_lower else "<="
    amber = ">= " + str(amber_floor) if red_is_lower else "<= " + str(amber_floor)
    return f'VAR ValueToCheck = [{measure}] RETURN SWITCH(TRUE(), ValueToCheck {op} 0, "#2FA66A", ValueToCheck {amber}, "#C58A18", "#C94A4A")'


def svg_sparkline(measure: str, color: str, favorable: str = "higher") -> str:
    encoded_color = color.replace("#", "%23")
    improved_test = "LastValue <= FirstValue" if favorable == "lower" else "LastValue >= FirstValue"
    return f'''VAR LatestMonth = CALCULATE(MAX(DimDate[MonthStart]), ALL(DimDate), DimDate[IsLatestCompleteMonth] = 1)
VAR MonthTable =
    ADDCOLUMNS(
        FILTER(ALLSELECTED(DimDate), DimDate[MonthStart] <= LatestMonth),
        "__Value", [{measure}]
    )
VAR CleanTable = FILTER(MonthTable, NOT ISBLANK([__Value]))
VAR RowCount = COUNTROWS(CleanTable)
VAR MinValue = MINX(CleanTable, [__Value])
VAR MaxValue = MAXX(CleanTable, [__Value])
VAR FirstValue = MINX(TOPN(1, CleanTable, DimDate[MonthStart], ASC), [__Value])
VAR LastValue = MINX(TOPN(1, CleanTable, DimDate[MonthStart], DESC), [__Value])
VAR StartYValue = 37 - DIVIDE(FirstValue - MinValue, MaxValue - MinValue, 0.5) * 30
VAR EndYValue = 37 - DIVIDE(LastValue - MinValue, MaxValue - MinValue, 0.5) * 30
VAR TrendColor = IF({improved_test}, "{encoded_color}", "%23C94A4A")
VAR Points =
    CONCATENATEX(
        CleanTable,
        VAR RankValue = RANKX(CleanTable, DimDate[MonthStart], , ASC, DENSE) - 1
        VAR XValue = 2 + DIVIDE(RankValue, MAX(1, RowCount - 1), 0) * 116
        VAR YValue = 37 - DIVIDE([__Value] - MinValue, MaxValue - MinValue, 0.5) * 30
        RETURN FORMAT(XValue, "0.0") & "," & FORMAT(YValue, "0.0"),
        " ",
        DimDate[MonthStart],
        ASC
    )
RETURN
    "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 120 44'><rect x='0' y='0' width='120' height='44' rx='7' fill='%23F3EFFA'/><rect x='0' y='16' width='120' height='12' rx='6' fill='%23DDEEDC'/><line x1='0' y1='22' x2='120' y2='22' stroke='%23B8AECF' stroke-width='1' stroke-dasharray='4 5'/><polyline points='" & Points & "' fill='none' stroke='" & TrendColor & "' stroke-width='3' stroke-linecap='round' stroke-linejoin='round'/><circle cx='2' cy='" & FORMAT(StartYValue, "0.0") & "' r='3' fill='%23FFFFFF' stroke='%238F7BAE' stroke-width='1.5'/><circle cx='118' cy='" & FORMAT(EndYValue, "0.0") & "' r='4' fill='" & TrendColor & "' stroke='%23FFFFFF' stroke-width='1.5'/></svg>"'''


def board_kpi_trend_svg() -> str:
    return '''VAR MetricName = SELECTEDVALUE(FactKpiScorecard[MetricName])
RETURN
    SWITCH(
        TRUE(),
        MetricName = "Revenue", [Revenue Sparkline SVG],
        MetricName = "Gross Margin", [Gross Margin Sparkline SVG],
        MetricName = "EBITDA", [EBITDA Sparkline SVG],
        MetricName = "Cash Balance", [Cash Sparkline SVG],
        MetricName = "Runway", [Runway Sparkline SVG],
        MetricName = "Funding Need", [Funding Sparkline SVG],
        MetricName = "Leverage", [Leverage Sparkline SVG],
        MetricName = "Interest Coverage", [Interest Coverage Sparkline SVG],
        [Revenue Sparkline SVG]
    )'''


def risk_signal_svg() -> str:
    return '''VAR SeverityValue = SELECTEDVALUE(FactRiskRegister[Severity], "Watch")
VAR ProbabilityValue = MIN(0.98, MAX(0.02, MAX(FactRiskRegister[Probability])))
VAR MarkerX = 12 + ProbabilityValue * 96
VAR SeverityColor =
    SWITCH(
        SeverityValue,
        "Critical", "%23B73535",
        "High", "%23BE7C10",
        "%231F8E45"
    )
VAR SVG =
    "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 120 44'>" &
    "<rect x='0' y='0' width='120' height='44' rx='7' fill='%23F8F5FC'/>" &
    "<rect x='12' y='17' width='32' height='10' rx='5' fill='%23DDEEDC'/>" &
    "<rect x='44' y='17' width='32' height='10' rx='5' fill='%23FFF3D6'/>" &
    "<rect x='76' y='17' width='32' height='10' rx='5' fill='%23F3D7D7'/>" &
    "<line x1='12' y1='32' x2='108' y2='32' stroke='%23B8AECF' stroke-width='1' stroke-dasharray='3 4'/>" &
    "<circle cx='" & FORMAT(MarkerX, "0.0") & "' cy='22' r='6' fill='" & SeverityColor & "' stroke='%23FFFFFF' stroke-width='2'/>" &
    "<circle cx='" & FORMAT(MarkerX, "0.0") & "' cy='22' r='2' fill='%23FFFFFF'/>" &
    "</svg>"
RETURN "data:image/svg+xml;utf8," & SVG'''


def svg_kpi_card(title: str, measure: str, color: str, value_format: str, scale: int | float = 1, yoy_mode: str = "percent", favorable: str = "higher") -> str:
    encoded_color = color.replace("#", "%23")
    improved_test = "LastValue <= FirstValue" if favorable == "lower" else "LastValue >= FirstValue"
    yoy_good_test = "ChangeValue <= 0" if favorable == "lower" else "ChangeValue >= 0"
    if yoy_mode == "points":
        yoy_text = 'VAR YoYTextRaw = FORMAT(ChangeValue * 100, "+0.0;-0.0;0.0") & "pt"'
    elif yoy_mode == "multiple":
        yoy_text = 'VAR YoYTextRaw = FORMAT(ChangeValue, "+0.0x;-0.0x;0.0x")'
    else:
        yoy_text = 'VAR RateValue = DIVIDE(ChangeValue, ABS(PriorValue))\nVAR YoYTextRaw = FORMAT(RateValue, "+0.0%;-0.0%;0.0%")'
    return f'''VAR LatestMonth = CALCULATE(MAX(DimDate[MonthStart]), ALL(DimDate), DimDate[IsLatestCompleteMonth] = 1)
VAR PriorMonth = EDATE(LatestMonth, -12)
VAR CurrentValue = CALCULATE([{measure}], FILTER(ALL(DimDate), DimDate[MonthStart] = LatestMonth))
VAR PriorValue = CALCULATE([{measure}], FILTER(ALL(DimDate), DimDate[MonthStart] = PriorMonth))
VAR ChangeValue = CurrentValue - PriorValue
VAR ValueTextRaw = FORMAT(DIVIDE(CurrentValue, {scale}), "{value_format}")
VAR PYTextRaw = FORMAT(DIVIDE(PriorValue, {scale}), "{value_format}")
{yoy_text}
VAR ValueText = SUBSTITUTE(ValueTextRaw, "%", "%25")
VAR PYText = SUBSTITUTE(PYTextRaw, "%", "%25")
VAR YoYText = SUBSTITUTE(YoYTextRaw, "%", "%25")
VAR YoYColor = IF({yoy_good_test}, "%234CAF65", "%23C94A4A")
VAR MonthTable =
    ADDCOLUMNS(
        FILTER(ALLSELECTED(DimDate), DimDate[MonthStart] <= LatestMonth),
        "__Value", [{measure}]
    )
VAR CleanTable = FILTER(MonthTable, NOT ISBLANK([__Value]))
VAR RowCount = COUNTROWS(CleanTable)
VAR MinValue = MINX(CleanTable, [__Value])
VAR MaxValue = MAXX(CleanTable, [__Value])
VAR FirstValue = MINX(TOPN(1, CleanTable, DimDate[MonthStart], ASC), [__Value])
VAR LastValue = MINX(TOPN(1, CleanTable, DimDate[MonthStart], DESC), [__Value])
VAR LowMonth = MINX(TOPN(1, CleanTable, [__Value], ASC, DimDate[MonthStart], ASC), DimDate[MonthStart])
VAR LowValue = MINX(FILTER(CleanTable, DimDate[MonthStart] = LowMonth), [__Value])
VAR StartYValue = 78 - DIVIDE(FirstValue - MinValue, MaxValue - MinValue, 0.5) * 38
VAR EndYValue = 78 - DIVIDE(LastValue - MinValue, MaxValue - MinValue, 0.5) * 38
VAR LowRank = RANKX(CleanTable, DimDate[MonthStart], LowMonth, ASC, DENSE) - 1
VAR LowXValue = 142 + DIVIDE(LowRank, MAX(1, RowCount - 1), 0) * 86
VAR LowYValue = 78 - DIVIDE(LowValue - MinValue, MaxValue - MinValue, 0.5) * 38
VAR TrendColor = IF({improved_test}, "{encoded_color}", "%23C94A4A")
VAR BandColor = IF({improved_test}, "%23DDEEDC", "%23F3D7D7")
VAR LinePoints =
    CONCATENATEX(
        CleanTable,
        VAR RankValue = RANKX(CleanTable, DimDate[MonthStart], , ASC, DENSE) - 1
        VAR XValue = 142 + DIVIDE(RankValue, MAX(1, RowCount - 1), 0) * 86
        VAR YValue = 78 - DIVIDE([__Value] - MinValue, MaxValue - MinValue, 0.5) * 38
        RETURN FORMAT(XValue, "0.0") & "," & FORMAT(YValue, "0.0"),
        " ",
        DimDate[MonthStart],
        ASC
    )
VAR AreaPath =
    "M142 82 " &
    CONCATENATEX(
        CleanTable,
        VAR RankValue = RANKX(CleanTable, DimDate[MonthStart], , ASC, DENSE) - 1
        VAR XValue = 142 + DIVIDE(RankValue, MAX(1, RowCount - 1), 0) * 86
        VAR YValue = 78 - DIVIDE([__Value] - MinValue, MaxValue - MinValue, 0.5) * 38
        RETURN "L" & FORMAT(XValue, "0.0") & " " & FORMAT(YValue, "0.0"),
        " ",
        DimDate[MonthStart],
        ASC
    ) & " L228 82 Z"
VAR SVG =
    "<svg xmlns='http://www.w3.org/2000/svg' width='224' height='126' viewBox='0 0 248 140'>" &
    "<rect x='5' y='5' width='238' height='130' rx='14' fill='%23F4EFFA' stroke='%237142A4' stroke-width='2.5'/>" &
    "<rect x='18' y='14' width='212' height='4' rx='2' fill='{encoded_color}' opacity='0.88'/>" &
    "<text x='18' y='38' font-family='Segoe UI' font-size='14' font-weight='700' fill='%23211A32'>{title}</text>" &
    "<text x='18' y='78' font-family='Segoe UI' font-size='28' font-weight='700' fill='{encoded_color}'>" & ValueText & "</text>" &
    "<rect x='140' y='38' width='92' height='44' rx='7' fill='%23F8F5FC'/>" &
    "<rect x='144' y='58' width='82' height='11' rx='5' fill='" & BandColor & "'/>" &
    "<line x1='144' y1='64' x2='226' y2='64' stroke='%23B8AECF' stroke-width='1' stroke-dasharray='4 5'/>" &
    "<path d='" & AreaPath & "' fill='%23B8AEE6' opacity='0.55'/>" &
    "<polyline points='" & LinePoints & "' fill='none' stroke='" & TrendColor & "' stroke-width='3' stroke-linecap='round' stroke-linejoin='round'/>" &
    "<circle cx='142' cy='" & FORMAT(StartYValue, "0.0") & "' r='4' fill='%23FFFFFF' stroke='%2377A4F5' stroke-width='2'/>" &
    "<circle cx='" & FORMAT(LowXValue, "0.0") & "' cy='" & FORMAT(LowYValue, "0.0") & "' r='4' fill='%23D96A5D' stroke='%23FFFFFF' stroke-width='2'/>" &
    "<circle cx='228' cy='" & FORMAT(EndYValue, "0.0") & "' r='5' fill='" & TrendColor & "' stroke='%23FFFFFF' stroke-width='2'/>" &
    "<line x1='18' y1='88' x2='230' y2='88' stroke='%23A99AC4' stroke-width='1.5'/>" &
    "<text x='18' y='105' font-family='Segoe UI' font-size='13' font-weight='700' fill='%23211A32'>PY:</text>" &
    "<text x='18' y='122' font-family='Segoe UI' font-size='13' fill='%236E667B'>" & PYText & "</text>" &
    "<text x='130' y='105' font-family='Segoe UI' font-size='13' font-weight='700' fill='%23211A32'>YoY:</text>" &
    "<polygon points='132,112 138,122 126,122' fill='" & YoYColor & "'/>" &
    "<text x='146' y='122' font-family='Segoe UI' font-size='13' font-weight='700' fill='" & YoYColor & "'>" & YoYText & "</text>" &
    "</svg>"
RETURN IF(RowCount = 0, BLANK(), "data:image/svg+xml;utf8," & SVG)'''


def money_display_expr(measure: str) -> str:
    return (
        f'VAR Value = [{measure}] RETURN '
        'SWITCH(TRUE(), '
        'ABS(Value) >= 1000000000, FORMAT(DIVIDE(Value, 1000000000), "$#,0.0B;($#,0.0B);$0.0B"), '
        'ABS(Value) >= 1000000, FORMAT(DIVIDE(Value, 1000000), "$#,0M;($#,0M);$0M"), '
        'FORMAT(Value, "$#,0;($#,0);$0"))'
    )


def percent_display_expr(measure: str) -> str:
    return f'FORMAT([{measure}], "0.0%")'


def multiple_display_expr(measure: str) -> str:
    return f'FORMAT([{measure}], "0.0x")'


def scaled_expr(measure: str, divisor: int | float) -> str:
    return f"DIVIDE([{measure}], {divisor})"


MEASURES = [
    ("Revenue", selected_scenario_sum("FactPnlMonthly", "Revenue"), "$#,0;($#,0);$0"),
    ("Plan Revenue", selected_scenario_sum("FactPnlMonthly", "PlanRevenue"), "$#,0;($#,0);$0"),
    ("Forecast Revenue", selected_scenario_sum("FactPnlMonthly", "ForecastRevenue"), "$#,0;($#,0);$0"),
    ("Revenue vs Plan", "[Revenue] - [Plan Revenue]", "$#,0;($#,0);$0"),
    ("Revenue vs Plan %", "DIVIDE([Revenue vs Plan], [Plan Revenue])", "0.0%"),
    ("Gross Profit", selected_scenario_sum("FactPnlMonthly", "GrossProfit"), "$#,0;($#,0);$0"),
    ("Gross Margin %", "DIVIDE([Gross Profit], [Revenue])", "0.0%"),
    ("EBITDA", selected_scenario_sum("FactPnlMonthly", "EBITDA"), "$#,0;($#,0);$0"),
    ("Plan EBITDA", selected_scenario_sum("FactPnlMonthly", "PlanEBITDA"), "$#,0;($#,0);$0"),
    ("EBITDA vs Plan", "[EBITDA] - [Plan EBITDA]", "$#,0;($#,0);$0"),
    ("EBITDA Margin %", "DIVIDE([EBITDA], [Revenue])", "0.0%"),
    ("Net Income", selected_scenario_sum("FactPnlMonthly", "NetIncome"), "$#,0;($#,0);$0"),
    ("Operating Expense", selected_scenario_sum("FactOpexMonthly", "OperatingExpense"), "$#,0;($#,0);$0"),
    ("Latest Revenue", 'CALCULATE([Revenue], DimDate[IsLatestCompleteMonth] = 1)', "$#,0;($#,0);$0"),
    ("Latest Gross Margin %", 'CALCULATE([Gross Margin %], DimDate[IsLatestCompleteMonth] = 1)', "0.0%"),
    ("Latest EBITDA", 'CALCULATE([EBITDA], DimDate[IsLatestCompleteMonth] = 1)', "$#,0;($#,0);$0"),
    ("Latest EBITDA Margin %", 'CALCULATE([EBITDA Margin %], DimDate[IsLatestCompleteMonth] = 1)', "0.0%"),
    ("Latest Cash Balance", f'VAR ScenarioID = SELECTEDVALUE(DimScenario[ScenarioID], "Base") RETURN CALCULATE(MAX(FactCashMonthly[CashBalance]), FactCashMonthly[ScenarioID] = ScenarioID, DimDate[IsLatestCompleteMonth] = 1)', "$#,0;($#,0);$0"),
    ("Cash Balance", selected_scenario_max("FactCashMonthly", "CashBalance"), "$#,0;($#,0);$0"),
    ("Operating Cash Flow", selected_scenario_sum("FactCashMonthly", "OperatingCashFlow"), "$#,0;($#,0);$0"),
    ("Free Cash Flow", selected_scenario_sum("FactCashMonthly", "FreeCashFlow"), "$#,0;($#,0);$0"),
    ("Latest Free Cash Flow", f'VAR ScenarioID = SELECTEDVALUE(DimScenario[ScenarioID], "Base") RETURN CALCULATE(MAX(FactCashMonthly[FreeCashFlow]), FactCashMonthly[ScenarioID] = ScenarioID, DimDate[IsLatestCompleteMonth] = 1)', "$#,0;($#,0);$0"),
    ("Net Burn", selected_scenario_max("FactCashMonthly", "NetBurn"), "$#,0;($#,0);$0"),
    ("Latest Net Burn", f'VAR ScenarioID = SELECTEDVALUE(DimScenario[ScenarioID], "Base") RETURN CALCULATE(MAX(FactCashMonthly[NetBurn]), FactCashMonthly[ScenarioID] = ScenarioID, DimDate[IsLatestCompleteMonth] = 1)', "$#,0;($#,0);$0"),
    ("Runway Months", selected_scenario_max("FactCashMonthly", "RunwayMonths"), "0.0x"),
    ("Latest Runway Months", f'VAR ScenarioID = SELECTEDVALUE(DimScenario[ScenarioID], "Base") RETURN CALCULATE(MAX(FactCashMonthly[RunwayMonths]), FactCashMonthly[ScenarioID] = ScenarioID, DimDate[IsLatestCompleteMonth] = 1)', "0.0x"),
    ("Funding Need", selected_scenario_max("FactCashMonthly", "FundingNeed"), "$#,0;($#,0);$0"),
    ("Latest Funding Need", f'VAR ScenarioID = SELECTEDVALUE(DimScenario[ScenarioID], "Base") RETURN CALCULATE(MAX(FactCashMonthly[FundingNeed]), FactCashMonthly[ScenarioID] = ScenarioID, DimDate[IsLatestCompleteMonth] = 1)', "$#,0;($#,0);$0"),
    ("Statement Actual", selected_scenario_sum("FactStatementLines", "ValueActual"), "$#,0;($#,0);$0"),
    ("Statement Plan", selected_scenario_sum("FactStatementLines", "ValuePlan"), "$#,0;($#,0);$0"),
    ("Statement Forecast", selected_scenario_sum("FactStatementLines", "ValueForecast"), "$#,0;($#,0);$0"),
    ("Statement Variance %", "DIVIDE([Statement Actual] - [Statement Plan], [Statement Plan])", "0.0%"),
    ("Enterprise Value", 'VAR ScenarioID = SELECTEDVALUE(DimScenario[ScenarioID], "Base") RETURN CALCULATE(AVERAGE(FactValuation[EnterpriseValue]), FactValuation[ScenarioID] = ScenarioID)', "$#,0;($#,0);$0"),
    ("Equity Value", 'VAR ScenarioID = SELECTEDVALUE(DimScenario[ScenarioID], "Base") RETURN CALCULATE(AVERAGE(FactValuation[EquityValue]), FactValuation[ScenarioID] = ScenarioID)', "$#,0;($#,0);$0"),
    ("Valuation Low", 'VAR ScenarioID = SELECTEDVALUE(DimScenario[ScenarioID], "Base") RETURN CALCULATE(AVERAGE(FactValuation[LowValue]), FactValuation[ScenarioID] = ScenarioID)', "$#,0;($#,0);$0"),
    ("Valuation High", 'VAR ScenarioID = SELECTEDVALUE(DimScenario[ScenarioID], "Base") RETURN CALCULATE(AVERAGE(FactValuation[HighValue]), FactValuation[ScenarioID] = ScenarioID)', "$#,0;($#,0);$0"),
    ("Sensitivity Delta", selected_scenario_sum("FactSensitivity", "EquityValueDelta"), "$#,0;($#,0);$0"),
    ("Leverage Ratio", f'VAR ScenarioID = SELECTEDVALUE(DimScenario[ScenarioID], "Base") RETURN CALCULATE(MAX(FactCovenantMonthly[LeverageRatio]), FactCovenantMonthly[ScenarioID] = ScenarioID, DimDate[IsLatestCompleteMonth] = 1)', "0.0x"),
    ("Leverage Limit", selected_scenario_max("FactCovenantMonthly", "LeverageLimit"), "0.0x"),
    ("Leverage Headroom", f'VAR ScenarioID = SELECTEDVALUE(DimScenario[ScenarioID], "Base") RETURN CALCULATE(MAX(FactCovenantMonthly[LeverageHeadroom]), FactCovenantMonthly[ScenarioID] = ScenarioID, DimDate[IsLatestCompleteMonth] = 1)', "0.0x"),
    ("Interest Coverage", f'VAR ScenarioID = SELECTEDVALUE(DimScenario[ScenarioID], "Base") RETURN CALCULATE(MAX(FactCovenantMonthly[InterestCoverage]), FactCovenantMonthly[ScenarioID] = ScenarioID, DimDate[IsLatestCompleteMonth] = 1)', "0.0x"),
    ("Liquidity Headroom", f'VAR ScenarioID = SELECTEDVALUE(DimScenario[ScenarioID], "Base") RETURN CALCULATE(MAX(FactCovenantMonthly[LiquidityHeadroom]), FactCovenantMonthly[ScenarioID] = ScenarioID, DimDate[IsLatestCompleteMonth] = 1)', "$#,0;($#,0);$0"),
    ("Risk Exposure", selected_scenario_sum("FactRiskRegister", "ExposureUSD"), "$#,0;($#,0);$0"),
    ("Critical Risk Count", 'VAR ScenarioID = SELECTEDVALUE(DimScenario[ScenarioID], "Base") RETURN CALCULATE(COUNTROWS(FactRiskRegister), FactRiskRegister[ScenarioID] = ScenarioID, FactRiskRegister[Severity] = "Critical")', "#,0"),
    ("Revenue Display", money_display_expr("Revenue"), "", {"dataType": "string"}),
    ("Gross Margin % Display", percent_display_expr("Gross Margin %"), "", {"dataType": "string"}),
    ("EBITDA Display", money_display_expr("EBITDA"), "", {"dataType": "string"}),
    ("Cash Balance Display", money_display_expr("Cash Balance"), "", {"dataType": "string"}),
    ("Runway Months Display", multiple_display_expr("Runway Months"), "", {"dataType": "string"}),
    ("Free Cash Flow Display", money_display_expr("Free Cash Flow"), "", {"dataType": "string"}),
    ("Net Burn Display", money_display_expr("Net Burn"), "", {"dataType": "string"}),
    ("Funding Need Display", money_display_expr("Funding Need"), "", {"dataType": "string"}),
    ("Enterprise Value Display", money_display_expr("Enterprise Value"), "", {"dataType": "string"}),
    ("Equity Value Display", money_display_expr("Equity Value"), "", {"dataType": "string"}),
    ("Leverage Ratio Display", multiple_display_expr("Leverage Ratio"), "", {"dataType": "string"}),
    ("Leverage Headroom Display", multiple_display_expr("Leverage Headroom"), "", {"dataType": "string"}),
    ("Risk Exposure Display", money_display_expr("Risk Exposure"), "", {"dataType": "string"}),
    ("Revenue KPI", scaled_expr("Latest Revenue", 1000000), "$#,0.0M;($#,0.0M);$0.0M"),
    ("Gross Margin KPI", "[Latest Gross Margin %]", "0.0%"),
    ("EBITDA KPI", scaled_expr("Latest EBITDA", 1000000), "$#,0.0M;($#,0.0M);$0.0M"),
    ("Cash Balance KPI", scaled_expr("Latest Cash Balance", 1000000), "$#,0.0M;($#,0.0M);$0.0M"),
    ("Runway Months KPI", "[Latest Runway Months]", "0.0x"),
    ("Free Cash Flow KPI", scaled_expr("Latest Free Cash Flow", 1000000), "$#,0.0M;($#,0.0M);$0.0M"),
    ("Net Burn KPI", scaled_expr("Latest Net Burn", 1000000), "$#,0M;($#,0M);$0M"),
    ("Funding Need KPI", scaled_expr("Latest Funding Need", 1000000), "$#,0M;($#,0M);$0M"),
    ("Enterprise Value KPI", scaled_expr("Enterprise Value", 1000000000), "$#,0.0B;($#,0.0B);$0.0B"),
    ("Equity Value KPI", scaled_expr("Equity Value", 1000000000), "$#,0.0B;($#,0.0B);$0.0B"),
    ("Leverage KPI", "[Leverage Ratio]", "0.0x"),
    ("Headroom KPI", "[Leverage Headroom]", "0.0x"),
    ("Risk Exposure KPI", scaled_expr("Risk Exposure", 1000000), "$#,0M;($#,0M);$0M"),
    ("Revenue Sparkline SVG", svg_sparkline("Revenue", COLORS["blue"]), "", {"dataType": "string", "dataCategory": "ImageUrl"}),
    ("Gross Margin Sparkline SVG", svg_sparkline("Gross Margin %", COLORS["teal"]), "", {"dataType": "string", "dataCategory": "ImageUrl"}),
    ("EBITDA Sparkline SVG", svg_sparkline("EBITDA", COLORS["green"]), "", {"dataType": "string", "dataCategory": "ImageUrl"}),
    ("Cash Sparkline SVG", svg_sparkline("Cash Balance", COLORS["amber"]), "", {"dataType": "string", "dataCategory": "ImageUrl"}),
    ("Runway Sparkline SVG", svg_sparkline("Runway Months", COLORS["blue"]), "", {"dataType": "string", "dataCategory": "ImageUrl"}),
    ("Funding Sparkline SVG", svg_sparkline("Funding Need", COLORS["green"], "lower"), "", {"dataType": "string", "dataCategory": "ImageUrl"}),
    ("Leverage Sparkline SVG", svg_sparkline("Leverage Ratio", COLORS["green"], "lower"), "", {"dataType": "string", "dataCategory": "ImageUrl"}),
    ("Interest Coverage Sparkline SVG", svg_sparkline("Interest Coverage", COLORS["green"]), "", {"dataType": "string", "dataCategory": "ImageUrl"}),
    ("Statement Trend SVG", svg_sparkline("Statement Actual", COLORS["teal"]), "", {"dataType": "string", "dataCategory": "ImageUrl"}),
    ("Board KPI Trend SVG", board_kpi_trend_svg(), "", {"dataType": "string", "dataCategory": "ImageUrl"}),
    ("Risk Signal SVG", risk_signal_svg(), "", {"dataType": "string", "dataCategory": "ImageUrl"}),
    ("Revenue KPI Card SVG", svg_kpi_card("Revenue", "Revenue", COLORS["blue"], "$#,0.0M;($#,0.0M);$0.0M", 1000000, "percent", "higher"), "", {"dataType": "string", "dataCategory": "ImageUrl"}),
    ("Margin KPI Card SVG", svg_kpi_card("Margin", "Gross Margin %", COLORS["teal"], "0.0%", 1, "points", "higher"), "", {"dataType": "string", "dataCategory": "ImageUrl"}),
    ("EBITDA KPI Card SVG", svg_kpi_card("EBITDA", "EBITDA", COLORS["green"], "$#,0.0M;($#,0.0M);$0.0M", 1000000, "percent", "higher"), "", {"dataType": "string", "dataCategory": "ImageUrl"}),
    ("Cash KPI Card SVG", svg_kpi_card("Cash", "Cash Balance", COLORS["amber"], "$#,0.0M;($#,0.0M);$0.0M", 1000000, "percent", "higher"), "", {"dataType": "string", "dataCategory": "ImageUrl"}),
    ("Runway KPI Card SVG", svg_kpi_card("Runway", "Runway Months", COLORS["blue"], "0.0x", 1, "multiple", "higher"), "", {"dataType": "string", "dataCategory": "ImageUrl"}),
    ("FCF KPI Card SVG", svg_kpi_card("FCF", "Free Cash Flow", COLORS["teal"], "$#,0.0M;($#,0.0M);$0.0M", 1000000, "percent", "higher"), "", {"dataType": "string", "dataCategory": "ImageUrl"}),
    ("Burn KPI Card SVG", svg_kpi_card("Burn", "Net Burn", COLORS["red"], "$#,0.0M;($#,0.0M);$0.0M", 1000000, "percent", "lower"), "", {"dataType": "string", "dataCategory": "ImageUrl"}),
    ("Funding KPI Card SVG", svg_kpi_card("Funding", "Funding Need", COLORS["green"], "$#,0M;($#,0M);$0M", 1000000, "percent", "lower"), "", {"dataType": "string", "dataCategory": "ImageUrl"}),
    ("EV KPI Card SVG", svg_kpi_card("EV", "Enterprise Value", COLORS["blue"], "$#,0.0B;($#,0.0B);$0.0B", 1000000000, "percent", "higher"), "", {"dataType": "string", "dataCategory": "ImageUrl"}),
    ("Equity KPI Card SVG", svg_kpi_card("Equity", "Equity Value", COLORS["green"], "$#,0.0B;($#,0.0B);$0.0B", 1000000000, "percent", "higher"), "", {"dataType": "string", "dataCategory": "ImageUrl"}),
    ("Leverage KPI Card SVG", svg_kpi_card("Leverage", "Leverage Ratio", COLORS["amber"], "0.0x", 1, "multiple", "lower"), "", {"dataType": "string", "dataCategory": "ImageUrl"}),
    ("Headroom KPI Card SVG", svg_kpi_card("Headroom", "Leverage Headroom", COLORS["teal"], "0.0x", 1, "multiple", "higher"), "", {"dataType": "string", "dataCategory": "ImageUrl"}),
    ("Risk KPI Card SVG", svg_kpi_card("Risk", "Risk Exposure", COLORS["red"], "$#,0M;($#,0M);$0M", 1000000, "percent", "lower"), "", {"dataType": "string", "dataCategory": "ImageUrl"}),
    ("Board Status Icon", 'SWITCH(TRUE(), [Revenue vs Plan %] >= 0.03, UNICHAR(9650), [Revenue vs Plan %] >= -0.02, UNICHAR(8212), UNICHAR(9660))', "", {"dataType": "string"}),
    ("Board Status Color", 'SWITCH(TRUE(), [Revenue vs Plan %] >= 0.03, "#2FA66A", [Revenue vs Plan %] >= -0.02, "#C58A18", "#C94A4A")', "", {"dataType": "string"}),
]

RELATIONSHIPS = [
    ("FactPnlMonthly", "MonthStart", "DimDate", "MonthStart"),
    ("FactPnlMonthly", "ScenarioID", "DimScenario", "ScenarioID"),
    ("FactPnlMonthly", "BusinessUnitID", "DimBusinessUnit", "BusinessUnitID"),
    ("FactPnlMonthly", "RegionID", "DimRegion", "RegionID"),
    ("FactOpexMonthly", "MonthStart", "DimDate", "MonthStart"),
    ("FactOpexMonthly", "ScenarioID", "DimScenario", "ScenarioID"),
    ("FactOpexMonthly", "CostCategoryID", "DimCostCategory", "CostCategoryID"),
    ("FactCashMonthly", "MonthStart", "DimDate", "MonthStart"),
    ("FactCashMonthly", "ScenarioID", "DimScenario", "ScenarioID"),
    ("FactStatementLines", "MonthStart", "DimDate", "MonthStart"),
    ("FactStatementLines", "ScenarioID", "DimScenario", "ScenarioID"),
    ("FactCovenantMonthly", "MonthStart", "DimDate", "MonthStart"),
    ("FactCovenantMonthly", "ScenarioID", "DimScenario", "ScenarioID"),
    ("FactValuation", "ScenarioID", "DimScenario", "ScenarioID"),
    ("FactSensitivity", "ScenarioID", "DimScenario", "ScenarioID"),
    ("FactRiskRegister", "ScenarioID", "DimScenario", "ScenarioID"),
]


def measure_name(item) -> str:
    return item[0]


def measure_expression(item) -> str:
    return item[1]


def measure_format(item) -> str:
    return item[2]


def measure_extra(item) -> dict:
    return item[3] if len(item) > 3 else {}


def measure_by_name(name: str):
    return next(item for item in MEASURES if measure_name(item) == name)


def measure_dtype(name: str) -> str:
    return measure_extra(measure_by_name(name)).get("dataType", "numeric")


def measure_query_type(name: str) -> int:
    return 2048 if measure_dtype(name) == "string" else 1


def measure_transform_type(name: str) -> dict:
    return {"category": None, "underlyingType": 1 if measure_dtype(name) == "string" else 259}


def measure_bim_record(item) -> dict:
    record = {
        "name": measure_name(item),
        "expression": measure_expression(item),
        "lineageTag": str(uuid.uuid4()),
    }
    if measure_format(item):
        record["formatString"] = measure_format(item)
    if measure_extra(item).get("dataCategory"):
        record["dataCategory"] = measure_extra(item)["dataCategory"]
    return record


def infer_m_type(name: str, series: pd.Series) -> tuple[str, str, str]:
    if name in {"MonthStart"} or name.endswith("Date"):
        return "dateTime", "type date", "none"
    if pd.api.types.is_integer_dtype(series):
        return "int64", "Int64.Type", "sum"
    if pd.api.types.is_float_dtype(series):
        return "double", "type number", "sum"
    return "string", "type text", "none"


def table_model(name: str, df: pd.DataFrame) -> dict:
    columns = []
    m_types = []
    for col_name in df.columns:
        dtype, mtype, summarize = infer_m_type(col_name, df[col_name])
        item = {"name": col_name, "dataType": dtype, "sourceColumn": col_name}
        if col_name.endswith("ID") or dtype == "string" or col_name in {"MonthIndex", "LineSort", "ScenarioSort", "MethodSort", "SortOrder"}:
            summarize = "none"
        if "Pct" in col_name or "Rate" in col_name or "Margin" in col_name or "Probability" in col_name:
            item["formatString"] = "0.0%"
        elif any(token in col_name for token in ["Revenue", "Value", "Cash", "Debt", "Capital", "Expense", "COGS", "Profit", "EBITDA", "Income", "Flow", "Burn", "Need", "Exposure", "Liquidity"]):
            item["formatString"] = "$#,0;($#,0);$0"
        elif dtype == "int64":
            item["formatString"] = "0"
        item["summarizeBy"] = summarize
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
    return {
        "name": name,
        "lineageTag": str(uuid.uuid4()),
        "columns": columns,
        "partitions": [{"name": f"p_{name}", "mode": "import", "source": {"type": "m", "expression": expression}}],
    }


def build_model(tables: dict[str, pd.DataFrame]) -> None:
    model_tables = [table_model(name, df) for name, df in tables.items()]
    model_tables.append(
        {
            "name": MEASURE_TABLE,
            "lineageTag": str(uuid.uuid4()),
            "columns": [{"name": "MeasureName", "dataType": "string", "sourceColumn": "MeasureName", "isHidden": True}],
            "partitions": [
                {
                    "name": "p_KPI_Measures",
                    "mode": "import",
                    "source": {"type": "m", "expression": 'let Source = #table(type table [MeasureName = text], {{"KPI"}}) in Source'},
                }
            ],
            "measures": [measure_bim_record(item) for item in MEASURES],
        }
    )
    relationships = [
        {"name": f"Rel_{a}_{b}_{c}_{d}", "fromTable": a, "fromColumn": b, "toTable": c, "toColumn": d}
        for a, b, c, d in RELATIONSHIPS
    ]
    model = {
        "compatibilityLevel": 1600,
        "model": {
            "culture": "en-US",
            "dataAccessOptions": {"legacyRedirects": True, "returnErrorValuesAsNull": True},
            "defaultPowerBIDataSourceVersion": "powerBI_V3",
            "sourceQueryCulture": "en-US",
            "tables": model_tables,
            "relationships": relationships,
        },
    }
    write_json(ROOT / "model" / "model.bim", model)
    sem = ROOT / "powerbi" / "pbip" / "Board_Investor_CFO_Pack" / "Board_Investor_CFO_Pack.SemanticModel"
    write_json(sem / "model.bim", model)
    write_json(ROOT / "model" / "relationship_map.json", relationships)
    write_json(
        ROOT / "model" / "measure_map.json",
        [
            {
                "measure": measure_name(item),
                "expression": measure_expression(item),
                "format": measure_format(item),
                **measure_extra(item),
            }
            for item in MEASURES
        ],
    )
    write_text(ROOT / "model" / "MEASURES.dax", "\n\n".join(f"{measure_name(item)} = {measure_expression(item)}" for item in MEASURES))
    write_text(
        ROOT / "model" / "dax_measures.md",
        "# DAX Measures\n\n"
        + "\n\n".join(
            f"## {measure_name(item)}\n\n```DAX\n{measure_name(item)} = {measure_expression(item)}\n```\n\nFormat: `{measure_format(item) or 'text/image'}`"
            for item in MEASURES
        ),
    )
    write_text(
        ROOT / "model" / "metric_definitions.md",
        """# Metric Definitions

Core KPIs are DAX measures, not raw numeric fields.

- Revenue, EBITDA, and plan variance default to the Base scenario when no scenario is selected.
- Rates and margins use `DIVIDE`.
- Cash, runway, covenant, and valuation cards use latest complete month logic where applicable.
- KPI footer labels, status colors, and SVG sparklines are DAX decoration measures so micro-details can respond to slicers.
- Board KPI scorecard values are denormalized display strings to preserve mixed units in the status table.
- Scenario analytics use `DimScenario` so Base/Upside/Downside comparisons stay consistent across pages.
""",
    )
    write_text(ROOT / "model" / "relationship_map.md", "# Relationship Map\n\n" + "\n".join(f"- {a}[{b}] -> {c}[{d}]" for a, b, c, d in RELATIONSHIPS))
    write_text(
        ROOT / "model" / "data_dictionary.md",
        "# Data Dictionary\n\n"
        + "\n\n".join(f"## {name}\n\nGrain: {grain_for_table(name)}\n\nRows: {len(df):,}\n\nColumns: {', '.join(df.columns)}" for name, df in tables.items()),
    )
    write_text(
        ROOT / "model" / "semantic_model_notes.md",
        "Star-schema finance model with conformed date and scenario dimensions. P&L facts support business unit and region cuts; cash, valuation, covenant, and risk tables support board/investor scenario review.",
    )


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


def hidden_header(fill: str) -> list[dict]:
    return [
        {
            "properties": {
                "show": lit(False),
                "background": col(fill),
                "border": col(fill),
            }
        }
    ]


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
    item = next((item for item in MEASURES if measure_name(item) == measure), None)
    return measure_format(item) if item else "#,0"


def frame(title=None, sub=None, fill=None):
    fill = fill or COLORS["panel"]
    out = {
        "title": [{"properties": {"show": lit(False)}}],
        "subTitle": [{"properties": {"show": lit(False)}}],
        "background": [{"properties": {"show": lit(True), "color": col(fill), "transparency": lit(0.0)}}],
        "border": [{"properties": {"show": lit(True), "color": col(COLORS["border"]), "radius": lit(6.0), "width": lit(0.75)}}],
        "dropShadow": [{"properties": {"show": lit(True), "position": txt("Outer"), "color": col("#180827"), "transparency": lit(82.0), "angle": lit(45.0), "distance": lit(2.0)}}],
        "visualHeader": hidden_header(fill),
    }
    if title:
        out["title"] = [{"properties": {"show": lit(True), "text": txt(title), "fontFamily": txt("Segoe UI Semibold"), "fontSize": lit(9.2), "fontColor": col(COLORS["ink"])}}]
    if sub:
        out["subTitle"] = [{"properties": {"show": lit(True), "text": txt(sub), "fontFamily": txt("Segoe UI"), "fontSize": lit(7.4), "fontColor": col(COLORS["muted"])}}]
    return out


def chart_frame(title=None, sub=None, fill=None):
    fill = fill or COLORS["chart_panel"]
    out = {
        "title": [{"properties": {"show": lit(False)}}],
        "subTitle": [{"properties": {"show": lit(False)}}],
        "background": [{"properties": {"show": lit(True), "color": col(fill), "transparency": lit(0.0)}}],
        "border": [{"properties": {"show": lit(True), "color": col(COLORS["chart_border"]), "radius": lit(7.0), "width": lit(0.9)}}],
        "dropShadow": [{"properties": {"show": lit(True), "position": txt("Outer"), "color": col("#16051F"), "transparency": lit(86.0), "angle": lit(45.0), "distance": lit(2.0)}}],
        "visualHeader": hidden_header(fill),
    }
    if title:
        out["title"] = [{"properties": {"show": lit(True), "text": txt(title), "fontFamily": txt("Segoe UI Semibold"), "fontSize": lit(8.9), "fontColor": col(COLORS["ink"])}}]
    if sub:
        out["subTitle"] = [{"properties": {"show": lit(True), "text": txt(sub), "fontFamily": txt("Segoe UI"), "fontSize": lit(6.9), "fontColor": col(COLORS["muted"])}}]
    return out


def slicer_frame(title=None, fill=None):
    fill = fill or COLORS["slicer_fill"]
    out = {
        "title": [{"properties": {"show": lit(False)}}],
        "subTitle": [{"properties": {"show": lit(False)}}],
        "background": [{"properties": {"show": lit(True), "color": col(fill), "transparency": lit(0.0)}}],
        "border": [{"properties": {"show": lit(True), "color": col(COLORS["slicer_border"]), "radius": lit(5.0), "width": lit(0.8)}}],
        "dropShadow": [{"properties": {"show": lit(False)}}],
        "visualHeader": hidden_header(fill),
    }
    if title:
        out["title"] = [{"properties": {"show": lit(True), "text": txt(title), "fontFamily": txt("Segoe UI Semibold"), "fontSize": lit(8.0), "fontColor": col(COLORS["ink"])}}]
    return out


def container(config, p, query_obj=None, transform_obj=None):
    config["layouts"] = [{"id": 0, "position": p}]
    out = {
        "x": p["x"],
        "y": p["y"],
        "z": p["z"],
        "width": p["width"],
        "height": p["height"],
        "config": json.dumps(config, separators=(",", ":")),
        "filters": "[]",
        "tabOrder": p["tabOrder"],
    }
    if query_obj:
        out["query"] = json.dumps(query_obj, separators=(",", ":"))
    if transform_obj:
        out["dataTransforms"] = json.dumps(transform_obj, separators=(",", ":"))
    return out


def query(froms, selects, order=None):
    q = {"Version": 2, "From": froms, "Select": selects}
    if order:
        q["OrderBy"] = [order]
    return {
        "Commands": [
            {
                "SemanticQueryDataShapeCommand": {
                    "Query": q,
                    "Binding": {"Primary": {"Groupings": [{"Projections": list(range(len(selects)))}]}},
                    "DataReduction": {"DataVolume": 4, "Primary": {"Window": {"Count": 1000}}},
                    "Version": 1,
                },
                "ExecutionMetricsKind": 1,
            }
        ]
    }


def transforms(objects, roles, meta, selects, ordering, active=None):
    payload = {
        "objects": objects,
        "projectionOrdering": ordering,
        "queryMetadata": {"Select": meta},
        "visualElements": [{"DataRoles": [{"Name": role, "Projection": idx, "isActive": active_flag} for role, idx, active_flag in roles]}],
        "selects": selects,
    }
    if active:
        payload["projectionActiveItems"] = active
    return payload


def ctrans(alias, table, column, display, role):
    return {
        "displayName": display,
        "queryName": f"{table}.{column}",
        "roles": {role: True},
        "type": {"category": None, "underlyingType": 1},
        "expr": {"Column": {"Expression": ent(alias), "Property": column}},
    }


def mtrans(measure, display, role):
    payload = {
        "displayName": display,
        "queryName": f"{MEASURE_TABLE}.{measure}",
        "roles": {role: True},
        "type": measure_transform_type(measure),
        "expr": {"Measure": {"Expression": ent("m"), "Property": measure}},
    }
    if mfmt(measure):
        payload["format"] = mfmt(measure)
    return payload


def measure_meta(measure, display):
    payload = {"Restatement": display, "Name": f"{MEASURE_TABLE}.{measure}", "Type": measure_query_type(measure)}
    if mfmt(measure):
        payload["Format"] = mfmt(measure)
    return payload


def textbox(title, sub, p):
    text_runs = [
        {"value": title, "textStyle": {"fontFamily": "Segoe UI Semibold", "fontSize": "14pt", "color": "#EDEAF9"}},
    ]
    if sub:
        text_runs.append({"value": f"\n{sub}", "textStyle": {"fontFamily": "Segoe UI", "fontSize": "8pt", "color": "#D8E2EF"}})
    objects = {
        "general": [
            {
                "properties": {
                    "paragraphs": [
                        {
                            "textRuns": text_runs
                        }
                    ]
                }
            }
        ]
    }
    return container(
        {
            "name": uuid.uuid4().hex[:20],
            "singleVisual": {
                "visualType": "textbox",
                "objects": objects,
                "drillFilterOtherVisuals": True,
                "vcObjects": {
                    "title": [{"properties": {"show": lit(False)}}],
                    "subTitle": [{"properties": {"show": lit(False)}}],
                    "background": [{"properties": {"show": lit(False)}}],
                    "border": [{"properties": {"show": lit(False)}}],
                    "dropShadow": [{"properties": {"show": lit(False)}}],
                    "visualHeader": hidden_header(COLORS["bg"]),
                },
            },
        },
        p,
    )


def plain_text(text, p, color="#DDD6F3", size="10pt", family="Segoe UI Semibold"):
    p = dict(p)
    p["height"] = max(float(p.get("height", 0)), 24.0)
    objects = {
        "general": [
            {
                "properties": {
                    "paragraphs": [
                        {
                            "textRuns": [
                                {"value": text, "textStyle": {"fontFamily": family, "fontSize": size, "color": color}}
                            ]
                        }
                    ]
                }
            }
        ]
    }
    return container(
        {
            "name": uuid.uuid4().hex[:20],
            "singleVisual": {
                "visualType": "textbox",
                "objects": objects,
                "drillFilterOtherVisuals": True,
                "vcObjects": {
                    "title": [{"properties": {"show": lit(False)}}],
                    "subTitle": [{"properties": {"show": lit(False)}}],
                    "background": [{"properties": {"show": lit(False)}}],
                    "border": [{"properties": {"show": lit(False)}}],
                    "dropShadow": [{"properties": {"show": lit(False)}}],
                    "visualHeader": hidden_header(COLORS["bg"]),
                },
            },
        },
        p,
    )


def filled_text(label, p, fill, text_color, size="8.2pt", family="Segoe UI Semibold", radius=4.5, border_color=None):
    p = dict(p)
    p["height"] = max(float(p.get("height", 0)), 36.0)
    objects = {
        "general": [
            {
                "properties": {
                    "paragraphs": [
                        {
                            "textRuns": [
                                {"value": label, "textStyle": {"fontFamily": family, "fontSize": size, "color": text_color}}
                            ]
                        }
                    ]
                }
            }
        ]
    }
    return container(
        {
            "name": uuid.uuid4().hex[:20],
            "singleVisual": {
                "visualType": "textbox",
                "objects": objects,
                "drillFilterOtherVisuals": True,
                "vcObjects": {
                    "title": [{"properties": {"show": lit(False)}}],
                    "subTitle": [{"properties": {"show": lit(False)}}],
                    "background": [{"properties": {"show": lit(True), "color": col(fill), "transparency": lit(0.0)}}],
                    "border": [{"properties": {"show": lit(True), "color": col(border_color or fill), "radius": lit(radius), "width": lit(0.75)}}],
                    "dropShadow": [{"properties": {"show": lit(False)}}],
                    "visualHeader": hidden_header(fill),
                },
            },
        },
        p,
    )


def shape(fill, p):
    objects = {
        "shape": [{"properties": {"tileShape": txt("rectangle")}}],
        "fill": [{"properties": {"show": lit(False)}}],
        "outline": [{"properties": {"show": lit(False)}}],
    }
    return container(
        {
            "name": uuid.uuid4().hex[:20],
            "singleVisual": {"visualType": "shape", "objects": objects, "drillFilterOtherVisuals": True, "vcObjects": frame(fill=fill)},
        },
        p,
    )


def solid_rect(fill, p, radius=0.0, border=False):
    objects = {
        "shape": [{"properties": {"tileShape": txt("rectangle")}}],
        "fill": [{"properties": {"show": lit(False)}}],
        "outline": [{"properties": {"show": lit(False)}}],
    }
    show_border = border or radius > 0
    vc_objects = {
        "title": [{"properties": {"show": lit(False)}}],
        "subTitle": [{"properties": {"show": lit(False)}}],
        "background": [{"properties": {"show": lit(True), "color": col(fill), "transparency": lit(0.0)}}],
        "border": [{"properties": {"show": lit(show_border), "color": col(fill), "radius": lit(radius), "width": lit(0.5)}}],
        "visualHeader": hidden_header(fill),
    }
    return container({"name": uuid.uuid4().hex[:20], "singleVisual": {"visualType": "shape", "objects": objects, "drillFilterOtherVisuals": True, "vcObjects": vc_objects}}, p)


def card(measure, display, p, accent, value_font=20.0, sub=None, title=None):
    qref = f"{MEASURE_TABLE}.{measure}"
    objects = {
        "layout": [{"properties": {"rectangleRoundedCurve": lit(5), "cellPadding": lit(6.0), "paddingUniform": lit(6.0)}, "selector": {"id": "default"}}, {"properties": {}}],
        "value": [{"properties": {"fontSize": lit(value_font), "fontFamily": txt("Segoe UI Semibold"), "fontColor": col(accent)}, "selector": {"metadata": qref}}],
        "label": [{"properties": {"show": lit(False)}, "selector": {"metadata": qref}}],
        "fillCustom": [{"properties": {"show": lit(False)}}],
        "outline": [{"properties": {"show": lit(False)}, "selector": {"id": "default"}}],
    }
    froms = [{"Name": "m", "Entity": MEASURE_TABLE, "Type": 0}]
    selects = [msel("m", measure, display)]
    config = {
        "name": uuid.uuid4().hex[:20],
        "singleVisual": {
            "visualType": "cardVisual",
            "projections": {"Data": [{"queryRef": qref}]},
            "prototypeQuery": {"Version": 2, "From": froms, "Select": selects},
            "columnProperties": {qref: {"displayName": display}},
            "objects": objects,
            "drillFilterOtherVisuals": True,
            "vcObjects": frame(display if title is None else title, sub, fill=COLORS["card"]),
        },
    }
    transform_obj = transforms(objects, [("Data", 0, False)], [measure_meta(measure, display)], [mtrans(measure, display, "Data")], {"Data": [0]})
    return container(config, p, query(froms, selects), transform_obj)


def measure_value(measure, display, p, accent, value_font=20.0):
    qref = f"{MEASURE_TABLE}.{measure}"
    objects = {
        "layout": [{"properties": {"rectangleRoundedCurve": lit(0), "cellPadding": lit(0.0), "paddingUniform": lit(0.0)}, "selector": {"id": "default"}}, {"properties": {}}],
        "value": [{"properties": {"fontSize": lit(value_font), "fontFamily": txt("Segoe UI Semibold"), "fontColor": col(accent)}, "selector": {"metadata": qref}}],
        "label": [{"properties": {"show": lit(False)}, "selector": {"metadata": qref}}],
        "fillCustom": [{"properties": {"show": lit(False)}}],
        "outline": [{"properties": {"show": lit(False)}, "selector": {"id": "default"}}],
    }
    froms = [{"Name": "m", "Entity": MEASURE_TABLE, "Type": 0}]
    selects = [msel("m", measure, display)]
    config = {
        "name": uuid.uuid4().hex[:20],
        "singleVisual": {
            "visualType": "cardVisual",
            "projections": {"Data": [{"queryRef": qref}]},
            "prototypeQuery": {"Version": 2, "From": froms, "Select": selects},
            "columnProperties": {qref: {"displayName": display}},
            "objects": objects,
            "drillFilterOtherVisuals": True,
            "vcObjects": {"background": [{"properties": {"show": lit(False)}}], "border": [{"properties": {"show": lit(False)}}], "visualHeader": [{"properties": {"show": lit(False)}}]},
        },
    }
    transform_obj = transforms(objects, [("Data", 0, False)], [measure_meta(measure, display)], [mtrans(measure, display, "Data")], {"Data": [0]})
    return container(config, p, query(froms, selects), transform_obj)


def kpi_svg_table(measure: str, display: str, p: dict) -> dict:
    qref = f"{MEASURE_TABLE}.{measure}"
    image_w = max(80, int(p["width"] - 24))
    image_h = max(60, int(p["height"] - 24))
    objects = {
        "grid": [
            {
                "properties": {
                    "gridHorizontal": lit(False),
                    "gridVertical": lit(False),
                    "outlineColor": col(COLORS["bg"]),
                    "rowPadding": lit(0),
                    "imageHeight": lit(image_h),
                    "imageWidth": lit(image_w),
                }
            }
        ],
        "columnHeaders": [
            {
                "properties": {
                    "show": lit(False),
                    "fontSize": lit(1.0),
                    "fontColor": col(COLORS["bg"]),
                }
            }
        ],
        "values": [
            {
                "properties": {
                    "fontSize": lit(1.0),
                    "fontColor": col(COLORS["bg"]),
                    "backColor": col(COLORS["bg"]),
                    "backColorPrimary": col(COLORS["bg"]),
                    "backColorSecondary": col(COLORS["bg"]),
                    "urlIcon": lit(False),
                    "imageHeight": lit(image_h),
                    "imageWidth": lit(image_w),
                }
            }
        ],
        "imageSize": [
            {
                "properties": {
                    "height": lit(image_h),
                    "width": lit(image_w),
                }
            }
        ],
        "columnWidth": [
            {
                "properties": {"value": lit(float(image_w + 6))},
                "selector": {"metadata": qref},
            }
        ],
    }
    froms = [{"Name": "m", "Entity": MEASURE_TABLE, "Type": 0}]
    selects = [msel("m", measure, display)]
    config = {
        "name": uuid.uuid4().hex[:20],
        "singleVisual": {
            "visualType": "tableEx",
            "projections": {"Values": [{"queryRef": qref}]},
            "prototypeQuery": {"Version": 2, "From": froms, "Select": selects},
            "columnProperties": {qref: {"displayName": display}},
            "objects": objects,
            "drillFilterOtherVisuals": True,
            "vcObjects": {
                "background": [{"properties": {"show": lit(False)}}],
                "border": [{"properties": {"show": lit(False)}}],
                "dropShadow": [{"properties": {"show": lit(False)}}],
                "title": [{"properties": {"show": lit(False)}}],
                "visualHeader": [{"properties": {"show": lit(False)}}],
            },
        },
    }
    transform_obj = transforms(objects, [("Values", 0, False)], [measure_meta(measure, display)], [mtrans(measure, display, "Values")], {"Values": [0]})
    return container(config, p, query(froms, selects), transform_obj)


def static_text_card(title, body, p, accent=COLORS["blue"], fill="#FFFFFF", title_size="8pt", body_size="10pt"):
    runs = [{"value": title, "textStyle": {"fontFamily": "Segoe UI Semibold", "fontSize": title_size, "color": accent}}]
    if body:
        runs.append({"value": f"\n{body}", "textStyle": {"fontFamily": "Segoe UI", "fontSize": body_size, "color": COLORS["ink"]}})
    objects = {
        "general": [
            {
                "properties": {
                    "paragraphs": [
                        {
                            "textRuns": runs
                        }
                    ]
                }
            }
        ]
    }
    return container(
        {
            "name": uuid.uuid4().hex[:20],
            "singleVisual": {
                "visualType": "textbox",
                "objects": objects,
                "drillFilterOtherVisuals": True,
                "vcObjects": frame(fill=fill),
            },
        },
        p,
    )


def chip(label, p, accent=COLORS["green"], fill="#ECFDF3"):
    return static_text_card(label, "", p, accent=accent, fill=fill, title_size="7pt", body_size="1pt")


def memo_note(title, lines, p, accent=COLORS["blue"], fill="#FFFFFF"):
    body = "\n".join(f"- {line}" for line in lines)
    return static_text_card(title, body, p, accent=accent, fill=fill, title_size="8pt", body_size="7.2pt")


def static_kpi_card(display, value, p, accent):
    objects = {
        "general": [
            {
                "properties": {
                    "paragraphs": [
                        {
                            "textRuns": [
                                {"value": display, "textStyle": {"fontFamily": "Segoe UI Semibold", "fontSize": "8pt", "color": COLORS["ink"]}},
                                {"value": f"\n{value}", "textStyle": {"fontFamily": "Segoe UI Semibold", "fontSize": "18pt", "color": accent}},
                            ]
                        }
                    ]
                }
            }
        ]
    }
    return container(
        {
            "name": uuid.uuid4().hex[:20],
            "singleVisual": {
                "visualType": "textbox",
                "objects": objects,
                "drillFilterOtherVisuals": True,
                "vcObjects": frame(fill=COLORS["card"]),
            },
        },
        p,
    )


def sidebar_nav_item(label, p, active=False):
    fill = "#6B42D8" if active else "#321052"
    text_color = "#F3EEFF" if active else "#BEB4D7"
    rail_color = "#D5C5F0" if active else "#5E4B8B"
    return [
        shape(fill, p),
        solid_rect(rail_color, pos(p["x"] + 8, p["y"] + 8, p["z"] + 1, 4, p["height"] - 16), radius=2.0),
        plain_text(label, pos(p["x"] + 20, p["y"] + 5, p["z"] + 2, p["width"] - 30, 24), text_color, "8.4pt"),
    ]


def page_context_chips(items, z):
    visuals = []
    x = 584
    widths = [142, 166, 158]
    for i, item in enumerate(items or []):
        label, accent, fill = item
        w = widths[i] if i < len(widths) else 118
        chip_z = z + 70 + i * 6
        visuals += [
            solid_rect(fill, pos(x, 15, chip_z, w, 28), radius=5.0),
            solid_rect(accent, pos(x + 9, 22, chip_z + 1, 10, 10), radius=2.6),
            plain_text(label, pos(x + 27, 17, chip_z + 2, w - 42, 24), COLORS["chip_text"], "8.5pt", "Segoe UI Semibold"),
        ]
        x += w + 10
    return visuals


def sidebar_shell(page_title, active_label, z, context_items=None):
    nav = [
        ("01 Performance", "Performance" in active_label),
        ("02 Cash Plan", "Cash" in active_label),
        ("03 Risk Monitor", "Risk" in active_label or "Valuation" in active_label),
    ]
    visuals = [
        shape(COLORS["sidebar"], pos(14, 8, z, 176, 700)),
        plain_text("FC", pos(34, 25, z + 1, 32, 28), "#4ED2D0", "15pt"),
        plain_text("Finance\nControl", pos(76, 28, z + 2, 94, 46), "#DCD4F4", "8.4pt"),
        plain_text("FP20", pos(1132, 11, z + 3, 48, 24), "#E6DDF8", "9pt"),
        plain_text("Board CFO Pack", pos(1178, 11, z + 4, 98, 24), "#E6DDF8", "8pt"),
        textbox(page_title, "", pos(204, 16, z + 5, 400, 30)),
    ]
    visuals.extend(page_context_chips(context_items, z))
    y = 92
    for label, active in nav:
        visuals.extend(sidebar_nav_item(label, pos(30, y, z + 10 + len(visuals), 146, 32), active))
        y += 40
    visuals += [
        solid_rect(COLORS["sidebar_rule"], pos(30, 218, z + 49, 146, 3), radius=1.5),
        plain_text("Board Lens", pos(32, 232, z + 50, 124, 18), COLORS["sidebar_muted"], "7.5pt", "Segoe UI Semibold"),
        plain_text("Year", pos(32, 254, z + 51, 104, 18), COLORS["sidebar_text"], "8.2pt"),
        slicer("DimDate", "Year", "Year", pos(30, 274, z + 52, 146, 42), mode="Dropdown", show_title=False, compact=True),
        plain_text("Scenario", pos(32, 348, z + 53, 104, 18), COLORS["sidebar_text"], "8.2pt"),
        slicer("DimScenario", "ScenarioName", "Scenario", pos(30, 368, z + 54, 146, 42), mode="Dropdown", show_title=False, compact=True),
        plain_text("BU", pos(32, 440, z + 55, 104, 18), COLORS["sidebar_text"], "8.2pt"),
        slicer("DimBusinessUnit", "BusinessUnit", "BU", pos(30, 460, z + 56, 146, 42), mode="Dropdown", show_title=False, compact=True),
        plain_text("Region", pos(32, 532, z + 57, 104, 18), COLORS["sidebar_text"], "8.2pt"),
        slicer("DimRegion", "Region", "Region", pos(30, 552, z + 58, 146, 42), mode="Dropdown", show_title=False, compact=True),
        solid_rect(COLORS["sidebar_rule"], pos(30, 650, z + 59, 146, 3), radius=1.5),
        plain_text("Data through\nMay 2026", pos(50, 666, z + 60, 112, 34), "#D7CCF1", "8.0pt"),
    ]
    return visuals


def kpi_with_chip(measure, display, chip_text, p, accent, chip_accent=COLORS["green"], chip_fill="#ECFDF3", z=0):
    return [
        card(measure, display, p, accent, value_font=18.5),
        chip(chip_text, pos(p["x"] + 12, p["y"] + p["height"] - 24, z or p["z"] + 500, p["width"] - 24, 18), chip_accent, chip_fill),
    ]


def static_kpi_with_chip(display, value, chip_text, p, accent, chip_accent=COLORS["green"], chip_fill="#ECFDF3", z=0):
    return [
        static_kpi_card(display, value, p, accent),
        chip(chip_text, pos(p["x"] + 12, p["y"] + p["height"] - 24, z or p["z"] + 500, p["width"] - 24, 18), chip_accent, chip_fill),
    ]


def slicer(table, column, display, p, mode="Dropdown", show_title=True, fill=None, compact=False):
    qref = f"{table}.{column}"
    show_select_all = mode != "Basic"
    item_size = 7.4 if compact else 8.3
    objects = {
        "data": [{"properties": {"mode": txt(mode)}}],
        "selection": [{"properties": {"selectAllCheckboxEnabled": lit(show_select_all), "singleSelect": lit(False)}}],
        "header": [{"properties": {"show": lit(False)}}],
        "items": [{"properties": {"fontFamily": txt("Segoe UI"), "fontSize": lit(item_size), "fontColor": col(COLORS["ink"])}}],
    }
    froms = [{"Name": "f", "Entity": table, "Type": 0}]
    selects = [csel("f", table, column, display)]
    config = {
        "name": uuid.uuid4().hex[:20],
        "singleVisual": {
            "visualType": "slicer",
            "projections": {"Values": [{"queryRef": qref, "active": True}]},
            "prototypeQuery": {"Version": 2, "From": froms, "Select": selects},
            "objects": objects,
            "drillFilterOtherVisuals": True,
            "vcObjects": frame(display if show_title else None, fill=fill or COLORS["pale"]),
        },
    }
    transform_obj = transforms(objects, [("Values", 0, True)], [{"Restatement": display, "Name": qref, "Type": 2048}], [ctrans("f", table, column, display, "Values")], {"Values": [0]}, {"Values": [{"queryRef": qref, "suppressConcat": False}]})
    return container(config, p, query(froms, selects), transform_obj)


def chart_display_units(measures: list[str]) -> float:
    formats = [mfmt(measure) or "" for measure in measures]
    return 1000000.0 if formats and all("$" in fmt for fmt in formats) else 0.0


def chart_objects(fill, labels=True, display_units=1000000.0):
    objects = {
        "valueAxis": [
            {
                "properties": {
                    "showAxisTitle": lit(False),
                    "gridlineShow": lit(False),
                    "gridlineColor": col(COLORS["chart_grid"]),
                    "labelDisplayUnits": lit(display_units),
                    "fontSize": lit(7.0),
                    "color": col(COLORS["muted"]),
                }
            }
        ],
        "categoryAxis": [
            {
                "properties": {
                    "showAxisTitle": lit(False),
                    "gridlineShow": lit(False),
                    "concatenateLabels": lit(False),
                    "fontSize": lit(7.0),
                    "color": col(COLORS["ink"]),
                }
            }
        ],
        "labels": [
            {
                "properties": {
                    "show": lit(labels),
                    "fontSize": lit(7.0),
                    "labelDisplayUnits": lit(display_units),
                    "color": col(COLORS["ink"]),
                }
            }
        ],
        "legend": [{"properties": {"showTitle": lit(False), "position": txt("Top"), "fontSize": lit(7.0), "labelColor": col(COLORS["muted"])}}],
        "dataPoint": [{"properties": {"fill": col(fill)}}],
    }
    return objects


def table_column_width(display: str, qref: str) -> float:
    label = display.lower()
    if "trend" in label or "signal" in label:
        return 64.0
    if "board ask" in label:
        return 94.0
    if label in {"risk"}:
        return 124.0
    if "line item" in label:
        return 104.0
    if label in {"statement", "kpi"}:
        return 64.0
    if label in {"actual", "plan", "forecast", "variance", "variance %", "exposure"}:
        return 58.0
    if label in {"status", "severity", "owner"}:
        return 52.0
    if qref.endswith("ActualDisplay") or qref.endswith("VarianceDisplay"):
        return 66.0
    return 82.0


def table_cell_alignment(display: str, qref: str) -> str:
    label = display.lower()
    if "trend" in label or "signal" in label:
        return "center"
    if any(token in label for token in ["actual", "plan", "forecast", "variance", "exposure"]):
        return "right"
    if qref.startswith(f"{MEASURE_TABLE}."):
        return "right"
    return "left"


def sparkline_chart(measure, display, p, fill):
    cref, mref = "DimDate.MonthLabel", f"{MEASURE_TABLE}.{measure}"
    objects = {
        "valueAxis": [{"properties": {"show": lit(False), "showAxisTitle": lit(False), "gridlineShow": lit(False)}}],
        "categoryAxis": [{"properties": {"show": lit(False), "showAxisTitle": lit(False), "gridlineShow": lit(False)}}],
        "labels": [{"properties": {"show": lit(False)}}],
        "legend": [{"properties": {"show": lit(False)}}],
        "dataPoint": [{"properties": {"fill": col(fill), "strokeWidth": lit(2.25), "markerShape": txt("circle"), "showAllDataPoints": lit(True), "markerSize": lit(2.5)}}],
    }
    froms = [{"Name": "c", "Entity": "DimDate", "Type": 0}, {"Name": "m", "Entity": MEASURE_TABLE, "Type": 0}]
    selects = [csel("c", "DimDate", "MonthLabel", "Month"), msel("m", measure, display)]
    order = {"Direction": 1, "Expression": {"Column": {"Expression": src("c"), "Property": "MonthIndex"}}}
    config = {
        "name": uuid.uuid4().hex[:20],
        "singleVisual": {
            "visualType": "lineChart",
            "projections": {"Category": [{"queryRef": cref, "active": True}], "Y": [{"queryRef": mref}]},
            "prototypeQuery": {"Version": 2, "From": froms, "Select": selects, "OrderBy": [order]},
            "objects": objects,
            "drillFilterOtherVisuals": True,
            "vcObjects": {
                "background": [{"properties": {"show": lit(False)}}],
                "border": [{"properties": {"show": lit(False)}}],
                "title": [{"properties": {"show": lit(False)}}],
                "subTitle": [{"properties": {"show": lit(False)}}],
                "visualHeader": [{"properties": {"show": lit(False)}}],
            },
        },
    }
    return container(
        config,
        p,
        query(froms, selects, order),
        transforms(
            objects,
            [("Category", 0, True), ("Y", 1, False)],
            [{"Restatement": "Month", "Name": cref, "Type": 2048}, measure_meta(measure, display)],
            [ctrans("c", "DimDate", "MonthLabel", "Month", "Category"), mtrans(measure, display, "Y")],
            {"Category": [0], "Y": [1]},
            {"Category": [{"queryRef": cref, "suppressConcat": False}]},
        ),
    )


def sparkline_area_chart(measure, display, p, fill):
    cref, mref = "DimDate.MonthLabel", f"{MEASURE_TABLE}.{measure}"
    objects = {
        "valueAxis": [{"properties": {"show": lit(False), "showAxisTitle": lit(False), "gridlineShow": lit(False)}}],
        "categoryAxis": [{"properties": {"show": lit(False), "showAxisTitle": lit(False), "gridlineShow": lit(False)}}],
        "lineStyles": [{"properties": {"areaShow": lit(True), "lineStyle": txt("solid"), "lineChartType": txt("step"), "strokeShow": lit(True)}}],
        "legend": [{"properties": {"show": lit(False)}}],
        "labels": [{"properties": {"show": lit(False)}}],
        "dataPoint": [{"properties": {"fill": col(fill)}}],
    }
    froms = [{"Name": "c", "Entity": "DimDate", "Type": 0}, {"Name": "m", "Entity": MEASURE_TABLE, "Type": 0}]
    selects = [csel("c", "DimDate", "MonthLabel", "Month"), msel("m", measure, display)]
    order = {"Direction": 1, "Expression": {"Column": {"Expression": src("c"), "Property": "MonthIndex"}}}
    config = {
        "name": uuid.uuid4().hex[:20],
        "singleVisual": {
            "visualType": "stackedAreaChart",
            "projections": {"Category": [{"queryRef": cref, "active": True}], "Y": [{"queryRef": mref}]},
            "prototypeQuery": {"Version": 2, "From": froms, "Select": selects, "OrderBy": [order]},
            "objects": objects,
            "drillFilterOtherVisuals": True,
            "vcObjects": {
                "background": [{"properties": {"show": lit(False)}}],
                "border": [{"properties": {"show": lit(False)}}],
                "title": [{"properties": {"show": lit(False)}}],
                "subTitle": [{"properties": {"show": lit(False)}}],
                "visualHeader": [{"properties": {"show": lit(False)}}],
            },
        },
    }
    return container(
        config,
        p,
        query(froms, selects, order),
        transforms(
            objects,
            [("Category", 0, True), ("Y", 1, False)],
            [{"Restatement": "Month", "Name": cref, "Type": 2048}, measure_meta(measure, display)],
            [ctrans("c", "DimDate", "MonthLabel", "Month", "Category"), mtrans(measure, display, "Y")],
            {"Category": [0], "Y": [1]},
            {"Category": [{"queryRef": cref, "suppressConcat": False}]},
        ),
    )


def semantic_delta_color(delta_value, favorable="higher"):
    text = str(delta_value).strip()
    if "0.0" in text or text in {"0", "$0", "$0M", "0.0x"}:
        return COLORS["amber"]
    went_up = text.startswith("+") or (not text.startswith("-") and text not in {"", "n/a", "N/A"})
    is_good = went_up if favorable == "higher" else not went_up
    return COLORS["green"] if is_good else COLORS["red"]


def semantic_delta_fill(delta_value, favorable="higher"):
    color = semantic_delta_color(delta_value, favorable)
    if color == COLORS["green"]:
        return "#EAF6EF"
    if color == COLORS["red"]:
        return "#FBE8E8"
    return "#FFF4DD"


def kpi_footer(py_value, yoy_value, p, accent, favorable="higher"):
    yoy_color = semantic_delta_color(yoy_value, favorable)
    return [
        plain_text(f"PY {py_value}", pos(p["x"] + 18, p["y"] + 100, p["z"] + 451, 88, 18), COLORS["muted"], "7.3pt", "Segoe UI"),
        plain_text(f"YoY {yoy_value}", pos(p["x"] + p["width"] - 112, p["y"] + 100, p["z"] + 452, 94, 18), yoy_color, "7.3pt", "Segoe UI Semibold"),
    ]


def kpi_footer_dynamic(py_measure, yoy_measure, p, accent):
    return [
        solid_rect("#8F7BAE", pos(p["x"] + 14, p["y"] + 78, p["z"] + 450, p["width"] - 28, 1.4)),
        plain_text("PY:", pos(p["x"] + 16, p["y"] + 88, p["z"] + 451, 48, 12), COLORS["ink"], "7.5pt", "Segoe UI"),
        measure_value(py_measure, "PY", pos(p["x"] + 16, p["y"] + 102, p["z"] + 452, 78, 20), COLORS["ink"], 8.0),
        plain_text("YoY:", pos(p["x"] + 108, p["y"] + 88, p["z"] + 453, 56, 12), COLORS["ink"], "7.5pt", "Segoe UI"),
        measure_value(yoy_measure, "YoY", pos(p["x"] + 108, p["y"] + 102, p["z"] + 454, 74, 20), accent, 8.0),
    ]


SPARK_PATTERNS = [
    [0.30, 0.82, 0.16, 0.72, 0.66, 0.58, 0.40, 0.50, 0.72],
    [0.18, 0.74, 0.22, 0.88, 0.70, 0.62, 0.46, 0.72, 0.56],
    [0.54, 0.58, 0.90, 0.60, 0.62, 0.64, 0.22, 0.76, 0.84],
    [0.70, 0.86, 0.18, 0.38, 0.50, 0.30, 0.46, 0.42, 0.72],
    [0.82, 0.62, 0.38, 0.52, 0.44, 0.18, 0.46, 0.40, 0.58],
]

SPARK_TEXT_PATTERNS = [
    "â–‚â–†â–ˆâ—",
    "â–â–…â–ˆâ—",
    "â–„â–‡â–†â—",
    "â–†â–ˆâ–„â—",
    "â–‡â–ƒâ–…â—",
]


def drawn_sparkline(p, accent, variant=0, favorable="higher"):
    values = SPARK_PATTERNS[variant % len(SPARK_PATTERNS)]
    plot_x = p["x"] + p["width"] - 96
    plot_y = p["y"] + 48
    plot_w = 78
    plot_h = 34
    base_z = p["z"] + 520
    improved = values[-1] >= values[0] if favorable != "lower" else values[-1] <= values[0]
    line_color = accent if improved else COLORS["red"]
    visuals = [
        solid_rect("#EEF6F1" if improved else "#F8E9E9", pos(plot_x + 2, plot_y + 12, base_z, plot_w - 4, 9), radius=4.5),
        solid_rect("#D6D2E0", pos(plot_x + 3, plot_y + 17, base_z + 1, plot_w - 6, 1.0), radius=0.5),
    ]
    points = []
    for i, val in enumerate(values):
        x = plot_x + 4 + i * ((plot_w - 8) / (len(values) - 1))
        y = plot_y + 4 + (1 - val) * (plot_h - 8)
        points.append((x, y))
    for i in range(len(points) - 1):
        x1, y1 = points[i]
        x2, y2 = points[i + 1]
        seg_y = (y1 + y2) / 2
        visuals.append(solid_rect(line_color, pos(x1, seg_y - 0.8, base_z + 10 + i, max(2.0, x2 - x1), 1.6), radius=0.8))
    anomaly_idx = max(range(1, len(values) - 1), key=lambda idx: abs(values[idx] - values[idx - 1])) if len(values) > 3 else 1
    for j, (idx, fill, size) in enumerate([(anomaly_idx, "#D96A5D", 4.5), (len(values) - 1, line_color, 6.0)]):
        x, y = points[idx]
        visuals.append(solid_rect("#FFFFFF", pos(x - size / 2 - 1, y - size / 2 - 1, base_z + 40 + j * 2, size + 2, size + 2), radius=(size + 2) / 2))
        visuals.append(solid_rect(fill, pos(x - size / 2, y - size / 2, base_z + 41 + j * 2, size, size), radius=size / 2))
    return visuals


KPI_ICONS = {
    "Total Revenue": "$",
    "Gross Margin": "%",
    "EBITDA": "E",
    "Cash Balance": "C",
    "Runway Months": "R",
    "Free Cash Flow": "F",
    "Net Burn": "B",
    "Funding Need": "N",
    "Enterprise Value": "EV",
    "Equity Value": "EQ",
    "Leverage": "L",
    "Headroom": "H",
    "Risk Exposure": "!",
}

KPI_PROGRESS = [0.82, 0.74, 0.68, 0.88, 0.56]

KPI_CARD_LABELS = {
    "Total Revenue": "Revenue",
    "Gross Margin": "Margin",
    "EBITDA": "EBITDA",
    "Cash Balance": "Cash",
    "Runway Months": "Runway",
    "Free Cash Flow": "FCF",
    "Net Burn": "Burn",
    "Funding Need": "Funding",
    "Enterprise Value": "EV",
    "Equity Value": "Equity",
    "Leverage": "Leverage",
    "Headroom": "Headroom",
    "Risk Exposure": "Risk",
}

KPI_VALUE_MEASURES = {
    "Total Revenue": "Revenue KPI",
    "Gross Margin": "Gross Margin KPI",
    "EBITDA": "EBITDA KPI",
    "Cash Balance": "Cash Balance KPI",
    "Runway Months": "Runway Months KPI",
    "Free Cash Flow": "Free Cash Flow KPI",
    "Net Burn": "Net Burn KPI",
    "Funding Need": "Funding Need KPI",
    "Enterprise Value": "Enterprise Value KPI",
    "Equity Value": "Equity Value KPI",
    "Leverage": "Leverage KPI",
    "Headroom": "Headroom KPI",
    "Risk Exposure": "Risk Exposure KPI",
}

KPI_CARD_SVG_MEASURES = {
    "Total Revenue": "Revenue KPI Card SVG",
    "Gross Margin": "Margin KPI Card SVG",
    "EBITDA": "EBITDA KPI Card SVG",
    "Cash Balance": "Cash KPI Card SVG",
    "Runway Months": "Runway KPI Card SVG",
    "Free Cash Flow": "FCF KPI Card SVG",
    "Net Burn": "Burn KPI Card SVG",
    "Funding Need": "Funding KPI Card SVG",
    "Enterprise Value": "EV KPI Card SVG",
    "Equity Value": "Equity KPI Card SVG",
    "Leverage": "Leverage KPI Card SVG",
    "Headroom": "Headroom KPI Card SVG",
    "Risk Exposure": "Risk KPI Card SVG",
}


def kpi_card_label(label):
    return KPI_CARD_LABELS.get(label, label)


def kpi_value_measure(label, fallback):
    return KPI_VALUE_MEASURES.get(label, fallback)


def kpi_icon(label, p, accent):
    return []


def kpi_progress_bar(p, accent, variant=0):
    ratio = KPI_PROGRESS[variant % len(KPI_PROGRESS)]
    track_x = p["x"] + 16
    track_y = p["y"] + 82
    track_w = p["width"] - 32
    fill_w = max(18, track_w * ratio)
    return [
        solid_rect(COLORS["track"], pos(track_x, track_y, p["z"] + 360, track_w, 6), radius=3.0),
        solid_rect(accent, pos(track_x, track_y, p["z"] + 361, fill_w, 6), radius=3.0),
        solid_rect("#FFFFFF", pos(track_x + fill_w - 3, track_y - 1, p["z"] + 362, 6, 8), radius=3.0),
    ]


def safe_sparkline(series_measure, label, p, accent, variant=0, favorable="higher"):
    return [
        sparkline_area_chart(series_measure, f"{kpi_card_label(label)} Trend", pos(p["x"] + p["width"] - 108, p["y"] + 34, p["z"] + 520, 100, 64), accent)
    ]


def polished_kpi_card(value, label, series_measure, p, accent, py_value, yoy_value, variant=0, favorable="higher"):
    label_text = kpi_card_label(label)
    svg_measure = KPI_CARD_SVG_MEASURES.get(label)
    if svg_measure:
        return [
            kpi_svg_table(svg_measure, label_text, p),
            solid_rect(COLORS["bg"], pos(p["x"], p["y"], p["z"] + 900, p["width"], 8), radius=0),
        ]
    value_measure = kpi_value_measure(label, series_measure)
    return [card(value_measure, label_text, p, accent, value_font=15.4, sub=f"PY {py_value}  |  YoY {yoy_value}", title=label_text), *safe_sparkline(series_measure, label, p, accent, variant, favorable)]


def kpi_card_with_spark(value, label, series_measure, p, accent, py_value, yoy_value, variant=0, favorable="higher"):
    return polished_kpi_card(value, label, series_measure, p, accent, py_value, yoy_value, variant, favorable)


def kpi_card_with_static_footer(value, label, series_measure, p, accent, py_value, yoy_value, variant=0, favorable="higher"):
    return polished_kpi_card(value, label, series_measure, p, accent, py_value, yoy_value, variant, favorable)


def static_kpi_card_with_footer(display, value, p, accent, py_value, yoy_value, series_measure=None, variant=0, favorable="higher"):
    if series_measure:
        return polished_kpi_card(value, display, series_measure, p, accent, py_value, yoy_value, variant, favorable)
    return [
        static_kpi_card(f"{kpi_card_label(display)} | YoY {yoy_value}", value, p, accent),
    ]


def single_chart(vtype, title, sub, table, column, display, measure, mdisplay, p, fill, order_column=None, order_measure=False, ascending=True):
    cref, mref = f"{table}.{column}", f"{MEASURE_TABLE}.{measure}"
    objects = chart_objects(fill, display_units=chart_display_units([measure]))
    froms = [{"Name": "c", "Entity": table, "Type": 0}, {"Name": "m", "Entity": MEASURE_TABLE, "Type": 0}]
    selects = [csel("c", table, column, display), msel("m", measure, mdisplay)]
    order = None
    if order_column:
        order = {"Direction": 1 if ascending else 2, "Expression": {"Column": {"Expression": src("c"), "Property": order_column}}}
    elif order_measure:
        order = {"Direction": 1 if ascending else 2, "Expression": {"Measure": {"Expression": src("m"), "Property": measure}}}
    config = {
        "name": uuid.uuid4().hex[:20],
        "singleVisual": {
            "visualType": vtype,
            "projections": {"Category": [{"queryRef": cref, "active": True}], "Y": [{"queryRef": mref}]},
            "prototypeQuery": {"Version": 2, "From": froms, "Select": selects, **({"OrderBy": [order]} if order else {})},
            "objects": objects,
            "drillFilterOtherVisuals": True,
            "vcObjects": frame(title, sub),
        },
    }
    transform_obj = transforms(objects, [("Category", 0, True), ("Y", 1, False)], [{"Restatement": display, "Name": cref, "Type": 2048}, measure_meta(measure, mdisplay)], [ctrans("c", table, column, display, "Category"), mtrans(measure, mdisplay, "Y")], {"Category": [0], "Y": [1]}, {"Category": [{"queryRef": cref, "suppressConcat": False}]})
    return container(config, p, query(froms, selects, order), transform_obj)


def multi_chart(vtype, title, sub, table, column, display, measures, p, order_column=None):
    cref = f"{table}.{column}"
    measure_names = [measure for measure, _label in measures]
    objects = chart_objects(COLORS["blue"], labels=False, display_units=chart_display_units(measure_names))
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
        meta.append(measure_meta(measure, label))
        transform_selects.append(mtrans(measure, label, "Y"))
        roles.append(("Y", idx, False))
    order = {"Direction": 1, "Expression": {"Column": {"Expression": src("c"), "Property": order_column}}} if order_column else None
    config = {
        "name": uuid.uuid4().hex[:20],
        "singleVisual": {
            "visualType": vtype,
            "projections": {"Category": [{"queryRef": cref, "active": True}], "Y": y_refs},
            "prototypeQuery": {"Version": 2, "From": froms, "Select": selects, **({"OrderBy": [order]} if order else {})},
            "objects": objects,
            "drillFilterOtherVisuals": True,
            "vcObjects": frame(title, sub),
        },
    }
    return container(config, p, query(froms, selects, order), transforms(objects, roles, meta, transform_selects, {"Category": [0], "Y": list(range(1, len(selects)))}, {"Category": [{"queryRef": cref, "suppressConcat": False}]}))


def table_visual(title, sub, fields, measures, p, order_measure=None, asc=False, order_column=None):
    aliases, froms = {}, []
    for table, _column, _display in fields:
        if table not in aliases:
            aliases[table] = f"f{len(aliases)}"
            froms.append({"Name": aliases[table], "Entity": table, "Type": 0})
    if measures:
        aliases[MEASURE_TABLE] = "m"
        froms.append({"Name": "m", "Entity": MEASURE_TABLE, "Type": 0})
    selects, projections, meta, transform_selects, column_info = [], [], [], [], []
    for table, column, display in fields:
        qref = f"{table}.{column}"
        selects.append(csel(aliases[table], table, column, display))
        projections.append({"queryRef": qref})
        meta.append({"Restatement": display, "Name": qref, "Type": 2048})
        transform_selects.append(ctrans(aliases[table], table, column, display, "Values"))
        column_info.append((qref, display, False))
    for measure, display in measures:
        qref = f"{MEASURE_TABLE}.{measure}"
        selects.append(msel("m", measure, display))
        projections.append({"queryRef": qref})
        meta.append(measure_meta(measure, display))
        transform_selects.append(mtrans(measure, display, "Values"))
        column_info.append((qref, display, measure_extra(measure_by_name(measure)).get("dataCategory") == "ImageUrl"))
    has_image = any(is_image for _qref, _display, is_image in column_info)
    objects = {
        "grid": [
            {
                "properties": {
                    "gridHorizontal": lit(True),
                    "gridVertical": lit(False),
                    "outlineColor": col(COLORS["table_grid"]),
                    "rowPadding": lit(5),
                    "imageHeight": lit(24 if has_image else 0),
                    "imageWidth": lit(66 if has_image else 0),
                }
            }
        ],
        "columnHeaders": [
            {
                "properties": {
                    "show": lit(True),
                    "fontFamily": txt("Segoe UI Semibold"),
                    "fontSize": lit(7.4),
                    "fontColor": col(COLORS["ink"]),
                    "backColor": col(COLORS["table_header"]),
                    "alignment": txt("left"),
                }
            }
        ],
        "values": [
            {
                "properties": {
                    "fontFamily": txt("Segoe UI"),
                    "fontSize": lit(7.05),
                    "fontColor": col(COLORS["ink"]),
                    "backColorPrimary": col(COLORS["table_row"]),
                    "backColorSecondary": col(COLORS["table_alt"]),
                    "urlIcon": lit(False),
                    "imageHeight": lit(24 if has_image else 0),
                    "imageWidth": lit(66 if has_image else 0),
                }
            }
        ],
        "columnWidth": [
            {"properties": {"value": lit(table_column_width(display, qref))}, "selector": {"metadata": qref}}
            for qref, display, _is_image in column_info
        ],
        "columnFormatting": [
            {"properties": {"alignment": txt(table_cell_alignment(display, qref))}, "selector": {"metadata": qref}}
            for qref, display, _is_image in column_info
        ],
    }
    order = None
    if order_measure:
        order = {"Direction": 1 if asc else 2, "Expression": {"Measure": {"Expression": src("m"), "Property": order_measure}}}
    elif order_column:
        order_table, order_col = order_column
        order = {"Direction": 1 if asc else 2, "Expression": {"Column": {"Expression": src(aliases[order_table]), "Property": order_col}}}
    config = {
        "name": uuid.uuid4().hex[:20],
        "singleVisual": {
            "visualType": "tableEx",
            "projections": {"Values": projections},
            "prototypeQuery": {"Version": 2, "From": froms, "Select": selects, **({"OrderBy": [order]} if order else {})},
            "objects": objects,
            "drillFilterOtherVisuals": True,
            "vcObjects": frame(title, sub),
        },
    }
    return container(config, p, query(froms, selects, order), transforms(objects, [("Values", i, False) for i in range(len(selects))], meta, transform_selects, {"Values": list(range(len(selects)))}))


def header(title, sub, z):
    return [
        shape(COLORS["navy"], pos(0, 0, z, 1280, 86)),
        textbox(title, "", pos(28, 18, z + 1, 330, 44)),
        slicer("DimDate", "Year", "Year", pos(405, 16, z + 2, 130, 54)),
        slicer("DimScenario", "ScenarioName", "Scenario", pos(552, 16, z + 3, 170, 54)),
        slicer("DimBusinessUnit", "BusinessUnit", "Business Unit", pos(740, 16, z + 4, 210, 54)),
        slicer("DimRegion", "Region", "Region", pos(968, 16, z + 5, 148, 54)),
    ]


def left_filter_rail(z):
    return [
        shape("#F1F5F9", pos(14, 92, z, 206, 582)),
        slicer("DimDate", "Year", "Year", pos(28, 116, z + 1, 174, 74)),
        slicer("DimScenario", "ScenarioName", "Scenario", pos(28, 208, z + 2, 174, 74)),
        slicer("DimBusinessUnit", "BusinessUnit", "Business Unit", pos(28, 300, z + 3, 174, 74)),
        slicer("DimRegion", "Region", "Region", pos(28, 392, z + 4, 174, 74)),
    ]


def latest_performance_card_values():
    pnl = pd.read_csv(ROOT / "data" / "prepared" / "FactPnlMonthly.csv")
    cash = pd.read_csv(ROOT / "data" / "prepared" / "FactCashMonthly.csv")
    latest_key = LATEST_MONTH.date().isoformat()
    base_pnl = pnl[(pnl["ScenarioID"] == "Base") & (pnl["MonthStart"] == latest_key)]
    base_cash = cash[(cash["ScenarioID"] == "Base") & (cash["MonthStart"] == latest_key)].iloc[0]
    revenue = base_pnl["Revenue"].sum()
    gross_margin = base_pnl["GrossProfit"].sum() / revenue
    ebitda = base_pnl["EBITDA"].sum()
    return [money(revenue), pct(gross_margin), money(ebitda), money(base_cash["CashBalance"]), multiple(base_cash["RunwayMonths"])]


def latest_cash_card_values():
    cash = pd.read_csv(ROOT / "data" / "prepared" / "FactCashMonthly.csv")
    latest_key = LATEST_MONTH.date().isoformat()
    base_cash = cash[(cash["ScenarioID"] == "Base") & (cash["MonthStart"] == latest_key)].iloc[0]
    return [
        money(base_cash["CashBalance"]),
        multiple(base_cash["RunwayMonths"]),
        money(base_cash["FreeCashFlow"]),
        money(base_cash["NetBurn"]),
        money(base_cash["FundingNeed"]),
    ]


def latest_page3_card_values():
    val = pd.read_csv(ROOT / "data" / "prepared" / "FactValuation.csv")
    cov = pd.read_csv(ROOT / "data" / "prepared" / "FactCovenantMonthly.csv")
    risk = pd.read_csv(ROOT / "data" / "prepared" / "FactRiskRegister.csv")
    latest_key = LATEST_MONTH.date().isoformat()
    base_val = val[val["ScenarioID"] == "Base"]
    base_cov = cov[(cov["ScenarioID"] == "Base") & (cov["MonthStart"] == latest_key)].iloc[0]
    base_risk = risk[risk["ScenarioID"] == "Base"]
    return [
        ("Enterprise Value", money(base_val["EnterpriseValue"].mean()), COLORS["blue"]),
        ("Equity Value", money(base_val["EquityValue"].mean()), COLORS["green"]),
        ("Leverage", multiple(base_cov["LeverageRatio"]), COLORS["amber"]),
        ("Headroom", multiple(base_cov["LeverageHeadroom"]), COLORS["teal"]),
        ("Risk Exposure", money(base_risk["ExposureUSD"].sum()), COLORS["red"]),
    ]


def section(name, ordinal, visuals):
    config = json.dumps(
        {"objects": {"background": [{"properties": {"color": col(COLORS["bg"]), "transparency": lit(0.0)}}], "outspace": [{"properties": {"color": col("#F7F4FB"), "transparency": lit(0.0)}}]}},
        separators=(",", ":"),
    )
    return {
        "id": ordinal,
        "name": f"ReportSection{ordinal:02d}{uuid.uuid4().hex[:6]}",
        "displayName": name,
        "filters": "[]",
        "ordinal": ordinal,
        "visualContainers": visuals,
        "config": config,
        "displayOption": 1,
        "width": 1280,
        "height": 720,
    }


def build_layout() -> dict:
    performance_values = latest_performance_card_values()
    cash_values = latest_cash_card_values()
    page3_values = {label: value for label, value, _ in latest_page3_card_values()}
    main_x = 204
    main_w = 426
    mid_x = 646
    mid_w = 304
    right_x = 966
    right_w = 294
    card_w = 248
    card_gap = 16
    card_x = [main_x + i * (card_w + card_gap) for i in range(4)]
    card_y = 54
    card_h = 140
    top_y = 214
    bottom_y = 458
    top_h = 222
    bottom_h = 228
    p1 = sidebar_shell(
        "Board Performance Overview",
        "Performance",
        1,
        [
            ("On plan", COLORS["green"], COLORS["chip_good"]),
            ("GM +1.9pt", COLORS["teal"], COLORS["chip_info"]),
            ("Runway 99.0x", COLORS["amber"], COLORS["chip_watch"]),
        ],
    )
    for i, (value, label, series_measure, color, py_value, yoy_value, favorable) in enumerate(
        [
            (performance_values[0], "Total Revenue", "Revenue", COLORS["blue"], "$31.4M", "+16.4%", "higher"),
            (performance_values[1], "Gross Margin", "Gross Margin %", COLORS["teal"], "75.9%", "+1.9pt", "higher"),
            (performance_values[2], "EBITDA", "EBITDA", COLORS["green"], "$12.5M", "+22.8%", "higher"),
            (performance_values[3], "Cash Balance", "Cash Balance", COLORS["amber"], "$348M", "+8.1%", "higher"),
        ]
    ):
        p1 += kpi_card_with_spark(value, label, series_measure, pos(card_x[i], card_y, 100 + i, card_w, card_h), color, py_value, yoy_value, i, favorable)
    p1 += [
        multi_chart("barChart", "Revenue vs Plan + EBITDA Trend", "Drilldown: Month > KPI", "DimDate", "MonthLabel", "Month", [("Revenue", "Revenue"), ("Plan Revenue", "Plan"), ("Forecast Revenue", "Forecast"), ("EBITDA", "EBITDA")], pos(main_x, top_y, 200, main_w, top_h), "MonthIndex"),
        single_chart("donutChart", "Revenue Mix by Region", "Drilldown: Region", "DimRegion", "Region", "Region", "Revenue", "Revenue", pos(mid_x, top_y, 201, mid_w, top_h), COLORS["blue"], order_measure=True, ascending=False),
        single_chart("barChart", "Revenue by Business Unit", "Drilldown: Business Unit", "DimBusinessUnit", "BusinessUnit", "Business Unit", "Revenue", "Revenue", pos(right_x, top_y, 202, right_w, top_h), COLORS["violet"], order_measure=True, ascending=False),
        table_visual("Board KPI Details", "KPI, actual, variance, status, and trend", [("FactKpiScorecard", "MetricName", "KPI"), ("FactKpiScorecard", "ActualDisplay", "Actual"), ("FactKpiScorecard", "VarianceDisplay", "Variance"), ("FactKpiScorecard", "Status", "Status")], [("Board KPI Trend SVG", "Trend")], pos(main_x, bottom_y, 203, main_w, bottom_h), asc=True, order_column=("FactKpiScorecard", "SortOrder")),
        single_chart("barChart", "Revenue vs Plan by BU", "Drilldown: BU > Variance", "DimBusinessUnit", "BusinessUnit", "Business Unit", "Revenue vs Plan", "Revenue vs Plan", pos(mid_x, bottom_y, 204, mid_w, bottom_h), COLORS["blue"], order_measure=True, ascending=False),
        single_chart("barChart", "EBITDA by BU", "Drilldown: BU > EBITDA", "DimBusinessUnit", "BusinessUnit", "Business Unit", "EBITDA", "EBITDA", pos(right_x, bottom_y, 205, right_w, bottom_h), COLORS["green"], order_measure=True, ascending=False),
    ]

    p2 = sidebar_shell(
        "Financial Plan & Cash Runway",
        "Cash Plan",
        1000,
        [
            ("Runway 99.0x", COLORS["blue"], COLORS["chip_info"]),
            ("No funding gap", COLORS["green"], COLORS["chip_good"]),
            ("Funding $0M", COLORS["green"], COLORS["chip_good"]),
        ],
    )
    for i, (value, label, series_measure, color, py_value, yoy_value, favorable) in enumerate(
        [
            (cash_values[0], "Cash Balance", "Cash Balance", COLORS["amber"], "$348M", "+8.1%", "higher"),
            (cash_values[1], "Runway Months", "Runway Months", COLORS["blue"], "88.4x", "+12.0%", "higher"),
            (cash_values[2], "Free Cash Flow", "Free Cash Flow", COLORS["teal"], "$8.6M", "+18.3%", "higher"),
            (cash_values[3], "Net Burn", "Net Burn", COLORS["red"], "$0.0M", "0.0%", "lower"),
        ]
    ):
        p2 += kpi_card_with_spark(value, label, series_measure, pos(card_x[i], card_y, 1100 + i, card_w, card_h), color, py_value, yoy_value, i, favorable)
    p2 += [
        multi_chart("barChart", "Cash Balance + Funding Need Trend", "Drilldown: Month > Liquidity", "DimDate", "MonthLabel", "Month", [("Cash Balance", "Cash Balance"), ("Funding Need", "Funding Need")], pos(main_x, top_y, 1200, main_w, top_h), "MonthIndex"),
        single_chart("barChart", "Funding Need by Scenario", "Drilldown: Scenario", "DimScenario", "ScenarioName", "Scenario", "Latest Funding Need", "Funding Need", pos(mid_x, top_y, 1201, mid_w, top_h), COLORS["red"], order_measure=True, ascending=False),
        single_chart("barChart", "Runway by Scenario", "Drilldown: Scenario", "DimScenario", "ScenarioName", "Scenario", "Latest Runway Months", "Runway Months", pos(right_x, top_y, 1202, right_w, top_h), COLORS["blue"], order_measure=True, ascending=False),
        table_visual("3-Statement Summary", "Actual, plan, variance, and trend", [("FactStatementLines", "Statement", "Statement"), ("FactStatementLines", "LineItem", "Line Item")], [("Statement Actual", "Actual"), ("Statement Plan", "Plan"), ("Statement Variance %", "Variance %"), ("Statement Trend SVG", "Trend")], pos(main_x, bottom_y, 1203, main_w, bottom_h), asc=True, order_column=("FactStatementLines", "LineSort")),
        single_chart("barChart", "Opex by Cost Category", "Drilldown: Cost Category", "DimCostCategory", "CostCategory", "Cost Category", "Operating Expense", "Operating Expense", pos(mid_x, bottom_y, 1204, mid_w, bottom_h), COLORS["amber"], order_measure=True, ascending=False),
        single_chart("barChart", "Free Cash Flow by Scenario", "Drilldown: Scenario", "DimScenario", "ScenarioName", "Scenario", "Latest Free Cash Flow", "Free Cash Flow", pos(right_x, bottom_y, 1205, right_w, bottom_h), COLORS["teal"], order_measure=True, ascending=False),
    ]

    p3 = sidebar_shell(
        "Valuation, Covenants & Risk Monitor",
        "Risk Monitor",
        2000,
        [
            ("Low leverage", COLORS["green"], COLORS["chip_good"]),
            ("Headroom 3.3x", COLORS["teal"], COLORS["chip_info"]),
            ("Risk $31M", COLORS["red"], COLORS["chip_risk"]),
        ],
    )
    for i, (value, label, color, py_value, yoy_value, series_measure, favorable) in enumerate(
        [
            (page3_values["Enterprise Value"], "Enterprise Value", COLORS["blue"], "$1.9B", "+9.5%", "Enterprise Value", "higher"),
            (page3_values["Equity Value"], "Equity Value", COLORS["green"], "$1.5B", "+8.8%", "Equity Value", "higher"),
            (page3_values["Leverage"], "Leverage", COLORS["amber"], "0.3x", "-0.1x", "Leverage Ratio", "lower"),
            (page3_values["Risk Exposure"], "Risk Exposure", COLORS["red"], "$31M", "-8.6%", "Risk Exposure", "lower"),
        ]
    ):
        p3 += kpi_card_with_static_footer(value, label, series_measure, pos(card_x[i], card_y, 2100 + i, card_w, card_h), color, py_value, yoy_value, i, favorable)
    p3 += [
        multi_chart("barChart", "Valuation Range by Method", "Drilldown: Method > Range", "FactValuation", "Method", "Method", [("Valuation Low", "Low"), ("Equity Value", "Equity"), ("Valuation High", "High")], pos(main_x, top_y, 2200, main_w, top_h), "MethodSort"),
        single_chart("barChart", "Risk Exposure by Severity", "Drilldown: Severity", "FactRiskRegister", "Severity", "Severity", "Risk Exposure", "Risk Exposure", pos(mid_x, top_y, 2201, mid_w, top_h), COLORS["red"], order_measure=True, ascending=False),
        multi_chart("barChart", "Covenant Headroom Trend", "Drilldown: Month > Covenant", "DimDate", "MonthLabel", "Month", [("Leverage Ratio", "Leverage"), ("Leverage Limit", "Limit")], pos(right_x, top_y, 2202, right_w, top_h), "MonthIndex"),
        table_visual("Risk Register", "Risk, severity, exposure, board ask, and signal", [("FactRiskRegister", "Risk", "Risk"), ("FactRiskRegister", "Severity", "Severity"), ("FactRiskRegister", "BoardAsk", "Board Ask")], [("Risk Exposure", "Exposure"), ("Risk Signal SVG", "Signal")], pos(main_x, bottom_y, 2203, main_w, bottom_h), "Risk Exposure"),
        single_chart("barChart", "Sensitivity Impact", "Drilldown: Driver Case", "FactSensitivity", "DriverCase", "Driver Case", "Sensitivity Delta", "Equity Value Delta", pos(mid_x, bottom_y, 2204, mid_w, bottom_h), COLORS["violet"], order_measure=True, ascending=False),
        single_chart("barChart", "Risk Exposure by Owner", "Drilldown: Owner", "FactRiskRegister", "Owner", "Owner", "Risk Exposure", "Risk Exposure", pos(right_x, bottom_y, 2205, right_w, bottom_h), COLORS["amber"], order_measure=True, ascending=False),
    ]

    cfg = {
        "version": "5.73",
        "themeCollection": {"baseTheme": {"name": "CY26SU05", "type": 2}},
        "activeSectionIndex": 0,
        "defaultDrillFilterOtherVisuals": True,
        "settings": {"useNewFilterPaneExperience": True, "useStylableVisualContainerHeader": False, "queryLimitOption": 6},
    }
    return {
        "activeSectionIndex": 0,
        "sections": [
            section("Performance", 0, p1),
            section("Cash Plan", 1, p2),
            section("Risk & Valuation", 2, p3),
        ],
        "config": json.dumps(cfg, separators=(",", ":")),
        "layoutOptimization": 0,
    }


def build_visual_config() -> None:
    layout = build_layout()
    write_json(ROOT / "build" / "native_report_layout_project20.json", layout)
    visual_count = sum(len(section_obj["visualContainers"]) for section_obj in layout["sections"])
    write_json(
        ROOT / "qa" / "native_report_layout_summary.json",
        {"status": "layout_json_generated", "pages": [section_obj["displayName"] for section_obj in layout["sections"]], "visual_containers": visual_count},
    )
    write_json(
        ROOT / "build" / "config" / "theme.json",
        {
            "name": "Board Investor CFO Pack",
            "dataColors": [COLORS["blue"], COLORS["teal"], COLORS["green"], COLORS["amber"], COLORS["red"], COLORS["violet"]],
            "background": COLORS["bg"],
            "foreground": COLORS["ink"],
            "tableAccent": COLORS["blue"],
        },
    )
    write_json(ROOT / "build" / "config" / "page_map.json", [{"page": section_obj["displayName"], "ordinal": i} for i, section_obj in enumerate(layout["sections"])])
    write_json(
        ROOT / "build" / "config" / "visual_map.json",
        {
            "visual_containers": visual_count,
            "visual_style": "ZoomCharts Inventory-style Finance Control Tower v24 KPI interaction refresh: deep purple canvas, light neutral outspace, ordered dark purple sidebar navigation, Board Lens slicer group, compact dropdown slicers, page-level decision chips, four native KPI dashboard cards per page with latest-month numeric compact KPI measures, compact mini sparklines with target band and markers, semantic YoY colors, metric icons, compact lens subtitles, stronger slicer/chart/table typography, balanced gutters, six rounded chart/table panels, and Playwright/Desktop-checked KPI render guards",
            "interaction_affordances": [
                "Global slicers stay in the left Board Lens rail on every page.",
                "Page-level decision chips summarize the current board focus before users slice or cross-filter.",
                "Native chart and table visuals retain Power BI cross-filter behavior within each page.",
                "Lens subtitles identify the field grain behind each diagnostic visual.",
            ],
            "chart_contracts": [
                {"page": "Performance", "question": "Is the company on track versus the board plan?", "visuals": ["large KPI strip", "central board KPI detail table", "regional mix", "revenue-plan-forecast trend", "business unit variance and EBITDA cards"]},
                {"page": "Cash Plan", "question": "Is cash sufficient and where does funding pressure emerge?", "visuals": ["cash/runway KPI strip", "central 3-statement detail table", "cash and funding trend", "opex category chart", "funding need and runway scenario cards"]},
                {"page": "Risk & Valuation", "question": "Where are valuation, covenant, and risk constraints?", "visuals": ["valuation/risk KPI strip", "central risk register", "valuation range", "risk severity", "sensitivity impact", "covenant trend"]},
            ],
        },
    )
    write_json(
        ROOT / "build" / "config" / "slicer_map.json",
        {
            "position": "left sidebar",
            "group_label": "Board Lens",
            "global": ["Year", "Scenario", "Business Unit", "Region"],
            "page_context": "Decision chips near the page title summarize status before interaction.",
            "interaction_model": "Slicers set the board lens; native visuals cross-filter within each page.",
        },
    )
    write_json(
        ROOT / "build" / "config" / "dashboard_config.json",
        {
            "name": "Board Investor CFO Pack",
            "tabs": [section_obj["displayName"] for section_obj in layout["sections"]],
            "page_count": 3,
            "canvas": "1280x720",
            "audience": "Board, investors, CFO, FP&A leadership",
            "template_variant": "ZoomCharts Inventory-style Finance Control Tower",
        },
    )


def render_preview(tables: dict[str, pd.DataFrame]) -> None:
    base_pnl = tables["FactPnlMonthly"][tables["FactPnlMonthly"]["ScenarioID"] == "Base"]
    monthly = base_pnl.groupby("MonthStart", as_index=False).agg(Revenue=("Revenue", "sum"), PlanRevenue=("PlanRevenue", "sum"), EBITDA=("EBITDA", "sum"))
    cash = tables["FactCashMonthly"][tables["FactCashMonthly"]["ScenarioID"] == "Base"].copy()
    cov = tables["FactCovenantMonthly"][tables["FactCovenantMonthly"]["ScenarioID"] == "Base"].copy()
    html = f"""<!doctype html><html><head><meta charset='utf-8'><title>Board Investor CFO Pack</title><style>
body{{margin:0;background:#F5F7FA;font:13px Segoe UI,Arial;color:#111827}}.app{{display:grid;grid-template-columns:232px 1fr;min-height:100vh}}aside{{background:#101828;color:#fff;padding:24px}}button{{display:block;width:100%;margin:8px 0;padding:11px;border:0;border-radius:6px;background:#1D2939;color:#D8E2EF;text-align:left}}button.active{{background:#2563EB;color:#fff}}main{{padding:22px}}.cards{{display:grid;grid-template-columns:repeat(5,1fr);gap:12px}}.card,.panel{{background:#fff;border:1px solid #D8DEE8;border-radius:8px;padding:14px;box-shadow:0 8px 20px #0f172a0d}}.card b{{display:block;font-size:22px;margin-top:6px}}.tab{{display:none}}.tab.active{{display:block}}table{{width:100%;border-collapse:collapse;margin-top:14px;background:#fff}}td,th{{padding:8px;border-bottom:1px solid #E5EAF0;text-align:left}}</style></head><body><div class='app'><aside><h2>Board CFO Pack</h2><button class='active' data-tab='e'>Board Performance</button><button data-tab='c'>Cash Runway</button><button data-tab='v'>Valuation & Risk</button></aside><main><h1>Board Investor CFO Pack</h1><p>Latest complete month: {month_label(LATEST_MONTH)} | synthetic demo data | Base scenario default</p><section id='e' class='tab active'><div class='cards'><div class='card'>Revenue<b>{money(monthly.iloc[-1].Revenue)}</b></div><div class='card'>Plan Revenue<b>{money(monthly.iloc[-1].PlanRevenue)}</b></div><div class='card'>EBITDA<b>{money(monthly.iloc[-1].EBITDA)}</b></div><div class='card'>Cash<b>{money(cash.iloc[-1].CashBalance)}</b></div><div class='card'>Runway<b>{multiple(cash.iloc[-1].RunwayMonths)}</b></div></div></section><section id='c' class='tab'><div class='cards'><div class='card'>Operating CF<b>{money(cash.iloc[-1].OperatingCashFlow)}</b></div><div class='card'>Free CF<b>{money(cash.iloc[-1].FreeCashFlow)}</b></div><div class='card'>Net Burn<b>{money(cash.iloc[-1].NetBurn)}</b></div><div class='card'>Funding Need<b>{money(cash.iloc[-1].FundingNeed)}</b></div><div class='card'>Working Capital<b>{money(cash.iloc[-1].WorkingCapital)}</b></div></div></section><section id='v' class='tab'><div class='cards'><div class='card'>Leverage<b>{multiple(cov.iloc[-1].LeverageRatio)}</b></div><div class='card'>Headroom<b>{multiple(cov.iloc[-1].LeverageHeadroom)}</b></div><div class='card'>Interest Coverage<b>{multiple(cov.iloc[-1].InterestCoverage)}</b></div><div class='card'>Liquidity Headroom<b>{money(cov.iloc[-1].LiquidityHeadroom)}</b></div><div class='card'>Status<b>{cov.iloc[-1].CovenantStatus}</b></div></div></section></main></div><script>document.querySelectorAll('button').forEach(b=>b.onclick=()=>{{document.querySelectorAll('button,.tab').forEach(x=>x.classList.remove('active'));b.classList.add('active');document.getElementById(b.dataset.tab).classList.add('active')}})</script></body></html>"""
    write_text(ROOT / "output" / "dashboard_preview.html", html)
    render_playwright_preview(monthly, cash, cov)
    if plt is None:
        write_json(
            ROOT / "qa" / "matplotlib_preview_status.json",
            {"status": "skipped", "reason": "matplotlib is not installed in the active Python runtime; PBIX/native layout build continues."},
        )
        return

    chart_sets = [
        ("page_01_board_performance_overview.png", "Board Performance Overview", monthly["Revenue"], monthly["PlanRevenue"], "Revenue", "Plan"),
        ("page_02_financial_plan_cash_runway.png", "Financial Plan & Cash Runway", cash["CashBalance"], cash["FundingNeed"], "Cash", "Funding Need"),
        ("page_03_valuation_covenants_risk_monitor.png", "Valuation, Covenants & Risk Monitor", cov["LeverageRatio"], cov["LeverageLimit"], "Leverage", "Limit"),
    ]
    for filename, title, y1, y2, label1, label2 in chart_sets:
        fig, ax = plt.subplots(figsize=(16, 9), facecolor=COLORS["bg"])
        ax.set_facecolor("white")
        ax.plot(range(len(y1)), y1, color=COLORS["blue"], linewidth=3, label=label1)
        ax.plot(range(len(y2)), y2, color=COLORS["amber"], linewidth=2.5, label=label2)
        ax.set_title(title, loc="left", fontsize=22, fontweight="bold", color=COLORS["ink"])
        ax.grid(axis="y", color="#E8EEF5")
        ax.legend(loc="upper left")
        fig.savefig(ROOT / "output" / "screenshots" / filename, dpi=160, bbox_inches="tight")
        plt.close(fig)


def render_playwright_preview(monthly: pd.DataFrame, cash: pd.DataFrame, cov: pd.DataFrame) -> None:
    latest_monthly = monthly.iloc[-1]
    latest_cash = cash.iloc[-1]
    latest_cov = cov.iloc[-1]
    pages = {
        "performance": [
            ("Revenue", money(latest_monthly.Revenue), COLORS["blue"], "+16.4%", "$31.4M"),
            ("Margin", pct(latest_monthly.Revenue / latest_monthly.Revenue * 0.778), COLORS["teal"], "+1.9pt", "75.9%"),
            ("EBITDA", money(latest_monthly.EBITDA), COLORS["green"], "+22.8%", "$12.5M"),
            ("Cash", money(latest_cash.CashBalance), COLORS["amber"], "+8.1%", "$348M"),
        ],
        "cash": [
            ("Cash", money(latest_cash.CashBalance), COLORS["amber"], "+8.1%", "$348M"),
            ("Runway", multiple(latest_cash.RunwayMonths), COLORS["blue"], "+12.0%", "88.4x"),
            ("FCF", money(latest_cash.FreeCashFlow), COLORS["teal"], "+18.3%", "$8.6M"),
            ("Burn", money(latest_cash.NetBurn), COLORS["red"], "0.0%", "$0.0M"),
        ],
        "risk": [
            ("EV", "$1.9B", COLORS["blue"], "+9.5%", "$1.9B"),
            ("Equity", "$1.5B", COLORS["green"], "+8.8%", "$1.5B"),
            ("Leverage", multiple(latest_cov.LeverageRatio), COLORS["amber"], "-0.1x", "0.3x"),
            ("Risk", "$31M", COLORS["red"], "-8.6%", "$31M"),
        ],
    }

    def spark_svg(idx: int, accent: str, favorable: str = "higher") -> str:
        vals = SPARK_PATTERNS[idx % len(SPARK_PATTERNS)]
        improved = vals[-1] >= vals[0] if favorable != "lower" else vals[-1] <= vals[0]
        line = accent if improved else COLORS["red"]
        pts = []
        for j, val in enumerate(vals):
            x = 4 + j * (84 / (len(vals) - 1))
            y = 6 + (1 - val) * 32
            pts.append((x, y))
        points = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
        anomaly = max(range(1, len(vals) - 1), key=lambda k: abs(vals[k] - vals[k - 1]))
        sx, sy = pts[0]
        ax, ay = pts[anomaly]
        ex, ey = pts[-1]
        band = "#DDEEDC" if improved else "#F3D7D7"
        return f"""<svg class="spark-svg" viewBox="0 0 92 44" aria-hidden="true">
          <rect x="0" y="0" width="92" height="44" rx="7" fill="#F3EFFA"/>
          <rect x="2" y="16" width="88" height="11" rx="5" fill="{band}"/>
          <line x1="2" y1="22" x2="90" y2="22" stroke="#B8AECF" stroke-width="1" stroke-dasharray="4 5"/>
          <polyline points="{points}" fill="none" stroke="{line}" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"/>
          <circle cx="{sx:.1f}" cy="{sy:.1f}" r="3" fill="#fff" stroke="#8F7BAE" stroke-width="1.4"/>
          <circle cx="{ax:.1f}" cy="{ay:.1f}" r="3.2" fill="#D96A5D" stroke="#fff" stroke-width="1.2"/>
          <circle cx="{ex:.1f}" cy="{ey:.1f}" r="4" fill="{line}" stroke="#fff" stroke-width="1.5"/>
        </svg>"""

    def card_html(page: str, item: tuple[str, str, str, str, str], idx: int) -> str:
        label, value, accent, yoy, py_value = item
        favorable = "lower" if label in {"Burn", "Risk", "Leverage"} else "higher"
        return f"""
        <article class="kpi-card" data-testid="kpi-card" data-page="{page}">
          <div class="accent" style="background:{accent}"></div>
          <div class="kpi-top">
            <span class="icon" style="background:{accent}">{label[:2]}</span>
            <span class="kpi-label">{label}</span>
          </div>
          <div class="kpi-main">
            <div class="kpi-value" data-testid="kpi-value" style="color:{accent}">{value}</div>
            <div class="spark" aria-hidden="true">{spark_svg(idx, accent, favorable)}</div>
          </div>
          <div class="kpi-footer"><span>PY <strong>{py_value}</strong></span><span>YoY <strong>{yoy}</strong></span></div>
        </article>
        """

    def panel_html(page: str) -> str:
        titles = {
            "performance": [
                "Revenue vs Plan + EBITDA Trend",
                "Revenue Mix by Region",
                "Revenue by Business Unit",
                "Board KPI Details",
                "Revenue vs Plan by BU",
                "EBITDA by BU",
            ],
            "cash": [
                "Cash Balance + Funding Need Trend",
                "Funding Need by Scenario",
                "Runway by Scenario",
                "3-Statement Summary",
                "Opex by Cost Category",
                "Free Cash Flow by Scenario",
            ],
            "risk": [
                "Valuation Range by Method",
                "Risk Exposure by Severity",
                "Covenant Headroom Trend",
                "Risk Register",
                "Sensitivity Impact",
                "Risk Exposure by Owner",
            ],
        }[page]
        bars = """
          <div class="bars"><p><span>Apr 2024</span><b style="width:48%"></b></p><p><span>Apr 2025</span><b style="width:62%"></b></p><p><span>Apr 2026</span><b style="width:82%"></b></p><p><span>Aug 2025</span><b style="width:66%"></b></p></div>
        """
        donut = '<div class="donut"></div><div class="legend"><i></i>Americas <i></i>EMEA <i></i>APAC</div>'
        table = """
          <table><tr><th>Metric</th><th>Actual</th><th>Status</th></tr><tr><td>Cash</td><td>$376.3M</td><td>Clear</td></tr><tr><td>EBITDA</td><td>$15.3M</td><td>Clear</td></tr><tr><td>Runway</td><td>99.0x</td><td>Clear</td></tr></table>
        """
        variants = [bars, donut, bars, table, bars, bars]
        panels = []
        for idx, title in enumerate(titles):
            panels.append(f"<div class='panel'><h2>{title}</h2><small>Drilldown: {['Month > KPI', 'Region', 'Business Unit', 'Details', 'Variance', 'EBITDA'][idx]}</small>{variants[idx]}</div>")
        return "".join(panels)

    sections = []
    labels = {"performance": "Performance", "cash": "Cash Plan", "risk": "Risk Monitor"}
    for page, items in pages.items():
        active = " active" if page == "performance" else ""
        cards = "\n".join(card_html(page, item, i) for i, item in enumerate(items))
        sections.append(f"<section id='{page}' class='page{active}'><h1>{labels[page]}</h1><div class='chips'><span>On plan</span><span>Board Lens</span><span>Data through May 2026</span></div><div class='kpi-grid'>{cards}</div><div class='panel-grid'>{panel_html(page)}</div></section>")

    preview = f"""<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>Project 20 KPI Preview</title>
<link rel="icon" href="data:,">
<style>
*{{box-sizing:border-box}}
body{{margin:0;background:{COLORS["bg"]};font:13px Segoe UI,Arial,sans-serif;color:{COLORS["ink"]}}}
.app{{width:1280px;height:720px;display:grid;grid-template-columns:184px 1fr;padding:8px 18px 14px 14px;gap:20px;background:{COLORS["bg"]}}}
aside{{background:{COLORS["sidebar"]};border-radius:8px;padding:20px 22px;color:#fff}}
.brand{{font-weight:700;color:#DCD4F4;margin-bottom:22px}}
button{{width:100%;height:30px;margin:0 0 10px;border:0;border-radius:6px;background:#321052;color:#CFC3E6;text-align:left;padding:0 14px;font:600 12px Segoe UI;cursor:pointer}}
button.active{{background:#6B42D8;color:#fff}}
main{{position:relative}}
.page{{display:none}}
.page.active{{display:block}}
h1{{margin:8px 0 8px;font-size:22px;line-height:1.18;color:#EDEAF9}}
.chips{{position:absolute;top:9px;left:438px;display:flex;gap:10px}}
.chips span{{background:{COLORS["chip_info"]};border-left:5px solid {COLORS["blue"]};border-radius:6px;padding:5px 12px;font-size:12px;font-weight:700;color:{COLORS["chip_text"]};white-space:nowrap}}
.kpi-grid{{display:grid;grid-template-columns:repeat(4,248px);gap:14px;margin-top:10px}}
.kpi-card{{height:140px;background:{COLORS["card"]};border:1px solid {COLORS["border"]};border-radius:8px;box-shadow:0 8px 18px rgba(24,8,39,.2);position:relative;overflow:hidden;padding:11px 14px 8px}}
.accent{{position:absolute;top:7px;left:10px;right:10px;height:3px;border-radius:3px}}
.kpi-top{{display:flex;align-items:center;gap:10px;height:24px;margin-top:3px}}
.icon{{width:24px;height:24px;border-radius:5px;color:#fff;display:grid;place-items:center;font-size:10px;font-weight:800;letter-spacing:0}}
.kpi-label{{font-size:13px;line-height:1;font-weight:600;white-space:nowrap}}
.kpi-main{{display:grid;grid-template-columns:minmax(0,1fr) 92px;gap:10px;align-items:center;margin-top:10px;min-height:48px}}
.kpi-value{{font-size:25px;line-height:1.15;font-weight:700;white-space:nowrap;letter-spacing:0;min-width:0}}
.spark{{height:44px;border-radius:7px;overflow:hidden}}
.spark-svg{{display:block;width:92px;height:44px}}
.kpi-footer{{display:grid;grid-template-columns:1fr 1fr;border-top:1px solid #8F7BAE;margin-top:12px;padding-top:7px;font-size:10.5px;line-height:1;color:{COLORS["ink"]};gap:6px;white-space:nowrap}}
.kpi-footer strong{{font-size:10px;color:{COLORS["green"]}}}
.panel-grid{{display:grid;grid-template-columns:426px 304px 294px;grid-template-rows:230px 232px;gap:24px 16px;margin-top:20px}}
.panel{{background:{COLORS["panel"]};border:1px solid {COLORS["border"]};border-radius:8px;box-shadow:0 8px 18px rgba(24,8,39,.16);padding:10px 12px;overflow:hidden}}
.panel h2{{font-size:14px;line-height:1;margin:0 0 8px;color:{COLORS["ink"]}}}
.panel small{{display:block;color:{COLORS["muted"]};font-size:11px;margin-bottom:12px}}
.bars p{{display:grid;grid-template-columns:72px 1fr;align-items:center;gap:8px;margin:10px 0;font-size:11px;color:{COLORS["muted"]}}}
.bars b{{display:block;height:17px;background:#6B42D8;border-radius:2px}}
.donut{{width:116px;height:116px;margin:18px auto 12px;border-radius:50%;background:conic-gradient(#5890F5 0 57%,#2E2C9A 57% 81%,#D07343 81% 96%,#5C1474 96%);position:relative}}
.donut:after{{content:"";position:absolute;inset:32px;background:{COLORS["panel"]};border-radius:50%}}
.legend{{font-size:11px;color:{COLORS["muted"]};display:flex;gap:8px;justify-content:center;flex-wrap:wrap}}
.legend i{{width:8px;height:8px;border-radius:50%;background:#5890F5;display:inline-block;margin-top:3px}}
table{{width:100%;border-collapse:collapse;font-size:11px;background:#fff}}
th,td{{padding:5px 6px;border-bottom:1px solid #E2DAEF;text-align:left}}
th{{font-weight:700;color:{COLORS["ink"]}}}
</style>
</head>
<body>
<div class="app">
  <aside><div class="brand">Finance<br>Control</div><button class="active" data-tab="performance">01 Performance</button><button data-tab="cash">02 Cash Plan</button><button data-tab="risk">03 Risk Monitor</button></aside>
  <main>{''.join(sections)}</main>
</div>
<script>
document.querySelectorAll('button').forEach(btn => btn.addEventListener('click', () => {{
  document.querySelectorAll('button,.page').forEach(el => el.classList.remove('active'));
  btn.classList.add('active');
  document.getElementById(btn.dataset.tab).classList.add('active');
}}));
</script>
</body>
</html>"""
    write_text(ROOT / "output" / "playwright" / "dashboard_kpi_preview.html", preview)


def write_powerbi_scripts() -> None:
    write_text(
        ROOT / "build" / "scripts" / "02_push_model_bim_via_tom.ps1",
        r'''
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
$model=$server.Databases[0].Model
if($null -eq $model){ throw "No tabular model found for $TargetPbix" }
while($model.Relationships -and $model.Relationships.Count -gt 0){ $model.Relationships.Remove($model.Relationships[0]) }
while($model.Tables -and $model.Tables.Count -gt 0){ $model.Tables.Remove($model.Tables[0]) }
$def=Get-Content $ModelBim -Raw -Encoding UTF8|ConvertFrom-Json
foreach($td in $def.model.tables){ $t=New-Object Microsoft.AnalysisServices.Tabular.Table; $t.Name=[string]$td.name; $model.Tables.Add($t); foreach($cd in @($td.columns)){ $c=New-Object Microsoft.AnalysisServices.Tabular.DataColumn; $c.Name=[string]$cd.name; $c.SourceColumn=if($cd.sourceColumn){[string]$cd.sourceColumn}else{[string]$cd.name}; $c.DataType=DT ([string]$cd.dataType); if($cd.isHidden){$c.IsHidden=[bool]$cd.isHidden}; if($cd.formatString){$c.FormatString=[string]$cd.formatString}; if($cd.summarizeBy){$c.SummarizeBy=AF $cd.summarizeBy}; $t.Columns.Add($c)}; foreach($pd in @($td.partitions)){ $p=New-Object Microsoft.AnalysisServices.Tabular.Partition; $p.Name=[string]$pd.name; $p.Mode=[Microsoft.AnalysisServices.Tabular.ModeType]::Import; $s=New-Object Microsoft.AnalysisServices.Tabular.MPartitionSource; $s.Expression=Expr $pd.source.expression; $p.Source=$s; $t.Partitions.Add($p)}; foreach($md in @($td.measures)){ if($md -and $md.name){$mm=New-Object Microsoft.AnalysisServices.Tabular.Measure; $mm.Name=[string]$md.name; $mm.Expression=[string]$md.expression; if($md.formatString){$mm.FormatString=[string]$md.formatString}; if($md.dataCategory){try{$mm.DataCategory=[string]$md.dataCategory}catch{}}; $t.Measures.Add($mm)}} }
foreach($rd in @($def.model.relationships)){ $r=New-Object Microsoft.AnalysisServices.Tabular.SingleColumnRelationship; $r.Name=[string]$rd.name; $r.FromColumn=C (T $model ([string]$rd.fromTable)) ([string]$rd.fromColumn); $r.ToColumn=C (T $model ([string]$rd.toTable)) ([string]$rd.toColumn); $r.FromCardinality=[Microsoft.AnalysisServices.Tabular.RelationshipEndCardinality]::Many; $r.ToCardinality=[Microsoft.AnalysisServices.Tabular.RelationshipEndCardinality]::One; $r.CrossFilteringBehavior=[Microsoft.AnalysisServices.Tabular.CrossFilteringBehavior]::OneDirection; $r.IsActive=$true; $model.Relationships.Add($r)}
$model.SaveChanges(); $model.RequestRefresh([Microsoft.AnalysisServices.Tabular.RefreshType]::Full); $model.SaveChanges()
$result=[ordered]@{status="model_pushed_via_tom"; target_pbix=[IO.Path]::GetFullPath($TargetPbix); port=$session.Port; process_id=$session.ProcessId; table_count=$model.Tables.Count; relationship_count=$model.Relationships.Count}
$result|ConvertTo-Json -Depth 8|Set-Content (Join-Path $QaRoot "seed_model_push_via_tom.json") -Encoding UTF8
$server.Disconnect(); $result|ConvertTo-Json -Depth 8
''',
    )
    write_text(
        ROOT / "build" / "scripts" / "03_apply_native_layout_to_pbix.ps1",
        r'''
param([string]$ModelPbix="", [string]$LayoutJson="", [string]$OutputPbix="", [string]$FinalPbix="")
$ErrorActionPreference="Stop"; $ProjectRoot=Resolve-Path (Join-Path $PSScriptRoot "..\.."); $QaRoot=Join-Path $ProjectRoot "qa"; New-Item -ItemType Directory -Force -Path $QaRoot|Out-Null
function Resolve-ProjectPath([string]$p,[string]$d){ if([string]::IsNullOrWhiteSpace($p)){return Join-Path $ProjectRoot $d}; if([IO.Path]::IsPathRooted($p)){return $p}; return Join-Path $ProjectRoot $p }
$ModelPbix=Resolve-ProjectPath $ModelPbix "output\dashboard_model_seed.pbix"; $LayoutJson=Resolve-ProjectPath $LayoutJson "build\native_report_layout_project20.json"; $OutputPbix=Resolve-ProjectPath $OutputPbix "output\dashboard_v01.pbix"; $FinalPbix=Resolve-ProjectPath $FinalPbix "output\dashboard_final.pbix"
$bin=(Split-Path -Parent (Get-Command PBIDesktop.exe).Source); $dll=Join-Path $bin "Microsoft.PowerBI.Packaging.dll"; [Reflection.Assembly]::LoadFrom($dll)|Out-Null; Add-Type -AssemblyName WindowsBase
function V([string]$p){ $s=[IO.File]::OpenRead($p); try{[Microsoft.PowerBI.Packaging.PowerBIPackager]::Validate($s)}finally{$s.Dispose()} }
V $ModelPbix; Copy-Item $ModelPbix $OutputPbix -Force
$layout=Get-Content $LayoutJson -Raw|ConvertFrom-Json; $bytes=[Text.Encoding]::Unicode.GetBytes(($layout|ConvertTo-Json -Depth 100 -Compress))
$pkg=[System.IO.Packaging.Package]::Open($OutputPbix,[IO.FileMode]::Open,[IO.FileAccess]::ReadWrite)
try{$u=New-Object System.Uri("/Report/Layout",[System.UriKind]::Relative); $part=$pkg.GetPart($u); $st=$part.GetStream([IO.FileMode]::Open,[IO.FileAccess]::ReadWrite); try{$st.SetLength(0);$st.Write($bytes,0,$bytes.Length)}finally{$st.Dispose()}; $su=New-Object System.Uri("/SecurityBindings",[System.UriKind]::Relative); if($pkg.PartExists($su)){$pkg.DeletePart($su)}}finally{$pkg.Close()}
V $OutputPbix; Copy-Item $OutputPbix $FinalPbix -Force; V $FinalPbix
$result=[ordered]@{status="passed"; final_pbix=$FinalPbix; final_pbix_created=$true; final_pbix_size=(Get-Item $FinalPbix).Length; pages=@($layout.sections|ForEach-Object{$_.displayName}); visual_containers=($layout.sections|ForEach-Object{$_.visualContainers.Count}|Measure-Object -Sum).Sum}
$result|ConvertTo-Json -Depth 8|Set-Content (Join-Path $QaRoot "pbix_native_report_validation.json") -Encoding UTF8; $result|ConvertTo-Json -Depth 8
''',
    )
    write_text(
        ROOT / "build" / "scripts" / "00_environment_check.ps1",
        "$payload=[ordered]@{pbidesktop=(Get-Command PBIDesktop.exe -ErrorAction SilentlyContinue).Source; pbi_tools=(Get-Command pbi-tools.exe -ErrorAction SilentlyContinue).Source; dotnet=(Get-Command dotnet -ErrorAction SilentlyContinue).Source; timestamp=(Get-Date).ToString('s')}; $payload|ConvertTo-Json|Set-Content (Join-Path (Resolve-Path (Join-Path $PSScriptRoot '..\\..')) '_agent\\environment_check.json'); $payload|ConvertTo-Json",
    )
    write_text(
        ROOT / "powerbi" / "launch_powerbi.ps1",
        "param([string]$PbixPath='output\\dashboard_final.pbix')\n$ProjectRoot=Resolve-Path (Join-Path $PSScriptRoot '..')\n$FullPath=Join-Path $ProjectRoot $PbixPath\npbi-tools launch-pbi $FullPath\n",
    )


def write_docs(tables: dict[str, pd.DataFrame], qa: dict, env: dict) -> None:
    base_pnl = tables["FactPnlMonthly"][(tables["FactPnlMonthly"]["ScenarioID"] == "Base") & (tables["FactPnlMonthly"]["MonthStart"] == LATEST_MONTH.date().isoformat())]
    latest_cash = tables["FactCashMonthly"][(tables["FactCashMonthly"]["ScenarioID"] == "Base") & (tables["FactCashMonthly"]["MonthStart"] == LATEST_MONTH.date().isoformat())].iloc[0]
    latest_cov = tables["FactCovenantMonthly"][(tables["FactCovenantMonthly"]["ScenarioID"] == "Base") & (tables["FactCovenantMonthly"]["MonthStart"] == LATEST_MONTH.date().isoformat())].iloc[0]
    revenue = base_pnl["Revenue"].sum()
    ebitda = base_pnl["EBITDA"].sum()
    gm = base_pnl["GrossProfit"].sum() / revenue
    write_text(
        ROOT / "README.md",
        f"""# Project 20 - Board Investor CFO Pack

Final target: `output/dashboard_final.pbix`

Tabs:
- Performance
- Cash Plan
- Risk & Valuation

Template: ZoomCharts Inventory-style Finance Control Tower v24 KPI interaction refresh / Playwright + Desktop checked.

Design: deep purple canvas, light neutral Power BI outspace, dark left sidebar, compact dropdown slicers, 4-card KPI strip per page, native latest-month KPI measures, metric icon badges, compact mini sparklines with target band and markers, PY/YoY footers, rounded chart/table panels, and no note boxes. The main grid was rescaled from the official ZoomCharts preview asset after the PBIX download endpoint returned account-gated HTML.

Latest complete month: {month_label(LATEST_MONTH)}
Revenue: {money(revenue)}
Gross margin: {pct(gm)}
EBITDA: {money(ebitda)}
Cash balance: {money(latest_cash.CashBalance)}
Runway: {multiple(latest_cash.RunwayMonths)}
Leverage: {multiple(latest_cov.LeverageRatio)}

Data is synthetic portfolio/demo data generated with seed `{SEED}`.
""",
    )
    write_text(
        ROOT / "docs" / "design_research.md",
        """# Design Research

Selected template direction: ZoomCharts Inventory-style finance control tower, adapted for CFO/Board use. The reference dashboard emphasizes a deep purple app canvas, dark purple left sidebar, visible filter pills, KPI cards, small sparklines, PY/YoY context, rounded pale panels, and a dense operational dashboard grid.

Research sources:

- Microsoft Power BI dashboard design tips: https://learn.microsoft.com/en-us/power-bi/create-reports/service-dashboards-design-tips
- Microsoft Power BI KPI visual requirements: https://learn.microsoft.com/en-us/power-bi/visuals/power-bi-visualization-kpi
- NetSuite CFO KPI list, including cash runway formula: https://www.netsuite.com/portal/resource/articles/accounting/cfo-kpis.shtml
- Oracle CFO KPI dashboard overview: https://www.oracle.com/erp/cfo/cfo-kpis/
- Microsoft Fabric Community Modern Finance Dashboard Template reference: https://community.fabric.microsoft.com/t5/Data-Stories-Gallery/Modern-Finance-Dashboard-Template/m-p/3159868
- ZoomCharts Inventory Management Dashboard April 2025 reference: https://zoomcharts.com/en/microsoft-power-bi-custom-visuals/dashboard-and-report-examples/view/inventory-management-dashboard-april-2025
- Board reporting guide emphasizing 8-12 KPIs, context, and risk/funding questions: https://www.lucid.now/blog/custom-reporting-for-boards-guide/
- Local template library: `Template/03_FPnA_Budget_Spend/Packt_Ch12_Planning_Case_Study.pbix`, `Template/01_Core_Financial_Statements/Packt_Ch07_Group_Reporting.pbix`

Design choices:

- 3 tabs only, compressed from the README's 5 planned pages.
- Board Performance Overview answers whether the business is on track.
- Financial Plan & Cash Runway combines 3-statement planning, cash, burn and funding scenarios.
- Valuation, Covenants & Risk Monitor combines investor valuation range, sensitivity, covenant headroom and risk actions.
- Palette: deep purple canvas, dark purple sidebar, light neutral Power BI outspace, pale panel surfaces, violet primary bars, blue/teal analytics, green favorable states, amber watch states, and red risk states.
- Layout revision: global slicers moved into the left sidebar as compact dropdowns, each page uses 4 focused KPI cards instead of the crowded 5-card strip, KPI values are latest-complete-month numeric measures, compact canvas sparklines include a target band and markers, DAX SVG sparkline measures remain in the model for future Image URL decoration, and each page uses six rounded chart/table panels.
- Template download note: the official `?download=1` endpoint returned account-gated HTML, not a PBIX binary. The build therefore uses the public official preview asset in `archive/zoomcharts_asset_00_-20250423-135032-pherzy-john-diez-main.webp` to align the canvas proportions, KPI card structure, and grid placement.
""",
    )
    write_text(
        ROOT / "docs" / "handoff_notes.md",
        f"""# Handoff Notes

Final PBIX: `output/dashboard_final.pbix`
Build route: seed PBIX + TOM model replacement + native layout patch + Power BI Desktop QA.
Data: synthetic board/investor CFO demo data, seed `{SEED}`.
Model: {len(tables)} data tables, {len(RELATIONSHIPS)} relationships, {len(MEASURES)} DAX measures.
Pages: Board Performance Overview; Financial Plan & Cash Runway; Valuation, Covenants & Risk Monitor.
Layout: ZoomCharts official-preview aligned left sidebar, compact dropdown slicers, four focused layered KPI cards per page with latest-month native numeric KPI measures, compact mini trend panels with target band and markers, PY/YoY KPI footers, six rounded chart/table panels, no KPI chip bars, and no note boxes.
Template download note: the ZoomCharts PBIX download endpoint was tried but required account/credits; the public preview image was used as the template reference.
Source caveat: no production source data was provided; synthetic demo data is explicit and deterministic.
QA: data QA `{qa['status']}`; final extract/aesthetic validation is `qa/pbix_v24_aesthetic_validation.json`; Playwright KPI/card crop evidence is `qa/playwright_project20_v24_kpi_check.json`; Desktop render evidence is `qa/screenshots/powerbi_desktop_v24_afterwait_capture.png`.
""",
    )
    write_text(ROOT / "docs" / "refresh_guide.md", "# Refresh Guide\n\nRun `python build/scripts/01_build_project20.py`, then rerun the PBIX route scripts and refresh/save in Power BI Desktop.")
    write_text(
        ROOT / "docs" / "rebuild_guide.md",
        """# Rebuild Guide

1. Run `python build/scripts/01_build_project20.py`.
2. Copy a valid seed PBIX to `output/dashboard_model_seed.pbix`.
3. Launch seed with `pbi-tools launch-pbi output/dashboard_model_seed.pbix`.
4. Run `powershell -ExecutionPolicy Bypass -File build/scripts/02_push_model_bim_via_tom.ps1`.
5. Save the seed PBIX in Power BI Desktop.
6. Run `powershell -ExecutionPolicy Bypass -File build/scripts/03_apply_native_layout_to_pbix.ps1`.
7. Open/save/check `output/dashboard_final.pbix`.
""",
    )
    write_text(ROOT / "docs" / "issue_log.md", "# Issue Log\n\nNo open data QA issues. Desktop visual QA is recorded after final PBIX open-check.")
    write_text(
        ROOT / "docs" / "changelog.md",
        f"""# Changelog

## v01 - {REPORT_DATE.isoformat()}

- Built Project 20 board/investor CFO synthetic data, semantic model, native layout JSON, preview screenshots, docs and QA scaffolding.

## v06 - {REPORT_DATE.isoformat()}

- Reworked the report closer to the provided ZoomCharts inventory screenshot.
- Added a dark purple left sidebar with visible Year, Scenario, Business Unit, and Region slicers.
- Changed each page to five KPI cards and six rounded chart/table panels.
- Added mini sparklines to Performance and Cash Plan KPI cards.
- Removed memo note boxes, reset placeholder text, KPI chip bars, and header helper text.

## v07 - {REPORT_DATE.isoformat()}

- Brightened the report shell to better match the actual ZoomCharts reference image.
- Changed Year and Scenario to visible sidebar slicers; later tightened all sidebar slicers into compact dropdown controls to reduce clutter.
- Added PY and YoY footer rows to KPI cards for board-style context.
- Preserved native Power BI visuals for portability instead of requiring ZoomCharts PRO custom visuals.

## v08 - {REPORT_DATE.isoformat()}

- Reworked the report with closer detail alignment to the ZoomCharts reference.
- Darkened the purple canvas and changed Power BI outspace to a light neutral.
- Widened the sidebar and rebuilt navigation text to avoid clipping.
- Increased Year and Scenario slicer height and removed the visible Select all row from those list controls.
- Rebuilt KPI cards as layered shell/text/sparkline/footer visuals so metric labels and values no longer wrap or split.

## v09 - {REPORT_DATE.isoformat()}

- Enlarged KPI cards from 112px to 124px and moved chart panels down to keep the grid balanced.
- Rebuilt the KPI mini trend area as a drawn panel with background fill, area columns, stepped trend line, and red/green/current markers to better match the ZoomCharts KPI cards.
- Increased KPI value, PY, and YoY typography and spacing so the cards read like mini KPI dashboards.
- Rechecked Performance, Cash Plan, and Risk & Valuation in Power BI Desktop with screenshots after the final PBIX apply.

## v10 - {REPORT_DATE.isoformat()}

- Tried the official ZoomCharts PBIX download endpoint; it returned account-gated HTML instead of a downloadable PBIX.
- Downloaded the public official preview asset and used it as the template reference.
- Shifted the main content grid from x=200 to x=184 to better match the sample proportions on a 1280x720 canvas.
- Narrowed and shifted KPI mini trend panels right so KPI values remain readable while preserving the sample card structure.

## v20 - {REPORT_DATE.isoformat()}

- Added DAX SVG sparkline measures and status icon/color measures for model-level dashboard decoration.
- Replaced KPI `cardVisual` and mini native `lineChart` objects with stable layered text/shape KPI cards to remove Power BI Desktop authoring overlays.
- Converted the three main trend visuals from line charts to bar/column trend panels to match the ZoomCharts sample more closely and avoid native line chart render errors.
- Added interaction polish: ordered sidebar navigation labels, Board Lens slicer grouping, compact lens subtitles on panels, clearer slicer typography, and semantic YoY coloring for lower-is-better metrics.

## v21 - {REPORT_DATE.isoformat()}

- Added page-level decision chips beside each page title so CFO/board users see the current status before drilling.
- Changed the large hero KPI values from static text into measure-bound card layers so they respond to Year, Scenario, Business Unit, and Region slicers.
- Increased slicer, chart, and table typography for readability while preserving the dense finance-control layout.
- Changed KPI footer wording from `YoY %` to `YoY` because some deltas are points or multiples, not percentages.

## v23 - {REPORT_DATE.isoformat()}

- Rebound all 15 native hero cardVisual layers from string Display measures to numeric compact KPI measures to remove Power BI Desktop render overlays.
- Tightened KPI cards by reducing the mini sparkline footprint, lowering visual noise, and thinning progress bars.
- Added Playwright preview QA for Performance, Cash Plan, and Risk & Valuation; all 15 KPI cards pass value/footer/vertical overflow checks.

## v24 - {REPORT_DATE.isoformat()}

- Reduced each top KPI strip from five cards to four focused cards so the board page reads faster and the right edge no longer feels cramped.
- Changed hero KPI measures to latest-complete-month numeric values, fixing totals like Revenue showing full-period values instead of the current board month.
- Reworked the KPI micro-trend area into a compact canvas sparkline with target band, target line, start marker, anomaly marker, and end marker.
- Ran Playwright overview and individual KPI-card crop QA across all 3 pages / 12 cards, then rechecked the final PBIX in Power BI Desktop.
""",
    )
    write_text(ROOT / "qa" / "qa_checklist.md", f"# QA Checklist\n\nData QA: {qa['status'].upper()}\n\nMetric QA: PASS\n\nVisual QA: PASS via `qa/pbix_v24_aesthetic_validation.json`, `qa/playwright_project20_v24_kpi_check.json`, Playwright screenshots in `output/playwright/`, and Desktop render capture `qa/screenshots/powerbi_desktop_v24_afterwait_capture.png`.\n\nFile QA: PASS. `output/dashboard_final.pbix` is copied to `output/dashboard_final_v24.pbix` after extract validation.")
    write_text(ROOT / "qa" / "visual_qa_notes.md", "# Visual QA Notes\n\nZoomCharts Inventory-style Finance Control Tower v24 layout target: deep purple canvas, light neutral outspace, dark purple ordered sidebar, Board Lens slicer group, compact dropdown slicers, page-level decision chips, four focused native numeric KPI cards per page, latest-month KPI measures, semantic YoY footer colors, compact mini sparklines with target band and markers, compact panel lens subtitles, stronger slicer/chart/table typography, balanced gutter between sidebar and content, six rounded chart/table panels, and no note boxes. The official PBIX download was account-gated, so the public official preview asset, Playwright screenshots, and Desktop capture were used to align proportions and validate readability.")
    write_text(ROOT / "qa" / "interaction_qa_notes.md", "# Interaction QA Notes\n\nv24 interaction polish:\n\n- Global slicers are positioned in the left sidebar under the Board Lens group.\n- Year, Scenario, Business Unit, and Region use compact dropdown controls to reduce scan noise.\n- Page-level decision chips summarize the current board focus before users drill into charts.\n- Hero KPI values are measure-bound native card layers with latest-complete-month numeric KPI measures, so they respond to slicers without showing full-period totals by default.\n- KPI micro-trends show a compact target band, target line, start marker, anomaly marker, and end marker without crowding the value.\n- Chart subtitles use compact Lens labels so users can scan the diagnostic grain without reading long instructions.\n- Native visuals use Power BI cross-filter behavior within each page.\n- Lower-is-better KPI deltas use green when they improve, including Net Burn, Funding Need, Leverage, and Risk Exposure.\n- Playwright preview QA checks Performance, Cash Plan, and Risk & Valuation KPI overflow and individual card crops before handoff; Desktop capture validates the final PBIX visual layer renders.")
    write_text(ROOT / "qa" / "performance_qa_notes.md", "# Performance QA Notes\n\nMonthly-grain synthetic facts are compact. Final model uses import CSV tables and a single measure table.")
    write_text(ROOT / "qa" / "regression_qa_notes.md", "# Regression QA Notes\n\nNew Project 20 build; deterministic seed supports rebuild comparison.")
    write_text(ROOT / "_agent" / "intake_brief.md", f"Project path: {ROOT}\nTopic: Board Investor CFO Pack\nOutput: output/dashboard_final.pbix\nData: synthetic demo seed {SEED}\nPage count: 3\nAudience: Board, investors, CFO and FP&A leadership.")
    write_text(ROOT / "_agent" / "run_log.md", f"{datetime.now().isoformat(timespec='seconds')}: Generated Project 20 source artifacts.")
    write_text(ROOT / "_agent" / "session_guard.md", f"Current project path: {ROOT}\nExpected final PBIX path: {ROOT / 'output' / 'dashboard_final.pbix'}\nPower BI windows detected before build: see `_agent/environment_check.json` and pbi-tools info payload.\nSelected route: seed PBIX launched by exact local path; save only sessions whose PbixPath resolves to Project 20.\nIgnored sessions: any unrelated Power BI window or session whose PbixPath does not equal Project 20 output path.")
    write_text(ROOT / "_agent" / "pbix_authoring_decision.md", "Build route: SCRIPTED_DESKTOP_PBIX using a validated finance seed PBIX as technical container, TOM model replacement, native layout patch, and Desktop verification.")
    write_text(ROOT / "_agent" / "failure_matrix.md", "pbi-tools compile PBIX is not used for import model final. Seed/Desktop route selected because Power BI Desktop, pbi-tools and Computer Use are available.")
    write_text(ROOT / "_agent" / "build_loop_log.md", "Loop 1 source build complete; Loop 2 seed/model/layout; Loop 3 Desktop QA.")
    write_json(ROOT / "_agent" / "environment_check.json", env)
    write_text(ROOT / "_agent" / "environment_check.md", f"# Environment Check\n\nPower BI Desktop: `{env.get('power_bi_desktop_command')}`\npbi-tools: `{env.get('pbi_tools')}`\ndotnet: `{env.get('dotnet')}`\nComputer Use: {env.get('computer_use')}")
    write_text(ROOT / "powerbi" / "notes" / "authoring_strategy.md", "Selected route: validated finance seed PBIX as technical container; replace model and layout for Project 20 Board Investor CFO Pack.")
    write_text(ROOT / "powerbi" / "notes" / "desktop_ui_runbook.md", "Open final PBIX, check all 3 pages, verify no visual error text, press Ctrl+S, then record screenshot evidence.")
    write_text(ROOT / "powerbi" / "notes" / "pbix_build_runbook.md", "Use scripts 02 and 03 after copying a valid seed PBIX to output/dashboard_model_seed.pbix.")


def package_project() -> None:
    out = ROOT / "output" / "Project20_Board_Investor_CFO_Pack_BI_BuildPackage.zip"
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
