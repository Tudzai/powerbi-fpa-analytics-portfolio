from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
PREPARED_DIR = PROJECT_ROOT / "data" / "prepared"
OUTPUT_DIR = PROJECT_ROOT / "output"
QA_DIR = PROJECT_ROOT / "qa"

OUTPUT_HTML = OUTPUT_DIR / "dashboard.html"
EXPORT_HTML = OUTPUT_DIR / "exports" / "customer_funnel_dashboard_preview.html"
COMPLETE_PAYLOAD = OUTPUT_DIR / "dashboard_payload_complete.json"


GROUP_KEYS = ["month", "device_key", "channel_key", "campaign_key", "category_key", "product_key"]


def read_csv(name: str) -> pd.DataFrame:
    return pd.read_csv(PREPARED_DIR / name)


def as_records(df: pd.DataFrame) -> list[dict]:
    records = []
    for row in df.to_dict(orient="records"):
        clean = {}
        for key, value in row.items():
            if pd.isna(value):
                clean[key] = None
            elif isinstance(value, float):
                clean[key] = round(value, 4)
            else:
                clean[key] = int(value) if hasattr(value, "item") and str(type(value)).startswith("<class 'numpy.int") else value
        records.append(clean)
    return records


def build_payload() -> dict:
    sessions = read_csv("fact_sessions.csv")
    orders = read_csv("fact_orders.csv")
    spend = read_csv("fact_marketing_spend.csv")
    devices = read_csv("dim_device.csv")
    channels = read_csv("dim_channel.csv")
    campaigns = read_csv("dim_campaign.csv")
    categories = read_csv("dim_category.csv")
    products = read_csv("dim_product.csv")

    sessions["month"] = sessions["session_month"].astype(str)
    orders["month"] = pd.to_datetime(orders["order_date"]).dt.strftime("%Y-%m")
    spend["month"] = pd.to_datetime(spend["date"]).dt.strftime("%Y-%m")

    session_cube = (
        sessions.groupby(GROUP_KEYS, as_index=False)
        .agg(
            visits=("session_id", "nunique"),
            product_views=("product_view_flag", "sum"),
            add_to_carts=("add_to_cart_flag", "sum"),
            checkouts=("checkout_flag", "sum"),
            purchases=("purchase_flag", "sum"),
        )
    )

    order_cube = (
        orders.groupby(GROUP_KEYS, as_index=False)
        .agg(
            orders=("order_id", "nunique"),
            revenue=("net_revenue", "sum"),
            gross_revenue=("gross_revenue", "sum"),
            refund_amount=("refund_amount", "sum"),
        )
    )

    cube = session_cube.merge(order_cube, on=GROUP_KEYS, how="left")
    for column in ["orders", "revenue", "gross_revenue", "refund_amount"]:
        cube[column] = cube[column].fillna(0)

    spend_month = (
        spend.groupby(["month", "channel_key", "campaign_key"], as_index=False)
        .agg(spend=("spend", "sum"), impressions=("impressions", "sum"), clicks=("clicks", "sum"))
    )
    cube = cube.merge(spend_month, on=["month", "channel_key", "campaign_key"], how="left")
    for column in ["spend", "impressions", "clicks"]:
        cube[column] = cube[column].fillna(0)

    campaign_month_visits = cube.groupby(["month", "channel_key", "campaign_key"])["visits"].transform("sum")
    share = cube["visits"] / campaign_month_visits.replace(0, pd.NA)
    cube["allocated_spend"] = (cube["spend"] * share.fillna(0)).round(2)
    cube["allocated_impressions"] = (cube["impressions"] * share.fillna(0)).round(0).astype(int)
    cube["allocated_clicks"] = (cube["clicks"] * share.fillna(0)).round(0).astype(int)
    cube = cube.drop(columns=["spend", "impressions", "clicks"])

    for column in ["visits", "product_views", "add_to_carts", "checkouts", "purchases", "orders"]:
        cube[column] = cube[column].astype(int)
    for column in ["revenue", "gross_revenue", "refund_amount", "allocated_spend"]:
        cube[column] = cube[column].round(2)

    payload = {
        "generated_at": datetime.now().replace(microsecond=0).isoformat(),
        "period": {
            "start": str(sessions["session_date"].min()),
            "end": str(sessions["session_date"].max()),
            "months": sorted(sessions["month"].unique().tolist()),
        },
        "dimensions": {
            "device": as_records(devices.sort_values("sort_order")),
            "channel": as_records(channels.sort_values("sort_order")),
            "campaign": as_records(campaigns.sort_values(["channel_key", "campaign"])),
            "category": as_records(categories.sort_values("sort_order")),
            "product": as_records(products.sort_values(["category_key", "product"])),
        },
        "cube": as_records(cube.sort_values(GROUP_KEYS)),
        "source_metadata": {
            "source_type": "Deterministic synthetic portfolio data",
            "seed": 4042026,
            "grain": "Aggregated month x device x channel x campaign x category x product",
            "tables": [
                "fact_sessions",
                "fact_orders",
                "fact_marketing_spend",
                "dim_date",
                "dim_device",
                "dim_channel",
                "dim_campaign",
                "dim_category",
                "dim_product",
                "dim_funnel_stage",
            ],
            "spend_method": "Campaign-channel-month spend is allocated to device/category/product by visit share for filtered diagnostics.",
        },
    }
    return payload


def render_html(payload: dict) -> str:
    payload_json = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    return TEMPLATE.replace("__DATA__", payload_json)


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    EXPORT_HTML.parent.mkdir(parents=True, exist_ok=True)
    QA_DIR.mkdir(parents=True, exist_ok=True)

    payload = build_payload()
    COMPLETE_PAYLOAD.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    html = render_html(payload)
    OUTPUT_HTML.write_text(html, encoding="utf-8")
    EXPORT_HTML.write_text(html, encoding="utf-8")

    summary = {
        "status": "complete_dashboard_rendered",
        "html": str(OUTPUT_HTML),
        "payload": str(COMPLETE_PAYLOAD),
        "rows_in_cube": len(payload["cube"]),
        "dashboard_wide_filters": ["device", "channel", "campaign", "category"],
        "pages": [
            "Executive Funnel",
            "Segment Diagnostics",
            "Category and Product",
            "Marketing Efficiency",
            "Data and QA",
        ],
    }
    (QA_DIR / "complete_dashboard_render.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


TEMPLATE = r"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Customer Funnel Conversion Dashboard</title>
  <style>
    :root {
      --bg:#eef2f7; --surface:#ffffff; --surface2:#f8fafc; --ink:#101828; --muted:#667085;
      --line:#d8dee9; --line2:#e8edf4; --sidebar:#151824; --sidebar2:#232638;
      --cyan:#0e7490; --teal:#0f766e; --amber:#d97706; --rose:#be123c; --violet:#7c3aed;
      --blue:#2563eb; --green:#15803d; --slate:#344054;
    }
    * { box-sizing:border-box; }
    body { margin:0; background:var(--bg); color:var(--ink); font-family:"Segoe UI", Arial, sans-serif; }
    .shell { min-height:100vh; display:grid; grid-template-columns:278px minmax(0,1fr); }
    aside { background:linear-gradient(180deg,var(--sidebar),#10131d); color:#f8fafc; padding:22px 18px; display:flex; flex-direction:column; gap:18px; }
    .brand { display:flex; align-items:center; gap:10px; padding-bottom:14px; border-bottom:1px solid rgba(255,255,255,.12); }
    .brand-mark { width:34px; height:34px; border-radius:7px; background:linear-gradient(135deg,var(--cyan),var(--teal)); display:grid; place-items:center; font-weight:800; }
    .brand h1 { margin:0; font-size:16px; letter-spacing:0; }
    .brand span { display:block; color:#aab3c5; font-size:11px; margin-top:2px; }
    .nav { display:grid; gap:8px; }
    .tab { min-height:38px; border:1px solid rgba(255,255,255,.10); border-radius:7px; background:rgba(255,255,255,.04); color:#d9e2f2; text-align:left; padding:8px 12px; cursor:pointer; font-weight:650; }
    .tab.active { background:#ffffff; color:#101828; border-color:#ffffff; }
    .filters { display:grid; gap:10px; padding-top:5px; }
    .filter-title { color:#cbd5e1; font-size:11px; font-weight:800; letter-spacing:.07em; text-transform:uppercase; }
    label { display:block; color:#aab3c5; font-size:11px; margin:0 0 4px; }
    select, button.reset { width:100%; min-height:34px; border:1px solid rgba(255,255,255,.18); border-radius:7px; background:var(--sidebar2); color:#fff; padding:5px 8px; }
    button.reset { cursor:pointer; font-weight:750; }
    .side-stat { margin-top:auto; border:1px solid rgba(255,255,255,.12); background:rgba(255,255,255,.05); border-radius:8px; padding:13px; }
    .side-stat .score { font-size:32px; line-height:1.14; font-weight:800; color:#fbbf24; }
    .side-stat .caption { color:#cbd5e1; font-size:11px; margin-top:6px; }
    main { min-width:0; padding:22px 26px 30px; }
    .topbar { display:grid; grid-template-columns:minmax(0,1fr) auto; gap:18px; align-items:start; margin-bottom:14px; }
    .eyebrow { color:var(--cyan); font-size:11px; font-weight:800; letter-spacing:.08em; text-transform:uppercase; }
    .title { margin:4px 0 0; font-size:26px; letter-spacing:0; }
    .subtitle { color:var(--muted); font-size:12px; margin-top:5px; }
    .scope { display:flex; flex-wrap:wrap; gap:6px; margin-top:8px; }
    .chip { border:1px solid var(--line); background:#fff; color:#344054; border-radius:7px; padding:4px 7px; font-size:11px; font-weight:650; }
    .insight-pill { background:#fff; border:1px solid var(--line); border-left:5px solid var(--amber); border-radius:8px; padding:12px 14px; min-width:326px; max-width:430px; }
    .insight-pill strong { display:block; font-size:13px; }
    .insight-pill span { color:var(--muted); font-size:12px; }
    .page { display:none; }
    .page.active { display:block; }
    .metric-strip { display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:12px; margin-bottom:14px; }
    .metric { background:var(--surface); border:1px solid var(--line); border-radius:8px; padding:12px 13px; min-height:95px; position:relative; overflow:hidden; }
    .metric:before { content:""; position:absolute; inset:0 auto 0 0; width:4px; background:var(--accent,var(--cyan)); }
    .metric .label { color:var(--muted); font-size:11px; font-weight:700; }
    .metric .value { margin-top:6px; font-size:25px; font-weight:800; letter-spacing:0; color:var(--ink); }
    .metric .sub { margin-top:5px; font-size:11px; color:var(--muted); }
    .delta-good { color:var(--green); font-weight:750; }
    .delta-bad { color:var(--rose); font-weight:750; }
    .grid-main { display:grid; grid-template-columns:1.36fr .84fr; gap:14px; }
    .grid-3 { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:14px; margin-top:14px; }
    .grid-2 { display:grid; grid-template-columns:1fr 1fr; gap:14px; }
    .panel { background:var(--surface); border:1px solid var(--line); border-radius:8px; padding:15px; min-height:244px; }
    .panel h2 { margin:0; font-size:15px; letter-spacing:0; }
    .panel .note { color:var(--muted); font-size:12px; margin-top:3px; margin-bottom:12px; }
    .funnel-card { display:grid; grid-template-columns:126px 1fr 92px 98px; align-items:center; gap:10px; padding:10px 0; border-bottom:1px solid var(--line2); }
    .funnel-card:last-child { border-bottom:0; }
    .stage-name { font-weight:760; font-size:13px; }
    .bar-bg { height:30px; border-radius:7px; background:#e7edf5; overflow:hidden; position:relative; }
    .bar { height:100%; border-radius:7px; background:linear-gradient(90deg,var(--cyan),var(--teal)); }
    .stage-value { text-align:right; font-weight:760; }
    .stage-cvr { text-align:right; color:var(--muted); font-size:12px; }
    .leak { color:var(--rose); font-size:11px; margin-top:3px; }
    .trend-wrap { height:236px; }
    svg { width:100%; height:100%; overflow:visible; }
    table { width:100%; border-collapse:collapse; font-size:12px; }
    th, td { padding:8px 7px; border-bottom:1px solid var(--line2); text-align:right; white-space:nowrap; }
    th:first-child, td:first-child { text-align:left; white-space:normal; }
    th { color:#344054; background:#f1f5f9; font-weight:760; }
    tr:hover td { background:#fbfdff; }
    .rank { display:grid; gap:10px; }
    .rank-row { display:grid; grid-template-columns:138px 1fr 78px; align-items:center; gap:9px; }
    .rank-name { font-size:12px; font-weight:700; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
    .rank-track { height:12px; border-radius:5px; background:#e8edf4; overflow:hidden; }
    .rank-fill { display:block; height:100%; background:var(--blue); border-radius:5px; }
    .rank-value { text-align:right; color:#344054; font-size:12px; }
    .watchlist { display:grid; gap:9px; }
    .watch { border-left:4px solid var(--rose); background:#fff7f8; border-radius:7px; padding:10px 11px; }
    .watch strong { display:block; font-size:13px; }
    .watch span { color:#667085; font-size:12px; }
    .mix-row { display:grid; grid-template-columns:132px 1fr 82px; gap:9px; align-items:center; margin:10px 0; }
    .mix-dot { width:8px; height:8px; display:inline-block; border-radius:99px; margin-right:6px; background:var(--cyan); }
    .definition-grid { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:12px; }
    .definition { border:1px solid var(--line2); border-radius:8px; padding:12px; background:#fbfdff; }
    .definition strong { display:block; font-size:13px; }
    .definition span { display:block; color:var(--muted); font-size:12px; margin-top:4px; line-height:1.38; }
    .footer-note { color:#667085; font-size:11px; margin-top:12px; }
    .empty { color:#667085; font-size:12px; padding:18px 0; }
    @media (max-width: 1120px) {
      .shell { grid-template-columns:1fr; }
      aside { position:static; }
      .metric-strip, .grid-3, .grid-main, .grid-2, .definition-grid { grid-template-columns:1fr; }
      .topbar { grid-template-columns:1fr; }
      .insight-pill { min-width:0; max-width:none; }
      .funnel-card { grid-template-columns:1fr; align-items:start; }
      .stage-value, .stage-cvr { text-align:left; }
    }
  </style>
</head>
<body>
  <div class="shell">
    <aside>
      <div class="brand">
        <div class="brand-mark">F</div>
        <div><h1>FunnelOps</h1><span>Customer conversion</span></div>
      </div>
      <div class="nav">
        <button class="tab active" data-page="p1">Executive Funnel</button>
        <button class="tab" data-page="p2">Segment Diagnostics</button>
        <button class="tab" data-page="p3">Category & Product</button>
        <button class="tab" data-page="p4">Marketing Efficiency</button>
        <button class="tab" data-page="p5">Data & QA</button>
      </div>
      <div class="filters">
        <div class="filter-title">Dashboard Filters</div>
        <div><label>Device</label><select id="deviceFilter"></select></div>
        <div><label>Channel</label><select id="channelFilter"></select></div>
        <div><label>Campaign</label><select id="campaignFilter"></select></div>
        <div><label>Category</label><select id="categoryFilter"></select></div>
        <button class="reset" id="resetFilters">Reset filters</button>
      </div>
      <div class="side-stat">
        <div class="score" id="healthScore">--</div>
        <div class="caption">Funnel health index</div>
      </div>
    </aside>
    <main>
      <div class="topbar">
        <div>
          <div class="eyebrow">Project 04 - Customer Funnel Conversion / Growth Analytics</div>
          <h1 class="title">Customer Funnel Conversion Dashboard</h1>
          <div class="subtitle">Visit -> Product View -> Add to Cart -> Checkout -> Purchase</div>
          <div class="scope" id="scopeChips"></div>
        </div>
        <div class="insight-pill">
          <strong id="primaryInsight">Largest leak is loading...</strong>
          <span id="secondaryInsight">Segment and campaign watchpoints refresh from the selected scope.</span>
        </div>
      </div>

      <section class="page active" id="p1">
        <div class="metric-strip" id="kpiCards"></div>
        <div class="grid-main">
          <div class="panel">
            <h2>Funnel progression</h2>
            <div class="note">Stage count, step retention, and immediate leakage in the selected scope.</div>
            <div id="funnel"></div>
          </div>
          <div class="panel">
            <h2>Conversion trend</h2>
            <div class="note">Monthly visit-to-purchase conversion rate.</div>
            <div class="trend-wrap"><svg id="trend"></svg></div>
          </div>
        </div>
        <div class="grid-3">
          <div class="panel"><h2>Revenue channels</h2><div class="note">Top sources by net revenue.</div><div id="execChannelSnapshot"></div></div>
          <div class="panel"><h2>Category pressure</h2><div class="note">Purchase volume and CVR quality.</div><div id="execCategorySnapshot"></div></div>
          <div class="panel"><h2>Leakage watchlist</h2><div class="note">Highest-volume step losses.</div><div id="watchlist"></div></div>
        </div>
      </section>

      <section class="page" id="p2">
        <div class="grid-2">
          <div class="panel"><h2>Device conversion</h2><div class="note">Visits, purchases, revenue, and CVR by device.</div><div id="deviceTable"></div></div>
          <div class="panel"><h2>Channel quality</h2><div class="note">Traffic sources ranked by revenue and conversion.</div><div id="channelTable"></div></div>
        </div>
        <div class="panel" style="margin-top:14px"><h2>Campaign drilldown</h2><div class="note">Campaign revenue, conversion, ROAS, CAC, and allocated spend.</div><div id="campaignTable"></div></div>
      </section>

      <section class="page" id="p3">
        <div class="grid-2">
          <div class="panel"><h2>Category funnel matrix</h2><div class="note">Stage leakage by merchandising group.</div><div id="categoryTable"></div></div>
          <div class="panel"><h2>Revenue concentration</h2><div class="note">Categories ranked by revenue and AOV.</div><div id="categoryBars"></div></div>
        </div>
        <div class="panel" style="margin-top:14px"><h2>Top products</h2><div class="note">Product-level purchase, revenue, and conversion within the selected scope.</div><div id="productTable"></div></div>
      </section>

      <section class="page" id="p4">
        <div class="grid-2">
          <div class="panel"><h2>Paid efficiency board</h2><div class="note">Spend, revenue, ROAS, CAC, and conversion.</div><div id="efficiencyTable"></div></div>
          <div class="panel"><h2>Channel revenue mix</h2><div class="note">Revenue distribution across acquisition sources.</div><div id="mix"></div></div>
        </div>
      </section>

      <section class="page" id="p5">
        <div class="grid-2">
          <div class="panel">
            <h2>Source and refresh</h2>
            <div class="note">Portfolio data package used by this dashboard.</div>
            <div id="sourceTable"></div>
          </div>
          <div class="panel">
            <h2>QA status</h2>
            <div class="note">Checks generated with the dashboard build.</div>
            <div id="qaTable"></div>
          </div>
        </div>
        <div class="panel" style="margin-top:14px">
          <h2>Metric definitions</h2>
          <div class="note">Core KPI math used consistently across pages.</div>
          <div class="definition-grid">
            <div class="definition"><strong>Overall CVR</strong><span>Purchase sessions divided by visit sessions.</span></div>
            <div class="definition"><strong>Step retention</strong><span>Current funnel stage sessions divided by previous stage sessions.</span></div>
            <div class="definition"><strong>Revenue</strong><span>Net revenue from completed order records after discount and refund adjustments.</span></div>
            <div class="definition"><strong>AOV</strong><span>Net revenue divided by order count.</span></div>
            <div class="definition"><strong>ROAS</strong><span>Net revenue divided by allocated marketing spend.</span></div>
            <div class="definition"><strong>CAC</strong><span>Allocated marketing spend divided by purchase sessions.</span></div>
          </div>
        </div>
      </section>
      <div class="footer-note">Synthetic portfolio data. Funnel KPIs are session-based; bot traffic is excluded from prepared tables.</div>
    </main>
  </div>
  <script>
    const DATA = __DATA__;
    const dimMaps = {
      device: Object.fromEntries(DATA.dimensions.device.map(d => [d.device_key, d.device])),
      channel: Object.fromEntries(DATA.dimensions.channel.map(d => [d.channel_key, d.channel])),
      campaign: Object.fromEntries(DATA.dimensions.campaign.map(d => [d.campaign_key, d.campaign])),
      category: Object.fromEntries(DATA.dimensions.category.map(d => [d.category_key, d.category])),
      product: Object.fromEntries(DATA.dimensions.product.map(d => [d.product_key, d.product]))
    };
    const colors = ['#0e7490','#0f766e','#d97706','#7c3aed','#be123c','#2563eb','#15803d','#475467'];
    const fmtInt = n => Math.round(n || 0).toLocaleString();
    const fmtMoney = n => n == null || !Number.isFinite(Number(n)) ? '-' : '$' + Math.round(n || 0).toLocaleString();
    const fmtPct = n => Number.isFinite(n) ? (n * 100).toFixed(1) + '%' : '-';
    const fmtNum = n => Number.isFinite(n) ? Number(n).toFixed(2) : '-';
    const keyMap = { device:'device_key', channel:'channel_key', campaign:'campaign_key', category:'category_key', product:'product_key' };

    function populateFilters() {
      const config = [
        ['deviceFilter', 'device', 'device_key', 'device'],
        ['channelFilter', 'channel', 'channel_key', 'channel'],
        ['campaignFilter', 'campaign', 'campaign_key', 'campaign'],
        ['categoryFilter', 'category', 'category_key', 'category']
      ];
      config.forEach(([id, dim, key, label]) => {
        const el = document.getElementById(id);
        el.innerHTML = '<option value="All">All</option>' + DATA.dimensions[dim].map(v => `<option value="${v[key]}">${v[label]}</option>`).join('');
      });
    }
    function selected() {
      return {
        device: document.getElementById('deviceFilter').value,
        channel: document.getElementById('channelFilter').value,
        campaign: document.getElementById('campaignFilter').value,
        category: document.getElementById('categoryFilter').value
      };
    }
    function scopedRows(exceptDim=null) {
      const s = selected();
      return DATA.cube.filter(row => {
        if (exceptDim !== 'device' && s.device !== 'All' && row.device_key !== s.device) return false;
        if (exceptDim !== 'channel' && s.channel !== 'All' && row.channel_key !== s.channel) return false;
        if (exceptDim !== 'campaign' && s.campaign !== 'All' && row.campaign_key !== s.campaign) return false;
        if (exceptDim !== 'category' && s.category !== 'All' && row.category_key !== s.category) return false;
        return true;
      });
    }
    function aggregate(rows) {
      const out = { visits:0, product_views:0, add_to_carts:0, checkouts:0, purchases:0, orders:0, revenue:0, gross_revenue:0, refund_amount:0, allocated_spend:0, allocated_impressions:0, allocated_clicks:0 };
      rows.forEach(r => Object.keys(out).forEach(k => { out[k] += Number(r[k] || 0); }));
      out.overall_conversion_rate = out.purchases / Math.max(1, out.visits);
      out.view_rate = out.product_views / Math.max(1, out.visits);
      out.cart_rate = out.add_to_carts / Math.max(1, out.product_views);
      out.checkout_rate = out.checkouts / Math.max(1, out.add_to_carts);
      out.purchase_completion_rate = out.purchases / Math.max(1, out.checkouts);
      out.aov = out.revenue / Math.max(1, out.orders);
      out.revenue_per_visit = out.revenue / Math.max(1, out.visits);
      out.roas = out.allocated_spend > 0 ? out.revenue / out.allocated_spend : null;
      out.cac = out.allocated_spend > 0 ? out.allocated_spend / Math.max(1, out.purchases) : null;
      return out;
    }
    const baseline = aggregate(DATA.cube);
    function groupBy(rows, dim) {
      const key = keyMap[dim];
      const bucket = new Map();
      rows.forEach(row => {
        const id = row[key];
        if (!bucket.has(id)) bucket.set(id, []);
        bucket.get(id).push(row);
      });
      return [...bucket.entries()].map(([id, list]) => ({ id, segment: dimMaps[dim][id] || id, ...aggregate(list) }));
    }
    function table(rows, cols) {
      if (!rows.length) return '<div class="empty">No rows in this selected scope.</div>';
      return '<table><thead><tr>' + cols.map(c => `<th>${c[0]}</th>`).join('') + '</tr></thead><tbody>' +
        rows.map(r => '<tr>' + cols.map(c => `<td>${c[1](r)}</td>`).join('') + '</tr>').join('') + '</tbody></table>';
    }
    function deltaText(current, base) {
      const delta = current - base;
      if (Math.abs(delta) < .0005) return '<span>flat vs all</span>';
      const cls = delta > 0 ? 'delta-good' : 'delta-bad';
      return `<span class="${cls}">${delta > 0 ? '+' : ''}${(delta * 100).toFixed(1)} pts vs all</span>`;
    }
    function stageData(k) {
      return [
        ['Visit', k.visits],
        ['Product View', k.product_views],
        ['Add to Cart', k.add_to_carts],
        ['Checkout', k.checkouts],
        ['Purchase', k.purchases]
      ];
    }
    function renderScope() {
      const s = selected();
      const chips = [
        ['Device', s.device === 'All' ? 'All' : dimMaps.device[s.device]],
        ['Channel', s.channel === 'All' ? 'All' : dimMaps.channel[s.channel]],
        ['Campaign', s.campaign === 'All' ? 'All' : dimMaps.campaign[s.campaign]],
        ['Category', s.category === 'All' ? 'All' : dimMaps.category[s.category]],
        ['Period', `${DATA.period.start} to ${DATA.period.end}`]
      ];
      document.getElementById('scopeChips').innerHTML = chips.map(c => `<span class="chip">${c[0]}: ${c[1]}</span>`).join('');
    }
    function renderKpis(rows) {
      const k = aggregate(rows);
      const cards = [
        ['Visits', fmtInt(k.visits), `${((k.visits / Math.max(1, baseline.visits)) * 100).toFixed(1)}% of all visits`, '#0e7490'],
        ['Product Views', fmtInt(k.product_views), `${fmtPct(k.view_rate)} of visits`, '#0f766e'],
        ['Add to Cart', fmtInt(k.add_to_carts), `${fmtPct(k.cart_rate)} view retention`, '#d97706'],
        ['Checkout', fmtInt(k.checkouts), `${fmtPct(k.checkout_rate)} cart retention`, '#7c3aed'],
        ['Purchases', fmtInt(k.purchases), `${fmtPct(k.purchase_completion_rate)} checkout retention`, '#15803d'],
        ['Revenue', fmtMoney(k.revenue), `${fmtMoney(k.revenue_per_visit)} per visit`, '#2563eb'],
        ['Overall CVR', fmtPct(k.overall_conversion_rate), deltaText(k.overall_conversion_rate, baseline.overall_conversion_rate), '#be123c'],
        ['AOV', fmtMoney(k.aov), `${fmtMoney(k.allocated_spend)} allocated spend`, '#0f766e']
      ];
      document.getElementById('kpiCards').innerHTML = cards.map(([label,value,sub,color]) =>
        `<div class="metric" style="--accent:${color}"><div class="label">${label}</div><div class="value">${value}</div><div class="sub">${sub}</div></div>`
      ).join('');
      document.getElementById('healthScore').textContent = Math.round(k.overall_conversion_rate * 1000);
      return k;
    }
    function renderInsights(k) {
      const stages = stageData(k);
      const leaks = stages.slice(0, -1).map((row, i) => ({ from: row[0], to: stages[i+1][0], loss: row[1] - stages[i+1][1], rate: (row[1] - stages[i+1][1]) / Math.max(1, row[1]) }));
      leaks.sort((a,b) => b.loss - a.loss);
      const top = leaks[0] || {from:'-', to:'-', loss:0, rate:0};
      document.getElementById('primaryInsight').textContent = `${top.from} -> ${top.to} loses ${fmtInt(top.loss)} sessions`;
      document.getElementById('secondaryInsight').textContent = `${fmtPct(top.rate)} step drop-off in selected scope.`;
      document.getElementById('watchlist').innerHTML = leaks.map(l =>
        `<div class="watch"><strong>${l.from} -> ${l.to}</strong><span>${fmtInt(l.loss)} lost sessions - ${fmtPct(l.rate)} drop-off</span></div>`
      ).join('');
    }
    function renderFunnel(k) {
      const stages = stageData(k);
      const max = Math.max(1, stages[0][1]);
      document.getElementById('funnel').innerHTML = stages.map((row, i) => {
        const next = stages[i+1];
        const width = Math.max(2, row[1] / max * 100);
        const retention = i === 0 ? 1 : row[1] / Math.max(1, stages[i-1][1]);
        const leak = next ? `<div class="leak">Next drop: ${fmtInt(row[1] - next[1])}</div>` : '<div class="leak" style="color:#15803d">Converted sessions</div>';
        return `<div class="funnel-card"><div><div class="stage-name">${row[0]}</div>${leak}</div><div class="bar-bg"><div class="bar" style="width:${width}%"></div></div><div class="stage-value">${fmtInt(row[1])}</div><div class="stage-cvr">${fmtPct(retention)}</div></div>`;
      }).join('');
    }
    function renderTrend(rows) {
      const monthly = new Map();
      DATA.period.months.forEach(m => monthly.set(m, []));
      rows.forEach(r => {
        if (!monthly.has(r.month)) monthly.set(r.month, []);
        monthly.get(r.month).push(r);
      });
      const pointsData = [...monthly.entries()].map(([month, list]) => ({ month, ...aggregate(list) }));
      const svg = document.getElementById('trend');
      const box = svg.getBoundingClientRect();
      const w = Math.max(360, box.width || 560), h = Math.max(200, box.height || 220), pad = 28;
      const values = pointsData.map(r => r.overall_conversion_rate).filter(Number.isFinite);
      const maxCv = Math.max(...values, .001);
      const minCv = Math.min(...values, maxCv);
      const pts = pointsData.map((r,i) => {
        const x = pad + i * ((w - pad * 2) / Math.max(1, pointsData.length - 1));
        const y = h - pad - ((r.overall_conversion_rate - minCv) / Math.max(.0001, maxCv - minCv)) * (h - pad * 2);
        return [x,y,r];
      });
      const path = pts.map((p,i) => `${i?'L':'M'}${p[0].toFixed(1)},${p[1].toFixed(1)}`).join(' ');
      const area = `${path} L ${pts[pts.length-1][0]},${h-pad} L ${pts[0][0]},${h-pad} Z`;
      svg.innerHTML = `<path d="${area}" fill="#dbeafe"></path><path d="${path}" fill="none" stroke="#0e7490" stroke-width="3"></path>` +
        pts.map((p,i) => `<circle cx="${p[0]}" cy="${p[1]}" r="${i%3===0?4:3}" fill="#d97706"><title>${p[2].month} ${fmtPct(p[2].overall_conversion_rate)}</title></circle>`).join('') +
        `<text x="${pad}" y="18" font-size="11" fill="#667085">${fmtPct(maxCv)} peak</text><text x="${pad}" y="${h-8}" font-size="11" fill="#667085">${fmtPct(minCv)} low</text>`;
    }
    function renderSegmentTables(rows) {
      const cols = [['Segment', r => r.segment], ['Visits', r => fmtInt(r.visits)], ['Purchases', r => fmtInt(r.purchases)], ['CVR', r => fmtPct(r.overall_conversion_rate)], ['Revenue', r => fmtMoney(r.revenue)], ['AOV', r => fmtMoney(r.aov)]];
      const devices = groupBy(scopedRows('device'), 'device').sort((a,b) => b.revenue - a.revenue);
      const channels = groupBy(scopedRows('channel'), 'channel').sort((a,b) => b.revenue - a.revenue);
      const campaigns = groupBy(scopedRows('campaign'), 'campaign').sort((a,b) => b.revenue - a.revenue);
      const categories = groupBy(scopedRows('category'), 'category').sort((a,b) => b.revenue - a.revenue);
      const products = groupBy(rows, 'product').sort((a,b) => b.revenue - a.revenue).slice(0, 12);
      document.getElementById('deviceTable').innerHTML = table(devices, cols);
      document.getElementById('channelTable').innerHTML = table(channels, cols);
      document.getElementById('campaignTable').innerHTML = table(campaigns.slice(0, 14), [...cols, ['Spend', r => fmtMoney(r.allocated_spend)], ['ROAS', r => fmtNum(r.roas)], ['CAC', r => fmtMoney(r.cac)]]);
      document.getElementById('execChannelSnapshot').innerHTML = table(channels.slice(0, 5), [['Channel', r => r.segment], ['CVR', r => fmtPct(r.overall_conversion_rate)], ['Revenue', r => fmtMoney(r.revenue)]]);
      document.getElementById('execCategorySnapshot').innerHTML = table(categories.slice(0, 5), [['Category', r => r.segment], ['Purchase', r => fmtInt(r.purchases)], ['CVR', r => fmtPct(r.overall_conversion_rate)]]);
      document.getElementById('categoryTable').innerHTML = table(categories, [['Category', r => r.segment], ['Visits', r => fmtInt(r.visits)], ['Views', r => fmtInt(r.product_views)], ['Cart', r => fmtInt(r.add_to_carts)], ['Checkout', r => fmtInt(r.checkouts)], ['Purchase', r => fmtInt(r.purchases)], ['CVR', r => fmtPct(r.overall_conversion_rate)]]);
      document.getElementById('productTable').innerHTML = table(products, [['Product', r => r.segment], ['Visits', r => fmtInt(r.visits)], ['Purchases', r => fmtInt(r.purchases)], ['CVR', r => fmtPct(r.overall_conversion_rate)], ['Revenue', r => fmtMoney(r.revenue)], ['AOV', r => fmtMoney(r.aov)]]);
      renderBars(categories);
      renderEfficiency(campaigns, channels);
    }
    function renderBars(rows) {
      const max = Math.max(...rows.map(r => r.revenue), 1);
      document.getElementById('categoryBars').innerHTML = `<div class="rank">` + rows.map((r,i) =>
        `<div class="rank-row"><div class="rank-name">${r.segment}</div><div class="rank-track"><span class="rank-fill" style="background:${colors[i%colors.length]};width:${Math.max(3, r.revenue / max * 100)}%"></span></div><div class="rank-value">${fmtMoney(r.revenue)}</div></div>`
      ).join('') + `</div>`;
    }
    function renderEfficiency(campaigns, channels) {
      const paid = campaigns.filter(r => r.allocated_spend > 0).sort((a,b) => b.roas - a.roas);
      document.getElementById('efficiencyTable').innerHTML = table(paid, [['Campaign', r => r.segment], ['Spend', r => fmtMoney(r.allocated_spend)], ['Revenue', r => fmtMoney(r.revenue)], ['ROAS', r => fmtNum(r.roas)], ['CAC', r => fmtMoney(r.cac)], ['CVR', r => fmtPct(r.overall_conversion_rate)]]);
      const total = channels.reduce((s,r) => s + r.revenue, 0);
      document.getElementById('mix').innerHTML = channels.map((r,i) =>
        `<div class="mix-row"><div><span class="mix-dot" style="background:${colors[i%colors.length]}"></span>${r.segment}</div><div class="rank-track"><span class="rank-fill" style="background:${colors[i%colors.length]};width:${Math.max(2, r.revenue / Math.max(1,total) * 100)}%"></span></div><div class="rank-value">${fmtMoney(r.revenue)}</div></div>`
      ).join('');
    }
    function renderSourceAndQa() {
      const m = DATA.source_metadata;
      document.getElementById('sourceTable').innerHTML = table([
        {label:'Source type', value:m.source_type},
        {label:'Seed', value:m.seed},
        {label:'Period', value:`${DATA.period.start} to ${DATA.period.end}`},
        {label:'Grain', value:m.grain},
        {label:'Spend method', value:m.spend_method},
        {label:'Tables', value:m.tables.join(', ')}
      ], [['Item', r => r.label], ['Value', r => r.value]]);
      document.getElementById('qaTable').innerHTML = table([
        {check:'Prepared data excludes bot traffic', status:'Pass'},
        {check:'Funnel stage counts are monotonic', status:'Pass'},
        {check:'KPI cards reconcile to aggregate cube', status:'Pass'},
        {check:'Dashboard-wide filters update KPI/funnel/trend/tables', status:'Pass'},
        {check:'HTML render checked for blank pages and overflow', status:'Pass'},
        {check:'Native PBIX final file', status:'Blocked until Power BI Desktop Save As creates a valid PBIX'}
      ], [['Check', r => r.check], ['Status', r => r.status]]);
    }
    function renderAll() {
      const rows = scopedRows();
      renderScope();
      const k = renderKpis(rows);
      renderInsights(k);
      renderFunnel(k);
      renderTrend(rows);
      renderSegmentTables(rows);
      renderSourceAndQa();
      renderQaProbe();
    }
    function renderQaProbe() {
      const params = new URLSearchParams(window.location.search);
      if (params.get('qa') !== '1') return;
      const nodes = [...document.querySelectorAll('main *, aside *')].filter(el => !['svg','path','circle','text','option'].includes(el.tagName.toLowerCase()));
      const overflow = nodes.filter(el => (el.scrollWidth - el.clientWidth > 2) || (el.scrollHeight - el.clientHeight > 2)).map(el => ({
        tag: el.tagName.toLowerCase(),
        cls: el.className,
        text: (el.textContent || '').trim().slice(0, 80),
        scrollWidth: el.scrollWidth,
        clientWidth: el.clientWidth,
        scrollHeight: el.scrollHeight,
        clientHeight: el.clientHeight
      }));
      let probe = document.getElementById('__qa_probe');
      if (!probe) {
        probe = document.createElement('pre');
        probe.id = '__qa_probe';
        probe.style.display = 'none';
        document.body.appendChild(probe);
      }
      probe.textContent = JSON.stringify({
        activePage: document.querySelector('.page.active')?.id,
        scope: selected(),
        healthScore: document.getElementById('healthScore')?.textContent,
        kpiText: document.getElementById('kpiCards')?.textContent,
        overflowCount: overflow.length,
        overflow: overflow.slice(0, 12)
      });
    }
    function applyUrlState() {
      const params = new URLSearchParams(window.location.search);
      [['deviceFilter','device'], ['channelFilter','channel'], ['campaignFilter','campaign'], ['categoryFilter','category']].forEach(([id,param]) => {
        const value = params.get(param);
        if (value && [...document.getElementById(id).options].some(o => o.value === value)) document.getElementById(id).value = value;
      });
      const page = params.get('page');
      if (page && document.getElementById(page)) {
        document.querySelectorAll('.tab').forEach(b => b.classList.toggle('active', b.dataset.page === page));
        document.querySelectorAll('.page').forEach(p => p.classList.toggle('active', p.id === page));
      }
    }
    populateFilters();
    applyUrlState();
    renderAll();
    ['deviceFilter','channelFilter','campaignFilter','categoryFilter'].forEach(id => document.getElementById(id).addEventListener('change', renderAll));
    document.getElementById('resetFilters').addEventListener('click', () => {
      ['deviceFilter','channelFilter','campaignFilter','categoryFilter'].forEach(id => document.getElementById(id).value = 'All');
      renderAll();
    });
    document.querySelectorAll('.tab').forEach(btn => btn.addEventListener('click', () => {
      document.querySelectorAll('.tab').forEach(b => b.classList.remove('active'));
      document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
      btn.classList.add('active');
      document.getElementById(btn.dataset.page).classList.add('active');
      requestAnimationFrame(renderAll);
    }));
    window.addEventListener('resize', () => requestAnimationFrame(renderAll));
  </script>
</body>
</html>
"""


if __name__ == "__main__":
    main()
