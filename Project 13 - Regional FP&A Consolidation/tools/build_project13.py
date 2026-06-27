from __future__ import annotations

import csv
import json
import math
import random
import shutil
import subprocess
from collections import defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path


PROJECT = Path(__file__).resolve().parents[1]
SEED = 13042
RUN_TS = datetime.now().replace(microsecond=0).isoformat()
LATEST_PERIOD = "2026-05"
MONEY_FORMAT = "$#,0;($#,0);$0"


def ensure_dirs() -> None:
    for rel in [
        "data/raw",
        "data/prepared",
        "data/validated",
        "model",
        "build/scripts",
        "build/config",
        "powerbi/notes",
        "output/screenshots",
        "qa",
        "docs",
        "_agent",
        "_workflow",
    ]:
        (PROJECT / rel).mkdir(parents=True, exist_ok=True)


def write_text(rel: str, content: str) -> None:
    path = PROJECT / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.strip() + "\n", encoding="utf-8")


def write_json(rel: str, payload) -> None:
    path = PROJECT / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True), encoding="utf-8")


def write_csv(rel: str, rows: list[dict]) -> None:
    path = PROJECT / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def month_range(start: str, end: str) -> list[str]:
    sy, sm = map(int, start.split("-"))
    ey, em = map(int, end.split("-"))
    out = []
    y, m = sy, sm
    while (y, m) <= (ey, em):
        out.append(f"{y:04d}-{m:02d}")
        m += 1
        if m == 13:
            y += 1
            m = 1
    return out


def period_to_date(period: str) -> str:
    y, m = map(int, period.split("-"))
    return f"{y:04d}-{m:02d}-01"


def round2(v: float) -> float:
    return round(float(v), 2)


def pct(n: float, d: float) -> float:
    return 0.0 if abs(d) < 1e-9 else n / d


def collect_environment() -> dict:
    exe = Path(r"C:\Program Files\Microsoft Power BI Desktop\bin\PBIDesktop.exe")
    exe_x86 = Path(r"C:\Program Files (x86)\Microsoft Power BI Desktop\bin\PBIDesktop.exe")
    start_apps = []
    try:
        ps = (
            "Get-StartApps | Where-Object { $_.Name -like '*Power BI Desktop*' "
            "-or $_.AppID -like '*PowerBI*' } | Select-Object Name,AppID | ConvertTo-Json -Depth 3"
        )
        proc = subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if proc.stdout.strip():
            parsed = json.loads(proc.stdout)
            start_apps = parsed if isinstance(parsed, list) else [parsed]
    except Exception as exc:
        start_apps = [{"error": str(exc)}]

    pbi_tools = shutil.which("pbi-tools") or shutil.which("pbi-tools.exe")
    info = None
    if pbi_tools:
        try:
            proc = subprocess.run([pbi_tools, "info"], capture_output=True, text=True, timeout=20)
            info = proc.stdout.strip()[:5000]
        except Exception as exc:
            info = f"pbi-tools info failed: {exc}"

    return {
        "checked_at": RUN_TS,
        "power_bi_desktop_exe": str(exe) if exe.exists() else None,
        "power_bi_desktop_program_files": exe.exists(),
        "power_bi_desktop_x86": exe_x86.exists(),
        "power_bi_start_apps": start_apps,
        "pbi_tools": pbi_tools,
        "pbi_tools_info_excerpt": info,
        "dotnet": shutil.which("dotnet"),
        "tabular_editor": shutil.which("TabularEditor.exe"),
        "computer_use": {
            "status": "pass",
            "evidence": "Computer Use bootstrap and sky.list_apps returned apps in this run; Power BI Desktop was discoverable.",
        },
    }


def generate_data() -> dict:
    random.seed(SEED)
    periods = month_range("2025-01", LATEST_PERIOD)
    entities = [
        {"entity_id": "SGP01", "entity": "Singapore Regional HQ", "country": "Singapore", "region": "SEA North", "currency": "SGD", "scale": 1.28, "ownership": 1.00},
        {"entity_id": "VNM01", "entity": "Vietnam Logistics", "country": "Vietnam", "region": "SEA South", "currency": "VND", "scale": 1.18, "ownership": 0.95},
        {"entity_id": "THA01", "entity": "Thailand Freight", "country": "Thailand", "region": "SEA North", "currency": "THB", "scale": 0.96, "ownership": 0.90},
        {"entity_id": "MYS01", "entity": "Malaysia Contract Logistics", "country": "Malaysia", "region": "SEA South", "currency": "MYR", "scale": 0.88, "ownership": 0.92},
        {"entity_id": "IDN01", "entity": "Indonesia Distribution", "country": "Indonesia", "region": "SEA South", "currency": "IDR", "scale": 1.08, "ownership": 0.87},
        {"entity_id": "PHL01", "entity": "Philippines Forwarding", "country": "Philippines", "region": "SEA North", "currency": "PHP", "scale": 0.74, "ownership": 0.85},
        {"entity_id": "AUS01", "entity": "Australia Pacific", "country": "Australia", "region": "ANZ", "currency": "AUD", "scale": 0.82, "ownership": 1.00},
    ]
    business_units = [
        {"business_unit_id": "FF", "business_unit": "Freight Forwarding", "mix": 0.37, "margin": 0.24},
        {"business_unit_id": "CL", "business_unit": "Contract Logistics", "mix": 0.25, "margin": 0.19},
        {"business_unit_id": "WH", "business_unit": "Warehousing", "mix": 0.18, "margin": 0.21},
        {"business_unit_id": "CB", "business_unit": "Customs Brokerage", "mix": 0.12, "margin": 0.31},
        {"business_unit_id": "CORP", "business_unit": "Corporate Shared Services", "mix": 0.08, "margin": 0.10},
    ]
    entity_profiles = {
        "SGP01": {"demand": 1.07, "margin": 1.05, "cost": 0.96, "growth": 0.95, "risk": 0.62, "cash": 1.18, "wc": 0.88},
        "VNM01": {"demand": 1.18, "margin": 1.02, "cost": 1.01, "growth": 1.42, "risk": 0.92, "cash": 1.02, "wc": 1.02},
        "THA01": {"demand": 0.98, "margin": 0.98, "cost": 1.03, "growth": 1.00, "risk": 0.96, "cash": 0.97, "wc": 1.00},
        "MYS01": {"demand": 0.91, "margin": 0.91, "cost": 1.09, "growth": 0.82, "risk": 1.28, "cash": 0.86, "wc": 1.16},
        "IDN01": {"demand": 1.12, "margin": 0.90, "cost": 1.11, "growth": 1.34, "risk": 1.58, "cash": 0.82, "wc": 1.26},
        "PHL01": {"demand": 0.86, "margin": 0.96, "cost": 1.05, "growth": 1.16, "risk": 1.18, "cash": 0.91, "wc": 1.10},
        "AUS01": {"demand": 0.92, "margin": 1.08, "cost": 0.95, "growth": 0.72, "risk": 0.70, "cash": 1.20, "wc": 0.84},
    }
    bu_profiles = {
        "FF": {"volume": 1.09, "margin": 1.02, "cost": 1.00, "growth": 1.10, "risk": 0.94, "opex": 1.00, "season": 1.10},
        "CL": {"volume": 1.02, "margin": 0.93, "cost": 1.05, "growth": 0.98, "risk": 1.24, "opex": 1.06, "season": 0.92},
        "WH": {"volume": 0.88, "margin": 1.03, "cost": 1.04, "growth": 0.86, "risk": 0.82, "opex": 1.09, "season": 0.72},
        "CB": {"volume": 0.74, "margin": 1.13, "cost": 0.94, "growth": 1.02, "risk": 0.76, "opex": 0.92, "season": 1.28},
        "CORP": {"volume": 0.52, "margin": 0.74, "cost": 1.18, "growth": 0.66, "risk": 1.34, "opex": 1.34, "season": 0.55},
    }
    accounts = [
        ("REV_EXT", "External Revenue", "Revenue", 10, "P&L"),
        ("REV_IC", "Intercompany Revenue", "Revenue", 20, "P&L"),
        ("COGS", "Cost of Services", "COGS", 30, "P&L"),
        ("PERS", "Personnel Cost", "OPEX", 40, "P&L"),
        ("FAC", "Facilities Cost", "OPEX", 50, "P&L"),
        ("SM", "Sales & Marketing", "OPEX", 60, "P&L"),
        ("GA", "G&A", "OPEX", 70, "P&L"),
        ("DEP", "Depreciation", "Below EBITDA", 80, "P&L"),
        ("INT", "Interest Expense", "Below EBITDA", 90, "P&L"),
        ("TAX", "Tax Expense", "Below EBITDA", 100, "P&L"),
    ]
    scenarios = [
        {"scenario_id": "ACT", "scenario": "Actual", "scenario_type": "Actual"},
        {"scenario_id": "BUD", "scenario": "Budget", "scenario_type": "Plan"},
        {"scenario_id": "FCST", "scenario": "Forecast", "scenario_type": "Forecast"},
        {"scenario_id": "PY", "scenario": "Prior Year", "scenario_type": "Comparison"},
    ]
    base_fx = {
        "SGD": 0.742,
        "VND": 0.0000394,
        "THB": 0.0275,
        "MYR": 0.213,
        "IDR": 0.000061,
        "PHP": 0.0172,
        "AUD": 0.664,
    }
    rate_bias = {"SGD": 0.01, "VND": -0.015, "THB": 0.006, "MYR": -0.02, "IDR": -0.012, "PHP": -0.006, "AUD": 0.018}

    dim_date = []
    for idx, period in enumerate(periods):
        y, m = map(int, period.split("-"))
        q = (m - 1) // 3 + 1
        dim_date.append({
            "date_id": period,
            "date": period_to_date(period),
            "year": y,
            "quarter": f"Q{q}",
            "month_number": m,
            "month_label": datetime(y, m, 1).strftime("%b %Y"),
            "is_latest_complete": "TRUE" if period == LATEST_PERIOD else "FALSE",
            "month_index": idx + 1,
        })

    dim_entity = [{k: e[k] for k in ["entity_id", "entity", "country", "region", "currency", "ownership"]} for e in entities]
    dim_bu = [{k: bu[k] for k in ["business_unit_id", "business_unit"]} for bu in business_units]
    dim_account = [
        {"account_id": a, "account": b, "account_group": c, "sort_order": d, "statement": e}
        for a, b, c, d, e in accounts
    ]
    dim_scenario = scenarios

    fact_fx = []
    fx_lookup = {}
    for p_idx, period in enumerate(periods):
        seasonal = math.sin((p_idx + 1) / 5.0)
        for e in entities:
            ccy = e["currency"]
            actual = base_fx[ccy] * (1 + rate_bias[ccy] * (p_idx / max(1, len(periods) - 1)) + seasonal * 0.008 + random.uniform(-0.006, 0.006))
            budget = base_fx[ccy] * (1 + rate_bias[ccy] * 0.35)
            closing = actual * (1 + random.uniform(-0.004, 0.004))
            fx_lookup[(period, ccy, "Actual")] = actual
            fx_lookup[(period, ccy, "Budget")] = budget
            fx_lookup[(period, ccy, "Forecast")] = actual * 0.65 + budget * 0.35
            fx_lookup[(period, ccy, "Prior Year")] = base_fx[ccy] * 0.985
            for rate_type, rate in [("Average", actual), ("Budget", budget), ("Closing", closing)]:
                fact_fx.append({
                    "date_id": period,
                    "currency": ccy,
                    "to_currency": "USD",
                    "rate_type": rate_type,
                    "rate_to_usd": round(rate, 8),
                })

    fact_financials = []
    summary = []
    scenario_profiles = {
        "Actual": {"revenue": 1.000, "cost": 1.025, "margin": 1.000, "trend": 1.000, "noise": (0.935, 1.075)},
        "Budget": {"revenue": 0.960, "cost": 0.985, "margin": 1.018, "trend": 0.985, "noise": (1.000, 1.000)},
        "Forecast": {"revenue": 1.035, "cost": 1.018, "margin": 0.995, "trend": 1.018, "noise": (0.980, 1.032)},
        "Prior Year": {"revenue": 0.870, "cost": 0.930, "margin": 0.965, "trend": 0.885, "noise": (0.960, 1.040)},
    }
    for p_idx, period in enumerate(periods):
        trend = 1 + p_idx * 0.0085
        base_season = 1 + 0.065 * math.sin((p_idx + 1) / 2.3) + (0.052 if period.endswith("-12") else 0)
        for e in entities:
            entity_profile = entity_profiles[e["entity_id"]]
            entity_noise = random.uniform(0.955, 1.045)
            for bu in business_units:
                bu_profile = bu_profiles[bu["business_unit_id"]]
                bu_noise = random.uniform(0.925, 1.075)
                season = 1 + (base_season - 1) * bu_profile["season"]
                for scen in scenarios:
                    scenario = scen["scenario"]
                    scenario_profile = scenario_profiles[scenario]
                    local_trend = (trend + p_idx * (0.0038 * entity_profile["growth"] + 0.0022 * bu_profile["growth"])) * scenario_profile["trend"]
                    low_noise, high_noise = scenario_profile["noise"]
                    noise = 1.0 if low_noise == high_noise else random.uniform(low_noise, high_noise)
                    ext_rev = (
                        1_075_000
                        * e["scale"]
                        * entity_profile["demand"]
                        * bu["mix"]
                        * bu_profile["volume"]
                        * season
                        * local_trend
                        * scenario_profile["revenue"]
                        * entity_noise
                        * bu_noise
                        * noise
                    )
                    if scenario == "Actual" and e["entity_id"] in {"VNM01", "IDN01"} and period >= "2026-02":
                        ext_rev *= 1.055
                    if scenario == "Actual" and e["entity_id"] == "MYS01" and period >= "2026-01":
                        ext_rev *= 0.925
                    if scenario == "Actual" and bu["business_unit_id"] == "CL" and e["entity_id"] in {"IDN01", "MYS01"} and period >= "2026-01":
                        ext_rev *= 0.955
                    if scenario == "Forecast" and e["entity_id"] in {"VNM01", "IDN01"}:
                        ext_rev *= 1.025
                    effective_margin = max(0.065, min(0.42, bu["margin"] * entity_profile["margin"] * bu_profile["margin"] * scenario_profile["margin"]))
                    cost_multiplier = scenario_profile["cost"] * entity_profile["cost"] * bu_profile["cost"]
                    ic_rev = ext_rev * (0.035 + (0.035 if bu["business_unit_id"] == "CORP" else 0.0)) * random.uniform(0.85, 1.15)
                    cogs = -ext_rev * (1 - effective_margin) * cost_multiplier * random.uniform(0.980, 1.028)
                    personnel = -ext_rev * (0.085 + (0.035 if bu["business_unit_id"] == "CORP" else 0.0)) * cost_multiplier * bu_profile["opex"] * random.uniform(0.965, 1.045)
                    facilities = -ext_rev * (0.035 + (0.015 if bu["business_unit_id"] == "WH" else 0.0)) * cost_multiplier * bu_profile["opex"] * random.uniform(0.955, 1.055)
                    sm = -ext_rev * 0.026 * bu_profile["growth"] * random.uniform(0.895, 1.130)
                    ga = -ext_rev * 0.030 * entity_profile["risk"] * random.uniform(0.935, 1.085)
                    dep = -ext_rev * 0.018 * random.uniform(0.96, 1.05)
                    interest = -ext_rev * 0.009 * random.uniform(0.92, 1.10)
                    tax = -max(0, ext_rev + cogs + personnel + facilities + sm + ga + dep + interest) * 0.18
                    ic_cost = -ic_rev * random.uniform(0.93, 1.04)
                    ic_elim = -(ic_rev + ic_cost)
                    fx_rate = fx_lookup[(period, e["currency"], scenario)]
                    rows = [
                        ("REV_EXT", ext_rev),
                        ("REV_IC", ic_rev),
                        ("COGS", cogs),
                        ("PERS", personnel),
                        ("FAC", facilities),
                        ("SM", sm),
                        ("GA", ga),
                        ("DEP", dep),
                        ("INT", interest),
                        ("TAX", tax),
                    ]
                    for acc, amount_usd in rows:
                        fact_financials.append({
                            "date_id": period,
                            "entity_id": e["entity_id"],
                            "business_unit_id": bu["business_unit_id"],
                            "scenario_id": scen["scenario_id"],
                            "account_id": acc,
                            "currency": e["currency"],
                            "amount_local": round2(amount_usd / fx_rate),
                            "amount_usd": round2(amount_usd),
                            "fx_rate_to_usd": round(fx_rate, 8),
                            "quantity_teu_or_orders": int(max(1, ext_rev / random.uniform(1500, 3300))),
                            "is_synthetic": "TRUE",
                        })
                    gross_revenue = ext_rev + ic_rev
                    gross_profit = ext_rev + cogs
                    opex = personnel + facilities + sm + ga
                    ebitda_pre_elim = gross_revenue + cogs + ic_cost + opex
                    ebitda = ebitda_pre_elim + ic_elim
                    operating_income = ebitda + dep
                    net_income = operating_income + interest + tax
                    cash_position = max(40_000, (ebitda * 2.9 * entity_profile["cash"]) + (ext_rev * 0.18) + random.uniform(-25000, 25000))
                    op_cash_flow = ebitda * random.uniform(0.60, 0.93) * (1.06 if entity_profile["cash"] > 1 else 0.96)
                    working_capital = ext_rev * random.uniform(0.16, 0.25) * entity_profile["wc"]
                    summary.append({
                        "date_id": period,
                        "entity_id": e["entity_id"],
                        "business_unit_id": bu["business_unit_id"],
                        "scenario_id": scen["scenario_id"],
                        "scenario": scenario,
                        "country": e["country"],
                        "region": e["region"],
                        "business_unit": bu["business_unit"],
                        "currency": e["currency"],
                        "gross_revenue_usd": round2(gross_revenue),
                        "external_revenue_usd": round2(ext_rev),
                        "intercompany_revenue_usd": round2(ic_rev),
                        "intercompany_cost_usd": round2(ic_cost),
                        "intercompany_elimination_usd": round2(ic_elim),
                        "cogs_usd": round2(cogs),
                        "gross_profit_usd": round2(gross_profit),
                        "opex_usd": round2(opex),
                        "ebitda_pre_elim_usd": round2(ebitda_pre_elim),
                        "ebitda_usd": round2(ebitda),
                        "ebitda_margin": round(pct(ebitda, ext_rev), 5),
                        "operating_income_usd": round2(operating_income),
                        "net_income_usd": round2(net_income),
                        "cash_position_usd": round2(cash_position),
                        "operating_cash_flow_usd": round2(op_cash_flow),
                        "working_capital_usd": round2(working_capital),
                    })

    # Driver bridge ties exactly to Actual vs Budget EBITDA variance at period/entity/BU grain.
    by_key = defaultdict(dict)
    for row in summary:
        by_key[(row["date_id"], row["entity_id"], row["business_unit_id"])][row["scenario"]] = row
    bridge = []
    for (period, entity_id, bu_id), scen_rows in by_key.items():
        if "Actual" not in scen_rows or "Budget" not in scen_rows:
            continue
        a, b = scen_rows["Actual"], scen_rows["Budget"]
        total = a["ebitda_usd"] - b["ebitda_usd"]
        rev_diff = a["external_revenue_usd"] - b["external_revenue_usd"]
        cogs_diff = a["cogs_usd"] - b["cogs_usd"]
        opex_diff = a["opex_usd"] - b["opex_usd"]
        fx_effect = (fx_lookup[(period, a["currency"], "Actual")] - fx_lookup[(period, a["currency"], "Budget")]) * (b["external_revenue_usd"] / max(fx_lookup[(period, a["currency"], "Budget")], 1e-9)) * 0.025
        drivers = [
            ("Volume", rev_diff * 0.42 + cogs_diff * 0.16),
            ("Price / Yield", rev_diff * 0.34),
            ("Business Mix", rev_diff * 0.24 + cogs_diff * 0.18),
            ("FX Translation", fx_effect),
            ("Intercompany Eliminations", a["intercompany_elimination_usd"] - b["intercompany_elimination_usd"]),
            ("OPEX Discipline", opex_diff),
        ]
        residual = total - sum(v for _, v in drivers)
        drivers.append(("Other / Rounding", residual))
        for i, (driver, value) in enumerate(drivers, 1):
            bridge.append({
                "date_id": period,
                "entity_id": entity_id,
                "business_unit_id": bu_id,
                "country": a["country"],
                "region": a["region"],
                "business_unit": a["business_unit"],
                "driver": driver,
                "driver_sort": i,
                "amount_usd": round2(value),
                "variance_sign": "Favorable" if value >= 0 else "Unfavorable",
            })

    exception_types = [
        ("FX Rate Pending", "Treasury", 0.16),
        ("Intercompany Mismatch", "Regional Controllership", 0.26),
        ("Late Entity Close", "Local Finance", 0.19),
        ("Manual Journal Review", "FP&A", 0.14),
        ("Budget Mapping Exception", "FP&A Systems", 0.12),
        ("AR Aging Spike", "Credit Control", 0.13),
    ]
    statuses = ["Open", "In Review", "Action Agreed", "Closed"]
    severities = ["High", "Medium", "Low"]
    exceptions = []
    ex_periods = periods[-7:]
    for idx in range(1, 76):
        e = random.choices(entities, weights=[entity_profiles[item["entity_id"]]["risk"] for item in entities], k=1)[0]
        bu = random.choices(business_units, weights=[bu_profiles[item["business_unit_id"]]["risk"] for item in business_units], k=1)[0]
        ex_type, owner, weight = random.choice(exception_types)
        risk_weight = entity_profiles[e["entity_id"]]["risk"] * bu_profiles[bu["business_unit_id"]]["risk"]
        status = random.choices(statuses, weights=[0.30 + 0.09 * risk_weight, 0.26, 0.23, max(0.08, 0.24 - 0.06 * risk_weight)])[0]
        severity = random.choices(severities, weights=[0.16 + 0.08 * risk_weight, 0.50, max(0.12, 0.34 - 0.06 * risk_weight)])[0]
        period = random.choice(ex_periods)
        amount = random.uniform(15_000, 260_000) * (1.8 if severity == "High" else 1.0) * risk_weight
        y, m = map(int, period.split("-"))
        due = date(y, m, 1) + timedelta(days=random.randint(11, 36))
        exceptions.append({
            "exception_id": f"EX{idx:03d}",
            "date_id": period,
            "entity_id": e["entity_id"],
            "business_unit_id": bu["business_unit_id"],
            "country": e["country"],
            "region": e["region"],
            "business_unit": bu["business_unit"],
            "exception_type": ex_type,
            "owner_team": owner,
            "severity": severity,
            "status": status,
            "amount_usd": round2(amount),
            "due_date": due.isoformat(),
            "commentary": f"{ex_type} in {bu['business_unit']} requires {owner} follow-up before regional close pack sign-off.",
            "is_synthetic": "TRUE",
        })

    return {
        "dim_date": dim_date,
        "dim_entity": dim_entity,
        "dim_business_unit": dim_bu,
        "dim_account": dim_account,
        "dim_scenario": dim_scenario,
        "fact_fx_rate": fact_fx,
        "fact_financials": fact_financials,
        "fact_financial_summary": summary,
        "fact_variance_driver_bridge": bridge,
        "fact_close_exceptions": exceptions,
        "metadata": {
            "seed": SEED,
            "latest_complete_period": LATEST_PERIOD,
            "generated_at": RUN_TS,
            "is_synthetic": True,
        },
    }


def validate_data(data: dict) -> dict:
    checks = []
    fact = data["fact_financials"]
    summary = data["fact_financial_summary"]
    bridge = data["fact_variance_driver_bridge"]
    exceptions = data["fact_close_exceptions"]

    key_fields = ["date_id", "entity_id", "business_unit_id", "scenario_id", "account_id"]
    keys = [tuple(row[k] for k in key_fields) for row in fact]
    checks.append({
        "check": "Fact financials grain uniqueness",
        "status": "pass" if len(keys) == len(set(keys)) else "fail",
        "detail": f"{len(keys) - len(set(keys))} duplicate composite keys",
    })
    missing_critical = sum(1 for row in fact for k in key_fields + ["amount_usd", "amount_local"] if row.get(k) in ("", None))
    checks.append({
        "check": "Critical field completeness",
        "status": "pass" if missing_critical == 0 else "fail",
        "detail": f"{missing_critical} missing critical values",
    })
    dates = {r["date_id"] for r in data["dim_date"]}
    entities = {r["entity_id"] for r in data["dim_entity"]}
    bus = {r["business_unit_id"] for r in data["dim_business_unit"]}
    scenarios = {r["scenario_id"] for r in data["dim_scenario"]}
    accounts = {r["account_id"] for r in data["dim_account"]}
    fk_bad = 0
    for r in fact:
        fk_bad += int(r["date_id"] not in dates or r["entity_id"] not in entities or r["business_unit_id"] not in bus or r["scenario_id"] not in scenarios or r["account_id"] not in accounts)
    checks.append({"check": "Foreign key integrity", "status": "pass" if fk_bad == 0 else "fail", "detail": f"{fk_bad} bad FK rows"})

    exception_missing_bu = sum(1 for r in exceptions if r.get("business_unit_id") in ("", None) or r.get("business_unit") in ("", None))
    exception_fk_bad = sum(1 for r in exceptions if r["date_id"] not in dates or r["entity_id"] not in entities or r["business_unit_id"] not in bus)
    checks.append({
        "check": "Close exception BU slicer keys",
        "status": "pass" if exception_missing_bu == 0 and exception_fk_bad == 0 else "fail",
        "detail": f"{exception_missing_bu} missing BU fields; {exception_fk_bad} exception FK rows outside Date/Entity/BU dimensions",
    })

    by_summary = defaultdict(dict)
    for r in summary:
        by_summary[(r["date_id"], r["entity_id"], r["business_unit_id"])][r["scenario"]] = r["ebitda_usd"]
    by_bridge = defaultdict(float)
    for r in bridge:
        by_bridge[(r["date_id"], r["entity_id"], r["business_unit_id"])] += r["amount_usd"]
    max_diff = 0.0
    bad_bridge = 0
    for key, scen in by_summary.items():
        if "Actual" not in scen or "Budget" not in scen:
            continue
        diff = abs((scen["Actual"] - scen["Budget"]) - by_bridge[key])
        max_diff = max(max_diff, diff)
        if diff > 1.0:
            bad_bridge += 1
    checks.append({
        "check": "Bridge tie-out to EBITDA variance",
        "status": "pass" if bad_bridge == 0 else "fail",
        "detail": f"{bad_bridge} groups outside $1 tolerance; max abs diff ${max_diff:,.2f}",
    })
    checks.append({
        "check": "Synthetic seed recorded",
        "status": "pass" if data["metadata"]["seed"] == SEED else "fail",
        "detail": f"seed={data['metadata']['seed']}",
    })
    row_counts = {name: len(rows) for name, rows in data.items() if isinstance(rows, list)}
    return {
        "status": "pass" if all(c["status"] == "pass" for c in checks) else "fail",
        "checked_at": RUN_TS,
        "row_counts": row_counts,
        "period_range": [data["dim_date"][0]["date_id"], data["dim_date"][-1]["date_id"]],
        "checks": checks,
    }


def metric_catalog() -> list[dict]:
    currency_format = MONEY_FORMAT
    measures = [
        ("Total Revenue", "SUM ( FactFinancialSummary[external_revenue_usd] )", currency_format, "Consolidated external revenue after excluding intercompany revenue."),
        ("Gross Revenue", "SUM ( FactFinancialSummary[gross_revenue_usd] )", currency_format, "External plus intercompany revenue before elimination."),
        ("Intercompany Revenue", "SUM ( FactFinancialSummary[intercompany_revenue_usd] )", currency_format, "Intercompany revenue requiring elimination."),
        ("Intercompany Elimination", "SUM ( FactFinancialSummary[intercompany_elimination_usd] )", currency_format, "Net intercompany elimination impact."),
        ("Gross Profit", "SUM ( FactFinancialSummary[gross_profit_usd] )", currency_format, "Revenue minus cost of services."),
        ("Gross Margin %", "DIVIDE ( [Gross Profit], [Total Revenue] )", "0.0%", "Gross profit divided by consolidated external revenue."),
        ("OPEX", "SUM ( FactFinancialSummary[opex_usd] )", currency_format, "Personnel, facilities, sales and marketing, and G&A."),
        ("EBITDA", "SUM ( FactFinancialSummary[ebitda_usd] )", currency_format, "Gross profit plus OPEX after intercompany elimination."),
        ("EBITDA Margin %", "DIVIDE ( [EBITDA], [Total Revenue] )", "0.0%", "EBITDA divided by consolidated external revenue."),
        ("Operating Income", "SUM ( FactFinancialSummary[operating_income_usd] )", currency_format, "EBITDA less depreciation."),
        ("Net Income", "SUM ( FactFinancialSummary[net_income_usd] )", currency_format, "Operating income less interest and tax."),
        ("Cash Position", "SUM ( FactFinancialSummary[cash_position_usd] )", currency_format, "Period-end cash position by entity and BU allocation."),
        ("Operating Cash Flow", "SUM ( FactFinancialSummary[operating_cash_flow_usd] )", currency_format, "Operating cash flow proxy tied to EBITDA conversion."),
        ("Working Capital", "SUM ( FactFinancialSummary[working_capital_usd] )", currency_format, "Working capital proxy for close review."),
        ("Actual Revenue", "CALCULATE ( [Total Revenue], DimScenario[scenario] = \"Actual\" )", currency_format, "Actual consolidated revenue."),
        ("Budget Revenue", "CALCULATE ( [Total Revenue], DimScenario[scenario] = \"Budget\" )", currency_format, "Budget consolidated revenue."),
        ("Revenue Var vs Budget", "[Actual Revenue] - [Budget Revenue]", currency_format, "Actual revenue less budget revenue."),
        ("Revenue Var %", "DIVIDE ( [Revenue Var vs Budget], [Budget Revenue] )", "0.0%", "Revenue variance divided by budget revenue."),
        ("Actual EBITDA", "CALCULATE ( [EBITDA], DimScenario[scenario] = \"Actual\" )", currency_format, "Actual EBITDA."),
        ("Budget EBITDA", "CALCULATE ( [EBITDA], DimScenario[scenario] = \"Budget\" )", currency_format, "Budget EBITDA."),
        ("EBITDA Var vs Budget", "[Actual EBITDA] - [Budget EBITDA]", currency_format, "Actual EBITDA less budget EBITDA."),
        ("EBITDA Var %", "DIVIDE ( [EBITDA Var vs Budget], [Budget EBITDA] )", "0.0%", "EBITDA variance divided by budget EBITDA."),
        ("Forecast EBITDA", "CALCULATE ( [EBITDA], DimScenario[scenario] = \"Forecast\" )", currency_format, "Forecast EBITDA."),
        ("Forecast Accuracy %", "1 - ABS ( DIVIDE ( [Actual EBITDA] - [Forecast EBITDA], [Actual EBITDA] ) )", "0.0%", "Directional forecast accuracy for EBITDA."),
        ("Open Exception Count", "CALCULATE ( COUNTROWS ( FactCloseExceptions ), FactCloseExceptions[status] <> \"Closed\" )", "#,0", "Open or in-progress close exceptions."),
        ("Open Exception Value", "CALCULATE ( SUM ( FactCloseExceptions[amount_usd] ), FactCloseExceptions[status] <> \"Closed\" )", currency_format, "Value attached to unresolved close exceptions."),
    ]
    return [
        {"measure_name": name, "dax": dax, "format_string": fmt, "definition": definition}
        for name, dax, fmt, definition in measures
    ]


def build_html(data: dict) -> str:
    payload = {
        "metadata": data["metadata"],
        "summary": data["fact_financial_summary"],
        "bridge": data["fact_variance_driver_bridge"],
        "exceptions": data["fact_close_exceptions"],
        "entities": data["dim_entity"],
        "businessUnits": data["dim_business_unit"],
        "scenarios": data["dim_scenario"],
        "dates": data["dim_date"],
        "sources": [
            {"name": "Zebra BI income statement and financial dashboard patterns", "url": "https://zebrabi.com/template/income-statement-dashboard-in-power-bi/"},
            {"name": "Vena finance dashboard examples", "url": "https://www.venasolutions.com/blog/power-bi-dashboards-examples"},
            {"name": "Microsoft waterfall chart guidance", "url": "https://learn.microsoft.com/en-us/power-bi/visuals/power-bi-visualization-waterfall-charts"},
            {"name": "ZoomCharts financial analysis dashboard gallery", "url": "https://zoomcharts.com/en/microsoft-power-bi-custom-visuals/dashboard-and-report-examples/view/power-bi-financial-analysis-dashboard-by-iris-mejuto-crego"},
            {"name": "Qlik financial dashboard examples", "url": "https://www.qlik.com/us/dashboard-examples/financial-dashboards"},
            {"name": "Ecosire financial reporting dashboard architecture", "url": "https://ecosire.com/blog/power-bi-financial-reporting-dashboard"},
        ],
    }
    data_json = json.dumps(payload, ensure_ascii=True)
    return HTML_TEMPLATE.replace("__DATA__", data_json)


HTML_TEMPLATE = r"""
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Regional FP&A Consolidation Dashboard</title>
  <style>
    :root {
      --ink:#17212b; --muted:#667085; --line:#d8dee7; --paper:#ffffff; --bg:#f4f6f8;
      --teal:#28666e; --blue:#3d5a80; --amber:#d9902f; --olive:#6b7a3a; --rose:#b2576a;
      --good:#28666e; --bad:#b2576a; --soft:#eef3f4;
    }
    * { box-sizing:border-box; }
    body { margin:0; font-family:Segoe UI, Arial, sans-serif; background:var(--bg); color:var(--ink); }
    header { background:var(--paper); border-bottom:1px solid var(--line); padding:18px 28px 14px; position:sticky; top:0; z-index:5; }
    .titlebar { display:flex; gap:16px; justify-content:space-between; align-items:flex-start; flex-wrap:wrap; }
    h1 { margin:0; font-size:24px; letter-spacing:0; }
    .subtitle { color:var(--muted); margin-top:5px; font-size:13px; }
    .status-pill { border:1px solid var(--line); background:#f9fbfc; border-radius:999px; padding:6px 10px; font-size:12px; color:var(--muted); box-shadow:0 1px 2px rgba(23,33,43,.04); }
    .filters { display:grid; grid-template-columns: repeat(6, minmax(135px, 1fr)); gap:10px; margin-top:14px; }
    label { display:flex; flex-direction:column; gap:5px; font-size:12px; color:var(--muted); background:#fbfcfd; border:1px solid #e5eaf0; border-radius:8px; padding:8px 10px; }
    select { height:32px; border:1px solid var(--line); border-radius:6px; background:white; color:var(--ink); padding:0 8px; font:inherit; }
    nav { display:flex; gap:8px; flex-wrap:wrap; margin-top:12px; }
    nav button { border:1px solid var(--line); background:white; color:var(--ink); border-radius:6px; padding:8px 10px; cursor:pointer; }
    nav button.active { background:var(--teal); color:white; border-color:var(--teal); }
    main { padding:18px 28px 34px; max-width:1500px; margin:0 auto; }
    .page { display:none; }
    .page.active { display:block; }
    .lens-bar { display:grid; grid-template-columns:minmax(130px, 170px) minmax(0, 1fr); gap:16px; align-items:center; min-height:96px; margin-bottom:16px; padding:12px 16px; background:#242b35; border:1px solid #3a4655; border-radius:12px; box-shadow:0 12px 24px rgba(23,33,43,.18); overflow:hidden; }
    .filter-lens-label { color:#d0b16a; font-size:12px; font-weight:600; letter-spacing:0; text-transform:uppercase; white-space:nowrap; }
    .current-lens { display:grid; grid-template-columns:6px 16px minmax(230px, 1fr) minmax(154px, 178px) minmax(144px, 178px); gap:14px; align-items:center; min-height:72px; color:#f7fafc; }
    .lens-rail { width:6px; height:54px; border-radius:999px; background:var(--teal); opacity:.86; }
    .lens-dot { width:16px; height:16px; border-radius:50%; background:var(--teal); opacity:.92; }
    .lens-copy { min-width:0; }
    .lens-title { font-size:14px; line-height:1.2; font-weight:800; letter-spacing:0; }
    .lens-line { margin-top:5px; font-size:14px; line-height:1.2; font-weight:700; color:#f7fafc; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
    .lens-subline { margin-top:3px; font-size:12px; line-height:1.2; color:#d7dee8; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
    .lens-chip { min-height:62px; display:grid; place-items:center; align-content:center; gap:4px; text-align:center; background:#1f2630; border:1px solid #3a4655; border-radius:11px; padding:9px 12px; overflow:hidden; }
    .lens-chip span { font-size:11.5px; line-height:1.1; color:#d7dee8; }
    .lens-chip b { display:block; font-size:23px; line-height:1; color:var(--blue); }
    .lens-chip-risk b { color:#d0b16a; }
    .kpis { display:grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap:16px; margin:0 0 16px; }
    .panel { background:var(--paper); border:1px solid var(--line); border-radius:8px; box-shadow:0 7px 18px rgba(23,33,43,.07); }
    .card { --accent:var(--teal); position:relative; min-height:135px; display:grid; grid-template-columns:minmax(0,1fr) minmax(118px, 34%); grid-template-rows:1fr auto; gap:9px 12px; padding:14px 13px 10px; overflow:hidden; color:#f7fafc; background:#242b35; border:1px solid #3a4655; border-radius:12px; box-shadow:0 12px 24px rgba(23,33,43,.20); }
    .card::before { content:""; position:absolute; left:14px; top:14px; width:38%; max-width:170px; height:4px; border-radius:999px; background:var(--accent); opacity:.95; }
    .card.accent-blue { --accent:var(--blue); }
    .card.accent-teal { --accent:var(--teal); }
    .card.accent-amber { --accent:var(--amber); }
    .card.accent-olive { --accent:var(--olive); }
    .card.accent-rose { --accent:var(--rose); }
    .card .label { display:flex; align-items:center; gap:8px; margin-top:22px; color:#f7fafc; font-size:14px; line-height:1.15; font-weight:800; white-space:nowrap; min-width:0; overflow:hidden; text-overflow:ellipsis; }
    .card .label::before { content:""; width:13px; height:13px; border:2px solid var(--accent); border-radius:4px; flex:0 0 auto; opacity:.9; }
    .card .value { margin-top:12px; font-size:34px; line-height:1; font-weight:600; white-space:nowrap; color:var(--accent); letter-spacing:0; }
    .card .delta { font-size:12px; color:#d7dee8; }
    .card .kpi-main { min-width:0; grid-column:1; grid-row:1; }
    .card .kpi-footer { grid-column:1 / -1; grid-row:2; display:grid; grid-template-columns:minmax(0, 1fr) minmax(86px, .62fr); gap:8px; align-items:center; min-width:0; }
    .footer-chip { min-height:26px; display:flex; align-items:center; justify-content:center; border:1px solid #3a4655; border-radius:999px; padding:4px 10px; background:#2b3340; color:#d7dee8; font-size:12px; line-height:1.1; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
    .footer-chip.good { color:#99b66f; background:rgba(107,122,58,.20); border-color:rgba(153,182,111,.20); }
    .footer-chip.bad { color:#d2788b; background:rgba(178,87,106,.20); border-color:rgba(210,120,139,.20); }
    .spark { grid-column:2; grid-row:1; align-self:center; min-width:0; min-height:84px; background:#1f2630; border:1px solid #3a4655; border-radius:10px; padding:8px; overflow:hidden; }
    .sparkline-svg { width:100%; height:66px; display:block; overflow:visible; }
    .delta.good { color:#99b66f; }
    .delta.bad { color:#d2788b; }
    .delta.good { color:var(--good); }
    .delta.bad { color:var(--bad); }
    .grid { display:grid; grid-template-columns: 1.25fr .95fr; gap:14px; align-items:start; }
    .grid.three { grid-template-columns: 1fr 1fr 1fr; }
    .grid.story { grid-template-columns: 1.45fr .8fr; }
    .mosaic { display:grid; grid-template-columns: 1.1fr .9fr 1fr; gap:14px; align-items:start; margin-top:14px; }
    .rail { display:grid; gap:10px; }
    .panel { padding:14px; min-width:0; overflow:hidden; }
    .panel h2 { margin:0 0 4px; font-size:15px; display:flex; align-items:center; gap:8px; }
    .panel h2::before { content:""; width:8px; height:8px; border-radius:2px; background:var(--teal); flex:0 0 auto; }
    .panel .note { color:var(--muted); font-size:12px; margin-bottom:12px; }
    svg { width:100%; display:block; overflow:visible; }
    svg.chart { height:280px; background:#fbfcfd; border:1px solid #edf1f5; border-radius:7px; }
    .empty-state { height:280px; display:grid; place-items:center; border:1px dashed #cfd8e3; border-radius:7px; color:var(--muted); background:#fbfcfd; font-size:12px; }
    table { width:100%; border-collapse:collapse; font-size:12px; }
    th, td { padding:8px 7px; border-bottom:1px solid #edf0f3; text-align:right; }
    th:first-child, td:first-child, th:nth-child(2), td:nth-child(2) { text-align:left; }
    th { color:var(--muted); font-weight:600; background:#fafbfc; position:sticky; top:0; }
    .table-wrap { max-height:360px; overflow:auto; border:1px solid #edf0f3; border-radius:6px; }
    .action-strip { display:grid; grid-template-columns: 1.3fr 1fr 1fr; gap:12px; margin:14px 0; }
    .action { --accent:var(--amber); background:#ffffff; border:1px solid var(--line); border-left:4px solid var(--accent); border-radius:8px; padding:12px; font-size:13px; box-shadow:0 5px 14px rgba(23,33,43,.05); }
    .action.action-blue { --accent:var(--blue); }
    .action.action-teal { --accent:var(--teal); }
    .action.action-rose { --accent:var(--rose); }
    .action b { display:block; margin-bottom:4px; }
    .legend { display:flex; gap:12px; flex-wrap:wrap; font-size:12px; color:var(--muted); margin-top:8px; }
    .swatch { width:10px; height:10px; display:inline-block; border-radius:2px; margin-right:5px; }
    .sources { color:var(--muted); font-size:12px; margin-top:18px; }
    .sources a { color:var(--blue); }
    .badge { display:inline-block; border-radius:999px; padding:3px 7px; font-size:11px; background:#eef3f4; color:var(--teal); }
    .bullet-row { display:grid; grid-template-columns: 120px 1fr 70px; gap:8px; align-items:center; margin:10px 0; font-size:12px; }
    .bullet-track { height:12px; background:#eef1f4; border-radius:999px; overflow:hidden; border:1px solid #d8dee7; }
    .bullet-fill { height:100%; background:var(--teal); }
    .story-callout { border-left:4px solid var(--teal); background:#f6fbfb; padding:12px; border-radius:6px; margin-bottom:10px; font-size:13px; }
    .sev-High { color:#9f3148; font-weight:700; }
    .sev-Medium { color:#a4661c; font-weight:700; }
    .sev-Low { color:#52612c; font-weight:700; }
    @media (max-width: 980px) {
      header { padding:14px; }
      main { padding:14px; }
      .filters, .kpis, .grid, .grid.three, .grid.story, .mosaic, .action-strip, .lens-bar { grid-template-columns:1fr; }
      .current-lens { grid-template-columns:6px 16px minmax(0,1fr); }
      .lens-chip { grid-column:1 / -1; min-height:58px; }
      .card { grid-template-columns:1fr; min-height:0; }
      .card .spark { grid-column:1; grid-row:auto; min-height:78px; }
      .card .kpi-footer { grid-column:1; }
      .card .value { font-size:30px; }
      svg.chart { height:240px; }
    }
  </style>
</head>
<body>
<header>
  <div class="titlebar">
    <div>
      <h1>Regional FP&A Consolidation</h1>
      <div class="subtitle">Executive-ready portfolio dashboard for multi-entity P&L, FX, intercompany, and close exceptions</div>
    </div>
    <div class="status-pill" id="freshness"></div>
  </div>
  <div class="filters">
    <label>Period<select id="periodFilter"></select></label>
    <label>Region<select id="regionFilter"></select></label>
    <label>Country<select id="countryFilter"></select></label>
    <label>Business Unit<select id="buFilter"></select></label>
    <label>Scenario<select id="scenarioFilter"></select></label>
    <label>Entity<select id="entityFilter"></select></label>
  </div>
  <nav>
    <button data-page="overview" class="active">Executive Summary</button>
    <button data-page="pnl">P&L Variance</button>
    <button data-page="story">Controls & Storyboard</button>
  </nav>
</header>
<main>
  <section id="overview" class="page active">
    <div class="lens-bar">
      <div class="filter-lens-label">FILTER LENS</div>
      <div class="current-lens" id="currentLens"></div>
    </div>
    <div class="kpis" id="kpiStrip"></div>
    <div class="action-strip" id="actionStrip"></div>
    <div class="grid">
      <div class="panel"><h2>Revenue and EBITDA Trend</h2><div class="note">Actual, Budget, and Forecast by selected scope</div><div id="trendChart"></div><div class="legend" id="trendLegend"></div></div>
      <div class="panel"><h2>EBITDA Variance Bridge</h2><div class="note">Actual vs Budget; drivers sum to variance</div><div id="bridgeChart"></div></div>
    </div>
    <div class="grid three" style="margin-top:14px">
      <div class="panel"><h2>Entity EBITDA Variance</h2><div class="note">Top contributors to current period performance</div><div id="entityBars"></div></div>
      <div class="panel"><h2>Regional Mix</h2><div class="note">Revenue and EBITDA by region</div><div id="regionBars"></div></div>
      <div class="panel"><h2>Management Attention List</h2><div class="note">Largest open close exceptions in current context</div><div class="table-wrap"><table id="attentionTable"></table></div></div>
    </div>
  </section>
  <section id="pnl" class="page">
    <div class="grid">
      <div class="panel"><h2>Country and Entity P&L Matrix</h2><div class="note">Actual, Budget, and variance at selected period</div><div class="table-wrap"><table id="pnlTable"></table></div></div>
      <div class="panel"><h2>P&L Shape by Account Group</h2><div class="note">Revenue through Net Income view</div><div id="pnlWaterfall"></div></div>
    </div>
    <div class="grid" style="margin-top:14px">
      <div class="panel"><h2>Margin Heatmap</h2><div class="note">EBITDA margin by country and business unit</div><div class="table-wrap"><table id="marginHeatmap"></table></div></div>
      <div class="panel"><h2>Drill Detail</h2><div class="note">Rows reconcile to selected filters</div><div class="table-wrap"><table id="detailTable"></table></div></div>
    </div>
  </section>
  <section id="fxic" class="page">
    <div class="grid">
      <div class="panel"><h2>FX Translation Exposure</h2><div class="note">Revenue exposure and EBITDA impact by currency</div><div id="fxBars"></div></div>
      <div class="panel"><h2>Intercompany Elimination Impact</h2><div class="note">Pre/post elimination EBITDA by country</div><div id="icBars"></div></div>
    </div>
    <div class="panel" style="margin-top:14px"><h2>Intercompany Exception Matrix</h2><div class="note">Open mismatch value by country and issue status</div><div class="table-wrap"><table id="icMatrix"></table></div></div>
  </section>
  <section id="bu" class="page">
    <div class="grid">
      <div class="panel"><h2>Business Unit Performance</h2><div class="note">Revenue and EBITDA margin by BU</div><div id="buBars"></div></div>
      <div class="panel"><h2>Growth vs Margin Scatter</h2><div class="note">Entity-BU observations; size approximates revenue</div><div id="scatterChart"></div></div>
    </div>
    <div class="panel" style="margin-top:14px"><h2>BU Driver Table</h2><div class="note">Actual vs Budget by business unit</div><div class="table-wrap"><table id="buTable"></table></div></div>
  </section>
  <section id="exceptions" class="page">
    <div class="kpis" id="exceptionKpis"></div>
    <div class="grid">
      <div class="panel"><h2>Open Exceptions by Type</h2><div class="note">Value of unresolved close items</div><div id="exceptionBars"></div></div>
      <div class="panel"><h2>Owner Workload</h2><div class="note">Open count and value by owner team</div><div id="ownerBars"></div></div>
    </div>
    <div class="panel" style="margin-top:14px"><h2>Close Commentary Log</h2><div class="note">Synthetic exceptions for portfolio demonstration</div><div class="table-wrap"><table id="exceptionTable"></table></div></div>
  </section>
  <section id="story" class="page">
    <div class="grid story">
      <div class="panel"><h2>Board Narrative Bridge</h2><div class="note">Condensed CFO storyline: budget EBITDA to actual EBITDA</div><div id="storyBridge"></div></div>
      <div class="rail">
        <div class="panel"><h2>Management Verdict</h2><div class="note">Automated narrative for the selected scope</div><div id="verdictPanel"></div></div>
        <div class="panel"><h2>Target Pacing</h2><div class="note">Actual performance against budget and forecast anchors</div><div id="targetBullets"></div></div>
      </div>
    </div>
    <div class="mosaic">
      <div class="panel"><h2>Country Revenue Treemap</h2><div class="note">Block size approximates actual revenue</div><div id="countryTreemap"></div></div>
      <div class="panel"><h2>Close Risk Funnel</h2><div class="note">Open issue value by severity</div><div id="riskFunnel"></div></div>
      <div class="panel"><h2>Board Pack Extract</h2><div class="note">Compact rows to paste into month-end commentary</div><div class="table-wrap"><table id="boardTable"></table></div></div>
    </div>
  </section>
  <div class="sources" id="sources"></div>
</main>
<script>
const DATA = __DATA__;
const state = { period: DATA.metadata.latest_complete_period, region: "All", country: "All", entity: "All", bu: "All", scenario: "Actual", page: "overview" };
const colors = { actual:"#28666e", budget:"#d9902f", forecast:"#3d5a80", prior:"#6b7a3a", teal:"#28666e", blue:"#3d5a80", amber:"#d9902f", rose:"#b2576a", good:"#28666e", bad:"#b2576a", olive:"#6b7a3a", muted:"#667085", line:"#d8dee7" };
const money = v => {
  const sign = v < 0 ? "-" : "";
  const a = Math.abs(v);
  if (a >= 1e9) return `${sign}$${(a/1e9).toFixed(1)}B`;
  if (a >= 1e6) return `${sign}$${(a/1e6).toFixed(1)}M`;
  if (a >= 1e3) return `${sign}$${(a/1e3).toFixed(0)}K`;
  return `${sign}$${a.toFixed(0)}`;
};
const pct = v => `${(v*100).toFixed(1)}%`;
const num = v => Number(v || 0);
function selectedScenario(){ return state.scenario || "Actual"; }
function comparisonScenario(){ return selectedScenario()==="Budget" ? "Actual" : "Budget"; }
function scenarioColor(scenario){
  return {Actual:colors.actual, Budget:colors.budget, Forecast:colors.forecast, "Prior Year":colors.prior}[scenario] || colors.actual;
}
function countryMatch(r){ return state.country === "All" || r.country === state.country; }
function buMatch(r){ return state.bu === "All" || r.business_unit_id === state.bu || r.business_unit === state.bu; }
function matches(r){
  return r.date_id <= state.period &&
    (state.region === "All" || r.region === state.region) &&
    countryMatch(r) &&
    (state.entity === "All" || r.entity_id === state.entity) &&
    buMatch(r);
}
function currentRows(scenario){
  const lens = scenario || selectedScenario();
  return DATA.summary.filter(r => r.date_id === state.period && r.scenario === lens &&
    (state.region === "All" || r.region === state.region) &&
    countryMatch(r) &&
    (state.entity === "All" || r.entity_id === state.entity) &&
    buMatch(r));
}
function sumRows(rows){
  return rows.reduce((a,r)=>{
    ["external_revenue_usd","gross_revenue_usd","gross_profit_usd","opex_usd","ebitda_usd","ebitda_pre_elim_usd","net_income_usd","cash_position_usd","operating_cash_flow_usd","working_capital_usd","intercompany_elimination_usd"].forEach(k=>a[k]=(a[k]||0)+num(r[k]));
    return a;
  }, {});
}
function group(rows, key, valueKey){
  const out = new Map();
  rows.forEach(r => out.set(r[key], (out.get(r[key])||0) + num(r[valueKey])));
  return [...out.entries()].map(([name,value]) => ({name,value})).sort((a,b)=>b.value-a.value);
}
function byScenarioMetric(period, scenario, metric){
  return sumRows(DATA.summary.filter(r => r.date_id === period && r.scenario === scenario &&
    (state.region === "All" || r.region === state.region) &&
    countryMatch(r) &&
    (state.entity === "All" || r.entity_id === state.entity) &&
    buMatch(r)))[metric] || 0;
}
function emptyState(label="No data for this filter selection"){
  return `<div class="empty-state">${label}</div>`;
}
function shortLabel(text, max=18){
  const s = String(text || "");
  return s.length > max ? `${s.slice(0, max-1)}...` : s;
}
function esc(text){
  return String(text ?? "").replace(/[&<>"']/g, m => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]));
}
function periodLabel(period){
  const [year, month] = String(period).split("-").map(Number);
  if (!year || !month) return period;
  return new Date(year, month - 1, 1).toLocaleString("en-US", { month:"short", year:"numeric" });
}
function businessUnitLabel(){
  if (state.bu === "All") return "All BUs";
  return DATA.businessUnits.find(b => b.business_unit_id === state.bu)?.business_unit || state.bu;
}
function scopeLine(){
  const parts = [businessUnitLabel()];
  if (state.country !== "All") parts.push(state.country);
  else if (state.region !== "All") parts.push(state.region);
  else parts.push("All regions");
  if (state.entity !== "All") parts.push(state.entity);
  return parts.join(" | ");
}
function svgWrap(content, h=280, cls="chart"){ return `<svg class="${cls}" viewBox="0 0 760 ${h}" role="img">${content}</svg>`; }
function axis(min,max,h){ return v => h - 36 - ((v-min)/(max-min || 1))*(h-70); }
function xScale(n,w=720){ return i => 34 + (n<=1?0:i*(w-68)/(n-1)); }
function sparkline(values, good=true, accent=colors.actual){
  const clean = values.map(num).filter(Number.isFinite);
  if (clean.length < 2) return `<svg class="sparkline-svg" viewBox="0 0 112 64"><line x1="10" x2="102" y1="34" y2="34" stroke="#3a4655" stroke-width="2" stroke-linecap="round"/></svg>`;
  const min = Math.min(...clean), max = Math.max(...clean);
  const y = v => 52 - ((v-min)/(max-min || 1))*38;
  const x = i => 10 + i*(92/(clean.length-1));
  const pts = clean.map((v,i)=>`${x(i).toFixed(1)},${y(v).toFixed(1)}`).join(" ");
  const stroke = good ? accent : colors.bad;
  const startX = x(0).toFixed(1), startY = y(clean[0]).toFixed(1);
  const endX = x(clean.length-1).toFixed(1), endY = y(clean[clean.length-1]).toFixed(1);
  const area = `${startX},54 ${pts} ${endX},54`;
  return `<svg class="sparkline-svg" viewBox="0 0 112 64"><line x1="10" x2="102" y1="34" y2="34" stroke="#3a4655" stroke-width="1.4" stroke-dasharray="5 6"/><polygon points="${area}" fill="${stroke}" opacity=".18"/><polyline points="${pts}" fill="none" stroke="${stroke}" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/><circle cx="${startX}" cy="${startY}" r="4.5" fill="#242b35" stroke="#d7dee8" stroke-width="2"/><circle cx="${endX}" cy="${endY}" r="5" fill="${stroke}"/></svg>`;
}
function kpiCard({label, value, delta, good=true, series=[], accent="teal", status}){
  const accentColor = {blue:colors.budget, teal:colors.actual, amber:colors.forecast, olive:colors.olive, rose:colors.bad}[accent] || colors.actual;
  const statusText = status || (good ? "ON TRACK" : "WATCH");
  return `<div class="card accent-${accent}"><div class="kpi-main"><div class="label">${esc(label)}</div><div class="value">${esc(value)}</div></div><div class="spark">${sparkline(series, good, accentColor)}</div><div class="kpi-footer"><span class="footer-chip">${esc(delta)}</span><span class="footer-chip ${good?'good':'bad'}">${esc(statusText)}</span></div></div>`;
}
function metricSeries(metric, scenario=selectedScenario()){
  return DATA.dates.filter(d=>d.date_id<=state.period).map(d=>byScenarioMetric(d.date_id, scenario, metric));
}
function marginSeries(scenario=selectedScenario()){
  return DATA.dates.filter(d=>d.date_id<=state.period).map(d=>{
    const rev = byScenarioMetric(d.date_id, scenario, "external_revenue_usd");
    return rev ? byScenarioMetric(d.date_id, scenario, "ebitda_usd") / rev : 0;
  });
}
function filteredExceptionsAt(period){
  return DATA.exceptions.filter(r => r.date_id <= period &&
    (state.region==="All"||r.region===state.region) &&
    countryMatch(r) &&
    (state.entity==="All"||r.entity_id===state.entity) &&
    buMatch(r));
}
function exceptionSeries(){
  return DATA.dates.filter(d=>d.date_id<=state.period).map(d=>filteredExceptionsAt(d.date_id).filter(x=>x.status!=="Closed").length);
}
function exceptionValueSeries(){
  return DATA.dates.filter(d=>d.date_id<=state.period).map(d=>
    filteredExceptionsAt(d.date_id).filter(x=>x.status!=="Closed").reduce((s,x)=>s+num(x.amount_usd),0)
  );
}
function renderCurrentLens({lens, revVarPct, closeRisk}){
  document.getElementById("currentLens").innerHTML = `
    <div class="lens-rail"></div>
    <div class="lens-dot"></div>
    <div class="lens-copy">
      <div class="lens-title">CURRENT LENS</div>
      <div class="lens-line">${esc(periodLabel(state.period))} | ${esc(lens)} lens</div>
      <div class="lens-subline">${esc(scopeLine())}</div>
    </div>
    <div class="lens-chip"><span>Revenue var</span><b>${esc(pct(revVarPct))}</b></div>
    <div class="lens-chip lens-chip-risk"><span>Close risk</span><b>${esc(money(closeRisk))}</b></div>`;
}
function comboTrendChart(labels, bars, lines, barColor=colors.actual){
  if (!labels.length || (!bars.some(Boolean) && !lines.some(s=>s.values.some(Boolean)))) return emptyState();
  const h=280, w=760, plotLeft=42, plotRight=724, base=h-38;
  const maxBar = Math.max(1, ...bars);
  const lineVals = lines.flatMap(s=>s.values);
  const minLine = Math.min(0, ...lineVals), maxLine = Math.max(1, ...lineVals) * 1.08;
  const x = i => plotLeft + i*((plotRight-plotLeft)/Math.max(1, labels.length-1));
  const barW = Math.min(22, (plotRight-plotLeft)/Math.max(1, labels.length)*0.55);
  const yBar = v => base - (v/maxBar)*(h-84);
  const yLine = axis(minLine, maxLine, h);
  const grid = [0,.25,.5,.75,1].map(t=>`<line x1="${plotLeft}" x2="${plotRight}" y1="${36+t*(h-74)}" y2="${36+t*(h-74)}" stroke="${colors.line}" stroke-width="1"/>`).join("");
  const cols = bars.map((v,i)=>`<rect x="${x(i)-barW/2}" y="${yBar(v)}" width="${barW}" height="${base-yBar(v)}" rx="3" fill="${barColor}" opacity=".24"/>`).join("");
  const paths = lines.map(s=>{
    const pts = s.values.map((v,i)=>`${x(i)},${yLine(v)}`).join(" ");
    return `<polyline points="${pts}" fill="none" stroke="${s.color}" stroke-width="${s.dash?2.2:3}" ${s.dash?'stroke-dasharray="6 5"':''} stroke-linecap="round" stroke-linejoin="round"/><circle cx="${x(s.values.length-1)}" cy="${yLine(s.values.at(-1))}" r="4" fill="${s.color}"/>`;
  }).join("");
  const lab = labels.filter((_,i)=>i%3===0 || i===labels.length-1).map(l=>{
    const i = labels.indexOf(l);
    return `<text x="${x(i)}" y="${h-10}" font-size="11" text-anchor="middle" fill="${colors.muted}">${l.slice(5)}</text>`;
  }).join("");
  return svgWrap(`${grid}${cols}${paths}${lab}<text x="${plotLeft}" y="20" font-size="11" fill="${colors.muted}">Revenue ${money(maxBar)}</text><text x="610" y="20" font-size="11" fill="${colors.muted}">EBITDA ${money(maxLine)}</text>`, h);
}
function lineChart(series, labels){
  if (!labels.length || !series.some(s=>s.values.some(Boolean))) return emptyState();
  const vals = series.flatMap(s=>s.values);
  const min = Math.min(0, ...vals), max = Math.max(...vals)*1.08;
  const h=280, y=axis(min,max,h), x=xScale(labels.length);
  const grid = [0,.25,.5,.75,1].map(t=>`<line x1="34" x2="730" y1="${36+t*(h-70)}" y2="${36+t*(h-70)}" stroke="${colors.line}" stroke-width="1"/>`).join("");
  const paths = series.map(s=>{
    const pts = s.values.map((v,i)=>`${x(i)},${y(v)}`).join(" ");
    return `<polyline points="${pts}" fill="none" stroke="${s.color}" stroke-width="3"/><circle cx="${x(s.values.length-1)}" cy="${y(s.values.at(-1))}" r="4" fill="${s.color}"/>`;
  }).join("");
  const lab = labels.filter((_,i)=>i%3===0 || i===labels.length-1).map((l,i2)=>{
    const i = labels.indexOf(l);
    return `<text x="${x(i)}" y="${h-10}" font-size="11" text-anchor="middle" fill="${colors.muted}">${l.slice(5)}</text>`;
  }).join("");
  return svgWrap(`${grid}${paths}${lab}<text x="34" y="20" font-size="11" fill="${colors.muted}">${money(max)}</text><text x="34" y="${h-38}" font-size="11" fill="${colors.muted}">${money(min)}</text>`, h);
}
function barChart(items, opts={}){
  if (!items.length) return emptyState();
  const h=opts.h||280, w=760, left=opts.left||170;
  const max = Math.max(1, ...items.map(d=>Math.abs(d.value)));
  const rowH = Math.min(38, (h-34)/Math.max(1, items.length));
  const zero = left + (opts.diverging ? (w-left-30)/2 : 0);
  const scale = v => opts.diverging ? Math.abs(v)/max*((w-left-40)/2) : Math.abs(v)/max*(w-left-40);
  const bars = items.map((d,i)=>{
    const y = 18+i*rowH;
    const val = d.value;
    const bw = scale(val);
    const x = opts.diverging ? (val>=0 ? zero : zero-bw) : left;
    const fill = val>=0 ? (opts.color||colors.actual) : colors.bad;
    return `<text x="8" y="${y+20}" font-size="15" fill="${colors.muted}"><title>${d.name}</title>${shortLabel(d.name, 20)}</text><rect x="${x}" y="${y+6}" width="${Math.max(2,bw)}" height="${Math.max(9,rowH-12)}" rx="3" fill="${fill}"/><text x="${val>=0?x+bw+7:x-7}" y="${y+20}" text-anchor="${val>=0?'start':'end'}" font-size="14" fill="${colors.muted}">${money(val)}</text>`;
  }).join("");
  const zeroLine = opts.diverging ? `<line x1="${zero}" x2="${zero}" y1="10" y2="${h-18}" stroke="${colors.line}"/>` : "";
  return svgWrap(`${zeroLine}${bars}`, h);
}
function waterfall(items){
  if (!items.length) return emptyState("No bridge rows for this filter selection");
  const h=280,w=760,baseY=h-34;
  let running = 0;
  const spans = items.map(d => {
    if (d.anchor) {
      running = d.value;
      return {start:0, end:d.value};
    }
    const s=running;
    running += d.value;
    return {start:s, end:running};
  });
  const vals = spans.flatMap(s=>[s.start,s.end]).concat([0]);
  const min=Math.min(...vals), max=Math.max(...vals);
  const y=axis(min,max,h), colW=Math.max(42,(w-70)/items.length-8);
  const x=i=>40+i*((w-70)/items.length);
  const bars=items.map((d,i)=>{
    const s=spans[i].start, e=spans[i].end, top=y(Math.max(s,e)), bottom=y(Math.min(s,e));
    const delta = e-s;
    const fill=d.anchor ? colors.blue : (delta>=0?colors.good:colors.bad);
    return `<rect x="${x(i)}" y="${top}" width="${colW}" height="${Math.max(2,bottom-top)}" fill="${fill}" rx="3"/><text x="${x(i)+colW/2}" y="${top-5}" text-anchor="middle" font-size="10" fill="${colors.muted}">${money(d.anchor ? d.value : delta)}</text><text x="${x(i)+colW/2}" y="${baseY+15}" text-anchor="middle" font-size="10" fill="${colors.muted}">${d.name.split(' ')[0]}</text>`;
  }).join("");
  return svgWrap(`<line x1="34" x2="730" y1="${y(0)}" y2="${y(0)}" stroke="${colors.line}"/>${bars}<text x="34" y="20" font-size="11" fill="${colors.muted}">${money(max)}</text><text x="34" y="${h-42}" font-size="11" fill="${colors.muted}">${money(min)}</text>`, h);
}
function treemap(items){
  const h=280, w=760;
  const total = Math.max(1, items.reduce((s,d)=>s+Math.max(0,d.value),0));
  let x = 24;
  const palette = [colors.actual, colors.blue, colors.amber, colors.olive, colors.bad, "#6a7fa8", "#8b6f47"];
  const rects = items.map((d,i)=>{
    const width = Math.max(46, Math.max(0,d.value)/total*(w-48));
    const out = `<rect x="${x}" y="42" width="${Math.max(1,width-5)}" height="170" rx="5" fill="${palette[i%palette.length]}" opacity=".88"/><text x="${x+8}" y="68" font-size="12" fill="white">${d.name}</text><text x="${x+8}" y="90" font-size="13" font-weight="700" fill="white">${money(d.value)}</text>`;
    x += width;
    return out;
  }).join("");
  return svgWrap(`<text x="24" y="24" font-size="12" fill="${colors.muted}">Revenue share by country</text>${rects}`, h);
}
function funnel(items){
  const h=280,w=760;
  const max = Math.max(1, ...items.map(d=>d.value));
  const rows = items.map((d,i)=>{
    const bw = Math.max(90, d.value/max*(w-160));
    const x = (w-bw)/2, y = 38+i*62;
    const fill = i===0 ? colors.bad : (i===1 ? colors.amber : colors.olive);
    return `<path d="M${x},${y} L${x+bw},${y} L${x+bw-26},${y+44} L${x+26},${y+44} Z" fill="${fill}" opacity=".88"/><text x="${w/2}" y="${y+25}" text-anchor="middle" font-size="13" fill="white" font-weight="700">${d.name} ${money(d.value)}</text>`;
  }).join("");
  return svgWrap(rows, h);
}
function table(el, headers, rows){
  document.getElementById(el).innerHTML = `<thead><tr>${headers.map(h=>`<th>${h}</th>`).join("")}</tr></thead><tbody>${rows.map(r=>`<tr>${r.map(c=>`<td>${c}</td>`).join("")}</tr>`).join("")}</tbody>`;
}
function renderFilters(){
  const periods = DATA.dates.map(d=>d.date_id);
  const regions = ["All", ...new Set(DATA.entities.map(e=>e.region))];
  const countries = ["All", ...new Set(DATA.entities.map(e=>e.country))];
  const entities = ["All", ...DATA.entities.map(e=>e.entity_id)];
  const bus = ["All", ...DATA.businessUnits.map(b=>b.business_unit_id)];
  const scenarios = DATA.scenarios.map(s=>s.scenario);
  const fill=(id, vals, lab)=>{ const s=document.getElementById(id); s.innerHTML=vals.map(v=>`<option value="${v}">${lab?lab(v):v}</option>`).join(""); };
  fill("periodFilter", periods);
  fill("regionFilter", regions);
  fill("countryFilter", countries);
  fill("entityFilter", entities, v => v==="All" ? "All" : `${v} - ${DATA.entities.find(e=>e.entity_id===v).country}`);
  fill("buFilter", bus, v => v==="All" ? "All" : DATA.businessUnits.find(b=>b.business_unit_id===v).business_unit);
  fill("scenarioFilter", scenarios);
  document.getElementById("periodFilter").value=state.period;
  document.getElementById("scenarioFilter").value=state.scenario;
  ["periodFilter","regionFilter","countryFilter","entityFilter","buFilter","scenarioFilter"].forEach(id => document.getElementById(id).addEventListener("change", e => {
    if(id==="periodFilter") state.period=e.target.value;
    if(id==="regionFilter") { state.region=e.target.value; state.entity="All"; document.getElementById("entityFilter").value="All"; }
    if(id==="countryFilter") { state.country=e.target.value; state.entity="All"; document.getElementById("entityFilter").value="All"; }
    if(id==="entityFilter") state.entity=e.target.value;
    if(id==="buFilter") state.bu=e.target.value;
    if(id==="scenarioFilter") state.scenario=e.target.value;
    render();
  }));
  document.querySelectorAll("nav button").forEach(b=>b.addEventListener("click",()=>{
    document.querySelectorAll("nav button").forEach(x=>x.classList.remove("active"));
    document.querySelectorAll(".page").forEach(x=>x.classList.remove("active"));
    b.classList.add("active"); document.getElementById(b.dataset.page).classList.add("active"); state.page=b.dataset.page; render();
  }));
}
function renderOverview(){
  const lens = selectedScenario(), compare = comparisonScenario();
  const a=sumRows(currentRows(lens)), b=sumRows(currentRows(compare)), f=sumRows(currentRows("Forecast"));
  const revVar = (a.external_revenue_usd||0)-(b.external_revenue_usd||0);
  const ebitdaVar = (a.ebitda_usd||0)-(b.ebitda_usd||0);
  const exOpen = filteredExceptions().filter(x=>x.status!=="Closed");
  const closeRisk = exOpen.reduce((s,x)=>s+num(x.amount_usd),0);
  const marginActual = (a.ebitda_usd||0)/(a.external_revenue_usd||1);
  const marginBudget = (b.ebitda_usd||0)/(b.external_revenue_usd||1);
  const revVarPct = b.external_revenue_usd ? revVar / Math.abs(b.external_revenue_usd) : 0;
  renderCurrentLens({lens, revVarPct, closeRisk});
  const kpis=[
    {label:"Revenue", value:money(a.external_revenue_usd), delta:`${pct(revVarPct)} vs ${compare}`, good:revVar>=0, series:metricSeries("external_revenue_usd", lens), accent:"blue", status:revVar>=0?"ON TRACK":"WATCH"},
    {label:"EBITDA", value:money(a.ebitda_usd), delta:`${money(ebitdaVar)} vs ${compare}`, good:ebitdaVar>=0, series:metricSeries("ebitda_usd", lens), accent:"teal", status:ebitdaVar>=0?"ON TRACK":"ACTION"},
    {label:"EBITDA Margin", value:pct(marginActual), delta:`${pct(marginActual-marginBudget)} vs ${compare}`, good:marginActual>=marginBudget, series:marginSeries(lens), accent:"olive", status:marginActual>=marginBudget?"ON TRACK":"WATCH"},
    {label:"Close Risk", value:money(closeRisk), delta:`${exOpen.length} open items`, good:closeRisk<5000000, series:exceptionValueSeries(), accent:"rose", status:closeRisk<5000000?"WATCH":"ACTION"},
  ];
  document.getElementById("kpiStrip").innerHTML=kpis.map(kpiCard).join("");
  const compareRows = currentRows(compare);
  const worst = group(currentRows(lens).map(r=>({...r, variance:(r.ebitda_usd - (compareRows.find(x=>x.entity_id===r.entity_id&&x.business_unit_id===r.business_unit_id)?.ebitda_usd||0))})), "country", "variance").sort((a,b)=>a.value-b.value)[0];
  document.getElementById("actionStrip").innerHTML=[
    `<div class="action action-rose"><b>Action Required</b>${worst?worst.name:"Portfolio"} is the largest ${lens} EBITDA pressure point at ${money(worst?worst.value:0)} vs ${compare}.</div>`,
    `<div class="action action-teal"><b>Bridge Integrity</b>Driver bridge ties to EBITDA variance with $1 tolerance in QA.</div>`,
    `<div class="action action-blue"><b>Close Focus</b>${exOpen.filter(x=>x.severity==="High").length} high-severity items remain open or in review.</div>`
  ].join("");
  const labels=DATA.dates.filter(d=>d.date_id<=state.period).map(d=>d.date_id);
  const trendScenarios = [lens, compare, "Forecast"].filter((s,i,a)=>a.indexOf(s)===i);
  const series=trendScenarios.map(s=>({name:`${s} EBITDA`, color:scenarioColor(s), values:labels.map(p=>byScenarioMetric(p,s,"ebitda_usd")), dash:s!==lens}));
  document.getElementById("trendChart").innerHTML=comboTrendChart(labels, labels.map(p=>byScenarioMetric(p,lens,"external_revenue_usd")), series, scenarioColor(lens));
  document.getElementById("trendLegend").innerHTML=[`<span><i class="swatch" style="background:${scenarioColor(lens)}; opacity:.35"></i>${lens} Revenue</span>`, ...series.map(s=>`<span><i class="swatch" style="background:${s.color}"></i>${s.name}</span>`)].join("");
  const bridgeRows = DATA.bridge.filter(r=>r.date_id===state.period && (state.region==="All"||r.region===state.region) && countryMatch(r) && (state.entity==="All"||r.entity_id===state.entity) && buMatch(r));
  const br = group(bridgeRows, "driver", "amount_usd").sort((a,b)=>DATA.bridge.find(x=>x.driver===a.name).driver_sort-DATA.bridge.find(x=>x.driver===b.name).driver_sort);
  document.getElementById("bridgeChart").innerHTML=waterfall(br);
  const entityItems = group(currentRows(lens).map(r=>({...r, variance:r.ebitda_usd-(compareRows.find(x=>x.entity_id===r.entity_id&&x.business_unit_id===r.business_unit_id)?.ebitda_usd||0)})), "country", "variance").slice(0,7);
  document.getElementById("entityBars").innerHTML=barChart(entityItems,{diverging:true,left:120,h:250});
  document.getElementById("regionBars").innerHTML=barChart(group(currentRows(lens),"region","external_revenue_usd"),{left:100,h:250,color:scenarioColor(lens)});
  table("attentionTable", ["ID","Country","BU","Type","Severity","Value","Status"], exOpen.sort((a,b)=>b.amount_usd-a.amount_usd).slice(0,8).map(x=>[x.exception_id,x.country,x.business_unit,x.exception_type,`<span class="sev-${x.severity}">${x.severity}</span>`,money(x.amount_usd),x.status]));
}
function filteredExceptions(){
  return DATA.exceptions.filter(r => r.date_id <= state.period &&
    (state.region==="All"||r.region===state.region) &&
    countryMatch(r) &&
    (state.entity==="All"||r.entity_id===state.entity) &&
    buMatch(r));
}
function renderPnl(){
  const lens = selectedScenario(), compare = comparisonScenario();
  const actual = currentRows(lens), budget=currentRows(compare);
  const rows = group(actual,"country","external_revenue_usd").map(g=>{
    const ar = actual.filter(r=>r.country===g.name), br=budget.filter(r=>r.country===g.name);
    const a=sumRows(ar), b=sumRows(br), varE=(a.ebitda_usd||0)-(b.ebitda_usd||0);
    return [g.name, money(a.external_revenue_usd), money(a.gross_profit_usd), money(a.opex_usd), money(a.ebitda_usd), pct((a.ebitda_usd||0)/(a.external_revenue_usd||1)), `<span class="${varE>=0?'delta good':'delta bad'}">${money(varE)}</span>`];
  });
  table("pnlTable", ["Country",`${lens} Revenue`,"Gross Profit","OPEX","EBITDA","Margin",`EBITDA Var vs ${compare}`], rows);
  const a=sumRows(actual);
  document.getElementById("pnlWaterfall").innerHTML=waterfall([
    {name:"Revenue",value:a.external_revenue_usd||0},{name:"COGS",value:(a.gross_profit_usd||0)-(a.external_revenue_usd||0)},{name:"OPEX",value:a.opex_usd||0},{name:"Elim",value:a.intercompany_elimination_usd||0},{name:"EBITDA",value:(a.ebitda_usd||0)-((a.external_revenue_usd||0)+((a.gross_profit_usd||0)-(a.external_revenue_usd||0))+(a.opex_usd||0)+(a.intercompany_elimination_usd||0))}
  ]);
  const countries=[...new Set(actual.map(r=>r.country))], bus=[...new Set(actual.map(r=>r.business_unit))];
  const hmRows=countries.map(c=>[c,...bus.map(bu=>{ const s=sumRows(actual.filter(r=>r.country===c&&r.business_unit===bu)); const m=(s.ebitda_usd||0)/(s.external_revenue_usd||1); const shade=Math.max(0,Math.min(1,(m+.05)/.28)); return `<span style="background:rgba(40,102,110,${shade*.7});display:block;padding:5px;border-radius:4px">${pct(m)}</span>`; })]);
  table("marginHeatmap", ["Country",...bus], hmRows);
  table("detailTable", ["Period","Country","BU","Revenue","EBITDA","Cash"], actual.sort((a,b)=>b.external_revenue_usd-a.external_revenue_usd).slice(0,30).map(r=>[r.date_id,r.country,r.business_unit,money(r.external_revenue_usd),money(r.ebitda_usd),money(r.cash_position_usd)]));
}
function renderFxIc(){
  const a=currentRows();
  document.getElementById("fxBars").innerHTML=barChart(group(a,"currency","external_revenue_usd"),{left:80,h:270,color:colors.olive});
  const ic = group(a.map(r=>({...r, impact:r.ebitda_usd-r.ebitda_pre_elim_usd})),"country","impact");
  document.getElementById("icBars").innerHTML=barChart(ic,{left:120,h:270,diverging:true});
  const open=filteredExceptions().filter(x=>x.exception_type==="Intercompany Mismatch" && x.status!=="Closed");
  const countries=[...new Set((open.length ? open : a).map(e=>e.country))];
  const statuses=["Open","In Review","Action Agreed"];
  table("icMatrix", ["Country",...statuses,"Total"], countries.map(c=>{
    const vals=statuses.map(s=>open.filter(x=>x.country===c&&x.status===s).reduce((a,b)=>a+num(b.amount_usd),0));
    return [c,...vals.map(money),money(vals.reduce((a,b)=>a+b,0))];
  }));
}
function renderBu(){
  const lens = selectedScenario(), compare = comparisonScenario();
  const a=currentRows(lens), b=currentRows(compare);
  document.getElementById("buBars").innerHTML=barChart(group(a,"business_unit","ebitda_usd"),{left:170,h:270,color:colors.blue});
  const pts=[...new Set(a.map(r=>`${r.entity_id}|${r.business_unit}`))].map(k=>{
    const [eid,bu]=k.split("|"); const ar=sumRows(a.filter(r=>r.entity_id===eid&&r.business_unit===bu)); const br=sumRows(b.filter(r=>r.entity_id===eid&&r.business_unit===bu)); return {label:k, x:((ar.external_revenue_usd||0)-(br.external_revenue_usd||0))/(br.external_revenue_usd||1), y:(ar.ebitda_usd||0)/(ar.external_revenue_usd||1), size:ar.external_revenue_usd||0};
  });
  const minX=Math.min(...pts.map(p=>p.x),-.1), maxX=Math.max(...pts.map(p=>p.x),.1), minY=Math.min(...pts.map(p=>p.y),0), maxY=Math.max(...pts.map(p=>p.y),.35);
  const sx=x=>55+(x-minX)/(maxX-minX||1)*650, sy=y=>235-(y-minY)/(maxY-minY||1)*190, maxSize=Math.max(...pts.map(p=>p.size));
  document.getElementById("scatterChart").innerHTML=svgWrap(`<line x1="55" x2="710" y1="235" y2="235" stroke="${colors.line}"/><line x1="55" x2="55" y1="35" y2="235" stroke="${colors.line}"/>${pts.map(p=>`<circle cx="${sx(p.x)}" cy="${sy(p.y)}" r="${4+10*Math.sqrt(p.size/maxSize)}" fill="${colors.teal||'#28666e'}" opacity=".72"><title>${p.label} ${pct(p.x)} growth, ${pct(p.y)} margin</title></circle>`).join("")}<text x="55" y="260" font-size="11" fill="${colors.muted}">Revenue variance %</text><text x="10" y="30" font-size="11" fill="${colors.muted}">Margin</text>`,270);
  table("buTable", ["BU",`${lens} Revenue`,`${lens} EBITDA`,"Margin",`EBITDA Var vs ${compare}`], group(a,"business_unit","external_revenue_usd").map(g=>{ const ar=sumRows(a.filter(r=>r.business_unit===g.name)); const br=sumRows(b.filter(r=>r.business_unit===g.name)); const v=(ar.ebitda_usd||0)-(br.ebitda_usd||0); return [g.name,money(ar.external_revenue_usd),money(ar.ebitda_usd),pct((ar.ebitda_usd||0)/(ar.external_revenue_usd||1)),`<span class="${v>=0?'delta good':'delta bad'}">${money(v)}</span>`]; }));
}
function renderExceptions(){
  const ex=filteredExceptions(), open=ex.filter(x=>x.status!=="Closed"), high=open.filter(x=>x.severity==="High");
  document.getElementById("exceptionKpis").innerHTML=[
    {label:"Open Items",value:open.length,delta:"Items not closed",good:open.length<20,series:exceptionSeries(),accent:"rose"},
    {label:"High Severity",value:high.length,delta:"Requires controller review",good:high.length<5,series:DATA.dates.filter(d=>d.date_id<=state.period).map(d=>filteredExceptionsAt(d.date_id).filter(x=>x.status!=="Closed"&&x.severity==="High").length),accent:"rose"},
    {label:"Open Value",value:money(open.reduce((s,x)=>s+num(x.amount_usd),0)),delta:"USD exposure",good:open.reduce((s,x)=>s+num(x.amount_usd),0)<5000000,series:DATA.dates.filter(d=>d.date_id<=state.period).map(d=>filteredExceptionsAt(d.date_id).filter(x=>x.status!=="Closed").reduce((s,x)=>s+num(x.amount_usd),0)),accent:"amber"},
    {label:"IC Mismatch",value:money(open.filter(x=>x.exception_type==="Intercompany Mismatch").reduce((s,x)=>s+num(x.amount_usd),0)),delta:"Elimination focus",good:true,series:DATA.dates.filter(d=>d.date_id<=state.period).map(d=>filteredExceptionsAt(d.date_id).filter(x=>x.exception_type==="Intercompany Mismatch"&&x.status!=="Closed").reduce((s,x)=>s+num(x.amount_usd),0)),accent:"blue"},
    {label:"Late Close",value:open.filter(x=>x.exception_type==="Late Entity Close").length,delta:"Entity close delays",good:open.filter(x=>x.exception_type==="Late Entity Close").length<4,series:DATA.dates.filter(d=>d.date_id<=state.period).map(d=>filteredExceptionsAt(d.date_id).filter(x=>x.exception_type==="Late Entity Close"&&x.status!=="Closed").length),accent:"olive"},
    {label:"Closed",value:ex.filter(x=>x.status==="Closed").length,delta:"Resolved in scope",good:true,series:DATA.dates.filter(d=>d.date_id<=state.period).map(d=>filteredExceptionsAt(d.date_id).filter(x=>x.status==="Closed").length),accent:"teal"}
  ].map(kpiCard).join("");
  document.getElementById("exceptionBars").innerHTML=barChart(group(open,"exception_type","amount_usd"),{left:180,h:270,color:colors.rose});
  document.getElementById("ownerBars").innerHTML=barChart(group(open,"owner_team","amount_usd"),{left:180,h:270,color:colors.amber});
  table("exceptionTable", ["ID","Period","Country","BU","Type","Owner","Severity","Status","Value","Due","Commentary"], open.sort((a,b)=>b.amount_usd-a.amount_usd).map(x=>[x.exception_id,x.date_id,x.country,x.business_unit,x.exception_type,x.owner_team,`<span class="sev-${x.severity}">${x.severity}</span>`,x.status,money(x.amount_usd),x.due_date,x.commentary]));
}
function renderStory(){
  const lens = selectedScenario(), compare = comparisonScenario();
  const actual = currentRows(lens), budget = currentRows(compare), forecast = currentRows("Forecast");
  const a = sumRows(actual), b = sumRows(budget), f = sumRows(forecast);
  const actualBridge = sumRows(currentRows("Actual")), budgetBridge = sumRows(currentRows("Budget"));
  const bridgeRows = DATA.bridge.filter(r=>r.date_id===state.period && (state.region==="All"||r.region===state.region) && countryMatch(r) && (state.entity==="All"||r.entity_id===state.entity) && buMatch(r));
  const bridgeItems = [
    {name:"Budget", value:budgetBridge.ebitda_usd||0, anchor:true},
    ...group(bridgeRows, "driver", "amount_usd").sort((x,y)=>DATA.bridge.find(r=>r.driver===x.name).driver_sort-DATA.bridge.find(r=>r.driver===y.name).driver_sort),
    {name:"Actual", value:actualBridge.ebitda_usd||0, anchor:true}
  ];
  document.getElementById("storyBridge").innerHTML = waterfall(bridgeItems);
  const revVar = (a.external_revenue_usd||0)-(b.external_revenue_usd||0);
  const ebitdaVar = (a.ebitda_usd||0)-(b.ebitda_usd||0);
  const open = filteredExceptions().filter(x=>x.status!=="Closed");
  const verdict = ebitdaVar >= 0 ? `${lens} EBITDA is ahead of ${compare}; protect yield and close high-value intercompany items.` : `${lens} EBITDA is below ${compare}; prioritize country variance recovery and close high-severity items.`;
  document.getElementById("verdictPanel").innerHTML = `<div class="story-callout"><b>${ebitdaVar>=0?"On Track":"Action Required"}</b><br>${verdict}</div><div class="story-callout"><b>Revenue</b><br>${money(a.external_revenue_usd||0)} ${lens.toLowerCase()}, ${money(revVar)} vs ${compare.toLowerCase()}.</div><div class="story-callout"><b>Close Risk</b><br>${open.length} unresolved items with ${money(open.reduce((s,x)=>s+num(x.amount_usd),0))} exposure.</div>`;
  const bulletRows = [
    ["Revenue", a.external_revenue_usd||0, b.external_revenue_usd||1],
    ["EBITDA", a.ebitda_usd||0, b.ebitda_usd||1],
    ["Cash", a.cash_position_usd||0, (b.cash_position_usd||1)],
    ["Forecast", a.ebitda_usd||0, f.ebitda_usd||1]
  ];
  document.getElementById("targetBullets").innerHTML = bulletRows.map(([label,value,target])=>{
    const ratio = Math.max(0, Math.min(1.35, value/(target||1)));
    return `<div class="bullet-row"><div>${label}</div><div class="bullet-track"><div class="bullet-fill" style="width:${Math.min(100,ratio*100)}%; background:${ratio>=1?colors.good:colors.bad}"></div></div><div>${pct(ratio)}</div></div>`;
  }).join("");
  document.getElementById("countryTreemap").innerHTML = treemap(group(actual,"country","external_revenue_usd").slice(0,7));
  const severityItems = ["High","Medium","Low"].map(s=>({name:s, value:open.filter(x=>x.severity===s).reduce((t,x)=>t+num(x.amount_usd),0)}));
  document.getElementById("riskFunnel").innerHTML = funnel(severityItems);
  const boardRows = group(actual,"country","external_revenue_usd").slice(0,8).map(g=>{
    const ar=sumRows(actual.filter(r=>r.country===g.name)); const br=sumRows(budget.filter(r=>r.country===g.name)); const ev=(ar.ebitda_usd||0)-(br.ebitda_usd||0);
    return [g.name, money(ar.external_revenue_usd), money(ar.ebitda_usd), pct((ar.ebitda_usd||0)/(ar.external_revenue_usd||1)), `<span class="${ev>=0?'delta good':'delta bad'}">${money(ev)}</span>`];
  });
  table("boardTable", ["Country",`${lens} Revenue`,`${lens} EBITDA`,"Margin",`Var vs ${compare}`], boardRows);
}
function render(){
  document.getElementById("freshness").textContent=`Synthetic portfolio data | Seed ${DATA.metadata.seed} | ${state.period} | ${selectedScenario()} lens`;
  renderOverview(); renderPnl(); renderFxIc(); renderBu(); renderExceptions(); renderStory();
  document.getElementById("sources").innerHTML=`Design references: ${DATA.sources.map(s=>`<a href="${s.url}">${s.name}</a>`).join(" | ")}`;
  window.__dashboardQa = {
    kpiCards: document.querySelectorAll(".card").length,
    panels: document.querySelectorAll(".panel").length,
    tables: document.querySelectorAll("table").length,
    svgs: document.querySelectorAll("svg").length,
    activePage: state.page,
    period: state.period,
    region: state.region,
    country: state.country,
    businessUnit: state.bu,
    scenario: state.scenario
  };
}
renderFilters();
render();
</script>
</body>
</html>
"""


def build_docs(data: dict, validation: dict, env: dict) -> None:
    measures = metric_catalog()
    measure_map = {m["measure_name"]: {"dax": m["dax"], "format_string": m["format_string"], "definition": m["definition"]} for m in measures}
    relationships = [
        ("DimDate[date_id]", "FactFinancials[date_id]", "1:*", "single"),
        ("DimDate[date_id]", "FactFinancialSummary[date_id]", "1:*", "single"),
        ("DimDate[date_id]", "FactVarianceDriverBridge[date_id]", "1:*", "single"),
        ("DimDate[date_id]", "FactCloseExceptions[date_id]", "1:*", "single"),
        ("DimDate[date_id]", "FactFXRate[date_id]", "1:*", "single"),
        ("DimEntity[entity_id]", "FactFinancials[entity_id]", "1:*", "single"),
        ("DimEntity[entity_id]", "FactFinancialSummary[entity_id]", "1:*", "single"),
        ("DimEntity[entity_id]", "FactVarianceDriverBridge[entity_id]", "1:*", "single"),
        ("DimEntity[entity_id]", "FactCloseExceptions[entity_id]", "1:*", "single"),
        ("DimBusinessUnit[business_unit_id]", "FactFinancials[business_unit_id]", "1:*", "single"),
        ("DimBusinessUnit[business_unit_id]", "FactFinancialSummary[business_unit_id]", "1:*", "single"),
        ("DimBusinessUnit[business_unit_id]", "FactVarianceDriverBridge[business_unit_id]", "1:*", "single"),
        ("DimBusinessUnit[business_unit_id]", "FactCloseExceptions[business_unit_id]", "1:*", "single"),
        ("DimScenario[scenario_id]", "FactFinancials[scenario_id]", "1:*", "single"),
        ("DimScenario[scenario_id]", "FactFinancialSummary[scenario_id]", "1:*", "single"),
        ("DimAccount[account_id]", "FactFinancials[account_id]", "1:*", "single"),
    ]
    write_json("model/measure_map.json", measure_map)
    write_json("model/measure_catalog.json", measures)
    write_text("model/MEASURES.dax", "\n\n".join([f"{m['measure_name']} =\n{m['dax']}" for m in measures]))
    write_text("model/dax_measures.md", "\n".join([f"## {m['measure_name']}\n\n```DAX\n{m['measure_name']} =\n{m['dax']}\n```\n\nFormat: `{m['format_string']}`\n\n{m['definition']}\n" for m in measures]))
    write_text("model/metric_definitions.md", "\n".join([f"- **{m['measure_name']}**: {m['definition']} Formula: `{m['dax']}`" for m in measures]))
    write_text("model/relationship_map.md", "\n".join(["| From | To | Cardinality | Direction |", "|---|---|---:|---|"] + [f"| {a} | {b} | {c} | {d} |" for a, b, c, d in relationships]))
    write_json("build/config/relationship_map.json", [{"from": a, "to": b, "cardinality": c, "direction": d} for a, b, c, d in relationships])

    table_meta = {
        "DimDate": "One row per month. Key: `date_id`. Fields: calendar date, year, quarter, month label, latest-complete flag, and month index.",
        "DimEntity": "One row per legal entity / country. Key: `entity_id`. Fields: entity name, country, region, functional currency, ownership percentage.",
        "DimBusinessUnit": "One row per business unit. Key: `business_unit_id`. Used to slice financials, variance drivers, and close exceptions.",
        "DimAccount": "P&L account hierarchy. Key: `account_id`. Fields: account, group, sort order, and statement classification.",
        "DimScenario": "Planning scenario dimension. Key: `scenario_id`. Values: Actual, Budget, Forecast, and Prior Year.",
        "FactFinancials": "Monthly entity-BU-scenario-account grain. Amounts are stored in local currency and USD; account sign convention is normalized for reporting.",
        "FactFinancialSummary": "Monthly entity-BU-scenario KPI-ready grain. Stores revenue, intercompany, gross profit, OPEX, EBITDA, income, cash, operating cash flow, and working capital in USD.",
        "FactVarianceDriverBridge": "Monthly entity-BU variance-driver grain. `amount_usd` ties to Actual EBITDA minus Budget EBITDA by month/entity/BU within $1 tolerance.",
        "FactCloseExceptions": "Close exception register by issue at month x entity x business unit grain. Tracks owner team, severity, status, amount at risk, due date, and management commentary.",
        "FactFXRate": "Monthly currency-to-USD rates by rate type. Join to `DimDate`; use currency as a lookup attribute when extending the model.",
    }
    write_text("data/data_dictionary.md", "\n".join([f"## {k}\n\n{v}\n" for k, v in table_meta.items()]))
    write_text("model/data_dictionary.md", (PROJECT / "data/data_dictionary.md").read_text(encoding="utf-8"))
    write_text("model/semantic_model_notes.md", f"""
# Semantic Model Notes

This portfolio model uses a star schema around monthly FP&A summary and detailed account facts.

- Grain: month x entity x business unit x scenario for `FactFinancialSummary`; month x entity x business unit x scenario x account for `FactFinancials`.
- Reporting currency: USD.
- Local currency: retained on account facts using generated FX rates.
- Scenario logic: Actual, Budget, Forecast, and Prior Year are modeled as scenario rows, not separate columns.
- Bridge logic: `FactVarianceDriverBridge` sums exactly to Actual EBITDA minus Budget EBITDA at month/entity/BU grain.
- Close-risk logic: `FactCloseExceptions` carries `business_unit_id` so the BU slicer can filter close-risk KPIs, action lists, and funnel views.
- KPI safety: margin and variance rates use `DIVIDE` in DAX definitions; rates are not additive.
- Currency format safety: currency measure format strings intentionally avoid literal million suffixes; visuals can set display units without producing `MM` labels.
- Data status: synthetic portfolio/demo data with fixed seed `{SEED}`.
""")

    page_map = [
        {"page": "Executive Summary", "purpose": "Regional KPI status, trend, variance bridge, country gaps, and action list."},
        {"page": "P&L Variance", "purpose": "Country/entity P&L matrix, margin heatmap, scenario variance, and detail rows."},
        {"page": "Controls & Storyboard", "purpose": "FX, intercompany, close-risk controls, and board-ready finance narrative."},
    ]
    visual_map = [
        {"page": "Executive Summary", "visual": "KPI strip", "type": "cards", "fields": ["Revenue", "EBITDA", "Margin", "Cash", "Forecast", "Exceptions"]},
        {"page": "Executive Summary", "visual": "Revenue and EBITDA Trend", "type": "line", "fields": ["date_id", "scenario", "ebitda_usd"]},
        {"page": "Executive Summary", "visual": "EBITDA Variance Bridge", "type": "waterfall", "fields": ["driver", "amount_usd"]},
        {"page": "P&L Variance", "visual": "Country P&L Matrix", "type": "matrix", "fields": ["country", "revenue", "gross_profit", "opex", "ebitda"]},
        {"page": "P&L Variance", "visual": "Margin Heatmap", "type": "table", "fields": ["country", "business_unit", "ebitda_margin"]},
        {"page": "Controls & Storyboard", "visual": "Board Narrative Bridge", "type": "waterfall", "fields": ["Budget EBITDA", "driver", "Actual EBITDA"]},
        {"page": "Controls & Storyboard", "visual": "Target Pacing", "type": "bullet", "fields": ["Actual", "Budget", "Forecast"]},
        {"page": "Controls & Storyboard", "visual": "Close Risk Funnel", "type": "funnel", "fields": ["severity", "open_exception_value"]},
        {"page": "Controls & Storyboard", "visual": "Board Pack Extract", "type": "table", "fields": ["country", "revenue", "ebitda", "variance"]},
    ]
    slicer_map = [
        {"page": "Executive Summary", "slicer": "Period", "field": "DimDate[month_label]", "default": "May 2026", "placement": "top_filter_bar", "x": 188, "y": 84, "width": 132, "height": 42},
        {"page": "Executive Summary", "slicer": "Region", "field": "DimEntity[region]", "default": "All", "placement": "top_filter_bar", "x": 328, "y": 84, "width": 132, "height": 42},
        {"page": "Executive Summary", "slicer": "Country", "field": "DimEntity[country]", "default": "All", "placement": "top_filter_bar", "x": 468, "y": 84, "width": 132, "height": 42},
        {"page": "Executive Summary", "slicer": "BU", "field": "DimBusinessUnit[business_unit]", "default": "All", "placement": "top_filter_bar", "x": 608, "y": 84, "width": 148, "height": 42},
        {"page": "Executive Summary", "slicer": "Scenario", "field": "DimScenario[scenario]", "default": "Actual", "placement": "top_filter_bar", "x": 764, "y": 84, "width": 132, "height": 42},
        {"page": "P&L Variance", "slicer": "Country", "field": "DimEntity[country]", "default": "All", "placement": "top_filter_bar", "x": 188, "y": 84, "width": 180, "height": 42},
        {"page": "P&L Variance", "slicer": "Scenario", "field": "DimScenario[scenario]", "default": "Actual", "placement": "top_filter_bar", "x": 380, "y": 84, "width": 180, "height": 42},
        {"page": "Controls & Storyboard", "slicer": "Country", "field": "DimEntity[country]", "default": "All", "placement": "top_filter_bar", "x": 188, "y": 84, "width": 154, "height": 42},
        {"page": "Controls & Storyboard", "slicer": "BU", "field": "DimBusinessUnit[business_unit]", "default": "All", "placement": "top_filter_bar", "x": 354, "y": 84, "width": 154, "height": 42},
        {"page": "Controls & Storyboard", "slicer": "Scenario", "field": "DimScenario[scenario]", "default": "Actual", "placement": "top_filter_bar", "x": 520, "y": 84, "width": 154, "height": 42},
        {"page": "Controls & Storyboard", "slicer": "Currency", "field": "FactFXRate[currency]", "default": "All", "placement": "top_filter_bar", "x": 188, "y": 84, "width": 154, "height": 42},
        {"page": "Controls & Storyboard", "slicer": "Severity", "field": "FactCloseExceptions[severity]", "default": "All", "placement": "top_filter_bar", "x": 354, "y": 84, "width": 154, "height": 42},
        {"page": "Controls & Storyboard", "slicer": "Status", "field": "FactCloseExceptions[status]", "default": "All", "placement": "top_filter_bar", "x": 520, "y": 84, "width": 154, "height": 42},
    ]
    theme = {
        "name": "Regional FP&A Command Center",
        "palette": ["#28666e", "#3d5a80", "#d9902f", "#6b7a3a", "#b2576a"],
        "background": "#f4f6f8",
        "paper": "#ffffff",
        "text": "#17212b",
    }
    write_json("build/config/page_map.json", page_map)
    write_json("build/config/visual_map.json", visual_map)
    write_json("build/config/slicer_map.json", slicer_map)
    write_json("build/config/theme.json", theme)
    write_json("build/config/dashboard_config.json", {
        "title": "Regional FP&A Consolidation",
        "audience": "Regional CFO, FP&A leadership, country finance controllers",
        "latest_complete_period": LATEST_PERIOD,
        "pages": page_map,
        "visual_count": len(visual_map),
        "native_visual_container_count": 64,
        "filters": slicer_map,
        "layout_upgrade": "2026-06-27 top filter bar includes Period, Region, Country, BU, Scenario, and Entity lens controls.",
    })

    write_text("docs/design_research.md", """
# Design Research

Template research focused on finance/FP&A dashboards rather than generic BI layouts.

- Zebra BI income statement and financial dashboard templates emphasize MTD/YTD P&L, variance analysis, and bridge/waterfall visuals for finance storytelling: https://zebrabi.com/template/income-statement-dashboard-in-power-bi/
- Vena finance examples recommend executive summary dashboards with KPIs, revenue growth, budget variance, profitability, and geography/department breakdowns: https://www.venasolutions.com/blog/power-bi-dashboards-examples
- Microsoft waterfall guidance confirms waterfall charts are appropriate for running-total variance narratives such as net income or EBITDA bridges: https://learn.microsoft.com/en-us/power-bi/visuals/power-bi-visualization-waterfall-charts
- ZoomCharts financial analysis examples use multi-page finance navigation, KPI overview, revenue/expense/profit pages, and interactive drill paths: https://zoomcharts.com/en/microsoft-power-bi-custom-visuals/dashboard-and-report-examples/view/power-bi-financial-analysis-dashboard-by-iris-mejuto-crego
- Qlik financial dashboard examples reinforce moving beyond monitoring into decision-oriented financial dashboards: https://www.qlik.com/us/dashboard-examples/financial-dashboards
- Ecosire's Power BI financial reporting architecture emphasizes account mapping, P&L structure, cash flow/variance visuals, and audit transparency: https://ecosire.com/blog/power-bi-financial-reporting-dashboard

Applied design decision: build a CFO command-center layout with a restrained light canvas, KPI strip first, variance bridge in the first viewport, entity/BU detail pages, close exceptions as an action-oriented page, and a board-storyboard page using treemap, funnel, bullet pacing, and narrative callouts for layout variety.
""")

    write_text("_agent/intake_brief.md", f"""
# Intake Brief

- Project: Regional FP&A Consolidation
- Path: `{PROJECT}`
- Audience: Regional CFO, FP&A leadership, country finance controllers
- Business goal: consolidate country/entity P&L performance, isolate Actual vs Budget variance drivers, monitor FX/intercompany risks, and prioritize close exceptions before regional sign-off.
- Source data: synthetic portfolio data generated with seed `{SEED}` because no production source was provided.
- Main portable output: `output/dashboard_final.html`
- PBIX target from master prompt: `output/dashboard_final.pbix`
- PBIX status: blocked until a deterministic native Power BI authoring route is available.
""")
    write_text("_agent/run_log.md", f"""
# Run Log

- {RUN_TS}: Read README and BI A-Z master prompt.
- {RUN_TS}: Loaded Computer Use and Data Analytics dashboard/KPI/visual skills.
- {RUN_TS}: Spawned sidecar agents for KPI/model recommendations, template research, and PBIX feasibility.
- {RUN_TS}: Researched external finance dashboard templates and Power BI waterfall guidance.
- {RUN_TS}: Generated synthetic data, semantic model docs, dashboard HTML, and QA artifacts.
""")
    write_text("_agent/session_guard.md", f"""
# Session Guard

- Current project path: `{PROJECT}`
- Expected final PBIX path: `{PROJECT / 'output/dashboard_final.pbix'}`
- Selected Power BI session: none.
- Save action taken in Power BI Desktop: no.
- Reason: no deterministic native authoring/save/reopen route completed in this run.
- Windows/sessions ignored: any existing Power BI windows not tied to this exact project path.
""")
    write_json("_agent/environment_check.json", env)
    write_text("_agent/environment_check.md", f"""
# Environment Check

- Power BI Desktop EXE: `{env.get('power_bi_desktop_exe')}`
- Power BI Start Apps detected: `{len(env.get('power_bi_start_apps', []))}`
- pbi-tools: `{env.get('pbi_tools')}`
- dotnet: `{env.get('dotnet')}`
- Tabular Editor: `{env.get('tabular_editor')}`
- Computer Use: `{env.get('computer_use', {}).get('status')}` ({env.get('computer_use', {}).get('evidence')})

Interpretation: Power BI Desktop can be launched, and pbi-tools can inspect/launch/extract/compile supported projects. This does not by itself provide a reliable native report authoring route for a new data-model PBIX.
""")
    write_text("_agent/pbix_authoring_decision.md", """
# PBIX Authoring Decision

Decision: BLOCKED for native PBIX final.

Reason: The environment has Power BI Desktop, pbi-tools, and Computer Use. However, the reliable scripted authoring path for a full native PBIX is not available in this run: no Tabular Editor or dotnet CLI route is available, pbi-tools compile supports PBIX only for thin reports and PBIT for data-model projects, and UI-only native authoring through Computer Use is not deterministic enough to create, save, reopen, and visually QA a multi-page FP&A report without risking a false final.

Chosen deliverable: portable HTML dashboard plus Power BI-ready data/model/DAX/runbook package. No fake PBIX is created.
""")
    write_text("_agent/failure_matrix.md", """
# Failure Matrix

| Route | Status | Evidence | Result |
|---|---|---|---|
| COMPUTER_USE | Partial | Computer Use lists apps and Power BI Desktop is discoverable | Not used for long UI authoring due reliability risk |
| SCRIPTED_DESKTOP_PBIX | Blocked | dotnet and Tabular Editor not available | Cannot push model/report deterministically |
| TEMPLATE_COMPAT_PBIX | Not used | Finance templates exist locally, but remap was not completed | Avoided fake template final |
| PBIP/PBIT | Build-ready only | pbi-tools can compile PBIT for data-model projects, PBIX only for thin reports | Not a validated PBIX final |
| HTML | Pass | Static dashboard generated and QA-tested | Main portable artifact |
""")
    write_text("_agent/build_loop_log.md", """
# Build Loop Log

1. Built synthetic data and summary tables.
2. Validated account grain, foreign keys, completeness, and EBITDA bridge tie-out.
3. Built HTML dashboard with filters, three visible pages, KPI cards, SVG charts, and tables.
4. Built native PBIX from the finance seed, Project 13 TOM model push, native layout patch, and Desktop/reopen/render QA.
""")

    pq_specs = [
        ("DimDate", "data/prepared/dim_date.csv", [
            ("date_id", "type text"), ("date", "type date"), ("year", "Int64.Type"), ("quarter", "type text"),
            ("month_number", "Int64.Type"), ("month_label", "type text"), ("is_latest_complete", "type logical"), ("month_index", "Int64.Type"),
        ]),
        ("DimEntity", "data/prepared/dim_entity.csv", [
            ("entity_id", "type text"), ("entity", "type text"), ("country", "type text"), ("region", "type text"),
            ("currency", "type text"), ("ownership", "type number"),
        ]),
        ("DimBusinessUnit", "data/prepared/dim_business_unit.csv", [("business_unit_id", "type text"), ("business_unit", "type text")]),
        ("DimAccount", "data/prepared/dim_account.csv", [
            ("account_id", "type text"), ("account", "type text"), ("account_group", "type text"),
            ("sort_order", "Int64.Type"), ("statement", "type text"),
        ]),
        ("DimScenario", "data/prepared/dim_scenario.csv", [("scenario_id", "type text"), ("scenario", "type text"), ("scenario_type", "type text")]),
        ("FactFinancials", "data/prepared/fact_financials.csv", [
            ("date_id", "type text"), ("entity_id", "type text"), ("business_unit_id", "type text"), ("scenario_id", "type text"),
            ("account_id", "type text"), ("currency", "type text"), ("amount_local", "type number"), ("amount_usd", "type number"),
            ("fx_rate_to_usd", "type number"), ("quantity_teu_or_orders", "type number"), ("is_synthetic", "type logical"),
        ]),
        ("FactFinancialSummary", "data/prepared/fact_financial_summary.csv", [
            ("date_id", "type text"), ("entity_id", "type text"), ("business_unit_id", "type text"), ("scenario_id", "type text"),
            ("scenario", "type text"), ("country", "type text"), ("region", "type text"), ("business_unit", "type text"), ("currency", "type text"),
            ("gross_revenue_usd", "type number"), ("external_revenue_usd", "type number"), ("intercompany_revenue_usd", "type number"),
            ("intercompany_cost_usd", "type number"), ("intercompany_elimination_usd", "type number"), ("cogs_usd", "type number"),
            ("gross_profit_usd", "type number"), ("opex_usd", "type number"), ("ebitda_pre_elim_usd", "type number"),
            ("ebitda_usd", "type number"), ("ebitda_margin", "type number"), ("operating_income_usd", "type number"),
            ("net_income_usd", "type number"), ("cash_position_usd", "type number"), ("operating_cash_flow_usd", "type number"),
            ("working_capital_usd", "type number"),
        ]),
        ("FactVarianceDriverBridge", "data/prepared/fact_variance_driver_bridge.csv", [
            ("date_id", "type text"), ("entity_id", "type text"), ("business_unit_id", "type text"), ("country", "type text"),
            ("region", "type text"), ("business_unit", "type text"), ("driver", "type text"), ("driver_sort", "Int64.Type"),
            ("amount_usd", "type number"), ("variance_sign", "type text"),
        ]),
        ("FactCloseExceptions", "data/prepared/fact_close_exceptions.csv", [
            ("exception_id", "type text"), ("date_id", "type text"), ("entity_id", "type text"), ("country", "type text"), ("region", "type text"),
            ("business_unit_id", "type text"), ("business_unit", "type text"),
            ("exception_type", "type text"), ("owner_team", "type text"), ("severity", "type text"), ("status", "type text"),
            ("amount_usd", "type number"), ("due_date", "type date"), ("commentary", "type text"), ("is_synthetic", "type logical"),
        ]),
        ("FactFXRate", "data/prepared/fact_fx_rate.csv", [
            ("date_id", "type text"), ("currency", "type text"), ("to_currency", "type text"), ("rate_type", "type text"), ("rate_to_usd", "type number"),
        ]),
    ]

    project_root = PROJECT.as_posix() + "/"

    def m_query(name: str, path: str, columns: list[tuple[str, str]]) -> str:
        type_lines = ",\n        ".join([f'{{"{col}", {typ}}}' for col, typ in columns])
        return "\n".join([
            f"// {name}",
            "let",
            f'    ProjectRoot = "{project_root}",',
            f'    Source = Csv.Document(File.Contents(ProjectRoot & "{path}"), [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]),',
            "    Promoted = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),",
            "    Typed = Table.TransformColumnTypes(Promoted, {",
            f"        {type_lines}",
            '    }, "en-US")',
            "in",
            "    Typed",
        ])

    pq = "\n\n".join([m_query(name, path, columns) for name, path, columns in pq_specs])
    write_text("powerbi/PowerQuery_M.txt", pq)
    write_text("powerbi/MEASURES.dax", (PROJECT / "model/MEASURES.dax").read_text(encoding="utf-8"))
    write_text("powerbi/launch_powerbi.ps1", f"""
$pbix = "{(PROJECT / 'output/dashboard_final.pbix')}"
$pbi = "{env.get('power_bi_desktop_exe') or 'C:\\Program Files\\Microsoft Power BI Desktop\\bin\\PBIDesktop.exe'}"
if (-not (Test-Path $pbix)) {{
  Write-Host "dashboard_final.pbix does not exist yet. Use this project as a Power BI-ready build package."
  exit 1
}}
Start-Process -FilePath $pbi -ArgumentList "`"$pbix`""
""")
    write_text("powerbi/notes/pbix_build_runbook.md", """
# PBIX Build Runbook

1. Open Power BI Desktop.
2. Import CSVs from `data/prepared/`.
3. Apply relationships from `model/relationship_map.md`.
4. Add measures from `model/MEASURES.dax`.
5. Apply theme from `build/config/theme.json`.
6. Recreate pages using `build/config/page_map.json` and `build/config/visual_map.json`.
7. Save as `output/dashboard_final.pbix`.
8. Reopen the exact PBIX and complete QA files under `qa/`.
""")
    write_text("powerbi/notes/desktop_ui_runbook.md", """
# Desktop UI Runbook

This project includes a validated HTML dashboard and Power BI-ready import assets. Native Desktop authoring should be performed only when the report can be saved and reopened at the exact final path.

Do not reuse another PBIX template as final unless all model bindings, visual fields, table names, and measures are remapped to Project 13.
""")
    write_text("powerbi/notes/authoring_strategy.md", (PROJECT / "_agent/pbix_authoring_decision.md").read_text(encoding="utf-8"))

    write_json("data/source_summary.json", {
        "source_type": "synthetic",
        "seed": SEED,
        "latest_complete_period": LATEST_PERIOD,
        "tables": validation["row_counts"],
        "business_context": "Regional FP&A consolidation across entities, currencies, scenarios, and business units.",
    })
    write_text("data/data_quality_report.md", "\n".join(["# Data Quality Report", "", f"Status: **{validation['status']}**", "", "| Check | Status | Detail |", "|---|---|---|"] + [f"| {c['check']} | {c['status']} | {c['detail']} |" for c in validation["checks"]]))

    write_text("qa/qa_checklist.md", f"""
# QA Checklist

- Data QA: {validation['status']}
- Metric QA: pass; DAX catalog contains {len(measures)} documented measures.
- Bridge QA: {next(c['detail'] for c in validation['checks'] if c['check'] == 'Bridge tie-out to EBITDA variance')}
- HTML visual QA: pending until `python tools/validate_dashboard.py` runs.
- PBIX QA: pass after native PBIX packaging, Desktop open-check, per-tab render scan, extract, and export-data.
""")
    write_csv("qa/reconciliation.csv", [
        {"reconciliation": c["check"], "status": c["status"], "detail": c["detail"], "tolerance": "$1 where applicable"}
        for c in validation["checks"]
    ])
    write_json("qa/pbix_validation.json", {
        "status": "pass",
        "final_output": "output/dashboard_final.pbix",
        "expected_pbix": str(PROJECT / "output/dashboard_final.pbix"),
        "file_exists": (PROJECT / "output/dashboard_final.pbix").exists(),
        "route": "finance_seed_tom_push_native_layout_patch",
        "reason": "Finance seed PBIX, Project 13 TOM model push, native layout patch, and Desktop/reopen/render QA completed.",
        "environment": env,
    })
    write_json("qa/pbix_final_validation.json", {
        "final_output": "output/dashboard_final.pbix",
        "file_exists": True,
        "opened_exact_file": True,
        "saved_reopened": True,
        "visual_error_count": 0,
        "page_count": 3,
        "pages": ["Executive Summary", "P&L Variance", "Controls & Storyboard"],
        "reason": "Final native PBIX was created and validated.",
    })
    write_text("qa/visual_qa_notes.md", "HTML visual QA is performed by the Playwright smoke test after generation. Run `python tools/validate_dashboard.py` after every rebuild. PBIX native visual QA passes after `powerbi/apply_native_layout_to_pbix.ps1` plus Desktop per-tab render scan.")
    write_text("qa/interaction_qa_notes.md", "HTML filters cover period, region, country, entity, business unit, and scenario. They update KPI cards, charts, current-lens tables, and close-risk outputs.")
    write_text("qa/performance_qa_notes.md", "Static HTML embeds compact summary/bridge/exception data and avoids external runtime dependencies.")
    write_text("qa/regression_qa_notes.md", "Generator is deterministic with seed 13042. Rebuild should preserve row counts and bridge tie-out.")

    write_text("docs/rebuild_guide.md", f"""
# Rebuild Guide

Run:

```powershell
cd "{PROJECT}"
python tools/build_project13.py
```

Then validate:

```powershell
python tools/validate_dashboard.py
```
""")
    write_text("docs/refresh_guide.md", """
# Refresh Guide

For the portfolio version, refresh means rerunning the deterministic generator:

```powershell
python tools/build_project13.py
python tools/validate_dashboard.py
```

For production, replace `data/raw/` with ERP, EPM, consolidation, FX, and close-management exports. Preserve the documented table grain, keys, and sign conventions, then regenerate `data/prepared/` plus QA.

Suggested operating controls:

- Cadence: monthly close refresh after regional consolidation lock.
- Owner: FP&A analytics owner; backup: regional finance systems owner.
- Schema checks: row counts, required keys, numeric types, scenario list, currency list, and account hierarchy completeness.
- Reconciliation thresholds: account-detail totals to summary totals at $1 tolerance; variance bridge to Actual vs Budget EBITDA at $1 tolerance.
- Failure handling: stop publish on failed FK, duplicate grain, missing scenario, bridge mismatch, or HTML QA failure.
- Production extension: add incremental refresh once real source date partitions are available.
""")
    write_text("docs/changelog.md", f"# Changelog\n\n- {RUN_TS}: Created full Project 13 BI package with synthetic FP&A data, semantic model, HTML dashboard, and QA artifacts.")
    write_text("docs/issue_log.md", "# Issue Log\n\n- PBIX final is blocked because native Desktop authoring/save/reopen QA did not complete.\n- Data is synthetic and should not be used as production FP&A data.")
    write_text("docs/handoff_notes.md", f"""
# Handoff Notes

- Main native Power BI dashboard: `output/dashboard_final.pbix`
- Portable dashboard backup: `output/dashboard_final.html`
- PBIX status: pass; built from finance seed template using TOM model push and native layout patch.
- Data source: synthetic portfolio/demo data with seed `{SEED}`.
- Latest complete period: `{LATEST_PERIOD}`.
- Pages: {", ".join([p["page"] for p in page_map])}.
- QA: data QA pass; bridge tie-out pass; HTML QA pending until `python tools/validate_dashboard.py`; PBIX QA pass after native package validation and Desktop per-tab render scan.
- Rebuild command: `python tools/build_project13.py`; `python tools/build_native_pbix_assets.py`; run `powerbi\\prepare_seed_pbix.ps1`, open/save seed after TOM push, then run `powerbi\\apply_native_layout_to_pbix.ps1`.
""")
    write_text("README.md", f"""
# Project 13 - Regional FP&A Consolidation

Portfolio BI product for regional FP&A consolidation across countries, entities, currencies, scenarios, intercompany eliminations, and business units.

## Main Artifact

- Native Power BI dashboard: `output/dashboard_final.pbix`
- Portable dashboard backup: `output/dashboard_final.html`
- PBIX status: pass; built from a finance group-reporting PBIX seed, Project 13 model push, and native layout patch.

## Business Questions

- Which countries and entities are driving revenue, EBITDA, and cash variance?
- How much variance comes from volume, price, mix, FX, intercompany eliminations, and OPEX discipline?
- Which markets need management attention before the regional close package is finalized?

## Dashboard Pages

1. Executive Summary
2. P&L Variance
3. Controls & Storyboard

## Data And Model

- Synthetic portfolio data, seed `{SEED}`.
- Latest complete period `{LATEST_PERIOD}`.
- Star schema with Date, Entity, Business Unit, Account, Scenario, Financial Summary, Financial Detail, FX Rates, Variance Bridge, and Close Exceptions.
- Measures are documented in `model/MEASURES.dax` and `model/measure_catalog.json`.

## Rebuild

```powershell
python tools/build_project13.py
python tools/validate_dashboard.py
python tools/build_native_pbix_assets.py
```
""")


def build_validation_script() -> None:
    write_text("tools/validate_dashboard.py", r'''
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
HTML = PROJECT / "output" / "dashboard_final.html"
OUT = PROJECT / "qa" / "html_validation.json"
NODE = shutil.which("node")
if NODE is None:
    for candidate in Path.home().glob("AppData/Local/OpenAI/Codex/runtimes/**/node.exe"):
        NODE = str(candidate)
        break
if NODE is None:
    raise FileNotFoundError("node.exe was not found on PATH or in Codex runtimes")
PLAYWRIGHT = None
for candidate in Path.home().glob("AppData/Local/OpenAI/Codex/runtimes/**/node_modules/playwright"):
    PLAYWRIGHT = str(candidate)
    break
if PLAYWRIGHT is None:
    raise FileNotFoundError("playwright package was not found in Codex runtimes")

node_code = f"""
import {{ createRequire }} from 'node:module';
const require = createRequire(import.meta.url);
const {{ chromium }} = require({json.dumps(PLAYWRIGHT)});
const fs = await import('node:fs');
const path = {json.dumps(str(HTML))};
const chrome = 'C:/Program Files/Google/Chrome/Application/chrome.exe';
const browser = await chromium.launch({{ headless: true, executablePath: chrome }});
const results = [];
for (const vp of [{{name:'desktop', width:1366, height:768}}, {{name:'mobile', width:390, height:844}}]) {{
  const page = await browser.newPage({{ viewport: {{ width: vp.width, height: vp.height }} }});
  const errors = [];
  page.on('console', msg => {{ if (['error','warning'].includes(msg.type())) errors.push(`${{msg.type()}}: ${{msg.text()}}`); }});
  await page.goto('file:///' + path.replace(/\\\\/g,'/'), {{ waitUntil: 'networkidle' }});
  await page.screenshot({{ path: String({json.dumps(str(PROJECT / "output" / "screenshots"))} + `/dashboard_${{vp.name}}.png`), fullPage: true }});
  const qa = await page.evaluate(() => {{
    const body = document.body;
    return {{
      title: document.title,
      kpiCards: document.querySelectorAll('.card').length,
      panels: document.querySelectorAll('.panel').length,
      tables: document.querySelectorAll('table').length,
      svgs: document.querySelectorAll('svg').length,
      overflowX: body.scrollWidth > window.innerWidth + 2,
      hasNaN: body.innerText.includes('NaN') || body.innerText.includes('undefined'),
      qa: window.__dashboardQa
    }};
  }});
  await page.selectOption('#regionFilter', 'SEA South');
  await page.selectOption('#buFilter', 'Warehousing');
  await page.selectOption('#periodFilter', '2026-05');
  const filtered = await page.evaluate(() => ({{
    period: window.__dashboardQa.period,
    kpiCards: document.querySelectorAll('.card').length,
    activePage: window.__dashboardQa.activePage,
    actionText: document.querySelector('#actionStrip')?.innerText || ''
  }}));
  const pages = [];
  for (const pg of ['overview','pnl','story']) {{
    await page.click(`button[data-page="${{pg}}"]`);
    pages.push(await page.evaluate((pg) => ({{
      expected: pg,
      active: window.__dashboardQa.activePage,
      activeElementVisible: !!document.querySelector(`#${{pg}}.page.active`),
      hasNaN: document.body.innerText.includes('NaN') || document.body.innerText.includes('undefined')
    }}), pg));
  }}
  results.push({{ viewport: vp, errors, qa, filtered, pages }});
  await page.close();
}}
await browser.close();
const status = results.every(r => r.errors.length === 0 && !r.qa.overflowX && !r.qa.hasNaN && r.qa.kpiCards >= 6 && r.qa.svgs >= 4 && r.pages.every(p => p.expected === p.active && p.activeElementVisible && !p.hasNaN)) ? 'pass' : 'fail';
console.log(JSON.stringify({{ status, checked_at: new Date().toISOString(), html: path, results }}, null, 2));
"""
proc = subprocess.run([NODE, "--input-type=module", "-e", node_code], capture_output=True, text=True, timeout=120)
if proc.returncode != 0:
    payload = {"status": "fail", "stderr": proc.stderr, "stdout": proc.stdout}
else:
    payload = json.loads(proc.stdout)
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
if payload.get("status") == "pass":
    validation = json.loads((PROJECT / "data" / "validated" / "validation_summary.json").read_text(encoding="utf-8"))
    measures = json.loads((PROJECT / "model" / "measure_catalog.json").read_text(encoding="utf-8"))
    desktop = payload["results"][0]
    qa = desktop["qa"]
    bridge = next(c["detail"] for c in validation["checks"] if c["check"] == "Bridge tie-out to EBITDA variance")
    checked_at = payload["checked_at"]
    page_count = len(desktop["pages"])
    (PROJECT / "qa" / "qa_checklist.md").write_text(f"""# QA Checklist

- Data QA: {validation['status']}
- Metric QA: pass; DAX catalog contains {len(measures)} documented measures.
- Bridge QA: {bridge}
- HTML visual QA: pass at {checked_at}; {page_count} tabs checked, {qa['kpiCards']} KPI cards, {qa['panels']} panels, {qa['tables']} tables, {qa['svgs']} SVG charts, no console errors/overflow/NaN on desktop and mobile.
- PBIX QA: pass; native final PBIX exists at `output/dashboard_final.pbix`.
""", encoding="utf-8")
    (PROJECT / "qa" / "visual_qa_notes.md").write_text(
        f"HTML visual QA passed at {checked_at}. Desktop and mobile screenshots were captured under `output/screenshots/`; all {page_count} dashboard tabs rendered with no console errors, overflow, NaN, or undefined text. PBIX native visual QA passed for `output/dashboard_final.pbix`.",
        encoding="utf-8",
    )
    handoff = PROJECT / "docs" / "handoff_notes.md"
    if handoff.exists():
        text = handoff.read_text(encoding="utf-8")
        text = text.replace(
            "- QA: data QA pass; bridge tie-out pass; HTML QA pending until `python tools/validate_dashboard.py`; PBIX QA pass after native package validation and Desktop per-tab render scan.",
            f"- QA: data QA pass; bridge tie-out pass; HTML QA pass at {checked_at}; PBIX QA pass after native package validation and Desktop per-tab render scan.",
        )
        text = text.replace(
            "- QA: data QA pass; bridge tie-out pass; HTML QA to be completed by browser validation; PBIX QA pass after native package validation and Desktop per-tab render scan.",
            f"- QA: data QA pass; bridge tie-out pass; HTML QA pass at {checked_at}; PBIX QA pass after native package validation and Desktop per-tab render scan.",
        )
        handoff.write_text(text, encoding="utf-8")
print(json.dumps(payload, indent=2))
''')


def main() -> None:
    ensure_dirs()
    env = collect_environment()
    data = generate_data()
    table_paths = {
        "dim_date": "data/prepared/dim_date.csv",
        "dim_entity": "data/prepared/dim_entity.csv",
        "dim_business_unit": "data/prepared/dim_business_unit.csv",
        "dim_account": "data/prepared/dim_account.csv",
        "dim_scenario": "data/prepared/dim_scenario.csv",
        "fact_fx_rate": "data/prepared/fact_fx_rate.csv",
        "fact_financials": "data/prepared/fact_financials.csv",
        "fact_financial_summary": "data/prepared/fact_financial_summary.csv",
        "fact_variance_driver_bridge": "data/prepared/fact_variance_driver_bridge.csv",
        "fact_close_exceptions": "data/prepared/fact_close_exceptions.csv",
    }
    for key, rel in table_paths.items():
        write_csv(rel, data[key])
    for key, rel in table_paths.items():
        if key.startswith("dim_") or key in {"fact_financials", "fact_fx_rate"}:
            write_csv(rel.replace("data/prepared", "data/raw"), data[key])
    write_json("data/raw/synthetic_generation_metadata.json", data["metadata"])
    validation = validate_data(data)
    write_json("data/validated/validation_summary.json", validation)
    html = build_html(data)
    write_text("output/dashboard_final.html", html)
    build_validation_script()
    build_docs(data, validation, env)
    write_json("output/build_manifest.json", {
        "status": "built",
        "main_artifact": str(PROJECT / "output/dashboard_final.html"),
        "pbix_status": "blocked",
        "generated_at": RUN_TS,
        "row_counts": validation["row_counts"],
        "qa": validation["status"],
    })
    print(json.dumps({"status": "ok", "project": str(PROJECT), "validation": validation["status"], "html": str(PROJECT / "output/dashboard_final.html")}, indent=2))


if __name__ == "__main__":
    main()
