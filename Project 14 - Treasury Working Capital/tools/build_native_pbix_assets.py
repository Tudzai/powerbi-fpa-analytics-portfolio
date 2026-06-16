from __future__ import annotations

import copy
import csv
import json
import random
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BI_ROOT = ROOT.parents[0]
SAMPLE_DIR = BI_ROOT / "Project 10 - AML Fraud Monitoring" / "qa" / "legacy_visual_samples"
MODEL_BIM = ROOT / "model" / "model.bim"
LAYOUT_JSON = ROOT / "build" / "native_report_layout_project14.json"
SEED_TEMPLATE = BI_ROOT / "Template" / "01_Core_Financial_Statements" / "Packt_Ch07_Group_Reporting.pbix"


THEME = {
    "bg": "#F3F6F8",
    "panel": "#FFFFFF",
    "panel2": "#F8FAFB",
    "border": "#D8E0E7",
    "grid": "#E7EDF2",
    "text": "#15202B",
    "muted": "#607081",
    "teal": "#0F766E",
    "blue": "#2F5F9E",
    "green": "#6F8552",
    "gold": "#B68B36",
    "rose": "#B85062",
    "ink": "#22313F",
}
PALETTE = [THEME["teal"], THEME["blue"], THEME["green"], THEME["gold"], THEME["rose"], THEME["ink"]]


TABLE_FILES = {
    "DimDate": "dim_date.csv",
    "DimWeek": "dim_week.csv",
    "DimEntity": "dim_entity.csv",
    "DimCustomer": "dim_customer.csv",
    "DimVendor": "dim_vendor.csv",
    "DimBank": "dim_bank.csv",
    "DimScenario": "dim_scenario.csv",
    "DimCashCategory": "dim_cash_category.csv",
    "FactCashPosition": "fact_cash_position.csv",
    "FactLiquidityFacility": "fact_liquidity_facility.csv",
    "FactWorkingCapital": "fact_working_capital.csv",
    "FactARInvoice": "fact_ar_invoice.csv",
    "FactAPInvoice": "fact_ap_invoice.csv",
    "FactCashForecast": "fact_cash_forecast.csv",
    "FactForecastAccuracy": "fact_forecast_accuracy.csv",
    "FactFXExposure": "fact_fx_exposure.csv",
    "FactTreasuryRiskAction": "fact_treasury_risk_action.csv",
}


COLUMN_TYPES = {
    "date": "dateTime",
    "week_start": "dateTime",
    "week_end": "dateTime",
    "snapshot_date": "dateTime",
    "invoice_date": "dateTime",
    "due_date": "dateTime",
    "maturity_date": "dateTime",
    "year": "int64",
    "month_number": "int64",
    "month_index": "int64",
    "week_number": "int64",
    "scenario_sort": "int64",
    "sort_order": "int64",
    "credit_terms_days": "int64",
    "payment_terms_days": "int64",
    "days_past_due": "int64",
    "days_to_due": "int64",
    "is_latest_complete": "boolean",
    "is_first_four_weeks": "boolean",
    "is_next_thirteen_weeks": "boolean",
    "is_synthetic": "boolean",
    "is_overdue": "boolean",
}


RELATIONSHIPS = [
    ("FactCashPosition", "entity_id", "DimEntity", "entity_id"),
    ("FactCashPosition", "bank_id", "DimBank", "bank_id"),
    ("FactLiquidityFacility", "entity_id", "DimEntity", "entity_id"),
    ("FactWorkingCapital", "date_id", "DimDate", "date_id"),
    ("FactWorkingCapital", "entity_id", "DimEntity", "entity_id"),
    ("FactARInvoice", "entity_id", "DimEntity", "entity_id"),
    ("FactARInvoice", "customer_id", "DimCustomer", "customer_id"),
    ("FactARInvoice", "expected_collection_week_id", "DimWeek", "week_id"),
    ("FactAPInvoice", "entity_id", "DimEntity", "entity_id"),
    ("FactAPInvoice", "vendor_id", "DimVendor", "vendor_id"),
    ("FactAPInvoice", "payment_week_id", "DimWeek", "week_id"),
    ("FactCashForecast", "week_id", "DimWeek", "week_id"),
    ("FactCashForecast", "entity_id", "DimEntity", "entity_id"),
    ("FactCashForecast", "scenario_id", "DimScenario", "scenario_id"),
    ("FactForecastAccuracy", "entity_id", "DimEntity", "entity_id"),
    ("FactFXExposure", "entity_id", "DimEntity", "entity_id"),
    ("FactTreasuryRiskAction", "entity_id", "DimEntity", "entity_id"),
]


def read_header(path: Path) -> list[str]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return next(csv.reader(handle))


def data_type(column: str) -> str:
    if column in COLUMN_TYPES:
        return COLUMN_TYPES[column]
    if column.endswith("_usd") or column.endswith("_ratio"):
        return "double"
    if column.endswith("_days") or column.endswith("_number") or column.endswith("_sort"):
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
    path = csv_path.as_posix()
    typed = ",\n        ".join([f'{{"{c["name"]}", {m_type(c["dataType"])}}}' for c in columns])
    return [
        "let",
        f'    Source = Csv.Document(File.Contents("{path}"), [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]),',
        "    PromotedHeaders = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),",
        "    TypedColumns = Table.TransformColumnTypes(PromotedHeaders, {",
        f"        {typed}",
        '    }, "en-US")',
        "in",
        "    TypedColumns",
    ]


def measure_catalog() -> list[dict]:
    return json.loads((ROOT / "model" / "measure_catalog.json").read_text(encoding="utf-8"))


def build_model_bim() -> dict:
    tables = []
    prepared = ROOT / "data" / "prepared"
    for table_name, file_name in TABLE_FILES.items():
        csv_path = prepared / file_name
        columns = [
            {
                "name": col,
                "dataType": data_type(col),
                "sourceColumn": col,
                "summarizeBy": "none",
            }
            for col in read_header(csv_path)
        ]
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

    tables.append(
        {
            "name": "KPI Measures",
            "columns": [
                {
                    "name": "Measure Group",
                    "dataType": "string",
                    "sourceColumn": "Measure Group",
                    "isHidden": True,
                    "summarizeBy": "none",
                }
            ],
            "partitions": [
                {
                    "name": "KPI Measures-Import",
                    "mode": "import",
                    "source": {
                        "type": "m",
                        "expression": [
                            "let",
                            '    Source = #table(type table [Measure Group = text], {{"Treasury Working Capital"}})',
                            "in",
                            "    Source",
                        ],
                    },
                }
            ],
            "measures": [
                {
                    "name": item["measure_name"],
                    "expression": item["dax"],
                    "formatString": item["format_string"],
                    "description": item["definition"],
                }
                for item in measure_catalog()
            ],
        }
    )

    relationships = [
        {
            "name": f"rel_{from_table}_{from_col}_{to_table}_{to_col}",
            "fromTable": from_table,
            "fromColumn": from_col,
            "toTable": to_table,
            "toColumn": to_col,
        }
        for from_table, from_col, to_table, to_col in RELATIONSHIPS
    ]

    return {
        "compatibilityLevel": 1550,
        "model": {
            "culture": "en-US",
            "defaultPowerBIDataSourceVersion": "powerBI_V3",
            "sourceQueryCulture": "en-US",
            "tables": tables,
            "relationships": relationships,
        },
    }


def load_sample(name: str) -> dict:
    return json.loads((SAMPLE_DIR / f"{name}.json").read_text(encoding="utf-8"))


SAMPLES = {
    "cardVisual": load_sample("cardVisual"),
    "barChart": load_sample("barChart"),
    "columnChart": load_sample("columnChart"),
    "donutChart": load_sample("donutChart"),
    "slicer": load_sample("slicer"),
    "tableEx": load_sample("tableEx"),
    "waterfallChart": load_sample("waterfallChart"),
}


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
    if any(token in text for token in ("risk", "overdue", "unhedged", "error")):
        return THEME["rose"]
    if any(token in text for token in ("cash", "liquidity", "runway", "forecast")):
        return THEME["teal"]
    if any(token in text for token in ("dso", "dpo", "working", "ar", "ap")):
        return THEME["blue"]
    if any(token in text for token in ("fx", "debt", "facility")):
        return THEME["gold"]
    return THEME["ink"]


def visual_shell(title: str | None = None, subtitle: str | None = None) -> dict:
    result = {
        "background": [{"properties": {"show": lit("true"), "color": color(THEME["panel"]), "transparency": lit("0D")}}],
        "border": [{"properties": {"show": lit("true"), "color": color(THEME["border"]), "radius": lit("6.0D"), "width": lit("1.0D")}}],
        "dropShadow": [{"properties": {"show": lit("true"), "color": color("#000000"), "transparency": lit("78.0D"), "angle": lit("45.0D"), "distance": lit("1.0D")}}],
    }
    if title:
        result["title"] = [
            {
                "properties": {
                    "show": lit("true"),
                    "text": prop_text(title),
                    "fontFamily": prop_text("Segoe UI Semibold"),
                    "fontSize": lit("9.5D"),
                    "fontColor": color(title_accent(title)),
                    "alignment": prop_text("left"),
                }
            }
        ]
    if subtitle:
        result["subTitle"] = [
            {
                "properties": {
                    "show": lit("true"),
                    "text": prop_text(subtitle),
                    "fontFamily": prop_text("Segoe UI"),
                    "fontSize": lit("7.4D"),
                    "fontColor": color(THEME["muted"]),
                }
            }
        ]
    return result


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
        objects["sentimentColors"] = [
            {
                "properties": {
                    "increaseFill": color(THEME["teal"]),
                    "decreaseFill": color(THEME["rose"]),
                    "totalFill": color(THEME["ink"]),
                }
            }
        ]
    for idx, metadata in enumerate(measures or ["_default"]):
        item = {"properties": {"fill": color(PALETTE[idx % len(PALETTE)])}}
        if metadata != "_default":
            item["selector"] = {"metadata": metadata}
        objects["dataPoint"].append(item)
    return objects


def table_objects() -> dict:
    return {
        "grid": [{"properties": {"gridHorizontal": lit("false"), "gridVertical": lit("false"), "outlineColor": color(THEME["border"]), "rowPadding": lit("5D")}}],
        "columnHeaders": [{"properties": {"fontFamily": prop_text("Segoe UI Semibold"), "fontSize": lit("8.0D"), "fontColor": color(THEME["teal"]), "backColor": color(THEME["panel2"])}}],
        "values": [{"properties": {"fontSize": lit("7.5D"), "fontFamily": prop_text("Segoe UI"), "fontColor": color(THEME["text"]), "backColorPrimary": color(THEME["panel"]), "backColorSecondary": color(THEME["panel2"])}}],
    }


def slicer_objects(title: str) -> dict:
    return {
        "data": [{"properties": {"mode": prop_text("Dropdown")}}],
        "general": [{"properties": {"orientation": lit("0D")}}],
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
    result = {}
    for bucket, fields in mapping.items():
        result[bucket] = [
            {"queryRef": f"{table}.{field}", **({"active": True} if idx == 0 else {})}
            for idx, (table, field, *_rest) in enumerate(fields)
        ]
    return result


def data_visual(kind: str, x, y, w, h, z, proj_map: dict[str, list[tuple[str, str, str, str]]], title: str, subtitle: str | None = None) -> dict:
    cfg = copy.deepcopy(SAMPLES[kind])
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
    sv["vcObjects"] = visual_shell(title, subtitle)
    return outer(cfg, x, y, w, h, z)


def card(measure: str, title: str, x, y, w, h, z) -> dict:
    visual = data_visual("cardVisual", x, y, w, h, z, {"Data": [("KPI Measures", measure, "measure", title)]}, title)
    cfg = json.loads(visual["config"])
    metadata = f"KPI Measures.{measure}"
    accent = title_accent(title)
    cfg["singleVisual"]["objects"] = {
        "layout": [{"properties": {"backgroundShow": lit("false"), "rectangleRoundedCurve": lit("6L"), "cellPadding": lit("6D"), "paddingUniform": lit("6D")}, "selector": {"id": "default"}}],
        "value": [{"properties": {"fontSize": lit("19.0D"), "fontFamily": lit("'Segoe UI Semibold'"), "fontColor": color(accent)}, "selector": {"metadata": metadata}}],
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


def slicer(table: str, field: str, title: str, x, y, w, h, z) -> dict:
    return data_visual("slicer", x, y, w, h, z, {"Values": [(table, field, "column", title)]}, title)


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


def header(title: str, subtitle: str) -> list[dict]:
    return [
        shape(24, 18, 5, 48, 10, THEME["teal"]),
        text_box("TREASURY WORKING CAPITAL", 38, 20, 260, 18, 20, 7.5, THEME["teal"], False),
        text_box(title, 38, 32, 520, 34, 30, 14, THEME["text"]),
        text_box(subtitle, 575, 36, 430, 24, 40, 8, THEME["muted"], False),
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
    seed_pbix = ROOT / "output" / "dashboard_model_seed_ch07.pbix"
    if seed_pbix.exists():
        with zipfile.ZipFile(seed_pbix, "r") as package:
            raw = package.read("Report/Layout")
        base = json.loads(raw.decode("utf-16le"))
        base["sections"] = []
        base["theme"] = {"themeJson": {"name": "Treasury Working Capital", "dataColors": PALETTE}}
        return base
    return {
        "version": "5.44",
        "theme": {"themeJson": {"name": "Treasury Working Capital", "dataColors": PALETTE}},
        "config": json.dumps({"version": "5.44"}, separators=(",", ":")),
        "layoutOptimization": 0,
        "sections": [],
    }


def build_layout() -> dict:
    random.seed(14042)
    layout = blank_layout()

    p1 = header("Treasury Command Center", "Liquidity, runway, scenario forecast, and action queue")
    p1 += [
        slicer("DimEntity", "region", "Region", 784, 24, 128, 42, 100),
        slicer("DimEntity", "entity", "Entity", 922, 24, 158, 42, 110),
        slicer("DimScenario", "scenario", "Scenario", 1090, 24, 166, 42, 120),
        card("Available Liquidity", "Available Liquidity", 24, 92, 190, 88, 200),
        card("Cash Balance", "Cash Balance", 224, 92, 190, 88, 210),
        card("Liquidity Headroom", "Liquidity Headroom", 424, 92, 190, 88, 220),
        card("Cash Runway Weeks", "Cash Runway", 624, 92, 190, 88, 230),
        card("Forecast Net Cash Flow", "13W Net Flow", 824, 92, 190, 88, 240),
        card("Forecast Error %", "Forecast Error", 1024, 92, 232, 88, 250),
        data_visual(
            "columnChart",
            24,
            204,
            610,
            236,
            300,
            {"Category": [("DimWeek", "week_label", "column", "Week")], "Y": [("KPI Measures", "Forecast Net Cash Flow", "measure", "Net Cash Flow")]},
            "13-week net cash flow",
            "Receipts less payments by week",
        ),
        data_visual(
            "barChart",
            646,
            204,
            300,
            236,
            310,
            {"Category": [("DimEntity", "region", "column", "Region")], "Y": [("KPI Measures", "Available Liquidity", "measure", "Available Liquidity")]},
            "Liquidity by region",
        ),
        data_visual(
            "barChart",
            958,
            204,
            298,
            236,
            320,
            {"Category": [("DimBank", "bank", "column", "Bank")], "Y": [("KPI Measures", "Available Cash", "measure", "Available Cash")]},
            "Cash by bank",
        ),
        data_visual(
            "barChart",
            24,
            462,
            610,
            176,
            330,
            {"Category": [("FactTreasuryRiskAction", "risk_type", "column", "Risk")], "Y": [("KPI Measures", "Open Risk Value", "measure", "Open Risk Value")]},
            "Management action queue",
        ),
        data_visual(
            "barChart",
            646,
            462,
            610,
            176,
            340,
            {"Category": [("DimEntity", "country", "column", "Country")], "Y": [("KPI Measures", "Liquidity Headroom", "measure", "Headroom")]},
            "Treasury operating snapshot",
        ),
    ]

    p2 = header("Working Capital Control", "AR/AP aging, DSO/DPO, and collection-payment focus")
    p2 += [
        slicer("DimEntity", "region", "Region", 784, 24, 128, 42, 100),
        slicer("DimCustomer", "risk_rating", "Customer Risk", 922, 24, 158, 42, 110),
        slicer("DimVendor", "criticality", "Vendor Criticality", 1090, 24, 166, 42, 120),
        card("AR Outstanding", "AR Outstanding", 24, 92, 190, 88, 200),
        card("Overdue AR", "Overdue AR", 224, 92, 190, 88, 210),
        card("Overdue AR %", "Overdue AR %", 424, 92, 190, 88, 220),
        card("AP Outstanding", "AP Outstanding", 624, 92, 190, 88, 230),
        card("DSO", "DSO", 824, 92, 190, 88, 240),
        card("Cash Conversion Cycle", "Cash Conversion", 1024, 92, 232, 88, 250),
        data_visual(
            "barChart",
            24,
            204,
            390,
            236,
            300,
            {"Category": [("FactARInvoice", "aging_bucket", "column", "Aging Bucket")], "Y": [("KPI Measures", "AR Outstanding", "measure", "AR Outstanding")]},
            "AR aging exposure",
        ),
        data_visual(
            "barChart",
            426,
            204,
            390,
            236,
            310,
            {"Category": [("FactAPInvoice", "due_window", "column", "Due Window")], "Y": [("KPI Measures", "AP Outstanding", "measure", "AP Outstanding")]},
            "AP due schedule",
        ),
        data_visual(
            "columnChart",
            828,
            204,
            428,
            236,
            320,
            {"Category": [("DimDate", "month_label", "column", "Month")], "Y": [("KPI Measures", "DSO", "measure", "DSO"), ("KPI Measures", "DPO", "measure", "DPO")]},
            "DSO and DPO trend",
        ),
        data_visual(
            "barChart",
            24,
            462,
            610,
            176,
            330,
            {"Category": [("DimCustomer", "risk_rating", "column", "Risk")], "Y": [("KPI Measures", "Overdue AR", "measure", "Overdue AR")]},
            "Collection focus customers",
        ),
        data_visual(
            "barChart",
            646,
            462,
            610,
            176,
            340,
            {"Category": [("DimVendor", "criticality", "column", "Criticality")], "Y": [("KPI Measures", "AP Due 14 Days", "measure", "Due 14 Days")]},
            "Payment planning vendors",
        ),
    ]

    p3 = header("Forecast, FX & Risk", "13-week cash forecast, unhedged FX, debt maturity, and exception actioning")
    p3 += [
        slicer("DimEntity", "region", "Region", 784, 24, 128, 42, 100),
        slicer("DimScenario", "scenario", "Scenario", 922, 24, 158, 42, 110),
        slicer("FactFXExposure", "exposure_currency", "Currency", 1090, 24, 166, 42, 120),
        card("Forecast Closing Cash", "Closing Cash", 24, 92, 190, 88, 200),
        card("Forecast Receipts", "Forecast Receipts", 224, 92, 190, 88, 210),
        card("Forecast Payments", "Forecast Payments", 424, 92, 190, 88, 220),
        card("FX Net Exposure", "FX Net Exposure", 624, 92, 190, 88, 230),
        card("Unhedged FX %", "Unhedged FX %", 824, 92, 190, 88, 240),
        card("Open Risk Count", "Open Risks", 1024, 92, 232, 88, 250),
        data_visual(
            "waterfallChart",
            24,
            204,
            610,
            236,
            300,
            {"Category": [("DimWeek", "week_label", "column", "Week")], "Y": [("KPI Measures", "Forecast Net Cash Flow", "measure", "Net Flow")]},
            "13-week cash movement walk",
            "Net flow by week for selected scenario",
        ),
        data_visual(
            "barChart",
            646,
            204,
            300,
            236,
            310,
            {"Category": [("FactFXExposure", "exposure_currency", "column", "Currency")], "Y": [("KPI Measures", "Unhedged FX Exposure", "measure", "Unhedged Exposure")]},
            "Unhedged FX by currency",
        ),
        data_visual(
            "barChart",
            958,
            204,
            298,
            236,
            320,
            {"Category": [("FactTreasuryRiskAction", "risk_level", "column", "Level")], "Y": [("KPI Measures", "Open Risk Value", "measure", "Open Risk Value")]},
            "Risk value by level",
        ),
        data_visual(
            "barChart",
            24,
            462,
            610,
            176,
            330,
            {"Category": [("FactLiquidityFacility", "facility_type", "column", "Facility")], "Y": [("KPI Measures", "Credit Available", "measure", "Credit Available")]},
            "Debt and facility maturity",
        ),
        data_visual(
            "barChart",
            646,
            462,
            610,
            176,
            340,
            {"Category": [("FactTreasuryRiskAction", "owner_team", "column", "Owner")], "Y": [("KPI Measures", "Open Risk Value", "measure", "Open Risk Value")]},
            "Treasury exception queue",
        ),
    ]

    layout["sections"] = [
        section("TreasuryCommandCenter", "Treasury Command Center", 0, p1),
        section("WorkingCapitalControl", "Working Capital Control", 1, p2),
        section("ForecastFxRisk", "Forecast, FX & Risk", 2, p3),
    ]
    return layout


def write_native_scripts() -> None:
    (ROOT / "powerbi").mkdir(parents=True, exist_ok=True)
    (ROOT / "qa").mkdir(parents=True, exist_ok=True)

    (ROOT / "powerbi" / "prepare_seed_pbix.ps1").write_text(f"""param(
  [string]$SeedTemplate = "{SEED_TEMPLATE}",
  [string]$TargetPbix = "{ROOT / 'output' / 'dashboard_model_seed_ch07.pbix'}"
)

$ErrorActionPreference = "Stop"
if (!(Test-Path -LiteralPath $SeedTemplate)) {{ throw "Seed template not found: $SeedTemplate" }}
New-Item -ItemType Directory -Force -Path (Split-Path -Parent $TargetPbix) | Out-Null
Copy-Item -LiteralPath $SeedTemplate -Destination $TargetPbix -Force
[Reflection.Assembly]::LoadFrom("C:\\Program Files\\Microsoft Power BI Desktop\\bin\\Microsoft.PowerBI.Packaging.dll") | Out-Null
$stream = [IO.File]::OpenRead($TargetPbix)
try {{ [Microsoft.PowerBI.Packaging.PowerBIPackager]::Validate($stream) }} finally {{ $stream.Dispose() }}
[ordered]@{{
  status = "seed_copied"
  seed_template = $SeedTemplate
  target_pbix = $TargetPbix
  target_bytes = (Get-Item -LiteralPath $TargetPbix).Length
}} | ConvertTo-Json -Depth 5
""", encoding="utf-8")

    (ROOT / "powerbi" / "push_model_bim_to_desktop.ps1").write_text(r"""param(
  [string]$ProjectRoot = "",
  [string]$TargetPbix = "",
  [string]$ModelBim = ""
)

$ErrorActionPreference = "Stop"
if ([string]::IsNullOrWhiteSpace($ProjectRoot)) { $ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..") }
if ([string]::IsNullOrWhiteSpace($TargetPbix)) { $TargetPbix = Join-Path $ProjectRoot "output\dashboard_model_seed_ch07.pbix" }
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
    $info.pbiSessions | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $QaRoot "seed_pbi_sessions_debug.json") -Encoding UTF8
    throw "Expected exactly one Power BI Desktop session for '$resolved'. Found $($matches.Count)."
  }
  return $matches[0]
}

function Convert-DataType([string]$TypeName) {
  switch ($TypeName) {
    "string" { return [Microsoft.AnalysisServices.Tabular.DataType]::String }
    "int64" { return [Microsoft.AnalysisServices.Tabular.DataType]::Int64 }
    "double" { return [Microsoft.AnalysisServices.Tabular.DataType]::Double }
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
  status = "project14_model_pushed_via_tom"
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
""", encoding="utf-8")

    (ROOT / "powerbi" / "apply_native_layout_to_pbix.ps1").write_text(r"""param(
  [string]$ProjectRoot = "",
  [string]$ModelPbix = "",
  [string]$LayoutJson = "",
  [string]$OutputPbix = "",
  [string]$FinalPbix = ""
)

$ErrorActionPreference = "Stop"
if ([string]::IsNullOrWhiteSpace($ProjectRoot)) { $ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..") }
if ([string]::IsNullOrWhiteSpace($ModelPbix)) { $ModelPbix = Join-Path $ProjectRoot "output\dashboard_model_seed_ch07.pbix" }
if ([string]::IsNullOrWhiteSpace($LayoutJson)) { $LayoutJson = Join-Path $ProjectRoot "build\native_report_layout_project14.json" }
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
""", encoding="utf-8")


def main() -> None:
    MODEL_BIM.parent.mkdir(parents=True, exist_ok=True)
    LAYOUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    MODEL_BIM.write_text(json.dumps(build_model_bim(), indent=2), encoding="utf-8")
    LAYOUT_JSON.write_text(json.dumps(build_layout(), ensure_ascii=False, indent=2), encoding="utf-8")
    write_native_scripts()
    summary = {
        "status": "native_assets_created",
        "model_bim": str(MODEL_BIM),
        "layout_json": str(LAYOUT_JSON),
        "seed_template": str(SEED_TEMPLATE),
        "pages": [section["displayName"] for section in json.loads(LAYOUT_JSON.read_text(encoding="utf-8"))["sections"]],
    }
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
