from __future__ import annotations

import csv
import html
import json
from collections import defaultdict
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
PREPARED_DIR = PROJECT_ROOT / "data" / "prepared"
OUTPUT_DIR = PROJECT_ROOT / "output"
EXPORT_DIR = OUTPUT_DIR / "exports"

COLORS = {
    "orange": "#F97316",
    "orange_dark": "#C2410C",
    "teal": "#2A9D8F",
    "blue": "#2563EB",
    "red": "#D62828",
    "amber": "#F59E0B",
    "ink": "#111827",
    "muted": "#64748B",
    "line": "#E5E7EB",
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def h(text: object) -> str:
    return html.escape(str(text), quote=True)


def fmt_m(value: float) -> str:
    return f"{value / 1_000_000:,.1f}M"


def fmt_pct(value: float) -> str:
    return f"{value * 100:,.1f}%"


def fmt_int(value: float) -> str:
    return f"{value:,.0f}"


def css_class_for_delta(value: float, inverse: bool = False) -> str:
    if abs(value) < 1e-9:
        return "neutral"
    good = value > 0
    if inverse:
        good = not good
    return "good" if good else "bad"


def sum_rows(rows: list[dict[str, object]], measure: str, **filters: object) -> float:
    total = 0.0
    for row in rows:
        if all(row.get(key) == value for key, value in filters.items()):
            total += float(row.get(measure, 0) or 0)
    return total


def month_label(month_start: str) -> str:
    return month_start[5:7] + "/" + month_start[2:4]


def enrich_financials() -> list[dict[str, object]]:
    facts = read_csv(PREPARED_DIR / "fact_financials.csv")
    dim_date = {r["DateKey"]: r for r in read_csv(PREPARED_DIR / "dim_date.csv")}
    dim_scenario = {r["ScenarioKey"]: r["Scenario"] for r in read_csv(PREPARED_DIR / "dim_scenario.csv")}
    dim_bu = {r["BusinessUnitKey"]: r["BusinessUnit"] for r in read_csv(PREPARED_DIR / "dim_business_unit.csv")}
    dim_product = {r["ProductKey"]: r["Product"] for r in read_csv(PREPARED_DIR / "dim_product.csv")}
    dim_region = {r["RegionKey"]: r["Region"] for r in read_csv(PREPARED_DIR / "dim_region.csv")}
    dim_customer = {r["CustomerKey"]: r for r in read_csv(PREPARED_DIR / "dim_customer.csv")}

    enriched: list[dict[str, object]] = []
    numeric_fields = ["Revenue", "COGS", "GrossMargin", "AllocatedOpex", "EBITDA", "Orders", "CashImpact"]
    for row in facts:
        item: dict[str, object] = dict(row)
        for field in numeric_fields:
            item[field] = float(row.get(field, 0) or 0)
        customer = dim_customer[row["CustomerKey"]]
        item["MonthStart"] = dim_date[row["DateKey"]]["MonthStart"]
        item["MonthYear"] = dim_date[row["DateKey"]]["MonthYear"]
        item["MonthName"] = dim_date[row["DateKey"]]["MonthName"]
        item["Scenario"] = dim_scenario[row["ScenarioKey"]]
        item["BusinessUnit"] = dim_bu[row["BusinessUnitKey"]]
        item["Product"] = dim_product[row["ProductKey"]]
        item["Region"] = dim_region[row["RegionKey"]]
        item["Customer"] = customer["Customer"]
        item["CustomerSegment"] = customer["CustomerSegment"]
        item["Industry"] = customer["Industry"]
        enriched.append(item)
    return enriched


def enrich_cash() -> list[dict[str, object]]:
    facts = read_csv(PREPARED_DIR / "fact_cash.csv")
    dim_date = {r["DateKey"]: r for r in read_csv(PREPARED_DIR / "dim_date.csv")}
    dim_scenario = {r["ScenarioKey"]: r["Scenario"] for r in read_csv(PREPARED_DIR / "dim_scenario.csv")}
    dim_bu = {r["BusinessUnitKey"]: r["BusinessUnit"] for r in read_csv(PREPARED_DIR / "dim_business_unit.csv")}
    dim_region = {r["RegionKey"]: r["Region"] for r in read_csv(PREPARED_DIR / "dim_region.csv")}

    enriched: list[dict[str, object]] = []
    numeric_fields = ["CashBalance", "ARBalance", "DSO", "Capex"]
    for row in facts:
        item: dict[str, object] = dict(row)
        for field in numeric_fields:
            item[field] = float(row.get(field, 0) or 0)
        item["MonthStart"] = dim_date[row["DateKey"]]["MonthStart"]
        item["Scenario"] = dim_scenario[row["ScenarioKey"]]
        item["BusinessUnit"] = dim_bu[row["BusinessUnitKey"]]
        item["Region"] = dim_region[row["RegionKey"]]
        enriched.append(item)
    return enriched


def latest_actual_month(rows: list[dict[str, object]]) -> str:
    return max(str(r["MonthStart"]) for r in rows if r["Scenario"] == "Actual")


def metric_snapshot(financials: list[dict[str, object]], cash: list[dict[str, object]], month: str) -> dict[str, dict[str, float]]:
    snapshot: dict[str, dict[str, float]] = {}
    scenarios = ["Actual", "Budget", "Forecast"]
    for scenario in scenarios:
        revenue = sum_rows(financials, "Revenue", MonthStart=month, Scenario=scenario)
        gm = sum_rows(financials, "GrossMargin", MonthStart=month, Scenario=scenario)
        ebitda = sum_rows(financials, "EBITDA", MonthStart=month, Scenario=scenario)
        opex = sum_rows(financials, "AllocatedOpex", MonthStart=month, Scenario=scenario)
        orders = sum_rows(financials, "Orders", MonthStart=month, Scenario=scenario)
        cash_balance = sum_rows(cash, "CashBalance", MonthStart=month, Scenario=scenario)
        ar_balance = sum_rows(cash, "ARBalance", MonthStart=month, Scenario=scenario)
        capex = sum_rows(cash, "Capex", MonthStart=month, Scenario=scenario)
        dso_count = sum(1 for row in cash if row["MonthStart"] == month and row["Scenario"] == scenario)
        dso = sum_rows(cash, "DSO", MonthStart=month, Scenario=scenario) / max(dso_count, 1)
        snapshot[scenario] = {
            "Revenue": revenue,
            "GrossMargin": gm,
            "GrossMarginPct": gm / revenue if revenue else 0.0,
            "EBITDA": ebitda,
            "EBITDAMarginPct": ebitda / revenue if revenue else 0.0,
            "Opex": opex,
            "Orders": orders,
            "Cash": cash_balance,
            "AR": ar_balance,
            "DSO": dso,
            "Capex": capex,
        }
    return snapshot


def trend_series(financials: list[dict[str, object]], latest_month: str) -> tuple[list[str], dict[str, list[float]]]:
    months = sorted({str(r["MonthStart"]) for r in financials if str(r["MonthStart"]) <= latest_month})[-12:]
    series = {
        "Actual": [sum_rows(financials, "Revenue", MonthStart=month, Scenario="Actual") for month in months],
        "Budget": [sum_rows(financials, "Revenue", MonthStart=month, Scenario="Budget") for month in months],
        "Forecast": [sum_rows(financials, "Revenue", MonthStart=month, Scenario="Forecast") for month in months],
        "EBITDA": [sum_rows(financials, "EBITDA", MonthStart=month, Scenario="Actual") for month in months],
    }
    return months, series


def svg_line_chart(months: list[str], series: dict[str, list[float]]) -> str:
    width, height = 820, 300
    pad_left, pad_right, pad_top, pad_bottom = 56, 28, 24, 46
    values = [value for vals in series.values() for value in vals]
    lo, hi = min(values), max(values)
    span = hi - lo or 1.0

    def xy(idx: int, value: float) -> tuple[float, float]:
        x = pad_left + idx * ((width - pad_left - pad_right) / max(1, len(months) - 1))
        y = height - pad_bottom - ((value - lo) / span) * (height - pad_top - pad_bottom)
        return x, y

    style = {
        "Actual": ("line-orange", COLORS["orange"]),
        "Budget": ("line-blue dashed", COLORS["blue"]),
        "Forecast": ("line-teal dashed", COLORS["teal"]),
        "EBITDA": ("line-amber", COLORS["amber"]),
    }
    paths = []
    for name, vals in series.items():
        points = [xy(idx, value) for idx, value in enumerate(vals)]
        path = " ".join(f"{'M' if idx == 0 else 'L'} {x:.1f} {y:.1f}" for idx, (x, y) in enumerate(points))
        paths.append(f'<path d="{path}" class="{style[name][0]}"/>')

    y_labels = ""
    for pct in [0.0, 0.5, 1.0]:
        y = height - pad_bottom - pct * (height - pad_top - pad_bottom)
        value = lo + pct * span
        y_labels += f'<line x1="{pad_left}" y1="{y:.1f}" x2="{width - pad_right}" y2="{y:.1f}" class="grid-line"/>'
        y_labels += f'<text x="{pad_left - 10}" y="{y + 4:.1f}" text-anchor="end" class="axis">{fmt_m(value)}</text>'

    x_labels = ""
    for idx, month in enumerate(months):
        if idx % 2 == 0 or idx == len(months) - 1:
            x, _ = xy(idx, lo)
            x_labels += f'<text x="{x:.1f}" y="{height - 16}" text-anchor="middle" class="axis">{month_label(month)}</text>'

    legend = ""
    legend_x = pad_left
    for name in ["Actual", "Budget", "Forecast", "EBITDA"]:
        color = style[name][1]
        legend += f'<circle cx="{legend_x}" cy="14" r="4" fill="{color}"/><text x="{legend_x + 9}" y="18" class="axis">{name}</text>'
        legend_x += 92

    return f"""
    <svg viewBox="0 0 {width} {height}" class="chart-svg" role="img" aria-label="12 month revenue trend by scenario">
      {legend}
      {y_labels}
      <line x1="{pad_left}" y1="{height - pad_bottom}" x2="{width - pad_right}" y2="{height - pad_bottom}" class="zero-line"/>
      {''.join(paths)}
      {x_labels}
    </svg>
    """


def dimension_rows(financials: list[dict[str, object]], month: str, dimension: str, limit: int | None = None) -> list[dict[str, object]]:
    rows = []
    for value in sorted({str(r[dimension]) for r in financials}):
        actual_revenue = sum_rows(financials, "Revenue", MonthStart=month, Scenario="Actual", **{dimension: value})
        budget_revenue = sum_rows(financials, "Revenue", MonthStart=month, Scenario="Budget", **{dimension: value})
        forecast_revenue = sum_rows(financials, "Revenue", MonthStart=month, Scenario="Forecast", **{dimension: value})
        actual_gm = sum_rows(financials, "GrossMargin", MonthStart=month, Scenario="Actual", **{dimension: value})
        actual_ebitda = sum_rows(financials, "EBITDA", MonthStart=month, Scenario="Actual", **{dimension: value})
        budget_ebitda = sum_rows(financials, "EBITDA", MonthStart=month, Scenario="Budget", **{dimension: value})
        orders = sum_rows(financials, "Orders", MonthStart=month, Scenario="Actual", **{dimension: value})
        rows.append({
            "name": value,
            "actualRevenue": actual_revenue,
            "budgetRevenue": budget_revenue,
            "forecastRevenue": forecast_revenue,
            "revenueVariance": actual_revenue - budget_revenue,
            "grossMarginPct": actual_gm / actual_revenue if actual_revenue else 0.0,
            "actualEbitda": actual_ebitda,
            "ebitdaVariance": actual_ebitda - budget_ebitda,
            "orders": orders,
        })
    rows.sort(key=lambda item: abs(float(item["ebitdaVariance"])), reverse=True)
    return rows[:limit] if limit else rows


def variance_driver_rows(rows: list[dict[str, object]]) -> str:
    max_abs = max(abs(float(row["ebitdaVariance"])) for row in rows) or 1.0
    output = []
    for row in rows:
        value = float(row["ebitdaVariance"])
        width = max(4.0, abs(value) / max_abs * 100)
        class_name = css_class_for_delta(value)
        output.append(f"""
          <div class="driver-row">
            <div class="driver-name">{h(row["name"])}</div>
            <div class="driver-track"><span class="driver-bar {class_name}" style="width:{width:.1f}%"></span></div>
            <div class="driver-value {class_name}">{fmt_m(value)}</div>
          </div>
        """)
    return "".join(output)


def waterfall_items(bridge: list[dict[str, str]]) -> list[dict[str, object]]:
    grouped: dict[str, float] = defaultdict(float)
    order: dict[str, int] = {}
    for row in bridge:
        grouped[row["BridgeStep"]] += float(row["Amount"])
        order[row["BridgeStep"]] = int(row["BridgeOrder"])
    return [{"name": name, "value": value} for name, value in sorted(grouped.items(), key=lambda item: order[item[0]])]


def waterfall_html(items: list[dict[str, object]]) -> str:
    max_abs = max(abs(float(item["value"])) for item in items) or 1.0
    bars = []
    for idx, item in enumerate(items):
        value = float(item["value"])
        height = max(8.0, abs(value) / max_abs * 170)
        is_total = idx == 0 or idx == len(items) - 1
        class_name = "total" if is_total else css_class_for_delta(value)
        bars.append(f"""
          <div class="wf-item">
            <div class="wf-plot">
              <div class="wf-bar {class_name}" style="height:{height:.1f}px"></div>
            </div>
            <div class="wf-value {class_name}">{fmt_m(value)}</div>
            <div class="wf-label">{h(item["name"])}</div>
          </div>
        """)
    return "".join(bars)


def summary_rows(snapshot: dict[str, dict[str, float]]) -> list[dict[str, object]]:
    rows = []
    metrics = [
        ("Revenue", "Revenue", "money", False),
        ("Gross Margin %", "GrossMarginPct", "pct", False),
        ("EBITDA", "EBITDA", "money", False),
        ("EBITDA Margin %", "EBITDAMarginPct", "pct", False),
        ("Opex", "Opex", "money", True),
        ("Cash", "Cash", "money", False),
        ("DSO", "DSO", "number", True),
    ]
    for label, key, kind, inverse in metrics:
        actual = snapshot["Actual"][key]
        budget = snapshot["Budget"][key]
        forecast = snapshot["Forecast"][key]
        if kind == "pct":
            fmt = fmt_pct
        elif kind == "number":
            fmt = lambda value: f"{value:,.1f}"
        else:
            fmt = fmt_m
        rows.append({
            "metric": label,
            "actual": fmt(actual),
            "budget": fmt(budget),
            "forecast": fmt(forecast),
            "varBudget": fmt(actual - budget),
            "varForecast": fmt(actual - forecast),
            "varBudgetClass": css_class_for_delta(actual - budget, inverse=inverse),
            "varForecastClass": css_class_for_delta(actual - forecast, inverse=inverse),
        })
    return rows


def table_rows_html(rows: list[dict[str, object]]) -> str:
    output = []
    for row in rows:
        output.append(f"""
          <tr>
            <td>{h(row["metric"])}</td>
            <td class="num">{h(row["actual"])}</td>
            <td class="num">{h(row["budget"])}</td>
            <td class="num">{h(row["forecast"])}</td>
            <td class="num {h(row["varBudgetClass"])}">{h(row["varBudget"])}</td>
            <td class="num {h(row["varForecastClass"])}">{h(row["varForecast"])}</td>
          </tr>
        """)
    return "".join(output)


def commentary_for_month(month: str) -> dict[str, str]:
    commentary = read_csv(PREPARED_DIR / "fact_commentary.csv")
    key = month.replace("-", "")
    for row in commentary:
        if row["DateKey"] == key:
            return row
    return {
        "WhatHappened": "Revenue and profitability moved versus plan during the close.",
        "Why": "Mix, productivity, and customer timing were the main operating drivers.",
        "WhatNext": "Validate actions in the next forecast refresh and track owner-level commitments.",
    }


def dashboard_html() -> str:
    financials = enrich_financials()
    cash = enrich_cash()
    month = latest_actual_month(financials)
    snapshot = metric_snapshot(financials, cash, month)
    months, trend = trend_series(financials, month)
    bridge = waterfall_items(read_csv(PREPARED_DIR / "fact_bridge.csv"))
    commentary = commentary_for_month(month)

    bu_rows = dimension_rows(financials, month, "BusinessUnit")
    product_rows = dimension_rows(financials, month, "Product")
    region_rows = dimension_rows(financials, month, "Region")
    customer_rows = dimension_rows(financials, month, "Customer", limit=12)
    drilldown = {
        "Business Unit": bu_rows,
        "Product": product_rows,
        "Region": region_rows,
        "Customer": customer_rows,
    }

    actual = snapshot["Actual"]
    budget = snapshot["Budget"]
    forecast = snapshot["Forecast"]
    revenue_vs_budget = actual["Revenue"] - budget["Revenue"]
    revenue_vs_forecast = actual["Revenue"] - forecast["Revenue"]
    ebitda_vs_budget = actual["EBITDA"] - budget["EBITDA"]
    cash_vs_budget = actual["Cash"] - budget["Cash"]

    table_data = json.dumps(drilldown, ensure_ascii=False)

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Monthly FP&A Performance Pack Dashboard</title>
  <style>
    :root {{
      --orange: {COLORS["orange"]};
      --orange-dark: {COLORS["orange_dark"]};
      --teal: {COLORS["teal"]};
      --blue: {COLORS["blue"]};
      --red: {COLORS["red"]};
      --amber: {COLORS["amber"]};
      --ink: {COLORS["ink"]};
      --muted: {COLORS["muted"]};
      --line: {COLORS["line"]};
      --soft-line: #F1F5F9;
      --bg: #F8FAFC;
      --panel: #FFFFFF;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: "Segoe UI", Arial, sans-serif;
      background: var(--bg);
      color: var(--ink);
    }}
    .shell {{ max-width: 1480px; margin: 0 auto; padding: 24px; }}
    .topbar {{
      display: grid;
      grid-template-columns: minmax(260px, 1fr) auto;
      gap: 18px;
      align-items: end;
      margin-bottom: 16px;
    }}
    h1 {{ font-size: 30px; line-height: 1.15; margin: 0; letter-spacing: 0; }}
    .subtitle {{ color: var(--muted); font-size: 13px; margin-top: 7px; }}
    .filterbar {{ display: flex; flex-wrap: wrap; justify-content: flex-end; gap: 8px; }}
    .chip {{
      border: 1px solid var(--line);
      background: var(--panel);
      border-radius: 6px;
      padding: 8px 10px;
      font-size: 12px;
      color: #334155;
      white-space: nowrap;
    }}
    .grid {{ display: grid; grid-template-columns: repeat(12, minmax(0, 1fr)); gap: 14px; }}
    .panel {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 16px;
      min-width: 0;
    }}
    .kpi {{
      grid-column: span 2;
      min-height: 136px;
      border-top: 4px solid var(--orange);
      display: flex;
      flex-direction: column;
      justify-content: space-between;
    }}
    .half {{ grid-column: span 6; }}
    .wide {{ grid-column: span 8; }}
    .side {{ grid-column: span 4; }}
    .full {{ grid-column: span 12; }}
    .label {{ font-size: 12px; color: var(--muted); margin-bottom: 8px; }}
    .value {{ font-size: 30px; line-height: 1.1; font-weight: 700; overflow-wrap: anywhere; }}
    .delta {{ margin-top: 8px; font-size: 12px; line-height: 1.35; }}
    .bad {{ color: var(--red); }}
    .good {{ color: var(--teal); }}
    .neutral {{ color: var(--muted); }}
    .chart-title {{ font-size: 15px; font-weight: 700; margin-bottom: 10px; }}
    .chart-subtitle {{ color: var(--muted); font-size: 12px; margin-top: -4px; margin-bottom: 10px; }}
    .chart-svg {{ width: 100%; min-height: 260px; display: block; }}
    .grid-line {{ stroke: #E5E7EB; stroke-width: 1; }}
    .zero-line {{ stroke: #CBD5E1; stroke-width: 1.3; }}
    .line-orange {{ fill: none; stroke: var(--orange); stroke-width: 4; stroke-linecap: round; stroke-linejoin: round; }}
    .line-teal {{ fill: none; stroke: var(--teal); stroke-width: 3; stroke-linecap: round; stroke-linejoin: round; }}
    .line-blue {{ fill: none; stroke: var(--blue); stroke-width: 3; stroke-linecap: round; stroke-linejoin: round; }}
    .line-amber {{ fill: none; stroke: var(--amber); stroke-width: 3; stroke-linecap: round; stroke-linejoin: round; }}
    .dashed {{ stroke-dasharray: 8 7; }}
    .axis {{ fill: var(--muted); font-size: 11px; }}
    .driver-list {{ display: grid; gap: 12px; margin-top: 12px; }}
    .driver-row {{
      display: grid;
      grid-template-columns: minmax(110px, 1.1fr) minmax(96px, 2fr) 72px;
      gap: 10px;
      align-items: center;
      font-size: 12px;
    }}
    .driver-name {{ color: #334155; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }}
    .driver-track {{ height: 12px; background: #F1F5F9; border-radius: 999px; overflow: hidden; }}
    .driver-bar {{ display: block; height: 100%; border-radius: 999px; }}
    .driver-bar.good {{ background: var(--teal); }}
    .driver-bar.bad {{ background: var(--red); }}
    .driver-value {{ text-align: right; font-weight: 700; }}
    .table-wrap {{ width: 100%; overflow-x: auto; }}
    table {{ width: 100%; border-collapse: collapse; min-width: 760px; }}
    th, td {{ border-bottom: 1px solid var(--soft-line); padding: 10px 8px; font-size: 12px; text-align: left; }}
    th {{ color: var(--muted); font-weight: 700; background: #F8FAFC; }}
    td.num, th.num {{ text-align: right; font-variant-numeric: tabular-nums; }}
    .wf {{
      display: grid;
      grid-template-columns: repeat(7, minmax(80px, 1fr));
      gap: 10px;
      align-items: end;
      min-height: 260px;
      overflow-x: auto;
      padding-top: 10px;
    }}
    .wf-item {{ min-width: 84px; text-align: center; }}
    .wf-plot {{
      height: 180px;
      display: flex;
      align-items: flex-end;
      justify-content: center;
      border-bottom: 1px solid var(--line);
    }}
    .wf-bar {{ width: 62%; border-radius: 6px 6px 0 0; }}
    .wf-bar.total {{ background: var(--orange); }}
    .wf-bar.good {{ background: var(--teal); }}
    .wf-bar.bad {{ background: var(--red); }}
    .wf-value {{ font-size: 12px; font-weight: 700; margin-top: 6px; }}
    .wf-value.total {{ color: var(--orange-dark); }}
    .wf-label {{ color: var(--muted); font-size: 11px; line-height: 1.25; margin-top: 5px; min-height: 30px; }}
    .commentary {{ display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 14px; }}
    .commentary-block {{
      border-left: 3px solid var(--orange);
      padding-left: 12px;
      min-width: 0;
    }}
    .commentary h3 {{ margin: 0 0 8px; font-size: 13px; }}
    .commentary p {{ margin: 0; color: #334155; font-size: 13px; line-height: 1.48; }}
    .tabs {{ display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 12px; }}
    .tab {{
      border: 1px solid var(--line);
      background: #FFFFFF;
      border-radius: 6px;
      padding: 8px 11px;
      color: #334155;
      font-size: 12px;
      cursor: pointer;
    }}
    .tab.active {{ border-color: var(--orange); background: #FFF7ED; color: #9A3412; font-weight: 700; }}
    .footnote {{ color: var(--muted); font-size: 11px; margin-top: 10px; }}
    @media (max-width: 1180px) {{
      .kpi {{ grid-column: span 4; }}
      .wide, .side, .half {{ grid-column: span 12; }}
    }}
    @media (max-width: 720px) {{
      .shell {{ padding: 16px; }}
      .topbar {{ grid-template-columns: 1fr; }}
      .filterbar {{ justify-content: flex-start; }}
      .kpi, .wide, .side, .half, .full {{ grid-column: span 12; }}
      .commentary {{ grid-template-columns: 1fr; }}
      .value {{ font-size: 28px; }}
      .driver-row {{ grid-template-columns: 1fr 1.5fr 68px; }}
      .chart-svg {{ min-height: 220px; }}
      h1 {{ font-size: 28px; }}
    }}
  </style>
</head>
<body>
  <main class="shell">
    <section class="topbar">
      <div>
        <h1>Monthly FP&A Performance Pack</h1>
        <div class="subtitle">May 2026 close package, orange executive theme, source-backed from prepared FP&A data</div>
      </div>
      <div class="filterbar">
        <div class="chip">Year 2026</div>
        <div class="chip">Month May</div>
        <div class="chip">Actual vs Budget vs Forecast</div>
        <div class="chip">Company Level</div>
      </div>
    </section>

    <section class="grid">
      <article class="panel kpi">
        <div>
          <div class="label">Revenue</div>
          <div class="value">{fmt_m(actual["Revenue"])}</div>
        </div>
        <div class="delta {css_class_for_delta(revenue_vs_budget)}">{fmt_m(revenue_vs_budget)} vs Budget<br>{fmt_m(revenue_vs_forecast)} vs Forecast</div>
      </article>
      <article class="panel kpi">
        <div>
          <div class="label">Gross Margin %</div>
          <div class="value">{fmt_pct(actual["GrossMarginPct"])}</div>
        </div>
        <div class="delta">GM {fmt_m(actual["GrossMargin"])}</div>
      </article>
      <article class="panel kpi">
        <div>
          <div class="label">EBITDA</div>
          <div class="value">{fmt_m(actual["EBITDA"])}</div>
        </div>
        <div class="delta {css_class_for_delta(ebitda_vs_budget)}">{fmt_m(ebitda_vs_budget)} vs Budget<br>{fmt_pct(actual["EBITDAMarginPct"])} margin</div>
      </article>
      <article class="panel kpi">
        <div>
          <div class="label">Opex</div>
          <div class="value">{fmt_m(actual["Opex"])}</div>
        </div>
        <div class="delta {css_class_for_delta(actual["Opex"] - budget["Opex"], inverse=True)}">{fmt_m(actual["Opex"] - budget["Opex"])} vs Budget</div>
      </article>
      <article class="panel kpi">
        <div>
          <div class="label">Cash</div>
          <div class="value">{fmt_m(actual["Cash"])}</div>
        </div>
        <div class="delta {css_class_for_delta(cash_vs_budget)}">{fmt_m(cash_vs_budget)} vs Budget<br>DSO {actual["DSO"]:,.1f} days</div>
      </article>
      <article class="panel kpi">
        <div>
          <div class="label">Orders</div>
          <div class="value">{fmt_int(actual["Orders"])}</div>
        </div>
        <div class="delta">Revenue/order {fmt_m(actual["Revenue"] / max(actual["Orders"], 1))}</div>
      </article>

      <article class="panel wide">
        <div class="chart-title">12M Trend: Revenue by Scenario plus Actual EBITDA</div>
        <div class="chart-subtitle">Actual is shown against operating plan and latest forecast to support monthly FP&A pacing.</div>
        {svg_line_chart(months, trend)}
      </article>
      <article class="panel side">
        <div class="chart-title">EBITDA Variance by Business Unit</div>
        <div class="chart-subtitle">Latest month actual less budget.</div>
        <div class="driver-list">
          {variance_driver_rows(bu_rows)}
        </div>
      </article>

      <article class="panel full">
        <div class="chart-title">Actual vs Budget vs Forecast</div>
        <div class="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Metric</th>
                <th class="num">Actual</th>
                <th class="num">Budget</th>
                <th class="num">Forecast</th>
                <th class="num">Var to Budget</th>
                <th class="num">Var to Forecast</th>
              </tr>
            </thead>
            <tbody>
              {table_rows_html(summary_rows(snapshot))}
            </tbody>
          </table>
        </div>
      </article>

      <article class="panel half">
        <div class="chart-title">Budget to Actual EBITDA Bridge</div>
        <div class="chart-subtitle">Bridge isolates planning gap into volume, rate, productivity, opex, and other drivers.</div>
        <div class="wf">
          {waterfall_html(bridge)}
        </div>
      </article>
      <article class="panel half">
        <div class="chart-title">Commentary</div>
        <div class="commentary">
          <div class="commentary-block"><h3>What happened?</h3><p>{h(commentary["WhatHappened"])}</p></div>
          <div class="commentary-block"><h3>Why?</h3><p>{h(commentary["Why"])}</p></div>
          <div class="commentary-block"><h3>What next?</h3><p>{h(commentary["WhatNext"])}</p></div>
        </div>
      </article>

      <article class="panel full">
        <div class="chart-title">Drill-down Matrix</div>
        <div class="chart-subtitle">Switch level to inspect company performance by business unit, product, region, or customer.</div>
        <div class="tabs" id="tabs"></div>
        <div class="table-wrap">
          <table>
            <thead>
              <tr>
                <th id="dimension-heading">Business Unit</th>
                <th class="num">Actual Revenue</th>
                <th class="num">Budget Revenue</th>
                <th class="num">Forecast Revenue</th>
                <th class="num">Revenue Var</th>
                <th class="num">GM %</th>
                <th class="num">EBITDA</th>
                <th class="num">EBITDA Var</th>
                <th class="num">Orders</th>
              </tr>
            </thead>
            <tbody id="drilldown-body"></tbody>
          </table>
        </div>
        <div class="footnote">Static HTML version of the dashboard. The PBIX in output contains the Power BI semantic model and DAX measures; this page is the visual management pack handoff.</div>
      </article>
    </section>
  </main>

  <script>
    const DATA = {table_data};
    const tabs = document.getElementById("tabs");
    const tbody = document.getElementById("drilldown-body");
    const heading = document.getElementById("dimension-heading");

    function formatM(value) {{
      return (value / 1000000).toLocaleString(undefined, {{ maximumFractionDigits: 1, minimumFractionDigits: 1 }}) + "M";
    }}

    function formatPct(value) {{
      return (value * 100).toLocaleString(undefined, {{ maximumFractionDigits: 1, minimumFractionDigits: 1 }}) + "%";
    }}

    function classFor(value) {{
      if (Math.abs(value) < 1e-9) return "neutral";
      return value > 0 ? "good" : "bad";
    }}

    function render(level) {{
      heading.textContent = level;
      tbody.innerHTML = DATA[level].map(row => `
        <tr>
          <td>${{row.name}}</td>
          <td class="num">${{formatM(row.actualRevenue)}}</td>
          <td class="num">${{formatM(row.budgetRevenue)}}</td>
          <td class="num">${{formatM(row.forecastRevenue)}}</td>
          <td class="num ${{classFor(row.revenueVariance)}}">${{formatM(row.revenueVariance)}}</td>
          <td class="num">${{formatPct(row.grossMarginPct)}}</td>
          <td class="num">${{formatM(row.actualEbitda)}}</td>
          <td class="num ${{classFor(row.ebitdaVariance)}}">${{formatM(row.ebitdaVariance)}}</td>
          <td class="num">${{Math.round(row.orders).toLocaleString()}}</td>
        </tr>
      `).join("");
      [...tabs.querySelectorAll("button")].forEach(button => {{
        button.classList.toggle("active", button.dataset.level === level);
      }});
    }}

    Object.keys(DATA).forEach((level, idx) => {{
      const button = document.createElement("button");
      button.className = "tab" + (idx === 0 ? " active" : "");
      button.type = "button";
      button.dataset.level = level;
      button.textContent = level;
      button.addEventListener("click", () => render(level));
      tabs.appendChild(button);
    }});
    render("Business Unit");
  </script>
</body>
</html>
"""


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    html_text = dashboard_html()
    dashboard_path = OUTPUT_DIR / "dashboard.html"
    export_path = EXPORT_DIR / "fpa_dashboard_preview.html"
    dashboard_path.write_text(html_text, encoding="utf-8")
    export_path.write_text(html_text, encoding="utf-8")
    print(f"Dashboard written to {dashboard_path}")
    print(f"Export mirror written to {export_path}")


if __name__ == "__main__":
    main()
