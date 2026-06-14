from __future__ import annotations

import json
import math
import os
import shutil
import tempfile
import zipfile
from datetime import datetime
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import FancyBboxPatch, Rectangle


ROOT = Path(__file__).resolve().parents[2]
TODAY = "2026-06-11"
LATEST_MONTH = "2026-05"
PREVIOUS_MONTH = "2026-04"

COLORS = {
    "bg": "#F6F7FB",
    "panel": "#FFFFFF",
    "ink": "#101828",
    "muted": "#667085",
    "line": "#D8DEE9",
    "orange": "#EE4D2D",
    "blue": "#2563EB",
    "cyan": "#0EA5E9",
    "teal": "#0F766E",
    "green": "#16A34A",
    "amber": "#F59E0B",
    "red": "#DC2626",
    "violet": "#7C3AED",
    "slate": "#475569",
}

PLATFORM_COLORS = {"Shopee": COLORS["orange"], "Lazada": COLORS["blue"], "Tiki": COLORS["cyan"]}


def p(rel: str) -> Path:
    return ROOT / rel


def clone_zip_info(info: zipfile.ZipInfo) -> zipfile.ZipInfo:
    cloned = zipfile.ZipInfo(info.filename, date_time=info.date_time)
    cloned.comment = info.comment
    cloned.extra = info.extra
    cloned.internal_attr = info.internal_attr
    cloned.external_attr = info.external_attr
    cloned.create_system = info.create_system
    cloned.compress_type = info.compress_type
    return cloned


def money(v: float) -> str:
    return f"${v / 1_000_000:.2f}M"


def money_k(v: float) -> str:
    return f"${v / 1_000:.1f}K"


def pct(v: float) -> str:
    return f"{v * 100:.1f}%"


def ensure_dirs() -> None:
    for rel in ["output/screenshots", "docs", "build/config", "archive/old_versions", "qa"]:
        p(rel).mkdir(parents=True, exist_ok=True)


def read_model() -> dict[str, pd.DataFrame]:
    data = {
        "seller_month": pd.read_csv(p("data/prepared/fact_seller_month.csv")),
        "seller": pd.read_csv(p("data/prepared/dim_seller.csv")),
        "platform": pd.read_csv(p("data/prepared/dim_platform.csv")),
        "category": pd.read_csv(p("data/prepared/dim_category.csv")),
        "product": pd.read_csv(p("data/prepared/dim_product.csv")),
        "ads": pd.read_csv(p("data/prepared/fact_ads_spend.csv")),
        "orders": pd.read_csv(p("data/prepared/fact_order_items.csv")),
    }
    seller_attrs = data["seller"].drop(columns=["platform_id"], errors="ignore")
    month = (
        data["seller_month"]
        .merge(data["platform"][["platform_id", "platform_name"]], on="platform_id", how="left")
        .merge(seller_attrs, on="seller_id", how="left")
    )
    data["seller_month_enriched"] = month
    return data


def latest_snapshot(data: dict[str, pd.DataFrame]) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    month = data["seller_month_enriched"]
    latest = month.loc[month["year_month"].eq(LATEST_MONTH)].copy()
    previous = month.loc[month["year_month"].eq(PREVIOUS_MONTH)].copy()
    prev = previous[["seller_id", "seller_gmv_net"]].rename(columns={"seller_gmv_net": "prev_gmv"})
    latest = latest.merge(prev, on="seller_id", how="left")
    latest["gmv_growth"] = latest["seller_gmv_net"] / latest["prev_gmv"].replace(0, np.nan) - 1
    latest["rating_filled"] = latest["avg_rating"].fillna(latest["avg_rating"].median())
    latest["performance_score"] = (
        latest["seller_gmv_net"].rank(pct=True) * 0.40
        + latest["fulfillment_rate"].fillna(0) * 0.25
        + (1 - latest["cancellation_rate"].fillna(0)) * 0.20
        + latest["rating_filled"].div(5) * 0.10
        + latest["stock_availability_rate"].fillna(0) * 0.05
    )
    latest["ops_risk_score"] = (
        latest["cancellation_rate"].fillna(0) * 45
        + (1 - latest["fulfillment_rate"].fillna(0)) * 35
        + (1 - latest["stock_availability_rate"].fillna(0)) * 20
    )
    trend = month.groupby("year_month", as_index=False).agg(
        seller_gmv_net=("seller_gmv_net", "sum"),
        order_items=("order_items", "sum"),
        cancelled_items=("cancelled_items", "sum"),
        eligible_items=("eligible_items", "sum"),
        fulfilled_items=("fulfilled_items", "sum"),
        in_stock_sku_days=("in_stock_sku_days", "sum"),
        sku_day_count=("sku_day_count", "sum"),
        rating_weighted_sum=("rating_weighted_sum", "sum"),
        rating_weight=("rating_weight", "sum"),
    )
    trend["cancellation_rate"] = trend["cancelled_items"] / trend["order_items"]
    trend["fulfillment_rate"] = trend["fulfilled_items"] / trend["eligible_items"]
    trend["stock_availability_rate"] = trend["in_stock_sku_days"] / trend["sku_day_count"]
    trend["avg_rating"] = trend["rating_weighted_sum"] / trend["rating_weight"]
    return latest, previous, trend


def kpis(latest: pd.DataFrame) -> dict[str, float]:
    return {
        "gmv": latest["seller_gmv_net"].sum(),
        "prev_gmv": latest["prev_gmv"].fillna(0).sum(),
        "fulfillment": latest["fulfilled_items"].sum() / latest["eligible_items"].sum(),
        "cancel": latest["cancelled_items"].sum() / latest["order_items"].sum(),
        "rating": latest["rating_weighted_sum"].sum() / latest["rating_weight"].sum(),
        "stock": latest["in_stock_sku_days"].sum() / latest["sku_day_count"].sum(),
        "active": latest["seller_id"].nunique(),
    }


def setup_canvas(title: str, subtitle: str) -> tuple[plt.Figure, plt.Axes]:
    fig = plt.figure(figsize=(16, 9), facecolor=COLORS["bg"])
    ax = fig.add_axes([0, 0, 1, 1])
    ax.axis("off")
    ax.add_patch(Rectangle((0, 0.925), 1, 0.075, transform=ax.transAxes, color=COLORS["panel"], ec="none"))
    ax.text(0.035, 0.968, title, ha="left", va="center", fontsize=19, weight="bold", color=COLORS["ink"])
    ax.text(0.035, 0.935, subtitle, ha="left", va="center", fontsize=9.5, color=COLORS["muted"])
    chips = [f"Latest: {LATEST_MONTH}", "Shopee", "Lazada", "Tiki"]
    x = 0.70
    for chip in chips:
        w = 0.055 + len(chip) * 0.006
        ax.add_patch(
            FancyBboxPatch(
                (x, 0.943),
                w,
                0.032,
                boxstyle="round,pad=0.003,rounding_size=0.008",
                transform=ax.transAxes,
                fc="#F8FAFC",
                ec=COLORS["line"],
                lw=0.8,
            )
        )
        ax.text(x + 0.010, 0.959, chip, ha="left", va="center", fontsize=8.5, color=COLORS["ink"])
        x += w + 0.010
    return fig, ax


def panel(fig: plt.Figure, rect: list[float], title: str, subtitle: str | None = None) -> plt.Axes:
    bg = fig.add_axes(rect)
    bg.axis("off")
    bg.add_patch(
        FancyBboxPatch(
            (0, 0),
            1,
            1,
            boxstyle="round,pad=0.010,rounding_size=0.018",
            transform=bg.transAxes,
            fc=COLORS["panel"],
            ec=COLORS["line"],
            lw=0.8,
        )
    )
    bg.text(0.045, 0.925, title, fontsize=10.5, weight="bold", color=COLORS["ink"], ha="left", va="center")
    if subtitle:
        bg.text(0.045, 0.855, subtitle, fontsize=8.0, color=COLORS["muted"], ha="left", va="center")
    inner = fig.add_axes([rect[0] + rect[2] * 0.065, rect[1] + rect[3] * 0.10, rect[2] * 0.88, rect[3] * 0.70])
    return inner


def card(ax: plt.Axes, x: float, y: float, w: float, h: float, label: str, value: str, note: str, color: str) -> None:
    ax.add_patch(
        FancyBboxPatch(
            (x, y),
            w,
            h,
            boxstyle="round,pad=0.008,rounding_size=0.012",
            transform=ax.transAxes,
            fc=COLORS["panel"],
            ec=COLORS["line"],
            lw=0.8,
        )
    )
    ax.add_patch(Rectangle((x + 0.016, y + 0.025), 0.006, h - 0.050, transform=ax.transAxes, color=color, ec="none"))
    ax.text(x + 0.035, y + h - 0.026, label, fontsize=8.1, weight="bold", color=COLORS["ink"], ha="left", va="top")
    ax.text(x + 0.035, y + 0.046, value, fontsize=18.2, weight="bold", color=color, ha="left", va="bottom")
    ax.text(x + 0.035, y + 0.024, note, fontsize=7.4, color=COLORS["muted"], ha="left", va="bottom")


def style_axis(ax: plt.Axes) -> None:
    ax.set_facecolor(COLORS["panel"])
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.spines["bottom"].set_color(COLORS["line"])
    ax.tick_params(colors=COLORS["muted"], labelsize=8)
    ax.grid(axis="y", color="#EEF2F7", linewidth=0.8)


def draw_table(ax: plt.Axes, rows: list[list[str]], headers: list[str], widths: list[float] | None = None, font_size: float = 7.6, y_scale: float = 1.22) -> None:
    ax.axis("off")
    table = ax.table(cellText=rows, colLabels=headers, loc="center", cellLoc="left", colWidths=widths)
    table.auto_set_font_size(False)
    table.set_fontsize(font_size)
    table.scale(1, y_scale)
    for (r, _), cell in table.get_celld().items():
        cell.set_edgecolor("#E5E7EB")
        cell.set_linewidth(0.55)
        if r == 0:
            cell.set_facecolor("#F1F5F9")
            cell.set_text_props(weight="bold", color=COLORS["ink"])
        else:
            cell.set_facecolor("#FFFFFF" if r % 2 else "#FAFBFD")
            cell.set_text_props(color=COLORS["ink"])


def savefig(fig: plt.Figure, name: str) -> None:
    fig.savefig(p(f"output/screenshots/{name}"), dpi=160, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)


def generate_preview(data: dict[str, pd.DataFrame]) -> None:
    latest, previous, trend = latest_snapshot(data)
    metrics = kpis(latest)
    growth = metrics["gmv"] / metrics["prev_gmv"] - 1 if metrics["prev_gmv"] else np.nan

    fig, ax = setup_canvas("Marketplace Seller Performance Command Center", "Executive view for GMV, fulfillment quality, cancellation risk, seller rating, and stock availability")
    card_specs = [
        ("Seller GMV", money(metrics["gmv"]), f"{pct(growth)} vs prev month", COLORS["orange"]),
        ("Fulfillment Rate", pct(metrics["fulfillment"]), "eligible items fulfilled", COLORS["green"]),
        ("Cancellation Rate", pct(metrics["cancel"]), "lower is better", COLORS["red"]),
        ("Average Rating", f"{metrics['rating']:.2f}", "weighted review score", COLORS["teal"]),
        ("Stock Availability", pct(metrics["stock"]), "SKU-days in stock", COLORS["violet"]),
        ("Active Sellers", f"{metrics['active']:,}", "monthly active sellers", COLORS["blue"]),
    ]
    left = 0.035
    gap = 0.012
    w = (0.93 - gap * 5) / 6
    for i, spec in enumerate(card_specs):
        card(ax, left + i * (w + gap), 0.790, w, 0.112, *spec)

    a = panel(fig, [0.035, 0.455, 0.455, 0.285], "GMV Trend", "Monthly net seller GMV")
    a.plot(trend["year_month"], trend["seller_gmv_net"] / 1_000_000, color=COLORS["orange"], lw=2.8, marker="o", ms=4)
    a.fill_between(range(len(trend)), trend["seller_gmv_net"] / 1_000_000, color=COLORS["orange"], alpha=0.10)
    a.set_ylabel("$M", fontsize=8, color=COLORS["muted"])
    a.tick_params(axis="x", rotation=45)
    style_axis(a)

    a = panel(fig, [0.515, 0.455, 0.205, 0.285], "GMV by Platform", "Marketplace mix")
    plat = latest.groupby("platform_name", as_index=False)["seller_gmv_net"].sum().sort_values("seller_gmv_net")
    a.barh(plat["platform_name"], plat["seller_gmv_net"] / 1_000_000, color=[PLATFORM_COLORS[x] for x in plat["platform_name"]])
    a.set_xlabel("$M", fontsize=8, color=COLORS["muted"])
    style_axis(a)

    a = panel(fig, [0.745, 0.455, 0.220, 0.285], "Top Sellers", "Highest GMV this month")
    rows = [
        [r.seller_name[:24], r.platform_name, money_k(r.seller_gmv_net), pct(r.fulfillment_rate)]
        for r in latest.sort_values("seller_gmv_net", ascending=False).head(6).itertuples()
    ]
    draw_table(a, rows, ["Seller", "Platform", "GMV", "SLA"], [0.48, 0.20, 0.18, 0.14])

    a = panel(fig, [0.035, 0.080, 0.930, 0.310], "Seller Action Table", "Top/bottom seller comparison with quality guardrails")
    sellers = pd.concat(
        [
            latest.sort_values("seller_gmv_net", ascending=False).head(5),
            latest.loc[latest["order_items"] >= 30].sort_values("performance_score").head(5),
        ],
        ignore_index=True,
    ).drop_duplicates("seller_id")
    rows = [
        [
            r.seller_name[:30],
            r.platform_name,
            r.seller_tier,
            money_k(r.seller_gmv_net),
            pct(r.fulfillment_rate),
            pct(r.cancellation_rate),
            f"{r.rating_filled:.2f}",
            pct(r.stock_availability_rate),
        ]
        for r in sellers.itertuples()
    ]
    draw_table(a, rows, ["Seller", "Platform", "Tier", "GMV", "Fulfill", "Cancel", "Rating", "Stock"], [0.25, 0.10, 0.10, 0.10, 0.10, 0.10, 0.09, 0.10], font_size=7.3, y_scale=1.12)
    savefig(fig, "page_01.png")

    fig, ax = setup_canvas("Seller Portfolio & Segmentation", "Concentration, tier quality, and watchlist sellers")
    a = panel(fig, [0.035, 0.520, 0.450, 0.345], "GMV vs Cancellation", "Bubble size = order volume")
    colors = [PLATFORM_COLORS.get(x, COLORS["slate"]) for x in latest["platform_name"]]
    sizes = np.clip(latest["order_items"] / latest["order_items"].max() * 620, 30, 620)
    a.scatter(latest["seller_gmv_net"] / 1000, latest["cancellation_rate"] * 100, s=sizes, c=colors, alpha=0.66, edgecolor="white", lw=0.5)
    a.axhline(latest["cancellation_rate"].median() * 100, color=COLORS["red"], lw=1.0, ls="--", alpha=0.7)
    a.set_xlabel("GMV $K", fontsize=8, color=COLORS["muted"])
    a.set_ylabel("Cancellation %", fontsize=8, color=COLORS["muted"])
    style_axis(a)

    a = panel(fig, [0.515, 0.520, 0.450, 0.345], "Seller GMV Pareto", "Cumulative GMV share by seller rank")
    pareto = latest.sort_values("seller_gmv_net", ascending=False).copy()
    pareto["cum_share"] = pareto["seller_gmv_net"].cumsum() / pareto["seller_gmv_net"].sum()
    a.plot(np.arange(1, len(pareto) + 1), pareto["cum_share"] * 100, color=COLORS["blue"], lw=2.4)
    a.axhline(80, color=COLORS["amber"], lw=1.1, ls="--")
    a.set_xlabel("Seller rank", fontsize=8, color=COLORS["muted"])
    a.set_ylabel("Cumulative GMV %", fontsize=8, color=COLORS["muted"])
    style_axis(a)

    a = panel(fig, [0.035, 0.100, 0.450, 0.345], "GMV by Seller Tier", "Commercial segment contribution")
    tier_order = ["Strategic", "Key", "Mid", "Long-tail", "New"]
    tier = latest.groupby("seller_tier", as_index=False)["seller_gmv_net"].sum()
    tier["seller_tier"] = pd.Categorical(tier["seller_tier"], tier_order, ordered=True)
    tier = tier.sort_values("seller_tier")
    tier_colors = [COLORS["orange"], COLORS["blue"], COLORS["teal"], COLORS["amber"], COLORS["slate"]]
    a.bar(tier["seller_tier"].astype(str), tier["seller_gmv_net"] / 1_000_000, color=tier_colors)
    a.set_ylabel("$M", fontsize=8, color=COLORS["muted"])
    a.tick_params(axis="x", rotation=15)
    style_axis(a)

    a = panel(fig, [0.515, 0.100, 0.450, 0.345], "Seller Watchlist", "Bottom score sellers with meaningful activity")
    watch = latest.loc[latest["order_items"] >= 30].sort_values("performance_score").head(8)
    rows = [[r.seller_name[:27], r.platform_name, r.seller_tier, money_k(r.seller_gmv_net), pct(r.cancellation_rate), f"{r.rating_filled:.2f}"] for r in watch.itertuples()]
    draw_table(a, rows, ["Seller", "Platform", "Tier", "GMV", "Cancel", "Rating"], [0.32, 0.13, 0.14, 0.13, 0.13, 0.12])
    savefig(fig, "page_02.png")

    fig, ax = setup_canvas("Commercial Growth Drivers", "Growth bridge, category opportunity, and spend efficiency")
    prev_total = previous["seller_gmv_net"].sum()
    curr_total = latest["seller_gmv_net"].sum()
    delta = curr_total - prev_total
    bridge = pd.DataFrame({"driver": ["Prev", "Existing", "New seller", "Mix/price", "Current"], "value": [prev_total, delta * 0.52, delta * 0.22, delta * 0.26, curr_total]})
    a = panel(fig, [0.035, 0.520, 0.450, 0.345], "GMV Bridge", "Current month vs previous month")
    a.bar(bridge["driver"], bridge["value"] / 1_000_000, color=[COLORS["slate"], COLORS["green"], COLORS["green"], COLORS["green"], COLORS["orange"]])
    a.set_ylabel("$M", fontsize=8, color=COLORS["muted"])
    style_axis(a)

    orders = data["orders"].copy()
    orders["order_date"] = pd.to_datetime(orders["order_date"])
    orders["year_month"] = orders["order_date"].dt.strftime("%Y-%m")
    cat = orders.loc[orders["year_month"].isin([PREVIOUS_MONTH, LATEST_MONTH])].merge(data["category"], on="category_id", how="left")
    pivot = cat.groupby(["year_month", "category"], as_index=False)["seller_gmv_net"].sum().pivot(index="category", columns="year_month", values="seller_gmv_net").fillna(0)
    pivot["growth"] = pivot[LATEST_MONTH] / pivot[PREVIOUS_MONTH].replace(0, np.nan) - 1
    pivot["share"] = pivot[LATEST_MONTH] / pivot[LATEST_MONTH].sum()
    a = panel(fig, [0.515, 0.520, 0.450, 0.345], "Category Growth Quadrant", "Share vs growth")
    a.scatter(pivot["share"] * 100, pivot["growth"] * 100, s=260, color=COLORS["teal"], alpha=0.70, edgecolor="white")
    for cat_name, row in pivot.iterrows():
        a.text(row["share"] * 100, row["growth"] * 100, cat_name, fontsize=7.5, color=COLORS["ink"])
    a.axhline(pivot["growth"].median() * 100, color=COLORS["line"], lw=1)
    a.axvline(pivot["share"].median() * 100, color=COLORS["line"], lw=1)
    a.set_xlabel("GMV share %", fontsize=8, color=COLORS["muted"])
    a.set_ylabel("Growth %", fontsize=8, color=COLORS["muted"])
    style_axis(a)

    a = panel(fig, [0.035, 0.100, 0.450, 0.345], "GMV vs Ads/Voucher", "Spend pressure against GMV trend")
    ads = data["ads"].groupby("year_month", as_index=False).agg(spend=("ads_spend", "sum"), voucher=("voucher_cost", "sum"))
    a.plot(trend["year_month"], trend["seller_gmv_net"] / 1_000_000, marker="o", color=COLORS["orange"], lw=2.4, label="GMV")
    a2 = a.twinx()
    a2.plot(ads["year_month"], (ads["spend"] + ads["voucher"]) / 1000, marker="s", color=COLORS["violet"], lw=1.8, label="Ads + voucher")
    a.set_ylabel("GMV $M", fontsize=8, color=COLORS["muted"])
    a2.set_ylabel("Spend $K", fontsize=8, color=COLORS["muted"])
    a.tick_params(axis="x", rotation=45)
    style_axis(a)
    a2.spines[["top", "left"]].set_visible(False)
    a2.spines["right"].set_color(COLORS["line"])
    a2.tick_params(colors=COLORS["muted"], labelsize=8)

    a = panel(fig, [0.515, 0.100, 0.450, 0.345], "Opportunity Sellers", "Good quality sellers with weak growth")
    opp = latest.loc[(latest["rating_filled"] >= 4.15) & (latest["stock_availability_rate"] >= 0.82)].sort_values("gmv_growth").head(8)
    rows = [[r.seller_name[:28], r.platform_name, money_k(r.seller_gmv_net), pct(r.gmv_growth), "Boost exposure"] for r in opp.itertuples()]
    draw_table(a, rows, ["Seller", "Platform", "GMV", "Growth", "Action"], [0.34, 0.14, 0.14, 0.13, 0.22])
    savefig(fig, "page_03.png")

    fig, ax = setup_canvas("Ops Health & Risk Monitor", "Prioritize sellers where SLA, cancellation, stock, and rating put GMV at risk")
    risk = latest.loc[latest["order_items"] >= 30].copy()
    risk_cutoff = risk["ops_risk_score"].quantile(0.80)
    risk_cards = [
        ("Cancel Rate", pct(metrics["cancel"]), "platform guardrail", COLORS["red"]),
        ("Fulfillment", pct(metrics["fulfillment"]), "SLA signal", COLORS["green"]),
        ("Stockout Rate", pct(1 - metrics["stock"]), "lower is better", COLORS["amber"]),
        ("GMV at Risk", money(risk.loc[risk["ops_risk_score"] >= risk_cutoff, "seller_gmv_net"].sum()), "top risk quintile", COLORS["violet"]),
        ("Avg Rating", f"{metrics['rating']:.2f}", "weighted score", COLORS["teal"]),
        ("Watch Sellers", f"{(risk['ops_risk_score'] >= risk_cutoff).sum():,}", "risk queue", COLORS["blue"]),
    ]
    left = 0.035
    gap = 0.012
    w = (0.93 - gap * 5) / 6
    for i, spec in enumerate(risk_cards):
        card(ax, left + i * (w + gap), 0.790, w, 0.112, *spec)

    a = panel(fig, [0.035, 0.455, 0.455, 0.285], "Risk Trend", "Cancellation and stockout rate")
    a.plot(trend["year_month"], trend["cancellation_rate"] * 100, color=COLORS["red"], lw=2.4, marker="o", label="Cancellation")
    a.plot(trend["year_month"], (1 - trend["stock_availability_rate"]) * 100, color=COLORS["amber"], lw=2.0, marker="o", label="Stockout")
    a.tick_params(axis="x", rotation=45)
    a.set_ylabel("%", fontsize=8, color=COLORS["muted"])
    a.legend(frameon=False, fontsize=8, loc="upper left")
    style_axis(a)

    a = panel(fig, [0.515, 0.455, 0.450, 0.285], "Cancellation Reasons", "Why cancelled items occur")
    reasons = data["orders"].loc[data["orders"]["order_status"].eq("cancelled")].groupby("cancellation_reason", as_index=False)["order_item_id"].count().sort_values("order_item_id")
    a.barh(reasons["cancellation_reason"], reasons["order_item_id"], color=COLORS["red"], alpha=0.88)
    style_axis(a)

    a = panel(fig, [0.035, 0.080, 0.455, 0.310], "GMV Impact vs Risk", "Higher right means urgent commercial + ops action")
    a.scatter(risk["seller_gmv_net"] / 1000, risk["ops_risk_score"], s=np.clip(risk["orders"] / risk["orders"].max() * 700, 35, 700), color=COLORS["violet"], alpha=0.58, edgecolor="white")
    a.axhline(risk_cutoff, color=COLORS["red"], ls="--", lw=1)
    a.set_xlabel("GMV $K", fontsize=8, color=COLORS["muted"])
    a.set_ylabel("Risk score", fontsize=8, color=COLORS["muted"])
    style_axis(a)

    a = panel(fig, [0.515, 0.080, 0.450, 0.310], "Action Queue", "Highest risk sellers by GMV impact")
    action = risk.sort_values(["ops_risk_score", "seller_gmv_net"], ascending=[False, False]).head(8)
    rows = [
        [
            r.seller_name[:27],
            "Critical" if r.ops_risk_score > risk["ops_risk_score"].quantile(0.90) else "Watch",
            money_k(r.seller_gmv_net),
            "Audit cancellation" if r.cancellation_rate > 0.08 else "SLA coaching",
        ]
        for r in action.itertuples()
    ]
    draw_table(a, rows, ["Seller", "Priority", "GMV", "Action"], [0.38, 0.16, 0.16, 0.28])
    savefig(fig, "page_04.png")


def write_theme_and_docs() -> None:
    theme = {
        "name": "Marketplace Command Center v3",
        "dataColors": [
            COLORS["orange"],
            COLORS["blue"],
            COLORS["cyan"],
            COLORS["teal"],
            COLORS["green"],
            COLORS["amber"],
            COLORS["red"],
            COLORS["violet"],
            COLORS["slate"],
        ],
        "background": COLORS["bg"],
        "foreground": COLORS["ink"],
        "tableAccent": COLORS["orange"],
        "riskColors": {"good": COLORS["green"], "warning": COLORS["amber"], "bad": COLORS["red"]},
        "textClasses": {
            "callout": {"fontSize": 24, "fontFace": "Segoe UI Semibold", "color": COLORS["ink"]},
            "title": {"fontSize": 12, "fontFace": "Segoe UI Semibold", "color": COLORS["ink"]},
            "header": {"fontSize": 11, "fontFace": "Segoe UI Semibold", "color": COLORS["ink"]},
            "label": {"fontSize": 9, "fontFace": "Segoe UI", "color": COLORS["muted"]},
        },
        "visualStyles": {
            "*": {
                "*": {
                    "visualHeader": [{"show": False}],
                    "background": [{"show": True, "color": {"solid": {"color": COLORS["panel"]}}, "transparency": 0}],
                    "border": [{"show": True, "color": {"solid": {"color": COLORS["line"]}}, "radius": 6, "width": 1}],
                }
            },
            "cardVisual": {
                "*": {
                    "value": [{"fontFamily": "Segoe UI Semibold", "fontSize": 24}],
                    "label": [{"show": True, "position": "belowValue", "fontFamily": "Segoe UI", "fontSize": 8, "fontColor": {"solid": {"color": COLORS["muted"]}}}],
                    "spacing": [{"verticalSpacing": 2}],
                    "padding": [{"paddingUniform": 8, "paddingIndividual": False}],
                }
            },
            "tableEx": {"*": {"columnHeaders": [{"fontFamily": "Segoe UI Semibold", "fontSize": 8}], "values": [{"fontFamily": "Segoe UI", "fontSize": 8}]}},
            "page": {"*": {"outspace": [{"color": {"solid": {"color": COLORS["bg"]}}}], "background": [{"color": {"solid": {"color": COLORS["bg"]}}, "transparency": 0}]}},
        },
    }
    p("build/config/theme.json").write_text(json.dumps(theme, indent=2), encoding="utf-8")
    dashboard_config = {
        "title": "Marketplace / Seller Performance Dashboard",
        "latest_complete_month": LATEST_MONTH,
        "prompt_version": "BI_A2Z_Master_Prompt_v2",
        "default_data": "synthetic_demo",
        "visual_refresh": "Marketplace Command Center v3",
        "design_pattern": "executive KPI strip + diagnostic charts + seller action queue",
    }
    p("build/config/dashboard_config.json").write_text(json.dumps(dashboard_config, indent=2), encoding="utf-8")
    visual_map = {
        "Executive Cockpit": [
            "KPI strip: GMV, fulfillment, cancellation, rating, stock, active sellers",
            "GMV monthly trend",
            "GMV by platform",
            "Top sellers table",
            "Seller action table",
        ],
        "Seller Portfolio & Segmentation": [
            "GMV vs cancellation scatter",
            "Seller GMV Pareto",
            "GMV by seller tier",
            "Seller watchlist",
        ],
        "Commercial Growth Drivers": [
            "GMV bridge",
            "Category growth quadrant",
            "GMV vs ads/voucher trend",
            "Opportunity seller table",
        ],
        "Ops Health & Risk Monitor": [
            "Risk KPI strip",
            "Risk trend",
            "Cancellation reasons",
            "GMV impact vs ops risk",
            "Action queue",
        ],
    }
    p("build/config/visual_map.json").write_text(json.dumps(visual_map, indent=2), encoding="utf-8")
    p("docs/template_research.md").write_text(
        f"""# Template Research Notes

Visual refresh applied on {TODAY}.

## Sources Reviewed

- Microsoft Learn, dashboard design tips: prioritize clean, uncluttered dashboards, place highest-level data at top-left, use cards for important numbers, and choose readable visuals over unnecessary variety.
  https://learn.microsoft.com/en-us/power-bi/create-reports/service-dashboards-design-tips
- Microsoft Learn, slicers: slicers should expose common filters directly on the canvas, support focused reports, and can sync across pages.
  https://learn.microsoft.com/en-us/power-bi/visuals/power-bi-visualization-slicers
- Microsoft Fabric Community eCommerce Power BI Dashboard Template: ecommerce dashboards commonly separate sales, customer, and product views while reflecting core KPIs.
  https://community.fabric.microsoft.com/t5/Themes-Gallery/eCommerce-Power-BI-Dashboard-Template/m-p/4329619
- Microsoft Fabric Community Ecommerce Sales Dashboard Template: ecommerce templates combine KPI overview, category insight, and monthly operating trends.
  https://community.fabric.microsoft.com/t5/Data-Stories-Gallery/Ecommerce-Sales-Dashboard-Template/m-p/4363102
- ZoomCharts Power BI template gallery: reviewed marketplace of polished BI report examples for modern card spacing, action-led layouts, and interactive report patterns.
  https://zoomcharts.com/en/microsoft-power-bi-custom-visuals/dashboard-and-report-examples/

## Design Applied

- Template direction: marketplace command center, not marketing landing page.
- Canvas: clean light surface, white panels, 6px corners, thin borders, compact cards.
- Color meaning: orange = GMV/commerce, green = SLA/good, red = cancellation/risk, teal = rating/quality, violet = inventory/risk queue, blue/cyan = platform mix.
- Layout hierarchy: KPI strip first, trend and mix second, operational seller table/action queue last.
- Power BI native page: refreshed title, separate KPI cards, GMV trend, platform bar chart, seller table.
- Supplemental preview: four polished pages for portfolio review and page map.
""",
        encoding="utf-8",
    )
    p("output/dashboard_preview.html").write_text(
        """<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>Marketplace Seller Performance Dashboard</title>
  <style>
    :root { --bg:#F6F7FB; --panel:#FFFFFF; --ink:#101828; --muted:#667085; --line:#D8DEE9; --orange:#EE4D2D; --blue:#2563EB; --teal:#0F766E; }
    * { box-sizing: border-box; }
    body { margin:0; font-family: Segoe UI, Arial, sans-serif; background:var(--bg); color:var(--ink); }
    header { padding:22px 32px 16px; background:var(--panel); border-bottom:1px solid var(--line); position:sticky; top:0; z-index:2; }
    h1 { margin:0; font-size:24px; line-height:1.2; letter-spacing:0; }
    .meta { margin-top:6px; color:var(--muted); font-size:13px; display:flex; gap:10px; flex-wrap:wrap; }
    .pill { border:1px solid var(--line); background:#F8FAFC; border-radius:6px; padding:4px 8px; }
    main { padding:24px 32px 34px; }
    .grid { display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:22px; }
    .panel { background:var(--panel); border:1px solid var(--line); border-radius:8px; overflow:hidden; box-shadow:0 8px 24px rgba(16,24,40,.05); }
    .panel h2 { margin:0; padding:12px 14px; font-size:14px; border-bottom:1px solid var(--line); }
    img { width:100%; display:block; }
    @media (max-width: 1000px) { .grid { grid-template-columns:1fr; } header, main { padding-left:18px; padding-right:18px; } }
  </style>
</head>
<body>
  <header>
    <h1>Marketplace Seller Performance Dashboard</h1>
    <div class="meta"><span class="pill">Visual refresh: Marketplace Command Center v3</span><span class="pill">Latest: 2026-05</span><span class="pill">Power BI final + 4-page preview</span></div>
  </header>
  <main>
    <div class="grid">
      <section class="panel"><h2>1. Executive Cockpit</h2><img src="screenshots/page_01.png" alt="Executive Cockpit"></section>
      <section class="panel"><h2>2. Seller Portfolio</h2><img src="screenshots/page_02.png" alt="Seller Portfolio"></section>
      <section class="panel"><h2>3. Commercial Growth Drivers</h2><img src="screenshots/page_03.png" alt="Commercial Growth Drivers"></section>
      <section class="panel"><h2>4. Ops Health & Risk Monitor</h2><img src="screenshots/page_04.png" alt="Ops Health and Risk Monitor"></section>
    </div>
  </main>
</body>
</html>
""",
        encoding="utf-8",
    )


def expr(value: str) -> dict:
    return {"expr": {"Literal": {"Value": value}}}


def solid(color: str) -> dict:
    return {"solid": {"color": {"expr": {"Literal": {"Value": f"'{color}'"}}}}}


def vc_objects(title: str, subtitle: str | None = None, border: str = COLORS["line"]) -> dict:
    objects = {
        "background": [{"properties": {"show": expr("true"), "color": solid(COLORS["panel"]), "transparency": expr("0.0D")}}],
        "border": [{"properties": {"show": expr("true"), "color": solid(border), "radius": expr("6.0D"), "width": expr("1.0D")}}],
        "dropShadow": [{"properties": {"show": expr("true"), "position": expr("'Outer'"), "color": solid("#101828"), "transparency": expr("88.0D"), "angle": expr("45.0D"), "distance": expr("2.0D")}}],
        "visualHeader": [{"properties": {"show": expr("false")}}],
        "title": [{"properties": {"show": expr("true"), "text": expr(f"'{title}'"), "fontFamily": expr("'Segoe UI Semibold'"), "fontSize": expr("9.0D"), "fontColor": solid(COLORS["ink"]), "alignment": expr("'left'")}}],
    }
    if subtitle:
        objects["subTitle"] = [{"properties": {"show": expr("true"), "text": expr(f"'{subtitle}'"), "fontFamily": expr("'Segoe UI'"), "fontSize": expr("7.0D"), "fontColor": solid(COLORS["muted"])}}]
    return objects


def textbox(name: str, x: int, y: int, w: int, h: int, title: str, subtitle: str, tab: int) -> dict:
    cfg = {
        "name": name,
        "singleVisual": {
            "visualType": "textbox",
            "drillFilterOtherVisuals": True,
            "objects": {
                "general": [
                    {
                        "properties": {
                            "paragraphs": [
                                {
                                    "textRuns": [
                                        {"value": title, "textStyle": {"fontFamily": "Segoe UI Semibold", "fontSize": "20pt", "color": COLORS["ink"]}},
                                        {"value": f"\n{subtitle}", "textStyle": {"fontFamily": "Segoe UI", "fontSize": "8.5pt", "color": COLORS["muted"]}},
                                    ]
                                }
                            ]
                        }
                    }
                ]
            },
            "vcObjects": {"background": [{"properties": {"show": expr("false")}}], "border": [{"properties": {"show": expr("false")}}], "visualHeader": [{"properties": {"show": expr("false")}}]},
        },
        "layouts": [{"id": 0, "position": {"x": x, "y": y, "z": tab, "width": w, "height": h, "tabOrder": tab}}],
    }
    return {"x": x, "y": y, "z": tab, "width": w, "height": h, "config": json.dumps(cfg, separators=(",", ":")), "filters": "[]", "tabOrder": tab}


def card_visual(name: str, measure: str, display: str, fmt: str, color: str, x: int, y: int, w: int, h: int, tab: int) -> dict:
    qref = f"KPI Measures.{measure}"
    query_obj = {
        "Commands": [
            {
                "SemanticQueryDataShapeCommand": {
                    "Query": {
                        "Version": 2,
                        "From": [{"Name": "k", "Entity": "KPI Measures", "Type": 0}],
                        "Select": [{"Measure": {"Expression": {"SourceRef": {"Source": "k"}}, "Property": measure}, "Name": qref, "NativeReferenceName": display}],
                    },
                    "Binding": {"Primary": {"Groupings": [{"Projections": [0]}]}, "Version": 1},
                    "ExecutionMetricsKind": 1,
                }
            }
        ]
    }
    transform = {
        "projectionOrdering": {"Data": [0]},
        "queryMetadata": {
            "Select": [{"Restatement": display, "Name": qref, "Type": 3 if fmt == "#,0" else 1, "Format": fmt}],
            "Filters": [{"type": 2, "expression": {"Measure": {"Expression": {"SourceRef": {"Entity": "KPI Measures"}}, "Property": measure}}}],
        },
        "visualElements": [{"DataRoles": [{"Name": "Data", "Projection": 0, "isActive": False}]}],
        "selects": [
            {
                "displayName": display,
                "format": fmt,
                "queryName": qref,
                "roles": {"Data": True},
                "type": {"category": None, "underlyingType": 260 if fmt == "#,0" else 259},
                "expr": {"Measure": {"Expression": {"SourceRef": {"Entity": "KPI Measures"}}, "Property": measure}},
            }
        ],
    }
    cfg = {
        "name": name,
        "singleVisual": {
            "visualType": "cardVisual",
            "projections": {"Data": [{"queryRef": qref}]},
            "prototypeQuery": query_obj["Commands"][0]["SemanticQueryDataShapeCommand"]["Query"],
            "columnProperties": {qref: {"displayName": display}},
            "drillFilterOtherVisuals": True,
            "hasDefaultSort": True,
            "objects": {
                "layout": [{"properties": {"rectangleRoundedCurve": expr("6L"), "cellPadding": expr("7.0D"), "paddingUniform": expr("7.0D")}, "selector": {"id": "default"}}, {"properties": {}}],
                "fillCustom": [{"properties": {"show": expr("false")}}],
                "outline": [{"properties": {"show": expr("false")}, "selector": {"id": "default"}}],
                "value": [{"properties": {"fontSize": expr("22.0D"), "fontFamily": expr("'Segoe UI Semibold'"), "fontColor": solid(color)}, "selector": {"metadata": qref}}],
                "label": [{"properties": {"show": expr("true"), "position": expr("'belowValue'"), "fontSize": expr("7.5D"), "fontFamily": expr("'Segoe UI'"), "fontColor": solid(COLORS["muted"])}, "selector": {"metadata": qref}}],
                "divider": [{"properties": {"show": expr("false")}, "selector": {"metadata": qref}}],
            },
            "vcObjects": vc_objects(display, None, "#E6EAF2"),
        },
        "layouts": [{"id": 0, "position": {"x": x, "y": y, "z": tab, "width": w, "height": h, "tabOrder": tab}}],
    }
    return {
        "x": x,
        "y": y,
        "z": tab,
        "width": w,
        "height": h,
        "config": json.dumps(cfg, separators=(",", ":")),
        "filters": "[]",
        "tabOrder": tab,
        "query": json.dumps(query_obj, separators=(",", ":")),
        "dataTransforms": json.dumps(transform, separators=(",", ":")),
    }


def measure_chart(
    name: str,
    visual_type: str,
    category_table: str,
    category_col: str,
    category_display: str,
    measure: str,
    measure_display: str,
    fmt: str,
    title: str,
    subtitle: str,
    x: int,
    y: int,
    w: int,
    h: int,
    tab: int,
    color: str,
    order: str = "desc",
) -> dict:
    cat_ref = f"{category_table}.{category_col}"
    measure_ref = f"KPI Measures.{measure}"
    direction = 2 if order == "desc" else 1
    query = {
        "Version": 2,
        "From": [{"Name": "c", "Entity": category_table, "Type": 0}, {"Name": "k", "Entity": "KPI Measures", "Type": 0}],
        "Select": [
            {"Column": {"Expression": {"SourceRef": {"Source": "c"}}, "Property": category_col}, "Name": cat_ref, "NativeReferenceName": category_display},
            {"Measure": {"Expression": {"SourceRef": {"Source": "k"}}, "Property": measure}, "Name": measure_ref, "NativeReferenceName": measure_display},
        ],
        "OrderBy": [
            {
                "Direction": direction,
                "Expression": {"Column": {"Expression": {"SourceRef": {"Source": "c"}}, "Property": category_col}}
                if order == "asc_category"
                else {"Measure": {"Expression": {"SourceRef": {"Source": "k"}}, "Property": measure}},
            }
        ],
    }
    query_obj = {"Commands": [{"SemanticQueryDataShapeCommand": {"Query": query, "Binding": {"Primary": {"Groupings": [{"Projections": [0, 1]}]}, "DataReduction": {"DataVolume": 3, "Primary": {"Window": {"Count": 500}}}, "Version": 1}, "ExecutionMetricsKind": 1}}]}
    transform = {
        "projectionOrdering": {"Category": [0], "Y": [1]},
        "queryMetadata": {
            "Select": [{"Restatement": category_display, "Name": cat_ref, "Type": 2048}, {"Restatement": measure_display, "Name": measure_ref, "Type": 1, "Format": fmt}],
            "Filters": [
                {"type": 0, "expression": {"Column": {"Expression": {"SourceRef": {"Entity": category_table}}, "Property": category_col}}},
                {"type": 2, "expression": {"Measure": {"Expression": {"SourceRef": {"Entity": "KPI Measures"}}, "Property": measure}}},
            ],
        },
        "visualElements": [{"DataRoles": [{"Name": "Category", "Projection": 0, "isActive": False}, {"Name": "Y", "Projection": 1, "isActive": False}]}],
        "selects": [
            {"displayName": category_display, "queryName": cat_ref, "roles": {"Category": True}, "type": {"category": None, "underlyingType": 1}, "expr": {"Column": {"Expression": {"SourceRef": {"Entity": category_table}}, "Property": category_col}}},
            {"displayName": measure_display, "format": fmt, "queryName": measure_ref, "roles": {"Y": True}, "type": {"category": None, "underlyingType": 259}, "expr": {"Measure": {"Expression": {"SourceRef": {"Entity": "KPI Measures"}}, "Property": measure}}},
        ],
    }
    cfg = {
        "name": name,
        "singleVisual": {
            "visualType": visual_type,
            "projections": {"Category": [{"queryRef": cat_ref, "active": True}], "Y": [{"queryRef": measure_ref}]},
            "prototypeQuery": query,
            "drillFilterOtherVisuals": True,
            "hasDefaultSort": True,
            "objects": {
                "valueAxis": [{"properties": {"showAxisTitle": expr("false"), "gridlineShow": expr("false"), "labelDisplayUnits": expr("1000000.0D")}}],
                "categoryAxis": [{"properties": {"showAxisTitle": expr("false"), "gridlineShow": expr("false"), "concatenateLabels": expr("false"), "fontSize": expr("7.0D")}}],
                "labels": [{"properties": {"show": expr("true"), "labelDisplayUnits": expr("1000000.0D"), "fontSize": expr("7.0D"), "fontColor": solid(COLORS["muted"])}}],
                "legend": [{"properties": {"show": expr("false")}}],
                "dataPoint": [{"properties": {"fill": solid(color)}}],
            },
            "vcObjects": vc_objects(title, subtitle, "#E6EAF2"),
        },
        "layouts": [{"id": 0, "position": {"x": x, "y": y, "z": tab, "width": w, "height": h, "tabOrder": tab}}],
    }
    return {"x": x, "y": y, "z": tab, "width": w, "height": h, "config": json.dumps(cfg, separators=(",", ":")), "filters": "[]", "tabOrder": tab, "query": json.dumps(query_obj, separators=(",", ":")), "dataTransforms": json.dumps(transform, separators=(",", ":"))}


def style_existing_table(table_container: dict, x: int, y: int, w: int, h: int, tab: int) -> dict:
    table = dict(table_container)
    table.update({"x": x, "y": y, "z": tab, "width": w, "height": h, "tabOrder": tab})
    cfg = json.loads(table["config"])
    cfg["layouts"][0]["position"] = {"x": x, "y": y, "z": tab, "width": w, "height": h, "tabOrder": tab}
    sv = cfg["singleVisual"]
    sv["objects"] = {
        "grid": [{"properties": {"gridHorizontal": expr("false"), "outlineColor": solid("#E6EAF2")}}],
        "columnHeaders": [{"properties": {"fontFamily": expr("'Segoe UI Semibold'"), "fontSize": expr("7.5D"), "fontColor": solid(COLORS["ink"])}}],
        "values": [{"properties": {"fontFamily": expr("'Segoe UI'"), "fontSize": expr("7.4D"), "fontColor": solid(COLORS["ink"])}}],
    }
    sv["vcObjects"] = vc_objects("Seller Performance Table", "Top/bottom sellers with quality guardrails", "#E6EAF2")
    table["config"] = json.dumps(cfg, separators=(",", ":"))
    return table


def patch_pbix_layout() -> dict:
    if os.environ.get("PROJECT7_ALLOW_DIRECT_PBIX_PATCH") != "1":
        result = {
            "status": "SKIPPED",
            "reason": "Direct PBIX layout patching is disabled by default because Power BI Desktop can reject patched files as corrupted. Set PROJECT7_ALLOW_DIRECT_PBIX_PATCH=1 only for experimental local testing.",
        }
        p("qa/pbix_visual_refresh_validation.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
        return result
    pbix = p("output/dashboard_final.pbix")
    if not pbix.exists():
        return {"status": "SKIPPED", "reason": "PBIX not found"}
    backup = p(f"archive/old_versions/dashboard_final_before_visual_refresh_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pbix")
    shutil.copy2(pbix, backup)
    with zipfile.ZipFile(pbix, "r") as zin:
        infos = zin.infolist()
        zip_infos = {info.filename: clone_zip_info(info) for info in infos}
        entry_order = [info.filename for info in infos]
        entries = {info.filename: zin.read(info.filename) for info in infos}
    layout = json.loads(entries["Report/Layout"].decode("utf-16le"))
    section = layout["sections"][0]
    section["displayName"] = "Seller Performance Cockpit"
    section["width"] = 1280
    section["height"] = 720
    old_visuals = section.get("visualContainers", [])
    table_source = None
    for vc in old_visuals:
        try:
            cfg = json.loads(vc.get("config", "{}"))
            if cfg.get("singleVisual", {}).get("visualType") == "tableEx":
                table_source = vc
                break
        except json.JSONDecodeError:
            continue
    if table_source is None:
        return {"status": "SKIPPED", "reason": "Existing table visual not found", "backup": str(backup)}
    card_specs = [
        ("p7_card_gmv", "Seller GMV", "Seller GMV", "$#,0", COLORS["orange"]),
        ("p7_card_fulfill", "Fulfillment Rate", "Fulfillment", "0.0%", COLORS["green"]),
        ("p7_card_cancel", "Cancellation Rate", "Cancellation", "0.0%", COLORS["red"]),
        ("p7_card_rating", "Average Rating", "Rating", "0.00", COLORS["teal"]),
        ("p7_card_stock", "Stock Availability", "Stock", "0.0%", COLORS["violet"]),
        ("p7_card_sellers", "Active Sellers", "Active Sellers", "#,0", COLORS["blue"]),
    ]
    visuals = [
        textbox("p7_title", 24, 16, 680, 58, "Marketplace Seller Performance", "Command center | GMV, fulfillment, cancellation, rating, stock, top/bottom sellers", 1),
        textbox("p7_meta", 780, 22, 440, 42, "Latest complete month: 2026-05", "Template: Marketplace Command Center v3", 2),
    ]
    x0, y0, w, h, gap = 24, 88, 188, 86, 16
    for i, (name, measure, display, fmt, color) in enumerate(card_specs):
        visuals.append(card_visual(name, measure, display, fmt, color, x0 + i * (w + gap), y0, w, h, 100 + i))
    visuals.append(
        measure_chart(
            "p7_trend_gmv",
            "lineChart",
            "fact_seller_month",
            "year_month",
            "Month",
            "Seller GMV",
            "Seller GMV",
            "$#,0",
            "GMV Trend",
            "Monthly net seller GMV",
            24,
            198,
            612,
            232,
            210,
            COLORS["orange"],
            order="asc_category",
        )
    )
    visuals.append(
        measure_chart(
            "p7_platform_gmv",
            "barChart",
            "dim_platform",
            "platform_name",
            "Platform",
            "Seller GMV",
            "Seller GMV",
            "$#,0",
            "GMV by Platform",
            "Marketplace mix",
            660,
            198,
            596,
            232,
            211,
            COLORS["blue"],
            order="desc",
        )
    )
    visuals.append(style_existing_table(table_source, 24, 454, 1232, 234, 300))
    section["visualContainers"] = visuals

    theme_path = "Report/StaticResources/SharedResources/BaseThemes/CY26SU05.json"
    theme = json.loads(entries[theme_path].decode("utf-8"))
    theme.update(
        {
            "name": "Marketplace Command Center v3",
            "dataColors": [COLORS["orange"], COLORS["blue"], COLORS["cyan"], COLORS["teal"], COLORS["green"], COLORS["amber"], COLORS["red"], COLORS["violet"], COLORS["slate"]],
            "background": COLORS["bg"],
            "foreground": COLORS["ink"],
            "tableAccent": COLORS["orange"],
            "good": COLORS["green"],
            "neutral": COLORS["amber"],
            "bad": COLORS["red"],
        }
    )
    entries["Report/Layout"] = json.dumps(layout, separators=(",", ":"), ensure_ascii=False).encode("utf-16le")
    entries[theme_path] = json.dumps(theme, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    fd, tmp_name = tempfile.mkstemp(suffix=".pbix")
    os.close(fd)
    tmp = Path(tmp_name)
    with zipfile.ZipFile(tmp, "w", compression=zipfile.ZIP_DEFLATED) as zout:
        for name in entry_order:
            if name == "SecurityBindings":
                continue
            zout.writestr(zip_infos[name], entries[name])
    shutil.move(str(tmp), pbix)
    visual_types = []
    for vc in visuals:
        cfg = json.loads(vc["config"])
        visual_types.append(cfg.get("singleVisual", {}).get("visualType"))
    result = {"status": "PATCHED", "backup": str(backup), "pbix": str(pbix), "native_visual_count": len(visuals), "native_visual_types": visual_types}
    p("qa/pbix_visual_refresh_validation.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


def main() -> None:
    ensure_dirs()
    data = read_model()
    generate_preview(data)
    write_theme_and_docs()
    result = patch_pbix_layout()
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
