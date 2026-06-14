from __future__ import annotations

import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
PAYLOAD_PATH = PROJECT_ROOT / "output" / "dashboard_payload.json"
OUTPUT_HTML = PROJECT_ROOT / "output" / "dashboard.html"
EXPORT_HTML = PROJECT_ROOT / "output" / "exports" / "customer_funnel_dashboard_preview.html"


def main() -> None:
    payload = json.loads(PAYLOAD_PATH.read_text(encoding="utf-8"))
    payload_json = json.dumps(payload, ensure_ascii=False)
    html = TEMPLATE.replace("__DATA__", payload_json)
    OUTPUT_HTML.write_text(html, encoding="utf-8")
    EXPORT_HTML.parent.mkdir(parents=True, exist_ok=True)
    EXPORT_HTML.write_text(html, encoding="utf-8")
    print(json.dumps({"status": "rendered", "html": str(OUTPUT_HTML), "template": "growth_command_center_v2"}, indent=2))


TEMPLATE = r"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Customer Funnel Command Center</title>
  <style>
    :root {
      --bg:#eef2f7; --surface:#ffffff; --surface-2:#f8fafc; --ink:#101828; --muted:#667085;
      --line:#d8dee9; --sidebar:#171923; --sidebar-2:#232638; --teal:#0f766e; --cyan:#0e7490;
      --amber:#d97706; --rose:#be123c; --violet:#7c3aed; --blue:#2563eb; --green:#15803d;
    }
    * { box-sizing:border-box; }
    body { margin:0; background:var(--bg); color:var(--ink); font-family:"Segoe UI", Arial, sans-serif; }
    .shell { min-height:100vh; display:grid; grid-template-columns:272px minmax(0,1fr); }
    aside { background:linear-gradient(180deg, var(--sidebar), #11131d); color:#f8fafc; padding:22px 18px; display:flex; flex-direction:column; gap:18px; }
    .brand { display:flex; align-items:center; gap:10px; padding-bottom:14px; border-bottom:1px solid rgba(255,255,255,.12); }
    .brand-mark { width:34px; height:34px; border-radius:7px; background:linear-gradient(135deg,var(--cyan),var(--teal)); display:grid; place-items:center; font-weight:800; }
    .brand h1 { margin:0; font-size:16px; letter-spacing:0; }
    .brand span { display:block; color:#aab3c5; font-size:11px; margin-top:2px; }
    .nav { display:grid; gap:8px; }
    .tab { height:38px; border:1px solid rgba(255,255,255,.10); border-radius:7px; background:rgba(255,255,255,.04); color:#d9e2f2; text-align:left; padding:0 12px; cursor:pointer; font-weight:650; }
    .tab.active { background:#ffffff; color:#101828; border-color:#ffffff; }
    .filters { display:grid; gap:10px; padding-top:6px; }
    label { display:block; color:#aab3c5; font-size:11px; margin:0 0 4px; }
    select { width:100%; height:34px; border:1px solid rgba(255,255,255,.18); border-radius:7px; background:var(--sidebar-2); color:#ffffff; padding:4px 8px; }
    .side-stat { margin-top:auto; border:1px solid rgba(255,255,255,.12); background:rgba(255,255,255,.05); border-radius:8px; padding:13px; }
    .side-stat .score { font-size:32px; line-height:1.16; font-weight:800; color:#fbbf24; }
    .side-stat .caption { color:#cbd5e1; font-size:11px; margin-top:6px; }
    main { min-width:0; padding:22px 26px 30px; }
    .topbar { display:grid; grid-template-columns:minmax(0,1fr) auto; gap:18px; align-items:start; margin-bottom:16px; }
    .eyebrow { color:var(--cyan); font-size:11px; font-weight:800; letter-spacing:.08em; text-transform:uppercase; }
    .title { margin:4px 0 0; font-size:25px; letter-spacing:0; }
    .subtitle { color:var(--muted); font-size:12px; margin-top:5px; }
    .insight-pill { background:#fff; border:1px solid var(--line); border-left:5px solid var(--amber); border-radius:8px; padding:12px 14px; min-width:320px; }
    .insight-pill strong { display:block; font-size:13px; }
    .insight-pill span { color:var(--muted); font-size:12px; }
    .page { display:none; }
    .page.active { display:block; }
    .metric-strip { display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:12px; margin-bottom:14px; }
    .metric { background:var(--surface); border:1px solid var(--line); border-radius:8px; padding:12px 13px; min-height:92px; position:relative; overflow:hidden; }
    .metric:before { content:""; position:absolute; inset:0 auto 0 0; width:4px; background:var(--accent,var(--cyan)); }
    .metric .label { color:var(--muted); font-size:11px; font-weight:650; }
    .metric .value { margin-top:6px; font-size:25px; font-weight:800; letter-spacing:0; color:var(--ink); }
    .metric .sub { margin-top:5px; font-size:11px; color:var(--muted); display:flex; justify-content:space-between; gap:8px; }
    .grid-main { display:grid; grid-template-columns:1.36fr .84fr; gap:14px; }
    .grid-3 { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:14px; margin-top:14px; }
    .grid-2 { display:grid; grid-template-columns:1fr 1fr; gap:14px; }
    .panel { background:var(--surface); border:1px solid var(--line); border-radius:8px; padding:15px; min-height:244px; }
    .panel h2 { margin:0; font-size:15px; letter-spacing:0; }
    .panel .note { color:var(--muted); font-size:12px; margin-top:3px; margin-bottom:12px; }
    .funnel-card { display:grid; grid-template-columns:122px 1fr 88px 94px; align-items:center; gap:10px; padding:10px 0; border-bottom:1px solid #e8edf4; }
    .funnel-card:last-child { border-bottom:0; }
    .stage-name { font-weight:750; font-size:13px; }
    .bar-bg { height:30px; border-radius:7px; background:#e7edf5; overflow:hidden; position:relative; }
    .bar { height:100%; border-radius:7px; background:linear-gradient(90deg,var(--cyan),var(--teal)); }
    .stage-value { text-align:right; font-weight:750; }
    .stage-cvr { text-align:right; color:var(--muted); font-size:12px; }
    .leak { color:var(--rose); font-size:11px; margin-top:3px; }
    .trend-wrap { height:236px; }
    svg { width:100%; height:100%; overflow:visible; }
    table { width:100%; border-collapse:collapse; font-size:12px; }
    th, td { padding:8px 7px; border-bottom:1px solid #e8edf4; text-align:right; white-space:nowrap; }
    th:first-child, td:first-child { text-align:left; white-space:normal; }
    th { color:#344054; background:#f1f5f9; font-weight:750; }
    tr:hover td { background:#fbfdff; }
    .rank { display:grid; gap:10px; }
    .rank-row { display:grid; grid-template-columns:130px 1fr 70px; align-items:center; gap:9px; }
    .rank-name { font-size:12px; font-weight:700; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
    .rank-track { height:12px; border-radius:5px; background:#e8edf4; overflow:hidden; }
    .rank-fill { display:block; height:100%; background:var(--blue); border-radius:5px; }
    .rank-value { text-align:right; color:#344054; font-size:12px; }
    .watchlist { display:grid; gap:9px; }
    .watch { border-left:4px solid var(--rose); background:#fff7f8; border-radius:7px; padding:10px 11px; }
    .watch strong { display:block; font-size:13px; }
    .watch span { color:#667085; font-size:12px; }
    .mix-row { display:grid; grid-template-columns:126px 1fr 74px; gap:9px; align-items:center; margin:10px 0; }
    .mix-dot { width:8px; height:8px; display:inline-block; border-radius:99px; margin-right:6px; background:var(--cyan); }
    .footer-note { color:#667085; font-size:11px; margin-top:12px; }
    @media (max-width: 1120px) {
      .shell { grid-template-columns:1fr; }
      aside { position:static; }
      .metric-strip, .grid-3, .grid-main, .grid-2 { grid-template-columns:1fr; }
      .topbar { grid-template-columns:1fr; }
      .insight-pill { min-width:0; }
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
      </div>
      <div class="filters">
        <div><label>Device</label><select id="deviceFilter"></select></div>
        <div><label>Channel</label><select id="channelFilter"></select></div>
        <div><label>Campaign</label><select id="campaignFilter"></select></div>
        <div><label>Category</label><select id="categoryFilter"></select></div>
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
          <h1 class="title">Customer Funnel Command Center</h1>
          <div class="subtitle">Visit → Product View → Add to Cart → Checkout → Purchase</div>
        </div>
        <div class="insight-pill">
          <strong id="primaryInsight">Largest leak is loading...</strong>
          <span id="secondaryInsight">Segment and campaign watchpoints refresh from the dashboard payload.</span>
        </div>
      </div>

      <section class="page active" id="p1">
        <div class="metric-strip" id="kpiCards"></div>
        <div class="grid-main">
          <div class="panel">
            <h2>Cart progression is the key conversion choke point</h2>
            <div class="note">Stage count, step retention, and immediate leakage.</div>
            <div id="funnel"></div>
          </div>
          <div class="panel">
            <h2>Conversion trend stays stable with promo bumps</h2>
            <div class="note">Monthly CVR, indexed against peak month.</div>
            <div class="trend-wrap"><svg id="trend"></svg></div>
          </div>
        </div>
        <div class="grid-3">
          <div class="panel"><h2>Revenue channels</h2><div class="note">Top sources by net revenue.</div><div id="execChannelSnapshot"></div></div>
          <div class="panel"><h2>Category pressure</h2><div class="note">Purchase volume and CVR quality.</div><div id="execCategorySnapshot"></div></div>
          <div class="panel"><h2>Leakage watchlist</h2><div class="note">Highest-value funnel risks.</div><div id="watchlist"></div></div>
        </div>
      </section>

      <section class="page" id="p2">
        <div class="grid-2">
          <div class="panel"><h2>Mobile traffic needs checkout recovery</h2><div class="note">Device conversion and revenue shape.</div><div id="deviceTable"></div></div>
          <div class="panel"><h2>Email and search carry conversion quality</h2><div class="note">Channel volume, CVR, and AOV.</div><div id="channelTable"></div></div>
        </div>
        <div class="panel" style="margin-top:14px"><h2>Campaign drilldown</h2><div class="note">Revenue, conversion, and paid efficiency ranked together.</div><div id="campaignTable"></div></div>
      </section>

      <section class="page" id="p3">
        <div class="grid-2">
          <div class="panel"><h2>Category funnel matrix</h2><div class="note">Stage leakage by merchandising group.</div><div id="categoryTable"></div></div>
          <div class="panel"><h2>Revenue concentration</h2><div class="note">Categories ranked by revenue and AOV.</div><div id="categoryBars"></div></div>
        </div>
      </section>

      <section class="page" id="p4">
        <div class="grid-2">
          <div class="panel"><h2>Paid efficiency board</h2><div class="note">Spend, ROAS, CAC, and conversion in one view.</div><div id="efficiencyTable"></div></div>
          <div class="panel"><h2>Channel revenue mix</h2><div class="note">Revenue distribution across acquisition sources.</div><div id="mix"></div></div>
        </div>
      </section>
      <div class="footer-note">Synthetic portfolio data. Funnel KPIs are session-based; raw duplicate product views are excluded from stage conversion.</div>
    </main>
  </div>
  <script>
    const DATA = __DATA__;
    const fmtInt = n => Math.round(n || 0).toLocaleString();
    const fmtMoney = n => '$' + Math.round(n || 0).toLocaleString();
    const fmtPct = n => ((n || 0) * 100).toFixed(1) + '%';
    const fmtNum = n => n == null ? '-' : Number(n).toFixed(2);
    const colors = ['#0e7490','#0f766e','#d97706','#7c3aed','#be123c','#2563eb','#15803d'];

    function populateFilters() {
      [['deviceFilter','device'], ['channelFilter','channel'], ['campaignFilter','campaign'], ['categoryFilter','category']].forEach(([id,key]) => {
        const el = document.getElementById(id);
        el.innerHTML = '<option value="All">All</option>' + DATA.filters[key].map(v => `<option>${v}</option>`).join('');
      });
    }
    function filteredRows(kind) {
      const rows = DATA[kind];
      const selected = {
        device: document.getElementById('deviceFilter').value,
        channel: document.getElementById('channelFilter').value,
        campaign: document.getElementById('campaignFilter').value,
        category: document.getElementById('categoryFilter').value
      };
      const dimension = kind === 'device' ? 'device' : kind === 'channel' ? 'channel' : kind === 'campaign' ? 'campaign' : kind === 'category' ? 'category' : null;
      if (!dimension || selected[dimension] === 'All') return rows;
      return rows.filter(r => r.segment === selected[dimension]);
    }
    function table(rows, cols) {
      return '<table><thead><tr>' + cols.map(c => `<th>${c[0]}</th>`).join('') + '</tr></thead><tbody>' +
        rows.map(r => '<tr>' + cols.map(c => `<td>${c[1](r)}</td>`).join('') + '</tr>').join('') + '</tbody></table>';
    }
    function renderKpis() {
      const k = DATA.kpis;
      const cards = [
        ['Visits', fmtInt(k.visits), 'Entry volume', '#0e7490'],
        ['Product Views', fmtInt(k.product_views), fmtPct(k.product_views / k.visits) + ' of visits', '#0f766e'],
        ['Add to Cart', fmtInt(k.add_to_carts), fmtPct(k.add_to_carts / k.product_views) + ' view retention', '#d97706'],
        ['Checkout', fmtInt(k.checkouts), fmtPct(k.checkouts / k.add_to_carts) + ' cart retention', '#7c3aed'],
        ['Purchases', fmtInt(k.purchases), fmtPct(k.purchases / k.checkouts) + ' checkout retention', '#15803d'],
        ['Revenue', fmtMoney(k.revenue), fmtMoney(k.revenue / k.visits) + ' per visit', '#2563eb'],
        ['Overall CVR', fmtPct(k.overall_conversion_rate), 'visit to purchase', '#be123c'],
        ['AOV', fmtMoney(k.aov), 'net revenue / orders', '#0f766e']
      ];
      document.getElementById('kpiCards').innerHTML = cards.map(([label,value,sub,color]) =>
        `<div class="metric" style="--accent:${color}"><div class="label">${label}</div><div class="value">${value}</div><div class="sub"><span>${sub}</span></div></div>`
      ).join('');
      document.getElementById('healthScore').textContent = Math.round(k.overall_conversion_rate * 1000);
    }
    function renderInsights() {
      const f = DATA.funnel;
      const leaks = f.slice(0, -1).map((row, i) => ({ from: row.stage, to: f[i+1].stage, loss: row.sessions - f[i+1].sessions, rate: (row.sessions - f[i+1].sessions) / row.sessions }));
      leaks.sort((a,b) => b.loss - a.loss);
      const top = leaks[0];
      document.getElementById('primaryInsight').textContent = `${top.from} → ${top.to} loses ${fmtInt(top.loss)} sessions`;
      document.getElementById('secondaryInsight').textContent = `${fmtPct(top.rate)} step drop-off; prioritize page-to-cart activation.`;
      document.getElementById('watchlist').innerHTML = leaks.slice(0, 4).map(l =>
        `<div class="watch"><strong>${l.from} → ${l.to}</strong><span>${fmtInt(l.loss)} lost sessions · ${fmtPct(l.rate)} drop-off</span></div>`
      ).join('');
    }
    function renderFunnel() {
      const max = DATA.funnel[0].sessions;
      const f = DATA.funnel;
      document.getElementById('funnel').innerHTML = f.map((row, i) => {
        const width = Math.max(2, row.sessions / max * 100);
        const retention = i === 0 ? 1 : row.sessions / f[i-1].sessions;
        const leak = i < f.length - 1 ? `<div class="leak">Next drop: ${fmtInt(row.sessions - f[i+1].sessions)}</div>` : '<div class="leak" style="color:#15803d">Converted sessions</div>';
        return `<div class="funnel-card"><div><div class="stage-name">${row.stage}</div>${leak}</div><div class="bar-bg"><div class="bar" style="width:${width}%"></div></div><div class="stage-value">${fmtInt(row.sessions)}</div><div class="stage-cvr">${i === 0 ? '100.0%' : fmtPct(retention)}</div></div>`;
      }).join('');
    }
    function renderTrend() {
      const svg = document.getElementById('trend');
      const rows = DATA.monthly;
      const box = svg.getBoundingClientRect();
      const w = Math.max(360, box.width || 560), h = Math.max(200, box.height || 220), pad = 28;
      const maxCv = Math.max(...rows.map(r => r.conversion_rate));
      const minCv = Math.min(...rows.map(r => r.conversion_rate));
      const pts = rows.map((r,i) => {
        const x = pad + i * ((w - pad * 2) / Math.max(1, rows.length - 1));
        const y = h - pad - ((r.conversion_rate - minCv) / Math.max(.0001, maxCv - minCv)) * (h - pad * 2);
        return [x,y,r];
      });
      const path = pts.map((p,i) => `${i?'L':'M'}${p[0].toFixed(1)},${p[1].toFixed(1)}`).join(' ');
      const area = `${path} L ${pts[pts.length-1][0]},${h-pad} L ${pts[0][0]},${h-pad} Z`;
      svg.innerHTML = `<path d="${area}" fill="#dbeafe"></path><path d="${path}" fill="none" stroke="#0e7490" stroke-width="3"></path>` +
        pts.map((p,i) => `<circle cx="${p[0]}" cy="${p[1]}" r="${i%3===0?4:3}" fill="#d97706"><title>${p[2].month_start} ${fmtPct(p[2].conversion_rate)}</title></circle>`).join('') +
        `<text x="${pad}" y="18" font-size="11" fill="#667085">${fmtPct(maxCv)} peak</text><text x="${pad}" y="${h-8}" font-size="11" fill="#667085">${fmtPct(minCv)} low</text>`;
    }
    function renderSegmentTables() {
      const cols = [['Segment', r => r.segment], ['Visits', r => fmtInt(r.visits)], ['Purchases', r => fmtInt(r.purchases)], ['CVR', r => fmtPct(r.conversion_rate)], ['Revenue', r => fmtMoney(r.revenue)], ['AOV', r => fmtMoney(r.aov)]];
      document.getElementById('deviceTable').innerHTML = table(filteredRows('device'), cols);
      document.getElementById('channelTable').innerHTML = table(filteredRows('channel'), cols);
      document.getElementById('campaignTable').innerHTML = table(filteredRows('campaign').slice(0, 14), [...cols, ['ROAS', r => fmtNum(r.roas)]]);
      document.getElementById('execChannelSnapshot').innerHTML = table(DATA.channel.slice(0, 5), [['Channel', r => r.segment], ['CVR', r => fmtPct(r.conversion_rate)], ['Revenue', r => fmtMoney(r.revenue)]]);
      document.getElementById('execCategorySnapshot').innerHTML = table(DATA.category.slice(0, 5), [['Category', r => r.segment], ['Purchase', r => fmtInt(r.purchases)], ['CVR', r => fmtPct(r.conversion_rate)]]);
      document.getElementById('categoryTable').innerHTML = table(filteredRows('category'), [['Category', r => r.segment], ['Visits', r => fmtInt(r.visits)], ['Views', r => fmtInt(r.product_views)], ['Cart', r => fmtInt(r.add_to_carts)], ['Checkout', r => fmtInt(r.checkouts)], ['Purchase', r => fmtInt(r.purchases)], ['CVR', r => fmtPct(r.conversion_rate)]]);
    }
    function renderBars() {
      const rows = filteredRows('category');
      const max = Math.max(...rows.map(r => r.revenue));
      document.getElementById('categoryBars').innerHTML = `<div class="rank">` + rows.map((r,i) =>
        `<div class="rank-row"><div class="rank-name">${r.segment}</div><div class="rank-track"><span class="rank-fill" style="background:${colors[i%colors.length]};width:${Math.max(3, r.revenue / max * 100)}%"></span></div><div class="rank-value">${fmtMoney(r.revenue)}</div></div>`
      ).join('') + `</div>`;
    }
    function renderEfficiency() {
      const rows = DATA.campaign.filter(r => r.spend > 0).sort((a,b) => (b.roas || 0) - (a.roas || 0));
      document.getElementById('efficiencyTable').innerHTML = table(rows, [['Campaign', r => r.segment], ['Spend', r => fmtMoney(r.spend)], ['Revenue', r => fmtMoney(r.revenue)], ['ROAS', r => fmtNum(r.roas)], ['CAC', r => fmtMoney(r.spend / Math.max(1, r.purchases))], ['CVR', r => fmtPct(r.conversion_rate)]]);
      const total = DATA.channel.reduce((s,r) => s + r.revenue, 0);
      document.getElementById('mix').innerHTML = DATA.channel.map((r,i) =>
        `<div class="mix-row"><div><span class="mix-dot" style="background:${colors[i%colors.length]}"></span>${r.segment}</div><div class="rank-track"><span class="rank-fill" style="background:${colors[i%colors.length]};width:${Math.max(2, r.revenue / total * 100)}%"></span></div><div class="rank-value">${fmtMoney(r.revenue)}</div></div>`
      ).join('');
    }
    function renderAll() { renderKpis(); renderInsights(); renderFunnel(); renderTrend(); renderSegmentTables(); renderBars(); renderEfficiency(); }
    populateFilters();
    renderAll();
    ['deviceFilter','channelFilter','campaignFilter','categoryFilter'].forEach(id => document.getElementById(id).addEventListener('change', renderAll));
    document.querySelectorAll('.tab').forEach(btn => btn.addEventListener('click', () => {
      document.querySelectorAll('.tab').forEach(b => b.classList.remove('active'));
      document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
      btn.classList.add('active');
      document.getElementById(btn.dataset.page).classList.add('active');
      requestAnimationFrame(renderAll);
    }));
  </script>
</body>
</html>
"""


if __name__ == "__main__":
    main()
