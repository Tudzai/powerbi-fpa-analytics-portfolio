from __future__ import annotations

import json
import uuid
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MEASURE_TABLE = "KPI_Measures"

COLORS = {
    "bg": "#463793",
    "ink": "#211A32",
}


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def measure_formats() -> dict[str, str | None]:
    model_path = ROOT / "model" / "model.bim"
    model = json.loads(model_path.read_text(encoding="utf-8"))
    formats: dict[str, str | None] = {}
    for table in model["model"]["tables"]:
        if table["name"] != MEASURE_TABLE:
            continue
        for measure in table.get("measures", []):
            formats[measure["name"]] = measure.get("formatString")
    return formats


MEASURE_FORMATS = measure_formats()


def lit(v):
    if isinstance(v, bool):
        s = "true" if v else "false"
    elif isinstance(v, int):
        s = f"{v}L"
    elif isinstance(v, float):
        s = f"{v}D"
    else:
        s = v
    return {"expr": {"Literal": {"Value": s}}}


def txt(v: str) -> dict:
    return lit("'" + v.replace("'", "''") + "'")


def col(v: str) -> dict:
    return {"solid": {"color": txt(v)}}


def pos(x, y, z, w, h):
    return {"x": x, "y": y, "z": z, "width": w, "height": h, "tabOrder": z}


def src(a):
    return {"SourceRef": {"Source": a}}


def ent(a):
    return {"SourceRef": {"Entity": a}}


def csel(a, table, column, display):
    return {"Column": {"Expression": src(a), "Property": column}, "Name": f"{table}.{column}", "NativeReferenceName": display}


def msel(a, measure, display):
    return {"Measure": {"Expression": src(a), "Property": measure}, "Name": f"{MEASURE_TABLE}.{measure}", "NativeReferenceName": display}


def mfmt(measure: str) -> str | None:
    return MEASURE_FORMATS.get(measure)


def measure_meta(measure, display):
    payload = {"Restatement": display, "Name": f"{MEASURE_TABLE}.{measure}", "Type": 1}
    if mfmt(measure):
        payload["Format"] = mfmt(measure)
    return payload


def ctrans(alias, table, column, display, role):
    return {
        "displayName": display,
        "queryName": f"{table}.{column}",
        "roles": {role: True},
        "type": {"category": None, "underlyingType": 1},
        "expr": {"Column": {"Expression": ent(alias), "Property": column}},
    }


def mtrans(measure, display, role):
    payload = {
        "displayName": display,
        "queryName": f"{MEASURE_TABLE}.{measure}",
        "roles": {role: True},
        "type": {"category": None, "underlyingType": 259},
        "expr": {"Measure": {"Expression": ent("m"), "Property": measure}},
    }
    if mfmt(measure):
        payload["format"] = mfmt(measure)
    return payload


def query(froms, selects, order=None):
    q = {"Version": 2, "From": froms, "Select": selects}
    if order:
        q["OrderBy"] = [order]
    return {
        "Commands": [
            {
                "SemanticQueryDataShapeCommand": {
                    "Query": q,
                    "Binding": {"Primary": {"Groupings": [{"Projections": list(range(len(selects)))}]}},
                    "DataReduction": {"DataVolume": 4, "Primary": {"Window": {"Count": 1000}}},
                    "Version": 1,
                },
                "ExecutionMetricsKind": 1,
            }
        ]
    }


def transforms(objects, roles, meta, selects, ordering, active=None):
    payload = {
        "objects": objects,
        "projectionOrdering": ordering,
        "queryMetadata": {"Select": meta},
        "visualElements": [{"DataRoles": [{"Name": role, "Projection": idx, "isActive": active_flag} for role, idx, active_flag in roles]}],
        "selects": selects,
    }
    if active:
        payload["projectionActiveItems"] = active
    return payload


def container(config, p, query_obj=None, transform_obj=None):
    config["layouts"] = [{"id": 0, "position": p}]
    out = {
        "x": p["x"],
        "y": p["y"],
        "z": p["z"],
        "width": p["width"],
        "height": p["height"],
        "config": json.dumps(config, separators=(",", ":")),
        "filters": "[]",
        "tabOrder": p["tabOrder"],
    }
    if query_obj:
        out["query"] = json.dumps(query_obj, separators=(",", ":"))
    if transform_obj:
        out["dataTransforms"] = json.dumps(transform_obj, separators=(",", ":"))
    return out


def plain_text(text, p, color="#DDD6F3", size="10pt", family="Segoe UI Semibold"):
    p = dict(p)
    p["height"] = max(float(p.get("height", 0)), 18.0)
    objects = {
        "general": [
            {
                "properties": {
                    "paragraphs": [
                        {
                            "textRuns": [
                                {"value": text, "textStyle": {"fontFamily": family, "fontSize": size, "color": color}}
                            ]
                        }
                    ]
                }
            }
        ]
    }
    return container(
        {
            "name": uuid.uuid4().hex[:20],
            "singleVisual": {
                "visualType": "textbox",
                "objects": objects,
                "drillFilterOtherVisuals": True,
                "vcObjects": {"background": [{"properties": {"show": lit(False)}}], "border": [{"properties": {"show": lit(False)}}]},
            },
        },
        p,
    )


def solid_rect(fill, p, radius=0.0):
    objects = {"general": [{"properties": {"paragraphs": [{"textRuns": [{"value": " ", "textStyle": {"fontFamily": "Segoe UI", "fontSize": "1pt", "color": fill}}]}]}}]}
    return container(
        {
            "name": uuid.uuid4().hex[:20],
            "singleVisual": {
                "visualType": "textbox",
                "objects": objects,
                "drillFilterOtherVisuals": True,
                "vcObjects": {
                    "background": [{"properties": {"show": lit(True), "color": col(fill), "transparency": lit(0.0)}}],
                    "border": [{"properties": {"show": lit(radius > 0), "color": col(fill), "radius": lit(radius), "width": lit(0.5)}}],
                    "visualHeader": [{"properties": {"show": lit(False)}}],
                },
            },
        },
        p,
    )


def measure_value(measure, display, p, accent, value_font=20.0, background: str | None = None):
    qref = f"{MEASURE_TABLE}.{measure}"
    objects = {
        "layout": [{"properties": {"rectangleRoundedCurve": lit(0), "cellPadding": lit(0.0), "paddingUniform": lit(0.0)}, "selector": {"id": "default"}}, {"properties": {}}],
        "value": [{"properties": {"fontSize": lit(value_font), "fontFamily": txt("Segoe UI Semibold"), "fontColor": col(accent)}, "selector": {"metadata": qref}}],
        "label": [{"properties": {"show": lit(False)}, "selector": {"metadata": qref}}],
        "fillCustom": [{"properties": {"show": lit(False)}}],
        "outline": [{"properties": {"show": lit(False)}, "selector": {"id": "default"}}],
    }
    froms = [{"Name": "m", "Entity": MEASURE_TABLE, "Type": 0}]
    selects = [msel("m", measure, display)]
    config = {
        "name": uuid.uuid4().hex[:20],
        "singleVisual": {
            "visualType": "cardVisual",
            "projections": {"Data": [{"queryRef": qref}]},
            "prototypeQuery": {"Version": 2, "From": froms, "Select": selects},
            "columnProperties": {qref: {"displayName": display}},
            "objects": objects,
            "drillFilterOtherVisuals": True,
            "vcObjects": {
                "background": [
                    {
                        "properties": {
                            "show": lit(bool(background)),
                            **({"color": col(background), "transparency": lit(0.0)} if background else {}),
                        }
                    }
                ],
                "border": [{"properties": {"show": lit(False)}}],
                "visualHeader": [{"properties": {"show": lit(False)}}],
            },
        },
    }
    transform_obj = transforms(objects, [("Data", 0, False)], [measure_meta(measure, display)], [mtrans(measure, display, "Data")], {"Data": [0]})
    return container(config, p, query(froms, selects), transform_obj)


def sparkline_area_chart(measure, display, p, fill):
    cref, mref = "DimDate.MonthLabel", f"{MEASURE_TABLE}.{measure}"
    objects = {
        "valueAxis": [{"properties": {"show": lit(False), "showAxisTitle": lit(False), "gridlineShow": lit(False)}}],
        "categoryAxis": [{"properties": {"show": lit(False), "showAxisTitle": lit(False), "gridlineShow": lit(False)}}],
        "lineStyles": [{"properties": {"areaShow": lit(True), "lineStyle": txt("solid"), "lineChartType": txt("step"), "strokeShow": lit(True)}}],
        "legend": [{"properties": {"show": lit(False)}}],
        "labels": [{"properties": {"show": lit(False)}}],
        "dataPoint": [{"properties": {"fill": col(fill)}}],
    }
    froms = [{"Name": "c", "Entity": "DimDate", "Type": 0}, {"Name": "m", "Entity": MEASURE_TABLE, "Type": 0}]
    selects = [csel("c", "DimDate", "MonthLabel", "Month"), msel("m", measure, display)]
    order = {"Direction": 1, "Expression": {"Column": {"Expression": src("c"), "Property": "MonthIndex"}}}
    config = {
        "name": uuid.uuid4().hex[:20],
        "singleVisual": {
            "visualType": "stackedAreaChart",
            "projections": {"Category": [{"queryRef": cref, "active": True}], "Y": [{"queryRef": mref}]},
            "prototypeQuery": {"Version": 2, "From": froms, "Select": selects, "OrderBy": [order]},
            "objects": objects,
            "drillFilterOtherVisuals": True,
            "vcObjects": {
                "background": [{"properties": {"show": lit(False)}}],
                "border": [{"properties": {"show": lit(False)}}],
                "title": [{"properties": {"show": lit(False)}}],
                "subTitle": [{"properties": {"show": lit(False)}}],
                "visualHeader": [{"properties": {"show": lit(False)}}],
            },
        },
    }
    return container(
        config,
        p,
        query(froms, selects, order),
        transforms(
            objects,
            [("Category", 0, True), ("Y", 1, False)],
            [{"Restatement": "Month", "Name": cref, "Type": 2048}, measure_meta(measure, display)],
            [ctrans("c", "DimDate", "MonthLabel", "Month", "Category"), mtrans(measure, display, "Y")],
            {"Category": [0], "Y": [1]},
            {"Category": [{"queryRef": cref, "suppressConcat": False}]},
        ),
    )


def svg_image_table(measure: str, display: str, p: dict) -> dict:
    qref = f"{MEASURE_TABLE}.{measure}"
    image_w = max(80, int(p["width"] - 24))
    image_h = max(60, int(p["height"] - 24))
    objects = {
        "grid": [
            {
                "properties": {
                    "gridHorizontal": lit(False),
                    "gridVertical": lit(False),
                    "outlineColor": col(COLORS["bg"]),
                    "outlineStyle": lit(0.0),
                    "outlineWeight": lit(0),
                    "gridHorizontalColor": col(COLORS["bg"]),
                    "gridHorizontalWeight": lit(0),
                    "gridVerticalColor": col(COLORS["bg"]),
                    "gridVerticalWeight": lit(0),
                    "rowPadding": lit(0),
                    "imageHeight": lit(image_h),
                    "imageWidth": lit(image_w),
                }
            }
        ],
        "columnHeaders": [
            {
                "properties": {
                    "show": lit(False),
                    "fontSize": lit(1.0),
                    "fontColor": col(COLORS["bg"]),
                }
            }
        ],
        "values": [
            {
                "properties": {
                    "fontSize": lit(1.0),
                    "fontColor": col(COLORS["bg"]),
                    "backColor": col(COLORS["bg"]),
                    "backColorPrimary": col(COLORS["bg"]),
                    "backColorSecondary": col(COLORS["bg"]),
                    "urlIcon": lit(False),
                    "imageHeight": lit(image_h),
                    "imageWidth": lit(image_w),
                }
            }
        ],
        "imageSize": [
            {
                "properties": {
                    "height": lit(image_h),
                    "width": lit(image_w),
                }
            }
        ],
        "columnWidth": [
            {
                "properties": {"value": lit(float(image_w + 6))},
                "selector": {"metadata": qref},
            }
        ],
    }
    froms = [{"Name": "m", "Entity": MEASURE_TABLE, "Type": 0}]
    selects = [msel("m", measure, display)]
    config = {
        "name": uuid.uuid4().hex[:20],
        "singleVisual": {
            "visualType": "tableEx",
            "projections": {"Values": [{"queryRef": qref}]},
            "prototypeQuery": {"Version": 2, "From": froms, "Select": selects},
            "columnProperties": {qref: {"displayName": display}},
            "objects": objects,
            "drillFilterOtherVisuals": True,
            "vcObjects": {
                "background": [{"properties": {"show": lit(False)}}],
                "border": [{"properties": {"show": lit(False)}}],
                "dropShadow": [{"properties": {"show": lit(False)}}],
                "title": [{"properties": {"show": lit(False)}}],
                "visualHeader": [{"properties": {"show": lit(False)}}],
            },
        },
    }
    transform_obj = transforms(objects, [("Values", 0, False)], [measure_meta(measure, display)], [mtrans(measure, display, "Values")], {"Values": [0]})
    return container(config, p, query(froms, selects), transform_obj)


def golden_card_visual(measure: str, display: str, p: dict, accent: str, fill: str, border: str) -> dict:
    qref = f"{MEASURE_TABLE}.{measure}"
    objects = {
        "layout": [
            {
                "properties": {
                    "rectangleRoundedCurveCustomStyle": lit(False),
                    "orientation": lit(2.0),
                    "style": txt("Cards"),
                    "alignment": txt("top"),
                },
                "selector": {"id": "default"},
            }
        ],
        "shapeCustomRectangle": [
            {"properties": {"tileShape": txt("rectangleRoundedByPixel")}, "selector": {"id": "default"}}
        ],
        "fillCustom": [
            {
                "properties": {
                    "show": lit(True),
                    "transparency": lit(0.0),
                    "color": col(fill),
                    "fill": col(fill),
                    "fillColor": col(fill),
                },
                "selector": {"id": "default"},
            }
        ],
        "outline": [
            {
                "properties": {
                    "show": lit(False),
                    "weight": lit(2.4),
                    "lineColor": col(border),
                },
                "selector": {"id": "default"},
            }
        ],
        "padding": [
            {
                "properties": {
                    "paddingSelection": txt("Custom"),
                    "leftMargin": lit(24),
                    "topMargin": lit(14),
                    "rightMargin": lit(16),
                    "bottomMargin": lit(10),
                },
                "selector": {"id": "default"},
            }
        ],
        "spacing": [{"properties": {"verticalSpacing": lit(8)}, "selector": {"id": "default"}}],
        "value": [
            {
                "properties": {
                    "fontSize": lit(22.0),
                    "fontFamily": txt("Segoe UI Semibold"),
                    "fontColor": col(accent),
                    "horizontalAlignment": txt("left"),
                    "textWrap": lit(False),
                },
                "selector": {"id": "default"},
            },
            {
                "properties": {
                    "fontSize": lit(22.0),
                    "fontColor": col(accent),
                    "horizontalAlignment": txt("left"),
                    "textWrap": lit(False),
                    "labelDisplayUnits": lit(-1.0),
                },
                "selector": {"metadata": qref},
            },
        ],
        "label": [
            {
                "properties": {
                    "show": lit(True),
                    "text": txt(display),
                    "fontSize": lit(11.0),
                    "fontFamily": txt("Segoe UI Semibold"),
                    "fontColor": col("#70677B"),
                    "position": txt("aboveValue"),
                    "horizontalAlignment": txt("left"),
                    "textWrap": lit(False),
                    "matchValueAlignment": lit(False),
                },
                "selector": {"metadata": qref},
            }
        ],
    }
    froms = [{"Name": "m", "Entity": MEASURE_TABLE, "Type": 0}]
    selects = [msel("m", measure, display)]
    config = {
        "name": uuid.uuid4().hex[:20],
        "singleVisual": {
            "visualType": "cardVisual",
            "projections": {"Data": [{"queryRef": qref}]},
            "prototypeQuery": {"Version": 2, "From": froms, "Select": selects},
            "columnProperties": {qref: {"displayName": display}},
            "objects": objects,
            "drillFilterOtherVisuals": True,
            "vcObjects": {
                "background": [
                    {
                        "properties": {
                            "show": lit(True),
                            "color": col(fill),
                            "transparency": lit(0.0),
                        }
                    }
                ],
                "border": [
                    {
                        "properties": {
                            "show": lit(True),
                            "color": col(border),
                            "radius": lit(14.0),
                            "width": lit(2.4),
                        }
                    }
                ],
                "dropShadow": [
                    {
                        "properties": {
                            "show": lit(True),
                            "position": txt("Outer"),
                            "color": col("#1A092A"),
                            "transparency": lit(72.0),
                            "angle": lit(45.0),
                            "distance": lit(2.0),
                        }
                    }
                ],
                "title": [{"properties": {"show": lit(False)}}],
                "visualHeader": [{"properties": {"show": lit(False)}}],
            },
        },
    }
    transform_obj = transforms(objects, [("Data", 0, False)], [measure_meta(measure, display)], [mtrans(measure, display, "Data")], {"Data": [0]})
    return container(config, p, query(froms, selects), transform_obj)


def rounded_rect(fill: str, border: str, p: dict, radius: float = 12.0, width: float = 1.0) -> dict:
    objects = {
        "general": [
            {
                "properties": {
                    "paragraphs": [
                        {
                            "textRuns": [
                                {
                                    "value": " ",
                                    "textStyle": {
                                        "fontFamily": "Segoe UI",
                                        "fontSize": "1pt",
                                        "color": fill,
                                    },
                                }
                            ]
                        }
                    ]
                }
            }
        ]
    }
    config = {
        "name": uuid.uuid4().hex[:20],
        "singleVisual": {
            "visualType": "textbox",
            "objects": objects,
            "drillFilterOtherVisuals": True,
            "vcObjects": {
                "background": [
                    {
                        "properties": {
                            "show": lit(True),
                            "color": col(fill),
                            "transparency": lit(0.0),
                        }
                    }
                ],
                "border": [
                    {
                        "properties": {
                            "show": lit(True),
                            "color": col(border),
                            "radius": lit(radius),
                            "width": lit(width),
                        }
                    }
                ],
                "dropShadow": [
                    {
                        "properties": {
                            "show": lit(True),
                            "position": txt("Outer"),
                            "color": col("#1A092A"),
                            "transparency": lit(70.0),
                            "angle": lit(45.0),
                            "distance": lit(2.0),
                        }
                    }
                ],
                "visualHeader": [{"properties": {"show": lit(False)}}],
            },
        },
    }
    return container(config, p)


def circle(fill: str, x: float, y: float, z: int, size: float, border: str = "#FFFFFF") -> list[dict]:
    return [
        solid_rect(border, pos(x - 1.2, y - 1.2, z, size + 2.4, size + 2.4), radius=(size + 2.4) / 2),
        solid_rect(fill, pos(x, y, z + 1, size, size), radius=size / 2),
    ]


def golden_revenue_card() -> list[dict]:
    x, y, z = 490, 42, 100
    return [
        svg_image_table("Revenue KPI Card SVG", "Revenue KPI Card", pos(x, y, z, 300, 168)),
        solid_rect(COLORS["bg"], pos(x, y, z + 900, 300, 8), radius=0),
    ]


def build_layout() -> dict:
    section_config = json.dumps(
        {
            "objects": {
                "background": [
                    {
                        "properties": {
                            "color": col(COLORS["bg"]),
                            "transparency": lit(0.0),
                        }
                    }
                ],
                "outspace": [
                    {
                        "properties": {
                            "color": col("#F7F4FB"),
                            "transparency": lit(0.0),
                        }
                    }
                ],
            }
        },
        separators=(",", ":"),
    )
    report_config = {
        "version": "5.73",
        "themeCollection": {"baseTheme": {"name": "CY26SU05", "type": 2}},
        "activeSectionIndex": 0,
        "defaultDrillFilterOtherVisuals": True,
        "settings": {
            "useNewFilterPaneExperience": True,
            "useStylableVisualContainerHeader": True,
            "queryLimitOption": 6,
        },
    }
    return {
        "activeSectionIndex": 0,
        "sections": [
            {
                "id": 0,
                "name": f"ReportSectionGolden{uuid.uuid4().hex[:6]}",
                "displayName": "Golden KPI Card",
                "filters": "[]",
                "ordinal": 0,
                "visualContainers": golden_revenue_card(),
                "config": section_config,
                "displayOption": 1,
                "width": 1280,
                "height": 720,
            }
        ],
        "config": json.dumps(report_config, separators=(",", ":")),
        "layoutOptimization": 0,
    }


def main() -> None:
    layout = build_layout()
    out = ROOT / "build" / "golden_kpi_card_layout.json"
    write_json(out, layout)
    summary = {
        "status": "layout_json_generated",
        "scope": "single golden KPI card prototype",
        "page": "Golden KPI Card",
        "visual_containers": len(layout["sections"][0]["visualContainers"]),
        "card_components": {
            "cardVisual": 0,
            "tableEx": 1,
            "svg_measure": "Revenue KPI Card SVG",
            "shape_text_layers": 1,
        },
        "target": "ZoomCharts-style single KPI card: lavender card, purple border, title, large value, right sparkline, divider, PY and YoY footer.",
        "layout": str(out),
    }
    write_json(ROOT / "qa" / "golden_kpi_card_layout_summary.json", summary)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
