from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data" / "prepared"
OUT = ROOT / "output" / "screenshots"

NAVY = "#0f172a"
SLATE = "#334155"
MUTED = "#64748b"
GRID = "#e2e8f0"
BLUE = "#2563eb"
TEAL = "#0f766e"
GREEN = "#16a34a"
RED = "#dc2626"
AMBER = "#d97706"
VIOLET = "#7c3aed"
BG = "#f8fafc"


def money(value: float) -> str:
    abs_value = abs(value)
    sign = "-" if value < 0 else ""
    if abs_value >= 1_000_000:
        return f"{sign}${abs_value / 1_000_000:.1f}M"
    if abs_value >= 1_000:
        return f"{sign}${abs_value / 1_000:.0f}K"
    return f"{sign}${abs_value:.0f}"


def pct(value: float, digits: int = 1) -> str:
    return f"{value * 100:.{digits}f}%"


def style_ax(ax, title: str | None = None) -> None:
    ax.set_facecolor("white")
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.grid(axis="y", color=GRID, linewidth=1)
    ax.tick_params(colors=MUTED, labelsize=9)
    if title:
        ax.set_title(title, loc="left", fontsize=13, color=NAVY, fontweight="bold", pad=10)


def card(fig, x, y, w, h, label, value, delta=None, color=BLUE):
    ax = fig.add_axes([x, y, w, h])
    ax.set_facecolor("white")
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_color("#cbd5e1")
        spine.set_linewidth(1.0)
    ax.text(0.05, 0.72, label.upper(), transform=ax.transAxes, color=MUTED, fontsize=8.5, fontweight="bold")
    ax.text(0.05, 0.28, value, transform=ax.transAxes, color=NAVY, fontsize=19, fontweight="bold")
    if delta:
        ax.text(0.95, 0.32, delta, transform=ax.transAxes, ha="right", color=color, fontsize=10, fontweight="bold")
    ax.axvline(0.015, color=color, linewidth=4, ymin=0.16, ymax=0.84)
    return ax


def title(fig, main: str, subtitle: str) -> None:
    fig.text(0.035, 0.94, main, fontsize=24, fontweight="bold", color=NAVY)
    fig.text(0.036, 0.905, subtitle, fontsize=10.5, color=MUTED)


def load():
    monthly = pd.read_csv(DATA / "MonthlyKPIs.csv", parse_dates=["MonthStart"])
    movement = pd.read_csv(DATA / "FactMRRMovement.csv", parse_dates=["MonthStart"])
    cohort = pd.read_csv(DATA / "FactCohortRetention.csv", parse_dates=["CohortMonth", "ActivityMonth"])
    finance = pd.read_csv(DATA / "FactFinanceMonthly.csv", parse_dates=["MonthStart"])
    forecast = pd.read_csv(DATA / "FactForecast.csv", parse_dates=["MonthStart"])
    acquisition = pd.read_csv(DATA / "FactAcquisitionMonthly.csv", parse_dates=["MonthStart"])
    health = pd.read_csv(DATA / "FactAccountHealth.csv")
    return monthly, movement, cohort, finance, forecast, acquisition, health


def page_1(monthly, finance):
    latest = monthly.iloc[-1]
    prev = monthly.iloc[-2]
    latest_fin = finance.iloc[-1]

    fig = plt.figure(figsize=(16, 9), dpi=160, facecolor=BG)
    title(fig, "SaaS CFO Executive Overview", "Board cockpit for recurring revenue, retention, margin, and cash efficiency")

    cards = [
        ("ARR", money(latest.ARR), f"{(latest.ARR / prev.ARR - 1) * 100:+.1f}%", BLUE),
        ("Net New ARR", money(latest.NetNewARR), "MoM", GREEN if latest.NetNewARR >= 0 else RED),
        ("NRR", pct(latest.NRR), f"GRR {pct(latest.GRR)}", TEAL),
        ("Gross Margin", pct(latest.GrossMarginPct), "latest", GREEN),
        ("Logo Churn", pct(latest.LogoChurnRate), "monthly", RED if latest.LogoChurnRate > 0.03 else AMBER),
        ("Cash Runway", f"{latest_fin.CashBalance / max(latest_fin.NetBurn, 1):.1f} mo", money(latest_fin.NetBurn), VIOLET),
    ]
    for i, (label, value, delta, color) in enumerate(cards):
        card(fig, 0.035 + i * 0.155, 0.78, 0.142, 0.095, label, value, delta, color)

    ax1 = fig.add_axes([0.05, 0.43, 0.42, 0.28])
    style_ax(ax1, "ARR trend")
    ax1.plot(monthly.MonthStart, monthly.ARR / 1_000_000, color=BLUE, linewidth=3)
    ax1.fill_between(monthly.MonthStart, monthly.ARR / 1_000_000, color=BLUE, alpha=0.08)
    ax1.set_ylabel("$M", color=MUTED)

    ax2 = fig.add_axes([0.53, 0.43, 0.42, 0.28])
    style_ax(ax2, "Retention quality")
    ax2.plot(monthly.MonthStart, monthly.NRR * 100, color=TEAL, linewidth=2.7, label="NRR")
    ax2.plot(monthly.MonthStart, monthly.GRR * 100, color=AMBER, linewidth=2.3, label="GRR")
    ax2.axhline(100, color=GRID, linewidth=1.2)
    ax2.set_ylabel("%", color=MUTED)
    ax2.legend(loc="lower right", frameon=False, fontsize=9)

    ax3 = fig.add_axes([0.05, 0.12, 0.42, 0.23])
    style_ax(ax3, "ARR vs plan / forecast")
    ax3.plot(finance.MonthStart, finance.ActualARR / 1_000_000, color=BLUE, linewidth=2.7, label="Actual")
    ax3.plot(finance.MonthStart, finance.PlanARR / 1_000_000, color=MUTED, linewidth=2, linestyle="--", label="Plan")
    ax3.plot(finance.MonthStart, finance.ForecastARR / 1_000_000, color=VIOLET, linewidth=2, linestyle=":", label="Forecast")
    ax3.set_ylabel("$M", color=MUTED)
    ax3.legend(frameon=False, fontsize=9)

    ax4 = fig.add_axes([0.53, 0.12, 0.42, 0.23])
    style_ax(ax4, "Profitability and burn")
    ax4.bar(finance.MonthStart, finance.EBITDA / 1_000_000, width=18, color=np.where(finance.EBITDA >= 0, GREEN, RED), alpha=0.85)
    ax4.plot(finance.MonthStart, finance.NetBurn / 1_000_000, color=AMBER, linewidth=2.3, label="Net burn")
    ax4.axhline(0, color=GRID, linewidth=1.1)
    ax4.set_ylabel("$M", color=MUTED)
    ax4.legend(frameon=False, fontsize=9)

    fig.savefig(OUT / "page_01_executive_overview.png", bbox_inches="tight", facecolor=BG)
    plt.close(fig)


def page_2(monthly, movement, cohort):
    latest_month = monthly.MonthStart.max()
    latest_movement = movement[movement.MonthStart == latest_month].copy()
    latest_movement["ARRMovementM"] = latest_movement.ARRMovement / 1_000_000

    cohort_latest = (
        cohort[cohort.MonthsSinceCohort <= 11]
        .groupby(["CohortLabel", "MonthsSinceCohort"], as_index=False)["NetRetentionRate"]
        .mean()
    )
    pivot = cohort_latest.pivot(index="CohortLabel", columns="MonthsSinceCohort", values="NetRetentionRate").tail(10)

    fig = plt.figure(figsize=(16, 9), dpi=160, facecolor=BG)
    title(fig, "Revenue & Retention", "MRR movement, cohort economics, churn pressure, and expansion quality")

    cards = [
        ("Latest ARR", money(monthly.iloc[-1].ARR), "ending", BLUE),
        ("NRR", pct(monthly.iloc[-1].NRR), "net", TEAL),
        ("GRR", pct(monthly.iloc[-1].GRR), "gross", AMBER),
        ("Revenue Churn", pct(monthly.iloc[-1].RevenueChurnRate), "monthly", RED),
    ]
    for i, (label, value, delta, color) in enumerate(cards):
        card(fig, 0.05 + i * 0.225, 0.78, 0.2, 0.095, label, value, delta, color)

    ax1 = fig.add_axes([0.05, 0.43, 0.42, 0.28])
    style_ax(ax1, "Latest ARR movement")
    colors = [GREEN if x >= 0 else RED for x in latest_movement.ARRMovementM]
    ax1.bar(latest_movement.MovementType, latest_movement.ARRMovementM, color=colors)
    ax1.axhline(0, color=GRID)
    ax1.set_ylabel("$M", color=MUTED)
    ax1.tick_params(axis="x", rotation=20)

    ax2 = fig.add_axes([0.53, 0.43, 0.42, 0.28])
    style_ax(ax2, "NRR, GRR, and logo churn")
    ax2.plot(monthly.MonthStart, monthly.NRR * 100, color=TEAL, linewidth=2.7, label="NRR")
    ax2.plot(monthly.MonthStart, monthly.GRR * 100, color=AMBER, linewidth=2.4, label="GRR")
    ax2b = ax2.twinx()
    ax2b.plot(monthly.MonthStart, monthly.LogoChurnRate * 100, color=RED, linewidth=1.8, alpha=0.7, label="Logo churn")
    ax2b.tick_params(colors=MUTED, labelsize=9)
    ax2.set_ylabel("Retention %", color=MUTED)
    ax2b.set_ylabel("Churn %", color=MUTED)
    lines, labels = ax2.get_legend_handles_labels()
    lines2, labels2 = ax2b.get_legend_handles_labels()
    ax2.legend(lines + lines2, labels + labels2, frameon=False, fontsize=9, loc="lower right")

    ax3 = fig.add_axes([0.05, 0.10, 0.9, 0.25])
    ax3.set_facecolor("white")
    im = ax3.imshow(pivot.values * 100, aspect="auto", cmap="YlGnBu", vmin=85, vmax=112)
    ax3.set_title("Net retention cohort heatmap", loc="left", fontsize=13, color=NAVY, fontweight="bold", pad=10)
    ax3.set_yticks(range(len(pivot.index)))
    ax3.set_yticklabels(pivot.index, fontsize=8, color=MUTED)
    ax3.set_xticks(range(len(pivot.columns)))
    ax3.set_xticklabels([f"M+{int(c)}" for c in pivot.columns], fontsize=8, color=MUTED)
    for spine in ax3.spines.values():
        spine.set_visible(False)
    cbar = fig.colorbar(im, ax=ax3, fraction=0.018, pad=0.012)
    cbar.ax.tick_params(labelsize=8, colors=MUTED)
    cbar.outline.set_visible(False)

    fig.savefig(OUT / "page_02_revenue_retention.png", bbox_inches="tight", facecolor=BG)
    plt.close(fig)


def page_3(finance, forecast, acquisition, health):
    latest_fin = finance.iloc[-1]
    channel = (
        acquisition.groupby("ChannelID", as_index=False)
        .agg(NewARRBooked=("NewARRBooked", "sum"), SalesMarketingSpend=("SalesMarketingSpend", "sum"))
    )
    channel["CACPaybackProxy"] = channel.SalesMarketingSpend / (channel.NewARRBooked / 12 * 0.78)
    risk = health.groupby("RenewalRisk", as_index=False).agg(CurrentARR=("CurrentARR", "sum"))

    fig = plt.figure(figsize=(16, 9), dpi=160, facecolor=BG)
    title(fig, "Efficiency & Forecast", "Capital allocation, CAC payback, revenue quality, and forecast confidence")

    cards = [
        ("Cash Balance", money(latest_fin.CashBalance), "latest", VIOLET),
        ("Net Burn", money(latest_fin.NetBurn), "monthly", AMBER),
        ("EBITDA", money(latest_fin.EBITDA), "latest", GREEN if latest_fin.EBITDA >= 0 else RED),
        ("S&M Spend", money(latest_fin.SalesMarketingExpense), "monthly", BLUE),
    ]
    for i, (label, value, delta, color) in enumerate(cards):
        card(fig, 0.05 + i * 0.225, 0.78, 0.2, 0.095, label, value, delta, color)

    ax1 = fig.add_axes([0.05, 0.43, 0.42, 0.28])
    style_ax(ax1, "Forecast vs actual ARR")
    for scenario, color, style in [("Actual", BLUE, "-"), ("Forecast", VIOLET, ":"), ("Plan", MUTED, "--")]:
        subset = forecast[forecast.Scenario == scenario]
        ax1.plot(subset.MonthStart, subset.ARRValue / 1_000_000, color=color, linestyle=style, linewidth=2.5, label=scenario)
    ax1.set_ylabel("$M", color=MUTED)
    ax1.legend(frameon=False, fontsize=9)

    ax2 = fig.add_axes([0.53, 0.43, 0.42, 0.28])
    style_ax(ax2, "CAC payback proxy by channel")
    ax2.bar(channel.ChannelID, channel.CACPaybackProxy, color=[BLUE, TEAL, VIOLET, AMBER, GREEN][: len(channel)], alpha=0.9)
    ax2.axhline(12, color=RED, linewidth=1.6, linestyle="--", label="12 mo target")
    ax2.set_ylabel("Months", color=MUTED)
    ax2.legend(frameon=False, fontsize=9)

    ax3 = fig.add_axes([0.05, 0.11, 0.42, 0.23])
    style_ax(ax3, "Cash balance and burn")
    ax3.plot(finance.MonthStart, finance.CashBalance / 1_000_000, color=VIOLET, linewidth=2.7, label="Cash")
    ax3b = ax3.twinx()
    ax3b.bar(finance.MonthStart, finance.NetBurn / 1_000_000, width=18, color=AMBER, alpha=0.35, label="Burn")
    ax3.set_ylabel("Cash $M", color=MUTED)
    ax3b.set_ylabel("Burn $M", color=MUTED)
    ax3b.tick_params(colors=MUTED, labelsize=9)

    ax4 = fig.add_axes([0.53, 0.11, 0.42, 0.23])
    style_ax(ax4, "ARR at risk by health tier")
    order = ["Healthy", "Watch", "At Risk"]
    risk = risk.set_index("RenewalRisk").reindex(order).fillna(0).reset_index()
    ax4.barh(risk.RenewalRisk, risk.CurrentARR / 1_000_000, color=[GREEN, AMBER, RED])
    ax4.set_xlabel("$M", color=MUTED)

    fig.savefig(OUT / "page_03_efficiency_forecast.png", bbox_inches="tight", facecolor=BG)
    plt.close(fig)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    monthly, movement, cohort, finance, forecast, acquisition, health = load()
    page_1(monthly, finance)
    page_2(monthly, movement, cohort)
    page_3(finance, forecast, acquisition, health)
    print("rendered static dashboard previews")


if __name__ == "__main__":
    main()
