import copy
import json
import random
import string
from pathlib import Path


ROOT = Path(r"C:\Users\Win\OneDrive\Codex\Portfolio\BI\Project 10 - AML Fraud Monitoring")
SAMPLE_DIR = ROOT / "qa" / "legacy_visual_samples"
BLANK_LAYOUT = ROOT / "qa" / "layout_dashboard_model_clean.json"
OUT = ROOT / "build" / "legacy_report_layout_aml.json"

THEME = {
    "bg": "#071018",
    "bg2": "#0B151F",
    "header": "#071018",
    "panel": "#111B24",
    "panel2": "#162230",
    "panel_soft": "#1B2A38",
    "border": "#263849",
    "grid": "#233241",
    "text": "#E7EDF3",
    "muted": "#A3B3C5",
    "dim": "#728397",
    "cyan": "#5EA8FF",
    "teal": "#2DD4BF",
    "green": "#64D2A6",
    "amber": "#F2B84B",
    "red": "#F05D5E",
    "violet": "#8B7CF6",
    "blue": "#5EA8FF",
    "navy": "#0A121A",
}

PALETTE = [
    THEME["cyan"],
    THEME["teal"],
    THEME["amber"],
    THEME["red"],
    THEME["violet"],
    THEME["blue"],
    THEME["green"],
]

CARD_ACCENTS = {
    "Total Transactions": THEME["cyan"],
    "Flagged Amount": THEME["amber"],
    "Alert Count": THEME["amber"],
    "Suspicious Cases": THEME["red"],
    "False Positive Rate": THEME["amber"],
    "Overdue Cases": THEME["red"],
    "Alert Rate": THEME["amber"],
    "Alert to Case Conversion": THEME["teal"],
    "Rule Precision": THEME["teal"],
    "High Risk Customers": THEME["red"],
    "Open Cases": THEME["amber"],
    "SLA Compliance Rate": THEME["teal"],
    "Average Case Age Days": THEME["amber"],
    "Governance Changes": THEME["violet"],
    "Avg Precision After Tuning": THEME["teal"],
}


def read_layout(path: Path) -> dict:
    for enc in ("utf-16-le", "utf-8-sig", "utf-8"):
        try:
            return json.loads(path.read_text(encoding=enc))
        except Exception:
            pass
    raise ValueError(f"Could not read JSON layout: {path}")


def sample(name: str) -> dict:
    return json.loads((SAMPLE_DIR / f"{name}.json").read_text(encoding="utf-8"))


SAMPLES = {
    "shape": None,
    "textbox": None,
    "cardVisual": sample("cardVisual"),
    "barChart": sample("barChart"),
    "columnChart": sample("columnChart"),
    "donutChart": sample("donutChart"),
    "lineClusteredColumnComboChart": sample("lineClusteredColumnComboChart"),
    "slicer": sample("slicer"),
    "tableEx": sample("tableEx"),
}


def rand_name() -> str:
    return "".join(random.choice("0123456789abcdef") for _ in range(20))


def lit(value: str) -> dict:
    return {"expr": {"Literal": {"Value": value}}}


def color(value: str) -> dict:
    return {"solid": {"color": {"expr": {"Literal": {"Value": f"'{value}'"}}}}}


def prop_text(value: str) -> dict:
    return lit("'" + value.replace("'", "''") + "'")


def title_accent(title):
    if not title:
        return THEME["cyan"]
    t = title.lower()
    if any(word in t for word in ("overdue", "high-risk", "risk", "suspicious", "aging")):
        return THEME["red"]
    if any(word in t for word in ("false", "funnel", "alert", "workload", "corridor", "watchlist")):
        return THEME["amber"]
    if any(word in t for word in ("precision", "sla", "conversion", "performance")):
        return THEME["teal"]
    if any(word in t for word in ("governance", "rule")):
        return THEME["violet"]
    return THEME["cyan"]


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


def shape(x, y, w, h, z, fill="#0F1B2A") -> dict:
    name = rand_name()
    cfg = {
        "name": name,
        "layouts": [{"id": 0, "position": pos(x, y, w, h, z)}],
        "singleVisual": {
            "visualType": "shape",
            "drillFilterOtherVisuals": True,
            "objects": {
                "shape": [{"properties": {"tileShape": lit("'rectangle'")}}],
                "fill": [{
                    "properties": {
                        "show": lit("true"),
                        "fillColor": color(fill),
                        "transparency": lit("0D"),
                    }
                }],
                "outline": [{"properties": {"show": lit("false")}}],
            },
        },
    }
    return outer(cfg, x, y, w, h, z)


def textbox(text, x, y, w, h, z, size=13, fg="#111827", bg=None, bold=True) -> dict:
    name = rand_name()
    style = {
        "fontFamily": "Segoe UI Semibold" if bold else "Segoe UI",
        "fontSize": f"{size}pt",
        "color": fg,
    }
    sv = {
        "visualType": "textbox",
        "drillFilterOtherVisuals": True,
        "objects": {
            "general": [{
                "properties": {
                    "paragraphs": [{"textRuns": [{"value": text, "textStyle": style}]}]
                }
            }]
        },
    }
    if bg:
        sv["vcObjects"] = {
            "background": [{
                "properties": {
                    "show": lit("true"),
                    "color": color(bg),
                    "transparency": lit("0D"),
                }
            }]
        }
    cfg = {"name": name, "layouts": [{"id": 0, "position": pos(x, y, w, h, z)}], "singleVisual": sv}
    return outer(cfg, x, y, w, h, z)


def visual_title(title=None, subtitle=None, size=10.5):
    result = {
        "background": [{
            "properties": {
                "show": lit("true"),
                "color": color(THEME["panel"]),
                "transparency": lit("0D"),
            }
        }],
        "border": [{
            "properties": {
                "show": lit("true"),
                "color": color(THEME["border"]),
                "radius": lit("6.0D"),
                "width": lit("1.0D"),
            }
        }],
        "dropShadow": [{
            "properties": {
                "show": lit("true"),
                "position": prop_text("Outer"),
                "color": color("#000000"),
                "transparency": lit("72.0D"),
                "angle": lit("45.0D"),
                "distance": lit("2.0D"),
            }
        }],
    }
    if title:
        result["title"] = [{
            "properties": {
                "show": lit("true"),
                "text": prop_text(title),
                "fontFamily": prop_text("Segoe UI Semibold"),
                "fontSize": lit(f"{size}D"),
                "fontColor": color(title_accent(title)),
                "alignment": prop_text("left"),
            }
        }]
    if subtitle:
        result["subTitle"] = [{
            "properties": {
                "show": lit("true"),
                "text": prop_text(subtitle),
                "fontFamily": prop_text("Segoe UI"),
                "fontSize": lit("7.5D"),
                "fontColor": color(THEME["muted"]),
            }
        }]
    return result


def chart_objects(kind, fields, title=None):
    measures = [f"{t}.{f}" for t, f, k, *_ in fields if k == "measure"]
    accent = title_accent(title)
    objects = {
        "valueAxis": [{
            "properties": {
                "showAxisTitle": lit("false"),
                "gridlineShow": lit("true"),
                "gridlineColor": color(THEME["grid"]),
                "labelColor": color(THEME["muted"]),
                "fontColor": color(THEME["muted"]),
                "fontSize": lit("8.0D"),
            }
        }],
        "categoryAxis": [{
            "properties": {
                "showAxisTitle": lit("false"),
                "gridlineShow": lit("false"),
                "concatenateLabels": lit("false"),
                "labelColor": color(THEME["muted"]),
                "fontColor": color(THEME["muted"]),
                "fontSize": lit("8.0D"),
            }
        }],
        "legend": [{
            "properties": {
                "showTitle": lit("false"),
                "position": prop_text("Top"),
                "fontColor": color(THEME["muted"]),
                "labelColor": color(THEME["muted"]),
                "fontSize": lit("8.0D"),
            }
        }],
        "labels": [{
            "properties": {
                "show": lit("false"),
                "fontColor": color(THEME["text"]),
                "labelColor": color(THEME["text"]),
            }
        }],
    }
    if kind == "donutChart":
        objects["labels"][0]["properties"].update({
            "show": lit("true"),
            "labelStyle": prop_text("Percent of total"),
            "fontColor": color(THEME["muted"]),
            "labelColor": color(THEME["muted"]),
        })
    objects["dataPoint"] = []
    for i, metadata in enumerate(measures or ["_default"]):
        entry = {
            "properties": {"fill": color(accent if i == 0 else PALETTE[i % len(PALETTE)])}
        }
        if metadata != "_default":
            entry["selector"] = {"metadata": metadata}
        objects["dataPoint"].append(entry)
    return objects


def table_objects():
    return {
        "grid": [{
            "properties": {
                "gridHorizontal": lit("false"),
                "gridVertical": lit("false"),
                "outlineColor": color(THEME["border"]),
                "rowPadding": lit("6D"),
            }
        }],
        "columnHeaders": [{
            "properties": {
                "fontFamily": prop_text("Segoe UI Semibold"),
                "fontSize": lit("8.0D"),
                "fontColor": color(THEME["cyan"]),
                "backColor": color(THEME["panel2"]),
            }
        }],
        "values": [{
            "properties": {
                "fontSize": lit("7.6D"),
                "fontFamily": prop_text("Segoe UI"),
                "fontColor": color(THEME["text"]),
                "backColorPrimary": color(THEME["panel"]),
                "backColorSecondary": color(THEME["panel2"]),
            }
        }],
    }


def slicer_objects(title):
    return {
        "data": [{"properties": {"mode": prop_text("Dropdown")}}],
        "general": [{"properties": {"orientation": lit("0D")}}],
        "selection": [{
            "properties": {
                "selectAllCheckboxEnabled": lit("true"),
                "singleSelect": lit("false"),
            }
        }],
        "header": [{
            "properties": {
                "show": lit("true"),
                "text": prop_text(title),
                "textSize": lit("8.0D"),
                "fontColor": color(THEME["muted"]),
                "fontFamily": prop_text("Segoe UI Semibold"),
            }
        }],
        "items": [{
            "properties": {
                "textSize": lit("8.0D"),
                "fontColor": color(THEME["text"]),
                "fontFamily": prop_text("Segoe UI"),
                "background": color(THEME["panel"]),
            }
        }],
    }


def ref(table, field, kind, alias, display=None) -> dict:
    qref = f"{table}.{field}"
    expr = {"SourceRef": {"Source": alias}}
    if kind == "measure":
        sel = {"Measure": {"Expression": expr, "Property": field}}
    else:
        sel = {"Column": {"Expression": expr, "Property": field}}
    sel["Name"] = qref
    sel["NativeReferenceName"] = display or field
    return sel


def proto(fields):
    froms = []
    aliases = {}
    for table, field, kind, display in fields:
        if table not in aliases:
            base = "".join(c.lower() for c in table if c.isalnum())[:1] or "t"
            alias = base
            n = 1
            used = set(aliases.values())
            while alias in used:
                n += 1
                alias = f"{base}{n}"
            aliases[table] = alias
            froms.append({"Name": alias, "Entity": table, "Type": 0})
    selects = [ref(table, field, kind, aliases[table], display) for table, field, kind, display in fields]
    return {"Version": 2, "From": froms, "Select": selects}


def projections(mapping):
    result = {}
    for bucket, fields in mapping.items():
        result[bucket] = [{"queryRef": f"{t}.{f}", **({"active": True} if i == 0 else {})} for i, (t, f, *_rest) in enumerate(fields)]
    return result


def data_visual(kind, x, y, w, h, z, proj_map, title=None):
    cfg = copy.deepcopy(SAMPLES[kind])
    cfg["name"] = rand_name()
    sv = cfg["singleVisual"]
    sv["visualType"] = kind
    fields = []
    for vals in proj_map.values():
        fields.extend(vals)
    sv["projections"] = projections(proj_map)
    sv["prototypeQuery"] = proto(fields)
    sv.pop("columnProperties", None)
    if kind == "tableEx":
        sv["objects"] = table_objects()
    elif kind == "slicer":
        sv["objects"] = slicer_objects(title or fields[0][1])
    else:
        sv["objects"] = chart_objects(kind, fields, title)
    sv["vcObjects"] = visual_title(title, None if kind == "slicer" else "Source-backed AML monitoring view")
    return outer(cfg, x, y, w, h, z)


def card(measure, title, x, y, w, h, z):
    visual = data_visual(
        "cardVisual", x, y, w, h, z,
        {"Data": [("KPI Measures", measure, "measure", title)]},
        title,
    )
    cfg = json.loads(visual["config"])
    metadata = f"KPI Measures.{measure}"
    accent = CARD_ACCENTS.get(measure, title_accent(title))
    cfg["singleVisual"]["objects"] = {
        "layout": [{
            "properties": {
                "backgroundShow": lit("false"),
                "rectangleRoundedCurve": lit("6L"),
                "cellPadding": lit("6D"),
                "paddingUniform": lit("6D"),
            },
            "selector": {"id": "default"},
        }],
        "value": [{
            "properties": {
                "fontSize": lit("22.0D"),
                "fontFamily": lit("'Segoe UI Semibold'"),
                "fontColor": color(accent),
            },
            "selector": {"metadata": metadata},
        }],
        "label": [{
            "properties": {"show": lit("false")},
            "selector": {"metadata": metadata},
        }],
        "spacing": [{
            "properties": {"verticalSpacing": lit("0D")},
            "selector": {"id": "default"},
        }],
        "padding": [{
            "properties": {
                "paddingUniform": lit("6D"),
                "paddingIndividual": lit("false"),
            },
            "selector": {"id": "default"},
        }],
        "fillCustom": [{
            "properties": {"show": lit("false")},
            "selector": {"id": "default"},
        }],
        "outline": [{
            "properties": {"show": lit("false")},
            "selector": {"id": "default"},
        }],
        "divider": [{
            "properties": {"show": lit("false")},
            "selector": {"metadata": metadata},
        }],
        "referenceLabelDetail": [{
            "properties": {"show": lit("false")},
            "selector": {"metadata": metadata},
        }],
    }
    cfg["singleVisual"]["vcObjects"] = visual_title(title, None, 8.8)
    cfg["singleVisual"]["vcObjects"]["background"][0]["properties"]["color"] = color("#F8FAFC")
    cfg["singleVisual"]["vcObjects"]["border"][0]["properties"]["color"] = color(accent)
    cfg["singleVisual"]["vcObjects"]["title"][0]["properties"]["fontColor"] = color("#475569")
    visual["config"] = json.dumps(cfg, separators=(",", ":"), ensure_ascii=False)
    return visual


def slicer(table, field, title, x, y, w, h, z):
    return data_visual("slicer", x, y, w, h, z, {"Values": [(table, field, "column", title)]}, title)


def section(name, display, ordinal, visuals):
    section_config = {
        "objects": {
            "background": [{
                "properties": {
                    "color": color(THEME["bg"]),
                    "transparency": lit("0.0D"),
                }
            }]
        }
    }
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


def page_header(title, subtitle):
    return [
        shape(22, 16, 5, 50, 11, THEME["teal"]),
        shape(34, 66, 1216, 2, 12, THEME["border"]),
        textbox("AML CONTROL ROOM", 38, 20, 170, 18, 100, 7.5, THEME["teal"], THEME["bg"], False),
        textbox(title, 38, 32, 485, 34, 110, 14, THEME["text"], THEME["bg"]),
        textbox(subtitle, 540, 35, 360, 28, 120, 8, THEME["muted"], THEME["bg"], False),
    ]


def build():
    random.seed(20260611)
    layout = read_layout(BLANK_LAYOUT)
    root_config = json.loads(layout.get("config") or "{}")
    root_config.setdefault("objects", {})
    root_config["objects"]["section"] = [{
        "properties": {
            "verticalAlignment": prop_text("Top"),
            "background": color(THEME["bg"]),
        }
    }]
    layout["config"] = json.dumps(root_config, separators=(",", ":"), ensure_ascii=False)
    p1 = page_header("AML / Fraud Monitoring Command Center", "Fraud & Compliance Overview | executive monitoring cockpit")
    p1 += [
        slicer("DimDate", "MonthYear", "Month", 930, 24, 100, 40, 300),
        slicer("DimCorridor", "Corridor", "Corridor", 1038, 24, 132, 40, 400),
        slicer("DimRule", "RuleSeverity", "Severity", 1178, 24, 86, 40, 500),
        card("Total Transactions", "Total Transactions", 24, 92, 196, 96, 1000),
        card("Flagged Amount", "Flagged Amount", 230, 92, 196, 96, 1100),
        card("Alert Count", "Alerts", 436, 92, 196, 96, 1200),
        card("Suspicious Cases", "Suspicious Cases", 642, 92, 196, 96, 1300),
        card("False Positive Rate", "False Positive Rate", 848, 92, 196, 96, 1400),
        card("Overdue Cases", "Overdue Cases", 1054, 92, 196, 96, 1500),
        data_visual("lineClusteredColumnComboChart", 24, 212, 720, 240, 2000, {
            "Category": [("DimDate", "MonthYear", "column", "Month")],
            "Y": [("KPI Measures", "Alert Count", "measure", "Alerts")],
            "Y2": [("KPI Measures", "Case Count", "measure", "Cases")],
        }, "Alert and Case Trend"),
        data_visual("donutChart", 756, 212, 250, 240, 2100, {
            "Category": [("DimRule", "Typology", "column", "Typology")],
            "Y": [("KPI Measures", "Alert Count", "measure", "Alerts")],
        }, "Typology Mix"),
        data_visual("barChart", 1018, 212, 238, 240, 2200, {
            "Category": [("DimCorridor", "Corridor", "column", "Corridor")],
            "Y": [("KPI Measures", "Alert Count", "measure", "Alerts")],
        }, "Country / Corridor Risk"),
        data_visual("tableEx", 24, 470, 1232, 170, 2300, {
            "Values": [
                ("DimCorridor", "Corridor", "column", "Corridor"),
                ("DimCorridor", "CorridorRiskTier", "column", "Tier"),
                ("KPI Measures", "Alert Count", "measure", "Alerts"),
                ("KPI Measures", "Alert Amount", "measure", "Alert Amount"),
                ("KPI Measures", "False Positive Rate", "measure", "FPR"),
            ]
        }, "Top Corridor Watchlist"),
    ]

    p2 = page_header("Alert & Customer Risk Deep Dive", "Alert funnel, rule performance, customer and corridor risk")
    p2 += [
        slicer("DimChannel", "Channel", "Channel", 930, 24, 100, 40, 300),
        slicer("DimCustomer", "CustomerRiskTier", "Customer Risk", 1038, 24, 132, 40, 400),
        slicer("DimRule", "RuleName", "Rule", 1178, 24, 86, 40, 500),
        card("Alert Rate", "Alert Rate", 24, 92, 230, 96, 1000),
        card("Alert to Case Conversion", "Alert > Case", 266, 92, 230, 96, 1100),
        card("Rule Precision", "Rule Precision", 508, 92, 230, 96, 1200),
        card("High Risk Customers", "High Risk Customers", 750, 92, 230, 96, 1300),
        data_visual("barChart", 24, 212, 360, 240, 2000, {
            "Category": [("FactAlerts", "AlertStatus", "column", "Alert Status")],
            "Y": [("KPI Measures", "Alert Count", "measure", "Alerts")],
        }, "Alert Funnel"),
        data_visual("columnChart", 396, 212, 420, 240, 2100, {
            "Category": [("DimRule", "RuleName", "column", "Rule")],
            "Y": [("KPI Measures", "Rule Precision", "measure", "Precision")],
        }, "Rule Performance"),
        data_visual("barChart", 828, 212, 428, 240, 2200, {
            "Category": [("DimCustomer", "Customer", "column", "Customer")],
            "Y": [("KPI Measures", "Alert Amount", "measure", "Alert Amount")],
        }, "High-Risk Customers"),
        data_visual("tableEx", 24, 470, 1232, 170, 2300, {
            "Values": [
                ("FactAlerts", "AlertKey", "column", "Alert ID"),
                ("DimCustomer", "Customer", "column", "Customer"),
                ("DimRule", "RuleName", "column", "Rule"),
                ("FactAlerts", "Severity", "column", "Severity"),
                ("FactAlerts", "AlertAmountUSD", "column", "Amount"),
                ("FactAlerts", "RiskScore", "column", "Risk Score"),
            ]
        }, "Alert Detail Queue"),
    ]

    p3 = page_header("Case SLA & Rule Governance", "Aging, analyst workload, overdue cases and rule tuning control")
    p3 += [
        slicer("FactCases", "CasePriority", "Priority", 930, 24, 100, 40, 300),
        slicer("DimAnalyst", "Queue", "Queue", 1038, 24, 132, 40, 400),
        slicer("FactCases", "CaseStatus", "Status", 1178, 24, 86, 40, 500),
        card("Open Cases", "Open Cases", 24, 92, 196, 96, 1000),
        card("Overdue Cases", "Overdue Cases", 230, 92, 196, 96, 1100),
        card("SLA Compliance Rate", "SLA Compliance", 436, 92, 196, 96, 1200),
        card("Average Case Age Days", "Avg Age Days", 642, 92, 196, 96, 1300),
        card("Governance Changes", "Governance Changes", 848, 92, 196, 96, 1400),
        card("Avg Precision After Tuning", "Precision After Tuning", 1054, 92, 196, 96, 1500),
        data_visual("columnChart", 24, 212, 390, 240, 2000, {
            "Category": [("FactCases", "CaseStatus", "column", "Case Status")],
            "Y": [("KPI Measures", "Case Count", "measure", "Cases")],
        }, "Aging Cases"),
        data_visual("barChart", 426, 212, 390, 240, 2100, {
            "Category": [("DimAnalyst", "Analyst", "column", "Analyst")],
            "Y": [("KPI Measures", "Case Count", "measure", "Cases")],
        }, "Analyst Workload"),
        data_visual("barChart", 828, 212, 428, 240, 2200, {
            "Category": [("DimRule", "RuleName", "column", "Rule")],
            "Y": [("KPI Measures", "Rule Precision", "measure", "Precision")],
        }, "Rule Precision"),
        data_visual("tableEx", 24, 470, 1232, 170, 2300, {
            "Values": [
                ("DimRule", "RuleName", "column", "Rule"),
                ("FactRuleGovernance", "ChangeType", "column", "Change Type"),
                ("FactRuleGovernance", "ChangeReason", "column", "Reason"),
                ("FactRuleGovernance", "ApprovalStatus", "column", "Approval"),
                ("FactRuleGovernance", "PrecisionBefore", "column", "Precision Before"),
                ("FactRuleGovernance", "PrecisionAfter", "column", "Precision After"),
            ]
        }, "Governance Log"),
    ]

    layout["sections"] = [
        section("FraudComplianceOverview", "Fraud & Compliance Overview", 0, p1),
        section("AlertCustomerRiskDeepDive", "Alert & Customer Risk Deep Dive", 1, p2),
        section("CaseSlaRuleGovernance", "Case SLA & Rule Governance", 2, p3),
    ]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(layout, ensure_ascii=False, indent=2), encoding="utf-8")
    summary = {
        "layout": str(OUT),
        "pages": [s["displayName"] for s in layout["sections"]],
        "visual_containers": sum(len(s["visualContainers"]) for s in layout["sections"]),
    }
    (ROOT / "build" / "legacy_report_layout_aml_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    build()
