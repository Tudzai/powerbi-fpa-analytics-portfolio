from __future__ import annotations

import json
import uuid
import csv
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
BUILD_DIR = PROJECT_ROOT / "build"
QA_DIR = PROJECT_ROOT / "qa"
KPI_SUMMARY_PATH = PROJECT_ROOT / "data" / "validated" / "kpi_summary.csv"

MEASURE_TABLE = "KPI Measures"

PAGE_BG = "#EEF3F8"
HEADER_BG = "#0B1220"
PANEL_BG = "#FFFFFF"
PANEL_BORDER = "#D8E0EA"
CARD_BG = "#FFFFFF"
CARD_BORDER = "#D8E0EA"
TEXT_DARK = "#101828"
TEXT_MUTED = "#667085"
TEXT_LIGHT = "#F8FAFC"
TEXT_LIGHT_MUTED = "#CBD5E1"
TEAL = "#14B8A6"
BLUE = "#3B82F6"
INDIGO = "#6366F1"
AMBER = "#F59E0B"
RED = "#EF4444"


def visual_id() -> str:
    return uuid.uuid4().hex[:20]


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def load_kpi_summary() -> dict[str, str]:
    if not KPI_SUMMARY_PATH.exists():
        return {}
    with KPI_SUMMARY_PATH.open("r", encoding="utf-8-sig", newline="") as handle:
        return {row["metric"]: row["value"] for row in csv.DictReader(handle)}


def fmt_money_compact(value: str) -> str:
    number = float(value)
    if abs(number) >= 1_000_000:
        return f"${number / 1_000_000:.0f}M"
    if abs(number) >= 1_000:
        return f"${number / 1_000:.0f}K"
    return f"${number:,.0f}"


def fmt_number_compact(value: str) -> str:
    number = float(value)
    if abs(number) >= 1_000_000:
        return f"{number / 1_000_000:.1f}M"
    if abs(number) >= 1_000:
        return f"{number / 1_000:.0f}K"
    return f"{number:,.0f}"


def fmt_pct(value: str) -> str:
    return f"{float(value):.2%}"


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


def text(value: str) -> dict:
    return pbi_literal("'" + value.replace("'", "''") + "'")


def color(value: str) -> dict:
    return {"solid": {"color": text(value)}}


def position(x: int, y: int, z: int, width: int, height: int) -> dict:
    return {"x": x, "y": y, "z": z, "width": width, "height": height, "tabOrder": z}


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
        "Name": f"{MEASURE_TABLE}.{measure}",
        "NativeReferenceName": display,
    }


def column_transform(alias: str, table: str, column: str, display: str, role: str) -> dict:
    return {
        "displayName": display,
        "queryName": f"{table}.{column}",
        "roles": {role: True},
        "type": {"category": None, "underlyingType": 1},
        "expr": {"Column": {"Expression": entity_ref(alias), "Property": column}},
    }


def measure_transform(measure: str, display: str, role: str, fmt: str) -> dict:
    return {
        "displayName": display,
        "queryName": f"{MEASURE_TABLE}.{measure}",
        "roles": {role: True},
        "type": {"category": None, "underlyingType": 259},
        "expr": {"Measure": {"Expression": entity_ref("m"), "Property": measure}},
        "format": fmt,
        "sort": 2,
        "sortOrder": 0,
    }


MEASURE_FORMATS = {
    "GMV": "$#,0",
    "Net Revenue": "$#,0",
    "Orders": "#,0",
    "Completed Orders": "#,0",
    "Refunded Orders": "#,0",
    "Cancelled Orders": "#,0",
    "AOV": "$#,0.00",
    "Sessions": "#,0",
    "Visitors": "#,0",
    "Conversion Rate": "0.00%",
    "Refund/Cancel Rate": "0.00%",
    "Marketing Spend": "$#,0",
    "ROAS": "0.00x",
    "Contribution Margin": "$#,0",
    "Contribution Margin %": "0.00%",
}


def measure_format(measure: str) -> str:
    return MEASURE_FORMATS.get(measure, "#,0")


def make_query(from_items: list[dict], selects: list[dict], order_by: dict | None = None, top: bool = False) -> str:
    query = {"Version": 2, "From": from_items, "Select": selects}
    if order_by:
        query["OrderBy"] = [order_by]
    data_reduction = {"DataVolume": 4, "Primary": {"Top": {}} if top else {"Window": {"Count": 1000}}}
    return json.dumps(
        {
            "Commands": [
                {
                    "SemanticQueryDataShapeCommand": {
                        "Query": query,
                        "Binding": {
                            "Primary": {"Groupings": [{"Projections": list(range(len(selects)))}]},
                            "DataReduction": data_reduction,
                            "Version": 1,
                        },
                        "ExecutionMetricsKind": 1,
                    }
                }
            ]
        },
        separators=(",", ":"),
    )


def data_transforms(
    objects: dict,
    roles: list[tuple[str, int, bool]],
    metadata: list[dict],
    selects: list[dict],
    projection_ordering: dict,
    active_items: dict | None = None,
) -> str:
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
    return json.dumps(payload, separators=(",", ":"))


def visual_frame(
    title: str | None = None,
    subtitle: str | None = None,
    *,
    fill: str = PANEL_BG,
    border_fill: str = PANEL_BORDER,
    title_fill: str = TEXT_DARK,
    subtitle_fill: str = TEXT_MUTED,
    radius: float = 8.0,
    shadow_transparency: float = 84.0,
    border_show: bool = True,
) -> dict:
    vc = {
        "background": [
            {"properties": {"show": pbi_literal(True), "color": color(fill), "transparency": pbi_literal(0.0)}}
        ],
        "border": [
            {
                "properties": {
                    "show": pbi_literal(border_show),
                    "color": color(border_fill),
                    "radius": pbi_literal(radius),
                    "width": pbi_literal(1.0),
                }
            }
        ],
        "dropShadow": [
            {
                "properties": {
                    "show": pbi_literal(True),
                    "position": text("Outer"),
                    "color": color("#0F172A"),
                    "transparency": pbi_literal(shadow_transparency),
                    "angle": pbi_literal(45.0),
                    "distance": pbi_literal(2.0),
                }
            }
        ],
        "visualHeader": [{"properties": {"show": pbi_literal(False)}}],
    }
    if title:
        vc["title"] = [
            {
                "properties": {
                    "show": pbi_literal(True),
                    "text": text(title),
                    "fontFamily": text("Segoe UI Semibold"),
                    "fontSize": pbi_literal(9.0),
                    "fontColor": color(title_fill),
                    "alignment": text("left"),
                }
            }
        ]
    if subtitle:
        vc["subTitle"] = [
            {
                "properties": {
                    "show": pbi_literal(True),
                    "text": text(subtitle),
                    "fontFamily": text("Segoe UI"),
                    "fontSize": pbi_literal(7.0),
                    "fontColor": color(subtitle_fill),
                }
            }
        ]
    return vc


def add_container(config: dict, pos: dict, query: str | None = None, transforms: str | None = None) -> dict:
    config["layouts"] = [{"id": 0, "position": pos}]
    payload = {
        "x": pos["x"],
        "y": pos["y"],
        "z": pos["z"],
        "width": pos["width"],
        "height": pos["height"],
        "config": json.dumps(config, separators=(",", ":")),
        "filters": "[]",
        "tabOrder": pos["tabOrder"],
    }
    if query:
        payload["query"] = query
    if transforms:
        payload["dataTransforms"] = transforms
    return payload


def title_text(
    title: str,
    subtitle: str,
    pos: dict,
    *,
    title_color: str = TEXT_DARK,
    subtitle_color: str = TEXT_MUTED,
) -> dict:
    objects = {
        "general": [
            {
                "properties": {
                    "paragraphs": [
                        {
                            "textRuns": [
                                {
                                        "value": title,
                                        "textStyle": {
                                            "fontFamily": "Segoe UI Semibold",
                                            "fontSize": "20pt",
                                            "color": title_color,
                                        },
                                    },
                                    {
                                        "value": f"\n{subtitle}",
                                        "textStyle": {
                                            "fontFamily": "Segoe UI",
                                            "fontSize": "8.5pt",
                                            "color": subtitle_color,
                                        },
                                },
                            ]
                        }
                    ]
                }
            }
        ]
    }
    config = {
        "name": visual_id(),
        "singleVisual": {
            "visualType": "textbox",
            "drillFilterOtherVisuals": True,
            "objects": objects,
            "vcObjects": {
                "background": [{"properties": {"show": pbi_literal(False)}}],
                "border": [{"properties": {"show": pbi_literal(False)}}],
                "visualHeader": [{"properties": {"show": pbi_literal(False)}}],
            },
        },
    }
    return add_container(config, pos)


def insight_card(label: str, value: str, caption: str, pos: dict, accent: str = TEAL) -> dict:
    objects = {
        "general": [
            {
                "properties": {
                    "paragraphs": [
                        {
                            "textRuns": [
                                {
                                    "value": label.upper(),
                                    "textStyle": {
                                        "fontFamily": "Segoe UI Semibold",
                                        "fontSize": "6.5pt",
                                        "color": TEXT_MUTED,
                                    },
                                },
                                {
                                    "value": f"\n{value}",
                                    "textStyle": {
                                        "fontFamily": "Segoe UI Semibold",
                                        "fontSize": "12.5pt",
                                        "color": accent,
                                    },
                                },
                                {
                                    "value": f"\n{caption}",
                                    "textStyle": {
                                        "fontFamily": "Segoe UI",
                                        "fontSize": "6.4pt",
                                        "color": TEXT_MUTED,
                                    },
                                },
                            ]
                        }
                    ]
                }
            }
        ]
    }
    config = {
        "name": visual_id(),
        "singleVisual": {
            "visualType": "textbox",
            "drillFilterOtherVisuals": True,
            "objects": objects,
            "vcObjects": visual_frame(fill=PANEL_BG, border_fill=PANEL_BORDER, radius=8.0, shadow_transparency=82.0),
        },
    }
    return add_container(config, pos)


def shape_box(pos: dict, fill: str, border_fill: str | None = None, radius: float = 0.0) -> dict:
    objects = {
        "general": [
            {
                "properties": {
                    "paragraphs": [
                        {
                            "textRuns": [
                                {
                                    "value": " ",
                                    "textStyle": {"fontFamily": "Segoe UI", "fontSize": "1pt", "color": fill},
                                }
                            ]
                        }
                    ]
                }
            }
        ]
    }
    config = {
        "name": visual_id(),
        "singleVisual": {
            "visualType": "textbox",
            "drillFilterOtherVisuals": True,
            "objects": objects,
            "vcObjects": visual_frame(
                fill=fill,
                border_fill=border_fill or fill,
                radius=radius,
                shadow_transparency=100.0,
                border_show=border_fill is not None,
            ),
        },
    }
    return add_container(config, pos)


def card(
    measure: str,
    display: str,
    pos: dict,
    value_color: str = TEAL,
    *,
    fill: str = PANEL_BG,
    title_fill: str = TEXT_DARK,
    label_fill: str = TEXT_MUTED,
    border_fill: str = PANEL_BORDER,
) -> dict:
    qref = f"{MEASURE_TABLE}.{measure}"
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
                    "fontColor": color(value_color),
                },
                "selector": {"metadata": qref},
            }
        ],
        "label": [
            {
                "properties": {
                    "show": pbi_literal(False),
                    "position": text("belowValue"),
                    "fontSize": pbi_literal(7.5),
                    "fontFamily": text("Segoe UI"),
                    "fontColor": color(label_fill),
                },
                "selector": {"metadata": qref},
            }
        ],
        "divider": [{"properties": {"show": pbi_literal(False)}, "selector": {"metadata": qref}}],
        "referenceLabelDetail": [{"properties": {"show": pbi_literal(False)}, "selector": {"metadata": qref}}],
    }
    selects = [measure_select("m", measure, display)]
    from_items = [{"Name": "m", "Entity": MEASURE_TABLE, "Type": 0}]
    config = {
        "name": visual_id(),
        "singleVisual": {
            "visualType": "cardVisual",
            "projections": {"Data": [{"queryRef": qref}]},
            "prototypeQuery": {"Version": 2, "From": from_items, "Select": selects},
            "columnProperties": {qref: {"displayName": display}},
            "drillFilterOtherVisuals": True,
            "hasDefaultSort": True,
            "objects": objects,
            "vcObjects": visual_frame(
                display,
                fill=fill,
                border_fill=border_fill,
                title_fill=title_fill,
                subtitle_fill=label_fill,
                radius=8.0,
                shadow_transparency=80.0,
            ),
        },
    }
    transforms = data_transforms(
        objects,
        [("Data", 0, False)],
        [{"Restatement": display, "Name": qref, "Type": 1, "Format": measure_format(measure)}],
        [measure_transform(measure, display, "Data", measure_format(measure))],
        {"Data": [0]},
    )
    return add_container(config, pos, make_query(from_items, selects), transforms)


def kpi_card(measure: str, display: str, pos: dict, value_color: str) -> dict:
    return card(
        measure,
        display,
        pos,
        value_color,
        fill=CARD_BG,
        title_fill=TEXT_DARK,
        label_fill=TEXT_MUTED,
        border_fill=CARD_BORDER,
    )


def slicer(table: str, column: str, display: str, pos: dict) -> dict:
    qref = f"{table}.{column}"
    objects = {
        "data": [{"properties": {"mode": text("Dropdown")}}],
        "selection": [{"properties": {"selectAllCheckboxEnabled": pbi_literal(True), "singleSelect": pbi_literal(False)}}],
        "header": [{"properties": {"show": pbi_literal(False), "text": text(display)}}],
        "items": [{"properties": {"textSize": pbi_literal(7.5), "fontColor": color(TEXT_DARK)}}],
    }
    from_items = [{"Name": "f", "Entity": table, "Type": 0}]
    selects = [column_select("f", table, column, display)]
    config = {
        "name": visual_id(),
        "singleVisual": {
            "visualType": "slicer",
            "projections": {"Values": [{"queryRef": qref, "active": True}]},
            "prototypeQuery": {"Version": 2, "From": from_items, "Select": selects},
            "drillFilterOtherVisuals": True,
            "hasDefaultSort": True,
            "objects": objects,
            "vcObjects": visual_frame(display, fill=PANEL_BG, border_fill="#D6DEE8", shadow_transparency=88.0),
        },
    }
    transforms = data_transforms(
        objects,
        [("Values", 0, True)],
        [{"Restatement": display, "Name": qref, "Type": 2048}],
        [column_transform("f", table, column, display, "Values")],
        {"Values": [0]},
    )
    return add_container(config, pos, make_query(from_items, selects), transforms)


def chart_objects(fill: str = BLUE, show_labels: bool = True) -> dict:
    return {
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
                    "concatenateLabels": pbi_literal(False),
                    "fontSize": pbi_literal(7.0),
                }
            }
        ],
        "labels": [{"properties": {"show": pbi_literal(show_labels), "fontSize": pbi_literal(7.0), "fontColor": color("#475467")}}],
        "legend": [{"properties": {"showTitle": pbi_literal(False), "position": text("Top")}}],
        "dataPoint": [{"properties": {"fill": color(fill)}}],
    }


def single_measure_chart(
    visual_type: str,
    title: str,
    subtitle: str,
    category_table: str,
    category_column: str,
    category_display: str,
    measure: str,
    measure_display: str,
    pos: dict,
    fill: str = BLUE,
    order_measure: bool = True,
    ascending: bool = False,
) -> dict:
    category_ref = f"{category_table}.{category_column}"
    measure_ref = f"{MEASURE_TABLE}.{measure}"
    objects = chart_objects(fill=fill)
    from_items = [{"Name": "c", "Entity": category_table, "Type": 0}, {"Name": "m", "Entity": MEASURE_TABLE, "Type": 0}]
    selects = [column_select("c", category_table, category_column, category_display), measure_select("m", measure, measure_display)]
    if order_measure:
        order_by = {"Direction": 1 if ascending else 2, "Expression": {"Measure": {"Expression": source_ref("m"), "Property": measure}}}
    else:
        order_by = {"Direction": 1 if ascending else 2, "Expression": {"Column": {"Expression": source_ref("c"), "Property": category_column}}}
    config = {
        "name": visual_id(),
        "singleVisual": {
            "visualType": visual_type,
            "projections": {"Category": [{"queryRef": category_ref, "active": True}], "Y": [{"queryRef": measure_ref}]},
            "prototypeQuery": {"Version": 2, "From": from_items, "Select": selects, "OrderBy": [order_by]},
            "drillFilterOtherVisuals": True,
            "hasDefaultSort": True,
            "objects": objects,
            "vcObjects": visual_frame(title, subtitle),
        },
    }
    transforms = data_transforms(
        objects,
        [("Category", 0, True), ("Y", 1, False)],
        [
            {"Restatement": category_display, "Name": category_ref, "Type": 2048},
            {"Restatement": measure_display, "Name": measure_ref, "Type": 1, "Format": measure_format(measure)},
        ],
        [
            column_transform("c", category_table, category_column, category_display, "Category"),
            measure_transform(measure, measure_display, "Y", measure_format(measure)),
        ],
        {"Category": [0], "Y": [1]},
        {"Category": [{"queryRef": category_ref, "suppressConcat": False}]},
    )
    return add_container(config, pos, make_query(from_items, selects, order_by), transforms)


def multi_measure_column(
    title: str,
    subtitle: str,
    category_table: str,
    category_column: str,
    category_display: str,
    measures: list[tuple[str, str]],
    pos: dict,
    visual_type: str = "columnChart",
    order_column: str | None = None,
) -> dict:
    category_ref = f"{category_table}.{category_column}"
    objects = chart_objects(fill=BLUE, show_labels=False)
    from_items = [{"Name": "c", "Entity": category_table, "Type": 0}, {"Name": "m", "Entity": MEASURE_TABLE, "Type": 0}]
    selects = [column_select("c", category_table, category_column, category_display)]
    projections_y = []
    metadata = [{"Restatement": category_display, "Name": category_ref, "Type": 2048}]
    transform_selects = [column_transform("c", category_table, category_column, category_display, "Category")]
    roles = [("Category", 0, True)]
    for measure, display in measures:
        idx = len(selects)
        qref = f"{MEASURE_TABLE}.{measure}"
        selects.append(measure_select("m", measure, display))
        projections_y.append({"queryRef": qref})
        metadata.append({"Restatement": display, "Name": qref, "Type": 1, "Format": measure_format(measure)})
        transform_selects.append(measure_transform(measure, display, "Y", measure_format(measure)))
        roles.append(("Y", idx, False))
    order_by = None
    if order_column:
        order_by = {"Direction": 1, "Expression": {"Column": {"Expression": source_ref("c"), "Property": order_column}}}
    config = {
        "name": visual_id(),
        "singleVisual": {
            "visualType": visual_type,
            "projections": {"Category": [{"queryRef": category_ref, "active": True}], "Y": projections_y},
            "prototypeQuery": {"Version": 2, "From": from_items, "Select": selects, **({"OrderBy": [order_by]} if order_by else {})},
            "drillFilterOtherVisuals": True,
            "hasDefaultSort": True,
            "objects": objects,
            "vcObjects": visual_frame(title, subtitle),
        },
    }
    transforms = data_transforms(
        objects,
        roles,
        metadata,
        transform_selects,
        {"Category": [0], "Y": list(range(1, len(selects)))},
        {"Category": [{"queryRef": category_ref, "suppressConcat": False}]},
    )
    return add_container(config, pos, make_query(from_items, selects, order_by), transforms)


def table_visual(
    title: str,
    subtitle: str,
    fields: list[tuple[str, str, str]],
    measures: list[tuple[str, str]],
    pos: dict,
    order_measure: str | None = None,
) -> dict:
    aliases: dict[str, str] = {}
    from_items: list[dict] = []
    for table, _, _ in fields:
        if table not in aliases:
            alias = f"f{len(aliases)}"
            aliases[table] = alias
            from_items.append({"Name": alias, "Entity": table, "Type": 0})
    if measures:
        aliases[MEASURE_TABLE] = "m"
        from_items.append({"Name": "m", "Entity": MEASURE_TABLE, "Type": 0})
    selects = []
    projections = []
    metadata = []
    transform_selects = []
    for table, column, display in fields:
        qref = f"{table}.{column}"
        selects.append(column_select(aliases[table], table, column, display))
        projections.append({"queryRef": qref})
        metadata.append({"Restatement": display, "Name": qref, "Type": 2048})
        transform_selects.append(column_transform(aliases[table], table, column, display, "Values"))
    for measure, display in measures:
        qref = f"{MEASURE_TABLE}.{measure}"
        selects.append(measure_select("m", measure, display))
        projections.append({"queryRef": qref})
        metadata.append({"Restatement": display, "Name": qref, "Type": 1, "Format": measure_format(measure)})
        transform_selects.append(measure_transform(measure, display, "Values", measure_format(measure)))
    objects = {
        "grid": [{"properties": {"gridHorizontal": pbi_literal(False), "outlineColor": color("#D8E0EA")}}],
        "columnHeaders": [
            {
                "properties": {
                    "fontFamily": text("Segoe UI Semibold"),
                    "fontSize": pbi_literal(7.5),
                    "fontColor": color(TEXT_DARK),
                }
            }
        ],
        "values": [{"properties": {"fontSize": pbi_literal(7.5), "fontFamily": text("Segoe UI")}}],
    }
    order_by = None
    if order_measure:
        order_by = {"Direction": 2, "Expression": {"Measure": {"Expression": source_ref("m"), "Property": order_measure}}}
    config = {
        "name": visual_id(),
        "singleVisual": {
            "visualType": "tableEx",
            "projections": {"Values": projections},
            "prototypeQuery": {"Version": 2, "From": from_items, "Select": selects, **({"OrderBy": [order_by]} if order_by else {})},
            "drillFilterOtherVisuals": True,
            "objects": objects,
            "vcObjects": visual_frame(title, subtitle),
        },
    }
    transforms = data_transforms(
        objects,
        [("Values", idx, False) for idx in range(len(selects))],
        metadata,
        transform_selects,
        {"Values": list(range(len(selects)))},
    )
    return add_container(config, pos, make_query(from_items, selects, order_by), transforms)


def section(name: str, display_name: str, ordinal: int, visuals: list[dict]) -> dict:
    return {
        "id": ordinal,
        "name": name,
        "displayName": display_name,
        "filters": "[]",
        "ordinal": ordinal,
        "visualContainers": visuals,
        "config": json.dumps(
            {
                "objects": {
                    "background": [{"properties": {"color": color(PAGE_BG), "transparency": pbi_literal(0.0)}}],
                    "outspace": [{"properties": {"color": color(PAGE_BG), "transparency": pbi_literal(0.0)}}],
                }
            },
            separators=(",", ":"),
        ),
        "displayOption": 1,
        "width": 1280,
        "height": 720,
    }


def common_slicers(z_base: int = 10, y: int = 20) -> list[dict]:
    return [
        slicer("dim_date", "year", "Year", position(718, y, z_base, 90, 46)),
        slicer("dim_region", "region", "Region", position(822, y, z_base + 1, 118, 46)),
        slicer("dim_channel", "channel", "Channel", position(954, y, z_base + 2, 142, 46)),
        slicer("dim_device", "device", "Device", position(1110, y, z_base + 3, 118, 46)),
    ]


def page_header(title: str, subtitle: str, slicer_z: int) -> list[dict]:
    return [
        shape_box(position(0, 0, 0, 1280, 84), HEADER_BG),
        title_text(title, subtitle, position(28, 14, 1, 660, 56), title_color=TEXT_LIGHT, subtitle_color=TEXT_LIGHT_MUTED),
        *common_slicers(slicer_z, 20),
    ]


def build_layout() -> dict:
    kpis = load_kpi_summary()
    top_category = kpis.get("top_category", "Electronics")
    top_channel = kpis.get("top_channel", "Organic Search")
    roas = f"{float(kpis.get('roas', '56.52')):.2f}x"
    refund_rate = fmt_pct(kpis.get("refund_cancel_rate", "0.0789"))
    page1 = [
        *page_header(
            "E-commerce Executive Performance Dashboard",
            "Executive business overview | GMV, revenue, orders, AOV, conversion, refund/cancel, category and channel",
            10,
        ),
        kpi_card("GMV", "GMV", position(28, 106, 100, 184, 96), TEAL),
        kpi_card("Net Revenue", "Net Revenue", position(224, 106, 101, 184, 96), BLUE),
        kpi_card("Orders", "Orders", position(420, 106, 102, 184, 96), INDIGO),
        kpi_card("AOV", "AOV", position(616, 106, 103, 184, 96), TEAL),
        kpi_card("Conversion Rate", "Conversion", position(812, 106, 104, 184, 96), AMBER),
        kpi_card("Refund/Cancel Rate", "Refund/Cancel", position(1008, 106, 105, 184, 96), RED),
        insight_card("Top Category", top_category, "Highest GMV category", position(28, 214, 150, 282, 92), TEAL),
        insight_card("Top Channel", top_channel, "Highest GMV acquisition source", position(324, 214, 151, 282, 92), BLUE),
        insight_card("ROAS", roas, "Net revenue per marketing dollar", position(620, 214, 152, 282, 92), INDIGO),
        insight_card("Quality Watch", refund_rate, "Refund/cancel rate", position(916, 214, 153, 276, 92), RED),
        multi_measure_column(
            "GMV and Orders Trend",
            "Monthly movement by order month",
            "dim_date",
            "year_month",
            "Month",
            [("GMV", "GMV"), ("Net Revenue", "Net Revenue"), ("Orders", "Orders")],
            position(28, 326, 200, 704, 192),
            "columnChart",
            "year_month",
        ),
        single_measure_chart(
            "barChart",
            "Top Category by GMV",
            "Category mix driving marketplace value",
            "dim_product",
            "category",
            "Category",
            "GMV",
            "GMV",
            position(756, 326, 201, 436, 192),
            TEAL,
        ),
        single_measure_chart(
            "barChart",
            "Traffic Channel GMV",
            "Revenue contribution by acquisition channel",
            "dim_channel",
            "channel",
            "Traffic Channel",
            "GMV",
            "GMV",
            position(28, 542, 202, 552, 142),
            BLUE,
        ),
        table_visual(
            "Executive Diagnostic Table",
            "Channel-level health metrics",
            [("dim_channel", "channel", "Channel")],
            [("Sessions", "Sessions"), ("Orders", "Orders"), ("Conversion Rate", "CVR"), ("AOV", "AOV"), ("ROAS", "ROAS")],
            position(604, 542, 203, 588, 142),
            "GMV",
        ),
    ]

    page2 = [
        *page_header("Revenue and Category", "Category, subcategory, margin and regional business mix", 20),
        table_visual(
            "Category Performance Matrix",
            "GMV, net revenue, AOV and margin by category and subcategory",
            [("dim_product", "category", "Category"), ("dim_product", "subcategory", "Subcategory")],
            [("GMV", "GMV"), ("Net Revenue", "Net Revenue"), ("AOV", "AOV"), ("Contribution Margin %", "Margin %")],
            position(28, 106, 200, 668, 358),
            "GMV",
        ),
        single_measure_chart(
            "barChart",
            "Region GMV",
            "Revenue contribution by region",
            "dim_region",
            "region",
            "Region",
            "GMV",
            "GMV",
            position(724, 106, 201, 468, 178),
            BLUE,
        ),
        single_measure_chart(
            "barChart",
            "Category Margin",
            "Contribution margin by category",
            "dim_product",
            "category",
            "Category",
            "Contribution Margin",
            "Contribution Margin",
            position(724, 306, 202, 468, 158),
            TEAL,
        ),
        table_visual(
            "Top Products",
            "Product-level lookup for executive follow-up",
            [("dim_product", "product_name", "Product"), ("dim_product", "brand", "Brand")],
            [("GMV", "GMV"), ("Orders", "Orders"), ("AOV", "AOV")],
            position(28, 492, 203, 1164, 192),
            "GMV",
        ),
    ]

    page3 = [
        *page_header("Traffic and Conversion", "Channel health, conversion funnel and marketing efficiency", 30),
        kpi_card("Sessions", "Sessions", position(28, 106, 100, 214, 96), BLUE),
        kpi_card("Visitors", "Visitors", position(258, 106, 101, 214, 96), TEAL),
        kpi_card("Conversion Rate", "Conversion", position(488, 106, 102, 214, 96), AMBER),
        kpi_card("Marketing Spend", "Marketing Spend", position(718, 106, 103, 214, 96), INDIGO),
        kpi_card("ROAS", "ROAS", position(948, 106, 104, 244, 96), TEAL),
        single_measure_chart(
            "barChart",
            "Sessions by Channel",
            "Traffic demand by acquisition source",
            "dim_channel",
            "channel",
            "Channel",
            "Sessions",
            "Sessions",
            position(28, 230, 200, 552, 278),
            BLUE,
        ),
        single_measure_chart(
            "barChart",
            "Conversion Rate by Channel",
            "Where traffic converts into orders",
            "dim_channel",
            "channel",
            "Channel",
            "Conversion Rate",
            "Conversion Rate",
            position(604, 230, 201, 588, 278),
            AMBER,
        ),
        table_visual(
            "Channel Operating Table",
            "Sessions, orders, conversion, AOV, spend and ROAS",
            [("dim_channel", "channel", "Channel")],
            [
                ("Sessions", "Sessions"),
                ("Orders", "Orders"),
                ("Conversion Rate", "CVR"),
                ("AOV", "AOV"),
                ("Marketing Spend", "Spend"),
                ("ROAS", "ROAS"),
            ],
            position(28, 536, 202, 1164, 148),
            "Sessions",
        ),
    ]

    page4 = [
        *page_header("Refunds and Operations", "Refund/cancel guardrails and operational mix", 40),
        kpi_card("Refund/Cancel Rate", "Refund/Cancel Rate", position(28, 106, 100, 280, 96), RED),
        kpi_card("Refunded Orders", "Refunded Orders", position(324, 106, 101, 280, 96), "#F87171"),
        kpi_card("Cancelled Orders", "Cancelled Orders", position(620, 106, 102, 280, 96), AMBER),
        kpi_card("Completed Orders", "Completed Orders", position(916, 106, 103, 276, 96), TEAL),
        single_measure_chart(
            "lineChart",
            "Refund/Cancel Rate Trend",
            "Monthly service and fulfillment guardrail",
            "dim_date",
            "year_month",
            "Month",
            "Refund/Cancel Rate",
            "Refund/Cancel Rate",
            position(28, 230, 200, 576, 278),
            RED,
            order_measure=False,
            ascending=True,
        ),
        multi_measure_column(
            "Refunded vs Cancelled Orders",
            "Category-level operational pressure",
            "dim_product",
            "category",
            "Category",
            [("Refunded Orders", "Refunded"), ("Cancelled Orders", "Cancelled")],
            position(628, 230, 201, 564, 278),
            "columnChart",
        ),
        table_visual(
            "Status by Channel",
            "Operational quality and cancellation watchlist",
            [("dim_channel", "channel", "Channel")],
            [("Completed Orders", "Completed"), ("Refunded Orders", "Refunded"), ("Cancelled Orders", "Cancelled"), ("Refund/Cancel Rate", "Rate")],
            position(28, 536, 202, 1164, 148),
            "Refund/Cancel Rate",
        ),
    ]

    report_config = {
        "version": "5.73",
        "themeCollection": {
            "baseTheme": {
                "name": "CY26SU05",
                "version": {"visual": "2.9.0", "report": "3.3.0", "page": "2.3.1"},
                "type": 2,
            }
        },
        "activeSectionIndex": 0,
        "defaultDrillFilterOtherVisuals": True,
        "settings": {
            "useNewFilterPaneExperience": True,
            "allowChangeFilterTypes": True,
            "useStylableVisualContainerHeader": True,
            "queryLimitOption": 6,
            "useEnhancedTooltips": True,
            "exportDataMode": 1,
            "useDefaultAggregateDisplayName": True,
        },
        "objects": {
            "section": [
                {"properties": {"verticalAlignment": {"expr": {"Literal": {"Value": "'Top'"}}}}}
            ]
        },
    }

    return {
        "activeSectionIndex": 0,
        "sections": [
            section("ReportSectionExecutive", "Executive Overview", 0, page1),
            section("ReportSectionRevenue", "Revenue & Category", 1, page2),
            section("ReportSectionTraffic", "Traffic & Conversion", 2, page3),
            section("ReportSectionRefunds", "Refunds & Operations", 3, page4),
        ],
        "config": json.dumps(report_config, separators=(",", ":")),
        "layoutOptimization": 0,
    }


def main() -> None:
    layout = build_layout()
    layout_path = BUILD_DIR / "native_report_layout_ecommerce.json"
    write_json(layout_path, layout)

    summary = {
        "generated_at": "2026-06-11",
        "status": "layout_json_generated",
        "layout_json": str(layout_path),
        "pages": [section["displayName"] for section in layout["sections"]],
        "visual_containers": sum(len(section["visualContainers"]) for section in layout["sections"]),
        "measure_table": MEASURE_TABLE,
        "target_model_pbix": "output/dashboard_model.pbix",
        "target_final_pbix": "output/dashboard_final.pbix",
        "note": "This creates native Power BI report layout JSON. Packaging into PBIX is handled by 10_apply_native_pbix_report.ps1 only when a valid model PBIX exists.",
    }
    write_json(QA_DIR / "native_report_layout_summary.json", summary)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
