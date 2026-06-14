from __future__ import annotations

from pathlib import Path
import textwrap

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle
import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
PREPARED_DIR = PROJECT_ROOT / "data" / "prepared"
OUTPUT_DIR = PROJECT_ROOT / "output"
SCREEN_DIR = OUTPUT_DIR / "screenshots" / "powerbi_mockup"
EXPORT_DIR = OUTPUT_DIR / "exports"


COLORS = {
    "bg": "#F4F6F8",
    "canvas": "#F7F8FA",
    "panel": "#FFFFFF",
    "border": "#DCE2EA",
    "text": "#1C2530",
    "muted": "#667085",
    "blue": "#2454A6",
    "teal": "#2A9D8F",
    "amber": "#D99A2B",
    "red": "#C43E3E",
    "purple": "#7C3AED",
    "slate": "#5C6B73",
    "green": "#2E7D32",
}

SCENARIO_COLORS = {
    "Actual": COLORS["slate"],
    "Base": COLORS["blue"],
    "Upside": COLORS["teal"],
    "Downside": COLORS["red"],
}

SCENARIO_LABEL = {
    "ACTUAL": "Actual",
    "BASE": "Base",
    "UPSIDE": "Upside",
    "DOWNSIDE": "Downside",
}


def read_csv(name: str) -> pd.DataFrame:
    return pd.read_csv(PREPARED_DIR / f"{name}.csv")


def usd_m(value: float) -> str:
    sign = "-" if value < 0 else ""
    return f"{sign}${abs(value) / 1_000_000:,.1f}M"


def compact_num(value: float) -> str:
    if abs(value) >= 1_000_000:
        return f"{value / 1_000_000:,.1f}M"
    if abs(value) >= 1_000:
        return f"{value / 1_000:,.1f}K"
    return f"{value:,.0f}"


def pct(value: float) -> str:
    return f"{value * 100:,.1f}%"


def make_canvas(title: str, subtitle: str, page_no: str):
    fig = plt.figure(figsize=(16, 9), dpi=140)
    fig.patch.set_facecolor(COLORS["canvas"])

    # Header
    header = fig.add_axes([0.025, 0.90, 0.95, 0.075])
    header.axis("off")
    header.add_patch(
        FancyBboxPatch((0, 0), 1, 1, boxstyle="round,pad=0.006,rounding_size=0.012", facecolor=COLORS["panel"], edgecolor=COLORS["border"], linewidth=1)
    )
    header.text(0.02, 0.62, title, fontsize=18, weight="bold", color=COLORS["text"], va="center")
    header.text(0.02, 0.22, subtitle, fontsize=9.5, color=COLORS["muted"], va="center")
    header.text(0.965, 0.82, page_no, fontsize=10, color=COLORS["muted"], ha="right", va="center")

    # Slicer strip
    slicers = [("Scenario", "Base"), ("Year", "2026-2027"), ("Region", "All"), ("Service", "All"), ("Currency", "USD")]
    x = 0.52
    for label, value in slicers:
        width = 0.08
        if label == "Year":
            width = 0.105
        elif label == "Scenario":
            width = 0.09
        elif label == "Currency":
            width = 0.075
        header.add_patch(
            FancyBboxPatch((x, 0.18), width, 0.56, boxstyle="round,pad=0.007,rounding_size=0.012", facecolor="#F9FAFB", edgecolor=COLORS["border"], linewidth=1)
        )
        header.text(x + 0.012, 0.52, label, fontsize=7.5, color=COLORS["muted"], va="center")
        header.text(x + 0.012, 0.30, value, fontsize=9, color=COLORS["text"], weight="bold", va="center")
        header.text(x + width - 0.015, 0.37, "v", fontsize=8, color=COLORS["muted"], ha="center", va="center")
        x += width + 0.008

    return fig


def panel(fig, rect, title: str, subtitle: str | None = None):
    ax = fig.add_axes(rect)
    ax.set_facecolor(COLORS["panel"])
    for spine in ax.spines.values():
        spine.set_edgecolor(COLORS["border"])
        spine.set_linewidth(1)
    ax.tick_params(colors=COLORS["muted"], labelsize=8)
    ax.set_title(title, loc="left", fontsize=10.5, color=COLORS["text"], pad=10, weight="bold")
    if subtitle:
        ax.text(0, 1.02, subtitle, transform=ax.transAxes, fontsize=7.5, color=COLORS["muted"], va="bottom")
    ax.grid(axis="y", color="#EDF1F5", linewidth=0.8)
    ax.set_axisbelow(True)
    return ax


def card(fig, rect, label: str, value: str, delta: str | None = None, accent: str = COLORS["blue"], note: str | None = None):
    ax = fig.add_axes(rect)
    ax.axis("off")
    ax.add_patch(
        FancyBboxPatch((0, 0), 1, 1, boxstyle="round,pad=0.007,rounding_size=0.02", facecolor=COLORS["panel"], edgecolor=COLORS["border"], linewidth=1.0)
    )
    ax.add_patch(Rectangle((0, 0), 0.018, 1, facecolor=accent, edgecolor=accent))
    ax.text(0.06, 0.73, label, fontsize=8.5, color=COLORS["muted"], va="center")
    ax.text(0.06, 0.43, value, fontsize=17, weight="bold", color=COLORS["text"], va="center")
    if delta:
        delta_color = COLORS["green"] if not delta.strip().startswith("-") else COLORS["red"]
        ax.text(0.06, 0.16, delta, fontsize=8.2, color=delta_color, va="center")
    if note:
        ax.text(0.94, 0.16, note, fontsize=7.5, color=COLORS["muted"], va="center", ha="right")
    return ax


def style_time_axis(ax):
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    ax.tick_params(axis="x", rotation=0)


def prepare():
    revenue = read_csv("fact_revenue_driver")
    cost = read_csv("fact_cost_driver")
    headcount = read_csv("fact_headcount_plan")
    opex = read_csv("fact_opex_driver")
    cash = read_csv("fact_cash_impact")
    accuracy = read_csv("fact_forecast_accuracy")
    service = read_csv("dim_service")
    region = read_csv("dim_region")
    segment = read_csv("dim_customer_segment")
    dept = read_csv("dim_department")

    for df in [revenue, cost, headcount, opex, cash, accuracy]:
        df["MonthStart"] = pd.to_datetime(df["MonthStart"])

    return revenue, cost, headcount, opex, cash, accuracy, service, region, segment, dept


def page_executive(revenue, cost, headcount, opex, cash, accuracy):
    fig = make_canvas(
        "Driver-Based Forecasting & Scenario Planning",
        "Executive overview | actuals through May 2026, forecast through Dec 2027",
        "01 / 05",
    )

    forecast_keys = ["BASE", "UPSIDE", "DOWNSIDE"]
    pnl = (
        revenue.groupby(["ScenarioKey"], as_index=False)["RevenueUSD"].sum()
        .merge(cost.groupby("ScenarioKey", as_index=False)["DirectCostUSD"].sum(), on="ScenarioKey")
        .merge(headcount.groupby("ScenarioKey", as_index=False)["PayrollCostUSD"].sum(), on="ScenarioKey")
        .merge(opex.groupby("ScenarioKey", as_index=False)["NonPayrollOpexUSD"].sum(), on="ScenarioKey")
    )
    pnl["GrossProfitUSD"] = pnl["RevenueUSD"] - pnl["DirectCostUSD"]
    pnl["EBITDAUSD"] = pnl["GrossProfitUSD"] - pnl["PayrollCostUSD"] - pnl["NonPayrollOpexUSD"]
    pnl["GrossMarginPct"] = pnl["GrossProfitUSD"] / pnl["RevenueUSD"]
    pnl["EBITDAMarginPct"] = pnl["EBITDAUSD"] / pnl["RevenueUSD"]
    base = pnl[pnl["ScenarioKey"] == "BASE"].iloc[0]
    upside = pnl[pnl["ScenarioKey"] == "UPSIDE"].iloc[0]
    downside = pnl[pnl["ScenarioKey"] == "DOWNSIDE"].iloc[0]
    base_cash = cash[cash["ScenarioKey"] == "BASE"].sort_values("MonthStart")["EndingCashUSD"].iloc[-1]

    card(fig, [0.025, 0.785, 0.18, 0.09], "Base Revenue", usd_m(base["RevenueUSD"]), f"+{usd_m(upside['RevenueUSD'] - base['RevenueUSD'])} upside", COLORS["blue"])
    card(fig, [0.215, 0.785, 0.18, 0.09], "Base EBITDA", usd_m(base["EBITDAUSD"]), f"{pct(base['EBITDAMarginPct'])} margin", COLORS["teal"])
    card(fig, [0.405, 0.785, 0.18, 0.09], "Gross Margin", pct(base["GrossMarginPct"]), f"{pct(base['GrossMarginPct'] - downside['GrossMarginPct'])} vs downside", COLORS["amber"])
    card(fig, [0.595, 0.785, 0.18, 0.09], "Ending Cash", usd_m(base_cash), "Dec 2027", COLORS["purple"])
    card(fig, [0.785, 0.785, 0.19, 0.09], "Forecast Accuracy", pct(accuracy["AbsolutePctError"].mean()), "MAPE historical", COLORS["red"])

    ax = panel(fig, [0.025, 0.435, 0.46, 0.31], "Revenue Forecast by Scenario")
    monthly_rev = revenue.groupby(["MonthStart", "ScenarioKey"], as_index=False)["RevenueUSD"].sum()
    for key in ["ACTUAL", "BASE", "UPSIDE", "DOWNSIDE"]:
        data = monthly_rev[monthly_rev["ScenarioKey"] == key]
        label = SCENARIO_LABEL[key]
        ax.plot(data["MonthStart"], data["RevenueUSD"] / 1_000_000, color=SCENARIO_COLORS[label], label=label, linewidth=2.2)
    ax.set_ylabel("USD M", color=COLORS["muted"], fontsize=8)
    style_time_axis(ax)
    ax.legend(loc="upper left", frameon=False, fontsize=8)

    ax = panel(fig, [0.515, 0.435, 0.46, 0.31], "Forecast P&L by Scenario")
    plot = pnl[pnl["ScenarioKey"].isin(forecast_keys)].copy()
    order = ["BASE", "UPSIDE", "DOWNSIDE"]
    plot = plot.set_index("ScenarioKey").loc[order].reset_index()
    labels = [SCENARIO_LABEL[x] for x in plot["ScenarioKey"]]
    x = np.arange(len(labels))
    ax.bar(x, plot["RevenueUSD"] / 1_000_000, color="#D9E4F5", label="Revenue")
    ax.bar(x, -plot["DirectCostUSD"] / 1_000_000, color="#F4C7C3", label="Direct Cost")
    ax.bar(x, -plot["PayrollCostUSD"] / 1_000_000, bottom=-plot["DirectCostUSD"] / 1_000_000, color="#F8DD9A", label="Payroll")
    ax.plot(x, plot["EBITDAUSD"] / 1_000_000, color=COLORS["teal"], marker="o", linewidth=2.5, label="EBITDA")
    ax.axhline(0, color=COLORS["border"], linewidth=1)
    ax.set_xticks(x, labels)
    ax.set_ylabel("USD M", color=COLORS["muted"], fontsize=8)
    ax.legend(loc="upper right", frameon=False, fontsize=8, ncols=2)

    ax = panel(fig, [0.025, 0.08, 0.46, 0.30], "Cash Impact")
    for key in forecast_keys:
        data = cash[cash["ScenarioKey"] == key]
        label = SCENARIO_LABEL[key]
        ax.plot(data["MonthStart"], data["EndingCashUSD"] / 1_000_000, label=label, color=SCENARIO_COLORS[label], linewidth=2.2)
    ax.set_ylabel("Ending cash USD M", color=COLORS["muted"], fontsize=8)
    style_time_axis(ax)
    ax.legend(loc="upper left", frameon=False, fontsize=8)

    ax = panel(fig, [0.515, 0.08, 0.46, 0.30], "Scenario Delta vs Base")
    delta = pd.DataFrame(
        {
            "Metric": ["Revenue", "Direct Cost", "EBITDA", "Ending Cash"],
            "Upside": [
                upside["RevenueUSD"] - base["RevenueUSD"],
                upside["DirectCostUSD"] - base["DirectCostUSD"],
                upside["EBITDAUSD"] - base["EBITDAUSD"],
                cash[cash["ScenarioKey"] == "UPSIDE"].sort_values("MonthStart")["EndingCashUSD"].iloc[-1] - base_cash,
            ],
            "Downside": [
                downside["RevenueUSD"] - base["RevenueUSD"],
                downside["DirectCostUSD"] - base["DirectCostUSD"],
                downside["EBITDAUSD"] - base["EBITDAUSD"],
                cash[cash["ScenarioKey"] == "DOWNSIDE"].sort_values("MonthStart")["EndingCashUSD"].iloc[-1] - base_cash,
            ],
        }
    )
    y = np.arange(len(delta))
    ax.barh(y + 0.18, delta["Upside"] / 1_000_000, height=0.32, color=COLORS["teal"], label="Upside")
    ax.barh(y - 0.18, delta["Downside"] / 1_000_000, height=0.32, color=COLORS["red"], label="Downside")
    ax.axvline(0, color=COLORS["border"], linewidth=1)
    ax.set_yticks(y, delta["Metric"])
    ax.set_xlabel("USD M", color=COLORS["muted"], fontsize=8)
    ax.legend(loc="lower right", frameon=False, fontsize=8)

    fig.savefig(SCREEN_DIR / "01_powerbi_executive_overview.png", bbox_inches="tight")
    plt.close(fig)


def page_revenue_cost(revenue, cost, service, segment):
    fig = make_canvas(
        "Revenue & Cost Driver Analysis",
        "Volume, rate, service mix and direct-cost levers by scenario",
        "02 / 05",
    )

    base_rev = revenue[revenue["ScenarioKey"] == "BASE"]
    base_cost = cost[cost["ScenarioKey"] == "BASE"]
    total_rev = base_rev["RevenueUSD"].sum()
    total_jobs = base_rev["VolumeJobs"].sum()
    direct_cost = base_cost["DirectCostUSD"].sum()
    gm = (total_rev - direct_cost) / total_rev

    card(fig, [0.025, 0.785, 0.18, 0.09], "Jobs", compact_num(total_jobs), "Base forecast", COLORS["blue"])
    card(fig, [0.215, 0.785, 0.18, 0.09], "Revenue / Job", f"${total_rev / total_jobs:,.0f}", "pricing driver", COLORS["teal"])
    card(fig, [0.405, 0.785, 0.18, 0.09], "Variable Cost / Job", f"${direct_cost / total_jobs:,.0f}", "cost driver", COLORS["amber"])
    card(fig, [0.595, 0.785, 0.18, 0.09], "Gross Margin", pct(gm), "portfolio mix", COLORS["purple"])
    card(fig, [0.785, 0.785, 0.19, 0.09], "Discounts", usd_m(base_rev["DiscountUSD"].sum()), "commercial lever", COLORS["red"])

    rev_service = base_rev.groupby("ServiceKey", as_index=False).agg(RevenueUSD=("RevenueUSD", "sum"), Jobs=("VolumeJobs", "sum")).merge(service[["ServiceKey", "ServiceLine"]], on="ServiceKey")
    cost_service = base_cost.groupby("ServiceKey", as_index=False).agg(DirectCostUSD=("DirectCostUSD", "sum"), CarrierCostUSD=("CarrierCostUSD", "sum"), HandlingCostUSD=("HandlingCostUSD", "sum"), FuelCostUSD=("FuelCostUSD", "sum"), CustomsCostUSD=("CustomsCostUSD", "sum")).merge(rev_service[["ServiceKey", "RevenueUSD", "Jobs", "ServiceLine"]], on="ServiceKey")
    cost_service["GrossMarginPct"] = (cost_service["RevenueUSD"] - cost_service["DirectCostUSD"]) / cost_service["RevenueUSD"]
    cost_service["RevenuePerJob"] = cost_service["RevenueUSD"] / cost_service["Jobs"]

    ax = panel(fig, [0.025, 0.44, 0.33, 0.31], "Revenue by Service")
    s = rev_service.sort_values("RevenueUSD")
    ax.barh(s["ServiceLine"], s["RevenueUSD"] / 1_000_000, color=COLORS["blue"])
    ax.set_xlabel("USD M", fontsize=8, color=COLORS["muted"])

    ax = panel(fig, [0.385, 0.44, 0.29, 0.31], "Jobs vs Revenue per Job")
    sizes = np.clip(cost_service["RevenueUSD"] / 18000, 80, 900)
    ax.scatter(cost_service["Jobs"], cost_service["RevenuePerJob"], s=sizes, color=COLORS["amber"], alpha=0.72, edgecolor="#B87F1F")
    for _, row in cost_service.iterrows():
        ax.annotate(row["ServiceLine"], (row["Jobs"], row["RevenuePerJob"]), fontsize=7, color=COLORS["text"])
    ax.set_xlabel("Jobs", fontsize=8, color=COLORS["muted"])
    ax.set_ylabel("USD / Job", fontsize=8, color=COLORS["muted"])

    ax = panel(fig, [0.705, 0.44, 0.27, 0.31], "Gross Margin by Service")
    ranked = cost_service.sort_values("GrossMarginPct")
    ax.barh(ranked["ServiceLine"], ranked["GrossMarginPct"] * 100, color=[COLORS["red"] if v < 0.17 else COLORS["teal"] for v in ranked["GrossMarginPct"]])
    ax.set_xlabel("%", fontsize=8, color=COLORS["muted"])
    ax.axvline(gm * 100, color=COLORS["blue"], linestyle="--", linewidth=1)

    ax = panel(fig, [0.025, 0.08, 0.46, 0.30], "Direct Cost Components by Service")
    components = cost_service.set_index("ServiceLine")[["CarrierCostUSD", "HandlingCostUSD", "FuelCostUSD", "CustomsCostUSD"]] / 1_000_000
    bottom = np.zeros(len(components))
    palette = [COLORS["blue"], COLORS["teal"], COLORS["amber"], COLORS["purple"]]
    for idx, col in enumerate(components.columns):
        ax.bar(components.index, components[col], bottom=bottom, color=palette[idx], label=col.replace("USD", ""))
        bottom += components[col].values
    ax.tick_params(axis="x", rotation=20)
    ax.set_ylabel("USD M", fontsize=8, color=COLORS["muted"])
    ax.legend(frameon=False, fontsize=7, ncols=2)

    ax = panel(fig, [0.515, 0.08, 0.46, 0.30], "Revenue Mix by Customer Segment")
    seg = base_rev.groupby("SegmentKey", as_index=False).agg(RevenueUSD=("RevenueUSD", "sum"), DiscountUSD=("DiscountUSD", "sum")).merge(segment[["SegmentKey", "CustomerSegment"]], on="SegmentKey")
    seg = seg.sort_values("RevenueUSD", ascending=False)
    ax.bar(seg["CustomerSegment"], seg["RevenueUSD"] / 1_000_000, color=COLORS["blue"], label="Revenue")
    ax2 = ax.twinx()
    ax2.plot(seg["CustomerSegment"], seg["DiscountUSD"] / seg["RevenueUSD"] * 100, color=COLORS["red"], marker="o", label="Discount %")
    ax.set_ylabel("Revenue USD M", fontsize=8, color=COLORS["muted"])
    ax2.set_ylabel("Discount %", fontsize=8, color=COLORS["muted"])
    ax.tick_params(axis="x", rotation=15)
    ax2.tick_params(colors=COLORS["muted"], labelsize=8)

    fig.savefig(SCREEN_DIR / "02_powerbi_revenue_cost_drivers.png", bbox_inches="tight")
    plt.close(fig)


def page_headcount(revenue, headcount, dept):
    fig = make_canvas(
        "Headcount & Capacity Plan",
        "Connect forecast volume to FTE, hiring, payroll and productivity",
        "03 / 05",
    )
    base_rev = revenue[revenue["ScenarioKey"] == "BASE"]
    base_hc = headcount[headcount["ScenarioKey"] == "BASE"]
    avg_fte = base_hc.groupby("MonthStart")["FTE"].sum().mean()
    payroll = base_hc["PayrollCostUSD"].sum()
    jobs = base_rev["VolumeJobs"].sum()
    hires = base_hc["NewHires"].sum()
    attrition = base_hc["Attrition"].sum()

    card(fig, [0.025, 0.785, 0.18, 0.09], "Average FTE", f"{avg_fte:,.0f}", "monthly avg", COLORS["blue"])
    card(fig, [0.215, 0.785, 0.18, 0.09], "Payroll Cost", usd_m(payroll), "forecast period", COLORS["teal"])
    card(fig, [0.405, 0.785, 0.18, 0.09], "Jobs / FTE", f"{jobs / avg_fte:,.0f}", "capacity", COLORS["amber"])
    card(fig, [0.595, 0.785, 0.18, 0.09], "New Hires", compact_num(hires), "forecast period", COLORS["purple"])
    card(fig, [0.785, 0.785, 0.19, 0.09], "Attrition", compact_num(attrition), "retention risk", COLORS["red"])

    ax = panel(fig, [0.025, 0.44, 0.46, 0.31], "FTE by Scenario")
    monthly = headcount[headcount["ScenarioKey"].isin(["BASE", "UPSIDE", "DOWNSIDE"])].groupby(["MonthStart", "ScenarioKey"], as_index=False)["FTE"].sum()
    for key in ["BASE", "UPSIDE", "DOWNSIDE"]:
        data = monthly[monthly["ScenarioKey"] == key]
        label = SCENARIO_LABEL[key]
        ax.plot(data["MonthStart"], data["FTE"], color=SCENARIO_COLORS[label], linewidth=2.2, label=label)
    style_time_axis(ax)
    ax.legend(frameon=False, fontsize=8)

    ax = panel(fig, [0.515, 0.44, 0.46, 0.31], "Payroll by Department")
    payroll_dept = base_hc.groupby("DepartmentKey", as_index=False)["PayrollCostUSD"].sum().merge(dept[["DepartmentKey", "Department"]], on="DepartmentKey").sort_values("PayrollCostUSD")
    ax.barh(payroll_dept["Department"], payroll_dept["PayrollCostUSD"] / 1_000_000, color=COLORS["blue"])
    ax.set_xlabel("USD M", fontsize=8, color=COLORS["muted"])

    ax = panel(fig, [0.025, 0.08, 0.46, 0.30], "Jobs per FTE")
    jobs_month = base_rev.groupby("MonthStart", as_index=False)["VolumeJobs"].sum()
    fte_month = base_hc.groupby("MonthStart", as_index=False)["FTE"].sum()
    prod = jobs_month.merge(fte_month, on="MonthStart")
    ax.plot(prod["MonthStart"], prod["VolumeJobs"] / prod["FTE"], color=COLORS["teal"], linewidth=2.4)
    ax.fill_between(prod["MonthStart"], prod["VolumeJobs"] / prod["FTE"], color=COLORS["teal"], alpha=0.10)
    style_time_axis(ax)

    ax = panel(fig, [0.515, 0.08, 0.46, 0.30], "Hiring vs Attrition")
    movement = base_hc.groupby("DepartmentKey", as_index=False)[["NewHires", "Attrition"]].sum().merge(dept[["DepartmentKey", "Department"]], on="DepartmentKey")
    movement = movement.sort_values("NewHires", ascending=False)
    x = np.arange(len(movement))
    ax.bar(x, movement["NewHires"], color=COLORS["teal"], label="New Hires")
    ax.bar(x, -movement["Attrition"], color=COLORS["red"], label="Attrition")
    ax.axhline(0, color=COLORS["border"], linewidth=1)
    ax.set_xticks(x, movement["Department"], rotation=15, ha="right")
    ax.legend(frameon=False, fontsize=8)

    fig.savefig(SCREEN_DIR / "03_powerbi_headcount_capacity.png", bbox_inches="tight")
    plt.close(fig)


def page_cash_accuracy(cash, accuracy, service):
    fig = make_canvas(
        "Cash Impact & Forecast Accuracy",
        "Liquidity, working capital and forecast discipline for planning reviews",
        "04 / 05",
    )
    base_cash = cash[cash["ScenarioKey"] == "BASE"]
    ending_cash = base_cash.sort_values("MonthStart")["EndingCashUSD"].iloc[-1]
    ocf = base_cash["OperatingCashFlowUSD"].sum()
    wc = base_cash["WorkingCapitalUSD"].mean()
    mape = accuracy["AbsolutePctError"].mean()
    bias = accuracy["ForecastBiasPct"].mean()

    card(fig, [0.025, 0.785, 0.18, 0.09], "Ending Cash", usd_m(ending_cash), "Dec 2027", COLORS["blue"])
    card(fig, [0.215, 0.785, 0.18, 0.09], "Operating Cash Flow", usd_m(ocf), "forecast total", COLORS["teal"])
    card(fig, [0.405, 0.785, 0.18, 0.09], "Working Capital", usd_m(wc), "monthly avg", COLORS["amber"])
    card(fig, [0.595, 0.785, 0.18, 0.09], "MAPE", pct(mape), "historical", COLORS["purple"])
    card(fig, [0.785, 0.785, 0.19, 0.09], "Forecast Bias", pct(bias), "signed error", COLORS["red"])

    ax = panel(fig, [0.025, 0.44, 0.46, 0.31], "Operating Cash Flow by Scenario")
    for key in ["BASE", "UPSIDE", "DOWNSIDE"]:
        data = cash[cash["ScenarioKey"] == key]
        label = SCENARIO_LABEL[key]
        ax.plot(data["MonthStart"], data["OperatingCashFlowUSD"] / 1_000_000, label=label, color=SCENARIO_COLORS[label], linewidth=2.2)
    style_time_axis(ax)
    ax.set_ylabel("USD M", fontsize=8, color=COLORS["muted"])
    ax.legend(frameon=False, fontsize=8)

    ax = panel(fig, [0.515, 0.44, 0.46, 0.31], "DSO / DPO by Scenario")
    c = cash[cash["ScenarioKey"].isin(["BASE", "UPSIDE", "DOWNSIDE"])].groupby("ScenarioKey", as_index=False)[["DSODays", "DPODays"]].mean()
    c = c.set_index("ScenarioKey").loc[["BASE", "UPSIDE", "DOWNSIDE"]].reset_index()
    x = np.arange(len(c))
    ax.bar(x - 0.18, c["DSODays"], width=0.34, color=COLORS["red"], label="DSO")
    ax.bar(x + 0.18, c["DPODays"], width=0.34, color=COLORS["teal"], label="DPO")
    ax.set_xticks(x, [SCENARIO_LABEL[k] for k in c["ScenarioKey"]])
    ax.set_ylabel("Days", fontsize=8, color=COLORS["muted"])
    ax.legend(frameon=False, fontsize=8)

    ax = panel(fig, [0.025, 0.08, 0.46, 0.30], "MAPE by Horizon")
    h = accuracy.groupby("ForecastHorizonMonths", as_index=False)["AbsolutePctError"].mean()
    ax.bar(h["ForecastHorizonMonths"].astype(str) + "M", h["AbsolutePctError"] * 100, color=COLORS["amber"])
    ax.set_ylabel("%", fontsize=8, color=COLORS["muted"])

    ax = panel(fig, [0.515, 0.08, 0.46, 0.30], "Forecast Accuracy by Service")
    svc = accuracy.groupby("ServiceKey", as_index=False).agg(MAPE=("AbsolutePctError", "mean"), Bias=("ForecastBiasPct", "mean")).merge(service[["ServiceKey", "ServiceLine"]], on="ServiceKey")
    svc = svc.sort_values("MAPE")
    ax.barh(svc["ServiceLine"], svc["MAPE"] * 100, color=COLORS["purple"], label="MAPE")
    ax.plot(svc["Bias"] * 100, svc["ServiceLine"], color=COLORS["red"], marker="o", linewidth=1.8, label="Bias")
    ax.set_xlabel("%", fontsize=8, color=COLORS["muted"])
    ax.legend(frameon=False, fontsize=8)

    fig.savefig(SCREEN_DIR / "04_powerbi_cash_accuracy.png", bbox_inches="tight")
    plt.close(fig)


def page_detail(revenue, cost, cash, accuracy, service, region, segment):
    fig = make_canvas(
        "Detail & Exceptions",
        "Planning review queue for low margin, high cash exposure and forecast-error outliers",
        "05 / 05",
    )

    base_rev = revenue[revenue["ScenarioKey"] == "BASE"]
    base_cost = cost[cost["ScenarioKey"] == "BASE"]
    detail = (
        base_rev.groupby(["MonthStart", "RegionKey", "ServiceKey", "SegmentKey"], as_index=False)
        .agg(RevenueUSD=("RevenueUSD", "sum"), Jobs=("VolumeJobs", "sum"), DiscountUSD=("DiscountUSD", "sum"))
        .merge(base_cost.groupby(["MonthStart", "RegionKey", "ServiceKey", "SegmentKey"], as_index=False)["DirectCostUSD"].sum(), on=["MonthStart", "RegionKey", "ServiceKey", "SegmentKey"])
        .merge(service[["ServiceKey", "ServiceLine"]], on="ServiceKey")
        .merge(region[["RegionKey", "Region"]], on="RegionKey")
        .merge(segment[["SegmentKey", "CustomerSegment"]], on="SegmentKey")
    )
    detail["GrossMarginPct"] = (detail["RevenueUSD"] - detail["DirectCostUSD"]) / detail["RevenueUSD"]
    low_margin = detail.sort_values("GrossMarginPct").head(8)
    high_wc = cash[cash["ScenarioKey"] == "DOWNSIDE"].sort_values("WorkingCapitalUSD", ascending=False).head(8)
    acc = accuracy.groupby(["RegionKey", "ServiceKey"], as_index=False).agg(MAPE=("AbsolutePctError", "mean"), Bias=("ForecastBiasPct", "mean")).merge(service[["ServiceKey", "ServiceLine"]], on="ServiceKey").merge(region[["RegionKey", "Region"]], on="RegionKey").sort_values("MAPE", ascending=False).head(8)

    card(fig, [0.025, 0.785, 0.18, 0.09], "Low Margin Rows", f"{len(detail[detail['GrossMarginPct'] < 0.16]):,.0f}", "GM < 16%", COLORS["red"])
    card(fig, [0.215, 0.785, 0.18, 0.09], "High MAPE Pairs", f"{len(acc):,.0f}", "top review list", COLORS["purple"])
    card(fig, [0.405, 0.785, 0.18, 0.09], "Downside WC Peak", usd_m(cash[cash["ScenarioKey"] == "DOWNSIDE"]["WorkingCapitalUSD"].max()), "cash risk", COLORS["amber"])
    card(fig, [0.595, 0.785, 0.18, 0.09], "Largest Service", detail.groupby("ServiceLine")["RevenueUSD"].sum().idxmax(), "by revenue", COLORS["blue"])
    card(fig, [0.785, 0.785, 0.19, 0.09], "Review Status", "Ready", "for FP&A", COLORS["teal"])

    def draw_table(ax, df, columns, formats):
        ax.axis("off")
        cell_text = []
        for _, row in df.iterrows():
            cells = []
            for col in columns:
                val = row[col]
                fmt = formats.get(col)
                if fmt == "usd":
                    cells.append(usd_m(val))
                elif fmt == "pct":
                    cells.append(pct(val))
                elif fmt == "date":
                    cells.append(pd.to_datetime(val).strftime("%Y-%m"))
                else:
                    cells.append(str(val))
            cell_text.append(cells)
        table = ax.table(cellText=cell_text, colLabels=columns, cellLoc="left", colLoc="left", loc="center")
        table.auto_set_font_size(False)
        table.set_fontsize(7.2)
        table.scale(1, 1.45)
        for (r, _c), cell in table.get_celld().items():
            cell.set_edgecolor("#E8EDF3")
            if r == 0:
                cell.set_facecolor("#EEF3FB")
                cell.set_text_props(weight="bold", color=COLORS["text"])
            else:
                cell.set_facecolor(COLORS["panel"])
                cell.set_text_props(color=COLORS["text"])

    ax = panel(fig, [0.025, 0.43, 0.46, 0.32], "Low Margin Review Queue")
    draw_table(
        ax,
        low_margin,
        ["MonthStart", "Region", "ServiceLine", "CustomerSegment", "RevenueUSD", "GrossMarginPct"],
        {"MonthStart": "date", "RevenueUSD": "usd", "GrossMarginPct": "pct"},
    )

    ax = panel(fig, [0.515, 0.43, 0.46, 0.32], "Forecast Error Outliers")
    draw_table(
        ax,
        acc,
        ["Region", "ServiceLine", "MAPE", "Bias"],
        {"MAPE": "pct", "Bias": "pct"},
    )

    ax = panel(fig, [0.025, 0.08, 0.46, 0.29], "Downside Working Capital Exposure")
    hw = high_wc[["MonthStart", "WorkingCapitalUSD", "OperatingCashFlowUSD", "EndingCashUSD"]].copy()
    draw_table(
        ax,
        hw,
        ["MonthStart", "WorkingCapitalUSD", "OperatingCashFlowUSD", "EndingCashUSD"],
        {"MonthStart": "date", "WorkingCapitalUSD": "usd", "OperatingCashFlowUSD": "usd", "EndingCashUSD": "usd"},
    )

    ax = panel(fig, [0.515, 0.08, 0.46, 0.29], "Exception Mix")
    exceptions = pd.DataFrame(
        {
            "Exception": ["Low margin", "High forecast error", "High WC exposure", "Discount pressure"],
            "Count": [
                len(detail[detail["GrossMarginPct"] < 0.16]),
                len(accuracy[accuracy["AbsolutePctError"] > 0.10]),
                len(cash[cash["WorkingCapitalUSD"] > cash["WorkingCapitalUSD"].quantile(0.85)]),
                len(detail[detail["DiscountUSD"] / detail["RevenueUSD"] > 0.05]),
            ],
        }
    )
    ax.barh(exceptions["Exception"], exceptions["Count"], color=[COLORS["red"], COLORS["purple"], COLORS["amber"], COLORS["blue"]])
    ax.set_xlabel("Rows", fontsize=8, color=COLORS["muted"])

    fig.savefig(SCREEN_DIR / "05_powerbi_detail_exceptions.png", bbox_inches="tight")
    plt.close(fig)


def write_html():
    images = [
        ("Executive Overview", "01_powerbi_executive_overview.png"),
        ("Revenue & Cost Drivers", "02_powerbi_revenue_cost_drivers.png"),
        ("Headcount & Capacity", "03_powerbi_headcount_capacity.png"),
        ("Cash & Forecast Accuracy", "04_powerbi_cash_accuracy.png"),
        ("Detail & Exceptions", "05_powerbi_detail_exceptions.png"),
    ]
    sections = []
    for title, filename in images:
        sections.append(
            f"""
      <section class="page">
        <h2>{title}</h2>
        <img src="../screenshots/powerbi_mockup/{filename}" alt="{title}">
      </section>"""
        )
    html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Project 02 - Driver-Based Forecasting Power BI Dashboard Mockup</title>
  <style>
    body {{ margin: 0; background: #f4f6f8; color: #1c2530; font-family: Segoe UI, Arial, sans-serif; }}
    header {{ background: #fff; border-bottom: 1px solid #dce2ea; padding: 24px 36px; position: sticky; top: 0; z-index: 1; }}
    h1 {{ margin: 0; font-size: 24px; }}
    p {{ color: #667085; margin: 8px 0 0; }}
    main {{ padding: 24px 36px 42px; }}
    .page {{ background: #fff; border: 1px solid #dce2ea; border-radius: 8px; padding: 18px; margin-bottom: 26px; }}
    h2 {{ margin: 0 0 12px; font-size: 18px; }}
    img {{ width: 100%; height: auto; display: block; border: 1px solid #e8edf3; }}
  </style>
</head>
<body>
  <header>
    <h1>Project 02 - Driver-Based Forecasting & Scenario Planning</h1>
    <p>Power BI-style dashboard mockup generated from the prepared model data.</p>
  </header>
  <main>
    {''.join(sections)}
  </main>
</body>
</html>
"""
    (EXPORT_DIR / "powerbi_dashboard_mockup.html").write_text(html, encoding="utf-8")


def main():
    SCREEN_DIR.mkdir(parents=True, exist_ok=True)
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)

    revenue, cost, headcount, opex, cash, accuracy, service, region, segment, dept = prepare()
    page_executive(revenue, cost, headcount, opex, cash, accuracy)
    page_revenue_cost(revenue, cost, service, segment)
    page_headcount(revenue, headcount, dept)
    page_cash_accuracy(cash, accuracy, service)
    page_detail(revenue, cost, cash, accuracy, service, region, segment)
    write_html()

    print(f"Wrote dashboard mockups to {SCREEN_DIR}")
    print(f"Wrote HTML preview to {EXPORT_DIR / 'powerbi_dashboard_mockup.html'}")


if __name__ == "__main__":
    main()
