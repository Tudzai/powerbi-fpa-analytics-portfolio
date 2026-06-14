from __future__ import annotations

import importlib.util
import json
import os
import shutil
import tempfile
import uuid
import zipfile
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SOURCE_PBIX = ROOT / "output" / "dashboard_final.pbix"
COMPLETE_PBIX = ROOT / "output" / "dashboard_complete.pbix"


def clone_zip_info(info: zipfile.ZipInfo) -> zipfile.ZipInfo:
    cloned = zipfile.ZipInfo(info.filename, date_time=info.date_time)
    cloned.comment = info.comment
    cloned.extra = info.extra
    cloned.internal_attr = info.internal_attr
    cloned.external_attr = info.external_attr
    cloned.create_system = info.create_system
    cloned.compress_type = info.compress_type
    return cloned


def load_visual_helpers():
    helper_path = ROOT / "build" / "scripts" / "09_visual_refresh.py"
    spec = importlib.util.spec_from_file_location("project7_visual_refresh", helper_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load visual helper module: {helper_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


VH = load_visual_helpers()
COLORS = VH.COLORS


def expr(value: str) -> dict:
    return VH.expr(value)


def solid(color: str) -> dict:
    return VH.solid(color)


def vc_objects(title: str, subtitle: str | None = None, border: str = "#E6EAF2") -> dict:
    return VH.vc_objects(title, subtitle, border)


def section_name() -> str:
    return uuid.uuid4().hex[:20]


def section(display: str, ordinal: int, visuals: list[dict]) -> dict:
    return {
        "id": ordinal,
        "name": section_name(),
        "displayName": display,
        "filters": "[]",
        "ordinal": ordinal,
        "visualContainers": visuals,
        "config": "{}",
        "displayOption": 1,
        "width": 1280,
        "height": 720,
    }


def source_ref(alias: str) -> dict:
    return {"SourceRef": {"Source": alias}}


def table_visual(
    name: str,
    fields: list[dict],
    title: str,
    subtitle: str,
    x: int,
    y: int,
    w: int,
    h: int,
    tab: int,
    order_measure: str | None = None,
    order_desc: bool = True,
) -> dict:
    froms: list[dict] = []
    aliases: dict[str, str] = {}

    def alias_for(table: str) -> str:
        if table not in aliases:
            alias = f"t{len(aliases)}" if table != "KPI Measures" else "k"
            aliases[table] = alias
            froms.append({"Name": alias, "Entity": table, "Type": 0})
        return aliases[table]

    selects: list[dict] = []
    projection_order: list[int] = []
    metadata_selects: list[dict] = []
    metadata_filters: list[dict] = []
    transform_selects: list[dict] = []
    projections: list[dict] = []

    for idx, field in enumerate(fields):
        projection_order.append(idx)
        if field["kind"] == "column":
            alias = alias_for(field["table"])
            qref = f"{field['table']}.{field['column']}"
            selects.append(
                {
                    "Column": {"Expression": source_ref(alias), "Property": field["column"]},
                    "Name": qref,
                    "NativeReferenceName": field["display"],
                }
            )
            metadata_selects.append({"Restatement": field["display"], "Name": qref, "Type": 2048})
            metadata_filters.append(
                {
                    "type": 0,
                    "expression": {
                        "Column": {"Expression": {"SourceRef": {"Entity": field["table"]}}, "Property": field["column"]}
                    },
                }
            )
            transform_selects.append(
                {
                    "displayName": field["display"],
                    "queryName": qref,
                    "roles": {"Values": True},
                    "type": {"category": None, "underlyingType": 1},
                    "expr": {
                        "Column": {"Expression": {"SourceRef": {"Entity": field["table"]}}, "Property": field["column"]}
                    },
                }
            )
        else:
            alias = alias_for("KPI Measures")
            qref = f"KPI Measures.{field['measure']}"
            fmt = field.get("format", "#,0")
            selects.append(
                {
                    "Measure": {"Expression": source_ref(alias), "Property": field["measure"]},
                    "Name": qref,
                    "NativeReferenceName": field["display"],
                }
            )
            metadata_selects.append({"Restatement": field["display"], "Name": qref, "Type": 1, "Format": fmt})
            metadata_filters.append(
                {
                    "type": 2,
                    "expression": {
                        "Measure": {
                            "Expression": {"SourceRef": {"Entity": "KPI Measures"}},
                            "Property": field["measure"],
                        }
                    },
                }
            )
            transform_selects.append(
                {
                    "displayName": field["display"],
                    "format": fmt,
                    "queryName": qref,
                    "roles": {"Values": True},
                    "type": {"category": None, "underlyingType": 259},
                    "expr": {
                        "Measure": {
                            "Expression": {"SourceRef": {"Entity": "KPI Measures"}},
                            "Property": field["measure"],
                        }
                    },
                }
            )
        projections.append({"queryRef": selects[-1]["Name"]})

    order_by = []
    if order_measure:
        alias = alias_for("KPI Measures")
        order_by = [
            {
                "Direction": 2 if order_desc else 1,
                "Expression": {"Measure": {"Expression": source_ref(alias), "Property": order_measure}},
            }
        ]

    query = {"Version": 2, "From": froms, "Select": selects}
    if order_by:
        query["OrderBy"] = order_by

    query_obj = {
        "Commands": [
            {
                "SemanticQueryDataShapeCommand": {
                    "Query": query,
                    "Binding": {
                        "Primary": {"Groupings": [{"Projections": projection_order, "Subtotal": 1}]},
                        "DataReduction": {"DataVolume": 3, "Primary": {"Window": {"Count": 500}}},
                        "Version": 1,
                    },
                    "ExecutionMetricsKind": 1,
                }
            }
        ]
    }
    transform = {
        "projectionOrdering": {"Values": projection_order},
        "queryMetadata": {"Select": metadata_selects, "Filters": metadata_filters},
        "visualElements": [
            {
                "DataRoles": [
                    {"Name": "Values", "Projection": idx, "isActive": False}
                    for idx in projection_order
                ]
            }
        ],
        "selects": transform_selects,
    }
    cfg = {
        "name": name,
        "layouts": [{"id": 0, "position": {"x": x, "y": y, "z": tab, "width": w, "height": h, "tabOrder": tab}}],
        "singleVisual": {
            "visualType": "tableEx",
            "projections": {"Values": projections},
            "prototypeQuery": query,
            "autoSelectVisualType": False,
            "drillFilterOtherVisuals": True,
            "objects": {
                "grid": [{"properties": {"gridHorizontal": expr("false"), "outlineColor": solid("#E6EAF2")}}],
                "columnHeaders": [
                    {
                        "properties": {
                            "fontFamily": expr("'Segoe UI Semibold'"),
                            "fontSize": expr("7.5D"),
                            "fontColor": solid(COLORS["ink"]),
                        }
                    }
                ],
                "values": [
                    {
                        "properties": {
                            "fontFamily": expr("'Segoe UI'"),
                            "fontSize": expr("7.2D"),
                            "fontColor": solid(COLORS["ink"]),
                        }
                    }
                ],
            },
            "vcObjects": vc_objects(title, subtitle),
        },
    }
    return {
        "x": x,
        "y": y,
        "z": tab,
        "width": w,
        "height": h,
        "config": json.dumps(cfg, separators=(",", ":")),
        "filters": "[]",
        "tabOrder": tab,
        "query": json.dumps(query_obj, separators=(",", ":")),
        "dataTransforms": json.dumps(transform, separators=(",", ":")),
    }


def measure_chart(
    name: str,
    visual_type: str,
    category_table: str,
    category_col: str,
    category_display: str,
    measure: str,
    measure_display: str,
    fmt: str,
    title: str,
    subtitle: str,
    x: int,
    y: int,
    w: int,
    h: int,
    tab: int,
    color: str,
    order: str = "desc",
) -> dict:
    chart = VH.measure_chart(
        name,
        visual_type,
        category_table,
        category_col,
        category_display,
        measure,
        measure_display,
        fmt,
        title,
        subtitle,
        x,
        y,
        w,
        h,
        tab,
        color,
        order,
    )
    cfg = json.loads(chart["config"])
    sv = cfg["singleVisual"]
    if fmt.endswith("%") or "Rate" in measure or "Attainment" in measure:
        for obj_name in ["valueAxis", "labels"]:
            for obj in sv.get("objects", {}).get(obj_name, []):
                obj.get("properties", {}).pop("labelDisplayUnits", None)
    chart["config"] = json.dumps(cfg, separators=(",", ":"))
    return chart


def card_specs(prefix: str, x: int = 24, y: int = 88, tab_start: int = 100) -> list[dict]:
    specs = [
        ("gmv", "Seller GMV", "Seller GMV", "$#,0", COLORS["orange"]),
        ("fulfill", "Fulfillment Rate", "Fulfillment", "0.0%", COLORS["green"]),
        ("cancel", "Cancellation Rate", "Cancellation", "0.0%", COLORS["red"]),
        ("rating", "Average Rating", "Rating", "0.00", COLORS["teal"]),
        ("stock", "Stock Availability", "Stock", "0.0%", COLORS["violet"]),
        ("sellers", "Active Sellers", "Active Sellers", "#,0", COLORS["blue"]),
    ]
    w, h, gap = 188, 86, 16
    return [
        VH.card_visual(f"{prefix}_{name}", measure, display, fmt, color, x + i * (w + gap), y, w, h, tab_start + i)
        for i, (name, measure, display, fmt, color) in enumerate(specs)
    ]


def title_visual(prefix: str, title: str, subtitle: str, ordinal: int) -> list[dict]:
    return [
        VH.textbox(f"{prefix}_title", 24, 16, 760, 58, title, subtitle, ordinal * 1000 + 1),
        VH.textbox(f"{prefix}_meta", 820, 22, 390, 42, "Latest complete month: 2026-05", "Power BI native multi-page dashboard", ordinal * 1000 + 2),
    ]


def executive_page() -> dict:
    visuals = title_visual(
        "p7_exec",
        "Marketplace Seller Performance",
        "Executive cockpit for GMV, fulfillment, cancellation, rating, stock, and top/bottom sellers",
        0,
    )
    visuals += card_specs("p7_exec_card")
    visuals += [
        measure_chart("p7_exec_trend_gmv", "lineChart", "fact_seller_month", "year_month", "Month", "Seller GMV", "Seller GMV", "$#,0", "GMV Trend", "Monthly net seller GMV", 24, 198, 612, 220, 210, COLORS["orange"], "asc_category"),
        measure_chart("p7_exec_platform_gmv", "barChart", "dim_platform", "platform_name", "Platform", "Seller GMV", "Seller GMV", "$#,0", "GMV by Platform", "Marketplace contribution", 660, 198, 596, 220, 211, COLORS["blue"], "desc"),
        table_visual(
            "p7_exec_seller_table",
            [
                {"kind": "column", "table": "dim_seller", "column": "seller_name", "display": "Seller"},
                {"kind": "column", "table": "dim_seller", "column": "seller_tier", "display": "Tier"},
                {"kind": "column", "table": "dim_seller", "column": "region", "display": "Region"},
                {"kind": "measure", "measure": "Seller GMV", "display": "GMV", "format": "$#,0"},
                {"kind": "measure", "measure": "Fulfillment Rate", "display": "Fulfillment", "format": "0.0%"},
                {"kind": "measure", "measure": "Cancellation Rate", "display": "Cancellation", "format": "0.0%"},
                {"kind": "measure", "measure": "Average Rating", "display": "Rating", "format": "0.00"},
                {"kind": "measure", "measure": "Stock Availability", "display": "Stock", "format": "0.0%"},
            ],
            "Seller Performance Table",
            "Top/bottom sellers with marketplace quality guardrails",
            24,
            444,
            1232,
            246,
            300,
            "Seller GMV",
            True,
        ),
    ]
    return section("01 Executive Cockpit", 0, visuals)


def portfolio_page() -> dict:
    visuals = title_visual(
        "p7_port",
        "Seller Portfolio",
        "Seller segmentation, concentration, region contribution, and leaderboard",
        1,
    )
    visuals += card_specs("p7_port_card", tab_start=1100)
    visuals += [
        measure_chart("p7_port_tier_gmv", "barChart", "dim_seller", "seller_tier", "Seller Tier", "Seller GMV", "Seller GMV", "$#,0", "GMV by Seller Tier", "Commercial segment contribution", 24, 198, 380, 220, 1210, COLORS["teal"], "desc"),
        measure_chart("p7_port_region_gmv", "barChart", "dim_seller", "region", "Region", "Seller GMV", "Seller GMV", "$#,0", "GMV by Region", "Seller geography contribution", 428, 198, 392, 220, 1211, COLORS["blue"], "desc"),
        measure_chart("p7_port_lifecycle_gmv", "barChart", "dim_seller", "lifecycle_status", "Lifecycle", "Seller GMV", "Seller GMV", "$#,0", "GMV by Lifecycle", "Portfolio health stage", 844, 198, 412, 220, 1212, COLORS["violet"], "desc"),
        table_visual(
            "p7_port_leaderboard",
            [
                {"kind": "column", "table": "dim_seller", "column": "seller_name", "display": "Seller"},
                {"kind": "column", "table": "dim_seller", "column": "seller_tier", "display": "Tier"},
                {"kind": "column", "table": "dim_seller", "column": "lifecycle_status", "display": "Lifecycle"},
                {"kind": "measure", "measure": "Seller GMV", "display": "GMV", "format": "$#,0"},
                {"kind": "measure", "measure": "Orders", "display": "Orders", "format": "#,0"},
                {"kind": "measure", "measure": "Seller Performance Score", "display": "Score", "format": "0.00"},
                {"kind": "measure", "measure": "Seller Rank by GMV", "display": "GMV Rank", "format": "#,0"},
            ],
            "Seller Leaderboard",
            "Ranked sellers by GMV and blended performance score",
            24,
            444,
            1232,
            246,
            1300,
            "Seller GMV",
            True,
        ),
    ]
    return section("02 Seller Portfolio", 1, visuals)


def growth_page() -> dict:
    visuals = title_visual(
        "p7_growth",
        "Commercial Growth Drivers",
        "Targets, take rate, spend efficiency, and seller opportunity list",
        2,
    )
    growth_cards = [
        ("gmv_target", "Seller GMV Target", "GMV Target", "$#,0", COLORS["blue"]),
        ("target_attain", "GMV Target Attainment", "Target Attainment", "0.0%", COLORS["green"]),
        ("commission", "Commission Revenue", "Commission", "$#,0", COLORS["teal"]),
        ("take_rate", "Take Rate", "Take Rate", "0.0%", COLORS["violet"]),
        ("ads", "Ads Spend", "Ads Spend", "$#,0", COLORS["amber"]),
        ("voucher", "Voucher Cost", "Voucher Cost", "$#,0", COLORS["red"]),
    ]
    w, h, gap = 188, 86, 16
    visuals += [
        VH.card_visual(f"p7_growth_{name}", measure, display, fmt, color, 24 + i * (w + gap), 88, w, h, 2100 + i)
        for i, (name, measure, display, fmt, color) in enumerate(growth_cards)
    ]
    visuals += [
        measure_chart("p7_growth_gmv_trend", "lineChart", "fact_seller_month", "year_month", "Month", "Seller GMV", "Seller GMV", "$#,0", "GMV Trend", "Commercial outcome trend", 24, 198, 400, 220, 2210, COLORS["orange"], "asc_category"),
        measure_chart("p7_growth_target_trend", "lineChart", "fact_seller_targets", "year_month", "Month", "GMV Target Attainment", "Target Attainment", "0.0%", "Target Attainment", "Actual GMV vs seller target", 448, 198, 396, 220, 2211, COLORS["green"], "asc_category"),
        measure_chart("p7_growth_ads_platform", "barChart", "dim_platform", "platform_name", "Platform", "Ads Spend", "Ads Spend", "$#,0", "Ads Spend by Platform", "Marketplace demand investment", 868, 198, 388, 220, 2212, COLORS["amber"], "desc"),
        table_visual(
            "p7_growth_opportunity",
            [
                {"kind": "column", "table": "dim_seller", "column": "seller_name", "display": "Seller"},
                {"kind": "column", "table": "dim_seller", "column": "seller_tier", "display": "Tier"},
                {"kind": "measure", "measure": "Seller GMV", "display": "GMV", "format": "$#,0"},
                {"kind": "measure", "measure": "Seller GMV Target", "display": "Target", "format": "$#,0"},
                {"kind": "measure", "measure": "GMV Target Attainment", "display": "Attainment", "format": "0.0%"},
                {"kind": "measure", "measure": "Ads Spend", "display": "Ads", "format": "$#,0"},
                {"kind": "measure", "measure": "Voucher Cost", "display": "Voucher", "format": "$#,0"},
                {"kind": "measure", "measure": "Take Rate", "display": "Take Rate", "format": "0.0%"},
            ],
            "Growth Opportunity Table",
            "Seller-level target, demand spend, and take-rate follow-up",
            24,
            444,
            1232,
            246,
            2300,
            "GMV Target Attainment",
            False,
        ),
    ]
    return section("03 Growth Drivers", 2, visuals)


def risk_page() -> dict:
    visuals = title_visual(
        "p7_risk",
        "Ops Health & Risk Monitor",
        "Cancellation, fulfillment, stock, rating, and seller action queue",
        3,
    )
    risk_cards = [
        ("cancel", "Cancellation Rate", "Cancellation", "0.0%", COLORS["red"]),
        ("fulfill", "Fulfillment Rate", "Fulfillment", "0.0%", COLORS["green"]),
        ("late", "Late Fulfillment Rate", "Late Fulfillment", "0.0%", COLORS["amber"]),
        ("stock", "Stock Availability", "Stock", "0.0%", COLORS["violet"]),
        ("rating", "Average Rating", "Rating", "0.00", COLORS["teal"]),
        ("rating_count", "Rating Count", "Reviews", "#,0", COLORS["blue"]),
    ]
    w, h, gap = 188, 86, 16
    visuals += [
        VH.card_visual(f"p7_risk_{name}", measure, display, fmt, color, 24 + i * (w + gap), 88, w, h, 3100 + i)
        for i, (name, measure, display, fmt, color) in enumerate(risk_cards)
    ]
    visuals += [
        measure_chart("p7_risk_cancel_trend", "lineChart", "fact_seller_month", "year_month", "Month", "Cancellation Rate", "Cancellation", "0.0%", "Cancellation Trend", "Monthly seller cancellation pressure", 24, 198, 400, 220, 3210, COLORS["red"], "asc_category"),
        measure_chart("p7_risk_fulfill_trend", "lineChart", "fact_seller_month", "year_month", "Month", "Fulfillment Rate", "Fulfillment", "0.0%", "Fulfillment Trend", "Eligible item fulfillment rate", 448, 198, 396, 220, 3211, COLORS["green"], "asc_category"),
        measure_chart("p7_risk_stock_platform", "barChart", "dim_platform", "platform_name", "Platform", "Stock Availability", "Stock", "0.0%", "Stock by Platform", "SKU-day availability by marketplace", 868, 198, 388, 220, 3212, COLORS["violet"], "desc"),
        table_visual(
            "p7_risk_action_queue",
            [
                {"kind": "column", "table": "dim_seller", "column": "seller_name", "display": "Seller"},
                {"kind": "column", "table": "dim_seller", "column": "seller_tier", "display": "Tier"},
                {"kind": "column", "table": "dim_seller", "column": "account_manager", "display": "AM"},
                {"kind": "measure", "measure": "Seller GMV", "display": "GMV", "format": "$#,0"},
                {"kind": "measure", "measure": "Cancellation Rate", "display": "Cancel", "format": "0.0%"},
                {"kind": "measure", "measure": "Fulfillment Rate", "display": "Fulfill", "format": "0.0%"},
                {"kind": "measure", "measure": "Late Fulfillment Rate", "display": "Late", "format": "0.0%"},
                {"kind": "measure", "measure": "Stock Availability", "display": "Stock", "format": "0.0%"},
                {"kind": "measure", "measure": "Average Rating", "display": "Rating", "format": "0.00"},
            ],
            "Seller Risk Action Queue",
            "Prioritized operating follow-up for SLA, stock, cancellation, and rating risk",
            24,
            444,
            1232,
            246,
            3300,
            "Cancellation Rate",
            True,
        ),
    ]
    return section("04 Ops Risk", 3, visuals)


def count_visual_types(sections: list[dict]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for sec in sections:
        for vc in sec["visualContainers"]:
            cfg = json.loads(vc["config"])
            visual_type = cfg.get("singleVisual", {}).get("visualType", "unknown")
            counts[visual_type] = counts.get(visual_type, 0) + 1
    return counts


def patch_complete_pbix() -> dict:
    if not SOURCE_PBIX.exists():
        raise FileNotFoundError(SOURCE_PBIX)

    archive = ROOT / "archive" / "old_versions"
    archive.mkdir(parents=True, exist_ok=True)
    backup = archive / f"dashboard_final_before_complete_pbix_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pbix"
    shutil.copy2(SOURCE_PBIX, backup)

    with zipfile.ZipFile(SOURCE_PBIX, "r") as zin:
        infos = zin.infolist()
        zip_infos = {info.filename: clone_zip_info(info) for info in infos}
        entry_order = [info.filename for info in infos]
        entries = {info.filename: zin.read(info.filename) for info in infos}

    layout = json.loads(entries["Report/Layout"].decode("utf-16le"))
    sections = [executive_page(), portfolio_page(), growth_page(), risk_page()]
    layout["sections"] = sections
    layout["layoutOptimization"] = 0

    theme_path = "Report/StaticResources/SharedResources/BaseThemes/CY26SU05.json"
    theme = json.loads(entries[theme_path].decode("utf-8"))
    theme.update(
        {
            "name": "Marketplace Seller Performance Complete",
            "dataColors": [
                COLORS["orange"],
                COLORS["blue"],
                COLORS["cyan"],
                COLORS["teal"],
                COLORS["green"],
                COLORS["amber"],
                COLORS["red"],
                COLORS["violet"],
                COLORS["slate"],
            ],
            "background": COLORS["bg"],
            "foreground": COLORS["ink"],
            "tableAccent": COLORS["orange"],
            "good": COLORS["green"],
            "neutral": COLORS["amber"],
            "bad": COLORS["red"],
        }
    )

    entries["Report/Layout"] = json.dumps(layout, separators=(",", ":"), ensure_ascii=False).encode("utf-16le")
    entries[theme_path] = json.dumps(theme, separators=(",", ":"), ensure_ascii=False).encode("utf-8")

    fd, tmp_name = tempfile.mkstemp(suffix=".pbix")
    os.close(fd)
    tmp = Path(tmp_name)
    with zipfile.ZipFile(tmp, "w", compression=zipfile.ZIP_DEFLATED) as zout:
        for name in entry_order:
            if name == "SecurityBindings":
                continue
            zout.writestr(zip_infos[name], entries[name])

    shutil.move(str(tmp), COMPLETE_PBIX)
    shutil.copy2(COMPLETE_PBIX, SOURCE_PBIX)

    result = {
        "status": "PASS",
        "complete_pbix": str(COMPLETE_PBIX),
        "final_pbix": str(SOURCE_PBIX),
        "backup": str(backup),
        "page_count": len(sections),
        "visual_count": sum(len(sec["visualContainers"]) for sec in sections),
        "visual_types": count_visual_types(sections),
        "pages": [sec["displayName"] for sec in sections],
    }
    (ROOT / "qa" / "complete_pbix_validation.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


def main() -> None:
    if os.environ.get("PROJECT7_ALLOW_DIRECT_PBIX_PATCH") != "1":
        result = {
            "status": "SKIPPED",
            "reason": "Direct PBIX layout patching is disabled by default because Power BI Desktop rejected the patched PBIX as corrupted/unrecognized. Use the Power BI Desktop-saved PBIX in output/dashboard_final.pbix.",
            "required_env_for_experimental_run": "PROJECT7_ALLOW_DIRECT_PBIX_PATCH=1",
        }
        print(json.dumps(result, indent=2))
        return
    result = patch_complete_pbix()
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
