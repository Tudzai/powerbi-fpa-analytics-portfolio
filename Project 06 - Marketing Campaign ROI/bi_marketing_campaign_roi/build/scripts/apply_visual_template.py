from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import FancyBboxPatch, Rectangle


PROJECT = Path(__file__).resolve().parents[2]

COLORS = {
    "ink": "#14213D",
    "ink2": "#233047",
    "muted": "#6C7280",
    "paper": "#F4F7FB",
    "panel": "#FFFFFF",
    "line": "#D7DEE8",
    "blue": "#3267B1",
    "teal": "#0E7C7B",
    "green": "#2E8B57",
    "amber": "#F0B429",
    "coral": "#E3645A",
    "red": "#C43E3E",
    "purple": "#7A5CFA",
}

ACTION_COLORS = {
    "Scale": COLORS["green"],
    "Optimize": COLORS["amber"],
    "Review/Cut": COLORS["coral"],
}


def money_m(value: float) -> str:
    return f"${value / 1_000_000:.1f}M"


def money_k(value: float) -> str:
    return f"${value / 1_000:.0f}K"


def pct(value: float) -> str:
    return f"{value:.1%}"


def short_label(value: str, limit: int = 30) -> str:
    return value if len(value) <= limit else value[: limit - 1].rstrip() + "…"


def read_tables() -> dict[str, pd.DataFrame]:
    return {
        "fact": pd.read_csv(PROJECT / "data/prepared/fact_campaign_daily.csv", parse_dates=["date"]),
        "channel": pd.read_csv(PROJECT / "data/prepared/dim_channel.csv"),
        "campaign": pd.read_csv(PROJECT / "data/prepared/dim_campaign.csv"),
    }


def build_metrics(tables: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame | dict]:
    fact = tables["fact"].merge(
        tables["channel"][["channel_key", "channel", "target_roas", "target_cac"]],
        on="channel_key",
        how="left",
    )
    fact = fact.merge(
        tables["campaign"][["campaign_key", "campaign_name", "funnel_stage", "budget_tier"]],
        on="campaign_key",
        how="left",
    )

    totals = {
        "spend": float(fact["spend"].sum()),
        "revenue": float(fact["revenue"].sum()),
        "gross_profit": float(fact["gross_profit"].sum()),
        "clicks": float(fact["clicks"].sum()),
        "conversions": float(fact["conversions"].sum()),
        "new_customers": float(fact["new_customers"].sum()),
    }
    totals["roas"] = totals["revenue"] / totals["spend"]
    totals["roi"] = (totals["gross_profit"] - totals["spend"]) / totals["spend"]
    totals["cac"] = totals["spend"] / totals["new_customers"]
    totals["conversion_rate"] = totals["conversions"] / totals["clicks"]

    ch = (
        fact.groupby(["channel_key", "channel", "paid_organic"], as_index=False)
        .agg(
            spend=("spend", "sum"),
            revenue=("revenue", "sum"),
            gross_profit=("gross_profit", "sum"),
            clicks=("clicks", "sum"),
            conversions=("conversions", "sum"),
            new_customers=("new_customers", "sum"),
            target_roas=("target_roas", "mean"),
            target_cac=("target_cac", "mean"),
        )
        .sort_values("spend", ascending=False)
    )
    ch["roas"] = ch["revenue"] / ch["spend"]
    ch["marketing_roi"] = (ch["gross_profit"] - ch["spend"]) / ch["spend"]
    ch["cac"] = ch["spend"] / ch["new_customers"]
    ch["conversion_rate"] = ch["conversions"] / ch["clicks"]
    ch["spend_share"] = ch["spend"] / ch["spend"].sum()
    ch["roas_vs_target"] = ch["roas"] - ch["target_roas"]
    ch["cac_vs_target"] = ch["target_cac"] - ch["cac"]
    ch["action"] = np.select(
        [
            (ch["roas_vs_target"] >= 0) & (ch["cac_vs_target"] >= 0),
            (ch["spend_share"] >= 0.06) & ((ch["roas_vs_target"] < 0) | (ch["cac_vs_target"] < 0)),
        ],
        ["Scale", "Review/Cut"],
        default="Optimize",
    )

    cp = (
        fact.groupby(["campaign_key", "campaign_name", "channel", "paid_organic", "funnel_stage"], as_index=False)
        .agg(
            spend=("spend", "sum"),
            revenue=("revenue", "sum"),
            gross_profit=("gross_profit", "sum"),
            clicks=("clicks", "sum"),
            conversions=("conversions", "sum"),
            new_customers=("new_customers", "sum"),
        )
        .sort_values("revenue", ascending=False)
    )
    cp["roas"] = cp["revenue"] / cp["spend"]
    cp["marketing_roi"] = (cp["gross_profit"] - cp["spend"]) / cp["spend"]
    cp["cac"] = cp["spend"] / cp["new_customers"]
    cp["conversion_rate"] = cp["conversions"] / cp["clicks"]
    count = len(cp)
    cp["scale_score"] = (
        cp["roas"].rank(pct=True) * 0.40
        + cp["marketing_roi"].rank(pct=True) * 0.30
        + (1 - cp["cac"].rank(pct=True)) * 0.20
        + cp["gross_profit"].rank(pct=True) * 0.10
    ) * 100
    if count <= 1:
        cp["scale_score"] = np.nan
    cp["action"] = np.where(cp["scale_score"] >= 70, "Scale", np.where(cp["scale_score"] <= 35, "Review/Cut", "Optimize"))

    monthly = fact.groupby("month_key", as_index=False).agg(spend=("spend", "sum"), revenue=("revenue", "sum"))
    monthly_po = fact.groupby(["month_key", "paid_organic"], as_index=False).agg(revenue=("revenue", "sum"), spend=("spend", "sum"))
    paid_org = fact.groupby("paid_organic", as_index=False).agg(spend=("spend", "sum"), revenue=("revenue", "sum"), conversions=("conversions", "sum"))

    return {"totals": totals, "channel": ch, "campaign": cp, "monthly": monthly, "monthly_po": monthly_po, "paid_org": paid_org}


def setup_fig(title: str, subtitle: str, page_name: str) -> plt.Figure:
    fig = plt.figure(figsize=(16, 9), dpi=160)
    fig.patch.set_facecolor(COLORS["paper"])
    fig.patches.append(Rectangle((0, 0), 0.105, 1, transform=fig.transFigure, facecolor=COLORS["ink"], edgecolor="none", zorder=-10))
    fig.text(0.029, 0.942, "MROI", color="white", fontsize=19, fontweight="bold")
    fig.text(0.028, 0.911, "PROJECT 6", color="#AFC3D9", fontsize=8, fontweight="bold")
    nav = ["Overview", "Channel", "Ranking", "Actions"]
    for i, item in enumerate(nav):
        y = 0.80 - i * 0.075
        active = item.lower() in page_name.lower() or (item == "Overview" and "Executive" in page_name)
        if active:
            fig.patches.append(
                FancyBboxPatch((0.018, y - 0.019), 0.073, 0.043, boxstyle="round,pad=0.004,rounding_size=0.007", transform=fig.transFigure, facecolor="#31445F", edgecolor="none")
            )
        fig.text(0.032, y, item, color="white" if active else "#9FB4CC", fontsize=8.5, fontweight="bold" if active else "normal")
    fig.text(0.025, 0.055, "Paid vs Organic\nROI command", color="#B8C7D8", fontsize=8, linespacing=1.5)
    fig.text(0.135, 0.93, title, color=COLORS["ink"], fontsize=22, fontweight="bold")
    fig.text(0.136, 0.897, subtitle, color=COLORS["muted"], fontsize=10.5)
    return fig


def panel(
    fig: plt.Figure,
    x: float,
    y: float,
    w: float,
    h: float,
    title: str,
    subtitle: str = "",
    left_pad: float = 0.028,
    right_pad: float = 0.028,
) -> plt.Axes:
    fig.patches.append(
        FancyBboxPatch(
            (x, y),
            w,
            h,
            boxstyle="round,pad=0.006,rounding_size=0.012",
            transform=fig.transFigure,
            facecolor=COLORS["panel"],
            edgecolor=COLORS["line"],
            linewidth=0.8,
            zorder=-5,
        )
    )
    fig.text(x + 0.018, y + h - 0.047, title, color=COLORS["ink"], fontsize=11.5, fontweight="bold")
    if subtitle:
        fig.text(x + 0.018, y + h - 0.073, subtitle, color=COLORS["muted"], fontsize=8.5)
    top_pad = 0.088 if subtitle else 0.065
    ax = fig.add_axes([x + left_pad, y + 0.045, w - left_pad - right_pad, h - top_pad - 0.045])
    return ax


def metric_card(fig: plt.Figure, x: float, y: float, w: float, h: float, label: str, value: str, note: str, color: str) -> None:
    fig.patches.append(
        FancyBboxPatch(
            (x, y),
            w,
            h,
            boxstyle="round,pad=0.006,rounding_size=0.012",
            transform=fig.transFigure,
            facecolor="white",
            edgecolor=COLORS["line"],
            linewidth=0.8,
            zorder=-4,
        )
    )
    fig.patches.append(Rectangle((x, y), 0.006, h, transform=fig.transFigure, facecolor=color, edgecolor="none", zorder=-3))
    fig.text(x + 0.018, y + h - 0.030, label.upper(), color=COLORS["muted"], fontsize=7.3, fontweight="bold")
    fig.text(x + 0.018, y + 0.034, value, color=COLORS["ink"], fontsize=19, fontweight="bold")
    fig.text(x + 0.018, y + 0.015, note, color=color, fontsize=7.8, fontweight="bold")


def style_axis(ax: plt.Axes, grid_axis: str = "x") -> None:
    ax.set_facecolor("white")
    ax.spines[["top", "right", "left", "bottom"]].set_visible(False)
    ax.tick_params(colors=COLORS["muted"], labelsize=8, length=0)
    ax.grid(axis=grid_axis, color="#E7EDF5", linewidth=0.8)
    ax.set_axisbelow(True)


def save(fig: plt.Figure, page: int) -> None:
    out = PROJECT / f"output/screenshots/page_{page:02d}.png"
    fig.savefig(out, facecolor=fig.get_facecolor(), bbox_inches="tight", pad_inches=0.0)
    plt.close(fig)


def page_overview(metrics: dict[str, pd.DataFrame | dict]) -> None:
    totals = metrics["totals"]
    ch = metrics["channel"]
    monthly = metrics["monthly"]
    paid_org = metrics["paid_org"]
    fig = setup_fig("Marketing Campaign ROI", "Executive view: spend efficiency, revenue lift, and budget actions by channel", "Executive Overview")

    card_y, card_h, card_w = 0.785, 0.092, 0.128
    cards = [
        ("Spend", money_m(totals["spend"]), "portfolio cost base", COLORS["blue"]),
        ("Revenue", money_m(totals["revenue"]), "attributed outcome", COLORS["teal"]),
        ("ROAS", f"{totals['roas']:.2f}x", "revenue / spend", COLORS["green"]),
        ("CAC", f"${totals['cac']:.0f}", "new customer cost", COLORS["amber"]),
        ("Mktg ROI", pct(totals["roi"]), "profit after spend", COLORS["purple"]),
        ("CVR", pct(totals["conversion_rate"]), "click to conversion", COLORS["coral"]),
    ]
    for i, card in enumerate(cards):
        metric_card(fig, 0.135 + i * (card_w + 0.012), card_y, card_w, card_h, *card)

    ax = panel(fig, 0.135, 0.445, 0.455, 0.295, "Spend and revenue trend", "Monthly totals; same unit in $M")
    style_axis(ax)
    x = np.arange(len(monthly))
    ax.bar(x, monthly["spend"] / 1_000_000, color="#BFD7D5", width=0.68, label="Spend")
    ax.plot(x, monthly["revenue"] / 1_000_000, color=COLORS["blue"], linewidth=2.7, marker="o", markersize=3.8, label="Revenue")
    ax.set_xticks(x[::2], monthly["month_key"].iloc[::2], rotation=0)
    ax.set_ylabel("$M", color=COLORS["muted"], fontsize=8)
    ax.legend(frameon=False, loc="upper right", fontsize=8, ncol=2)

    ax = panel(fig, 0.615, 0.445, 0.33, 0.295, "Paid vs organic value", "Revenue, spend, and conversion contribution")
    style_axis(ax)
    y = np.arange(len(paid_org))
    ax.barh(y - 0.18, paid_org["revenue"] / 1_000_000, 0.34, color=COLORS["teal"], label="Revenue")
    ax.barh(y + 0.18, paid_org["spend"] / 1_000_000, 0.34, color=COLORS["coral"], label="Spend")
    ax.set_yticks(y, paid_org["paid_organic"])
    ax.set_xlabel("$M", color=COLORS["muted"], fontsize=8)
    ax.legend(frameon=False, loc="upper right", bbox_to_anchor=(1.0, 1.18), fontsize=8, ncol=2)

    ax = panel(fig, 0.135, 0.095, 0.50, 0.305, "Spend vs ROAS action map", "Bubble size = revenue; color = recommended budget action")
    style_axis(ax)
    colors = [ACTION_COLORS[a] for a in ch["action"]]
    sizes = ch["revenue"] / ch["revenue"].max() * 1700 + 160
    ax.scatter(ch["spend"] / 1000, ch["roas"], s=sizes, c=colors, alpha=0.82, edgecolor="white", linewidth=1.2)
    for _, row in ch.iterrows():
        if row["channel"] in {"Google Search", "Meta", "Organic Search", "Email", "Direct", "Referral Partners", "LinkedIn"}:
            ax.annotate(row["channel"], (row["spend"] / 1000, row["roas"]), xytext=(5, 5), textcoords="offset points", fontsize=7.5, color=COLORS["ink2"])
    ax.set_xlabel("Spend ($K)", color=COLORS["muted"], fontsize=8)
    ax.set_ylabel("ROAS", color=COLORS["muted"], fontsize=8)

    ax = panel(fig, 0.662, 0.095, 0.283, 0.305, "Budget callouts", "What to scale, optimize, and review")
    ax.axis("off")
    callouts = [
        ("Scale", ", ".join(ch.loc[ch["action"].eq("Scale"), "channel"].head(3)), ACTION_COLORS["Scale"]),
        ("Optimize", ", ".join(ch.loc[ch["action"].eq("Optimize"), "channel"].head(3)), ACTION_COLORS["Optimize"]),
        ("Review/Cut", ", ".join(ch.loc[ch["action"].eq("Review/Cut"), "channel"].head(4)), ACTION_COLORS["Review/Cut"]),
    ]
    for i, (label, body, color) in enumerate(callouts):
        y = 0.74 - i * 0.30
        ax.add_patch(FancyBboxPatch((0.00, y), 0.98, 0.205, boxstyle="round,pad=0.012,rounding_size=0.028", transform=ax.transAxes, facecolor="#F7FAFD", edgecolor="#E3EAF2"))
        ax.add_patch(Rectangle((0.02, y + 0.035), 0.018, 0.135, transform=ax.transAxes, facecolor=color, edgecolor="none"))
        ax.text(0.06, y + 0.122, label, transform=ax.transAxes, fontsize=10, fontweight="bold", color=COLORS["ink"])
        ax.text(0.06, y + 0.060, body or "No channel", transform=ax.transAxes, fontsize=8.2, color=COLORS["muted"], wrap=True)
    save(fig, 1)


def page_channel(metrics: dict[str, pd.DataFrame | dict]) -> None:
    ch = metrics["channel"].copy()
    fig = setup_fig("Channel ROI Deep Dive", "Compare each channel against ROAS and CAC targets before moving budget", "Channel")

    ax = panel(fig, 0.135, 0.535, 0.39, 0.34, "ROAS vs target", "Bar = actual ROAS; marker = target", left_pad=0.082)
    roas = ch.sort_values("roas")
    style_axis(ax)
    ax.barh(roas["channel"], roas["roas"], color=[ACTION_COLORS[a] for a in roas["action"]], alpha=0.92)
    ax.scatter(roas["target_roas"], roas["channel"], marker="|", s=300, color=COLORS["ink"], linewidths=2.2, label="Target")
    ax.set_xlabel("ROAS", color=COLORS["muted"], fontsize=8)
    ax.legend(frameon=False, loc="lower right", fontsize=8)

    ax = panel(fig, 0.555, 0.535, 0.39, 0.34, "CAC vs target", "Lower CAC is better; marker = target", left_pad=0.082)
    cac = ch.sort_values("cac", ascending=False)
    style_axis(ax)
    ax.barh(cac["channel"], cac["cac"], color=np.where(cac["cac"] <= cac["target_cac"], COLORS["green"], COLORS["coral"]), alpha=0.92)
    ax.scatter(cac["target_cac"], cac["channel"], marker="|", s=300, color=COLORS["ink"], linewidths=2.2, label="Target")
    ax.set_xlabel("CAC ($)", color=COLORS["muted"], fontsize=8)
    ax.legend(frameon=False, loc="lower right", fontsize=8)

    ax = panel(fig, 0.135, 0.095, 0.50, 0.36, "Efficiency quadrant", "X = ROAS gap; Y = CAC gap; top-right is best")
    style_axis(ax)
    ax.axvline(0, color=COLORS["ink"], linewidth=0.9)
    ax.axhline(0, color=COLORS["ink"], linewidth=0.9)
    sizes = ch["spend_share"] * 5200 + 180
    ax.scatter(ch["roas_vs_target"], ch["cac_vs_target"], s=sizes, c=[ACTION_COLORS[a] for a in ch["action"]], alpha=0.82, edgecolor="white", linewidth=1.2)
    label_offsets = {
        "Direct": (6, 4),
        "Email": (6, 4),
        "Referral Partners": (6, 8),
        "Organic Search": (6, -10),
        "Google Search": (6, -12),
        "Meta": (6, 5),
        "LinkedIn": (6, -2),
        "Programmatic Display": (6, -10),
    }
    for _, row in ch.iterrows():
        if row["channel"] not in label_offsets:
            continue
        ax.annotate(row["channel"], (row["roas_vs_target"], row["cac_vs_target"]), xytext=label_offsets[row["channel"]], textcoords="offset points", fontsize=7.3, color=COLORS["ink2"])
    ax.set_xlabel("ROAS gap vs target", color=COLORS["muted"], fontsize=8)
    ax.set_ylabel("CAC gap vs target", color=COLORS["muted"], fontsize=8)

    ax = panel(fig, 0.662, 0.095, 0.283, 0.36, "Channel scorecard", "Spend share, ROAS, CAC, and action")
    ax.axis("off")
    table = ch.sort_values("spend", ascending=False)[["channel", "spend_share", "roas", "cac", "action"]].head(8).copy()
    table["spend_share"] = table["spend_share"].map(pct)
    table["roas"] = table["roas"].map(lambda v: f"{v:.2f}x")
    table["cac"] = table["cac"].map(lambda v: f"${v:.0f}")
    y0 = 0.88
    headers = ["Channel", "Share", "ROAS", "CAC", "Action"]
    xs = [0.00, 0.43, 0.58, 0.71, 0.84]
    for x, h in zip(xs, headers):
        ax.text(x, y0, h, transform=ax.transAxes, fontsize=7.2, color=COLORS["muted"], fontweight="bold")
    for i, row in table.iterrows():
        yy = y0 - 0.085 * (list(table.index).index(i) + 1)
        ax.plot([0, 1], [yy + 0.043, yy + 0.043], transform=ax.transAxes, color="#EDF2F7", linewidth=0.8)
        ax.text(xs[0], yy, row["channel"][:22], transform=ax.transAxes, fontsize=7.5, color=COLORS["ink2"])
        ax.text(xs[1], yy, row["spend_share"], transform=ax.transAxes, fontsize=7.5, color=COLORS["ink2"])
        ax.text(xs[2], yy, row["roas"], transform=ax.transAxes, fontsize=7.5, color=COLORS["ink2"])
        ax.text(xs[3], yy, row["cac"], transform=ax.transAxes, fontsize=7.5, color=COLORS["ink2"])
        ax.text(xs[4], yy, row["action"], transform=ax.transAxes, fontsize=7.3, color=ACTION_COLORS[row["action"]], fontweight="bold")
    save(fig, 2)


def page_campaign(metrics: dict[str, pd.DataFrame | dict]) -> None:
    cp = metrics["campaign"].copy()
    fig = setup_fig("Campaign Ranking", "Top and bottom campaigns ranked by scale score, ROAS, ROI, CAC, and profit", "Ranking")

    ax = panel(fig, 0.135, 0.515, 0.39, 0.36, "Scale candidates", "Highest composite scale score", left_pad=0.145)
    top = cp.sort_values("scale_score", ascending=True).tail(10).copy()
    top["campaign_short"] = top["campaign_name"].map(lambda v: short_label(v, 35))
    style_axis(ax)
    ax.barh(top["campaign_short"], top["scale_score"], color=COLORS["green"], alpha=0.92)
    ax.set_xlim(0, 100)
    ax.set_xlabel("Scale score", color=COLORS["muted"], fontsize=8)

    ax = panel(fig, 0.555, 0.515, 0.39, 0.36, "Review / cut candidates", "Lowest composite scale score", left_pad=0.145)
    bottom = cp.sort_values("scale_score", ascending=False).tail(10).copy()
    bottom["campaign_short"] = bottom["campaign_name"].map(lambda v: short_label(v, 35))
    style_axis(ax)
    ax.barh(bottom["campaign_short"], bottom["scale_score"], color=COLORS["coral"], alpha=0.92)
    ax.set_xlim(0, 100)
    ax.set_xlabel("Scale score", color=COLORS["muted"], fontsize=8)

    ax = panel(fig, 0.135, 0.095, 0.81, 0.34, "Campaign decision table", "Use as the monthly budget meeting handoff")
    ax.axis("off")
    table = pd.concat([cp.sort_values("scale_score", ascending=False).head(6), cp.sort_values("scale_score").head(4)])
    table = table[["campaign_name", "channel", "paid_organic", "spend", "revenue", "roas", "cac", "scale_score", "action"]].copy()
    table["spend"] = table["spend"].map(money_k)
    table["revenue"] = table["revenue"].map(money_k)
    table["roas"] = table["roas"].map(lambda v: f"{v:.2f}x")
    table["cac"] = table["cac"].map(lambda v: f"${v:.0f}")
    table["scale_score"] = table["scale_score"].map(lambda v: f"{v:.0f}")
    headers = ["Campaign", "Channel", "Type", "Spend", "Revenue", "ROAS", "CAC", "Score", "Action"]
    xs = [0.00, 0.31, 0.45, 0.55, 0.64, 0.75, 0.82, 0.88, 0.94]
    y0 = 0.90
    for x, h in zip(xs, headers):
        ax.text(x, y0, h, transform=ax.transAxes, fontsize=7.4, color=COLORS["muted"], fontweight="bold")
    for r, (_, row) in enumerate(table.iterrows()):
        yy = y0 - 0.078 * (r + 1)
        ax.plot([0, 1], [yy + 0.037, yy + 0.037], transform=ax.transAxes, color="#EDF2F7", linewidth=0.8)
        vals = [short_label(row["campaign_name"], 40), row["channel"], row["paid_organic"], row["spend"], row["revenue"], row["roas"], row["cac"], row["scale_score"], row["action"]]
        for x, val in zip(xs, vals):
            color = ACTION_COLORS[row["action"]] if val == row["action"] else COLORS["ink2"]
            weight = "bold" if val == row["action"] else "normal"
            ax.text(x, yy, val, transform=ax.transAxes, fontsize=7.3, color=color, fontweight=weight)
    save(fig, 3)


def page_actions(metrics: dict[str, pd.DataFrame | dict]) -> None:
    ch = metrics["channel"].copy()
    fig = setup_fig("Exceptions and Actions", "Budget move list: protect efficient demand, fix waste, and rebalance high-spend misses", "Actions")

    ax = panel(fig, 0.135, 0.455, 0.49, 0.42, "Budget action matrix", "X = ROAS gap; Y = CAC gap; bubble = spend share")
    style_axis(ax)
    ax.axvline(0, color=COLORS["ink"], linewidth=0.9)
    ax.axhline(0, color=COLORS["ink"], linewidth=0.9)
    sizes = ch["spend_share"] * 6200 + 180
    ax.scatter(ch["roas_vs_target"], ch["cac_vs_target"], s=sizes, c=[ACTION_COLORS[a] for a in ch["action"]], alpha=0.82, edgecolor="white", linewidth=1.2)
    label_offsets = {
        "Direct": (6, 4),
        "Email": (6, 4),
        "Referral Partners": (6, 8),
        "Organic Search": (6, -10),
        "Google Search": (6, -12),
        "Meta": (6, 5),
        "LinkedIn": (6, -2),
        "Programmatic Display": (6, -10),
    }
    for _, row in ch.iterrows():
        if row["channel"] not in label_offsets:
            continue
        ax.annotate(row["channel"], (row["roas_vs_target"], row["cac_vs_target"]), xytext=label_offsets[row["channel"]], textcoords="offset points", fontsize=7.3, color=COLORS["ink2"])
    ax.set_xlabel("ROAS gap vs target", color=COLORS["muted"], fontsize=8)
    ax.set_ylabel("CAC gap vs target", color=COLORS["muted"], fontsize=8)

    ax = panel(fig, 0.655, 0.455, 0.29, 0.42, "Next-month budget moves", "Ranked by spend share and target miss")
    ax.axis("off")
    review = ch[ch["action"].eq("Review/Cut")].sort_values("spend_share", ascending=False).head(4)
    scale = ch[ch["action"].eq("Scale")].sort_values("roas_vs_target", ascending=False).head(4)
    blocks = [("Reduce / fix", review, COLORS["coral"]), ("Scale carefully", scale, COLORS["green"])]
    y = 0.82
    for title, data, color in blocks:
        ax.text(0.00, y, title, transform=ax.transAxes, color=color, fontsize=10, fontweight="bold")
        y -= 0.09
        for _, row in data.iterrows():
            ax.add_patch(FancyBboxPatch((0, y - 0.008), 0.96, 0.062, boxstyle="round,pad=0.008,rounding_size=0.02", transform=ax.transAxes, facecolor="#F7FAFD", edgecolor="#E3EAF2"))
            ax.text(0.03, y + 0.016, row["channel"], transform=ax.transAxes, fontsize=8.3, color=COLORS["ink2"], fontweight="bold")
            ax.text(0.63, y + 0.016, f"{pct(row['spend_share'])} spend", transform=ax.transAxes, fontsize=7.4, color=COLORS["muted"])
            y -= 0.075
        y -= 0.055

    ax = panel(fig, 0.135, 0.095, 0.81, 0.29, "Operating view", "Channel-level exception details for the weekly growth review")
    ax.axis("off")
    table = ch.sort_values(["action", "spend_share"], ascending=[True, False])[["channel", "paid_organic", "spend_share", "roas_vs_target", "cac_vs_target", "roas", "cac", "action"]].copy()
    table["spend_share"] = table["spend_share"].map(pct)
    table["roas_vs_target"] = table["roas_vs_target"].map(lambda v: f"{v:+.2f}")
    table["cac_vs_target"] = table["cac_vs_target"].map(lambda v: f"{v:+.0f}")
    table["roas"] = table["roas"].map(lambda v: f"{v:.2f}x")
    table["cac"] = table["cac"].map(lambda v: f"${v:.0f}")
    headers = ["Channel", "Type", "Spend Share", "ROAS Gap", "CAC Gap", "ROAS", "CAC", "Action"]
    xs = [0.00, 0.22, 0.34, 0.49, 0.60, 0.70, 0.79, 0.88]
    y0 = 0.88
    for x, h in zip(xs, headers):
        ax.text(x, y0, h, transform=ax.transAxes, fontsize=7.4, color=COLORS["muted"], fontweight="bold")
    for r, (_, row) in enumerate(table.iterrows()):
        yy = y0 - 0.072 * (r + 1)
        ax.plot([0, 1], [yy + 0.034, yy + 0.034], transform=ax.transAxes, color="#EDF2F7", linewidth=0.8)
        vals = [row["channel"], row["paid_organic"], row["spend_share"], row["roas_vs_target"], row["cac_vs_target"], row["roas"], row["cac"], row["action"]]
        for x, val in zip(xs, vals):
            color = ACTION_COLORS[row["action"]] if val == row["action"] else COLORS["ink2"]
            weight = "bold" if val == row["action"] else "normal"
            ax.text(x, yy, val, transform=ax.transAxes, fontsize=7.3, color=color, fontweight=weight)
    save(fig, 4)


def write_theme_and_specs(metrics: dict[str, pd.DataFrame | dict]) -> None:
    research = {
        "template_direction": "Executive ROI command center",
        "applied_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "research_sources": [
            {
                "source": "Microsoft Learn - Tips for designing a great Power BI dashboard",
                "url": "https://learn.microsoft.com/en-us/power-bi/create-reports/service-dashboards-design-tips",
                "applied": "Most important information top-left, one-screen story, clean/uncluttered cards, consistent colors and simple comparisons.",
            },
            {
                "source": "Microsoft Learn - Create custom report themes in Power BI Desktop",
                "url": "https://learn.microsoft.com/en-us/power-bi/create-reports/report-themes-create-custom",
                "applied": "Theme JSON includes data colors, status colors, structural colors, and primary text classes.",
            },
            {
                "source": "Supermetrics - Power BI marketing dashboard examples",
                "url": "https://supermetrics.com/blog/power-bi-marketing-dashboard-examples",
                "applied": "Marketing campaign layout covers spend, revenue, conversions, paid vs organic performance, campaign ranking, and executive CMO summary.",
            },
            {
                "source": "Coupler.io - Power BI templates",
                "url": "https://www.coupler.io/dashboard-examples/power-bi-templates",
                "applied": "Budget optimization layout highlights cost spikes, diminishing returns, performance improvements, and channel/campaign/time filters.",
            },
            {
                "source": "Windsor.ai - Power BI templates",
                "url": "https://windsor.ai/powerbi-templates/",
                "applied": "Operational marketing dashboards should focus on one subject, choose charts by message, add context, and clearly outline actions.",
            },
        ],
    }
    (PROJECT / "build/config").mkdir(parents=True, exist_ok=True)
    (PROJECT / "docs").mkdir(parents=True, exist_ok=True)
    (PROJECT / "qa").mkdir(parents=True, exist_ok=True)
    (PROJECT / "output").mkdir(parents=True, exist_ok=True)
    (PROJECT / "output/screenshots").mkdir(parents=True, exist_ok=True)

    theme = {
        "name": "Marketing ROI Command Center",
        "dataColors": [
            COLORS["blue"],
            COLORS["teal"],
            COLORS["green"],
            COLORS["amber"],
            COLORS["coral"],
            COLORS["purple"],
            "#7B8794",
            "#A3B18A",
        ],
        "good": COLORS["green"],
        "neutral": COLORS["amber"],
        "bad": COLORS["coral"],
        "maximum": COLORS["blue"],
        "center": COLORS["amber"],
        "minimum": "#DCE6F2",
        "null": "#B8C2CC",
        "background": COLORS["paper"],
        "foreground": COLORS["ink"],
        "firstLevelElements": COLORS["ink"],
        "secondLevelElements": COLORS["muted"],
        "thirdLevelElements": "#E7EDF5",
        "fourthLevelElements": "#B8C2CC",
        "secondaryBackground": "#E9EEF6",
        "tableAccent": COLORS["teal"],
        "textClasses": {
            "callout": {"fontSize": 34, "fontFace": "Segoe UI Semibold", "color": COLORS["ink"]},
            "title": {"fontSize": 12, "fontFace": "Segoe UI Semibold", "color": COLORS["ink"]},
            "header": {"fontSize": 12, "fontFace": "Segoe UI Semibold", "color": COLORS["ink"]},
            "label": {"fontSize": 10, "fontFace": "Segoe UI", "color": COLORS["ink2"]},
        },
    }
    page_map = {
        "template_direction": research["template_direction"],
        "canvas": {"size": "16:9", "background": COLORS["paper"], "left_rail": COLORS["ink"], "panel_radius": 8},
        "layout_rules": [
            "Left rail navigation across all pages.",
            "Top KPI strip on executive page.",
            "White chart panels on cool neutral canvas.",
            "Green/amber/coral action states for scale, optimize, and review/cut.",
            "Charts above detail tables; action tables at the bottom.",
        ],
        "pages": [
            {"page": 1, "name": "Executive Overview", "hero": "Portfolio ROI, paid vs organic value, and spend-vs-ROAS action map.", "primary_question": "Which channels are worth scaling and which are burning budget?"},
            {"page": 2, "name": "Channel ROI", "hero": "ROAS/CAC target gaps and channel scorecard.", "primary_question": "Which channels beat target efficiency and which need intervention?"},
            {"page": 3, "name": "Campaign Ranking", "hero": "Scale candidates and review/cut candidates.", "primary_question": "Which campaigns should get more or less budget next month?"},
            {"page": 4, "name": "Exceptions and Actions", "hero": "Budget action matrix and operating table.", "primary_question": "What should the growth team do after reading the dashboard?"},
        ],
    }
    visual_map = {
        "template_direction": research["template_direction"],
        "visuals": [
            {"page": "Executive Overview", "visual": "KPI strip", "type": "Cards", "fields": ["Spend", "Revenue", "ROAS", "CAC", "Marketing ROI", "Conversion Rate"], "placement": "top row", "style": "left accent stripe, compact context label"},
            {"page": "Executive Overview", "visual": "Spend and revenue trend", "type": "Line and clustered column", "fields": ["DimMonth[month_key]", "Spend", "Revenue"], "placement": "middle left", "style": "spend muted bar, revenue blue line"},
            {"page": "Executive Overview", "visual": "Paid vs organic value", "type": "Clustered bar", "fields": ["DimChannel[paid_organic]", "Spend", "Revenue"], "placement": "middle right", "style": "teal revenue, coral spend"},
            {"page": "Executive Overview", "visual": "Spend vs ROAS action map", "type": "Scatter", "fields": ["Spend", "ROAS", "Revenue", "DimChannel[channel]", "Action"], "placement": "bottom left", "style": "bubble size by revenue, color by action"},
            {"page": "Executive Overview", "visual": "Budget callouts", "type": "Card group", "fields": ["Action", "DimChannel[channel]"], "placement": "bottom right", "style": "Scale/Optimize/Review action badges"},
            {"page": "Channel ROI", "visual": "ROAS vs target", "type": "Horizontal bar with target marker", "fields": ["DimChannel[channel]", "ROAS", "Target ROAS"], "placement": "top left", "style": "action color bars"},
            {"page": "Channel ROI", "visual": "CAC vs target", "type": "Horizontal bar with target marker", "fields": ["DimChannel[channel]", "CAC", "Target CAC"], "placement": "top right", "style": "green when below target, coral when above target"},
            {"page": "Channel ROI", "visual": "Efficiency quadrant", "type": "Scatter", "fields": ["ROAS vs Target", "CAC vs Target", "Spend Share", "DimChannel[channel]"], "placement": "bottom left", "style": "target crosshair and spend-share bubbles"},
            {"page": "Channel ROI", "visual": "Channel scorecard", "type": "Table", "fields": ["DimChannel[channel]", "Spend Share", "ROAS", "CAC", "Action"], "placement": "bottom right", "style": "compact operational table"},
            {"page": "Campaign Ranking", "visual": "Scale candidates", "type": "Horizontal bar", "fields": ["DimCampaign[campaign_name]", "Campaign Scale Score"], "placement": "top left", "style": "green sorted ranking"},
            {"page": "Campaign Ranking", "visual": "Review/cut candidates", "type": "Horizontal bar", "fields": ["DimCampaign[campaign_name]", "Campaign Scale Score"], "placement": "top right", "style": "coral sorted ranking"},
            {"page": "Campaign Ranking", "visual": "Campaign decision table", "type": "Table", "fields": ["DimCampaign[campaign_name]", "DimChannel[channel]", "Spend", "Revenue", "ROAS", "CAC", "Campaign Scale Score", "Action"], "placement": "bottom", "style": "budget meeting handoff"},
            {"page": "Exceptions and Actions", "visual": "Budget action matrix", "type": "Scatter", "fields": ["ROAS vs Target", "CAC vs Target", "Spend Share", "DimChannel[channel]"], "placement": "top left", "style": "quadrant action read"},
            {"page": "Exceptions and Actions", "visual": "Next-month budget moves", "type": "Card group", "fields": ["Action", "Spend Share", "DimChannel[channel]"], "placement": "top right", "style": "reduce/fix and scale lists"},
            {"page": "Exceptions and Actions", "visual": "Operating view", "type": "Table", "fields": ["DimChannel[channel]", "Spend Share", "ROAS vs Target", "CAC vs Target", "ROAS", "CAC", "Action"], "placement": "bottom", "style": "exception table"},
        ],
    }

    (PROJECT / "build/config/theme.json").write_text(json.dumps(theme, indent=2) + "\n", encoding="utf-8")
    (PROJECT / "build/config/page_map.json").write_text(json.dumps(page_map, indent=2) + "\n", encoding="utf-8")
    (PROJECT / "build/config/visual_map.json").write_text(json.dumps(visual_map, indent=2) + "\n", encoding="utf-8")
    (PROJECT / "build/config/template_research.json").write_text(json.dumps(research, indent=2) + "\n", encoding="utf-8")

    research_md = [
        "# Template Research Notes",
        "",
        f"- Applied template direction: `{research['template_direction']}`",
        "- Goal: make Project 06 - Marketing Campaign ROI look like an executive marketing ROI command center rather than a plain chart dump.",
        "",
        "## Sources Used",
        "",
    ]
    for item in research["research_sources"]:
        research_md += [f"- {item['source']}: {item['url']}", f"  - Applied: {item['applied']}"]
    research_md += [
        "",
        "## Design Decisions",
        "",
        "- Kept the dashboard one subject: marketing campaign ROI and budget action.",
        "- Put the highest-level portfolio KPIs at the top-left/top row.",
        "- Replaced generic chart grids with panelized executive pages and action-focused tables.",
        "- Used green, amber, and coral only for action states: Scale, Optimize, Review/Cut.",
        "- Kept charts simple: trend, target bars, scatter/quadrant, ranking bars, and operating tables.",
    ]
    (PROJECT / "docs/template_research_notes.md").write_text("\n".join(research_md) + "\n", encoding="utf-8")


def write_preview_html(metrics: dict[str, pd.DataFrame | dict]) -> None:
    totals = metrics["totals"]
    cards = [
        ("Spend", money_m(totals["spend"])),
        ("Revenue", money_m(totals["revenue"])),
        ("ROAS", f"{totals['roas']:.2f}x"),
        ("CAC", f"${totals['cac']:.0f}"),
        ("Mktg ROI", pct(totals["roi"])),
        ("CVR", pct(totals["conversion_rate"])),
    ]
    card_html = "\n".join(f"<article><span>{label}</span><strong>{value}</strong></article>" for label, value in cards)
    pages = "\n".join(
        f"""
        <section class="page">
          <div class="page-head"><span>Page {idx}</span><h2>{title}</h2></div>
          <img src="screenshots/page_{idx:02d}.png" alt="{title}">
        </section>
        """
        for idx, title in enumerate(["Executive Overview", "Channel ROI", "Campaign Ranking", "Exceptions and Actions"], start=1)
    )
    html = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Marketing Campaign ROI Dashboard Preview</title>
<style>
:root {{
  --ink:#14213D;
  --muted:#6C7280;
  --paper:#F4F7FB;
  --panel:#FFFFFF;
  --line:#D7DEE8;
  --teal:#0E7C7B;
  --coral:#E3645A;
  --green:#2E8B57;
  --amber:#F0B429;
}}
* {{ box-sizing:border-box; }}
body {{ margin:0; font-family:"Segoe UI", Arial, sans-serif; background:var(--paper); color:var(--ink); }}
.shell {{ display:grid; grid-template-columns:156px 1fr; min-height:100vh; }}
aside {{ background:var(--ink); color:white; padding:28px 22px; position:sticky; top:0; height:100vh; }}
.logo {{ font-size:24px; font-weight:800; letter-spacing:.02em; }}
.kicker {{ margin-top:4px; color:#AFC3D9; font-size:11px; font-weight:700; }}
nav {{ margin-top:56px; display:grid; gap:10px; }}
nav span {{ color:#9FB4CC; font-size:13px; padding:10px 12px; border-radius:8px; }}
nav span:first-child {{ background:#31445F; color:white; }}
.side-note {{ position:absolute; left:22px; bottom:28px; right:22px; color:#B8C7D8; font-size:12px; line-height:1.45; }}
main {{ padding:32px 38px 48px; }}
.hero {{ display:flex; align-items:flex-end; justify-content:space-between; gap:24px; margin-bottom:18px; }}
h1 {{ margin:0; font-size:32px; line-height:1.1; }}
.hero p {{ margin:8px 0 0; color:var(--muted); max-width:760px; }}
.badge {{ border:1px solid var(--line); background:white; padding:10px 14px; border-radius:8px; color:var(--teal); font-weight:700; white-space:nowrap; }}
.cards {{ display:grid; grid-template-columns:repeat(6,minmax(120px,1fr)); gap:12px; margin:18px 0 26px; }}
article {{ background:white; border:1px solid var(--line); border-left:6px solid var(--teal); border-radius:8px; padding:14px 16px; min-height:84px; }}
article:nth-child(2) {{ border-left-color:var(--green); }}
article:nth-child(4) {{ border-left-color:var(--amber); }}
article:nth-child(5), article:nth-child(6) {{ border-left-color:var(--coral); }}
article span {{ display:block; color:var(--muted); font-size:11px; font-weight:800; text-transform:uppercase; }}
article strong {{ display:block; margin-top:9px; font-size:25px; }}
.research {{ background:white; border:1px solid var(--line); border-radius:8px; padding:16px 18px; margin-bottom:24px; display:grid; grid-template-columns:1.2fr 1fr; gap:16px; }}
.research h2 {{ font-size:16px; margin:0 0 8px; }}
.research p, .research li {{ color:var(--muted); font-size:13px; line-height:1.45; }}
.research ul {{ margin:0; padding-left:18px; }}
.page {{ margin:26px 0 36px; }}
.page-head {{ display:flex; align-items:baseline; gap:12px; margin-bottom:10px; }}
.page-head span {{ color:var(--teal); font-size:12px; font-weight:800; text-transform:uppercase; }}
.page h2 {{ margin:0; font-size:20px; }}
img {{ width:100%; display:block; background:white; border:1px solid var(--line); border-radius:8px; box-shadow:0 16px 38px rgba(20,33,61,.10); }}
@media (max-width:980px) {{
  .shell {{ grid-template-columns:1fr; }}
  aside {{ height:auto; position:relative; }}
  nav {{ grid-template-columns:repeat(4,1fr); margin-top:20px; }}
  .side-note {{ display:none; }}
  main {{ padding:24px 18px; }}
  .hero {{ display:block; }}
  .badge {{ display:inline-block; margin-top:14px; }}
  .cards {{ grid-template-columns:repeat(2,minmax(0,1fr)); }}
  .research {{ grid-template-columns:1fr; }}
}}
</style>
</head>
<body>
<div class="shell">
<aside>
  <div class="logo">MROI</div>
  <div class="kicker">PROJECT 6</div>
  <nav><span>Overview</span><span>Channel</span><span>Ranking</span><span>Actions</span></nav>
  <div class="side-note">Marketing ROI command center<br>Power BI template preview</div>
</aside>
<main>
  <section class="hero">
    <div>
      <h1>Marketing Campaign ROI Dashboard</h1>
      <p>Spend, CAC, ROAS, conversion, revenue by channel, paid vs organic, and campaign ranking redesigned as an executive-ready Power BI canvas.</p>
    </div>
    <div class="badge">Template: Executive ROI Command Center</div>
  </section>
  <section class="cards">
    {card_html}
  </section>
  <section class="research">
    <div>
      <h2>Applied design research</h2>
      <p>Inspired by current Power BI and marketing dashboard examples: one-screen executive hierarchy, top KPI strip, paid-vs-organic comparison, cost spike detection, and action-first budget movement.</p>
    </div>
    <ul>
      <li>Top-left/top-row portfolio KPIs.</li>
      <li>Simple charts: trend, target bars, quadrant, ranking, table.</li>
      <li>Action states: Scale, Optimize, Review/Cut.</li>
    </ul>
  </section>
  {pages}
</main>
</div>
</body>
</html>
"""
    (PROJECT / "output/dashboard_preview.html").write_text(html, encoding="utf-8")


def update_existing_docs() -> None:
    changelog = PROJECT / "docs/changelog.md"
    current = changelog.read_text(encoding="utf-8") if changelog.exists() else "# Changelog\n"
    entry = """\n## v04\n\n- Researched current Power BI and marketing dashboard template patterns.\n- Applied `Executive ROI Command Center` visual direction.\n- Rebuilt `build/config/theme.json`, `page_map.json`, and `visual_map.json` for a polished Power BI-ready design system.\n- Regenerated `output/dashboard_preview.html` and all four preview screenshots with the new layout.\n- Added `docs/template_research_notes.md` and `build/config/template_research.json`.\n"""
    if "## v04" not in current:
        changelog.write_text(current.rstrip() + "\n" + entry, encoding="utf-8")

    visual_qa = """# Visual QA Notes

Preview screenshots were regenerated with the `Executive ROI Command Center` template direction.

- Page 1: KPI strip, spend/revenue trend, paid-vs-organic bar, action map, and budget callouts.
- Page 2: ROAS/CAC target bars, efficiency quadrant, and channel scorecard.
- Page 3: scale/review campaign rankings and decision table.
- Page 4: exception matrix, budget moves, and operating view.

Native Power BI visual QA remains pending until a clean PBIX is built and extracted.
"""
    (PROJECT / "qa/visual_qa_notes.md").write_text(visual_qa, encoding="utf-8")

    runbook = PROJECT / "powerbi/notes/desktop_ui_runbook.md"
    if runbook.exists():
        text = runbook.read_text(encoding="utf-8")
        text = text.replace(
            "10. Apply `build/config/theme.json`.",
            "10. Apply `build/config/theme.json` (`Marketing ROI Command Center`) and use the left rail / panel layout in `build/config/page_map.json`.",
        )
        text = text.replace(
            "11. Build pages from `build/config/page_map.json` and `build/config/visual_map.json`.",
            "11. Build pages from `build/config/page_map.json` and `build/config/visual_map.json`; match the preview screenshots in `output/screenshots/`.",
        )
        runbook.write_text(text, encoding="utf-8")


def main() -> None:
    tables = read_tables()
    metrics = build_metrics(tables)
    write_theme_and_specs(metrics)
    page_overview(metrics)
    page_channel(metrics)
    page_campaign(metrics)
    page_actions(metrics)
    write_preview_html(metrics)
    update_existing_docs()


if __name__ == "__main__":
    main()
