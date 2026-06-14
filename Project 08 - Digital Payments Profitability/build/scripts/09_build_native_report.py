from __future__ import annotations

import json
import uuid
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
BUILD_DIR = PROJECT_ROOT / "build"
OUTPUT_DIR = PROJECT_ROOT / "output"

MEASURE_TABLE = "KPI Measures"


def visual_id() -> str:
    return uuid.uuid4().hex[:20]


def write_json(path: Path, payload: dict) -> None:
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
    "Revenue": "#,0",
    "Actual Revenue": "#,0",
    "Budget Revenue": "#,0",
    "Forecast Revenue": "#,0",
    "Actual Revenue Current Month": "#,0",
    "Budget Revenue Current Month": "#,0",
    "Forecast Revenue Current Month": "#,0",
    "Gross Margin": "#,0",
    "Actual Gross Margin": "#,0",
    "Gross Margin %": "0.0%",
    "EBITDA": "#,0",
    "Actual EBITDA": "#,0",
    "Budget EBITDA": "#,0",
    "Actual EBITDA Current Month": "#,0",
    "EBITDA %": "0.0%",
    "EBITDA Var vs Budget": "#,0",
    "Revenue Var vs Budget": "#,0",
    "Allocated Opex": "#,0",
    "Actual Opex": "#,0",
    "Budget Opex": "#,0",
    "Department Opex": "#,0",
    "Actual Cash Balance": "#,0",
    "Budget Cash Balance": "#,0",
    "Actual Cash Balance Current Month": "#,0",
    "Budget Cash Balance Current Month": "#,0",
    "Cash Var Current Month vs Budget": "#,0",
    "Cash Balance Latest Month": "#,0",
    "Bridge Amount": "#,0",
    "Orders": "#,0",
    "Weighted DSO": "#,0.0",
    "Weighted DSO Current Month": "#,0.0",
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


def visual_frame(title: str | None = None, subtitle: str | None = None) -> dict:
    vc = {
        "background": [
            {"properties": {"show": pbi_literal(True), "color": color("#FFFFFF"), "transparency": pbi_literal(0.0)}}
        ],
        "border": [
            {
                "properties": {
                    "show": pbi_literal(True),
                    "color": color("#D8DEE9"),
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
                    "color": color("#94A3B8"),
                    "transparency": pbi_literal(86.0),
                    "angle": pbi_literal(45.0),
                    "distance": pbi_literal(1.0),
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
                    "fontColor": color("#1F2937"),
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
                    "fontColor": color("#64748B"),
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
                                    "textStyle": {
                                        "fontFamily": "Segoe UI Semibold",
                                        "fontSize": "20pt",
                                        "color": "#111827",
                                    },
                                },
                                {
                                    "value": f"\n{subtitle}",
                                    "textStyle": {
                                        "fontFamily": "Segoe UI",
                                        "fontSize": "8.5pt",
                                        "color": "#64748B",
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


def card(measure: str, display: str, pos: dict, value_color: str = "#EA580C") -> dict:
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
                    "fontSize": pbi_literal(23.0),
                    "fontFamily": text("Segoe UI Semibold"),
                    "fontColor": color(value_color),
                },
                "selector": {"metadata": qref},
            }
        ],
        "label": [
            {
                "properties": {
                    "show": pbi_literal(True),
                    "position": text("belowValue"),
                    "fontSize": pbi_literal(7.5),
                    "fontFamily": text("Segoe UI"),
                    "fontColor": color("#475569"),
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
            "vcObjects": visual_frame(display),
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


def slicer(table: str, column: str, display: str, pos: dict) -> dict:
    qref = f"{table}.{column}"
    objects = {
        "data": [{"properties": {"mode": text("Dropdown")}}],
        "selection": [{"properties": {"selectAllCheckboxEnabled": pbi_literal(True), "singleSelect": pbi_literal(False)}}],
        "header": [
            {
                "properties": {
                    "show": pbi_literal(False),
                    "text": text(display),
                    "textSize": pbi_literal(7.5),
                    "fontColor": color("#9A3412"),
                    "fontFamily": text("Segoe UI Semibold"),
                }
            }
        ],
        "items": [
            {
                "properties": {
                    "textSize": pbi_literal(7.5),
                    "fontColor": color("#111827"),
                    "fontFamily": text("Segoe UI"),
                }
            }
        ],
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
            "vcObjects": visual_frame(display),
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


def chart_objects(fill: str = "#F97316", show_labels: bool = True) -> dict:
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
        "labels": [
            {
                "properties": {
                    "show": pbi_literal(show_labels),
                    "labelDisplayUnits": pbi_literal(1000000.0),
                    "fontSize": pbi_literal(7.0),
                }
            }
        ],
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
    fill: str = "#F97316",
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
    return add_container(config, pos, make_query(from_items, selects, order_by, top=visual_type == "waterfallChart"), transforms)


def multi_measure_column(
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
    objects = chart_objects(fill="#F97316", show_labels=False)
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
            "visualType": "columnChart",
            "projections": {"Category": [{"queryRef": category_ref, "active": True}], "Y": projections_y},
            "prototypeQuery": {"Version": 2, "From": from_items, "Select": selects, **({"OrderBy": [order_by]} if order_by else {})},
            "drillFilterOtherVisuals": True,
            "hasDefaultSort": True,
            "objects": objects,
            "vcObjects": visual_frame(title, subtitle),
        },
    }
    projection_ordering = {"Category": [0], "Y": list(range(1, len(selects)))}
    transforms = data_transforms(
        objects,
        roles,
        metadata,
        transform_selects,
        projection_ordering,
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
    for idx, (table, _, _) in enumerate(fields):
        if table not in aliases:
            alias = f"f{idx}"
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
        "grid": [{"properties": {"gridHorizontal": pbi_literal(False), "outlineColor": color("#FED7AA")}}],
        "columnHeaders": [
            {
                "properties": {
                    "fontFamily": text("Segoe UI Semibold"),
                    "fontSize": pbi_literal(7.5),
                    "fontColor": color("#9A3412"),
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
                    "background": [{"properties": {"color": color("#F8FAFC"), "transparency": pbi_literal(0.0)}}],
                    "outspace": [{"properties": {"color": color("#F8FAFC"), "transparency": pbi_literal(0.0)}}],
                }
            },
            separators=(",", ":"),
        ),
        "displayOption": 1,
        "width": 1280,
        "height": 720,
    }


def build_layout() -> dict:
    kpi_x = [24, 260, 496, 732, 968]
    slicer_y = 18
    page1 = [
        title_text("Monthly FP&A Performance Pack", "Executive KPI view | May 2026 latest actual", position(24, 14, 1, 455, 54)),
        slicer("DimDate", "Year", "Year", position(700, slicer_y, 10, 110, 48)),
        slicer("DimBusinessUnit", "BusinessUnit", "BU", position(824, slicer_y, 11, 146, 48)),
        slicer("DimRegion", "Region", "Region", position(984, slicer_y, 12, 100, 48)),
        slicer("DimProduct", "Product", "Product", position(1098, slicer_y, 13, 88, 48)),
        card("Actual Revenue Current Month", "Revenue", position(kpi_x[0], 88, 100, 208, 92)),
        card("Gross Margin %", "GM %", position(kpi_x[1], 88, 101, 208, 92), "#0F766E"),
        card("Actual EBITDA Current Month", "EBITDA", position(kpi_x[2], 88, 102, 208, 92), "#EA580C"),
        card("Actual Opex", "Opex", position(kpi_x[3], 88, 103, 208, 92), "#B45309"),
        card("Actual Cash Balance Current Month", "Cash", position(kpi_x[4], 88, 104, 208, 92), "#0F766E"),
        multi_measure_column(
            "Revenue Trend",
            "Actual, Budget, Forecast by month",
            "DimDate",
            "MonthYear",
            "Month",
            [("Actual Revenue", "Actual"), ("Budget Revenue", "Budget"), ("Forecast Revenue", "Forecast")],
            position(24, 210, 200, 760, 300),
            "MonthIndex",
        ),
        single_measure_chart(
            "barChart",
            "EBITDA Variance by BU",
            "Actual less Budget",
            "DimBusinessUnit",
            "BusinessUnit",
            "Business Unit",
            "EBITDA Var vs Budget",
            "EBITDA Var",
            position(814, 210, 201, 372, 300),
            "#EA580C",
        ),
        table_visual(
            "Actual vs Budget vs Forecast",
            "Scenario comparison for core KPIs",
            [("DimScenario", "Scenario", "Scenario")],
            [
                ("Revenue", "Revenue"),
                ("Gross Margin %", "GM %"),
                ("EBITDA", "EBITDA"),
                ("Allocated Opex", "Opex"),
                ("Cash Balance Latest Month", "Cash"),
            ],
            position(24, 540, 300, 760, 150),
        ),
        single_measure_chart(
            "barChart",
            "Revenue Variance by Region",
            "Actual less Budget",
            "DimRegion",
            "Region",
            "Region",
            "Revenue Var vs Budget",
            "Revenue Var",
            position(814, 540, 301, 372, 150),
            "#C2410C",
        ),
    ]

    page2 = [
        title_text("Variance Bridge", "Budget to Actual EBITDA and driver views", position(24, 14, 1, 455, 54)),
        slicer("DimBusinessUnit", "BusinessUnit", "BU", position(824, slicer_y, 11, 146, 48)),
        slicer("DimRegion", "Region", "Region", position(984, slicer_y, 12, 100, 48)),
        slicer("DimProduct", "Product", "Product", position(1098, slicer_y, 13, 88, 48)),
        single_measure_chart(
            "waterfallChart",
            "Budget to Actual EBITDA Bridge",
            "Bridge steps by May 2026",
            "FactBridge",
            "BridgeStep",
            "Bridge Step",
            "Bridge Amount",
            "Amount",
            position(24, 88, 100, 760, 390),
            "#F97316",
            order_measure=False,
            ascending=True,
        ),
        single_measure_chart(
            "barChart",
            "Revenue Variance by Product",
            "Actual less Budget",
            "DimProduct",
            "Product",
            "Product",
            "Revenue Var vs Budget",
            "Revenue Var",
            position(814, 88, 101, 372, 390),
            "#EA580C",
        ),
        table_visual(
            "Variance Detail by BU / Region",
            "Revenue and EBITDA variance",
            [("DimBusinessUnit", "BusinessUnit", "Business Unit"), ("DimRegion", "Region", "Region")],
            [
                ("Actual Revenue", "Actual Rev"),
                ("Budget Revenue", "Budget Rev"),
                ("Revenue Var vs Budget", "Rev Var"),
                ("Actual EBITDA", "Actual EBITDA"),
                ("EBITDA Var vs Budget", "EBITDA Var"),
            ],
            position(24, 505, 200, 1162, 185),
            "EBITDA Var vs Budget",
        ),
    ]

    page3 = [
        title_text("Dimension Drilldown", "Customer, product and region views", position(24, 14, 1, 455, 54)),
        slicer("DimCustomer", "Customer", "Customer", position(650, slicer_y, 10, 210, 48)),
        slicer("DimProduct", "Product", "Product", position(876, slicer_y, 11, 146, 48)),
        slicer("DimRegion", "Region", "Region", position(1038, slicer_y, 12, 148, 48)),
        single_measure_chart(
            "barChart",
            "Top Customers by Revenue",
            "Current filter context",
            "DimCustomer",
            "Customer",
            "Customer",
            "Actual Revenue",
            "Revenue",
            position(24, 88, 100, 560, 285),
            "#F97316",
        ),
        single_measure_chart(
            "columnChart",
            "Revenue by Region",
            "Current filter context",
            "DimRegion",
            "Region",
            "Region",
            "Actual Revenue",
            "Revenue",
            position(616, 88, 101, 260, 285),
            "#EA580C",
        ),
        single_measure_chart(
            "barChart",
            "EBITDA Variance by Product",
            "Actual less Budget",
            "DimProduct",
            "Product",
            "Product",
            "EBITDA Var vs Budget",
            "EBITDA Var",
            position(904, 88, 102, 282, 285),
            "#C2410C",
        ),
        table_visual(
            "Customer / Product / Region Detail",
            "Lookup table for drilldown",
            [
                ("DimCustomer", "Customer", "Customer"),
                ("DimCustomer", "CustomerSegment", "Segment"),
                ("DimProduct", "Product", "Product"),
                ("DimRegion", "Region", "Region"),
            ],
            [
                ("Actual Revenue", "Revenue"),
                ("Gross Margin %", "GM %"),
                ("Actual EBITDA", "EBITDA"),
                ("EBITDA Var vs Budget", "EBITDA Var"),
            ],
            position(24, 400, 200, 1162, 290),
            "Actual Revenue",
        ),
    ]

    page4 = [
        title_text("Opex & Cash Control", "Spend, cash balance and working capital KPIs", position(24, 14, 1, 520, 54)),
        slicer("DimBusinessUnit", "BusinessUnit", "BU", position(760, slicer_y, 11, 146, 48)),
        slicer("DimRegion", "Region", "Region", position(920, slicer_y, 12, 100, 48)),
        slicer("DimDepartment", "Department", "Dept", position(1034, slicer_y, 13, 152, 48)),
        card("Actual Opex", "Actual Opex", position(kpi_x[0], 88, 100, 208, 92), "#B45309"),
        card("Budget Opex", "Budget Opex", position(kpi_x[1], 88, 101, 208, 92), "#64748B"),
        card("Actual Cash Balance Current Month", "Cash Balance", position(kpi_x[2], 88, 102, 208, 92), "#0F766E"),
        card("Cash Var Current Month vs Budget", "Cash Var", position(kpi_x[3], 88, 103, 208, 92), "#0F766E"),
        card("Weighted DSO Current Month", "Weighted DSO", position(kpi_x[4], 88, 104, 208, 92), "#EA580C"),
        single_measure_chart(
            "barChart",
            "Department Opex",
            "Actual + Budget + Forecast total by department",
            "DimDepartment",
            "Department",
            "Department",
            "Department Opex",
            "Opex",
            position(24, 210, 200, 560, 310),
            "#EA580C",
        ),
        multi_measure_column(
            "Cash Balance Trend",
            "Actual, Budget, Forecast by month",
            "DimDate",
            "MonthYear",
            "Month",
            [("Actual Cash Balance", "Actual"), ("Budget Cash Balance", "Budget"), ("Forecast Cash Balance", "Forecast")],
            position(616, 210, 201, 570, 310),
            "MonthIndex",
        ),
        table_visual(
            "Cash Detail by Region",
            "Cash and revenue context",
            [("DimRegion", "Region", "Region")],
            [
                ("Actual Cash Balance", "Cash"),
                ("Budget Cash Balance", "Budget Cash"),
                ("Cash Var vs Budget", "Cash Var"),
                ("Actual Revenue", "Revenue"),
                ("Actual EBITDA", "EBITDA"),
            ],
            position(24, 548, 300, 1162, 142),
            "Actual Cash Balance",
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
                {
                    "properties": {
                        "verticalAlignment": text("Top"),
                    }
                }
            ]
        },
    }
    return {
        "id": 0,
        "resourcePackages": [
            {
                "resourcePackage": {
                    "name": "SharedResources",
                    "type": 2,
                    "items": [{"type": 202, "path": "BaseThemes/CY26SU05.json", "name": "CY26SU05"}],
                    "disabled": False,
                }
            }
        ],
        "sections": [
            section("v06_executive_kpi", "Executive KPI", 0, page1),
            section("v06_variance_bridge", "Variance Bridge", 1, page2),
            section("v06_dimension_drilldown", "Dimension Drilldown", 2, page3),
            section("v06_opex_cash", "Opex & Cash", 3, page4),
        ],
        "config": json.dumps(report_config, separators=(",", ":")),
        "layoutOptimization": 0,
    }


def build_layout_project8() -> dict:
    MEASURE_FORMATS.update(
        {
            "Payment GMV": "$#,0",
            "Transactions": "#,0",
            "Revenue": "$#,0",
            "Take Rate": "0.0%",
            "Contribution Margin": "$#,0",
            "Contribution Margin %": "0.0%",
            "Variable Cost": "$#,0",
            "Cost per Transaction": "$0.00",
            "Refund Amount": "$#,0",
            "Refund Rate": "0.0%",
            "Chargeback Amount": "$#,0",
            "Chargeback Bps": "0.0",
            "Auth Success Rate": "0.0%",
            "Revenue per Transaction": "$0.00",
            "Current GMV": "$#,0",
            "Current Transactions": "#,0",
            "Current Revenue": "$#,0",
            "Current Take Rate": "0.0%",
            "Current Contribution Margin": "$#,0",
            "Current CM %": "0.0%",
            "Current Variable Cost": "$#,0",
            "Current Cost per Transaction": "$0.00",
            "MoM GMV Growth": "0.0%",
            "MoM Revenue Growth": "0.0%",
            "Bridge Amount": "$#,0",
            "Scenario GMV": "$#,0",
            "Scenario Revenue": "$#,0",
            "Scenario Variable Cost": "$#,0",
            "Scenario Contribution Margin": "$#,0",
            "Scenario CM %": "0.0%",
            "Scenario Margin Uplift": "$#,0",
            "Scenario Take Rate Delta Bps": "0",
            "Scenario Cost Delta %": "0.0%",
            "Scenario Volume Elasticity": "0.0%",
            "Merchant Rank by CM": "#,0",
        }
    )

    blue = "#2563EB"
    cyan = "#0891B2"
    green = "#16A34A"
    teal = "#0F766E"
    amber = "#D97706"
    red = "#DC2626"
    violet = "#7C3AED"
    slate = "#475569"
    kpi_x = [24, 228, 432, 636, 840, 1044]
    slicer_y = 18

    def global_slicers(z: int) -> list[dict]:
        return [
            slicer("dim_date", "year_month", "Month", position(700, slicer_y, z, 108, 48)),
            slicer("dim_merchant", "merchant_segment", "Segment", position(822, slicer_y, z + 1, 126, 48)),
            slicer("dim_payment_method", "payment_method", "Method", position(962, slicer_y, z + 2, 138, 48)),
            slicer("dim_channel", "channel", "Channel", position(1114, slicer_y, z + 3, 142, 48)),
        ]

    page1 = [
        title_text(
            "Digital Payments Profitability",
            "Executive Overview | GMV, transaction volume, revenue, take rate, contribution margin, and MoM growth",
            position(24, 14, 1, 660, 54),
        ),
        *global_slicers(10),
        card("Current GMV", "GMV", position(kpi_x[0], 88, 100, 188, 86), blue),
        card("Current Transactions", "Transactions", position(kpi_x[1], 88, 101, 188, 86), cyan),
        card("Current Revenue", "Revenue", position(kpi_x[2], 88, 102, 188, 86), green),
        card("Current Take Rate", "Take Rate", position(kpi_x[3], 88, 103, 188, 86), teal),
        card("Current Contribution Margin", "Contribution Margin", position(kpi_x[4], 88, 104, 188, 86), violet),
        card("MoM GMV Growth", "MoM GMV", position(kpi_x[5], 88, 105, 188, 86), amber),
        single_measure_chart(
            "lineChart",
            "GMV Trend",
            "Monthly payment volume",
            "dim_date",
            "year_month",
            "Month",
            "Payment GMV",
            "GMV",
            position(24, 198, 210, 496, 220),
            blue,
            False,
            True,
        ),
        single_measure_chart(
            "lineChart",
            "Revenue Trend",
            "Monthly fee revenue",
            "dim_date",
            "year_month",
            "Month",
            "Revenue",
            "Revenue",
            position(544, 198, 211, 332, 220),
            green,
            False,
            True,
        ),
        single_measure_chart(
            "barChart",
            "Contribution Margin by Segment",
            "Current selection",
            "dim_merchant",
            "merchant_segment",
            "Segment",
            "Contribution Margin",
            "CM",
            position(900, 198, 212, 356, 220),
            violet,
        ),
        table_visual(
            "Top Merchants",
            "GMV, revenue, take-rate, and margin",
            [
                ("dim_merchant", "merchant_name", "Merchant"),
                ("dim_merchant", "merchant_segment", "Segment"),
                ("dim_merchant", "vertical", "Vertical"),
            ],
            [
                ("Current GMV", "GMV"),
                ("Current Revenue", "Revenue"),
                ("Current Take Rate", "Take Rate"),
                ("Current Contribution Margin", "CM"),
                ("Current CM %", "CM %"),
            ],
            position(24, 444, 300, 1232, 246),
            "Current Contribution Margin",
        ),
    ]

    page2 = [
        title_text(
            "Merchant & Transaction Drivers",
            "Merchant segment, payment method, channel, refund, chargeback, and top/bottom merchant diagnostics",
            position(24, 14, 1, 660, 54),
        ),
        *global_slicers(20),
        card("Auth Success Rate", "Auth Success", position(kpi_x[0], 88, 100, 188, 86), green),
        card("Refund Rate", "Refund Rate", position(kpi_x[1], 88, 101, 188, 86), amber),
        card("Chargeback Bps", "Chargeback Bps", position(kpi_x[2], 88, 102, 188, 86), red),
        card("Cost per Transaction", "Cost / Txn", position(kpi_x[3], 88, 103, 188, 86), amber),
        card("Contribution Margin %", "CM %", position(kpi_x[4], 88, 104, 188, 86), violet),
        card("Revenue per Transaction", "Revenue / Txn", position(kpi_x[5], 88, 105, 188, 86), teal),
        single_measure_chart(
            "barChart",
            "GMV by Payment Method",
            "Payment rail mix",
            "dim_payment_method",
            "payment_method",
            "Method",
            "Payment GMV",
            "GMV",
            position(24, 198, 210, 388, 220),
            blue,
        ),
        single_measure_chart(
            "barChart",
            "Transactions by Channel",
            "Entry point volume",
            "dim_channel",
            "channel",
            "Channel",
            "Transactions",
            "Transactions",
            position(436, 198, 211, 396, 220),
            cyan,
        ),
        single_measure_chart(
            "barChart",
            "Chargeback Bps by Method",
            "Risk by payment rail",
            "dim_payment_method",
            "payment_method",
            "Method",
            "Chargeback Bps",
            "CB Bps",
            position(856, 198, 212, 400, 220),
            red,
        ),
        table_visual(
            "Merchant Margin Watchlist",
            "High chargeback/refund pressure and margin leakage",
            [
                ("dim_merchant", "merchant_name", "Merchant"),
                ("dim_merchant", "merchant_segment", "Segment"),
                ("dim_merchant", "risk_tier", "Risk"),
            ],
            [
                ("Current GMV", "GMV"),
                ("Refund Rate", "Refund"),
                ("Chargeback Bps", "CB Bps"),
                ("Current Contribution Margin", "CM"),
                ("Current CM %", "CM %"),
            ],
            position(24, 444, 300, 1232, 246),
            "Chargeback Bps",
        ),
    ]

    page3 = [
        title_text(
            "Margin & Scenario Planning",
            "Fee revenue bridge, cost per transaction, margin sensitivity, and take-rate scenario planning",
            position(24, 14, 1, 650, 54),
        ),
        slicer("dim_date", "year_month", "Month", position(690, slicer_y, 20, 108, 48)),
        slicer("dim_merchant", "merchant_segment", "Segment", position(812, slicer_y, 21, 126, 48)),
        slicer("dim_payment_method", "payment_method", "Method", position(952, slicer_y, 22, 138, 48)),
        slicer("dim_scenario", "scenario_name", "Scenario", position(1104, slicer_y, 23, 152, 48)),
        card("Current Revenue", "Base Revenue", position(kpi_x[0], 88, 100, 188, 86), green),
        card("Current Variable Cost", "Base Cost", position(kpi_x[1], 88, 101, 188, 86), amber),
        card("Current Contribution Margin", "Base CM", position(kpi_x[2], 88, 102, 188, 86), violet),
        card("Current Cost per Transaction", "Cost / Txn", position(kpi_x[3], 88, 103, 188, 86), amber),
        card("Scenario Contribution Margin", "Scenario CM", position(kpi_x[4], 88, 104, 188, 86), blue),
        card("Scenario Margin Uplift", "CM Uplift", position(kpi_x[5], 88, 105, 188, 86), teal),
        single_measure_chart(
            "waterfallChart",
            "Fee Revenue Bridge",
            "Previous revenue to current revenue",
            "fact_fee_bridge",
            "bridge_step",
            "Bridge Step",
            "Bridge Amount",
            "Bridge",
            position(24, 198, 210, 420, 220),
            blue,
            False,
            True,
        ),
        single_measure_chart(
            "lineChart",
            "Cost per Transaction Trend",
            "Unit economics over time",
            "dim_date",
            "year_month",
            "Month",
            "Cost per Transaction",
            "Cost / Txn",
            position(468, 198, 211, 392, 220),
            amber,
            False,
            True,
        ),
        single_measure_chart(
            "barChart",
            "Margin Sensitivity by Segment",
            "Contribution margin percentage",
            "dim_merchant",
            "merchant_segment",
            "Segment",
            "Contribution Margin %",
            "CM %",
            position(884, 198, 212, 372, 220),
            violet,
        ),
        table_visual(
            "Scenario Menu",
            "Take-rate, cost, and volume elasticity assumptions",
            [
                ("dim_scenario", "scenario_name", "Scenario"),
                ("dim_scenario", "description", "Description"),
            ],
            [
                ("Scenario Take Rate Delta Bps", "Take Rate Bps"),
                ("Scenario Cost Delta %", "Cost Delta"),
                ("Scenario Volume Elasticity", "Volume Elasticity"),
                ("Scenario Contribution Margin", "Scenario CM"),
                ("Scenario Margin Uplift", "CM Uplift"),
            ],
            position(24, 444, 300, 1232, 246),
            "Scenario Margin Uplift",
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
        "objects": {"section": [{"properties": {"verticalAlignment": text("Top")}}]},
    }

    return {
        "id": 0,
        "resourcePackages": [
            {
                "resourcePackage": {
                    "name": "SharedResources",
                    "type": 2,
                    "items": [{"type": 202, "path": "BaseThemes/CY26SU05.json", "name": "CY26SU05"}],
                    "disabled": False,
                }
            }
        ],
        "sections": [
            section("p8_executive_overview", "01 Executive Overview", 0, page1),
            section("p8_merchant_transaction_drivers", "02 Merchant & Transaction Drivers", 1, page2),
            section("p8_margin_scenario_planning", "03 Margin & Scenario Planning", 2, page3),
        ],
        "config": json.dumps(report_config, separators=(",", ":")),
        "layoutOptimization": 0,
    }


def main() -> None:
    layout = build_layout_project8()
    output = BUILD_DIR / "native_report_layout_project8.json"
    write_json(output, layout)
    summary = {
        "layout": str(output),
        "pages": len(layout["sections"]),
        "visual_containers": sum(len(section["visualContainers"]) for section in layout["sections"]),
        "commentary_removed": True,
        "visual_strategy": "native Power BI visual containers with slicers, cards, charts, waterfall, and tables",
        "page_names": [section["displayName"] for section in layout["sections"]],
    }
    write_json(BUILD_DIR / "native_report_layout_project8_summary.json", summary)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
