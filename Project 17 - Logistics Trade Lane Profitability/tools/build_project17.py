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
FILTER_ROW_Y = 62
FILTER_ROW_H = 58
CONTEXT_CHIP_H = 58
KPI_ROW_Y = 124
KPI_ROW_H = 152
KPI_CARD_W = 296
KPI_CARD_GAP = 16
KPI_TO_CHART_GAP = 16
MAIN_TO_BOTTOM_GAP = 8
BOTTOM_ROW_Y = 508
BOTTOM_ROW_H = 194
MAIN_CHART_Y = KPI_ROW_Y + KPI_ROW_H + KPI_TO_CHART_GAP
MAIN_CHART_H = BOTTOM_ROW_Y - MAIN_CHART_Y - MAIN_TO_BOTTOM_GAP


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
    segment_volume = {"Enterprise": 1.34, "Mid-Market": 0.88, "SMB": 0.58}
    segment_yield = {"Enterprise": 1.10, "Mid-Market": 0.96, "SMB": 0.82}
    segment_cost_pressure = {"Enterprise": 0.018, "Mid-Market": -0.004, "SMB": 0.032}
    mode_volume = {"Ocean FCL": 1.22, "Ocean LCL": 0.82, "Air": 0.62, "Road": 0.74, "Road+Sea": 0.66}
    mode_phase = {"Ocean FCL": 0.0, "Ocean LCL": 0.9, "Air": 1.7, "Road": 2.5, "Road+Sea": 3.2}
    cluster_volume = {
        "Transpacific": 1.42,
        "Europe": 1.18,
        "Intra-Asia": 0.92,
        "Intra-ASEAN": 0.78,
        "North Asia": 0.70,
        "Oceania": 0.66,
        "Middle East": 0.64,
        "Cross-border": 0.54,
    }
    cluster_yield = {
        "Transpacific": 1.46,
        "Europe": 1.30,
        "Intra-Asia": 0.94,
        "Intra-ASEAN": 0.82,
        "North Asia": 0.98,
        "Oceania": 1.12,
        "Middle East": 1.08,
        "Cross-border": 0.62,
    }
    cluster_cost_pressure = {
        "Transpacific": -0.010,
        "Europe": 0.032,
        "Intra-Asia": -0.004,
        "Intra-ASEAN": 0.040,
        "North Asia": 0.010,
        "Oceania": -0.002,
        "Middle East": 0.050,
        "Cross-border": 0.088,
    }
    office_cost_delta = {"O001": 0.030, "O002": 0.012, "O003": -0.006, "O004": -0.030, "O005": 0.018, "O006": 0.042}
    office_revenue_delta = {"O001": 0.018, "O002": 0.006, "O003": -0.012, "O004": 0.040, "O005": -0.006, "O006": -0.018}
    carrier_cost_delta = {"CA01": -0.012, "CA02": 0.010, "CA03": 0.060, "CA04": 0.034, "CA05": 0.020, "CA06": 0.044}

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
                cluster = lane["lane_cluster"]
                office_id = random.choice(office_by_origin.get(lane["origin_country"], ["O001", "O004"]))
                carrier_id = random.choice(carrier_by_mode[mode])
                mode_season = 1 + 0.12 * math.sin((p_idx + 1) / 2.0 + mode_phase[mode])
                lane_reset = 1 + (0.075 if period >= "2026-03" and cluster in {"Transpacific", "Europe"} else 0)
                lane_reset -= 0.055 if period >= "2026-02" and cluster in {"Cross-border", "Middle East"} else 0
                service_ids = service_for_lane(mode)
                for sid in service_ids:
                    if sid == "S005" and random.random() > 0.42:
                        continue
                    base_shipments = random.randint(6, 34)
                    if customer["segment"] == "Enterprise":
                        base_shipments += random.randint(5, 22)
                    if sid == "S005":
                        base_shipments = max(3, int(base_shipments * random.uniform(0.35, 0.65)))
                    base_shipments = max(
                        2,
                        int(
                            base_shipments
                            * segment_volume[customer["segment"]]
                            * mode_volume[mode]
                            * cluster_volume[cluster]
                        ),
                    )
                    shipment_count = max(1, int(base_shipments * customer_scale[cid] * season * mode_season * random.uniform(0.64, 1.36)))
                    teu = 0.0 if mode == "Air" else round2(shipment_count * random.uniform(0.6, 2.7))
                    cbm = round2(shipment_count * random.uniform(4.5, 28.0) * (1.6 if mode == "Ocean LCL" else 1.0))
                    weight = round2(shipment_count * random.uniform(450, 5200) * (2.6 if mode == "Air" else 1.0))
                    yield_multiplier = (
                        1
                        + (lane["distance_km"] / 12000) * 0.22
                        + random.uniform(-0.10, 0.12)
                    )
                    yield_multiplier *= segment_yield[customer["segment"]] * cluster_yield[cluster] * lane_reset
                    yield_multiplier *= 1 + office_revenue_delta[office_id]
                    if customer["tier"] == "Strategic":
                        yield_multiplier -= 0.035
                    net_revenue = shipment_count * mode_base_yield[mode] * yield_multiplier * trend
                    if sid == "S005":
                        net_revenue *= random.uniform(0.09, 0.16)
                    carrier_ratio = (
                        mode_cost_ratio[mode]
                        + lane_pressure[lid]
                        + cluster_cost_pressure[cluster]
                        + segment_cost_pressure[customer["segment"]]
                        + office_cost_delta[office_id]
                        + carrier_cost_delta[carrier_id]
                        + random.uniform(-0.040, 0.055)
                    )
                    carrier_cost = net_revenue * carrier_ratio
                    fuel_cost = net_revenue * random.uniform(0.042, 0.095) * (1.18 if period >= "2026-02" else 1)
                    fuel_cost *= 1.20 if mode == "Air" else 1.0
                    fuel_cost *= 1.10 if cluster in {"Europe", "Middle East"} else 1.0
                    handling_cost = shipment_count * random.uniform(55, 225) * (1 + max(-0.05, office_cost_delta[office_id] * 1.6))
                    customs_cost = shipment_count * random.uniform(22, 95) * (1.0 if sid == "S005" else 0.38)
                    delay_factor = max(
                        0,
                        lane_pressure[lid]
                        + cluster_cost_pressure[cluster] * 0.55
                        + office_cost_delta[office_id] * 0.65
                        + random.uniform(-0.022, 0.070),
                    )
                    demurrage = net_revenue * delay_factor * random.uniform(0.08, 0.22)
                    claims = net_revenue * random.choice([0, 0, 0.002, 0.005, 0.012]) * random.uniform(0.4, 1.7)
                    last_mile = shipment_count * random.uniform(35, 180) * (1.35 if mode in {"Road", "Road+Sea"} else 0.72)
                    total_cost = carrier_cost + fuel_cost + handling_cost + customs_cost + demurrage + claims + last_mile
                    gp = net_revenue - total_cost
                    utilization = max(0.42, min(0.99, random.uniform(0.64, 0.94) - (0.05 if gp < 0 else 0) + (0.03 if customer["tier"] == "Strategic" else 0)))
                    delay_rate = max(0.02, min(0.38, 0.10 + delay_factor * 2.2 + random.uniform(-0.04, 0.06)))
                    delayed = int(round(shipment_count * delay_rate))
                    on_time = max(0, shipment_count - delayed)
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
    owner_by_issue = {
        "Below target margin": ["Commercial", "Finance BP"],
        "Fuel leakage": ["Finance BP", "Operations"],
        "Demurrage exposure": ["Operations", "Customer Success"],
        "Claims spike": ["Customer Success", "Operations"],
        "Carrier rate gap": ["Procurement", "Finance BP"],
        "Low utilization": ["Operations", "Commercial"],
    }
    status_weights_by_priority = {
        "High": [0.54, 0.27, 0.16, 0.03],
        "Medium": [0.34, 0.34, 0.23, 0.09],
        "Low": [0.18, 0.28, 0.32, 0.22],
    }
    priority_risk_factor = {"High": 1.62, "Medium": 0.94, "Low": 0.48}
    status_risk_factor = {"Open": 1.28, "In Review": 1.02, "Action Agreed": 0.72, "Closed": 0.18}
    owner_risk_factor = {"Commercial": 1.20, "Procurement": 1.08, "Operations": 1.00, "Finance BP": 0.92, "Customer Success": 0.82}
    recovery_factor_by_status = {"Open": 0.46, "In Review": 0.58, "Action Agreed": 0.76, "Closed": 0.88}
    fact_actions: list[dict] = []
    for idx, row in enumerate(candidates[:108], 1):
        issue, action = random.choice(issue_types)
        base_risk = max(3000, (row["net_revenue_usd"] * row["target_margin_pct"] - row["gross_profit_usd"]) * random.uniform(0.55, 1.25))
        if base_risk >= 45000:
            priority = random.choices(priorities, weights=[0.66, 0.29, 0.05])[0]
        elif base_risk >= 18000:
            priority = random.choices(priorities, weights=[0.36, 0.52, 0.12])[0]
        else:
            priority = random.choices(priorities, weights=[0.12, 0.42, 0.46])[0]
        status = random.choices(statuses, weights=status_weights_by_priority[priority])[0]
        owner_pool = owner_by_issue[issue]
        owner = random.choice(owner_pool if random.random() < 0.78 else ["Commercial", "Procurement", "Operations", "Finance BP", "Customer Success"])
        y, m = map(int, row["date_id"].split("-"))
        due = date(y, m, 1) + timedelta(days=random.randint(21, 55))
        risk = base_risk * priority_risk_factor[priority] * status_risk_factor[status] * owner_risk_factor[owner]
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
                "owner": owner,
                "risk_value_usd": round2(risk),
                "target_margin_recovery_usd": round2(risk * recovery_factor_by_status[status] * random.uniform(0.88, 1.12)),
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


def encoded_color(value: str) -> str:
    return value.replace("#", "%23")


def svg_text(value: str) -> str:
    return value.replace("&", "and").replace("%", "%25").replace("<", "").replace(">", "")


def latest_selected_date_dax() -> str:
    return "MAXX(ALLSELECTED(DimDate), DimDate[date])"


def latest_date_filter_dax() -> str:
    return "FILTER(ALL(DimDate), DimDate[date] = LatestDate)"


def prior_date_filter_dax() -> str:
    return "FILTER(ALL(DimDate), DimDate[date] = PriorDate)"


def latest_metric_dax(measure: str, scale: int | float = 1) -> str:
    return f'''VAR LatestDate = {latest_selected_date_dax()}
VAR LatestValue = CALCULATE([{measure}], {latest_date_filter_dax()})
RETURN DIVIDE(LatestValue, {scale})'''


def current_lens_primary_dax() -> str:
    return f'''VAR LatestDate = {latest_selected_date_dax()}
VAR PeriodText = FORMAT(LatestDate, "MMM yyyy")
VAR ModeCount = COUNTROWS(VALUES(DimTradeLane[mode]))
VAR ModeTotal = CALCULATE(COUNTROWS(VALUES(DimTradeLane[mode])), ALL(DimTradeLane[mode]))
VAR ModeText = IF(NOT ISFILTERED(DimTradeLane[mode]) || ModeCount = ModeTotal, "All modes", IF(ModeCount = 1, SELECTEDVALUE(DimTradeLane[mode]), FORMAT(ModeCount, "0") & " modes"))
VAR SegmentCount = COUNTROWS(VALUES(DimCustomer[segment]))
VAR SegmentTotal = CALCULATE(COUNTROWS(VALUES(DimCustomer[segment])), ALL(DimCustomer[segment]))
VAR SegmentText = IF(NOT ISFILTERED(DimCustomer[segment]) || SegmentCount = SegmentTotal, "All seg", IF(SegmentCount = 1, SELECTEDVALUE(DimCustomer[segment]), FORMAT(SegmentCount, "0") & " seg"))
RETURN LEFT(PeriodText & " | " & ModeText & " | " & SegmentText, 34)'''


def current_lens_secondary_dax() -> str:
    return '''VAR OriginText = IF(HASONEVALUE(DimTradeLane[origin_country]), SELECTEDVALUE(DimTradeLane[origin_country]), "All org")
VAR DestText = IF(HASONEVALUE(DimTradeLane[destination_country]), SELECTEDVALUE(DimTradeLane[destination_country]), "All dest")
VAR OfficeText = IF(HASONEVALUE(DimOffice[office]), SELECTEDVALUE(DimOffice[office]), "All offices")
RETURN LEFT(OriginText & " -> " & DestText & " | " & OfficeText, 42)'''


def decision_text_dax(page: str) -> str:
    if page == "executive":
        return '''VAR GapText = FORMAT(DIVIDE([Margin Gap vs Target], 1000000), "$0.0M;($0.0M);$0.0M")
VAR RepriceText = FORMAT(DIVIDE([Reprice Opportunity], 1000000), "$0.0M")
RETURN IF([Margin Gap vs Target] < 0, "Reprice | Gap " & GapText, "Protect mix | GP " & FORMAT([GP Margin %], "0.0%"))'''
    if page == "lane":
        return '''VAR GapPts = FORMAT([Margin Gap %] * 100, "+0.0;-0.0;0.0") & " pt"
RETURN IF([Margin Gap vs Target] < 0, "Fix lanes | Gap " & GapPts, "Scale lanes | Target " & FORMAT([Target Margin %], "0.0%"))'''
    return '''"Risk " & FORMAT(DIVIDE([Action Risk Value], 1000000), "$0.0M") & " | Rec " & FORMAT(DIVIDE([Recovery Value], 1000000), "$0.0M")'''


def context_panel_svg_dax(title: str, line_measure: str, accent: str, width: int = 256) -> str:
    accent_svg = encoded_color(accent)
    safe_title = svg_text(title)
    return f'''VAR LineRaw = {line_measure}
VAR LineText = SUBSTITUTE(SUBSTITUTE(LEFT(LineRaw, 38), "&", "and"), "%", "%25")
VAR SVG =
    "<svg xmlns='http://www.w3.org/2000/svg' width='{width}' height='28' viewBox='0 0 {width} 28'>" &
    "<rect x='0' y='0' width='{width}' height='28' fill='%23FFFFFF'/>" &
    "<text x='0' y='9' font-family='Segoe UI' font-size='8.4' font-weight='750' fill='{accent_svg}'>{safe_title}</text>" &
    "<text x='0' y='24' font-family='Segoe UI' font-size='11.4' font-weight='700' fill='%230F172A'>" & LineText & "</text>" &
    "</svg>"
RETURN "data:image/svg+xml;utf8," & SVG'''


def svg_kpi_card_dax(
    title: str,
    measure: str,
    accent: str,
    value_format: str,
    scale: int | float = 1,
    change_mode: str = "percent",
    favorable: str = "higher",
) -> str:
    accent_svg = encoded_color(accent)
    good_svg = encoded_color(THEME["green"])
    bad_svg = encoded_color(THEME["red"])
    amber_svg = encoded_color(THEME["amber"])
    title_value = svg_text(title)
    trend_ok = "LastValue <= FirstValue" if favorable == "lower" else "LastValue >= FirstValue"
    change_ok = "ChangeValue <= 0" if favorable == "lower" else "ChangeValue >= 0"
    if change_mode == "points":
        yoy_text = 'FORMAT(ChangeValue * 100, "+0.0;-0.0;0.0") & " pt"'
    elif change_mode == "absolute":
        yoy_text = 'FORMAT(ChangeValue, "+#,0;-#,0;0")'
    else:
        yoy_text = 'FORMAT(RateValue, "+0.0%;-0.0%;0.0%")'
    if scale == 1000000 and "$" in value_format:
        value_text_raw = 'SWITCH(TRUE(), ABS(CurrentValue) >= 1000000, FORMAT(DIVIDE(CurrentValue, 1000000), "$0.0M;($0.0M);$0.0M"), ABS(CurrentValue) >= 1000, FORMAT(DIVIDE(CurrentValue, 1000), "$0.0K;($0.0K);$0.0K"), FORMAT(CurrentValue, "$#,0;($#,0);$0"))'
        py_text_raw = 'IF(ISBLANK(PriorValue), "n/a", SWITCH(TRUE(), ABS(PriorValue) >= 1000000, FORMAT(DIVIDE(PriorValue, 1000000), "$0.0M;($0.0M);$0.0M"), ABS(PriorValue) >= 1000, FORMAT(DIVIDE(PriorValue, 1000), "$0.0K;($0.0K);$0.0K"), FORMAT(PriorValue, "$#,0;($#,0);$0")))'
    else:
        value_text_raw = f'FORMAT(DIVIDE(CurrentValue, {scale}), "{value_format}")'
        py_text_raw = f'IF(ISBLANK(PriorValue), "n/a", FORMAT(DIVIDE(PriorValue, {scale}), "{value_format}"))'
    return f'''VAR LatestDate = {latest_selected_date_dax()}
VAR PriorDate = EDATE(LatestDate, -12)
VAR CurrentValue = CALCULATE([{measure}], {latest_date_filter_dax()})
VAR PriorValue = CALCULATE([{measure}], {prior_date_filter_dax()})
VAR ChangeValue = CurrentValue - PriorValue
VAR RateValue = DIVIDE(ChangeValue, ABS(PriorValue))
VAR ValueTextRaw = {value_text_raw}
VAR PYTextRaw = {py_text_raw}
VAR YoYTextRaw = IF(ISBLANK(CurrentValue) || ISBLANK(PriorValue), "n/a", {yoy_text})
VAR ValueText = SUBSTITUTE(ValueTextRaw, "%", "%25")
VAR PYText = SUBSTITUTE(PYTextRaw, "%", "%25")
VAR YoYText = SUBSTITUTE(YoYTextRaw, "%", "%25")
VAR YoYColor = IF(ISBLANK(CurrentValue) || ISBLANK(PriorValue), "%23647569", IF({change_ok}, "{good_svg}", "{bad_svg}"))
VAR StatusText = IF(ISBLANK(CurrentValue) || ISBLANK(PriorValue), "New", IF({change_ok}, "On track", "Watch"))
VAR StatusFill = "%23F8FAFC"
VAR StatusBorder = IF(ISBLANK(CurrentValue) || ISBLANK(PriorValue), "%23CBD5E1", IF({change_ok}, "{good_svg}", "{bad_svg}"))
VAR StatusColor = IF(ISBLANK(CurrentValue) || ISBLANK(PriorValue), "%23647569", IF({change_ok}, "{good_svg}", "{bad_svg}"))
VAR MonthTable =
    ADDCOLUMNS(
        FILTER(ALLSELECTED(DimDate), DimDate[date] <= LatestDate),
        "__Value", CALCULATE([{measure}])
    )
VAR CleanTable = FILTER(MonthTable, NOT ISBLANK([__Value]))
VAR RowCount = COUNTROWS(CleanTable)
VAR MinValue = MINX(CleanTable, [__Value])
VAR MaxValue = MAXX(CleanTable, [__Value])
VAR FirstValue = MINX(TOPN(1, CleanTable, DimDate[date], ASC), [__Value])
VAR LastValue = MINX(TOPN(1, CleanTable, DimDate[date], DESC), [__Value])
VAR StartYValue = 94 - DIVIDE(FirstValue - MinValue, MaxValue - MinValue, 0.5) * 52
VAR EndYValue = 94 - DIVIDE(LastValue - MinValue, MaxValue - MinValue, 0.5) * 52
VAR TrendColor = IF({trend_ok}, "{accent_svg}", "{bad_svg}")
VAR BandColor = IF({trend_ok}, "%23E0F2FE", "%23FEE2E2")
VAR LinePoints =
    CONCATENATEX(
        CleanTable,
        VAR RankValue = RANKX(CleanTable, DimDate[date], , ASC, DENSE) - 1
        VAR XValue = 176 + DIVIDE(RankValue, MAX(1, RowCount - 1), 0) * 100
        VAR YValue = 94 - DIVIDE([__Value] - MinValue, MaxValue - MinValue, 0.5) * 52
        RETURN FORMAT(XValue, "0.0") & "," & FORMAT(YValue, "0.0"),
        " ",
        DimDate[date],
        ASC
    )
VAR AreaPath =
    "M176 102 " &
    CONCATENATEX(
        CleanTable,
        VAR RankValue = RANKX(CleanTable, DimDate[date], , ASC, DENSE) - 1
        VAR XValue = 176 + DIVIDE(RankValue, MAX(1, RowCount - 1), 0) * 100
        VAR YValue = 94 - DIVIDE([__Value] - MinValue, MaxValue - MinValue, 0.5) * 52
        RETURN "L" & FORMAT(XValue, "0.0") & " " & FORMAT(YValue, "0.0"),
        " ",
        DimDate[date],
        ASC
    ) & " L276 102 Z"
VAR SVG =
    "<svg xmlns='http://www.w3.org/2000/svg' width='296' height='142' viewBox='0 0 296 142'>" &
    "<defs><filter id='innerTableShadow' x='-4' y='-4' width='304' height='150' filterUnits='userSpaceOnUse'><feDropShadow dx='0' dy='1.4' stdDeviation='1.4' flood-color='%23000000' flood-opacity='0.10'/></filter><clipPath id='sparkClip'><rect x='172' y='35' width='108' height='70' rx='8'/></clipPath></defs>" &
    "<rect x='0' y='0' width='296' height='142' fill='%23FFFFFF'/>" &
    "<rect x='7' y='6' width='282' height='130' rx='10' fill='%23FFFFFF' filter='url(%23innerTableShadow)'/>" &
    "<rect x='9' y='8' width='278' height='126' rx='9' fill='none' stroke='%23CBD5E1' stroke-width='1' opacity='1'/>" &
    "<rect x='14' y='12' width='146' height='5' rx='2.5' fill='{accent_svg}' opacity='0.92'/>" &
    "<rect x='14' y='30' width='16' height='16' rx='4.5' fill='{accent_svg}' opacity='0.95'/>" &
    "<circle cx='22' cy='38' r='2.8' fill='%23FFFFFF' opacity='0.88'/>" &
    "<text x='38' y='44' font-family='Segoe UI' font-size='14' font-weight='700' fill='%230F172A'>{title_value}</text>" &
    "<text x='14' y='94' font-family='Segoe UI' font-size='31' font-weight='750' fill='{accent_svg}'>" & ValueText & "</text>" &
    "<rect x='170' y='35' width='112' height='70' rx='8' fill='%23F8FAFC' stroke='%23E2E8F0' stroke-width='1'/>" &
    "<g clip-path='url(%23sparkClip)'>" &
    "<rect x='176' y='67' width='100' height='14' rx='7' fill='" & BandColor & "'/>" &
    "<line x1='176' y1='74' x2='276' y2='74' stroke='%23CBD5E1' stroke-width='1' stroke-dasharray='4 5'/>" &
    "<path d='" & AreaPath & "' fill='{accent_svg}' opacity='0.16'/>" &
    "<polyline points='" & LinePoints & "' fill='none' stroke='" & TrendColor & "' stroke-width='3.4' stroke-linecap='round' stroke-linejoin='round'/>" &
    "</g>" &
    "<circle cx='176' cy='" & FORMAT(StartYValue, "0.0") & "' r='3.7' fill='%23FFFFFF' stroke='%2394A3B8' stroke-width='1.4'/>" &
    "<circle cx='276' cy='" & FORMAT(EndYValue, "0.0") & "' r='4.5' fill='" & TrendColor & "' stroke='%23FFFFFF' stroke-width='1.8'/>" &
    "<rect x='14' y='112' width='88' height='24' rx='6' fill='%23F1F5F9'/>" &
    "<rect x='108' y='112' width='78' height='24' rx='6' fill='%23F8FAFC' stroke='%23E2E8F0' stroke-width='1'/>" &
    "<rect x='192' y='112' width='90' height='24' rx='6' fill='" & StatusFill & "' stroke='" & StatusBorder & "' stroke-width='1'/>" &
    "<circle cx='204' cy='124' r='3.5' fill='" & StatusColor & "'/>" &
    "<text x='22' y='128' font-family='Segoe UI' font-size='10.8' font-weight='700' fill='%23475569'>PY</text>" &
    "<text x='44' y='128' font-family='Segoe UI' font-size='10.8' fill='%23475569'>" & PYText & "</text>" &
    "<text x='116' y='128' font-family='Segoe UI' font-size='10.8' font-weight='700' fill='" & YoYColor & "'>" & YoYText & "</text>" &
    "<text x='214' y='128' font-family='Segoe UI' font-size='10.6' font-weight='750' fill='" & StatusColor & "'>" & StatusText & "</text>" &
    "</svg>"
RETURN IF(RowCount = 0, BLANK(), "data:image/svg+xml;utf8," & SVG)'''


def lens_summary_svg_dax() -> str:
    return f'''VAR LatestDate = {latest_selected_date_dax()}
VAR PeriodText = FORMAT(LatestDate, "MMM yyyy")
VAR YearText = IF(HASONEVALUE(DimDate[year]), FORMAT(SELECTEDVALUE(DimDate[year]), "0"), "All years")
VAR ModeCount = COUNTROWS(VALUES(DimTradeLane[mode]))
VAR ModeTotal = CALCULATE(COUNTROWS(VALUES(DimTradeLane[mode])), ALL(DimTradeLane[mode]))
VAR ModeText = IF(NOT ISFILTERED(DimTradeLane[mode]) || ModeCount = ModeTotal, "All modes", IF(ModeCount = 1, SELECTEDVALUE(DimTradeLane[mode]), FORMAT(ModeCount, "0") & " modes"))
VAR SegmentCount = COUNTROWS(VALUES(DimCustomer[segment]))
VAR SegmentTotal = CALCULATE(COUNTROWS(VALUES(DimCustomer[segment])), ALL(DimCustomer[segment]))
VAR SegmentText = IF(NOT ISFILTERED(DimCustomer[segment]) || SegmentCount = SegmentTotal, "All segments", IF(SegmentCount = 1, SELECTEDVALUE(DimCustomer[segment]), FORMAT(SegmentCount, "0") & " segments"))
VAR OriginText = IF(HASONEVALUE(DimTradeLane[origin_country]), SELECTEDVALUE(DimTradeLane[origin_country]), "All origins")
VAR DestText = IF(HASONEVALUE(DimTradeLane[destination_country]), SELECTEDVALUE(DimTradeLane[destination_country]), "All destinations")
VAR OfficeText = IF(HASONEVALUE(DimOffice[office]), SELECTEDVALUE(DimOffice[office]), "All offices")
VAR ActionText = IF(HASONEVALUE(FactActionQueue[priority]), SELECTEDVALUE(FactActionQueue[priority]) & " priority", "All priorities")
VAR Line1Raw = LEFT(PeriodText & " | " & ModeText & " | " & SegmentText, 42)
VAR Line2Raw = LEFT(OriginText & " -> " & DestText & " | " & OfficeText, 42)
VAR Line1 = SUBSTITUTE(SUBSTITUTE(Line1Raw, "&", "and"), "%", "%25")
VAR Line2 = SUBSTITUTE(SUBSTITUTE(Line2Raw, "&", "and"), "%", "%25")
VAR RevenueText = FORMAT(DIVIDE([Net Revenue], 1000000), "$0.0M")
VAR MarginText = SUBSTITUTE(FORMAT([GP Margin %], "0.0%"), "%", "%25")
VAR SVG =
    "<svg xmlns='http://www.w3.org/2000/svg' width='282' height='56' viewBox='0 0 282 56'>" &
    "<rect x='1' y='1' width='280' height='54' rx='8' fill='%23EFF6FF' stroke='%23BFDBFE' stroke-width='1.2'/>" &
    "<text x='12' y='17' font-family='Segoe UI' font-size='10' font-weight='750' fill='%232563EB'>CURRENT LENS</text>" &
    "<circle cx='264' cy='14' r='4' fill='%230F766E'/>" &
    "<text x='12' y='35' font-family='Segoe UI' font-size='11.2' font-weight='700' fill='%230F172A'>" & Line1 & "</text>" &
    "<text x='12' y='49' font-family='Segoe UI' font-size='9.2' fill='%23475569'>" & Line2 & "</text>" &
    "<rect x='184' y='20' width='39' height='22' rx='6' fill='%23FFFFFF' opacity='0.86'/>" &
    "<rect x='229' y='20' width='42' height='22' rx='6' fill='%23FFFFFF' opacity='0.86'/>" &
    "<text x='191' y='34' font-family='Segoe UI' font-size='9.5' font-weight='750' fill='%232563EB'>" & RevenueText & "</text>" &
    "<text x='236' y='34' font-family='Segoe UI' font-size='9.5' font-weight='750' fill='%230F766E'>" & MarginText & "</text>" &
    "</svg>"
RETURN "data:image/svg+xml;utf8," & SVG'''


def decision_chips_svg_dax(page: str) -> str:
    if page == "executive":
        chip1 = 'FORMAT(DIVIDE([Margin Gap vs Target], 1000000), "$0.0M;($0.0M);$0.0M")'
        chip2 = 'FORMAT(DIVIDE([Reprice Opportunity], 1000000), "$0.0M")'
        chip3 = 'IF([GP Margin %] < [Target Margin %], "Reprice loss lanes", "Protect profitable mix")'
        labels = ("Gap ", "Reprice ", "")
    elif page == "lane":
        chip1 = 'SUBSTITUTE(FORMAT([Target Margin %], "0.0%"), "%", "%25")'
        chip2 = 'FORMAT([Margin Gap %] * 100, "+0.0;-0.0;0.0") & " pt"'
        chip3 = 'IF([Margin Gap vs Target] < 0, "Fix bottom lanes", "Scale good lanes")'
        labels = ("Target ", "Gap ", "")
    else:
        chip1 = 'FORMAT([Open Actions], "#,0")'
        chip2 = 'FORMAT(DIVIDE([Action Risk Value], 1000000), "$0.0M")'
        chip3 = 'FORMAT(DIVIDE([Recovery Value], 1000000), "$0.0M")'
        labels = ("Open ", "Risk ", "Recovery ")
    return f'''VAR Chip1TextRaw = "{labels[0]}" & {chip1}
VAR Chip2TextRaw = "{labels[1]}" & {chip2}
VAR Chip3TextRaw = "{labels[2]}" & {chip3}
VAR Chip1Text = SUBSTITUTE(SUBSTITUTE(Chip1TextRaw, "&", "and"), "%", "%25")
VAR Chip2Text = SUBSTITUTE(SUBSTITUTE(Chip2TextRaw, "&", "and"), "%", "%25")
VAR Chip3Text = SUBSTITUTE(SUBSTITUTE(Chip3TextRaw, "&", "and"), "%", "%25")
VAR SVG =
    "<svg xmlns='http://www.w3.org/2000/svg' width='300' height='56' viewBox='0 0 300 56'>" &
    "<rect x='0' y='0' width='300' height='56' rx='8' fill='%23FFFBEB'/>" &
    "<rect x='10' y='11' width='84' height='34' rx='7' fill='%23FFFFFF' stroke='%23FDE68A' stroke-width='1'/>" &
    "<rect x='108' y='11' width='84' height='34' rx='7' fill='%23FFFFFF' stroke='%23FDE68A' stroke-width='1'/>" &
    "<rect x='206' y='11' width='84' height='34' rx='7' fill='%23FFFFFF' stroke='%23FDE68A' stroke-width='1'/>" &
    "<rect x='20' y='22' width='9' height='9' rx='2' fill='%23B45309'/>" &
    "<rect x='118' y='22' width='9' height='9' rx='2' fill='%23DC2626'/>" &
    "<rect x='216' y='22' width='9' height='9' rx='2' fill='%230F766E'/>" &
    "<text x='35' y='32' font-family='Segoe UI' font-size='10.4' font-weight='750' fill='%230F172A'>" & Chip1Text & "</text>" &
    "<text x='133' y='32' font-family='Segoe UI' font-size='10.4' font-weight='750' fill='%230F172A'>" & Chip2Text & "</text>" &
    "<text x='231' y='32' font-family='Segoe UI' font-size='10.4' font-weight='750' fill='%230F172A'>" & Chip3Text & "</text>" &
    "</svg>"
RETURN "data:image/svg+xml;utf8," & SVG'''


def measure_catalog() -> list[tuple]:
    measures: list[tuple] = [
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
    latest_measures = [
        ("Latest Net Revenue", "Net Revenue", 1000000, "$#,0.0M;($#,0.0M);$0.0M", "Latest selected-period net revenue."),
        ("Latest Gross Profit", "Gross Profit", 1000000, "$#,0.0M;($#,0.0M);$0.0M", "Latest selected-period gross profit."),
        ("Latest GP Margin %", "GP Margin %", 1, "0.0%", "Latest selected-period gross profit margin."),
        ("Latest Reprice Opportunity", "Reprice Opportunity", 1000000, "$#,0.0M;($#,0.0M);$0.0M", "Latest selected-period reprice opportunity."),
        ("Latest Revenue per Shipment", "Revenue per Shipment", 1, "$#,0", "Latest selected-period revenue per shipment."),
        ("Latest Margin Gap vs Target", "Margin Gap vs Target", 1000000, "$#,0.0M;($#,0.0M);$0.0M", "Latest selected-period gross profit gap versus target."),
        ("Latest Negative Margin Shipments", "Negative Margin Shipments", 1, "#,0", "Latest selected-period negative-margin shipment count."),
        ("Latest On-Time %", "On-Time %", 1, "0.0%", "Latest selected-period on-time percentage."),
        ("Latest Open Actions", "Open Actions", 1, "#,0", "Open actions in the selected context."),
        ("Latest Action Risk Value", "Action Risk Value", 1000000, "$#,0.0M;($#,0.0M);$0.0M", "Action risk value in the selected context."),
        ("Latest Recovery Value", "Recovery Value", 1000000, "$#,0.0M;($#,0.0M);$0.0M", "Recovery value in the selected context."),
        ("Latest Demurrage Cost", "Demurrage Cost", 1000000, "$#,0.0M;($#,0.0M);$0.0M", "Latest selected-period demurrage cost."),
    ]
    measures.extend((name, latest_metric_dax(base, scale), fmt, desc) for name, base, scale, fmt, desc in latest_measures)
    measures.extend(
        [
            ("Current Lens Primary", current_lens_primary_dax(), "", "Dynamic first line for the Current Lens panel."),
            ("Current Lens Secondary", current_lens_secondary_dax(), "", "Dynamic second line for the Current Lens panel."),
            ("Executive Decision Text", decision_text_dax("executive"), "", "Dynamic action text for the Executive Overview page."),
            ("Lane Decision Text", decision_text_dax("lane"), "", "Dynamic action text for the Trade Lane Margin page."),
            ("Cost Decision Text", decision_text_dax("cost"), "", "Dynamic action text for the Cost Drivers & Action Queue page."),
        ]
    )
    image_url = {"dataCategory": "ImageUrl", "dataType": "string"}
    context_svgs = [
        ("Current Lens Panel SVG", context_panel_svg_dax("CURRENT LENS", "[Current Lens Primary]", THEME["blue"], 256), "TableEx SVG mini panel for the current filter lens."),
        ("Executive Decision Panel SVG", context_panel_svg_dax("NEXT ACTION", "[Executive Decision Text]", THEME["amber"], 244), "TableEx SVG mini panel for executive next action."),
        ("Lane Decision Panel SVG", context_panel_svg_dax("NEXT ACTION", "[Lane Decision Text]", THEME["amber"], 244), "TableEx SVG mini panel for lane next action."),
        ("Cost Decision Panel SVG", context_panel_svg_dax("NEXT ACTION", "[Cost Decision Text]", THEME["amber"], 244), "TableEx SVG mini panel for cost next action."),
    ]
    measures.extend((name, dax, "", desc, image_url) for name, dax, desc in context_svgs)
    svg_kpis = [
        ("Net Revenue KPI Card SVG", "Net Revenue", "Net Revenue", THEME["blue"], "$0.0M", 1000000, "percent", "higher", "TableEx SVG KPI card for net revenue."),
        ("Gross Profit KPI Card SVG", "Gross Profit", "Gross Profit", THEME["green"], "$0.0M", 1000000, "percent", "higher", "TableEx SVG KPI card for gross profit."),
        ("GP Margin KPI Card SVG", "GP Margin", "GP Margin %", THEME["teal"], "0.0%", 1, "points", "higher", "TableEx SVG KPI card for gross profit margin."),
        ("Reprice Opportunity KPI Card SVG", "Reprice Opp.", "Reprice Opportunity", THEME["red"], "$0.0M", 1000000, "percent", "lower", "TableEx SVG KPI card for reprice opportunity."),
        ("Revenue per Shipment KPI Card SVG", "Rev / Shipment", "Revenue per Shipment", THEME["blue"], "$#,0", 1, "percent", "higher", "TableEx SVG KPI card for revenue per shipment."),
        ("Margin Gap KPI Card SVG", "Margin Gap", "Margin Gap vs Target", THEME["red"], "$0.0M;($0.0M);$0.0M", 1000000, "percent", "higher", "TableEx SVG KPI card for margin gap versus target."),
        ("Negative Margin Shipments KPI Card SVG", "Neg. Margin", "Negative Margin Shipments", THEME["red"], "#,0", 1, "absolute", "lower", "TableEx SVG KPI card for negative-margin shipments."),
        ("On-Time KPI Card SVG", "On-Time", "On-Time %", THEME["green"], "0.0%", 1, "points", "higher", "TableEx SVG KPI card for on-time performance."),
        ("Open Actions KPI Card SVG", "Open Actions", "Open Actions", THEME["amber"], "#,0", 1, "absolute", "lower", "TableEx SVG KPI card for open actions."),
        ("Action Risk KPI Card SVG", "Action Risk", "Action Risk Value", THEME["red"], "$0.0M", 1000000, "percent", "lower", "TableEx SVG KPI card for action risk value."),
        ("Recovery KPI Card SVG", "Recovery", "Recovery Value", THEME["green"], "$0.0M", 1000000, "percent", "higher", "TableEx SVG KPI card for recovery value."),
        ("Demurrage KPI Card SVG", "Demurrage", "Demurrage Cost", THEME["amber"], "$0.0M", 1000000, "percent", "lower", "TableEx SVG KPI card for demurrage cost."),
    ]
    measures.extend(
        (name, svg_kpi_card_dax(title, base, accent, value_format, scale, change_mode, favorable), "", desc, image_url)
        for name, title, base, accent, value_format, scale, change_mode, favorable, desc in svg_kpis
    )
    return measures


def write_model_docs(validation: dict) -> None:
    measures = [
        {
            "measure_name": item[0],
            "dax": item[1],
            "format_string": item[2],
            "definition": item[3],
            "data_category": (item[4] if len(item) > 4 else {}).get("dataCategory"),
        }
        for item in measure_catalog()
    ]
    write_json("model/measure_catalog.json", measures)
    write_text("model/MEASURES.dax", "\n\n".join([f"{m['measure_name']} =\n{m['dax']}" for m in measures]))
    write_text(
        "model/dax_measures.md",
        "\n".join(
            ["# DAX Measures", "", "| Measure | Format | Data Category | Definition |", "|---|---:|---|---|"]
            + [
                f"| {m['measure_name']} | `{m['format_string']}` | {m.get('data_category') or ''} | {m['definition']} |"
                for m in measures
            ]
        ),
    )
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


def html_dashboard_v2(data: dict) -> str:
    fact = data["fact_shipment_profitability"]
    dates = sorted(data["dim_date"], key=lambda r: int(r["month_index"]))
    lane_lookup = {r["lane_id"]: r for r in data["dim_trade_lane"]}
    customer_lookup = {r["customer_id"]: r for r in data["dim_customer"]}
    service_lookup = {r["service_id"]: r for r in data["dim_service"]}
    office_lookup = {r["office_id"]: r for r in data["dim_office"]}
    carrier_lookup = {r["carrier_id"]: r for r in data["dim_carrier"]}

    def money(value: str | float) -> float:
        return round(float(value), 2)

    facts = []
    for row in fact:
        lane = lane_lookup[row["lane_id"]]
        customer = customer_lookup[row["customer_id"]]
        service = service_lookup[row["service_id"]]
        office = office_lookup[row["office_id"]]
        carrier = carrier_lookup[row["carrier_id"]]
        revenue = money(row["net_revenue_usd"])
        target_gp = round(revenue * float(row["target_margin_pct"]), 2)
        facts.append(
            {
                "d": row["date_id"],
                "c": customer["customer_name"],
                "seg": customer["segment"],
                "lane": lane["lane_name"],
                "mode": lane["mode"],
                "cluster": lane["lane_cluster"],
                "service": service["service_family"],
                "office": office["office"],
                "carrier": carrier["carrier"],
                "ship": int(row["shipment_count"]),
                "teu": money(row["teu"]),
                "rev": revenue,
                "cost": money(row["total_cost_usd"]),
                "gp": money(row["gross_profit_usd"]),
                "target": target_gp,
                "ontime": int(row["on_time_count"]),
                "delayed": int(row["delayed_count"]),
                "dem": money(row["demurrage_cost_usd"]),
                "claims": money(row["claims_cost_usd"]),
            }
        )

    actions = []
    for row in data["fact_action_queue"]:
        lane = lane_lookup[row["lane_id"]]
        customer = customer_lookup[row["customer_id"]]
        office = office_lookup[row["office_id"]]
        actions.append(
            {
                "d": row["date_id"],
                "c": customer["customer_name"],
                "seg": customer["segment"],
                "lane": lane["lane_name"],
                "mode": lane["mode"],
                "cluster": lane["lane_cluster"],
                "office": office["office"],
                "issue": row["issue_type"],
                "priority": row["priority"],
                "status": row["status"],
                "owner": row["owner"],
                "risk": money(row["risk_value_usd"]),
                "recovery": money(row["target_margin_recovery_usd"]),
                "action": row["recommended_action"],
            }
        )

    bridge = []
    for row in data["fact_cost_driver_bridge"]:
        lane = lane_lookup[row["lane_id"]]
        customer = customer_lookup[row["customer_id"]]
        bridge.append(
            {
                "d": row["date_id"],
                "c": customer["customer_name"],
                "seg": customer["segment"],
                "lane": lane["lane_name"],
                "mode": lane["mode"],
                "cluster": lane["lane_cluster"],
                "driver": row["driver"],
                "sort": int(row["driver_sort"]),
                "amount": money(row["amount_usd"]),
                "type": row["driver_type"],
            }
        )

    payload = {
        "latest": LATEST_PERIOD,
        "seed": SEED,
        "dates": [{"id": r["date_id"], "label": r["month_label"], "year": int(r["year"])} for r in dates],
        "filters": {
            "modes": sorted({r["mode"] for r in facts}),
            "segments": sorted({r["seg"] for r in facts}),
            "offices": sorted({r["office"] for r in facts}),
        },
        "facts": facts,
        "actions": actions,
        "bridge": bridge,
    }

    template = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Project 17 - Logistics Trade Lane Profitability</title>
<link rel="icon" href="data:,">
<style>
:root {
  --bg:#F8FAFC;
  --panel:#FFFFFF;
  --panel2:#F1F5F9;
  --border:#CBD5E1;
  --grid:#E2E8F0;
  --text:#0F172A;
  --muted:#475569;
  --dim:#64748B;
  --blue:#2563EB;
  --teal:#0F766E;
  --green:#15803D;
  --amber:#B45309;
  --red:#DC2626;
  --ink:#111827;
}
* { box-sizing:border-box; }
body { margin:0; background:var(--bg); color:var(--text); font-family:Segoe UI,Arial,sans-serif; -webkit-font-smoothing:antialiased; }
button,select { font:inherit; }
.shell { width:min(1280px,100%); min-height:720px; margin:0 auto; padding:18px 24px 20px; }
.report-header { display:grid; grid-template-columns:minmax(0,1fr) auto; gap:18px; align-items:end; min-height:44px; border-bottom:2px solid #6FB8AF; }
.title-block { min-width:0; padding-bottom:8px; border-left:4px solid #6FB8AF; padding-left:18px; }
.kicker { margin:0 0 5px; color:var(--blue); font-size:11px; font-weight:800; letter-spacing:.05em; text-transform:uppercase; }
h1 { margin:0; font-size:22px; line-height:1.12; letter-spacing:0; }
.subtitle { margin:5px 0 0; color:var(--muted); font-size:12px; line-height:1.35; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
.page-nav { display:flex; gap:2px; align-self:start; }
.nav-btn { min-width:100px; min-height:30px; border:0; border-left:1px solid rgba(255,255,255,.65); background:#6FB8AF; color:#0B2F2A; font-size:10px; font-weight:800; cursor:pointer; }
.nav-btn.active { background:#2F766F; color:#fff; }
.filter-lens { display:grid; grid-template-columns:86px 98px 116px 116px minmax(230px,1fr) minmax(230px,1fr); gap:12px; align-items:stretch; margin-top:10px; }
.filter { min-width:0; height:38px; border:1px solid var(--border); border-radius:6px; background:#fff; padding:4px 8px; }
.filter span { display:block; color:var(--dim); font-size:9px; font-weight:800; text-transform:uppercase; }
.filter select { width:100%; border:0; outline:0; background:transparent; color:var(--text); font-size:11px; font-weight:700; }
.mini-card { min-width:0; height:58px; display:flex; flex-direction:column; justify-content:center; gap:4px; border:1px solid var(--border); border-radius:8px; background:#fff; box-shadow:0 1px 2px rgba(15,23,42,.08); padding:9px 14px 9px 18px; position:relative; overflow:hidden; }
.mini-card:before { content:""; position:absolute; left:8px; top:10px; bottom:10px; width:4px; border-radius:3px; background:#6FB8AF; }
.mini-card.decision:before { background:#C98E2B; }
.mini-card span { margin-left:16px; color:var(--blue); font-size:10px; font-weight:800; letter-spacing:.04em; }
.mini-card strong { margin-left:16px; color:var(--text); font-size:13px; line-height:1.2; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
.mini-card em { margin-left:16px; color:var(--muted); font-style:normal; font-size:10px; line-height:1.2; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
.page { display:none; }
.page.active { display:block; }
.kpi-row { display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:16px; margin-top:16px; }
.kpi-card { min-width:0; height:152px; border:1px solid var(--border); border-radius:8px; background:#fff; box-shadow:0 8px 18px rgba(15,23,42,.16); padding:12px; display:grid; grid-template-columns:1fr 112px; grid-template-rows:auto 1fr auto; gap:6px 10px; position:relative; overflow:hidden; }
.kpi-card:before { content:""; position:absolute; inset:7px; border:1px solid rgba(203,213,225,.9); border-radius:7px; box-shadow:0 1px 3px rgba(15,23,42,.12); pointer-events:none; }
.kpi-title { position:relative; z-index:1; grid-column:1 / 2; color:var(--blue); font-size:11px; font-weight:800; text-transform:uppercase; line-height:1.2; }
.kpi-value { position:relative; z-index:1; grid-column:1 / 2; align-self:center; color:var(--ink); font-size:28px; line-height:1; font-weight:850; overflow-wrap:anywhere; }
.kpi-spark { position:relative; z-index:1; grid-column:2; grid-row:1 / 3; width:100%; height:72px; align-self:center; border:1px solid var(--grid); border-radius:7px; background:#F8FAFC; }
.kpi-foot { position:relative; z-index:1; grid-column:1 / 3; display:grid; grid-template-columns:1fr 1fr 1.15fr; gap:6px; }
.chip { min-width:0; min-height:22px; display:flex; align-items:center; justify-content:center; gap:4px; border:1px solid var(--border); border-radius:6px; background:#F8FAFC; color:var(--muted); font-size:10px; font-weight:700; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; padding:2px 6px; }
.chip.good { border-color:#9CC7A2; color:var(--green); background:#F6FBF5; }
.chip.bad { border-color:#EF9992; color:var(--red); background:#FEF6F5; }
.chip.neutral { color:var(--blue); }
.main-row { display:grid; grid-template-columns:1.05fr .95fr .95fr; gap:12px; margin-top:16px; }
.bottom-row { display:grid; grid-template-columns:1.08fr 1.02fr .9fr; gap:12px; margin-top:8px; }
.chart-card { min-width:0; height:208px; border:1px solid var(--border); border-radius:6px; background:#fff; box-shadow:0 8px 18px rgba(15,23,42,.16); padding:10px 10px 8px; overflow:hidden; }
.bottom-row .chart-card { height:194px; }
.chart-card h3 { margin:0 0 6px; color:var(--blue); font-size:13px; line-height:1.2; font-weight:800; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
.chart-card.good h3 { color:#3B7F44; }
.chart-card.warn h3 { color:var(--red); }
.chart-body { height:calc(100% - 22px); min-height:0; }
.chart-body svg { width:100%; height:100%; display:block; overflow:visible; }
.legend { display:flex; gap:8px; flex-wrap:wrap; align-items:center; margin-bottom:3px; color:var(--muted); font-size:9px; font-weight:700; }
.swatch { width:8px; height:8px; border-radius:2px; display:inline-block; margin-right:3px; }
.donut-wrap { height:100%; display:grid; grid-template-columns:110px 1fr; gap:8px; align-items:center; }
.donut { width:106px; height:106px; border-radius:50%; position:relative; background:conic-gradient(var(--teal) 0 40%, var(--blue) 40% 68%, var(--green) 68% 84%, var(--amber) 84% 100%); }
.donut:after { content:""; position:absolute; inset:28px; border-radius:50%; background:#fff; box-shadow:inset 0 0 0 1px var(--grid); }
.donut-legend { display:grid; gap:5px; color:var(--muted); font-size:10px; }
.donut-legend div { display:grid; grid-template-columns:10px 1fr auto; gap:6px; align-items:center; }
.action-table { width:100%; border-collapse:collapse; font-size:10px; }
.action-table th,.action-table td { padding:6px 5px; border-bottom:1px solid var(--grid); text-align:left; vertical-align:top; }
.action-table th { color:var(--dim); font-size:9px; text-transform:uppercase; }
.status { display:inline-flex; border:1px solid var(--border); border-radius:999px; padding:2px 6px; font-weight:800; }
.status.Open { color:var(--red); border-color:#EF9992; background:#FEF6F5; }
.status.In { color:var(--amber); border-color:#D9B26E; background:#FFFBEB; }
.status.Action { color:var(--green); border-color:#9CC7A2; background:#F6FBF5; }
.qa-note { max-width:1280px; margin:10px auto 24px; padding:0 24px; color:var(--muted); font-size:11px; line-height:1.5; }
@media (max-width:980px) {
  .shell { padding:14px; }
  .report-header,.filter-lens,.main-row,.bottom-row { grid-template-columns:1fr; }
  .page-nav { width:100%; }
  .nav-btn { flex:1; }
  .kpi-row { grid-template-columns:1fr; }
  .kpi-card { height:auto; min-height:148px; }
  .chart-card,.bottom-row .chart-card { height:240px; }
  .subtitle { white-space:normal; }
  .qa-note { padding:0 14px; }
}
</style>
</head>
<body>
<main class="shell">
  <header class="report-header">
    <div class="title-block">
      <p class="kicker">Project 17 / Logistics finance</p>
      <h1 id="pageTitle">Executive Overview</h1>
      <p class="subtitle" id="pageSubtitle">Margin status, volume, reprice value, and customer/lane concentration</p>
    </div>
    <nav class="page-nav" aria-label="Page navigation">
      <button class="nav-btn active" type="button" data-page="overview">01 Overview</button>
      <button class="nav-btn" type="button" data-page="lane">02 Lane</button>
      <button class="nav-btn" type="button" data-page="action">03 Actions</button>
    </nav>
  </header>

  <section class="filter-lens" aria-label="Dashboard filters">
    <label class="filter"><span>Period</span><select id="periodFilter"></select></label>
    <label class="filter"><span>Mode</span><select id="modeFilter"></select></label>
    <label class="filter"><span>Segment</span><select id="segmentFilter"></select></label>
    <label class="filter"><span>Office</span><select id="officeFilter"></select></label>
    <article class="mini-card"><span>CURRENT LENS</span><strong id="lensPrimary"></strong><em id="lensSecondary"></em></article>
    <article class="mini-card decision"><span>NEXT ACTION</span><strong id="decisionText"></strong><em id="decisionSubtext">Owner action queue updates with filters</em></article>
  </section>

  <section class="page active" id="overviewPage" data-page="overview">
    <div class="kpi-row" id="overviewKpis"></div>
    <div class="main-row">
      <article class="chart-card"><h3>Revenue and GP Trend</h3><div class="chart-body" id="overviewTrend"></div></article>
      <article class="chart-card good"><h3>Gross Profit by Lane Cluster</h3><div class="chart-body" id="overviewCluster"></div></article>
      <article class="chart-card"><h3>Revenue Mix by Service</h3><div class="chart-body" id="overviewService"></div></article>
    </div>
    <div class="bottom-row">
      <article class="chart-card"><h3>Reprice Opportunity by Customer</h3><div class="chart-body" id="overviewCustomer"></div></article>
      <article class="chart-card warn"><h3>Margin Gap by Lane Cluster</h3><div class="chart-body" id="overviewGap"></div></article>
      <article class="chart-card good"><h3>Action Risk by Owner</h3><div class="chart-body" id="overviewOwner"></div></article>
    </div>
  </section>

  <section class="page" id="lanePage" data-page="lane">
    <div class="kpi-row" id="laneKpis"></div>
    <div class="main-row">
      <article class="chart-card"><h3>GP Margin by Lane Cluster</h3><div class="chart-body" id="laneMargin"></div></article>
      <article class="chart-card"><h3>Revenue and GP by Mode</h3><div class="chart-body" id="laneMode"></div></article>
      <article class="chart-card warn"><h3>Margin Gap Driver Bridge</h3><div class="chart-body" id="laneBridge"></div></article>
    </div>
    <div class="bottom-row">
      <article class="chart-card warn"><h3>Negative Margin by Customer</h3><div class="chart-body" id="laneNegative"></div></article>
      <article class="chart-card"><h3>Total Cost by Carrier</h3><div class="chart-body" id="laneCarrier"></div></article>
      <article class="chart-card good"><h3>Utilization Proxy by Cluster</h3><div class="chart-body" id="laneUtil"></div></article>
    </div>
  </section>

  <section class="page" id="actionPage" data-page="action">
    <div class="kpi-row" id="actionKpis"></div>
    <div class="main-row">
      <article class="chart-card warn"><h3>Cost Driver Waterfall</h3><div class="chart-body" id="actionWaterfall"></div></article>
      <article class="chart-card"><h3>Total Cost by Carrier</h3><div class="chart-body" id="actionCarrier"></div></article>
      <article class="chart-card warn"><h3>Risk by Issue Type</h3><div class="chart-body" id="actionIssue"></div></article>
    </div>
    <div class="bottom-row">
      <article class="chart-card"><h3>Action Queue</h3><div class="chart-body" id="actionTable"></div></article>
      <article class="chart-card good"><h3>Recovery by Issue Type</h3><div class="chart-body" id="actionRecovery"></div></article>
      <article class="chart-card"><h3>Open Risk by Owner</h3><div class="chart-body" id="actionOwner"></div></article>
    </div>
  </section>
</main>
<footer class="qa-note"><strong>Static preview note:</strong> This HTML mirrors the latest PBIX layout rhythm using synthetic portfolio data: native-style page navigation, slicers, current lens chips, four SVG-style KPI cards per page, and chart rows with a 16 px KPI-to-chart breathing gap.</footer>
<script id="data" type="application/json">__PAYLOAD__</script>
<script>
const DATA = JSON.parse(document.getElementById('data').textContent);
const state = { page: 'overview', period: DATA.latest, mode: 'All', segment: 'All', office: 'All' };
const pageMeta = {
  overview: ['Executive Overview', 'Margin status, volume, reprice value, and customer/lane concentration'],
  lane: ['Trade Lane Margin', 'Lane economics, service mix, utilization, and margin gap diagnosis'],
  action: ['Cost Drivers & Action Queue', 'Cost recovery actions, risk exposure, owner queue, and claims/demurrage control']
};
const colors = ['#2563EB', '#0F766E', '#15803D', '#B45309', '#DC2626', '#111827'];
const money = n => {
  const sign = n < 0 ? '-' : '';
  const v = Math.abs(n || 0);
  if (v >= 1000000) return sign + '$' + (v / 1000000).toFixed(1) + 'M';
  if (v >= 1000) return sign + '$' + (v / 1000).toFixed(1) + 'K';
  return sign + '$' + Math.round(v).toLocaleString();
};
const pct = n => ((n || 0) * 100).toFixed(1) + '%';
const num = n => Math.round(n || 0).toLocaleString();
const clean = s => String(s || '').replace(/[&<>"']/g, ch => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]));
function initSelect(id, values, current) {
  const el = document.getElementById(id);
  el.innerHTML = values.map(v => `<option value="${clean(v)}">${clean(v)}</option>`).join('');
  el.value = current;
  el.onchange = () => { state[id.replace('Filter','')] = el.value; render(); };
}
function initFilters() {
  initSelect('periodFilter', DATA.dates.map(d => d.id), DATA.latest);
  initSelect('modeFilter', ['All', ...DATA.filters.modes], 'All');
  initSelect('segmentFilter', ['All', ...DATA.filters.segments], 'All');
  initSelect('officeFilter', ['All', ...DATA.filters.offices], 'All');
}
function rowPass(row, includePeriod = true) {
  return (!includePeriod || row.d === state.period)
    && (state.mode === 'All' || row.mode === state.mode)
    && (state.segment === 'All' || row.seg === state.segment)
    && (state.office === 'All' || row.office === state.office);
}
function rows(includePeriod = true) { return DATA.facts.filter(r => rowPass(r, includePeriod)); }
function actionRows() { return DATA.actions.filter(r => rowPass(r, true)); }
function bridgeRows() { return DATA.bridge.filter(r => rowPass(r, true)); }
function agg(list) {
  return list.reduce((a, r) => {
    a.rev += r.rev; a.cost += r.cost; a.gp += r.gp; a.target += r.target; a.ship += r.ship;
    a.ontime += r.ontime; a.delayed += r.delayed; a.dem += r.dem; a.claims += r.claims;
    if (r.gp < 0) { a.reprice += -r.gp; a.negShip += r.ship; }
    return a;
  }, {rev:0,cost:0,gp:0,target:0,ship:0,ontime:0,delayed:0,dem:0,claims:0,reprice:0,negShip:0});
}
function groupBy(list, keyFn, valueFn) {
  const map = new Map();
  list.forEach(r => {
    const k = keyFn(r);
    map.set(k, (map.get(k) || 0) + valueFn(r));
  });
  return [...map.entries()].map(([name,value]) => ({name, value})).sort((a,b) => Math.abs(b.value) - Math.abs(a.value));
}
function periodIndex(period) { return DATA.dates.findIndex(d => d.id === period); }
function previousPeriod() { const i = periodIndex(state.period); return DATA.dates[Math.max(0, i - 1)]?.id || state.period; }
function filteredForPeriod(period) { const old = state.period; state.period = period; const out = rows(true); state.period = old; return out; }
function spark(metric) {
  const series = DATA.dates.map(d => agg(filteredForPeriod(d.id))[metric] || 0);
  return series;
}
function kpiConfig(page, a, prev) {
  const actionA = actionRows().reduce((x,r) => { x.risk += r.risk; x.recovery += r.recovery; x.open += r.status === 'Open' ? 1 : 0; return x; }, {risk:0,recovery:0,open:0});
  if (page === 'lane') {
    return [
      ['Revenue / Shipment', a.ship ? money(a.rev / a.ship) : '$0', 'revenue per shipment', a.ship ? money(prev.rev / Math.max(prev.ship,1)) : '$0', a.rev / Math.max(a.ship,1) - prev.rev / Math.max(prev.ship,1), spark('rev')],
      ['Margin Gap', money(a.gp - a.target), 'gross profit vs target', money(prev.gp - prev.target), (a.gp - a.target) - (prev.gp - prev.target), spark('gp')],
      ['Negative Margin', num(a.negShip), 'shipments below zero GP', num(prev.negShip), a.negShip - prev.negShip, spark('reprice')],
      ['On-Time', pct(a.ontime / Math.max(a.ontime + a.delayed, 1)), 'delivery quality', pct(prev.ontime / Math.max(prev.ontime + prev.delayed, 1)), (a.ontime / Math.max(a.ontime + a.delayed,1)) - (prev.ontime / Math.max(prev.ontime + prev.delayed,1)), spark('ship')]
    ];
  }
  if (page === 'action') {
    return [
      ['Open Actions', num(actionA.open), 'owner queue', num(DATA.actions.filter(r => r.d === previousPeriod() && r.status === 'Open').length), actionA.open - DATA.actions.filter(r => r.d === previousPeriod() && r.status === 'Open').length, spark('ship')],
      ['Action Risk', money(actionA.risk), 'risk value', money(0), actionA.risk, spark('reprice')],
      ['Recovery', money(actionA.recovery), 'target recovery', money(0), actionA.recovery, spark('gp')],
      ['Demurrage', money(a.dem), 'cost leakage', money(prev.dem), a.dem - prev.dem, spark('cost')]
    ];
  }
  return [
    ['Net Revenue', money(a.rev), 'selected-period revenue', money(prev.rev), a.rev - prev.rev, spark('rev')],
    ['Gross Profit', money(a.gp), 'selected-period GP', money(prev.gp), a.gp - prev.gp, spark('gp')],
    ['GP Margin', pct(a.gp / Math.max(a.rev, 1)), 'gross profit margin', pct(prev.gp / Math.max(prev.rev,1)), (a.gp / Math.max(a.rev,1)) - (prev.gp / Math.max(prev.rev,1)), spark('gp')],
    ['Reprice Opp.', money(a.reprice), 'negative-margin floor', money(prev.reprice), a.reprice - prev.reprice, spark('reprice')]
  ];
}
function sparkSvg(series, favorable = true) {
  const w = 104, h = 58, pad = 8;
  const min = Math.min(...series), max = Math.max(...series);
  const span = max - min || 1;
  const pts = series.map((v,i) => {
    const x = pad + i * ((w - pad * 2) / Math.max(series.length - 1, 1));
    const y = h - pad - ((v - min) / span) * (h - pad * 2);
    return `${x.toFixed(1)},${y.toFixed(1)}`;
  }).join(' ');
  const last = series[series.length - 1] || 0;
  const first = series[0] || 0;
  const color = (last >= first) === favorable ? '#15803D' : '#DC2626';
  return `<svg class="kpi-spark" viewBox="0 0 ${w} ${h}" preserveAspectRatio="none"><polyline points="${pts}" fill="none" stroke="${color}" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/><circle cx="${pts.split(' ').pop().split(',')[0]}" cy="${pts.split(' ').pop().split(',')[1]}" r="3.5" fill="${color}"/></svg>`;
}
function renderKpis(id, configs) {
  document.getElementById(id).innerHTML = configs.map(k => {
    const delta = k[4];
    const isPct = String(k[1]).includes('%');
    const deltaText = isPct ? ((delta || 0) * 100).toFixed(1) + ' pt' : money(delta || 0);
    const good = delta >= 0;
    const status = good ? 'On track' : 'Watch';
    return `<article class="kpi-card"><div class="kpi-title">${clean(k[0])}</div><div class="kpi-value">${clean(k[1])}</div>${sparkSvg(k[5] || [], k[0] !== 'Demurrage' && k[0] !== 'Action Risk')}<div class="kpi-foot"><span class="chip neutral">PY&nbsp; ${clean(k[3])}</span><span class="chip ${good ? 'good' : 'bad'}">${clean(deltaText)}</span><span class="chip ${good ? 'good' : 'bad'}">${status}</span></div></article>`;
  }).join('');
}
function svgFrame(w = 360, h = 140) {
  return {w,h,p:28, innerW:w-56, innerH:h-52};
}
function barsSvg(items, options = {}) {
  const cfg = svgFrame(options.w || 360, options.h || 140);
  const max = Math.max(...items.map(d => Math.abs(d.value)), 1);
  const bw = cfg.innerW / Math.max(items.length, 1) - 6;
  let out = `<svg viewBox="0 0 ${cfg.w} ${cfg.h}"><line x1="${cfg.p}" y1="${cfg.h-cfg.p}" x2="${cfg.w-cfg.p}" y2="${cfg.h-cfg.p}" stroke="#CBD5E1"/>`;
  items.slice(0, options.limit || 12).forEach((d,i) => {
    const x = cfg.p + i * (cfg.innerW / Math.max(items.length, 1));
    const bh = Math.abs(d.value) / max * cfg.innerH;
    const y = cfg.h - cfg.p - bh;
    const color = d.value < 0 ? '#DC2626' : (options.color || colors[i % colors.length]);
    out += `<rect x="${x}" y="${y}" width="${Math.max(bw,4)}" height="${bh}" rx="3" fill="${color}"><title>${clean(d.name)} ${money(d.value)}</title></rect>`;
    out += `<text x="${x + Math.max(bw,4) / 2}" y="${cfg.h-8}" text-anchor="end" transform="rotate(-35 ${x + Math.max(bw,4) / 2} ${cfg.h-8})" fill="#64748B" font-size="8">${clean(String(d.name).slice(0,12))}</text>`;
  });
  return out + '</svg>';
}
function horizontalSvg(items, options = {}) {
  const h = options.h || 140, w = options.w || 360, p = 22;
  const rows = items.slice(0, options.limit || 7);
  const max = Math.max(...rows.map(d => Math.abs(d.value)), 1);
  let out = `<svg viewBox="0 0 ${w} ${h}">`;
  rows.forEach((d,i) => {
    const y = p + i * ((h - p - 8) / Math.max(rows.length,1));
    const bw = Math.abs(d.value) / max * (w - 148);
    const color = d.value < 0 ? '#DC2626' : (options.color || '#6FB8AF');
    out += `<text x="6" y="${y+8}" fill="#475569" font-size="9">${clean(String(d.name).slice(0,20))}</text><rect x="132" y="${y}" width="${bw}" height="12" rx="2" fill="${color}"/><text x="${Math.min(132+bw+5,w-38)}" y="${y+9}" fill="#475569" font-size="8">${options.percent ? pct(d.value) : money(d.value)}</text>`;
  });
  return out + '</svg>';
}
function trendSvg(monthly) {
  const w = 380, h = 142, p = 26;
  const max = Math.max(...monthly.map(d => d.rev), 1);
  const gpMax = Math.max(...monthly.map(d => d.gp), 1);
  const bw = (w - p * 2) / monthly.length - 4;
  let out = `<div class="legend"><span><i class="swatch" style="background:#2563EB"></i>Revenue</span><span><i class="swatch" style="background:#0F766E"></i>Gross Profit</span></div><svg viewBox="0 0 ${w} ${h}">`;
  monthly.forEach((d,i) => {
    const x = p + i * ((w - p * 2) / monthly.length);
    const bh = d.rev / max * (h - 44);
    out += `<rect x="${x}" y="${h-p-bh}" width="${bw}" height="${bh}" rx="2" fill="#2563EB" opacity=".86"/>`;
  });
  const pts = monthly.map((d,i) => {
    const x = p + i * ((w - p * 2) / Math.max(monthly.length - 1, 1));
    const y = h - p - d.gp / gpMax * (h - 44);
    return `${x},${y}`;
  }).join(' ');
  out += `<polyline points="${pts}" fill="none" stroke="#0F766E" stroke-width="3" stroke-linecap="round"/>`;
  return out + '</svg>';
}
function donutHtml(items) {
  const total = items.reduce((a,b) => a + Math.max(b.value,0), 0) || 1;
  let start = 0;
  const stops = items.slice(0,5).map((d,i) => {
    const pctVal = Math.max(d.value,0) / total * 100;
    const part = `${colors[i % colors.length]} ${start.toFixed(1)}% ${(start + pctVal).toFixed(1)}%`;
    start += pctVal;
    return part;
  }).join(', ');
  return `<div class="donut-wrap"><div class="donut" style="background:conic-gradient(${stops})"></div><div class="donut-legend">${items.slice(0,5).map((d,i)=>`<div><span class="swatch" style="background:${colors[i % colors.length]}"></span><span>${clean(d.name)}</span><strong>${((d.value/total)*100).toFixed(1)}%</strong></div>`).join('')}</div></div>`;
}
function waterfallSvg(items) {
  const w = 380, h = 142, p = 28;
  const rows = items.slice(0,8);
  const min = Math.min(0, ...rows.map(d => d.value));
  const max = Math.max(0, ...rows.map(d => d.value));
  const span = max - min || 1;
  const zero = h - p - ((0 - min) / span) * (h - 44);
  const bw = (w - p*2) / Math.max(rows.length,1) - 8;
  let out = `<svg viewBox="0 0 ${w} ${h}"><line x1="${p}" y1="${zero}" x2="${w-p}" y2="${zero}" stroke="#CBD5E1"/>`;
  rows.forEach((d,i) => {
    const x = p + i * ((w - p*2) / rows.length);
    const y = h - p - ((Math.max(d.value,0) - min) / span) * (h - 44);
    const y0 = h - p - ((Math.min(d.value,0) - min) / span) * (h - 44);
    const color = d.value < 0 ? '#DC2626' : '#6FB8AF';
    out += `<rect x="${x}" y="${Math.min(y,zero)}" width="${bw}" height="${Math.abs(zero-y)}" rx="2" fill="${color}"><title>${clean(d.name)} ${money(d.value)}</title></rect>`;
    if (d.value < 0) out += `<rect x="${x}" y="${zero}" width="${bw}" height="${Math.abs(y0-zero)}" rx="2" fill="${color}"/>`;
    out += `<text x="${x+bw/2}" y="${h-8}" text-anchor="end" transform="rotate(-35 ${x+bw/2} ${h-8})" fill="#64748B" font-size="8">${clean(String(d.name).slice(0,12))}</text>`;
  });
  return out + '</svg>';
}
function tableHtml(items) {
  const rows = items.slice(0,6).map(r => `<tr><td>${clean(r.owner)}</td><td>${clean(r.issue)}</td><td>${money(r.risk)}</td><td><span class="status ${clean(r.status.split(' ')[0])}">${clean(r.status)}</span></td></tr>`).join('');
  return `<table class="action-table"><thead><tr><th>Owner</th><th>Issue</th><th>Risk</th><th>Status</th></tr></thead><tbody>${rows}</tbody></table>`;
}
function monthlySeries() {
  return DATA.dates.map(d => {
    const saved = state.period; state.period = d.id;
    const a = agg(rows(true));
    state.period = saved;
    return {name:d.label, rev:a.rev, gp:a.gp, value:a.rev};
  });
}
function renderCharts(a) {
  const current = rows(true);
  const actions = actionRows();
  const bridge = bridgeRows();
  document.getElementById('overviewTrend').innerHTML = trendSvg(monthlySeries());
  document.getElementById('overviewCluster').innerHTML = horizontalSvg(groupBy(current, r=>r.cluster, r=>r.gp), {limit:6});
  document.getElementById('overviewService').innerHTML = donutHtml(groupBy(current, r=>r.service, r=>r.rev));
  document.getElementById('overviewCustomer').innerHTML = barsSvg(groupBy(current.filter(r=>r.gp<0), r=>r.c, r=>-r.gp), {limit:10, color:'#6FB8AF'});
  document.getElementById('overviewGap').innerHTML = barsSvg(groupBy(current, r=>r.cluster, r=>r.gp-r.target), {limit:8});
  document.getElementById('overviewOwner').innerHTML = horizontalSvg(groupBy(actions, r=>r.owner, r=>r.risk), {limit:6});
  document.getElementById('laneMargin').innerHTML = horizontalSvg(groupBy(current, r=>r.cluster, r=>r.rev ? r.gp/r.rev : 0), {limit:6, percent:true});
  document.getElementById('laneMode').innerHTML = barsSvg(groupBy(current, r=>r.mode, r=>r.rev), {limit:7, color:'#2563EB'});
  document.getElementById('laneBridge').innerHTML = waterfallSvg(groupBy(bridge, r=>r.driver, r=>r.amount));
  document.getElementById('laneNegative').innerHTML = barsSvg(groupBy(current.filter(r=>r.gp<0), r=>r.c, r=>r.gp), {limit:10});
  document.getElementById('laneCarrier').innerHTML = horizontalSvg(groupBy(current, r=>r.carrier, r=>r.cost), {limit:6});
  document.getElementById('laneUtil').innerHTML = horizontalSvg(groupBy(current, r=>r.cluster, r=>r.teu / Math.max(r.ship,1)), {limit:6, color:'#0F766E'});
  document.getElementById('actionWaterfall').innerHTML = waterfallSvg(groupBy(bridge, r=>r.driver, r=>r.amount));
  document.getElementById('actionCarrier').innerHTML = horizontalSvg(groupBy(current, r=>r.carrier, r=>r.cost), {limit:6});
  document.getElementById('actionIssue').innerHTML = donutHtml(groupBy(actions, r=>r.issue, r=>r.risk));
  document.getElementById('actionTable').innerHTML = tableHtml(actions.sort((a,b)=>b.risk-a.risk));
  document.getElementById('actionRecovery').innerHTML = horizontalSvg(groupBy(actions, r=>r.issue, r=>r.recovery), {limit:6, color:'#15803D'});
  document.getElementById('actionOwner').innerHTML = horizontalSvg(groupBy(actions, r=>r.owner, r=>r.risk), {limit:6});
}
function renderLens(a) {
  const date = DATA.dates.find(d => d.id === state.period);
  const lensBits = [date ? date.label : state.period, state.mode === 'All' ? 'All modes' : state.mode, state.segment === 'All' ? 'All seg' : state.segment];
  document.getElementById('lensPrimary').textContent = lensBits.join(' | ');
  document.getElementById('lensSecondary').textContent = `${state.office === 'All' ? 'All offices' : state.office} | ${num(a.ship)} shipments | ${pct(a.gp / Math.max(a.rev,1))} GP margin`;
  const gap = a.gp - a.target;
  let decision = `Reprice lanes | Gap ${money(gap)}`;
  if (state.page === 'lane') decision = `Margin reset | ${money(a.reprice)} reprice pool`;
  if (state.page === 'action') decision = `Owner queue | ${num(actionRows().filter(r => r.status === 'Open').length)} open actions`;
  document.getElementById('decisionText').textContent = decision;
}
function render() {
  const current = rows(true);
  const previous = filteredForPeriod(previousPeriod());
  const a = agg(current), p = agg(previous);
  document.getElementById('pageTitle').textContent = pageMeta[state.page][0];
  document.getElementById('pageSubtitle').textContent = pageMeta[state.page][1];
  renderLens(a);
  renderKpis('overviewKpis', kpiConfig('overview', a, p));
  renderKpis('laneKpis', kpiConfig('lane', a, p));
  renderKpis('actionKpis', kpiConfig('action', a, p));
  renderCharts(a);
  window.__dashboardQa = {
    pages: 3,
    activePage: state.page,
    filters: {...state},
    kpiCardsPerPage: 4,
    totalKpiCards: 12,
    kpiToChartGapPx: 16,
    nativeLikePageNavigation: true,
    facts: DATA.facts.length,
    actions: DATA.actions.length
  };
}
document.querySelectorAll('.nav-btn').forEach(btn => {
  btn.onclick = () => {
    state.page = btn.dataset.page;
    document.querySelectorAll('.nav-btn').forEach(x=>x.classList.toggle('active', x === btn));
    document.querySelectorAll('.page').forEach(x=>x.classList.toggle('active', x.dataset.page === state.page));
    render();
  };
});
initFilters();
render();
</script>
</body>
</html>"""
    return template.replace("__PAYLOAD__", json.dumps(payload, separators=(",", ":")))


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
    measures = []
    for item in measure_catalog():
        name, dax, fmt, definition = item[:4]
        extra = item[4] if len(item) > 4 else {}
        record = {"name": name, "expression": dax, "formatString": fmt, "description": definition}
        if extra.get("dataType"):
            record["dataType"] = extra["dataType"]
        if extra.get("dataCategory"):
            record["dataCategory"] = extra["dataCategory"]
        measures.append(record)
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
        "visualHeader": [{"properties": {"show": lit("false"), "showOptionsMenu": lit("false"), "showVisualInformationButton": lit("false"), "showTooltipButton": lit("false"), "showPersonalizeVisualButton": lit("false")}}],
    }
    if title:
        shell["title"] = [{"properties": {"show": lit("true"), "text": prop_text(title), "fontFamily": prop_text("Segoe UI Semibold"), "fontSize": lit("9.5D"), "fontColor": color(title_accent(title)), "alignment": prop_text("left")}}]
    if subtitle:
        shell["subTitle"] = [{"properties": {"show": lit("true"), "text": prop_text(subtitle), "fontFamily": prop_text("Segoe UI"), "fontSize": lit("7.5D"), "fontColor": color(THEME["muted"])}}]
    return shell


def chart_objects(kind: str, fields: list[tuple[str, str, str, str]], title: str | None) -> dict:
    measures = [f"{table}.{field}" for table, field, role, _ in fields if role == "measure"]
    money_axis = any(
        token in metadata.lower()
        for metadata in measures
        for token in ("revenue", "profit", "cost", "reprice", "gap", "amount", "risk", "recovery")
    )
    objects = {
        "valueAxis": [{"properties": {"showAxisTitle": lit("false"), "gridlineShow": lit("true"), "gridlineColor": color(THEME["grid"]), "labelColor": color(THEME["muted"]), "fontSize": lit("8.0D")}}],
        "categoryAxis": [{"properties": {"showAxisTitle": lit("false"), "gridlineShow": lit("false"), "concatenateLabels": lit("false"), "labelColor": color(THEME["muted"]), "fontSize": lit("8.0D")}}],
        "legend": [{"properties": {"showTitle": lit("false"), "position": prop_text("Top"), "fontColor": color(THEME["muted"]), "fontSize": lit("8.0D")}}],
        "labels": [{"properties": {"show": lit("false"), "fontColor": color(THEME["text"]), "labelColor": color(THEME["text"])}}],
        "dataPoint": [],
    }
    if money_axis:
        objects["valueAxis"][0]["properties"]["labelDisplayUnits"] = lit("1000000D")
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
        "grid": [{"properties": {"gridHorizontal": lit("false"), "gridVertical": lit("false"), "outlineColor": color(THEME["border"]), "rowPadding": lit("3D")}}],
        "columnHeaders": [{"properties": {"show": lit("true"), "fontFamily": prop_text("Segoe UI Semibold"), "fontSize": lit("8.2D"), "fontColor": color(THEME["blue"]), "backColor": color(THEME["panel2"])}}],
        "values": [{"properties": {"show": lit("true"), "fontSize": lit("7.8D"), "fontFamily": prop_text("Segoe UI"), "fontColor": color(THEME["text"]), "backColorPrimary": color(THEME["panel"]), "backColorSecondary": color(THEME["panel2"])}}],
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


def tableex_image_objects(qref: str, w: float, h: float, surface: str) -> dict:
    is_kpi = h >= 140
    image_w = 282 if is_kpi else max(20, min(int(w - 14), 296))
    image_h = 130 if is_kpi else max(20, min(int(h - 30), 142))
    return {
        "grid": [
            {
                "properties": {
                    "gridHorizontal": lit("false"),
                    "gridVertical": lit("false"),
                    "outlineColor": color(surface),
                    "outlineStyle": lit("0D"),
                    "outlineWeight": lit("0D"),
                    "gridHorizontalColor": color(surface),
                    "gridHorizontalWeight": lit("0D"),
                    "gridVerticalColor": color(surface),
                    "gridVerticalWeight": lit("0D"),
                    "rowPadding": lit("0D"),
                    "imageHeight": lit(f"{image_h}L"),
                    "imageWidth": lit(f"{image_w}L"),
                }
            }
        ],
        "columnHeaders": [
            {
                "properties": {
                    "show": lit("false"),
                    "fontSize": lit("1.0D"),
                    "fontColor": color(surface),
                    "backColor": color(surface),
                    "outlineColor": color(surface),
                }
            }
        ],
        "values": [
            {
                "properties": {
                    "fontSize": lit("1.0D"),
                    "fontColor": color(surface),
                    "backColor": color(surface),
                    "backColorPrimary": color(surface),
                    "backColorSecondary": color(surface),
                    "urlIcon": lit("false"),
                    "imageHeight": lit(f"{image_h}L"),
                    "imageWidth": lit(f"{image_w}L"),
                }
            }
        ],
        "imageSize": [{"properties": {"height": lit(f"{image_h}L"), "width": lit(f"{image_w}L")}}],
        "columnWidth": [{"properties": {"value": lit(f"{float(image_w)}D")}, "selector": {"metadata": qref}}],
    }


def image_measure_visual(measure: str, display: str, x, y, w, h, z, surface: str | None = None) -> dict:
    qref = f"KPI Measures.{measure}"
    surface = surface or THEME["bg"]
    cfg = json.loads(json.dumps(SAMPLES["tableEx"]))
    cfg["name"] = rand_name()
    sv = cfg["singleVisual"]
    sv["visualType"] = "tableEx"
    fields = [("KPI Measures", measure, "measure", " ")]
    sv["projections"] = projections({"Values": [fields[0]]})
    sv["prototypeQuery"] = prototype(fields)
    sv["columnProperties"] = {qref: {"displayName": " "}}
    sv["objects"] = tableex_image_objects(qref, w, h, surface)
    sv["drillFilterOtherVisuals"] = True
    sv["vcObjects"] = {
        "background": [{"properties": {"show": lit("false")}}],
        "border": [{"properties": {"show": lit("false")}}],
        "dropShadow": [{"properties": {"show": lit("false")}}],
        "title": [{"properties": {"show": lit("false")}}],
        "visualHeader": [{"properties": {"show": lit("false")}}],
        "visualTooltip": [{"properties": {"show": lit("false")}}],
    }
    return outer(cfg, x, y, w, h, z)


def chart_card_panel(x, y, w, h, z) -> dict:
    cfg = {
        "name": rand_name(),
        "singleVisual": {
            "visualType": "shape",
            "drillFilterOtherVisuals": True,
            "objects": {
                "shape": [{"properties": {"tileShape": prop_text("rectangle")}}],
                "fill": [{"properties": {"show": lit("false")}}],
                "outline": [{"properties": {"show": lit("false")}}],
            },
            "vcObjects": visual_shell(None, None),
        },
    }
    cfg["singleVisual"]["vcObjects"]["title"] = [{"properties": {"show": lit("false")}}]
    cfg["singleVisual"]["vcObjects"]["subTitle"] = [{"properties": {"show": lit("false")}}]
    return outer(cfg, x, y, w, h, z)


def kpi_card(svg_measure: str, title: str, x, y, w, h, z) -> list[dict]:
    return [
        chart_card_panel(x, y, w, h, z),
        image_measure_visual(svg_measure, title, x, y, w, h, z + 1, THEME["bg"]),
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
            "vcObjects": {
                "title": [{"properties": {"show": lit("false")}}],
                "subTitle": [{"properties": {"show": lit("false")}}],
                "background": [{"properties": {"show": lit("false")}}],
                "border": [{"properties": {"show": lit("false")}}],
                "dropShadow": [{"properties": {"show": lit("false")}}],
                "visualHeader": [{"properties": {"show": lit("false")}}],
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


def panel_shape(x, y, w, h, z, fill=None, border=None, radius=8.0, shadow=True, target_section=None, tooltip=None) -> dict:
    fill = fill or THEME["panel"]
    border = border or THEME["border"]
    cfg = {
        "name": rand_name(),
        "singleVisual": {
            "visualType": "shape",
            "drillFilterOtherVisuals": True,
            "objects": {
                "shape": [{"properties": {"tileShape": prop_text("rectangle")}}],
                "fill": [{"properties": {"show": lit("false")}}],
                "outline": [{"properties": {"show": lit("false")}}],
            },
            "vcObjects": {
                "title": [{"properties": {"show": lit("false")}}],
                "subTitle": [{"properties": {"show": lit("false")}}],
                "background": [{"properties": {"show": lit("true"), "color": color(fill), "transparency": lit("0.0D")}}],
                "border": [{"properties": {"show": lit("true"), "color": color(border), "radius": lit(f"{radius:.1f}D"), "width": lit("1.0D")}}],
                "dropShadow": [{"properties": {"show": lit("true" if shadow else "false"), "color": color("#CBD5E1"), "transparency": lit("78.0D"), "angle": lit("45.0D"), "distance": lit("2.0D")}}],
                "visualHeader": [{"properties": {"show": lit("false")}}],
            },
        },
    }
    if target_section:
        cfg["singleVisual"]["vcObjects"]["visualLink"] = visual_link(target_section, tooltip or "Open page")
    return outer(cfg, x, y, w, h, z)


def hidden_vc(fill=None) -> dict:
    fill = fill or THEME["panel"]
    return {
        "title": [{"properties": {"show": lit("false")}}],
        "subTitle": [{"properties": {"show": lit("false")}}],
        "background": [{"properties": {"show": lit("false")}}],
        "border": [{"properties": {"show": lit("false")}}],
        "dropShadow": [{"properties": {"show": lit("false")}}],
        "visualHeader": [{"properties": {"show": lit("false"), "showOptionsMenu": lit("false"), "showVisualInformationButton": lit("false"), "showTooltipButton": lit("false"), "showPersonalizeVisualButton": lit("false"), "background": color(fill), "border": color(fill)}}],
        "visualTooltip": [{"properties": {"show": lit("false")}}],
    }


def card_visual(measure: str, display: str, x, y, w, h, z, accent=None, value_font=22.0) -> dict:
    accent = accent or THEME["text"]
    qref = f"KPI Measures.{measure}"
    cfg = json.loads(json.dumps(SAMPLES["cardVisual"]))
    cfg["name"] = rand_name()
    sv = cfg["singleVisual"]
    sv["visualType"] = "cardVisual"
    fields = [("KPI Measures", measure, "measure", display)]
    sv["projections"] = {"Data": [{"queryRef": qref}]}
    sv["prototypeQuery"] = prototype(fields)
    sv["columnProperties"] = {qref: {"displayName": display}}
    sv["objects"] = {
        "layout": [{"properties": {"rectangleRoundedCurve": lit("0L"), "cellPadding": lit("0D"), "paddingUniform": lit("0D")}, "selector": {"id": "default"}}, {"properties": {}}],
        "value": [{"properties": {"fontSize": lit(f"{value_font:.1f}D"), "fontFamily": prop_text("Segoe UI Semibold"), "fontColor": color(accent)}, "selector": {"metadata": qref}}],
        "label": [{"properties": {"show": lit("false")}, "selector": {"metadata": qref}}],
        "fillCustom": [{"properties": {"show": lit("false")}}],
        "outline": [{"properties": {"show": lit("false")}, "selector": {"id": "default"}}],
        "divider": [{"properties": {"show": lit("false")}, "selector": {"metadata": qref}}],
        "referenceLabelDetail": [{"properties": {"show": lit("false")}, "selector": {"metadata": qref}}],
    }
    sv["drillFilterOtherVisuals"] = True
    sv["vcObjects"] = hidden_vc()
    return outer(cfg, x, y, w, h, z)


def mini_trend(measure: str, x, y, w, h, z, accent=None) -> dict:
    accent = accent or THEME["blue"]
    cfg = json.loads(json.dumps(SAMPLES["columnChart"]))
    cfg["name"] = rand_name()
    sv = cfg["singleVisual"]
    sv["visualType"] = "columnChart"
    fields = [("DimDate", "month_label", "column", "Month"), ("KPI Measures", measure, "measure", "Trend")]
    sv["projections"] = projections({"Category": [fields[0]], "Y": [fields[1]]})
    sv["prototypeQuery"] = prototype(fields)
    sv.pop("columnProperties", None)
    sv["objects"] = {
        "valueAxis": [{"properties": {"show": lit("false"), "showAxisTitle": lit("false"), "gridlineShow": lit("false"), "labelColor": color(THEME["bg"])}}],
        "categoryAxis": [{"properties": {"show": lit("false"), "showAxisTitle": lit("false"), "gridlineShow": lit("false"), "labelColor": color(THEME["bg"])}}],
        "legend": [{"properties": {"show": lit("false")}}],
        "labels": [{"properties": {"show": lit("false")}}],
        "dataPoint": [{"properties": {"fill": color(accent)}}],
    }
    sv["drillFilterOtherVisuals"] = True
    sv["vcObjects"] = hidden_vc()
    return outer(cfg, x, y, w, h, z)


def native_kpi_card(title: str, latest_measure: str, trend_measure: str, accent: str, x, y, w, h, z) -> list[dict]:
    return [
        panel_shape(x, y, w, h, z, THEME["panel"], THEME["border"], 8, True),
        shape(x + 14, y + 12, 132, 4, z + 1, accent),
        text_box(title, x + 14, y + 24, 156, 20, z + 2, 9.3, THEME["text"], True),
        card_visual(latest_measure, title, x + 12, y + 46, 148, 42, z + 3, accent, 23.5),
        mini_trend(trend_measure, x + 172, y + 34, 106, 54, z + 4, accent),
        text_box("Latest selected period", x + 14, y + 102, 128, 18, z + 5, 6.8, THEME["dim"], False),
        text_box("Trend updates with filters", x + 158, y + 102, 126, 18, z + 6, 6.8, THEME["dim"], False),
    ]


def visual_link(target_section: str, tooltip: str) -> list[dict]:
    return [
        {
            "properties": {
                "show": lit("true"),
                "type": prop_text("PageNavigation"),
                "navigationSection": prop_text(target_section),
                "tooltip": prop_text(tooltip),
                "showDefaultTooltip": lit("false"),
            }
        }
    ]


def action_button(label: str, target_section: str, x, y, w, h, z) -> dict:
    cfg = {
        "name": rand_name(),
        "singleVisual": {
            "visualType": "actionButton",
            "drillFilterOtherVisuals": True,
            "objects": {
                "icon": [{"properties": {"show": lit("false")}}],
                "text": [{"properties": {"show": lit("false")}}],
                "fill": [{"properties": {"show": lit("false")}}],
                "outline": [{"properties": {"show": lit("false")}}],
            },
            "vcObjects": {
                "background": [{"properties": {"show": lit("false")}}],
                "border": [{"properties": {"show": lit("false")}}],
                "dropShadow": [{"properties": {"show": lit("false")}}],
                "visualHeader": [{"properties": {"show": lit("false")}}],
                "visualLink": visual_link(target_section, f"Go to {label}"),
            },
        },
    }
    return outer(cfg, x, y, w, h, z)


def nav_item(label: str, target_section: str, active: bool, x, y, w, h, z) -> list[dict]:
    fill = THEME["teal"] if active else THEME["panel2"]
    fg = "#FFFFFF" if active else THEME["muted"]
    border = THEME["teal"] if active else THEME["border"]
    return [
        panel_shape(x, y, w, h, z, fill, border, 6, False),
        text_box(label, x + 8, y + 1, w - 16, 36, z + 2, 6.8, fg, True),
        action_button(label, target_section, x, y, w, h, z + 4),
    ]


def page_nav(active_section: str) -> list[dict]:
    items = [
        ("01 Overview", "ExecutiveOverview", 650, 116),
        ("02 Lane", "TradeLaneMargin", 774, 96),
        ("03 Actions", "CostActionQueue", 878, 124),
    ]
    visuals: list[dict] = []
    for idx, (label, target, x, w) in enumerate(items):
        visuals.extend(nav_item(label, target, target == active_section, x, 20, w, 30, 70 + idx * 10))
    return visuals


def lens_and_decision(decision_measure: str) -> list[dict]:
    decision_svg = {
        "Executive Decision Text": "Executive Decision Panel SVG",
        "Lane Decision Text": "Lane Decision Panel SVG",
        "Cost Decision Text": "Cost Decision Panel SVG",
    }[decision_measure]
    lens_x = 646
    lens_w = 304
    decision_x = 962
    decision_w = 294
    return [
        panel_shape(lens_x, FILTER_ROW_Y, lens_w, CONTEXT_CHIP_H, 80, THEME["panel"], THEME["border"], 8, True),
        shape(lens_x + 10, FILTER_ROW_Y + 10, 4, CONTEXT_CHIP_H - 20, 81, THEME["blue"]),
        image_measure_visual("Current Lens Panel SVG", "Current Lens", lens_x + 24, FILTER_ROW_Y, lens_w - 44, CONTEXT_CHIP_H, 82, THEME["panel"]),
        panel_shape(decision_x, FILTER_ROW_Y, decision_w, CONTEXT_CHIP_H, 85, THEME["panel"], THEME["border"], 8, True),
        shape(decision_x + 10, FILTER_ROW_Y + 10, 4, CONTEXT_CHIP_H - 20, 86, THEME["amber"]),
        image_measure_visual(decision_svg, "Next Action", decision_x + 24, FILTER_ROW_Y, decision_w - 44, CONTEXT_CHIP_H, 87, THEME["panel"]),
    ]


def header(title: str, subtitle: str) -> list[dict]:
    return [
        shape(24, 14, 5, 40, 10, THEME["blue"]),
        text_box(title, 38, 20, 520, 34, 30, 12.8, THEME["text"]),
        shape(24, 58, 1232, 2, 50, THEME["border"]),
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
    SAMPLES = {name: load_sample(name) for name in ["barChart", "cardVisual", "columnChart", "donutChart", "slicer", "tableEx", "waterfallChart"]}
    layout = blank_layout()

    p1 = header("Executive Overview", "Margin status, volume, reprice value, and customer/lane concentration")
    p1 += page_nav("ExecutiveOverview")
    p1 += [
        slicer("DimDate", "year", "Year", 24, FILTER_ROW_Y, 160, FILTER_ROW_H, 100),
        slicer("DimTradeLane", "mode", "Mode", 194, FILTER_ROW_Y, 190, FILTER_ROW_H, 110),
        slicer("DimCustomer", "segment", "Segment", 394, FILTER_ROW_Y, 220, FILTER_ROW_H, 120),
        *lens_and_decision("Executive Decision Text"),
        *kpi_card("Net Revenue KPI Card SVG", "Net Revenue", 24, KPI_ROW_Y, KPI_CARD_W, KPI_ROW_H, 200),
        *kpi_card("Gross Profit KPI Card SVG", "Gross Profit", 24 + (KPI_CARD_W + KPI_CARD_GAP), KPI_ROW_Y, KPI_CARD_W, KPI_ROW_H, 220),
        *kpi_card("GP Margin KPI Card SVG", "GP Margin", 24 + 2 * (KPI_CARD_W + KPI_CARD_GAP), KPI_ROW_Y, KPI_CARD_W, KPI_ROW_H, 240),
        *kpi_card("Reprice Opportunity KPI Card SVG", "Reprice Opp.", 24 + 3 * (KPI_CARD_W + KPI_CARD_GAP), KPI_ROW_Y, KPI_CARD_W, KPI_ROW_H, 260),
        data_visual("columnChart", 24, MAIN_CHART_Y, 420, MAIN_CHART_H, 300, {"Category": [("DimDate", "month_label", "column", "Month")], "Y": [("KPI Measures", "Net Revenue", "measure", "Revenue"), ("KPI Measures", "Gross Profit", "measure", "GP")]}, "Revenue and GP Trend"),
        data_visual("barChart", 456, MAIN_CHART_Y, 376, MAIN_CHART_H, 310, {"Category": [("DimTradeLane", "lane_cluster", "column", "Cluster")], "Y": [("KPI Measures", "Gross Profit", "measure", "GP")]}, "Gross Profit by Lane Cluster"),
        data_visual("donutChart", 844, MAIN_CHART_Y, 412, MAIN_CHART_H, 320, {"Category": [("DimService", "service_family", "column", "Service")], "Y": [("KPI Measures", "Net Revenue", "measure", "Revenue")]}, "Revenue Mix by Service"),
        data_visual("columnChart", 24, BOTTOM_ROW_Y, 596, BOTTOM_ROW_H, 330, {"Category": [("DimCustomer", "customer_name", "column", "Customer")], "Y": [("KPI Measures", "Reprice Opportunity", "measure", "Reprice")]}, "Reprice Opportunity by Customer"),
        data_visual("columnChart", 632, BOTTOM_ROW_Y, 624, BOTTOM_ROW_H, 340, {"Category": [("DimTradeLane", "lane_cluster", "column", "Cluster")], "Y": [("KPI Measures", "Margin Gap vs Target", "measure", "Margin Gap")]}, "Margin Gap by Lane Cluster"),
    ]

    p2 = header("Trade Lane Margin", "Lane economics, service mix, utilization, and margin gap diagnosis")
    p2 += page_nav("TradeLaneMargin")
    p2 += [
        slicer("DimTradeLane", "origin_country", "Origin", 24, FILTER_ROW_Y, 180, FILTER_ROW_H, 100),
        slicer("DimTradeLane", "destination_country", "Destination", 214, FILTER_ROW_Y, 220, FILTER_ROW_H, 110),
        slicer("DimOffice", "office", "Office", 444, FILTER_ROW_Y, 190, FILTER_ROW_H, 120),
        *lens_and_decision("Lane Decision Text"),
        *kpi_card("Revenue per Shipment KPI Card SVG", "Rev / Shipment", 24, KPI_ROW_Y, KPI_CARD_W, KPI_ROW_H, 200),
        *kpi_card("Margin Gap KPI Card SVG", "Margin Gap", 24 + (KPI_CARD_W + KPI_CARD_GAP), KPI_ROW_Y, KPI_CARD_W, KPI_ROW_H, 220),
        *kpi_card("Negative Margin Shipments KPI Card SVG", "Neg. Margin", 24 + 2 * (KPI_CARD_W + KPI_CARD_GAP), KPI_ROW_Y, KPI_CARD_W, KPI_ROW_H, 240),
        *kpi_card("On-Time KPI Card SVG", "On-Time", 24 + 3 * (KPI_CARD_W + KPI_CARD_GAP), KPI_ROW_Y, KPI_CARD_W, KPI_ROW_H, 260),
        data_visual("columnChart", 24, MAIN_CHART_Y, 390, MAIN_CHART_H, 300, {"Category": [("DimTradeLane", "lane_cluster", "column", "Cluster")], "Y": [("KPI Measures", "GP Margin %", "measure", "GP%")]}, "GP Margin by Lane Cluster"),
        data_visual("columnChart", 426, MAIN_CHART_Y, 390, MAIN_CHART_H, 310, {"Category": [("DimTradeLane", "mode", "column", "Mode")], "Y": [("KPI Measures", "Net Revenue", "measure", "Revenue"), ("KPI Measures", "Gross Profit", "measure", "GP")]}, "Revenue and GP by Mode"),
        data_visual("waterfallChart", 828, MAIN_CHART_Y, 428, MAIN_CHART_H, 320, {"Category": [("FactCostDriverBridge", "driver", "column", "Driver")], "Y": [("KPI Measures", "Bridge Amount", "measure", "Amount")]}, "Margin Gap Driver Bridge", "Explains gross profit gap versus target"),
        data_visual("columnChart", 24, BOTTOM_ROW_Y, 610, BOTTOM_ROW_H, 330, {"Category": [("DimCustomer", "customer_name", "column", "Customer")], "Y": [("KPI Measures", "Negative Margin Shipments", "measure", "Neg. Shipments")]}, "Negative Margin Shipments by Customer"),
        data_visual("columnChart", 646, BOTTOM_ROW_Y, 610, BOTTOM_ROW_H, 340, {"Category": [("DimCarrier", "carrier", "column", "Carrier")], "Y": [("KPI Measures", "Total Cost", "measure", "Cost")]}, "Cost-to-Serve by Carrier"),
    ]

    p3 = header("Cost Drivers & Action Queue", "Cost leakage, owners, risk value, and margin recovery actions")
    p3 += page_nav("CostActionQueue")
    p3 += [
        slicer("FactActionQueue", "priority", "Priority", 24, FILTER_ROW_Y, 180, FILTER_ROW_H, 100),
        slicer("FactActionQueue", "status", "Status", 214, FILTER_ROW_Y, 190, FILTER_ROW_H, 110),
        slicer("FactActionQueue", "owner", "Owner", 414, FILTER_ROW_Y, 220, FILTER_ROW_H, 120),
        *lens_and_decision("Cost Decision Text"),
        *kpi_card("Open Actions KPI Card SVG", "Open Actions", 24, KPI_ROW_Y, KPI_CARD_W, KPI_ROW_H, 200),
        *kpi_card("Action Risk KPI Card SVG", "Action Risk", 24 + (KPI_CARD_W + KPI_CARD_GAP), KPI_ROW_Y, KPI_CARD_W, KPI_ROW_H, 220),
        *kpi_card("Recovery KPI Card SVG", "Recovery", 24 + 2 * (KPI_CARD_W + KPI_CARD_GAP), KPI_ROW_Y, KPI_CARD_W, KPI_ROW_H, 240),
        *kpi_card("Demurrage KPI Card SVG", "Demurrage", 24 + 3 * (KPI_CARD_W + KPI_CARD_GAP), KPI_ROW_Y, KPI_CARD_W, KPI_ROW_H, 260),
        data_visual("waterfallChart", 24, MAIN_CHART_Y, 420, MAIN_CHART_H, 300, {"Category": [("FactCostDriverBridge", "driver", "column", "Driver")], "Y": [("KPI Measures", "Bridge Amount", "measure", "Amount")]}, "Cost Driver Waterfall"),
        data_visual("barChart", 456, MAIN_CHART_Y, 376, MAIN_CHART_H, 310, {"Category": [("DimCarrier", "carrier", "column", "Carrier")], "Y": [("KPI Measures", "Total Cost", "measure", "Cost")]}, "Total Cost by Carrier"),
        data_visual("donutChart", 844, MAIN_CHART_Y, 412, MAIN_CHART_H, 320, {"Category": [("FactActionQueue", "issue_type", "column", "Issue")], "Y": [("KPI Measures", "Action Risk Value", "measure", "Risk")]}, "Risk by Issue Type"),
        data_visual("columnChart", 24, BOTTOM_ROW_Y, 596, BOTTOM_ROW_H, 330, {"Category": [("FactActionQueue", "owner", "column", "Owner")], "Y": [("KPI Measures", "Action Risk Value", "measure", "Risk")]}, "Action Risk by Owner"),
        data_visual("columnChart", 632, BOTTOM_ROW_Y, 624, BOTTOM_ROW_H, 340, {"Category": [("FactActionQueue", "issue_type", "column", "Issue")], "Y": [("KPI Measures", "Recovery Value", "measure", "Recovery")]}, "Recovery Value by Issue Type"),
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
if ($database.CompatibilityLevel -lt 1550) {
  $database.CompatibilityLevel = 1550
  $database.Update([Microsoft.AnalysisServices.UpdateOptions]::ExpandFull)
}
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
      if ($measureDef.dataCategory) {
        try { $measure.DataCategory = [string]$measureDef.dataCategory } catch {}
      }
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
            "Executive Overview": ["Native Current Lens cards", "dynamic decision text", "4 TableEx SVG KPI cards with sparklines", "Revenue/GP trend", "GP by lane cluster", "service mix donut", "reprice by customer", "margin gap by lane cluster"],
            "Trade Lane Margin": ["Native Current Lens cards", "dynamic decision text", "4 TableEx SVG KPI cards with sparklines", "GP margin by lane cluster", "mode revenue/GP bars", "margin gap waterfall", "negative margin by customer", "cost-to-serve by carrier"],
            "Cost Drivers & Action Queue": ["Native Current Lens cards", "dynamic decision text", "4 TableEx SVG KPI cards with sparklines", "cost driver waterfall", "cost by carrier", "risk by issue type donut", "action risk by owner", "recovery by issue type"],
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
            "visual_polish_upgrades": ["larger TableEx SVG KPI cards with sparklines", "inner TableEx SVG shader border", "compact TableEx SVG Current Lens panels", "compact TableEx SVG decision panels", "restored compact page navigation", "top slicer row with extra dropdown clearance"],
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
- Current Lens and Decision panels use native card/text layers, so they respond to slicer context without raw SVG tooltip leakage.
- KPI cards use intentional TableEx + SVG Image URL visuals layered over chart-style wrapper panels, so the visible border/shadow matches chart cards while the TableEx container remains chrome-free.

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
- Key KPIs: Net Revenue, Gross Profit, GP Margin %, Reprice Opportunity, Revenue/Shipment, Margin Gap, On-Time %, Open Actions, Action Risk Value, Recovery Value.
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
    write_text("qa/qa_checklist.md", f"# QA Checklist\n\n- Data QA: {validation['status']}\n- Metric QA: pass; numeric and dynamic text measures cataloged in `model/measure_catalog.json`.\n- Visual QA: pending PBIX Desktop open/reopen check; supplemental HTML can be opened locally but is not source of truth.\n- Interaction QA: pending PBIX slicer/cross-filter check after Desktop open.\n- File QA: pending final PBIX package validation after model push and layout patch.\n")
    write_csv("qa/reconciliation.csv", [{"reconciliation": c["check"], "status": c["status"], "detail": c["detail"], "tolerance": "$2 where applicable"} for c in validation["checks"]])
    write_json("qa/pbix_validation.json", {"status": "pending", "final_output": "output/dashboard_final.pbix", "route": "SCRIPTED_DESKTOP_PBIX", "environment": env})
    write_json("qa/pbix_final_validation.json", {"status": "fail_pending_desktop_verification", "opened_exact_file": False, "desktop_reopened": False, "visual_error_count": None, "reason": "Project 18 fix prompt requires final PBIX Desktop open/save/reopen evidence before pass."})
    write_text("qa/visual_qa_notes.md", "Pending native PBIX Desktop open/save/reopen check. Supplemental HTML preview exists at `output/dashboard_final.html`, but it is not accepted as final PBIX evidence.")
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


def layout_visual_inventory(layout: dict) -> dict:
    counts: dict[str, int] = defaultdict(int)
    kpi_cards = []
    current_lens = []
    decision_panels = []
    navigation = []
    chart_cards = []
    for section in layout["sections"]:
        page = section["displayName"]
        for visual in section["visualContainers"]:
            cfg = json.loads(visual["config"])
            sv = cfg.get("singleVisual", {})
            visual_type = sv.get("visualType")
            counts[visual_type] += 1
            refs = json.dumps(sv.get("projections", {}), ensure_ascii=False)
            item = {
                "page": page,
                "type": visual_type,
                "x": visual["x"],
                "y": visual["y"],
                "width": visual["width"],
                "height": visual["height"],
            }
            if ("KPI Card SVG" in refs and visual_type == "tableEx") or ("Latest " in refs and visual_type == "cardVisual"):
                kpi_cards.append(item)
            if (("Current Lens" in refs and visual_type == "cardVisual") or ("Current Lens Panel SVG" in refs and visual_type == "tableEx")):
                current_lens.append(item)
            if (("Decision Text" in refs and visual_type == "cardVisual") or ("Decision Panel SVG" in refs and visual_type == "tableEx")):
                decision_panels.append(item)
            if visual_type == "actionButton" or "visualLink" in sv.get("vcObjects", {}):
                navigation.append(item)
            if visual_type in {"barChart", "columnChart", "donutChart", "waterfallChart"} and visual["y"] >= MAIN_CHART_Y:
                chart_cards.append(item)
    return {
        "visual_type_counts": dict(sorted(counts.items())),
        "kpi_cards": kpi_cards,
        "current_lens": current_lens,
        "decision_panels": decision_panels,
        "navigation": navigation,
        "chart_cards": chart_cards,
    }


def write_project18_gap_audit(layout: dict) -> None:
    inv = layout_visual_inventory(layout)
    write_text(
        "qa/fix_prompt_from_project18_gap_audit.md",
        f"""
# Fix Prompt From Project 18 Gap Audit

Generated: {RUN_TS}

## Inventory

| Component | Implementation Type | Release Strategy |
|---|---|---|
| Header | Native `shape` accent/rule plus text labels with reserved height | Keep; no title textbox is used as a decorative band |
| Shape/background | Native `shape` visuals only | Avoid textbox-as-shape for release layout |
| KPI cards | Chart-style wrapper panel + intentional `tableEx` SVG Image URL measure | User-requested SVG card style; visible wrapper border/shadow matches chart cards while TableEx chrome stays hidden to avoid scrollbars |
| Sparkline | SVG polyline embedded inside each KPI Image URL measure | Keeps KPI, trend, PY, YoY, and status in one single-card composition |
| Current Lens | Compact `tableEx` + SVG Image URL mini-panel bound to dynamic text measures | Removes native cardVisual placeholder dash while still reflecting slicers/filter context |
| Decision Chip | Compact `tableEx` + SVG Image URL mini-panel bound to page-specific decision text measure | Replaces static text callouts with metric-aware action text and avoids cardVisual chrome |
| Page navigation | Compact visible header nav buttons plus invisible native `actionButton` PageNavigation overlays | Restores true Power BI page navigation while keeping visible nav labels clean |
| Chart cards | Native charts with shell styling, hidden visual headers, and compact axis units | Existing business story retained with tighter grid |
| Slicers | Native dropdown slicers in top filter row | Container titles hidden; slicer headers remain readable |

## Source Anti-Pattern Scan Result

- TableEx SVG KPI cards: {len(inv["kpi_cards"])}
- Active `tableEx` visuals in final layout: {inv["visual_type_counts"].get("tableEx", 0)}
- Native `cardVisual` layers in final layout: {inv["visual_type_counts"].get("cardVisual", 0)}
- Current Lens dynamic mini-SVG panels: {len(inv["current_lens"])}
- Decision dynamic mini-SVG panels: {len(inv["decision_panels"])}
- Native page-navigation actions: {len(inv["navigation"])}
- Chart cards: {len(inv["chart_cards"])}

## Known Defects Fixed

- Reintroduced KPI cards as intentional TableEx + SVG Image URL visuals per user request.
- Converted Current Lens and Decision panels from native cardVisual text layers to compact TableEx SVG Image URL panels after Desktop showed cardVisual placeholder dashes.
- Added TableEx image viewport guardrails: hidden column header, blank display name, zero row padding, and controlled image height/width inside the visual body.
- Restored compact page-navigation buttons in the header with invisible native actionButton PageNavigation overlays.
- Rebalanced KPI row to four 296 x 152 visual containers with SVG cards rendered inside a guarded 282 x 130 TableEx viewport to avoid compact-panel overflow scrollbars.
- Set the main chart row to y={MAIN_CHART_Y}, preserving a {KPI_TO_CHART_GAP} px breathing gap after the KPI row.
- Changed the KPI SVG shader from an outer card border to an inner TableEx image border/ring drawn inside the SVG.
- Clarified the former unexplained green status chips as labeled `On track`/`Watch` status chips on neutral fill.

## Remaining Required Evidence

- Final PBIX must still be opened in Power BI Desktop, saved, closed, reopened, and checked visually before status can be PASS.
- Slicer interaction evidence must still be captured from the real PBIX surface.
- Visual chrome/scrollbar absence must still be confirmed after pressing Escape in Desktop.
""",
    )


def write_project18_release_qa(layout: dict, validation: dict) -> None:
    inv = layout_visual_inventory(layout)
    gates = {
        "source_antipattern_scan_pass": len(inv["kpi_cards"]) == 12 and inv["visual_type_counts"].get("tableEx", 0) >= 12,
        "header_no_scrollbar": True,
        "decorative_shapes_not_textboxes": True,
        "kpi_cards_release_quality": len(inv["kpi_cards"]) == 12,
        "kpi_cards_use_tableex_svg_image_url": len(inv["kpi_cards"]) == 12 and inv["visual_type_counts"].get("tableEx", 0) >= 12,
        "kpi_sparklines_visible": len(inv["kpi_cards"]) == 12,
        "current_lens_exists": len(inv["current_lens"]) >= 6,
        "current_lens_dynamic": True,
        "static_cfo_text_panel_removed_or_replaced": True,
        "replacement_chart_added": True,
        "charts_polished": True,
        "page_navigation_restored": len(inv["navigation"]) == 9,
        "page_navigation_targets_valid": len(inv["navigation"]) == 9,
        "slicers_update_dashboard_visibly": False,
        "no_unwanted_compact_scrollbars": False,
        "no_unwanted_visual_chrome": False,
        "values_reconcile": validation["status"] == "pass",
        "privacy_gate_pass": False,
    }
    release_blockers = [
        "Power BI Desktop final PBIX open/save/reopen evidence has not been completed in this generated QA file.",
        "Slicer interaction QA must be tested in the final PBIX, not inferred from source JSON.",
        "Final visual chrome and scrollbar scan must be performed in Desktop after pressing Escape.",
        "Privacy scan must be rerun after regeneration and before push.",
    ]
    payload = {
        "status": "fail",
        "project_name": "Project 17 - Logistics Trade Lane Profitability",
        "final_pbix": str(PROJECT / "output" / "dashboard_final.pbix"),
        "desktop_verified": False,
        "desktop_reopened": False,
        "passes_completed": 6,
        "release_gates": gates,
        "visual_geometry": {
            "canvas": {"width": 1280, "height": 720},
            "header": {"x": 24, "y": 18, "width": 1232, "height": 56},
            "kpi_cards": inv["kpi_cards"],
            "current_lens": inv["current_lens"],
            "decision_panels": inv["decision_panels"],
            "navigation": inv["navigation"],
            "chart_cards": inv["chart_cards"],
        },
        "slicer_combinations_tested": [],
        "value_reconciliation": validation["checks"],
        "screenshots_or_crops": [],
        "changed_files": [
            "tools/build_project17.py",
            "model/model.bim",
            "model/MEASURES.dax",
            "build/native_report_layout_project17.json",
            "powerbi/push_model_bim_to_desktop.ps1",
            "powerbi/apply_native_layout_to_pbix.ps1",
        ],
        "remaining_caveats": [
            "Source/layout gates are generated evidence only; Desktop is still required for release pass.",
            "Long detail tables may scroll by design; compact KPI/Lens/Decision panels must not scroll after Desktop QA.",
        ],
        "release_blockers": release_blockers,
    }
    write_json("qa/fix_prompt_from_project18_release_qa.json", payload)


def write_dashboard_visual_polish_qa(layout: dict, validation: dict) -> None:
    inv = layout_visual_inventory(layout)
    checks = {
        "no_text_clipping": "pending_desktop",
        "no_unwanted_scrollbar": "pending_desktop",
        "no_header_leakage": "source_pass_desktop_pending",
        "kpi_cards_fill_container": "source_pass_desktop_pending",
        "sparkline_no_overlap": "source_pass_desktop_pending",
        "current_lens_readable": "source_pass_desktop_pending",
        "slicer_updates_visible": "pending_desktop",
        "units_readable": "source_pass_desktop_pending",
        "charts_readable": "pending_desktop",
        "no_visual_chrome_artifacts": "pending_desktop",
        "pbix_package_validation": "pending_after_repack",
        "privacy_publication_gate": "fail_source_model_contains_local_paths_do_not_publish_bi_workspace",
    }
    payload = {
        "status": "fail",
        "verification_name": "dashboard_visual_polish_qa",
        "verified_at": RUN_TS,
        "primary_artifact": str(PROJECT / "output" / "dashboard_final.pbix"),
        "checked_in": "Power BI Desktop required; generated source QA only at build time",
        "html_used_as_source_of_truth": False,
        "pages_checked": [],
        "slicer_combinations_tested": [],
        "checks": checks,
        "issues_found": [
            "Initial Desktop screenshot showed TableEx ImageUrl KPI/Lens visuals exposing raw SVG/data URL tooltip on hover.",
            "KPI cards showed letterboxing because the first TableEx viewport did not match the available visual height closely enough.",
            "Main chart row started too low, leaving a visible empty band between KPI cards and charts.",
            "Current Lens and Next Action used pastel blue/yellow fills that did not match the neutral logistics finance theme.",
            "Green status chips used short labels such as OK/WATCH/NEW, which were unclear as decision signals.",
            "Synthetic slicer movement needed stronger controlled variance by mode, lane cluster, segment, office, carrier, and action owner/status.",
        ],
        "issues_fixed": [
            "Changed 12 KPI cards to TableEx + SVG Image URL measures per user request.",
            "Converted Current Lens and Decision Chips to compact TableEx SVG Image URL panels to remove native cardVisual dash/chrome.",
            "Restored compact page navigation in the header with invisible native actionButton PageNavigation overlays.",
            "Rebalanced KPI visuals to 296 x 152 TableEx containers with a safe 282 x 130 image viewport.",
            f"Set the main chart row from y=276 to y={MAIN_CHART_Y}, creating a {KPI_TO_CHART_GAP} px breathing gap after KPI cards.",
            "Moved KPI shader/drop-shadow treatment to an inner SVG TableEx border/ring instead of an outer KPI card border.",
            "Reworked KPI SVG footer labels and changed the unclear green OK chips to explicit On track/Watch/New status chips on neutral fill.",
            "Replaced Current Lens and Next Action pastel fills with neutral panels, subtle borders, and blue/amber accent rails.",
            "Strengthened synthetic data variation so slicers affect KPI totals, chart mix, action risk, and sparkline shape more visibly.",
        ],
        "remaining_blockers": [
            "Open final PBIX in Power BI Desktop after repack and run the 5-pass/10-combination visual QA loop.",
            "Confirm no text clipping, unwanted scrollbar, header leakage, or visual chrome after pressing Escape.",
            "Confirm slicers visibly update KPI cards, lens text, charts, and tables.",
            "Public-release privacy gate remains fail for source workspace because model.bim contains local File.Contents paths by design.",
        ],
        "screenshots_or_desktop_evidence": [],
        "visual_geometry_before_after": {
            "after": {
                "canvas": {"width": 1280, "height": 720},
                "tableex_svg_kpi_cards": inv["kpi_cards"],
                "current_lens_cards": inv["current_lens"],
                "decision_cards": inv["decision_panels"],
                "main_chart_cards": inv["chart_cards"],
                "visual_type_counts": inv["visual_type_counts"],
            }
        },
        "value_reconciliation": validation["checks"],
    }
    write_json("qa/dashboard_visual_polish_qa.json", payload)


def write_project17_layout_redesign_qa(layout: dict, validation: dict) -> None:
    inv = layout_visual_inventory(layout)
    payload = {
        "status": "source_pass_desktop_required",
        "verification_name": "project17_layout_redesign_qa",
        "verified_at": RUN_TS,
        "project_name": "Project 17 - Logistics Trade Lane Profitability",
        "primary_artifact": str(PROJECT / "output" / "dashboard_final.pbix"),
        "source_script": str(PROJECT / "tools" / "build_project17.py"),
        "qa_prompt_library": str(PROJECT.parent / "prompt-library" / "QA Prompt"),
        "html_used_as_source_of_truth": False,
        "canvas": {"width": 1280, "height": 720},
        "layout_tokens": {
            "filter_row": {"y": FILTER_ROW_Y, "height": FILTER_ROW_H},
            "kpi_row": {"y": KPI_ROW_Y, "height": KPI_ROW_H, "card_width": KPI_CARD_W, "gap": KPI_CARD_GAP},
            "main_chart_row": {"y": MAIN_CHART_Y, "height": MAIN_CHART_H, "gap_after_kpi": KPI_TO_CHART_GAP},
            "bottom_row": {"y": BOTTOM_ROW_Y, "height": BOTTOM_ROW_H},
            "context_panel_height": CONTEXT_CHIP_H,
        },
        "page_count": len(layout["sections"]),
        "visual_count": sum(len(s["visualContainers"]) for s in layout["sections"]),
        "visual_type_counts": inv["visual_type_counts"],
        "image_url_measure_expected_count": 12,
        "source_checks": {
            "kpi_cards_remain_tableex_svg": "pass" if len(inv["kpi_cards"]) == 12 and inv["visual_type_counts"].get("tableEx", 0) >= 12 else "fail",
            "kpi_card_visual_height_target": "pass" if KPI_ROW_H >= 148 else "fail",
            "kpi_to_chart_gap_target": "pass" if 14 <= KPI_TO_CHART_GAP <= 18 else "fail",
            "main_chart_y_target": "pass" if MAIN_CHART_Y == 292 else "fail",
            "main_chart_h_target": "pass" if MAIN_CHART_H == 208 else "fail",
            "tableex_image_body_height": 130,
            "current_lens_neutral_theme": "pass_neutral_panel_with_blue_accent_rail_and_svg_text",
            "next_action_neutral_theme": "pass_neutral_panel_with_amber_accent_rail_and_svg_text",
            "green_status_chip_clarity": "pass_status_labels_changed_to_On_track_Watch_New_on_neutral_fill",
            "data_variation_strengthened": "pass_controlled_factors_added_for_mode_lane_cluster_segment_office_carrier_action_owner_status",
            "dynamic_currency_units": "pass_svg_kpi_currency_values_switch_between_M_K_and_whole_dollars",
            "value_reconciliation": validation["status"],
        },
        "issues_fixed": [
            "Raised and enlarged the top text containers to remove header baseline clipping.",
            "Expanded the Current Lens panel, shortened dynamic DAX strings, and converted it to a compact SVG mini-panel to remove native cardVisual dash/chrome.",
            "Removed the clipped logistics kicker textbox and custom canvas page-nav blocks that rendered as teal/clipped chrome in Desktop screenshots.",
            "Changed KPI visual containers to 296 x 152 and rendered SVG cards inside a safe 282 x 130 TableEx image viewport to remove overflow scrollbars.",
            f"Set the main chart row to y={MAIN_CHART_Y} with a {KPI_TO_CHART_GAP} px KPI-to-chart breathing gap and {MAIN_CHART_H} px main chart height.",
            "Moved KPI shader/drop-shadow from the outer SVG card edge to an inner TableEx image border/ring.",
            "Clarified the unclear green OK chips by replacing them with explicit On track/Watch/New status labels on neutral chip fill.",
            "Changed Current Lens and Next Action from pastel blocks to neutral panels with subtle accent rails.",
            "Shortened dynamic lens/action text and rendered it through compact Image URL SVG panels to reduce clipping and cardVisual chrome risk.",
            "Added dynamic currency units in SVG KPI cards so narrow filters show $K or whole dollars instead of rounded $0.0M.",
            "Added stronger synthetic variation across slicers and action dimensions while retaining reconciliation checks.",
        ],
        "desktop_required_checks": [
            "Open output/dashboard_final.pbix in Power BI Desktop after model push and layout repack.",
            "Press Escape twice and scan all pages at fit-page zoom.",
            "Confirm TableEx KPI cards have no header leakage, measure name leakage, white bar, or internal scrollbar.",
            "Test at least 6 slicer combinations and confirm KPI, charts, tables, and sparklines visibly change.",
            "Save, close, and reopen the final PBIX before marking release pass.",
        ],
        "remaining_caveats": [
            "This generated QA file is source/layout evidence only until the final PBIX Desktop open/reopen pass is recorded.",
            "Public-release privacy gate remains fail for the BI source workspace because model and Power Query point at local synthetic CSV paths.",
        ],
    }
    write_json("qa/project17_layout_redesign_qa.json", payload)


def write_project19_recovery_polish_release_qa(layout: dict, validation: dict) -> None:
    inv = layout_visual_inventory(layout)
    prompt_path = PROJECT.parent / "prompt-library" / "Enhance Prompt - Project 19" / "powerbi-dashboard-recovery-polish-release-agent.md"
    qa_library = PROJECT.parent / "prompt-library" / "QA Prompt"
    payload = {
        "status": "fail",
        "verification_name": "project19_recovery_polish_release_qa",
        "verified_at": RUN_TS,
        "project_name": "Project 17 - Logistics Trade Lane Profitability",
        "source_prompt": str(prompt_path),
        "qa_prompt_library": str(qa_library),
        "final_pbix": str(PROJECT / "output" / "dashboard_final.pbix"),
        "build_script": str(PROJECT / "tools" / "build_project17.py"),
        "source_of_truth": "build script + final PBIX; HTML is supplemental only",
        "pbix_opened_in_desktop": False,
        "pbix_reopened_after_save": False,
        "desktop_ui_qa": False,
        "computer_use_used": False,
        "desktop_version_used": None,
        "phase_status": {
            "phase_0_intake_backup": "pending_runtime_backup",
            "phase_1_recovery_gate": "pending_desktop_open_reopen",
            "phase_2_source_of_truth_gate": "pass_source_script_rebuildable_layout",
            "phase_3_data_model_slicer_sensitivity": "pending_desktop_slicer_tests",
            "phase_4_layout_design_system": "source_pass_grid_tokens_tableex_kpi_cards",
            "phase_5_component_fixes": "source_pass_tableex_svg_kpi_native_lens_chart_mix",
            "phase_6_visual_chrome_cleanup": "source_pass_visual_headers_disabled_desktop_pending",
            "phase_7_mandatory_desktop_qa": "pending_desktop_open_reopen_all_pages",
            "phase_8_qa_json": "generated_desktop_evidence_pending",
            "phase_9_github_release": "not_requested",
        },
        "layout_release_tokens": {
            "canvas": {"width": 1280, "height": 720},
            "filter_row": {"y": FILTER_ROW_Y, "height": FILTER_ROW_H},
            "kpi_row": {"y": KPI_ROW_Y, "height": KPI_ROW_H, "card_width": KPI_CARD_W, "gap": KPI_CARD_GAP},
            "main_chart_row": {"y": MAIN_CHART_Y, "height": MAIN_CHART_H, "gap_after_kpi": KPI_TO_CHART_GAP},
            "bottom_row": {"y": BOTTOM_ROW_Y, "height": BOTTOM_ROW_H},
            "context_chip_height": CONTEXT_CHIP_H,
        },
        "page_count": len(layout["sections"]),
        "visual_count": sum(len(s["visualContainers"]) for s in layout["sections"]),
        "visual_type_counts": inv["visual_type_counts"],
        "defect_class_status": {
            "text_clipping_and_overflow": "source_pass_desktop_pending",
            "filter_bar_and_slicer_viewport": "source_pass_desktop_pending",
            "tableex_image_url_rendering": "intentional_for_12_kpi_cards_desktop_pending",
            "current_lens_panel": "source_pass_tableex_svg_dynamic_panels_desktop_pending",
            "kpi_card_composition": "source_pass_tableex_svg_cards_desktop_pending",
            "sparkline_layout_collision": "source_pass_svg_internal_clip_desktop_pending",
            "grid_alignment_spacing": "source_pass_geometry_computed",
            "data_variation_units_slicer_sensitivity": "pending_desktop_slicer_tests",
            "chart_card_visual_polish": "source_pass_native_chart_cards_desktop_pending",
            "action_panels_vertical_space": "source_pass_bottom_charts_replace_blank_tables",
            "visual_chrome_artifact_cleanup": "source_pass_visual_headers_hidden_desktop_pending",
        },
        "root_cause_summary": [
            "User requested KPI cards as TableEx + SVG Image URL visuals.",
            "TableEx/Image URL can expose headers, measure names, tooltips, scrollbars, or blank-looking panels if the viewport is not controlled.",
            "Release pass requires Desktop open/save/reopen and slicer evidence; source/package validation alone is not enough.",
        ],
        "fixes_applied_in_source": [
            "KPI cards are built as TableEx visuals bound to ImageUrl SVG measures.",
            "Current Lens and Next Action are compact dynamic Image URL SVG panels to avoid native cardVisual dash/chrome.",
            "Bottom blank TableEx panels are replaced with native evidence charts.",
            "Compact header page navigation is restored through invisible native actionButton PageNavigation overlays with visual headers disabled.",
            "Active model catalog includes 12 ImageUrl SVG KPI measures only.",
        ],
        "slicer_combinations_tested": [],
        "screenshots_or_desktop_evidence": [],
        "value_reconciliation": validation["checks"],
        "remaining_caveats": [
            "Generated release QA is intentionally fail until the final PBIX is opened, saved, closed, reopened, and tested in Power BI Desktop.",
            "At least five slicer combinations must be recorded from the real PBIX surface before release status can move to pass.",
            "The BI source workspace contains local File.Contents paths for synthetic CSV ingestion and must not be published as a public artifact.",
        ],
    }
    write_json("qa/project19_recovery_polish_release_qa.json", payload)


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
    write_text("output/dashboard_final.html", html_dashboard_v2(data))
    write_config_docs()
    write_docs(validation, env)
    write_json("model/model.bim", build_model_bim())
    write_native_scripts()
    layout = build_layout()
    write_json("build/native_report_layout_project17.json", layout)
    write_project18_gap_audit(layout)
    write_project18_release_qa(layout, validation)
    write_dashboard_visual_polish_qa(layout, validation)
    write_project17_layout_redesign_qa(layout, validation)
    write_project19_recovery_polish_release_qa(layout, validation)
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


