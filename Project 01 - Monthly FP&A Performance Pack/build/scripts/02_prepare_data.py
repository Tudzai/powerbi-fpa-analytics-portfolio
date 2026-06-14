from __future__ import annotations

import csv
from datetime import date
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
PREPARED_DIR = PROJECT_ROOT / "data" / "prepared"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def date_key(value: str) -> int:
    return int(value.replace("-", ""))


def month_name(month: int) -> str:
    return [
        "Jan",
        "Feb",
        "Mar",
        "Apr",
        "May",
        "Jun",
        "Jul",
        "Aug",
        "Sep",
        "Oct",
        "Nov",
        "Dec",
    ][month - 1]


def build_date_dim(months: list[str]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for idx, month_text in enumerate(sorted(set(months)), start=1):
        dt = date.fromisoformat(month_text)
        rows.append(
            {
                "DateKey": date_key(month_text),
                "MonthStart": month_text,
                "Year": dt.year,
                "Quarter": f"Q{((dt.month - 1) // 3) + 1}",
                "MonthNumber": dt.month,
                "MonthName": month_name(dt.month),
                "MonthYear": f"{month_name(dt.month)} {dt.year}",
                "MonthIndex": idx,
                "IsActualClosed": "Yes" if dt <= date(2026, 5, 1) else "No",
                "FiscalYear": dt.year,
                "FiscalQuarter": f"FY{dt.year} Q{((dt.month - 1) // 3) + 1}",
            }
        )
    return rows


def dimension(values: list[dict[str, object]], key_name: str, name_fields: list[str]) -> tuple[list[dict[str, object]], dict[tuple[object, ...], str]]:
    unique: dict[tuple[object, ...], dict[str, object]] = {}
    for row in values:
        key = tuple(row[field] for field in name_fields)
        unique.setdefault(key, {field: row[field] for field in name_fields})
    rows: list[dict[str, object]] = []
    lookup: dict[tuple[object, ...], str] = {}
    prefix = "".join(part[0] for part in key_name.replace("Key", "").split("_")).upper()
    for idx, key in enumerate(sorted(unique), start=1):
        surrogate = f"{prefix}{idx:03d}"
        lookup[key] = surrogate
        rows.append({key_name: surrogate, **unique[key]})
    return rows, lookup


def to_float(row: dict[str, str], field: str) -> float:
    return round(float(row[field]), 2)


def main() -> None:
    PREPARED_DIR.mkdir(parents=True, exist_ok=True)
    financials = read_csv(RAW_DIR / "raw_fpa_financials.csv")
    opex = read_csv(RAW_DIR / "raw_fpa_opex_department.csv")
    cash = read_csv(RAW_DIR / "raw_fpa_cash.csv")
    bridge = read_csv(RAW_DIR / "raw_fpa_budget_actual_bridge.csv")
    commentary = read_csv(RAW_DIR / "raw_monthly_commentary.csv")

    all_months = [r["MonthStart"] for r in financials] + [r["MonthStart"] for r in cash] + [r["MonthStart"] for r in opex]
    dim_date = build_date_dim(all_months)

    dim_scenario = [
        {"ScenarioKey": "S001", "Scenario": "Actual", "ScenarioSort": 1, "ScenarioType": "Closed actual"},
        {"ScenarioKey": "S002", "Scenario": "Budget", "ScenarioSort": 2, "ScenarioType": "Annual operating plan"},
        {"ScenarioKey": "S003", "Scenario": "Forecast", "ScenarioSort": 3, "ScenarioType": "Latest forecast"},
    ]
    scenario_lookup = {row["Scenario"]: row["ScenarioKey"] for row in dim_scenario}

    bu_seed = [{"BusinessUnit": r["BusinessUnit"]} for r in financials]
    dim_bu, bu_lookup = dimension(bu_seed, "BusinessUnitKey", ["BusinessUnit"])

    product_seed = [{"Product": r["Product"], "BusinessUnit": r["BusinessUnit"]} for r in financials]
    dim_product, product_lookup = dimension(product_seed, "ProductKey", ["BusinessUnit", "Product"])

    region_seed = [{"Region": r["Region"]} for r in financials]
    dim_region, region_lookup = dimension(region_seed, "RegionKey", ["Region"])

    customer_seed = [
        {"Customer": r["Customer"], "CustomerSegment": r["CustomerSegment"], "Industry": r["Industry"]}
        for r in financials
    ]
    dim_customer, customer_lookup = dimension(customer_seed, "CustomerKey", ["Customer", "CustomerSegment", "Industry"])

    department_seed = [{"Department": r["Department"]} for r in opex]
    dim_department, department_lookup = dimension(department_seed, "DepartmentKey", ["Department"])

    fact_financials: list[dict[str, object]] = []
    for idx, r in enumerate(financials, start=1):
        fact_financials.append(
            {
                "FactFinanceKey": f"FIN{idx:07d}",
                "DateKey": date_key(r["MonthStart"]),
                "ScenarioKey": scenario_lookup[r["Scenario"]],
                "BusinessUnitKey": bu_lookup[(r["BusinessUnit"],)],
                "ProductKey": product_lookup[(r["BusinessUnit"], r["Product"])],
                "RegionKey": region_lookup[(r["Region"],)],
                "CustomerKey": customer_lookup[(r["Customer"], r["CustomerSegment"], r["Industry"])],
                "Revenue": to_float(r, "Revenue"),
                "COGS": to_float(r, "COGS"),
                "GrossMargin": to_float(r, "GrossMargin"),
                "AllocatedOpex": to_float(r, "AllocatedOpex"),
                "EBITDA": to_float(r, "EBITDA"),
                "Orders": int(r["Orders"]),
                "CashImpact": to_float(r, "CashImpact"),
            }
        )

    fact_opex: list[dict[str, object]] = []
    for idx, r in enumerate(opex, start=1):
        fact_opex.append(
            {
                "FactOpexKey": f"OPX{idx:07d}",
                "DateKey": date_key(r["MonthStart"]),
                "ScenarioKey": scenario_lookup[r["Scenario"]],
                "BusinessUnitKey": bu_lookup[(r["BusinessUnit"],)],
                "RegionKey": region_lookup[(r["Region"],)],
                "DepartmentKey": department_lookup[(r["Department"],)],
                "Opex": to_float(r, "Opex"),
                "FTE": round(float(r["FTE"]), 1),
            }
        )

    fact_cash: list[dict[str, object]] = []
    for idx, r in enumerate(cash, start=1):
        fact_cash.append(
            {
                "FactCashKey": f"CSH{idx:07d}",
                "DateKey": date_key(r["MonthStart"]),
                "ScenarioKey": scenario_lookup[r["Scenario"]],
                "BusinessUnitKey": bu_lookup[(r["BusinessUnit"],)],
                "RegionKey": region_lookup[(r["Region"],)],
                "CashBalance": to_float(r, "CashBalance"),
                "ARBalance": to_float(r, "ARBalance"),
                "DSO": round(float(r["DSO"]), 1),
                "Capex": to_float(r, "Capex"),
            }
        )

    fact_bridge: list[dict[str, object]] = []
    for idx, r in enumerate(bridge, start=1):
        fact_bridge.append(
            {
                "BridgeKey": f"BRG{idx:05d}",
                "DateKey": date_key(r["MonthStart"]),
                "BusinessUnitKey": bu_lookup[(r["BusinessUnit"],)],
                "RegionKey": region_lookup[(r["Region"],)],
                "BridgeStep": r["BridgeStep"],
                "BridgeOrder": int(r["BridgeOrder"]),
                "Amount": to_float(r, "Amount"),
            }
        )

    fact_commentary = [
        {
            "DateKey": date_key(r["MonthStart"]),
            "Audience": r["Audience"],
            "WhatHappened": r["WhatHappened"],
            "Why": r["Why"],
            "WhatNext": r["WhatNext"],
            "Severity": r["Severity"],
        }
        for r in commentary
    ]

    write_csv(PREPARED_DIR / "dim_date.csv", dim_date, list(dim_date[0].keys()))
    write_csv(PREPARED_DIR / "dim_scenario.csv", dim_scenario, list(dim_scenario[0].keys()))
    write_csv(PREPARED_DIR / "dim_business_unit.csv", dim_bu, list(dim_bu[0].keys()))
    write_csv(PREPARED_DIR / "dim_product.csv", dim_product, list(dim_product[0].keys()))
    write_csv(PREPARED_DIR / "dim_region.csv", dim_region, list(dim_region[0].keys()))
    write_csv(PREPARED_DIR / "dim_customer.csv", dim_customer, list(dim_customer[0].keys()))
    write_csv(PREPARED_DIR / "dim_department.csv", dim_department, list(dim_department[0].keys()))
    write_csv(PREPARED_DIR / "fact_financials.csv", fact_financials, list(fact_financials[0].keys()))
    write_csv(PREPARED_DIR / "fact_opex_department.csv", fact_opex, list(fact_opex[0].keys()))
    write_csv(PREPARED_DIR / "fact_cash.csv", fact_cash, list(fact_cash[0].keys()))
    write_csv(PREPARED_DIR / "fact_bridge.csv", fact_bridge, list(fact_bridge[0].keys()))
    write_csv(PREPARED_DIR / "fact_commentary.csv", fact_commentary, list(fact_commentary[0].keys()))

    print(f"Prepared star-schema data in {PREPARED_DIR}")


if __name__ == "__main__":
    main()
