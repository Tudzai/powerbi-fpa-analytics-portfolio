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
KPI_RESOURCE_DIR = ROOT / "assets" / "kpi_cards_project20_upgrade"


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
MEASURE_TABLE = "KPI_Measures"


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


def model_measure(item: dict) -> dict:
    result = {
        "name": item["measure_name"],
        "expression": item["dax"],
        "formatString": item.get("format_string", ""),
        "description": item.get("definition", ""),
    }
    if item.get("data_type"):
        result["dataType"] = item["data_type"]
    if item.get("data_category"):
        result["dataCategory"] = item["data_category"]
    return result


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
            "name": MEASURE_TABLE,
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
                    "name": f"{MEASURE_TABLE}-Import",
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
            "measures": [model_measure(item) for item in measure_catalog()],
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


def measure_format(measure_name: str) -> str:
    for item in measure_catalog():
        if item["measure_name"] == measure_name:
            return item.get("format_string", "")
    return ""


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
    measure_names = [field for _table, field, role, _ in fields if role == "measure"]
    formats = [measure_format(name) for name in measure_names]
    display_units = "1000000D" if formats and all("$" in fmt for fmt in formats if fmt) else "0D"
    objects = {
        "valueAxis": [{"properties": {"showAxisTitle": lit("false"), "gridlineShow": lit("false"), "gridlineColor": color(THEME["grid"]), "labelColor": color(THEME["muted"]), "fontSize": lit("8.0D"), "labelDisplayUnits": lit(display_units)}}],
        "categoryAxis": [{"properties": {"showAxisTitle": lit("false"), "gridlineShow": lit("false"), "concatenateLabels": lit("false"), "labelColor": color(THEME["muted"]), "fontSize": lit("8.0D")}}],
        "legend": [{"properties": {"showTitle": lit("false"), "position": prop_text("Top"), "fontColor": color(THEME["muted"]), "fontSize": lit("8.0D")}}],
        "labels": [{"properties": {"show": lit("false"), "fontColor": color(THEME["text"]), "labelColor": color(THEME["text"]), "labelDisplayUnits": lit(display_units)}}],
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


def table_image_objects(image_w: int, image_h: int, surface_color: str, qref: str) -> dict:
    return {
        "grid": [
            {
                "properties": {
                    "gridHorizontal": lit("false"),
                    "gridVertical": lit("false"),
                    "outlineColor": color(surface_color),
                    "rowPadding": lit("0L"),
                    "imageWidth": lit(f"{image_w}L"),
                    "imageHeight": lit(f"{image_h}L"),
                }
            }
        ],
        "columnHeaders": [
            {
                "properties": {
                    "show": lit("false"),
                    "fontSize": lit("1.0D"),
                    "fontColor": color(surface_color),
                }
            }
        ],
        "values": [
            {
                "properties": {
                    "fontSize": lit("1.0D"),
                    "fontColor": color(surface_color),
                    "urlIcon": lit("false"),
                    "imageWidth": lit(f"{image_w}L"),
                    "imageHeight": lit(f"{image_h}L"),
                    "backColor": color(surface_color),
                    "backColorPrimary": color(surface_color),
                    "backColorSecondary": color(surface_color),
                }
            }
        ],
        "imageSize": [
            {
                "properties": {
                    "height": lit(f"{image_h}L"),
                    "width": lit(f"{image_w}L"),
                }
            }
        ],
        "columnWidth": [
            {
                "properties": {"value": lit(f"{image_w}D")},
                "selector": {"metadata": qref},
            }
        ],
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


def single_measure_query(table: str, measure: str, display: str, alias: str, qref: str) -> dict:
    return {
        "Commands": [
            {
                "SemanticQueryDataShapeCommand": {
                    "Query": {
                        "Version": 2,
                        "From": [{"Name": alias, "Entity": table, "Type": 0}],
                        "Select": [ref(table, measure, "measure", alias, display)],
                    },
                    "Binding": {"Primary": {"Groupings": [{"Projections": [0]}]}},
                    "DataReduction": {"DataVolume": 4, "Primary": {"Window": {"Count": 1000}}},
                    "Version": 1,
                },
                "ExecutionMetricsKind": 1,
            }
        ]
    }


def single_measure_transforms(objects: dict, measure: str, display: str, alias: str, qref: str) -> dict:
    return {
        "objects": objects,
        "projectionOrdering": {"Values": [0]},
        "queryMetadata": {"Select": [{"Restatement": display, "Name": qref, "Type": 2048}]},
        "visualElements": [{"DataRoles": [{"Name": "Values", "Projection": 0, "isActive": False}]}],
        "selects": [
            {
                "displayName": display,
                "queryName": qref,
                "roles": {"Values": True},
                "type": {"category": None, "underlyingType": 1},
                "expr": {"Measure": {"Expression": {"SourceRef": {"Entity": alias}}, "Property": measure}},
            }
        ],
    }


def card(measure: str, title: str, x, y, w, h, z) -> dict:
    visual = data_visual("cardVisual", x, y, w, h, z, {"Data": [(MEASURE_TABLE, measure, "measure", title)]}, title)
    cfg = json.loads(visual["config"])
    metadata = f"{MEASURE_TABLE}.{measure}"
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


def svg_measure(measure: str, x, y, w, h, z, image_w: int, image_h: int, display: str | None = None) -> dict:
    display = display or measure.replace(" KPI Card SVG", "").replace(" SVG", "")
    qref = f"{MEASURE_TABLE}.{measure}"
    alias = "k"
    surface_color = THEME["ink"] if measure == "Current Lens SVG" else THEME["bg"]
    if measure.endswith("Decision Chips SVG"):
        image_w = max(20, min(int(image_w), int(w) - 44))
        image_h = max(20, min(int(image_h), 32))
    elif measure == "Current Lens SVG":
        image_w = max(20, min(int(image_w), int(w) - 4))
        image_h = max(20, min(int(image_h), int(h) - 4))
    elif measure.endswith("KPI Card SVG"):
        image_w = max(20, int(w) - 6)
        image_h = max(20, int(h) - 6)
    visual = data_visual("tableEx", x, y, w, h, z, {"Values": [(MEASURE_TABLE, measure, "measure", display)]}, "")
    cfg = json.loads(visual["config"])
    cfg["singleVisual"]["columnProperties"] = {qref: {"displayName": display}}
    objects = table_image_objects(image_w, image_h, surface_color, qref)
    cfg["singleVisual"]["objects"] = objects
    cfg["singleVisual"]["vcObjects"] = {
        "background": [{"properties": {"show": lit("false")}}],
        "border": [{"properties": {"show": lit("false")}}],
        "dropShadow": [{"properties": {"show": lit("false")}}],
        "title": [{"properties": {"show": lit("false")}}],
        "visualHeader": [{"properties": {"show": lit("false")}}],
        "visualTooltip": [{"properties": {"show": lit("false")}}],
    }
    visual["config"] = json.dumps(cfg, separators=(",", ":"), ensure_ascii=False)
    visual["query"] = json.dumps(single_measure_query(MEASURE_TABLE, measure, display, alias, qref), separators=(",", ":"), ensure_ascii=False)
    visual["dataTransforms"] = json.dumps(single_measure_transforms(objects, measure, display, alias, qref), separators=(",", ":"), ensure_ascii=False)
    return visual


KPI_IMAGE_DATA = {
    "Available Liquidity KPI Card SVG": ("Liquidity", "$92.5M", "PY $92.5M", "Delta 0.0%", THEME["teal"], "flat"),
    "Liquidity Headroom KPI Card SVG": ("Headroom", "$82.3M", "PY $82.3M", "Delta 0.0%", THEME["blue"], "flat"),
    "Forecast Net Flow KPI Card SVG": ("13W Net Flow", "($2.9M)", "PY ($3.4M)", "Delta +14.5%", THEME["gold"], "up"),
    "Cash Runway KPI Card SVG": ("Runway", "19.4w", "PY 18.9w", "Delta +0.5w", THEME["green"], "up"),
    "AR Outstanding KPI Card SVG": ("AR Balance", "$58.4M", "PY $61.2M", "Delta -4.6%", THEME["blue"], "down_good"),
    "Overdue AR KPI Card SVG": ("Overdue AR", "19.7%", "PY 22.4%", "Delta -2.7pt", THEME["rose"], "down_good"),
    "AP Due 14 Days KPI Card SVG": ("AP 14d", "$11.8M", "PY $10.6M", "Delta +11.3%", THEME["gold"], "up_bad"),
    "Cash Conversion KPI Card SVG": ("CCC", "42d", "PY 45d", "Delta -3d", THEME["green"], "down_good"),
    "Forecast Closing Cash KPI Card SVG": ("Closing Cash", "$172.9M", "PY $175.8M", "Delta -1.7%", THEME["teal"], "down"),
    "Forecast Error KPI Card SVG": ("Fcst Error", "22.1%", "PY 22.1%", "Delta 0.0pt", THEME["rose"], "flat"),
    "Unhedged FX KPI Card SVG": ("Unhedged FX", "54.8%", "PY 54.8%", "Delta 0.0pt", THEME["gold"], "flat"),
    "Open Risk KPI Card SVG": ("Open Risks", "24", "PY 26", "Delta -2", THEME["rose"], "down_good"),
}


def static_kpi_svg(title: str, value: str, prior: str, delta: str, accent: str, trend: str) -> str:
    trend_color = THEME["rose"] if trend in {"down", "up_bad"} else THEME["teal"]
    delta_color = THEME["rose"] if trend in {"down", "up_bad"} else THEME["teal"]
    if trend == "flat":
        points = "138,74 160,74 182,74 204,74 226,74"
    elif trend.startswith("down"):
        points = "138,48 160,54 182,62 204,72 226,86"
    else:
        points = "138,86 160,76 182,66 204,56 226,48"
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="252" height="158" viewBox="0 0 252 158">
<rect x="1" y="1" width="250" height="156" rx="10" fill="#FFFFFF" stroke="#D8E0E7" stroke-width="1.2"/>
<rect x="12" y="11" width="228" height="4" rx="2" fill="{accent}"/>
<rect x="14" y="30" width="12" height="12" rx="3" fill="{accent}"/>
<text x="34" y="41" font-family="Segoe UI Semibold" font-size="12.5" fill="#15202B">{title}</text>
<text x="14" y="82" font-family="Segoe UI Semibold" font-size="25" fill="{accent}">{value}</text>
<rect x="130" y="32" width="108" height="74" rx="8" fill="#F3F6F8"/>
<rect x="136" y="67" width="92" height="12" rx="6" fill="#E6F4EC"/>
<line x1="136" y1="73" x2="228" y2="73" stroke="#AAB7C4" stroke-width="1" stroke-dasharray="4 5"/>
<polyline points="{points}" fill="none" stroke="{trend_color}" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>
<circle cx="138" cy="{points.split()[0].split(',')[1]}" r="3.6" fill="#FFFFFF" stroke="#607081" stroke-width="1.4"/>
<circle cx="226" cy="{points.split()[-1].split(',')[1]}" r="4.8" fill="{trend_color}" stroke="#FFFFFF" stroke-width="1.8"/>
<rect x="14" y="126" width="98" height="20" rx="6" fill="#F8FAFB"/>
<rect x="120" y="126" width="118" height="20" rx="6" fill="#F8FAFB"/>
<text x="22" y="140" font-family="Segoe UI" font-size="9.4" fill="#607081">{prior}</text>
<text x="130" y="140" font-family="Segoe UI Semibold" font-size="9.4" fill="{delta_color}">{delta}</text>
</svg>"""
    return svg


def kpi_resource_name(measure: str) -> str:
    safe = measure.lower().replace(" ", "_").replace("%", "pct")
    safe = "".join(ch if ch.isalnum() or ch == "_" else "_" for ch in safe)
    return f"project14_{safe}.svg"


def write_kpi_resources() -> None:
    KPI_RESOURCE_DIR.mkdir(parents=True, exist_ok=True)
    for measure, (title, value, prior, delta, accent, trend) in KPI_IMAGE_DATA.items():
        svg = static_kpi_svg(title, value, prior, delta, accent, trend)
        (KPI_RESOURCE_DIR / kpi_resource_name(measure)).write_text(svg, encoding="utf-8")


def kpi_image(measure: str, x, y, w, h, z) -> dict:
    item_name = kpi_resource_name(measure)
    cfg = {
        "name": rand_name(),
        "layouts": [{"id": 0, "position": pos(x, y, w, h, z)}],
        "singleVisual": {
            "visualType": "image",
            "objects": {
                "general": [
                    {
                        "properties": {
                            "image": {
                                "image": {
                                    "name": prop_text(measure),
                                    "url": {
                                        "expr": {
                                            "ResourcePackageItem": {
                                                "PackageName": "RegisteredResources",
                                                "PackageType": 1,
                                                "ItemName": item_name,
                                            }
                                        }
                                    },
                                    "scaling": prop_text("Fit"),
                                }
                            }
                        }
                    }
                ]
            },
            "drillFilterOtherVisuals": True,
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
                "fill": [{"properties": {"show": lit("false")}}],
                "outline": [{"properties": {"show": lit("false")}}],
            },
            "vcObjects": {
                "title": [{"properties": {"show": lit("false")}}],
                "subTitle": [{"properties": {"show": lit("false")}}],
                "background": [{"properties": {"show": lit("true"), "color": color(fill), "transparency": lit("0D")}}],
                "border": [{"properties": {"show": lit("false")}}],
                "visualHeader": [{"properties": {"show": lit("false")}}],
            },
        },
    }
    return outer(cfg, x, y, w, h, z)


def kpi_tile(measure: str, x, y, w, h, z) -> list[dict]:
    title, value, prior, delta, accent, trend = KPI_IMAGE_DATA[measure]
    trend_color = THEME["rose"] if trend in {"down", "up_bad"} else THEME["teal"]
    delta_color = THEME["rose"] if trend in {"down", "up_bad"} else THEME["teal"]
    if trend == "flat":
        bar_heights = [12, 12, 12, 12, 12]
    elif trend.startswith("down"):
        bar_heights = [42, 34, 27, 21, 16]
    else:
        bar_heights = [16, 21, 27, 34, 42]

    visuals: list[dict] = [
        shape(x, y, w, h, z, THEME["border"]),
        shape(x + 1, y + 1, w - 2, h - 2, z + 1, "#FFFFFF"),
        shape(x + 12, y + 11, w - 24, 4, z + 2, accent),
        shape(x + 14, y + 30, 12, 12, z + 3, accent),
        text_box(title, x + 34, y + 26, 100, 22, z + 4, 8.8, THEME["text"], True),
        text_box(value, x + 14, y + 55, 112, 36, z + 5, 19.2, accent, True),
        shape(x + 142, y + 32, 96, 74, z + 6, THEME["panel2"]),
        shape(x + 148, y + 73, 78, 1.5, z + 7, THEME["border"]),
    ]
    for idx, bar_height in enumerate(bar_heights):
        visuals.append(shape(x + 154 + idx * 14, y + 88 - bar_height, 8, bar_height, z + 8 + idx, trend_color))
    visuals += [
        shape(x + 14, y + 126, 98, 20, z + 20, THEME["panel2"]),
        shape(x + 120, y + 126, 118, 20, z + 21, THEME["panel2"]),
        text_box(prior, x + 22, y + 128, 82, 16, z + 22, 6.8, THEME["muted"], False),
        text_box(delta, x + 130, y + 128, 98, 16, z + 23, 6.8, delta_color, True),
    ]
    return visuals


PAGES = [
    ("Treasury Command Center", "Liquidity control"),
    ("Working Capital Control", "AR AP execution"),
    ("Forecast, FX & Risk", "Forecast risk"),
]


def nav_items(active_page: str, z: int = 20) -> list[dict]:
    visuals: list[dict] = []
    y = 126
    for idx, (page, short_label) in enumerate(PAGES):
        is_active = page == active_page
        fill = THEME["teal"] if is_active else "#1C3B45"
        fg = "#FFFFFF" if is_active else "#B8C8CF"
        visuals.append(shape(22, y + idx * 42, 140, 30, z + idx * 2, fill))
        visuals.append(text_box(short_label, 34, y + 7 + idx * 42, 116, 15, z + idx * 2 + 1, 7.8, fg, True))
    return visuals


def sidebar(active_page: str, lens_y: int, slicers: list[tuple[str, str, str, int]]) -> list[dict]:
    visuals: list[dict] = [
        shape(0, 0, 184, 720, 1, THEME["ink"]),
        shape(18, 24, 8, 44, 2, THEME["teal"]),
        text_box("TWC", 34, 22, 90, 24, 3, 14, "#FFFFFF", True),
        text_box("Treasury lens", 34, 48, 112, 16, 4, 8, "#9ACBC6", False),
        shape(22, 82, 140, 1.5, 5, "#435866"),
        text_box("PAGES", 24, 96, 120, 14, 6, 7.2, "#9ACBC6", False),
    ]
    visuals += nav_items(active_page, 20)
    visuals.append(text_box("GLOBAL LENS", 24, 250, 120, 14, 50, 7.2, "#9ACBC6", False))
    for table, field, title, y in slicers:
        visuals.append(slicer(table, field, title, 24, y, 136, 38, 70 + y))
    visuals.append(text_box("CURRENT LENS", 24, lens_y - 20, 120, 14, 150, 7.2, "#9ACBC6", False))
    visuals.append(svg_measure("Current Lens SVG", 22, lens_y, 144, 76, 160, 144, 76))
    visuals.append(shape(22, 664, 140, 1.5, 170, "#435866"))
    visuals.append(text_box("Synthetic demo data", 24, 676, 122, 14, 180, 7, "#B8C8CF", False))
    visuals.append(text_box("Seed 14042", 24, 692, 122, 14, 181, 7, "#9ACBC6", False))
    return visuals


def header(title: str, subtitle: str, chip_measure: str) -> list[dict]:
    return [
        text_box("TREASURY WORKING CAPITAL", 204, 24, 260, 18, 200, 7.5, THEME["teal"], False),
        text_box(title, 204, 39, 470, 34, 210, 15, THEME["text"]),
        text_box(subtitle, 204, 70, 450, 18, 220, 8, THEME["muted"], False),
        svg_measure(chip_measure, 766, 35, 490, 38, 230, 490, 38),
        shape(204, 88, 1052, 2, 240, THEME["border"]),
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


def register_kpi_resource_items(layout: dict) -> None:
    packages = layout.setdefault("resourcePackages", [])
    registered = None
    for package in packages:
        resource_package = package.get("resourcePackage", {})
        if resource_package.get("name") == "RegisteredResources":
            registered = resource_package
            break
    if registered is None:
        registered = {"name": "RegisteredResources", "type": 1, "items": [], "disabled": False}
        packages.append({"resourcePackage": registered})

    items = registered.setdefault("items", [])
    existing = {item.get("name") for item in items}
    for measure in KPI_IMAGE_DATA:
        item_name = kpi_resource_name(measure)
        if item_name in existing:
            continue
        items.append({"type": 100, "path": item_name, "name": item_name})


def build_layout() -> dict:
    random.seed(14042)
    layout = blank_layout()

    kx = [204, 471, 738, 1005]
    ky, kw, kh = 104, 255, 164
    top_y, top_h = 284, 172
    bot_y, bot_h = 480, 166

    p1 = sidebar(
        "Treasury Command Center",
        514,
        [
            ("DimEntity", "region", "Region", 274),
            ("DimEntity", "entity", "Entity", 326),
            ("DimScenario", "scenario", "Scenario", 378),
            ("DimWeek", "week_label", "Forecast Week", 430),
        ],
    )
    p1 += header("Treasury Command Center", "Liquidity, runway, scenario forecast, and action queue", "Treasury Decision Chips SVG")
    p1 += [
        svg_measure("Available Liquidity KPI Card SVG", kx[0], ky, kw, kh, 300, 252, 158, "Liquidity KPI Card"),
        svg_measure("Liquidity Headroom KPI Card SVG", kx[1], ky, kw, kh, 310, 252, 158, "Headroom KPI Card"),
        svg_measure("Forecast Net Flow KPI Card SVG", kx[2], ky, kw, kh, 320, 252, 158, "Net Flow KPI Card"),
        svg_measure("Cash Runway KPI Card SVG", kx[3], ky, kw, kh, 330, 252, 158, "Runway KPI Card"),
        data_visual(
            "columnChart",
            204,
            top_y,
            426,
            top_h,
            400,
            {"Category": [("DimWeek", "week_label", "column", "Week")], "Y": [(MEASURE_TABLE, "Forecast Net Cash Flow", "measure", "Net Cash Flow")]},
            "13-week net cash flow",
            "Drilldown: Forecast week",
        ),
        data_visual(
            "barChart",
            642,
            top_y,
            304,
            top_h,
            410,
            {"Category": [("DimEntity", "region", "column", "Region")], "Y": [(MEASURE_TABLE, "Available Liquidity", "measure", "Available Liquidity")]},
            "Liquidity by region",
            "Drilldown: Region",
        ),
        data_visual(
            "barChart",
            966,
            top_y,
            290,
            top_h,
            420,
            {"Category": [("DimBank", "bank", "column", "Bank")], "Y": [(MEASURE_TABLE, "Available Cash", "measure", "Available Cash")]},
            "Cash by bank",
            "Drilldown: Bank",
        ),
        data_visual(
            "barChart",
            204,
            bot_y,
            332,
            bot_h,
            430,
            {"Category": [("FactTreasuryRiskAction", "risk_type", "column", "Risk")], "Y": [(MEASURE_TABLE, "Open Risk Value", "measure", "Open Risk Value")]},
            "Management action queue",
            "Drilldown: Risk type",
        ),
        data_visual(
            "barChart",
            548,
            bot_y,
            332,
            bot_h,
            440,
            {"Category": [("DimEntity", "country", "column", "Country")], "Y": [(MEASURE_TABLE, "Liquidity Headroom", "measure", "Headroom")]},
            "Treasury operating snapshot",
            "Drilldown: Country",
        ),
        data_visual(
            "tableEx",
            892,
            bot_y,
            364,
            bot_h,
            450,
            {
                "Values": [
                    ("FactTreasuryRiskAction", "risk_type", "column", "Risk"),
                    ("FactTreasuryRiskAction", "owner_team", "column", "Owner"),
                    ("FactTreasuryRiskAction", "status", "column", "Status"),
                    (MEASURE_TABLE, "Open Risk Value", "measure", "Open Value"),
                ]
            },
            "Action detail",
            "Drilldown: Risk > owner",
        ),
    ]

    p2 = sidebar(
        "Working Capital Control",
        514,
        [
            ("DimEntity", "region", "Region", 274),
            ("DimEntity", "entity", "Entity", 326),
            ("DimCustomer", "risk_rating", "Customer Risk", 378),
            ("DimVendor", "criticality", "Vendor Criticality", 430),
        ],
    )
    p2 += header("Working Capital Control", "AR/AP aging, DSO/DPO, and collection-payment focus", "Working Capital Decision Chips SVG")
    p2 += [
        svg_measure("AR Outstanding KPI Card SVG", kx[0], ky, kw, kh, 300, 252, 158, "AR KPI Card"),
        svg_measure("Overdue AR KPI Card SVG", kx[1], ky, kw, kh, 310, 252, 158, "Overdue KPI Card"),
        svg_measure("AP Due 14 Days KPI Card SVG", kx[2], ky, kw, kh, 320, 252, 158, "AP 14d KPI Card"),
        svg_measure("Cash Conversion KPI Card SVG", kx[3], ky, kw, kh, 330, 252, 158, "CCC KPI Card"),
        data_visual(
            "barChart",
            204,
            top_y,
            426,
            top_h,
            400,
            {"Category": [("FactARInvoice", "aging_bucket", "column", "Aging Bucket")], "Y": [(MEASURE_TABLE, "AR Outstanding", "measure", "AR Outstanding")]},
            "AR aging exposure",
            "Drilldown: Aging bucket",
        ),
        data_visual(
            "barChart",
            642,
            top_y,
            304,
            top_h,
            410,
            {"Category": [("FactAPInvoice", "due_window", "column", "Due Window")], "Y": [(MEASURE_TABLE, "AP Outstanding", "measure", "AP Outstanding")]},
            "AP due schedule",
            "Drilldown: Due window",
        ),
        data_visual(
            "columnChart",
            966,
            top_y,
            290,
            top_h,
            420,
            {"Category": [("DimDate", "month_label", "column", "Month")], "Y": [(MEASURE_TABLE, "DSO", "measure", "DSO"), (MEASURE_TABLE, "DPO", "measure", "DPO")]},
            "DSO and DPO trend",
            "Drilldown: Month",
        ),
        data_visual(
            "barChart",
            204,
            bot_y,
            332,
            bot_h,
            430,
            {"Category": [("DimCustomer", "risk_rating", "column", "Risk")], "Y": [(MEASURE_TABLE, "Overdue AR", "measure", "Overdue AR")]},
            "Collection focus customers",
            "Drilldown: Customer risk",
        ),
        data_visual(
            "barChart",
            548,
            bot_y,
            332,
            bot_h,
            440,
            {"Category": [("DimVendor", "criticality", "column", "Criticality")], "Y": [(MEASURE_TABLE, "AP Due 14 Days", "measure", "Due 14 Days")]},
            "Payment planning vendors",
            "Drilldown: Vendor criticality",
        ),
        data_visual(
            "tableEx",
            892,
            bot_y,
            364,
            bot_h,
            450,
            {
                "Values": [
                    ("FactARInvoice", "aging_bucket", "column", "Aging"),
                    ("DimCustomer", "risk_rating", "column", "Risk"),
                    ("FactARInvoice", "is_overdue", "column", "Overdue"),
                    (MEASURE_TABLE, "AR Outstanding", "measure", "AR"),
                    (MEASURE_TABLE, "Overdue AR", "measure", "Overdue AR"),
                ]
            },
            "Execution detail",
            "Drilldown: Customer AR status",
        ),
    ]

    p3 = sidebar(
        "Forecast, FX & Risk",
        514,
        [
            ("DimEntity", "region", "Region", 274),
            ("DimEntity", "entity", "Entity", 326),
            ("DimScenario", "scenario", "Scenario", 378),
            ("FactFXExposure", "exposure_currency", "Currency", 430),
        ],
    )
    p3 += header("Forecast, FX & Risk", "13-week cash forecast, unhedged FX, debt maturity, and exception actioning", "Risk Decision Chips SVG")
    p3 += [
        svg_measure("Forecast Closing Cash KPI Card SVG", kx[0], ky, kw, kh, 300, 252, 158, "Closing Cash KPI Card"),
        svg_measure("Forecast Error KPI Card SVG", kx[1], ky, kw, kh, 310, 252, 158, "Forecast Error KPI Card"),
        svg_measure("Unhedged FX KPI Card SVG", kx[2], ky, kw, kh, 320, 252, 158, "Unhedged FX KPI Card"),
        svg_measure("Open Risk KPI Card SVG", kx[3], ky, kw, kh, 330, 252, 158, "Open Risk KPI Card"),
        data_visual(
            "waterfallChart",
            204,
            top_y,
            426,
            top_h,
            400,
            {"Category": [("DimWeek", "week_label", "column", "Week")], "Y": [(MEASURE_TABLE, "Forecast Net Cash Flow", "measure", "Net Flow")]},
            "13-week cash movement walk",
            "Drilldown: Forecast week",
        ),
        data_visual(
            "barChart",
            642,
            top_y,
            304,
            top_h,
            410,
            {"Category": [("FactFXExposure", "exposure_currency", "column", "Currency")], "Y": [(MEASURE_TABLE, "Unhedged FX Exposure", "measure", "Unhedged Exposure")]},
            "Unhedged FX by currency",
            "Drilldown: Currency",
        ),
        data_visual(
            "barChart",
            966,
            top_y,
            290,
            top_h,
            420,
            {"Category": [("FactTreasuryRiskAction", "risk_level", "column", "Level")], "Y": [(MEASURE_TABLE, "Open Risk Value", "measure", "Open Risk Value")]},
            "Risk value by level",
            "Drilldown: Risk level",
        ),
        data_visual(
            "barChart",
            204,
            bot_y,
            332,
            bot_h,
            430,
            {"Category": [("FactLiquidityFacility", "facility_type", "column", "Facility")], "Y": [(MEASURE_TABLE, "Credit Available", "measure", "Credit Available")]},
            "Debt and facility maturity",
            "Drilldown: Facility",
        ),
        data_visual(
            "barChart",
            548,
            bot_y,
            332,
            bot_h,
            440,
            {"Category": [("FactTreasuryRiskAction", "owner_team", "column", "Owner")], "Y": [(MEASURE_TABLE, "Open Risk Value", "measure", "Open Risk Value")]},
            "Treasury exception queue",
            "Drilldown: Owner",
        ),
        data_visual(
            "tableEx",
            892,
            bot_y,
            364,
            bot_h,
            450,
            {
                "Values": [
                    ("FactTreasuryRiskAction", "risk_level", "column", "Level"),
                    ("FactTreasuryRiskAction", "owner_team", "column", "Owner"),
                    ("FactTreasuryRiskAction", "status", "column", "Status"),
                    (MEASURE_TABLE, "Open Risk Value", "measure", "Open Value"),
                ]
            },
            "Risk actions",
            "Drilldown: Severity > owner",
        ),
    ]

    layout["sections"] = [
        section("TreasuryCommandCenter", "Treasury Command Center", 0, p1),
        section("WorkingCapitalControl", "Working Capital Control", 1, p2),
        section("ForecastFxRisk", "Forecast, FX & Risk", 2, p3),
    ]
    register_kpi_resource_items(layout)
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
      if ($measureDef.dataCategory) { $measure.DataCategory = [string]$measureDef.dataCategory }
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
  [string]$ResourceDir = "",
  [string]$OutputPbix = "",
  [string]$FinalPbix = ""
)

$ErrorActionPreference = "Stop"
if ([string]::IsNullOrWhiteSpace($ProjectRoot)) { $ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..") }
if ([string]::IsNullOrWhiteSpace($ModelPbix)) { $ModelPbix = Join-Path $ProjectRoot "output\dashboard_model_seed_ch07.pbix" }
if ([string]::IsNullOrWhiteSpace($LayoutJson)) { $LayoutJson = Join-Path $ProjectRoot "build\native_report_layout_project14.json" }
if ([string]::IsNullOrWhiteSpace($ResourceDir)) { $ResourceDir = Join-Path $ProjectRoot "assets\kpi_cards_project20_upgrade" }
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
  if (Test-Path -LiteralPath $ResourceDir) {
    foreach ($file in Get-ChildItem -LiteralPath $ResourceDir -Filter "*.svg" -File) {
      $resourceUri = New-Object System.Uri(("/Report/StaticResources/RegisteredResources/{0}" -f $file.Name), [System.UriKind]::Relative)
      if ($package.PartExists($resourceUri)) { $package.DeletePart($resourceUri) }
      $resourcePart = $package.CreatePart($resourceUri, "image/svg+xml", [System.IO.Packaging.CompressionOption]::Normal)
      $source = [IO.File]::OpenRead($file.FullName)
      $target = $resourcePart.GetStream([IO.FileMode]::Create, [IO.FileAccess]::Write)
      try { $source.CopyTo($target) }
      finally {
        $target.Dispose()
        $source.Dispose()
      }
    }
  }
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
  resource_dir = $ResourceDir
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


def visual_config(visual: dict) -> dict:
    return json.loads(visual["config"])


def visual_query_refs(visual: dict) -> list[str]:
    cfg = visual_config(visual)
    refs: list[str] = []
    for bucket in cfg.get("singleVisual", {}).get("projections", {}).values():
        for item in bucket:
            if item.get("queryRef"):
                refs.append(item["queryRef"])
    return refs


def verify_project20_upgrade(layout: dict) -> dict:
    visual_type_counts: dict[str, int] = {}
    page_checks = []
    for section_data in layout["sections"]:
        visuals = section_data["visualContainers"]
        checks = {
            "page": section_data["displayName"],
            "dynamic_kpi_cards": [],
            "lens_count": 0,
            "decision_chip_count": 0,
            "slicer_count": 0,
            "top_chart_slots": [],
            "detail_tables": [],
        }
        for visual in visuals:
            cfg = visual_config(visual)
            vtype = cfg.get("singleVisual", {}).get("visualType")
            visual_type_counts[vtype] = visual_type_counts.get(vtype, 0) + 1
            refs = visual_query_refs(visual)
            position = visual.get("x"), visual.get("y"), visual.get("width"), visual.get("height")
            is_kpi_card = vtype == "tableEx" and any(ref.endswith("KPI Card SVG") for ref in refs)
            is_lens = f"{MEASURE_TABLE}.Current Lens SVG" in refs
            is_decision_chip = any(ref.endswith("Decision Chips SVG") for ref in refs)
            if vtype == "slicer":
                checks["slicer_count"] += 1
            if is_kpi_card and visual.get("y") == 104 and visual.get("width") == 255 and visual.get("height") == 164:
                checks["dynamic_kpi_cards"].append({"type": vtype, "refs": refs, "rect": position})
            elif is_lens:
                checks["lens_count"] += 1
            elif is_decision_chip:
                checks["decision_chip_count"] += 1
            elif vtype == "tableEx":
                checks["detail_tables"].append({"refs": refs, "rect": position})
            if vtype in {"barChart", "columnChart", "waterfallChart"} and 280 <= visual.get("y", 0) <= 295:
                checks["top_chart_slots"].append({"type": vtype, "rect": position})

        checks["kpi_slots_pass"] = len(checks["dynamic_kpi_cards"]) == 4
        checks["lens_pass"] = checks["lens_count"] == 1
        checks["decision_chips_pass"] = checks["decision_chip_count"] == 1
        checks["slicer_pass"] = checks["slicer_count"] == 4
        checks["top_chart_slots_pass"] = len(checks["top_chart_slots"]) == 3
        checks["detail_table_pass"] = len(checks["detail_tables"]) >= 1
        page_checks.append(checks)

    status = "pass" if all(
        item["kpi_slots_pass"]
        and item["lens_pass"]
        and item["decision_chips_pass"]
        and item["slicer_pass"]
        and item["top_chart_slots_pass"]
        and item["detail_table_pass"]
        for item in page_checks
    ) and visual_type_counts.get("cardVisual", 0) == 0 else "fail"

    return {
        "status": status,
        "checked_layout": str(LAYOUT_JSON),
        "quality_benchmark": "Project 20 v77-style direct layout verification adapted to Project 14 treasury palette",
        "visual_type_counts": visual_type_counts,
        "pages": page_checks,
        "checks": {
            "card_visual_removed": visual_type_counts.get("cardVisual", 0) == 0,
            "dynamic_svg_kpi_cards_per_page": "4",
            "current_lens_per_page": "1",
            "decision_chip_per_page": "1",
            "compact_slicers_per_page": "4",
            "top_chart_slots_per_page": "3",
        },
    }


def main() -> None:
    MODEL_BIM.parent.mkdir(parents=True, exist_ok=True)
    LAYOUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    write_kpi_resources()
    MODEL_BIM.write_text(json.dumps(build_model_bim(), indent=2), encoding="utf-8")
    layout = build_layout()
    LAYOUT_JSON.write_text(json.dumps(layout, ensure_ascii=False, indent=2), encoding="utf-8")
    write_native_scripts()
    verification = verify_project20_upgrade(layout)
    (ROOT / "qa").mkdir(parents=True, exist_ok=True)
    (ROOT / "qa" / "project20_upgrade_verification.json").write_text(json.dumps(verification, indent=2), encoding="utf-8")
    summary = {
        "status": "native_assets_created",
        "model_bim": str(MODEL_BIM),
        "layout_json": str(LAYOUT_JSON),
        "seed_template": str(SEED_TEMPLATE),
        "pages": [section["displayName"] for section in layout["sections"]],
        "project20_upgrade_verification": verification["status"],
    }
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()

