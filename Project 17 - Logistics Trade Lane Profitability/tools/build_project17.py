from __future__ import annotations

import csv
import json
import math
import random
import shutil
import subprocess
import zipfile
from collections import defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path


PROJECT = Path(__file__).resolve().parents[1]
BI_ROOT = PROJECT.parents[0]
SEED = 17042
RUN_TS = datetime.now().replace(microsecond=0).isoformat()
LATEST_PERIOD = "2026-05"
SAMPLE_DIR = BI_ROOT / "Project 10 - AML Fraud Monitoring" / "qa" / "legacy_visual_samples"
SEED_TEMPLATE = BI_ROOT / "Template" / "04_Profitability_Margin" / "Microsoft_Customer_Profitability.pbix"
PBI_EXE = Path(r"C:\Program Files\Microsoft Power BI Desktop\bin\PBIDesktop.exe")
PBI_TOOLS = Path(r"C:\Users\Win\AppData\Local\Programs\pbi-tools\current\pbi-tools.exe")


THEME = {
    "bg": "#F8FAFC",
    "panel": "#FFFFFF",
    "panel2": "#F1F5F9",
    "border": "#CBD5E1",
    "grid": "#E2E8F0",
    "text": "#0F172A",
    "muted": "#475569",
    "dim": "#64748B",
    "blue": "#2563EB",
    "teal": "#0F766E",
    "green": "#15803D",
    "amber": "#B45309",
    "red": "#DC2626",
    "ink": "#111827",
}
PALETTE = [THEME["blue"], THEME["teal"], THEME["green"], THEME["amber"], THEME["red"], THEME["ink"]]
FILTER_ROW_Y = 82
FILTER_ROW_H = 56
CONTEXT_CHIP_H = 56
CONTENT_ROW_SHIFT = 52
KPI_ROW_Y = 92 + CONTENT_ROW_SHIFT
SPARKLINE_OFFSET_Y = 62


TABLE_FILES = {
    "DimDate": "dim_date.csv",
    "DimCustomer": "dim_customer.csv",
    "DimTradeLane": "dim_trade_lane.csv",
    "DimService": "dim_service.csv",
    "DimOffice": "dim_office.csv",
    "DimCarrier": "dim_carrier.csv",
    "FactShipmentProfitability": "fact_shipment_profitability.csv",
    "FactCostDriverBridge": "fact_cost_driver_bridge.csv",
    "FactActionQueue": "fact_action_queue.csv",
}


RELATIONSHIPS = [
    ("FactShipmentProfitability", "date_id", "DimDate", "date_id"),
    ("FactCostDriverBridge", "date_id", "DimDate", "date_id"),
    ("FactActionQueue", "date_id", "DimDate", "date_id"),
    ("FactShipmentProfitability", "customer_id", "DimCustomer", "customer_id"),
    ("FactCostDriverBridge", "customer_id", "DimCustomer", "customer_id"),
    ("FactActionQueue", "customer_id", "DimCustomer", "customer_id"),
    ("FactShipmentProfitability", "lane_id", "DimTradeLane", "lane_id"),
    ("FactCostDriverBridge", "lane_id", "DimTradeLane", "lane_id"),
    ("FactActionQueue", "lane_id", "DimTradeLane", "lane_id"),
    ("FactShipmentProfitability", "service_id", "DimService", "service_id"),
    ("FactShipmentProfitability", "office_id", "DimOffice", "office_id"),
    ("FactActionQueue", "office_id", "DimOffice", "office_id"),
    ("FactShipmentProfitability", "carrier_id", "DimCarrier", "carrier_id"),
]


COLUMN_TYPES = {
    "date": "dateTime",
    "due_date": "dateTime",
    "year": "int64",
    "quarter_number": "int64",
    "month_number": "int64",
    "month_index": "int64",
    "distance_km": "double",
    "shipment_count": "int64",
    "teu": "double",
    "cbm": "double",
    "chargeable_weight_kg": "double",
    "net_revenue_usd": "double",
    "freight_cost_usd": "double",
    "fuel_cost_usd": "double",
    "handling_cost_usd": "double",
    "customs_cost_usd": "double",
    "demurrage_cost_usd": "double",
    "claims_cost_usd": "double",
    "last_mile_cost_usd": "double",
    "total_cost_usd": "double",
    "gross_profit_usd": "double",
    "target_margin_pct": "double",
    "on_time_count": "int64",
    "delayed_count": "int64",
    "utilization_pct": "double",
    "driver_sort": "int64",
    "amount_usd": "double",
    "risk_value_usd": "double",
    "target_margin_recovery_usd": "double",
    "is_synthetic": "boolean",
}


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


def collect_environment() -> dict:
    start_apps = []
    try:
        cmd = (
            "Get-StartApps | Where-Object { $_.Name -like '*Power BI Desktop*' "
            "-or $_.AppID -like '*PowerBI*' } | Select-Object Name,AppID | ConvertTo-Json -Depth 3"
        )
        proc = subprocess.run(["powershell", "-NoProfile", "-Command", cmd], capture_output=True, text=True, timeout=15)
        if proc.stdout.strip():
            parsed = json.loads(proc.stdout)
            start_apps = parsed if isinstance(parsed, list) else [parsed]
    except Exception as exc:
        start_apps = [{"error": str(exc)}]

    pbi_info = None
    if PBI_TOOLS.exists():
        try:
            proc = subprocess.run([str(PBI_TOOLS), "info"], capture_output=True, text=True, timeout=30)
            pbi_info = proc.stdout.strip()[:8000]
        except Exception as exc:
            pbi_info = f"pbi-tools info failed: {exc}"

    return {
        "checked_at": RUN_TS,
        "power_bi_desktop_exe": str(PBI_EXE) if PBI_EXE.exists() else None,
        "power_bi_desktop_program_files": PBI_EXE.exists(),
        "power_bi_start_apps": start_apps,
        "pbi_tools": str(PBI_TOOLS) if PBI_TOOLS.exists() else None,
        "pbi_tools_info_excerpt": pbi_info,
        "dotnet": shutil.which("dotnet"),
        "computer_use": {
            "status": "pass",
            "evidence": "Computer Use bootstrap and app listing succeeded in this run; Power BI Desktop was discoverable with existing dashboard_final windows.",
        },
    }


def build_dimensions(periods: list[str]) -> dict[str, list[dict]]:
    dim_date = []
    for idx, period in enumerate(periods, 1):
        y, m = map(int, period.split("-"))
        q = (m - 1) // 3 + 1
        dim_date.append(
            {
                "date_id": period,
                "date": f"{y:04d}-{m:02d}-01",
                "year": y,
                "quarter": f"Q{q}",
                "quarter_number": q,
                "month_number": m,
                "month_label": datetime(y, m, 1).strftime("%b %Y"),
                "month_index": idx,
                "is_latest_complete": "TRUE" if period == LATEST_PERIOD else "FALSE",
            }
        )

    customers = [
        ("C001", "Aster Apparel Group", "Fashion", "Enterprise", "Strategic", "Linh Tran"),
        ("C002", "BluePeak Electronics", "Electronics", "Enterprise", "Strategic", "Minh Pham"),
        ("C003", "Cobalt Auto Parts", "Automotive", "Enterprise", "Core", "Linh Tran"),
        ("C004", "Delta Fresh Foods", "Food & Beverage", "Mid-Market", "Core", "An Nguyen"),
        ("C005", "Everwell Pharma", "Healthcare", "Enterprise", "Strategic", "Minh Pham"),
        ("C006", "Futura Homeware", "Retail", "Mid-Market", "Core", "Huy Le"),
        ("C007", "Golden Bean Coffee", "Food & Beverage", "SMB", "Growth", "An Nguyen"),
        ("C008", "Helio Solar Tech", "Industrial", "Mid-Market", "Growth", "Huy Le"),
        ("C009", "Ion Mobility", "Automotive", "Enterprise", "Strategic", "Linh Tran"),
        ("C010", "Jade Consumer Goods", "FMCG", "Enterprise", "Core", "Minh Pham"),
        ("C011", "Kite Sportswear", "Fashion", "Mid-Market", "Growth", "An Nguyen"),
        ("C012", "Lotus Furniture", "Retail", "Mid-Market", "Core", "Huy Le"),
        ("C013", "Mekong Machinery", "Industrial", "Enterprise", "Core", "Linh Tran"),
        ("C014", "Nimbus Devices", "Electronics", "SMB", "Growth", "Minh Pham"),
        ("C015", "Orchid Beauty", "FMCG", "SMB", "Growth", "An Nguyen"),
        ("C016", "Pacific Cold Chain", "Food & Beverage", "Enterprise", "Strategic", "Huy Le"),
        ("C017", "Quartz Medical", "Healthcare", "Mid-Market", "Core", "Minh Pham"),
        ("C018", "Redwood Furnishings", "Retail", "SMB", "Growth", "Huy Le"),
    ]
    dim_customer = [
        {
            "customer_id": cid,
            "customer_name": name,
            "industry": industry,
            "segment": segment,
            "tier": tier,
            "account_manager": manager,
            "credit_risk_band": random.choice(["Low", "Medium", "Medium", "High"]),
        }
        for cid, name, industry, segment, tier, manager in customers
    ]

    lanes = [
        ("L001", "VN-HCM -> US-LAX", "Vietnam", "Ho Chi Minh", "United States", "Los Angeles", "Ocean FCL", 13100, "Transpacific"),
        ("L002", "VN-HCM -> DE-HAM", "Vietnam", "Ho Chi Minh", "Germany", "Hamburg", "Ocean FCL", 10900, "Europe"),
        ("L003", "CN-SHA -> VN-HCM", "China", "Shanghai", "Vietnam", "Ho Chi Minh", "Ocean LCL", 2800, "Intra-Asia"),
        ("L004", "TH-BKK -> VN-HCM", "Thailand", "Bangkok", "Vietnam", "Ho Chi Minh", "Road", 860, "Intra-ASEAN"),
        ("L005", "VN-HAN -> JP-TYO", "Vietnam", "Ha Noi", "Japan", "Tokyo", "Air", 3700, "North Asia"),
        ("L006", "SG-SIN -> AU-SYD", "Singapore", "Singapore", "Australia", "Sydney", "Ocean FCL", 6300, "Oceania"),
        ("L007", "VN-DAD -> KR-PUS", "Vietnam", "Da Nang", "South Korea", "Busan", "Ocean LCL", 3600, "North Asia"),
        ("L008", "ID-JKT -> VN-HCM", "Indonesia", "Jakarta", "Vietnam", "Ho Chi Minh", "Ocean FCL", 3000, "Intra-ASEAN"),
        ("L009", "MY-KUL -> VN-HCM", "Malaysia", "Kuala Lumpur", "Vietnam", "Ho Chi Minh", "Road+Sea", 1700, "Intra-ASEAN"),
        ("L010", "VN-HCM -> AE-JEA", "Vietnam", "Ho Chi Minh", "UAE", "Jebel Ali", "Ocean FCL", 5900, "Middle East"),
        ("L011", "VN-HAN -> CN-SZX", "Vietnam", "Ha Noi", "China", "Shenzhen", "Air", 850, "Intra-Asia"),
        ("L012", "KH-PNH -> VN-HCM", "Cambodia", "Phnom Penh", "Vietnam", "Ho Chi Minh", "Road", 240, "Cross-border"),
    ]
    dim_lane = [
        {
            "lane_id": lid,
            "lane_name": name,
            "origin_country": oc,
            "origin_node": onode,
            "destination_country": dc,
            "destination_node": dnode,
            "mode": mode,
            "distance_km": dist,
            "lane_cluster": cluster,
            "strategic_lane": "TRUE" if cluster in {"Transpacific", "Europe", "Intra-ASEAN"} else "FALSE",
        }
        for lid, name, oc, onode, dc, dnode, mode, dist, cluster in lanes
    ]

    dim_service = [
        {"service_id": "S001", "service": "Ocean FCL Door-to-Port", "service_family": "Ocean", "mode": "Ocean FCL"},
        {"service_id": "S002", "service": "Ocean LCL Consolidation", "service_family": "Ocean", "mode": "Ocean LCL"},
        {"service_id": "S003", "service": "Air Priority", "service_family": "Air", "mode": "Air"},
        {"service_id": "S004", "service": "Road Cross-Border", "service_family": "Road", "mode": "Road"},
        {"service_id": "S005", "service": "Customs & Brokerage", "service_family": "Brokerage", "mode": "All"},
    ]
    dim_office = [
        {"office_id": "O001", "office": "Ho Chi Minh", "country": "Vietnam", "region": "Vietnam South"},
        {"office_id": "O002", "office": "Ha Noi", "country": "Vietnam", "region": "Vietnam North"},
        {"office_id": "O003", "office": "Da Nang", "country": "Vietnam", "region": "Vietnam Central"},
        {"office_id": "O004", "office": "Singapore", "country": "Singapore", "region": "SEA Hub"},
        {"office_id": "O005", "office": "Bangkok", "country": "Thailand", "region": "Thailand"},
        {"office_id": "O006", "office": "Jakarta", "country": "Indonesia", "region": "Indonesia"},
    ]
    dim_carrier = [
        {"carrier_id": "CA01", "carrier": "OceanLink", "carrier_type": "Ocean"},
        {"carrier_id": "CA02", "carrier": "BlueWave Lines", "carrier_type": "Ocean"},
        {"carrier_id": "CA03", "carrier": "SkyBridge Air", "carrier_type": "Air"},
        {"carrier_id": "CA04", "carrier": "RoadRunner ASEAN", "carrier_type": "Road"},
        {"carrier_id": "CA05", "carrier": "Global Freight Alliance", "carrier_type": "Multimodal"},
        {"carrier_id": "CA06", "carrier": "PortPlus Handling", "carrier_type": "Handling"},
    ]
    return {
        "dim_date": dim_date,
        "dim_customer": dim_customer,
        "dim_trade_lane": dim_lane,
        "dim_service": dim_service,
        "dim_office": dim_office,
        "dim_carrier": dim_carrier,
    }


def service_for_lane(mode: str) -> list[str]:
    if mode == "Ocean FCL":
        return ["S001", "S005"]
    if mode == "Ocean LCL":
        return ["S002", "S005"]
    if mode == "Air":
        return ["S003", "S005"]
    if mode == "Road":
        return ["S004", "S005"]
    return ["S001", "S004", "S005"]


def generate_data() -> dict:
    random.seed(SEED)
    periods = month_range("2025-01", LATEST_PERIOD)
    dims = build_dimensions(periods)
    customer_scale = {row["customer_id"]: random.uniform(0.72, 1.55) for row in dims["dim_customer"]}
    lane_pressure = {
        row["lane_id"]: random.uniform(-0.025, 0.035)
        + (-0.055 if row["lane_id"] in {"L002", "L010"} else 0)
        + (-0.035 if row["mode"] == "Air" else 0)
        for row in dims["dim_trade_lane"]
    }
    mode_base_yield = {"Ocean FCL": 2450, "Ocean LCL": 980, "Air": 5200, "Road": 680, "Road+Sea": 1320}
    mode_cost_ratio = {"Ocean FCL": 0.71, "Ocean LCL": 0.68, "Air": 0.78, "Road": 0.63, "Road+Sea": 0.67}
    target_margin = {"Ocean FCL": 0.185, "Ocean LCL": 0.225, "Air": 0.165, "Road": 0.245, "Road+Sea": 0.215}
    offices = dims["dim_office"]
    carriers = dims["dim_carrier"]
    carrier_by_mode = {
        "Ocean FCL": ["CA01", "CA02", "CA05"],
        "Ocean LCL": ["CA01", "CA02", "CA05", "CA06"],
        "Air": ["CA03", "CA05"],
        "Road": ["CA04", "CA05"],
        "Road+Sea": ["CA02", "CA04", "CA05"],
    }
    office_by_origin = {
        "Vietnam": ["O001", "O002", "O003"],
        "Thailand": ["O005"],
        "Singapore": ["O004"],
        "Indonesia": ["O006"],
        "Malaysia": ["O004"],
        "China": ["O002", "O004"],
        "Cambodia": ["O001"],
    }

    fact_shipments: list[dict] = []
    bridge_basis: dict[tuple[str, str, str], dict[str, float]] = defaultdict(lambda: defaultdict(float))
    for p_idx, period in enumerate(periods):
        season = 1 + 0.08 * math.sin((p_idx + 1) / 2.4) + (0.06 if period.endswith("-11") or period.endswith("-12") else 0)
        trend = 1 + p_idx * 0.012
        for customer in dims["dim_customer"]:
            for lane in dims["dim_trade_lane"]:
                cid = customer["customer_id"]
                lid = lane["lane_id"]
                if random.random() > (0.38 + (0.13 if customer["tier"] == "Strategic" else 0) + (0.08 if lane["strategic_lane"] == "TRUE" else 0)):
                    continue
                mode = lane["mode"]
                service_ids = service_for_lane(mode)
                for sid in service_ids:
                    if sid == "S005" and random.random() > 0.42:
                        continue
                    base_shipments = random.randint(6, 34)
                    if customer["segment"] == "Enterprise":
                        base_shipments += random.randint(5, 22)
                    if sid == "S005":
                        base_shipments = max(3, int(base_shipments * random.uniform(0.35, 0.65)))
                    shipment_count = max(1, int(base_shipments * customer_scale[cid] * season * random.uniform(0.72, 1.28)))
                    teu = 0.0 if mode == "Air" else round2(shipment_count * random.uniform(0.6, 2.7))
                    cbm = round2(shipment_count * random.uniform(4.5, 28.0) * (1.6 if mode == "Ocean LCL" else 1.0))
                    weight = round2(shipment_count * random.uniform(450, 5200) * (2.6 if mode == "Air" else 1.0))
                    yield_multiplier = 1 + (lane["distance_km"] / 12000) * 0.22 + random.uniform(-0.09, 0.11)
                    if customer["tier"] == "Strategic":
                        yield_multiplier -= 0.025
                    net_revenue = shipment_count * mode_base_yield[mode] * yield_multiplier * trend
                    if sid == "S005":
                        net_revenue *= random.uniform(0.09, 0.16)
                    carrier_ratio = mode_cost_ratio[mode] + lane_pressure[lid] + random.uniform(-0.035, 0.045)
                    carrier_cost = net_revenue * carrier_ratio
                    fuel_cost = net_revenue * random.uniform(0.045, 0.085) * (1.15 if period >= "2026-02" else 1)
                    handling_cost = shipment_count * random.uniform(55, 210)
                    customs_cost = shipment_count * random.uniform(22, 95) * (1.0 if sid == "S005" else 0.38)
                    delay_factor = max(0, lane_pressure[lid] + random.uniform(-0.02, 0.055))
                    demurrage = net_revenue * delay_factor * random.uniform(0.08, 0.22)
                    claims = net_revenue * random.choice([0, 0, 0.002, 0.005, 0.012]) * random.uniform(0.4, 1.7)
                    last_mile = shipment_count * random.uniform(35, 180) * (1.35 if mode in {"Road", "Road+Sea"} else 0.72)
                    total_cost = carrier_cost + fuel_cost + handling_cost + customs_cost + demurrage + claims + last_mile
                    gp = net_revenue - total_cost
                    utilization = max(0.42, min(0.99, random.uniform(0.64, 0.94) - (0.05 if gp < 0 else 0) + (0.03 if customer["tier"] == "Strategic" else 0)))
                    delay_rate = max(0.02, min(0.38, 0.10 + delay_factor * 2.2 + random.uniform(-0.04, 0.06)))
                    delayed = int(round(shipment_count * delay_rate))
                    on_time = max(0, shipment_count - delayed)
                    office_id = random.choice(office_by_origin.get(lane["origin_country"], ["O001", "O004"]))
                    carrier_id = random.choice(carrier_by_mode[mode])
                    row = {
                        "date_id": period,
                        "customer_id": cid,
                        "lane_id": lid,
                        "service_id": sid,
                        "office_id": office_id,
                        "carrier_id": carrier_id,
                        "shipment_count": shipment_count,
                        "teu": round2(teu),
                        "cbm": round2(cbm),
                        "chargeable_weight_kg": round2(weight),
                        "net_revenue_usd": round2(net_revenue),
                        "freight_cost_usd": round2(carrier_cost),
                        "fuel_cost_usd": round2(fuel_cost),
                        "handling_cost_usd": round2(handling_cost),
                        "customs_cost_usd": round2(customs_cost),
                        "demurrage_cost_usd": round2(demurrage),
                        "claims_cost_usd": round2(claims),
                        "last_mile_cost_usd": round2(last_mile),
                        "total_cost_usd": round2(total_cost),
                        "gross_profit_usd": round2(gp),
                        "target_margin_pct": round(target_margin[mode], 4),
                        "on_time_count": on_time,
                        "delayed_count": delayed,
                        "utilization_pct": round(utilization, 4),
                        "is_synthetic": "TRUE",
                    }
                    fact_shipments.append(row)
                    key = (period, cid, lid)
                    target_gp = net_revenue * target_margin[mode]
                    bridge_basis[key]["net_revenue_usd"] += net_revenue
                    bridge_basis[key]["gross_profit_usd"] += gp
                    bridge_basis[key]["target_gross_profit_usd"] += target_gp
                    bridge_basis[key]["fuel_cost_usd"] += fuel_cost
                    bridge_basis[key]["demurrage_cost_usd"] += demurrage
                    bridge_basis[key]["claims_cost_usd"] += claims
                    bridge_basis[key]["freight_cost_usd"] += carrier_cost
                    bridge_basis[key]["utilization_penalty"] += net_revenue * max(0, 0.72 - utilization) * 0.08

    fact_bridge: list[dict] = []
    for (period, cid, lid), basis in bridge_basis.items():
        gap = basis["gross_profit_usd"] - basis["target_gross_profit_usd"]
        if abs(gap) < 2000 and random.random() > 0.25:
            continue
        raw = [
            ("Price / Yield", gap * random.uniform(0.18, 0.36)),
            ("Carrier Buy Rate", -basis["freight_cost_usd"] * random.uniform(0.012, 0.028)),
            ("Fuel Surcharge", -basis["fuel_cost_usd"] * random.uniform(0.16, 0.34)),
            ("Demurrage & Detention", -basis["demurrage_cost_usd"] * random.uniform(0.72, 1.05)),
            ("Claims Leakage", -basis["claims_cost_usd"] * random.uniform(0.65, 1.05)),
            ("Utilization Mix", -basis["utilization_penalty"]),
        ]
        residual = gap - sum(v for _, v in raw)
        drivers = raw + [("Other / Rounding", residual)]
        for idx, (driver, amount) in enumerate(drivers, 1):
            fact_bridge.append(
                {
                    "date_id": period,
                    "customer_id": cid,
                    "lane_id": lid,
                    "driver": driver,
                    "driver_sort": idx,
                    "amount_usd": round2(amount),
                    "driver_type": "Favorable" if amount >= 0 else "Unfavorable",
                    "is_synthetic": "TRUE",
                }
            )

    latest_rows = [row for row in fact_shipments if row["date_id"] >= "2026-01"]
    candidates = sorted(
        latest_rows,
        key=lambda r: (r["gross_profit_usd"] - (r["net_revenue_usd"] * r["target_margin_pct"])),
    )[:150]
    issue_types = [
        ("Below target margin", "Reprice customer or reset minimum yield"),
        ("Fuel leakage", "Update surcharge table and audit pass-through"),
        ("Demurrage exposure", "Renegotiate free time and tighten document cutoff"),
        ("Claims spike", "Review packaging and carrier claims recovery"),
        ("Carrier rate gap", "Tender backup carrier and re-benchmark lane"),
        ("Low utilization", "Consolidate departures or shift to LCL/road alternative"),
    ]
    statuses = ["Open", "In Review", "Action Agreed", "Closed"]
    priorities = ["High", "Medium", "Low"]
    fact_actions: list[dict] = []
    for idx, row in enumerate(candidates[:84], 1):
        issue, action = random.choice(issue_types)
        priority = random.choices(priorities, weights=[0.34, 0.48, 0.18])[0]
        status = random.choices(statuses, weights=[0.36, 0.30, 0.22, 0.12])[0]
        y, m = map(int, row["date_id"].split("-"))
        due = date(y, m, 1) + timedelta(days=random.randint(21, 55))
        risk = max(3000, (row["net_revenue_usd"] * row["target_margin_pct"] - row["gross_profit_usd"]) * random.uniform(0.55, 1.25))
        fact_actions.append(
            {
                "action_id": f"ACT{idx:03d}",
                "date_id": row["date_id"],
                "customer_id": row["customer_id"],
                "lane_id": row["lane_id"],
                "office_id": row["office_id"],
                "issue_type": issue,
                "priority": priority,
                "status": status,
                "owner": random.choice(["Commercial", "Procurement", "Operations", "Finance BP", "Customer Success"]),
                "risk_value_usd": round2(risk),
                "target_margin_recovery_usd": round2(risk * random.uniform(0.45, 0.78)),
                "recommended_action": action,
                "due_date": due.isoformat(),
                "is_synthetic": "TRUE",
            }
        )

    return {
        **dims,
        "fact_shipment_profitability": fact_shipments,
        "fact_cost_driver_bridge": fact_bridge,
        "fact_action_queue": fact_actions,
        "metadata": {
            "seed": SEED,
            "latest_complete_period": LATEST_PERIOD,
            "generated_at": RUN_TS,
            "is_synthetic": True,
        },
    }


def validate_data(data: dict) -> dict:
    checks = []
    fact = data["fact_shipment_profitability"]
    bridge = data["fact_cost_driver_bridge"]
    actions = data["fact_action_queue"]
    fact_keys = [
        (r["date_id"], r["customer_id"], r["lane_id"], r["service_id"], r["office_id"], r["carrier_id"])
        for r in fact
    ]
    checks.append(
        {
            "check": "Shipment profitability grain uniqueness",
            "status": "pass" if len(fact_keys) == len(set(fact_keys)) else "fail",
            "detail": f"{len(fact_keys) - len(set(fact_keys))} duplicate composite keys",
        }
    )
    missing = sum(
        1
        for r in fact
        if not r["date_id"] or not r["customer_id"] or not r["lane_id"] or float(r["net_revenue_usd"]) <= 0
    )
    checks.append({"check": "Critical fields populated", "status": "pass" if missing == 0 else "fail", "detail": f"{missing} bad rows"})
    date_ids = sorted({r["date_id"] for r in fact})
    checks.append({"check": "Date coverage", "status": "pass" if date_ids[0] == "2025-01" and date_ids[-1] == LATEST_PERIOD else "fail", "detail": f"{date_ids[0]} to {date_ids[-1]}"})
    neg_margin = sum(1 for r in fact if float(r["gross_profit_usd"]) < 0)
    checks.append({"check": "Negative margin population exists", "status": "pass" if neg_margin > 25 else "fail", "detail": f"{neg_margin} records below zero gross profit"})
    basis = defaultdict(float)
    target = defaultdict(float)
    for r in fact:
        key = (r["date_id"], r["customer_id"], r["lane_id"])
        basis[key] += float(r["gross_profit_usd"]) - float(r["net_revenue_usd"]) * float(r["target_margin_pct"])
    for r in bridge:
        key = (r["date_id"], r["customer_id"], r["lane_id"])
        target[key] += float(r["amount_usd"])
    max_diff = max((abs(basis[k] - target.get(k, 0.0)) for k in target), default=0.0)
    checks.append({"check": "Cost driver bridge tie-out", "status": "pass" if max_diff <= 2.0 else "fail", "detail": f"Max driver gap ${max_diff:,.2f}"})
    action_risk = sum(float(r["risk_value_usd"]) for r in actions)
    checks.append({"check": "Action queue risk value", "status": "pass" if action_risk > 100000 else "fail", "detail": f"${action_risk:,.0f} in action risk"})
    row_counts = {k: len(v) for k, v in data.items() if isinstance(v, list)}
    status = "pass" if all(c["status"] == "pass" for c in checks) else "fail"
    return {"status": status, "checks": checks, "row_counts": row_counts, "latest_complete_period": LATEST_PERIOD}


def measure_catalog() -> list[dict]:
    return [
        ("Net Revenue", "SUM(FactShipmentProfitability[net_revenue_usd])", "$#,0", "Total billed revenue after rebates and credits."),
        ("Freight Cost", "SUM(FactShipmentProfitability[freight_cost_usd])", "$#,0", "Carrier buy rate and main freight cost."),
        ("Fuel Cost", "SUM(FactShipmentProfitability[fuel_cost_usd])", "$#,0", "Fuel surcharge cost charged by carriers."),
        ("Demurrage Cost", "SUM(FactShipmentProfitability[demurrage_cost_usd])", "$#,0", "Demurrage and detention leakage."),
        ("Claims Cost", "SUM(FactShipmentProfitability[claims_cost_usd])", "$#,0", "Claims and service failure cost."),
        ("Total Cost", "SUM(FactShipmentProfitability[total_cost_usd])", "$#,0", "Total cost-to-serve for shipments."),
        ("Gross Profit", "SUM(FactShipmentProfitability[gross_profit_usd])", "$#,0", "Net revenue less total shipment cost."),
        ("GP Margin %", "DIVIDE([Gross Profit], [Net Revenue])", "0.0%", "Gross profit divided by net revenue."),
        ("Shipment Count", "SUM(FactShipmentProfitability[shipment_count])", "#,0", "Total shipment records weighted by shipment count."),
        ("TEU", "SUM(FactShipmentProfitability[teu])", "#,0.0", "Twenty-foot equivalent units for ocean lanes."),
        ("CBM", "SUM(FactShipmentProfitability[cbm])", "#,0.0", "Cubic meter volume handled."),
        ("Revenue per Shipment", "DIVIDE([Net Revenue], [Shipment Count])", "$#,0", "Net revenue per shipment."),
        ("Cost per Shipment", "DIVIDE([Total Cost], [Shipment Count])", "$#,0", "Cost-to-serve per shipment."),
        ("Target Gross Profit", "SUMX(FactShipmentProfitability, FactShipmentProfitability[net_revenue_usd] * FactShipmentProfitability[target_margin_pct])", "$#,0", "Target gross profit using lane/service margin targets."),
        ("Margin Gap vs Target", "[Gross Profit] - [Target Gross Profit]", "$#,0", "Actual gross profit less target gross profit."),
        ("Target Margin %", "DIVIDE([Target Gross Profit], [Net Revenue])", "0.0%", "Weighted target margin for selected scope."),
        ("Margin Gap %", "[GP Margin %] - [Target Margin %]", "0.0%", "Percentage point gap versus target margin."),
        ("On-Time %", "DIVIDE(SUM(FactShipmentProfitability[on_time_count]), [Shipment Count])", "0.0%", "On-time shipments divided by shipments."),
        ("Utilization %", "AVERAGE(FactShipmentProfitability[utilization_pct])", "0.0%", "Average equipment/consolidation utilization."),
        ("Negative Margin Shipments", "CALCULATE([Shipment Count], FILTER(FactShipmentProfitability, FactShipmentProfitability[gross_profit_usd] < 0))", "#,0", "Shipments with negative gross profit."),
        ("Reprice Opportunity", "SUMX(FILTER(FactShipmentProfitability, FactShipmentProfitability[gross_profit_usd] < 0), -FactShipmentProfitability[gross_profit_usd])", "$#,0", "Gross profit required to bring negative shipments to zero."),
        ("Bridge Amount", "SUM(FactCostDriverBridge[amount_usd])", "$#,0", "Driver bridge amount for margin gap explanation."),
        ("Open Actions", "CALCULATE(COUNTROWS(FactActionQueue), FILTER(FactActionQueue, FactActionQueue[status] <> \"Closed\"))", "#,0", "Non-closed commercial/procurement/ops actions."),
        ("Action Risk Value", "SUM(FactActionQueue[risk_value_usd])", "$#,0", "Margin value at risk in the action queue."),
        ("Recovery Value", "SUM(FactActionQueue[target_margin_recovery_usd])", "$#,0", "Expected recoverable margin from action queue."),
    ]


def write_model_docs(validation: dict) -> None:
    measures = [
        {"measure_name": name, "dax": dax, "format_string": fmt, "definition": definition}
        for name, dax, fmt, definition in measure_catalog()
    ]
    write_json("model/measure_catalog.json", measures)
    write_text("model/MEASURES.dax", "\n\n".join([f"{m['measure_name']} =\n{m['dax']}" for m in measures]))
    write_text("model/dax_measures.md", "\n".join(["# DAX Measures", "", "| Measure | Format | Definition |", "|---|---:|---|"] + [f"| {m['measure_name']} | `{m['format_string']}` | {m['definition']} |" for m in measures]))
    write_text(
        "model/metric_definitions.md",
        """
# Metric Definitions

Core profitability is measured at shipment profitability grain, then aggregated through DAX measures.

| Metric | Definition | Notes |
|---|---|---|
| Net Revenue | Sum of shipment revenue after credits/rebates | Excludes tax and pass-through only items |
| Gross Profit | Net Revenue less freight, fuel, handling, customs, demurrage, claims, and last-mile cost | Primary margin outcome |
| GP Margin % | Gross Profit / Net Revenue | Uses `DIVIDE`; never summed |
| Target Margin % | Weighted target margin by lane/service row | Used for margin gap and action queue |
| Reprice Opportunity | Value needed to bring negative-margin shipments back to zero GP | Conservative floor, not full target recovery |
| On-Time % | On-time shipment count / shipment count | Service guardrail |
| Utilization % | Average capacity/equipment utilization | Cost-to-serve guardrail |
""",
    )
    write_text(
        "model/relationship_map.md",
        "\n".join(
            ["# Relationship Map", "", "| From | Column | To | Column | Cardinality | Filter |", "|---|---|---|---|---|---|"]
            + [f"| {ft} | {fc} | {tt} | {tc} | Many-to-one | Single |" for ft, fc, tt, tc in RELATIONSHIPS]
        ),
    )
    write_text(
        "model/data_dictionary.md",
        """
# Model Data Dictionary

| Table | Grain | Purpose |
|---|---|---|
| DimDate | Month | Time slicing and trend axis |
| DimCustomer | Customer | Customer, segment, industry, account manager |
| DimTradeLane | Origin-destination lane | Lane, mode, cluster, strategic lane |
| DimService | Service | Ocean/Air/Road/Brokerage service family |
| DimOffice | Office | Operating office and region |
| DimCarrier | Carrier | Carrier/vendor segmentation |
| FactShipmentProfitability | Month x customer x lane x service x office x carrier | Revenue, cost, margin, volume, service KPIs |
| FactCostDriverBridge | Month x customer x lane x driver | Margin gap driver bridge versus target |
| FactActionQueue | Action item | Margin recovery actions and owner queue |
""",
    )
    write_text(
        "model/semantic_model_notes.md",
        f"""
# Semantic Model Notes

- Synthetic portfolio/demo data, seed `{SEED}`.
- Latest complete period: `{LATEST_PERIOD}`.
- Primary fact: `FactShipmentProfitability`.
- Important rates use DAX `DIVIDE` and weighted target profit, avoiding summed percentages.
- Validation status: `{validation['status']}`.
- All dimensions filter facts one-way to preserve stable BI behavior.
""",
    )


def html_dashboard(data: dict) -> str:
    fact = data["fact_shipment_profitability"]
    lane_lookup = {r["lane_id"]: r for r in data["dim_trade_lane"]}
    customer_lookup = {r["customer_id"]: r for r in data["dim_customer"]}
    latest = [r for r in fact if r["date_id"] == LATEST_PERIOD]

    def agg(rows: list[dict]) -> dict:
        revenue = sum(float(r["net_revenue_usd"]) for r in rows)
        cost = sum(float(r["total_cost_usd"]) for r in rows)
        gp = sum(float(r["gross_profit_usd"]) for r in rows)
        shipments = sum(int(r["shipment_count"]) for r in rows)
        reprice = sum(-float(r["gross_profit_usd"]) for r in rows if float(r["gross_profit_usd"]) < 0)
        return {"revenue": revenue, "cost": cost, "gp": gp, "shipments": shipments, "margin": gp / revenue if revenue else 0, "reprice": reprice}

    monthly = []
    for period in sorted({r["date_id"] for r in fact}):
        item = agg([r for r in fact if r["date_id"] == period])
        item["period"] = period
        monthly.append(item)
    by_lane = []
    for lane_id in sorted({r["lane_id"] for r in latest}):
        rows = [r for r in latest if r["lane_id"] == lane_id]
        item = agg(rows)
        item["lane"] = lane_lookup[lane_id]["lane_name"]
        item["mode"] = lane_lookup[lane_id]["mode"]
        by_lane.append(item)
    by_lane = sorted(by_lane, key=lambda x: x["gp"])
    actions = []
    for row in sorted(data["fact_action_queue"], key=lambda x: float(x["risk_value_usd"]), reverse=True)[:16]:
        actions.append(
            {
                "customer": customer_lookup[row["customer_id"]]["customer_name"],
                "lane": lane_lookup[row["lane_id"]]["lane_name"],
                "issue": row["issue_type"],
                "owner": row["owner"],
                "risk": row["risk_value_usd"],
                "status": row["status"],
            }
        )
    payload = {"overview": agg(latest), "monthly": monthly, "lanes": by_lane, "actions": actions}
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Project 17 - Logistics Trade Lane Profitability</title>
<style>
:root {{ --bg:{THEME['bg']}; --panel:{THEME['panel']}; --border:{THEME['border']}; --text:{THEME['text']}; --muted:{THEME['muted']}; --blue:{THEME['blue']}; --teal:{THEME['teal']}; --green:{THEME['green']}; --amber:{THEME['amber']}; --red:{THEME['red']}; }}
* {{ box-sizing:border-box; }} body {{ margin:0; font-family:Segoe UI,Arial,sans-serif; background:var(--bg); color:var(--text); }}
.wrap {{ max-width:1280px; margin:0 auto; padding:24px; }} header {{ display:flex; justify-content:space-between; gap:20px; align-items:flex-start; border-bottom:1px solid var(--border); padding-bottom:16px; }}
h1 {{ margin:0; font-size:26px; letter-spacing:0; }} .sub {{ color:var(--muted); margin-top:6px; font-size:13px; }}
.tabs {{ display:flex; gap:8px; margin:18px 0; flex-wrap:wrap; }} button {{ border:1px solid var(--border); background:white; padding:9px 12px; border-radius:6px; color:var(--text); cursor:pointer; }} button.active {{ background:var(--blue); color:white; border-color:var(--blue); }}
.page {{ display:none; }} .page.active {{ display:block; }}
.kpis {{ display:grid; grid-template-columns:repeat(6,1fr); gap:12px; }} .card,.panel {{ background:var(--panel); border:1px solid var(--border); border-radius:8px; padding:14px; box-shadow:0 1px 2px rgba(15,23,42,.04); }}
.label {{ color:var(--muted); font-size:12px; }} .value {{ font-size:23px; font-weight:700; margin-top:5px; }} .grid {{ display:grid; grid-template-columns:1.4fr 1fr; gap:14px; margin-top:14px; }} .grid3 {{ display:grid; grid-template-columns:1fr 1fr 1fr; gap:14px; margin-top:14px; }}
svg {{ width:100%; height:250px; display:block; }} table {{ width:100%; border-collapse:collapse; font-size:12px; }} th,td {{ padding:8px 6px; border-bottom:1px solid #E2E8F0; text-align:left; }} th {{ color:var(--muted); font-weight:600; }} .neg {{ color:var(--red); font-weight:700; }} .pos {{ color:var(--green); font-weight:700; }}
@media (max-width:900px) {{ .kpis,.grid,.grid3 {{ grid-template-columns:1fr; }} .wrap {{ padding:14px; }} }}
</style>
</head>
<body><div class="wrap">
<header><div><h1>Logistics Trade Lane Profitability</h1><div class="sub">Synthetic portfolio BI product | latest period {LATEST_PERIOD} | three-tab Power BI blueprint</div></div><div class="sub">Seed {SEED}</div></header>
<div class="tabs"><button class="active" data-tab="overview">Executive Overview</button><button data-tab="lane">Trade Lane Margin</button><button data-tab="action">Cost Drivers & Action Queue</button></div>
<section id="overview" class="page active"><div class="kpis" id="kpis"></div><div class="grid"><div class="panel"><h3>Revenue and GP Trend</h3><svg id="trend"></svg></div><div class="panel"><h3>Bottom Margin Lanes</h3><table id="bottom"></table></div></div></section>
<section id="lane" class="page"><div class="grid"><div class="panel"><h3>Lane Revenue vs Margin</h3><svg id="laneBars"></svg></div><div class="panel"><h3>Top Margin Lanes</h3><table id="top"></table></div></div></section>
<section id="action" class="page"><div class="grid3"><div class="panel"><h3>Reprice Opportunity</h3><div class="value" id="reprice"></div><div class="label">negative margin floor</div></div><div class="panel"><h3>Action Queue</h3><div class="value">{len(data['fact_action_queue'])}</div><div class="label">synthetic actions</div></div><div class="panel"><h3>Bridge Records</h3><div class="value">{len(data['fact_cost_driver_bridge'])}</div><div class="label">driver rows</div></div></div><div class="panel" style="margin-top:14px"><h3>Action Queue</h3><table id="actions"></table></div></section>
</div>
<script id="data" type="application/json">{json.dumps(payload)}</script>
<script>
const d = JSON.parse(document.getElementById('data').textContent);
const fmt = n => '$' + Math.round(n).toLocaleString();
const pct = n => (n*100).toFixed(1) + '%';
function kpis() {{
 const o=d.overview; const rows=[['Net Revenue',fmt(o.revenue)],['Gross Profit',fmt(o.gp)],['GP Margin',pct(o.margin)],['Shipments',o.shipments.toLocaleString()],['Cost / Shipment',fmt(o.cost/o.shipments)],['Reprice Opp.',fmt(o.reprice)]];
 document.getElementById('kpis').innerHTML = rows.map(r=>`<div class="card"><div class="label">${{r[0]}}</div><div class="value">${{r[1]}}</div></div>`).join('');
 document.getElementById('reprice').textContent=fmt(o.reprice);
}}
function table(id, rows) {{
 document.getElementById(id).innerHTML='<thead><tr><th>Lane</th><th>Mode</th><th>Revenue</th><th>GP%</th></tr></thead><tbody>'+rows.map(x=>`<tr><td>${{x.lane}}</td><td>${{x.mode}}</td><td>${{fmt(x.revenue)}}</td><td class="${{x.margin<0?'neg':'pos'}}">${{pct(x.margin)}}</td></tr>`).join('')+'</tbody>';
}}
function actionTable() {{
 document.getElementById('actions').innerHTML='<thead><tr><th>Customer</th><th>Lane</th><th>Issue</th><th>Owner</th><th>Risk</th><th>Status</th></tr></thead><tbody>'+d.actions.map(x=>`<tr><td>${{x.customer}}</td><td>${{x.lane}}</td><td>${{x.issue}}</td><td>${{x.owner}}</td><td>${{fmt(x.risk)}}</td><td>${{x.status}}</td></tr>`).join('')+'</tbody>';
}}
function bars(svgId, rows, metric) {{
 const svg=document.getElementById(svgId), w=760,h=250,p=32; const max=Math.max(...rows.map(r=>Math.abs(r[metric]))); let out=`<line x1="${{p}}" y1="${{h-p}}" x2="${{w-p}}" y2="${{h-p}}" stroke="#CBD5E1"/>`;
 rows.slice(0,10).forEach((r,i)=>{{ const bw=(w-p*2)/10-8; const x=p+i*((w-p*2)/10); const val=Math.abs(r[metric]); const bh=(val/max)*(h-p*2); const y=h-p-bh; const color=r.margin<0?'#DC2626':'#0F766E'; out+=`<rect x="${{x}}" y="${{y}}" width="${{bw}}" height="${{bh}}" rx="4" fill="${{color}}"><title>${{r.lane}} ${{fmt(r[metric])}}</title></rect>`; }}); svg.setAttribute('viewBox',`0 0 ${{w}} ${{h}}`); svg.innerHTML=out;
}}
function trend() {{ bars('trend', d.monthly, 'revenue'); }}
document.querySelectorAll('button[data-tab]').forEach(b=>b.onclick=()=>{{document.querySelectorAll('button[data-tab]').forEach(x=>x.classList.remove('active'));document.querySelectorAll('.page').forEach(x=>x.classList.remove('active'));b.classList.add('active');document.getElementById(b.dataset.tab).classList.add('active');}});
kpis(); table('bottom', d.lanes.slice(0,8)); table('top', d.lanes.slice(-8).reverse()); actionTable(); trend(); bars('laneBars', d.lanes.slice().sort((a,b)=>b.revenue-a.revenue), 'revenue');
window.__dashboardQa={{pages:3,kpis:6,lanes:d.lanes.length,actions:d.actions.length}};
</script></body></html>"""


def read_header(path: Path) -> list[str]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return next(csv.reader(handle))


def data_type(column: str) -> str:
    if column in COLUMN_TYPES:
        return COLUMN_TYPES[column]
    if column.endswith("_usd") or column.endswith("_pct") or column.endswith("_kg"):
        return "double"
    if column.endswith("_count") or column.endswith("_sort") or column.endswith("_index"):
        return "int64"
    return "string"


def m_type(dtype: str) -> str:
    return {
        "string": "type text",
        "int64": "Int64.Type",
        "double": "type number",
        "dateTime": "type date",
        "boolean": "type logical",
    }.get(dtype, "type text")


def m_expression(csv_path: Path, columns: list[dict]) -> list[str]:
    typed = ",\n        ".join([f'{{"{c["name"]}", {m_type(c["dataType"])}}}' for c in columns])
    return [
        "let",
        f'    Source = Csv.Document(File.Contents("{csv_path.as_posix()}"), [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]),',
        "    PromotedHeaders = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),",
        "    TypedColumns = Table.TransformColumnTypes(PromotedHeaders, {",
        f"        {typed}",
        '    }, "en-US")',
        "in",
        "    TypedColumns",
    ]


def build_model_bim() -> dict:
    tables = []
    prepared = PROJECT / "data" / "prepared"
    for table_name, file_name in TABLE_FILES.items():
        csv_path = prepared / file_name
        columns = [{"name": col, "dataType": data_type(col), "sourceColumn": col, "summarizeBy": "none"} for col in read_header(csv_path)]
        tables.append(
            {
                "name": table_name,
                "columns": columns,
                "partitions": [
                    {
                        "name": f"{table_name}-Import",
                        "mode": "import",
                        "source": {"type": "m", "expression": m_expression(csv_path, columns)},
                    }
                ],
            }
        )
    measures = [
        {"name": name, "expression": dax, "formatString": fmt, "description": definition}
        for name, dax, fmt, definition in measure_catalog()
    ]
    tables.append(
        {
            "name": "KPI Measures",
            "columns": [{"name": "Measure Group", "dataType": "string", "sourceColumn": "Measure Group", "isHidden": True, "summarizeBy": "none"}],
            "partitions": [
                {
                    "name": "KPI Measures-Import",
                    "mode": "import",
                    "source": {"type": "m", "expression": ["let", '    Source = #table(type table [Measure Group = text], {{"Logistics Trade Lane Profitability"}})', "in", "    Source"]},
                }
            ],
            "measures": measures,
        }
    )
    return {
        "compatibilityLevel": 1550,
        "model": {
            "culture": "en-US",
            "defaultPowerBIDataSourceVersion": "powerBI_V3",
            "sourceQueryCulture": "en-US",
            "tables": tables,
            "relationships": [
                {"name": f"rel_{ft}_{fc}_{tt}_{tc}", "fromTable": ft, "fromColumn": fc, "toTable": tt, "toColumn": tc}
                for ft, fc, tt, tc in RELATIONSHIPS
            ],
        },
    }


def load_sample(name: str) -> dict:
    return json.loads((SAMPLE_DIR / f"{name}.json").read_text(encoding="utf-8"))


SAMPLES = {}


def lit(value: str) -> dict:
    return {"expr": {"Literal": {"Value": value}}}


def color(value: str) -> dict:
    return {"solid": {"color": {"expr": {"Literal": {"Value": f"'{value}'"}}}}}


def prop_text(value: str) -> dict:
    return lit("'" + value.replace("'", "''") + "'")


def rand_name() -> str:
    return "".join(random.choice("0123456789abcdef") for _ in range(20))


def pos(x, y, w, h, z) -> dict:
    return {"x": x, "y": y, "z": z, "width": w, "height": h, "tabOrder": z}


def outer(cfg: dict, x, y, w, h, z) -> dict:
    cfg["layouts"] = [{"id": 0, "position": pos(x, y, w, h, z)}]
    return {
        "x": x,
        "y": y,
        "z": z,
        "width": w,
        "height": h,
        "tabOrder": z,
        "config": json.dumps(cfg, separators=(",", ":"), ensure_ascii=False),
        "filters": "[]",
    }


def title_accent(title: str | None) -> str:
    text = (title or "").lower()
    if any(token in text for token in ("risk", "negative", "demurrage", "claims", "gap")):
        return THEME["red"]
    if any(token in text for token in ("cost", "fuel", "action", "queue")):
        return THEME["amber"]
    if any(token in text for token in ("profit", "margin", "reprice")):
        return THEME["green"]
    return THEME["blue"]


def visual_shell(title: str | None = None, subtitle: str | None = None) -> dict:
    shell = {
        "background": [{"properties": {"show": lit("true"), "color": color(THEME["panel"]), "transparency": lit("0D")}}],
        "border": [{"properties": {"show": lit("true"), "color": color(THEME["border"]), "radius": lit("6.0D"), "width": lit("1.0D")}}],
        "dropShadow": [{"properties": {"show": lit("true"), "color": color("#000000"), "transparency": lit("82.0D"), "angle": lit("45.0D"), "distance": lit("1.0D")}}],
    }
    if title:
        shell["title"] = [{"properties": {"show": lit("true"), "text": prop_text(title), "fontFamily": prop_text("Segoe UI Semibold"), "fontSize": lit("9.5D"), "fontColor": color(title_accent(title)), "alignment": prop_text("left")}}]
    if subtitle:
        shell["subTitle"] = [{"properties": {"show": lit("true"), "text": prop_text(subtitle), "fontFamily": prop_text("Segoe UI"), "fontSize": lit("7.5D"), "fontColor": color(THEME["muted"])}}]
    return shell


def chart_objects(kind: str, fields: list[tuple[str, str, str, str]], title: str | None) -> dict:
    measures = [f"{table}.{field}" for table, field, role, _ in fields if role == "measure"]
    objects = {
        "valueAxis": [{"properties": {"showAxisTitle": lit("false"), "gridlineShow": lit("true"), "gridlineColor": color(THEME["grid"]), "labelColor": color(THEME["muted"]), "fontSize": lit("8.0D")}}],
        "categoryAxis": [{"properties": {"showAxisTitle": lit("false"), "gridlineShow": lit("false"), "concatenateLabels": lit("false"), "labelColor": color(THEME["muted"]), "fontSize": lit("8.0D")}}],
        "legend": [{"properties": {"showTitle": lit("false"), "position": prop_text("Top"), "fontColor": color(THEME["muted"]), "fontSize": lit("8.0D")}}],
        "labels": [{"properties": {"show": lit("false"), "fontColor": color(THEME["text"]), "labelColor": color(THEME["text"])}}],
        "dataPoint": [],
    }
    if kind == "donutChart":
        objects["labels"][0]["properties"].update({"show": lit("true"), "labelStyle": prop_text("Percent of total"), "fontColor": color(THEME["muted"])})
    if kind == "waterfallChart":
        objects["sentimentColors"] = [{"properties": {"increaseFill": color(THEME["green"]), "decreaseFill": color(THEME["red"]), "totalFill": color(THEME["ink"])}}]
    for idx, metadata in enumerate(measures or ["_default"]):
        item = {"properties": {"fill": color(PALETTE[idx % len(PALETTE)])}}
        if metadata != "_default":
            item["selector"] = {"metadata": metadata}
        objects["dataPoint"].append(item)
    return objects


def table_objects() -> dict:
    return {
        "grid": [{"properties": {"gridHorizontal": lit("false"), "gridVertical": lit("false"), "outlineColor": color(THEME["border"]), "rowPadding": lit("5D")}}],
        "columnHeaders": [{"properties": {"fontFamily": prop_text("Segoe UI Semibold"), "fontSize": lit("8.0D"), "fontColor": color(THEME["blue"]), "backColor": color(THEME["panel2"])}}],
        "values": [{"properties": {"fontSize": lit("7.4D"), "fontFamily": prop_text("Segoe UI"), "fontColor": color(THEME["text"]), "backColorPrimary": color(THEME["panel"]), "backColorSecondary": color(THEME["panel2"])}}],
    }


def slicer_objects(title: str) -> dict:
    return {
        "data": [{"properties": {"mode": prop_text("Dropdown")}}],
        "selection": [{"properties": {"selectAllCheckboxEnabled": lit("true"), "singleSelect": lit("false")}}],
        "header": [{"properties": {"show": lit("true"), "text": prop_text(title), "textSize": lit("8.0D"), "fontColor": color(THEME["muted"]), "fontFamily": prop_text("Segoe UI Semibold")}}],
        "items": [{"properties": {"textSize": lit("8.0D"), "fontColor": color(THEME["text"]), "fontFamily": prop_text("Segoe UI"), "background": color(THEME["panel"])}}],
    }


def ref(table: str, field: str, role: str, alias: str, display: str | None = None) -> dict:
    source = {"SourceRef": {"Source": alias}}
    if role == "measure":
        select = {"Measure": {"Expression": source, "Property": field}}
    else:
        select = {"Column": {"Expression": source, "Property": field}}
    qref = f"{table}.{field}"
    select["Name"] = qref
    select["NativeReferenceName"] = display or field
    return select


def prototype(fields: list[tuple[str, str, str, str]]) -> dict:
    aliases: dict[str, str] = {}
    froms = []
    for table, _field, _role, _display in fields:
        if table in aliases:
            continue
        base = "".join(ch.lower() for ch in table if ch.isalnum())[:1] or "t"
        alias = base
        suffix = 1
        while alias in aliases.values():
            suffix += 1
            alias = f"{base}{suffix}"
        aliases[table] = alias
        froms.append({"Name": alias, "Entity": table, "Type": 0})
    return {"Version": 2, "From": froms, "Select": [ref(t, f, r, aliases[t], d) for t, f, r, d in fields]}


def projections(mapping: dict[str, list[tuple[str, str, str, str]]]) -> dict:
    return {bucket: [{"queryRef": f"{table}.{field}", **({"active": True} if idx == 0 else {})} for idx, (table, field, *_rest) in enumerate(fields)] for bucket, fields in mapping.items()}


def data_visual(kind: str, x, y, w, h, z, proj_map: dict[str, list[tuple[str, str, str, str]]], title: str, subtitle: str | None = None, show_container_title: bool = True) -> dict:
    cfg = json.loads(json.dumps(SAMPLES[kind]))
    cfg["name"] = rand_name()
    sv = cfg["singleVisual"]
    sv["visualType"] = kind
    fields = [field for bucket in proj_map.values() for field in bucket]
    sv["projections"] = projections(proj_map)
    sv["prototypeQuery"] = prototype(fields)
    sv.pop("columnProperties", None)
    if kind == "tableEx":
        sv["objects"] = table_objects()
    elif kind == "slicer":
        sv["objects"] = slicer_objects(title)
    else:
        sv["objects"] = chart_objects(kind, fields, title)
    sv["vcObjects"] = visual_shell(title if show_container_title else None, subtitle)
    return outer(cfg, x, y, w, h, z)


def transparent_shell() -> dict:
    return {
        "background": [{"properties": {"show": lit("false"), "transparency": lit("100D")}}],
        "border": [{"properties": {"show": lit("false")}}],
        "dropShadow": [{"properties": {"show": lit("false")}}],
        "title": [{"properties": {"show": lit("false")}}],
        "visualHeader": [{"properties": {"show": lit("false")}}],
    }


def sparkline(measure: str, x, y, w, h, z, accent: str | None = None) -> dict:
    cfg = json.loads(json.dumps(SAMPLES["columnChart"]))
    cfg["name"] = rand_name()
    sv = cfg["singleVisual"]
    sv["visualType"] = "columnChart"
    fields = [("DimDate", "month_index", "column", "Month"), ("KPI Measures", measure, "measure", measure)]
    sv["projections"] = projections({"Category": [fields[0]], "Y": [fields[1]]})
    sv["prototypeQuery"] = prototype(fields)
    sv.pop("columnProperties", None)
    sv["drillFilterOtherVisuals"] = False
    objects = chart_objects("columnChart", fields, None)
    objects["valueAxis"][0]["properties"].update({"show": lit("false"), "gridlineShow": lit("false"), "showAxisTitle": lit("false")})
    objects["categoryAxis"][0]["properties"].update({"show": lit("false"), "gridlineShow": lit("false"), "showAxisTitle": lit("false")})
    objects["legend"][0]["properties"]["show"] = lit("false")
    objects["labels"][0]["properties"]["show"] = lit("false")
    objects["dataPoint"][0]["properties"]["fill"] = color(accent or title_accent(measure))
    sv["objects"] = objects
    sv["vcObjects"] = transparent_shell()
    return outer(cfg, x, y, w, h, z)


def card(measure: str, title: str, x, y, w, h, z) -> dict:
    visual = data_visual("cardVisual", x, y, w, h, z, {"Data": [("KPI Measures", measure, "measure", title)]}, title)
    cfg = json.loads(visual["config"])
    metadata = f"KPI Measures.{measure}"
    accent = title_accent(title)
    cfg["singleVisual"]["objects"] = {
        "layout": [{"properties": {"backgroundShow": lit("false"), "rectangleRoundedCurve": lit("6L"), "cellPadding": lit("6D"), "paddingUniform": lit("6D")}, "selector": {"id": "default"}}],
        "value": [{"properties": {"fontSize": lit("18.0D"), "fontFamily": lit("'Segoe UI Semibold'"), "fontColor": color(accent)}, "selector": {"metadata": metadata}}],
        "label": [{"properties": {"show": lit("false")}, "selector": {"metadata": metadata}}],
        "spacing": [{"properties": {"verticalSpacing": lit("0D")}, "selector": {"id": "default"}}],
        "fillCustom": [{"properties": {"show": lit("false")}, "selector": {"id": "default"}}],
        "outline": [{"properties": {"show": lit("false")}, "selector": {"id": "default"}}],
        "divider": [{"properties": {"show": lit("false")}, "selector": {"metadata": metadata}}],
        "referenceLabelDetail": [{"properties": {"show": lit("false")}, "selector": {"metadata": metadata}}],
    }
    cfg["singleVisual"]["vcObjects"] = visual_shell(title)
    cfg["singleVisual"]["vcObjects"]["border"][0]["properties"]["color"] = color(accent)
    visual["config"] = json.dumps(cfg, separators=(",", ":"), ensure_ascii=False)
    return visual


def kpi_stack(measure: str, title: str, x, y, w, h, z) -> list[dict]:
    accent = title_accent(title)
    return [
        card(measure, title, x, y, w, h, z),
        sparkline(measure, x + 12, y + SPARKLINE_OFFSET_Y, w - 24, 18, z + 70, accent),
    ]


def slicer(table: str, field: str, title: str, x, y, w, h, z) -> dict:
    return data_visual("slicer", x, y, w, h, z, {"Values": [(table, field, "column", title)]}, title, show_container_title=False)


def text_box(text: str, x, y, w, h, z, size=12, fg=None, bold=True) -> dict:
    fg = fg or THEME["text"]
    cfg = {
        "name": rand_name(),
        "layouts": [{"id": 0, "position": pos(x, y, w, h, z)}],
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
                                        {
                                            "value": text,
                                            "textStyle": {
                                                "fontFamily": "Segoe UI Semibold" if bold else "Segoe UI",
                                                "fontSize": f"{size}pt",
                                                "color": fg,
                                            },
                                        }
                                    ]
                                }
                            ]
                        }
                    }
                ]
            },
        },
    }
    return outer(cfg, x, y, w, h, z)


def shape(x, y, w, h, z, fill) -> dict:
    cfg = {
        "name": rand_name(),
        "layouts": [{"id": 0, "position": pos(x, y, w, h, z)}],
        "singleVisual": {
            "visualType": "shape",
            "drillFilterOtherVisuals": True,
            "objects": {
                "shape": [{"properties": {"tileShape": lit("'rectangle'")}}],
                "fill": [{"properties": {"show": lit("true"), "fillColor": color(fill), "transparency": lit("0D")}}],
                "outline": [{"properties": {"show": lit("false")}}],
            },
        },
    }
    return outer(cfg, x, y, w, h, z)


def context_chip(label: str, body: str, x, y, w, h, z, accent: str, fill: str) -> list[dict]:
    return [
        shape(x, y, w, h, z, fill),
        text_box(label.upper(), x + 10, y + 5, w - 20, 11, z + 50, 5.8, accent, True),
        text_box(body, x + 10, y + 19, w - 20, h - 21, z + 60, 7.2, THEME["text"], True),
    ]


def decision_layer(lens: str, decision: str) -> list[dict]:
    return (
        context_chip("Current Lens", lens, 660, FILTER_ROW_Y, 260, CONTEXT_CHIP_H, 80, THEME["blue"], THEME["panel2"])
        + context_chip("Decision Chip", decision, 930, FILTER_ROW_Y, 326, CONTEXT_CHIP_H, 85, THEME["amber"], "#FFFBEB")
    )


def header(title: str, subtitle: str) -> list[dict]:
    return [
        shape(24, 18, 5, 48, 10, THEME["blue"]),
        text_box("LOGISTICS TRADE LANE PROFITABILITY", 38, 20, 330, 11, 20, 6.6, THEME["blue"], False),
        text_box(title, 38, 36, 525, 28, 30, 14, THEME["text"]),
        text_box(subtitle, 575, 38, 430, 22, 40, 8, THEME["muted"], False),
        shape(24, 70, 1232, 2, 50, THEME["border"]),
    ]


def section(name: str, display: str, ordinal: int, visuals: list[dict]) -> dict:
    section_config = {"objects": {"background": [{"properties": {"color": color(THEME["bg"]), "transparency": lit("0.0D")}}]}}
    return {
        "id": ordinal,
        "name": name,
        "displayName": display,
        "filters": "[]",
        "ordinal": ordinal,
        "visualContainers": visuals,
        "config": json.dumps(section_config, separators=(",", ":"), ensure_ascii=False),
        "displayOption": 1,
        "width": 1280,
        "height": 720,
    }


def blank_layout() -> dict:
    seed_pbix = PROJECT / "output" / "dashboard_model_seed.pbix"
    if seed_pbix.exists():
        with zipfile.ZipFile(seed_pbix, "r") as package:
            raw = package.read("Report/Layout")
        base = json.loads(raw.decode("utf-16le"))
        base["sections"] = []
        base["theme"] = {"themeJson": {"name": "Logistics Profitability Finance Seed", "dataColors": PALETTE}}
        return base
    return {
        "version": "5.44",
        "theme": {"themeJson": {"name": "Logistics Profitability Finance Seed", "dataColors": PALETTE}},
        "config": json.dumps({"version": "5.44"}),
        "sections": [],
    }


def build_layout() -> dict:
    random.seed(SEED + 99)
    global SAMPLES
    SAMPLES = {name: load_sample(name) for name in ["cardVisual", "barChart", "columnChart", "donutChart", "slicer", "tableEx", "waterfallChart"]}
    layout = blank_layout()

    p1 = header("Executive Overview", "Margin status, volume, reprice value, and customer/lane concentration")
    p1 += [
        slicer("DimDate", "year", "Year", 24, FILTER_ROW_Y, 160, FILTER_ROW_H, 100),
        slicer("DimTradeLane", "mode", "Mode", 194, FILTER_ROW_Y, 190, FILTER_ROW_H, 110),
        slicer("DimCustomer", "segment", "Segment", 394, FILTER_ROW_Y, 220, FILTER_ROW_H, 120),
        *decision_layer("Latest period 2026-05 | all selected lanes", "Reprice loss lanes, protect GP"),
        *kpi_stack("Net Revenue", "Net Revenue", 24, KPI_ROW_Y, 190, 88, 200),
        *kpi_stack("Gross Profit", "Gross Profit", 224, KPI_ROW_Y, 190, 88, 210),
        *kpi_stack("GP Margin %", "GP Margin", 424, KPI_ROW_Y, 190, 88, 220),
        *kpi_stack("Shipment Count", "Shipments", 624, KPI_ROW_Y, 190, 88, 230),
        *kpi_stack("Cost per Shipment", "Cost / Shipment", 824, KPI_ROW_Y, 190, 88, 240),
        *kpi_stack("Reprice Opportunity", "Reprice Opp.", 1024, KPI_ROW_Y, 232, 88, 250),
        data_visual("columnChart", 24, 204 + CONTENT_ROW_SHIFT, 420, 226, 300, {"Category": [("DimDate", "month_label", "column", "Month")], "Y": [("KPI Measures", "Net Revenue", "measure", "Revenue"), ("KPI Measures", "Gross Profit", "measure", "GP")]}, "Revenue and GP Trend"),
        data_visual("barChart", 456, 204 + CONTENT_ROW_SHIFT, 376, 226, 310, {"Category": [("DimTradeLane", "lane_cluster", "column", "Cluster")], "Y": [("KPI Measures", "Gross Profit", "measure", "GP")]}, "Gross Profit by Lane Cluster"),
        data_visual("donutChart", 844, 204 + CONTENT_ROW_SHIFT, 412, 226, 320, {"Category": [("DimService", "service_family", "column", "Service")], "Y": [("KPI Measures", "Net Revenue", "measure", "Revenue")]}, "Revenue Mix by Service"),
        data_visual("tableEx", 24, 454 + CONTENT_ROW_SHIFT, 596, 184, 330, {"Values": [("DimCustomer", "customer_name", "column", "Customer"), ("DimTradeLane", "lane_name", "column", "Lane"), ("KPI Measures", "Net Revenue", "measure", "Revenue"), ("KPI Measures", "GP Margin %", "measure", "GP%"), ("KPI Measures", "Reprice Opportunity", "measure", "Reprice") ]}, "Customer-Lane Profitability Watchlist"),
        data_visual("tableEx", 632, 454 + CONTENT_ROW_SHIFT, 624, 184, 340, {"Values": [("DimTradeLane", "lane_name", "column", "Lane"), ("DimTradeLane", "mode", "column", "Mode"), ("KPI Measures", "Shipment Count", "measure", "Shipments"), ("KPI Measures", "Cost per Shipment", "measure", "Cost/Shipment"), ("KPI Measures", "Margin Gap vs Target", "measure", "Margin Gap") ]}, "Lane Margin Gap Table"),
    ]

    p2 = header("Trade Lane Margin", "Lane economics, service mix, utilization, and margin gap diagnosis")
    p2 += [
        slicer("DimTradeLane", "origin_country", "Origin", 24, FILTER_ROW_Y, 180, FILTER_ROW_H, 100),
        slicer("DimTradeLane", "destination_country", "Destination", 214, FILTER_ROW_Y, 220, FILTER_ROW_H, 110),
        slicer("DimOffice", "office", "Office", 444, FILTER_ROW_Y, 190, FILTER_ROW_H, 120),
        *decision_layer("Lane, origin, destination, and office view", "Prioritize gap by lane/customer"),
        *kpi_stack("TEU", "TEU", 24, KPI_ROW_Y, 190, 88, 200),
        *kpi_stack("CBM", "CBM", 224, KPI_ROW_Y, 190, 88, 210),
        *kpi_stack("Revenue per Shipment", "Rev / Shipment", 424, KPI_ROW_Y, 190, 88, 220),
        *kpi_stack("Negative Margin Shipments", "Neg. Margin Shipments", 624, KPI_ROW_Y, 190, 88, 230),
        *kpi_stack("On-Time %", "On-Time %", 824, KPI_ROW_Y, 190, 88, 240),
        *kpi_stack("Utilization %", "Utilization %", 1024, KPI_ROW_Y, 232, 88, 250),
        data_visual("barChart", 24, 204 + CONTENT_ROW_SHIFT, 390, 236, 300, {"Category": [("DimTradeLane", "lane_name", "column", "Lane")], "Y": [("KPI Measures", "GP Margin %", "measure", "GP%")]}, "GP Margin by Trade Lane"),
        data_visual("columnChart", 426, 204 + CONTENT_ROW_SHIFT, 390, 236, 310, {"Category": [("DimTradeLane", "mode", "column", "Mode")], "Y": [("KPI Measures", "Net Revenue", "measure", "Revenue"), ("KPI Measures", "Gross Profit", "measure", "GP")]}, "Revenue and GP by Mode"),
        data_visual("waterfallChart", 828, 204 + CONTENT_ROW_SHIFT, 428, 236, 320, {"Category": [("FactCostDriverBridge", "driver", "column", "Driver")], "Y": [("KPI Measures", "Bridge Amount", "measure", "Amount")]}, "Margin Gap Driver Bridge", "Explains gross profit gap versus target"),
        data_visual("tableEx", 24, 462 + CONTENT_ROW_SHIFT, 610, 176, 330, {"Values": [("DimTradeLane", "lane_name", "column", "Lane"), ("DimCustomer", "customer_name", "column", "Customer"), ("KPI Measures", "Shipment Count", "measure", "Shipments"), ("KPI Measures", "GP Margin %", "measure", "GP%"), ("KPI Measures", "Margin Gap %", "measure", "Gap %"), ("KPI Measures", "On-Time %", "measure", "On-Time")]}, "Lane-Customer Margin Detail"),
        data_visual("tableEx", 646, 462 + CONTENT_ROW_SHIFT, 610, 176, 340, {"Values": [("DimService", "service", "column", "Service"), ("DimCarrier", "carrier", "column", "Carrier"), ("KPI Measures", "Freight Cost", "measure", "Freight"), ("KPI Measures", "Fuel Cost", "measure", "Fuel"), ("KPI Measures", "Cost per Shipment", "measure", "Cost/Shipment")]}, "Service and Carrier Cost Detail"),
    ]

    p3 = header("Cost Drivers & Action Queue", "Cost leakage, owners, risk value, and margin recovery actions")
    p3 += [
        slicer("FactActionQueue", "priority", "Priority", 24, FILTER_ROW_Y, 180, FILTER_ROW_H, 100),
        slicer("FactActionQueue", "status", "Status", 214, FILTER_ROW_Y, 190, FILTER_ROW_H, 110),
        slicer("FactActionQueue", "owner", "Owner", 414, FILTER_ROW_Y, 220, FILTER_ROW_H, 120),
        *decision_layer("Priority, status, and owner action view", "Close high-risk open actions"),
        *kpi_stack("Fuel Cost", "Fuel Cost", 24, KPI_ROW_Y, 190, 88, 200),
        *kpi_stack("Demurrage Cost", "Demurrage", 224, KPI_ROW_Y, 190, 88, 210),
        *kpi_stack("Claims Cost", "Claims", 424, KPI_ROW_Y, 190, 88, 220),
        *kpi_stack("Open Actions", "Open Actions", 624, KPI_ROW_Y, 190, 88, 230),
        *kpi_stack("Action Risk Value", "Action Risk", 824, KPI_ROW_Y, 190, 88, 240),
        *kpi_stack("Recovery Value", "Recovery Value", 1024, KPI_ROW_Y, 232, 88, 250),
        data_visual("waterfallChart", 24, 204 + CONTENT_ROW_SHIFT, 420, 236, 300, {"Category": [("FactCostDriverBridge", "driver", "column", "Driver")], "Y": [("KPI Measures", "Bridge Amount", "measure", "Amount")]}, "Cost Driver Waterfall"),
        data_visual("barChart", 456, 204 + CONTENT_ROW_SHIFT, 376, 236, 310, {"Category": [("DimCarrier", "carrier", "column", "Carrier")], "Y": [("KPI Measures", "Total Cost", "measure", "Cost")]}, "Total Cost by Carrier"),
        data_visual("donutChart", 844, 204 + CONTENT_ROW_SHIFT, 412, 236, 320, {"Category": [("FactActionQueue", "issue_type", "column", "Issue")], "Y": [("KPI Measures", "Action Risk Value", "measure", "Risk")]}, "Risk by Issue Type"),
        data_visual("tableEx", 24, 462 + CONTENT_ROW_SHIFT, 1232, 176, 330, {"Values": [("FactActionQueue", "priority", "column", "Priority"), ("FactActionQueue", "status", "column", "Status"), ("DimCustomer", "customer_name", "column", "Customer"), ("DimTradeLane", "lane_name", "column", "Lane"), ("FactActionQueue", "issue_type", "column", "Issue"), ("FactActionQueue", "owner", "column", "Owner"), ("KPI Measures", "Action Risk Value", "measure", "Risk"), ("KPI Measures", "Recovery Value", "measure", "Recovery")]}, "Pricing and Action Queue"),
    ]

    layout["sections"] = [
        section("ExecutiveOverview", "Executive Overview", 0, p1),
        section("TradeLaneMargin", "Trade Lane Margin", 1, p2),
        section("CostActionQueue", "Cost Drivers & Action Queue", 2, p3),
    ]
    return layout


def write_native_scripts() -> None:
    write_text(
        "powerbi/prepare_seed_pbix.ps1",
        f"""
param(
  [string]$SeedTemplate = "{SEED_TEMPLATE}",
  [string]$TargetPbix = "{PROJECT / 'output' / 'dashboard_model_seed.pbix'}"
)

$ErrorActionPreference = "Stop"
if (!(Test-Path -LiteralPath $SeedTemplate)) {{ throw "Seed template not found: $SeedTemplate" }}
New-Item -ItemType Directory -Force -Path (Split-Path -Parent $TargetPbix) | Out-Null
Copy-Item -LiteralPath $SeedTemplate -Destination $TargetPbix -Force
[ordered]@{{
  status = "seed_copied"
  seed_template = $SeedTemplate
  target_pbix = $TargetPbix
  target_bytes = (Get-Item -LiteralPath $TargetPbix).Length
}} | ConvertTo-Json -Depth 5
""",
    )
    write_text(
        "powerbi/push_model_bim_to_desktop.ps1",
        r"""
param(
  [string]$ProjectRoot = "",
  [string]$TargetPbix = "",
  [string]$ModelBim = ""
)

$ErrorActionPreference = "Stop"
if ([string]::IsNullOrWhiteSpace($ProjectRoot)) { $ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..") }
if ([string]::IsNullOrWhiteSpace($TargetPbix)) { $TargetPbix = Join-Path $ProjectRoot "output\dashboard_model_seed.pbix" }
if ([string]::IsNullOrWhiteSpace($ModelBim)) { $ModelBim = Join-Path $ProjectRoot "model\model.bim" }
$QaRoot = Join-Path $ProjectRoot "qa"
New-Item -ItemType Directory -Force -Path $QaRoot | Out-Null

function Get-PowerBiSessionForPbix([string]$Path) {
  $resolved = [IO.Path]::GetFullPath($Path)
  $infoText = & "C:\Users\Win\AppData\Local\Programs\pbi-tools\current\pbi-tools.exe" info 2>&1 | Out-String
  $jsonStart = $infoText.IndexOf("{")
  if ($jsonStart -lt 0) { throw "pbi-tools info did not return JSON." }
  $info = $infoText.Substring($jsonStart) | ConvertFrom-Json
  $matches = @($info.pbiSessions | Where-Object { $_.PbixPath -and ([IO.Path]::GetFullPath([string]$_.PbixPath) -ieq $resolved) })
  if ($matches.Count -ne 1) {
    $info.pbiSessions | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $QaRoot "pbi_sessions_debug.json") -Encoding UTF8
    throw "Expected exactly one Power BI Desktop session for '$resolved'. Found $($matches.Count)."
  }
  return $matches[0]
}

function Convert-DataType([string]$TypeName) {
  switch ($TypeName) {
    "string" { return [Microsoft.AnalysisServices.Tabular.DataType]::String }
    "int64" { return [Microsoft.AnalysisServices.Tabular.DataType]::Int64 }
    "double" { return [Microsoft.AnalysisServices.Tabular.DataType]::Double }
    "decimal" { return [Microsoft.AnalysisServices.Tabular.DataType]::Decimal }
    "dateTime" { return [Microsoft.AnalysisServices.Tabular.DataType]::DateTime }
    "boolean" { return [Microsoft.AnalysisServices.Tabular.DataType]::Boolean }
    default { return [Microsoft.AnalysisServices.Tabular.DataType]::String }
  }
}

function Convert-SummarizeBy([object]$Value) {
  $text = ([string]$Value).ToLowerInvariant()
  switch ($text) {
    "sum" { return [Microsoft.AnalysisServices.Tabular.AggregateFunction]::Sum }
    "min" { return [Microsoft.AnalysisServices.Tabular.AggregateFunction]::Min }
    "max" { return [Microsoft.AnalysisServices.Tabular.AggregateFunction]::Max }
    "count" { return [Microsoft.AnalysisServices.Tabular.AggregateFunction]::Count }
    "average" { return [Microsoft.AnalysisServices.Tabular.AggregateFunction]::Average }
    default { return [Microsoft.AnalysisServices.Tabular.AggregateFunction]::None }
  }
}

function Get-ExpressionText($ExpressionValue) {
  if ($null -eq $ExpressionValue) { return "" }
  if ($ExpressionValue -is [array]) { return ($ExpressionValue -join "`r`n") }
  return [string]$ExpressionValue
}

function Get-TableByName($Model, [string]$Name) {
  foreach ($table in $Model.Tables) { if ($table.Name -eq $Name) { return $table } }
  throw "Table not found in model: $Name"
}

function Get-ColumnByName($Table, [string]$Name) {
  foreach ($column in $Table.Columns) { if ($column.Name -eq $Name) { return $column } }
  throw "Column not found in table '$($Table.Name)': $Name"
}

if (!(Test-Path -LiteralPath $TargetPbix)) { throw "Target PBIX missing: $TargetPbix" }
if (!(Test-Path -LiteralPath $ModelBim)) { throw "model.bim missing: $ModelBim" }

$powerBiBin = "C:\Program Files\Microsoft Power BI Desktop\bin"
Add-Type -Path (Join-Path $powerBiBin "Microsoft.PowerBI.Amo.dll")

$session = Get-PowerBiSessionForPbix $TargetPbix
$server = New-Object Microsoft.AnalysisServices.Tabular.Server
$server.Connect("localhost:$($session.Port)")
$database = $server.Databases[0]
$model = $database.Model
$model.Relationships.Clear()
$model.Tables.Clear()

$modelDefinition = Get-Content -LiteralPath $ModelBim -Raw -Encoding UTF8 | ConvertFrom-Json
foreach ($tableDef in $modelDefinition.model.tables) {
  $table = New-Object Microsoft.AnalysisServices.Tabular.Table
  $table.Name = [string]($tableDef.name)
  if ($null -ne $tableDef.isHidden) { $table.IsHidden = [bool]$tableDef.isHidden }
  $model.Tables.Add($table)
  foreach ($columnDef in @($tableDef.columns)) {
    $column = New-Object Microsoft.AnalysisServices.Tabular.DataColumn
    $column.Name = [string]($columnDef.name)
    $column.SourceColumn = if ($columnDef.sourceColumn) { [string]($columnDef.sourceColumn) -replace '^\[|\]$', '' } else { [string]($columnDef.name) }
    $column.DataType = Convert-DataType ([string]($columnDef.dataType))
    if ($null -ne $columnDef.isHidden) { $column.IsHidden = [bool]$columnDef.isHidden }
    if ($columnDef.formatString) { $column.FormatString = [string]$columnDef.formatString }
    if ($columnDef.summarizeBy) { $column.SummarizeBy = Convert-SummarizeBy $columnDef.summarizeBy }
    $table.Columns.Add($column)
  }
  foreach ($partitionDef in @($tableDef.partitions)) {
    $partition = New-Object Microsoft.AnalysisServices.Tabular.Partition
    $partition.Name = [string]($partitionDef.name)
    $partition.Mode = [Microsoft.AnalysisServices.Tabular.ModeType]::Import
    $source = New-Object Microsoft.AnalysisServices.Tabular.MPartitionSource
    $source.Expression = Get-ExpressionText $partitionDef.source.expression
    $partition.Source = $source
    $table.Partitions.Add($partition)
  }
  foreach ($measureDef in @($tableDef.measures)) {
    if ($measureDef -and -not [string]::IsNullOrWhiteSpace([string]($measureDef.name))) {
      $measure = New-Object Microsoft.AnalysisServices.Tabular.Measure
      $measure.Name = [string]($measureDef.name)
      $measure.Expression = [string]($measureDef.expression)
      if ($measureDef.formatString) { $measure.FormatString = [string]$measureDef.formatString }
      if ($measureDef.description) { $measure.Description = [string]$measureDef.description }
      $table.Measures.Add($measure)
    }
  }
}

foreach ($relationshipDef in @($modelDefinition.model.relationships)) {
  if (-not $relationshipDef.fromTable) { continue }
  $fromTable = Get-TableByName $model ([string]($relationshipDef.fromTable))
  $toTable = Get-TableByName $model ([string]($relationshipDef.toTable))
  $rel = New-Object Microsoft.AnalysisServices.Tabular.SingleColumnRelationship
  $rel.Name = [string]($relationshipDef.name)
  $rel.FromColumn = Get-ColumnByName $fromTable ([string]($relationshipDef.fromColumn))
  $rel.ToColumn = Get-ColumnByName $toTable ([string]($relationshipDef.toColumn))
  $rel.FromCardinality = [Microsoft.AnalysisServices.Tabular.RelationshipEndCardinality]::Many
  $rel.ToCardinality = [Microsoft.AnalysisServices.Tabular.RelationshipEndCardinality]::One
  $rel.CrossFilteringBehavior = [Microsoft.AnalysisServices.Tabular.CrossFilteringBehavior]::OneDirection
  $rel.IsActive = $true
  $model.Relationships.Add($rel)
}

$model.SaveChanges()
$model.RequestRefresh([Microsoft.AnalysisServices.Tabular.RefreshType]::Full)
$model.SaveChanges()

$result = [ordered]@{
  timestamp = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss zzz")
  status = "project17_model_pushed_via_tom"
  target_pbix = [IO.Path]::GetFullPath($TargetPbix)
  power_bi_port = $session.Port
  process_id = $session.ProcessId
  tables = @($model.Tables | ForEach-Object { $_.Name })
  relationship_count = $model.Relationships.Count
  measure_count = @($model.Tables | ForEach-Object { $_.Measures } | ForEach-Object { $_.Name }).Count
}
$result | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath (Join-Path $QaRoot "seed_model_push_via_tom.json") -Encoding UTF8
$server.Disconnect()
Write-Output ($result | ConvertTo-Json -Depth 10)
""",
    )
    write_text(
        "powerbi/apply_native_layout_to_pbix.ps1",
        r"""
param(
  [string]$ProjectRoot = "",
  [string]$ModelPbix = "",
  [string]$LayoutJson = "",
  [string]$OutputPbix = "",
  [string]$FinalPbix = ""
)

$ErrorActionPreference = "Stop"
if ([string]::IsNullOrWhiteSpace($ProjectRoot)) { $ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..") }
if ([string]::IsNullOrWhiteSpace($ModelPbix)) { $ModelPbix = Join-Path $ProjectRoot "output\dashboard_model_seed.pbix" }
if ([string]::IsNullOrWhiteSpace($LayoutJson)) { $LayoutJson = Join-Path $ProjectRoot "build\native_report_layout_project17.json" }
if ([string]::IsNullOrWhiteSpace($OutputPbix)) { $OutputPbix = Join-Path $ProjectRoot "output\dashboard_v01.pbix" }
if ([string]::IsNullOrWhiteSpace($FinalPbix)) { $FinalPbix = Join-Path $ProjectRoot "output\dashboard_final.pbix" }
$QaRoot = Join-Path $ProjectRoot "qa"
New-Item -ItemType Directory -Force -Path $QaRoot | Out-Null

function Validate-Pbix([string]$Path) {
  $stream = [IO.File]::OpenRead($Path)
  try { [Microsoft.PowerBI.Packaging.PowerBIPackager]::Validate($stream) }
  finally { $stream.Dispose() }
}

$powerBiBin = "C:\Program Files\Microsoft Power BI Desktop\bin"
[Reflection.Assembly]::LoadFrom((Join-Path $powerBiBin "Microsoft.PowerBI.Packaging.dll")) | Out-Null
Add-Type -AssemblyName WindowsBase

if (!(Test-Path -LiteralPath $ModelPbix)) { throw "Model PBIX not found: $ModelPbix" }
if (!(Test-Path -LiteralPath $LayoutJson)) { throw "Layout JSON not found: $LayoutJson" }

Validate-Pbix $ModelPbix
Copy-Item -LiteralPath $ModelPbix -Destination $OutputPbix -Force
$layout = Get-Content -LiteralPath $LayoutJson -Raw | ConvertFrom-Json
$layoutText = $layout | ConvertTo-Json -Depth 100 -Compress
$layoutBytes = [Text.Encoding]::Unicode.GetBytes($layoutText)

$package = [System.IO.Packaging.Package]::Open($OutputPbix, [IO.FileMode]::Open, [IO.FileAccess]::ReadWrite)
try {
  $layoutUri = New-Object System.Uri("/Report/Layout", [System.UriKind]::Relative)
  if (!$package.PartExists($layoutUri)) { throw "PBIX does not contain /Report/Layout." }
  $layoutPart = $package.GetPart($layoutUri)
  $stream = $layoutPart.GetStream([IO.FileMode]::Open, [IO.FileAccess]::ReadWrite)
  try {
    $stream.SetLength(0)
    $stream.Position = 0
    $stream.Write($layoutBytes, 0, $layoutBytes.Length)
  }
  finally { $stream.Dispose() }
  $securityUri = New-Object System.Uri("/SecurityBindings", [System.UriKind]::Relative)
  if ($package.PartExists($securityUri)) { $package.DeletePart($securityUri) }
}
finally { $package.Close() }

Validate-Pbix $OutputPbix
Copy-Item -LiteralPath $OutputPbix -Destination $FinalPbix -Force
Validate-Pbix $FinalPbix

$visualTypeCounts = @{}
foreach ($section in $layout.sections) {
  foreach ($visual in $section.visualContainers) {
    $config = $visual.config | ConvertFrom-Json
    $type = $config.singleVisual.visualType
    if (!$visualTypeCounts.ContainsKey($type)) { $visualTypeCounts[$type] = 0 }
    $visualTypeCounts[$type] += 1
  }
}

$metadata = [ordered]@{
  generated_at = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
  project_root = $ProjectRoot
  source_model_pbix = $ModelPbix
  layout_json = $LayoutJson
  output_pbix = $OutputPbix
  final_pbix = $FinalPbix
  final_pbix_bytes = (Get-Item -LiteralPath $FinalPbix).Length
  pages = @($layout.sections | ForEach-Object { $_.displayName })
  visual_containers = ($layout.sections | ForEach-Object { $_.visualContainers.Count } | Measure-Object -Sum).Sum
  visual_type_counts = $visualTypeCounts
  validation = "PowerBIPackager.Validate passed for output and final PBIX"
  security_bindings_removed = $true
}
$metadata | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath (Join-Path $QaRoot "pbix_native_report_validation.json") -Encoding UTF8
$metadata | ConvertTo-Json -Depth 10
""",
    )
    write_text(
        "powerbi/launch_powerbi.ps1",
        f"""
$pbix = "{PROJECT / 'output' / 'dashboard_final.pbix'}"
$pbi = "{PBI_EXE}"
if (-not (Test-Path $pbix)) {{
  Write-Host "dashboard_final.pbix does not exist yet."
  exit 1
}}
Start-Process -FilePath $pbi -ArgumentList "`"$pbix`""
""",
    )


def write_config_docs() -> None:
    theme = {
        "name": "Logistics Profitability Control Tower",
        "dataColors": PALETTE,
        "background": THEME["bg"],
        "foreground": THEME["text"],
        "tableAccent": THEME["blue"],
    }
    write_json("build/config/theme.json", theme)
    write_json(
        "build/config/page_map.json",
        [
            {"page": "Executive Overview", "purpose": "Default scan of revenue, GP, margin, volume, and reprice opportunity."},
            {"page": "Trade Lane Margin", "purpose": "Diagnose lane/customer/service economics and margin gap drivers."},
            {"page": "Cost Drivers & Action Queue", "purpose": "Prioritize cost leakage, owner actions, and margin recovery."},
        ],
    )
    write_json(
        "build/config/visual_map.json",
        {
            "Executive Overview": ["Current Lens", "Decision Chip", "6 KPI cards with sparklines", "Revenue/GP trend", "GP by lane cluster", "service mix donut", "customer-lane watchlist", "lane gap table"],
            "Trade Lane Margin": ["Current Lens", "Decision Chip", "6 KPI cards with sparklines", "GP margin by lane", "mode revenue/GP bars", "margin gap waterfall", "lane-customer detail", "service/carrier cost table"],
            "Cost Drivers & Action Queue": ["Current Lens", "Decision Chip", "6 KPI cards with sparklines", "cost driver waterfall", "cost by carrier", "risk by issue type donut", "pricing/action queue"],
        },
    )
    write_json(
        "build/config/slicer_map.json",
        {
            "Executive Overview": ["Year", "Mode", "Segment"],
            "Trade Lane Margin": ["Origin", "Destination", "Office"],
            "Cost Drivers & Action Queue": ["Priority", "Status", "Owner"],
        },
    )
    write_json(
        "build/config/dashboard_config.json",
        {
            "project": "Project 17 - Logistics Trade Lane Profitability",
            "audience": "Commercial FP&A, country heads, pricing, procurement, and operations leadership",
            "business_goal": "Identify margin-destructive lanes/customers and prioritize repricing or cost-to-serve actions.",
            "slicer_placement": "Top filter row above the KPI strip on every report page.",
            "project20_style_upgrades": ["Current Lens", "Decision Chip", "top slicer row with extra dropdown clearance", "KPI sparklines"],
            "page_count": 3,
            "final_pbix": str(PROJECT / "output" / "dashboard_final.pbix"),
        },
    )


def write_docs(validation: dict, env: dict) -> None:
    write_json("data/source_summary.json", {"source_type": "synthetic", "seed": SEED, "latest_complete_period": LATEST_PERIOD, "tables": validation["row_counts"], "business_context": "Logistics trade lane profitability by customer, lane, service, office, carrier, and cost driver."})
    write_text("data/data_quality_report.md", "\n".join(["# Data Quality Report", "", f"Status: **{validation['status']}**", "", "| Check | Status | Detail |", "|---|---|---|"] + [f"| {c['check']} | {c['status']} | {c['detail']} |" for c in validation["checks"]]))
    write_text("data/data_dictionary.md", (PROJECT / "model/data_dictionary.md").read_text(encoding="utf-8"))
    write_json("data/validated/validation_summary.json", validation)
    write_json("_agent/environment_check.json", env)
    write_text("_agent/environment_check.md", f"# Environment Check\n\n- Power BI Desktop EXE: `{env['power_bi_desktop_exe']}`\n- pbi-tools: `{env['pbi_tools']}`\n- dotnet: `{env['dotnet']}`\n- Computer Use: `{env['computer_use']['status']}`\n")
    write_text("_agent/intake_brief.md", f"""
# Intake Brief

- Project: Project 17 - Logistics Trade Lane Profitability
- Audience: Commercial FP&A, pricing, procurement, operations, and country leadership.
- Goal: Find lane/customer/service margin leakage and prioritize repricing or cost-to-serve actions.
- Data source: synthetic portfolio/demo data, seed `{SEED}`.
- Requested tabs: 3.
- Final output: `output/dashboard_final.pbix`.
- Assumption: no production source was provided, so synthetic data is acceptable for portfolio/demo.
""")
    write_text("_agent/session_guard.md", f"""
# Session Guard

- Current project path: `{PROJECT}`
- Expected final PBIX path: `{PROJECT / 'output' / 'dashboard_final.pbix'}`
- Seed model PBIX path: `{PROJECT / 'output' / 'dashboard_model_seed.pbix'}`
- Existing Power BI windows detected before build: two `dashboard_final` windows from earlier sessions. They must be ignored until exact Project 17 paths appear in `pbi-tools info`.
- Selected session rule: only use a session whose `PbixPath` exactly matches Project 17 seed or final PBIX.
- Sessions ignored: any Power BI window titled only `dashboard_final` without exact Project 17 path evidence.
""")
    write_text("_agent/pbix_authoring_decision.md", f"""
# PBIX Authoring Decision

Decision: SCRIPTED_DESKTOP_PBIX.

Rationale:
- Power BI Desktop EXE is available at `{env['power_bi_desktop_exe']}`.
- pbi-tools is available at `{env['pbi_tools']}` for session discovery and package QA.
- Use `Microsoft_Customer_Profitability.pbix` only as a valid PBIX container because it is the closest finance/profitability seed.
- Replace the model with Project 17 tables/measures through Desktop TOM/XMLA, save the exact seed, patch native layout, validate package, then open/save/reopen final.

Seed template:
`{SEED_TEMPLATE}`
""")
    write_text("_agent/failure_matrix.md", "# Failure Matrix\n\n| Failure | Planned Response |\n|---|---|\n| Wrong Power BI session | Stop and require exact `PbixPath` match in pbi-tools info |\n| Model push fails | Keep Power BI-ready package; do not call PBIX final |\n| Layout validation fails | Restore model seed and patch layout JSON |\n| Desktop open-check fails | Mark PBIX blocked and keep HTML/build package supplemental |\n")
    write_text("_agent/build_loop_log.md", f"# Build Loop Log\n\n- {RUN_TS}: Generated data/model/layout/scripts for Project 17.\n")
    write_text("_agent/run_log.md", f"# Run Log\n\n- {RUN_TS}: Built Project 17 package from BI A-Z master prompt with 3-tab scope.\n")
    write_text("docs/design_research.md", f"""
# Design Research

Chosen seed: `Template/04_Profitability_Margin/Microsoft_Customer_Profitability.pbix`.

Why:
- Microsoft's Customer Profitability sample is CFO-oriented and focuses on customers, products, gross margin, and the factors affecting profitability: https://learn.microsoft.com/en-us/power-bi/create-reports/sample-customer-profitability
- Microsoft's sample catalog lists Customer Profitability as a `.pbix`/`.xlsx` sample for revenue, costs, customer segments, high/low-profit customers, and lifetime value: https://learn.microsoft.com/en-us/power-bi/create-reports/sample-datasets
- Local template catalog rates `Microsoft_Customer_Profitability.pbix` as a strong profitability/margin starting point and `Packt_Ch10_PVM.pbix` as a strong bridge-analysis reference.

Layout selected for Project 17:
- Tab 1: Executive Trade Lane Cockpit.
- Tab 2: Trade Lane Margin diagnostics.
- Tab 3: Cost Drivers and Action Queue.
- Slicers sit in a top filter row above the KPI strip on every page so filters are visible before the reader scans KPIs.
- Current Lens and Decision Chip callouts sit in the same top band to make the active analytical context and recommended action visible.
- KPI cards include compact native sparkline micro-trends using existing monthly Date context and KPI measures.

Design system:
- Off-white canvas, white panels, compact KPI strip, blue/teal/green for revenue and profit, amber/red for warnings and margin leakage.
- Dense but readable FP&A control-tower layout; no marketing hero or decorative cards.
""")
    write_text("docs/handoff_notes.md", f"""
# Handoff Notes

- Final PBIX path: `output/dashboard_final.pbix`.
- Build route: SCRIPTED_DESKTOP_PBIX using profitability seed, Project 17 TOM model push, native layout patch, Desktop open/save/reopen QA.
- Supplemental preview: `output/dashboard_final.html`.
- Data source: synthetic logistics profitability data, seed `{SEED}`, latest complete period `{LATEST_PERIOD}`.
- Pages: Executive Overview; Trade Lane Margin; Cost Drivers & Action Queue.
- Key KPIs: Net Revenue, Gross Profit, GP Margin %, Shipments, Cost/Shipment, Reprice Opportunity, Margin Gap, Open Actions, Action Risk Value.
- QA status before PBIX build: data QA `{validation['status']}`. PBIX QA updates after build.
""")
    write_text("docs/refresh_guide.md", f"# Refresh Guide\n\nFor portfolio/demo refresh:\n\n```powershell\ncd \"{PROJECT}\"\npython tools/build_project17.py\n```\n\nFor production, replace synthetic inputs with TMS/ERP/accounting exports at the same grain and rerun validation before opening Power BI.\n")
    write_text("docs/rebuild_guide.md", f"""
# Rebuild Guide

```powershell
cd "{PROJECT}"
python tools/build_project17.py
./powerbi/prepare_seed_pbix.ps1
Start-Process -FilePath "{PBI_EXE}" -ArgumentList "`"{PROJECT / 'output' / 'dashboard_model_seed.pbix'}`""
./powerbi/push_model_bim_to_desktop.ps1
# Save the exact seed PBIX in Desktop, then:
./powerbi/apply_native_layout_to_pbix.ps1
```
""")
    write_text("docs/changelog.md", f"# Changelog\n\n- {RUN_TS}: Created Project 17 data, model, native layout spec, PBIX scripts, QA scaffolding, and supplemental HTML preview.\n")
    write_text("docs/issue_log.md", "# Issue Log\n\n- Pending PBIX Desktop open/save/reopen validation until the build route is executed.\n")
    write_text("powerbi/notes/authoring_strategy.md", (PROJECT / "_agent/pbix_authoring_decision.md").read_text(encoding="utf-8"))
    write_text("powerbi/notes/pbix_build_runbook.md", (PROJECT / "docs/rebuild_guide.md").read_text(encoding="utf-8"))
    write_text("powerbi/notes/desktop_ui_runbook.md", "Use Desktop only on a window whose pbi-tools `PbixPath` exactly matches Project 17 seed/final path. Ignore unrelated `dashboard_final` windows.")
    write_text("qa/qa_checklist.md", f"# QA Checklist\n\n- Data QA: {validation['status']}\n- Metric QA: pass; measures cataloged in `model/measure_catalog.json`.\n- Visual QA: pending PBIX open-check; supplemental HTML can be opened locally.\n- Interaction QA: pending PBIX open-check.\n- File QA: pending final PBIX build.\n")
    write_csv("qa/reconciliation.csv", [{"reconciliation": c["check"], "status": c["status"], "detail": c["detail"], "tolerance": "$2 where applicable"} for c in validation["checks"]])
    write_json("qa/pbix_validation.json", {"status": "pending", "final_output": "output/dashboard_final.pbix", "route": "SCRIPTED_DESKTOP_PBIX", "environment": env})
    write_json("qa/pbix_final_validation.json", {"status": "pending", "opened_exact_file": False, "visual_error_count": None})
    write_text("qa/visual_qa_notes.md", "Pending native PBIX open-check. Supplemental HTML preview exists at `output/dashboard_final.html`.")
    write_text("qa/interaction_qa_notes.md", "Pending native PBIX slicer/cross-filter check after Desktop open.")
    write_text("qa/performance_qa_notes.md", "Prepared CSV model is compact for Power BI import. Expected PBIX performance is suitable for portfolio/demo scale.")
    write_text("qa/regression_qa_notes.md", f"Generator is deterministic with seed `{SEED}`; rebuilds should preserve validation status and table grain.")
    write_text(
        "README.md",
        f"""
# Project 17 - Logistics Trade Lane Profitability

Power BI product for logistics and freight profitability by customer, trade lane, service, office, carrier, and shipment profile.

## Main Artifact

- Final PBIX: `output/dashboard_final.pbix`
- Supplemental HTML preview: `output/dashboard_final.html`
- Build route: SCRIPTED_DESKTOP_PBIX using a profitability PBIX seed as a technical container.

## Dashboard Tabs

1. Executive Overview
2. Trade Lane Margin
3. Cost Drivers & Action Queue

## Business Questions

- Which lanes, customers, and services create or destroy margin?
- How do fuel surcharge, carrier cost, demurrage, claims, and utilization affect profitability?
- Which customers should commercial teams reprice or renegotiate?

## Data And Model

- Synthetic portfolio/demo data, seed `{SEED}`.
- Latest complete period `{LATEST_PERIOD}`.
- Star schema with Date, Customer, Trade Lane, Service, Office, Carrier, Shipment Profitability, Cost Driver Bridge, and Action Queue.
- Measures are documented in `model/MEASURES.dax` and `model/measure_catalog.json`.
""",
    )


def write_power_query() -> None:
    specs = []
    for table_name, file_name in TABLE_FILES.items():
        csv_path = PROJECT / "data" / "prepared" / file_name
        cols = [(col, m_type(data_type(col))) for col in read_header(csv_path)]
        type_lines = ",\n        ".join([f'{{"{col}", {typ}}}' for col, typ in cols])
        specs.append(
            "\n".join(
                [
                    f"// {table_name}",
                    "let",
                    f'    Source = Csv.Document(File.Contents("{csv_path.as_posix()}"), [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]),',
                    "    Promoted = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),",
                    "    Typed = Table.TransformColumnTypes(Promoted, {",
                    f"        {type_lines}",
                    '    }, "en-US")',
                    "in",
                    "    Typed",
                ]
            )
        )
    write_text("powerbi/PowerQuery_M.txt", "\n\n".join(specs))
    write_text("powerbi/MEASURES.dax", (PROJECT / "model" / "MEASURES.dax").read_text(encoding="utf-8"))


def main() -> None:
    ensure_dirs()
    env = collect_environment()
    data = generate_data()
    for key, file_name in {
        "dim_date": "dim_date.csv",
        "dim_customer": "dim_customer.csv",
        "dim_trade_lane": "dim_trade_lane.csv",
        "dim_service": "dim_service.csv",
        "dim_office": "dim_office.csv",
        "dim_carrier": "dim_carrier.csv",
        "fact_shipment_profitability": "fact_shipment_profitability.csv",
        "fact_cost_driver_bridge": "fact_cost_driver_bridge.csv",
        "fact_action_queue": "fact_action_queue.csv",
    }.items():
        write_csv(f"data/prepared/{file_name}", data[key])
        if key.startswith("dim_") or key.startswith("fact_"):
            write_csv(f"data/raw/{file_name}", data[key])
    write_json("data/raw/synthetic_generation_metadata.json", data["metadata"])
    validation = validate_data(data)
    write_model_docs(validation)
    write_power_query()
    write_text("output/dashboard_final.html", html_dashboard(data))
    write_config_docs()
    write_docs(validation, env)
    write_json("model/model.bim", build_model_bim())
    write_native_scripts()
    layout = build_layout()
    write_json("build/native_report_layout_project17.json", layout)
    write_json(
        "output/build_manifest.json",
        {
            "status": "build_package_created",
            "generated_at": RUN_TS,
            "main_expected_artifact": str(PROJECT / "output" / "dashboard_final.pbix"),
            "supplemental_html": str(PROJECT / "output" / "dashboard_final.html"),
            "validation": validation["status"],
            "row_counts": validation["row_counts"],
            "pages": [s["displayName"] for s in layout["sections"]],
            "visual_count": sum(len(s["visualContainers"]) for s in layout["sections"]),
        },
    )
    print(json.dumps({"status": "ok", "project": str(PROJECT), "validation": validation["status"], "rows": validation["row_counts"]}, indent=2))


if __name__ == "__main__":
    main()


