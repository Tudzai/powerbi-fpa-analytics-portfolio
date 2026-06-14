from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.patches import FancyBboxPatch, Rectangle


def _palette(colors: dict[str, str]) -> dict[str, str]:
    base = {
        "ink": "#172033",
        "muted": "#667085",
        "grid": "#D9E2EC",
        "paper": "#F4F7FB",
        "card": "#FFFFFF",
        "blue": "#2F80ED",
        "teal": "#00A6A6",
        "green": "#16A34A",
        "amber": "#F59E0B",
        "red": "#E5484D",
        "violet": "#7C3AED",
        "navy": "#102033",
        "sky": "#D9ECFF",
        "mint": "#DFF7F3",
        "rose": "#FFE8EA",
    }
    base.update(colors or {})
    return base


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.strip() + "\n", encoding="utf-8")


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def _fmt_num(value: float) -> str:
    value = float(value)
    if abs(value) >= 1_000_000:
        return f"{value / 1_000_000:.1f}M"
    if abs(value) >= 1_000:
        return f"{value / 1_000:.1f}K"
    return f"{value:,.0f}"


def _fmt_money(value: float) -> str:
    value = float(value)
    if abs(value) >= 1_000_000:
        return f"${value / 1_000_000:.1f}M"
    if abs(value) >= 1_000:
        return f"${value / 1_000:.1f}K"
    return f"${value:,.0f}"


def _fmt_pct(value: float) -> str:
    return f"{float(value) * 100:.1f}%"


def _delta(current: float, previous: float, mode: str = "number", positive_good: bool = True) -> tuple[str, bool]:
    diff = float(current) - float(previous)
    if mode == "pct":
        text = f"{diff * 100:+.1f} pts"
    elif mode == "money":
        text = f"{_fmt_money(abs(diff))} {'up' if diff >= 0 else 'down'}"
    else:
        text = f"{diff:+,.0f}"
    good = diff >= 0 if positive_good else diff <= 0
    return text, good


def _new_fig(c: dict[str, str]) -> plt.Figure:
    plt.rcParams.update(
        {
            "font.family": "Segoe UI",
            "font.size": 10,
            "axes.titleweight": "bold",
            "axes.labelcolor": c["muted"],
            "xtick.color": c["muted"],
            "ytick.color": c["muted"],
            "figure.facecolor": c["paper"],
            "axes.facecolor": "none",
            "savefig.facecolor": c["paper"],
        }
    )
    return plt.figure(figsize=(16, 9), dpi=150, facecolor=c["paper"])


def _panel(
    fig: plt.Figure,
    x: float,
    y: float,
    w: float,
    h: float,
    c: dict[str, str],
    fc: str | None = None,
    ec: str | None = None,
    radius: float = 0.045,
    shadow: bool = True,
    z: int = 1,
) -> plt.Axes:
    ax = fig.add_axes([x, y, w, h], zorder=z)
    ax.set_axis_off()
    if shadow:
        ax.add_patch(
            FancyBboxPatch(
                (0.012, -0.014),
                0.976,
                0.992,
                boxstyle=f"round,pad=0.0,rounding_size={radius}",
                transform=ax.transAxes,
                facecolor="#0B1220",
                edgecolor="none",
                alpha=0.075,
                clip_on=False,
            )
        )
    ax.add_patch(
        FancyBboxPatch(
            (0, 0),
            1,
            1,
            boxstyle=f"round,pad=0.0,rounding_size={radius}",
            transform=ax.transAxes,
            facecolor=fc or c["card"],
            edgecolor=ec or c["grid"],
            linewidth=1.0,
            clip_on=False,
        )
    )
    return ax


def _chip(fig: plt.Figure, x: float, y: float, text: str, c: dict[str, str], active: bool = False) -> None:
    fc = c["navy"] if active else c["card"]
    tc = "#FFFFFF" if active else c["muted"]
    _panel(fig, x, y, 0.108, 0.036, c, fc=fc, ec=c["grid"], radius=0.20, shadow=False, z=5)
    fig.text(x + 0.014, y + 0.018, text, ha="left", va="center", fontsize=8.2, color=tc, weight="bold", zorder=8)


def _shell(fig: plt.Figure, title: str, subtitle: str, active: str, c: dict[str, str]) -> None:
    _panel(fig, 0.025, 0.04, 0.148, 0.92, c, fc=c["navy"], ec=c["navy"], radius=0.035, shadow=True, z=2)
    fig.text(0.052, 0.905, "P5", color="#FFFFFF", fontsize=24, weight="bold", zorder=7)
    fig.text(0.052, 0.872, "Retention\nCohorts", color="#DDE7F3", fontsize=10, linespacing=1.25, zorder=7)

    nav = [
        ("Overview", "Lifecycle"),
        ("Cohorts", "Retention"),
        ("LTV", "Value"),
        ("Churn", "Winback"),
    ]
    y = 0.745
    for label, small in nav:
        is_active = label == active
        if is_active:
            _panel(fig, 0.043, y - 0.011, 0.112, 0.066, c, fc="#1B3553", ec="#1B3553", radius=0.12, shadow=False, z=4)
            fig.add_artist(Rectangle((0.047, y + 0.003), 0.004, 0.038, transform=fig.transFigure, facecolor=c["teal"], edgecolor="none", zorder=9))
        fig.text(0.061, y + 0.027, label, color="#FFFFFF" if is_active else "#A9B7C9", fontsize=9.5, weight="bold", zorder=8)
        fig.text(0.061, y + 0.006, small, color="#9AACBF", fontsize=7.7, zorder=8)
        y -= 0.092

    fig.text(0.052, 0.145, "Source", color="#7F91A8", fontsize=8, weight="bold", zorder=8)
    fig.text(0.052, 0.116, "Fixed-seed portfolio\nlifecycle data", color="#C6D2E1", fontsize=8, linespacing=1.3, zorder=8)
    fig.text(0.052, 0.068, "Latest complete\nMay 2026", color="#C6D2E1", fontsize=8, linespacing=1.3, zorder=8)

    fig.text(0.205, 0.928, title, color=c["ink"], fontsize=23, weight="bold", zorder=8)
    fig.text(0.205, 0.895, subtitle, color=c["muted"], fontsize=10.5, zorder=8)
    _chip(fig, 0.650, 0.910, "Jan 2024-May 2026", c)
    _chip(fig, 0.764, 0.910, "All segments", c)
    _chip(fig, 0.878, 0.910, "Executive view", c, active=True)


def _style_axis(ax: plt.Axes, c: dict[str, str], grid_axis: str = "y") -> None:
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.tick_params(axis="both", labelsize=8.5, length=0)
    ax.grid(True, axis=grid_axis, color=c["grid"], linewidth=0.8, alpha=0.75)
    ax.set_axisbelow(True)


def _chart_panel(
    fig: plt.Figure,
    x: float,
    y: float,
    w: float,
    h: float,
    title: str,
    subtitle: str,
    c: dict[str, str],
    title_height: float = 0.075,
) -> plt.Axes:
    _panel(fig, x, y, w, h, c, radius=0.038, shadow=True, z=1)
    fig.text(x + 0.020, y + h - 0.034, title, color=c["ink"], fontsize=11.5, weight="bold", zorder=8)
    if subtitle:
        fig.text(x + 0.020, y + h - 0.058, subtitle, color=c["muted"], fontsize=8.4, zorder=8)
    ax = fig.add_axes([x + 0.030, y + 0.052, w - 0.060, h - title_height - 0.062], zorder=4)
    return ax


def _kpi_card(
    fig: plt.Figure,
    x: float,
    y: float,
    w: float,
    h: float,
    label: str,
    value: str,
    delta_text: str,
    delta_good: bool,
    caption: str,
    accent: str,
    c: dict[str, str],
    spark: pd.Series | np.ndarray | None = None,
) -> None:
    ax = _panel(fig, x, y, w, h, c, radius=0.050, shadow=True, z=3)
    ax.add_patch(Rectangle((0, 0.91), 1, 0.09, transform=ax.transAxes, facecolor=accent, edgecolor="none", alpha=0.95))
    fig.text(x + 0.015, y + h - 0.045, label, color=c["muted"], fontsize=8.6, weight="bold", zorder=9)
    fig.text(x + 0.015, y + 0.054, value, color=c["ink"], fontsize=19, weight="bold", zorder=9)
    fig.text(x + 0.015, y + 0.024, caption, color=c["muted"], fontsize=7.8, zorder=9)
    pill_color = c["green"] if delta_good else c["red"]
    fig.text(x + w - 0.018, y + h - 0.045, delta_text, ha="right", va="center", color=pill_color, fontsize=8.2, weight="bold", zorder=9)
    if spark is not None:
        vals = pd.Series(spark).dropna().tail(10).to_numpy(dtype=float)
        if len(vals) > 1 and np.nanmax(vals) != np.nanmin(vals):
            sax = fig.add_axes([x + w * 0.58, y + h * 0.20, w * 0.34, h * 0.34], zorder=9)
            sax.plot(vals, color=accent, linewidth=1.8)
            sax.fill_between(np.arange(len(vals)), vals, vals.min(), color=accent, alpha=0.10)
            sax.set_xticks([])
            sax.set_yticks([])
            for spine in sax.spines.values():
                spine.set_visible(False)
            sax.set_facecolor("none")


def _save(fig: plt.Figure, path: Path, c: dict[str, str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=150, facecolor=c["paper"], edgecolor="none")


def _latest_month_label(monthly: pd.DataFrame) -> str:
    if "MonthYear" in monthly:
        return str(monthly.iloc[-1]["MonthYear"])
    return pd.to_datetime(monthly.iloc[-1]["MonthStart"]).strftime("%b %Y")


def _page_lifecycle(prepared: dict[str, pd.DataFrame], c: dict[str, str]) -> plt.Figure:
    monthly = prepared["MonthlyKPIs"].copy()
    monthly["MonthTS"] = pd.to_datetime(monthly["MonthStart"])
    lifecycle = prepared["MonthlyLifecycleMix"].copy()
    lifecycle["MonthTS"] = pd.to_datetime(lifecycle["MonthStart"])
    latest = monthly.iloc[-1]
    prev = monthly.iloc[-2]

    fig = _new_fig(c)
    _shell(
        fig,
        "Lifecycle Overview",
        "Executive scan of acquisition, retained demand, repeat behavior, value, and churn pressure.",
        "Overview",
        c,
    )

    cards = [
        (
            "Active users",
            _fmt_num(latest["ActiveUsers"]),
            *_delta(latest["ActiveUsers"], prev["ActiveUsers"], "number", True),
            "latest complete month",
            c["blue"],
            monthly["ActiveUsers"],
        ),
        (
            "Returning users",
            _fmt_num(latest["ReturningUsers"]),
            *_delta(latest["ReturningUsers"], prev["ReturningUsers"], "number", True),
            "signup before current month",
            c["teal"],
            monthly["ReturningUsers"],
        ),
        (
            "Repeat purchase",
            _fmt_pct(latest["RepeatPurchaseRate"]),
            *_delta(latest["RepeatPurchaseRate"], prev["RepeatPurchaseRate"], "pct", True),
            "repeat purchasers / active customers",
            c["green"],
            monthly["RepeatPurchaseRate"],
        ),
        (
            "Revenue",
            _fmt_money(latest["NetRevenue"]),
            *_delta(latest["NetRevenue"], prev["NetRevenue"], "money", True),
            "completed orders",
            c["violet"],
            monthly["NetRevenue"],
        ),
        (
            "Churn signals",
            _fmt_num(latest["ChurnSignalCustomers"]),
            *_delta(latest["ChurnSignalCustomers"], prev["ChurnSignalCustomers"], "number", False),
            "90+ days since purchase",
            c["red"],
            monthly["ChurnSignalCustomers"],
        ),
    ]
    left = 0.205
    gap = 0.012
    card_w = (0.760 - gap * 4) / 5
    for idx, card_args in enumerate(cards):
        _kpi_card(fig, left + idx * (card_w + gap), 0.735, card_w, 0.125, *card_args[:-1], c, spark=card_args[-1])

    ax = _chart_panel(fig, 0.205, 0.405, 0.455, 0.285, "New vs returning users", "Lifecycle balance is now driven more by returning demand.", c)
    ax.plot(monthly["MonthTS"], monthly["NewUsers"], color=c["blue"], linewidth=2.4, label="New users")
    ax.plot(monthly["MonthTS"], monthly["ReturningUsers"], color=c["teal"], linewidth=2.4, label="Returning users")
    ax.fill_between(monthly["MonthTS"], monthly["ReturningUsers"], color=c["teal"], alpha=0.10)
    _style_axis(ax, c)
    ax.set_ylabel("Users", fontsize=8.5)
    ax.legend(frameon=False, loc="upper left", fontsize=8.5)

    ax = _chart_panel(fig, 0.682, 0.405, 0.283, 0.285, "Repeat rate and churn pressure", "Use this pair to separate healthy habit from latent churn risk.", c)
    ax.plot(monthly["MonthTS"], monthly["RepeatPurchaseRate"] * 100, color=c["green"], linewidth=2.5, label="Repeat purchase rate")
    ax.set_ylabel("Repeat rate %", fontsize=8.5, color=c["green"])
    _style_axis(ax, c)
    ax2 = ax.twinx()
    ax2.bar(monthly["MonthTS"], monthly["ChurnSignalCustomers"], width=18, color=c["rose"], edgecolor=c["red"], linewidth=0.7, alpha=0.70, label="Churn signals")
    ax2.set_ylabel("Signals", fontsize=8.5, color=c["red"])
    ax2.tick_params(axis="y", labelsize=8.5, colors=c["red"], length=0)
    for spine in ax2.spines.values():
        spine.set_visible(False)

    ax = _chart_panel(fig, 0.205, 0.105, 0.455, 0.250, "Lifecycle mix", "Monthly user base by lifecycle state.", c)
    pivot = lifecycle.pivot_table(index="MonthTS", columns="LifecycleType", values="Users", aggfunc="sum").fillna(0)
    preferred = [x for x in ["New Users", "Returning Users", "Dormant / Signal"] if x in pivot.columns]
    if not preferred:
        preferred = list(pivot.columns)
    stack_colors = [c["blue"], c["teal"], c["red"], c["amber"], c["violet"]][: len(preferred)]
    ax.stackplot(pivot.index, [pivot[col] for col in preferred], labels=preferred, colors=stack_colors, alpha=0.86)
    _style_axis(ax, c)
    ax.legend(frameon=False, ncol=3, loc="upper left", fontsize=8.2)

    notes = _panel(fig, 0.682, 0.105, 0.283, 0.250, c, radius=0.038, shadow=True, z=2)
    notes.add_patch(Rectangle((0.06, 0.76), 0.012, 0.14, transform=notes.transAxes, facecolor=c["red"], edgecolor="none"))
    notes.add_patch(Rectangle((0.06, 0.50), 0.012, 0.14, transform=notes.transAxes, facecolor=c["green"], edgecolor="none"))
    notes.add_patch(Rectangle((0.06, 0.24), 0.012, 0.14, transform=notes.transAxes, facecolor=c["blue"], edgecolor="none"))
    fig.text(0.707, 0.312, "Decision prompts", color=c["ink"], fontsize=11.5, weight="bold", zorder=9)
    prompts = [
        ("Protect", f"{_fmt_money(latest['ChurnRiskRevenue'])} at risk. Prioritize winback."),
        ("Amplify", f"{_fmt_pct(latest['M3Retention'])} M3 retention. Watch habit quality."),
        ("Compare", "Use segment quality before budget shifts."),
    ]
    y = 0.268
    for label, text in prompts:
        fig.text(0.707, y, label, color=c["ink"], fontsize=9.2, weight="bold", zorder=9)
        fig.text(0.765, y, text, color=c["muted"], fontsize=8.6, zorder=9)
        y -= 0.064
    fig.text(0.707, 0.124, f"Latest complete month: {_latest_month_label(monthly)}", color=c["muted"], fontsize=8.2, zorder=9)
    return fig


def _page_cohorts(prepared: dict[str, pd.DataFrame], c: dict[str, str]) -> plt.Figure:
    monthly = prepared["MonthlyKPIs"].copy()
    cohort = prepared["CohortRetention"].copy()
    cohort["CohortTS"] = pd.to_datetime(cohort["CohortMonth"])
    latest = monthly.iloc[-1]
    prev = monthly.iloc[-2]

    fig = _new_fig(c)
    _shell(
        fig,
        "Monthly Cohort Retention",
        "Cohort heatmap with retention horizons for first-purchase customer cohorts.",
        "Cohorts",
        c,
    )

    cards = [
        ("M1 retention", _fmt_pct(latest["M1Retention"]), *_delta(latest["M1Retention"], prev["M1Retention"], "pct", True), "first month after purchase", c["blue"], monthly["M1Retention"]),
        ("M3 retention", _fmt_pct(latest["M3Retention"]), *_delta(latest["M3Retention"], prev["M3Retention"], "pct", True), "quarterly habit marker", c["teal"], monthly["M3Retention"]),
        ("M6 retention", _fmt_pct(latest["M6Retention"]), *_delta(latest["M6Retention"], prev["M6Retention"], "pct", True), "longer-term quality", c["green"], monthly["M6Retention"]),
        ("Latest cohort", _fmt_num(cohort.loc[cohort["CohortTS"] == cohort["CohortTS"].max(), "CohortSize"].max()), "+0", True, "first-purchase users", c["amber"], None),
    ]
    left = 0.205
    gap = 0.015
    card_w = (0.760 - gap * 3) / 4
    for idx, card_args in enumerate(cards):
        _kpi_card(fig, left + idx * (card_w + gap), 0.735, card_w, 0.125, *card_args[:-1], c, spark=card_args[-1])

    ax = _chart_panel(fig, 0.205, 0.110, 0.555, 0.580, "Retention heatmap by cohort month", "Darker cells show stronger retention. Recent incomplete ages are intentionally blank.", c)
    heat_source = cohort[cohort["MonthsSinceCohort"].between(0, 12)].copy()
    heat = heat_source.pivot_table(index="CohortTS", columns="MonthsSinceCohort", values="RetentionRate", aggfunc="mean")
    heat = heat.sort_index().tail(15)
    cmap = LinearSegmentedColormap.from_list("retention", ["#F8FBFF", "#CFEFEA", c["teal"], "#116466"])
    matrix = heat.to_numpy(dtype=float)
    masked = np.ma.masked_invalid(matrix)
    ax.imshow(masked, aspect="auto", cmap=cmap, vmin=0, vmax=max(0.75, np.nanmax(matrix)))
    ax.set_xticks(range(len(heat.columns)))
    ax.set_xticklabels([f"M{int(x)}" for x in heat.columns], fontsize=8)
    ax.set_yticks(range(len(heat.index)))
    ax.set_yticklabels([pd.Timestamp(x).strftime("%b %Y") for x in heat.index], fontsize=8)
    ax.tick_params(length=0)
    for spine in ax.spines.values():
        spine.set_visible(False)
    for i in range(matrix.shape[0]):
        for j in range(matrix.shape[1]):
            val = matrix[i, j]
            if np.isfinite(val) and (j <= 6 or j in [9, 12]):
                ax.text(j, i, f"{val * 100:.0f}", ha="center", va="center", fontsize=6.9, color="#0B2D36" if val < 0.52 else "#FFFFFF")

    ax = _chart_panel(fig, 0.785, 0.405, 0.180, 0.285, "Selected cohort curves", "Mature cohorts with 6+ observed months.", c)
    mature = cohort.groupby(["CohortTS", "CohortMonthLabel"])["MonthsSinceCohort"].max().reset_index().sort_values("CohortTS")
    labels = mature.loc[mature["MonthsSinceCohort"] >= 6, "CohortMonthLabel"].tail(4).tolist()
    for idx, label in enumerate(labels):
        part = cohort[(cohort["CohortMonthLabel"] == label) & (cohort["MonthsSinceCohort"] <= 8)]
        ax.plot(part["MonthsSinceCohort"], part["RetentionRate"] * 100, linewidth=2.0, label=label, color=[c["blue"], c["teal"], c["amber"], c["violet"]][idx % 4])
    _style_axis(ax, c)
    ax.set_xlabel("Months since cohort", fontsize=8.5)
    ax.set_ylabel("Retention %", fontsize=8.5)
    ax.legend(frameon=False, fontsize=7.4, loc="upper right")

    panel = _panel(fig, 0.785, 0.110, 0.180, 0.250, c, radius=0.038, shadow=True, z=2)
    fig.text(0.805, 0.312, "Readout", color=c["ink"], fontsize=11.5, weight="bold", zorder=9)
    callouts = [
        ("Early habit", "M1 reveals onboarding quality."),
        ("Durability", "M3 and M6 separate sticky cohorts."),
        ("Budget lens", "Compare heatmap bands before scaling channels."),
    ]
    y = 0.262
    for label, text in callouts:
        fig.text(0.805, y, label, color=c["ink"], fontsize=8.8, weight="bold", zorder=9)
        fig.text(0.805, y - 0.026, text, color=c["muted"], fontsize=8.0, zorder=9)
        y -= 0.060
    return fig


def _segment_latest(seg: pd.DataFrame, segment_type: str) -> pd.DataFrame:
    part = seg[seg["SegmentType"] == segment_type].copy()
    if part.empty:
        return part
    latest_month = part["MonthStart"].max()
    return part[part["MonthStart"] == latest_month].copy()


def _page_ltv(prepared: dict[str, pd.DataFrame], c: dict[str, str]) -> plt.Figure:
    monthly = prepared["MonthlyKPIs"].copy()
    cohort = prepared["CohortRetention"].copy()
    cohort["CohortTS"] = pd.to_datetime(cohort["CohortMonth"])
    seg = prepared["SegmentMonthly"].copy()
    seg["MonthStart"] = pd.to_datetime(seg["MonthStart"])
    latest = monthly.iloc[-1]
    prev = monthly.iloc[-2]

    fig = _new_fig(c)
    _shell(
        fig,
        "LTV & Revenue Cohorts",
        "Value quality by cohort age, acquisition source, and customer segment.",
        "LTV",
        c,
    )

    revenue_per_customer = latest["NetRevenue"] / max(latest["ActiveCustomers"], 1)
    prev_revenue_per_customer = prev["NetRevenue"] / max(prev["ActiveCustomers"], 1)
    cards = [
        ("LTV to date", _fmt_money(latest["LTVToDate"]), *_delta(latest["LTVToDate"], prev["LTVToDate"], "money", True), "historical customer LTV", c["violet"], monthly["LTVToDate"]),
        ("Net revenue", _fmt_money(latest["NetRevenue"]), *_delta(latest["NetRevenue"], prev["NetRevenue"], "money", True), "latest complete month", c["blue"], monthly["NetRevenue"]),
        ("Revenue / customer", _fmt_money(revenue_per_customer), *_delta(revenue_per_customer, prev_revenue_per_customer, "money", True), "active customer basis", c["teal"], monthly["NetRevenue"] / monthly["ActiveCustomers"].clip(lower=1)),
        ("Repeat purchasers", _fmt_num(latest["RepeatPurchasers"]), *_delta(latest["RepeatPurchasers"], prev["RepeatPurchasers"], "number", True), "high-value behavior", c["green"], monthly["RepeatPurchasers"]),
    ]
    left = 0.205
    gap = 0.015
    card_w = (0.760 - gap * 3) / 4
    for idx, card_args in enumerate(cards):
        _kpi_card(fig, left + idx * (card_w + gap), 0.735, card_w, 0.125, *card_args[:-1], c, spark=card_args[-1])

    ax = _chart_panel(fig, 0.205, 0.405, 0.455, 0.285, "Cumulative LTV curves", "Mature cohorts show whether retention is translating into durable value.", c)
    mature = cohort.groupby(["CohortTS", "CohortMonthLabel"])["MonthsSinceCohort"].max().reset_index().sort_values("CohortTS")
    labels = mature.loc[mature["MonthsSinceCohort"] >= 8, "CohortMonthLabel"].tail(5).tolist()
    for idx, label in enumerate(labels):
        part = cohort[(cohort["CohortMonthLabel"] == label) & (cohort["MonthsSinceCohort"] <= 10)]
        ax.plot(part["MonthsSinceCohort"], part["CumulativeLTV"], linewidth=2.2, label=label, color=[c["blue"], c["teal"], c["green"], c["amber"], c["violet"]][idx % 5])
    _style_axis(ax, c)
    ax.set_xlabel("Months since cohort", fontsize=8.5)
    ax.set_ylabel("Cumulative LTV", fontsize=8.5)
    ax.legend(frameon=False, fontsize=7.4, loc="upper left")

    ax = _chart_panel(fig, 0.682, 0.405, 0.283, 0.285, "LTV by acquisition channel", "Latest complete month snapshot.", c)
    channel = _segment_latest(seg, "AcquisitionChannel")
    if channel.empty:
        channel = _segment_latest(seg, seg["SegmentType"].iloc[0])
    channel = channel.sort_values("LTVToDate", ascending=True).tail(6)
    ax.barh(channel["SegmentName"], channel["LTVToDate"], color=c["sky"], edgecolor=c["blue"], linewidth=1.0)
    _style_axis(ax, c, grid_axis="x")
    ax.set_xlabel("LTV to date", fontsize=8.5)

    ax = _chart_panel(fig, 0.205, 0.105, 0.350, 0.250, "Revenue by cohort age", "Most value accrues in the first repeat window.", c)
    age = cohort[cohort["MonthsSinceCohort"].between(0, 12)].groupby("MonthsSinceCohort", as_index=False)["NetRevenue"].sum()
    ax.bar(age["MonthsSinceCohort"], age["NetRevenue"] / 1000, color=c["mint"], edgecolor=c["teal"], linewidth=0.9)
    _style_axis(ax, c)
    ax.set_xlabel("Months since cohort", fontsize=8.5)
    ax.set_ylabel("Revenue, $K", fontsize=8.5)

    ax = _chart_panel(fig, 0.580, 0.105, 0.385, 0.250, "Segment value profile", "Retention, LTV, and revenue should be read together.", c)
    segment_type = "CustomerSegment" if "CustomerSegment" in set(seg["SegmentType"]) else seg["SegmentType"].iloc[0]
    segment = _segment_latest(seg, segment_type).sort_values("NetRevenue", ascending=False).head(4)
    x = np.arange(len(segment))
    width = 0.34
    ax.bar(x - width / 2, segment["NetRevenue"] / 1000, width=width, color=c["blue"], alpha=0.85, label="Revenue $K")
    ax2 = ax.twinx()
    ax2.plot(x + width / 2, segment["RepeatPurchaseRate"] * 100, color=c["green"], marker="o", linewidth=2.0, label="Repeat %")
    ax.set_xticks(x)
    ax.set_xticklabels(segment["SegmentName"], rotation=0, fontsize=8)
    _style_axis(ax, c)
    ax.set_ylabel("Revenue, $K", fontsize=8.5)
    ax2.set_ylabel("Repeat %", fontsize=8.5, color=c["green"])
    ax2.tick_params(axis="y", labelsize=8, colors=c["green"], length=0)
    for spine in ax2.spines.values():
        spine.set_visible(False)
    return fig


def _page_churn(prepared: dict[str, pd.DataFrame], c: dict[str, str]) -> plt.Figure:
    monthly = prepared["MonthlyKPIs"].copy()
    risk = prepared["ChurnRiskSnapshot"].copy()
    latest = monthly.iloc[-1]
    prev = monthly.iloc[-2]
    at_risk = risk[risk["ChurnSignal"] == True].copy()
    high_risk = risk[risk["RiskBand"].astype(str).str.contains("High", case=False, na=False)]

    fig = _new_fig(c)
    _shell(
        fig,
        "Churn Signal & Winback",
        "Prioritize customers with recency risk, revenue exposure, and clear next actions.",
        "Churn",
        c,
    )

    high_share = len(high_risk) / max(len(risk), 1)
    cards = [
        ("Churn signals", _fmt_num(latest["ChurnSignalCustomers"]), *_delta(latest["ChurnSignalCustomers"], prev["ChurnSignalCustomers"], "number", False), "90+ days since purchase", c["red"], monthly["ChurnSignalCustomers"]),
        ("Revenue at risk", _fmt_money(latest["ChurnRiskRevenue"]), *_delta(latest["ChurnRiskRevenue"], prev["ChurnRiskRevenue"], "money", False), "from signal customers", c["amber"], monthly["ChurnRiskRevenue"]),
        ("High risk share", _fmt_pct(high_share), "+0.0 pts", False, "latest customer snapshot", c["violet"], None),
        ("Winback queue", _fmt_num(len(at_risk)), "+0", False, "customers with action", c["blue"], None),
    ]
    left = 0.205
    gap = 0.015
    card_w = (0.760 - gap * 3) / 4
    for idx, card_args in enumerate(cards):
        _kpi_card(fig, left + idx * (card_w + gap), 0.735, card_w, 0.125, *card_args[:-1], c, spark=card_args[-1])

    ax = _chart_panel(fig, 0.205, 0.405, 0.330, 0.285, "Risk band distribution", "Count of customers by risk band.", c)
    order = ["Low", "Watch", "Medium", "High", "Critical"]
    counts = risk["RiskBand"].value_counts()
    labels = [x for x in order if x in counts.index] + [x for x in counts.index if x not in order]
    values = [counts[x] for x in labels]
    risk_color = {"Low": c["green"], "Watch": c["amber"], "Medium": c["amber"], "High": c["red"], "Critical": c["violet"]}
    bar_colors = [risk_color.get(str(label), c["muted"]) for label in labels]
    ax.bar(labels, values, color=bar_colors, alpha=0.88)
    _style_axis(ax, c)
    ax.set_ylabel("Customers", fontsize=8.5)
    ax.tick_params(axis="x", rotation=0)

    ax = _chart_panel(fig, 0.560, 0.405, 0.405, 0.285, "Recency vs lifetime value", "High-value dormant customers sit in the upper-right action zone.", c)
    sample = risk.sample(n=min(1100, len(risk)), random_state=20260611).copy()
    sample["DisplayDays"] = sample["DaysSinceLastPurchase"].clip(upper=365)
    color_map = {"Low": c["green"], "Watch": c["amber"], "Medium": c["amber"], "High": c["red"], "Critical": c["violet"]}
    colors = [color_map.get(str(x), c["muted"]) for x in sample["RiskBand"]]
    ax.scatter(sample["DisplayDays"], sample["LifetimeNetRevenue"], s=13, color=colors, alpha=0.45, edgecolors="none")
    ax.axvline(90, color=c["red"], linewidth=1.2, linestyle="--", alpha=0.80)
    _style_axis(ax, c)
    ax.set_xlabel("Days since last purchase, capped at 365", fontsize=8.5)
    ax.set_ylabel("Lifetime revenue", fontsize=8.5)

    ax = _chart_panel(fig, 0.205, 0.105, 0.330, 0.250, "Recommended action mix", "Operational sizing for winback playbooks.", c)
    action = risk["RecommendedAction"].value_counts().sort_values(ascending=True)
    ax.barh(action.index, action.values, color=c["sky"], edgecolor=c["blue"], linewidth=0.9)
    _style_axis(ax, c, grid_axis="x")
    ax.set_xlabel("Customers", fontsize=8.5)

    panel = _panel(fig, 0.560, 0.105, 0.405, 0.250, c, radius=0.038, shadow=True, z=2)
    fig.text(0.582, 0.312, "Top revenue-at-risk customers", color=c["ink"], fontsize=11.5, weight="bold", zorder=9)
    top = risk.sort_values(["RiskScore", "LifetimeNetRevenue"], ascending=[False, False]).head(6)
    headers = ["User", "Band", "Days", "Revenue", "Action"]
    xs = [0.582, 0.642, 0.702, 0.758, 0.825]
    for x, header in zip(xs, headers):
        fig.text(x, 0.274, header, color=c["muted"], fontsize=7.7, weight="bold", zorder=9)
    y = 0.248
    for _, row in top.iterrows():
        action_label = str(row["RecommendedAction"]).replace("Offer ", "").replace("Send ", "")
        fig.text(xs[0], y, str(row["UserID"]), color=c["ink"], fontsize=7.6, zorder=9)
        fig.text(xs[1], y, str(row["RiskBand"]), color=c["red"], fontsize=7.6, weight="bold", zorder=9)
        fig.text(xs[2], y, f"{int(row['DaysSinceLastPurchase'])}", color=c["ink"], fontsize=7.6, zorder=9)
        fig.text(xs[3], y, _fmt_money(row["LifetimeNetRevenue"]), color=c["ink"], fontsize=7.6, zorder=9)
        fig.text(xs[4], y, action_label[:24], color=c["muted"], fontsize=7.6, zorder=9)
        y -= 0.025
    panel.add_patch(Rectangle((0.045, 0.73), 0.91, 0.006, transform=panel.transAxes, facecolor=c["grid"], edgecolor="none"))
    return fig


def _make_contact_sheet(image_paths: list[Path], project_root: Path, c: dict[str, str]) -> None:
    fig = _new_fig(c)
    fig.text(0.055, 0.925, "Project 05 - Retention Cohort LTV Retention & Cohort Dashboard", color=c["ink"], fontsize=24, weight="bold")
    fig.text(0.055, 0.890, "Portfolio-ready visual refresh: executive summary, cohort heatmap, LTV, and churn winback views.", color=c["muted"], fontsize=10.5)
    positions = [
        (0.055, 0.500, 0.420, 0.320),
        (0.525, 0.500, 0.420, 0.320),
        (0.055, 0.100, 0.420, 0.320),
        (0.525, 0.100, 0.420, 0.320),
    ]
    titles = ["Lifecycle Overview", "Monthly Cohort Retention", "LTV & Revenue Cohorts", "Churn Signal & Winback"]
    for path, pos, title in zip(image_paths, positions, titles):
        x, y, w, h = pos
        _panel(fig, x - 0.006, y - 0.012, w + 0.012, h + 0.048, c, radius=0.028, shadow=True, z=1)
        fig.text(x, y + h + 0.018, title, color=c["ink"], fontsize=10.5, weight="bold", zorder=8)
        ax = fig.add_axes([x, y, w, h], zorder=5)
        ax.imshow(plt.imread(path))
        ax.set_axis_off()
    _save(fig, project_root / "output/dashboard_final.png", c)
    plt.close(fig)


def _write_html(project_root: Path, image_paths: list[Path], c: dict[str, str]) -> None:
    cards = []
    for idx, path in enumerate(image_paths, 1):
        rel = path.relative_to(project_root / "output").as_posix()
        cards.append(
            f"""
            <article class="page-card">
              <div class="page-meta">Page {idx:02d}</div>
              <img src="{rel}" alt="Dashboard page {idx}">
            </article>
            """
        )
    html = f"""
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Project 05 - Retention Cohort LTV Retention & Cohort Dashboard</title>
  <style>
    :root {{
      --paper: {c["paper"]};
      --ink: {c["ink"]};
      --muted: {c["muted"]};
      --card: {c["card"]};
      --grid: {c["grid"]};
      --blue: {c["blue"]};
      --navy: {c["navy"]};
    }}
    body {{
      margin: 0;
      background: var(--paper);
      color: var(--ink);
      font-family: "Segoe UI", Arial, sans-serif;
    }}
    header {{
      padding: 36px clamp(20px, 5vw, 70px) 18px;
      display: flex;
      gap: 24px;
      align-items: end;
      justify-content: space-between;
    }}
    h1 {{
      margin: 0 0 8px;
      font-size: clamp(28px, 4vw, 46px);
      line-height: 1;
      letter-spacing: 0;
    }}
    p {{
      margin: 0;
      color: var(--muted);
      max-width: 820px;
      line-height: 1.55;
    }}
    .badge {{
      background: var(--navy);
      color: white;
      border-radius: 8px;
      padding: 10px 14px;
      font-size: 13px;
      font-weight: 700;
      white-space: nowrap;
    }}
    main {{
      padding: 14px clamp(20px, 5vw, 70px) 56px;
      display: grid;
      grid-template-columns: 1fr;
      gap: 24px;
    }}
    .page-card {{
      background: var(--card);
      border: 1px solid var(--grid);
      border-radius: 8px;
      padding: 14px;
      box-shadow: 0 14px 34px rgba(15, 23, 42, 0.08);
    }}
    .page-meta {{
      color: var(--muted);
      font-size: 12px;
      font-weight: 700;
      margin: 0 0 10px;
      text-transform: uppercase;
    }}
    img {{
      display: block;
      width: 100%;
      height: auto;
      border-radius: 6px;
    }}
  </style>
</head>
<body>
  <header>
    <div>
      <h1>Retention & Cohort Dashboard</h1>
      <p>Visual refresh inspired by modern Power BI dashboard guidance: fewer stronger KPIs, clear reading order, consistent theme, and chart-led lifecycle diagnostics.</p>
    </div>
    <div class="badge">Project 05 - Retention Cohort LTV</div>
  </header>
  <main>
    {''.join(cards)}
  </main>
</body>
</html>
"""
    _write_text(project_root / "output/dashboard_preview.html", html)


def render_previews_v2(project_root: Path, prepared: dict[str, pd.DataFrame], colors: dict[str, str], report_date: date) -> None:
    c = _palette(colors)
    out_dir = project_root / "output/screenshots"
    out_dir.mkdir(parents=True, exist_ok=True)
    (project_root / "output/exports").mkdir(parents=True, exist_ok=True)

    builders = [
        ("page_01_lifecycle_overview.png", _page_lifecycle),
        ("page_02_monthly_cohort_retention.png", _page_cohorts),
        ("page_03_ltv_revenue_cohorts.png", _page_ltv),
        ("page_04_churn_signal_winback.png", _page_churn),
    ]
    image_paths: list[Path] = []
    pdf_path = project_root / "output/exports/dashboard_preview.pdf"
    with PdfPages(pdf_path) as pdf:
        for filename, builder in builders:
            fig = builder(prepared, c)
            path = out_dir / filename
            _save(fig, path, c)
            pdf.savefig(fig, facecolor=c["paper"], edgecolor="none")
            image_paths.append(path)
            plt.close(fig)

    _make_contact_sheet(image_paths, project_root, c)
    _write_html(project_root, image_paths, c)
    _write_json(
        project_root / "output/design_direction.json",
        {
            "version": "v02",
            "date": report_date.isoformat(),
            "style": "modern product analytics console",
            "principles": [
                "summary first",
                "five or fewer hero KPIs per page",
                "one-screen story",
                "consistent theme and visual hierarchy",
                "chart-led diagnostics with sparse annotation",
            ],
            "outputs": [str(path.relative_to(project_root)) for path in image_paths],
        },
    )


def build_design_docs(project_root: Path, report_date: date) -> None:
    _write_text(
        project_root / "docs/design_research.md",
        f"""
# Design Research Notes

Updated: {report_date.isoformat()}

## Sources Reviewed

- Microsoft Learn, `Tips for designing a great Power BI dashboard`: one-screen story, top-left priority, remove clutter, provide context for cards, and use consistent visual encodings.
- Microsoft Learn, `Create custom report themes in Power BI Desktop`: theme JSON should standardize data colors, structural colors, and visual styles.
- Tabular Editor, `Better KPI visualizations in Power BI reports`: limit KPI cards, add target/trend/context, and make each formatting choice help the reader decide faster.
- Vidi Corp, `54 Power BI KPI Dashboard Examples`: reviewed KPI dashboard template patterns for dense but polished management reporting inspiration.

## Applied Direction

- Replaced the plain chart grid preview with a product analytics console layout.
- Added a navy left rail, compact top filter chips, and a stronger visual hierarchy.
- Reduced top KPI count per page and added context, deltas, and sparklines where useful.
- Gave each page a single primary diagnostic visual plus supporting panels.
- Updated the Power BI theme palette and PBIR visual container defaults.
""",
    )
    _write_text(
        project_root / "docs/design_system.md",
        """
# Dashboard Design System

## Layout

- Canvas: 16:9 executive dashboard.
- Navigation: fixed left rail with page-level orientation.
- Reading order: title and filters, KPI strip, primary diagnostic chart, supporting drivers, action surface.
- Cards: 8px-or-less Power BI radius, compact titles, large values, short context.

## Palette

- Paper: #F4F7FB
- Card: #FFFFFF
- Ink: #172033
- Muted: #667085
- Grid: #D9E2EC
- Primary: #2F80ED
- Lifecycle teal: #00A6A6
- Good: #16A34A
- Warning: #F59E0B
- Risk: #E5484D
- Navigation: #102033

## Visual Rules

- Use no more than five hero KPIs on a page.
- Show context near every KPI: period, denominator, or movement.
- Prefer bars, lines, heatmaps, and scatterplots for lifecycle analysis.
- Use red only for churn/risk states.
- Keep annotations sparse and action-oriented.
""",
    )

    changelog_path = project_root / "docs/changelog.md"
    existing = changelog_path.read_text(encoding="utf-8") if changelog_path.exists() else "# Changelog\n"
    if "## v02" not in existing:
        addition = f"""

## v02 - {report_date.isoformat()}

- Researched Power BI dashboard design/template guidance and applied a modern product analytics console style.
- Rebuilt preview screenshots with sidebar navigation, compact filter chips, contextual KPI cards, improved heatmap styling, and clearer diagnostic panels.
- Updated Power BI theme colors and visual container styling for a cleaner portfolio presentation.
- Added design research and design system documentation.
"""
        changelog_path.write_text(existing.rstrip() + addition, encoding="utf-8")
