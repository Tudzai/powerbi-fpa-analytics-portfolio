from __future__ import annotations

import csv
import math
import random
from datetime import date
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = PROJECT_ROOT / "data" / "raw"

random.seed(20260608)


BUSINESS_UNITS = [
    {"BusinessUnit": "Freight Forwarding", "BUCode": "FF"},
    {"BusinessUnit": "Contract Logistics", "BUCode": "CL"},
    {"BusinessUnit": "Customs Brokerage", "BUCode": "CB"},
    {"BusinessUnit": "E-commerce Fulfillment", "BUCode": "EC"},
]

PRODUCTS_BY_BU = {
    "Freight Forwarding": ["Air Freight", "Ocean Freight", "Road Freight"],
    "Contract Logistics": ["Warehousing", "Value Added Services"],
    "Customs Brokerage": ["Customs Clearance", "Trade Compliance"],
    "E-commerce Fulfillment": ["Fulfillment", "Last Mile"],
}

REGIONS = ["North", "Central", "South", "Overseas"]

CUSTOMERS = [
    ("Aster Retail Group", "Strategic", "Retail"),
    ("Bluewave Electronics", "Strategic", "Electronics"),
    ("Cobalt Manufacturing", "Enterprise", "Industrial"),
    ("Delta Pharma", "Enterprise", "Healthcare"),
    ("Evergreen Foods", "Enterprise", "FMCG"),
    ("Futura Apparel", "Enterprise", "Fashion"),
    ("GreenMart Online", "Growth", "E-commerce"),
    ("Helio Auto Parts", "Growth", "Automotive"),
    ("Indigo Home", "Growth", "Home Goods"),
    ("Jade Coffee", "SMB", "FMCG"),
    ("Kite Cosmetics", "SMB", "Beauty"),
    ("Long Tail Customers", "SMB", "Mixed"),
]

DEPARTMENTS = [
    ("Sales & Marketing", 0.22),
    ("Operations", 0.42),
    ("Finance", 0.12),
    ("People & Admin", 0.14),
    ("Technology", 0.10),
]


def month_range(start_year: int, start_month: int, end_year: int, end_month: int) -> list[date]:
    months: list[date] = []
    year = start_year
    month = start_month
    while (year, month) <= (end_year, end_month):
        months.append(date(year, month, 1))
        month += 1
        if month == 13:
            month = 1
            year += 1
    return months


def scenario_months() -> list[tuple[str, date]]:
    rows: list[tuple[str, date]] = []
    for month in month_range(2025, 1, 2026, 5):
        rows.append(("Actual", month))
    for month in month_range(2026, 1, 2026, 12):
        rows.append(("Budget", month))
    for month in month_range(2026, 1, 2026, 12):
        rows.append(("Forecast", month))
    return rows


def seasonality(month: date) -> float:
    # Logistics activity is usually stronger around Q4 and softer in February.
    m = month.month
    return {
        1: 0.94,
        2: 0.86,
        3: 1.02,
        4: 1.00,
        5: 1.03,
        6: 1.04,
        7: 1.07,
        8: 1.06,
        9: 1.10,
        10: 1.16,
        11: 1.20,
        12: 1.24,
    }[m]


def trend_factor(month: date) -> float:
    month_index = (month.year - 2025) * 12 + month.month - 1
    return 1 + month_index * 0.008


def scenario_factor(scenario: str, month: date, base_actual: float) -> float:
    if scenario == "Budget":
        return base_actual * 1.055
    if scenario == "Forecast":
        # Forecast is updated after actual YTD: near actual in closed months,
        # lower than original budget in H2 due to a softer enterprise pipeline.
        h2_softness = 0.965 if month.month >= 7 else 0.99
        return base_actual * 1.035 * h2_softness
    return base_actual


def customer_weight(customer: str) -> float:
    weights = {
        "Aster Retail Group": 1.38,
        "Bluewave Electronics": 1.27,
        "Cobalt Manufacturing": 1.12,
        "Delta Pharma": 1.06,
        "Evergreen Foods": 0.98,
        "Futura Apparel": 0.90,
        "GreenMart Online": 0.86,
        "Helio Auto Parts": 0.79,
        "Indigo Home": 0.73,
        "Jade Coffee": 0.58,
        "Kite Cosmetics": 0.53,
        "Long Tail Customers": 1.45,
    }
    return weights[customer]


def product_base(product: str) -> float:
    values = {
        "Air Freight": 1_250_000,
        "Ocean Freight": 1_520_000,
        "Road Freight": 760_000,
        "Warehousing": 980_000,
        "Value Added Services": 620_000,
        "Customs Clearance": 520_000,
        "Trade Compliance": 360_000,
        "Fulfillment": 880_000,
        "Last Mile": 690_000,
    }
    return values[product]


def margin_rate(product: str, scenario: str, month: date) -> float:
    base = {
        "Air Freight": 0.235,
        "Ocean Freight": 0.275,
        "Road Freight": 0.210,
        "Warehousing": 0.335,
        "Value Added Services": 0.385,
        "Customs Clearance": 0.420,
        "Trade Compliance": 0.455,
        "Fulfillment": 0.315,
        "Last Mile": 0.245,
    }[product]
    if scenario == "Budget":
        base += 0.012
    if scenario == "Forecast":
        base -= 0.004 if month.month >= 7 else 0.000
    if month.year == 2026 and month.month in (3, 4, 5):
        base -= 0.009
    return base


def opex_rate(product: str, scenario: str, month: date) -> float:
    base = {
        "Air Freight": 0.142,
        "Ocean Freight": 0.128,
        "Road Freight": 0.156,
        "Warehousing": 0.188,
        "Value Added Services": 0.202,
        "Customs Clearance": 0.168,
        "Trade Compliance": 0.182,
        "Fulfillment": 0.196,
        "Last Mile": 0.224,
    }[product]
    if scenario == "Budget":
        base -= 0.006
    if scenario == "Forecast" and month.month >= 6:
        base += 0.004
    if month.year == 2026 and month.month in (4, 5):
        base += 0.008
    return base


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def generate_financials() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    record_id = 1
    for scenario, month in scenario_months():
        for bu in BUSINESS_UNITS:
            for product in PRODUCTS_BY_BU[bu["BusinessUnit"]]:
                for region in REGIONS:
                    region_factor = {"North": 0.86, "Central": 0.58, "South": 1.12, "Overseas": 0.72}[region]
                    for customer, segment, industry in CUSTOMERS:
                        base = product_base(product)
                        actual_base = base * region_factor * customer_weight(customer) * seasonality(month) * trend_factor(month)
                        actual_base *= 1 + random.uniform(-0.055, 0.055)
                        revenue = scenario_factor(scenario, month, actual_base)
                        # Intentional FP&A story: 2026 May has revenue pressure in Contract Logistics.
                        if scenario == "Actual" and month == date(2026, 5, 1) and bu["BusinessUnit"] == "Contract Logistics":
                            revenue *= 0.925
                        # Ocean freight recovers ahead of budget in South.
                        if scenario == "Actual" and month == date(2026, 5, 1) and product == "Ocean Freight" and region == "South":
                            revenue *= 1.075
                        margin = margin_rate(product, scenario, month)
                        gross_margin = revenue * margin
                        cogs = revenue - gross_margin
                        allocated_opex = revenue * opex_rate(product, scenario, month)
                        ebitda = gross_margin - allocated_opex
                        orders = max(1, int((revenue / 18_500) * random.uniform(0.82, 1.16)))
                        cash_impact = ebitda - revenue * random.uniform(0.018, 0.036)
                        rows.append(
                            {
                                "RecordID": f"F{record_id:07d}",
                                "MonthStart": month.isoformat(),
                                "Scenario": scenario,
                                "BusinessUnit": bu["BusinessUnit"],
                                "Product": product,
                                "Region": region,
                                "Customer": customer,
                                "CustomerSegment": segment,
                                "Industry": industry,
                                "Revenue": round(revenue, 2),
                                "COGS": round(cogs, 2),
                                "GrossMargin": round(gross_margin, 2),
                                "AllocatedOpex": round(allocated_opex, 2),
                                "EBITDA": round(ebitda, 2),
                                "Orders": orders,
                                "CashImpact": round(cash_impact, 2),
                            }
                        )
                        record_id += 1
    return rows


def aggregate(rows: list[dict[str, object]], keys: list[str], measures: list[str]) -> dict[tuple[object, ...], dict[str, float]]:
    grouped: dict[tuple[object, ...], dict[str, float]] = {}
    for row in rows:
        key = tuple(row[k] for k in keys)
        grouped.setdefault(key, {m: 0.0 for m in measures})
        for measure in measures:
            grouped[key][measure] += float(row[measure])
    return grouped


def generate_opex(financials: list[dict[str, object]]) -> list[dict[str, object]]:
    keys = ["MonthStart", "Scenario", "BusinessUnit", "Region"]
    grouped = aggregate(financials, keys, ["AllocatedOpex"])
    rows: list[dict[str, object]] = []
    for key, values in grouped.items():
        month_start, scenario, bu, region = key
        total = values["AllocatedOpex"]
        for department, weight in DEPARTMENTS:
            noise = 1 + random.uniform(-0.035, 0.035)
            opex = total * weight * noise
            rows.append(
                {
                    "MonthStart": month_start,
                    "Scenario": scenario,
                    "BusinessUnit": bu,
                    "Region": region,
                    "Department": department,
                    "Opex": round(opex, 2),
                    "FTE": round((opex / 42_000) * random.uniform(0.94, 1.08), 1),
                }
            )
    return rows


def generate_cash(financials: list[dict[str, object]]) -> list[dict[str, object]]:
    keys = ["MonthStart", "Scenario", "BusinessUnit", "Region"]
    grouped = aggregate(financials, keys, ["Revenue", "EBITDA", "CashImpact"])
    rows: list[dict[str, object]] = []
    opening_cash = {
        ("Freight Forwarding", "North"): 8_800_000,
        ("Freight Forwarding", "Central"): 4_700_000,
        ("Freight Forwarding", "South"): 9_900_000,
        ("Freight Forwarding", "Overseas"): 6_200_000,
        ("Contract Logistics", "North"): 5_300_000,
        ("Contract Logistics", "Central"): 3_100_000,
        ("Contract Logistics", "South"): 7_400_000,
        ("Contract Logistics", "Overseas"): 2_900_000,
        ("Customs Brokerage", "North"): 2_400_000,
        ("Customs Brokerage", "Central"): 1_600_000,
        ("Customs Brokerage", "South"): 3_200_000,
        ("Customs Brokerage", "Overseas"): 1_800_000,
        ("E-commerce Fulfillment", "North"): 3_900_000,
        ("E-commerce Fulfillment", "Central"): 2_500_000,
        ("E-commerce Fulfillment", "South"): 5_100_000,
        ("E-commerce Fulfillment", "Overseas"): 1_200_000,
    }
    running = {k: v for k, v in opening_cash.items()}
    sorted_items = sorted(grouped.items(), key=lambda item: (item[0][1], item[0][0], item[0][2], item[0][3]))
    for key, values in sorted_items:
        month_start, scenario, bu, region = key
        month = date.fromisoformat(str(month_start))
        base_key = (str(bu), str(region))
        if scenario != "Actual":
            scenario_multiplier = 1.03 if scenario == "Budget" else 1.015
            cash_balance = opening_cash[base_key] * scenario_multiplier + values["CashImpact"] * 0.055 * month.month
        else:
            running[base_key] += values["CashImpact"] * 0.082
            cash_balance = running[base_key]
        dso = 42 + 5 * math.sin(month.month / 12 * math.tau) + random.uniform(-2.4, 2.4)
        ar_balance = values["Revenue"] / 30 * max(25, dso)
        capex = values["Revenue"] * random.uniform(0.012, 0.026)
        rows.append(
            {
                "MonthStart": month_start,
                "Scenario": scenario,
                "BusinessUnit": bu,
                "Region": region,
                "CashBalance": round(cash_balance, 2),
                "ARBalance": round(ar_balance, 2),
                "DSO": round(dso, 1),
                "Capex": round(capex, 2),
            }
        )
    return rows


def generate_bridge(financials: list[dict[str, object]]) -> list[dict[str, object]]:
    target_month = "2026-05-01"
    measures = ["Revenue", "GrossMargin", "AllocatedOpex", "EBITDA"]
    grouped = aggregate(
        [r for r in financials if r["MonthStart"] == target_month and r["Scenario"] in ("Actual", "Budget")],
        ["BusinessUnit", "Region", "Scenario"],
        measures,
    )
    rows: list[dict[str, object]] = []
    steps = [
        ("Budget EBITDA", 1),
        ("Revenue volume/mix", 2),
        ("Price/rate", 3),
        ("COGS productivity", 4),
        ("Opex control", 5),
        ("FX and other", 6),
        ("Actual EBITDA", 7),
    ]
    for bu in [b["BusinessUnit"] for b in BUSINESS_UNITS]:
        for region in REGIONS:
            budget = grouped[(bu, region, "Budget")]
            actual = grouped[(bu, region, "Actual")]
            ebitda_var = actual["EBITDA"] - budget["EBITDA"]
            revenue_var = actual["Revenue"] - budget["Revenue"]
            gm_rate_budget = budget["GrossMargin"] / budget["Revenue"] if budget["Revenue"] else 0
            gm_rate_actual = actual["GrossMargin"] / actual["Revenue"] if actual["Revenue"] else 0
            volume_mix = revenue_var * gm_rate_budget
            price_rate = actual["Revenue"] * (gm_rate_actual - gm_rate_budget)
            cogs_productivity = (actual["GrossMargin"] - budget["GrossMargin"]) - volume_mix - price_rate
            opex_control = -(actual["AllocatedOpex"] - budget["AllocatedOpex"])
            fx_other = ebitda_var - volume_mix - price_rate - cogs_productivity - opex_control
            values = {
                "Budget EBITDA": budget["EBITDA"],
                "Revenue volume/mix": volume_mix,
                "Price/rate": price_rate,
                "COGS productivity": cogs_productivity,
                "Opex control": opex_control,
                "FX and other": fx_other,
                "Actual EBITDA": actual["EBITDA"],
            }
            for step, order in steps:
                rows.append(
                    {
                        "MonthStart": target_month,
                        "BusinessUnit": bu,
                        "Region": region,
                        "BridgeStep": step,
                        "BridgeOrder": order,
                        "Amount": round(values[step], 2),
                    }
                )
    return rows


def generate_commentary() -> list[dict[str, object]]:
    return [
        {
            "MonthStart": "2026-05-01",
            "Audience": "CFO / FP&A Monthly Review",
            "WhatHappened": "Revenue finished below budget, mainly from Contract Logistics softness, while Ocean Freight South partly offset the gap.",
            "Why": "Enterprise renewal delays and higher last-mile handling cost compressed EBITDA versus budget. Customs Brokerage stayed resilient with healthy margin mix.",
            "WhatNext": "Prioritize CL renewal actions, tighten last-mile productivity, and protect Ocean Freight pricing through Q3 forecast refresh.",
            "Severity": "Watch",
        },
        {
            "MonthStart": "2026-04-01",
            "Audience": "CFO / FP&A Monthly Review",
            "WhatHappened": "EBITDA trailed budget despite revenue being broadly in line.",
            "Why": "Temporary labor and warehouse utilities pushed Opex above plan.",
            "WhatNext": "Track overtime, rebid short-term labor suppliers, and update run-rate assumptions for June forecast.",
            "Severity": "Watch",
        },
        {
            "MonthStart": "2026-03-01",
            "Audience": "CFO / FP&A Monthly Review",
            "WhatHappened": "Gross margin improved sequentially but remained below the annual budget rate.",
            "Why": "Air Freight mix recovered, but cost inflation remained visible in South and Overseas lanes.",
            "WhatNext": "Push lane-level repricing and monitor customer margin exceptions weekly.",
            "Severity": "Normal",
        },
    ]


def main() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    financials = generate_financials()
    opex = generate_opex(financials)
    cash = generate_cash(financials)
    bridge = generate_bridge(financials)
    commentary = generate_commentary()

    write_csv(
        RAW_DIR / "raw_fpa_financials.csv",
        financials,
        [
            "RecordID",
            "MonthStart",
            "Scenario",
            "BusinessUnit",
            "Product",
            "Region",
            "Customer",
            "CustomerSegment",
            "Industry",
            "Revenue",
            "COGS",
            "GrossMargin",
            "AllocatedOpex",
            "EBITDA",
            "Orders",
            "CashImpact",
        ],
    )
    write_csv(
        RAW_DIR / "raw_fpa_opex_department.csv",
        opex,
        ["MonthStart", "Scenario", "BusinessUnit", "Region", "Department", "Opex", "FTE"],
    )
    write_csv(
        RAW_DIR / "raw_fpa_cash.csv",
        cash,
        ["MonthStart", "Scenario", "BusinessUnit", "Region", "CashBalance", "ARBalance", "DSO", "Capex"],
    )
    write_csv(
        RAW_DIR / "raw_fpa_budget_actual_bridge.csv",
        bridge,
        ["MonthStart", "BusinessUnit", "Region", "BridgeStep", "BridgeOrder", "Amount"],
    )
    write_csv(
        RAW_DIR / "raw_monthly_commentary.csv",
        commentary,
        ["MonthStart", "Audience", "WhatHappened", "Why", "WhatNext", "Severity"],
    )
    print(f"Generated raw FP&A sample data in {RAW_DIR}")


if __name__ == "__main__":
    main()
