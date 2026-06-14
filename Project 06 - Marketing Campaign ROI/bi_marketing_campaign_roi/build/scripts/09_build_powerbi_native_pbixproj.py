from __future__ import annotations

import json
import re
import shutil
import uuid
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
PREPARED_DIR = PROJECT_ROOT / "data" / "prepared"
MODEL_DIR = PROJECT_ROOT / "model"
CONFIG_DIR = PROJECT_ROOT / "build" / "config"
PROJECT_DIR = PROJECT_ROOT / "build" / "pbixproj" / "Project6_Marketing_ROI"
OUTPUT_DIR = PROJECT_ROOT / "output"
THEME_NAME = "Project6_Marketing_ROI_Theme.json"

TABLES = [
    ("dim_date", "DimDate"),
    ("dim_month", "DimMonth"),
    ("dim_channel", "DimChannel"),
    ("dim_campaign", "DimCampaign"),
    ("fact_campaign_daily", "FactCampaignDaily"),
]

RELATIONSHIPS = [
    ("FactCampaignDaily", "date", "DimDate", "date"),
    ("FactCampaignDaily", "month_key", "DimMonth", "month_key"),
    ("FactCampaignDaily", "channel_key", "DimChannel", "channel_key"),
    ("FactCampaignDaily", "campaign_key", "DimCampaign", "campaign_key"),
]

MEASURES = [
    ("Spend", "SUM ( FactCampaignDaily[spend] )", "$#,0,,.0M", "Portfolio media and owned-channel spend."),
    ("Revenue", "SUM ( FactCampaignDaily[revenue] )", "$#,0,,.0M", "Attributed revenue."),
    ("Gross Profit", "SUM ( FactCampaignDaily[gross_profit] )", "$#,0,,.0M", "Attributed gross profit."),
    ("Clicks", "SUM ( FactCampaignDaily[clicks] )", "#,0", "Total clicks."),
    ("Conversions", "SUM ( FactCampaignDaily[conversions] )", "#,0", "Total conversions."),
    ("New Customers", "SUM ( FactCampaignDaily[new_customers] )", "#,0", "New customers attributed to campaigns."),
    ("ROAS", "DIVIDE ( [Revenue], [Spend] )", "0.00x", "Revenue divided by spend."),
    ("Marketing ROI", "DIVIDE ( [Gross Profit] - [Spend], [Spend] )", "0.0%", "Profit after spend divided by spend."),
    ("CAC", "DIVIDE ( [Spend], [New Customers] )", "$#,0", "Spend divided by new customers."),
    ("Conversion Rate", "DIVIDE ( [Conversions], [Clicks] )", "0.0%", "Conversions divided by clicks."),
    ("Target ROAS", "AVERAGE ( DimChannel[target_roas] )", "0.00x", "Average selected channel ROAS target."),
    ("Target CAC", "AVERAGE ( DimChannel[target_cac] )", "$#,0", "Average selected channel CAC target."),
    ("ROAS vs Target", "[ROAS] - [Target ROAS]", "0.00x", "ROAS minus target ROAS."),
    ("CAC vs Target", "[Target CAC] - [CAC]", "$#,0", "Positive values mean CAC is under target."),
    ("Spend Share", "DIVIDE ( [Spend], CALCULATE ( [Spend], ALLSELECTED ( DimChannel[channel] ) ) )", "0.0%", "Share of selected spend."),
    (
        "Campaign Scale Score",
        "VAR campaignCount = COUNTROWS ( ALLSELECTED ( DimCampaign[campaign_name] ) )\n"
        "VAR roasPct = DIVIDE ( RANKX ( ALLSELECTED ( DimCampaign[campaign_name] ), [ROAS], , ASC, DENSE ) - 1, campaignCount - 1 )\n"
        "VAR roiPct = DIVIDE ( RANKX ( ALLSELECTED ( DimCampaign[campaign_name] ), [Marketing ROI], , ASC, DENSE ) - 1, campaignCount - 1 )\n"
        "VAR inverseCacPct = 1 - DIVIDE ( RANKX ( ALLSELECTED ( DimCampaign[campaign_name] ), [CAC], , ASC, DENSE ) - 1, campaignCount - 1 )\n"
        "VAR profitPct = DIVIDE ( RANKX ( ALLSELECTED ( DimCampaign[campaign_name] ), [Gross Profit], , ASC, DENSE ) - 1, campaignCount - 1 )\n"
        "RETURN IF ( campaignCount <= 1, BLANK (), ( roasPct * 0.4 + roiPct * 0.3 + inverseCacPct * 0.2 + profitPct * 0.1 ) * 100 )",
        "0.0",
        "Slicer-aware scale ranking score.",
    ),
]


def guid() -> str:
    return str(uuid.uuid4())


def visual_id() -> str:
    return uuid.uuid4().hex[:20]


def write_json(path: Path, payload: dict | list) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def pbi_literal(value: str | bool | int | float) -> dict:
    if isinstance(value, bool):
        rendered = "true" if value else "false"
    elif isinstance(value, int):
        rendered = f"{value}L"
    elif isinstance(value, float):
        rendered = f"{value}D"
    else:
        rendered = value
    return {"expr": {"Literal": {"Value": rendered}}}


def color(value: str) -> dict:
    return {"solid": {"color": pbi_literal(f"'{value}'")}}


def text(value: str) -> dict:
    return pbi_literal("'" + value.replace("'", "''") + "'")


def clean_folder_name(value: str) -> str:
    safe = re.sub(r"[^A-Za-z0-9 _-]+", "", value).strip().replace(" ", "_")
    return safe[:70] or "visual"


def infer_type(series: pd.Series, column: str) -> tuple[str, str]:
    if column.lower() in {"date", "launch_date", "week_start", "month_start"}:
        return "dateTime", "type date"
    if pd.api.types.is_bool_dtype(series):
        return "boolean", "type logical"
    if pd.api.types.is_integer_dtype(series):
        return "int64", "Int64.Type"
    if pd.api.types.is_float_dtype(series):
        return "double", "type number"
    return "string", "type text"


def column_format(column: str, data_type: str) -> str | None:
    if column in {"spend", "revenue", "gross_profit", "base_spend", "target_cac"}:
        return "$#,0;($#,0);$0"
    if column in {"target_roas"}:
        return "0.00x"
    if "Pct" in column or "rate" in column.lower():
        return "0.0%"
    if data_type == "int64":
        return "0"
    return None


def create_import_table(csv_name: str, table_name: str) -> dict:
    csv_path = PREPARED_DIR / f"{csv_name}.csv"
    sample = pd.read_csv(csv_path, nrows=200)
    source_column_count = len(sample.columns)
    if table_name in {"DimChannel", "DimCampaign"}:
        sample["recommended_action"] = ""
    columns = []
    m_types = []
    for name in sample.columns:
        model_type, m_type = infer_type(sample[name], name)
        col = {
            "name": name,
            "dataType": model_type,
            "sourceColumn": name,
            "lineageTag": guid(),
        }
        fmt = column_format(name, model_type)
        if fmt:
            col["formatString"] = fmt
        if name.endswith("Key") or model_type in {"string", "dateTime", "boolean"}:
            col["summarizeBy"] = "none"
        columns.append(col)
        if name != "recommended_action":
            m_types.append(f'{{"{name}", {m_type}}}')

    file_path = str(csv_path).replace("\\", "\\\\")
    expression = [
        "let",
        f'    Source = Csv.Document(File.Contents("{file_path}"), [Delimiter=",", Columns={source_column_count}, Encoding=65001, QuoteStyle=QuoteStyle.Csv]),',
        "    PromotedHeaders = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),",
        f"    ChangedType = Table.TransformColumnTypes(PromotedHeaders, {{{', '.join(m_types)}}}, \"en-US\")",
    ]
    if table_name in {"DimChannel", "DimCampaign"}:
        expression[-1] += ","
        expression.extend(
            [
                '    WithAction = Table.AddColumn(ChangedType, "recommended_action", each if List.Contains({"Direct", "Email", "Referral Partners", "Organic Search"}, [channel]) then "Scale" else if [channel] = "Affiliates" then "Optimize" else "Review/Cut", type text)',
                "in",
                "    WithAction",
            ]
        )
    else:
        expression.extend(["in", "    ChangedType"])
    return {
        "name": table_name,
        "lineageTag": guid(),
        "columns": columns,
        "partitions": [
            {
                "name": f"p_{table_name}",
                "mode": "import",
                "source": {"type": "m", "expression": expression},
            }
        ],
    }


def load_measures() -> list[dict]:
    measures = []
    for name, expression, fmt, definition in MEASURES:
        measures.append(
            {
                "name": name,
                "description": definition,
                "expression": expression,
                "formatString": fmt,
                "lineageTag": guid(),
            }
        )
    return measures


def create_measure_table(measures: list[dict]) -> dict:
    return {
        "name": "KPI_Measures",
        "lineageTag": guid(),
        "columns": [
            {
                "type": "calculatedTableColumn",
                "name": "MeasureName",
                "dataType": "string",
                "isNameInferred": True,
                "isDataTypeInferred": True,
                "sourceColumn": "[MeasureName]",
                "isHidden": True,
                "lineageTag": guid(),
            }
        ],
        "partitions": [
            {
                "name": "KPI_Measures",
                "mode": "import",
                "source": {"type": "calculated", "expression": 'DATATABLE("MeasureName", STRING, {{"KPI"}})'},
            }
        ],
        "measures": measures,
    }


def create_database() -> None:
    tables = [create_import_table(csv_name, table_name) for csv_name, table_name in TABLES]
    tables.append(create_measure_table(load_measures()))
    relationships = [
        {
            "name": f"Rel_{fact}_{fact_col}_{dim}_{dim_col}",
            "fromTable": fact,
            "fromColumn": fact_col,
            "toTable": dim,
            "toColumn": dim_col,
        }
        for fact, fact_col, dim, dim_col in RELATIONSHIPS
    ]
    database = {
        "name": "Project6_Marketing_Campaign_ROI",
        "compatibilityLevel": 1600,
        "model": {
            "culture": "en-US",
            "dataAccessOptions": {"legacyRedirects": True, "returnErrorValuesAsNull": True},
            "defaultPowerBIDataSourceVersion": "powerBI_V3",
            "sourceQueryCulture": "en-US",
            "tables": tables,
            "relationships": relationships,
            "annotations": [
                {"name": "__PBI_TimeIntelligenceEnabled", "value": "1"},
                {"name": "Project", "value": "Project 06 - Marketing Campaign ROI Marketing Campaign ROI Dashboard"},
            ],
        },
    }
    write_json(PROJECT_DIR / "Model" / "database.json", database)
    create_diagram_layout(tables)


def create_diagram_layout(tables: list[dict]) -> None:
    nodes = []
    for idx, table in enumerate(tables):
        nodes.append(
            {
                "location": {"x": (idx % 6) * 280, "y": (idx // 6) * 260},
                "nodeIndex": table["name"],
                "nodeLineageTag": table.get("lineageTag"),
                "size": {"height": 220, "width": 234},
                "zIndex": 0,
            }
        )
    write_json(
        PROJECT_DIR / "DiagramLayout.json",
        {
            "version": "1.1.0",
            "diagrams": [
                {
                    "ordinal": 0,
                    "scrollPosition": {"x": 0, "y": 0},
                    "nodes": nodes,
                    "name": "All tables",
                    "zoomValue": 100,
                    "pinKeyFieldsToTop": False,
                    "showExtraHeaderInfo": False,
                    "hideKeyFieldsWhenCollapsed": False,
                    "tablesLocked": False,
                }
            ],
            "selectedDiagram": "All tables",
            "defaultDiagram": "All tables",
        },
    )


def visual_frame(title_value: str, subtitle_value: str | None = None) -> dict:
    vc = {
        "background": [
            {"properties": {"show": pbi_literal(True), "color": color("#FFFFFF"), "transparency": pbi_literal(0.0)}}
        ],
        "border": [
            {
                "properties": {
                    "show": pbi_literal(True),
                    "color": color("#D9DEE7"),
                    "radius": pbi_literal(6.0),
                    "width": pbi_literal(1.0),
                }
            }
        ],
        "dropShadow": [
            {
                "properties": {
                    "show": pbi_literal(True),
                    "position": text("Outer"),
                    "color": color("#C8D2E0"),
                    "transparency": pbi_literal(78.0),
                    "angle": pbi_literal(45.0),
                    "distance": pbi_literal(2.0),
                }
            }
        ],
        "title": [
            {
                "properties": {
                    "show": pbi_literal(True),
                    "text": text(title_value),
                    "fontFamily": text("Segoe UI Semibold"),
                    "fontSize": pbi_literal(9.5),
                    "fontColor": color("#17202A"),
                    "alignment": text("left"),
                }
            }
        ],
    }
    if subtitle_value:
        vc["subTitle"] = [
            {
                "properties": {
                    "show": pbi_literal(True),
                    "text": text(subtitle_value),
                    "fontFamily": text("Segoe UI"),
                    "fontSize": pbi_literal(7.5),
                    "fontColor": color("#5C6B73"),
                }
            }
        ]
    return vc


def position(x: int, y: int, z: int, width: int, height: int) -> dict:
    return {"x": x, "y": y, "z": z, "width": width, "height": height, "tabOrder": z}


def add_position(config: dict, pos: dict) -> dict:
    config["layouts"] = [{"id": 0, "position": pos}]
    return config


def source_ref(alias: str) -> dict:
    return {"SourceRef": {"Source": alias}}


def entity_ref(alias: str) -> dict:
    return {"SourceRef": {"Entity": alias}}


def column_select(alias: str, table: str, column: str, display: str) -> dict:
    return {
        "Column": {"Expression": source_ref(alias), "Property": column},
        "Name": f"{table}.{column}",
        "NativeReferenceName": display,
    }


def measure_select(alias: str, measure: str, display: str) -> dict:
    return {
        "Measure": {"Expression": source_ref(alias), "Property": measure},
        "Name": f"KPI_Measures.{measure}",
        "NativeReferenceName": display,
    }


def make_query(from_items: list[dict], selects: list[dict], order_by: dict | None = None) -> dict:
    query = {"Version": 2, "From": from_items, "Select": selects}
    if order_by:
        query["OrderBy"] = [order_by]
    return {
        "Commands": [
            {
                "SemanticQueryDataShapeCommand": {
                    "Query": query,
                    "Binding": {
                        "Primary": {"Groupings": [{"Projections": list(range(len(selects)))}]},
                        "DataReduction": {"DataVolume": 4, "Primary": {"Window": {"Count": 1000}}},
                        "Version": 1,
                    },
                    "ExecutionMetricsKind": 1,
                }
            }
        ]
    }


def select_transform_for_column(alias: str, table: str, column: str, display: str, role: str) -> dict:
    return {
        "displayName": display,
        "queryName": f"{table}.{column}",
        "roles": {role: True},
        "type": {"category": None, "underlyingType": 1},
        "expr": {"Column": {"Expression": entity_ref(alias), "Property": column}},
    }


def select_transform_for_measure(measure: str, display: str, role: str, fmt: str) -> dict:
    return {
        "displayName": display,
        "queryName": f"KPI_Measures.{measure}",
        "roles": {role: True},
        "type": {"category": None, "underlyingType": 259},
        "expr": {"Measure": {"Expression": entity_ref("m"), "Property": measure}},
        "format": fmt,
        "sort": 2,
        "sortOrder": 0,
    }


def data_transform(
    objects: dict,
    roles: list[tuple[str, int, bool]],
    metadata: list[dict],
    selects: list[dict],
    projection_ordering: dict,
    active_items: dict | None = None,
) -> dict:
    payload = {
        "objects": objects,
        "projectionOrdering": projection_ordering,
        "queryMetadata": {"Select": metadata},
        "visualElements": [
            {"DataRoles": [{"Name": role, "Projection": idx, "isActive": active} for role, idx, active in roles]}
        ],
        "selects": selects,
    }
    if active_items:
        payload["projectionActiveItems"] = active_items
    return payload


def measure_format(measure: str) -> str:
    for item in load_measures():
        if item["name"] == measure:
            return item.get("formatString", "#,0")
    return "#,0"


def chart_objects(fill_metadata: str | None = None) -> dict:
    objects = {
        "valueAxis": [
            {
                "properties": {
                    "showAxisTitle": pbi_literal(False),
                    "gridlineShow": pbi_literal(False),
                    "labelDisplayUnits": pbi_literal(1000000.0),
                }
            }
        ],
        "categoryAxis": [
            {
                "properties": {
                    "showAxisTitle": pbi_literal(False),
                    "gridlineShow": pbi_literal(False),
                    "concatenateLabels": pbi_literal(True),
                }
            }
        ],
        "labels": [
            {"properties": {"show": pbi_literal(True), "labelDisplayUnits": pbi_literal(1000000.0)}}
        ],
        "legend": [{"properties": {"showTitle": pbi_literal(False), "position": text("Top")}}],
    }
    if fill_metadata:
        objects["dataPoint"] = [
            {"properties": {"fill": color("#2454A6")}, "selector": {"metadata": fill_metadata}}
        ]
    return objects


def card_visual(measure: str, display: str, pos: dict) -> tuple[dict, dict, dict]:
    qref = f"KPI_Measures.{measure}"
    objects = {
        "layout": [
            {
                "properties": {
                    "rectangleRoundedCurve": pbi_literal(6),
                    "cellPadding": pbi_literal(6.0),
                    "paddingUniform": pbi_literal(6.0),
                },
                "selector": {"id": "default"},
            },
            {"properties": {}},
        ],
        "fillCustom": [{"properties": {"show": pbi_literal(False)}}],
        "outline": [{"properties": {"show": pbi_literal(False)}, "selector": {"id": "default"}}],
        "value": [
            {
                "properties": {
                    "fontSize": pbi_literal(21.0),
                    "fontFamily": text("Segoe UI Semibold"),
                    "fontColor": color("#2454A6"),
                },
                "selector": {"metadata": qref},
            }
        ],
        "label": [
            {
                "properties": {
                    "show": pbi_literal(True),
                    "position": text("belowValue"),
                    "fontSize": pbi_literal(8.0),
                    "fontFamily": text("Segoe UI"),
                    "fontColor": color("#5C6B73"),
                },
                "selector": {"metadata": qref},
            }
        ],
        "divider": [{"properties": {"show": pbi_literal(False)}, "selector": {"metadata": qref}}],
        "referenceLabelDetail": [{"properties": {"show": pbi_literal(False)}, "selector": {"metadata": qref}}],
    }
    config = add_position(
        {
            "name": visual_id(),
            "singleVisual": {
                "visualType": "cardVisual",
                "projections": {"Data": [{"queryRef": qref}]},
                "prototypeQuery": {
                    "Version": 2,
                    "From": [{"Name": "m", "Entity": "KPI_Measures", "Type": 0}],
                    "Select": [measure_select("m", measure, display)],
                },
                "columnProperties": {qref: {"displayName": display}},
                "drillFilterOtherVisuals": True,
                "hasDefaultSort": True,
                "objects": objects,
                "vcObjects": visual_frame(display),
            },
        },
        pos,
    )
    query = make_query(
        [{"Name": "m", "Entity": "KPI_Measures", "Type": 0}],
        [measure_select("m", measure, display)],
    )
    transforms = data_transform(
        objects,
        [("Data", 0, False)],
        [{"Restatement": display, "Name": qref, "Type": 1, "Format": measure_format(measure)}],
        [select_transform_for_measure(measure, display, "Data", measure_format(measure))],
        {"Data": [0]},
    )
    return config, query, transforms


def slicer_visual(table: str, column: str, display: str, pos: dict) -> tuple[dict, dict, dict]:
    qref = f"{table}.{column}"
    objects = {
        "data": [{"properties": {"mode": text("Dropdown")}}],
        "general": [{"properties": {"orientation": pbi_literal(0.0)}}],
        "selection": [
            {
                "properties": {
                    "selectAllCheckboxEnabled": pbi_literal(True),
                    "singleSelect": pbi_literal(False),
                }
            }
        ],
        "header": [
            {
                "properties": {
                    "show": pbi_literal(True),
                    "text": text(display),
                    "textSize": pbi_literal(8.0),
                    "fontColor": color("#5C6B73"),
                    "fontFamily": text("Segoe UI Semibold"),
                }
            }
        ],
        "items": [
            {
                "properties": {
                    "textSize": pbi_literal(8.0),
                    "fontColor": color("#17202A"),
                    "fontFamily": text("Segoe UI"),
                }
            }
        ],
    }
    config = add_position(
        {
            "name": visual_id(),
            "singleVisual": {
                "visualType": "slicer",
                "projections": {"Values": [{"queryRef": qref, "active": True}]},
                "prototypeQuery": {
                    "Version": 2,
                    "From": [{"Name": "f", "Entity": table, "Type": 0}],
                    "Select": [column_select("f", table, column, display)],
                },
                "drillFilterOtherVisuals": True,
                "hasDefaultSort": True,
                "objects": objects,
                "vcObjects": visual_frame(display),
            },
        },
        pos,
    )
    query = make_query(
        [{"Name": "f", "Entity": table, "Type": 0}],
        [column_select("f", table, column, display)],
    )
    transforms = data_transform(
        objects,
        [("Values", 0, True)],
        [{"Restatement": display, "Name": qref, "Type": 2048}],
        [select_transform_for_column("f", table, column, display, "Values")],
        {"Values": [0]},
    )
    return config, query, transforms


def bar_or_column_visual(
    visual_type: str,
    title_value: str,
    subtitle: str,
    category_table: str,
    category_column: str,
    category_display: str,
    measure: str,
    measure_display: str,
    pos: dict,
) -> tuple[dict, dict, dict]:
    category_ref = f"{category_table}.{category_column}"
    measure_ref = f"KPI_Measures.{measure}"
    objects = chart_objects(measure_ref)
    from_items = [
        {"Name": "c", "Entity": category_table, "Type": 0},
        {"Name": "m", "Entity": "KPI_Measures", "Type": 0},
    ]
    selects = [column_select("c", category_table, category_column, category_display), measure_select("m", measure, measure_display)]
    order_by = {"Direction": 2, "Expression": {"Measure": {"Expression": source_ref("m"), "Property": measure}}}
    config = add_position(
        {
            "name": visual_id(),
            "singleVisual": {
                "visualType": visual_type,
                "projections": {"Category": [{"queryRef": category_ref, "active": True}], "Y": [{"queryRef": measure_ref}]},
                "prototypeQuery": {"Version": 2, "From": from_items, "Select": selects, "OrderBy": [order_by]},
                "drillFilterOtherVisuals": True,
                "hasDefaultSort": True,
                "objects": objects,
                "vcObjects": visual_frame(title_value, subtitle),
            },
        },
        pos,
    )
    query = make_query(from_items, selects, order_by)
    transforms = data_transform(
        objects,
        [("Category", 0, True), ("Y", 1, False)],
        [
            {"Restatement": category_display, "Name": category_ref, "Type": 2048},
            {"Restatement": measure_display, "Name": measure_ref, "Type": 1, "Format": measure_format(measure)},
        ],
        [
            select_transform_for_column("c", category_table, category_column, category_display, "Category"),
            select_transform_for_measure(measure, measure_display, "Y", measure_format(measure)),
        ],
        {"Category": [0], "Y": [1]},
        {"Category": [{"queryRef": category_ref, "suppressConcat": False}]},
    )
    return config, query, transforms


def combo_visual(
    title_value: str,
    subtitle: str,
    category_table: str,
    category_column: str,
    category_display: str,
    bar_measure: str,
    bar_display: str,
    line_measure: str,
    line_display: str,
    pos: dict,
) -> tuple[dict, dict, dict]:
    category_ref = f"{category_table}.{category_column}"
    bar_ref = f"KPI_Measures.{bar_measure}"
    line_ref = f"KPI_Measures.{line_measure}"
    objects = chart_objects(bar_ref)
    from_items = [
        {"Name": "c", "Entity": category_table, "Type": 0},
        {"Name": "m", "Entity": "KPI_Measures", "Type": 0},
    ]
    selects = [
        column_select("c", category_table, category_column, category_display),
        measure_select("m", bar_measure, bar_display),
        measure_select("m", line_measure, line_display),
    ]
    order_by = {"Direction": 2, "Expression": {"Column": {"Expression": source_ref("c"), "Property": category_column}}}
    config = add_position(
        {
            "name": visual_id(),
            "singleVisual": {
                "visualType": "lineClusteredColumnComboChart",
                "projections": {
                    "Category": [{"queryRef": category_ref, "active": True}],
                    "Y": [{"queryRef": bar_ref}],
                    "Y2": [{"queryRef": line_ref}],
                },
                "prototypeQuery": {"Version": 2, "From": from_items, "Select": selects, "OrderBy": [order_by]},
                "drillFilterOtherVisuals": True,
                "hasDefaultSort": True,
                "objects": objects,
                "vcObjects": visual_frame(title_value, subtitle),
            },
        },
        pos,
    )
    query = make_query(from_items, selects, order_by)
    transforms = data_transform(
        objects,
        [("Category", 0, True), ("Y", 1, False), ("Y2", 2, False)],
        [
            {"Restatement": category_display, "Name": category_ref, "Type": 2048},
            {"Restatement": bar_display, "Name": bar_ref, "Type": 1, "Format": measure_format(bar_measure)},
            {"Restatement": line_display, "Name": line_ref, "Type": 1, "Format": measure_format(line_measure)},
        ],
        [
            select_transform_for_column("c", category_table, category_column, category_display, "Category"),
            select_transform_for_measure(bar_measure, bar_display, "Y", measure_format(bar_measure)),
            select_transform_for_measure(line_measure, line_display, "Y2", measure_format(line_measure)),
        ],
        {"Category": [0], "Y": [1], "Y2": [2]},
        {"Category": [{"queryRef": category_ref, "suppressConcat": False}]},
    )
    return config, query, transforms


def table_visual(title_value: str, subtitle: str, fields: list[tuple[str, str, str]], measures: list[tuple[str, str]], pos: dict) -> tuple[dict, dict, dict]:
    from_items = []
    aliases: dict[str, str] = {}
    for idx, (table, _, _) in enumerate(fields):
        if table not in aliases:
            alias = f"f{idx}"
            aliases[table] = alias
            from_items.append({"Name": alias, "Entity": table, "Type": 0})
    if measures:
        aliases["KPI_Measures"] = "m"
        from_items.append({"Name": "m", "Entity": "KPI_Measures", "Type": 0})
    selects = []
    projections = []
    metadata = []
    transform_selects = []
    for table, column, display in fields:
        idx = len(selects)
        selects.append(column_select(aliases[table], table, column, display))
        qref = f"{table}.{column}"
        projections.append({"queryRef": qref})
        metadata.append({"Restatement": display, "Name": qref, "Type": 2048})
        transform_selects.append(select_transform_for_column(aliases[table], table, column, display, "Values"))
    for measure, display in measures:
        idx = len(selects)
        selects.append(measure_select("m", measure, display))
        qref = f"KPI_Measures.{measure}"
        projections.append({"queryRef": qref})
        metadata.append({"Restatement": display, "Name": qref, "Type": 1, "Format": measure_format(measure)})
        transform_selects.append(select_transform_for_measure(measure, display, "Values", measure_format(measure)))
    objects = {
        "grid": [{"properties": {"gridHorizontal": pbi_literal(False), "outlineColor": color("#D9DEE7")}}],
        "columnHeaders": [
            {
                "properties": {
                    "fontFamily": text("Segoe UI Semibold"),
                    "fontSize": pbi_literal(7.5),
                    "fontColor": color("#2454A6"),
                }
            }
        ],
        "values": [{"properties": {"fontSize": pbi_literal(7.5), "fontFamily": text("Segoe UI")}}],
    }
    order_by = None
    if measures:
        order_by = {"Direction": 2, "Expression": {"Measure": {"Expression": source_ref("m"), "Property": measures[0][0]}}}
    config = add_position(
        {
            "name": visual_id(),
            "singleVisual": {
                "visualType": "tableEx",
                "projections": {"Values": projections},
                "prototypeQuery": {
                    "Version": 2,
                    "From": from_items,
                    "Select": selects,
                    **({"OrderBy": [order_by]} if order_by else {}),
                },
                "drillFilterOtherVisuals": True,
                "objects": objects,
                "vcObjects": visual_frame(title_value, subtitle),
            },
        },
        pos,
    )
    query = make_query(from_items, selects, order_by)
    transforms = data_transform(
        objects,
        [("Values", idx, False) for idx in range(len(selects))],
        metadata,
        transform_selects,
        {"Values": list(range(len(selects)))},
    )
    return config, query, transforms


def shape_visual(hex_color: str, pos: dict) -> tuple[dict, None, None]:
    config = add_position(
        {
            "name": visual_id(),
            "singleVisual": {
                "visualType": "shape",
                "drillFilterOtherVisuals": True,
                "objects": {
                    "shape": [{"properties": {"tileShape": text("rectangle")}}],
                    "fill": [
                        {
                            "properties": {
                                "show": pbi_literal(True),
                                "fillColor": color(hex_color),
                                "transparency": pbi_literal(0.0),
                            }
                        }
                    ],
                    "outline": [{"properties": {"show": pbi_literal(False)}}],
                },
            },
        },
        pos,
    )
    return config, None, None


def textbox_visual(value: str, font_size: int, hex_color: str, pos: dict, bold: bool = True) -> tuple[dict, None, None]:
    config = add_position(
        {
            "name": visual_id(),
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
                                                "value": value,
                                                "textStyle": {
                                                    "fontFamily": "Segoe UI Semibold" if bold else "Segoe UI",
                                                    "fontSize": f"{font_size}pt",
                                                    "color": hex_color,
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
        },
        pos,
    )
    return config, None, None


def visual_files(section_dir: Path, order: int, title_value: str, triple: tuple[dict, dict | None, dict | None]) -> None:
    config, query, transforms = triple
    vdir = section_dir / "visualContainers" / f"{order:05d}_{clean_folder_name(title_value)}"
    write_json(vdir / "config.json", config)
    write_json(vdir / "visualContainer.json", config["layouts"][0]["position"])
    write_json(vdir / "filters.json", [])
    if query is not None:
        write_json(vdir / "query.json", query)
    if transforms is not None:
        write_json(vdir / "dataTransforms.json", transforms)


def add_common_header(section_dir: Path, title_value: str, subtitle: str) -> int:
    visual_files(section_dir, 0, "Header Band", shape_visual("#10223F", position(0, 0, 0, 1280, 68)))
    visual_files(section_dir, 1, "Page Title", textbox_visual(title_value, 16, "#FFFFFF", position(24, 12, 100, 600, 32)))
    visual_files(section_dir, 2, "Page Subtitle", textbox_visual(subtitle, 8, "#E8F0F7", position(24, 42, 101, 680, 18), bold=False))
    visual_files(section_dir, 3, "Year Slicer", slicer_visual("DimDate", "year", "Year", position(760, 14, 300, 90, 45)))
    visual_files(section_dir, 4, "Channel Slicer", slicer_visual("DimChannel", "channel", "Channel", position(860, 14, 301, 145, 45)))
    visual_files(section_dir, 5, "Paid Organic Slicer", slicer_visual("DimChannel", "paid_organic", "Paid / Organic", position(1015, 14, 302, 120, 45)))
    visual_files(section_dir, 6, "Action Slicer", slicer_visual("DimChannel", "recommended_action", "Action", position(1145, 14, 303, 120, 45)))
    return 10


def create_section(folder: str, display_name: str, ordinal: int, title_value: str, subtitle: str) -> Path:
    section_dir = PROJECT_DIR / "Report" / "sections" / folder
    section_dir.mkdir(parents=True, exist_ok=True)
    write_json(
        section_dir / "section.json",
        {"displayName": display_name, "displayOption": 1, "height": 720, "name": f"project2_page_{ordinal+1:02d}", "ordinal": ordinal, "width": 1280},
    )
    write_json(
        section_dir / "config.json",
        {
            "objects": {
                "background": [
                    {
                        "properties": {
                            "color": color("#F3F6FA"),
                            "transparency": pbi_literal(0.0),
                        }
                    }
                ]
            }
        },
    )
    add_common_header(section_dir, title_value, subtitle)
    return section_dir


def create_report() -> None:
    report_dir = PROJECT_DIR / "Report"
    write_json(
        report_dir / "report.json",
        {
            "id": 0,
            "layoutOptimization": 0,
            "resourcePackages": [
                {
                    "resourcePackage": {
                        "disabled": False,
                        "items": [{"name": THEME_NAME, "path": THEME_NAME, "type": 201}],
                        "name": "RegisteredResources",
                        "type": 1,
                    }
                }
            ],
            "theme": THEME_NAME,
        },
    )
    write_json(
        report_dir / "config.json",
        {
            "version": "5.68",
            "themeCollection": {
                "customTheme": {
                    "name": THEME_NAME,
                    "type": 1,
                    "version": {"visual": "1.8.26", "report": "2.0.26", "page": "1.3.26"},
                }
            },
            "activeSectionIndex": 0,
            "linguisticSchemaSyncVersion": 2,
        },
    )

    page1 = create_section(
        "000_Executive_Overview",
        "01 Executive Overview",
        0,
        "01 Executive Overview",
        "Spend, revenue, ROAS, CAC and paid versus organic value.",
    )
    for idx, (measure, label) in enumerate(
        [("Spend", "Spend"), ("Revenue", "Revenue"), ("ROAS", "ROAS"), ("CAC", "CAC")]
    ):
        visual_files(page1, 100 + idx, label, card_visual(measure, label, position(20 + idx * 155, 88, 1000 + idx, 145, 76)))
    visual_files(page1, 210, "Spend and Revenue Trend", combo_visual("Spend and Revenue Trend", "Monthly spend as columns; revenue as line", "DimMonth", "month_label", "Month", "Spend", "Spend", "Revenue", "Revenue", position(20, 185, 2100, 610, 255)))
    visual_files(page1, 220, "Paid vs Organic Revenue", bar_or_column_visual("barChart", "Paid vs Organic Revenue", "Revenue contribution by traffic type", "DimChannel", "paid_organic", "Paid / Organic", "Revenue", "Revenue", position(650, 185, 2200, 300, 255)))
    visual_files(page1, 230, "Spend by Channel", bar_or_column_visual("barChart", "Spend by Channel", "Where budget is being consumed", "DimChannel", "channel", "Channel", "Spend", "Spend", position(970, 185, 2300, 290, 255)))
    visual_files(page1, 240, "Channel Decision Table", table_visual("Channel Decision Table", "Scale, optimize, or review budget by channel", [("DimChannel", "channel", "Channel"), ("DimChannel", "paid_organic", "Type"), ("DimChannel", "recommended_action", "Action")], [("Spend", "Spend"), ("Revenue", "Revenue"), ("ROAS", "ROAS"), ("CAC", "CAC"), ("Marketing ROI", "Mktg ROI")], position(20, 462, 2400, 1240, 188)))

    page2 = create_section(
        "001_Channel_ROI",
        "02 Channel ROI",
        1,
        "02 Channel ROI",
        "Channel efficiency versus ROAS and CAC targets.",
    )
    for idx, (measure, label) in enumerate(
        [("Marketing ROI", "Marketing ROI"), ("Target ROAS", "Target ROAS"), ("Target CAC", "Target CAC"), ("Conversion Rate", "CVR")]
    ):
        visual_files(page2, 100 + idx, label, card_visual(measure, label, position(20 + idx * 155, 88, 1000 + idx, 145, 76)))
    visual_files(page2, 210, "ROAS by Channel", bar_or_column_visual("barChart", "ROAS by Channel", "Higher is better; compare with target card", "DimChannel", "channel", "Channel", "ROAS", "ROAS", position(20, 185, 2100, 430, 255)))
    visual_files(page2, 220, "CAC by Channel", bar_or_column_visual("barChart", "CAC by Channel", "Lower CAC channels are easier to scale", "DimChannel", "channel", "Channel", "CAC", "CAC", position(470, 185, 2200, 380, 255)))
    visual_files(page2, 230, "Marketing ROI by Channel", bar_or_column_visual("columnChart", "Marketing ROI by Channel", "Profit-aware return after spend", "DimChannel", "channel", "Channel", "Marketing ROI", "Mktg ROI", position(870, 185, 2300, 390, 255)))
    visual_files(page2, 240, "Channel Target Gap Table", table_visual("Channel Target Gap Table", "Target deltas identify channels to tune", [("DimChannel", "channel", "Channel"), ("DimChannel", "recommended_action", "Action")], [("ROAS", "ROAS"), ("Target ROAS", "Target ROAS"), ("ROAS vs Target", "ROAS Gap"), ("CAC", "CAC"), ("CAC vs Target", "CAC Gap")], position(20, 462, 2400, 1240, 188)))

    page3 = create_section(
        "002_Campaign_Ranking",
        "03 Campaign Ranking",
        2,
        "03 Campaign Ranking",
        "Rank campaigns by scale score, ROAS, CAC and profit.",
    )
    for idx, (measure, label) in enumerate(
        [("Conversions", "Conversions"), ("New Customers", "New Customers"), ("Campaign Scale Score", "Scale Score"), ("Gross Profit", "Gross Profit")]
    ):
        visual_files(page3, 100 + idx, label, card_visual(measure, label, position(20 + idx * 155, 88, 1000 + idx, 145, 76)))
    visual_files(page3, 210, "Campaign Scale Score", bar_or_column_visual("barChart", "Campaign Scale Score", "Campaigns most ready for incremental budget", "DimCampaign", "campaign_name", "Campaign", "Campaign Scale Score", "Scale Score", position(20, 185, 2100, 610, 255)))
    visual_files(page3, 220, "Campaign Revenue Ranking", bar_or_column_visual("barChart", "Campaign Revenue Ranking", "Revenue concentration by campaign", "DimCampaign", "campaign_name", "Campaign", "Revenue", "Revenue", position(650, 185, 2200, 610, 255)))
    visual_files(page3, 240, "Campaign Ranking Table", table_visual("Campaign Ranking Table", "Campaign lookup for scale or cut decisions", [("DimCampaign", "campaign_name", "Campaign"), ("DimCampaign", "channel", "Channel"), ("DimCampaign", "recommended_action", "Action")], [("Spend", "Spend"), ("Revenue", "Revenue"), ("ROAS", "ROAS"), ("CAC", "CAC"), ("Campaign Scale Score", "Scale Score")], position(20, 462, 2400, 1240, 188)))

    page4 = create_section(
        "003_Actions",
        "04 Actions",
        3,
        "04 Actions",
        "Budget action matrix for channels burning spend or ready to scale.",
    )
    for idx, (measure, label) in enumerate(
        [("Spend Share", "Spend Share"), ("ROAS vs Target", "ROAS Gap"), ("CAC vs Target", "CAC Gap"), ("Conversion Rate", "CVR")]
    ):
        visual_files(page4, 100 + idx, label, card_visual(measure, label, position(20 + idx * 155, 88, 1000 + idx, 145, 76)))
    visual_files(page4, 210, "Spend by Action", bar_or_column_visual("columnChart", "Spend by Action", "Budget grouped by recommended action", "DimChannel", "recommended_action", "Action", "Spend", "Spend", position(20, 185, 2100, 390, 255)))
    visual_files(page4, 220, "Revenue by Action", bar_or_column_visual("columnChart", "Revenue by Action", "Outcome grouped by recommended action", "DimChannel", "recommended_action", "Action", "Revenue", "Revenue", position(430, 185, 2200, 390, 255)))
    visual_files(page4, 230, "ROAS by Action", bar_or_column_visual("columnChart", "ROAS by Action", "Efficiency of each action bucket", "DimChannel", "recommended_action", "Action", "ROAS", "ROAS", position(840, 185, 2300, 420, 255)))
    visual_files(page4, 240, "Budget Action Matrix", table_visual("Budget Action Matrix", "Operational next step by channel", [("DimChannel", "recommended_action", "Action"), ("DimChannel", "channel", "Channel"), ("DimChannel", "paid_organic", "Type")], [("Spend", "Spend"), ("Revenue", "Revenue"), ("ROAS", "ROAS"), ("CAC", "CAC"), ("Marketing ROI", "Mktg ROI")], position(20, 462, 2400, 1240, 188)))


def create_project_files() -> None:
    if PROJECT_DIR.exists():
        shutil.rmtree(PROJECT_DIR)
    PROJECT_DIR.mkdir(parents=True)
    write_json(
        PROJECT_DIR / ".pbixproj.json",
        {"version": "1.0", "created": "2026-06-11T00:00:00", "lastModified": "2026-06-11T00:00:00", "settings": {"model": {"serializationMode": "Raw"}, "mashup": {"serializationMode": "Raw"}}},
    )
    (PROJECT_DIR / "Version.txt").write_text("1.28", encoding="utf-8")
    write_json(PROJECT_DIR / "ReportMetadata.json", {"Version": 5, "AutoCreatedRelationships": [], "CreatedFrom": "Desktop", "CreatedFromRelease": "2026.06"})
    write_json(
        PROJECT_DIR / "ReportSettings.json",
        {"Version": 4, "ReportSettings": {}, "QueriesSettings": {"TypeDetectionEnabled": True, "RelationshipImportEnabled": True, "Version": "2.154.778.0"}},
    )
    theme_target = PROJECT_DIR / "StaticResources" / "RegisteredResources" / THEME_NAME
    theme_target.parent.mkdir(parents=True, exist_ok=True)
    source_theme = CONFIG_DIR / "theme.json"
    if source_theme.exists():
        shutil.copyfile(source_theme, theme_target)
    else:
        write_json(theme_target, {"name": "Project6 Theme", "dataColors": ["#2F66B3", "#11887F", "#F2B62D", "#EA6A65"]})


def main() -> None:
    create_project_files()
    create_database()
    create_report()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Generated PbixProj: {PROJECT_DIR}")


if __name__ == "__main__":
    main()
