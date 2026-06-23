from __future__ import annotations

import csv
import hashlib
import json
import uuid
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PREP = ROOT / "data" / "prepared"
MEASURE_TABLE = "KPI_Measures"

COLORS = {
    "bg": "#F7F9F8",
    "ink": "#202A25",
    "muted": "#5B6C5D",
    "border": "#D9E2DC",
    "navy": "#12372A",
    "teal": "#2A9D8F",
    "lime": "#B7D968",
    "amber": "#F4A261",
    "coral": "#E76F51",
    "gray": "#59656F",
    "green2": "#8AB17D",
}


TABLE_FILES = [
    "dim_date",
    "dim_business_unit",
    "dim_facility",
    "dim_activity",
    "dim_supplier",
    "dim_carbon_scenario",
    "fact_emissions",
    "fact_supplier_month",
    "fact_carbon_exposure",
    "fact_abatement_initiatives",
]

RELATIONSHIPS = [
    ("fact_emissions", "date_key", "dim_date", "date_key"),
    ("fact_supplier_month", "date_key", "dim_date", "date_key"),
    ("fact_carbon_exposure", "date_key", "dim_date", "date_key"),
    ("fact_emissions", "business_unit_id", "dim_business_unit", "business_unit_id"),
    ("fact_emissions", "facility_id", "dim_facility", "facility_id"),
    ("fact_emissions", "activity_id", "dim_activity", "activity_id"),
    ("fact_emissions", "supplier_id", "dim_supplier", "supplier_id"),
    ("fact_supplier_month", "supplier_id", "dim_supplier", "supplier_id"),
    ("fact_carbon_exposure", "scenario_id", "dim_carbon_scenario", "scenario_id"),
]

MEASURES = [
    ("Total Emissions tCO2e", "SUM ( fact_emissions[emissions_tco2e] )", "#,0.0"),
    ("Scope 1 Emissions tCO2e", 'CALCULATE ( [Total Emissions tCO2e], fact_emissions[scope] = "Scope 1" )', "#,0.0"),
    ("Scope 2 Emissions tCO2e", 'CALCULATE ( [Total Emissions tCO2e], fact_emissions[scope] = "Scope 2" )', "#,0.0"),
    ("Scope 3 Emissions tCO2e", 'CALCULATE ( [Total Emissions tCO2e], fact_emissions[scope] = "Scope 3" )', "#,0.0"),
    ("Total Spend USD", "SUM ( fact_emissions[spend_usd] )", "$#,0"),
    ("Revenue USD", "SUM ( fact_emissions[revenue_usd] )", "$#,0"),
    ("Emissions Intensity tCO2e per $M Revenue", "DIVIDE ( [Total Emissions tCO2e], [Revenue USD] ) * 1000000", "#,0.0"),
    ("Selected Carbon Price USD/t", "SELECTEDVALUE ( dim_carbon_scenario[carbon_price_usd_per_t], 50 )", "$#,0"),
    ("Carbon Cost USD", "[Total Emissions tCO2e] * [Selected Carbon Price USD/t]", "$#,0"),
    ("Scenario Carbon Cost USD", "SUM ( fact_carbon_exposure[carbon_cost_usd] )", "$#,0"),
    ("Probability Weighted Carbon Cost USD", "SUM ( fact_carbon_exposure[probability_weighted_cost_usd] )", "$#,0"),
    ("Stress Scenario Carbon Cost USD", 'CALCULATE ( [Scenario Carbon Cost USD], dim_carbon_scenario[scenario] = "Stress price shock" )', "$#,0"),
    ("Supplier Emissions tCO2e", "SUM ( fact_supplier_month[emissions_tco2e] )", "#,0.0"),
    ("Supplier Spend USD", "SUM ( fact_supplier_month[spend_usd] )", "$#,0"),
    ("Supplier Intensity tCO2e per $M Spend", "DIVIDE ( [Supplier Emissions tCO2e], [Supplier Spend USD] ) * 1000000", "#,0.0"),
    ("High Risk Supplier Emissions tCO2e", 'CALCULATE ( [Supplier Emissions tCO2e], fact_supplier_month[carbon_risk_tier] = "High" )', "#,0.0"),
    ("Average Data Quality Score", "AVERAGE ( fact_supplier_month[data_quality_score] )", "0.0%"),
    ("Abatement Annual Reduction tCO2e", "SUM ( fact_abatement_initiatives[annual_reduction_tco2e] )", "#,0"),
    ("Abatement Capex USD", "SUM ( fact_abatement_initiatives[capex_usd] )", "$#,0"),
    ("Planned Abatement Capex USD", 'CALCULATE ( [Abatement Capex USD], fact_abatement_initiatives[implementation_status] = "Planned" )', "$#,0"),
    ("Committed and In Flight Reduction tCO2e", 'CALCULATE ( [Abatement Annual Reduction tCO2e], fact_abatement_initiatives[implementation_status] IN { "Committed", "In flight", "Implemented" } )', "#,0"),
    ("Avoided Carbon Cost USD at Selected Price", "[Abatement Annual Reduction tCO2e] * [Selected Carbon Price USD/t]", "$#,0"),
    ("Abatement Annual Benefit USD", "SUM ( fact_abatement_initiatives[annual_opex_savings_usd] ) + [Avoided Carbon Cost USD at Selected Price]", "$#,0"),
    ("Abatement ROI", "DIVIDE ( [Abatement Annual Benefit USD], [Abatement Capex USD] )", "0.0%"),
    ("Payback Years", "DIVIDE ( [Abatement Capex USD], [Abatement Annual Benefit USD] )", "0.0"),
    ("MACC USD per tCO2e", "DIVIDE ( DIVIDE ( [Abatement Capex USD], 7 ) - SUM ( fact_abatement_initiatives[annual_opex_savings_usd] ), [Abatement Annual Reduction tCO2e] )", "$#,0.0"),
    ("Latest Month Emissions tCO2e", "VAR LatestMonth = MAX ( dim_date[date_key] ) RETURN CALCULATE ( [Total Emissions tCO2e], dim_date[date_key] = LatestMonth )", "#,0.0"),
    ("YoY Emissions Change %", "VAR CurrentEmissions = [Total Emissions tCO2e] VAR PriorEmissions = CALCULATE ( [Total Emissions tCO2e], DATEADD ( dim_date[month_start], -1, YEAR ) ) RETURN DIVIDE ( CurrentEmissions - PriorEmissions, PriorEmissions )", "0.0%"),
]


def write_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def sha256_file(path: Path) -> str | None:
    if not path.exists():
        return None
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.strip() + "\n", encoding="utf-8")


def csv_headers(table: str) -> list[str]:
    with (PREP / f"{table}.csv").open("r", encoding="utf-8", newline="") as f:
        return next(csv.reader(f))


def infer_type(name: str) -> tuple[str, str, str | None]:
    lower = name.lower()
    if name == "month_start":
        return "dateTime", "type date", "Long Date"
    if lower in {"year", "month_no", "fiscal_year", "month_index", "start_year"}:
        return "int64", "Int64.Type", "0"
    if any(token in lower for token in ["usd", "tco2e", "volume", "factor", "score", "probability", "price", "latitude", "longitude", "roi", "macc", "payback"]):
        is_currency = "usd" in lower or "price" in lower or "macc" in lower
        fmt = "$#,0" if is_currency else "#,0.00"
        if not is_currency and ("score" in lower or "roi" in lower or "probability" in lower):
            fmt = "0.0%"
        return "double", "type number", fmt
    return "string", "type text", None


def table_model(table: str) -> dict:
    fields = csv_headers(table)
    columns = []
    m_types = []
    for field in fields:
        dtype, mtype, fmt = infer_type(field)
        col = {
            "name": field,
            "dataType": dtype,
            "sourceColumn": field,
            "summarizeBy": "sum" if dtype == "double" and not field.endswith("_id") else "none",
        }
        if field.endswith("_id") or field in {"date_key"}:
            col["summarizeBy"] = "none"
            if field.endswith("_id"):
                col["isHidden"] = True
        if fmt:
            col["formatString"] = fmt
        columns.append(col)
        m_types.append(f'{{"{field}", {mtype}}}')
    path = str(PREP / f"{table}.csv").replace("\\", "\\\\")
    expression = [
        "let",
        f'    Source = Csv.Document(File.Contents("{path}"), [Delimiter=",", Columns={len(fields)}, Encoding=65001, QuoteStyle=QuoteStyle.Csv]),',
        "    PromotedHeaders = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),",
        f"    ChangedType = Table.TransformColumnTypes(PromotedHeaders, {{{', '.join(m_types)}}}, \"en-US\")",
        "in",
        "    ChangedType",
    ]
    return {
        "name": table,
        "lineageTag": str(uuid.uuid4()),
        "columns": columns,
        "partitions": [{"name": f"p_{table}", "mode": "import", "source": {"type": "m", "expression": expression}}],
        "annotations": [{"name": "PBI_ResultType", "value": "Table"}],
    }


def build_model() -> None:
    tables = [table_model(t) for t in TABLE_FILES]
    tables.append(
        {
            "name": MEASURE_TABLE,
            "lineageTag": str(uuid.uuid4()),
            "columns": [{"name": "MeasureName", "dataType": "string", "sourceColumn": "MeasureName", "isHidden": True}],
            "partitions": [
                {
                    "name": "p_KPI_Measures",
                    "mode": "import",
                    "source": {"type": "m", "expression": 'let Source = #table(type table [MeasureName = text], {{"KPI"}}) in Source'},
                }
            ],
            "measures": [
                {"name": name, "expression": expression, "formatString": fmt, "lineageTag": str(uuid.uuid4())}
                for name, expression, fmt in MEASURES
            ],
        }
    )
    relationships = [
        {"name": f"Rel_{a}_{b}_{c}_{d}", "fromTable": a, "fromColumn": b, "toTable": c, "toColumn": d}
        for a, b, c, d in RELATIONSHIPS
    ]
    model = {
        "compatibilityLevel": 1600,
        "model": {
            "culture": "en-US",
            "dataAccessOptions": {"legacyRedirects": True, "returnErrorValuesAsNull": True},
            "defaultPowerBIDataSourceVersion": "powerBI_V3",
            "sourceQueryCulture": "en-US",
            "tables": tables,
            "relationships": relationships,
            "annotations": [{"name": "__PBI_TimeIntelligenceEnabled", "value": "0"}],
        },
    }
    write_json(ROOT / "model" / "model.bim", model)
    write_json(ROOT / "model" / "relationship_map.json", relationships)


def lit(v):
    if isinstance(v, bool):
        s = "true" if v else "false"
    elif isinstance(v, int):
        s = f"{v}L"
    elif isinstance(v, float):
        s = f"{v}D"
    else:
        s = str(v)
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


def mfmt(measure):
    return next((fmt for name, _expression, fmt in MEASURES if name == measure), "#,0")


def frame(title=None, sub=None, fill="#FFFFFF"):
    out = {
        "background": [{"properties": {"show": lit(True), "color": col(fill), "transparency": lit(0.0)}}],
        "border": [{"properties": {"show": lit(True), "color": col(COLORS["border"]), "radius": lit(6.0), "width": lit(1.0)}}],
        "dropShadow": [{"properties": {"show": lit(True), "position": txt("Outer"), "color": col("#D5DED8"), "transparency": lit(82.0), "angle": lit(45.0), "distance": lit(2.0)}}],
        "visualHeader": [{"properties": {"show": lit(False)}}],
    }
    if title:
        out["title"] = [{"properties": {"show": lit(True), "text": txt(title), "fontFamily": txt("Segoe UI Semibold"), "fontSize": lit(9.0), "fontColor": col(COLORS["ink"])}}]
    if sub:
        out["subTitle"] = [{"properties": {"show": lit(True), "text": txt(sub), "fontFamily": txt("Segoe UI"), "fontSize": lit(7.0), "fontColor": col(COLORS["muted"])}}]
    return out


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


def query(froms, selects, order=None):
    q = {"Version": 2, "From": froms, "Select": selects}
    if order:
        q["OrderBy"] = [order]
    return {
        "Commands": [
            {
                "SemanticQueryDataShapeCommand": {
                    "Query": q,
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


def ctrans(alias, table, column, display, role):
    return {
        "displayName": display,
        "queryName": f"{table}.{column}",
        "roles": {role: True},
        "type": {"category": None, "underlyingType": 1},
        "expr": {"Column": {"Expression": ent(alias), "Property": column}},
    }


def mtrans(measure, display, role):
    return {
        "displayName": display,
        "queryName": f"{MEASURE_TABLE}.{measure}",
        "roles": {role: True},
        "type": {"category": None, "underlyingType": 259},
        "expr": {"Measure": {"Expression": ent("m"), "Property": measure}},
        "format": mfmt(measure),
    }


def textbox(title, sub, p):
    objects = {
        "general": [
            {
                "properties": {
                    "paragraphs": [
                        {
                            "textRuns": [
                                {"value": title, "textStyle": {"fontFamily": "Segoe UI Semibold", "fontSize": "19pt", "color": "#FFFFFF"}},
                                {"value": f"\n{sub}", "textStyle": {"fontFamily": "Segoe UI", "fontSize": "8pt", "color": "#DCEAE4"}},
                            ]
                        }
                    ]
                }
            }
        ]
    }
    return container({"name": uuid.uuid4().hex[:20], "singleVisual": {"visualType": "textbox", "objects": objects, "drillFilterOtherVisuals": True, "vcObjects": {"background": [{"properties": {"show": lit(False)}}], "border": [{"properties": {"show": lit(False)}}]}}}, p)


def shape(fill, p):
    objects = {"general": [{"properties": {"paragraphs": [{"textRuns": [{"value": " ", "textStyle": {"fontFamily": "Segoe UI", "fontSize": "1pt", "color": fill}}]}]}}]}
    return container({"name": uuid.uuid4().hex[:20], "singleVisual": {"visualType": "textbox", "objects": objects, "drillFilterOtherVisuals": True, "vcObjects": frame(fill=fill)}}, p)


def card(measure, display, p, accent):
    qref = f"{MEASURE_TABLE}.{measure}"
    objects = {
        "layout": [{"properties": {"rectangleRoundedCurve": lit(5), "cellPadding": lit(6.0), "paddingUniform": lit(6.0)}, "selector": {"id": "default"}}],
        "value": [{"properties": {"fontSize": lit(19.0), "fontFamily": txt("Segoe UI Semibold"), "fontColor": col(accent)}, "selector": {"metadata": qref}}],
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
            "vcObjects": frame(display),
        },
    }
    transform_obj = transforms(objects, [("Data", 0, False)], [{"Restatement": display, "Name": qref, "Type": 1, "Format": mfmt(measure)}], [mtrans(measure, display, "Data")], {"Data": [0]})
    return container(config, p, query(froms, selects), transform_obj)


def slicer(table, column, display, p):
    qref = f"{table}.{column}"
    objects = {"data": [{"properties": {"mode": txt("Dropdown")}}], "selection": [{"properties": {"selectAllCheckboxEnabled": lit(True), "singleSelect": lit(False)}}], "header": [{"properties": {"show": lit(False)}}]}
    froms = [{"Name": "f", "Entity": table, "Type": 0}]
    selects = [csel("f", table, column, display)]
    config = {"name": uuid.uuid4().hex[:20], "singleVisual": {"visualType": "slicer", "projections": {"Values": [{"queryRef": qref, "active": True}]}, "prototypeQuery": {"Version": 2, "From": froms, "Select": selects}, "objects": objects, "drillFilterOtherVisuals": True, "vcObjects": frame(display)}}
    transform_obj = transforms(objects, [("Values", 0, True)], [{"Restatement": display, "Name": qref, "Type": 2048}], [ctrans("f", table, column, display, "Values")], {"Values": [0]}, {"Values": [{"queryRef": qref, "suppressConcat": False}]})
    return container(config, p, query(froms, selects), transform_obj)


def chart_objects(fill, labels=True):
    return {
        "valueAxis": [{"properties": {"showAxisTitle": lit(False), "gridlineShow": lit(False), "labelDisplayUnits": lit(1000000.0)}}],
        "categoryAxis": [{"properties": {"showAxisTitle": lit(False), "gridlineShow": lit(False), "concatenateLabels": lit(False), "fontSize": lit(7.0)}}],
        "labels": [{"properties": {"show": lit(labels), "fontSize": lit(7.0), "labelDisplayUnits": lit(1000000.0)}}],
        "legend": [{"properties": {"showTitle": lit(False), "position": txt("Top")}}],
        "dataPoint": [{"properties": {"fill": col(fill)}}],
    }


def single_chart(vtype, title, sub, table, column, display, measure, mdisplay, p, fill, order_column=None, order_measure=False, ascending=True):
    cref, mref = f"{table}.{column}", f"{MEASURE_TABLE}.{measure}"
    objects = chart_objects(fill)
    froms = [{"Name": "c", "Entity": table, "Type": 0}, {"Name": "m", "Entity": MEASURE_TABLE, "Type": 0}]
    selects = [csel("c", table, column, display), msel("m", measure, mdisplay)]
    order = None
    if order_column:
        order = {"Direction": 1 if ascending else 2, "Expression": {"Column": {"Expression": src("c"), "Property": order_column}}}
    elif order_measure:
        order = {"Direction": 1 if ascending else 2, "Expression": {"Measure": {"Expression": src("m"), "Property": measure}}}
    prototype = {"Version": 2, "From": froms, "Select": selects}
    if order:
        prototype["OrderBy"] = [order]
    config = {"name": uuid.uuid4().hex[:20], "singleVisual": {"visualType": vtype, "projections": {"Category": [{"queryRef": cref, "active": True}], "Y": [{"queryRef": mref}]}, "prototypeQuery": prototype, "objects": objects, "drillFilterOtherVisuals": True, "vcObjects": frame(title, sub)}}
    transform_obj = transforms(objects, [("Category", 0, True), ("Y", 1, False)], [{"Restatement": display, "Name": cref, "Type": 2048}, {"Restatement": mdisplay, "Name": mref, "Type": 1, "Format": mfmt(measure)}], [ctrans("c", table, column, display, "Category"), mtrans(measure, mdisplay, "Y")], {"Category": [0], "Y": [1]}, {"Category": [{"queryRef": cref, "suppressConcat": False}]})
    return container(config, p, query(froms, selects, order), transform_obj)


def multi_chart(vtype, title, sub, table, column, display, measures, p, order_column=None):
    cref = f"{table}.{column}"
    objects = chart_objects(COLORS["teal"], labels=False)
    froms = [{"Name": "c", "Entity": table, "Type": 0}, {"Name": "m", "Entity": MEASURE_TABLE, "Type": 0}]
    selects = [csel("c", table, column, display)]
    meta = [{"Restatement": display, "Name": cref, "Type": 2048}]
    transform_selects = [ctrans("c", table, column, display, "Category")]
    roles = [("Category", 0, True)]
    y_refs = []
    for measure, label in measures:
        idx = len(selects)
        qref = f"{MEASURE_TABLE}.{measure}"
        selects.append(msel("m", measure, label))
        y_refs.append({"queryRef": qref})
        meta.append({"Restatement": label, "Name": qref, "Type": 1, "Format": mfmt(measure)})
        transform_selects.append(mtrans(measure, label, "Y"))
        roles.append(("Y", idx, False))
    order = {"Direction": 1, "Expression": {"Column": {"Expression": src("c"), "Property": order_column}}} if order_column else None
    prototype = {"Version": 2, "From": froms, "Select": selects}
    if order:
        prototype["OrderBy"] = [order]
    config = {"name": uuid.uuid4().hex[:20], "singleVisual": {"visualType": vtype, "projections": {"Category": [{"queryRef": cref, "active": True}], "Y": y_refs}, "prototypeQuery": prototype, "objects": objects, "drillFilterOtherVisuals": True, "vcObjects": frame(title, sub)}}
    return container(config, p, query(froms, selects, order), transforms(objects, roles, meta, transform_selects, {"Category": [0], "Y": list(range(1, len(selects)))}, {"Category": [{"queryRef": cref, "suppressConcat": False}]}))


def table_visual(title, sub, fields, measures, p, order_measure=None, asc=False):
    aliases, froms = {}, []
    for table, _column, _display in fields:
        if table not in aliases:
            aliases[table] = f"f{len(aliases)}"
            froms.append({"Name": aliases[table], "Entity": table, "Type": 0})
    if measures:
        aliases[MEASURE_TABLE] = "m"
        froms.append({"Name": "m", "Entity": MEASURE_TABLE, "Type": 0})
    selects, projections, meta, transform_selects = [], [], [], []
    for table, column, display in fields:
        qref = f"{table}.{column}"
        selects.append(csel(aliases[table], table, column, display))
        projections.append({"queryRef": qref})
        meta.append({"Restatement": display, "Name": qref, "Type": 2048})
        transform_selects.append(ctrans(aliases[table], table, column, display, "Values"))
    for measure, display in measures:
        qref = f"{MEASURE_TABLE}.{measure}"
        selects.append(msel("m", measure, display))
        projections.append({"queryRef": qref})
        meta.append({"Restatement": display, "Name": qref, "Type": 1, "Format": mfmt(measure)})
        transform_selects.append(mtrans(measure, display, "Values"))
    objects = {"grid": [{"properties": {"gridHorizontal": lit(False), "outlineColor": col(COLORS["border"])}}], "columnHeaders": [{"properties": {"fontFamily": txt("Segoe UI Semibold"), "fontSize": lit(7.2), "fontColor": col(COLORS["ink"])}}], "values": [{"properties": {"fontFamily": txt("Segoe UI"), "fontSize": lit(7.0), "fontColor": col(COLORS["ink"])}}]}
    order = {"Direction": 1 if asc else 2, "Expression": {"Measure": {"Expression": src("m"), "Property": order_measure}}} if order_measure else None
    prototype = {"Version": 2, "From": froms, "Select": selects}
    if order:
        prototype["OrderBy"] = [order]
    config = {"name": uuid.uuid4().hex[:20], "singleVisual": {"visualType": "tableEx", "projections": {"Values": projections}, "prototypeQuery": prototype, "objects": objects, "drillFilterOtherVisuals": True, "vcObjects": frame(title, sub)}}
    return container(config, p, query(froms, selects, order), transforms(objects, [("Values", i, False) for i in range(len(selects))], meta, transform_selects, {"Values": list(range(len(selects)))}))


def header(title, sub, z):
    return [
        shape(COLORS["navy"], pos(0, 0, z, 1280, 82)),
        textbox(title, sub, pos(28, 12, z + 1, 570, 58)),
        slicer("dim_date", "year", "Year", pos(630, 18, z + 2, 84, 44)),
        slicer("dim_facility", "region", "Region", pos(728, 18, z + 3, 124, 44)),
        slicer("dim_business_unit", "business_unit", "Business Unit", pos(866, 18, z + 4, 160, 44)),
        slicer("fact_emissions", "scope", "Scope", pos(1040, 18, z + 5, 90, 44)),
        slicer("dim_carbon_scenario", "scenario", "Scenario", pos(1144, 18, z + 6, 106, 44)),
    ]


def section(name, ordinal, visuals):
    config = json.dumps({"objects": {"background": [{"properties": {"color": col(COLORS["bg"]), "transparency": lit(0.0)}}], "outspace": [{"properties": {"color": col(COLORS["bg"]), "transparency": lit(0.0)}}]}}, separators=(",", ":"))
    return {"id": ordinal, "name": f"ReportSection{ordinal:02d}{uuid.uuid4().hex[:6]}", "displayName": name, "filters": "[]", "ordinal": ordinal, "visualContainers": visuals, "config": config, "displayOption": 1, "width": 1280, "height": 720}


def build_layout() -> None:
    def read_rows(name: str) -> list[dict]:
        with (PREP / f"{name}.csv").open(newline="", encoding="utf-8") as f:
            return list(csv.DictReader(f))

    def fnum(row: dict, key: str) -> float:
        return float(row.get(key) or 0)

    def group_sum(rows: list[dict], key_fn, value_key: str) -> list[tuple[str, float]]:
        out: dict[str, float] = {}
        for row in rows:
            key = key_fn(row)
            out[key] = out.get(key, 0.0) + fnum(row, value_key)
        return sorted(out.items(), key=lambda x: x[1], reverse=True)

    fe = read_rows("fact_emissions")
    suppliers = read_rows("fact_supplier_month")
    scenarios = read_rows("fact_carbon_exposure")
    initiatives = read_rows("fact_abatement_initiatives")
    supplier_dim = read_rows("dim_supplier")
    bu = {r["business_unit_id"]: r["business_unit"] for r in read_rows("dim_business_unit")}
    fac = {r["facility_id"]: r["facility"] for r in read_rows("dim_facility")}
    act = {r["activity_id"]: r["ghg_category"] for r in read_rows("dim_activity")}

    total = sum(fnum(r, "emissions_tco2e") for r in fe)
    spend = sum(fnum(r, "spend_usd") for r in fe)
    revenue = sum(fnum(r, "revenue_usd") for r in fe)
    carbon_price = 50
    carbon_cost = total * carbon_price
    intensity = total / revenue * 1_000_000
    latest_key = max(r["date_key"] for r in fe)
    latest = sum(fnum(r, "emissions_tco2e") for r in fe if r["date_key"] == latest_key)
    prior_key = str(int(latest_key) - 100)
    prior = sum(fnum(r, "emissions_tco2e") for r in fe if r["date_key"] == prior_key)
    yoy = (latest - prior) / prior if prior else 0
    scope = dict(group_sum(fe, lambda r: r["scope"], "emissions_tco2e"))
    monthly = group_sum(fe, lambda r: r["date_key"], "emissions_tco2e")
    monthly = sorted(monthly, key=lambda x: x[0])[-10:]
    monthly_values = [v for _, v in monthly]
    monthly_scope_values = {
        scope_name: [
            sum(fnum(r, "emissions_tco2e") for r in fe if r["date_key"] == date_key and r["scope"] == scope_name)
            for date_key, _ in monthly
        ]
        for scope_name in ["Scope 1", "Scope 2", "Scope 3"]
    }
    supplier_monthly_values = [
        sum(fnum(r, "emissions_tco2e") for r in suppliers if r["date_key"] == date_key)
        for date_key, _ in monthly
    ]
    high_risk_monthly_values = [
        sum(fnum(r, "emissions_tco2e") for r in suppliers if r["date_key"] == date_key and r["carbon_risk_tier"] == "High")
        for date_key, _ in monthly
    ]
    scenario_monthly_values = [
        sum(fnum(r, "carbon_cost_usd") for r in scenarios if r["date_key"] == date_key and r["scenario"] == "Base internal price")
        for date_key, _ in monthly
    ]
    bu_hotspots = group_sum(fe, lambda r: bu.get(r["business_unit_id"], r["business_unit_id"]), "emissions_tco2e")[:5]
    scope_rows = group_sum(fe, lambda r: r["scope"], "emissions_tco2e")
    category_rows = group_sum(fe, lambda r: act.get(r["activity_id"], r["activity_id"]), "emissions_tco2e")[:6]
    facility_rows = group_sum(fe, lambda r: fac.get(r["facility_id"], r["facility_id"]), "emissions_tco2e")[:6]
    supplier_intensity = sorted(
        group_sum(suppliers, lambda r: r["supplier"], "supplier_intensity_tco2e_per_musd"),
        key=lambda x: x[1],
        reverse=True,
    )[:6]
    supplier_table = sorted(suppliers, key=lambda r: fnum(r, "supplier_intensity_tco2e_per_musd"), reverse=True)[:6]
    scenario_rows = group_sum(scenarios, lambda r: r["scenario"], "carbon_cost_usd")
    abatement_reduction = sum(fnum(r, "annual_reduction_tco2e") for r in initiatives)
    abatement_capex = sum(fnum(r, "capex_usd") for r in initiatives)
    abatement_benefit = sum(fnum(r, "annual_opex_savings_usd") for r in initiatives) + abatement_reduction * 90
    abatement_roi = abatement_benefit / abatement_capex if abatement_capex else 0
    payback = abatement_capex / abatement_benefit if abatement_benefit else 0
    macc_rows = sorted(
        [(r["initiative"], (fnum(r, "capex_usd") / 7 - fnum(r, "annual_opex_savings_usd")) / fnum(r, "annual_reduction_tco2e")) for r in initiatives],
        key=lambda x: x[1],
    )[:6]
    reduction_rows = sorted([(r["initiative"], fnum(r, "annual_reduction_tco2e")) for r in initiatives], key=lambda x: x[1], reverse=True)[:6]
    supplier_risk_rows = group_sum(suppliers, lambda r: r["carbon_risk_tier"], "emissions_tco2e")
    target_status_rows = group_sum(suppliers, lambda r: r["target_status"], "emissions_tco2e")[:6]
    initiative_status_capex = group_sum(initiatives, lambda r: r["implementation_status"], "capex_usd")
    high_risk_supplier_emissions = sum(fnum(r, "emissions_tco2e") for r in suppliers if r["carbon_risk_tier"] == "High")
    avg_data_quality = sum(fnum(r, "data_quality_score") for r in supplier_dim) / len(supplier_dim)
    no_verified_target_suppliers = sum(1 for r in supplier_dim if r["target_status"] == "No verified target")
    planned_capex = sum(fnum(r, "capex_usd") for r in initiatives if r["implementation_status"] == "Planned")
    committed_reduction = sum(
        fnum(r, "annual_reduction_tco2e")
        for r in initiatives
        if r["implementation_status"] in {"Committed", "In flight", "Implemented"}
    )
    probability_weighted_cost = sum(fnum(r, "probability_weighted_cost_usd") for r in scenarios)
    months_2026 = sorted({r["date_key"] for r in fe if r["date_key"].startswith("2026")})
    run_rate_2026 = (
        sum(fnum(r, "emissions_tco2e") for r in fe if r["date_key"].startswith("2026")) / len(months_2026) * 12
        if months_2026
        else 0
    )
    baseline_annual = total / (len({r["date_key"] for r in fe}) / 12)
    target_gap = run_rate_2026 - baseline_annual * 0.86
    supplier_action: dict[str, dict] = {}
    for row in suppliers:
        item = supplier_action.setdefault(
            row["supplier"],
            {
                "risk": row["carbon_risk_tier"],
                "target": row["target_status"],
                "emissions": 0.0,
                "spend": 0.0,
            },
        )
        item["emissions"] += fnum(row, "emissions_tco2e")
        item["spend"] += fnum(row, "spend_usd")
    high_risk_supplier_table = sorted(
        [
            [
                supplier,
                item["risk"],
                item["target"],
                f"{(item['emissions'] / item['spend'] * 1_000_000) if item['spend'] else 0:.0f}",
            ]
            for supplier, item in supplier_action.items()
            if item["risk"] == "High" or item["target"] == "No verified target"
        ],
        key=lambda row: float(row[3]),
        reverse=True,
    )[:6]

    def fmt_k(v: float) -> str:
        return f"{v / 1000:.1f}K"

    def fmt_m(v: float) -> str:
        return f"${v / 1_000_000:.1f}M"

    def fmt_n(v: float) -> str:
        return f"{v:,.0f}"

    def fmt_pct(v: float) -> str:
        return f"{v * 100:.1f}%"

    def spark(values: list[float]) -> str:
        blocks = "▁▂▃▄▅▆▇█"
        cleaned = [float(v) for v in values if v is not None]
        if not cleaned:
            return ""
        lo, hi = min(cleaned), max(cleaned)
        if hi == lo:
            return blocks[3] * len(cleaned)
        return "".join(blocks[min(len(blocks) - 1, max(0, round((v - lo) / (hi - lo) * (len(blocks) - 1))))] for v in cleaned)

    def fit_text(value: object, width: float, min_chars: int = 8) -> str:
        text = str(value)
        max_chars = max(min_chars, int(width / 5.8))
        if len(text) <= max_chars:
            return text
        return text[: max_chars - 3].rstrip() + "..."

    def visual_text(runs: list[tuple[str, int, str, str]], p: dict, fill: str | None = None, border: bool = False):
        text_runs = [{"value": value, "textStyle": {"fontFamily": family, "fontSize": f"{size}pt", "color": color}} for value, size, color, family in runs]
        objects = {"general": [{"properties": {"paragraphs": [{"textRuns": text_runs}]}}]}
        vc = {
            "background": [{"properties": {"show": lit(fill is not None), "color": col(fill or "#FFFFFF"), "transparency": lit(0.0)}}],
            "border": [{"properties": {"show": lit(border), "color": col(COLORS["border"]), "radius": lit(6.0), "width": lit(1.0)}}],
            "visualHeader": [{"properties": {"show": lit(False)}}],
        }
        if border:
            vc["dropShadow"] = [{"properties": {"show": lit(True), "position": txt("Outer"), "color": col("#D5DED8"), "transparency": lit(86.0), "angle": lit(45.0), "distance": lit(2.0)}}]
        return container({"name": uuid.uuid4().hex[:20], "singleVisual": {"visualType": "textbox", "objects": objects, "drillFilterOtherVisuals": True, "vcObjects": vc}}, p)

    def rect(fill: str, p: dict, border: bool = False):
        return visual_text([(" ", 1, fill, "Segoe UI")], p, fill=fill, border=border)

    def title_text(text: str, p: dict):
        return visual_text([(text, 10, COLORS["ink"], "Segoe UI Semibold")], p)

    def small_text(text: str, p: dict, color: str = COLORS["muted"]):
        return visual_text([(text, 7, color, "Segoe UI")], p)

    def static_header(page_title: str, subtitle: str, base: int, chips: list[tuple[str, str, int]] | None = None):
        visuals = [
            rect(COLORS["navy"], pos(0, 0, base, 1280, 86), border=False),
            visual_text([(page_title, 20, "#FFFFFF", "Segoe UI Semibold"), (f"\n{subtitle}", 8, "#DCEAE4", "Segoe UI")], pos(30, 14, base + 1, 560, 58)),
        ]
        chip_defs = chips or [("Year", "All", 86), ("Region", "All", 98), ("Business Unit", "All", 118), ("Scope", "All", 90), ("Carbon price", "Base $50/t", 146)]
        x = 610
        for i, (label, value, width) in enumerate(chip_defs):
            visuals.append(
                visual_text(
                    [(fit_text(label, width - 16), 6, COLORS["muted"], "Segoe UI"), (f"\n{fit_text(value, width - 16)}", 8, COLORS["ink"], "Segoe UI Semibold")],
                    pos(x, 18, base + 10 + i, width, 46),
                    fill="#FFFFFF",
                    border=True,
                )
            )
            x += width + 10
        return visuals

    def kpi(label: str, value: str, p: dict, accent: str, trend: list[float] | None = None, note: str | None = None):
        runs = [
            (fit_text(label, p["width"] - 24), 8, COLORS["ink"], "Segoe UI Semibold"),
            (f"\n{value}", 19, accent, "Segoe UI Semibold"),
        ]
        if trend:
            runs.append((f"\n{spark(trend)}", 8, accent, "Segoe UI Semibold"))
        if note:
            runs.append((f"  {fit_text(note, p['width'] - 24)}", 6, COLORS["muted"], "Segoe UI"))
        return visual_text(runs, p, fill="#FFFFFF", border=True)

    def panel(title: str, sub: str, p: dict, z: int):
        return [rect("#FFFFFF", pos(p["x"], p["y"], z, p["width"], p["height"]), border=True), title_text(title, pos(p["x"] + 12, p["y"] + 10, z + 1, p["width"] - 24, 20)), small_text(sub, pos(p["x"] + 12, p["y"] + 32, z + 2, p["width"] - 24, 18))]

    def bars(title: str, sub: str, rows: list[tuple[str, float]], p: dict, z: int, color: str, value_fmt=fmt_k):
        visuals = panel(title, sub, p, z)
        max_v = max([v for _, v in rows] or [1])
        label_w = min(210, max(132, p["width"] * 0.38))
        bar_x = p["x"] + 18 + label_w
        value_w = 74
        bar_max_w = p["width"] - label_w - value_w - 52
        for i, (label, value) in enumerate(rows[:6]):
            y = p["y"] + 58 + i * 22
            visuals.append(small_text(fit_text(label, label_w), pos(p["x"] + 14, y - 2, z + 10 + i * 4, label_w - 6, 18), COLORS["ink"]))
            visuals.append(rect("#EDF2EF", pos(bar_x, y, z + 11 + i * 4, bar_max_w, 12)))
            visuals.append(rect(color, pos(bar_x, y, z + 12 + i * 4, max(8, bar_max_w * value / max_v), 12)))
            visuals.append(small_text(value_fmt(value), pos(p["x"] + p["width"] - value_w - 10, y - 2, z + 13 + i * 4, value_w, 18), COLORS["muted"]))
        return visuals

    def mini_trend(title: str, sub: str, rows: list[tuple[str, float]], p: dict, z: int):
        visuals = panel(title, sub, p, z)
        max_v = max([v for _, v in rows] or [1])
        bar_w = (p["width"] - 60) / max(len(rows), 1)
        for i, y in enumerate([p["y"] + 78, p["y"] + 126, p["y"] + 174]):
            visuals.append(rect("#E7EEE9", pos(p["x"] + 22, y, z + 8 + i, p["width"] - 44, 1)))
        for i, (label, value) in enumerate(rows):
            h = 108 * value / max_v
            x = p["x"] + 24 + i * bar_w
            y = p["y"] + 174 - h
            visuals.append(rect(COLORS["teal"], pos(x, y, z + 20 + i, max(10, bar_w - 6), h)))
            visuals.append(small_text(label[-2:], pos(x, p["y"] + 180, z + 40 + i, 28, 16), COLORS["muted"]))
        return visuals

    def status_tone(value: object) -> str:
        text = str(value).lower()
        if any(token in text for token in ["high", "shock", "no verified", "planned", "gap"]):
            return "#FBE7E1"
        if any(token in text for token in ["medium", "committed", "in flight", "target"]):
            return "#FFF2D9"
        if any(token in text for token in ["low", "implemented", "renewable", "sbti", "owned"]):
            return "#EAF3EA"
        return "#F4F7F5"

    def text_table(title: str, sub: str, headers: list[str], rows: list[list[str]], p: dict, z: int, widths: list[float] | None = None, status_cols: set[int] | None = None):
        visuals = panel(title, sub, p, z)
        available_w = p["width"] - 28
        if widths:
            total = sum(widths)
            col_widths = [available_w * w / total for w in widths]
        else:
            col_widths = [available_w / len(headers)] * len(headers)
        visuals.append(rect("#EAF1ED", pos(p["x"] + 10, p["y"] + 54, z + 18, p["width"] - 20, 22)))
        x_positions = []
        x = p["x"] + 14
        for i, h in enumerate(headers):
            x_positions.append(x)
            visuals.append(visual_text([(fit_text(h, col_widths[i]), 7, COLORS["ink"], "Segoe UI Semibold")], pos(x, p["y"] + 58, z + 20 + i, col_widths[i] - 4, 18)))
            x += col_widths[i]
        for r, row in enumerate(rows[:6]):
            y = p["y"] + 84 + r * 18
            if r % 2 == 0:
                visuals.append(rect("#F4F7F5", pos(p["x"] + 10, y - 2, z + 40 + r, p["width"] - 20, 18)))
            for c, val in enumerate(row):
                cell_x = x_positions[c]
                cell_w = col_widths[c] - 4
                if status_cols and c in status_cols:
                    visuals.append(rect(status_tone(val), pos(cell_x - 3, y - 1, z + 58 + r * 10 + c, min(cell_w, max(36, len(str(val)) * 5.3 + 12)), 15)))
                visuals.append(small_text(fit_text(val, cell_w), pos(cell_x, y, z + 60 + r * 10 + c, cell_w, 16), COLORS["ink"]))
        return visuals

    def actual_header(page_title: str, subtitle: str, base: int, slicers_def: list[tuple[str, str, str, int]] | None = None):
        slicers_def = slicers_def or [
            ("dim_date", "year", "Year", 72),
            ("dim_facility", "region", "Region", 82),
            ("dim_business_unit", "business_unit", "Business Unit", 112),
            ("fact_emissions", "scope", "Scope", 76),
            ("dim_carbon_scenario", "scenario", "Carbon price", 118),
        ]
        visuals = [
            shape(COLORS["navy"], pos(0, 0, base, 1280, 86)),
            textbox(page_title, subtitle, pos(28, 12, base + 1, 500, 58)),
        ]
        x = 552
        for i, (table, column, display, width) in enumerate(slicers_def):
            visuals.append(slicer(table, column, display, pos(x, 18, base + 10 + i, width, 50)))
            x += width + 10
        return visuals

    def kpi_native(label: str, measure: str, p: dict, accent: str, trend: list[float] | None = None, note: str | None = None):
        visuals = [card(measure, label, p, accent)]
        if trend:
            suffix = f"  {note}" if note else ""
            visuals.append(visual_text([(spark(trend), 8, accent, "Segoe UI Semibold"), (suffix, 6, COLORS["muted"], "Segoe UI")], pos(p["x"] + 12, p["y"] + p["height"] - 24, p["z"] + 500, p["width"] - 24, 18)))
        return visuals

    p1 = actual_header("ESG Finance Overview", "Emissions, carbon cost exposure, intensity and executive trend", 1)
    for i, (label, measure, color, trend, note) in enumerate([
        ("Total emissions", "Total Emissions tCO2e", COLORS["teal"], monthly_values, "10 mo"),
        ("Carbon cost", "Carbon Cost USD", COLORS["amber"], [v * carbon_price for v in monthly_values], "base"),
        ("Intensity", "Emissions Intensity tCO2e per $M Revenue", COLORS["lime"], monthly_values, "t/$M"),
        ("YoY change", "YoY Emissions Change %", COLORS["coral"], monthly_values, "latest"),
        ("Latest month", "Latest Month Emissions tCO2e", COLORS["green2"], monthly_values, "May 26"),
    ]):
        p1 += kpi_native(label, measure, pos(28 + i * 222, 104, 100 + i, 206, 90), color, trend, note)
    p1.append(multi_chart("lineChart", "Monthly Emissions + Carbon Cost", "Trend by month with selected carbon price", "dim_date", "month_start", "Month", [("Total Emissions tCO2e", "Emissions"), ("Carbon Cost USD", "Carbon Cost")], pos(28, 214, 200, 500, 210), "month_start"))
    p1.append(single_chart("barChart", "Emissions by Scope", "Scope 1, 2 and 3 contribution", "fact_emissions", "scope", "Scope", "Total Emissions tCO2e", "tCO2e", pos(552, 214, 300, 280, 210), COLORS["teal"], order_measure=True, ascending=False))
    p1.append(single_chart("barChart", "Business Unit Hotspots", "Where emissions concentrate", "dim_business_unit", "business_unit", "Business Unit", "Total Emissions tCO2e", "tCO2e", pos(856, 214, 400, 320, 210), COLORS["navy"], order_measure=True, ascending=False))
    p1.append(table_visual("Executive Detail", "Carbon finance follow-up priorities", [("dim_business_unit", "business_unit", "Business Unit"), ("dim_facility", "region", "Region")], [("Total Emissions tCO2e", "Emissions"), ("Carbon Cost USD", "Carbon Cost"), ("Emissions Intensity tCO2e per $M Revenue", "Intensity")], pos(28, 458, 500, 1148, 190), "Carbon Cost USD"))

    p2 = actual_header(
        "Emissions & Supplier Intensity",
        "Scope/source diagnostics, supplier intensity and data quality",
        1000,
        [
            ("dim_date", "year", "Year", 72),
            ("fact_emissions", "scope", "Scope", 80),
            ("fact_supplier_month", "carbon_risk_tier", "Risk tier", 96),
            ("dim_supplier", "target_status", "Target status", 118),
            ("dim_facility", "region", "Region", 84),
        ],
    )
    for i, (label, measure, color, trend, note) in enumerate([
        ("Scope 1", "Scope 1 Emissions tCO2e", COLORS["coral"], monthly_scope_values["Scope 1"], "owned"),
        ("Scope 2", "Scope 2 Emissions tCO2e", COLORS["amber"], monthly_scope_values["Scope 2"], "energy"),
        ("Scope 3", "Scope 3 Emissions tCO2e", COLORS["teal"], monthly_scope_values["Scope 3"], "value chain"),
        ("Supplier intensity", "Supplier Intensity tCO2e per $M Spend", COLORS["lime"], supplier_monthly_values, "t/$M"),
    ]):
        p2 += kpi_native(label, measure, pos(28 + i * 286, 104, 1100 + i, 268, 90), color, trend, note)
    p2.append(single_chart("barChart", "Source Category Emissions", "GHG source categories ranked by footprint", "dim_activity", "ghg_category", "Category", "Total Emissions tCO2e", "tCO2e", pos(28, 214, 1200, 360, 210), COLORS["teal"], order_measure=True, ascending=False))
    p2.append(single_chart("barChart", "Supplier Intensity Ranking", "tCO2e per $M spend", "dim_supplier", "supplier", "Supplier", "Supplier Intensity tCO2e per $M Spend", "Intensity", pos(408, 214, 1300, 360, 210), COLORS["amber"], order_measure=True, ascending=False))
    p2.append(single_chart("barChart", "Facility Emissions", "Operational footprint by facility", "dim_facility", "facility", "Facility", "Total Emissions tCO2e", "tCO2e", pos(788, 214, 1400, 388, 210), COLORS["navy"], order_measure=True, ascending=False))
    p2.append(table_visual("Supplier Risk Table", "Risk, target status and spend-normalized intensity", [("dim_supplier", "supplier", "Supplier"), ("dim_supplier", "supplier_category", "Category"), ("dim_supplier", "carbon_risk_tier", "Risk"), ("dim_supplier", "target_status", "Target")], [("Supplier Emissions tCO2e", "Emissions"), ("Supplier Intensity tCO2e per $M Spend", "Intensity")], pos(28, 458, 1500, 1148, 190), "Supplier Intensity tCO2e per $M Spend"))

    p3 = actual_header(
        "Carbon Scenario & Abatement ROI",
        "Carbon price exposure, MACC and capital prioritization",
        2000,
        [
            ("dim_carbon_scenario", "scenario", "Scenario", 118),
            ("fact_emissions", "scope", "Scope", 76),
            ("fact_abatement_initiatives", "implementation_status", "Status", 100),
            ("dim_date", "year", "Year", 72),
            ("dim_facility", "region", "Region", 84),
        ],
    )
    for i, (label, measure, color, trend, note) in enumerate([
        ("Carbon price", "Selected Carbon Price USD/t", COLORS["amber"], scenario_monthly_values, "base"),
        ("Scenario cost", "Scenario Carbon Cost USD", COLORS["coral"], scenario_monthly_values, "all scenarios"),
        ("Annual reduction", "Abatement Annual Reduction tCO2e", COLORS["teal"], [fnum(r, "annual_reduction_tco2e") for r in initiatives], "pipeline"),
        ("Abatement ROI", "Abatement ROI", COLORS["lime"], [fnum(r, "roi_at_90") for r in initiatives], "@$90/t"),
        ("Payback years", "Payback Years", COLORS["green2"], [fnum(r, "payback_years_at_90") for r in initiatives], "portfolio"),
    ]):
        p3 += kpi_native(label, measure, pos(28 + i * 222, 104, 2100 + i, 206, 90), color, trend, note)
    p3.append(single_chart("barChart", "Scenario Exposure by Path", "Carbon cost under each pricing scenario", "dim_carbon_scenario", "scenario", "Scenario", "Scenario Carbon Cost USD", "Scenario cost", pos(28, 214, 2200, 360, 210), COLORS["coral"], order_measure=True, ascending=False))
    p3.append(single_chart("barChart", "MACC Priority Ranking", "Lower cost per tCO2e first", "fact_abatement_initiatives", "initiative", "Initiative", "MACC USD per tCO2e", "MACC", pos(408, 214, 2300, 360, 210), COLORS["teal"], order_measure=True, ascending=True))
    p3.append(single_chart("barChart", "Reduction by Initiative", "Annual tCO2e reduction potential", "fact_abatement_initiatives", "initiative", "Initiative", "Abatement Annual Reduction tCO2e", "Reduction", pos(788, 214, 2400, 388, 210), COLORS["navy"], order_measure=True, ascending=False))
    p3.append(table_visual("Abatement Action Queue", "Investment case by status, payback, ROI and MACC", [("fact_abatement_initiatives", "initiative", "Initiative"), ("fact_abatement_initiatives", "implementation_status", "Status"), ("fact_abatement_initiatives", "scope", "Scope")], [("Abatement Capex USD", "Capex"), ("Abatement Annual Reduction tCO2e", "Reduction"), ("Abatement ROI", "ROI"), ("MACC USD per tCO2e", "MACC")], pos(28, 458, 2500, 1148, 190), "Abatement ROI"))

    p4 = actual_header(
        "Risk & Action Control Tower",
        "Supplier risk, target gaps and governance queue",
        3000,
        [
            ("fact_supplier_month", "carbon_risk_tier", "Risk tier", 96),
            ("dim_supplier", "target_status", "Target status", 118),
            ("fact_abatement_initiatives", "implementation_status", "Impl. status", 108),
            ("dim_date", "year", "Year", 72),
            ("dim_facility", "region", "Region", 82),
        ],
    )
    p4.append(kpi("High-risk emissions", fmt_k(high_risk_supplier_emissions), pos(28, 104, 3100, 206, 90), COLORS["coral"], high_risk_monthly_values, "supplier"))
    p4.append(kpi("No target suppliers", fmt_n(no_verified_target_suppliers), pos(250, 104, 3101, 206, 90), COLORS["amber"], [no_verified_target_suppliers] * 10, "count"))
    p4 += kpi_native("Data quality", "Average Data Quality Score", pos(472, 104, 3102, 206, 90), COLORS["teal"], [avg_data_quality] * 10, "avg")
    p4.append(kpi("2026 target gap", fmt_k(target_gap), pos(694, 104, 3103, 206, 90), COLORS["lime"] if target_gap <= 0 else COLORS["coral"], monthly_values, "run-rate"))
    p4.append(kpi("Planned capex", fmt_m(planned_capex), pos(916, 104, 3104, 206, 90), COLORS["green2"], [fnum(r, "capex_usd") for r in initiatives if r["implementation_status"] == "Planned"], "pipeline"))
    p4.append(single_chart("barChart", "Supplier Risk Exposure", "Emissions by supplier risk tier", "fact_supplier_month", "carbon_risk_tier", "Risk tier", "Supplier Emissions tCO2e", "Emissions", pos(28, 214, 3200, 360, 210), COLORS["coral"], order_measure=True, ascending=False))
    p4.append(single_chart("barChart", "Target Status Exposure", "Supplier emissions by target maturity", "dim_supplier", "target_status", "Target status", "Supplier Emissions tCO2e", "Emissions", pos(408, 214, 3300, 360, 210), COLORS["amber"], order_measure=True, ascending=False))
    p4.append(single_chart("barChart", "Capex by Action Status", "Abatement investment still to govern", "fact_abatement_initiatives", "implementation_status", "Status", "Abatement Capex USD", "Capex", pos(788, 214, 3400, 388, 210), COLORS["navy"], order_measure=True, ascending=False))
    p4.append(table_visual("Risk Action Queue", "Supplier follow-up for CFO/ESG review", [("dim_supplier", "supplier", "Supplier"), ("dim_supplier", "carbon_risk_tier", "Risk"), ("dim_supplier", "target_status", "Target")], [("Supplier Emissions tCO2e", "Emissions"), ("Supplier Intensity tCO2e per $M Spend", "Intensity")], pos(28, 458, 3500, 744, 190), "Supplier Intensity tCO2e per $M Spend"))
    p4.append(
        visual_text(
            [
                ("Guardrail Summary", 10, COLORS["ink"], "Segoe UI Semibold"),
                ("\nValues reconcile to model guardrails", 7, COLORS["muted"], "Segoe UI"),
                (f"\n\nWeighted cost        {fmt_m(probability_weighted_cost)}", 8, COLORS["ink"], "Segoe UI Semibold"),
                (f"\nSecured reduction    {fmt_k(committed_reduction)}", 8, COLORS["ink"], "Segoe UI Semibold"),
                (f"\nPlanned capex        {fmt_m(planned_capex)}", 8, COLORS["ink"], "Segoe UI Semibold"),
                (f"\nHigh-risk emissions  {fmt_k(high_risk_supplier_emissions)}", 8, COLORS["ink"], "Segoe UI Semibold"),
            ],
            pos(796, 458, 3600, 380, 190),
            fill="#FFFFFF",
            border=True,
        )
    )

    cfg = {"version": "5.73", "activeSectionIndex": 0, "defaultDrillFilterOtherVisuals": True, "settings": {"useNewFilterPaneExperience": True, "useStylableVisualContainerHeader": True, "queryLimitOption": 6}}
    layout = {
        "activeSectionIndex": 0,
        "sections": [
            section("ESG Finance Overview", 0, p1),
            section("Emissions & Supplier Intensity", 1, p2),
            section("Carbon Scenario & Abatement ROI", 2, p3),
            section("Risk & Action Control Tower", 3, p4),
        ],
        "config": json.dumps(cfg, separators=(",", ":")),
        "layoutOptimization": 0,
    }
    visual_type_counts: dict[str, int] = {}
    for report_section in layout["sections"]:
        for visual_container in report_section["visualContainers"]:
            try:
                visual_type = json.loads(visual_container["config"])["singleVisual"]["visualType"]
            except Exception:
                visual_type = "unknown"
            visual_type_counts[visual_type] = visual_type_counts.get(visual_type, 0) + 1
    write_json(ROOT / "build" / "native_report_layout_project18.json", layout)
    write_json(
        ROOT / "qa" / "native_report_layout_summary.json",
        {
            "status": "layout_json_generated",
            "pages": [s["displayName"] for s in layout["sections"]],
            "visual_containers": sum(len(s["visualContainers"]) for s in layout["sections"]),
            "visual_type_counts": visual_type_counts,
            "native_visual_containers": sum(count for visual_type, count in visual_type_counts.items() if visual_type != "textbox"),
        },
    )


def write_scripts() -> None:
    write_text(ROOT / "build" / "scripts" / "02_push_model_bim_via_tom.ps1", r'''
param([string]$ProjectRoot="", [string]$TargetPbix="", [string]$ModelBim="")
$ErrorActionPreference="Stop"
if([string]::IsNullOrWhiteSpace($ProjectRoot)){ $ProjectRoot=Resolve-Path (Join-Path $PSScriptRoot "..\..") }
if([string]::IsNullOrWhiteSpace($TargetPbix)){ $TargetPbix=Join-Path $ProjectRoot "output\dashboard_model_seed.pbix" }
if([string]::IsNullOrWhiteSpace($ModelBim)){ $ModelBim=Join-Path $ProjectRoot "model\model.bim" }
$QaRoot=Join-Path $ProjectRoot "qa"; New-Item -ItemType Directory -Force -Path $QaRoot|Out-Null
function Get-PowerBiBin { $cmd=Get-Command PBIDesktop.exe -ErrorAction SilentlyContinue; if($cmd){ return Split-Path -Parent $cmd.Source }; return "C:\Program Files\Microsoft Power BI Desktop\bin" }
function Get-Session([string]$Path){ $resolved=[IO.Path]::GetFullPath($Path); $text=& pbi-tools info 2>&1|Out-String; $info=$text.Substring($text.IndexOf("{"))|ConvertFrom-Json; $m=@($info.pbiSessions|Where-Object{$_.PbixPath -and ([IO.Path]::GetFullPath([string]$_.PbixPath) -ieq $resolved)}); if($m.Count -ne 1){$info.pbiSessions|ConvertTo-Json -Depth 8|Set-Content (Join-Path $QaRoot "pbi_sessions_debug.json"); throw "Expected one session for $resolved, found $($m.Count)"}; return $m[0] }
function DT([string]$t){ switch($t){"string"{[Microsoft.AnalysisServices.Tabular.DataType]::String}"int64"{[Microsoft.AnalysisServices.Tabular.DataType]::Int64}"double"{[Microsoft.AnalysisServices.Tabular.DataType]::Double}"dateTime"{[Microsoft.AnalysisServices.Tabular.DataType]::DateTime} default{[Microsoft.AnalysisServices.Tabular.DataType]::String}}}
function AF([object]$v){ switch(([string]$v).ToLowerInvariant()){"sum"{[Microsoft.AnalysisServices.Tabular.AggregateFunction]::Sum} default{[Microsoft.AnalysisServices.Tabular.AggregateFunction]::None}}}
function Expr($e){ if($e -is [array]){return ($e -join "`r`n")}; return [string]$e }
function T($m,[string]$n){ foreach($t in $m.Tables){if($t.Name -eq $n){return $t}} throw "Table not found $n" }
function C($t,[string]$n){ foreach($c in $t.Columns){if($c.Name -eq $n){return $c}} throw "Column not found $($t.Name).$n" }
Add-Type -Path (Join-Path (Get-PowerBiBin) "Microsoft.PowerBI.Amo.dll")
$session=Get-Session $TargetPbix
$server=New-Object Microsoft.AnalysisServices.Tabular.Server; $server.Connect("localhost:$($session.Port)")
$model=$server.Databases[0].Model; $model.Relationships.Clear(); $model.Tables.Clear()
$def=Get-Content $ModelBim -Raw -Encoding UTF8|ConvertFrom-Json
foreach($td in $def.model.tables){ $t=New-Object Microsoft.AnalysisServices.Tabular.Table; $t.Name=[string]$td.name; $model.Tables.Add($t); foreach($cd in @($td.columns)){ $c=New-Object Microsoft.AnalysisServices.Tabular.DataColumn; $c.Name=[string]$cd.name; $c.SourceColumn=if($cd.sourceColumn){[string]$cd.sourceColumn}else{[string]$cd.name}; $c.DataType=DT ([string]$cd.dataType); if($cd.isHidden){$c.IsHidden=[bool]$cd.isHidden}; if($cd.formatString){$c.FormatString=[string]$cd.formatString}; if($cd.summarizeBy){$c.SummarizeBy=AF $cd.summarizeBy}; $t.Columns.Add($c)}; foreach($pd in @($td.partitions)){ $p=New-Object Microsoft.AnalysisServices.Tabular.Partition; $p.Name=[string]$pd.name; $p.Mode=[Microsoft.AnalysisServices.Tabular.ModeType]::Import; $s=New-Object Microsoft.AnalysisServices.Tabular.MPartitionSource; $s.Expression=Expr $pd.source.expression; $p.Source=$s; $t.Partitions.Add($p)}; foreach($md in @($td.measures)){ if($md -and $md.name){$mm=New-Object Microsoft.AnalysisServices.Tabular.Measure; $mm.Name=[string]$md.name; $mm.Expression=[string]$md.expression; if($md.formatString){$mm.FormatString=[string]$md.formatString}; $t.Measures.Add($mm)}} }
foreach($rd in @($def.model.relationships)){ $r=New-Object Microsoft.AnalysisServices.Tabular.SingleColumnRelationship; $r.Name=[string]$rd.name; $r.FromColumn=C (T $model ([string]$rd.fromTable)) ([string]$rd.fromColumn); $r.ToColumn=C (T $model ([string]$rd.toTable)) ([string]$rd.toColumn); $r.FromCardinality=[Microsoft.AnalysisServices.Tabular.RelationshipEndCardinality]::Many; $r.ToCardinality=[Microsoft.AnalysisServices.Tabular.RelationshipEndCardinality]::One; $r.CrossFilteringBehavior=[Microsoft.AnalysisServices.Tabular.CrossFilteringBehavior]::OneDirection; $r.IsActive=$true; $model.Relationships.Add($r)}
$model.SaveChanges(); $model.RequestRefresh([Microsoft.AnalysisServices.Tabular.RefreshType]::Full); $model.SaveChanges()
$result=[ordered]@{status="model_pushed_via_tom"; target_pbix=[IO.Path]::GetFullPath($TargetPbix); port=$session.Port; process_id=$session.ProcessId; table_count=$model.Tables.Count; relationship_count=$model.Relationships.Count}
$result|ConvertTo-Json -Depth 8|Set-Content (Join-Path $QaRoot "seed_model_push_via_tom.json") -Encoding UTF8
$server.Disconnect(); $result|ConvertTo-Json -Depth 8
''')
    write_text(ROOT / "build" / "scripts" / "03_apply_native_layout_to_pbix.ps1", r'''
param([string]$ModelPbix="", [string]$LayoutJson="", [string]$OutputPbix="", [string]$FinalPbix="")
$ErrorActionPreference="Stop"; $ProjectRoot=Resolve-Path (Join-Path $PSScriptRoot "..\.."); $QaRoot=Join-Path $ProjectRoot "qa"; New-Item -ItemType Directory -Force -Path $QaRoot|Out-Null
function Resolve-ProjectPath([string]$p,[string]$d){ if([string]::IsNullOrWhiteSpace($p)){return Join-Path $ProjectRoot $d}; if([IO.Path]::IsPathRooted($p)){return $p}; return Join-Path $ProjectRoot $p }
$ModelPbix=Resolve-ProjectPath $ModelPbix "output\dashboard_model_seed.pbix"; $LayoutJson=Resolve-ProjectPath $LayoutJson "build\native_report_layout_project18.json"; $OutputPbix=Resolve-ProjectPath $OutputPbix "output\dashboard_v01.pbix"; $FinalPbix=Resolve-ProjectPath $FinalPbix "output\dashboard_final.pbix"
$bin=(Split-Path -Parent (Get-Command PBIDesktop.exe).Source); $dll=Join-Path $bin "Microsoft.PowerBI.Packaging.dll"; [Reflection.Assembly]::LoadFrom($dll)|Out-Null; Add-Type -AssemblyName WindowsBase
function V([string]$p){ $s=[IO.File]::OpenRead($p); try{[Microsoft.PowerBI.Packaging.PowerBIPackager]::Validate($s)}finally{$s.Dispose()} }
V $ModelPbix; Copy-Item $ModelPbix $OutputPbix -Force
$layout=Get-Content $LayoutJson -Raw|ConvertFrom-Json; $bytes=[Text.Encoding]::Unicode.GetBytes(($layout|ConvertTo-Json -Depth 100 -Compress))
$pkg=[System.IO.Packaging.Package]::Open($OutputPbix,[IO.FileMode]::Open,[IO.FileAccess]::ReadWrite)
try{$u=New-Object System.Uri("/Report/Layout",[System.UriKind]::Relative); $part=$pkg.GetPart($u); $st=$part.GetStream([IO.FileMode]::Open,[IO.FileAccess]::ReadWrite); try{$st.SetLength(0);$st.Write($bytes,0,$bytes.Length)}finally{$st.Dispose()}; $su=New-Object System.Uri("/SecurityBindings",[System.UriKind]::Relative); if($pkg.PartExists($su)){$pkg.DeletePart($su)}}finally{$pkg.Close()}
V $OutputPbix; Copy-Item $OutputPbix $FinalPbix -Force; V $FinalPbix
$result=[ordered]@{status="passed"; final_pbix=$FinalPbix; final_pbix_created=$true; final_pbix_size=(Get-Item $FinalPbix).Length; pages=@($layout.sections|ForEach-Object{$_.displayName}); visual_containers=($layout.sections|ForEach-Object{$_.visualContainers.Count}|Measure-Object -Sum).Sum}
$result|ConvertTo-Json -Depth 8|Set-Content (Join-Path $QaRoot "pbix_native_report_validation.json") -Encoding UTF8; $result|ConvertTo-Json -Depth 8
''')
    write_text(ROOT / "build" / "scripts" / "04_validate_output.py", """import json
import hashlib
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
p=ROOT/'output'/'dashboard_final.pbix'
native_path = ROOT / 'qa' / 'pbix_native_report_validation.json'
native = json.loads(native_path.read_text(encoding='utf-8-sig')) if native_path.exists() else {}
desktop_path = ROOT / 'qa' / 'desktop_open_check.json'
desktop = json.loads(desktop_path.read_text(encoding='utf-8-sig')) if desktop_path.exists() else {}

def sha256(path: Path) -> str | None:
    if not path.exists():
        return None
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest().upper()

current_sha = sha256(p)
package_ok = p.exists() and p.stat().st_size > 100000
screenshots = desktop.get('screenshots', [])
screenshots_ok = bool(screenshots) and all((ROOT / s).exists() for s in screenshots)
desktop_pass = (
    desktop.get('status') == 'passed'
    and desktop.get('pbix_sha256') == current_sha
    and desktop.get('visual_error_count') == 0
    and screenshots_ok
)
pending_gap = 'Open output/dashboard_final.pbix in Power BI Desktop and capture fresh screenshots for all 4 pages before claiming fresh Desktop visual QA pass.'

r={
    'status':'desktop_open_check_passed' if package_ok and desktop_pass else ('package_pass_desktop_open_check_pending' if package_ok else 'fail'),
    'pbix_exists':p.exists(),
    'pbix_size_bytes':p.stat().st_size if p.exists() else 0,
    'sha256': current_sha,
    'build_route':'SCRIPTED_DESKTOP_PBIX',
    'native_package_validation_status': native.get('status'),
    'pages': native.get('pages', []),
    'visual_containers': native.get('visual_containers'),
    'desktop_open_check':'passed' if desktop_pass else 'not_rerun_after_v3_patch',
    'desktop_checked_at': desktop.get('checked_at') if desktop_pass else None,
    'visual_error_count': 0 if desktop_pass else None,
    'screenshots': screenshots if desktop_pass else [],
    'known_gap': None if desktop_pass else pending_gap
}
(ROOT/'qa'/'pbix_final_validation.json').write_text(json.dumps(r,indent=2),encoding='utf-8')
(ROOT/'qa'/'pbix_validation.json').write_text(json.dumps({
    'final_pbix_path': str(p),
    'opened_in_power_bi_desktop': bool(desktop_pass),
    'saved_after_open': False,
    'page_count': len(r['pages']),
    'visual_count': r['visual_containers'],
    'visual_error_count': r['visual_error_count'],
    'screenshots': r['screenshots'],
    'qa_status': r['status'],
    'native_package_validation': r['native_package_validation_status'],
    'build_route': r['build_route'],
    'known_issues': [] if desktop_pass else [r['known_gap']],
}, indent=2), encoding='utf-8')
print(json.dumps(r,indent=2))
""")


def main() -> None:
    build_model()
    build_layout()
    # PowerShell wrappers are maintained separately after Desktop compatibility fixes.
    final_pbix = ROOT / "output" / "dashboard_final.pbix"
    desktop_path = ROOT / "qa" / "desktop_open_check.json"
    desktop = json.loads(desktop_path.read_text(encoding="utf-8-sig")) if desktop_path.exists() else {}
    final_sha = sha256_file(final_pbix)
    screenshots = desktop.get("screenshots", [])
    screenshots_ok = bool(screenshots) and all((ROOT / s).exists() for s in screenshots)
    desktop_pass = (
        desktop.get("status") == "passed"
        and desktop.get("pbix_sha256") == final_sha
        and desktop.get("visual_error_count") == 0
        and screenshots_ok
    )
    manifest = {
        "status": "native_powerbi_assets_created",
        "version": "v3_upgrade_2026-06-23",
        "model_bim": str(ROOT / "model" / "model.bim"),
        "layout_json": str(ROOT / "build" / "native_report_layout_project18.json"),
        "target_seed_pbix": str(ROOT / "output" / "dashboard_model_seed.pbix"),
        "final_pbix": str(final_pbix),
        "pages": [
            "ESG Finance Overview",
            "Emissions & Supplier Intensity",
            "Carbon Scenario & Abatement ROI",
            "Risk & Action Control Tower",
        ],
        "desktop_open_check": "passed" if desktop_pass else "pending_after_v3_patch",
    }
    if desktop_pass:
        manifest.update({
            "desktop_checked_at": desktop.get("checked_at"),
            "final_pbix_sha256": final_sha,
            "visual_error_count": 0,
            "desktop_qa_contact_sheet": str(ROOT / "output" / "screenshots" / "desktop_qa_contact_sheet.png"),
        })
    write_json(ROOT / "output" / "build_manifest.json", manifest)
    print(json.dumps({"status": "ok", "model_bim": str(ROOT / "model" / "model.bim"), "layout": str(ROOT / "build" / "native_report_layout_project18.json")}, indent=2))


if __name__ == "__main__":
    main()
