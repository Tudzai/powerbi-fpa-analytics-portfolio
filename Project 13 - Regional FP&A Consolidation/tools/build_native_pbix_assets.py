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
LAYOUT_JSON = ROOT / "build" / "native_report_layout_project13.json"
SEED_TEMPLATE = BI_ROOT / "Template" / "01_Core_Financial_Statements" / "Packt_Ch07_Group_Reporting.pbix"


THEME = {
    "bg": "#F5F7FA",
    "panel": "#FFFFFF",
    "panel2": "#F8FAFC",
    "border": "#D5DEE8",
    "grid": "#E6ECF2",
    "text": "#0F172A",
    "muted": "#526173",
    "dim": "#718096",
    "teal": "#2B6F75",
    "blue": "#2F5F9E",
    "green": "#6F8552",
    "gold": "#A8894B",
    "rose": "#B85A72",
    "ink": "#1E1E1E",
}
PALETTE = [THEME["teal"], THEME["blue"], THEME["green"], THEME["gold"], THEME["rose"], THEME["ink"]]


TABLE_FILES = {
    "DimDate": "dim_date.csv",
    "DimEntity": "dim_entity.csv",
    "DimBusinessUnit": "dim_business_unit.csv",
    "DimAccount": "dim_account.csv",
    "DimScenario": "dim_scenario.csv",
    "FactFinancials": "fact_financials.csv",
    "FactFinancialSummary": "fact_financial_summary.csv",
    "FactVarianceDriverBridge": "fact_variance_driver_bridge.csv",
    "FactCloseExceptions": "fact_close_exceptions.csv",
    "FactFXRate": "fact_fx_rate.csv",
}

COLUMN_TYPES = {
    "date": "dateTime",
    "due_date": "dateTime",
    "year": "int64",
    "month_number": "int64",
    "month_index": "int64",
    "sort_order": "int64",
    "driver_sort": "int64",
    "is_latest_complete": "boolean",
    "is_synthetic": "boolean",
    "ownership": "double",
    "amount_local": "double",
    "amount_usd": "double",
    "fx_rate_to_usd": "double",
    "quantity_teu_or_orders": "double",
    "rate_to_usd": "double",
}

RELATIONSHIPS = [
    ("FactFinancials", "date_id", "DimDate", "date_id"),
    ("FactFinancialSummary", "date_id", "DimDate", "date_id"),
    ("FactVarianceDriverBridge", "date_id", "DimDate", "date_id"),
    ("FactCloseExceptions", "date_id", "DimDate", "date_id"),
    ("FactFXRate", "date_id", "DimDate", "date_id"),
    ("FactFinancials", "entity_id", "DimEntity", "entity_id"),
    ("FactFinancialSummary", "entity_id", "DimEntity", "entity_id"),
    ("FactVarianceDriverBridge", "entity_id", "DimEntity", "entity_id"),
    ("FactCloseExceptions", "entity_id", "DimEntity", "entity_id"),
    ("FactFinancials", "business_unit_id", "DimBusinessUnit", "business_unit_id"),
    ("FactFinancialSummary", "business_unit_id", "DimBusinessUnit", "business_unit_id"),
    ("FactVarianceDriverBridge", "business_unit_id", "DimBusinessUnit", "business_unit_id"),
    ("FactFinancials", "scenario_id", "DimScenario", "scenario_id"),
    ("FactFinancialSummary", "scenario_id", "DimScenario", "scenario_id"),
    ("FactFinancials", "account_id", "DimAccount", "account_id"),
]


def read_header(path: Path) -> list[str]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return next(csv.reader(handle))


def data_type(column: str) -> str:
    if column in COLUMN_TYPES:
        return COLUMN_TYPES[column]
    if column.endswith("_usd") or column.endswith("_margin"):
        return "double"
    if column.endswith("_count") or column.endswith("_index"):
        return "int64"
    return "string"


def m_type(dtype: str) -> str:
    return {
        "string": "type text",
        "int64": "Int64.Type",
        "double": "type number",
        "decimal": "type number",
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


def _measure(name: str, dax: str, fmt: str, definition: str, data_category: str | None = None) -> dict:
    payload = {
        "measure_name": name,
        "dax": dax.strip(),
        "format_string": fmt,
        "definition": definition,
    }
    if data_category:
        payload["dataCategory"] = data_category
    return payload


def _latest_measure(name: str, base_measure: str, fmt: str, definition: str) -> dict:
    dax = f"""
VAR d = [Selected Latest Complete Date]
RETURN
    CALCULATE ( [{base_measure}], REMOVEFILTERS ( DimDate ), DimDate[date] = d )
"""
    return _measure(name, dax, fmt, definition)


def _py_measure(name: str, base_measure: str, fmt: str, definition: str) -> dict:
    dax = f"""
VAR d = EDATE ( [Selected Latest Complete Date], -12 )
RETURN
    CALCULATE ( [{base_measure}], REMOVEFILTERS ( DimDate ), DimDate[date] = d )
"""
    return _measure(name, dax, fmt, definition)


def _svg_text_expr(var_name: str) -> str:
    return f'SUBSTITUTE ( SUBSTITUTE ( {var_name}, "%", "%25" ), "&", "and" )'


def _kpi_card_svg(
    name: str,
    label: str,
    base_measure: str,
    fmt: str,
    value_kind: str,
    accent: str,
    definition: str,
    budget_measure: str | None = None,
    lower_is_better: bool = False,
) -> dict:
    accent_enc = accent.replace("#", "%23")
    muted = THEME["muted"].replace("#", "%23")
    text = THEME["text"].replace("#", "%23")
    panel = THEME["panel"].replace("#", "%23")
    border = THEME["border"].replace("#", "%23")
    grid = THEME["grid"].replace("#", "%23")
    good = THEME["green"].replace("#", "%23")
    warn = THEME["gold"].replace("#", "%23")
    bad = THEME["rose"].replace("#", "%23")
    budget_expr = f"CALCULATE ( [{budget_measure}], REMOVEFILTERS ( DimDate ), DimDate[date] = d )" if budget_measure else "BLANK ()"
    if value_kind == "money":
        value_text = 'FORMAT ( DIVIDE ( CurrentValue, 1000000 ), "$0.0M;($0.0M);$0.0M" )'
        py_text = 'FORMAT ( DIVIDE ( PriorValue, 1000000 ), "$0.0M;($0.0M);$0.0M" )'
        delta_text = 'FORMAT ( ChangePct, "+0.0%;-0.0%;0.0%" )'
    elif value_kind == "percent":
        value_text = 'FORMAT ( CurrentValue, "0.0%" )'
        py_text = 'FORMAT ( PriorValue, "0.0%" )'
        delta_text = 'FORMAT ( DeltaPoints, "+0.0pt;-0.0pt;0.0pt" )'
    elif value_kind == "count":
        value_text = 'FORMAT ( CurrentValue, "#,0" )'
        py_text = 'FORMAT ( PriorValue, "#,0" )'
        delta_text = 'FORMAT ( CurrentValue - PriorValue, "+#,0;-#,0;0" )'
    else:
        value_text = 'FORMAT ( CurrentValue, "#,0.0" )'
        py_text = 'FORMAT ( PriorValue, "#,0.0" )'
        delta_text = 'FORMAT ( ChangePct, "+0.0%;-0.0%;0.0%" )'
    status_good = "StatusBasis <= -0.02" if lower_is_better else "StatusBasis >= 0.02"
    status_warn = "StatusBasis <= 0.02" if lower_is_better else "StatusBasis >= -0.02"
    dax = f"""
VAR d = [Selected Latest Complete Date]
VAR LatestIdx =
    CALCULATE ( MAX ( DimDate[month_index] ), REMOVEFILTERS ( DimDate ), DimDate[date] = d )
VAR CurrentValue =
    CALCULATE ( [{base_measure}], REMOVEFILTERS ( DimDate ), DimDate[date] = d )
VAR PriorDate = EDATE ( d, -12 )
VAR PriorValue =
    CALCULATE ( [{base_measure}], REMOVEFILTERS ( DimDate ), DimDate[date] = PriorDate )
VAR BudgetValue = {budget_expr}
VAR ChangePct = DIVIDE ( CurrentValue - PriorValue, ABS ( PriorValue ) )
VAR DeltaPoints = ( CurrentValue - PriorValue ) * 100
VAR StatusBasis =
    IF (
        NOT ISBLANK ( BudgetValue ),
        DIVIDE ( CurrentValue - BudgetValue, ABS ( BudgetValue ) ),
        ChangePct
    )
VAR StatusColor =
    IF ( {status_good}, "{good}", IF ( {status_warn}, "{warn}", "{bad}" ) )
VAR StatusText =
    IF ( {status_good}, "ON TRACK", IF ( {status_warn}, "WATCH", "ACTION" ) )
VAR TrendColor =
    IF ( {"CurrentValue <= PriorValue" if lower_is_better else "CurrentValue >= PriorValue"}, "{good}", "{bad}" )
VAR MonthTable =
    ADDCOLUMNS (
        FILTER (
            ALL ( DimDate ),
            DimDate[date] <= d
                && DimDate[month_index] >= LatestIdx - 11
        ),
        "__Value", CALCULATE ( [{base_measure}] )
    )
VAR CleanTable = FILTER ( MonthTable, NOT ISBLANK ( [__Value] ) )
VAR RowCount = COUNTROWS ( CleanTable )
VAR MinValue = MINX ( CleanTable, [__Value] )
VAR MaxValue = MAXX ( CleanTable, [__Value] )
VAR FirstValue = MINX ( TOPN ( 1, CleanTable, DimDate[date], ASC ), [__Value] )
VAR LastValue = MAXX ( TOPN ( 1, CleanTable, DimDate[date], DESC ), [__Value] )
VAR FirstY =
    IF (
        MaxValue = MinValue,
        52,
        74 - DIVIDE ( FirstValue - MinValue, MaxValue - MinValue, 0.5 ) * 38
    )
VAR LastY =
    IF (
        MaxValue = MinValue,
        52,
        74 - DIVIDE ( LastValue - MinValue, MaxValue - MinValue, 0.5 ) * 38
    )
VAR LinePoints =
    CONCATENATEX (
        CleanTable,
        VAR RankValue = RANKX ( CleanTable, DimDate[date], , ASC, DENSE ) - 1
        VAR XValue = 164 + DIVIDE ( RankValue, MAX ( 1, RowCount - 1 ), 0 ) * 100
        VAR YRatio =
            IF (
                MaxValue = MinValue,
                0.5,
                DIVIDE ( [__Value] - MinValue, MaxValue - MinValue, 0.5 )
            )
        VAR YValue = 74 - YRatio * 38
        RETURN FORMAT ( XValue, "0.0", "en-US" ) & "," & FORMAT ( YValue, "0.0", "en-US" ),
        " ",
        DimDate[date],
        ASC
    )
VAR ValueText = {_svg_text_expr(value_text)}
VAR PyText = {_svg_text_expr(py_text)}
VAR DeltaText = {_svg_text_expr(delta_text)}
VAR Sparkline =
    IF (
        RowCount >= 2,
        "<polyline points='" & LinePoints & "' fill='none' stroke='" & TrendColor & "' stroke-width='3' stroke-linecap='round' stroke-linejoin='round'/>"
            & "<circle cx='164' cy='" & FORMAT ( FirstY, "0.0", "en-US" ) & "' r='3.2' fill='{panel}' stroke='{muted}' stroke-width='1.2'/>"
            & "<circle cx='264' cy='" & FORMAT ( LastY, "0.0", "en-US" ) & "' r='4.2' fill='" & TrendColor & "'/>",
        "<line x1='164' y1='56' x2='264' y2='56' stroke='{grid}' stroke-width='3' stroke-linecap='round'/>"
    )
VAR SVG =
    "<svg xmlns='http://www.w3.org/2000/svg' width='292' height='104' viewBox='0 0 292 104'>"
    & "<rect x='1' y='1' width='290' height='102' rx='7' fill='{panel}' stroke='{border}'/>"
    & "<rect x='1' y='1' width='290' height='4' rx='2' fill='{accent_enc}'/>"
    & "<text x='16' y='24' font-family='Segoe UI Semibold' font-size='10.5' fill='{muted}'>{label}</text>"
    & "<text x='16' y='54' font-family='Segoe UI Semibold' font-size='25' fill='{text}'>" & ValueText & "</text>"
    & "<rect x='160' y='34' width='108' height='44' rx='8' fill='%23F8FAFC'/>"
    & "<line x1='166' y1='56' x2='264' y2='56' stroke='{grid}' stroke-width='1' stroke-dasharray='3 5'/>"
    & Sparkline
    & "<rect x='16' y='72' width='76' height='18' rx='9' fill='%23F8FAFC' stroke='{border}'/>"
    & "<text x='26' y='85' font-family='Segoe UI' font-size='8.2' fill='{muted}'>PY " & PyText & "</text>"
    & "<rect x='98' y='72' width='56' height='18' rx='9' fill='" & StatusColor & "' fill-opacity='0.14'/>"
    & "<text x='108' y='85' font-family='Segoe UI Semibold' font-size='8.2' fill='" & StatusColor & "'>" & DeltaText & "</text>"
    & "<text x='190' y='91' font-family='Segoe UI Semibold' font-size='8' fill='" & StatusColor & "'>" & StatusText & "</text>"
    & "</svg>"
RETURN
    "data:image/svg+xml;utf8," & SVG
"""
    return _measure(name, dax, fmt, definition, "ImageUrl")


def _lens_svg_measure() -> dict:
    teal = THEME["teal"].replace("#", "%23")
    blue = THEME["blue"].replace("#", "%23")
    gold = THEME["gold"].replace("#", "%23")
    text = THEME["text"].replace("#", "%23")
    muted = THEME["muted"].replace("#", "%23")
    panel = THEME["panel"].replace("#", "%23")
    border = THEME["border"].replace("#", "%23")
    dax = f"""
VAR PeriodText = [Selected Latest Complete Period Label]
VAR RegionText =
    IF ( ISFILTERED ( DimEntity[region] ), LEFT ( CONCATENATEX ( VALUES ( DimEntity[region] ), DimEntity[region], ", " ), 20 ), "All regions" )
VAR BUText =
    IF ( ISFILTERED ( DimBusinessUnit[business_unit] ), LEFT ( CONCATENATEX ( VALUES ( DimBusinessUnit[business_unit] ), DimBusinessUnit[business_unit], ", " ), 24 ), "All BUs" )
VAR ScenarioText =
    IF ( ISFILTERED ( DimScenario[scenario] ), LEFT ( CONCATENATEX ( VALUES ( DimScenario[scenario] ), DimScenario[scenario], ", " ), 18 ), "Actual lens" )
VAR RevVar = [Latest Revenue Var %]
VAR EbitdaVar = [Latest EBITDA Var %]
VAR RiskValue = [Latest Open Exception Value]
VAR RevText = SUBSTITUTE ( FORMAT ( RevVar, "+0.0%;-0.0%;0.0%" ), "%", "%25" )
VAR StatusColor = IF ( EbitdaVar >= 0.02, "{teal}", IF ( EbitdaVar >= -0.02, "{gold}", "%23B85A72" ) )
VAR SVG =
    "<svg xmlns='http://www.w3.org/2000/svg' width='536' height='42' viewBox='0 0 536 42'>"
    & "<rect x='0.5' y='0.5' width='535' height='41' rx='7' fill='{panel}' stroke='{border}'/>"
    & "<circle cx='18' cy='21' r='5' fill='" & StatusColor & "'/>"
    & "<text x='32' y='17' font-family='Segoe UI Semibold' font-size='9.5' fill='{text}'>Current Lens</text>"
    & "<text x='32' y='31' font-family='Segoe UI' font-size='8.3' fill='{muted}'>" & PeriodText & " | " & ScenarioText & "</text>"
    & "<rect x='174' y='9' width='102' height='24' rx='12' fill='%23F8FAFC' stroke='{border}'/>"
    & "<text x='186' y='25' font-family='Segoe UI Semibold' font-size='8.4' fill='{blue}'>" & RegionText & "</text>"
    & "<rect x='286' y='9' width='118' height='24' rx='12' fill='%23F8FAFC' stroke='{border}'/>"
    & "<text x='298' y='25' font-family='Segoe UI Semibold' font-size='8.4' fill='{teal}'>" & BUText & "</text>"
    & "<rect x='414' y='9' width='108' height='24' rx='12' fill='%23F8FAFC' stroke='{border}'/>"
    & "<text x='426' y='25' font-family='Segoe UI Semibold' font-size='8.2' fill='{gold}'>Rev " & RevText & " | Risk $" & FORMAT ( DIVIDE ( RiskValue, 1000000 ), "0.0M" ) & "</text>"
    & "</svg>"
RETURN
    "data:image/svg+xml;utf8," & SUBSTITUTE ( SVG, "%", "%25" )
"""
    # Re-open encoded colors after the generic percent encoding above.
    dax = dax.replace('RETURN\n    "data:image/svg+xml;utf8," & SUBSTITUTE ( SVG, "%", "%25" )', 'RETURN\n    "data:image/svg+xml;utf8," & SVG')
    return _measure("Lens Summary SVG", dax, "", "Top-bar Current Lens SVG for selected period, region, BU, revenue variance, and close-risk exposure.", "ImageUrl")


def _decision_chips_svg(name: str, title: str, chips: list[tuple[str, str, str]], definition: str) -> dict:
    text = THEME["text"].replace("#", "%23")
    muted = THEME["muted"].replace("#", "%23")
    panel = THEME["panel"].replace("#", "%23")
    border = THEME["border"].replace("#", "%23")
    colors = [THEME["blue"].replace("#", "%23"), THEME["teal"].replace("#", "%23"), THEME["gold"].replace("#", "%23")]
    chip_svg = ""
    for idx, (label, value_expr, color_var) in enumerate(chips):
        x = 14 + idx * 178
        chip_svg += (
            f'    & "<rect x=\'{x}\' y=\'28\' width=\'164\' height=\'28\' rx=\'14\' fill=\'%23F8FAFC\' stroke=\'{border}\'/>"\n'
            f'    & "<circle cx=\'{x + 16}\' cy=\'42\' r=\'4\' fill=\'" & {color_var} & "\'/>"\n'
            f'    & "<text x=\'{x + 28}\' y=\'39\' font-family=\'Segoe UI\' font-size=\'7.6\' fill=\'{muted}\'>{label}</text>"\n'
            f'    & "<text x=\'{x + 28}\' y=\'51\' font-family=\'Segoe UI Semibold\' font-size=\'8.4\' fill=\'{text}\'>" & SUBSTITUTE ( {value_expr}, "%", "%25" ) & "</text>"\n'
        )
    dax = f"""
VAR Blue = "{colors[0]}"
VAR Teal = "{colors[1]}"
VAR Gold = "{colors[2]}"
VAR Rose = "%23B85A72"
VAR RevColor = IF ( [Latest Revenue Var %] >= 0, Teal, Rose )
VAR EbitdaColor = IF ( [Latest EBITDA Var %] >= 0, Teal, Rose )
VAR RiskColor = IF ( [Latest Open Exception Count] = 0, Teal, IF ( [Latest Open Exception Value] < 5000000, Gold, Rose ) )
VAR ICColor = IF ( ABS ( DIVIDE ( [Latest Intercompany Elimination], [Latest Gross Revenue] ) ) < 0.08, Teal, Gold )
VAR SVG =
    "<svg xmlns='http://www.w3.org/2000/svg' width='536' height='68' viewBox='0 0 536 68'>"
    & "<rect x='0.5' y='0.5' width='535' height='67' rx='7' fill='{panel}' stroke='{border}'/>"
    & "<text x='14' y='17' font-family='Segoe UI Semibold' font-size='10' fill='{text}'>{title}</text>"
{chip_svg}    & "</svg>"
RETURN
    "data:image/svg+xml;utf8," & SVG
"""
    return _measure(name, dax, "", definition, "ImageUrl")


def project20_svg_measure_catalog() -> list[dict]:
    helpers = [
        _measure(
            "Selected Latest Complete Date",
            """
VAR GlobalLatestComplete =
    CALCULATE (
        MAX ( DimDate[date] ),
        REMOVEFILTERS ( DimDate ),
        DimDate[is_latest_complete] = TRUE ()
    )
VAR SelectedLatest =
    MAXX (
        FILTER ( ALLSELECTED ( DimDate ), DimDate[date] <= GlobalLatestComplete ),
        DimDate[date]
    )
RETURN
    COALESCE ( SelectedLatest, GlobalLatestComplete )
""",
            "mmm yyyy",
            "Latest complete date within the selected date context, capped to the global closed period.",
        ),
        _measure(
            "Selected Latest Complete Period Label",
            'FORMAT ( [Selected Latest Complete Date], "MMM yyyy" )',
            "",
            "Display label for the selected latest complete month.",
        ),
        _latest_measure("Latest Actual Revenue", "Actual Revenue", "$#,0,,.0M", "Actual revenue at selected latest complete period."),
        _latest_measure("Latest Budget Revenue", "Budget Revenue", "$#,0,,.0M", "Budget revenue at selected latest complete period."),
        _latest_measure("Latest Revenue Var vs Budget", "Revenue Var vs Budget", "$#,0,,.0M", "Revenue variance at selected latest complete period."),
        _latest_measure("Latest Revenue Var %", "Revenue Var %", "0.0%", "Revenue variance percent at selected latest complete period."),
        _latest_measure("Latest Actual EBITDA", "Actual EBITDA", "$#,0,,.0M", "Actual EBITDA at selected latest complete period."),
        _latest_measure("Latest Budget EBITDA", "Budget EBITDA", "$#,0,,.0M", "Budget EBITDA at selected latest complete period."),
        _latest_measure("Latest EBITDA Var vs Budget", "EBITDA Var vs Budget", "$#,0,,.0M", "EBITDA variance at selected latest complete period."),
        _latest_measure("Latest EBITDA Var %", "EBITDA Var %", "0.0%", "EBITDA variance percent at selected latest complete period."),
        _latest_measure("Latest Gross Revenue", "Gross Revenue", "$#,0,,.0M", "Gross revenue at selected latest complete period."),
        _latest_measure("Latest Gross Profit", "Gross Profit", "$#,0,,.0M", "Gross profit at selected latest complete period."),
        _latest_measure("Latest Gross Margin %", "Gross Margin %", "0.0%", "Gross margin at selected latest complete period."),
        _latest_measure("Latest OPEX", "OPEX", "$#,0,,.0M", "OPEX at selected latest complete period."),
        _latest_measure("Latest Net Income", "Net Income", "$#,0,,.0M", "Net income at selected latest complete period."),
        _latest_measure("Latest EBITDA Margin %", "EBITDA Margin %", "0.0%", "EBITDA margin at selected latest complete period."),
        _latest_measure("Latest Cash Position", "Cash Position", "$#,0,,.0M", "Cash position at selected latest complete period."),
        _latest_measure("Latest Operating Cash Flow", "Operating Cash Flow", "$#,0,,.0M", "Operating cash flow at selected latest complete period."),
        _latest_measure("Latest Forecast Accuracy %", "Forecast Accuracy %", "0.0%", "Forecast accuracy at selected latest complete period."),
        _latest_measure("Latest Intercompany Revenue", "Intercompany Revenue", "$#,0,,.0M", "Intercompany revenue at selected latest complete period."),
        _latest_measure("Latest Intercompany Elimination", "Intercompany Elimination", "$#,0,,.0M", "Intercompany elimination impact at selected latest complete period."),
        _latest_measure("Latest Open Exception Count", "Open Exception Count", "#,0", "Open close-exception count at selected latest complete period."),
        _latest_measure("Latest Open Exception Value", "Open Exception Value", "$#,0,,.0M", "Open close-exception exposure at selected latest complete period."),
        _py_measure("Revenue PY", "Actual Revenue", "$#,0,,.0M", "Actual revenue for the same month in the prior year."),
        _py_measure("EBITDA PY", "Actual EBITDA", "$#,0,,.0M", "Actual EBITDA for the same month in the prior year."),
        _py_measure("Gross Margin PY %", "Gross Margin %", "0.0%", "Gross margin for the same month in the prior year."),
        _py_measure("Cash Position PY", "Cash Position", "$#,0,,.0M", "Cash position for the same month in the prior year."),
        _py_measure("Open Exception Value PY", "Open Exception Value", "$#,0,,.0M", "Open exception value for the same month in the prior year."),
    ]
    cards = [
        _kpi_card_svg("Revenue KPI Card SVG", "Revenue", "Actual Revenue", "", "money", THEME["blue"], "SVG KPI card for revenue with latest value, PY delta, status chip, and sparkline.", "Budget Revenue"),
        _kpi_card_svg("EBITDA KPI Card SVG", "EBITDA", "Actual EBITDA", "", "money", THEME["teal"], "SVG KPI card for EBITDA with latest value, PY delta, status chip, and sparkline.", "Budget EBITDA"),
        _kpi_card_svg("Margin KPI Card SVG", "EBITDA Margin", "EBITDA Margin %", "", "percent", THEME["green"], "SVG KPI card for EBITDA margin with prior-year point delta and sparkline."),
        _kpi_card_svg("Cash KPI Card SVG", "Cash Position", "Cash Position", "", "money", THEME["gold"], "SVG KPI card for cash position with prior-year delta and sparkline."),
        _kpi_card_svg("Gross Revenue KPI Card SVG", "Gross Revenue", "Gross Revenue", "", "money", THEME["blue"], "SVG KPI card for gross revenue with prior-year delta and sparkline."),
        _kpi_card_svg("Gross Profit KPI Card SVG", "Gross Profit", "Gross Profit", "", "money", THEME["teal"], "SVG KPI card for gross profit with prior-year delta and sparkline."),
        _kpi_card_svg("OPEX KPI Card SVG", "OPEX", "OPEX", "", "money", THEME["rose"], "SVG KPI card for OPEX with lower-is-better status and sparkline.", lower_is_better=True),
        _kpi_card_svg("Net Income KPI Card SVG", "Net Income", "Net Income", "", "money", THEME["green"], "SVG KPI card for net income with prior-year delta and sparkline."),
        _kpi_card_svg("IC Revenue KPI Card SVG", "IC Revenue", "Intercompany Revenue", "", "money", THEME["blue"], "SVG KPI card for intercompany revenue with prior-year delta and sparkline.", lower_is_better=True),
        _kpi_card_svg("Intercompany Elimination KPI Card SVG", "IC Elimination", "Intercompany Elimination", "", "money", THEME["teal"], "SVG KPI card for intercompany elimination impact with lower-is-better status and sparkline.", lower_is_better=True),
        _kpi_card_svg("Close Exceptions KPI Card SVG", "Close Risk", "Open Exception Value", "", "money", THEME["rose"], "SVG KPI card for open exception exposure with lower-is-better status and sparkline.", lower_is_better=True),
        _kpi_card_svg("Forecast Accuracy KPI Card SVG", "Forecast Accuracy", "Forecast Accuracy %", "", "percent", THEME["gold"], "SVG KPI card for forecast accuracy with prior-year point delta and sparkline."),
    ]
    chips = [
        _lens_svg_measure(),
        _decision_chips_svg(
            "Regional FP&A Decision Chips SVG",
            "Decision Signals",
            [
                ("Revenue vs budget", 'FORMAT ( [Latest Revenue Var %], "+0.0%;-0.0%;0.0%" )', "RevColor"),
                ("EBITDA vs budget", 'FORMAT ( [Latest EBITDA Var %], "+0.0%;-0.0%;0.0%" )', "EbitdaColor"),
                ("Open close risk", 'FORMAT ( [Latest Open Exception Count], "#,0" ) & " items | $" & FORMAT ( DIVIDE ( [Latest Open Exception Value], 1000000 ), "0.0M" )', "RiskColor"),
            ],
            "Executive decision-chip SVG for regional FP&A revenue, EBITDA, and close-risk status.",
        ),
        _decision_chips_svg(
            "Controls Decision Chips SVG",
            "Control Signals",
            [
                ("Intercompany", '"$" & FORMAT ( DIVIDE ( ABS ( [Latest Intercompany Elimination] ), 1000000 ), "0.0M" )', "ICColor"),
                ("Close risk", 'FORMAT ( [Latest Open Exception Count], "#,0" ) & " open"', "RiskColor"),
                ("Forecast quality", 'FORMAT ( [Latest Forecast Accuracy %], "0.0%" )', "EbitdaColor"),
            ],
            "Control decision-chip SVG for intercompany, close risk, and forecast quality.",
        ),
    ]
    return helpers + cards + chips


def measure_catalog() -> list[dict]:
    base = json.loads((ROOT / "model" / "measure_catalog.json").read_text(encoding="utf-8"))
    names = {item["measure_name"] for item in base}
    extras = [item for item in project20_svg_measure_catalog() if item["measure_name"] not in names]
    return base + extras


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

    measure_table = {
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
                        '    Source = #table(type table [Measure Group = text], {{"Regional FP&A Consolidation"}})',
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
                **({"dataCategory": item["dataCategory"]} if item.get("dataCategory") else {}),
            }
            for item in measure_catalog()
        ],
    }
    tables.append(measure_table)

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
    "lineClusteredColumnComboChart": load_sample("lineClusteredColumnComboChart"),
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
    if any(token in text for token in ("exception", "risk", "gap", "variance")):
        return THEME["rose"]
    if any(token in text for token in ("cash", "forecast", "target")):
        return THEME["gold"]
    if any(token in text for token in ("revenue", "country")):
        return THEME["blue"]
    return THEME["teal"]


def visual_shell(title: str | None = None, subtitle: str | None = None) -> dict:
    result = {
        "background": [{"properties": {"show": lit("true"), "color": color(THEME["panel"]), "transparency": lit("0D")}}],
        "border": [{"properties": {"show": lit("true"), "color": color(THEME["border"]), "radius": lit("6.0D"), "width": lit("0.75D")}}],
        "dropShadow": [{"properties": {"show": lit("true"), "color": color("#000000"), "transparency": lit("82.0D"), "angle": lit("45.0D"), "distance": lit("1.5D")}}],
    }
    if title:
        result["title"] = [{"properties": {"show": lit("true"), "text": prop_text(title), "fontFamily": prop_text("Segoe UI Semibold"), "fontSize": lit("9.0D"), "fontColor": color(title_accent(title)), "alignment": prop_text("left")}}]
    if subtitle:
        result["subTitle"] = [{"properties": {"show": lit("true"), "text": prop_text(subtitle), "fontFamily": prop_text("Segoe UI"), "fontSize": lit("7.2D"), "fontColor": color(THEME["muted"])}}]
    return result


def visual_shell_hidden() -> dict:
    return {
        "background": [{"properties": {"show": lit("false"), "transparency": lit("100D")}}],
        "border": [{"properties": {"show": lit("false")}}],
        "dropShadow": [{"properties": {"show": lit("false")}}],
        "title": [{"properties": {"show": lit("false")}}],
    }


def measure_format(field: str) -> str:
    for item in measure_catalog():
        if item["measure_name"] == field:
            return item.get("format_string", "")
    return ""


def chart_display_units(fields: list[tuple[str, str, str, str]]) -> str:
    numeric_fields = [(table, field, role) for table, field, role, _ in fields if role == "measure" or field.endswith("_usd") or "amount" in field]
    if not numeric_fields:
        return "0D"
    money_like = []
    for table, field, role in numeric_fields:
        fmt = measure_format(field) if table == "KPI Measures" and role == "measure" else ""
        money_like.append("$" in fmt or field.endswith("_usd") or "amount" in field)
    return "1000000D" if money_like and all(money_like) else "0D"


def chart_objects(kind: str, fields: list[tuple[str, str, str, str]], title: str | None) -> dict:
    measures = [f"{table}.{field}" for table, field, role, _ in fields if role == "measure"]
    units = chart_display_units(fields)
    show_labels = kind in {"barChart", "columnChart", "donutChart", "waterfallChart"}
    objects = {
        "valueAxis": [{"properties": {"showAxisTitle": lit("false"), "gridlineShow": lit("false"), "labelDisplayUnits": lit(units), "gridlineColor": color(THEME["grid"]), "labelColor": color(THEME["muted"]), "color": color(THEME["muted"]), "fontSize": lit("7.2D")}}],
        "categoryAxis": [{"properties": {"showAxisTitle": lit("false"), "gridlineShow": lit("false"), "concatenateLabels": lit("false"), "labelColor": color(THEME["muted"]), "color": color(THEME["muted"]), "fontSize": lit("7.2D")}}],
        "legend": [{"properties": {"showTitle": lit("false"), "position": prop_text("Top"), "fontColor": color(THEME["muted"]), "labelColor": color(THEME["muted"]), "fontSize": lit("7.2D")}}],
        "labels": [{"properties": {"show": lit("true" if show_labels else "false"), "fontSize": lit("7.0D"), "labelDisplayUnits": lit(units), "fontColor": color(THEME["text"]), "labelColor": color(THEME["text"])}}],
        "dataPoint": [],
    }
    if kind == "donutChart":
        objects["labels"][0]["properties"].update({"show": lit("true"), "labelStyle": prop_text("Percent of total"), "fontColor": color(THEME["muted"])})
    if kind == "waterfallChart":
        objects["sentimentColors"] = [{
            "properties": {
                "increaseFill": color(THEME["teal"]),
                "decreaseFill": color(THEME["rose"]),
                "totalFill": color(THEME["ink"]),
            }
        }]
    for idx, metadata in enumerate(measures or ["_default"]):
        item = {"properties": {"fill": color(PALETTE[idx % len(PALETTE)])}}
        if metadata != "_default":
            item["selector"] = {"metadata": metadata}
        objects["dataPoint"].append(item)
    return objects


def table_objects() -> dict:
    return {
        "grid": [{"properties": {"gridHorizontal": lit("true"), "gridVertical": lit("false"), "outlineColor": color(THEME["border"]), "rowPadding": lit("3D")}}],
        "columnHeaders": [{"properties": {"fontFamily": prop_text("Segoe UI Semibold"), "fontSize": lit("7.4D"), "fontColor": color(THEME["text"]), "backColor": color(THEME["panel2"])}}],
        "values": [{"properties": {"fontSize": lit("7.05D"), "fontFamily": prop_text("Segoe UI"), "fontColor": color(THEME["text"]), "backColorPrimary": color(THEME["panel"]), "backColorSecondary": color(THEME["panel2"]), "urlIcon": lit("false")}}],
    }


def image_table_objects(image_w: int, image_h: int) -> dict:
    return {
        "grid": [{"properties": {"gridHorizontal": lit("false"), "gridVertical": lit("false"), "outlineColor": color(THEME["panel"]), "rowPadding": lit("0D"), "imageHeight": lit(f"{image_h}D"), "imageWidth": lit(f"{image_w}D")}}],
        "columnHeaders": [{"properties": {"show": lit("false")}}],
        "values": [{"properties": {"urlIcon": lit("false"), "fontSize": lit("1D"), "fontFamily": prop_text("Segoe UI"), "fontColor": color(THEME["text"]), "backColorPrimary": color(THEME["bg"]), "backColorSecondary": color(THEME["bg"]), "imageHeight": lit(f"{image_h}D"), "imageWidth": lit(f"{image_w}D")}}],
    }


def slicer_objects(title: str, single_select: bool = False) -> dict:
    return {
        "data": [{"properties": {"mode": prop_text("Dropdown")}}],
        "general": [{"properties": {"orientation": lit("0D")}}],
        "selection": [{"properties": {"selectAllCheckboxEnabled": lit("true"), "singleSelect": lit("true" if single_select else "false")}}],
        "header": [{"properties": {"show": lit("true"), "text": prop_text(title), "textSize": lit("8.4D"), "fontColor": color(THEME["muted"]), "fontFamily": prop_text("Segoe UI Semibold")}}],
        "items": [{"properties": {"textSize": lit("8.6D"), "fontColor": color(THEME["text"]), "fontFamily": prop_text("Segoe UI"), "background": color(THEME["panel"])}}],
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
        result[bucket] = [{"queryRef": f"{table}.{field}", **({"active": True} if idx == 0 else {})} for idx, (table, field, *_rest) in enumerate(fields)]
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
        sv["vcObjects"] = visual_shell(title, subtitle)
    elif kind == "slicer":
        sv["objects"] = slicer_objects(title, title.lower() == "scenario")
        sv["vcObjects"] = visual_shell(None, None)
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


def value_card(measure: str, title: str, x, y, w, h, z) -> dict:
    visual = data_visual("cardVisual", x, y, w, h, z, {"Data": [("KPI Measures", measure, "measure", title)]}, "")
    cfg = json.loads(visual["config"])
    metadata = f"KPI Measures.{measure}"
    cfg["singleVisual"]["objects"] = {
        "layout": [{"properties": {"backgroundShow": lit("false"), "rectangleRoundedCurve": lit("0L"), "cellPadding": lit("0D"), "paddingUniform": lit("0D")}, "selector": {"id": "default"}}],
        "value": [{"properties": {"fontSize": lit("18.5D"), "fontFamily": lit("'Segoe UI Semibold'"), "fontColor": color(title_accent(title))}, "selector": {"metadata": metadata}}],
        "label": [{"properties": {"show": lit("false")}, "selector": {"metadata": metadata}}],
        "spacing": [{"properties": {"verticalSpacing": lit("0D")}, "selector": {"id": "default"}}],
        "fillCustom": [{"properties": {"show": lit("false")}, "selector": {"id": "default"}}],
        "outline": [{"properties": {"show": lit("false")}, "selector": {"id": "default"}}],
        "divider": [{"properties": {"show": lit("false")}, "selector": {"metadata": metadata}}],
        "referenceLabelDetail": [{"properties": {"show": lit("false")}, "selector": {"metadata": metadata}}],
    }
    cfg["singleVisual"]["vcObjects"] = visual_shell_hidden()
    visual["config"] = json.dumps(cfg, separators=(",", ":"), ensure_ascii=False)
    return visual


def mini_sparkline(measure: str, x, y, w, h, z) -> dict:
    visual = data_visual(
        "lineClusteredColumnComboChart",
        x,
        y,
        w,
        h,
        z,
        {
            "Category": [("DimDate", "date", "column", "Date")],
            "Y2": [("KPI Measures", measure, "measure", "Trend")],
        },
        "",
    )
    cfg = json.loads(visual["config"])
    sv = cfg["singleVisual"]
    sv["vcObjects"] = visual_shell_hidden()
    sv["objects"].setdefault("valueAxis", [{"properties": {}}])[0]["properties"].update({
        "show": lit("false"),
        "gridlineShow": lit("false"),
        "labelDisplayUnits": lit("0D"),
    })
    sv["objects"].setdefault("categoryAxis", [{"properties": {}}])[0]["properties"].update({
        "show": lit("false"),
        "gridlineShow": lit("false"),
    })
    sv["objects"].setdefault("legend", [{"properties": {}}])[0]["properties"].update({"show": lit("false")})
    sv["objects"].setdefault("labels", [{"properties": {}}])[0]["properties"].update({"show": lit("false")})
    sv["objects"]["dataPoint"] = [{"properties": {"fill": color(THEME["teal"])}, "selector": {"metadata": f"KPI Measures.{measure}"}}]
    visual["config"] = json.dumps(cfg, separators=(",", ":"), ensure_ascii=False)
    return visual


def native_kpi_card(measure: str, title: str, x, y, z, w: int = 292, h: int = 104) -> list[dict]:
    accent = title_accent(title)
    return [
        shape(x, y, w, h, z, THEME["panel"]),
        shape(x, y, 4, h, z + 1, accent),
        text_box(title.upper(), x + 16, y + 12, w - 32, 14, z + 2, 7.2, THEME["muted"], False),
        value_card(measure, title, x + 14, y + 26, w - 28, 34, z + 3),
        mini_sparkline(measure, x + 14, y + 62, w - 28, 32, z + 4),
    ]


def decision_panel(title: str, lines: list[str], x, y, z, w: int = 536, h: int = 68) -> list[dict]:
    accent = title_accent(title)
    visuals = [
        shape(x, y, w, h, z, THEME["panel"]),
        shape(x, y, 4, h, z + 1, accent),
        text_box(title.upper(), x + 16, y + 8, w - 32, 13, z + 2, 7.2, accent, False),
    ]
    for idx, line in enumerate(lines[:3]):
        visuals.append(text_box(line, x + 16, y + 24 + idx * 13, w - 32, 12, z + 3 + idx, 7.2, THEME["text"] if idx == 0 else THEME["muted"], idx == 0))
    return visuals


def slicer(table: str, field: str, title: str, x, y, w, h, z) -> dict:
    return data_visual("slicer", x, y, w, h, z, {"Values": [(table, field, "column", title)]}, title)


def image_measure(measure: str, title: str, x, y, w, h, z, image_w: int | None = None, image_h: int | None = None) -> dict:
    image_w = int(image_w or w)
    image_h = int(image_h or h)
    visual = data_visual("tableEx", x, y, w, h, z, {"Values": [("KPI Measures", measure, "measure", title)]}, title)
    cfg = json.loads(visual["config"])
    cfg["singleVisual"]["objects"] = image_table_objects(image_w, image_h)
    cfg["singleVisual"]["vcObjects"] = visual_shell_hidden()
    visual["config"] = json.dumps(cfg, separators=(",", ":"), ensure_ascii=False)
    return visual


def kpi_card(measure: str, title: str, x, y, z) -> dict:
    return image_measure(measure, title, x, y, 292, 104, z, 292, 104)


def decision_chip_card(measure: str, title: str, x, y, z) -> dict:
    return image_measure(measure, title, x, y, 536, 68, z, 536, 68)


def text_box(text: str, x, y, w, h, z, size=12, fg=None, bold=True) -> dict:
    fg = fg or THEME["text"]
    cfg = {
        "name": rand_name(),
        "layouts": [{"id": 0, "position": pos(x, y, w, h, z)}],
        "singleVisual": {
            "visualType": "textbox",
            "drillFilterOtherVisuals": True,
            "objects": {
                "general": [{
                    "properties": {
                        "paragraphs": [{
                            "textRuns": [{
                                "value": text,
                                "textStyle": {
                                    "fontFamily": "Segoe UI Semibold" if bold else "Segoe UI",
                                    "fontSize": f"{size}pt",
                                    "color": fg,
                                },
                            }]
                        }]
                    }
                }]
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
        text_box("REGIONAL FP&A CONSOLIDATION", 38, 18, 260, 14, 20, 7.2, THEME["teal"], False),
        text_box(title, 38, 36, 520, 30, 30, 14, THEME["text"]),
        text_box(subtitle, 575, 36, 430, 24, 40, 8, THEME["muted"], False),
        shape(24, 70, 1232, 2, 50, THEME["border"]),
    ]


def top_filter_bar(filters: list[tuple[str, str, str, int]], start_x: int = 174) -> list[dict]:
    visuals = [
        shape(24, 78, 1232, 60, 60, THEME["panel2"]),
        shape(24, 78, 5, 60, 65, THEME["gold"]),
        text_box("FILTER LENS", 38, 98, 110, 18, 70, 8.0, THEME["gold"], False),
    ]
    x = start_x
    for idx, (table, field, title, width) in enumerate(filters):
        visuals.append(slicer(table, field, title, x, 86, width, 44, 100 + idx * 10))
        x += width + 12
    visuals.append(shape(704, 86, 536, 42, 180, THEME["panel"]))
    visuals.append(shape(704, 86, 4, 42, 181, THEME["teal"]))
    visuals.append(text_box("CURRENT LENS", 718, 92, 92, 12, 182, 6.8, THEME["teal"], False))
    visuals.append(text_box("Top slicers apply across the page; labels are sized for dropdown readability.", 718, 106, 500, 18, 183, 7.4, THEME["muted"], False))
    return visuals


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
    seed_pbix = ROOT / "output" / "dashboard_model_seed.pbix"
    if seed_pbix.exists():
        with zipfile.ZipFile(seed_pbix, "r") as package:
            raw = package.read("Report/Layout")
        base = json.loads(raw.decode("utf-16le"))
        base["sections"] = []
        base["theme"] = {"themeJson": {"name": "Regional FP&A Finance Seed", "dataColors": PALETTE}}
        return base
    return {
        "version": "5.44",
        "theme": {"themeJson": {"name": "Regional FP&A Finance Seed", "dataColors": PALETTE}},
        "config": json.dumps({"version": "5.44", "objects": {"section": [{"properties": {"verticalAlignment": prop_text("Top"), "background": color(THEME["bg"])}}]}}, separators=(",", ":")),
        "sections": [],
    }


def build_layout_six_tab_reference() -> dict:
    random.seed(13042)
    layout = blank_layout()
    p1 = header("Executive Overview", "CFO command page: status, variance drivers, and actions")
    p1 += [
        slicer("DimDate", "month_label", "Period", 900, 24, 110, 42, 100),
        slicer("DimEntity", "region", "Region", 1018, 24, 112, 42, 110),
        slicer("DimBusinessUnit", "business_unit", "BU", 1138, 24, 118, 42, 120),
        card("Actual Revenue", "Actual Revenue", 24, 92, 190, 88, 200),
        card("Actual EBITDA", "Actual EBITDA", 224, 92, 190, 88, 210),
        card("EBITDA Var vs Budget", "EBITDA Var", 424, 92, 190, 88, 220),
        card("EBITDA Margin %", "EBITDA Margin", 624, 92, 190, 88, 230),
        card("Cash Position", "Cash Position", 824, 92, 190, 88, 240),
        card("Open Exception Value", "Open Exceptions $", 1024, 92, 232, 88, 250),
        data_visual("waterfallChart", 24, 204, 610, 236, 300, {"Category": [("FactVarianceDriverBridge", "driver", "column", "Driver")], "Y": [("FactVarianceDriverBridge", "amount_usd", "column", "Amount")]}, "EBITDA Driver Bridge", "Actual vs budget bridge by variance driver"),
        data_visual("lineClusteredColumnComboChart", 646, 204, 610, 236, 310, {"Category": [("DimDate", "month_label", "column", "Month")], "Y": [("KPI Measures", "Actual Revenue", "measure", "Revenue")], "Y2": [("KPI Measures", "Actual EBITDA", "measure", "EBITDA")]}, "Revenue and EBITDA Trend", "Monthly consolidated performance"),
        data_visual("barChart", 24, 462, 438, 176, 320, {"Category": [("DimEntity", "country", "column", "Country")], "Y": [("KPI Measures", "EBITDA Var vs Budget", "measure", "EBITDA Var")]}, "Country EBITDA Variance", "Largest country pressure points"),
        data_visual("columnChart", 474, 462, 350, 176, 330, {"Category": [("DimBusinessUnit", "business_unit", "column", "BU")], "Y": [("KPI Measures", "Actual Revenue", "measure", "Revenue")]}, "BU Revenue Mix", "Business-unit contribution"),
        data_visual("tableEx", 836, 462, 420, 176, 340, {"Values": [("DimEntity", "country", "column", "Country"), ("KPI Measures", "Actual Revenue", "measure", "Revenue"), ("KPI Measures", "Actual EBITDA", "measure", "EBITDA"), ("KPI Measures", "EBITDA Var vs Budget", "measure", "Var"), ("KPI Measures", "Open Exception Value", "measure", "Open $")]}, "Management Attention List"),
    ]

    p2 = header("Entity & Country P&L", "Statement-style country review with actuals, budget and variance")
    p2 += [
        slicer("DimEntity", "country", "Country", 970, 24, 130, 42, 100),
        slicer("DimScenario", "scenario", "Scenario", 1110, 24, 146, 42, 110),
        card("Gross Revenue", "Gross Revenue", 24, 92, 190, 88, 200),
        card("Gross Profit", "Gross Profit", 224, 92, 190, 88, 210),
        card("OPEX", "OPEX", 424, 92, 190, 88, 220),
        card("Net Income", "Net Income", 624, 92, 190, 88, 230),
        card("Revenue Var %", "Revenue Var %", 824, 92, 190, 88, 240),
        card("Forecast Accuracy %", "Forecast Accuracy", 1024, 92, 232, 88, 250),
        data_visual("tableEx", 24, 204, 610, 434, 300, {"Values": [("DimAccount", "account_group", "column", "Group"), ("DimAccount", "account", "column", "Account"), ("FactFinancials", "amount_usd", "column", "Amount USD"), ("FactFinancials", "amount_local", "column", "Local"), ("DimScenario", "scenario", "column", "Scenario")]}, "P&L Statement Matrix", "Account hierarchy and scenario values"),
        data_visual("barChart", 646, 204, 300, 206, 310, {"Category": [("DimEntity", "country", "column", "Country")], "Y": [("KPI Measures", "Actual Revenue", "measure", "Revenue")]}, "Revenue by Country"),
        data_visual("donutChart", 958, 204, 298, 206, 320, {"Category": [("DimBusinessUnit", "business_unit", "column", "BU")], "Y": [("KPI Measures", "Actual Revenue", "measure", "Revenue")]}, "Revenue Mix by BU"),
        data_visual("tableEx", 646, 432, 610, 206, 330, {"Values": [("DimEntity", "region", "column", "Region"), ("DimEntity", "country", "column", "Country"), ("KPI Measures", "Budget Revenue", "measure", "Budget Rev"), ("KPI Measures", "Actual Revenue", "measure", "Actual Rev"), ("KPI Measures", "Revenue Var vs Budget", "measure", "Rev Var"), ("KPI Measures", "EBITDA Var vs Budget", "measure", "EBITDA Var")]}, "Country Variance Table"),
    ]

    p3 = header("FX & Intercompany", "Currency impact and elimination control view")
    p3 += [
        slicer("FactFXRate", "currency", "Currency", 1018, 24, 112, 42, 100),
        slicer("FactFXRate", "rate_type", "Rate Type", 1138, 24, 118, 42, 110),
        card("Intercompany Revenue", "IC Revenue", 24, 92, 190, 88, 200),
        card("Intercompany Elimination", "IC Elimination", 224, 92, 190, 88, 210),
        card("Gross Revenue", "Gross Revenue", 424, 92, 190, 88, 220),
        card("Total Revenue", "External Revenue", 624, 92, 190, 88, 230),
        card("Operating Cash Flow", "Operating Cash Flow", 824, 92, 190, 88, 240),
        card("Working Capital", "Working Capital", 1024, 92, 232, 88, 250),
        data_visual("lineClusteredColumnComboChart", 24, 204, 610, 236, 300, {"Category": [("DimDate", "month_label", "column", "Month")], "Y": [("FactFXRate", "rate_to_usd", "column", "FX Rate")], "Y2": [("KPI Measures", "Actual Revenue", "measure", "Revenue")]}, "FX Rate and Revenue Trend"),
        data_visual("barChart", 646, 204, 610, 236, 310, {"Category": [("DimEntity", "country", "column", "Country")], "Y": [("KPI Measures", "Intercompany Elimination", "measure", "IC Elimination")]}, "Intercompany Elimination by Country"),
        data_visual("tableEx", 24, 462, 610, 176, 320, {"Values": [("FactFXRate", "currency", "column", "Currency"), ("FactFXRate", "rate_type", "column", "Rate Type"), ("FactFXRate", "rate_to_usd", "column", "Rate to USD"), ("DimDate", "month_label", "column", "Month")]}, "FX Rate Register"),
        data_visual("tableEx", 646, 462, 610, 176, 330, {"Values": [("DimEntity", "country", "column", "Country"), ("KPI Measures", "Intercompany Revenue", "measure", "IC Revenue"), ("KPI Measures", "Intercompany Elimination", "measure", "Elimination"), ("KPI Measures", "Actual EBITDA", "measure", "EBITDA")]}, "IC Control Matrix"),
    ]

    p4 = header("BU Drilldown", "Portfolio view by business unit, country and margin")
    p4 += [
        slicer("DimBusinessUnit", "business_unit", "Business Unit", 970, 24, 130, 42, 100),
        slicer("DimEntity", "region", "Region", 1110, 24, 146, 42, 110),
        card("Actual Revenue", "Revenue", 24, 92, 230, 88, 200),
        card("Actual EBITDA", "EBITDA", 266, 92, 230, 88, 210),
        card("EBITDA Margin %", "Margin", 508, 92, 230, 88, 220),
        card("EBITDA Var %", "EBITDA Var %", 750, 92, 230, 88, 230),
        data_visual("barChart", 24, 204, 610, 236, 300, {"Category": [("DimBusinessUnit", "business_unit", "column", "BU")], "Y": [("KPI Measures", "Actual EBITDA", "measure", "EBITDA")]}, "EBITDA by Business Unit"),
        data_visual("columnChart", 646, 204, 610, 236, 310, {"Category": [("DimEntity", "country", "column", "Country")], "Y": [("KPI Measures", "EBITDA Margin %", "measure", "Margin")]}, "Margin by Country"),
        data_visual("tableEx", 24, 462, 1232, 176, 320, {"Values": [("DimBusinessUnit", "business_unit", "column", "BU"), ("DimEntity", "country", "column", "Country"), ("KPI Measures", "Actual Revenue", "measure", "Revenue"), ("KPI Measures", "Actual EBITDA", "measure", "EBITDA"), ("KPI Measures", "EBITDA Margin %", "measure", "Margin"), ("KPI Measures", "Revenue Var vs Budget", "measure", "Revenue Var")]}, "BU Detail Table"),
    ]

    p5 = header("Close Exceptions", "Operational close risk and owner queue")
    p5 += [
        slicer("FactCloseExceptions", "severity", "Severity", 970, 24, 130, 42, 100),
        slicer("FactCloseExceptions", "status", "Status", 1110, 24, 146, 42, 110),
        card("Open Exception Count", "Open Count", 24, 92, 230, 88, 200),
        card("Open Exception Value", "Open Value", 266, 92, 230, 88, 210),
        card("Actual EBITDA", "Actual EBITDA", 508, 92, 230, 88, 220),
        card("EBITDA Var vs Budget", "EBITDA Var", 750, 92, 230, 88, 230),
        data_visual("barChart", 24, 204, 390, 236, 300, {"Category": [("FactCloseExceptions", "severity", "column", "Severity")], "Y": [("FactCloseExceptions", "amount_usd", "column", "Amount")]}, "Exposure by Severity"),
        data_visual("columnChart", 426, 204, 390, 236, 310, {"Category": [("FactCloseExceptions", "status", "column", "Status")], "Y": [("FactCloseExceptions", "amount_usd", "column", "Amount")]}, "Exception Value by Status"),
        data_visual("barChart", 828, 204, 428, 236, 320, {"Category": [("FactCloseExceptions", "owner_team", "column", "Owner")], "Y": [("FactCloseExceptions", "amount_usd", "column", "Amount")]}, "Owner Exposure"),
        data_visual("tableEx", 24, 462, 1232, 176, 330, {"Values": [("FactCloseExceptions", "exception_id", "column", "ID"), ("FactCloseExceptions", "country", "column", "Country"), ("FactCloseExceptions", "exception_type", "column", "Type"), ("FactCloseExceptions", "owner_team", "column", "Owner"), ("FactCloseExceptions", "severity", "column", "Severity"), ("FactCloseExceptions", "status", "column", "Status"), ("FactCloseExceptions", "amount_usd", "column", "Amount"), ("FactCloseExceptions", "commentary", "column", "Commentary")]}, "Close Exception Queue"),
    ]

    p6 = header("Board Storyboard", "Board-ready finance narrative from budget to actual")
    p6 += [
        card("Budget EBITDA", "Budget EBITDA", 24, 92, 230, 88, 200),
        card("Actual EBITDA", "Actual EBITDA", 266, 92, 230, 88, 210),
        card("EBITDA Var vs Budget", "EBITDA Gap", 508, 92, 230, 88, 220),
        card("Forecast EBITDA", "Forecast EBITDA", 750, 92, 230, 88, 230),
        card("Forecast Accuracy %", "Forecast Accuracy", 992, 92, 264, 88, 240),
        data_visual("waterfallChart", 24, 204, 728, 274, 300, {"Category": [("FactVarianceDriverBridge", "driver", "column", "Driver")], "Y": [("FactVarianceDriverBridge", "amount_usd", "column", "Amount")]}, "Board EBITDA Walk", "Variance bridge for the selected scope"),
        data_visual("barChart", 764, 204, 492, 274, 310, {"Category": [("DimEntity", "country", "column", "Country")], "Y": [("KPI Measures", "Actual Revenue", "measure", "Revenue")]}, "Country Revenue Blocks"),
        data_visual("tableEx", 24, 500, 1232, 138, 320, {"Values": [("DimEntity", "country", "column", "Country"), ("KPI Measures", "Actual Revenue", "measure", "Revenue"), ("KPI Measures", "Actual EBITDA", "measure", "EBITDA"), ("KPI Measures", "EBITDA Margin %", "measure", "Margin"), ("KPI Measures", "EBITDA Var vs Budget", "measure", "Var vs Budget"), ("KPI Measures", "Open Exception Value", "measure", "Close Risk")]}, "Board Pack Extract"),
    ]

    layout["sections"] = [
        section("ExecutiveOverview", "Executive Overview", 0, p1),
        section("EntityCountryPnL", "Entity & Country P&L", 1, p2),
        section("FxIntercompany", "FX & Intercompany", 2, p3),
        section("BuDrilldown", "BU Drilldown", 3, p4),
        section("CloseExceptions", "Close Exceptions", 4, p5),
        section("BoardStoryboard", "Board Storyboard", 5, p6),
    ]
    return layout


def build_layout() -> dict:
    random.seed(13042)
    layout = blank_layout()

    p1 = header("Executive Summary", "CFO snapshot: performance, drivers, country gaps, and close-risk exposure")
    p1 += top_filter_bar([
        ("DimDate", "month_label", "Period", 148),
        ("DimEntity", "region", "Region", 148),
        ("DimBusinessUnit", "business_unit", "BU", 166),
    ])
    p1 += [
        *native_kpi_card("Actual Revenue", "Revenue", 24, 150, 200),
        *native_kpi_card("Actual EBITDA", "EBITDA", 332, 150, 210),
        *native_kpi_card("EBITDA Margin %", "Margin", 640, 150, 220),
        *native_kpi_card("Open Exception Value", "Close Risk", 948, 150, 230),
        data_visual(
            "lineClusteredColumnComboChart",
            24,
            278,
            610,
            222,
            300,
            {
                "Category": [("DimDate", "date", "column", "Month")],
                "Y": [("KPI Measures", "Actual Revenue", "measure", "Revenue")],
                "Y2": [("KPI Measures", "Actual EBITDA", "measure", "EBITDA")],
            },
            "Revenue and EBITDA Trend",
            "Monthly consolidated performance",
        ),
        data_visual(
            "waterfallChart",
            646,
            278,
            610,
            222,
            310,
            {
                "Category": [("FactVarianceDriverBridge", "driver", "column", "Driver")],
                "Y": [("FactVarianceDriverBridge", "amount_usd", "column", "Amount")],
            },
            "EBITDA Driver Bridge",
            "Actual vs budget bridge by variance driver",
        ),
        data_visual(
            "barChart",
            24,
            522,
            438,
            174,
            320,
            {
                "Category": [("DimEntity", "country", "column", "Country")],
                "Y": [("KPI Measures", "EBITDA Var vs Budget", "measure", "EBITDA Var")],
            },
            "Country EBITDA Variance",
            "Largest country pressure points",
        ),
        data_visual(
            "columnChart",
            474,
            522,
            350,
            174,
            330,
            {
                "Category": [("DimBusinessUnit", "business_unit", "column", "BU")],
                "Y": [("KPI Measures", "Actual Revenue", "measure", "Revenue")],
            },
            "BU Revenue Mix",
            "Business-unit contribution",
        ),
        data_visual(
            "tableEx",
            836,
            522,
            420,
            174,
            340,
            {
                "Values": [
                    ("DimEntity", "country", "column", "Country"),
                    ("KPI Measures", "Actual Revenue", "measure", "Revenue"),
                    ("KPI Measures", "Actual EBITDA", "measure", "EBITDA"),
                    ("KPI Measures", "EBITDA Var vs Budget", "measure", "Var"),
                    ("KPI Measures", "Open Exception Value", "measure", "Open $"),
                ]
            },
            "Management Attention List",
        ),
    ]

    p2 = header("P&L Variance", "Statement view by entity, scenario, business unit, and variance")
    p2 += top_filter_bar([
        ("DimEntity", "country", "Country", 180),
        ("DimScenario", "scenario", "Scenario", 180),
    ])
    p2 += [
        *native_kpi_card("Gross Revenue", "Gross Revenue", 24, 150, 200),
        *native_kpi_card("Gross Profit", "Gross Profit", 332, 150, 210),
        *native_kpi_card("OPEX", "OPEX", 640, 150, 220),
        *native_kpi_card("Net Income", "Net Income", 948, 150, 230),
        data_visual(
            "tableEx",
            24,
            278,
            610,
            418,
            300,
            {
                "Values": [
                    ("DimAccount", "account_group", "column", "Group"),
                    ("DimAccount", "account", "column", "Account"),
                    ("FactFinancials", "amount_usd", "column", "Amount USD"),
                    ("FactFinancials", "amount_local", "column", "Local"),
                    ("DimScenario", "scenario", "column", "Scenario"),
                ]
            },
            "P&L Statement Matrix",
            "Account hierarchy and scenario values",
        ),
        data_visual(
            "barChart",
            646,
            278,
            300,
            200,
            310,
            {
                "Category": [("DimEntity", "country", "column", "Country")],
                "Y": [("KPI Measures", "Actual Revenue", "measure", "Revenue")],
            },
            "Revenue by Country",
        ),
        data_visual(
            "donutChart",
            958,
            278,
            298,
            200,
            320,
            {
                "Category": [("DimBusinessUnit", "business_unit", "column", "BU")],
                "Y": [("KPI Measures", "Actual Revenue", "measure", "Revenue")],
            },
            "Revenue Mix by BU",
        ),
        data_visual(
            "tableEx",
            646,
            496,
            610,
            200,
            330,
            {
                "Values": [
                    ("DimEntity", "region", "column", "Region"),
                    ("DimEntity", "country", "column", "Country"),
                    ("KPI Measures", "Budget Revenue", "measure", "Budget Rev"),
                    ("KPI Measures", "Actual Revenue", "measure", "Actual Rev"),
                    ("KPI Measures", "Revenue Var vs Budget", "measure", "Rev Var"),
                    ("KPI Measures", "EBITDA Var vs Budget", "measure", "EBITDA Var"),
                ]
            },
            "Country Variance Table",
        ),
    ]

    p3 = header("Controls & Storyboard", "FX, intercompany, close exceptions, and board-ready narrative")
    p3 += top_filter_bar([
        ("FactFXRate", "currency", "Currency", 154),
        ("FactCloseExceptions", "severity", "Severity", 154),
        ("FactCloseExceptions", "status", "Status", 154),
    ])
    p3 += [
        *native_kpi_card("Intercompany Revenue", "IC Revenue", 24, 150, 200),
        *native_kpi_card("Intercompany Elimination", "IC Elimination", 332, 150, 210),
        *native_kpi_card("Open Exception Value", "Close Risk", 640, 150, 220),
        *native_kpi_card("Forecast Accuracy %", "Forecast Accuracy", 948, 150, 230),
        data_visual(
            "barChart",
            24,
            278,
            390,
            222,
            300,
            {
                "Category": [("DimEntity", "country", "column", "Country")],
                "Y": [("KPI Measures", "Intercompany Elimination", "measure", "IC Elimination")],
            },
            "Intercompany Elimination by Country",
        ),
        data_visual(
            "columnChart",
            426,
            278,
            390,
            222,
            310,
            {
                "Category": [("FactCloseExceptions", "status", "column", "Status")],
                "Y": [("FactCloseExceptions", "amount_usd", "column", "Amount")],
            },
            "Exception Value by Status",
        ),
        data_visual(
            "waterfallChart",
            828,
            278,
            428,
            222,
            320,
            {
                "Category": [("FactVarianceDriverBridge", "driver", "column", "Driver")],
                "Y": [("FactVarianceDriverBridge", "amount_usd", "column", "Amount")],
            },
            "Board EBITDA Walk",
            "Variance bridge for the selected scope",
        ),
        *decision_panel("Decision Signals", ["Revenue and EBITDA trend are visible against monthly context.", "Country variance and BU mix stay on the executive page.", "Use the queue below for follow-up ownership."], 24, 522, 330),
        data_visual(
            "tableEx",
            24,
            596,
            610,
            100,
            330,
            {
                "Values": [
                    ("FactCloseExceptions", "exception_id", "column", "ID"),
                    ("FactCloseExceptions", "country", "column", "Country"),
                    ("FactCloseExceptions", "exception_type", "column", "Type"),
                    ("FactCloseExceptions", "owner_team", "column", "Owner"),
                    ("FactCloseExceptions", "severity", "column", "Severity"),
                    ("FactCloseExceptions", "status", "column", "Status"),
                    ("FactCloseExceptions", "amount_usd", "column", "Amount"),
                ]
            },
            "Close Exception Queue",
        ),
        *decision_panel("Control Signals", ["IC elimination and exception exposure sit beside the board bridge.", "Severity and status filters keep close-risk review focused.", "Board extract is ready for country-level discussion."], 646, 522, 340),
        data_visual(
            "tableEx",
            646,
            596,
            610,
            100,
            340,
            {
                "Values": [
                    ("DimEntity", "country", "column", "Country"),
                    ("KPI Measures", "Actual Revenue", "measure", "Revenue"),
                    ("KPI Measures", "Actual EBITDA", "measure", "EBITDA"),
                    ("KPI Measures", "EBITDA Margin %", "measure", "Margin"),
                    ("KPI Measures", "EBITDA Var vs Budget", "measure", "Var vs Budget"),
                    ("KPI Measures", "Open Exception Value", "measure", "Close Risk"),
                ]
            },
            "Board Pack Extract",
        ),
    ]

    layout["activeSectionIndex"] = 0
    layout["sections"] = [
        section("ExecutiveSummary", "Executive Summary", 0, p1),
        section("PnLVariance", "P&L Variance", 1, p2),
        section("ControlsStoryboard", "Controls & Storyboard", 2, p3),
    ]
    return layout


def write_native_scripts() -> None:
    (ROOT / "powerbi").mkdir(parents=True, exist_ok=True)
    (ROOT / "build").mkdir(parents=True, exist_ok=True)
    (ROOT / "qa").mkdir(parents=True, exist_ok=True)

    (ROOT / "powerbi" / "prepare_seed_pbix.ps1").write_text(f"""param(
  [string]$SeedTemplate = "{SEED_TEMPLATE}",
  [string]$TargetPbix = "{ROOT / 'output' / 'dashboard_model_seed.pbix'}"
)

$ErrorActionPreference = "Stop"
if (!(Test-Path -LiteralPath $SeedTemplate)) {{ throw "Seed template not found: $SeedTemplate" }}
New-Item -ItemType Directory -Force -Path (Split-Path -Parent $TargetPbix) | Out-Null
Copy-Item -LiteralPath $SeedTemplate -Destination $TargetPbix -Force
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
if ([string]::IsNullOrWhiteSpace($TargetPbix)) { $TargetPbix = Join-Path $ProjectRoot "output\dashboard_model_seed.pbix" }
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
    "decimal" { return [Microsoft.AnalysisServices.Tabular.DataType]::Decimal }
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
      if ($measureDef.dataCategory) { try { $measure.DataCategory = [string]$measureDef.dataCategory } catch {} }
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
  status = "project13_model_pushed_via_tom"
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
if ([string]::IsNullOrWhiteSpace($ModelPbix)) { $ModelPbix = Join-Path $ProjectRoot "output\dashboard_model_seed.pbix" }
if ([string]::IsNullOrWhiteSpace($LayoutJson)) { $LayoutJson = Join-Path $ProjectRoot "build\native_report_layout_project13.json" }
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
