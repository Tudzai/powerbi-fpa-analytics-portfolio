from __future__ import annotations

import csv
import json
import uuid
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
BUILD_DIR = PROJECT_ROOT / "build"
QA_DIR = PROJECT_ROOT / "qa"
PREPARED_DIR = PROJECT_ROOT / "data" / "prepared"

MEASURE_TABLE = "KPI Measures"

PAGE_BG = "#F3F6FA"
HEADER_BG = "#111827"
PANEL_BG = "#FFFFFF"
PANEL_BORDER = "#D8E0EA"
TEXT_DARK = "#111827"
TEXT_MUTED = "#64748B"
TEXT_LIGHT = "#F8FAFC"
TEXT_LIGHT_MUTED = "#CBD5E1"
TEAL = "#0F766E"
BLUE = "#2563EB"
INDIGO = "#4F46E5"
AMBER = "#D97706"
RED = "#DC2626"
GREEN = "#16A34A"


MEASURE_FORMATS = {
    "Latest Month": "yyyy-mm-dd",
    "New Users": "#,0",
    "Active Users": "#,0",
    "Returning Users": "#,0",
    "New Customers": "#,0",
    "Active Customers": "#,0",
    "Returning Customers": "#,0",
    "Repeat Purchasers": "#,0",
    "Repeat Purchase Rate": "0.0%",
    "Churn Signal Customers": "#,0",
    "Churn Risk Revenue": "$#,0,.0K",
    "Net Revenue": "$#,0,.0K",
    "LTV To Date": "$#,0",
    "Cohort Retention %": "0.0%",
    "Cohort Repeat Purchase %": "0.0%",
    "Cumulative LTV": "$#,0",
    "Latest Active Users": "#,0",
    "Latest Returning Users": "#,0",
    "Latest Repeat Purchase Rate": "0.0%",
    "Latest Churn Signals": "#,0",
    "Latest Net Revenue": "$#,0,.0K",
}


def visual_id() -> str:
    return uuid.uuid4().hex[:20]


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def read_csv_rows(name: str) -> list[dict[str, str]]:
    path = PREPARED_DIR / name
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def latest_monthly_row() -> dict[str, str]:
    rows = read_csv_rows("MonthlyKPIs.csv")
    return rows[-1] if rows else {}


def fmt_number(value: str | float | int, digits: int = 0) -> str:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return "n/a"
    if abs(number) >= 1_000_000:
        return f"{number / 1_000_000:.{digits}f}M"
    if abs(number) >= 1_000:
        return f"{number / 1_000:.{digits}f}K"
    return f"{number:,.{digits}f}"


def fmt_money(value: str | float | int) -> str:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return "n/a"
    if abs(number) >= 1_000_000:
        return f"${number / 1_000_000:.1f}M"
    if abs(number) >= 1_000:
        return f"${number / 1_000:.1f}K"
    return f"${number:,.0f}"


def fmt_pct(value: str | float | int) -> str:
    try:
        return f"{float(value):.1%}"
    except (TypeError, ValueError):
        return "n/a"


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


def measure_format(measure: str) -> str:
    return MEASURE_FORMATS.get(measure, "#,0")


def measure_transform(measure: str, display: str, role: str) -> dict:
    return {
        "displayName": display,
        "queryName": f"{MEASURE_TABLE}.{measure}",
        "roles": {role: True},
        "type": {"category": None, "underlyingType": 259},
        "expr": {"Measure": {"Expression": entity_ref("m"), "Property": measure}},
        "format": measure_format(measure),
        "sort": 2,
        "sortOrder": 0,
    }


def make_query(from_items: list[dict], selects: list[dict], order_by: dict | None = None) -> str:
    query = {"Version": 2, "From": from_items, "Select": selects}
    if order_by:
        query["OrderBy"] = [order_by]
    return json.dumps(
        {
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
    shadow_transparency: float = 86.0,
    border_show: bool = True,
) -> dict:
    vc = {
        "background": [{"properties": {"show": pbi_literal(True), "color": color(fill), "transparency": pbi_literal(0.0)}}],
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


def title_text(title: str, subtitle: str, pos: dict) -> dict:
    objects = {
        "general": [
            {
                "properties": {
                    "paragraphs": [
                        {
                            "textRuns": [
                                {
                                    "value": title,
                                    "textStyle": {"fontFamily": "Segoe UI Semibold", "fontSize": "20pt", "color": TEXT_LIGHT},
                                },
                                {
                                    "value": f"\n{subtitle}",
                                    "textStyle": {"fontFamily": "Segoe UI", "fontSize": "8.5pt", "color": TEXT_LIGHT_MUTED},
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
                                    "textStyle": {"fontFamily": "Segoe UI Semibold", "fontSize": "6.5pt", "color": TEXT_MUTED},
                                },
                                {
                                    "value": f"\n{value}",
                                    "textStyle": {"fontFamily": "Segoe UI Semibold", "fontSize": "14pt", "color": accent},
                                },
                                {
                                    "value": f"\n{caption}",
                                    "textStyle": {"fontFamily": "Segoe UI", "fontSize": "6.5pt", "color": TEXT_MUTED},
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


def card(measure: str, display: str, pos: dict, value_color: str = TEAL) -> dict:
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
                    "fontColor": color(TEXT_MUTED),
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
            "vcObjects": visual_frame(display, fill=PANEL_BG, border_fill=PANEL_BORDER, shadow_transparency=80.0),
        },
    }
    transforms = data_transforms(
        objects,
        [("Data", 0, False)],
        [{"Restatement": display, "Name": qref, "Type": 1, "Format": measure_format(measure)}],
        [measure_transform(measure, display, "Data")],
        {"Data": [0]},
    )
    return add_container(config, pos, make_query(from_items, selects), transforms)


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
                    "labelDisplayUnits": pbi_literal(1000.0),
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
    order_column: str | None = None,
    order_measure: bool = False,
    ascending: bool = True,
) -> dict:
    category_ref = f"{category_table}.{category_column}"
    measure_ref = f"{MEASURE_TABLE}.{measure}"
    objects = chart_objects(fill=fill)
    from_items = [{"Name": "c", "Entity": category_table, "Type": 0}, {"Name": "m", "Entity": MEASURE_TABLE, "Type": 0}]
    selects = [column_select("c", category_table, category_column, category_display), measure_select("m", measure, measure_display)]
    order_by = None
    if order_column:
        order_by = {"Direction": 1 if ascending else 2, "Expression": {"Column": {"Expression": source_ref("c"), "Property": order_column}}}
    elif order_measure:
        order_by = {"Direction": 1 if ascending else 2, "Expression": {"Measure": {"Expression": source_ref("m"), "Property": measure}}}
    config = {
        "name": visual_id(),
        "singleVisual": {
            "visualType": visual_type,
            "projections": {"Category": [{"queryRef": category_ref, "active": True}], "Y": [{"queryRef": measure_ref}]},
            "prototypeQuery": {"Version": 2, "From": from_items, "Select": selects, **({"OrderBy": [order_by]} if order_by else {})},
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
            measure_transform(measure, measure_display, "Y"),
        ],
        {"Category": [0], "Y": [1]},
        {"Category": [{"queryRef": category_ref, "suppressConcat": False}]},
    )
    return add_container(config, pos, make_query(from_items, selects, order_by), transforms)


def multi_measure_chart(
    visual_type: str,
    title: str,
    subtitle: str,
    category_table: str,
    category_column: str,
    category_display: str,
    measures: list[tuple[str, str]],
    pos: dict,
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
        transform_selects.append(measure_transform(measure, display, "Y"))
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
        transform_selects.append(measure_transform(measure, display, "Values"))
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
        "values": [{"properties": {"fontSize": pbi_literal(7.3), "fontFamily": text("Segoe UI")}}],
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
        slicer("DimMonth", "Year", "Year", position(704, y, z_base, 84, 46)),
        slicer("DimUser", "AcquisitionChannel", "Channel", position(802, y, z_base + 1, 128, 46)),
        slicer("DimUser", "Region", "Region", position(944, y, z_base + 2, 118, 46)),
        slicer("DimUser", "PlanTier", "Plan", position(1076, y, z_base + 3, 118, 46)),
    ]


def page_header(title: str, subtitle: str, slicer_z: int) -> list[dict]:
    return [
        shape_box(position(0, 0, 0, 1280, 84), HEADER_BG),
        title_text(title, subtitle, position(28, 14, 1, 650, 56)),
        *common_slicers(slicer_z, 20),
    ]


def build_layout() -> dict:
    latest = latest_monthly_row()
    latest_month = latest.get("MonthYear", "Latest month")
    active_users = fmt_number(latest.get("ActiveUsers", "0"))
    repeat_rate = fmt_pct(latest.get("RepeatPurchaseRate", "0"))
    ltv = fmt_money(latest.get("LTVToDate", "0"))
    churn_risk = fmt_money(latest.get("ChurnRiskRevenue", "0"))

    page1 = [
        *page_header(
            "Retention & Cohort Dashboard",
            "User lifecycle control tower | new vs returning, repeat purchase, LTV and churn signals",
            10,
        ),
        card("Latest Active Users", "Active Users", position(28, 106, 100, 184, 96), BLUE),
        card("Latest Returning Users", "Returning Users", position(224, 106, 101, 184, 96), TEAL),
        card("Latest Repeat Purchase Rate", "Repeat Purchase", position(420, 106, 102, 184, 96), GREEN),
        card("Latest Churn Signals", "Churn Signals", position(616, 106, 103, 184, 96), RED),
        card("Latest Net Revenue", "Net Revenue", position(812, 106, 104, 184, 96), INDIGO),
        insight_card("Latest Month", latest_month, "Complete reporting month", position(1008, 106, 105, 184, 96), AMBER),
        multi_measure_chart(
            "lineChart",
            "New vs Returning Users",
            "Monthly acquisition and re-engagement pattern",
            "DimMonth",
            "MonthYear",
            "Month",
            [("New Users", "New Users"), ("Returning Users", "Returning Users")],
            position(28, 226, 200, 586, 210),
            "MonthIndex",
        ),
        single_measure_chart(
            "lineChart",
            "Repeat Purchase Rate",
            "Share of active customers with repeat purchases",
            "DimMonth",
            "MonthYear",
            "Month",
            "Repeat Purchase Rate",
            "Repeat Purchase",
            position(638, 226, 201, 556, 210),
            GREEN,
            "MonthIndex",
        ),
        multi_measure_chart(
            "columnChart",
            "Lifecycle Volume",
            "New, active and returning customer scale",
            "DimMonth",
            "MonthYear",
            "Month",
            [("New Customers", "New Customers"), ("Active Customers", "Active Customers"), ("Returning Customers", "Returning Customers")],
            position(28, 464, 202, 586, 190),
            "MonthIndex",
        ),
        table_visual(
            "Monthly Lifecycle Detail",
            "Reconciles the hero cards and trend views",
            [("DimMonth", "MonthYear", "Month")],
            [
                ("Active Users", "Active Users"),
                ("New Users", "New Users"),
                ("Returning Users", "Returning Users"),
                ("Repeat Purchase Rate", "Repeat %"),
                ("Net Revenue", "Revenue"),
            ],
            position(638, 464, 203, 556, 190),
            "Active Users",
        ),
    ]

    page2 = [
        *page_header(
            "Monthly Cohort Retention",
            "Cohort age, repeat purchase and retained customer quality",
            20,
        ),
        insight_card("Latest Active", active_users, "Users active in latest month", position(28, 106, 100, 260, 88), BLUE),
        insight_card("Repeat Purchase", repeat_rate, "Latest repeat purchase rate", position(306, 106, 101, 260, 88), GREEN),
        insight_card("LTV", ltv, "Latest LTV to date", position(584, 106, 102, 260, 88), INDIGO),
        insight_card("Churn Risk", churn_risk, "Revenue exposed to churn", position(862, 106, 103, 332, 88), RED),
        table_visual(
            "Cohort Retention Matrix",
            "Cohort month by age with retention, repeat rate and cumulative LTV",
            [("CohortRetention", "CohortMonthLabel", "Cohort"), ("CohortRetention", "MonthsSinceCohort", "Age")],
            [
                ("Cohort Retention %", "Retention %"),
                ("Cohort Repeat Purchase %", "Repeat %"),
                ("Cumulative LTV", "Cumulative LTV"),
            ],
            position(28, 224, 200, 742, 416),
            "Cohort Retention %",
        ),
        single_measure_chart(
            "lineChart",
            "Retention by Cohort Age",
            "Retention curve across months since first purchase",
            "CohortRetention",
            "MonthsSinceCohort",
            "Age",
            "Cohort Retention %",
            "Retention %",
            position(794, 224, 201, 400, 192),
            BLUE,
            "MonthsSinceCohort",
        ),
        single_measure_chart(
            "lineChart",
            "Repeat Purchase by Cohort Age",
            "Repeat purchase curve across months since first purchase",
            "CohortRetention",
            "MonthsSinceCohort",
            "Age",
            "Cohort Repeat Purchase %",
            "Repeat %",
            position(794, 448, 202, 400, 192),
            GREEN,
            "MonthsSinceCohort",
        ),
    ]

    page3 = [
        *page_header("LTV & Revenue Cohorts", "Customer value development by month, cohort age and segment", 30),
        card("LTV To Date", "LTV To Date", position(28, 106, 100, 216, 96), INDIGO),
        card("Net Revenue", "Net Revenue", position(260, 106, 101, 216, 96), BLUE),
        card("Repeat Purchase Rate", "Repeat Purchase", position(492, 106, 102, 216, 96), GREEN),
        card("Churn Risk Revenue", "Churn Risk Revenue", position(724, 106, 103, 216, 96), RED),
        card("Active Customers", "Active Customers", position(956, 106, 104, 238, 96), TEAL),
        multi_measure_chart(
            "lineChart",
            "Revenue and LTV Trend",
            "Net revenue and LTV movement by reporting month",
            "DimMonth",
            "MonthYear",
            "Month",
            [("Net Revenue", "Net Revenue"), ("LTV To Date", "LTV To Date")],
            position(28, 232, 200, 580, 230),
            "MonthIndex",
        ),
        single_measure_chart(
            "lineChart",
            "Cumulative LTV by Cohort Age",
            "Value accrued after first purchase",
            "CohortRetention",
            "MonthsSinceCohort",
            "Age",
            "Cumulative LTV",
            "Cumulative LTV",
            position(632, 232, 201, 562, 230),
            INDIGO,
            "MonthsSinceCohort",
        ),
        table_visual(
            "Segment Value Detail",
            "Segment-level active customers, repeat rate, revenue, churn and LTV",
            [
                ("SegmentMonthly", "SegmentType", "Segment Type"),
                ("SegmentMonthly", "SegmentName", "Segment"),
                ("SegmentMonthly", "ActiveCustomers", "Active Customers"),
                ("SegmentMonthly", "RepeatPurchaseRate", "Repeat Rate"),
                ("SegmentMonthly", "NetRevenue", "Revenue"),
                ("SegmentMonthly", "LTVToDate", "LTV"),
                ("SegmentMonthly", "ChurnSignalCustomers", "Churn Signals"),
            ],
            [],
            position(28, 494, 202, 1166, 160),
        ),
    ]

    page4 = [
        *page_header("Churn Signal & Winback", "Risk detection, exposed revenue and action list", 40),
        card("Latest Churn Signals", "Latest Churn Signals", position(28, 106, 100, 236, 96), RED),
        card("Churn Risk Revenue", "Churn Risk Revenue", position(280, 106, 101, 236, 96), RED),
        card("Latest Repeat Purchase Rate", "Repeat Purchase", position(532, 106, 102, 236, 96), GREEN),
        card("Latest Active Users", "Active Users", position(784, 106, 103, 236, 96), BLUE),
        insight_card("Action View", "Winback", "Prioritize high risk and high value users", position(1036, 106, 104, 158, 96), AMBER),
        single_measure_chart(
            "columnChart",
            "Churn Signal Trend",
            "Customers crossing churn signal threshold by month",
            "DimMonth",
            "MonthYear",
            "Month",
            "Churn Signal Customers",
            "Churn Signals",
            position(28, 232, 200, 486, 210),
            RED,
            "MonthIndex",
        ),
        table_visual(
            "Risk Band Snapshot",
            "User-level risk signal with revenue and recommended action",
            [
                ("ChurnRiskSnapshot", "RiskBand", "Risk Band"),
                ("ChurnRiskSnapshot", "UserID", "User ID"),
                ("ChurnRiskSnapshot", "DaysSinceLastPurchase", "Days Since Last Purchase"),
                ("ChurnRiskSnapshot", "LifetimeOrders", "Lifetime Orders"),
                ("ChurnRiskSnapshot", "LifetimeNetRevenue", "Lifetime Revenue"),
                ("ChurnRiskSnapshot", "RecommendedAction", "Action"),
            ],
            [],
            position(538, 232, 201, 656, 210),
        ),
        table_visual(
            "Winback Candidate Detail",
            "Operational follow-up list for customer lifecycle teams",
            [
                ("ChurnRiskSnapshot", "UserID", "User ID"),
                ("ChurnRiskSnapshot", "AcquisitionChannel", "Channel"),
                ("ChurnRiskSnapshot", "Region", "Region"),
                ("ChurnRiskSnapshot", "PlanTier", "Plan"),
                ("ChurnRiskSnapshot", "CustomerSegment", "Segment"),
                ("ChurnRiskSnapshot", "RiskScore", "Risk Score"),
                ("ChurnRiskSnapshot", "RiskBand", "Risk Band"),
                ("ChurnRiskSnapshot", "RecommendedAction", "Recommended Action"),
            ],
            [],
            position(28, 474, 202, 1166, 180),
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
        "objects": {"section": [{"properties": {"verticalAlignment": {"expr": {"Literal": {"Value": "'Top'"}}}}}]},
    }

    return {
        "activeSectionIndex": 0,
        "sections": [
            section("ReportSectionLifecycle", "Lifecycle Overview", 0, page1),
            section("ReportSectionCohort", "Monthly Cohort Retention", 1, page2),
            section("ReportSectionLTV", "LTV & Revenue Cohorts", 2, page3),
            section("ReportSectionChurn", "Churn Signal & Winback", 3, page4),
        ],
        "config": json.dumps(report_config, separators=(",", ":")),
        "layoutOptimization": 0,
    }


def main() -> None:
    layout = build_layout()
    layout_path = BUILD_DIR / "native_report_layout_retention.json"
    write_json(layout_path, layout)
    summary = {
        "generated_at": "2026-06-11",
        "status": "layout_json_generated",
        "layout_json": str(layout_path),
        "pages": [section["displayName"] for section in layout["sections"]],
        "visual_containers": sum(len(section["visualContainers"]) for section in layout["sections"]),
        "measure_table": MEASURE_TABLE,
        "target_model_pbix": str(PROJECT_ROOT / "output" / "dashboard_model.pbix"),
        "target_final_pbix": str(PROJECT_ROOT / "output" / "dashboard_final.pbix"),
    }
    write_json(QA_DIR / "native_report_layout_summary.json", summary)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
