from __future__ import annotations

import json
import shutil
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = PROJECT_ROOT / "output"
PROJECT_DIR = OUTPUT_DIR / "powerbi_project"
REPORT_NAME = "Monthly_FPA_Performance_Pack"
REPORT_DIR = PROJECT_DIR / f"{REPORT_NAME}.Report"
MODEL_DIR = PROJECT_DIR / f"{REPORT_NAME}.SemanticModel"
REPORT_DEF_DIR = REPORT_DIR / "definition"
PAGES_DIR = REPORT_DEF_DIR / "pages"


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def literal(value: str | int | float | bool) -> dict:
    if isinstance(value, bool):
        literal_value = "true" if value else "false"
    elif isinstance(value, str):
        literal_value = "'" + value.replace("'", "''") + "'"
    else:
        literal_value = str(value)
    return {"expr": {"Literal": {"Value": literal_value}}}


def solid(color: str) -> dict:
    return {"solid": {"color": color}}


def column(table: str, prop: str) -> dict:
    return {
        "Column": {
            "Expression": {"SourceRef": {"Entity": table}},
            "Property": prop,
        }
    }


def measure(table: str, prop: str) -> dict:
    return {
        "Measure": {
            "Expression": {"SourceRef": {"Entity": table}},
            "Property": prop,
        }
    }


def projection(field: dict, query_ref: str, display_name: str | None = None) -> dict:
    payload = {"field": field, "queryRef": query_ref}
    if display_name:
        payload["displayName"] = display_name
    return payload


def title_objects(title: str, subtitle: str | None = None) -> dict:
    objects = {
        "title": [
            {
                "properties": {
                    "show": literal(True),
                    "text": literal(title),
                    "fontColor": solid("#111827"),
                    "fontSize": literal(11),
                    "bold": literal(True),
                    "titleWrap": literal(True),
                }
            }
        ],
        "background": [
            {
                "properties": {
                    "show": literal(True),
                    "color": solid("#FFFFFF"),
                    "transparency": literal(0),
                }
            }
        ],
        "border": [
            {
                "properties": {
                    "show": literal(True),
                    "color": solid("#E5E7EB"),
                    "radius": literal(6),
                }
            }
        ],
        "visualHeader": [{"properties": {"show": literal(False)}}],
    }
    if subtitle:
        objects["subTitle"] = [
            {
                "properties": {
                    "show": literal(True),
                    "text": literal(subtitle),
                    "fontColor": solid("#64748B"),
                    "fontSize": literal(9),
                    "titleWrap": literal(True),
                }
            }
        ]
    return objects


def make_visual(
    *,
    name: str,
    visual_type: str,
    x: float,
    y: float,
    width: float,
    height: float,
    z: int,
    query_state: dict[str, list[dict]] | None = None,
    title: str | None = None,
    subtitle: str | None = None,
    sort_field: dict | None = None,
    sort_direction: str = "Descending",
) -> dict:
    visual: dict = {"visualType": visual_type}
    if query_state is not None:
        visual["query"] = {
            "queryState": {
                role: {"projections": projections}
                for role, projections in query_state.items()
            }
        }
        if sort_field is not None:
            visual["query"]["sortDefinition"] = {
                "sort": [{"field": sort_field, "direction": sort_direction}]
            }
    if title:
        visual["visualContainerObjects"] = title_objects(title, subtitle)
    return {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.9.0/schema.json",
        "name": name,
        "position": {
            "x": x,
            "y": y,
            "z": z,
            "height": height,
            "width": width,
            "tabOrder": z,
        },
        "visual": visual,
    }


def measure_projection(name: str, display: str | None = None) -> dict:
    return projection(measure("KPI Measures", name), f"KPI Measures.{name}", display)


def column_projection(table: str, name: str, display: str | None = None) -> dict:
    return projection(column(table, name), f"{table}.{name}", display)


def card(name: str, title: str, metric: str, x: float, y: float, z: int) -> dict:
    return make_visual(
        name=name,
        visual_type="card",
        x=x,
        y=y,
        width=185,
        height=105,
        z=z,
        title=title,
        query_state={"Values": [measure_projection(metric, title)]},
    )


def build_pages() -> dict[str, list[dict]]:
    revenue = measure("KPI Measures", "Actual Revenue")
    ebitda_var = measure("KPI Measures", "EBITDA Var vs Budget")
    bridge = measure("KPI Measures", "Bridge Amount")

    return {
        "Executive Overview": [
            card("kpi_revenue", "Revenue", "Actual Revenue Current Month", 24, 84, 1000),
            card("kpi_gm", "Gross Margin %", "Gross Margin %", 224, 84, 1001),
            card("kpi_ebitda", "EBITDA", "Actual EBITDA Current Month", 424, 84, 1002),
            card("kpi_opex", "Opex", "Actual Opex", 624, 84, 1003),
            card("kpi_cash", "Cash", "Actual Cash Balance", 824, 84, 1004),
            card("kpi_orders", "Orders", "Orders", 1024, 84, 1005),
            make_visual(
                name="trend_revenue",
                visual_type="lineChart",
                x=24,
                y=220,
                width=760,
                height=300,
                z=1006,
                title="12M Revenue Trend",
                subtitle="Actual, budget, and forecast pacing by month.",
                query_state={
                    "Category": [column_projection("DimDate", "MonthYear", "Month")],
                    "Series": [column_projection("DimScenario", "Scenario")],
                    "Y": [measure_projection("Revenue")],
                },
                sort_field=column("DimDate", "MonthIndex"),
                sort_direction="Ascending",
            ),
            make_visual(
                name="variance_by_bu",
                visual_type="barChart",
                x=812,
                y=220,
                width=444,
                height=300,
                z=1007,
                title="EBITDA Variance by Business Unit",
                subtitle="Actual less budget.",
                query_state={
                    "Category": [column_projection("DimBusinessUnit", "BusinessUnit")],
                    "Y": [measure_projection("EBITDA Var vs Budget")],
                },
                sort_field=ebitda_var,
            ),
            make_visual(
                name="summary_matrix",
                visual_type="matrix",
                x=24,
                y=548,
                width=1232,
                height=148,
                z=1008,
                title="Actual vs Budget vs Forecast",
                query_state={
                    "Rows": [column_projection("DimScenario", "Scenario")],
                    "Values": [
                        measure_projection("Revenue"),
                        measure_projection("Gross Margin"),
                        measure_projection("Gross Margin %"),
                        measure_projection("EBITDA"),
                        measure_projection("Allocated Opex"),
                        measure_projection("Cash Balance Latest Month"),
                    ],
                },
            ),
        ],
        "Variance Bridge": [
            make_visual(
                name="bridge_waterfall",
                visual_type="waterfallChart",
                x=24,
                y=96,
                width=760,
                height=520,
                z=2000,
                title="Budget to Actual EBITDA Bridge",
                subtitle="Bridge isolates volume, mix, price, COGS, opex, and cash timing.",
                query_state={
                    "Category": [column_projection("FactBridge", "BridgeStep", "Bridge Step")],
                    "Y": [measure_projection("Bridge Amount")],
                },
                sort_field=column("FactBridge", "BridgeOrder"),
                sort_direction="Ascending",
            ),
            make_visual(
                name="variance_matrix",
                visual_type="matrix",
                x=812,
                y=96,
                width=444,
                height=520,
                z=2001,
                title="Variance by BU and Region",
                query_state={
                    "Rows": [
                        column_projection("DimBusinessUnit", "BusinessUnit"),
                        column_projection("DimRegion", "Region"),
                    ],
                    "Values": [
                        measure_projection("Actual Revenue"),
                        measure_projection("Budget Revenue"),
                        measure_projection("Revenue Var vs Budget"),
                        measure_projection("Actual EBITDA"),
                        measure_projection("Budget EBITDA"),
                        measure_projection("EBITDA Var vs Budget"),
                    ],
                },
                sort_field=revenue,
            ),
        ],
        "Customer and Product Drilldown": [
            make_visual(
                name="customer_scatter",
                visual_type="scatterChart",
                x=24,
                y=96,
                width=610,
                height=500,
                z=3000,
                title="Customer Revenue vs Margin",
                subtitle="Size is orders; color is customer segment.",
                query_state={
                    "Details": [column_projection("DimCustomer", "Customer")],
                    "Legend": [column_projection("DimCustomer", "CustomerSegment")],
                    "X": [measure_projection("Actual Revenue")],
                    "Y": [measure_projection("Gross Margin %")],
                    "Size": [measure_projection("Orders")],
                },
            ),
            make_visual(
                name="customer_product_table",
                visual_type="tableEx",
                x=660,
                y=96,
                width=596,
                height=500,
                z=3001,
                title="Customer, Product, Region Detail",
                query_state={
                    "Values": [
                        column_projection("DimCustomer", "Customer"),
                        column_projection("DimProduct", "Product"),
                        column_projection("DimRegion", "Region"),
                        measure_projection("Actual Revenue"),
                        measure_projection("Gross Margin %"),
                        measure_projection("Actual EBITDA"),
                        measure_projection("EBITDA Var vs Budget"),
                    ]
                },
                sort_field=ebitda_var,
            ),
        ],
        "Opex and Cash Control": [
            make_visual(
                name="opex_by_department",
                visual_type="clusteredColumnChart",
                x=24,
                y=96,
                width=610,
                height=420,
                z=4000,
                title="Opex by Department",
                query_state={
                    "Category": [column_projection("DimDepartment", "Department")],
                    "Series": [column_projection("DimScenario", "Scenario")],
                    "Y": [measure_projection("Department Opex")],
                },
            ),
            make_visual(
                name="cash_trend",
                visual_type="lineChart",
                x=660,
                y=96,
                width=596,
                height=420,
                z=4001,
                title="Cash Balance Trend",
                query_state={
                    "Category": [column_projection("DimDate", "MonthYear", "Month")],
                    "Series": [column_projection("DimScenario", "Scenario")],
                    "Y": [measure_projection("Cash Balance Latest Month")],
                },
                sort_field=column("DimDate", "MonthIndex"),
                sort_direction="Ascending",
            ),
            make_visual(
                name="commentary_card",
                visual_type="multiRowCard",
                x=24,
                y=540,
                width=1232,
                height=140,
                z=4002,
                title="Commentary: What happened, why, what next",
                query_state={
                    "Values": [
                        measure_projection("Selected Commentary - What Happened"),
                        measure_projection("Selected Commentary - Why"),
                        measure_projection("Selected Commentary - What Next"),
                    ]
                },
            ),
        ],
    }


def write_report() -> None:
    pages = build_pages()
    page_names = {}
    for index, display_name in enumerate(pages):
        safe = "Page" + str(index + 1).zfill(2) + "_" + "".join(
            ch if ch.isalnum() else "_" for ch in display_name
        )
        page_names[display_name] = safe[:50]

    write_json(
        REPORT_DIR / "definition.pbir",
        {
            "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definitionProperties/2.0.0/schema.json",
            "version": "4.0",
            "datasetReference": {
                "byPath": {"path": f"../{REPORT_NAME}.SemanticModel"}
            },
        },
    )
    write_json(
        REPORT_DEF_DIR / "version.json",
        {
            "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/versionMetadata/1.0.0/schema.json",
            "version": "1.0.0",
        },
    )
    write_json(
        REPORT_DEF_DIR / "report.json",
        {
            "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/report/2.0.0/schema.json",
            "themeCollection": {
                "baseTheme": {
                    "name": "CY26SU05",
                    "reportVersionAtImport": "5.73",
                    "type": "SharedResources",
                }
            },
            "settings": {
                "useStylableVisualContainerHeader": True,
                "defaultFilterActionIsDataFilter": True,
                "defaultDrillFilterOtherVisuals": True,
                "allowChangeFilterTypes": True,
                "useEnhancedTooltips": True,
            },
            "annotations": [
                {"name": "defaultPage", "value": page_names["Executive Overview"]},
                {"name": "theme", "value": "orange"},
            ],
        },
    )
    write_json(
        PAGES_DIR / "pages.json",
        {
            "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/pagesMetadata/1.1.0/schema.json",
            "pageOrder": list(page_names.values()),
            "activePageName": page_names["Executive Overview"],
        },
    )

    for display_name, visuals in pages.items():
        page_dir = PAGES_DIR / page_names[display_name]
        write_json(
            page_dir / "page.json",
            {
                "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/page/2.1.0/schema.json",
                "name": page_names[display_name],
                "displayName": display_name,
                "displayOption": "FitToPage",
                "height": 720,
                "width": 1280,
                "objects": {
                    "background": [
                        {
                            "properties": {
                                "color": solid("#F8FAFC"),
                                "transparency": literal(0),
                            }
                        }
                    ],
                    "outspace": [
                        {
                            "properties": {
                                "color": solid("#F8FAFC"),
                                "transparency": literal(0),
                            }
                        }
                    ],
                },
            },
        )
        for visual in visuals:
            write_json(
                page_dir / "visuals" / visual["name"] / "visual.json",
                visual,
            )


def write_model() -> None:
    script_path = OUTPUT_DIR / "tmp_model_script.json"
    if not script_path.exists():
        raise SystemExit(
            f"Missing {script_path}. Run 07_push_model_to_powerbi_desktop.ps1 and export the model script first."
        )
    script_payload = json.loads(script_path.read_text(encoding="utf-8"))
    database = script_payload["create"]["database"]
    database["name"] = "Monthly FP&A Performance Pack"

    write_json(
        MODEL_DIR / "definition.pbism",
        {
            "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/semanticModel/definitionProperties/1.0.0/schema.json",
            "version": "1.0",
            "settings": {"qnaEnabled": False},
        },
    )
    write_json(MODEL_DIR / "model.bim", database)


def write_shortcuts() -> None:
    payload = {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/pbip/pbipProperties/1.0.0/schema.json",
        "version": "1.0",
        "artifacts": [{"report": {"path": f"{REPORT_NAME}.Report"}}],
        "settings": {"enableAutoRecovery": True},
    }
    write_json(PROJECT_DIR / f"{REPORT_NAME}.pbip", payload)
    root_payload = dict(payload)
    root_payload["artifacts"] = [
        {"report": {"path": f"powerbi_project/{REPORT_NAME}.Report"}}
    ]
    write_json(OUTPUT_DIR / "open_dashboard_powerbi.pbip", root_payload)


def write_handoff() -> None:
    notes = """# Power BI Dashboard Entry Point

Open this file in Power BI Desktop:

`output/open_dashboard_powerbi.pbip`

This PBIP package includes:

- Report PBIR pages and visuals.
- Local semantic model TMSL (`model.bim`).
- CSV import partitions pointing to this project prepared data.
- Orange FP&A dashboard layout across 4 pages.

If Power BI opens without data, click Refresh. The model points to `data/prepared/*.csv`.
"""
    (OUTPUT_DIR / "OPEN_POWERBI_DASHBOARD.md").write_text(notes, encoding="utf-8")


def main() -> None:
    if PROJECT_DIR.exists():
        shutil.rmtree(PROJECT_DIR)
    PROJECT_DIR.mkdir(parents=True, exist_ok=True)
    write_model()
    write_report()
    write_shortcuts()
    write_handoff()
    print(f"Power BI project written to {PROJECT_DIR}")
    print(f"Open shortcut written to {OUTPUT_DIR / 'open_dashboard_powerbi.pbip'}")


if __name__ == "__main__":
    main()
