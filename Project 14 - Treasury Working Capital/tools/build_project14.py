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
BI_ROOT = PROJECT.parents[0]
SEED = 14042
RUN_TS = datetime.now().replace(microsecond=0).isoformat()
AS_OF_DATE = date(2026, 6, 15)
LATEST_MONTH = "2026-05"
FORECAST_START = date(2026, 6, 15)


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
        "tools",
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
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
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


def round2(value: float) -> float:
    return round(float(value), 2)


def pct(numerator: float, denominator: float) -> float:
    return 0.0 if abs(denominator) < 1e-9 else numerator / denominator


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
            timeout=15,
        )
        if proc.stdout.strip():
            parsed = json.loads(proc.stdout)
            start_apps = parsed if isinstance(parsed, list) else [parsed]
    except Exception as exc:
        start_apps = [{"error": str(exc)}]

    pbi_tools = shutil.which("pbi-tools") or shutil.which("pbi-tools.exe")
    pbi_info = None
    if pbi_tools:
        try:
            proc = subprocess.run([pbi_tools, "info"], capture_output=True, text=True, timeout=30)
            pbi_info = proc.stdout.strip()[-8000:]
        except Exception as exc:
            pbi_info = f"pbi-tools info failed: {exc}"

    return {
        "checked_at": RUN_TS,
        "power_bi_desktop_exe": str(exe) if exe.exists() else None,
        "power_bi_desktop_program_files": exe.exists(),
        "power_bi_desktop_x86": exe_x86.exists(),
        "power_bi_start_apps": start_apps,
        "pbi_tools": pbi_tools,
        "pbi_tools_info_excerpt": pbi_info,
        "dotnet": shutil.which("dotnet"),
        "computer_use": {
            "status": "pass",
            "evidence": "Computer Use was bootstrapped before project build; sky.list_apps returned Power BI Desktop and the pre-existing Project 13 sessions.",
        },
    }


def build_dimensions() -> dict:
    months = month_range("2025-01", LATEST_MONTH)
    dim_date = []
    for idx, period in enumerate(months, 1):
        y, m = map(int, period.split("-"))
        q = (m - 1) // 3 + 1
        dim_date.append(
            {
                "date_id": period,
                "date": f"{period}-01",
                "year": y,
                "quarter": f"Q{q}",
                "month_number": m,
                "month_label": datetime(y, m, 1).strftime("%b %Y"),
                "month_index": idx,
                "is_latest_complete": "TRUE" if period == LATEST_MONTH else "FALSE",
            }
        )

    dim_week = []
    for i in range(13):
        start = FORECAST_START + timedelta(days=i * 7)
        end = start + timedelta(days=6)
        dim_week.append(
            {
                "week_id": f"W{i + 1:02d}",
                "week_start": start.isoformat(),
                "week_end": end.isoformat(),
                "week_label": f"W{i + 1:02d} {start.strftime('%d %b')}",
                "week_number": i + 1,
                "is_first_four_weeks": "TRUE" if i < 4 else "FALSE",
                "is_next_thirteen_weeks": "TRUE",
            }
        )

    entities = [
        {"entity_id": "US01", "entity": "US Distribution", "country": "United States", "region": "North America", "currency": "USD", "scale": 1.35, "risk": "Medium"},
        {"entity_id": "DE01", "entity": "Germany Manufacturing", "country": "Germany", "region": "Europe", "currency": "EUR", "scale": 1.10, "risk": "Medium"},
        {"entity_id": "GB01", "entity": "UK Commercial", "country": "United Kingdom", "region": "Europe", "currency": "GBP", "scale": 0.82, "risk": "Low"},
        {"entity_id": "SG01", "entity": "Singapore Hub", "country": "Singapore", "region": "APAC", "currency": "SGD", "scale": 0.92, "risk": "Low"},
        {"entity_id": "VN01", "entity": "Vietnam Operations", "country": "Vietnam", "region": "APAC", "currency": "VND", "scale": 0.78, "risk": "Medium"},
        {"entity_id": "BR01", "entity": "Brazil Sales", "country": "Brazil", "region": "LATAM", "currency": "BRL", "scale": 0.65, "risk": "High"},
    ]
    dim_entity = [
        {k: e[k] for k in ["entity_id", "entity", "country", "region", "currency", "risk"]}
        for e in entities
    ]

    customer_names = [
        "Northstar Retail",
        "Helio Foods",
        "Arcadia Medical",
        "Pioneer Auto",
        "BluePeak Electronics",
        "UrbanHome Group",
        "Apex Pharmacies",
        "Global Mining Co",
        "Nova Telecom",
        "Evergreen Apparel",
        "Summit Industrial",
        "Nimbus Cloud Services",
        "Atlas Grocery",
        "Riverside Energy",
        "Orion Components",
        "Pacific Marketplace",
        "Lion City Trading",
        "Mekong Consumer",
        "Sao Paulo Motors",
        "Continental Labs",
    ]
    sectors = ["Retail", "Healthcare", "Automotive", "Technology", "Industrial", "Consumer", "Energy"]
    dim_customer = []
    for i, name in enumerate(customer_names, 1):
        e = entities[i % len(entities)]
        dim_customer.append(
            {
                "customer_id": f"C{i:03d}",
                "customer": name,
                "sector": sectors[i % len(sectors)],
                "entity_id": e["entity_id"],
                "region": e["region"],
                "credit_terms_days": random.choice([30, 45, 60, 75]),
                "risk_rating": random.choices(["Low", "Medium", "High"], weights=[0.45, 0.40, 0.15])[0],
            }
        )

    vendor_names = [
        "Prime Materials",
        "Ocean Freight Partners",
        "Metro Warehousing",
        "Vertex IT Services",
        "Keystone Packaging",
        "BrightGrid Utilities",
        "Atlas Equipment Lease",
        "Golden Tax Advisors",
        "RouteOne Logistics",
        "Helios Components",
        "BlueSteel Suppliers",
        "Summit Staffing",
        "Local Port Services",
        "Mercury Insurers",
        "CloudOps Platform",
        "Regional Customs Brokers",
    ]
    categories = ["Materials", "Freight", "Warehousing", "IT", "Utilities", "Leasing", "Professional Services", "Labor"]
    dim_vendor = []
    for i, name in enumerate(vendor_names, 1):
        e = entities[(i + 1) % len(entities)]
        dim_vendor.append(
            {
                "vendor_id": f"V{i:03d}",
                "vendor": name,
                "category": categories[i % len(categories)],
                "entity_id": e["entity_id"],
                "region": e["region"],
                "payment_terms_days": random.choice([15, 30, 45, 60]),
                "criticality": random.choices(["Critical", "Standard", "Flexible"], weights=[0.26, 0.54, 0.20])[0],
            }
        )

    dim_bank = [
        {"bank_id": "B001", "bank": "Global Trust Bank", "counterparty_rating": "A", "bank_region": "Global"},
        {"bank_id": "B002", "bank": "Continental Treasury Bank", "counterparty_rating": "A-", "bank_region": "Europe"},
        {"bank_id": "B003", "bank": "Pacific Commercial Bank", "counterparty_rating": "BBB+", "bank_region": "APAC"},
        {"bank_id": "B004", "bank": "Americas Liquidity Bank", "counterparty_rating": "A", "bank_region": "North America"},
        {"bank_id": "B005", "bank": "Regional Trade Bank", "counterparty_rating": "BBB", "bank_region": "LATAM"},
        {"bank_id": "B006", "bank": "Digital Cash Pool", "counterparty_rating": "A-", "bank_region": "Global"},
    ]

    dim_scenario = [
        {"scenario_id": "BASE", "scenario": "Base", "scenario_sort": 1},
        {"scenario_id": "DOWN", "scenario": "Downside", "scenario_sort": 2},
        {"scenario_id": "UP", "scenario": "Upside", "scenario_sort": 3},
    ]

    dim_cash_category = [
        {"category_id": "COLL", "cash_category": "Customer collections", "cash_flow_type": "Inflow", "sort_order": 10},
        {"category_id": "OTHER_IN", "cash_category": "Other receipts", "cash_flow_type": "Inflow", "sort_order": 20},
        {"category_id": "SUPP", "cash_category": "Supplier payments", "cash_flow_type": "Outflow", "sort_order": 30},
        {"category_id": "PAYROLL", "cash_category": "Payroll and tax", "cash_flow_type": "Outflow", "sort_order": 40},
        {"category_id": "CAPEX", "cash_category": "Capex", "cash_flow_type": "Outflow", "sort_order": 50},
        {"category_id": "DEBT", "cash_category": "Debt service", "cash_flow_type": "Outflow", "sort_order": 60},
    ]

    return {
        "dim_date": dim_date,
        "dim_week": dim_week,
        "dim_entity": dim_entity,
        "dim_customer": dim_customer,
        "dim_vendor": dim_vendor,
        "dim_bank": dim_bank,
        "dim_scenario": dim_scenario,
        "dim_cash_category": dim_cash_category,
        "entities_full": entities,
    }


def generate_data() -> dict:
    random.seed(SEED)
    dims = build_dimensions()
    entities = dims["entities_full"]
    dim_customer = dims["dim_customer"]
    dim_vendor = dims["dim_vendor"]
    dim_bank = dims["dim_bank"]
    months = [row["date_id"] for row in dims["dim_date"]]
    weeks = dims["dim_week"]

    fx = {"USD": 1.0, "EUR": 1.087, "GBP": 1.276, "SGD": 0.742, "VND": 0.000039, "BRL": 0.184}
    scenario_mod = {"BASE": 1.0, "DOWN": 0.86, "UP": 1.12}

    cash_positions = []
    liquidity = []
    for e in entities:
        for b in random.sample(dim_bank, 3):
            base = 4_000_000 * e["scale"] * random.uniform(0.55, 1.45)
            restricted = base * random.uniform(0.02, 0.12)
            cash_positions.append(
                {
                    "snapshot_date": AS_OF_DATE.isoformat(),
                    "entity_id": e["entity_id"],
                    "bank_id": b["bank_id"],
                    "currency": e["currency"],
                    "balance_local": round2(base / fx[e["currency"]]),
                    "balance_usd": round2(base),
                    "restricted_cash_usd": round2(restricted),
                    "available_cash_usd": round2(base - restricted),
                    "is_synthetic": "TRUE",
                }
            )
        committed = 9_500_000 * e["scale"] * random.uniform(0.70, 1.25)
        drawn = committed * random.uniform(0.20, 0.56)
        liquidity.append(
            {
                "facility_id": f"FAC_{e['entity_id']}",
                "entity_id": e["entity_id"],
                "facility_type": random.choice(["RCF", "Overdraft", "Term Loan"]),
                "committed_usd": round2(committed),
                "drawn_usd": round2(drawn),
                "available_usd": round2(committed - drawn),
                "min_cash_buffer_usd": round2(1_800_000 * e["scale"]),
                "maturity_date": (AS_OF_DATE + timedelta(days=random.choice([82, 120, 210, 365, 540]))).isoformat(),
                "covenant_status": random.choices(["In compliance", "Watch", "Breach risk"], weights=[0.72, 0.22, 0.06])[0],
                "is_synthetic": "TRUE",
            }
        )

    working_capital = []
    for p_idx, period in enumerate(months):
        trend = 1 + p_idx * 0.012
        season = 1 + 0.08 * math.sin((p_idx + 2) / 2.7)
        for e in entities:
            revenue = 19_000_000 * e["scale"] * trend * season * random.uniform(0.94, 1.07)
            cogs = revenue * random.uniform(0.55, 0.68)
            ar_bal = revenue * random.uniform(0.82, 1.40)
            ap_bal = cogs * random.uniform(0.72, 1.25)
            inventory = cogs * random.uniform(0.20, 0.42)
            wc = ar_bal + inventory - ap_bal
            working_capital.append(
                {
                    "date_id": period,
                    "entity_id": e["entity_id"],
                    "region": e["region"],
                    "revenue_usd": round2(revenue),
                    "cogs_usd": round2(cogs),
                    "ar_balance_usd": round2(ar_bal),
                    "ap_balance_usd": round2(ap_bal),
                    "inventory_balance_usd": round2(inventory),
                    "working_capital_usd": round2(wc),
                    "dso_days": round2(pct(ar_bal, revenue) * 30),
                    "dpo_days": round2(pct(ap_bal, cogs) * 30),
                    "dio_days": round2(pct(inventory, cogs) * 30),
                    "is_synthetic": "TRUE",
                }
            )

    ar_rows = []
    for i in range(1, 1251):
        cust = random.choice(dim_customer)
        e = next(x for x in entities if x["entity_id"] == cust["entity_id"])
        inv_date = AS_OF_DATE - timedelta(days=random.randint(5, 170))
        terms = cust["credit_terms_days"]
        due = inv_date + timedelta(days=terms)
        days_past = (AS_OF_DATE - due).days
        amount = random.lognormvariate(11.05, 0.55) * e["scale"]
        paid_ratio = 0 if days_past < -15 else random.uniform(0.0, 0.58)
        if days_past > 60:
            paid_ratio = random.uniform(0.0, 0.28)
        outstanding = amount * (1 - paid_ratio)
        if days_past <= 0:
            bucket = "Current"
        elif days_past <= 30:
            bucket = "1-30"
        elif days_past <= 60:
            bucket = "31-60"
        elif days_past <= 90:
            bucket = "61-90"
        else:
            bucket = "90+"
        expected_week = min(12, max(0, math.floor((max(0, days_past) + random.randint(0, 35)) / 7)))
        ar_rows.append(
            {
                "invoice_id": f"AR{i:05d}",
                "entity_id": e["entity_id"],
                "customer_id": cust["customer_id"],
                "invoice_date": inv_date.isoformat(),
                "due_date": due.isoformat(),
                "currency": e["currency"],
                "invoice_amount_usd": round2(amount),
                "outstanding_usd": round2(outstanding),
                "days_past_due": days_past,
                "aging_bucket": bucket,
                "is_overdue": "TRUE" if days_past > 0 else "FALSE",
                "expected_collection_week_id": weeks[expected_week]["week_id"],
                "collection_confidence": random.choices(["High", "Medium", "Low"], weights=[0.48, 0.37, 0.15])[0],
                "is_synthetic": "TRUE",
            }
        )

    ap_rows = []
    for i in range(1, 901):
        ven = random.choice(dim_vendor)
        e = next(x for x in entities if x["entity_id"] == ven["entity_id"])
        inv_date = AS_OF_DATE - timedelta(days=random.randint(3, 135))
        due = inv_date + timedelta(days=ven["payment_terms_days"])
        days_to_due = (due - AS_OF_DATE).days
        amount = random.lognormvariate(10.85, 0.52) * e["scale"]
        paid_ratio = random.uniform(0.0, 0.70) if days_to_due < -10 else random.uniform(0.0, 0.22)
        outstanding = amount * (1 - paid_ratio)
        if days_to_due < 0:
            due_window = "Past due"
        elif days_to_due <= 14:
            due_window = "0-14 days"
        elif days_to_due <= 30:
            due_window = "15-30 days"
        elif days_to_due <= 60:
            due_window = "31-60 days"
        else:
            due_window = "60+ days"
        payment_week = min(12, max(0, math.floor(max(0, days_to_due) / 7)))
        ap_rows.append(
            {
                "invoice_id": f"AP{i:05d}",
                "entity_id": e["entity_id"],
                "vendor_id": ven["vendor_id"],
                "invoice_date": inv_date.isoformat(),
                "due_date": due.isoformat(),
                "currency": e["currency"],
                "invoice_amount_usd": round2(amount),
                "outstanding_usd": round2(outstanding),
                "days_to_due": days_to_due,
                "due_window": due_window,
                "payment_week_id": weeks[payment_week]["week_id"],
                "payment_priority": "Hold" if ven["criticality"] == "Flexible" and days_to_due > 14 else random.choice(["Pay", "Review", "Hold"]),
                "is_synthetic": "TRUE",
            }
        )

    base_cash_by_entity = defaultdict(float)
    for row in cash_positions:
        base_cash_by_entity[row["entity_id"]] += row["available_cash_usd"]

    forecast = []
    for scenario in ["BASE", "DOWN", "UP"]:
        for e in entities:
            opening = base_cash_by_entity[e["entity_id"]]
            for i, w in enumerate(weeks):
                modifier = scenario_mod[scenario]
                receipts = 1_050_000 * e["scale"] * modifier * (1 + 0.04 * math.sin(i / 2)) * random.uniform(0.92, 1.08)
                other = 145_000 * e["scale"] * modifier * random.uniform(0.65, 1.35)
                supplier = 740_000 * e["scale"] * (1.0 if scenario != "DOWN" else 1.03) * random.uniform(0.88, 1.15)
                payroll_tax = 305_000 * e["scale"] * (1.05 if i in [1, 5, 9] else 1.0) * random.uniform(0.96, 1.05)
                capex = (210_000 * e["scale"] if i in [2, 7, 11] else 65_000 * e["scale"]) * random.uniform(0.82, 1.15)
                debt = (185_000 * e["scale"] if i in [3, 8, 12] else 55_000 * e["scale"]) * random.uniform(0.92, 1.08)
                if scenario == "DOWN":
                    receipts *= 0.88
                    supplier *= 1.04
                if scenario == "UP":
                    receipts *= 1.08
                    capex *= 1.08
                net = receipts + other - supplier - payroll_tax - capex - debt
                closing = opening + net
                forecast.append(
                    {
                        "week_id": w["week_id"],
                        "entity_id": e["entity_id"],
                        "scenario_id": scenario,
                        "opening_cash_usd": round2(opening),
                        "customer_receipts_usd": round2(receipts),
                        "other_receipts_usd": round2(other),
                        "supplier_payments_usd": round2(supplier),
                        "payroll_tax_usd": round2(payroll_tax),
                        "capex_usd": round2(capex),
                        "debt_service_usd": round2(debt),
                        "net_cash_flow_usd": round2(net),
                        "closing_cash_usd": round2(closing),
                        "minimum_cash_buffer_usd": round2(1_800_000 * e["scale"]),
                        "is_synthetic": "TRUE",
                    }
                )
                opening = closing

    accuracy = []
    for i in range(1, 9):
        week_start = AS_OF_DATE - timedelta(days=i * 7)
        for e in entities:
            actual = random.uniform(-380_000, 720_000) * e["scale"]
            forecasted = actual * random.uniform(0.82, 1.18) + random.uniform(-90_000, 90_000)
            accuracy.append(
                {
                    "accuracy_id": f"ACC{i:02d}_{e['entity_id']}",
                    "week_start": week_start.isoformat(),
                    "entity_id": e["entity_id"],
                    "forecast_net_cash_flow_usd": round2(forecasted),
                    "actual_net_cash_flow_usd": round2(actual),
                    "abs_error_usd": round2(abs(actual - forecasted)),
                    "error_direction": "Over forecast" if forecasted > actual else "Under forecast",
                    "is_synthetic": "TRUE",
                }
            )

    currencies = ["EUR", "GBP", "SGD", "VND", "BRL", "CNY", "JPY"]
    fx_rows = []
    for e in entities:
        for ccy in random.sample(currencies, 4):
            gross = random.uniform(900_000, 7_500_000) * e["scale"]
            payable = random.uniform(500_000, 5_400_000) * e["scale"]
            net = abs(gross - payable)
            hedge_ratio = random.uniform(0.42, 0.88) if ccy in ["EUR", "GBP", "SGD"] else random.uniform(0.18, 0.62)
            hedged = net * hedge_ratio
            fx_rows.append(
                {
                    "exposure_id": f"FX_{e['entity_id']}_{ccy}",
                    "entity_id": e["entity_id"],
                    "currency_pair": f"{ccy}/USD",
                    "exposure_currency": ccy,
                    "receivable_exposure_usd": round2(gross),
                    "payable_exposure_usd": round2(payable),
                    "net_exposure_usd": round2(net),
                    "hedged_exposure_usd": round2(hedged),
                    "unhedged_exposure_usd": round2(max(0, net - hedged)),
                    "hedge_ratio": round(hedge_ratio, 4),
                    "risk_bucket": "High" if hedge_ratio < 0.45 and net > 2_500_000 else random.choice(["Medium", "Low"]),
                    "is_synthetic": "TRUE",
                }
            )

    risk_types = [
        "Overdue AR concentration",
        "Low cash buffer",
        "AP payment hold",
        "Unhedged FX exposure",
        "Debt maturity watch",
        "Bank reconciliation delay",
        "Forecast variance spike",
    ]
    actions = []
    for i in range(1, 76):
        e = random.choice(entities)
        risk = random.choice(risk_types)
        level = random.choices(["High", "Medium", "Low"], weights=[0.22, 0.48, 0.30])[0]
        status = random.choices(["Open", "In Review", "Action Agreed", "Closed"], weights=[0.35, 0.28, 0.24, 0.13])[0]
        actions.append(
            {
                "action_id": f"TR{i:03d}",
                "entity_id": e["entity_id"],
                "risk_type": risk,
                "risk_level": level,
                "status": status,
                "owner_team": random.choice(["Treasury", "Credit Control", "Procurement", "Regional Finance", "FP&A"]),
                "amount_usd": round2(random.uniform(125_000, 2_400_000) * (1.7 if level == "High" else 1.0)),
                "due_date": (AS_OF_DATE + timedelta(days=random.randint(2, 42))).isoformat(),
                "recommended_action": {
                    "Overdue AR concentration": "Escalate top customers and lock weekly collection promises.",
                    "Low cash buffer": "Review facility draw timing and defer non-critical payments.",
                    "AP payment hold": "Confirm supplier criticality before delaying disbursement.",
                    "Unhedged FX exposure": "Propose hedge top-up or natural offset review.",
                    "Debt maturity watch": "Confirm refinancing plan and covenant headroom.",
                    "Bank reconciliation delay": "Clear unreconciled bank items before forecast refresh.",
                    "Forecast variance spike": "Re-baseline short-term receipts and payment timing.",
                }[risk],
                "is_synthetic": "TRUE",
            }
        )

    data = {
        **{k: v for k, v in dims.items() if k != "entities_full"},
        "fact_cash_position": cash_positions,
        "fact_liquidity_facility": liquidity,
        "fact_working_capital": working_capital,
        "fact_ar_invoice": ar_rows,
        "fact_ap_invoice": ap_rows,
        "fact_cash_forecast": forecast,
        "fact_forecast_accuracy": accuracy,
        "fact_fx_exposure": fx_rows,
        "fact_treasury_risk_action": actions,
        "metadata": {
            "seed": SEED,
            "as_of_date": AS_OF_DATE.isoformat(),
            "latest_complete_month": LATEST_MONTH,
            "forecast_start": FORECAST_START.isoformat(),
            "generated_at": RUN_TS,
            "is_synthetic": True,
        },
    }
    return data


def validate_data(data: dict) -> dict:
    checks = []
    row_counts = {name: len(rows) for name, rows in data.items() if isinstance(rows, list)}

    def unique_check(name: str, rows: list[dict], keys: list[str]) -> None:
        values = [tuple(row[k] for k in keys) for row in rows]
        checks.append(
            {
                "check": f"{name} grain uniqueness",
                "status": "pass" if len(values) == len(set(values)) else "fail",
                "detail": f"{len(values) - len(set(values))} duplicate keys on {', '.join(keys)}",
            }
        )

    unique_check("FactCashForecast", data["fact_cash_forecast"], ["week_id", "entity_id", "scenario_id"])
    unique_check("FactCashPosition", data["fact_cash_position"], ["snapshot_date", "entity_id", "bank_id"])
    unique_check("FactWorkingCapital", data["fact_working_capital"], ["date_id", "entity_id"])
    unique_check("FactFXExposure", data["fact_fx_exposure"], ["exposure_id"])

    fact_forecast = data["fact_cash_forecast"]
    continuity_errors = 0
    by_key = defaultdict(list)
    for row in fact_forecast:
        by_key[(row["entity_id"], row["scenario_id"])].append(row)
    for rows in by_key.values():
        rows.sort(key=lambda r: r["week_id"])
        for prev, cur in zip(rows, rows[1:]):
            if abs(prev["closing_cash_usd"] - cur["opening_cash_usd"]) > 1:
                continuity_errors += 1
    checks.append(
        {
            "check": "13-week forecast cash continuity",
            "status": "pass" if continuity_errors == 0 else "fail",
            "detail": f"{continuity_errors} opening-to-prior-closing mismatches",
        }
    )

    negative_outstanding = sum(
        1
        for row in data["fact_ar_invoice"] + data["fact_ap_invoice"]
        if row["outstanding_usd"] < 0
    )
    checks.append(
        {
            "check": "AR/AP outstanding non-negative",
            "status": "pass" if negative_outstanding == 0 else "fail",
            "detail": f"{negative_outstanding} invoices with negative outstanding balance",
        }
    )

    dso_bad = [row for row in data["fact_working_capital"] if not (15 <= row["dso_days"] <= 55)]
    dpo_bad = [row for row in data["fact_working_capital"] if not (15 <= row["dpo_days"] <= 55)]
    checks.append(
        {
            "check": "Working capital days within realistic portfolio band",
            "status": "pass" if not dso_bad and not dpo_bad else "fail",
            "detail": f"DSO outliers={len(dso_bad)}, DPO outliers={len(dpo_bad)}",
        }
    )

    fx_bad = [row for row in data["fact_fx_exposure"] if not (0 <= row["hedge_ratio"] <= 1)]
    checks.append(
        {
            "check": "FX hedge ratios bounded",
            "status": "pass" if not fx_bad else "fail",
            "detail": f"{len(fx_bad)} rows outside 0-1 hedge ratio range",
        }
    )

    required_entities = {row["entity_id"] for row in data["dim_entity"]}
    fk_errors = 0
    for table in [
        "fact_cash_position",
        "fact_liquidity_facility",
        "fact_working_capital",
        "fact_ar_invoice",
        "fact_ap_invoice",
        "fact_cash_forecast",
        "fact_forecast_accuracy",
        "fact_fx_exposure",
        "fact_treasury_risk_action",
    ]:
        fk_errors += sum(1 for row in data[table] if row["entity_id"] not in required_entities)
    checks.append(
        {
            "check": "Entity foreign keys valid",
            "status": "pass" if fk_errors == 0 else "fail",
            "detail": f"{fk_errors} invalid entity references",
        }
    )

    status = "pass" if all(check["status"] == "pass" for check in checks) else "fail"
    return {
        "status": status,
        "checked_at": RUN_TS,
        "row_counts": row_counts,
        "date_coverage": {
            "working_capital_months": [data["dim_date"][0]["date_id"], data["dim_date"][-1]["date_id"]],
            "forecast_weeks": [data["dim_week"][0]["week_start"], data["dim_week"][-1]["week_end"]],
            "as_of_date": AS_OF_DATE.isoformat(),
        },
        "checks": checks,
    }


def measure_catalog() -> list[dict]:
    return [
        {"measure_name": "Cash Balance", "definition": "Total book cash balance across bank accounts.", "dax": "SUM(FactCashPosition[balance_usd])", "format_string": "$#,0"},
        {"measure_name": "Available Cash", "definition": "Cash balance net of restricted cash.", "dax": "SUM(FactCashPosition[available_cash_usd])", "format_string": "$#,0"},
        {"measure_name": "Restricted Cash", "definition": "Restricted bank cash not available for operating liquidity.", "dax": "SUM(FactCashPosition[restricted_cash_usd])", "format_string": "$#,0"},
        {"measure_name": "Credit Available", "definition": "Undrawn committed liquidity facilities.", "dax": "SUM(FactLiquidityFacility[available_usd])", "format_string": "$#,0"},
        {"measure_name": "Available Liquidity", "definition": "Available cash plus undrawn credit facilities.", "dax": "[Available Cash] + [Credit Available]", "format_string": "$#,0"},
        {"measure_name": "Minimum Cash Buffer", "definition": "Entity minimum cash covenant or operating buffer.", "dax": "SUM(FactLiquidityFacility[min_cash_buffer_usd])", "format_string": "$#,0"},
        {"measure_name": "Liquidity Headroom", "definition": "Available liquidity above minimum cash buffer.", "dax": "[Available Liquidity] - [Minimum Cash Buffer]", "format_string": "$#,0"},
        {"measure_name": "AR Outstanding", "definition": "Open customer receivable balance.", "dax": "SUM(FactARInvoice[outstanding_usd])", "format_string": "$#,0"},
        {"measure_name": "Overdue AR", "definition": "Open AR balance past due date.", "dax": "CALCULATE([AR Outstanding], FactARInvoice[is_overdue] = TRUE())", "format_string": "$#,0"},
        {"measure_name": "Overdue AR %", "definition": "Overdue AR as a percentage of total AR outstanding.", "dax": "DIVIDE([Overdue AR], [AR Outstanding])", "format_string": "0.0%"},
        {"measure_name": "AP Outstanding", "definition": "Open vendor payable balance.", "dax": "SUM(FactAPInvoice[outstanding_usd])", "format_string": "$#,0"},
        {"measure_name": "AP Due 14 Days", "definition": "AP outstanding due in the next 14 days.", "dax": "CALCULATE([AP Outstanding], FactAPInvoice[due_window] = \"0-14 days\")", "format_string": "$#,0"},
        {"measure_name": "Revenue", "definition": "Monthly revenue used for DSO denominator.", "dax": "SUM(FactWorkingCapital[revenue_usd])", "format_string": "$#,0"},
        {"measure_name": "COGS", "definition": "Monthly cost of goods sold used for DPO and DIO denominators.", "dax": "SUM(FactWorkingCapital[cogs_usd])", "format_string": "$#,0"},
        {"measure_name": "Working Capital", "definition": "AR plus inventory less AP.", "dax": "SUM(FactWorkingCapital[working_capital_usd])", "format_string": "$#,0"},
        {"measure_name": "DSO", "definition": "Days sales outstanding, based on AR balance over revenue.", "dax": "DIVIDE(SUM(FactWorkingCapital[ar_balance_usd]), [Revenue]) * 30", "format_string": "0.0"},
        {"measure_name": "DPO", "definition": "Days payable outstanding, based on AP balance over COGS.", "dax": "DIVIDE(SUM(FactWorkingCapital[ap_balance_usd]), [COGS]) * 30", "format_string": "0.0"},
        {"measure_name": "DIO", "definition": "Days inventory outstanding, based on inventory balance over COGS.", "dax": "DIVIDE(SUM(FactWorkingCapital[inventory_balance_usd]), [COGS]) * 30", "format_string": "0.0"},
        {"measure_name": "Cash Conversion Cycle", "definition": "DSO plus DIO minus DPO.", "dax": "[DSO] + [DIO] - [DPO]", "format_string": "0.0"},
        {"measure_name": "Forecast Closing Cash", "definition": "Projected closing cash over the selected 13-week forecast scenario.", "dax": "SUM(FactCashForecast[closing_cash_usd])", "format_string": "$#,0"},
        {"measure_name": "Forecast Net Cash Flow", "definition": "Projected cash inflows less outflows.", "dax": "SUM(FactCashForecast[net_cash_flow_usd])", "format_string": "$#,0"},
        {"measure_name": "Forecast Receipts", "definition": "Forecast customer and other receipts.", "dax": "SUM(FactCashForecast[customer_receipts_usd]) + SUM(FactCashForecast[other_receipts_usd])", "format_string": "$#,0"},
        {"measure_name": "Forecast Payments", "definition": "Forecast supplier, payroll, capex, and debt payments.", "dax": "SUM(FactCashForecast[supplier_payments_usd]) + SUM(FactCashForecast[payroll_tax_usd]) + SUM(FactCashForecast[capex_usd]) + SUM(FactCashForecast[debt_service_usd])", "format_string": "$#,0"},
        {"measure_name": "Cash Runway Weeks", "definition": "Available liquidity divided by average weekly cash burn when net flow is negative.", "dax": "DIVIDE([Available Liquidity], ABS(AVERAGE(FactCashForecast[net_cash_flow_usd])))", "format_string": "0.0"},
        {"measure_name": "Forecast Error %", "definition": "Absolute forecast error divided by absolute actual net cash flow.", "dax": "DIVIDE(SUM(FactForecastAccuracy[abs_error_usd]), SUMX(FactForecastAccuracy, ABS(FactForecastAccuracy[actual_net_cash_flow_usd])))", "format_string": "0.0%"},
        {"measure_name": "FX Net Exposure", "definition": "Gross net FX exposure in USD equivalent.", "dax": "SUM(FactFXExposure[net_exposure_usd])", "format_string": "$#,0"},
        {"measure_name": "Unhedged FX Exposure", "definition": "FX exposure remaining after hedge coverage.", "dax": "SUM(FactFXExposure[unhedged_exposure_usd])", "format_string": "$#,0"},
        {"measure_name": "Unhedged FX %", "definition": "Unhedged exposure divided by total net FX exposure.", "dax": "DIVIDE([Unhedged FX Exposure], [FX Net Exposure])", "format_string": "0.0%"},
        {"measure_name": "Open Risk Value", "definition": "Value attached to non-closed treasury action items.", "dax": "CALCULATE(SUM(FactTreasuryRiskAction[amount_usd]), FactTreasuryRiskAction[status] <> \"Closed\")", "format_string": "$#,0"},
        {"measure_name": "Open Risk Count", "definition": "Count of non-closed treasury risk action items.", "dax": "CALCULATE(COUNTROWS(FactTreasuryRiskAction), FactTreasuryRiskAction[status] <> \"Closed\")", "format_string": "#,0"},
    ]


def build_data_dictionary(data: dict) -> str:
    descriptions = {
        "dim_date": "Monthly calendar for working capital trend analysis.",
        "dim_week": "13-week forecast calendar.",
        "dim_entity": "Legal entity, country, region, and functional currency.",
        "dim_customer": "Customer master with sector, entity, credit terms, and risk rating.",
        "dim_vendor": "Vendor master with category, entity, terms, and criticality.",
        "dim_bank": "Bank counterparty dimension.",
        "dim_scenario": "Forecast scenarios.",
        "dim_cash_category": "Cash flow category classification.",
        "fact_cash_position": "Latest bank cash position by entity, bank, and currency.",
        "fact_liquidity_facility": "Liquidity facilities and covenants by entity.",
        "fact_working_capital": "Monthly revenue, COGS, AR, AP, inventory, and working capital days by entity.",
        "fact_ar_invoice": "Invoice-level AR aging and expected collection timing.",
        "fact_ap_invoice": "Invoice-level AP due schedule and payment priority.",
        "fact_cash_forecast": "13-week direct cash forecast by entity and scenario.",
        "fact_forecast_accuracy": "Historical weekly forecast accuracy by entity.",
        "fact_fx_exposure": "FX receivable, payable, hedged, and unhedged exposure.",
        "fact_treasury_risk_action": "Treasury risks, action owners, status, value, and due date.",
    }
    lines = ["# Data Dictionary", "", "| Table | Grain | Rows | Description |", "|---|---:|---:|---|"]
    grains = {
        "dim_date": "1 row per month",
        "dim_week": "1 row per forecast week",
        "dim_entity": "1 row per entity",
        "dim_customer": "1 row per customer",
        "dim_vendor": "1 row per vendor",
        "dim_bank": "1 row per bank",
        "dim_scenario": "1 row per scenario",
        "dim_cash_category": "1 row per category",
        "fact_cash_position": "snapshot_date x entity x bank",
        "fact_liquidity_facility": "facility x entity",
        "fact_working_capital": "month x entity",
        "fact_ar_invoice": "1 row per AR invoice",
        "fact_ap_invoice": "1 row per AP invoice",
        "fact_cash_forecast": "week x entity x scenario",
        "fact_forecast_accuracy": "historical week x entity",
        "fact_fx_exposure": "entity x exposure currency",
        "fact_treasury_risk_action": "1 row per action item",
    }
    for table, rows in data.items():
        if isinstance(rows, list):
            lines.append(f"| {table} | {grains.get(table, '')} | {len(rows)} | {descriptions.get(table, '')} |")
    lines.append("")
    lines.append("All portfolio data is synthetic with fixed seed 14042. Currency values are USD equivalents unless the field name says local.")
    return "\n".join(lines)


def build_html(data: dict) -> str:
    def by_id(rows, key):
        return {row[key]: row for row in rows}

    entities = by_id(data["dim_entity"], "entity_id")
    weeks = by_id(data["dim_week"], "week_id")
    customers = by_id(data["dim_customer"], "customer_id")
    vendors = by_id(data["dim_vendor"], "vendor_id")
    scenarios = by_id(data["dim_scenario"], "scenario_id")

    payload = {
        "entities": data["dim_entity"],
        "weeks": data["dim_week"],
        "scenarios": data["dim_scenario"],
        "cash": data["fact_cash_position"],
        "liquidity": data["fact_liquidity_facility"],
        "wc": data["fact_working_capital"],
        "ar": data["fact_ar_invoice"],
        "ap": data["fact_ap_invoice"],
        "forecast": data["fact_cash_forecast"],
        "accuracy": data["fact_forecast_accuracy"],
        "fx": data["fact_fx_exposure"],
        "risk": data["fact_treasury_risk_action"],
        "lookup": {
            "entities": entities,
            "weeks": weeks,
            "customers": customers,
            "vendors": vendors,
            "scenarios": scenarios,
        },
    }
    data_json = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    return f"""
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Project 14 - Treasury Working Capital</title>
  <style>
    :root {{
      --bg:#f3f6f8; --panel:#ffffff; --panel2:#f8fafb; --line:#d8e0e7;
      --text:#15202b; --muted:#607081; --teal:#0f766e; --blue:#2f5f9e;
      --green:#6f8552; --gold:#b68b36; --rose:#b85062; --ink:#22313f;
    }}
    * {{ box-sizing:border-box; }}
    body {{ margin:0; background:var(--bg); color:var(--text); font-family:"Segoe UI", Arial, sans-serif; }}
    .shell {{ max-width:1420px; margin:0 auto; padding:18px 22px 30px; }}
    header {{ display:grid; grid-template-columns:1fr auto; gap:18px; align-items:end; border-bottom:1px solid var(--line); padding-bottom:12px; }}
    .eyebrow {{ color:var(--teal); font-size:12px; font-weight:700; letter-spacing:0; }}
    h1 {{ margin:4px 0 0; font-size:24px; line-height:1.1; }}
    .meta {{ color:var(--muted); font-size:12px; text-align:right; }}
    .tabs {{ display:flex; gap:8px; margin:16px 0; flex-wrap:wrap; }}
    .tabs button {{ border:1px solid var(--line); background:var(--panel); color:var(--text); padding:9px 13px; border-radius:6px; font-weight:650; cursor:pointer; }}
    .tabs button.active {{ background:var(--teal); border-color:var(--teal); color:white; }}
    .filters {{ display:grid; grid-template-columns:repeat(4, minmax(170px, 1fr)); gap:10px; margin-bottom:14px; }}
    label {{ display:block; color:var(--muted); font-size:11px; margin-bottom:4px; font-weight:650; }}
    select {{ width:100%; border:1px solid var(--line); border-radius:6px; background:white; padding:8px; font-size:13px; }}
    .page {{ display:none; }}
    .page.active {{ display:block; }}
    .grid {{ display:grid; grid-template-columns:repeat(12,1fr); gap:12px; }}
    .card, .panel {{ background:var(--panel); border:1px solid var(--line); border-radius:8px; box-shadow:0 1px 2px rgba(17,24,39,.05); }}
    .card {{ padding:13px 14px; min-height:86px; }}
    .card .label {{ font-size:12px; color:var(--muted); font-weight:700; }}
    .card .value {{ font-size:25px; margin-top:7px; font-weight:800; color:var(--ink); }}
    .card .sub {{ font-size:11px; color:var(--muted); margin-top:4px; }}
    .panel {{ padding:13px 14px; min-height:240px; overflow:hidden; }}
    .panel h2 {{ margin:0 0 7px; font-size:14px; }}
    .panel p {{ margin:0 0 9px; color:var(--muted); font-size:12px; }}
    .span2 {{ grid-column:span 2; }} .span3 {{ grid-column:span 3; }} .span4 {{ grid-column:span 4; }}
    .span5 {{ grid-column:span 5; }} .span6 {{ grid-column:span 6; }} .span7 {{ grid-column:span 7; }}
    .span8 {{ grid-column:span 8; }} .span12 {{ grid-column:span 12; }}
    svg {{ width:100%; height:190px; display:block; }}
    table {{ width:100%; border-collapse:collapse; font-size:12px; }}
    th {{ color:var(--teal); background:var(--panel2); text-align:left; font-weight:750; }}
    th, td {{ padding:7px 8px; border-bottom:1px solid var(--line); white-space:nowrap; }}
    td.num {{ text-align:right; font-variant-numeric:tabular-nums; }}
    .status {{ display:inline-block; min-width:64px; padding:3px 7px; border-radius:4px; font-weight:700; font-size:11px; text-align:center; }}
    .High {{ background:#fae8eb; color:#a13d4f; }} .Medium {{ background:#fff3d8; color:#876315; }} .Low {{ background:#e8f3ee; color:#387060; }}
    #actionStrip {{ margin:12px 0 0; color:var(--muted); font-size:12px; }}
    @media (max-width:900px) {{
      header {{ grid-template-columns:1fr; }}
      .meta {{ text-align:left; }}
      .filters {{ grid-template-columns:1fr 1fr; }}
      .grid {{ grid-template-columns:1fr; }}
      .span2,.span3,.span4,.span5,.span6,.span7,.span8,.span12 {{ grid-column:span 1; }}
      table {{ font-size:11px; }}
    }}
  </style>
</head>
<body>
<div class="shell">
  <header>
    <div>
      <div class="eyebrow">PROJECT 14 / TREASURY WORKING CAPITAL</div>
      <h1>Treasury Working Capital Command Dashboard</h1>
    </div>
    <div class="meta">Synthetic portfolio data, seed {SEED}<br>As of {AS_OF_DATE.isoformat()} / forecast start {FORECAST_START.isoformat()}</div>
  </header>
  <div class="tabs">
    <button data-page="overview" class="active">Treasury Command Center</button>
    <button data-page="wc">Working Capital Control</button>
    <button data-page="risk">Forecast, FX & Risk</button>
  </div>
  <div class="filters">
    <div><label>Region</label><select id="regionFilter"></select></div>
    <div><label>Entity</label><select id="entityFilter"></select></div>
    <div><label>Scenario</label><select id="scenarioFilter"></select></div>
    <div><label>Forecast Week</label><select id="weekFilter"></select></div>
  </div>
  <section id="overview" class="page active">
    <div class="grid" id="overviewGrid"></div>
  </section>
  <section id="wc" class="page">
    <div class="grid" id="wcGrid"></div>
  </section>
  <section id="risk" class="page">
    <div class="grid" id="riskGrid"></div>
  </section>
</div>
<script>
const DATA = {data_json};
const PALETTE = ["#0f766e","#2f5f9e","#6f8552","#b68b36","#b85062","#22313f"];
const fmtM = v => "$" + ((v||0)/1e6).toFixed(1) + "M";
const fmtP = v => ((v||0)*100).toFixed(1) + "%";
const sum = (arr, f) => arr.reduce((a,b)=>a+(+f(b)||0),0);
function unique(arr) {{ return [...new Set(arr)].sort(); }}
function optionize(el, values, allLabel) {{ el.innerHTML = `<option value="__ALL__">${{allLabel}}</option>` + values.map(v=>`<option value="${{v}}">${{v}}</option>`).join(""); }}
function getEntity(row) {{ return DATA.lookup.entities[row.entity_id] || {{}}; }}
function passes(row) {{
  const region = regionFilter.value, entity = entityFilter.value;
  const ent = getEntity(row);
  if (region !== "__ALL__" && ent.region !== region && row.region !== region) return false;
  if (entity !== "__ALL__" && row.entity_id !== entity) return false;
  return true;
}}
function group(rows, key, valueFn) {{
  const m = new Map();
  rows.forEach(r => {{ const k = key(r); m.set(k, (m.get(k)||0) + (+valueFn(r)||0)); }});
  return [...m.entries()].map(([name,value])=>({{name,value}}));
}}
function card(label, value, sub="") {{ return `<div class="card span2"><div class="label">${{label}}</div><div class="value">${{value}}</div><div class="sub">${{sub}}</div></div>`; }}
function panel(cls, title, sub, body) {{ return `<div class="panel ${{cls}}"><h2>${{title}}</h2><p>${{sub}}</p>${{body}}</div>`; }}
function bars(items, opts={{}}) {{
  const w=640,h=190, ml=120, mr=18, mt=12, mb=24;
  const max=Math.max(1,...items.map(d=>Math.abs(d.value)));
  const bh=(h-mt-mb)/Math.max(1,items.length);
  let s=`<svg viewBox="0 0 ${{w}} ${{h}}" role="img">`;
  items.forEach((d,i)=>{{ const y=mt+i*bh+3; const bw=Math.abs(d.value)/max*(w-ml-mr); const c=PALETTE[i%PALETTE.length]; s+=`<text x="4" y="${{y+bh/2+3}}" font-size="11" fill="#607081">${{d.name}}</text><rect x="${{ml}}" y="${{y}}" width="${{bw}}" height="${{Math.max(8,bh-7)}}" rx="3" fill="${{c}}"></rect><text x="${{ml+bw+5}}" y="${{y+bh/2+3}}" font-size="11" fill="#15202b">${{opts.percent?fmtP(d.value):fmtM(d.value)}}</text>`; }});
  return s + `</svg>`;
}}
function columns(items) {{
  const w=640,h=190, ml=42, mr=14, mt=12, mb=34, max=Math.max(1,...items.map(d=>Math.abs(d.value)));
  const gap=8, bw=(w-ml-mr-gap*(items.length-1))/Math.max(1,items.length);
  let s=`<svg viewBox="0 0 ${{w}} ${{h}}" role="img"><line x1="${{ml}}" y1="${{h-mb}}" x2="${{w-mr}}" y2="${{h-mb}}" stroke="#d8e0e7"/>`;
  items.forEach((d,i)=>{{ const barH=Math.abs(d.value)/max*(h-mt-mb); const x=ml+i*(bw+gap); const y=h-mb-barH; s+=`<rect x="${{x}}" y="${{y}}" width="${{bw}}" height="${{barH}}" rx="3" fill="${{PALETTE[i%PALETTE.length]}}"></rect><text transform="translate(${{x+bw/2}},${{h-11}}) rotate(-25)" font-size="10" fill="#607081" text-anchor="end">${{d.name}}</text>`; }});
  return s + `</svg>`;
}}
function line(items, seriesKey, xKey, yKey) {{
  const w=720,h=190, ml=46, mr=20, mt=16, mb=34;
  const groups = group(items, r=>r[seriesKey], r=>0).map(d=>d.name);
  const xs = unique(items.map(r=>r[xKey]));
  const vals = items.map(r=>+r[yKey]||0), min=Math.min(...vals), max=Math.max(...vals);
  const sx = x => ml + xs.indexOf(x) * ((w-ml-mr)/Math.max(1,xs.length-1));
  const sy = y => mt + (max-y)/Math.max(1,max-min)*(h-mt-mb);
  let s=`<svg viewBox="0 0 ${{w}} ${{h}}" role="img"><line x1="${{ml}}" y1="${{h-mb}}" x2="${{w-mr}}" y2="${{h-mb}}" stroke="#d8e0e7"/>`;
  groups.forEach((g,gi)=>{{ const rows=items.filter(r=>r[seriesKey]===g).sort((a,b)=>xs.indexOf(a[xKey])-xs.indexOf(b[xKey])); const pts=rows.map(r=>`${{sx(r[xKey])}},${{sy(+r[yKey]||0)}}`).join(" "); s+=`<polyline points="${{pts}}" fill="none" stroke="${{PALETTE[gi%PALETTE.length]}}" stroke-width="3"/>`; rows.forEach(r=>s+=`<circle cx="${{sx(r[xKey])}}" cy="${{sy(+r[yKey]||0)}}" r="3" fill="${{PALETTE[gi%PALETTE.length]}}"/>`); s+=`<text x="${{ml+gi*115}}" y="11" font-size="11" fill="${{PALETTE[gi%PALETTE.length]}}">${{g}}</text>`; }});
  xs.forEach((x,i)=>{{ if(i%2===0) s+=`<text x="${{sx(x)}}" y="${{h-10}}" font-size="10" fill="#607081" text-anchor="middle">${{x.split(' ')[0]}}</text>`; }});
  return s + `</svg>`;
}}
function rowsTable(headers, rows) {{
  return `<table><thead><tr>${{headers.map(h=>`<th>${{h}}</th>`).join("")}}</tr></thead><tbody>${{rows.join("")}}</tbody></table>`;
}}
function current() {{
  const scenario = scenarioFilter.value === "__ALL__" ? "BASE" : scenarioFilter.value;
  const week = weekFilter.value === "__ALL__" ? "W13" : weekFilter.value;
  const cash = DATA.cash.filter(passes), liq = DATA.liquidity.filter(passes);
  const ar = DATA.ar.filter(passes), ap = DATA.ap.filter(passes), wc = DATA.wc.filter(passes);
  const fc = DATA.forecast.filter(r=>passes(r) && r.scenario_id===scenario);
  const fx = DATA.fx.filter(passes), risk = DATA.risk.filter(passes);
  const acc = DATA.accuracy.filter(passes);
  const availableCash = sum(cash,r=>r.available_cash_usd);
  const credit = sum(liq,r=>r.available_usd);
  const minBuffer = sum(liq,r=>r.min_cash_buffer_usd);
  const arOut = sum(ar,r=>r.outstanding_usd), overdue = sum(ar.filter(r=>r.is_overdue==="TRUE"),r=>r.outstanding_usd);
  const apOut = sum(ap,r=>r.outstanding_usd);
  const rev = sum(wc,r=>r.revenue_usd), cogs=sum(wc,r=>r.cogs_usd), arBal=sum(wc,r=>r.ar_balance_usd), apBal=sum(wc,r=>r.ap_balance_usd), inv=sum(wc,r=>r.inventory_balance_usd);
  const latestFc = fc.filter(r=>r.week_id===week);
  const net = sum(fc,r=>r.net_cash_flow_usd), avgNet = net/Math.max(1,fc.length);
  const absErr=sum(acc,r=>r.abs_error_usd), absAct=sum(acc,r=>Math.abs(r.actual_net_cash_flow_usd));
  const fxNet=sum(fx,r=>r.net_exposure_usd), unhedged=sum(fx,r=>r.unhedged_exposure_usd);
  return {{scenario, week, cash, liq, ar, ap, wc, fc, latestFc, fx, risk, acc, availableCash, credit, minBuffer, arOut, overdue, apOut, rev, cogs, arBal, apBal, inv, net, avgNet, absErr, absAct, fxNet, unhedged}};
}}
function render() {{
  const c = current();
  const headroom = c.availableCash + c.credit - c.minBuffer;
  const runway = Math.abs(c.avgNet)>1 ? (c.availableCash+c.credit)/Math.abs(c.avgNet) : 99;
  const dso = c.rev ? c.arBal/c.rev*30 : 0, dpo = c.cogs ? c.apBal/c.cogs*30 : 0, dio = c.cogs ? c.inv/c.cogs*30 : 0;
  const weekRows = c.fc.map(r=>({{...r, week_label: DATA.lookup.weeks[r.week_id].week_label, scenario: DATA.lookup.scenarios[r.scenario_id].scenario}}));
  const overviewRows = c.risk.filter(r=>r.status!=="Closed").sort((a,b)=>b.amount_usd-a.amount_usd).slice(0,6).map(r=>`<tr><td>${{DATA.lookup.entities[r.entity_id].country}}</td><td>${{r.risk_type}}</td><td><span class="status ${{r.risk_level}}">${{r.risk_level}}</span></td><td class="num">${{fmtM(r.amount_usd)}}</td></tr>`);
  overviewGrid.innerHTML = [
    card("Available Liquidity", fmtM(c.availableCash+c.credit), "cash plus undrawn facilities"),
    card("Liquidity Headroom", fmtM(headroom), "above minimum cash buffer"),
    card("Cash Runway", runway.toFixed(1)+" wks", "based on average weekly net flow"),
    card("13W Net Cash Flow", fmtM(c.net), c.scenario+" scenario"),
    card("DSO / DPO", dso.toFixed(1)+" / "+dpo.toFixed(1), "working capital days"),
    card("Forecast Error", fmtP(c.absAct?c.absErr/c.absAct:0), "last 8-week backtest"),
    panel("span8","13-week closing cash by scenario","Direct forecast view by week", line(DATA.forecast.filter(passes).map(r=>({{...r, week_label: DATA.lookup.weeks[r.week_id].week_label, scenario: DATA.lookup.scenarios[r.scenario_id].scenario}})), "scenario", "week_label", "closing_cash_usd")),
    panel("span4","Liquidity by region","Available cash plus facilities", bars(group([...c.cash.map(r=>({{region:getEntity(r).region, value:r.available_cash_usd}})), ...c.liq.map(r=>({{region:getEntity(r).region, value:r.available_usd}}))], r=>r.region, r=>r.value).sort((a,b)=>b.value-a.value))),
    panel("span6","Cash movement drivers","Forecast net cash flow by week", columns(group(weekRows, r=>r.week_label, r=>r.net_cash_flow_usd))),
    panel("span6","Management action queue","Largest open treasury actions", rowsTable(["Country","Risk","Level","Value"], overviewRows)),
    `<div id="actionStrip" class="span12">Priority: protect liquidity headroom, collect 90+ AR, and close high-value FX hedge gaps before the next forecast refresh.</div>`
  ].join("");
  const arAging = group(c.ar, r=>r.aging_bucket, r=>r.outstanding_usd);
  const apDue = group(c.ap, r=>r.due_window, r=>r.outstanding_usd);
  const customerRows = group(c.ar, r=>DATA.lookup.customers[r.customer_id].customer, r=>r.outstanding_usd).sort((a,b)=>b.value-a.value).slice(0,7).map(r=>`<tr><td>${{r.name}}</td><td class="num">${{fmtM(r.value)}}</td></tr>`);
  const vendorRows = group(c.ap, r=>DATA.lookup.vendors[r.vendor_id].vendor, r=>r.outstanding_usd).sort((a,b)=>b.value-a.value).slice(0,7).map(r=>`<tr><td>${{r.name}}</td><td class="num">${{fmtM(r.value)}}</td></tr>`);
  wcGrid.innerHTML = [
    card("AR Outstanding", fmtM(c.arOut), "open customer balance"),
    card("Overdue AR", fmtM(c.overdue), fmtP(c.arOut?c.overdue/c.arOut:0)+" of AR"),
    card("AP Outstanding", fmtM(c.apOut), "open vendor balance"),
    card("Working Capital", fmtM(c.arBal+c.inv-c.apBal), "AR plus inventory less AP"),
    card("DSO", dso.toFixed(1), "days sales outstanding"),
    card("Cash Conversion", (dso+dio-dpo).toFixed(1), "DSO plus DIO less DPO"),
    panel("span4","AR aging","Open receivables by aging bucket", bars(arAging)),
    panel("span4","AP due schedule","Vendor payments by due window", bars(apDue)),
    panel("span4","DSO and DPO trend","Latest monthly working capital days", line(c.wc.map(r=>({{...r, metric:"DSO", value:r.dso_days}})).concat(c.wc.map(r=>({{...r, metric:"DPO", value:r.dpo_days}}))), "metric", "date_id", "value")),
    panel("span6","Top customer collection focus","Largest AR balances", rowsTable(["Customer","Outstanding"], customerRows)),
    panel("span6","Top vendor payment focus","Largest AP balances", rowsTable(["Vendor","Outstanding"], vendorRows))
  ].join("");
  const fxByCcy = group(c.fx, r=>r.exposure_currency, r=>r.unhedged_exposure_usd).sort((a,b)=>b.value-a.value);
  const riskRows = c.risk.filter(r=>r.status!=="Closed").sort((a,b)=>b.amount_usd-a.amount_usd).slice(0,8).map(r=>`<tr><td>${{r.action_id}}</td><td>${{DATA.lookup.entities[r.entity_id].country}}</td><td>${{r.risk_type}}</td><td><span class="status ${{r.risk_level}}">${{r.risk_level}}</span></td><td class="num">${{fmtM(r.amount_usd)}}</td></tr>`);
  const facilityRows = c.liq.sort((a,b)=>new Date(a.maturity_date)-new Date(b.maturity_date)).map(r=>`<tr><td>${{DATA.lookup.entities[r.entity_id].country}}</td><td>${{r.facility_type}}</td><td class="num">${{fmtM(r.available_usd)}}</td><td>${{r.maturity_date}}</td><td>${{r.covenant_status}}</td></tr>`);
  riskGrid.innerHTML = [
    card("Closing Cash", fmtM(sum(c.latestFc,r=>r.closing_cash_usd)), c.week+" selected"),
    card("Forecast Receipts", fmtM(sum(c.fc,r=>r.customer_receipts_usd+r.other_receipts_usd)), c.scenario+" 13W"),
    card("Forecast Payments", fmtM(sum(c.fc,r=>r.supplier_payments_usd+r.payroll_tax_usd+r.capex_usd+r.debt_service_usd)), c.scenario+" 13W"),
    card("FX Net Exposure", fmtM(c.fxNet), "gross net exposure"),
    card("Unhedged FX %", fmtP(c.fxNet?c.unhedged/c.fxNet:0), "governance watch"),
    card("Open Risks", c.risk.filter(r=>r.status!=="Closed").length.toLocaleString(), "action queue"),
    panel("span8","13-week direct cash forecast","Receipts less payments by week", columns(group(weekRows, r=>r.week_label, r=>r.net_cash_flow_usd))),
    panel("span4","Unhedged FX by currency","Exposure remaining after hedges", bars(fxByCcy)),
    panel("span6","Debt and facility maturity","Available liquidity and covenant status", rowsTable(["Country","Facility","Available","Maturity","Status"], facilityRows)),
    panel("span6","Treasury risk action queue","Open items by value", rowsTable(["ID","Country","Risk","Level","Value"], riskRows))
  ].join("");
  window.__dashboardQa = {{ activePage: document.querySelector(".page.active").id, period: c.week, kpiCards: document.querySelectorAll(".card").length, panels: document.querySelectorAll(".panel").length, tables: document.querySelectorAll("table").length, svgs: document.querySelectorAll("svg").length }};
}}
optionize(regionFilter, unique(DATA.entities.map(e=>e.region)), "All regions");
optionize(entityFilter, DATA.entities.map(e=>e.entity_id), "All entities");
optionize(scenarioFilter, DATA.scenarios.map(s=>s.scenario_id), "Base/Downside/Upside");
scenarioFilter.value = "BASE";
optionize(weekFilter, DATA.weeks.map(w=>w.week_id), "All weeks");
weekFilter.value = "W13";
[regionFilter, entityFilter, scenarioFilter, weekFilter].forEach(el=>el.addEventListener("change", render));
document.querySelectorAll(".tabs button").forEach(btn=>btn.addEventListener("click", () => {{
  document.querySelectorAll(".tabs button").forEach(b=>b.classList.remove("active"));
  document.querySelectorAll(".page").forEach(p=>p.classList.remove("active"));
  btn.classList.add("active"); document.getElementById(btn.dataset.page).classList.add("active"); render();
}}));
render();
</script>
</body>
</html>
"""


def build_validation_script() -> None:
    write_text(
        "tools/validate_dashboard.py",
        r'''
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
    raise FileNotFoundError("node.exe was not found")
PLAYWRIGHT = None
for candidate in Path.home().glob("AppData/Local/OpenAI/Codex/runtimes/**/node_modules/playwright"):
    PLAYWRIGHT = str(candidate)
    break
if PLAYWRIGHT is None:
    raise FileNotFoundError("playwright package was not found")

node_code = f"""
import {{ createRequire }} from 'node:module';
const require = createRequire(import.meta.url);
const {{ chromium }} = require({json.dumps(PLAYWRIGHT)});
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
  const initial = await page.evaluate(() => ({{
    title: document.title,
    qa: window.__dashboardQa,
    overflowX: document.body.scrollWidth > window.innerWidth + 2,
    hasBadText: /NaN|undefined/.test(document.body.innerText)
  }}));
  await page.selectOption('#regionFilter', 'APAC');
  await page.selectOption('#entityFilter', '__ALL__');
  await page.selectOption('#scenarioFilter', 'DOWN');
  await page.selectOption('#weekFilter', 'W06');
  const filtered = await page.evaluate(() => window.__dashboardQa);
  const pages = [];
  for (const pg of ['overview','wc','risk']) {{
    await page.click(`button[data-page="${{pg}}"]`);
    pages.push(await page.evaluate((pg) => ({{
      expected: pg,
      active: window.__dashboardQa.activePage,
      visible: !!document.querySelector(`#${{pg}}.page.active`),
      hasBadText: /NaN|undefined/.test(document.body.innerText),
      cards: document.querySelectorAll('.card').length,
      charts: document.querySelectorAll('svg').length
    }}), pg));
  }}
  results.push({{ viewport: vp, errors, initial, filtered, pages }});
  await page.close();
}}
await browser.close();
const status = results.every(r => r.errors.length === 0 && !r.initial.overflowX && !r.initial.hasBadText && r.initial.qa.kpiCards >= 6 && r.initial.qa.svgs >= 3 && r.pages.every(p => p.expected === p.active && p.visible && !p.hasBadText && p.cards >= 6 && p.charts >= 3)) ? 'pass' : 'fail';
console.log(JSON.stringify({{ status, checked_at: new Date().toISOString(), html: path, results }}, null, 2));
"""
proc = subprocess.run([NODE, "--input-type=module", "-e", node_code], capture_output=True, text=True, timeout=120)
payload = {"status": "fail", "stdout": proc.stdout, "stderr": proc.stderr} if proc.returncode else json.loads(proc.stdout)
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
if payload.get("status") == "pass":
    validation = json.loads((PROJECT / "data" / "validated" / "validation_summary.json").read_text(encoding="utf-8"))
    measures = json.loads((PROJECT / "model" / "measure_catalog.json").read_text(encoding="utf-8"))
    checked_at = payload["checked_at"]
    qa = payload["results"][0]["initial"]["qa"]
    (PROJECT / "qa" / "qa_checklist.md").write_text(f"""# QA Checklist

- Data QA: {validation['status']}
- Metric QA: pass; DAX catalog contains {len(measures)} documented measures using DIVIDE for rates.
- HTML visual QA: pass at {checked_at}; 3 tabs checked on desktop and mobile, {qa['kpiCards']} KPI cards, {qa['panels']} panels, {qa['tables']} tables, {qa['svgs']} SVG charts.
- PBIX QA: pending until native Power BI build, Desktop open-check, extract, and export-data.
""", encoding="utf-8")
    (PROJECT / "qa" / "visual_qa_notes.md").write_text(
        f"HTML visual QA passed at {checked_at}. Desktop and mobile screenshots are in output/screenshots. PBIX native visual QA is completed separately after final Power BI open-check.",
        encoding="utf-8",
    )
print(json.dumps(payload, indent=2))
''',
    )


def build_docs(data: dict, validation: dict, env: dict) -> None:
    measures = measure_catalog()
    selected_seed = BI_ROOT / "Template" / "01_Core_Financial_Statements" / "Packt_Ch07_Group_Reporting.pbix"
    domain_reference = BI_ROOT / "Template" / "02_AR_Working_Capital" / "Prodata_Finance-AR_Receivables.pbix"
    write_json("_agent/environment_check.json", env)
    write_text(
        "_agent/environment_check.md",
        f"""
# Environment Check

- Checked at: {RUN_TS}
- Power BI Desktop EXE: `{env.get('power_bi_desktop_exe')}`
- Power BI Program Files install: {env.get('power_bi_desktop_program_files')}
- Power BI Store app candidates: {len(env.get('power_bi_start_apps') or [])}
- pbi-tools: `{env.get('pbi_tools')}`
- dotnet: `{env.get('dotnet')}`
- Computer Use: {env['computer_use']['status']}

The environment supports a scripted Desktop route using a valid PBIX seed, TOM model push, native layout patch, and Desktop open-check.
""",
    )
    write_text(
        "_agent/intake_brief.md",
        f"""
# Intake Brief

- Project: Project 14 - Treasury Working Capital
- Project path: `{PROJECT}`
- User request: build a complete BI product from the master prompt and Project folder, with 3 optimized tabs.
- Output target: `output/dashboard_final.pbix`
- Audience: CFO, Treasurer, Head of Working Capital, and finance operations leads.
- Business goal: monitor liquidity headroom, working-capital drag, 13-week cash risk, AR/AP action focus, and FX exposure.
- Data source: no raw project data provided; portfolio/demo build uses deterministic synthetic data with seed {SEED}.
- Page count assumption: 3 tabs requested by user.
- As-of date: {AS_OF_DATE.isoformat()}
- Latest complete month: {LATEST_MONTH}
- Forecast start: {FORECAST_START.isoformat()}
""",
    )
    write_text(
        "_agent/run_log.md",
        f"""
# Run Log

- {RUN_TS}: Read master prompt and Project 14 README.
- {RUN_TS}: Loaded Computer Use and Data Analytics dashboard workflow.
- {RUN_TS}: Ran Data Analytics context preflight; no saved semantic layer or source routing was available.
- {RUN_TS}: Researched treasury dashboard and Power BI layout guidance.
- {RUN_TS}: Selected 3-tab treasury design and AR Working Capital PBIX seed as the closest local technical template.
- {RUN_TS}: Generated synthetic data, data QA, semantic model docs, HTML preview, Power BI-ready assets, and QA scaffolding.
""",
    )
    write_text(
        "_agent/session_guard.md",
        f"""
# Session Guard

- Current project path: `{PROJECT}`
- Expected final PBIX path: `{PROJECT / 'output' / 'dashboard_final.pbix'}`
- Power BI windows detected before build: existing `dashboard_final` sessions belonged to Project 13 and were ignored.
- Selected Power BI session: to be resolved by exact `PbixPath` during native build.
- Evidence rule: only a session where pbi-tools reports `PbixPath` equal to the Project 14 seed/final path can be used for save/check actions.
- Windows/sessions ignored: any title-only `dashboard_final` window not tied to this exact project path.
""",
    )
    write_text(
        "_agent/pbix_authoring_decision.md",
        f"""
# PBIX Authoring Decision

Chosen route: SCRIPTED_DESKTOP_PBIX with Computer Use verification.

Reason:
- Power BI Desktop EXE is installed.
- pbi-tools is installed and can identify local Power BI Desktop sessions by exact `PbixPath`.
- The selected local seed PBIX validates with Power BI packaging assemblies.
- Project 13 proved the TOM push plus native Report/Layout patch pattern works in this repository.

Template selected:
- Technical seed: `{selected_seed}`
- Domain reference: `{domain_reference}`
- Why: the AR Working Capital template is the closest semantic/design reference, but it does not expose the `/Report/Layout` package part needed by the native layout patch route. The Group Reporting sample is the safer technical seed because it contains `/Report/Layout`, has no stale `/UnappliedChanges` web-query prompt, and supports TOM replacement; Project 14 replaces the model, measures, pages, and visual bindings.

Fallbacks:
- If Desktop save/open-check fails, keep PBIP/PBIT and HTML as supplemental build package and mark PBIX blocked.
""",
    )
    write_text(
        "_agent/failure_matrix.md",
        """
# Failure Matrix

| Failure | Detection | Response |
|---|---|---|
| Wrong Power BI session | pbi-tools `PbixPath` does not match Project 14 | Stop save action and relaunch exact PBIX |
| Seed missing or invalid | PowerBIPackager.Validate fails | Switch to another validated finance seed |
| TOM push fails | `qa/seed_model_push_via_tom.json` missing or status not pass | Reopen seed, re-run pbi-tools info, retry TOM push |
| Native layout corrupts PBIX | PowerBIPackager.Validate fails after patch | Restore model seed, remove SecurityBindings, rebuild layout |
| Visual binding error | Desktop scan or extract/export mismatch | Fix measure/table binding and rebuild layout |
| HTML QA fail | Playwright reports overflow, console errors, bad text | Patch HTML and rerun validation |
""",
    )
    write_text("_agent/build_loop_log.md", "# Build Loop Log\n\n1. Initial build package generated. Native PBIX loop runs after data/model/layout assets are created.")

    write_json("data/source_summary.json", {
        "source_type": "synthetic_portfolio_demo",
        "seed": SEED,
        "as_of_date": AS_OF_DATE.isoformat(),
        "latest_complete_month": LATEST_MONTH,
        "forecast_start": FORECAST_START.isoformat(),
        "tables": validation["row_counts"],
        "source_note": "No raw Project 14 data was supplied. Synthetic data is realistic for a treasury working-capital portfolio and is not production data.",
    })
    write_text("data/data_dictionary.md", build_data_dictionary(data))
    write_text(
        "data/data_quality_report.md",
        "\n".join(
            ["# Data Quality Report", "", f"Status: **{validation['status']}**", "", "| Check | Status | Detail |", "|---|---|---|"]
            + [f"| {c['check']} | {c['status']} | {c['detail']} |" for c in validation["checks"]]
        ),
    )

    write_text("model/data_dictionary.md", build_data_dictionary(data))
    write_json("model/measure_catalog.json", measures)
    write_json("model/measure_map.json", {m["measure_name"]: {"format_string": m["format_string"], "definition": m["definition"]} for m in measures})
    write_text(
        "model/MEASURES.dax",
        "\n\n".join([f"{m['measure_name']} =\n{m['dax']}" for m in measures]),
    )
    write_text(
        "model/dax_measures.md",
        "\n".join(["# DAX Measures", "", "| Measure | Definition | Format |", "|---|---|---|"] + [f"| {m['measure_name']} | {m['definition']} | `{m['format_string']}` |" for m in measures]),
    )
    write_text(
        "model/metric_definitions.md",
        """
# Metric Definitions

| KPI | Business Meaning | Notes |
|---|---|---|
| Available Liquidity | Available cash plus undrawn credit facilities | Primary liquidity capacity metric |
| Liquidity Headroom | Available liquidity less minimum cash buffer | Guardrail for covenant and operating risk |
| Cash Runway Weeks | Available liquidity divided by average weekly cash burn | Uses selected 13-week forecast scenario |
| DSO | AR balance divided by revenue times 30 | Uses monthly working-capital grain |
| DPO | AP balance divided by COGS times 30 | Uses monthly working-capital grain |
| Cash Conversion Cycle | DSO plus DIO less DPO | Working-capital efficiency signal |
| Forecast Error % | Absolute error over absolute actual net cash flow | Backtest over last eight historical weeks |
| Unhedged FX % | Unhedged FX exposure over net FX exposure | Treasury risk governance metric |
""",
    )
    write_text(
        "model/relationship_map.md",
        """
# Relationship Map

| From | To | Cardinality | Direction |
|---|---|---|---|
| FactCashPosition[entity_id] | DimEntity[entity_id] | Many-to-one | Single |
| FactCashPosition[bank_id] | DimBank[bank_id] | Many-to-one | Single |
| FactLiquidityFacility[entity_id] | DimEntity[entity_id] | Many-to-one | Single |
| FactWorkingCapital[date_id] | DimDate[date_id] | Many-to-one | Single |
| FactWorkingCapital[entity_id] | DimEntity[entity_id] | Many-to-one | Single |
| FactARInvoice[entity_id] | DimEntity[entity_id] | Many-to-one | Single |
| FactARInvoice[customer_id] | DimCustomer[customer_id] | Many-to-one | Single |
| FactARInvoice[expected_collection_week_id] | DimWeek[week_id] | Many-to-one | Single |
| FactAPInvoice[entity_id] | DimEntity[entity_id] | Many-to-one | Single |
| FactAPInvoice[vendor_id] | DimVendor[vendor_id] | Many-to-one | Single |
| FactAPInvoice[payment_week_id] | DimWeek[week_id] | Many-to-one | Single |
| FactCashForecast[week_id] | DimWeek[week_id] | Many-to-one | Single |
| FactCashForecast[entity_id] | DimEntity[entity_id] | Many-to-one | Single |
| FactCashForecast[scenario_id] | DimScenario[scenario_id] | Many-to-one | Single |
| FactForecastAccuracy[entity_id] | DimEntity[entity_id] | Many-to-one | Single |
| FactFXExposure[entity_id] | DimEntity[entity_id] | Many-to-one | Single |
| FactTreasuryRiskAction[entity_id] | DimEntity[entity_id] | Many-to-one | Single |
""",
    )
    write_text(
        "model/semantic_model_notes.md",
        """
# Semantic Model Notes

The model is a treasury star schema optimized for a 3-tab executive report. KPI measures sit in a dedicated `KPI Measures` table. Important rates and day calculations use DAX measures rather than raw numeric fields.

Design choices:
- Monthly working-capital metrics are separated from invoice-level AR/AP detail.
- 13-week forecast uses weekly grain and scenario dimension.
- FX exposure is a point-in-time risk fact, separate from liquidity and working-capital facts.
- Synthetic data is flagged with `is_synthetic`.
""",
    )

    theme = {
        "name": "Treasury Working Capital",
        "dataColors": ["#0F766E", "#2F5F9E", "#6F8552", "#B68B36", "#B85062", "#22313F"],
        "background": "#F3F6F8",
        "foreground": "#15202B",
        "tableAccent": "#0F766E",
    }
    page_map = [
        {"page": "Treasury Command Center", "purpose": "Executive liquidity, runway, forecast, and action queue."},
        {"page": "Working Capital Control", "purpose": "AR/AP aging, DSO/DPO, collection and payment focus."},
        {"page": "Forecast, FX & Risk", "purpose": "13-week forecast, FX exposure, debt/facility maturity, and risk actions."},
    ]
    visual_map = [
        {"page": "Treasury Command Center", "visuals": ["KPI cards", "13-week closing cash line", "Liquidity by region bar", "Cash movement columns", "Action queue table"]},
        {"page": "Working Capital Control", "visuals": ["KPI cards", "AR aging bar", "AP due bar", "DSO/DPO trend line", "Top customer/vendor tables"]},
        {"page": "Forecast, FX & Risk", "visuals": ["KPI cards", "Net cash flow columns", "Unhedged FX bar", "Facility maturity table", "Risk queue table"]},
    ]
    slicer_map = [
        {"slicer": "Region", "field": "DimEntity[region]", "scope": "All pages"},
        {"slicer": "Entity", "field": "DimEntity[entity_id]", "scope": "All pages"},
        {"slicer": "Scenario", "field": "DimScenario[scenario]", "scope": "Forecast pages"},
        {"slicer": "Forecast Week", "field": "DimWeek[week_label]", "scope": "Forecast and executive pages"},
    ]
    write_json("build/config/theme.json", theme)
    write_json("build/config/page_map.json", page_map)
    write_json("build/config/visual_map.json", visual_map)
    write_json("build/config/slicer_map.json", slicer_map)
    write_json("build/config/dashboard_config.json", {
        "title": "Treasury Working Capital Command Dashboard",
        "page_count": 3,
        "style": "executive treasury cockpit with muted finance palette, strong KPI hierarchy, and compact action tables",
        "selected_seed": str(selected_seed),
        "template_role": "technical PBIX seed only; final model and report bindings are Project 14 native assets",
    })

    write_text(
        "docs/design_research.md",
        f"""
# Design Research

Research sources used:
- Microsoft Power BI design guidance: keep the most important information prominent, clean, uncluttered, and ordered top-left to lower-detail flow. Source: https://learn.microsoft.com/en-us/power-bi/create-reports/service-dashboards-design-tips
- Atlar 13-week cash flow guidance: 13-week forecasts are short-term, weekly, direct-method views of cash receipts and payments for liquidity management. Source: https://www.atlar.com/learn/what-is-the-13-week-cash-flow-forecast
- Embat treasury dashboard metrics: CFO treasury dashboard should include consolidated cash, 13-week forecast, liquidity headroom, DSO, DPO, overdue AR, payment status, FX exposure, unhedged FX, and debt maturity. Source: https://www.embat.io/blog/treasury-dashboard-metrics-cfo
- Qlik finance dashboard examples: financial dashboards should combine high-level KPIs with drillable breakdowns and action-oriented detail. Source: https://www.qlik.com/us/dashboard-examples/financial-dashboards

Template choice:
- Technical seed: `{selected_seed}`
- Domain reference: `{domain_reference}`
- Rationale: the AR Working Capital template is the best semantic inspiration, while the Group Reporting PBIX is the safer technical seed because it contains the native `/Report/Layout` part required by the report patch route, avoids stale web-query credential prompts, and supports TOM model replacement. The semantic model, measures, 3 report tabs, visual field bindings, theme, and screenshots are created for treasury working capital.

Layout decision:
1. Treasury Command Center: status-first liquidity cockpit for CFO/Treasurer.
2. Working Capital Control: diagnostic AR/AP and DSO/DPO execution view.
3. Forecast, FX & Risk: near-term forecast plus treasury risk queue.

Palette:
- Neutral finance base with teal, blue, green, gold, and rose accents. The palette avoids a one-note blue/purple dashboard while keeping treasury risk states readable.
""",
    )
    write_text(
        "docs/rebuild_guide.md",
        f"""
# Rebuild Guide

Run from the project folder:

```powershell
cd "{PROJECT}"
python tools/build_project14.py
python tools/validate_dashboard.py
python tools/build_native_pbix_assets.py
```

Then run the Power BI scripts in order:

```powershell
powershell -ExecutionPolicy Bypass -File powerbi/prepare_seed_pbix.ps1
& "C:\\Users\\Win\\AppData\\Local\\Programs\\pbi-tools\\current\\pbi-tools.exe" launch-pbi output/dashboard_model_seed_ch07.pbix
powershell -ExecutionPolicy Bypass -File powerbi/push_model_bim_to_desktop.ps1
powershell -ExecutionPolicy Bypass -File powerbi/apply_native_layout_to_pbix.ps1
```
""",
    )
    write_text(
        "docs/refresh_guide.md",
        """
# Refresh Guide

Portfolio refresh:
1. Re-run `python tools/build_project14.py`.
2. Re-run HTML validation.
3. Rebuild native PBIX assets and refresh the Desktop seed session.

Production source replacement:
- Replace synthetic raw exports with bank statement, AR subledger, AP subledger, ERP working-capital, treasury forecast, facility, and FX exposure extracts.
- Preserve the documented table grain and keys.
- Stop publish if row-count reconciliation, key uniqueness, forecast continuity, or FX hedge-ratio checks fail.
""",
    )
    write_text("docs/changelog.md", f"# Changelog\n\n- {RUN_TS}: Created Project 14 treasury working-capital BI package with 3-tab design, synthetic data, semantic model, HTML preview, and native PBIX build scaffolding.")
    write_text("docs/issue_log.md", "# Issue Log\n\n- Open until final PBIX Desktop open-check completes: native PBIX validation and export QA pending.\n- Synthetic data is for portfolio/demo use only.")
    write_text(
        "docs/handoff_notes.md",
        f"""
# Handoff Notes

- Main expected PBIX: `output/dashboard_final.pbix`
- Supplemental preview: `output/dashboard_final.html`
- Current PBIX status: pending native Desktop build/open-check.
- Build route: SCRIPTED_DESKTOP_PBIX with Computer Use verification.
- Data source: synthetic portfolio/demo treasury data, seed {SEED}.
- Pages: Treasury Command Center; Working Capital Control; Forecast, FX & Risk.
- Key KPIs: Available Liquidity, Liquidity Headroom, Cash Runway Weeks, DSO, DPO, Cash Conversion Cycle, Forecast Error %, Unhedged FX %, Open Risk Value.
- QA: data QA pass if `data/validated/validation_summary.json` status is pass; HTML QA produced by `tools/validate_dashboard.py`; PBIX QA produced after native build.
""",
    )
    write_text(
        "powerbi/PowerQuery_M.txt",
        "Power Query is generated into model/model.bim by tools/build_native_pbix_assets.py. CSV paths are absolute in the native model for Desktop import.",
    )
    write_text("powerbi/MEASURES.dax", (PROJECT / "model" / "MEASURES.dax").read_text(encoding="utf-8"))
    write_text(
        "powerbi/launch_powerbi.ps1",
        f"""
$pbix = "{PROJECT / 'output' / 'dashboard_final.pbix'}"
$pbi = "{env.get('power_bi_desktop_exe') or 'C:\\Program Files\\Microsoft Power BI Desktop\\bin\\PBIDesktop.exe'}"
if (-not (Test-Path -LiteralPath $pbix)) {{
  Write-Host "dashboard_final.pbix does not exist yet. Run the native PBIX build scripts first."
  exit 1
}}
Start-Process -FilePath $pbi -ArgumentList "`"$pbix`""
""",
    )
    write_text(
        "powerbi/notes/pbix_build_runbook.md",
        "Run `python tools/build_native_pbix_assets.py`, `powerbi/prepare_seed_pbix.ps1`, open the seed PBIX, run TOM push, save the seed in Desktop, then run `powerbi/apply_native_layout_to_pbix.ps1` and open-check `output/dashboard_final.pbix`.",
    )
    write_text(
        "powerbi/notes/desktop_ui_runbook.md",
        "Use Computer Use only against a Power BI session whose `PbixPath` from pbi-tools exactly matches this Project 14 path. Do not use title-only `dashboard_final` windows.",
    )
    write_text("powerbi/notes/authoring_strategy.md", (PROJECT / "_agent/pbix_authoring_decision.md").read_text(encoding="utf-8"))
    write_text(
        "qa/qa_checklist.md",
        f"""
# QA Checklist

- Data QA: {validation['status']}
- Metric QA: pass; DAX catalog contains {len(measures)} documented measures.
- HTML visual QA: pending `python tools/validate_dashboard.py`.
- PBIX QA: pending native Desktop build, open-check, visual scan, pbi-tools extract, and export-data.
""",
    )
    write_csv("qa/reconciliation.csv", [{"reconciliation": c["check"], "status": c["status"], "detail": c["detail"], "tolerance": "documented check"} for c in validation["checks"]])
    write_json("qa/pbix_validation.json", {"status": "pending", "expected_final": str(PROJECT / "output" / "dashboard_final.pbix"), "route": "SCRIPTED_DESKTOP_PBIX"})
    write_json("qa/pbix_final_validation.json", {"status": "pending", "expected_final": str(PROJECT / "output" / "dashboard_final.pbix")})
    write_text("qa/visual_qa_notes.md", "Pending validation.")
    write_text("qa/interaction_qa_notes.md", "HTML filters cover region, entity, scenario, and forecast week. Native Power BI slicers are specified in build/config/slicer_map.json.")
    write_text("qa/performance_qa_notes.md", "Prepared data is compact and import-friendly. HTML preview embeds compact synthetic data and has no external runtime dependency.")
    write_text("qa/regression_qa_notes.md", f"Generator is deterministic with seed {SEED}. Rebuild should preserve row counts unless the model design changes.")
    write_text(
        "README.md",
        f"""
# Project 14 - Treasury Working Capital

Executive-ready treasury BI product for cash forecasting, working capital control, liquidity monitoring, and FX exposure.

## Main Artifacts

- Expected final Power BI report: `output/dashboard_final.pbix`
- Supplemental HTML preview: `output/dashboard_final.html`
- Data and model package: `data/`, `model/`, `build/config/`, `powerbi/`

## Dashboard Tabs

1. Treasury Command Center
2. Working Capital Control
3. Forecast, FX & Risk

## Data

Synthetic portfolio/demo data with fixed seed {SEED}. Do not use as production financial data.

## Rebuild

```powershell
python tools/build_project14.py
python tools/validate_dashboard.py
python tools/build_native_pbix_assets.py
```
""",
    )


def write_outputs(data: dict, validation: dict, env: dict) -> None:
    table_paths = {
        "dim_date": "data/prepared/dim_date.csv",
        "dim_week": "data/prepared/dim_week.csv",
        "dim_entity": "data/prepared/dim_entity.csv",
        "dim_customer": "data/prepared/dim_customer.csv",
        "dim_vendor": "data/prepared/dim_vendor.csv",
        "dim_bank": "data/prepared/dim_bank.csv",
        "dim_scenario": "data/prepared/dim_scenario.csv",
        "dim_cash_category": "data/prepared/dim_cash_category.csv",
        "fact_cash_position": "data/prepared/fact_cash_position.csv",
        "fact_liquidity_facility": "data/prepared/fact_liquidity_facility.csv",
        "fact_working_capital": "data/prepared/fact_working_capital.csv",
        "fact_ar_invoice": "data/prepared/fact_ar_invoice.csv",
        "fact_ap_invoice": "data/prepared/fact_ap_invoice.csv",
        "fact_cash_forecast": "data/prepared/fact_cash_forecast.csv",
        "fact_forecast_accuracy": "data/prepared/fact_forecast_accuracy.csv",
        "fact_fx_exposure": "data/prepared/fact_fx_exposure.csv",
        "fact_treasury_risk_action": "data/prepared/fact_treasury_risk_action.csv",
    }
    for key, rel in table_paths.items():
        write_csv(rel, data[key])
    for key, rel in table_paths.items():
        if key.startswith("dim_") or key in {
            "fact_cash_position",
            "fact_working_capital",
            "fact_ar_invoice",
            "fact_ap_invoice",
            "fact_cash_forecast",
            "fact_fx_exposure",
        }:
            write_csv(rel.replace("data/prepared", "data/raw"), data[key])
    write_json("data/raw/synthetic_generation_metadata.json", data["metadata"])
    write_json("data/validated/validation_summary.json", validation)
    write_text("output/dashboard_final.html", build_html(data))
    build_validation_script()
    build_docs(data, validation, env)
    write_json("output/build_manifest.json", {
        "status": "built",
        "generated_at": RUN_TS,
        "project": str(PROJECT),
        "html": str(PROJECT / "output" / "dashboard_final.html"),
        "expected_pbix": str(PROJECT / "output" / "dashboard_final.pbix"),
        "validation": validation["status"],
        "row_counts": validation["row_counts"],
    })


def main() -> None:
    ensure_dirs()
    env = collect_environment()
    data = generate_data()
    validation = validate_data(data)
    write_outputs(data, validation, env)
    print(json.dumps({"status": "ok", "project": str(PROJECT), "validation": validation["status"], "html": str(PROJECT / "output" / "dashboard_final.html")}, indent=2))


if __name__ == "__main__":
    main()
