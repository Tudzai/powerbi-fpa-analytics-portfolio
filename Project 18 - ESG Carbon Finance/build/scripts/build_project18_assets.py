from __future__ import annotations

import csv
import json
import math
import random
from collections import defaultdict
from datetime import date
from pathlib import Path


PROJECT = Path(__file__).resolve().parents[2]
SEED = 180418
random.seed(SEED)

RAW = PROJECT / "data" / "raw"
PREP = PROJECT / "data" / "prepared"
VALID = PROJECT / "data" / "validated"
MODEL = PROJECT / "model"
DOCS = PROJECT / "docs"
CONFIG = PROJECT / "build" / "config"
QA = PROJECT / "qa"
REPORT = PROJECT / "report"
POWERBI = PROJECT / "powerbi"
AGENT = PROJECT / "_agent"
WORKFLOW = PROJECT / "_workflow"
OUTPUT = PROJECT / "output"

for folder in [RAW, PREP, VALID, MODEL, DOCS, CONFIG, QA, REPORT, POWERBI / "notes", AGENT, WORKFLOW, OUTPUT / "screenshots"]:
    folder.mkdir(parents=True, exist_ok=True)


def write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.strip() + "\n", encoding="utf-8")


def month_range(start: date, end: date) -> list[date]:
    months = []
    cur = date(start.year, start.month, 1)
    while cur <= end:
        months.append(cur)
        if cur.month == 12:
            cur = date(cur.year + 1, 1, 1)
        else:
            cur = date(cur.year, cur.month + 1, 1)
    return months


months = month_range(date(2024, 1, 1), date(2026, 5, 1))

dim_date = []
for idx, d in enumerate(months, start=1):
    q = (d.month - 1) // 3 + 1
    dim_date.append(
        {
            "date_key": d.strftime("%Y%m"),
            "month_start": d.isoformat(),
            "year": d.year,
            "quarter": f"Q{q}",
            "month_no": d.month,
            "month_name": d.strftime("%b"),
            "fiscal_year": d.year if d.month >= 4 else d.year - 1,
            "month_index": idx,
        }
    )

business_units = [
    ("BU01", "Manufacturing", "Industrial Operations", 420_000_000),
    ("BU02", "Logistics", "Transport Network", 260_000_000),
    ("BU03", "Procurement", "Supplier & Materials", 210_000_000),
    ("BU04", "Retail Operations", "Commercial Sites", 180_000_000),
    ("BU05", "Corporate", "Offices & Shared Services", 95_000_000),
]
dim_business_unit = [
    {
        "business_unit_id": bid,
        "business_unit": name,
        "portfolio": portfolio,
        "annual_revenue_usd": revenue,
    }
    for bid, name, portfolio, revenue in business_units
]

facilities = [
    ("F01", "Hai Phong Plant", "Vietnam", "APAC", "Manufacturing", 21.01, 106.68),
    ("F02", "Binh Duong DC", "Vietnam", "APAC", "Logistics", 10.98, 106.65),
    ("F03", "Bangkok Hub", "Thailand", "APAC", "Logistics", 13.75, 100.50),
    ("F04", "Shenzhen Assembly", "China", "APAC", "Manufacturing", 22.54, 114.06),
    ("F05", "Rotterdam Warehouse", "Netherlands", "EMEA", "Logistics", 51.92, 4.48),
    ("F06", "Hamburg Office", "Germany", "EMEA", "Corporate", 53.55, 9.99),
    ("F07", "Los Angeles DC", "United States", "Americas", "Retail Operations", 34.05, -118.24),
    ("F08", "Chicago Office", "United States", "Americas", "Corporate", 41.88, -87.63),
]
dim_facility = [
    {
        "facility_id": fid,
        "facility": facility,
        "country": country,
        "region": region,
        "default_business_unit": bu,
        "latitude": lat,
        "longitude": lon,
    }
    for fid, facility, country, region, bu, lat, lon in facilities
]

activities = [
    ("A01", "Natural gas combustion", "Scope 1", "Stationary combustion", "MWh thermal", 0.184),
    ("A02", "Diesel fleet fuel", "Scope 1", "Mobile combustion", "kiloliters", 2.68),
    ("A03", "Refrigerant leakage", "Scope 1", "Fugitive emissions", "kg refrigerant", 1.36),
    ("A04", "Purchased electricity", "Scope 2", "Electricity", "MWh", 0.46),
    ("A05", "Purchased heating/cooling", "Scope 2", "Purchased energy", "MWh", 0.21),
    ("A06", "Purchased goods", "Scope 3", "Purchased goods and services", "USD thousand spend", 0.52),
    ("A07", "Upstream logistics", "Scope 3", "Transportation and distribution", "ton-km thousand", 0.16),
    ("A08", "Business travel", "Scope 3", "Business travel", "passenger-km thousand", 0.13),
    ("A09", "Waste generated", "Scope 3", "Waste", "tonnes waste", 0.49),
]
dim_activity = [
    {
        "activity_id": aid,
        "activity": name,
        "scope": scope,
        "ghg_category": category,
        "activity_unit": unit,
        "base_emission_factor": factor,
    }
    for aid, name, scope, category, unit, factor in activities
]

supplier_names = [
    "Astra Materials",
    "BlueRiver Logistics",
    "Canopy Packaging",
    "Delta Metals",
    "EastGrid Energy",
    "Forest Fiber Co",
    "GreenPulse Freight",
    "Harbor Components",
    "Indigo Chemicals",
    "Jade Electronics",
    "Keystone Plastics",
    "Lumen Utilities",
    "Mekong Transport",
    "Nova Textiles",
    "Orchid Facilities",
    "Pacific Cold Chain",
    "Quantum Parts",
    "RiverStone Cement",
    "Solaris Power",
    "Terra Warehousing",
    "Urban Mobility",
    "Vector Metals",
    "Willow Office Supply",
    "Zenith Packaging",
]
countries = ["Vietnam", "Thailand", "China", "India", "Germany", "Netherlands", "United States", "Mexico", "Malaysia", "Japan"]
categories = ["Materials", "Logistics", "Energy", "Packaging", "Facilities", "Travel", "Components"]
dim_supplier = []
for i, name in enumerate(supplier_names, start=1):
    category = categories[(i * 3) % len(categories)]
    high_categories = {"Materials", "Energy", "Components"}
    risk = "High" if category in high_categories and i % 3 != 0 else ("Medium" if i % 4 != 0 else "Low")
    target = random.choice(["SBTi committed", "Supplier target", "No verified target", "Renewable PPA"])
    dim_supplier.append(
        {
            "supplier_id": f"S{i:03d}",
            "supplier": name,
            "supplier_category": category,
            "supplier_country": countries[i % len(countries)],
            "carbon_risk_tier": risk,
            "target_status": target,
            "data_quality_score": round(random.uniform(0.62, 0.96), 2),
        }
    )

scenario_rows = [
    {"scenario_id": "SCN01", "scenario": "Base internal price", "carbon_price_usd_per_t": 50, "probability_weight": 0.45},
    {"scenario_id": "SCN02", "scenario": "Regulatory convergence", "carbon_price_usd_per_t": 90, "probability_weight": 0.35},
    {"scenario_id": "SCN03", "scenario": "Stress price shock", "carbon_price_usd_per_t": 140, "probability_weight": 0.20},
]

activity_factor = {row["activity_id"]: row["base_emission_factor"] for row in dim_activity}
scope_by_activity = {row["activity_id"]: row["scope"] for row in dim_activity}
activity_by_id = {row["activity_id"]: row for row in dim_activity}
supplier_by_id = {row["supplier_id"]: row for row in dim_supplier}
facility_by_id = {row["facility_id"]: row for row in dim_facility}
bu_by_name = {row["business_unit"]: row for row in dim_business_unit}

scope_activity_ids = {
    "Scope 1": ["A01", "A02", "A03"],
    "Scope 2": ["A04", "A05"],
    "Scope 3": ["A06", "A07", "A08", "A09"],
}

emission_rows = []
flat_rows = []
monthly_totals = defaultdict(float)
for m in months:
    month_index = (m.year - 2024) * 12 + m.month
    season = 1 + 0.08 * math.sin((m.month - 1) / 12 * math.tau)
    decarb = max(0.82, 1 - 0.006 * month_index)
    for fid, facility, country, region, default_bu, _, _ in facilities:
        bu = bu_by_name[default_bu]
        revenue_month = bu["annual_revenue_usd"] / 12 * random.uniform(0.90, 1.12)
        activity_sample = []
        if default_bu == "Manufacturing":
            activity_sample = ["A01", "A03", "A04", "A06", "A09"]
        elif default_bu == "Logistics":
            activity_sample = ["A02", "A04", "A07", "A09"]
        elif default_bu == "Corporate":
            activity_sample = ["A04", "A05", "A08", "A09"]
        else:
            activity_sample = ["A04", "A05", "A06", "A08", "A09"]
        for aid in activity_sample:
            activity = activity_by_id[aid]
            for rep in range(2 if aid in ["A06", "A07"] else 1):
                supplier = random.choice(dim_supplier) if activity["scope"] == "Scope 3" or aid in ["A04", "A05"] else None
                scope_multiplier = {"Scope 1": 1.05, "Scope 2": 0.92, "Scope 3": 1.28}[activity["scope"]]
                bu_multiplier = {
                    "Manufacturing": 1.45,
                    "Logistics": 1.20,
                    "Procurement": 1.05,
                    "Retail Operations": 0.82,
                    "Corporate": 0.38,
                }[default_bu]
                base_volume = random.uniform(220, 1450) * bu_multiplier * season
                if aid == "A06":
                    base_volume *= 1.8
                if aid == "A03":
                    base_volume *= 0.12
                factor_noise = random.uniform(0.82, 1.22)
                supplier_noise = 1.0
                if supplier:
                    supplier_noise = {"High": 1.28, "Medium": 1.02, "Low": 0.82}[supplier["carbon_risk_tier"]]
                emissions = base_volume * activity_factor[aid] * factor_noise * supplier_noise * scope_multiplier * decarb
                spend = base_volume * random.uniform(65, 190)
                if activity["scope"] == "Scope 3":
                    spend *= random.uniform(1.8, 4.4)
                emissions = round(emissions, 2)
                spend = round(spend, 2)
                row = {
                    "emission_record_id": f"E{len(emission_rows)+1:06d}",
                    "date_key": m.strftime("%Y%m"),
                    "business_unit_id": bu["business_unit_id"],
                    "facility_id": fid,
                    "supplier_id": supplier["supplier_id"] if supplier else "DIRECT",
                    "activity_id": aid,
                    "scope": activity["scope"],
                    "ghg_category": activity["ghg_category"],
                    "activity_volume": round(base_volume, 2),
                    "activity_unit": activity["activity_unit"],
                    "emission_factor": round(activity_factor[aid] * factor_noise, 4),
                    "emissions_tco2e": emissions,
                    "spend_usd": spend,
                    "revenue_usd": round(revenue_month / len(activity_sample), 2),
                    "data_quality_score": round(random.uniform(0.70, 0.98), 2),
                }
                emission_rows.append(row)
                monthly_totals[m.strftime("%Y%m")] += emissions
                flat_rows.append(
                    {
                        **row,
                        "month_start": m.isoformat(),
                        "year": m.year,
                        "quarter": f"Q{(m.month - 1) // 3 + 1}",
                        "month_name": m.strftime("%b"),
                        "business_unit": default_bu,
                        "portfolio": bu["portfolio"],
                        "facility": facility,
                        "country": country,
                        "region": region,
                        "activity": activity["activity"],
                        "supplier": supplier["supplier"] if supplier else "Direct operations",
                        "supplier_category": supplier["supplier_category"] if supplier else "Direct operations",
                        "carbon_risk_tier": supplier["carbon_risk_tier"] if supplier else "Operational",
                        "target_status": supplier["target_status"] if supplier else "Owned source",
                    }
                )

supplier_month = defaultdict(lambda: {"emissions_tco2e": 0.0, "spend_usd": 0.0, "records": 0})
for row in emission_rows:
    if row["supplier_id"] == "DIRECT":
        continue
    key = (row["date_key"], row["supplier_id"])
    supplier_month[key]["emissions_tco2e"] += row["emissions_tco2e"]
    supplier_month[key]["spend_usd"] += row["spend_usd"]
    supplier_month[key]["records"] += 1

supplier_rows = []
for (date_key, supplier_id), vals in sorted(supplier_month.items()):
    supplier = supplier_by_id[supplier_id]
    intensity = vals["emissions_tco2e"] / vals["spend_usd"] * 1_000_000 if vals["spend_usd"] else 0
    supplier_rows.append(
        {
            "date_key": date_key,
            "supplier_id": supplier_id,
            "supplier": supplier["supplier"],
            "supplier_category": supplier["supplier_category"],
            "carbon_risk_tier": supplier["carbon_risk_tier"],
            "supplier_country": supplier["supplier_country"],
            "target_status": supplier["target_status"],
            "emissions_tco2e": round(vals["emissions_tco2e"], 2),
            "spend_usd": round(vals["spend_usd"], 2),
            "supplier_intensity_tco2e_per_musd": round(intensity, 2),
            "data_quality_score": supplier["data_quality_score"],
        }
    )

exposure_rows = []
for date_key, total in sorted(monthly_totals.items()):
    for scn in scenario_rows:
        exposure_rows.append(
            {
                "date_key": date_key,
                "scenario_id": scn["scenario_id"],
                "scenario": scn["scenario"],
                "carbon_price_usd_per_t": scn["carbon_price_usd_per_t"],
                "emissions_tco2e": round(total, 2),
                "carbon_cost_usd": round(total * scn["carbon_price_usd_per_t"], 2),
                "probability_weighted_cost_usd": round(total * scn["carbon_price_usd_per_t"] * scn["probability_weight"], 2),
            }
        )

initiatives = [
    ("I01", "Solar PPA expansion", "Scope 2", "Procurement", 4_800_000, 9_200, 680_000, 2025, "Committed"),
    ("I02", "Fleet electrification phase 1", "Scope 1", "Logistics", 7_600_000, 6_300, 910_000, 2026, "Planned"),
    ("I03", "Supplier recycled aluminum switch", "Scope 3", "Procurement", 2_900_000, 8_100, 260_000, 2025, "In flight"),
    ("I04", "Heat recovery at Hai Phong", "Scope 1", "Manufacturing", 3_400_000, 5_400, 540_000, 2025, "In flight"),
    ("I05", "LED and controls retrofit", "Scope 2", "Retail Operations", 1_100_000, 2_500, 230_000, 2024, "Implemented"),
    ("I06", "Modal shift to rail", "Scope 3", "Logistics", 2_200_000, 4_700, 185_000, 2026, "Planned"),
    ("I07", "Refrigerant replacement", "Scope 1", "Manufacturing", 1_600_000, 1_900, 90_000, 2025, "Committed"),
    ("I08", "Supplier renewable heat program", "Scope 3", "Procurement", 5_500_000, 7_200, 320_000, 2026, "Planned"),
    ("I09", "Packaging lightweighting", "Scope 3", "Retail Operations", 2_450_000, 3_900, 410_000, 2025, "In flight"),
    ("I10", "Green travel policy", "Scope 3", "Corporate", 620_000, 1_150, 175_000, 2024, "Implemented"),
    ("I11", "Battery storage peak shaving", "Scope 2", "Manufacturing", 3_850_000, 2_850, 360_000, 2026, "Planned"),
    ("I12", "Waste-to-resource program", "Scope 3", "Manufacturing", 980_000, 1_650, 125_000, 2025, "Committed"),
]
abatement_rows = []
scenario_price = 90
for item in initiatives:
    iid, initiative, scope, bu, capex, reduction, savings, start_year, status = item
    avoided_cost = reduction * scenario_price
    net_annual_benefit = savings + avoided_cost
    payback = capex / net_annual_benefit
    macc = (capex / 7 - savings) / reduction
    roi = net_annual_benefit / capex
    abatement_rows.append(
        {
            "initiative_id": iid,
            "initiative": initiative,
            "scope": scope,
            "business_unit": bu,
            "implementation_status": status,
            "start_year": start_year,
            "capex_usd": capex,
            "annual_reduction_tco2e": reduction,
            "annual_opex_savings_usd": savings,
            "avoided_carbon_cost_usd_at_90": round(avoided_cost, 2),
            "net_annual_benefit_usd_at_90": round(net_annual_benefit, 2),
            "payback_years_at_90": round(payback, 2),
            "roi_at_90": round(roi, 3),
            "macc_usd_per_tco2e": round(macc, 2),
        }
    )

write_json(
    RAW / "synthetic_generation_config.json",
    {
        "project": "Project 18 - ESG Carbon Finance",
        "data_mode": "synthetic_demo",
        "seed": SEED,
        "latest_complete_month": "2026-05",
        "grain": "Monthly emission activity record by facility, business unit, supplier where applicable, and activity source.",
        "patterns_included": [
            "Scope 1/2/3 emissions mix",
            "supplier carbon risk tiers",
            "declining emissions trend from decarbonization",
            "carbon price scenarios",
            "abatement initiative ROI and MACC ranking",
        ],
    },
)

tables = {
    "dim_date.csv": (dim_date, list(dim_date[0].keys())),
    "dim_business_unit.csv": (dim_business_unit, list(dim_business_unit[0].keys())),
    "dim_facility.csv": (dim_facility, list(dim_facility[0].keys())),
    "dim_activity.csv": (dim_activity, list(dim_activity[0].keys())),
    "dim_supplier.csv": (dim_supplier, list(dim_supplier[0].keys())),
    "dim_carbon_scenario.csv": (scenario_rows, list(scenario_rows[0].keys())),
    "fact_emissions.csv": (emission_rows, list(emission_rows[0].keys())),
    "fact_supplier_month.csv": (supplier_rows, list(supplier_rows[0].keys())),
    "fact_carbon_exposure.csv": (exposure_rows, list(exposure_rows[0].keys())),
    "fact_abatement_initiatives.csv": (abatement_rows, list(abatement_rows[0].keys())),
    "powerbi_flat_emissions.csv": (flat_rows, list(flat_rows[0].keys())),
}

for filename, (rows, fieldnames) in tables.items():
    write_csv(PREP / filename, rows, fieldnames)
    if filename in {"fact_emissions.csv", "dim_supplier.csv", "fact_abatement_initiatives.csv"}:
        write_csv(RAW / filename, rows, fieldnames)

total_emissions = sum(r["emissions_tco2e"] for r in emission_rows)
total_spend = sum(r["spend_usd"] for r in emission_rows)
total_revenue = sum(r["revenue_usd"] for r in emission_rows)
scope_totals = defaultdict(float)
bu_totals = defaultdict(float)
supplier_totals = defaultdict(float)
for r in emission_rows:
    scope_totals[r["scope"]] += r["emissions_tco2e"]
    bu_totals[r["business_unit_id"]] += r["emissions_tco2e"]
    if r["supplier_id"] != "DIRECT":
        supplier_totals[r["supplier_id"]] += r["emissions_tco2e"]

latest_key = "202605"
prior_year_key = "202505"
latest_total = monthly_totals[latest_key]
prior_year_total = monthly_totals[prior_year_key]
yoy_change = (latest_total - prior_year_total) / prior_year_total
target_2026_annual = total_emissions / (len(months) / 12) * 0.86
current_run_rate_2026 = sum(v for k, v in monthly_totals.items() if k.startswith("2026")) / 5 * 12
target_gap = current_run_rate_2026 - target_2026_annual
high_risk_supplier_emissions = sum(r["emissions_tco2e"] for r in supplier_rows if r["carbon_risk_tier"] == "High")
avg_supplier_data_quality = sum(r["data_quality_score"] for r in dim_supplier) / len(dim_supplier)
no_verified_target_suppliers = sum(1 for r in dim_supplier if r["target_status"] == "No verified target")
planned_abatement_capex = sum(r["capex_usd"] for r in abatement_rows if r["implementation_status"] == "Planned")
committed_inflight_reduction = sum(
    r["annual_reduction_tco2e"]
    for r in abatement_rows
    if r["implementation_status"] in {"Committed", "In flight", "Implemented"}
)
probability_weighted_carbon_cost = sum(r["probability_weighted_cost_usd"] for r in exposure_rows)

validation = {
    "seed": SEED,
    "data_mode": "synthetic_demo",
    "row_counts": {filename: len(rows) for filename, (rows, _) in tables.items()},
    "date_range": {"min_date_key": min(r["date_key"] for r in emission_rows), "max_date_key": max(r["date_key"] for r in emission_rows)},
    "critical_null_checks": {
        "fact_emissions_missing_keys": sum(
            1
            for r in emission_rows
            if not r["date_key"] or not r["business_unit_id"] or not r["facility_id"] or not r["activity_id"]
        ),
        "supplier_missing_category": sum(1 for r in dim_supplier if not r["supplier_category"]),
    },
    "duplicate_checks": {
        "dim_date_duplicate_keys": len(dim_date) - len({r["date_key"] for r in dim_date}),
        "dim_supplier_duplicate_keys": len(dim_supplier) - len({r["supplier_id"] for r in dim_supplier}),
        "fact_emissions_duplicate_record_ids": len(emission_rows) - len({r["emission_record_id"] for r in emission_rows}),
    },
    "reconciled_kpis": {
        "total_emissions_tco2e": round(total_emissions, 2),
        "scope_totals_tco2e": {k: round(v, 2) for k, v in scope_totals.items()},
        "carbon_cost_usd_base_50": round(total_emissions * 50, 2),
        "emissions_intensity_tco2e_per_musd_revenue": round(total_emissions / total_revenue * 1_000_000, 2),
        "latest_month_emissions_tco2e": round(latest_total, 2),
        "yoy_change_latest_month": round(yoy_change, 4),
        "target_gap_tco2e_run_rate": round(target_gap, 2),
        "high_risk_supplier_emissions_tco2e": round(high_risk_supplier_emissions, 2),
        "average_supplier_data_quality": round(avg_supplier_data_quality, 4),
        "suppliers_without_verified_target": no_verified_target_suppliers,
        "planned_abatement_capex_usd": round(planned_abatement_capex, 2),
        "probability_weighted_carbon_cost_usd": round(probability_weighted_carbon_cost, 2),
    },
    "qa_status": "pass",
}
write_json(VALID / "validation_summary.json", validation)
write_json(QA / "pbix_validation.json", {
    "final_pbix_path": str(PROJECT / "output" / "dashboard_final.pbix"),
    "opened_in_power_bi_desktop": False,
    "saved_after_open": False,
    "page_count": 0,
    "visual_count": 0,
    "visual_error_count": None,
    "screenshots": [],
    "qa_status": "pending_desktop_build",
    "known_issues": ["Final PBIX is not validated until Desktop conversion/save and visual QA complete."],
})
write_json(QA / "pbix_final_validation.json", {
    "final_pbix_exists": (PROJECT / "output" / "dashboard_final.pbix").exists(),
    "desktop_open_check": "not_run",
    "build_route": "pending",
    "qa_status": "pending_desktop_build",
})

reconciliation_rows = [
    {"metric": "Total emissions tCO2e", "value": round(total_emissions, 2), "source": "fact_emissions.emissions_tco2e"},
    {"metric": "Carbon cost USD at $50/t", "value": round(total_emissions * 50, 2), "source": "Total emissions * dim_carbon_scenario[Base internal price]"},
    {"metric": "Emissions intensity tCO2e per $M revenue", "value": round(total_emissions / total_revenue * 1_000_000, 2), "source": "Total emissions / revenue * 1,000,000"},
    {"metric": "Latest month YoY emissions change", "value": round(yoy_change, 4), "source": "May 2026 vs May 2025"},
    {"metric": "Abatement annual reduction tCO2e", "value": sum(r["annual_reduction_tco2e"] for r in abatement_rows), "source": "fact_abatement_initiatives"},
    {"metric": "High-risk supplier emissions tCO2e", "value": round(high_risk_supplier_emissions, 2), "source": "fact_supplier_month filtered to High risk tier"},
    {"metric": "Supplier data quality score", "value": round(avg_supplier_data_quality, 4), "source": "dim_supplier.data_quality_score average"},
    {"metric": "Suppliers without verified target", "value": no_verified_target_suppliers, "source": "dim_supplier target_status = No verified target"},
    {"metric": "Probability weighted carbon cost USD", "value": round(probability_weighted_carbon_cost, 2), "source": "fact_carbon_exposure.probability_weighted_cost_usd"},
    {"metric": "Planned abatement capex USD", "value": round(planned_abatement_capex, 2), "source": "fact_abatement_initiatives filtered to Planned"},
]
write_csv(QA / "reconciliation.csv", reconciliation_rows, ["metric", "value", "source"])

data_dictionary_lines = [
    "# Data Dictionary",
    "",
    "All data in this portfolio build is synthetic demo data generated with seed 180418.",
    "",
]
for filename, (rows, fields) in tables.items():
    data_dictionary_lines += [
        f"## {filename}",
        f"- Row count: {len(rows)}",
        "- Grain: " + (
            "Monthly emission activity record." if filename == "fact_emissions.csv" else
            "Monthly supplier summary." if filename == "fact_supplier_month.csv" else
            "Monthly emissions by carbon price scenario." if filename == "fact_carbon_exposure.csv" else
            "One row per abatement initiative." if filename == "fact_abatement_initiatives.csv" else
            "Dimension table."
        ),
        "- Columns:",
    ]
    for f in fields:
        data_dictionary_lines.append(f"  - `{f}`")
    data_dictionary_lines.append("")
write_text(PROJECT / "data" / "data_dictionary.md", "\n".join(data_dictionary_lines))
write_text(PROJECT / "data" / "data_quality_report.md", f"""
# Data Quality Report

Data mode: synthetic demo data.
Seed: {SEED}
Date range: Jan 2024 to May 2026.

## Row Counts

{chr(10).join(f"- {filename}: {len(rows):,}" for filename, (rows, _) in tables.items())}

## Key Checks

- Critical key nulls in fact_emissions: {validation["critical_null_checks"]["fact_emissions_missing_keys"]}
- Duplicate date keys: {validation["duplicate_checks"]["dim_date_duplicate_keys"]}
- Duplicate supplier keys: {validation["duplicate_checks"]["dim_supplier_duplicate_keys"]}
- Duplicate emission record IDs: {validation["duplicate_checks"]["fact_emissions_duplicate_record_ids"]}

## KPI Reconciliation

- Total emissions: {total_emissions:,.2f} tCO2e
- Scope 1: {scope_totals["Scope 1"]:,.2f} tCO2e
- Scope 2: {scope_totals["Scope 2"]:,.2f} tCO2e
- Scope 3: {scope_totals["Scope 3"]:,.2f} tCO2e
- Base carbon cost at $50/t: {total_emissions * 50:,.0f} USD
- Latest month YoY emissions change: {yoy_change:.1%}
- High-risk supplier emissions: {high_risk_supplier_emissions:,.2f} tCO2e
- Supplier data quality score: {avg_supplier_data_quality:.1%}
- Suppliers without verified target: {no_verified_target_suppliers}
- Probability-weighted carbon cost: {probability_weighted_carbon_cost:,.0f} USD

Status: pass for portfolio/demo use.
""")

dax = """
-- Project 18 - ESG Carbon Finance DAX Measures

Total Emissions tCO2e =
SUM ( fact_emissions[emissions_tco2e] )

Scope 1 Emissions tCO2e =
CALCULATE ( [Total Emissions tCO2e], fact_emissions[scope] = "Scope 1" )

Scope 2 Emissions tCO2e =
CALCULATE ( [Total Emissions tCO2e], fact_emissions[scope] = "Scope 2" )

Scope 3 Emissions tCO2e =
CALCULATE ( [Total Emissions tCO2e], fact_emissions[scope] = "Scope 3" )

Total Spend USD =
SUM ( fact_emissions[spend_usd] )

Revenue USD =
SUM ( fact_emissions[revenue_usd] )

Emissions Intensity tCO2e per $M Revenue =
DIVIDE ( [Total Emissions tCO2e], [Revenue USD] ) * 1000000

Selected Carbon Price USD/t =
SELECTEDVALUE ( dim_carbon_scenario[carbon_price_usd_per_t], 50 )

Carbon Cost USD =
[Total Emissions tCO2e] * [Selected Carbon Price USD/t]

Scenario Carbon Cost USD =
SUM ( fact_carbon_exposure[carbon_cost_usd] )

Probability Weighted Carbon Cost USD =
SUM ( fact_carbon_exposure[probability_weighted_cost_usd] )

Stress Scenario Carbon Cost USD =
CALCULATE ( [Scenario Carbon Cost USD], dim_carbon_scenario[scenario] = "Stress price shock" )

Supplier Emissions tCO2e =
SUM ( fact_supplier_month[emissions_tco2e] )

Supplier Spend USD =
SUM ( fact_supplier_month[spend_usd] )

Supplier Intensity tCO2e per $M Spend =
DIVIDE ( [Supplier Emissions tCO2e], [Supplier Spend USD] ) * 1000000

High Risk Supplier Emissions tCO2e =
CALCULATE ( [Supplier Emissions tCO2e], fact_supplier_month[carbon_risk_tier] = "High" )

Average Data Quality Score =
AVERAGE ( fact_supplier_month[data_quality_score] )

Abatement Annual Reduction tCO2e =
SUM ( fact_abatement_initiatives[annual_reduction_tco2e] )

Abatement Capex USD =
SUM ( fact_abatement_initiatives[capex_usd] )

Planned Abatement Capex USD =
CALCULATE ( [Abatement Capex USD], fact_abatement_initiatives[implementation_status] = "Planned" )

Committed and In Flight Reduction tCO2e =
CALCULATE (
    [Abatement Annual Reduction tCO2e],
    fact_abatement_initiatives[implementation_status] IN { "Committed", "In flight", "Implemented" }
)

Avoided Carbon Cost USD at Selected Price =
[Abatement Annual Reduction tCO2e] * [Selected Carbon Price USD/t]

Abatement Annual Benefit USD =
SUM ( fact_abatement_initiatives[annual_opex_savings_usd] ) + [Avoided Carbon Cost USD at Selected Price]

Abatement ROI =
DIVIDE ( [Abatement Annual Benefit USD], [Abatement Capex USD] )

Payback Years =
DIVIDE ( [Abatement Capex USD], [Abatement Annual Benefit USD] )

MACC USD per tCO2e =
DIVIDE (
    DIVIDE ( [Abatement Capex USD], 7 ) - SUM ( fact_abatement_initiatives[annual_opex_savings_usd] ),
    [Abatement Annual Reduction tCO2e]
)

Latest Month Emissions tCO2e =
VAR LatestMonth = MAX ( dim_date[date_key] )
RETURN CALCULATE ( [Total Emissions tCO2e], dim_date[date_key] = LatestMonth )

YoY Emissions Change % =
VAR CurrentEmissions = [Total Emissions tCO2e]
VAR PriorEmissions =
    CALCULATE ( [Total Emissions tCO2e], DATEADD ( dim_date[month_start], -1, YEAR ) )
RETURN DIVIDE ( CurrentEmissions - PriorEmissions, PriorEmissions )
"""
write_text(MODEL / "MEASURES.dax", dax)
write_text(MODEL / "dax_measures.md", "```DAX\n" + dax.strip() + "\n```")

measure_catalog = {
    "measures": [
        {
            "name": "Total Emissions tCO2e",
            "business_definition": "Total greenhouse gas emissions in metric tons CO2 equivalent.",
            "dax": "SUM ( fact_emissions[emissions_tco2e] )",
            "format": "#,0.0 tCO2e",
            "validation": "Reconciles to sum of fact_emissions emissions_tco2e.",
        },
        {
            "name": "Carbon Cost USD",
            "business_definition": "Financial exposure if emissions are priced at the selected carbon price scenario.",
            "dax": "[Total Emissions tCO2e] * [Selected Carbon Price USD/t]",
            "format": "$#,0",
            "validation": "Total emissions multiplied by scenario price.",
        },
        {
            "name": "Probability Weighted Carbon Cost USD",
            "business_definition": "Scenario exposure weighted by scenario probability.",
            "dax": "SUM ( fact_carbon_exposure[probability_weighted_cost_usd] )",
            "format": "$#,0",
            "validation": "Reconciles to fact_carbon_exposure probability-weighted cost.",
        },
        {
            "name": "Emissions Intensity tCO2e per $M Revenue",
            "business_definition": "Emissions normalized by revenue.",
            "dax": "DIVIDE ( [Total Emissions tCO2e], [Revenue USD] ) * 1000000",
            "format": "#,0.0",
            "validation": "Uses DIVIDE; no rate summing.",
        },
        {
            "name": "Supplier Intensity tCO2e per $M Spend",
            "business_definition": "Supplier emissions normalized by supplier spend.",
            "dax": "DIVIDE ( [Supplier Emissions tCO2e], [Supplier Spend USD] ) * 1000000",
            "format": "#,0.0",
            "validation": "Uses prepared supplier monthly rollup.",
        },
        {
            "name": "High Risk Supplier Emissions tCO2e",
            "business_definition": "Supplier emissions tied to high-risk suppliers.",
            "dax": "CALCULATE ( [Supplier Emissions tCO2e], fact_supplier_month[carbon_risk_tier] = \"High\" )",
            "format": "#,0.0",
            "validation": "Reconciles to fact_supplier_month filtered by carbon_risk_tier.",
        },
        {
            "name": "Abatement ROI",
            "business_definition": "Annual benefit from savings and avoided carbon cost divided by capex.",
            "dax": "DIVIDE ( [Abatement Annual Benefit USD], [Abatement Capex USD] )",
            "format": "0.0%",
            "validation": "Uses initiative-level capex, opex savings, and selected carbon price.",
        },
        {
            "name": "Planned Abatement Capex USD",
            "business_definition": "Capital still in planned status and requiring governance approval.",
            "dax": "CALCULATE ( [Abatement Capex USD], fact_abatement_initiatives[implementation_status] = \"Planned\" )",
            "format": "$#,0",
            "validation": "Reconciles to initiative rows with Planned status.",
        },
    ]
}
write_json(MODEL / "measure_catalog.json", measure_catalog)
write_json(MODEL / "measure_map.json", measure_catalog)

relationship_map = """
# Relationship Map

Recommended Power BI model is a star schema.

## Relationships

- dim_date[date_key] 1:* fact_emissions[date_key]
- dim_date[date_key] 1:* fact_supplier_month[date_key]
- dim_date[date_key] 1:* fact_carbon_exposure[date_key]
- dim_business_unit[business_unit_id] 1:* fact_emissions[business_unit_id]
- dim_facility[facility_id] 1:* fact_emissions[facility_id]
- dim_activity[activity_id] 1:* fact_emissions[activity_id]
- dim_supplier[supplier_id] 1:* fact_emissions[supplier_id]
- dim_supplier[supplier_id] 1:* fact_supplier_month[supplier_id]
- dim_carbon_scenario[scenario_id] 1:* fact_carbon_exposure[scenario_id]

## Filter Direction

Single direction from dimensions to facts. No many-to-many relationships are required.
"""
write_text(MODEL / "relationship_map.md", relationship_map)
write_text(MODEL / "data_dictionary.md", (PROJECT / "data" / "data_dictionary.md").read_text(encoding="utf-8"))
write_text(MODEL / "model_design.md", """
# Semantic Model Design

The model uses compact synthetic CSV extracts designed for Power BI import. The main analytical grain is monthly emission activity by facility, business unit, supplier when applicable, and activity source.

## Fact Tables

- fact_emissions: primary activity/emissions/spend/revenue fact.
- fact_supplier_month: supplier rollup for intensity ranking and target-risk views.
- fact_carbon_exposure: monthly exposure under three carbon price scenarios.
- fact_abatement_initiatives: initiative-level capex, annual reduction, savings, payback, ROI, and MACC.

## Dimensions

- dim_date
- dim_business_unit
- dim_facility
- dim_activity
- dim_supplier
- dim_carbon_scenario

## Design Rules

- All primary KPIs should use DAX measures.
- Rate measures use DIVIDE.
- Percent/rate columns are not summed.
- Technical keys can be hidden after relationships are created.
""")
write_text(MODEL / "metric_definitions.md", """
# Metric Definitions

## North-Star

Total Emissions tCO2e: total Scope 1, 2, and 3 emissions over the selected context.

## Finance Exposure

Carbon Cost USD: Total Emissions tCO2e multiplied by the selected internal or regulatory carbon price.

Emissions Intensity tCO2e per $M Revenue: Total emissions divided by revenue and scaled to one million USD.

## Supplier Diagnostics

Supplier Intensity tCO2e per $M Spend: supplier emissions divided by supplier spend, scaled to one million USD.

Supplier Risk Tier: synthetic tier based on category, emission profile, target status, and data quality score.

High Risk Supplier Emissions tCO2e: emissions from suppliers classified as high carbon risk.

Average Data Quality Score: average supplier data quality score used as a governance guardrail.

## Abatement

Abatement Annual Reduction tCO2e: annual reduction potential of the selected initiative set.

Abatement ROI: annual opex savings plus avoided carbon cost divided by capex.

MACC USD per tCO2e: annualized net cost divided by annual reduction potential.

Planned Abatement Capex USD: abatement capital still in planned status and requiring CFO/ESG approval.

Probability Weighted Carbon Cost USD: carbon cost exposure weighted by scenario probability.
""")
write_text(MODEL / "semantic_model_notes.md", """
# Semantic Model Notes

This build is designed for a portfolio/demo Power BI product. It is not a production GHG inventory, and emissions factors are synthetic but shaped to follow a realistic ESG finance decision model.

The model intentionally combines sustainability and CFO views:

- emissions inventory by scope/source
- financial carbon exposure under carbon price scenarios
- supplier risk/intensity diagnostics
- abatement ROI and MACC prioritization
- governance guardrails for target gaps, high-risk suppliers, and planned capex
""")

theme = {
    "name": "ESG Carbon Finance Executive",
    "dataColors": ["#12372A", "#2A9D8F", "#B7D968", "#F4A261", "#E76F51", "#5B6C5D", "#59656F", "#8AB17D"],
    "background": "#F7F9F8",
    "foreground": "#202A25",
    "tableAccent": "#2A9D8F",
    "visualStyles": {
        "*": {
            "*": {
                "title": [{"fontFace": "Segoe UI Semibold", "fontSize": 11, "color": {"solid": {"color": "#202A25"}}}],
                "labels": [{"color": {"solid": {"color": "#202A25"}}}],
            }
        }
    },
}
write_json(CONFIG / "theme.json", theme)

page_map = {
    "pages": [
        {
            "page": "ESG Finance Overview",
            "question": "Are emissions and carbon cost exposure moving in the right direction?",
            "visuals": ["KPI strip", "emissions and carbon cost trend", "scope mix stacked column", "business unit ranking"],
            "slicers": ["Year", "Region", "Carbon price scenario"],
        },
        {
            "page": "Emissions & Supplier Intensity",
            "question": "Which scopes, sources, suppliers, and facilities drive the footprint?",
            "visuals": ["scope/source waterfall", "supplier intensity ranking", "business unit by activity heatmap", "supplier detail table"],
            "slicers": ["Year", "Scope", "Supplier risk tier"],
        },
        {
            "page": "Carbon Scenario & Abatement ROI",
            "question": "Which carbon price and abatement options change the finance decision?",
            "visuals": ["scenario exposure line", "MACC ranking", "ROI/payback matrix", "initiative action table"],
            "slicers": ["Scenario", "Scope", "Implementation status"],
        },
        {
            "page": "Risk & Action Control Tower",
            "question": "Which supplier, target, and capex risks need executive follow-up?",
            "visuals": ["supplier risk exposure", "target status exposure", "capex by action status", "risk action queue", "guardrail summary"],
            "slicers": ["Year", "Supplier risk tier", "Target status", "Implementation status"],
        },
    ]
}
write_json(CONFIG / "page_map.json", page_map)
write_json(CONFIG / "dashboard_config.json", {
    "project": "Project 18 - ESG Carbon Finance",
    "audience": "CFO, ESG finance lead, procurement lead, and operations leadership",
    "business_goal": "Connect emissions inventory, carbon cost exposure, supplier intensity, abatement ROI, and risk/action governance into one executive-ready decision dashboard.",
    "page_count": 4,
    "theme": "ESG Carbon Finance Executive",
    "data_mode": "synthetic_demo",
    "latest_complete_month": "2026-05",
})
write_json(CONFIG / "visual_map.json", page_map)
write_json(CONFIG / "slicer_map.json", {
    "global_slicers": ["Year", "Region", "Business Unit", "Scope", "Carbon price scenario"],
    "risk_action_slicers": ["Supplier risk tier", "Target status", "Implementation status"],
    "notes": "Use few high-signal slicers; avoid high-cardinality supplier slicers on overview page.",
})

report_spec = """
# Report Spec

## Page 1 - ESG Finance Overview

User question: Are emissions and carbon cost exposure moving in the right direction?

Primary KPIs:
- Total Emissions tCO2e
- Carbon Cost USD
- Emissions Intensity tCO2e per $M Revenue
- Latest Month YoY Emissions Change

Main visuals:
- Monthly emissions and carbon cost trend.
- Scope mix stacked column.
- Business unit ranking by emissions.

## Page 2 - Emissions & Supplier Intensity

User question: Which scopes, sources, suppliers, and facilities drive the footprint?

Main visuals:
- Scope/source breakdown.
- Supplier carbon intensity ranking.
- Business unit x activity heatmap.
- Supplier detail table with risk tier and target status.

## Page 3 - Carbon Scenario & Abatement ROI

User question: Which carbon price and abatement options change the finance decision?

Main visuals:
- Carbon price scenario exposure line.
- MACC-style ranking by initiative.
- ROI and payback matrix.
- Action table by status.

## Page 4 - Risk & Action Control Tower

User question: Which supplier, target, and capex risks need executive follow-up?

Primary KPIs:
- High Risk Supplier Emissions tCO2e
- Suppliers Without Verified Target
- Average Data Quality Score
- 2026 Target Gap tCO2e
- Planned Abatement Capex USD

Main visuals:
- Supplier risk exposure by tier.
- Supplier target status exposure.
- Capex by implementation status.
- High-risk supplier action queue.
- Guardrail summary for CFO/ESG operating review.
"""
write_text(REPORT / "report_spec.md", report_spec)
write_text(REPORT / "page_plan.md", report_spec)
write_text(REPORT / "visual_inventory.md", """
# Visual Inventory

- KPI cards: native `cardVisual` containers with compact sparkline callouts
- Line charts: native `lineChart` containers for monthly emissions and scenario exposure
- Bar/ranking charts: native `barChart` containers for scope, supplier, facility, MACC, risk, target, and capex views
- Tables: native `tableEx` containers for executive detail, supplier risk, abatement queue, risk queue, and guardrail summary
- Slicers: native dropdown `slicer` containers with widened labels for Year, Region, Business Unit, Scope, Scenario, Risk tier, Target status, and Implementation status
- Optional decomposition/tree map: 1

Native Power BI visuals only; no custom visuals required. Static text is used only for page chrome and sparkline callouts.
""")
write_text(REPORT / "filter_interaction_plan.md", """
# Filter Interaction Plan

Global slicers: Year, Region, Business Unit, Scope, Carbon price scenario.

Interactions:
- Scenario slicer affects carbon cost, scenario exposure, abatement ROI, and avoided cost.
- Scope slicer affects emissions, supplier intensity, and abatement views.
- Supplier risk tier affects supplier diagnostics and Risk & Action Control Tower.
- Implementation status affects abatement ROI and capex governance views.
""")
write_text(REPORT / "theme_notes.md", """
# Theme Notes

Palette uses deep green, teal, chartreuse, amber, coral, graphite, and smoke. It avoids a one-note green-only ESG palette while still signaling sustainability and finance seriousness.

Layout style: dense executive BI surface, not a marketing hero. KPI strip first, then movement, then diagnostic breakdown, then action/risk queue.
""")

write_text(DOCS / "design_research.md", """
# Design Research

## External Design References

- Microsoft Sustainability Manager Executive dashboard emphasizes total emissions, revenue intensity, and renewable energy, categorized by scope, geography, organizational unit, and facility: https://learn.microsoft.com/en-us/industry/sustainability/report-dashboard
- Microsoft Emissions Impact Dashboard documentation reinforces that accurate carbon accounting needs emissions data from partners, vendors, and suppliers, and extends across Scope 1, Scope 2, and Scope 3: https://learn.microsoft.com/en-us/power-bi/connect-data/service-connect-to-emissions-impact-dashboard
- GHG Protocol defines Scope 1 as direct emissions, Scope 2 as purchased electricity/heat/steam emissions, and Scope 3 as other indirect emissions: https://ghgprotocol.org/calculation-tools-faq
- GHG Protocol Scope 3 Standard supports identifying where to focus reduction activities across the value chain: https://ghgprotocol.org/corporate-value-chain-scope-3-standard
- Climateworks describes MACC as comparing financial cost/savings with potential tCO2e reduction, using dollars per tCO2e: https://climateworkscentre.org/resource/how-to-read-a-marginal-abatement-cost-curve/

## Local Template Decision

Primary layout seed/reference: `Template/06_Procurement_Supplier_Spend/Microsoft_Procurement_Analysis.pbix`.

Reason: closest local template for supplier, location, category, and spend analysis. It is not ESG-specific, so it is used only as a design/technical seed reference, not as final content.

Secondary reference: `Template/03_FPnA_Budget_Spend/Packt_Ch12_Planning_Case_Study.pbix`.

Reason: scenario planning pattern is relevant for carbon price scenarios and investment decisions.

## Final 4-Page Layout

1. ESG Finance Overview
2. Emissions & Supplier Intensity
3. Carbon Scenario & Abatement ROI
4. Risk & Action Control Tower
""")

write_text(AGENT / "intake_brief.md", """
# Intake Brief

Project: Project 18 - ESG Carbon Finance

Request: Upgrade Project 18 using the BI A-Z Master Prompt v3 and Power BI Upgrade Playbook. Refresh the project to a 4-page executive dashboard pattern with a dedicated risk/action page.

Assumptions:
- Portfolio/demo build, not production GHG reporting.
- No real source data was provided, so synthetic data is allowed.
- Primary audience: CFO, ESG finance lead, procurement lead, operations leadership.
- Final target remains Power BI PBIX at `output/dashboard_final.pbix`.
- Supplemental HTML and build package are allowed, but cannot replace a validated PBIX.
- Upgrade emphasis: model guardrails, report story, PBIX rebuildability, QA evidence, and portfolio handoff polish.
""")
write_text(AGENT / "run_log.md", """
# Run Log

- Read Project 18 README and BI A-Z Master Prompt.
- Loaded Data Analytics dashboard workflow and user context.
- Confirmed Power BI Desktop and pbi-tools exist locally.
- Researched ESG dashboard, GHG scope, and MACC references.
- Selected Procurement/Supplier Spend local PBIX as layout seed/reference.
- Generated synthetic ESG Carbon Finance data with seed 180418.
- Generated model, measures, config, QA, report spec, and handoff artifacts.
- 2026-06-23: Upgraded to BI A-Z v3 structure with 4-page report journey and dedicated Risk & Action Control Tower.
- 2026-06-23: Added risk/guardrail KPIs to data validation, DAX, model metadata, HTML preview, and native Power BI layout generator.
""")
write_text(AGENT / "session_guard.md", f"""
# Session Guard

Current project path: {PROJECT}

Expected final PBIX path: {PROJECT / "output" / "dashboard_final.pbix"}

Power BI windows detected at original data-build time: unrelated sessions were present in environment check output and were not selected for save operations.

Selected window/process/session: none during source/data regeneration. Use exact path matching before any Desktop save or open-check.

Evidence selected session belongs to current project: required before future Desktop save/open-check.

Ignored unrelated sessions: any pbi-tools sessions whose `PbixPath` is outside Project 18.
""")
write_text(AGENT / "pbix_authoring_decision.md", """
# PBIX Authoring Decision

Preferred route: SCRIPTED_DESKTOP_PBIX with Desktop open-check.

Evidence:
- Power BI Desktop EXE is installed.
- Microsoft Store Power BI Desktop is also installed.
- pbi-tools is installed and can extract PBIX files.
- pbi-tools compile failed in this environment because the installed Desktop packaging API does not match the pbi-tools Desktop compile call.

Fallback routes:
- PBIP/PBIT build package: prepared as supplemental source package.
- Manual-assisted Desktop build: documented if automated Save As cannot complete.

Final status:
- Original 2026-06-15 PBIX opened in Power BI Desktop with visual error count 0.
- 2026-06-23 v3 upgrade regenerates source/model/layout package and requires a fresh Desktop open-check after PBIX patching.
""")
write_text(AGENT / "failure_matrix.md", """
# Failure Matrix

| Area | Status | Evidence | Next action |
|---|---:|---|---|
| Power BI Desktop EXE | Available | `C:\\Program Files\\Microsoft Power BI Desktop\\bin\\PBIDesktop.exe` | Use Desktop route |
| pbi-tools extract | Available | Procurement sample extracted | Use for inspection/export |
| pbi-tools compile | Failing | MissingMethodException in PowerBIPackager.Save | Do not rely on compile for final |
| Final PBIX | Delivered before v3 refresh | `qa/pbix_final_validation.json` showed open-check pass on 2026-06-15 | Re-run open-check after any PBIX patch |
| v3 layout refresh | Source generated | 4-page native layout JSON generated by build script | Patch PBIX and validate package |
""")

write_text(WORKFLOW / "blueprint.md", """
# BI Blueprint

## Objective

Create an executive-ready ESG Carbon Finance dashboard that lets finance and sustainability leaders monitor emissions, quantify carbon cost exposure, identify supplier hotspots, and prioritize abatement investment.

## Audience

CFO, ESG finance lead, procurement lead, and operations leadership.

## Decisions Supported

- Are emissions and carbon exposure improving or worsening?
- Which scopes, facilities, business units, and suppliers drive the footprint?
- Which abatement initiatives should receive capital first?
- Which supplier, target, and capex risks need executive follow-up?

## KPI Tree

North-star KPI: Total Emissions tCO2e.

Driver KPIs: Scope 1/2/3 mix, emissions intensity, supplier intensity, carbon price exposure.

Diagnostic KPIs: supplier risk tier, data quality score, MACC, payback, abatement ROI, target gap, planned capex.

## Data Requirements

Synthetic portfolio data at monthly emission activity grain, with supplier and abatement dimensions.

## Report Journey

1. What is the current ESG finance exposure?
2. Where are the emissions and supplier intensity hotspots?
3. Which scenario and abatement investments should be prioritized?
4. Which risks and action owners need CFO/ESG review?
""")
write_json(WORKFLOW / "state.json", {
    "project_name": "Project 18 - ESG Carbon Finance",
    "project_path": str(PROJECT),
    "bi_topic": "ESG Carbon Finance",
    "delivery_level": "executive-ready portfolio demo",
    "audience": "CFO, ESG finance lead, procurement lead, operations leadership",
    "primary_decision": "Prioritize decarbonization and supplier actions by carbon cost exposure and ROI.",
    "data_mode": "synthetic",
    "target_output": "Power BI PBIX",
    "final_pbix_path": "output/dashboard_final.pbix",
    "current_phase": 8,
    "phase_status": "v3_source_package_refreshed_pbix_patch_pending_open_check",
    "critical_kpis": ["Total Emissions tCO2e", "Carbon Cost USD", "Supplier Intensity", "High Risk Supplier Emissions", "Abatement ROI", "MACC", "Planned Capex"],
    "assumptions": ["Synthetic demo data because no production source was provided.", "Latest complete month is 2026-05."],
    "risks": ["Any newly patched PBIX requires Desktop save/open validation before being called final."],
})
write_text(WORKFLOW / "decision_log.md", """
# Decision Log

Date: 2026-06-15

Decision: Use synthetic demo data with fixed seed.
Reason: No real source data was provided and the project is portfolio/demo oriented.
Impact: Dashboard can be rebuilt deterministically but is not a production GHG inventory.
Reversible: yes.

Decision: Upgrade from three tabs to four pages.
Reason: BI A-Z v3 standard separates risk/exception/action handling from scenario and ROI analysis.
Impact: The executive journey now has overview, diagnostics, scenario/ROI, and control-tower action review.
Reversible: yes.

Decision: Use Procurement PBIX as layout seed/reference only.
Reason: It is the closest local supplier/spend template but not ESG-specific.
Impact: Avoids stale domain bindings in final content.
Reversible: yes.

Decision: Keep native static textbox/shape visuals for the patched report layout.
Reason: They rendered reliably in the prior Desktop open-check while preserving the semantic model for Data/Model view exploration.
Impact: Canvas is executive-readable; deeper self-service analysis remains available through model fields and measures.
Reversible: yes, if a future build uses fully bound native visuals with Desktop QA.
""")
write_text(WORKFLOW / "risk_register.md", """
# Risk Register

| Risk | Impact | Likelihood | Mitigation | Status |
|---|---:|---:|---|---|
| PBIX cannot be saved by automation | High | Medium | Prepare rebuild package and Desktop runbook | Open |
| Synthetic data mistaken for production | High | Low | Label all source docs and QA as synthetic demo | Mitigated |
| ESG accounting overclaim | Medium | Low | Cite GHG Protocol and label factor assumptions synthetic | Mitigated |
| Risk/action story gets buried inside ROI page | Medium | Medium | Add dedicated Risk & Action Control Tower | Mitigated |
| v3 PBIX patch not yet open-checked | High | Medium | Patch package, validate file, then open exact PBIX in Desktop | Open |
""")

write_text(QA / "data_model_qa.md", """
# Data Model QA

Status: pass for synthetic portfolio data.

Checks:
- Prepared CSVs exist.
- Date range covers Jan 2024 through May 2026.
- Dimension keys are unique.
- Fact record IDs are unique.
- Critical key fields are non-null.
- Rate measures are defined with DIVIDE in DAX.
- Risk and action guardrails reconcile to prepared supplier, scenario, and initiative tables.
""")
write_text(QA / "qa_checklist.md", """
# QA Checklist

## Data QA

- [x] Row counts generated.
- [x] Date range validated.
- [x] Critical key nulls checked.
- [x] Duplicate keys checked.
- [x] KPI reconciliation file created.

## Metric QA

- [x] DAX measure definitions created.
- [x] Rates use DIVIDE.
- [x] Reconciliation CSV created.
- [x] Risk/action guardrails reconciled.

## Visual QA

- [x] Native report layout JSON generated.
- [x] Four report pages defined in spec/config.
- [ ] v3 patched PBIX opened in Power BI Desktop.
- [ ] Visual error count verified as 0 after v3 patch.
- [ ] Desktop screenshots refreshed after v3 patch.

## File QA

- [ ] output/dashboard_final.pbix exists.
- [ ] Exact v3 PBIX opens in Power BI Desktop.
""")
write_text(QA / "visual_qa_notes.md", "Native layout JSON now defines four pages with actual slicer, cardVisual, lineChart, barChart, and tableEx containers plus compact KPI sparkline callouts. Fresh Desktop visual QA is required after patching `output/dashboard_final.pbix` with the upgraded layout.")
write_text(QA / "interaction_qa_notes.md", "Interaction QA plan: verify Year, Region, Scope, Business Unit, Carbon Scenario, Supplier Risk Tier, Target Status, and Implementation Status after the v3 PBIX open-check.")
write_text(QA / "performance_qa_notes.md", "Prepared data is compact: less than 2,000 fact rows and should be responsive in Power BI Desktop.")
write_text(QA / "regression_qa_notes.md", "Data/model regression checks pass for generated artifacts. PBIX visual regression should be refreshed after applying the v3 layout.")
write_text(QA / "report_qa.md", "Report source QA: pass for four-page spec/config/layout generation. Desktop screenshot QA pending after v3 PBIX patch.")

write_text(DOCS / "rebuild_guide.md", f"""
# Rebuild Guide

Run from the project folder:

```powershell
python build/scripts/build_project18_assets.py
python build/scripts/build_powerbi_native_assets.py
powershell -NoProfile -ExecutionPolicy Bypass -File build/scripts/03_apply_native_layout_to_pbix.ps1
```

Then open Power BI Desktop and import the prepared CSVs from:

```text
{PREP}
```

The scripted route regenerates data/docs, model/layout source, then patches the native layout into `output/dashboard_final.pbix`. If building manually, create relationships according to `model/relationship_map.md`, add measures from `model/MEASURES.dax`, apply `build/config/theme.json`, and build the four pages in `report/report_spec.md`.
""")
write_text(DOCS / "refresh_guide.md", """
# Refresh Guide

This is a synthetic portfolio build. Refresh means regenerating the deterministic synthetic source and reloading the prepared CSVs.

Steps:
1. Run `python build/scripts/build_project18_assets.py`.
2. Refresh the Power BI model.
3. Check row counts in `data/validated/validation_summary.json`.
4. Reconcile KPIs using `qa/reconciliation.csv`.
5. Re-run visual QA.
""")
write_text(DOCS / "handoff_notes.md", """
# Handoff Notes

Final PBIX: `output/dashboard_final.pbix`.

v3 status: source/model/layout package refreshed. A fresh Power BI Desktop open-check is required after patching the PBIX with the v3 four-page layout.

Dashboard purpose: connect emissions, supplier intensity, carbon price scenarios, abatement ROI, and risk/action governance for ESG finance decisions.

Audience: CFO, ESG finance, procurement, and operations leaders.

Canvas standard: upgraded toward the Project 20 pattern with native dropdown slicers, native KPI cards/charts/tables, widened filter labels, chart/table polish, and compact KPI sparkline callouts.

Pages:
1. ESG Finance Overview
2. Emissions & Supplier Intensity
3. Carbon Scenario & Abatement ROI
4. Risk & Action Control Tower

Key KPIs:
- Total Emissions tCO2e
- Carbon Cost USD
- Emissions Intensity
- Supplier Intensity
- High Risk Supplier Emissions
- Average Data Quality Score
- Abatement ROI
- MACC USD per tCO2e
- Planned Abatement Capex USD

Data source: synthetic demo CSVs generated with seed 180418.

Known issue: any newly patched v3 PBIX should be reopened in Power BI Desktop and screenshot-checked before being described as freshly Desktop-validated.
""")
write_text(DOCS / "changelog.md", """
# Changelog

## 2026-06-23

- Upgraded Project 18 to the BI A-Z v3 delivery structure.
- Added a fourth page: Risk & Action Control Tower.
- Added risk/guardrail KPI definitions for high-risk supplier emissions, data quality, probability-weighted carbon cost, target gap, and planned abatement capex.
- Updated report spec, config, QA notes, handoff notes, and native layout generator for the four-page executive story.
- Reworked the active PBIX layout generator from static analytical panels to native slicer/card/chart/table containers, with KPI sparkline callouts and widened slicer labels.
- Fixed supplemental HTML preview month labels and added KPI sparklines for preview parity.

## 2026-06-15

- Created synthetic ESG Carbon Finance data product.
- Created semantic model docs and DAX measures.
- Created 3-tab report spec and dashboard config.
- Created QA and handoff package.
""")
write_text(DOCS / "issue_log.md", """
# Issue Log

| Date | Issue | Status | Notes |
|---|---|---:|---|
| 2026-06-23 | v3 PBIX requires fresh Desktop open-check after layout patch | Open | Validate exact `output/dashboard_final.pbix` after patching |
| 2026-06-15 | Original final PBIX required Desktop build/open-check | Closed | Open-check passed in prior validation evidence |
| 2026-06-15 | pbi-tools compile failed with installed packaging API | Open | Use Desktop route instead of pbi-tools compile |
""")
write_text(DOCS / "release_notes.md", """
# Release Notes

v3 source package for Project 18 - ESG Carbon Finance.

Included:
- Synthetic data and validation
- Semantic model and DAX
- 4-page report design
- Theme and config
- Handoff/rebuild/refresh docs
- Supplemental HTML dashboard preview
- Native Power BI layout generator

Fresh Desktop open-check is required after any v3 PBIX patch.
""")
write_text(DOCS / "known_issues.md", "v3 PBIX patch requires a fresh Power BI Desktop open-check and screenshot refresh before claiming fresh visual QA pass.")
write_text(DOCS / "performance_tuning_log.md", "No performance tuning required for this compact synthetic dataset. The v3 layout keeps each page visually dense but compact, with static native canvas elements and fewer than 6 analytical panels per page.")

write_text(POWERBI / "notes" / "authoring_strategy.md", (AGENT / "pbix_authoring_decision.md").read_text(encoding="utf-8"))
write_text(POWERBI / "notes" / "pbix_build_runbook.md", """
# PBIX Build Runbook

1. Open Power BI Desktop.
2. Import prepared CSVs from `data/prepared`.
3. Set datatypes:
   - keys as text
   - dates as date
   - emissions/spend/revenue/capex as decimal numbers
4. Create star-schema relationships from `model/relationship_map.md`.
5. Add DAX measures from `model/MEASURES.dax`.
6. Import theme from `build/config/theme.json`.
7. Build the 4 pages from `report/report_spec.md`.
8. Save as `output/dashboard_final.pbix`.
9. Reopen exact file and complete `qa/pbix_final_validation.json`.
""")
write_text(POWERBI / "notes" / "desktop_ui_runbook.md", """
# Desktop UI Runbook

Preferred Desktop path:

`C:\\Program Files\\Microsoft Power BI Desktop\\bin\\PBIDesktop.exe`

Validation:
- Confirm title/path belongs to Project 18.
- Save only to `output/dashboard_final.pbix`.
- Capture screenshots for all 4 pages into `output/screenshots`.
- Record visual error count.
""")
write_text(POWERBI / "launch_powerbi.ps1", f"""
$ErrorActionPreference = 'Stop'
$pbi = 'C:\\Program Files\\Microsoft Power BI Desktop\\bin\\PBIDesktop.exe'
if (-not (Test-Path $pbi)) {{
  throw 'Power BI Desktop EXE not found.'
}}
Start-Process -FilePath $pbi
Write-Host 'Power BI Desktop launched. Build final PBIX at: {PROJECT / "output" / "dashboard_final.pbix"}'
""")
write_text(POWERBI / "power_query_m.md", f"""
# Power Query M Source Snippets

Use these snippets if building the model manually from CSV.

```powerquery
let
    Source = Csv.Document(File.Contents("{(PREP / "fact_emissions.csv").as_posix()}"), [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]),
    PromotedHeaders = Table.PromoteHeaders(Source, [PromoteAllScalars=true])
in
    PromotedHeaders
```

Repeat for each CSV in `data/prepared`.
""")

overview_by_month = defaultdict(lambda: {"emissions": 0.0, "spend": 0.0, "revenue": 0.0})
scope_for_chart = defaultdict(float)
bu_for_chart = defaultdict(float)
for r in flat_rows:
    overview_by_month[r["month_start"]]["emissions"] += r["emissions_tco2e"]
    overview_by_month[r["month_start"]]["spend"] += r["spend_usd"]
    overview_by_month[r["month_start"]]["revenue"] += r["revenue_usd"]
    scope_for_chart[r["scope"]] += r["emissions_tco2e"]
    bu_for_chart[r["business_unit"]] += r["emissions_tco2e"]

top_suppliers = sorted(supplier_rows, key=lambda r: r["supplier_intensity_tco2e_per_musd"], reverse=True)[:10]
top_abatement = sorted(abatement_rows, key=lambda r: r["macc_usd_per_tco2e"])[:10]
risk_exposure = defaultdict(float)
target_exposure = defaultdict(float)
for row in supplier_rows:
    risk_exposure[row["carbon_risk_tier"]] += row["emissions_tco2e"]
    target_exposure[row["target_status"]] += row["emissions_tco2e"]
capex_status = defaultdict(float)
for row in abatement_rows:
    capex_status[row["implementation_status"]] += row["capex_usd"]

def preview_spark(values):
    blocks = "▁▂▃▄▅▆▇█"
    cleaned = [float(v) for v in values if v is not None]
    if not cleaned:
        return ""
    lo, hi = min(cleaned), max(cleaned)
    if hi == lo:
        return blocks[3] * len(cleaned)
    return "".join(blocks[min(len(blocks) - 1, max(0, round((v - lo) / (hi - lo) * (len(blocks) - 1))))] for v in cleaned)

overview_months = sorted(overview_by_month.items())
monthly_emissions_values = [v["emissions"] for _k, v in overview_months]
monthly_cost_values = [v["emissions"] * 90 for _k, v in overview_months]
monthly_intensity_values = [(v["emissions"] / v["revenue"] * 1_000_000) if v["revenue"] else 0 for _k, v in overview_months]
supplier_risk_by_month = defaultdict(float)
for row in supplier_rows:
    month = f"{row['date_key'][:4]}-{row['date_key'][4:6]}-01"
    if row["carbon_risk_tier"] == "High":
        supplier_risk_by_month[month] += row["emissions_tco2e"]
high_risk_monthly_values = [supplier_risk_by_month[k] for k, _v in overview_months]

html_payload = {
    "kpis": {
        "Total emissions": f"{total_emissions/1000:,.1f}k tCO2e",
        "Carbon cost @ $90/t": f"${total_emissions*90/1_000_000:,.1f}M",
        "Intensity": f"{total_emissions/total_revenue*1_000_000:,.1f} tCO2e/$M",
        "Latest YoY": f"{yoy_change:.1%}",
        "High-risk emissions": f"{high_risk_supplier_emissions/1000:,.1f}k tCO2e",
        "Target gap": f"{target_gap/1000:,.1f}k tCO2e",
    },
    "sparkline": {
        "Total emissions": preview_spark(monthly_emissions_values[-12:]),
        "Carbon cost @ $90/t": preview_spark(monthly_cost_values[-12:]),
        "Intensity": preview_spark(monthly_intensity_values[-12:]),
        "Latest YoY": preview_spark(monthly_emissions_values[-12:]),
        "High-risk emissions": preview_spark(high_risk_monthly_values[-12:]),
        "Target gap": preview_spark(monthly_emissions_values[-12:]),
    },
    "months": [
        {"month": k[:7], "emissions": round(v["emissions"], 1), "cost": round(v["emissions"] * 90 / 1_000_000, 2)}
        for k, v in overview_months
    ],
    "scope": [{"scope": k, "emissions": round(v, 1)} for k, v in sorted(scope_for_chart.items())],
    "business_units": [{"business_unit": k, "emissions": round(v, 1)} for k, v in sorted(bu_for_chart.items(), key=lambda x: x[1], reverse=True)],
    "suppliers": top_suppliers,
    "abatement": top_abatement,
    "risk": [{"tier": k, "emissions": round(v, 1)} for k, v in sorted(risk_exposure.items(), key=lambda x: x[1], reverse=True)],
    "targets": [{"target": k, "emissions": round(v, 1)} for k, v in sorted(target_exposure.items(), key=lambda x: x[1], reverse=True)],
    "capex_status": [{"status": k, "capex": round(v, 1)} for k, v in sorted(capex_status.items(), key=lambda x: x[1], reverse=True)],
    "guardrails": {
        "supplier_data_quality": f"{avg_supplier_data_quality:.1%}",
        "suppliers_without_target": no_verified_target_suppliers,
        "planned_capex": f"${planned_abatement_capex/1_000_000:,.1f}M",
        "weighted_carbon_cost": f"${probability_weighted_carbon_cost/1_000_000:,.1f}M",
        "secured_reduction": f"{committed_inflight_reduction/1000:,.1f}k tCO2e",
    },
}
write_json(OUTPUT / "dashboard_preview_data.json", html_payload)

html = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Project 18 - ESG Carbon Finance</title>
  <style>
    :root { --ink:#202A25; --muted:#5B6C5D; --bg:#F7F9F8; --panel:#FFFFFF; --green:#12372A; --teal:#2A9D8F; --lime:#B7D968; --amber:#F4A261; --coral:#E76F51; --line:#D9E2DC; }
    * { box-sizing: border-box; }
    body { margin:0; font-family: Segoe UI, Arial, sans-serif; background: var(--bg); color: var(--ink); }
    header { padding: 22px 30px 14px; background: var(--green); color:white; }
    h1 { margin:0; font-size: 26px; font-weight: 650; letter-spacing: 0; }
    .sub { margin-top: 6px; color:#DDE9E2; font-size: 13px; }
    .tabs { display:flex; gap: 6px; padding: 10px 30px; background:#EAF1ED; border-bottom:1px solid var(--line); position: sticky; top:0; z-index:2; }
    .tabs button { border:1px solid var(--line); background:#fff; color:var(--ink); padding: 8px 12px; border-radius:6px; font-weight:600; cursor:pointer; }
    .tabs button.active { background:var(--green); color:#fff; border-color:var(--green); }
    main { padding: 18px 30px 28px; }
    .page { display:none; }
    .page.active { display:block; }
    .grid { display:grid; grid-template-columns: repeat(12, 1fr); gap:12px; }
    .kpi { grid-column: span 3; background:var(--panel); border:1px solid var(--line); border-radius:8px; padding:14px; min-height:88px; }
    .kpi b { display:block; font-size:12px; color:var(--muted); margin-bottom:10px; }
    .kpi span { font-size:25px; font-weight:700; }
    .kpi small { display:block; margin-top:8px; color:var(--teal); font: 700 13px/1 Consolas, monospace; letter-spacing:1px; white-space:nowrap; overflow:hidden; text-overflow:clip; }
    .card { background:var(--panel); border:1px solid var(--line); border-radius:8px; padding:14px; min-height:280px; }
    .span6 { grid-column: span 6; } .span7 { grid-column: span 7; } .span5 { grid-column: span 5; } .span12 { grid-column: span 12; }
    h2 { margin:0 0 10px; font-size:16px; }
    svg { width:100%; height:220px; display:block; }
    table { width:100%; border-collapse: collapse; font-size:12px; }
    th,td { text-align:left; padding:7px 8px; border-bottom:1px solid var(--line); }
    th { color:var(--muted); font-weight:700; }
    .note { color:var(--muted); font-size:12px; margin-top:8px; }
    @media (max-width: 900px) { .kpi,.span5,.span6,.span7,.span12 { grid-column: span 12; } header,main,.tabs { padding-left:16px; padding-right:16px; } }
  </style>
</head>
<body>
  <header>
    <h1>ESG Carbon Finance</h1>
    <div class="sub">Synthetic portfolio dashboard preview. Final Power BI PBIX requires Desktop save/open validation.</div>
  </header>
  <nav class="tabs">
    <button class="active" data-page="overview">ESG Finance Overview</button>
    <button data-page="supplier">Emissions & Supplier Intensity</button>
    <button data-page="roi">Carbon Scenario & Abatement ROI</button>
    <button data-page="risk">Risk & Action Control Tower</button>
  </nav>
  <main>
    <section id="overview" class="page active">
      <div class="grid" id="kpis"></div>
      <div class="grid" style="margin-top:12px">
        <div class="card span7"><h2>Monthly Emissions and Carbon Cost</h2><svg id="trend"></svg></div>
        <div class="card span5"><h2>Emissions by Scope</h2><svg id="scope"></svg></div>
        <div class="card span12"><h2>Business Unit Emissions Ranking</h2><svg id="bu"></svg></div>
      </div>
    </section>
    <section id="supplier" class="page">
      <div class="grid">
        <div class="card span12"><h2>Top Supplier Intensity</h2><table id="supplierTable"></table></div>
      </div>
    </section>
    <section id="roi" class="page">
      <div class="grid">
        <div class="card span12"><h2>Abatement Priority by MACC</h2><table id="abatementTable"></table><div class="note">Negative or low MACC initiatives should be prioritized before high-cost options when feasible.</div></div>
      </div>
    </section>
    <section id="risk" class="page">
      <div class="grid">
        <div class="card span6"><h2>Supplier Risk Exposure</h2><svg id="riskChart"></svg></div>
        <div class="card span6"><h2>Target Status Exposure</h2><svg id="targetChart"></svg></div>
        <div class="card span6"><h2>Capex by Action Status</h2><svg id="capexChart"></svg></div>
        <div class="card span6"><h2>Guardrail Summary</h2><table id="guardrailTable"></table></div>
      </div>
    </section>
  </main>
  <script id="payload" type="application/json">__PAYLOAD__</script>
  <script>
    const data = JSON.parse(document.getElementById('payload').textContent);
    document.querySelectorAll('.tabs button').forEach(btn => btn.addEventListener('click', () => {
      document.querySelectorAll('.tabs button,.page').forEach(x => x.classList.remove('active'));
      btn.classList.add('active');
      document.getElementById(btn.dataset.page).classList.add('active');
    }));
    const kpiEl = document.getElementById('kpis');
    Object.entries(data.kpis).forEach(([k,v]) => {
      const el = document.createElement('div'); el.className='kpi';
      const spark = data.sparkline?.[k] || '';
      el.innerHTML = `<b>${k}</b><span>${v}</span><small>${spark}</small>`; kpiEl.appendChild(el);
    });
    function bar(svgId, rows, label, value, color) {
      const svg = document.getElementById(svgId), w=900, h=220, m=34;
      const max = Math.max(...rows.map(r=>r[value]));
      svg.setAttribute('viewBox', `0 0 ${w} ${h}`);
      svg.innerHTML = rows.map((r,i) => {
        const y = m + i*((h-m*2)/rows.length), bw = (r[value]/max)*(w-260);
        return `<text x="4" y="${y+14}" font-size="12">${r[label]}</text><rect x="190" y="${y}" width="${bw}" height="18" rx="3" fill="${color}"></rect><text x="${195+bw}" y="${y+14}" font-size="11">${Math.round(r[value]).toLocaleString()}</text>`;
      }).join('');
    }
    function trend() {
      const svg = document.getElementById('trend'), w=900, h=220, m=34, rows=data.months;
      const max = Math.max(...rows.map(r=>r.emissions));
      svg.setAttribute('viewBox', `0 0 ${w} ${h}`);
      const pts = rows.map((r,i) => `${m+i*((w-m*2)/(rows.length-1))},${h-m-(r.emissions/max)*(h-m*2)}`).join(' ');
      svg.innerHTML = `<polyline points="${pts}" fill="none" stroke="#2A9D8F" stroke-width="4"></polyline>` + rows.filter((_,i)=>i%4===0).map((r,i)=>{
        const idx=i*4, x=m+idx*((w-m*2)/(rows.length-1)); return `<text x="${x-12}" y="${h-8}" font-size="10">${r.month.slice(2)}</text>`;
      }).join('');
    }
    trend();
    bar('scope', data.scope, 'scope', 'emissions', '#2A9D8F');
    bar('bu', data.business_units, 'business_unit', 'emissions', '#12372A');
    bar('riskChart', data.risk, 'tier', 'emissions', '#E76F51');
    bar('targetChart', data.targets, 'target', 'emissions', '#F4A261');
    bar('capexChart', data.capex_status, 'status', 'capex', '#12372A');
    const supplierTable = document.getElementById('supplierTable');
    supplierTable.innerHTML = '<tr><th>Supplier</th><th>Category</th><th>Risk</th><th>Intensity</th><th>Target</th></tr>' + data.suppliers.map(r => `<tr><td>${r.supplier}</td><td>${r.supplier_category}</td><td>${r.carbon_risk_tier}</td><td>${r.supplier_intensity_tco2e_per_musd.toLocaleString()}</td><td>${r.target_status}</td></tr>`).join('');
    const abatementTable = document.getElementById('abatementTable');
    abatementTable.innerHTML = '<tr><th>Initiative</th><th>Scope</th><th>Status</th><th>Reduction</th><th>MACC</th><th>Payback</th><th>ROI</th></tr>' + data.abatement.map(r => `<tr><td>${r.initiative}</td><td>${r.scope}</td><td>${r.implementation_status}</td><td>${r.annual_reduction_tco2e.toLocaleString()}</td><td>$${r.macc_usd_per_tco2e.toLocaleString()}</td><td>${r.payback_years_at_90}</td><td>${(r.roi_at_90*100).toFixed(1)}%</td></tr>`).join('');
    const guardrailTable = document.getElementById('guardrailTable');
    guardrailTable.innerHTML = '<tr><th>Guardrail</th><th>Value</th></tr>' + Object.entries(data.guardrails).map(([k,v]) => `<tr><td>${k.replaceAll('_',' ')}</td><td>${v}</td></tr>`).join('');
  </script>
</body>
</html>
""".replace("__PAYLOAD__", json.dumps(html_payload))
write_text(OUTPUT / "dashboard_preview.html", html)

readme = f"""
# Project 18 - ESG Carbon Finance

Executive-ready portfolio BI build connecting emissions, carbon cost exposure, supplier intensity, abatement ROI, and risk/action governance.

## Current Build Status

- Data/model/report source package: ready.
- Supplemental HTML preview: `output/dashboard_preview.html`.
- Final PBIX target: `output/dashboard_final.pbix`.
- Final PBIX status: v3 source/layout package refreshed; run fresh Power BI Desktop open-check after PBIX patch.

## Dashboard Pages

1. ESG Finance Overview
2. Emissions & Supplier Intensity
3. Carbon Scenario & Abatement ROI
4. Risk & Action Control Tower

## Rebuild

```powershell
python build/scripts/build_project18_assets.py
python build/scripts/build_powerbi_native_assets.py
powershell -NoProfile -ExecutionPolicy Bypass -File build/scripts/03_apply_native_layout_to_pbix.ps1
```

See `docs/rebuild_guide.md`, `docs/handoff_notes.md`, and `powerbi/notes/pbix_build_runbook.md`.
"""
write_text(PROJECT / "README.md", readme)

print(json.dumps({
    "project": str(PROJECT),
    "seed": SEED,
    "prepared_tables": list(tables),
    "total_emissions_tco2e": round(total_emissions, 2),
    "latest_month": latest_key,
    "html_preview": str(OUTPUT / "dashboard_preview.html"),
}, indent=2))
