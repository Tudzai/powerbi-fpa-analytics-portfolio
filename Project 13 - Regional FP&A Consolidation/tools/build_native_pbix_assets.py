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
MONEY_FORMAT = "$#,0;($#,0);$0"


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
    ("FactCloseExceptions", "business_unit_id", "DimBusinessUnit", "business_unit_id"),
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
    dark_panel = "%23242B35"
    dark_panel_2 = "%231F2630"
    dark_border = "%233A4655"
    dark_rule = "%23313B48"
    muted = "%23B9C3CF"
    text = "%23F7FAFC"
    footer_fill = "%232C3440"
    good = THEME["green"].replace("#", "%23")
    warn = THEME["gold"].replace("#", "%23")
    bad = THEME["rose"].replace("#", "%23")
    label_font = "13.0" if len(label) > 12 else "14.2"
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
    COALESCE ( CALCULATE ( [{base_measure}], REMOVEFILTERS ( DimDate ), DimDate[date] = d ), 0 )
VAR PriorDate = EDATE ( d, -12 )
VAR PriorValue =
    COALESCE ( CALCULATE ( [{base_measure}], REMOVEFILTERS ( DimDate ), DimDate[date] = PriorDate ), 0 )
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
        70,
        96 - DIVIDE ( FirstValue - MinValue, MaxValue - MinValue, 0.5 ) * 52
    )
VAR LastY =
    IF (
        MaxValue = MinValue,
        70,
        96 - DIVIDE ( LastValue - MinValue, MaxValue - MinValue, 0.5 ) * 52
    )
VAR LinePoints =
    CONCATENATEX (
        CleanTable,
        VAR RankValue = RANKX ( CleanTable, DimDate[date], , ASC, DENSE ) - 1
        VAR XValue = 172 + DIVIDE ( RankValue, MAX ( 1, RowCount - 1 ), 0 ) * 102
        VAR YRatio =
            IF (
                MaxValue = MinValue,
                0.5,
                DIVIDE ( [__Value] - MinValue, MaxValue - MinValue, 0.5 )
            )
        VAR YValue = 96 - YRatio * 52
        RETURN FORMAT ( XValue, "0.0", "en-US" ) & "," & FORMAT ( YValue, "0.0", "en-US" ),
        " ",
        DimDate[date],
        ASC
    )
VAR AreaPoints = "172,106 " & LinePoints & " 274,106"
VAR ValueText = {_svg_text_expr(value_text)}
VAR PyText = {_svg_text_expr(py_text)}
VAR DeltaText = {_svg_text_expr(delta_text)}
VAR Sparkline =
    IF (
        RowCount >= 2,
        "<g clip-path='url(%23sparkClip)'><polygon points='" & AreaPoints & "' fill='" & TrendColor & "' fill-opacity='0.26'/>"
            & "<polyline points='" & LinePoints & "' fill='none' stroke='" & TrendColor & "' stroke-width='4.0' stroke-linecap='round' stroke-linejoin='round'/></g>"
            & "<circle cx='172' cy='" & FORMAT ( FirstY, "0.0", "en-US" ) & "' r='4.4' fill='{dark_panel_2}' stroke='{muted}' stroke-width='1.45'/>"
            & "<circle cx='274' cy='" & FORMAT ( LastY, "0.0", "en-US" ) & "' r='5.6' fill='" & TrendColor & "'/>",
        "<line x1='172' y1='70' x2='274' y2='70' stroke='{dark_rule}' stroke-width='4.0' stroke-linecap='round'/>"
    )
VAR SVG =
    "<svg xmlns='http://www.w3.org/2000/svg' width='296' height='135' viewBox='0 0 296 135'>"
    & "<defs><clipPath id='sparkClip'><rect x='170' y='43' width='106' height='64' rx='5'/></clipPath></defs>"
    & "<rect x='1.2' y='1.2' width='293.6' height='132.6' rx='12' fill='{dark_panel}' stroke='{dark_border}' stroke-width='1.05'/>"
    & "<rect x='13' y='13' width='150' height='4.5' rx='2.25' fill='{accent_enc}'/>"
    & "<rect x='13' y='31' width='16' height='16' rx='4.2' fill='{accent_enc}' fill-opacity='0.22' stroke='{accent_enc}' stroke-width='1.15'/>"
    & "<text x='38' y='45' font-family='Segoe UI Semibold' font-size='{label_font}' fill='{text}' letter-spacing='0'>{label}</text>"
    & "<text x='13' y='98' font-family='Segoe UI Semibold' font-size='38' fill='{accent_enc}' letter-spacing='0'>" & ValueText & "</text>"
    & "<rect x='162' y='32' width='120' height='82' rx='9' fill='{dark_panel_2}' stroke='{dark_border}' stroke-width='1.0'/>"
    & "<rect x='170' y='43' width='106' height='64' rx='5.5' fill='{accent_enc}' fill-opacity='0.13'/>"
    & "<line x1='170' y1='73' x2='276' y2='73' stroke='{dark_rule}' stroke-width='1.4' stroke-dasharray='4 5'/>"
    & Sparkline
    & "<rect x='13' y='110' width='94' height='20' rx='9' fill='{footer_fill}' stroke='{dark_border}' stroke-width='0.75'/>"
    & "<text x='23' y='124' font-family='Segoe UI Semibold' font-size='10.5' fill='{muted}'>PY " & PyText & "</text>"
    & "<rect x='113' y='110' width='76' height='20' rx='9' fill='" & StatusColor & "' fill-opacity='0.16' stroke='" & StatusColor & "' stroke-opacity='0.18'/>"
    & "<text x='151' y='124' text-anchor='middle' font-family='Segoe UI Semibold' font-size='10.5' fill='" & StatusColor & "'>" & DeltaText & "</text>"
    & "<rect x='195' y='110' width='87' height='20' rx='9' fill='" & StatusColor & "' fill-opacity='0.11'/>"
    & "<text x='238.5' y='124' text-anchor='middle' font-family='Segoe UI Semibold' font-size='10.2' fill='" & StatusColor & "'>" & StatusText & "</text>"
    & "</svg>"
RETURN
    "data:image/svg+xml;utf8," & SVG
"""
    return _measure(name, dax, fmt, definition, "ImageUrl")


def _lens_svg_measure() -> dict:
    teal = THEME["teal"].replace("#", "%23")
    blue = THEME["blue"].replace("#", "%23")
    gold = THEME["gold"].replace("#", "%23")
    rose = THEME["rose"].replace("#", "%23")
    text = "%23F7FAFC"
    muted = "%23C7D0DB"
    dark_panel = "%23242B35"
    dark_panel_2 = "%231F2630"
    border = "%233A4655"
    dax = f"""
VAR PeriodText = [Selected Latest Complete Period Label]
VAR RegionRaw =
    IF ( ISFILTERED ( DimEntity[region] ), CONCATENATEX ( VALUES ( DimEntity[region] ), DimEntity[region], ", " ), "All regions" )
VAR BURaw =
    IF ( ISFILTERED ( DimBusinessUnit[business_unit] ), CONCATENATEX ( VALUES ( DimBusinessUnit[business_unit] ), DimBusinessUnit[business_unit], ", " ), "All BUs" )
VAR ScenarioRaw =
    IF ( ISFILTERED ( DimScenario[scenario] ), CONCATENATEX ( VALUES ( DimScenario[scenario] ), DimScenario[scenario], ", " ), "Actual lens" )
VAR ScenarioText = SUBSTITUTE ( LEFT ( ScenarioRaw, 20 ), "&", "and" )
VAR RegionText = SUBSTITUTE ( LEFT ( RegionRaw, 24 ), "&", "and" )
VAR BUText = SUBSTITUTE ( LEFT ( BURaw, 28 ), "&", "and" )
VAR RevVar = [Latest Revenue Var %]
VAR EbitdaVar = [Latest EBITDA Var %]
VAR RiskValue = COALESCE ( [Latest Open Exception Value], 0 )
VAR RevText = SUBSTITUTE ( FORMAT ( RevVar, "+0.0%;-0.0%;0.0%" ), "%", "%25" )
VAR StatusColor = IF ( EbitdaVar >= 0.02, "{teal}", IF ( EbitdaVar >= -0.02, "{gold}", "{rose}" ) )
VAR Line1 = SUBSTITUTE ( LEFT ( PeriodText & " | " & ScenarioText, 38 ), "&", "and" )
VAR Line2 = SUBSTITUTE ( LEFT ( BUText & " | " & RegionText, 48 ), "&", "and" )
VAR RiskText = "$" & FORMAT ( DIVIDE ( RiskValue, 1000000 ), "0.0M" )
VAR SVG =
    "<svg xmlns='http://www.w3.org/2000/svg' width='568' height='78' viewBox='0 0 568 78'>"
    & "<rect x='18' y='14' width='5' height='50' rx='2.5' fill='{teal}'/>"
    & "<circle cx='46' cy='27' r='7.4' fill='" & StatusColor & "'/>"
    & "<text x='64' y='28' font-family='Segoe UI Semibold' font-size='14.0' fill='{text}'>CURRENT LENS</text>"
    & "<text x='64' y='50' font-family='Segoe UI Semibold' font-size='13.1' fill='{text}'>" & Line1 & "</text>"
    & "<text x='64' y='66' font-family='Segoe UI' font-size='12.2' fill='{muted}'>" & Line2 & "</text>"
    & "<rect x='244' y='10' width='154' height='58' rx='11' fill='{dark_panel_2}' stroke='{border}' stroke-width='1.05'/>"
    & "<text x='321' y='30' text-anchor='middle' font-family='Segoe UI' font-size='11.2' fill='{muted}'>Revenue var</text>"
    & "<text x='321' y='57' text-anchor='middle' font-family='Segoe UI Semibold' font-size='22.0' fill='{blue}'>" & RevText & "</text>"
    & "<rect x='410' y='10' width='144' height='58' rx='11' fill='{dark_panel_2}' stroke='{border}' stroke-width='1.05'/>"
    & "<text x='482' y='30' text-anchor='middle' font-family='Segoe UI' font-size='11.2' fill='{muted}'>Close risk</text>"
    & "<text x='482' y='57' text-anchor='middle' font-family='Segoe UI Semibold' font-size='22.0' fill='{gold}'>" & RiskText & "</text>"
    & "</svg>"
RETURN
    "data:image/svg+xml;utf8," & SVG
"""
    return _measure("Lens Summary SVG", dax, "", "Top-bar Current Lens SVG for selected period, region, BU, revenue variance, and close-risk exposure.", "ImageUrl")


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
        _measure("Bridge Amount", "SUM ( FactVarianceDriverBridge[amount_usd] )", MONEY_FORMAT, "Variance-driver bridge amount with explicit aggregation for native Power BI visuals."),
        _latest_measure("Latest Bridge Amount", "Bridge Amount", MONEY_FORMAT, "Variance-driver bridge amount at selected latest complete period."),
        _measure("Exception Amount", "SUM ( FactCloseExceptions[amount_usd] )", MONEY_FORMAT, "Close-exception exposure with explicit aggregation for native Power BI visuals."),
        _latest_measure("Latest Exception Amount", "Exception Amount", MONEY_FORMAT, "Close-exception exposure at selected latest complete period."),
        _measure("Financial Amount", "SUM ( FactFinancials[amount_usd] )", MONEY_FORMAT, "P&L statement amount with explicit aggregation for native Power BI visuals."),
        _latest_measure("Latest Actual Revenue", "Actual Revenue", MONEY_FORMAT, "Actual revenue at selected latest complete period."),
        _latest_measure("Latest Budget Revenue", "Budget Revenue", MONEY_FORMAT, "Budget revenue at selected latest complete period."),
        _latest_measure("Latest Revenue Var vs Budget", "Revenue Var vs Budget", MONEY_FORMAT, "Revenue variance at selected latest complete period."),
        _latest_measure("Latest Revenue Var %", "Revenue Var %", "0.0%", "Revenue variance percent at selected latest complete period."),
        _latest_measure("Latest Actual EBITDA", "Actual EBITDA", MONEY_FORMAT, "Actual EBITDA at selected latest complete period."),
        _latest_measure("Latest Budget EBITDA", "Budget EBITDA", MONEY_FORMAT, "Budget EBITDA at selected latest complete period."),
        _latest_measure("Latest EBITDA Var vs Budget", "EBITDA Var vs Budget", MONEY_FORMAT, "EBITDA variance at selected latest complete period."),
        _latest_measure("Latest EBITDA Var %", "EBITDA Var %", "0.0%", "EBITDA variance percent at selected latest complete period."),
        _latest_measure("Latest Gross Revenue", "Gross Revenue", MONEY_FORMAT, "Gross revenue at selected latest complete period."),
        _latest_measure("Latest Gross Profit", "Gross Profit", MONEY_FORMAT, "Gross profit at selected latest complete period."),
        _latest_measure("Latest Gross Margin %", "Gross Margin %", "0.0%", "Gross margin at selected latest complete period."),
        _latest_measure("Latest OPEX", "OPEX", MONEY_FORMAT, "OPEX at selected latest complete period."),
        _latest_measure("Latest Net Income", "Net Income", MONEY_FORMAT, "Net income at selected latest complete period."),
        _latest_measure("Latest EBITDA Margin %", "EBITDA Margin %", "0.0%", "EBITDA margin at selected latest complete period."),
        _latest_measure("Latest Cash Position", "Cash Position", MONEY_FORMAT, "Cash position at selected latest complete period."),
        _latest_measure("Latest Operating Cash Flow", "Operating Cash Flow", MONEY_FORMAT, "Operating cash flow at selected latest complete period."),
        _latest_measure("Latest Forecast Accuracy %", "Forecast Accuracy %", "0.0%", "Forecast accuracy at selected latest complete period."),
        _latest_measure("Latest Intercompany Revenue", "Intercompany Revenue", MONEY_FORMAT, "Intercompany revenue at selected latest complete period."),
        _latest_measure("Latest Intercompany Elimination", "Intercompany Elimination", MONEY_FORMAT, "Intercompany elimination impact at selected latest complete period."),
        _latest_measure("Latest Open Exception Count", "Open Exception Count", "#,0", "Open close-exception count at selected latest complete period."),
        _latest_measure("Latest Open Exception Value", "Open Exception Value", MONEY_FORMAT, "Open close-exception exposure at selected latest complete period."),
        _measure("Display Actual Revenue", 'FORMAT ( DIVIDE ( [Latest Actual Revenue], 1000000 ), "$0.0M;($0.0M);$0.0M" )', "", "Text display for latest revenue KPI card."),
        _measure("Display Actual EBITDA", 'FORMAT ( DIVIDE ( [Latest Actual EBITDA], 1000000 ), "$0.0M;($0.0M);$0.0M" )', "", "Text display for latest EBITDA KPI card."),
        _measure("Display EBITDA Margin %", 'FORMAT ( [Latest EBITDA Margin %], "0.0%" )', "", "Text display for latest EBITDA margin KPI card."),
        _measure("Display Gross Revenue", 'FORMAT ( DIVIDE ( [Latest Gross Revenue], 1000000 ), "$0.0M;($0.0M);$0.0M" )', "", "Text display for latest gross revenue KPI card."),
        _measure("Display Gross Profit", 'FORMAT ( DIVIDE ( [Latest Gross Profit], 1000000 ), "$0.0M;($0.0M);$0.0M" )', "", "Text display for latest gross profit KPI card."),
        _measure("Display OPEX", 'FORMAT ( DIVIDE ( [Latest OPEX], 1000000 ), "$0.0M;($0.0M);$0.0M" )', "", "Text display for latest OPEX KPI card."),
        _measure("Display Net Income", 'FORMAT ( DIVIDE ( [Latest Net Income], 1000000 ), "$0.0M;($0.0M);$0.0M" )', "", "Text display for latest net income KPI card."),
        _measure("Display Intercompany Revenue", 'FORMAT ( DIVIDE ( [Latest Intercompany Revenue], 1000000 ), "$0.0M;($0.0M);$0.0M" )', "", "Text display for latest intercompany revenue KPI card."),
        _measure("Display Intercompany Elimination", 'FORMAT ( DIVIDE ( [Latest Intercompany Elimination], 1000000 ), "$0.0M;($0.0M);$0.0M" )', "", "Text display for latest intercompany elimination KPI card."),
        _measure("Display Forecast Accuracy %", 'FORMAT ( [Latest Forecast Accuracy %], "0.0%" )', "", "Text display for latest forecast accuracy KPI card."),
        _measure("Display Open Exception Value", 'FORMAT ( DIVIDE ( [Latest Open Exception Value], 1000000 ), "$0.0M;($0.0M);$0.0M" )', "", "Text display for latest close-risk KPI card."),
        _measure("Display Open Exception Count", 'FORMAT ( [Latest Open Exception Count], "#,0" )', "", "Text display for latest close-exception count chip."),
        _measure("Display Revenue PY", 'FORMAT ( DIVIDE ( [Revenue PY], 1000000 ), "$0.0M;($0.0M);$0.0M" )', "", "Text display for prior-year revenue."),
        _measure("Display EBITDA PY", 'FORMAT ( DIVIDE ( [EBITDA PY], 1000000 ), "$0.0M;($0.0M);$0.0M" )', "", "Text display for prior-year EBITDA."),
        _measure("Display Open Exception Value PY", 'FORMAT ( DIVIDE ( [Open Exception Value PY], 1000000 ), "$0.0M;($0.0M);$0.0M" )', "", "Text display for prior-year open exception value."),
        _measure("Display Revenue Var %", 'FORMAT ( [Latest Revenue Var %], "+0.0%;-0.0%;0.0%" )', "", "Text display for latest revenue variance percent."),
        _measure("Display EBITDA Var %", 'FORMAT ( [Latest EBITDA Var %], "+0.0%;-0.0%;0.0%" )', "", "Text display for latest EBITDA variance percent."),
        _measure("Display Forecast Accuracy Delta", 'FORMAT ( [Latest Forecast Accuracy %], "0.0%" )', "", "Text display for latest forecast accuracy footer."),
        _measure(
            "Current Lens Line 1",
            """
VAR ScenarioRaw =
    IF ( ISFILTERED ( DimScenario[scenario] ), CONCATENATEX ( VALUES ( DimScenario[scenario] ), DimScenario[scenario], ", " ), "Actual lens" )
RETURN
    [Selected Latest Complete Period Label] & " | " & LEFT ( ScenarioRaw, 24 )
""",
            "",
            "First dynamic line for the Current Lens native panel.",
        ),
        _measure(
            "Current Lens Line 2",
            """
VAR RegionRaw =
    IF ( ISFILTERED ( DimEntity[region] ), CONCATENATEX ( VALUES ( DimEntity[region] ), DimEntity[region], ", " ), "All regions" )
VAR BURaw =
    IF ( ISFILTERED ( DimBusinessUnit[business_unit] ), CONCATENATEX ( VALUES ( DimBusinessUnit[business_unit] ), DimBusinessUnit[business_unit], ", " ), "All BUs" )
RETURN
    LEFT ( BURaw, 28 ) & " | " & LEFT ( RegionRaw, 28 )
""",
            "",
            "Second dynamic line for the Current Lens native panel.",
        ),
        _py_measure("Revenue PY", "Actual Revenue", MONEY_FORMAT, "Actual revenue for the same month in the prior year."),
        _py_measure("EBITDA PY", "Actual EBITDA", MONEY_FORMAT, "Actual EBITDA for the same month in the prior year."),
        _py_measure("Gross Margin PY %", "Gross Margin %", "0.0%", "Gross margin for the same month in the prior year."),
        _py_measure("Cash Position PY", "Cash Position", MONEY_FORMAT, "Cash position for the same month in the prior year."),
        _py_measure("Open Exception Value PY", "Open Exception Value", MONEY_FORMAT, "Open exception value for the same month in the prior year."),
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
    chips = [_lens_svg_measure()]
    return helpers + cards + chips


def measure_catalog() -> list[dict]:
    base = json.loads((ROOT / "model" / "measure_catalog.json").read_text(encoding="utf-8"))
    names = {item["measure_name"] for item in base}
    extras = [item for item in project20_svg_measure_catalog() if item["measure_name"] not in names]
    catalog = base + extras
    for item in catalog:
        if item.get("format_string") in {"$#,0,,.0M", "$#,0.0,,M;($#,0.0,,M);$0.0M"}:
            item["format_string"] = MONEY_FORMAT
    return catalog


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
    "lineChart": load_sample("columnChart"),
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
        "visualHeader": [{"properties": {"show": lit("false")}}],
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
        "visualHeader": [{"properties": {"show": lit("false")}}],
    }


def svg_card_shell(fill: str = "#242B35", border: str = "#3A4655", radius: float = 10.0, shadow: bool = True) -> dict:
    return {
        "background": [{"properties": {"show": lit("true"), "color": color(fill), "transparency": lit("0D")}}],
        "border": [{"properties": {"show": lit("true"), "color": color(border), "radius": lit(f"{radius:.1f}D"), "width": lit("0.9D")}}],
        "dropShadow": [{"properties": {"show": lit("true" if shadow else "false"), "color": color("#000000"), "transparency": lit("84.0D"), "angle": lit("45.0D"), "distance": lit("1.5D")}}],
        "title": [{"properties": {"show": lit("false")}}],
        "visualHeader": [{"properties": {"show": lit("false")}}],
    }


def measure_format(field: str) -> str:
    for item in measure_catalog():
        if item["measure_name"] == field:
            return item.get("format_string", "")
    return ""


def chart_display_units(fields: list[tuple[str, str, str, str]]) -> str:
    has_currency = any("$" in measure_format(field) for table, field, role, _ in fields if role == "measure")
    return "1000000D" if has_currency else "0D"


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


def image_table_objects(image_w: int, image_h: int, backing: str | None = None) -> dict:
    backing = backing or THEME["bg"]
    return {
        "grid": [{"properties": {"gridHorizontal": lit("false"), "gridVertical": lit("false"), "outlineColor": color(backing), "outlineWeight": lit("0D"), "rowPadding": lit("0D"), "imageHeight": lit(f"{image_h}D"), "imageWidth": lit(f"{image_w}D")}}],
        "columnHeaders": [{"properties": {"show": lit("false"), "fontSize": lit("1D"), "fontColor": color(backing), "backColor": color(backing), "outlineColor": color(backing), "wordWrap": lit("false"), "autoSizeColumnWidth": lit("false"), "alignment": prop_text("center")}}],
        "values": [{"properties": {"urlIcon": lit("false"), "fontSize": lit("1D"), "fontFamily": prop_text("Segoe UI"), "fontColor": color(backing), "backColor": color(backing), "backColorPrimary": color(backing), "backColorSecondary": color(backing), "imageHeight": lit(f"{image_h}D"), "imageWidth": lit(f"{image_w}D"), "wordWrap": lit("false"), "alignment": prop_text("center")}}],
        "imageSize": [{"properties": {"height": lit(f"{image_h}D"), "width": lit(f"{image_w}D")}}],
        "total": [{"properties": {"show": lit("false")}}],
    }


def slicer_objects(title: str, single_select: bool = False) -> dict:
    return {
        "data": [{"properties": {"mode": prop_text("Dropdown")}}],
        "general": [{"properties": {"orientation": lit("0D")}}],
        "selection": [{"properties": {"selectAllCheckboxEnabled": lit("true"), "singleSelect": lit("true" if single_select else "false")}}],
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


def value_card(
    measure: str,
    title: str,
    x,
    y,
    w,
    h,
    z,
    font_size: float = 18.5,
    accent_override: str | None = None,
    background_override: str | None = None,
) -> dict:
    visual = data_visual("cardVisual", x, y, w, h, z, {"Data": [("KPI Measures", measure, "measure", title)]}, "")
    cfg = json.loads(visual["config"])
    metadata = f"KPI Measures.{measure}"
    cfg["singleVisual"]["objects"] = {
        "layout": [{"properties": {"backgroundShow": lit("true" if background_override else "false"), "rectangleRoundedCurve": lit("0L"), "cellPadding": lit("0D"), "paddingUniform": lit("0D")}, "selector": {"id": "default"}}],
        "value": [{"properties": {"fontSize": lit(f"{font_size:.1f}D"), "fontFamily": lit("'Segoe UI Semibold'"), "fontColor": color(accent_override or title_accent(title))}, "selector": {"metadata": metadata}}],
        "label": [{"properties": {"show": lit("false")}, "selector": {"metadata": metadata}}],
        "spacing": [{"properties": {"verticalSpacing": lit("0D")}, "selector": {"id": "default"}}],
        "fillCustom": [{"properties": {"show": lit("true" if background_override else "false"), **({"transparency": lit("0D"), "color": color(background_override), "fill": color(background_override), "fillColor": color(background_override)} if background_override else {})}, "selector": {"id": "default"}}],
        "outline": [{"properties": {"show": lit("false")}, "selector": {"id": "default"}}],
        "divider": [{"properties": {"show": lit("false")}, "selector": {"metadata": metadata}}],
        "referenceLabelDetail": [{"properties": {"show": lit("false")}, "selector": {"metadata": metadata}}],
    }
    cfg["singleVisual"]["vcObjects"] = visual_shell_hidden()
    if background_override:
        cfg["singleVisual"]["vcObjects"]["background"] = [{"properties": {"show": lit("true"), "color": color(background_override), "transparency": lit("0D")}}]
    visual["config"] = json.dumps(cfg, separators=(",", ":"), ensure_ascii=False)
    return visual


def mini_sparkline(measure: str, x, y, w, h, z, accent: str | None = None) -> dict:
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
    sv["objects"].setdefault("markers", [{"properties": {}}])[0]["properties"].update({"show": lit("true"), "markerSize": lit("3D")})
    sv["objects"]["dataPoint"] = [{"properties": {"fill": color(accent or title_accent(measure))}, "selector": {"metadata": f"KPI Measures.{measure}"}}]
    visual["config"] = json.dumps(cfg, separators=(",", ":"), ensure_ascii=False)
    return visual


def sparkline_glyph(x, y, z, accent: str, w: int = 106, h: int = 42) -> list[dict]:
    levels = [0.74, 0.62, 0.66, 0.50, 0.58, 0.34, 0.42, 0.20]
    bright = {
        THEME["blue"]: "#6F8FE0",
        THEME["teal"]: "#6CA9AE",
        THEME["green"]: "#A5B967",
        THEME["rose"]: "#D47C94",
        THEME["gold"]: "#D9BE70",
    }.get(accent, accent)
    step = (w - 10) / (len(levels) - 1)
    line_h = 9
    line_color = bright
    visuals = [
        shape(round(x), round(y + h - 9), round(w), 2, z, "#3A4655"),
    ]
    order = 1
    for idx in range(len(levels) - 1):
        x1 = round(x + 5 + idx * step)
        x2 = round(x + 5 + (idx + 1) * step)
        y1 = round(y + 4 + levels[idx] * (h - 16))
        y2 = round(y + 4 + levels[idx + 1] * (h - 16))
        visuals.append(shape(x1, y1, max(8, x2 - x1), line_h, z + order, line_color))
        order += 1
        connector_y = min(y1, y2)
        visuals.append(shape(x2 - 4, connector_y, 8, max(line_h, abs(y2 - y1) + line_h), z + order, line_color))
        order += 1
    visuals.append(shape(round(x + w - 12), round(y + 4 + levels[-1] * (h - 16) - 5), 11, 11, z + order, bright))
    return visuals


def kpi_native_spec(measure: str, title: str) -> dict:
    specs = {
        "Actual Revenue": {
            "display": "Display Actual Revenue",
            "py": "Display Revenue PY",
            "delta": "Display Revenue Var %",
            "accent": THEME["blue"],
            "status": "ON TRACK",
        },
        "Actual EBITDA": {
            "display": "Display Actual EBITDA",
            "py": "Display EBITDA PY",
            "delta": "Display EBITDA Var %",
            "accent": THEME["teal"],
            "status": "ACTION",
        },
        "EBITDA Margin %": {
            "display": "Display EBITDA Margin %",
            "py": "Gross Margin PY %",
            "delta": "Display EBITDA Var %",
            "accent": THEME["green"],
            "status": "WATCH",
        },
        "Open Exception Value": {
            "display": "Display Open Exception Value",
            "py": "Display Open Exception Value PY",
            "delta": "Display Open Exception Count",
            "accent": THEME["rose"],
            "status": "WATCH",
        },
        "Gross Revenue": {
            "display": "Display Gross Revenue",
            "py": "Display Revenue PY",
            "delta": "Display Revenue Var %",
            "accent": THEME["blue"],
            "status": "ON TRACK",
        },
        "Gross Profit": {
            "display": "Display Gross Profit",
            "py": "Display EBITDA PY",
            "delta": "Display EBITDA Var %",
            "accent": THEME["teal"],
            "status": "WATCH",
        },
        "OPEX": {
            "display": "Display OPEX",
            "py": "Display EBITDA PY",
            "delta": "Display EBITDA Var %",
            "accent": THEME["rose"],
            "status": "ACTION",
        },
        "Net Income": {
            "display": "Display Net Income",
            "py": "Display EBITDA PY",
            "delta": "Display EBITDA Var %",
            "accent": THEME["green"],
            "status": "WATCH",
        },
        "Intercompany Revenue": {
            "display": "Display Intercompany Revenue",
            "py": "Display Revenue PY",
            "delta": "Display Revenue Var %",
            "accent": THEME["blue"],
            "status": "WATCH",
        },
        "Intercompany Elimination": {
            "display": "Display Intercompany Elimination",
            "py": "Display EBITDA PY",
            "delta": "Display EBITDA Var %",
            "accent": THEME["teal"],
            "status": "WATCH",
        },
        "Forecast Accuracy %": {
            "display": "Display Forecast Accuracy %",
            "py": "Latest Forecast Accuracy %",
            "delta": "Display Forecast Accuracy Delta",
            "accent": THEME["gold"],
            "status": "ON TRACK",
        },
    }
    return specs.get(measure, {"display": measure, "py": measure, "delta": measure, "accent": title_accent(title), "status": "WATCH"})


def kpi_svg_measure_name(measure: str) -> str:
    mapping = {
        "Actual Revenue": "Revenue KPI Card SVG",
        "Actual EBITDA": "EBITDA KPI Card SVG",
        "EBITDA Margin %": "Margin KPI Card SVG",
        "Open Exception Value": "Close Exceptions KPI Card SVG",
        "Gross Revenue": "Gross Revenue KPI Card SVG",
        "Gross Profit": "Gross Profit KPI Card SVG",
        "OPEX": "OPEX KPI Card SVG",
        "Net Income": "Net Income KPI Card SVG",
        "Intercompany Revenue": "IC Revenue KPI Card SVG",
        "Intercompany Elimination": "Intercompany Elimination KPI Card SVG",
        "Forecast Accuracy %": "Forecast Accuracy KPI Card SVG",
    }
    return mapping.get(measure, measure)


def native_kpi_card(measure: str, title: str, x, y, z, w: int = 296, h: int = 135) -> list[dict]:
    _ = title
    return [
        svg_image_visual(
            kpi_svg_measure_name(measure),
            x,
            y,
            w,
            h,
            z,
            "#242B35",
            shell_radius=10.5,
            shell=False,
        )
    ]


def decision_panel(title: str, lines: list[str], x, y, z, w: int = 536, h: int = 68) -> list[dict]:
    accent = title_accent(title)
    is_tall = h > 100
    title_size = 8.4 if is_tall else 7.4
    title_y = y + (12 if is_tall else 8)
    line_y = y + (44 if is_tall else 26)
    line_gap = 38 if is_tall else 16
    line_h = 30 if is_tall else 15
    line_size = 8.2 if is_tall else 7.2
    visuals = [
        shape(x, y, w, h, z, THEME["ink"]),
        shape(x, y, 4, h, z + 1, accent),
        text_box(title.upper(), x + 16, title_y, w - 32, 24, z + 2, title_size, accent, False),
    ]
    for idx, line in enumerate(lines[:3]):
        visuals.append(text_box(line, x + 16, line_y + idx * line_gap, w - 32, line_h, z + 3 + idx, line_size, "#FFFFFF" if idx == 0 else "#D8E0EA", idx == 0))
    return visuals


def native_current_lens(x, y, z, w: int = 568, h: int = 78) -> list[dict]:
    return [
        svg_image_visual(
            "Lens Summary SVG",
            x,
            y,
            w,
            h,
            z,
            "#242B35",
            shell_radius=10.5,
        )
    ]


def slicer(table: str, field: str, title: str, x, y, w, h, z) -> dict:
    return data_visual("slicer", x, y, w, h, z, {"Values": [(table, field, "column", title)]}, title)


def svg_image_visual(measure: str, x, y, w, h, z, backing: str = "#242B35", shell_radius: float = 10.0, shell: bool = True) -> dict:
    cfg = {
        "name": rand_name(),
        "layouts": [{"id": 0, "position": pos(x, y, w, h, z)}],
        "singleVisual": {
            "visualType": "image",
            "drillFilterOtherVisuals": True,
            "objects": {
                "image": [{
                    "properties": {
                        "sourceType": prop_text("imageData"),
                        "transparency": lit("0D"),
                        "sourceField": {
                            "expr": {
                                "Measure": {
                                    "Expression": {"SourceRef": {"Entity": "KPI Measures"}},
                                    "Property": measure,
                                }
                            }
                        },
                        "effects": lit("false"),
                    }
                }]
            },
            "vcObjects": svg_card_shell(backing, "#3A4655", shell_radius, True) if shell else visual_shell_hidden(),
        },
    }
    return outer(cfg, x, y, w, h, z)


def image_measure(
    measure: str,
    title: str,
    x,
    y,
    w,
    h,
    z,
    image_w: int | None = None,
    image_h: int | None = None,
    backing: str | None = None,
    display_alias: str = " ",
    shell: bool = True,
    shell_radius: float = 10.0,
) -> dict:
    image_w = int(image_w or w)
    image_h = int(image_h or h)
    visual = data_visual("tableEx", x, y, w, h, z, {"Values": [("KPI Measures", measure, "measure", display_alias)]}, display_alias)
    cfg = json.loads(visual["config"])
    qref = f"KPI Measures.{measure}"
    cfg["singleVisual"]["objects"] = image_table_objects(image_w, image_h, backing)
    cfg["singleVisual"]["objects"]["columnWidth"] = [{"properties": {"value": lit(f"{float(image_w):.1f}D")}, "selector": {"metadata": qref}}]
    cfg["singleVisual"]["columnProperties"] = {qref: {"displayName": display_alias}}
    cfg["singleVisual"]["vcObjects"] = svg_card_shell(backing or "#242B35", "#3A4655", shell_radius, True) if shell else visual_shell_hidden()
    visual["config"] = json.dumps(cfg, separators=(",", ":"), ensure_ascii=False)
    return visual


def kpi_card(measure: str, title: str, x, y, z) -> dict:
    return image_measure(measure, title, x, y, 308, 166, z, 300, 146, "#242B35")


def metric_chip(label: str, value: str, title: str, x, y, w, h, z, accent: str) -> list[dict]:
    return [
        shape(x, y, w, h, z, "#F8FAFC"),
        shape(x, y, 4, h, z + 1, accent),
        text_box(label, x + 14, y + 5, w - 28, 13, z + 2, 6.6, THEME["muted"], False),
        text_box(value, x + 14, y + 18, w - 28, 14, z + 3, 7.6, accent, True),
    ]


def decision_chip_panel(title: str, chips: list[tuple[str, str, str]], x, y, z, w: int = 610, h: int = 70) -> list[dict]:
    accent = title_accent(title)
    summary = "  |  ".join(f"{label}: {value}" for label, value, _metric_title in chips[:3])
    visuals = [
        shape(x, y, w, h, z, THEME["panel"]),
        shape(x, y, 4, h, z + 1, accent),
        text_box(title.upper(), x + 16, y + 10, w - 32, 22, z + 2, 8.0, accent, False),
        text_box(summary, x + 16, y + 36, w - 32, 24, z + 3, 7.8, "#FFFFFF", True),
    ]
    return visuals


def panel_box(x, y, w, h, z, fill: str, border: str = "#3A4655", radius: float = 8.0, shadow: bool = False) -> dict:
    cfg = {
        "name": rand_name(),
        "layouts": [{"id": 0, "position": pos(x, y, w, h, z)}],
        "singleVisual": {
            "visualType": "textbox",
            "drillFilterOtherVisuals": True,
            "vcObjects": {
                "background": [{"properties": {"show": lit("true"), "color": color(fill), "transparency": lit("0D")}}],
                "border": [{"properties": {"show": lit("true"), "color": color(border), "radius": lit(f"{radius:.1f}D"), "width": lit("0.75D")}}],
                "dropShadow": [{"properties": {"show": lit("true" if shadow else "false"), "color": color("#000000"), "transparency": lit("85.0D"), "angle": lit("45.0D"), "distance": lit("1.0D")}}],
                "title": [{"properties": {"show": lit("false")}}],
                "visualHeader": [{"properties": {"show": lit("false")}}],
            },
            "objects": {
                "general": [{
                    "properties": {
                        "paragraphs": [{
                            "textRuns": [{
                                "value": " ",
                                "textStyle": {
                                    "fontFamily": "Segoe UI",
                                    "fontSize": "1pt",
                                    "color": fill,
                                },
                            }]
                        }]
                    }
                }]
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
            "vcObjects": {
                "visualHeader": [{"properties": {"show": lit("false")}}],
            },
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
            "visualType": "basicShape",
            "drillFilterOtherVisuals": True,
            "vcObjects": {
                "visualHeader": [{"properties": {"show": lit("false")}}],
            },
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
        text_box(subtitle, 575, 30, 610, 36, 40, 8, THEME["muted"], False),
        shape(24, 72, 1232, 2, 50, THEME["border"]),
    ]


def top_filter_bar(filters: list[tuple[str, str, str, int]], start_x: int = 174) -> list[dict]:
    dark_bar = "#242B35"
    visuals = [
        shape(24, 78, 1232, 78, 60, dark_bar),
        shape(24, 78, 5, 78, 65, THEME["gold"]),
        text_box("FILTER LENS", 38, 96, 112, 38, 70, 8.0, "#D0B16A", False),
    ]
    x = start_x
    for idx, (table, field, title, width) in enumerate(filters):
        visuals.append(slicer(table, field, title, x, 84, width, 58, 100 + idx * 10))
        x += width + 12
    visuals.extend(native_current_lens(672, 78, 180, 568, 78))
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
        *native_kpi_card("Actual Revenue", "Revenue", 24, 178, 200),
        *native_kpi_card("Actual EBITDA", "EBITDA", 336, 178, 210),
        *native_kpi_card("EBITDA Margin %", "Margin", 648, 178, 220),
        *native_kpi_card("Open Exception Value", "Close Risk", 960, 178, 230),
        data_visual(
            "lineClusteredColumnComboChart",
            24,
            334,
            610,
            176,
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
            334,
            610,
            176,
            310,
            {
                "Category": [("FactVarianceDriverBridge", "driver", "column", "Driver")],
                "Y": [("KPI Measures", "Latest Bridge Amount", "measure", "Amount")],
            },
            "EBITDA Driver Bridge",
            "Actual vs budget bridge by variance driver",
        ),
        data_visual(
            "columnChart",
            24,
            528,
            438,
            158,
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
            528,
            350,
            158,
            330,
            {
                "Category": [("DimBusinessUnit", "business_unit", "column", "BU")],
                "Y": [("KPI Measures", "Actual Revenue", "measure", "Revenue")],
            },
            "BU Revenue Mix",
            "Business-unit contribution",
        ),
        *decision_panel(
            "Management Attention List",
            [
                "1. Indonesia margin reset: regional owner action.",
                "2. Close risk: controller follow-up before board pack.",
                "3. Bridge levers: price/yield, volume, productivity.",
            ],
            836,
            528,
            340,
            420,
            158,
        ),
    ]

    p2 = header("P&L Variance", "Statement view by entity, scenario, business unit, and variance")
    p2 += top_filter_bar([
        ("DimEntity", "country", "Country", 180),
        ("DimScenario", "scenario", "Scenario", 180),
    ])
    p2 += [
        *native_kpi_card("Gross Revenue", "Gross Revenue", 24, 178, 200),
        *native_kpi_card("Gross Profit", "Gross Profit", 336, 178, 210),
        *native_kpi_card("OPEX", "OPEX", 648, 178, 220),
        *native_kpi_card("Net Income", "Net Income", 960, 178, 230),
        data_visual(
            "barChart",
            24,
            334,
            610,
            352,
            300,
            {
                "Category": [("DimAccount", "account_group", "column", "Group")],
                "Y": [("KPI Measures", "Financial Amount", "measure", "Amount")],
            },
            "P&L Statement by Account Group",
            "Scenario-filtered account movement",
        ),
        data_visual(
            "columnChart",
            646,
            334,
            300,
            174,
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
            334,
            298,
            174,
            320,
            {
                "Category": [("DimBusinessUnit", "business_unit", "column", "BU")],
                "Y": [("KPI Measures", "Actual Revenue", "measure", "Revenue")],
            },
            "Revenue Mix by BU",
        ),
        data_visual(
            "columnChart",
            646,
            516,
            610,
            176,
            330,
            {
                "Category": [("DimEntity", "country", "column", "Country")],
                "Y": [("KPI Measures", "EBITDA Var vs Budget", "measure", "EBITDA Var")],
            },
            "Country Variance by EBITDA",
        ),
    ]

    p3 = header("Controls & Storyboard", "FX, intercompany, close exceptions, and board-ready narrative")
    p3 += top_filter_bar([
        ("FactFXRate", "currency", "Currency", 154),
        ("FactCloseExceptions", "severity", "Severity", 154),
        ("FactCloseExceptions", "status", "Status", 154),
    ])
    p3 += [
        *native_kpi_card("Intercompany Revenue", "IC Revenue", 24, 178, 200),
        *native_kpi_card("Intercompany Elimination", "IC Elimination", 336, 178, 210),
        *native_kpi_card("Open Exception Value", "Close Risk", 648, 178, 220),
        *native_kpi_card("Forecast Accuracy %", "Forecast Accuracy", 960, 178, 230),
        data_visual(
            "columnChart",
            24,
            334,
            390,
            176,
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
            334,
            390,
            176,
            310,
            {
                "Category": [("FactCloseExceptions", "status", "column", "Status")],
                "Y": [("KPI Measures", "Exception Amount", "measure", "Amount")],
            },
            "Exception Value by Status",
        ),
        data_visual(
            "waterfallChart",
            828,
            334,
            428,
            176,
            320,
            {
                "Category": [("FactVarianceDriverBridge", "driver", "column", "Driver")],
                "Y": [("KPI Measures", "Latest Bridge Amount", "measure", "Amount")],
            },
            "Board EBITDA Walk",
            "Variance bridge for the selected scope",
        ),
        data_visual(
            "columnChart",
            24,
            528,
            610,
            158,
            330,
            {
                "Category": [("FactCloseExceptions", "owner_team", "column", "Owner")],
                "Y": [("KPI Measures", "Exception Amount", "measure", "Amount")],
            },
            "Close Exception Exposure by Owner",
        ),
        data_visual(
            "columnChart",
            646,
            528,
            610,
            158,
            340,
            {
                "Category": [("DimEntity", "country", "column", "Country")],
                "Y": [("KPI Measures", "Actual EBITDA", "measure", "EBITDA")],
            },
            "Board Pack EBITDA by Country",
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
  $pbiTools = (Get-Command pbi-tools -ErrorAction Stop).Source
  $infoText = & $pbiTools info 2>&1 | Out-String
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
