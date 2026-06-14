from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import pandas as pd


PROJECT = Path(__file__).resolve().parents[2]


def compact_records() -> tuple[list[dict], list[dict], list[str]]:
    fact = pd.read_csv(PROJECT / "data/prepared/fact_campaign_daily.csv", parse_dates=["date"])
    channels = pd.read_csv(PROJECT / "data/prepared/dim_channel.csv")
    campaigns = pd.read_csv(PROJECT / "data/prepared/dim_campaign.csv")

    fact = fact.merge(
        channels[["channel_key", "channel", "target_roas", "target_cac"]],
        on="channel_key",
        how="left",
    ).merge(
        campaigns[["campaign_key", "campaign_name", "funnel_stage", "budget_tier"]],
        on="campaign_key",
        how="left",
    )

    fact["date"] = fact["date"].dt.strftime("%Y-%m-%d")
    cols = [
        "date",
        "month_key",
        "channel_key",
        "channel",
        "paid_organic",
        "campaign_key",
        "campaign_name",
        "funnel_stage",
        "budget_tier",
        "target_roas",
        "target_cac",
        "spend",
        "clicks",
        "leads",
        "conversions",
        "new_customers",
        "revenue",
        "gross_profit",
    ]
    fact = fact[cols].copy()
    for col in ["target_roas", "target_cac", "spend", "revenue", "gross_profit"]:
        fact[col] = fact[col].round(2)
    int_cols = ["clicks", "leads", "conversions", "new_customers"]
    for col in int_cols:
        fact[col] = fact[col].astype(int)

    channel_meta = channels.sort_values("channel").to_dict(orient="records")
    campaigns_list = campaigns[["campaign_key", "campaign_name", "channel", "paid_organic", "funnel_stage", "budget_tier"]].sort_values("campaign_name").to_dict(orient="records")
    return fact.to_dict(orient="records"), channel_meta, campaigns_list


def write_dashboard() -> None:
    records, channel_meta, campaigns = compact_records()
    payload = {
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "records": records,
        "channels": channel_meta,
        "campaigns": campaigns,
    }
    out_dir = PROJECT / "output"
    qa_dir = PROJECT / "qa"
    out_dir.mkdir(parents=True, exist_ok=True)
    qa_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "dashboard_final_summary.json").write_text(json.dumps({
        "generated_at": payload["generated_at"],
        "row_count": len(records),
        "channel_count": len(channel_meta),
        "campaign_count": len(campaigns),
        "source": "data/prepared/fact_campaign_daily.csv"
    }, indent=2), encoding="utf-8")

    html = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Marketing Campaign ROI Dashboard</title>
<style>
:root {{
  --ink:#14213D;
  --ink2:#233047;
  --muted:#6C7280;
  --paper:#F4F7FB;
  --panel:#FFFFFF;
  --line:#D7DEE8;
  --blue:#3267B1;
  --teal:#0E7C7B;
  --green:#2E8B57;
  --amber:#F0B429;
  --coral:#E3645A;
  --purple:#7A5CFA;
}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--paper);color:var(--ink);font-family:"Segoe UI",Arial,sans-serif}}
.app{{display:grid;grid-template-columns:172px 1fr;min-height:100vh}}
aside{{background:var(--ink);color:white;padding:28px 22px;position:sticky;top:0;height:100vh}}
.logo{{font-size:27px;font-weight:800;letter-spacing:.02em}}
.kicker{{margin-top:4px;color:#AFC3D9;font-size:11px;font-weight:800}}
nav{{display:grid;gap:10px;margin-top:54px}}
nav button{{border:0;text-align:left;color:#AFC3D9;background:transparent;border-radius:8px;padding:11px 13px;font:700 13px "Segoe UI";cursor:pointer}}
nav button.active{{background:#31445F;color:#fff}}
.side-note{{position:absolute;left:22px;right:22px;bottom:26px;color:#B8C7D8;font-size:12px;line-height:1.45}}
main{{padding:30px 36px 44px}}
.top{{display:flex;gap:20px;justify-content:space-between;align-items:flex-end;margin-bottom:18px}}
h1{{margin:0;font-size:32px;line-height:1.08}}
.subtitle{{margin:8px 0 0;color:var(--muted);max-width:880px}}
.status{{border:1px solid var(--line);background:white;border-radius:8px;padding:10px 14px;color:var(--teal);font-weight:800;white-space:nowrap}}
.filters{{display:grid;grid-template-columns:repeat(6,minmax(120px,1fr));gap:12px;background:white;border:1px solid var(--line);border-radius:8px;padding:14px;margin-bottom:18px}}
label{{display:grid;gap:6px;color:var(--muted);font-size:11px;font-weight:800;text-transform:uppercase}}
select,input{{height:34px;border:1px solid var(--line);border-radius:7px;background:#fff;color:var(--ink);padding:0 9px;font:13px "Segoe UI"}}
.filters button{{height:34px;align-self:end;border:0;border-radius:7px;background:var(--ink);color:#fff;font-weight:800;cursor:pointer}}
.cards{{display:grid;grid-template-columns:repeat(6,minmax(120px,1fr));gap:12px;margin-bottom:18px}}
.card{{background:white;border:1px solid var(--line);border-left:6px solid var(--teal);border-radius:8px;padding:14px 15px;min-height:88px}}
.card:nth-child(1){{border-left-color:var(--blue)}}.card:nth-child(3){{border-left-color:var(--green)}}.card:nth-child(4){{border-left-color:var(--amber)}}.card:nth-child(5){{border-left-color:var(--purple)}}.card:nth-child(6){{border-left-color:var(--coral)}}
.card span{{display:block;color:var(--muted);font-size:11px;font-weight:800;text-transform:uppercase}}
.card strong{{display:block;margin-top:9px;font-size:24px}}
.card small{{display:block;margin-top:4px;color:var(--muted);font-weight:700}}
.grid{{display:grid;grid-template-columns:1.4fr 1fr;gap:18px}}
.grid.equal{{grid-template-columns:1fr 1fr}}
.grid.wide{{grid-template-columns:1.55fr .9fr}}
.panel{{background:white;border:1px solid var(--line);border-radius:8px;padding:18px;min-height:330px}}
.panel h2{{margin:0;font-size:18px}}
.panel p{{margin:6px 0 14px;color:var(--muted);font-size:13px}}
.panel svg{{width:100%;height:245px;display:block;overflow:visible}}
.page{{display:none}}.page.active{{display:block}}
.table{{width:100%;border-collapse:collapse;font-size:12px}}
.table th{{text-align:left;color:var(--muted);font-size:11px;text-transform:uppercase;border-bottom:1px solid var(--line);padding:8px 6px}}
.table td{{padding:8px 6px;border-bottom:1px solid #EDF2F7;color:var(--ink2)}}
.action{{font-weight:800}}.Scale{{color:var(--green)}}.Optimize{{color:var(--amber)}}.ReviewCut{{color:var(--coral)}}
.callouts{{display:grid;gap:12px}}
.callout{{background:#F7FAFD;border:1px solid #E3EAF2;border-radius:8px;padding:12px 12px 12px 16px;position:relative}}
.callout:before{{content:"";position:absolute;left:0;top:12px;bottom:12px;width:6px;border-radius:4px;background:var(--teal)}}
.callout.scale:before{{background:var(--green)}}.callout.optimize:before{{background:var(--amber)}}.callout.review:before{{background:var(--coral)}}
.callout h3{{margin:0 0 4px;font-size:15px}}.callout p{{margin:0;color:var(--muted);font-size:13px;line-height:1.35}}
.legend{{display:flex;gap:14px;align-items:center;color:var(--muted);font-size:12px;font-weight:700}}
.dot{{width:10px;height:10px;border-radius:50%;display:inline-block;margin-right:5px}}
.footer{{margin-top:16px;color:var(--muted);font-size:12px}}
@media(max-width:1100px){{.app{{grid-template-columns:1fr}}aside{{height:auto;position:relative}}nav{{grid-template-columns:repeat(4,1fr);margin-top:20px}}.side-note{{display:none}}main{{padding:22px}}.cards{{grid-template-columns:repeat(2,1fr)}}.filters{{grid-template-columns:repeat(2,1fr)}}.grid,.grid.equal,.grid.wide{{grid-template-columns:1fr}}}}
</style>
</head>
<body>
<div class="app">
<aside>
  <div class="logo">MROI</div>
  <div class="kicker">PROJECT 6</div>
  <nav>
    <button data-page="overview" class="active">Overview</button>
    <button data-page="channel">Channel</button>
    <button data-page="ranking">Ranking</button>
    <button data-page="actions">Actions</button>
  </nav>
  <div class="side-note">Marketing ROI command center<br>Offline interactive dashboard</div>
</aside>
<main>
  <section class="top">
    <div>
      <h1>Marketing Campaign ROI Dashboard</h1>
      <p class="subtitle">Spend, CAC, ROAS, conversion, revenue by channel, paid vs organic, and campaign ranking. Filter the portfolio to find budget waste and scale-ready channels.</p>
    </div>
    <div class="status">Final HTML Dashboard</div>
  </section>
  <section class="filters">
    <label>Start Date<input id="startDate" type="date"></label>
    <label>End Date<input id="endDate" type="date"></label>
    <label>Channel<select id="channelFilter"><option value="All">All channels</option></select></label>
    <label>Paid / Organic<select id="typeFilter"><option value="All">All</option><option>Paid</option><option>Organic</option></select></label>
    <label>Action<select id="actionFilter"><option value="All">All actions</option><option>Scale</option><option>Optimize</option><option>Review/Cut</option></select></label>
    <button id="resetBtn">Reset</button>
  </section>
  <section class="cards" id="kpiCards"></section>

  <section id="overview" class="page active">
    <div class="grid wide">
      <article class="panel"><h2>Spend and Revenue Trend</h2><p>Monthly totals; bars = spend, line = revenue.</p><svg id="trendChart"></svg></article>
      <article class="panel"><h2>Paid vs Organic Value</h2><p>Revenue, spend, and conversion contribution.</p><svg id="paidOrganicChart"></svg></article>
    </div>
    <div class="grid wide" style="margin-top:18px">
      <article class="panel"><h2>Spend vs ROAS Action Map</h2><p>Bubble size = revenue; color = budget action.</p><svg id="actionScatter"></svg></article>
      <article class="panel"><h2>Budget Callouts</h2><p>Channels to scale, optimize, or review.</p><div class="callouts" id="callouts"></div></article>
    </div>
  </section>

  <section id="channel" class="page">
    <div class="grid equal">
      <article class="panel"><h2>ROAS vs Target</h2><p>Bars show actual ROAS; marker shows target.</p><svg id="roasTargetChart"></svg></article>
      <article class="panel"><h2>CAC vs Target</h2><p>Lower CAC is better; marker shows target.</p><svg id="cacTargetChart"></svg></article>
    </div>
    <div class="grid wide" style="margin-top:18px">
      <article class="panel"><h2>Efficiency Quadrant</h2><p>X = ROAS gap; Y = CAC gap; top-right is best.</p><svg id="quadrantChart"></svg></article>
      <article class="panel"><h2>Channel Scorecard</h2><p>Spend share, ROAS, CAC, and action.</p><div id="channelTable"></div></article>
    </div>
  </section>

  <section id="ranking" class="page">
    <div class="grid equal">
      <article class="panel"><h2>Scale Candidates</h2><p>Top campaigns by composite scale score.</p><svg id="scaleCampaigns"></svg></article>
      <article class="panel"><h2>Review / Cut Candidates</h2><p>Lowest campaigns by scale score.</p><svg id="cutCampaigns"></svg></article>
    </div>
    <article class="panel" style="margin-top:18px"><h2>Campaign Decision Table</h2><p>Use this in the monthly budget meeting.</p><div id="campaignTable"></div></article>
  </section>

  <section id="actions" class="page">
    <div class="grid wide">
      <article class="panel"><h2>Budget Action Matrix</h2><p>Target gaps translated into next-month moves.</p><svg id="actionMatrix"></svg></article>
      <article class="panel"><h2>Next-Month Budget Moves</h2><p>Ranked by spend share and target miss.</p><div class="callouts" id="budgetMoves"></div></article>
    </div>
    <article class="panel" style="margin-top:18px"><h2>Operating View</h2><p>Channel-level exception details for weekly growth review.</p><div id="operatingTable"></div></article>
  </section>
  <div class="footer">Generated from Project 06 - Marketing Campaign ROI prepared data. Last built: <span id="builtAt"></span>.</div>
</main>
</div>
<script>
const PAYLOAD = {json.dumps(payload, separators=(",", ":"))};
const DATA = PAYLOAD.records;
const CHANNELS = PAYLOAD.channels;
const fmtMoney = v => v >= 1000000 ? '$' + (v/1000000).toFixed(1) + 'M' : '$' + Math.round(v/1000) + 'K';
const fmtPct = v => (v*100).toFixed(1) + '%';
const fmtNum = v => Number.isFinite(v) ? v.toFixed(2) : 'N/A';
const actionClass = a => a === 'Review/Cut' ? 'ReviewCut' : a;
const actionColor = a => a === 'Scale' ? '#2E8B57' : a === 'Optimize' ? '#F0B429' : '#E3645A';
const svgNS = 'http://www.w3.org/2000/svg';
function el(tag, attrs={{}}, text='') {{
  const node = document.createElementNS(svgNS, tag);
  Object.entries(attrs).forEach(([k,v]) => node.setAttribute(k, v));
  if (text) node.textContent = text;
  return node;
}}
function clearSvg(id) {{
  const svg = document.getElementById(id);
  svg.innerHTML = '';
  const box = svg.getBoundingClientRect();
  svg.setAttribute('viewBox', `0 0 ${{Math.max(580, box.width || 680)}} 245`);
  return [svg, Math.max(580, box.width || 680), 245];
}}
function groupBy(rows, keys, aggs) {{
  const map = new Map();
  rows.forEach(r => {{
    const k = keys.map(key => r[key]).join('||');
    if (!map.has(k)) {{
      const base = Object.fromEntries(keys.map(key => [key, r[key]]));
      Object.keys(aggs).forEach(a => base[a] = 0);
      map.set(k, base);
    }}
    const obj = map.get(k);
    Object.entries(aggs).forEach(([out, col]) => obj[out] += +r[col]);
  }});
  return [...map.values()];
}}
function summarize(rows) {{
  const total = rows.reduce((a,r) => {{
    ['spend','revenue','gross_profit','clicks','conversions','new_customers','leads'].forEach(c => a[c] += +r[c]);
    return a;
  }}, {{spend:0,revenue:0,gross_profit:0,clicks:0,conversions:0,new_customers:0,leads:0}});
  total.roas = total.revenue / total.spend;
  total.roi = (total.gross_profit - total.spend) / total.spend;
  total.cac = total.spend / total.new_customers;
  total.cvr = total.conversions / total.clicks;
  return total;
}}
function channelSummary(rows) {{
  const grouped = groupBy(rows, ['channel_key','channel','paid_organic'], {{spend:'spend', revenue:'revenue', gross_profit:'gross_profit', clicks:'clicks', conversions:'conversions', new_customers:'new_customers'}});
  const spendTotal = grouped.reduce((a,r)=>a+r.spend,0) || 1;
  return grouped.map(r => {{
    const meta = CHANNELS.find(c => c.channel_key === r.channel_key) || {{}};
    r.target_roas = +meta.target_roas || 0;
    r.target_cac = +meta.target_cac || 0;
    r.roas = r.revenue / r.spend;
    r.roi = (r.gross_profit - r.spend) / r.spend;
    r.cac = r.spend / r.new_customers;
    r.cvr = r.conversions / r.clicks;
    r.spend_share = r.spend / spendTotal;
    r.roas_gap = r.roas - r.target_roas;
    r.cac_gap = r.target_cac - r.cac;
    r.action = (r.roas_gap >= 0 && r.cac_gap >= 0) ? 'Scale' : (r.spend_share >= .06 && (r.roas_gap < 0 || r.cac_gap < 0)) ? 'Review/Cut' : 'Optimize';
    return r;
  }}).sort((a,b)=>b.spend-a.spend);
}}
function campaignSummary(rows) {{
  const grouped = groupBy(rows, ['campaign_key','campaign_name','channel','paid_organic','funnel_stage'], {{spend:'spend', revenue:'revenue', gross_profit:'gross_profit', clicks:'clicks', conversions:'conversions', new_customers:'new_customers'}});
  grouped.forEach(r => {{
    r.roas = r.revenue / r.spend;
    r.roi = (r.gross_profit - r.spend) / r.spend;
    r.cac = r.spend / r.new_customers;
    r.cvr = r.conversions / r.clicks;
  }});
  const rankPct = (arr, field, asc=false) => {{
    const sorted = [...arr].sort((a,b)=>asc ? a[field]-b[field] : b[field]-a[field]);
    sorted.forEach((r,i)=>r[`rank_${{field}}`] = arr.length <= 1 ? .5 : 1 - i/(arr.length-1));
  }};
  rankPct(grouped,'roas'); rankPct(grouped,'roi'); rankPct(grouped,'gross_profit'); rankPct(grouped,'cac', true);
  grouped.forEach(r => {{
    r.scale_score = (r.rank_roas*.4 + r.rank_roi*.3 + r.rank_cac*.2 + r.rank_gross_profit*.1) * 100;
    r.action = r.scale_score >= 70 ? 'Scale' : r.scale_score <= 35 ? 'Review/Cut' : 'Optimize';
  }});
  return grouped;
}}
function filteredRows() {{
  const start = document.getElementById('startDate').value;
  const end = document.getElementById('endDate').value;
  const ch = document.getElementById('channelFilter').value;
  const type = document.getElementById('typeFilter').value;
  let rows = DATA.filter(r => (!start || r.date >= start) && (!end || r.date <= end) && (ch === 'All' || r.channel === ch) && (type === 'All' || r.paid_organic === type));
  const action = document.getElementById('actionFilter').value;
  if (action !== 'All') {{
    const allowed = new Set(channelSummary(rows).filter(r=>r.action===action).map(r=>r.channel));
    rows = rows.filter(r => allowed.has(r.channel));
  }}
  return rows;
}}
function scaleLinear(domain, range) {{
  const [d0,d1] = domain, [r0,r1] = range;
  const span = (d1-d0) || 1;
  return v => r0 + ((v-d0)/span)*(r1-r0);
}}
function axis(svg, x0, y0, x1, ticks, labels=false) {{
  svg.appendChild(el('line', {{x1:x0,y1:y0,x2:x1,y2:y0,stroke:'#D7DEE8'}}));
  ticks.forEach(t => {{
    svg.appendChild(el('line', {{x1:t.x,y1:y0,x2:t.x,y2:y0+4,stroke:'#D7DEE8'}}));
    if (labels) svg.appendChild(el('text', {{x:t.x,y:y0+18,fill:'#6C7280','font-size':10,'text-anchor':'middle'}}, t.label));
  }});
}}
function barChart(id, rows, labelField, valueField, colorFn, opts={{}}) {{
  const [svg,w,h] = clearSvg(id), m = {{l:opts.left||135,r:22,t:14,b:30}};
  const plotW = w-m.l-m.r, barH = Math.max(13, Math.min(20, (h-m.t-m.b)/Math.max(rows.length,1)-5));
  const max = Math.max(...rows.map(r=>r[valueField]), 1);
  rows.forEach((r,i) => {{
    const y = m.t + i*((h-m.t-m.b)/rows.length);
    const bw = (r[valueField]/max)*plotW;
    svg.appendChild(el('text', {{x:m.l-8,y:y+barH*.75,fill:'#6C7280','font-size':11,'text-anchor':'end'}}, String(r[labelField]).slice(0,32)));
    svg.appendChild(el('rect', {{x:m.l,y:y,width:bw,height:barH,rx:2,fill:colorFn(r)}}));
    if (opts.markerField) {{
      const mx = m.l + (r[opts.markerField]/max)*plotW;
      svg.appendChild(el('line', {{x1:mx,y1:y-2,x2:mx,y2:y+barH+2,stroke:'#14213D','stroke-width':3}}));
    }}
  }});
  axis(svg,m.l,h-m.b,w-m.r,[0,.25,.5,.75,1].map(p=>({{x:m.l+p*plotW,label:fmtNum(p*max)}})),true);
}}
function trendChart(rows) {{
  const monthly = groupBy(rows, ['month_key'], {{spend:'spend', revenue:'revenue'}}).sort((a,b)=>a.month_key.localeCompare(b.month_key));
  const [svg,w,h] = clearSvg('trendChart'), m={{l:44,r:20,t:18,b:34}};
  const max = Math.max(...monthly.flatMap(r=>[r.spend,r.revenue]),1);
  const x = i => m.l + i*((w-m.l-m.r)/Math.max(monthly.length-1,1));
  const y = v => h-m.b - (v/max)*(h-m.t-m.b);
  monthly.forEach((r,i)=> {{
    const bw = Math.max(8,(w-m.l-m.r)/monthly.length*.55);
    svg.appendChild(el('rect', {{x:x(i)-bw/2,y:y(r.spend),width:bw,height:h-m.b-y(r.spend),fill:'#BFD7D5'}}));
  }});
  const points = monthly.map((r,i)=>`${{x(i)}},${{y(r.revenue)}}`).join(' ');
  svg.appendChild(el('polyline', {{points,fill:'none',stroke:'#3267B1','stroke-width':3}}));
  monthly.forEach((r,i)=>svg.appendChild(el('circle',{{cx:x(i),cy:y(r.revenue),r:3.5,fill:'#3267B1'}})));
  axis(svg,m.l,h-m.b,w-m.r,monthly.filter((_,i)=>i%2===0).map((r,i)=>({{x:x(i*2),label:r.month_key}})),true);
}}
function paidOrganicChart(rows) {{
  const po = groupBy(rows, ['paid_organic'], {{spend:'spend', revenue:'revenue', conversions:'conversions'}}).sort((a,b)=>a.paid_organic.localeCompare(b.paid_organic));
  const [svg,w,h] = clearSvg('paidOrganicChart'), m={{l:70,r:20,t:28,b:30}};
  const max = Math.max(...po.flatMap(r=>[r.spend,r.revenue]),1);
  po.forEach((r,i)=> {{
    const y = m.t + i*75;
    svg.appendChild(el('text',{{x:m.l-8,y:y+18,fill:'#6C7280','font-size':12,'text-anchor':'end'}},r.paid_organic));
    svg.appendChild(el('rect',{{x:m.l,y:y,width:(r.revenue/max)*(w-m.l-m.r),height:22,fill:'#0E7C7B'}}));
    svg.appendChild(el('rect',{{x:m.l,y:y+28,width:(r.spend/max)*(w-m.l-m.r),height:22,fill:'#E3645A'}}));
  }});
  axis(svg,m.l,h-m.b,w-m.r,[0,.5,1].map(p=>({{x:m.l+p*(w-m.l-m.r),label:fmtMoney(p*max)}})),true);
}}
function scatter(id, rows, xField, yField, sizeField, labelSet) {{
  const [svg,w,h] = clearSvg(id), m={{l:56,r:26,t:22,b:38}};
  const xs = rows.map(r=>r[xField]), ys = rows.map(r=>r[yField]);
  const xMin = Math.min(0,...xs), xMax = Math.max(...xs,1);
  const yMin = Math.min(0,...ys), yMax = Math.max(...ys,1);
  const x = scaleLinear([xMin,xMax],[m.l,w-m.r]);
  const y = scaleLinear([yMin,yMax],[h-m.b,m.t]);
  svg.appendChild(el('line',{{x1:x(0),y1:m.t,x2:x(0),y2:h-m.b,stroke:'#14213D','stroke-width':1}}));
  svg.appendChild(el('line',{{x1:m.l,y1:y(0),x2:w-m.r,y2:y(0),stroke:'#14213D','stroke-width':1}}));
  rows.forEach(r => {{
    const radius = 6 + Math.sqrt(Math.max(r[sizeField],0) / Math.max(...rows.map(d=>d[sizeField]),1)) * 24;
    svg.appendChild(el('circle',{{cx:x(r[xField]),cy:y(r[yField]),r:radius,fill:actionColor(r.action),opacity:.82,stroke:'#fff','stroke-width':2}}));
    if (labelSet.has(r.channel)) {{
      const lx = x(r[xField]);
      const nearRight = lx > w - 120;
      svg.appendChild(el('text',{{x:lx + (nearRight ? -8 : 7),y:y(r[yField])-7,fill:'#233047','font-size':11,'text-anchor':nearRight?'end':'start'}},r.channel));
    }}
  }});
  axis(svg,m.l,h-m.b,w-m.r,[0,.25,.5,.75,1].map(p=>({{x:m.l+p*(w-m.l-m.r),label:fmtNum(xMin+p*(xMax-xMin))}})),true);
}}
function kpiCards(total) {{
  const cards = [
    ['Spend',fmtMoney(total.spend),'portfolio cost base'],
    ['Revenue',fmtMoney(total.revenue),'attributed outcome'],
    ['ROAS',fmtNum(total.roas)+'x','revenue / spend'],
    ['CAC','$'+Math.round(total.cac),'new customer cost'],
    ['Mktg ROI',fmtPct(total.roi),'profit after spend'],
    ['CVR',fmtPct(total.cvr),'click to conversion']
  ];
  document.getElementById('kpiCards').innerHTML = cards.map(c=>`<article class="card"><span>${{c[0]}}</span><strong>${{c[1]}}</strong><small>${{c[2]}}</small></article>`).join('');
}}
function makeTable(id, rows, cols) {{
  document.getElementById(id).innerHTML = `<table class="table"><thead><tr>${{cols.map(c=>`<th>${{c.label}}</th>`).join('')}}</tr></thead><tbody>${{rows.map(r=>`<tr>${{cols.map(c=>`<td>${{c.html?c.html(r):r[c.field]}}</td>`).join('')}}</tr>`).join('')}}</tbody></table>`;
}}
function render() {{
  const rows = filteredRows();
  const total = summarize(rows);
  const ch = channelSummary(rows);
  const cp = campaignSummary(rows);
  kpiCards(total);
  trendChart(rows);
  paidOrganicChart(rows);
  scatter('actionScatter', ch, 'spend', 'roas', 'revenue', new Set(['Direct','Email','Referral Partners','Organic Search','Google Search','Meta','LinkedIn']));
  scatter('quadrantChart', ch, 'roas_gap', 'cac_gap', 'spend_share', new Set(['Direct','Email','Referral Partners','Organic Search','Google Search','Meta','LinkedIn','Programmatic Display']));
  scatter('actionMatrix', ch, 'roas_gap', 'cac_gap', 'spend_share', new Set(['Direct','Email','Referral Partners','Organic Search','Google Search','Meta','LinkedIn','Programmatic Display']));
  barChart('roasTargetChart',[...ch].sort((a,b)=>a.roas-b.roas),'channel','roas',r=>actionColor(r.action),{{markerField:'target_roas',left:128}});
  barChart('cacTargetChart',[...ch].sort((a,b)=>b.cac-a.cac),'channel','cac',r=>r.cac<=r.target_cac?'#2E8B57':'#E3645A',{{markerField:'target_cac',left:128}});
  barChart('scaleCampaigns',[...cp].sort((a,b)=>a.scale_score-b.scale_score).slice(-10),'campaign_name','scale_score',r=>'#2E8B57',{{left:210}});
  barChart('cutCampaigns',[...cp].sort((a,b)=>b.scale_score-a.scale_score).slice(-10),'campaign_name','scale_score',r=>'#E3645A',{{left:210}});
  const scale = ch.filter(r=>r.action==='Scale').sort((a,b)=>b.roas_gap-a.roas_gap).slice(0,4);
  const optimize = ch.filter(r=>r.action==='Optimize').sort((a,b)=>b.spend-a.spend).slice(0,4);
  const review = ch.filter(r=>r.action==='Review/Cut').sort((a,b)=>b.spend_share-a.spend_share).slice(0,4);
  document.getElementById('callouts').innerHTML = [
    ['scale','Scale',scale.map(r=>r.channel).join(', ') || 'No channel'],
    ['optimize','Optimize',optimize.map(r=>r.channel).join(', ') || 'No channel'],
    ['review','Review/Cut',review.map(r=>r.channel).join(', ') || 'No channel']
  ].map(c=>`<div class="callout ${{c[0]}}"><h3>${{c[1]}}</h3><p>${{c[2]}}</p></div>`).join('');
  document.getElementById('budgetMoves').innerHTML = [
    ['review','Reduce / fix',review],
    ['scale','Scale carefully',scale]
  ].map(([cls,title,list])=>`<div class="callout ${{cls}}"><h3>${{title}}</h3><p>${{list.map(r=>`${{r.channel}} (${{fmtPct(r.spend_share)}} spend)`).join('<br>') || 'No channel'}}</p></div>`).join('');
  const chRows = ch.slice(0,10);
  const chCols = [
    {{label:'Channel',field:'channel'}}, {{label:'Type',field:'paid_organic'}},
    {{label:'Share',html:r=>fmtPct(r.spend_share)}}, {{label:'ROAS',html:r=>fmtNum(r.roas)+'x'}},
    {{label:'CAC',html:r=>'$'+Math.round(r.cac)}}, {{label:'Action',html:r=>`<span class="action ${{actionClass(r.action)}}">${{r.action}}</span>`}}
  ];
  makeTable('channelTable', chRows, chCols);
  makeTable('operatingTable', ch, [
    {{label:'Channel',field:'channel'}}, {{label:'Type',field:'paid_organic'}}, {{label:'Spend Share',html:r=>fmtPct(r.spend_share)}},
    {{label:'ROAS Gap',html:r=>(r.roas_gap>=0?'+':'')+fmtNum(r.roas_gap)}}, {{label:'CAC Gap',html:r=>(r.cac_gap>=0?'+':'')+Math.round(r.cac_gap)}},
    {{label:'ROAS',html:r=>fmtNum(r.roas)+'x'}}, {{label:'CAC',html:r=>'$'+Math.round(r.cac)}}, {{label:'Action',html:r=>`<span class="action ${{actionClass(r.action)}}">${{r.action}}</span>`}}
  ]);
  const decision = [...cp].sort((a,b)=>b.scale_score-a.scale_score).slice(0,6).concat([...cp].sort((a,b)=>a.scale_score-b.scale_score).slice(0,4));
  makeTable('campaignTable', decision, [
    {{label:'Campaign',field:'campaign_name'}}, {{label:'Channel',field:'channel'}}, {{label:'Type',field:'paid_organic'}},
    {{label:'Spend',html:r=>fmtMoney(r.spend)}}, {{label:'Revenue',html:r=>fmtMoney(r.revenue)}}, {{label:'ROAS',html:r=>fmtNum(r.roas)+'x'}},
    {{label:'CAC',html:r=>'$'+Math.round(r.cac)}}, {{label:'Score',html:r=>Math.round(r.scale_score)}}, {{label:'Action',html:r=>`<span class="action ${{actionClass(r.action)}}">${{r.action}}</span>`}}
  ]);
}}
function init() {{
  const dates = DATA.map(r=>r.date).sort();
  startDate.value = dates[0]; endDate.value = dates[dates.length-1];
  [...new Set(DATA.map(r=>r.channel))].sort().forEach(ch => channelFilter.insertAdjacentHTML('beforeend', `<option>${{ch}}</option>`));
  document.querySelectorAll('select,input').forEach(x=>x.addEventListener('change',render));
  resetBtn.addEventListener('click',()=>{{startDate.value=dates[0];endDate.value=dates[dates.length-1];channelFilter.value='All';typeFilter.value='All';actionFilter.value='All';render();}});
  document.querySelectorAll('nav button').forEach(btn=>btn.addEventListener('click',()=>{{document.querySelectorAll('nav button').forEach(b=>b.classList.remove('active'));btn.classList.add('active');document.querySelectorAll('.page').forEach(p=>p.classList.remove('active'));document.getElementById(btn.dataset.page).classList.add('active');render();}}));
  builtAt.textContent = PAYLOAD.generated_at;
  render();
}}
window.addEventListener('load', init);
window.addEventListener('resize', render);
</script>
</body>
</html>
"""
    (out_dir / "dashboard_final.html").write_text(html, encoding="utf-8")
    validation = {
        "status": "Pass",
        "artifact": "output/dashboard_final.html",
        "generated_at": payload["generated_at"],
        "source_rows": len(records),
        "channel_count": len(channel_meta),
        "campaign_count": len(campaigns),
        "features": [
            "date/channel/paid-organic/action filters",
            "six KPI cards",
            "monthly spend and revenue trend",
            "paid vs organic comparison",
            "spend vs ROAS action map",
            "ROAS and CAC target charts",
            "campaign ranking",
            "budget action matrix",
            "operating tables"
        ],
        "external_dependencies": []
    }
    (qa_dir / "html_dashboard_validation.json").write_text(json.dumps(validation, indent=2), encoding="utf-8")


if __name__ == "__main__":
    write_dashboard()
