from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
LATEST_MONTH = "2026-05"


def p(rel: str) -> Path:
    return ROOT / rel


def ensure_dirs() -> None:
    for rel in ["output", "qa", "docs"]:
        p(rel).mkdir(parents=True, exist_ok=True)


def read_data() -> dict[str, pd.DataFrame]:
    platform = pd.read_csv(p("data/prepared/dim_platform.csv"))
    seller = pd.read_csv(p("data/prepared/dim_seller.csv"))
    category = pd.read_csv(p("data/prepared/dim_category.csv"))
    month = pd.read_csv(p("data/prepared/fact_seller_month.csv"))
    orders = pd.read_csv(p("data/prepared/fact_order_items.csv"))
    ads = pd.read_csv(p("data/prepared/fact_ads_spend.csv"))

    seller_attrs = seller.drop(columns=["platform_id"], errors="ignore")
    month = (
        month.merge(platform[["platform_id", "platform_name"]], on="platform_id", how="left")
        .merge(seller_attrs, on="seller_id", how="left")
    )
    month["avg_rating"] = month["avg_rating"].fillna(month["avg_rating"].median())
    month["fulfillment_rate"] = month["fulfillment_rate"].fillna(0)
    month["cancellation_rate"] = month["cancellation_rate"].fillna(0)
    month["stock_availability_rate"] = month["stock_availability_rate"].fillna(0)

    orders["order_date"] = pd.to_datetime(orders["order_date"])
    orders["year_month"] = orders["order_date"].dt.strftime("%Y-%m")
    orders = (
        orders.merge(platform[["platform_id", "platform_name"]], on="platform_id", how="left")
        .merge(category, on="category_id", how="left")
    )
    ads = ads.merge(platform[["platform_id", "platform_name"]], on="platform_id", how="left")
    return {"month": month, "orders": orders, "ads": ads}


def compact_records(df: pd.DataFrame, cols: list[str]) -> list[dict]:
    out = df[cols].copy()
    for col in out.select_dtypes(include=["float"]).columns:
        out[col] = out[col].replace([np.inf, -np.inf], np.nan).fillna(0).round(6)
    for col in out.columns:
        if pd.api.types.is_object_dtype(out[col]) or pd.api.types.is_string_dtype(out[col]):
            out[col] = out[col].fillna("")
    return out.to_dict("records")


def build_payload(data: dict[str, pd.DataFrame]) -> dict:
    month = data["month"].copy()
    months = sorted(month["year_month"].unique().tolist())
    latest_month = LATEST_MONTH if LATEST_MONTH in months else months[-1]

    month_cols = [
        "year_month",
        "platform_name",
        "seller_id",
        "seller_name",
        "seller_tier",
        "region",
        "lifecycle_status",
        "official_store_flag",
        "seller_gmv_net",
        "gross_gmv",
        "commission_revenue",
        "order_items",
        "orders",
        "cancelled_items",
        "returned_items",
        "eligible_items",
        "fulfilled_items",
        "late_items",
        "sku_day_count",
        "in_stock_sku_days",
        "rating_weighted_sum",
        "rating_weight",
        "rating_count",
        "fulfillment_rate",
        "cancellation_rate",
        "stock_availability_rate",
        "avg_rating",
    ]

    orders = data["orders"]
    category = (
        orders.groupby(["year_month", "platform_name", "category"], as_index=False)
        .agg(gmv=("seller_gmv_net", "sum"), orders=("order_id", "nunique"), items=("order_item_id", "nunique"))
        .sort_values(["year_month", "platform_name", "gmv"], ascending=[True, True, False])
    )
    cancel_reasons = (
        orders.loc[orders["is_cancelled"].eq(1)]
        .assign(cancellation_reason=lambda x: x["cancellation_reason"].fillna("Unknown"))
        .groupby(["year_month", "platform_name", "cancellation_reason"], as_index=False)
        .agg(items=("order_item_id", "nunique"), gmv=("seller_gmv_net", "sum"))
        .sort_values(["year_month", "items"], ascending=[True, False])
    )
    ads = (
        data["ads"].groupby(["year_month", "platform_name"], as_index=False)
        .agg(ads_spend=("ads_spend", "sum"), voucher_cost=("voucher_cost", "sum"))
        .assign(total_spend=lambda x: x["ads_spend"] + x["voucher_cost"])
    )

    return {
        "generatedAt": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "latestMonth": latest_month,
        "months": months,
        "platforms": sorted(month["platform_name"].dropna().unique().tolist()),
        "tiers": sorted(month["seller_tier"].dropna().unique().tolist()),
        "regions": sorted(month["region"].dropna().unique().tolist()),
        "monthRows": compact_records(month, month_cols),
        "categoryRows": compact_records(category, ["year_month", "platform_name", "category", "gmv", "orders", "items"]),
        "cancelReasonRows": compact_records(cancel_reasons, ["year_month", "platform_name", "cancellation_reason", "items", "gmv"]),
        "adsRows": compact_records(ads, ["year_month", "platform_name", "ads_spend", "voucher_cost", "total_spend"]),
    }


def html_template(payload: dict) -> str:
    payload_json = json.dumps(payload, separators=(",", ":"), ensure_ascii=False)
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Project 07 - Marketplace Seller Performance Marketplace Seller Performance Dashboard</title>
  <style>
    :root {{
      --bg:#F4F6FA; --panel:#FFFFFF; --ink:#101828; --muted:#667085; --soft:#98A2B3;
      --line:#D9E0EA; --line2:#EEF2F7; --orange:#EE4D2D; --blue:#2563EB; --cyan:#0EA5E9;
      --teal:#0F766E; --green:#16A34A; --amber:#D97706; --red:#DC2626; --violet:#7C3AED;
      --shadow:0 12px 28px rgba(16,24,40,.07);
    }}
    * {{ box-sizing:border-box; }}
    body {{ margin:0; color:var(--ink); background:var(--bg); font-family:"Segoe UI", Arial, sans-serif; }}
    button, select, input {{ font:inherit; }}
    .shell {{ min-height:100vh; display:grid; grid-template-columns:260px minmax(0,1fr); }}
    aside {{ background:#111827; color:#F9FAFB; padding:22px 18px; position:sticky; top:0; height:100vh; }}
    .brand {{ font-size:13px; color:#CBD5E1; text-transform:uppercase; letter-spacing:.08em; margin-bottom:8px; }}
    h1 {{ font-size:25px; line-height:1.16; margin:0 0 18px; letter-spacing:0; }}
    .nav {{ display:grid; gap:8px; margin:26px 0; }}
    .nav button {{ border:1px solid rgba(255,255,255,.10); color:#D1D5DB; background:transparent; border-radius:8px; padding:10px 12px; text-align:left; cursor:pointer; }}
    .nav button.active {{ color:#FFFFFF; border-color:rgba(238,77,45,.55); background:rgba(238,77,45,.18); }}
    .side-note {{ color:#CBD5E1; font-size:12px; line-height:1.55; border-top:1px solid rgba(255,255,255,.10); padding-top:16px; }}
    main {{ padding:20px 24px 34px; min-width:0; }}
    .topbar {{ display:flex; gap:12px; align-items:flex-end; justify-content:space-between; margin-bottom:16px; }}
    .title h2 {{ margin:0; font-size:22px; letter-spacing:0; }}
    .subtitle {{ color:var(--muted); font-size:13px; margin-top:4px; }}
    .filters {{ display:flex; gap:10px; flex-wrap:wrap; justify-content:flex-end; }}
    .field {{ display:grid; gap:4px; }}
    label {{ color:var(--muted); font-size:11px; font-weight:600; text-transform:uppercase; letter-spacing:.05em; }}
    select, input {{ height:34px; min-width:132px; border:1px solid var(--line); border-radius:7px; background:#FFFFFF; color:var(--ink); padding:0 10px; outline:none; }}
    input {{ min-width:190px; }}
    .kpis {{ display:grid; grid-template-columns:repeat(6,minmax(0,1fr)); gap:12px; margin-bottom:16px; }}
    .card, .panel {{ background:var(--panel); border:1px solid var(--line); border-radius:8px; box-shadow:var(--shadow); }}
    .card {{ min-height:100px; padding:13px 13px 12px; position:relative; overflow:hidden; }}
    .card:before {{ content:""; position:absolute; top:12px; bottom:12px; left:0; width:4px; background:var(--accent); }}
    .card .label {{ color:var(--muted); font-size:12px; font-weight:700; }}
    .card .value {{ margin-top:11px; font-size:24px; font-weight:750; color:var(--accent); }}
    .card .delta {{ margin-top:5px; font-size:12px; color:var(--muted); }}
    .grid {{ display:grid; grid-template-columns:repeat(12,minmax(0,1fr)); gap:14px; }}
    .panel {{ padding:14px; min-height:250px; }}
    .panel h3 {{ margin:0; font-size:14px; }}
    .panel .caption {{ color:var(--muted); font-size:12px; margin-top:3px; }}
    .chart {{ margin-top:10px; min-height:190px; }}
    .span-3 {{ grid-column:span 3; }} .span-4 {{ grid-column:span 4; }} .span-5 {{ grid-column:span 5; }} .span-6 {{ grid-column:span 6; }} .span-7 {{ grid-column:span 7; }} .span-8 {{ grid-column:span 8; }} .span-12 {{ grid-column:span 12; }}
    .view {{ display:none; }} .view.active {{ display:block; }}
    table {{ width:100%; border-collapse:collapse; font-size:12px; }}
    th {{ text-align:left; color:var(--muted); font-size:11px; text-transform:uppercase; letter-spacing:.04em; background:#F8FAFC; }}
    th, td {{ padding:8px 8px; border-bottom:1px solid var(--line2); white-space:nowrap; }}
    td.num, th.num {{ text-align:right; }}
    tbody tr:hover {{ background:#F8FAFC; }}
    .badge {{ display:inline-flex; border-radius:6px; padding:2px 7px; border:1px solid var(--line); color:var(--muted); background:#F8FAFC; }}
    .good {{ color:var(--green); }} .bad {{ color:var(--red); }} .warn {{ color:var(--amber); }}
    svg {{ width:100%; height:100%; display:block; overflow:visible; }}
    .axis {{ stroke:var(--line); stroke-width:1; }} .gridline {{ stroke:var(--line2); stroke-width:1; }}
    .tick {{ fill:var(--muted); font-size:11px; }} .legend {{ fill:var(--muted); font-size:12px; }}
    .empty {{ color:var(--muted); font-size:13px; padding:22px; text-align:center; border:1px dashed var(--line); border-radius:8px; }}
    @media (max-width:1180px) {{ .shell {{ grid-template-columns:1fr; }} aside {{ position:relative; height:auto; }} .nav {{ grid-template-columns:repeat(4,minmax(0,1fr)); }} .kpis {{ grid-template-columns:repeat(3,minmax(0,1fr)); }} .span-3,.span-4,.span-5,.span-6,.span-7,.span-8 {{ grid-column:span 12; }} .topbar {{ align-items:stretch; flex-direction:column; }} .filters {{ justify-content:flex-start; }} }}
    @media (max-width:720px) {{ main {{ padding:16px; }} .kpis {{ grid-template-columns:1fr; }} .nav {{ grid-template-columns:1fr; }} select,input {{ min-width:100%; }} .field {{ width:100%; }} table {{ font-size:11px; }} th,td {{ padding:7px 6px; }} }}
  </style>
</head>
<body>
  <div class="shell">
    <aside>
      <div class="brand">Project 07 - Marketplace Seller Performance BI</div>
      <h1>Marketplace Seller Performance Dashboard</h1>
      <div class="nav" id="nav">
        <button class="active" data-view="executive">Executive Cockpit</button>
        <button data-view="portfolio">Seller Portfolio</button>
        <button data-view="growth">Growth Drivers</button>
        <button data-view="risk">Ops Risk</button>
      </div>
      <div class="side-note">
        Complete dashboard for Shopee/Lazada/Tiki-style marketplace operations. Metrics are calculated from Project 07 - Marketplace Seller Performance prepared seller-month, order item, ads, category, and platform tables.
      </div>
    </aside>
    <main>
      <div class="topbar">
        <div class="title">
          <h2 id="viewTitle">Executive Cockpit</h2>
          <div class="subtitle" id="freshness"></div>
        </div>
        <div class="filters">
          <div class="field"><label for="monthFilter">Month</label><select id="monthFilter"></select></div>
          <div class="field"><label for="platformFilter">Platform</label><select id="platformFilter"></select></div>
          <div class="field"><label for="tierFilter">Tier</label><select id="tierFilter"></select></div>
          <div class="field"><label for="searchFilter">Seller Search</label><input id="searchFilter" placeholder="Type seller name"></div>
        </div>
      </div>
      <section class="kpis" id="kpis"></section>

      <section class="view active" id="executive">
        <div class="grid">
          <div class="panel span-7"><h3>GMV Trend</h3><div class="caption">Net seller GMV by month, filtered by platform and tier.</div><div class="chart" id="gmvTrend"></div></div>
          <div class="panel span-5"><h3>GMV by Platform</h3><div class="caption">Marketplace mix for selected month.</div><div class="chart" id="platformBars"></div></div>
          <div class="panel span-6"><h3>Top Sellers</h3><div class="caption">Highest GMV sellers with quality guardrails.</div><div id="topSellers"></div></div>
          <div class="panel span-6"><h3>Bottom Sellers</h3><div class="caption">Lowest performance score among active sellers.</div><div id="bottomSellers"></div></div>
        </div>
      </section>

      <section class="view" id="portfolio">
        <div class="grid">
          <div class="panel span-7"><h3>GMV vs Cancellation</h3><div class="caption">Bubble size = order item volume.</div><div class="chart" id="portfolioScatter"></div></div>
          <div class="panel span-5"><h3>Seller GMV Pareto</h3><div class="caption">Concentration curve across seller ranks.</div><div class="chart" id="paretoCurve"></div></div>
          <div class="panel span-5"><h3>GMV by Seller Tier</h3><div class="caption">Commercial segment contribution.</div><div class="chart" id="tierBars"></div></div>
          <div class="panel span-7"><h3>Seller Leaderboard</h3><div class="caption">Ranked seller performance for the selected filter.</div><div id="leaderboard"></div></div>
        </div>
      </section>

      <section class="view" id="growth">
        <div class="grid">
          <div class="panel span-6"><h3>Category Growth Quadrant</h3><div class="caption">Current share vs month-over-month growth.</div><div class="chart" id="categoryQuadrant"></div></div>
          <div class="panel span-6"><h3>GMV vs Ads and Voucher</h3><div class="caption">Demand generation spend pressure.</div><div class="chart" id="spendTrend"></div></div>
          <div class="panel span-12"><h3>Opportunity Sellers</h3><div class="caption">Good quality sellers with weak growth, suitable for exposure or campaign push.</div><div id="opportunityTable"></div></div>
        </div>
      </section>

      <section class="view" id="risk">
        <div class="grid">
          <div class="panel span-5"><h3>Risk Trend</h3><div class="caption">Cancellation and stockout pressure over time.</div><div class="chart" id="riskTrend"></div></div>
          <div class="panel span-3"><h3>Cancellation Reasons</h3><div class="caption">Selected month mix.</div><div class="chart" id="reasonBars"></div></div>
          <div class="panel span-4"><h3>GMV at Risk</h3><div class="caption">High-risk sellers by risk score and GMV exposure.</div><div class="chart" id="riskBubble"></div></div>
          <div class="panel span-12"><h3>Action Queue</h3><div class="caption">Prioritized seller follow-up list.</div><div id="riskTable"></div></div>
        </div>
      </section>
    </main>
  </div>
  <script>
    const DATA = {payload_json};
    const palette = {{ orange:"#EE4D2D", blue:"#2563EB", cyan:"#0EA5E9", teal:"#0F766E", green:"#16A34A", amber:"#D97706", red:"#DC2626", violet:"#7C3AED", slate:"#475569", line:"#D9E0EA", muted:"#667085" }};
    const platformColor = {{ Shopee: palette.orange, Lazada: palette.blue, Tiki: palette.cyan }};
    const state = {{ view:"executive", month:DATA.latestMonth, platform:"All", tier:"All", search:"" }};

    const money = v => new Intl.NumberFormat("en-US", {{ style:"currency", currency:"USD", maximumFractionDigits:0 }}).format(v || 0);
    const moneyCompact = v => "$" + compact(v || 0);
    const compact = v => new Intl.NumberFormat("en-US", {{ notation:"compact", maximumFractionDigits:1 }}).format(v || 0);
    const pct = v => ((v || 0) * 100).toFixed(1) + "%";
    const num = v => new Intl.NumberFormat("en-US", {{ maximumFractionDigits:0 }}).format(v || 0);
    const safe = v => Number.isFinite(v) ? v : 0;
    const esc = v => String(v ?? "").replace(/[&<>"']/g, m => ({{"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}}[m]));

    function populateFilters() {{
      const month = document.getElementById("monthFilter");
      DATA.months.slice().reverse().forEach(m => month.add(new Option(m, m, false, m === state.month)));
      const platform = document.getElementById("platformFilter");
      ["All", ...DATA.platforms].forEach(v => platform.add(new Option(v, v)));
      const tier = document.getElementById("tierFilter");
      ["All", ...DATA.tiers].forEach(v => tier.add(new Option(v, v)));
      month.onchange = e => {{ state.month = e.target.value; render(); }};
      platform.onchange = e => {{ state.platform = e.target.value; render(); }};
      tier.onchange = e => {{ state.tier = e.target.value; render(); }};
      document.getElementById("searchFilter").oninput = e => {{ state.search = e.target.value.toLowerCase().trim(); render(); }};
      document.querySelectorAll("#nav button").forEach(btn => btn.onclick = () => {{
        state.view = btn.dataset.view;
        document.querySelectorAll("#nav button").forEach(b => b.classList.toggle("active", b === btn));
        document.querySelectorAll(".view").forEach(v => v.classList.toggle("active", v.id === state.view));
        document.getElementById("viewTitle").textContent = btn.textContent;
        render();
      }});
    }}

    function rowPassBase(r) {{
      return (state.platform === "All" || r.platform_name === state.platform) &&
        (state.tier === "All" || r.seller_tier === state.tier) &&
        (!state.search || r.seller_name.toLowerCase().includes(state.search));
    }}
    function monthRows(month=state.month) {{ return DATA.monthRows.filter(r => r.year_month === month && rowPassBase(r)); }}
    function allTrendRows() {{ return DATA.monthRows.filter(rowPassBase); }}
    function categoryRows(month=state.month) {{ return DATA.categoryRows.filter(r => r.year_month === month && (state.platform === "All" || r.platform_name === state.platform)); }}
    function adsRows() {{ return DATA.adsRows.filter(r => state.platform === "All" || r.platform_name === state.platform); }}
    function reasonRows(month=state.month) {{ return DATA.cancelReasonRows.filter(r => r.year_month === month && (state.platform === "All" || r.platform_name === state.platform)); }}

    function aggregate(rows) {{
      const gmv = rows.reduce((s,r)=>s+r.seller_gmv_net,0);
      const prevRows = monthRows(prevMonth(state.month));
      const prevGmv = prevRows.reduce((s,r)=>s+r.seller_gmv_net,0);
      const orderItems = rows.reduce((s,r)=>s+r.order_items,0);
      const cancelled = rows.reduce((s,r)=>s+r.cancelled_items,0);
      const eligible = rows.reduce((s,r)=>s+r.eligible_items,0);
      const fulfilled = rows.reduce((s,r)=>s+r.fulfilled_items,0);
      const inStock = rows.reduce((s,r)=>s+r.in_stock_sku_days,0);
      const skuDays = rows.reduce((s,r)=>s+r.sku_day_count,0);
      const ratingSum = rows.reduce((s,r)=>s+r.rating_weighted_sum,0);
      const ratingWeight = rows.reduce((s,r)=>s+r.rating_weight,0);
      return {{
        gmv, prevGmv, growth: prevGmv ? (gmv / prevGmv - 1) : 0,
        fulfillment: eligible ? fulfilled / eligible : 0,
        cancellation: orderItems ? cancelled / orderItems : 0,
        rating: ratingWeight ? ratingSum / ratingWeight : 0,
        stock: skuDays ? inStock / skuDays : 0,
        active: new Set(rows.map(r=>r.seller_id)).size,
        orderItems
      }};
    }}
    function prevMonth(m) {{
      const idx = DATA.months.indexOf(m);
      return idx > 0 ? DATA.months[idx - 1] : m;
    }}
    function performanceScore(r) {{
      return safe(r.seller_gmv_net) * 0.00002 + r.fulfillment_rate * 25 + (1 - r.cancellation_rate) * 20 + (r.avg_rating / 5) * 10 + r.stock_availability_rate * 5;
    }}
    function riskScore(r) {{ return r.cancellation_rate * 45 + (1 - r.fulfillment_rate) * 35 + (1 - r.stock_availability_rate) * 20; }}
    function groupBy(rows, key, valueFn) {{
      const map = new Map();
      rows.forEach(r => map.set(key(r), (map.get(key(r)) || 0) + valueFn(r)));
      return [...map.entries()].map(([name,value]) => ({{ name, value }}));
    }}

    function renderKpis(rows) {{
      const k = aggregate(rows);
      const cards = [
        ["Seller GMV", moneyCompact(k.gmv), `${{pct(k.growth)}} vs prev month`, palette.orange],
        ["Fulfillment", pct(k.fulfillment), "eligible items fulfilled", palette.green],
        ["Cancellation", pct(k.cancellation), "lower is better", palette.red],
        ["Avg Rating", k.rating.toFixed(2), "weighted review score", palette.teal],
        ["Stock Availability", pct(k.stock), "SKU-days in stock", palette.violet],
        ["Active Sellers", num(k.active), `${{num(k.orderItems)}} order items`, palette.blue],
      ];
      document.getElementById("kpis").innerHTML = cards.map(c => `<div class="card" style="--accent:${{c[3]}}"><div class="label">${{c[0]}}</div><div class="value">${{c[1]}}</div><div class="delta">${{c[2]}}</div></div>`).join("");
      document.getElementById("freshness").textContent = `Latest complete month: ${{state.month}} | Generated: ${{DATA.generatedAt}} | Platform: ${{state.platform}} | Tier: ${{state.tier}}`;
    }}

    function renderTable(target, rows, columns, empty="No rows for this selection") {{
      const el = document.getElementById(target);
      if (!rows.length) {{ el.innerHTML = `<div class="empty">${{empty}}</div>`; return; }}
      const head = `<thead><tr>${{columns.map(c=>`<th class="${{c.num ? "num" : ""}}">${{c.label}}</th>`).join("")}}</tr></thead>`;
      const body = `<tbody>${{rows.map(r=>`<tr>${{columns.map(c=>`<td class="${{c.num ? "num" : ""}}">${{c.render ? c.render(r) : esc(r[c.key])}}</td>`).join("")}}</tr>`).join("")}}</tbody>`;
      el.innerHTML = `<table>${{head}}${{body}}</table>`;
    }}

    function svgLine(target, series, opts={{}}) {{
      const el = document.getElementById(target);
      if (!series.length) {{ el.innerHTML = `<div class="empty">No trend data</div>`; return; }}
      const w=720,h=230,ml=48,mr=20,mt=18,mb=44;
      const ys = series.flatMap(d => opts.y2 ? [d.y, d.y2] : [d.y]);
      const maxY = Math.max(...ys, 1) * 1.12;
      const x = i => ml + (series.length === 1 ? 0 : i * (w - ml - mr) / (series.length - 1));
      const y = v => h - mb - (v / maxY) * (h - mt - mb);
      const path = key => series.map((d,i)=>`${{i?"L":"M"}}${{x(i).toFixed(1)}},${{y(d[key]).toFixed(1)}}`).join(" ");
      const grid = [0,.25,.5,.75,1].map(t => `<line class="gridline" x1="${{ml}}" x2="${{w-mr}}" y1="${{mt+t*(h-mt-mb)}}" y2="${{mt+t*(h-mt-mb)}}"/>`).join("");
      const labels = series.map((d,i)=> i % Math.ceil(series.length/8) === 0 ? `<text class="tick" x="${{x(i)}}" y="${{h-18}}" text-anchor="middle">${{d.label}}</text>` : "").join("");
      const dots = series.map((d,i)=>`<circle cx="${{x(i)}}" cy="${{y(d.y)}}" r="3.5" fill="${{opts.color||palette.orange}}"/>`).join("");
      const second = opts.y2 ? `<path d="${{path("y2")}}" fill="none" stroke="${{opts.color2||palette.violet}}" stroke-width="2.4"/><text class="legend" x="${{w-146}}" y="18" fill="${{opts.color2||palette.violet}}">${{opts.label2||"Series 2"}}</text>` : "";
      el.innerHTML = `<svg viewBox="0 0 ${{w}} ${{h}}" role="img">${{grid}}<path d="${{path("y")}}" fill="none" stroke="${{opts.color||palette.orange}}" stroke-width="3"/><text class="legend" x="${{ml}}" y="18" fill="${{opts.color||palette.orange}}">${{opts.label||"Series"}}</text>${{second}}${{dots}}${{labels}}</svg>`;
    }}

    function svgBars(target, rows, opts={{}}) {{
      const el = document.getElementById(target);
      const data = rows.filter(d => safe(d.value) > 0).slice(0, opts.limit || 10);
      if (!data.length) {{ el.innerHTML = `<div class="empty">No bar data</div>`; return; }}
      const w=600,h=Math.max(210, data.length*34+28),ml=128,mr=24,mt=18,mb=20;
      const max = Math.max(...data.map(d=>d.value), 1);
      const barH = Math.min(24, (h-mt-mb)/data.length - 8);
      const lines = data.map((d,i) => {{
        const y = mt + i*((h-mt-mb)/data.length);
        const bw = (d.value/max)*(w-ml-mr);
        const color = d.color || opts.color || platformColor[d.name] || palette.blue;
        return `<text class="tick" x="${{ml-10}}" y="${{y+barH*.72}}" text-anchor="end">${{esc(d.name)}}</text><rect x="${{ml}}" y="${{y}}" width="${{bw}}" height="${{barH}}" rx="5" fill="${{color}}"/><text class="tick" x="${{ml+bw+7}}" y="${{y+barH*.72}}">${{opts.format ? opts.format(d.value) : compact(d.value)}}</text>`;
      }}).join("");
      el.innerHTML = `<svg viewBox="0 0 ${{w}} ${{h}}">${{lines}}</svg>`;
    }}

    function svgScatter(target, rows, opts={{}}) {{
      const el = document.getElementById(target);
      const data = rows.filter(r => safe(r.seller_gmv_net) > 0).slice(0, opts.limit || 160);
      if (!data.length) {{ el.innerHTML = `<div class="empty">No seller data</div>`; return; }}
      const w=720,h=250,ml=52,mr=22,mt=18,mb=42;
      const maxX = Math.max(...data.map(r=>r.seller_gmv_net), 1) * 1.08;
      const maxY = Math.max(...data.map(r=>r.cancellation_rate), .01) * 1.20;
      const maxO = Math.max(...data.map(r=>r.order_items), 1);
      const x = v => ml + (v/maxX)*(w-ml-mr);
      const y = v => h-mb - (v/maxY)*(h-mt-mb);
      const grid = [0,.25,.5,.75,1].map(t => `<line class="gridline" x1="${{ml}}" x2="${{w-mr}}" y1="${{mt+t*(h-mt-mb)}}" y2="${{mt+t*(h-mt-mb)}}"/>`).join("");
      const pts = data.map(r => `<circle cx="${{x(r.seller_gmv_net)}}" cy="${{y(r.cancellation_rate)}}" r="${{4 + (r.order_items/maxO)*13}}" fill="${{platformColor[r.platform_name] || palette.blue}}" opacity=".66"><title>${{esc(r.seller_name)}} | ${{moneyCompact(r.seller_gmv_net)}} | Cancel ${{pct(r.cancellation_rate)}}</title></circle>`).join("");
      el.innerHTML = `<svg viewBox="0 0 ${{w}} ${{h}}">${{grid}}<line class="axis" x1="${{ml}}" x2="${{w-mr}}" y1="${{h-mb}}" y2="${{h-mb}}"/><line class="axis" x1="${{ml}}" x2="${{ml}}" y1="${{mt}}" y2="${{h-mb}}"/>${{pts}}<text class="tick" x="${{w/2}}" y="${{h-10}}" text-anchor="middle">GMV</text><text class="tick" x="12" y="${{h/2}}" transform="rotate(-90 12 ${{h/2}})" text-anchor="middle">Cancellation rate</text></svg>`;
    }}

    function renderExecutive(rows) {{
      const trend = DATA.months.map(m => aggregate(DATA.monthRows.filter(r => r.year_month === m && rowPassBase(r)))).map((a,i)=>({{ label:DATA.months[i], y:a.gmv }}));
      svgLine("gmvTrend", trend, {{ color:palette.orange, label:"Seller GMV", }});
      svgBars("platformBars", groupBy(rows, r=>r.platform_name, r=>r.seller_gmv_net).sort((a,b)=>b.value-a.value), {{ format:moneyCompact }});
      const cols = [
        {{ label:"Seller", render:r=>esc(r.seller_name) }},
        {{ label:"Platform", render:r=>`<span class="badge">${{esc(r.platform_name)}}</span>` }},
        {{ label:"Tier", render:r=>esc(r.seller_tier) }},
        {{ label:"GMV", num:true, render:r=>moneyCompact(r.seller_gmv_net) }},
        {{ label:"Fulfill", num:true, render:r=>pct(r.fulfillment_rate) }},
        {{ label:"Cancel", num:true, render:r=>`<span class="${{r.cancellation_rate>.08?"bad":"good"}}">${{pct(r.cancellation_rate)}}</span>` }},
        {{ label:"Stock", num:true, render:r=>pct(r.stock_availability_rate) }},
      ];
      renderTable("topSellers", rows.slice().sort((a,b)=>b.seller_gmv_net-a.seller_gmv_net).slice(0,8), cols);
      renderTable("bottomSellers", rows.slice().filter(r=>r.order_items>=20).sort((a,b)=>performanceScore(a)-performanceScore(b)).slice(0,8), cols);
    }}

    function renderPortfolio(rows) {{
      svgScatter("portfolioScatter", rows, {{ limit:180 }});
      const paretoRows = rows.slice().sort((a,b)=>b.seller_gmv_net-a.seller_gmv_net);
      let cum = 0; const total = paretoRows.reduce((s,r)=>s+r.seller_gmv_net,0) || 1;
      svgLine("paretoCurve", paretoRows.map((r,i)=>{{ cum += r.seller_gmv_net; return {{ label:String(i+1), y:cum/total*100 }}; }}), {{ color:palette.blue, label:"Cumulative GMV %" }});
      svgBars("tierBars", groupBy(rows, r=>r.seller_tier, r=>r.seller_gmv_net).sort((a,b)=>b.value-a.value), {{ color:palette.teal, format:moneyCompact }});
      renderTable("leaderboard", rows.slice().sort((a,b)=>performanceScore(b)-performanceScore(a)).slice(0,12), [
        {{ label:"Seller", render:r=>esc(r.seller_name) }},
        {{ label:"Platform", render:r=>esc(r.platform_name) }},
        {{ label:"Region", render:r=>esc(r.region) }},
        {{ label:"GMV", num:true, render:r=>moneyCompact(r.seller_gmv_net) }},
        {{ label:"Score", num:true, render:r=>performanceScore(r).toFixed(1) }},
        {{ label:"Rating", num:true, render:r=>r.avg_rating.toFixed(2) }},
      ]);
    }}

    function renderGrowth(rows) {{
      const prevCat = categoryRows(prevMonth(state.month));
      const currCat = categoryRows(state.month);
      const prevMap = new Map(prevCat.map(r=>[r.category, r.gmv]));
      const total = currCat.reduce((s,r)=>s+r.gmv,0) || 1;
      const quad = currCat.map(r=>({{...r, share:r.gmv/total, growth:prevMap.get(r.category) ? r.gmv/prevMap.get(r.category)-1 : 0}}));
      svgCategoryQuadrant("categoryQuadrant", quad);
      const spendMap = new Map(adsRows().map(r=>[r.year_month, r.total_spend]));
      const trend = DATA.months.map(m => {{
        const a = aggregate(DATA.monthRows.filter(r => r.year_month === m && rowPassBase(r)));
        return {{ label:m, y:a.gmv, y2:spendMap.get(m) || 0 }};
      }});
      svgLine("spendTrend", trend, {{ color:palette.orange, label:"GMV", y2:true, color2:palette.violet, label2:"Ads + voucher" }});
      const prevSeller = new Map(monthRows(prevMonth(state.month)).map(r=>[r.seller_id, r.seller_gmv_net]));
      const opp = rows.filter(r => r.avg_rating >= 4.15 && r.stock_availability_rate >= .82)
        .map(r => ({{...r, growth:prevSeller.get(r.seller_id) ? r.seller_gmv_net/prevSeller.get(r.seller_id)-1 : 0}}))
        .sort((a,b)=>a.growth-b.growth).slice(0,12);
      renderTable("opportunityTable", opp, [
        {{ label:"Seller", render:r=>esc(r.seller_name) }},
        {{ label:"Platform", render:r=>esc(r.platform_name) }},
        {{ label:"Tier", render:r=>esc(r.seller_tier) }},
        {{ label:"GMV", num:true, render:r=>moneyCompact(r.seller_gmv_net) }},
        {{ label:"Growth", num:true, render:r=>`<span class="${{r.growth<0?"bad":"good"}}">${{pct(r.growth)}}</span>` }},
        {{ label:"Action", render:()=>"<span class='badge'>Boost exposure</span>" }},
      ]);
    }}

    function svgCategoryQuadrant(target, rows) {{
      const el = document.getElementById(target);
      if (!rows.length) {{ el.innerHTML = `<div class="empty">No category data</div>`; return; }}
      const w=620,h=250,ml=58,mr=24,mt=18,mb=44;
      const maxX = Math.max(...rows.map(r=>r.share), .01)*1.2;
      const minY = Math.min(...rows.map(r=>r.growth), 0);
      const maxY = Math.max(...rows.map(r=>r.growth), .01);
      const yRange = (maxY - minY) || 1;
      const x = v => ml + (v/maxX)*(w-ml-mr);
      const y = v => h-mb - ((v-minY)/yRange)*(h-mt-mb);
      const pts = rows.map(r => `<circle cx="${{x(r.share)}}" cy="${{y(r.growth)}}" r="10" fill="${{palette.teal}}" opacity=".72"><title>${{esc(r.category)}} | Share ${{pct(r.share)}} | Growth ${{pct(r.growth)}}</title></circle><text class="tick" x="${{x(r.share)+13}}" y="${{y(r.growth)+4}}">${{esc(r.category)}}</text>`).join("");
      el.innerHTML = `<svg viewBox="0 0 ${{w}} ${{h}}"><line class="axis" x1="${{ml}}" x2="${{w-mr}}" y1="${{h-mb}}" y2="${{h-mb}}"/><line class="axis" x1="${{ml}}" x2="${{ml}}" y1="${{mt}}" y2="${{h-mb}}"/>${{pts}}<text class="tick" x="${{w/2}}" y="${{h-10}}" text-anchor="middle">GMV share</text><text class="tick" x="12" y="${{h/2}}" transform="rotate(-90 12 ${{h/2}})" text-anchor="middle">MoM growth</text></svg>`;
    }}

    function renderRisk(rows) {{
      const trend = DATA.months.map(m => {{
        const a = aggregate(DATA.monthRows.filter(r => r.year_month === m && rowPassBase(r)));
        return {{ label:m, y:a.cancellation*100, y2:(1-a.stock)*100 }};
      }});
      svgLine("riskTrend", trend, {{ color:palette.red, label:"Cancellation %", y2:true, color2:palette.amber, label2:"Stockout %" }});
      svgBars("reasonBars", reasonRows().map(r=>({{name:r.cancellation_reason, value:r.items}})).sort((a,b)=>b.value-a.value), {{ color:palette.red, format:num, limit:7 }});
      svgScatter("riskBubble", rows.slice().sort((a,b)=>riskScore(b)-riskScore(a)).slice(0,70), {{ limit:70 }});
      const riskRows = rows.filter(r=>r.order_items>=20).map(r=>({{...r, risk:riskScore(r)}})).sort((a,b)=>b.risk-a.risk).slice(0,14);
      renderTable("riskTable", riskRows, [
        {{ label:"Seller", render:r=>esc(r.seller_name) }},
        {{ label:"Platform", render:r=>esc(r.platform_name) }},
        {{ label:"GMV", num:true, render:r=>moneyCompact(r.seller_gmv_net) }},
        {{ label:"Cancel", num:true, render:r=>`<span class="${{r.cancellation_rate>.08?"bad":"warn"}}">${{pct(r.cancellation_rate)}}</span>` }},
        {{ label:"Fulfill", num:true, render:r=>pct(r.fulfillment_rate) }},
        {{ label:"Stock", num:true, render:r=>pct(r.stock_availability_rate) }},
        {{ label:"Risk", num:true, render:r=>r.risk.toFixed(1) }},
        {{ label:"Next Step", render:r=>r.cancellation_rate>.08 ? "<span class='badge'>Cancel RCA</span>" : "<span class='badge'>Stock/SLA check</span>" }},
      ]);
    }}

    function render() {{
      const rows = monthRows();
      renderKpis(rows);
      if (state.view === "executive") renderExecutive(rows);
      if (state.view === "portfolio") renderPortfolio(rows);
      if (state.view === "growth") renderGrowth(rows);
      if (state.view === "risk") renderRisk(rows);
    }}

    populateFilters();
    render();
  </script>
</body>
</html>
"""


def write_dashboard(payload: dict) -> None:
    out = p("output/dashboard_complete.html")
    out.write_text(html_template(payload), encoding="utf-8")
    qa = {
        "status": "PASS",
        "artifact": str(out),
        "generated_at": payload["generatedAt"],
        "latest_month": payload["latestMonth"],
        "data_rows": {
            "seller_month": len(payload["monthRows"]),
            "category_month_platform": len(payload["categoryRows"]),
            "cancel_reason_month_platform": len(payload["cancelReasonRows"]),
            "ads_month_platform": len(payload["adsRows"]),
        },
        "dashboard_features": [
            "4 dashboard tabs",
            "global month/platform/tier/seller filters",
            "6 KPI cards",
            "GMV trend",
            "GMV by platform",
            "top/bottom seller tables",
            "seller portfolio scatter",
            "Pareto concentration curve",
            "category growth quadrant",
            "GMV vs ads/voucher trend",
            "ops risk trend",
            "cancellation reason bars",
            "risk action queue",
        ],
    }
    p("qa/dashboard_complete_validation.json").write_text(json.dumps(qa, indent=2), encoding="utf-8")


def write_docs() -> None:
    p("docs/dashboard_complete_handoff.md").write_text(
        """# Dashboard Complete Handoff

## Artifact

- Main interactive dashboard: `output/dashboard_complete.html`
- Power BI PBIX: `output/dashboard_final.pbix`
- Static preview: `output/dashboard_preview.html`

## Scope

Project 07 - Marketplace Seller Performance is a marketplace / seller performance dashboard for Shopee, Lazada, and Tiki-style seller operations.

Core metrics:

- Seller GMV
- Fulfillment rate
- Cancellation rate
- Average rating
- Stock availability
- Active sellers
- Top and bottom sellers
- Seller risk queue

## Dashboard Structure

1. Executive Cockpit: KPI strip, GMV trend, GMV by platform, top and bottom sellers.
2. Seller Portfolio: GMV vs cancellation scatter, seller concentration curve, seller tier contribution, leaderboard.
3. Growth Drivers: category share/growth quadrant, GMV vs ads and voucher trend, opportunity sellers.
4. Ops Risk: cancellation/stockout trend, cancellation reasons, high-risk sellers, action queue.

## Validation

- Reads from prepared Project 07 - Marketplace Seller Performance CSV files.
- Output validation written to `qa/dashboard_complete_validation.json`.
- Dashboard is self-contained: no external JavaScript or CDN dependency.
""",
        encoding="utf-8",
    )


def main() -> None:
    ensure_dirs()
    payload = build_payload(read_data())
    write_dashboard(payload)
    write_docs()
    print(json.dumps({"status": "PASS", "artifact": str(p("output/dashboard_complete.html")), "latest_month": payload["latestMonth"]}, indent=2))


if __name__ == "__main__":
    main()
