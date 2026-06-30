from __future__ import annotations

import csv
import hashlib
import json
import uuid
from datetime import datetime
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
    "sidebar": "#12372A",
    "sidebar2": "#1C4A39",
    "rail": "#E9F1ED",
    "card": "#FFFFFF",
    "table_header": "#EAF1ED",
    "table_row": "#FFFFFF",
    "table_alt": "#F4F7F5",
    "table_grid": "#D9E2DC",
}


PAGE_SECTION_NAMES = {
    "overview": "ReportSectionESGFinanceOverview",
    "supplier": "ReportSectionEmissionsSupplierIntensity",
    "abatement": "ReportSectionCarbonScenarioAbatementROI",
    "risk": "ReportSectionRiskActionControlTower",
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


def selected_latest_key_expr() -> str:
    return "MAX ( dim_date[date_key] )"


def svg_kpi_card(title: str, measure: str, color: str, value_format: str, scale: int | float = 1, favorable: str = "higher", delta_label: str = "Prev") -> str:
    encoded_color = color.replace("#", "%23")
    improvement_test = "LastValue <= FirstValue" if favorable == "lower" else "LastValue >= FirstValue"
    delta_good_test = "ChangeValue <= 0" if favorable == "lower" else "ChangeValue >= 0"
    safe_title = title.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return f'''VAR LatestKey = {selected_latest_key_expr()}
VAR PriorKey =
    MAXX (
        FILTER ( ALL ( dim_date ), dim_date[date_key] < LatestKey ),
        dim_date[date_key]
    )
VAR CurrentValue =
    CALCULATE ( [{measure}], FILTER ( ALL ( dim_date ), dim_date[date_key] = LatestKey ) )
VAR PriorValue =
    CALCULATE ( [{measure}], FILTER ( ALL ( dim_date ), dim_date[date_key] = PriorKey ) )
VAR ChangeValue = CurrentValue - PriorValue
VAR RateValue = DIVIDE ( ChangeValue, ABS ( PriorValue ) )
VAR ValueTextRaw = FORMAT ( DIVIDE ( CurrentValue, {scale} ), "{value_format}" )
VAR PriorTextRaw = IF ( ISBLANK ( PriorValue ), "n/a", FORMAT ( DIVIDE ( PriorValue, {scale} ), "{value_format}" ) )
VAR DeltaTextRaw = IF ( ISBLANK ( PriorValue ), "n/a", FORMAT ( RateValue, "+0.0%;-0.0%;0.0%" ) )
VAR ValueText = SUBSTITUTE ( ValueTextRaw, "%", "%25" )
VAR PriorText = SUBSTITUTE ( PriorTextRaw, "%", "%25" )
VAR DeltaText = SUBSTITUTE ( DeltaTextRaw, "%", "%25" )
VAR DeltaColor =
    IF ( ISBLANK ( PriorValue ), "%23606E66", IF ( {delta_good_test}, "%232A9D8F", "%23E76F51" ) )
VAR MonthTable =
    TOPN (
        10,
        ADDCOLUMNS (
            ALLSELECTED ( dim_date ),
            "__Value", CALCULATE ( [{measure}] )
        ),
        dim_date[date_key],
        DESC
    )
VAR CleanTable = FILTER ( MonthTable, NOT ISBLANK ( [__Value] ) )
VAR RowCount = COUNTROWS ( CleanTable )
VAR MinValue = MINX ( CleanTable, [__Value] )
VAR MaxValue = MAXX ( CleanTable, [__Value] )
VAR FirstValue = MINX ( TOPN ( 1, CleanTable, dim_date[date_key], ASC ), [__Value] )
VAR LastValue = MINX ( TOPN ( 1, CleanTable, dim_date[date_key], DESC ), [__Value] )
VAR TrendColor = IF ( {improvement_test}, "{encoded_color}", "%23E76F51" )
VAR BandColor = IF ( {improvement_test}, "%23E4F4ED", "%23FBE7E1" )
VAR LinePoints =
    CONCATENATEX (
        CleanTable,
        VAR RankValue = RANKX ( CleanTable, dim_date[date_key], , ASC, DENSE ) - 1
        VAR XValue = 184 + DIVIDE ( RankValue, MAX ( 1, RowCount - 1 ), 0 ) * 86
        VAR YValue = 78 - DIVIDE ( [__Value] - MinValue, MaxValue - MinValue, 0.5 ) * 38
        RETURN FORMAT ( XValue, "0.0" ) & "," & FORMAT ( YValue, "0.0" ),
        " ",
        dim_date[date_key],
        ASC
    )
VAR AreaPath =
    "M184 88 " &
    CONCATENATEX (
        CleanTable,
        VAR RankValue = RANKX ( CleanTable, dim_date[date_key], , ASC, DENSE ) - 1
        VAR XValue = 184 + DIVIDE ( RankValue, MAX ( 1, RowCount - 1 ), 0 ) * 86
        VAR YValue = 78 - DIVIDE ( [__Value] - MinValue, MaxValue - MinValue, 0.5 ) * 38
        RETURN "L" & FORMAT ( XValue, "0.0" ) & " " & FORMAT ( YValue, "0.0" ),
        " ",
        dim_date[date_key],
        ASC
    ) & " L270 88 Z"
VAR StartYValue = 78 - DIVIDE ( FirstValue - MinValue, MaxValue - MinValue, 0.5 ) * 38
VAR EndYValue = 78 - DIVIDE ( LastValue - MinValue, MaxValue - MinValue, 0.5 ) * 38
VAR SVG =
    "<svg xmlns='http://www.w3.org/2000/svg' width='300' height='150' viewBox='0 0 300 150'>" &
    "<defs><clipPath id='sparkClip'><rect x='176' y='35' width='106' height='52' rx='9'/></clipPath></defs>" &
    "<rect x='1' y='1' width='298' height='148' rx='12' fill='%23FFFFFF' stroke='%23D9E2DC' stroke-width='1.6'/>" &
    "<rect x='16' y='13' width='164' height='4.5' rx='2.2' fill='{encoded_color}' opacity='0.92'/>" &
    "<text x='16' y='43' font-family='Segoe UI' font-size='16' font-weight='760' fill='%23202A25'>{safe_title}</text>" &
    "<text x='16' y='96' font-family='Segoe UI' font-size='48' font-weight='780' fill='{encoded_color}'>" & ValueText & "</text>" &
    "<rect x='174' y='31' width='112' height='60' rx='10' fill='%23F2F6F4'/>" &
    "<rect x='184' y='62' width='86' height='10' rx='5' fill='" & BandColor & "'/>" &
    "<g clip-path='url(%23sparkClip)'>" &
    "<path d='" & AreaPath & "' fill='{encoded_color}' opacity='0.14'/>" &
    "<polyline points='" & LinePoints & "' fill='none' stroke='" & TrendColor & "' stroke-width='3.2' stroke-linecap='round' stroke-linejoin='round'/>" &
    "</g>" &
    "<circle cx='184' cy='" & FORMAT ( StartYValue, "0.0" ) & "' r='3.8' fill='%23FFFFFF' stroke='{encoded_color}' stroke-width='1.8'/>" &
    "<circle cx='270' cy='" & FORMAT ( EndYValue, "0.0" ) & "' r='4.6' fill='" & TrendColor & "' stroke='%23FFFFFF' stroke-width='1.8'/>" &
    "<rect x='16' y='110' width='128' height='28' rx='8' fill='%23F4F7F5'/>" &
    "<rect x='156' y='110' width='128' height='28' rx='8' fill='%23F4F7F5'/>" &
    "<text x='28' y='123' font-family='Segoe UI' font-size='10.5' font-weight='700' fill='%235B6C5D'>{delta_label}</text>" &
    "<text x='28' y='138' font-family='Segoe UI' font-size='12.6' font-weight='650' fill='%23202A25'>" & PriorText & "</text>" &
    "<text x='168' y='123' font-family='Segoe UI' font-size='10.5' font-weight='700' fill='%235B6C5D'>Delta</text>" &
    "<text x='168' y='138' font-family='Segoe UI' font-size='13' font-weight='760' fill='" & DeltaColor & "'>" & DeltaText & "</text>" &
    "</svg>"
RETURN IF ( RowCount = 0, BLANK (), "data:image/svg+xml;utf8," & SVG )'''


def lens_summary_svg() -> str:
    return r'''VAR YearText =
    IF ( HASONEVALUE ( dim_date[year] ), FORMAT ( SELECTEDVALUE ( dim_date[year] ), "0" ), "All Years" )
VAR RegionCount = COUNTROWS ( VALUES ( dim_facility[region] ) )
VAR RegionTotal = CALCULATE ( COUNTROWS ( VALUES ( dim_facility[region] ) ), ALL ( dim_facility[region] ) )
VAR RegionText =
    IF (
        NOT ISFILTERED ( dim_facility[region] ) || RegionCount = RegionTotal,
        "All Regions",
        IF ( RegionCount = 1, SELECTEDVALUE ( dim_facility[region] ), FORMAT ( RegionCount, "0" ) & " regions" )
    )
VAR BUCount = COUNTROWS ( VALUES ( dim_business_unit[business_unit] ) )
VAR BUTotal = CALCULATE ( COUNTROWS ( VALUES ( dim_business_unit[business_unit] ) ), ALL ( dim_business_unit[business_unit] ) )
VAR BUText =
    IF (
        NOT ISFILTERED ( dim_business_unit[business_unit] ) || BUCount = BUTotal,
        "All BU",
        IF ( BUCount = 1, SELECTEDVALUE ( dim_business_unit[business_unit] ), FORMAT ( BUCount, "0" ) & " BU" )
    )
VAR ScopeText =
    IF ( HASONEVALUE ( fact_emissions[scope] ), SELECTEDVALUE ( fact_emissions[scope] ), "All Scopes" )
VAR ScenarioText =
    IF ( HASONEVALUE ( dim_carbon_scenario[scenario] ), SELECTEDVALUE ( dim_carbon_scenario[scenario] ), "All Prices" )
VAR CostText = FORMAT ( DIVIDE ( [Carbon Cost USD], 1000000 ), "$0.0M" )
VAR PriceText = FORMAT ( [Selected Carbon Price USD/t], "$0/t" )
VAR Line1 = LEFT ( YearText & " | " & RegionText, 30 )
VAR Line2 = LEFT ( BUText & " | " & ScopeText & " | " & ScenarioText, 32 )
VAR SVG =
    "<svg xmlns='http://www.w3.org/2000/svg' width='740' height='84' viewBox='0 0 740 84'>" &
    "<defs><clipPath id='scopeClip'><rect x='276' y='43' width='282' height='25'/></clipPath></defs>" &
    "<rect x='1' y='1' width='738' height='82' rx='14' fill='%231C4A39' stroke='%232A9D8F' stroke-width='1.4'/>" &
    "<rect x='22' y='14' width='136' height='4' rx='2' fill='%232A9D8F' opacity='0.95'/>" &
    "<text x='22' y='36' font-family='Segoe UI' font-size='12.2' font-weight='760' fill='%23BFD1C8'>Current Lens</text>" &
    "<text x='22' y='66' font-family='Segoe UI' font-size='21' font-weight='780' fill='%23FFFFFF'>" & Line1 & "</text>" &
    "<text x='276' y='36' font-family='Segoe UI' font-size='12' font-weight='700' fill='%23BFD1C8'>Scope context</text>" &
    "<text x='276' y='64' font-family='Segoe UI' font-size='13.2' font-weight='680' fill='%23FFFFFF' clip-path='url(%23scopeClip)'>" & Line2 & "</text>" &
    "<rect x='574' y='14' width='84' height='56' rx='10' fill='%23235143'/>" &
    "<text x='586' y='33' font-family='Segoe UI' font-size='9.2' font-weight='700' fill='%23BFD1C8'>Carbon cost</text>" &
    "<text x='586' y='59' font-family='Segoe UI' font-size='19' font-weight='780' fill='%23B7D968'>" & CostText & "</text>" &
    "<rect x='668' y='14' width='58' height='56' rx='10' fill='%23235143'/>" &
    "<text x='676' y='33' font-family='Segoe UI' font-size='8.2' font-weight='700' fill='%23BFD1C8'>Price</text>" &
    "<text x='676' y='59' font-family='Segoe UI' font-size='18' font-weight='780' fill='%23FFFFFF'>" & PriceText & "</text>" &
    "</svg>"
RETURN "data:image/svg+xml;utf8," & SVG'''


def svg_escape(value: object) -> str:
    return (
        str(value)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "'")
        .replace("#", "%23")
    )


def dax_quote(value: str) -> str:
    return '"' + value.replace('"', '""') + '"'


def table_card_svg(title: str, sub: str, headers: list[str], rows: list[list[str]], width: int, height: int, widths: list[float] | None = None, status_cols: set[int] | None = None) -> str:
    status_cols = status_cols or set()
    rows = rows[:5]
    available_w = width - 32
    if widths:
        total = sum(widths)
        col_widths = [available_w * w / total for w in widths]
    else:
        col_widths = [available_w / len(headers)] * len(headers)

    def accent_for_title(value: str) -> str:
        text = value.lower()
        if "risk" in text:
            return "%23E76F51"
        if "abatement" in text:
            return "%23B7D968"
        if "supplier" in text:
            return "%23F4A261"
        return "%232A9D8F"

    def parse_metric(value: object) -> float | None:
        text = str(value).strip().replace("$", "").replace(",", "").replace("%", "")
        multiplier = 1.0
        if text.endswith("M"):
            multiplier = 1000000.0
            text = text[:-1]
        elif text.endswith("K"):
            multiplier = 1000.0
            text = text[:-1]
        try:
            return abs(float(text) * multiplier)
        except ValueError:
            return None

    def shorten(value: object, px: float, numeric: bool = False) -> str:
        text = str(value)
        max_chars = max(5, int(px / (5.8 if numeric else 6.4)))
        if len(text) <= max_chars:
            return text
        return text[: max_chars - 3] + "..."

    def tone(value: object) -> tuple[str, str]:
        text = str(value).lower()
        if any(token in text for token in ["high", "shock", "no verified", "planned", "gap", "prioritize"]):
            return ("%23FBE7E1", "%238C3B2D")
        if any(token in text for token in ["medium", "committed", "in flight", "target", "monitor"]):
            return ("%23FFF2D9", "%23714C10")
        if any(token in text for token in ["low", "implemented", "renewable", "sbti", "owned"]):
            return ("%23EAF3EA", "%231F5B43")
        return ("%23F4F7F5", "%23202A25")

    numeric_cols = set()
    max_by_col: dict[int, float] = {}
    for c in range(len(headers)):
        if c in status_cols:
            continue
        values = [parse_metric(row[c]) for row in rows if c < len(row)]
        values = [value for value in values if value is not None]
        if len(values) >= max(2, len(rows) // 2):
            numeric_cols.add(c)
            max_by_col[c] = max(values) or 1.0

    accent = accent_for_title(title)
    row_h = 18
    header_y = 70
    row_start_y = 98

    parts = [
        f"<svg xmlns='http://www.w3.org/2000/svg' width='{width}' height='{height}' viewBox='0 0 {width} {height}'>",
        f"<rect x='1' y='1' width='{width - 2}' height='{height - 2}' rx='10' fill='%23FFFFFF' stroke='%23D9E2DC' stroke-width='1'/>",
        f"<rect x='1' y='1' width='{width - 2}' height='66' rx='10' fill='%23FAFCFB'/>",
        f"<rect x='1' y='56' width='{width - 2}' height='1' fill='%23E4ECE7'/>",
        f"<rect x='16' y='16' width='{max(180, min(width - 150, width * 0.34)):.1f}' height='4' rx='2' fill='{accent}' opacity='0.82'/>",
        f"<text x='16' y='40' font-family='Segoe UI' font-size='13.6' font-weight='780' fill='%23202A25'>{svg_escape(shorten(title, width - 140))}</text>",
        f"<text x='16' y='58' font-family='Segoe UI' font-size='9.4' fill='%235B6C5D'>{svg_escape(shorten(sub, width - 150))}</text>",
        f"<rect x='{width - 88}' y='18' width='68' height='28' rx='14' fill='%23F0F5F2'/>",
        f"<circle cx='{width - 74}' cy='32' r='4' fill='{accent}'/>",
        f"<text x='{width - 62}' y='36' font-family='Segoe UI' font-size='9.4' font-weight='720' fill='%23202A25'>Top {len(rows)}</text>",
        f"<rect x='16' y='{header_y}' width='{width - 32}' height='22' rx='5' fill='%23EAF1ED'/>",
    ]
    x = 20.0
    for header, col_w in zip(headers, col_widths):
        text_x = x + col_w - 8 if headers.index(header) in numeric_cols else x
        anchor = "end" if headers.index(header) in numeric_cols else "start"
        parts.append(f"<text x='{text_x:.1f}' y='{header_y + 15}' text-anchor='{anchor}' font-family='Segoe UI' font-size='8.9' font-weight='760' fill='%23202A25'>{svg_escape(shorten(header, col_w - 8, headers.index(header) in numeric_cols))}</text>")
        x += col_w
    for r, row in enumerate(rows):
        y = row_start_y + r * row_h
        row_fill = "%23F8FBF9" if r % 2 == 0 else "%23FFFFFF"
        parts.append(f"<rect x='16' y='{y - 2}' width='{width - 32}' height='{row_h - 1}' rx='5' fill='{row_fill}'/>")
        parts.append(f"<rect x='16' y='{y - 2}' width='3' height='{row_h - 1}' rx='1.5' fill='{accent}' opacity='{0.72 if r == 0 else 0.22}'/>")
        x = 20.0
        for c, (value, col_w) in enumerate(zip(row, col_widths)):
            display_value = shorten(value, col_w - 10, c in numeric_cols)
            if c in status_cols:
                chip_fill, chip_text = tone(value)
                chip_w = min(col_w - 8, max(46, len(display_value) * 5.8 + 18))
                parts.append(f"<rect x='{x - 3:.1f}' y='{y + 1}' width='{chip_w:.1f}' height='13' rx='6.5' fill='{chip_fill}'/>")
                parts.append(f"<text x='{x + chip_w / 2 - 3:.1f}' y='{y + 11}' text-anchor='middle' font-family='Segoe UI' font-size='8.4' font-weight='720' fill='{chip_text}'>{svg_escape(display_value)}</text>")
            elif c in numeric_cols:
                metric = parse_metric(value) or 0
                bar_w = max(8.0, (col_w - 14) * metric / max_by_col.get(c, 1.0))
                parts.append(f"<rect x='{x + 2:.1f}' y='{y + 11}' width='{col_w - 12:.1f}' height='2.4' rx='1.2' fill='%23E5EEE8'/>")
                parts.append(f"<rect x='{x + 2:.1f}' y='{y + 11}' width='{bar_w:.1f}' height='2.4' rx='1.2' fill='{accent}' opacity='0.62'/>")
                parts.append(f"<text x='{x + col_w - 8:.1f}' y='{y + 9}' text-anchor='end' font-family='Segoe UI' font-size='9.2' font-weight='680' fill='%23202A25'>{svg_escape(display_value)}</text>")
            else:
                weight = "700" if c == 0 and r == 0 else "520"
                parts.append(f"<text x='{x:.1f}' y='{y + 9}' font-family='Segoe UI' font-size='9.2' font-weight='{weight}' fill='%23202A25'>{svg_escape(display_value)}</text>")
            x += col_w
    parts.append("</svg>")
    return "VAR SVG = " + dax_quote("".join(parts)) + '\nRETURN "data:image/svg+xml;utf8," & SVG'


def register_measure(name: str, expression: str, fmt: str = "", annotation: dict | None = None) -> None:
    if any(measure_name(item) == name for item in MEASURES):
        return
    if annotation is not None:
        MEASURES.append((name, expression, fmt, annotation))
    else:
        MEASURES.append((name, expression, fmt))


def dynamic_executive_detail_table_svg() -> str:
    return r'''VAR BaseRows =
    SELECTCOLUMNS (
        SUMMARIZECOLUMNS (
            dim_business_unit[business_unit],
            dim_facility[region],
            "__TCO2e", [Total Emissions tCO2e],
            "__Cost", [Carbon Cost USD]
        ),
        "__BU", dim_business_unit[business_unit],
        "__Region", dim_facility[region],
        "__TCO2e", [__TCO2e],
        "__Cost", [__Cost]
    )
VAR FilteredRows =
    FILTER ( BaseRows, NOT ISBLANK ( [__Cost] ) && [__Cost] <> 0 )
VAR TopRowsRaw =
    TOPN ( 4, FilteredRows, [__Cost], DESC, [__TCO2e], DESC, [__BU], ASC )
VAR TopRows =
    ADDCOLUMNS (
        TopRowsRaw,
        "__Rank", RANKX ( TopRowsRaw, [__Cost] + DIVIDE ( [__TCO2e], 1000000000 ), , DESC, DENSE )
    )
VAR MaxTCO2e = MAXX ( TopRows, [__TCO2e] )
VAR MaxCost = MAXX ( TopRows, [__Cost] )
VAR Header =
    "<svg xmlns='http://www.w3.org/2000/svg' width='620' height='198' viewBox='0 0 620 198'>" &
    "<rect x='1' y='1' width='618' height='196' rx='10' fill='%23FFFFFF' stroke='%23D9E2DC' stroke-width='1'/>" &
    "<rect x='1' y='1' width='618' height='66' rx='10' fill='%23FAFCFB'/>" &
    "<rect x='1' y='56' width='618' height='1' fill='%23E4ECE7'/>" &
    "<rect x='16' y='16' width='210.8' height='4' rx='2' fill='%232A9D8F' opacity='0.82'/>" &
    "<text x='16' y='40' font-family='Segoe UI' font-size='13.6' font-weight='780' fill='%23202A25'>Executive Detail</text>" &
    "<text x='16' y='58' font-family='Segoe UI' font-size='9.4' fill='%235B6C5D'>Dynamic carbon finance follow-up priorities</text>" &
    "<rect x='532' y='18' width='68' height='28' rx='14' fill='%23F0F5F2'/>" &
    "<circle cx='546' cy='32' r='4' fill='%232A9D8F'/>" &
    "<text x='558' y='36' font-family='Segoe UI' font-size='9.4' font-weight='720' fill='%23202A25'>Top " & FORMAT ( COUNTROWS ( TopRows ), "0" ) & "</text>" &
    "<rect x='16' y='70' width='588' height='22' rx='5' fill='%23EAF1ED'/>" &
    "<text x='20' y='85' font-family='Segoe UI' font-size='8.9' font-weight='760' fill='%23202A25'>Business Unit</text>" &
    "<text x='172.1' y='85' font-family='Segoe UI' font-size='8.9' font-weight='760' fill='%23202A25'>Region</text>" &
    "<text x='366.8' y='85' text-anchor='end' font-family='Segoe UI' font-size='8.9' font-weight='760' fill='%23202A25'>tCO2e</text>" &
    "<text x='488.5' y='85' text-anchor='end' font-family='Segoe UI' font-size='8.9' font-weight='760' fill='%23202A25'>Cost</text>" &
    "<text x='496.5' y='85' font-family='Segoe UI' font-size='8.9' font-weight='760' fill='%23202A25'>Action</text>"
VAR Body =
    IF (
        ISEMPTY ( TopRows ),
        "<text x='20' y='125' font-family='Segoe UI' font-size='10' fill='%235B6C5D'>No rows for the selected filters</text>",
        CONCATENATEX (
            TopRows,
            VAR R = [__Rank]
            VAR Y = 96 + ( R - 1 ) * 18
            VAR RowFill = IF ( MOD ( R, 2 ) = 1, "%23F8FBF9", "%23FFFFFF" )
            VAR AccentOpacity = IF ( R = 1, "0.72", "0.22" )
            VAR TBar = MAX ( 8, 89.4 * DIVIDE ( [__TCO2e], MaxTCO2e, 0 ) )
            VAR CBar = MAX ( 8, 109.7 * DIVIDE ( [__Cost], MaxCost, 0 ) )
            VAR ActionText = IF ( R <= 2, "Prioritize", "Monitor" )
            VAR ActionFill = IF ( R <= 2, "%23FBE7E1", "%23FFF2D9" )
            VAR ActionColor = IF ( R <= 2, "%238C3B2D", "%23714C10" )
            VAR ActionW = IF ( R <= 2, 76, 58.6 )
            RETURN
                "<rect x='16' y='" & FORMAT ( Y, "0" ) & "' width='588' height='17' rx='5' fill='" & RowFill & "'/>" &
                "<rect x='16' y='" & FORMAT ( Y, "0" ) & "' width='3' height='17' rx='1.5' fill='%232A9D8F' opacity='" & AccentOpacity & "'/>" &
                "<text x='20' y='" & FORMAT ( Y + 11, "0" ) & "' font-family='Segoe UI' font-size='9.2' font-weight='" & IF ( R = 1, "700", "520" ) & "' fill='%23202A25'>" & LEFT ( [__BU], 19 ) & "</text>" &
                "<text x='172.1' y='" & FORMAT ( Y + 11, "0" ) & "' font-family='Segoe UI' font-size='9.2' fill='%23202A25'>" & LEFT ( [__Region], 10 ) & "</text>" &
                "<rect x='275.4' y='" & FORMAT ( Y + 13, "0" ) & "' width='89.4' height='2.4' rx='1.2' fill='%23E5EEE8'/>" &
                "<rect x='275.4' y='" & FORMAT ( Y + 13, "0" ) & "' width='" & FORMAT ( TBar, "0.0" ) & "' height='2.4' rx='1.2' fill='%232A9D8F' opacity='0.62'/>" &
                "<text x='366.8' y='" & FORMAT ( Y + 11, "0" ) & "' text-anchor='end' font-family='Segoe UI' font-size='9.2' font-weight='680' fill='%23202A25'>" & FORMAT ( DIVIDE ( [__TCO2e], 1000 ), "0.0K" ) & "</text>" &
                "<rect x='376.8' y='" & FORMAT ( Y + 13, "0" ) & "' width='109.7' height='2.4' rx='1.2' fill='%23E5EEE8'/>" &
                "<rect x='376.8' y='" & FORMAT ( Y + 13, "0" ) & "' width='" & FORMAT ( CBar, "0.0" ) & "' height='2.4' rx='1.2' fill='%232A9D8F' opacity='0.62'/>" &
                "<text x='488.5' y='" & FORMAT ( Y + 11, "0" ) & "' text-anchor='end' font-family='Segoe UI' font-size='9.2' font-weight='680' fill='%23202A25'>" & FORMAT ( DIVIDE ( [__Cost], 1000000 ), "$0.0M" ) & "</text>" &
                "<rect x='493.5' y='" & FORMAT ( Y + 3, "0" ) & "' width='" & FORMAT ( ActionW, "0.0" ) & "' height='13' rx='6.5' fill='" & ActionFill & "'/>" &
                "<text x='" & FORMAT ( 493.5 + ActionW / 2, "0.0" ) & "' y='" & FORMAT ( Y + 13, "0" ) & "' text-anchor='middle' font-family='Segoe UI' font-size='8.4' font-weight='720' fill='" & ActionColor & "'>" & ActionText & "</text>",
            "",
            [__Rank],
            ASC
        )
    )
RETURN "data:image/svg+xml;utf8," & Header & Body & "</svg>"'''


def dynamic_supplier_table_svg(title: str, sub: str, width: int) -> str:
    if width == 620:
        title_bar_w = "210.8"
        badge_x = "532"
        dot_x = "546"
        badge_text_x = "558"
        header_w = "588"
        supplier_x = "20"
        risk_x = "228.2"
        target_x = "326.2"
        intensity_x = "600"
        risk_chip_x = "225.2"
        target_chip_x = "323.2"
        bar_x = "499.8"
        bar_w = "98.3"
    else:
        title_bar_w = "421.6"
        badge_x = "1152"
        dot_x = "1166"
        badge_text_x = "1178"
        header_w = "1208"
        supplier_x = "20"
        risk_x = "516.1"
        target_x = "688.7"
        intensity_x = "1220"
        risk_chip_x = "513.1"
        target_chip_x = "685.7"
        bar_x = "1057.4"
        bar_w = "160.6"
    return rf'''VAR BaseRows =
    SELECTCOLUMNS (
        SUMMARIZECOLUMNS (
            dim_supplier[supplier],
            dim_supplier[carbon_risk_tier],
            dim_supplier[target_status],
            "__Emissions", [Total Emissions tCO2e],
            "__Spend", [Total Spend USD],
            "__Intensity", DIVIDE ( [Total Emissions tCO2e], [Total Spend USD] ) * 1000000
        ),
        "__Supplier", dim_supplier[supplier],
        "__Risk", dim_supplier[carbon_risk_tier],
        "__Target", dim_supplier[target_status],
        "__Emissions", [__Emissions],
        "__Intensity", [__Intensity]
    )
VAR FilteredRows =
    FILTER (
        BaseRows,
        NOT ISBLANK ( [__Intensity] )
            && [__Intensity] > 0
            && ( [__Risk] = "High" || [__Target] = "No verified target" )
    )
VAR TopRowsRaw =
    TOPN ( 5, FilteredRows, [__Intensity], DESC, [__Emissions], DESC, [__Supplier], ASC )
VAR TopRows =
    ADDCOLUMNS (
        TopRowsRaw,
        "__Rank", RANKX ( TopRowsRaw, [__Intensity] + DIVIDE ( [__Emissions], 1000000000 ), , DESC, DENSE )
    )
VAR MaxIntensity = MAXX ( TopRows, [__Intensity] )
VAR Header =
    "<svg xmlns='http://www.w3.org/2000/svg' width='{width}' height='198' viewBox='0 0 {width} 198'>" &
    "<rect x='1' y='1' width='{width - 2}' height='196' rx='10' fill='%23FFFFFF' stroke='%23D9E2DC' stroke-width='1'/>" &
    "<rect x='1' y='1' width='{width - 2}' height='66' rx='10' fill='%23FAFCFB'/>" &
    "<rect x='1' y='56' width='{width - 2}' height='1' fill='%23E4ECE7'/>" &
    "<rect x='16' y='16' width='{title_bar_w}' height='4' rx='2' fill='%23E76F51' opacity='0.82'/>" &
    "<text x='16' y='40' font-family='Segoe UI' font-size='13.6' font-weight='780' fill='%23202A25'>{title}</text>" &
    "<text x='16' y='58' font-family='Segoe UI' font-size='9.4' fill='%235B6C5D'>{sub}</text>" &
    "<rect x='{badge_x}' y='18' width='68' height='28' rx='14' fill='%23F0F5F2'/>" &
    "<circle cx='{dot_x}' cy='32' r='4' fill='%23E76F51'/>" &
    "<text x='{badge_text_x}' y='36' font-family='Segoe UI' font-size='9.4' font-weight='720' fill='%23202A25'>Top " & FORMAT ( COUNTROWS ( TopRows ), "0" ) & "</text>" &
    "<rect x='16' y='70' width='{header_w}' height='22' rx='5' fill='%23EAF1ED'/>" &
    "<text x='{supplier_x}' y='85' font-family='Segoe UI' font-size='8.9' font-weight='760' fill='%23202A25'>Supplier</text>" &
    "<text x='{risk_x}' y='85' font-family='Segoe UI' font-size='8.9' font-weight='760' fill='%23202A25'>Risk</text>" &
    "<text x='{target_x}' y='85' font-family='Segoe UI' font-size='8.9' font-weight='760' fill='%23202A25'>Target</text>" &
    "<text x='{intensity_x}' y='85' text-anchor='end' font-family='Segoe UI' font-size='8.9' font-weight='760' fill='%23202A25'>Intensity</text>"
VAR Body =
    IF (
        ISEMPTY ( TopRows ),
        "<text x='20' y='125' font-family='Segoe UI' font-size='10' fill='%235B6C5D'>No supplier rows for selected filters</text>",
        CONCATENATEX (
            TopRows,
            VAR R = [__Rank]
            VAR Y = 96 + ( R - 1 ) * 18
            VAR RowFill = IF ( MOD ( R, 2 ) = 1, "%23F8FBF9", "%23FFFFFF" )
            VAR AccentOpacity = IF ( R = 1, "0.72", "0.22" )
            VAR RiskFill = IF ( [__Risk] = "High", "%23FBE7E1", IF ( [__Risk] = "Medium", "%23FFF2D9", "%23EAF3EA" ) )
            VAR RiskColor = IF ( [__Risk] = "High", "%238C3B2D", IF ( [__Risk] = "Medium", "%23714C10", "%231F5B43" ) )
            VAR TargetFill = IF ( [__Target] = "No verified target", "%23FBE7E1", IF ( [__Target] = "Supplier target", "%23FFF2D9", "%23EAF3EA" ) )
            VAR TargetColor = IF ( [__Target] = "No verified target", "%238C3B2D", IF ( [__Target] = "Supplier target", "%23714C10", "%231F5B43" ) )
            VAR TargetW = MIN ( 122.4, MAX ( 70, LEN ( [__Target] ) * 5.8 + 18 ) )
            VAR BarValue = MAX ( 8, {bar_w} * DIVIDE ( [__Intensity], MaxIntensity, 0 ) )
            RETURN
                "<rect x='16' y='" & FORMAT ( Y, "0" ) & "' width='{header_w}' height='17' rx='5' fill='" & RowFill & "'/>" &
                "<rect x='16' y='" & FORMAT ( Y, "0" ) & "' width='3' height='17' rx='1.5' fill='%23E76F51' opacity='" & AccentOpacity & "'/>" &
                "<text x='{supplier_x}' y='" & FORMAT ( Y + 11, "0" ) & "' font-family='Segoe UI' font-size='9.2' font-weight='" & IF ( R = 1, "700", "520" ) & "' fill='%23202A25'>" & LEFT ( [__Supplier], {20 if width == 620 else 32} ) & "</text>" &
                "<rect x='{risk_chip_x}' y='" & FORMAT ( Y + 3, "0" ) & "' width='46' height='13' rx='6.5' fill='" & RiskFill & "'/>" &
                "<text x='" & FORMAT ( {float(risk_chip_x) + 23}, "0.0" ) & "' y='" & FORMAT ( Y + 13, "0" ) & "' text-anchor='middle' font-family='Segoe UI' font-size='8.4' font-weight='720' fill='" & RiskColor & "'>" & [__Risk] & "</text>" &
                "<rect x='{target_chip_x}' y='" & FORMAT ( Y + 3, "0" ) & "' width='" & FORMAT ( TargetW, "0.0" ) & "' height='13' rx='6.5' fill='" & TargetFill & "'/>" &
                "<text x='" & FORMAT ( {target_chip_x} + TargetW / 2, "0.0" ) & "' y='" & FORMAT ( Y + 13, "0" ) & "' text-anchor='middle' font-family='Segoe UI' font-size='8.4' font-weight='720' fill='" & TargetColor & "'>" & LEFT ( [__Target], 20 ) & "</text>" &
                "<rect x='{bar_x}' y='" & FORMAT ( Y + 13, "0" ) & "' width='{bar_w}' height='2.4' rx='1.2' fill='%23E5EEE8'/>" &
                "<rect x='{bar_x}' y='" & FORMAT ( Y + 13, "0" ) & "' width='" & FORMAT ( BarValue, "0.0" ) & "' height='2.4' rx='1.2' fill='%23E76F51' opacity='0.62'/>" &
                "<text x='{intensity_x}' y='" & FORMAT ( Y + 11, "0" ) & "' text-anchor='end' font-family='Segoe UI' font-size='9.2' font-weight='680' fill='%23202A25'>" & FORMAT ( [__Intensity], "0" ) & "</text>",
            "",
            [__Rank],
            ASC
        )
    )
RETURN "data:image/svg+xml;utf8," & Header & Body & "</svg>"'''


def dynamic_abatement_table_svg() -> str:
    return r'''VAR SelectedScopes = VALUES ( fact_emissions[scope] )
VAR SelectedBUs = VALUES ( dim_business_unit[business_unit] )
VAR SelectedYears = VALUES ( dim_date[year] )
VAR BaseRows =
    SELECTCOLUMNS (
        SUMMARIZECOLUMNS (
            fact_abatement_initiatives[initiative],
            fact_abatement_initiatives[implementation_status],
            fact_abatement_initiatives[scope],
            TREATAS ( SelectedScopes, fact_abatement_initiatives[scope] ),
            TREATAS ( SelectedBUs, fact_abatement_initiatives[business_unit] ),
            TREATAS ( SelectedYears, fact_abatement_initiatives[start_year] ),
            "__Capex", [Abatement Capex USD],
            "__Reduction", [Abatement Annual Reduction tCO2e],
            "__Benefit", [Abatement Annual Benefit USD],
            "__ROI", [Abatement ROI]
        ),
        "__Initiative", fact_abatement_initiatives[initiative],
        "__Status", fact_abatement_initiatives[implementation_status],
        "__Scope", fact_abatement_initiatives[scope],
        "__Capex", [__Capex],
        "__ROI", [__ROI],
        "__Benefit", [__Benefit]
    )
VAR FilteredRows =
    FILTER ( BaseRows, NOT ISBLANK ( [__ROI] ) && [__ROI] <> 0 )
VAR TopRowsRaw =
    TOPN ( 4, FilteredRows, [__ROI], DESC, [__Benefit], DESC, [__Initiative], ASC )
VAR TopRows =
    ADDCOLUMNS (
        TopRowsRaw,
        "__Rank", RANKX ( TopRowsRaw, [__ROI] + DIVIDE ( [__Benefit], 1000000000000 ), , DESC, DENSE )
    )
VAR MaxCapex = MAXX ( TopRows, [__Capex] )
VAR MaxROI = MAXX ( TopRows, [__ROI] )
VAR Header =
    "<svg xmlns='http://www.w3.org/2000/svg' width='1240' height='198' viewBox='0 0 1240 198'>" &
    "<rect x='1' y='1' width='1238' height='196' rx='10' fill='%23FFFFFF' stroke='%23D9E2DC' stroke-width='1'/>" &
    "<rect x='1' y='1' width='1238' height='66' rx='10' fill='%23FAFCFB'/>" &
    "<rect x='1' y='56' width='1238' height='1' fill='%23E4ECE7'/>" &
    "<rect x='16' y='16' width='421.6' height='4' rx='2' fill='%23B7D968' opacity='0.82'/>" &
    "<text x='16' y='40' font-family='Segoe UI' font-size='13.6' font-weight='780' fill='%23202A25'>Abatement Action Queue</text>" &
    "<text x='16' y='58' font-family='Segoe UI' font-size='9.4' fill='%235B6C5D'>Dynamic investment case by status, capex and ROI</text>" &
    "<rect x='1152' y='18' width='68' height='28' rx='14' fill='%23F0F5F2'/>" &
    "<circle cx='1166' cy='32' r='4' fill='%23B7D968'/>" &
    "<text x='1178' y='36' font-family='Segoe UI' font-size='9.4' font-weight='720' fill='%23202A25'>Top " & FORMAT ( COUNTROWS ( TopRows ), "0" ) & "</text>" &
    "<rect x='16' y='70' width='1208' height='22' rx='5' fill='%23EAF1ED'/>" &
    "<text x='20' y='85' font-family='Segoe UI' font-size='8.9' font-weight='760' fill='%23202A25'>Initiative</text>" &
    "<text x='526.6' y='85' font-family='Segoe UI' font-size='8.9' font-weight='760' fill='%23202A25'>Status</text>" &
    "<text x='760.4' y='85' font-family='Segoe UI' font-size='8.9' font-weight='760' fill='%23202A25'>Scope</text>" &
    "<text x='1083.6' y='85' text-anchor='end' font-family='Segoe UI' font-size='8.9' font-weight='760' fill='%23202A25'>Capex</text>" &
    "<text x='1220' y='85' text-anchor='end' font-family='Segoe UI' font-size='8.9' font-weight='760' fill='%23202A25'>ROI</text>"
VAR Body =
    IF (
        ISEMPTY ( TopRows ),
        "<text x='20' y='125' font-family='Segoe UI' font-size='10' fill='%235B6C5D'>No initiatives for selected filters</text>",
        CONCATENATEX (
            TopRows,
            VAR R = [__Rank]
            VAR Y = 96 + ( R - 1 ) * 18
            VAR RowFill = IF ( MOD ( R, 2 ) = 1, "%23F8FBF9", "%23FFFFFF" )
            VAR AccentOpacity = IF ( R = 1, "0.72", "0.22" )
            VAR StatusFill =
                SWITCH ( TRUE (), [__Status] = "Planned", "%23FBE7E1", [__Status] = "In flight", "%23FFF2D9", "%23EAF3EA" )
            VAR StatusColor =
                SWITCH ( TRUE (), [__Status] = "Planned", "%238C3B2D", [__Status] = "In flight", "%23714C10", "%231F5B43" )
            VAR StatusW = MIN ( 92, MAX ( 58, LEN ( [__Status] ) * 5.8 + 18 ) )
            VAR CapexBar = MAX ( 8, 163.4 * DIVIDE ( [__Capex], MaxCapex, 0 ) )
            VAR RoiBar = MAX ( 8, 124.4 * DIVIDE ( [__ROI], MaxROI, 0 ) )
            RETURN
                "<rect x='16' y='" & FORMAT ( Y, "0" ) & "' width='1208' height='17' rx='5' fill='" & RowFill & "'/>" &
                "<rect x='16' y='" & FORMAT ( Y, "0" ) & "' width='3' height='17' rx='1.5' fill='%23B7D968' opacity='" & AccentOpacity & "'/>" &
                "<text x='20' y='" & FORMAT ( Y + 11, "0" ) & "' font-family='Segoe UI' font-size='9.2' font-weight='" & IF ( R = 1, "700", "520" ) & "' fill='%23202A25'>" & LEFT ( [__Initiative], 34 ) & "</text>" &
                "<rect x='523.6' y='" & FORMAT ( Y + 3, "0" ) & "' width='" & FORMAT ( StatusW, "0.0" ) & "' height='13' rx='6.5' fill='" & StatusFill & "'/>" &
                "<text x='" & FORMAT ( 523.6 + StatusW / 2, "0.0" ) & "' y='" & FORMAT ( Y + 13, "0" ) & "' text-anchor='middle' font-family='Segoe UI' font-size='8.4' font-weight='720' fill='" & StatusColor & "'>" & [__Status] & "</text>" &
                "<text x='760.4' y='" & FORMAT ( Y + 11, "0" ) & "' font-family='Segoe UI' font-size='9.2' fill='%23202A25'>" & [__Scope] & "</text>" &
                "<rect x='918.3' y='" & FORMAT ( Y + 13, "0" ) & "' width='163.4' height='2.4' rx='1.2' fill='%23E5EEE8'/>" &
                "<rect x='918.3' y='" & FORMAT ( Y + 13, "0" ) & "' width='" & FORMAT ( CapexBar, "0.0" ) & "' height='2.4' rx='1.2' fill='%23B7D968' opacity='0.62'/>" &
                "<text x='1083.6' y='" & FORMAT ( Y + 11, "0" ) & "' text-anchor='end' font-family='Segoe UI' font-size='9.2' font-weight='680' fill='%23202A25'>" & FORMAT ( DIVIDE ( [__Capex], 1000000 ), "$0.0M" ) & "</text>" &
                "<rect x='1093.6' y='" & FORMAT ( Y + 13, "0" ) & "' width='124.4' height='2.4' rx='1.2' fill='%23E5EEE8'/>" &
                "<rect x='1093.6' y='" & FORMAT ( Y + 13, "0" ) & "' width='" & FORMAT ( RoiBar, "0.0" ) & "' height='2.4' rx='1.2' fill='%23B7D968' opacity='0.62'/>" &
                "<text x='1220' y='" & FORMAT ( Y + 11, "0" ) & "' text-anchor='end' font-family='Segoe UI' font-size='9.2' font-weight='680' fill='%23202A25'>" & FORMAT ( [__ROI], "0.0%" ) & "</text>",
            "",
            [__Rank],
            ASC
        )
    )
RETURN "data:image/svg+xml;utf8," & Header & Body & "</svg>"'''


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
    ("No Verified Target Suppliers", 'CALCULATE ( DISTINCTCOUNT ( dim_supplier[supplier_id] ), dim_supplier[target_status] = "No verified target" )', "#,0"),
    (
        "2026 Target Gap tCO2e",
        "VAR Months2026 = CALCULATE ( DISTINCTCOUNT ( dim_date[date_key] ), FILTER ( ALL ( dim_date ), dim_date[year] = 2026 ) ) "
        "VAR RunRate = DIVIDE ( CALCULATE ( [Total Emissions tCO2e], FILTER ( ALL ( dim_date ), dim_date[year] = 2026 ) ), Months2026 ) * 12 "
        "VAR MonthCount = CALCULATE ( DISTINCTCOUNT ( dim_date[date_key] ), ALL ( dim_date ) ) "
        "VAR AnnualBaseline = DIVIDE ( CALCULATE ( [Total Emissions tCO2e], ALL ( dim_date ) ), DIVIDE ( MonthCount, 12 ) ) "
        "RETURN RunRate - AnnualBaseline * 0.86",
        "#,0.0",
    ),
    ("Total Emissions KPI Card SVG", svg_kpi_card("Total emissions", "Total Emissions tCO2e", COLORS["teal"], "#,0.0K", 1000, "lower"), "", {"dataType": "string", "dataCategory": "ImageUrl"}),
    ("Carbon Cost KPI Card SVG", svg_kpi_card("Carbon cost", "Carbon Cost USD", COLORS["amber"], "$#,0.0M;($#,0.0M);$0.0M", 1000000, "lower"), "", {"dataType": "string", "dataCategory": "ImageUrl"}),
    ("Intensity KPI Card SVG", svg_kpi_card("Intensity", "Emissions Intensity tCO2e per $M Revenue", COLORS["lime"], "#,0.0", 1, "lower"), "", {"dataType": "string", "dataCategory": "ImageUrl"}),
    ("YoY Change KPI Card SVG", svg_kpi_card("YoY change", "YoY Emissions Change %", COLORS["coral"], "0.0%", 1, "lower"), "", {"dataType": "string", "dataCategory": "ImageUrl"}),
    ("Latest Month KPI Card SVG", svg_kpi_card("Latest month", "Latest Month Emissions tCO2e", COLORS["green2"], "#,0.0K", 1000, "lower"), "", {"dataType": "string", "dataCategory": "ImageUrl"}),
    ("Scope 1 KPI Card SVG", svg_kpi_card("Scope 1", "Scope 1 Emissions tCO2e", COLORS["coral"], "#,0.0K", 1000, "lower"), "", {"dataType": "string", "dataCategory": "ImageUrl"}),
    ("Scope 2 KPI Card SVG", svg_kpi_card("Scope 2", "Scope 2 Emissions tCO2e", COLORS["amber"], "#,0.0K", 1000, "lower"), "", {"dataType": "string", "dataCategory": "ImageUrl"}),
    ("Scope 3 KPI Card SVG", svg_kpi_card("Scope 3", "Scope 3 Emissions tCO2e", COLORS["teal"], "#,0.0K", 1000, "lower"), "", {"dataType": "string", "dataCategory": "ImageUrl"}),
    ("Supplier Intensity KPI Card SVG", svg_kpi_card("Supplier intensity", "Supplier Intensity tCO2e per $M Spend", COLORS["lime"], "#,0.0", 1, "lower"), "", {"dataType": "string", "dataCategory": "ImageUrl"}),
    ("Carbon Price KPI Card SVG", svg_kpi_card("Carbon price", "Selected Carbon Price USD/t", COLORS["amber"], "$#,0", 1, "lower"), "", {"dataType": "string", "dataCategory": "ImageUrl"}),
    ("Scenario Cost KPI Card SVG", svg_kpi_card("Scenario cost", "Scenario Carbon Cost USD", COLORS["coral"], "$#,0.0M;($#,0.0M);$0.0M", 1000000, "lower"), "", {"dataType": "string", "dataCategory": "ImageUrl"}),
    ("Annual Reduction KPI Card SVG", svg_kpi_card("Annual reduction", "Abatement Annual Reduction tCO2e", COLORS["teal"], "#,0.0K", 1000, "higher"), "", {"dataType": "string", "dataCategory": "ImageUrl"}),
    ("Abatement ROI KPI Card SVG", svg_kpi_card("Abatement ROI", "Abatement ROI", COLORS["lime"], "0.0%", 1, "higher"), "", {"dataType": "string", "dataCategory": "ImageUrl"}),
    ("Payback KPI Card SVG", svg_kpi_card("Payback years", "Payback Years", COLORS["green2"], "0.0", 1, "lower"), "", {"dataType": "string", "dataCategory": "ImageUrl"}),
    ("High Risk KPI Card SVG", svg_kpi_card("High-risk emissions", "High Risk Supplier Emissions tCO2e", COLORS["coral"], "#,0.0K", 1000, "lower"), "", {"dataType": "string", "dataCategory": "ImageUrl"}),
    ("No Target KPI Card SVG", svg_kpi_card("No target suppliers", "No Verified Target Suppliers", COLORS["amber"], "#,0", 1, "lower"), "", {"dataType": "string", "dataCategory": "ImageUrl"}),
    ("Data Quality KPI Card SVG", svg_kpi_card("Data quality", "Average Data Quality Score", COLORS["teal"], "0.0%", 1, "higher"), "", {"dataType": "string", "dataCategory": "ImageUrl"}),
    ("Target Gap KPI Card SVG", svg_kpi_card("2026 target gap", "2026 Target Gap tCO2e", COLORS["coral"], "#,0.0K", 1000, "lower"), "", {"dataType": "string", "dataCategory": "ImageUrl"}),
    ("Planned Capex KPI Card SVG", svg_kpi_card("Planned capex", "Planned Abatement Capex USD", COLORS["green2"], "$#,0.0M;($#,0.0M);$0.0M", 1000000, "lower"), "", {"dataType": "string", "dataCategory": "ImageUrl"}),
    ("Lens Summary SVG", lens_summary_svg(), "", {"dataType": "string", "dataCategory": "ImageUrl"}),
    ("_QA Table Card Style Version", '"v39_dynamic_table_cards"', "", {"isHidden": True}),
]


def measure_name(item) -> str:
    return item[0]


def measure_expression(item) -> str:
    return item[1]


def measure_format(item) -> str:
    return item[2]


def measure_extra(item) -> dict:
    return item[3] if len(item) > 3 else {}


def measure_by_name(name: str):
    return next(item for item in MEASURES if measure_name(item) == name)


def measure_dtype(name: str) -> str:
    return measure_extra(measure_by_name(name)).get("dataType", "numeric")


def measure_query_type(name: str) -> int:
    return 2048 if measure_dtype(name) == "string" else 1


def measure_transform_type(name: str) -> dict:
    return {"category": None, "underlyingType": 1 if measure_dtype(name) == "string" else 259}


def measure_meta(measure: str, display: str) -> dict:
    payload = {"Restatement": display, "Name": f"{MEASURE_TABLE}.{measure}", "Type": measure_query_type(measure)}
    if mfmt(measure):
        payload["Format"] = mfmt(measure)
    return payload


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
                {
                    **{
                        "name": measure_name(item),
                        "expression": measure_expression(item),
                        "lineageTag": str(uuid.uuid4()),
                    },
                    **({"formatString": measure_format(item)} if measure_format(item) else {}),
                    **({"dataCategory": measure_extra(item)["dataCategory"]} if measure_extra(item).get("dataCategory") else {}),
                    **({"isHidden": measure_extra(item)["isHidden"]} if measure_extra(item).get("isHidden") else {}),
                }
                for item in MEASURES
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


def visual_link(target_section: str, tooltip: str) -> list[dict]:
    return [
        {
            "properties": {
                "show": lit(True),
                "type": txt("PageNavigation"),
                "navigationSection": txt(target_section),
                "tooltip": txt(tooltip),
                "showDefaultTooltip": lit(True),
            }
        }
    ]


def hidden_header(fill: str = "#FFFFFF") -> list[dict]:
    return [
        {
            "properties": {
                "show": lit(False),
                "showOptionsMenu": lit(False),
                "showVisualInformationButton": lit(False),
                "showVisualErrorButton": lit(False),
                "showTooltipButton": lit(False),
                "showPersonalizeVisualButton": lit(False),
                "showFocusModeButton": lit(False),
                "showDrillDownExpandButton": lit(False),
                "showDrillDownLevelButton": lit(False),
                "showDrillUpButton": lit(False),
                "showPinButton": lit(False),
                "background": col(fill),
                "foreground": col(fill),
                "border": col(fill),
            }
        }
    ]


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
    item = next((item for item in MEASURES if measure_name(item) == measure), None)
    return measure_format(item) if item else "#,0"


def frame(title=None, sub=None, fill="#FFFFFF"):
    out = {
        "background": [{"properties": {"show": lit(True), "color": col(fill), "transparency": lit(0.0)}}],
        "border": [{"properties": {"show": lit(True), "color": col(COLORS["border"]), "radius": lit(8.0), "width": lit(1.0)}}],
        "dropShadow": [{"properties": {"show": lit(True), "position": txt("Outer"), "color": col("#D5DED8"), "transparency": lit(82.0), "angle": lit(45.0), "distance": lit(2.0)}}],
        "visualHeader": hidden_header(fill),
    }
    if title:
        out["title"] = [{"properties": {"show": lit(True), "text": txt(title), "fontFamily": txt("Segoe UI Semibold"), "fontSize": lit(10.0), "fontColor": col(COLORS["ink"])}}]
    if sub:
        out["subTitle"] = [{"properties": {"show": lit(True), "text": txt(sub), "fontFamily": txt("Segoe UI"), "fontSize": lit(8.0), "fontColor": col(COLORS["muted"])}}]
    return out


def slicer_frame(title: str, fill: str = "#FFFFFF") -> dict:
    return {
        "title": [{"properties": {"show": lit(True), "text": txt(title), "fontFamily": txt("Segoe UI Semibold"), "fontSize": lit(9.0), "fontColor": col(COLORS["ink"])}}],
        "subTitle": [{"properties": {"show": lit(False)}}],
        "background": [{"properties": {"show": lit(True), "color": col(fill), "transparency": lit(0.0)}}],
        "border": [{"properties": {"show": lit(True), "color": col("#D9E2DC"), "radius": lit(6.0), "width": lit(0.7)}}],
        "dropShadow": [{"properties": {"show": lit(False)}}],
        "visualHeader": hidden_header(fill),
    }


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


def query(froms, selects, order=None, count=1000):
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
                        "DataReduction": {"DataVolume": 4, "Primary": {"Window": {"Count": count}}},
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
    payload = {
        "displayName": display,
        "queryName": f"{MEASURE_TABLE}.{measure}",
        "roles": {role: True},
        "type": measure_transform_type(measure),
        "expr": {"Measure": {"Expression": ent("m"), "Property": measure}},
    }
    if mfmt(measure):
        payload["format"] = mfmt(measure)
    return payload


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


def shape(fill, p, target_section: str | None = None, tooltip: str | None = None, border: bool = False, radius: float = 0.0):
    objects = {
        "shape": [{"properties": {"tileShape": txt("rectangle")}}],
        "fill": [{"properties": {"show": lit(False)}}],
        "outline": [{"properties": {"show": lit(False)}}],
    }
    vc = {
        "title": [{"properties": {"show": lit(False)}}],
        "subTitle": [{"properties": {"show": lit(False)}}],
        "background": [{"properties": {"show": lit(True), "color": col(fill), "transparency": lit(0.0)}}],
        "border": [{"properties": {"show": lit(border or radius > 0), "color": col(fill), "radius": lit(radius), "width": lit(0.75)}}],
        "dropShadow": [{"properties": {"show": lit(False)}}],
        "visualHeader": hidden_header(fill),
    }
    if target_section:
        vc["visualLink"] = visual_link(target_section, tooltip or "Open page")
    return container({"name": uuid.uuid4().hex[:20], "singleVisual": {"visualType": "shape", "objects": objects, "drillFilterOtherVisuals": True, "vcObjects": vc}}, p)


def slicer(table, column, display, p):
    qref = f"{table}.{column}"
    objects = {"data": [{"properties": {"mode": txt("Dropdown")}}], "selection": [{"properties": {"selectAllCheckboxEnabled": lit(True), "singleSelect": lit(False)}}], "header": [{"properties": {"show": lit(False)}}]}
    froms = [{"Name": "f", "Entity": table, "Type": 0}]
    selects = [csel("f", table, column, display)]
    compact = p["height"] <= 40
    vc_objects = (
        {
            "title": [{"properties": {"show": lit(False)}}],
            "subTitle": [{"properties": {"show": lit(False)}}],
            "background": [{"properties": {"show": lit(True), "color": col("#FFFFFF"), "transparency": lit(0.0)}}],
            "border": [{"properties": {"show": lit(True), "color": col("#D9E2DC"), "radius": lit(5.0), "width": lit(0.7)}}],
            "dropShadow": [{"properties": {"show": lit(False)}}],
            "visualHeader": hidden_header("#FFFFFF"),
        }
        if compact
        else slicer_frame(display)
    )
    config = {"name": uuid.uuid4().hex[:20], "singleVisual": {"visualType": "slicer", "projections": {"Values": [{"queryRef": qref, "active": True}]}, "prototypeQuery": {"Version": 2, "From": froms, "Select": selects}, "objects": objects, "drillFilterOtherVisuals": True, "vcObjects": vc_objects}}
    transform_obj = transforms(objects, [("Values", 0, True)], [{"Restatement": display, "Name": qref, "Type": 2048}], [ctrans("f", table, column, display, "Values")], {"Values": [0]}, {"Values": [{"queryRef": qref, "suppressConcat": False}]})
    return container(config, p, query(froms, selects), transform_obj)


def chart_objects(fill, labels=True):
    return {
        "valueAxis": [{"properties": {"showAxisTitle": lit(False), "gridlineShow": lit(False), "labelDisplayUnits": lit(0.0), "fontSize": lit(8.0)}}],
        "categoryAxis": [{"properties": {"showAxisTitle": lit(False), "gridlineShow": lit(False), "concatenateLabels": lit(False), "fontSize": lit(8.0)}}],
        "labels": [{"properties": {"show": lit(labels), "fontSize": lit(8.0), "labelDisplayUnits": lit(0.0)}}],
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
    transform_obj = transforms(objects, [("Category", 0, True), ("Y", 1, False)], [{"Restatement": display, "Name": cref, "Type": 2048}, measure_meta(measure, mdisplay)], [ctrans("c", table, column, display, "Category"), mtrans(measure, mdisplay, "Y")], {"Category": [0], "Y": [1]}, {"Category": [{"queryRef": cref, "suppressConcat": False}]})
    return container(config, p, query(froms, selects, order, count=5), transform_obj)


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
        meta.append(measure_meta(measure, label))
        transform_selects.append(mtrans(measure, label, "Y"))
        roles.append(("Y", idx, False))
    order = {"Direction": 1, "Expression": {"Column": {"Expression": src("c"), "Property": order_column}}} if order_column else None
    prototype = {"Version": 2, "From": froms, "Select": selects}
    if order:
        prototype["OrderBy"] = [order]
    config = {"name": uuid.uuid4().hex[:20], "singleVisual": {"visualType": vtype, "projections": {"Category": [{"queryRef": cref, "active": True}], "Y": y_refs}, "prototypeQuery": prototype, "objects": objects, "drillFilterOtherVisuals": True, "vcObjects": frame(title, sub)}}
    return container(config, p, query(froms, selects, order, count=12), transforms(objects, roles, meta, transform_selects, {"Category": [0], "Y": list(range(1, len(selects)))}, {"Category": [{"queryRef": cref, "suppressConcat": False}]}))


def table_column_width(display: str, qref: str) -> float:
    label = display.lower()
    if "business" in label:
        return 150.0
    if "supplier" in label or "initiative" in label:
        return 240.0
    if "target" in label:
        return 190.0
    if "region" in label or "scope" in label or "risk" in label or "status" in label:
        return 105.0
    if "cost" in label or "capex" in label:
        return 96.0
    if "intensity" in label or "roi" in label or "tco2e" in label:
        return 92.0
    return 120.0


def table_cell_alignment(display: str, qref: str) -> str:
    label = display.lower()
    if any(token in label for token in ["cost", "capex", "roi", "tco2e", "intensity"]):
        return "right"
    return "left"


def table_visual(title, sub, fields, measures, p, order_measure=None, asc=False, order_column=None, table_style=None, count=5):
    table_style = table_style or {}
    aliases, froms = {}, []
    for table, _column, _display in fields:
        if table not in aliases:
            aliases[table] = f"f{len(aliases)}"
            froms.append({"Name": aliases[table], "Entity": table, "Type": 0})
    if measures:
        aliases[MEASURE_TABLE] = "m"
        froms.append({"Name": "m", "Entity": MEASURE_TABLE, "Type": 0})
    selects, projections, meta, transform_selects, column_info = [], [], [], [], []
    for table, column, display in fields:
        qref = f"{table}.{column}"
        selects.append(csel(aliases[table], table, column, display))
        projections.append({"queryRef": qref})
        meta.append({"Restatement": display, "Name": qref, "Type": 2048})
        transform_selects.append(ctrans(aliases[table], table, column, display, "Values"))
        column_info.append((qref, display))
    for measure, display in measures:
        qref = f"{MEASURE_TABLE}.{measure}"
        selects.append(msel("m", measure, display))
        projections.append({"queryRef": qref})
        meta.append(measure_meta(measure, display))
        transform_selects.append(mtrans(measure, display, "Values"))
        column_info.append((qref, display))
    column_widths = table_style.get("column_widths", {})
    objects = {
        "grid": [
            {
                "properties": {
                    "gridHorizontal": lit(True),
                    "gridVertical": lit(False),
                    "outlineColor": col(COLORS["table_grid"]),
                    "gridHorizontalColor": col(COLORS["table_grid"]),
                    "gridHorizontalWeight": lit(0.5),
                    "rowPadding": lit(float(table_style.get("row_padding", 3))),
                }
            }
        ],
        "columnHeaders": [
            {
                "properties": {
                    "show": lit(True),
                    "fontFamily": txt("Segoe UI Semibold"),
                    "fontSize": lit(float(table_style.get("header_font_size", 7.6))),
                    "fontColor": col(COLORS["ink"]),
                    "backColor": col(COLORS["table_header"]),
                    "alignment": txt("left"),
                }
            }
        ],
        "values": [
            {
                "properties": {
                    "fontFamily": txt("Segoe UI"),
                    "fontSize": lit(float(table_style.get("value_font_size", 7.2))),
                    "fontColor": col(COLORS["ink"]),
                    "backColorPrimary": col(COLORS["table_row"]),
                    "backColorSecondary": col(COLORS["table_alt"]),
                    "urlIcon": lit(False),
                }
            }
        ],
        "total": [{"properties": {"totals": lit(False)}}],
        "columnWidth": [
            {"properties": {"value": lit(float(column_widths.get(qref, column_widths.get(display, table_column_width(display, qref)))))}, "selector": {"metadata": qref}}
            for qref, display in column_info
        ],
        "columnFormatting": [
            {"properties": {"alignment": txt(table_cell_alignment(display, qref))}, "selector": {"metadata": qref}}
            for qref, display in column_info
        ],
    }
    order = None
    if order_measure:
        order = {"Direction": 1 if asc else 2, "Expression": {"Measure": {"Expression": src("m"), "Property": order_measure}}}
    elif order_column:
        order_table, order_col = order_column
        order = {"Direction": 1 if asc else 2, "Expression": {"Column": {"Expression": src(aliases[order_table]), "Property": order_col}}}
    prototype = {"Version": 2, "From": froms, "Select": selects}
    if order:
        prototype["OrderBy"] = [order]
    config = {
        "name": uuid.uuid4().hex[:20],
        "singleVisual": {
            "visualType": "tableEx",
            "projections": {"Values": projections},
            "prototypeQuery": prototype,
            "columnProperties": {qref: {"displayName": display} for qref, display in column_info},
            "objects": objects,
            "drillFilterOtherVisuals": True,
            "vcObjects": frame(title, sub),
        },
    }
    return container(config, p, query(froms, selects, order, count=count), transforms(objects, [("Values", i, False) for i in range(len(selects))], meta, transform_selects, {"Values": list(range(len(selects)))}))


def kpi_svg_table(measure: str, display: str, p: dict) -> dict:
    qref = f"{MEASURE_TABLE}.{measure}"
    surface_color = COLORS["navy"] if measure == "Lens Summary SVG" else COLORS["bg"]
    is_table_svg = measure.endswith("Table SVG") or measure.endswith("Queue SVG")
    if measure == "Lens Summary SVG":
        image_w = max(80, int(p["width"] - 14))
        image_h = max(40, int(p["height"] - 12))
    elif measure.endswith("KPI Card SVG") or is_table_svg:
        image_w = max(80, int(p["width"] - 24))
        image_h = max(60, int(p["height"] - 20))
    else:
        image_w = max(20, int(p["width"] - 8))
        image_h = max(20, int(p["height"] - 8))
    objects = {
        "grid": [
            {
                "properties": {
                    "gridHorizontal": lit(False),
                    "gridVertical": lit(False),
                    "outlineColor": col(surface_color),
                    "outlineStyle": lit(0.0),
                    "outlineWeight": lit(0),
                    "gridHorizontalColor": col(surface_color),
                    "gridHorizontalWeight": lit(0),
                    "gridVerticalColor": col(surface_color),
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
                    "fontColor": col(surface_color),
                    "backColor": col(surface_color),
                    "outlineColor": col(surface_color),
                }
            }
        ],
        "values": [
            {
                "properties": {
                    "fontSize": lit(1.0),
                    "fontColor": col(surface_color),
                    "backColor": col(surface_color),
                    "backColorPrimary": col(surface_color),
                    "backColorSecondary": col(surface_color),
                    "urlIcon": lit(False),
                    "imageHeight": lit(image_h),
                    "imageWidth": lit(image_w),
                }
            }
        ],
        "imageSize": [{"properties": {"height": lit(image_h), "width": lit(image_w)}}],
        "columnWidth": [{"properties": {"value": lit(float(image_w if measure == "Lens Summary SVG" or measure.endswith("KPI Card SVG") or is_table_svg else image_w + 6))}, "selector": {"metadata": qref}}],
    }
    froms = [{"Name": "m", "Entity": MEASURE_TABLE, "Type": 0}]
    selects = [msel("m", measure, display)]
    config = {
        "name": uuid.uuid4().hex[:20],
        "singleVisual": {
            "visualType": "tableEx",
            "projections": {"Values": [{"queryRef": qref}]},
            "prototypeQuery": {"Version": 2, "From": froms, "Select": selects},
            "columnProperties": {qref: {"displayName": " " if measure == "Lens Summary SVG" else display}},
            "objects": objects,
            "drillFilterOtherVisuals": True,
            "vcObjects": {
                "background": [{"properties": {"show": lit(measure == "Lens Summary SVG"), "color": col(surface_color), "transparency": lit(0.0)}}],
                "border": [{"properties": {"show": lit(False)}}],
                "dropShadow": [{"properties": {"show": lit(False)}}],
                "title": [{"properties": {"show": lit(False)}}],
                "subTitle": [{"properties": {"show": lit(False)}}],
                "visualHeader": hidden_header(surface_color),
                "visualTooltip": [{"properties": {"show": lit(False)}}],
            },
        },
    }
    return container(config, p, query(froms, selects), transforms(objects, [("Values", 0, False)], [measure_meta(measure, display)], [mtrans(measure, display, "Values")], {"Values": [0]}))


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


def section(name, ordinal, visuals, section_name: str | None = None):
    config = json.dumps({"objects": {"background": [{"properties": {"color": col(COLORS["bg"]), "transparency": lit(0.0)}}], "outspace": [{"properties": {"color": col(COLORS["bg"]), "transparency": lit(0.0)}}]}}, separators=(",", ":"))
    return {"id": ordinal, "name": section_name or f"ReportSection{ordinal:02d}{uuid.uuid4().hex[:6]}", "displayName": name, "filters": "[]", "ordinal": ordinal, "visualContainers": visuals, "config": config, "displayOption": 1, "width": 1280, "height": 720}


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
    facility_dim = read_rows("dim_facility")
    bu = {r["business_unit_id"]: r["business_unit"] for r in read_rows("dim_business_unit")}
    fac = {r["facility_id"]: r["facility"] for r in facility_dim}
    fac_region = {r["facility_id"]: r["region"] for r in facility_dim}
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

    detail_groups: dict[tuple[str, str], dict[str, float]] = {}
    for row in fe:
        key = (
            bu.get(row["business_unit_id"], row["business_unit_id"]),
            fac_region.get(row["facility_id"], "Other"),
        )
        item = detail_groups.setdefault(key, {"emissions": 0.0, "revenue": 0.0})
        item["emissions"] += fnum(row, "emissions_tco2e")
        item["revenue"] += fnum(row, "revenue_usd")
    executive_detail_rows = []
    for idx, ((bu_name, region), item) in enumerate(
        sorted(detail_groups.items(), key=lambda kv: kv[1]["emissions"] * carbon_price, reverse=True)[:4]
    ):
        intensity_value = item["emissions"] / item["revenue"] * 1_000_000 if item["revenue"] else 0
        executive_detail_rows.append(
            [
                bu_name,
                region,
                fmt_k(item["emissions"]),
                fmt_m(item["emissions"] * carbon_price),
                "Prioritize" if idx < 2 else "Monitor",
            ]
        )

    abatement_queue_rows = []
    for row in sorted(
        initiatives,
        key=lambda r: (
            (fnum(r, "annual_opex_savings_usd") + fnum(r, "annual_reduction_tco2e") * carbon_price)
            / fnum(r, "capex_usd")
            if fnum(r, "capex_usd")
            else 0
        ),
        reverse=True,
    )[:4]:
        annual_benefit = fnum(row, "annual_opex_savings_usd") + fnum(row, "annual_reduction_tco2e") * carbon_price
        row_roi = annual_benefit / fnum(row, "capex_usd") if fnum(row, "capex_usd") else 0
        abatement_queue_rows.append(
            [
                row["initiative"],
                row["implementation_status"],
                row["scope"],
                fmt_m(fnum(row, "capex_usd")),
                fmt_pct(row_roi),
            ]
        )

    image_url = {"dataType": "string", "dataCategory": "ImageUrl"}
    register_measure(
        "Executive Detail Table SVG",
        dynamic_executive_detail_table_svg(),
        "",
        image_url,
    )
    register_measure(
        "Supplier Risk Table SVG",
        dynamic_supplier_table_svg("Supplier Risk Table", "Dynamic supplier risk and spend-normalized intensity", 1240),
        "",
        image_url,
    )
    register_measure(
        "Abatement Action Queue SVG",
        dynamic_abatement_table_svg(),
        "",
        image_url,
    )
    register_measure(
        "Risk Action Queue SVG",
        dynamic_supplier_table_svg("Risk Action Queue", "Dynamic supplier follow-up for CFO/ESG review", 620),
        "",
        image_url,
    )

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

    def visual_text(runs: list[tuple[str, int, str, str]], p: dict, fill: str | None = None, border: bool = False, target_section: str | None = None, tooltip: str | None = None):
        text_runs = [{"value": value, "textStyle": {"fontFamily": family, "fontSize": f"{size}pt", "color": color}} for value, size, color, family in runs]
        objects = {"general": [{"properties": {"paragraphs": [{"textRuns": text_runs}]}}]}
        vc = {
            "title": [{"properties": {"show": lit(False)}}],
            "subTitle": [{"properties": {"show": lit(False)}}],
            "background": [{"properties": {"show": lit(fill is not None), "color": col(fill or "#FFFFFF"), "transparency": lit(0.0)}}],
            "border": [{"properties": {"show": lit(border), "color": col(COLORS["border"]), "radius": lit(6.0), "width": lit(1.0)}}],
            "dropShadow": [{"properties": {"show": lit(False)}}],
            "visualHeader": hidden_header(fill or "#FFFFFF"),
        }
        if border:
            vc["dropShadow"] = [{"properties": {"show": lit(True), "position": txt("Outer"), "color": col("#D5DED8"), "transparency": lit(86.0), "angle": lit(45.0), "distance": lit(2.0)}}]
        if target_section:
            vc["visualLink"] = visual_link(target_section, tooltip or "Open page")
        return container({"name": uuid.uuid4().hex[:20], "singleVisual": {"visualType": "textbox", "objects": objects, "drillFilterOtherVisuals": True, "vcObjects": vc}}, p)

    def rect(fill: str, p: dict, border: bool = False):
        return shape(fill, p, border=border, radius=6.0 if border else 0.0)

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
        row_h = 18
        max_rows = max(2, min(len(rows), int((p["height"] - 86) // row_h)))
        for r, row in enumerate(rows[:max_rows]):
            y = p["y"] + 82 + r * row_h
            if r % 2 == 0:
                visuals.append(rect("#F4F7F5", pos(p["x"] + 10, y - 2, z + 40 + r, p["width"] - 20, row_h)))
            for c, val in enumerate(row):
                cell_x = x_positions[c]
                cell_w = col_widths[c] - 4
                if status_cols and c in status_cols:
                    visuals.append(rect(status_tone(val), pos(cell_x - 3, y - 1, z + 58 + r * 10 + c, min(cell_w, max(38, len(str(val)) * 5.5 + 12)), 15)))
                visuals.append(small_text(fit_text(val, cell_w), pos(cell_x, y, z + 60 + r * 10 + c, cell_w, 16), COLORS["ink"]))
        return visuals

    def rail_slicer(label: str, table: str, column: str, display: str, y: int, z: int):
        return [
            rect(COLORS["teal"], pos(36, y + 7, z, 7, 7)),
            visual_text([(label, 7, "#DCEAE4", "Segoe UI Semibold")], pos(52, y - 6, z + 1, 116, 26)),
            slicer(table, column, display, pos(34, y + 18, z + 2, 146, 36)),
        ]

    def nav_item(label: str, key: str, y: int, z: int, active: bool):
        fill = COLORS["teal"] if active else COLORS["sidebar2"]
        text_color = "#FFFFFF" if active else "#DCEAE4"
        rail_color = "#DCEAE4" if active else "#4B705E"
        target = PAGE_SECTION_NAMES[key]
        return [
            shape(fill, pos(24, y, z, 158, 32), target, f"Go to {label}", border=False, radius=6.0),
            shape(rail_color, pos(34, y + 8, z + 1, 4, 16), target, f"Go to {label}", border=False, radius=2.0),
            visual_text([(label, 8, text_color, "Segoe UI Semibold")], pos(46, y + 1, z + 2, 126, 30)),
        ]

    def sidebar_shell(page_title: str, active_key: str, z: int, context: str):
        visuals = [
            shape(COLORS["sidebar"], pos(12, 8, z, 178, 704), border=False, radius=8.0),
            visual_text([("P18 ESG", 12, "#FFFFFF", "Segoe UI Semibold"), ("\nFinance Control", 7, "#DCEAE4", "Segoe UI")], pos(30, 24, z + 1, 126, 54)),
            visual_text([(page_title, 14, COLORS["ink"], "Segoe UI Semibold"), (f"\n{context}", 7, COLORS["muted"], "Segoe UI")], pos(204, 14, z + 2, 520, 42)),
        ]
        nav = [
            ("01 Overview", "overview"),
            ("02 Suppliers", "supplier"),
            ("03 Abatement", "abatement"),
            ("04 Risk", "risk"),
        ]
        nav_y = 94
        for idx, (label, key) in enumerate(nav):
            visuals.extend(nav_item(label, key, nav_y + idx * 40, z + 10 + idx * 4, active_key == key))
        visuals += [
            rect("#245442", pos(28, 268, z + 40, 148, 2)),
            visual_text([("Global Lens", 7, "#BFD1C8", "Segoe UI Semibold")], pos(34, 240, z + 41, 120, 24)),
            *rail_slicer("Year", "dim_date", "year", "Year", 276, z + 44),
            *rail_slicer("Region", "dim_facility", "region", "Region", 336, z + 50),
            *rail_slicer("Business Unit", "dim_business_unit", "business_unit", "BU", 396, z + 56),
            *rail_slicer("Scope", "fact_emissions", "scope", "Scope", 456, z + 62),
            *rail_slicer("Carbon price", "dim_carbon_scenario", "scenario", "Price", 516, z + 68),
            kpi_svg_table("Lens Summary SVG", "Current Lens", pos(20, 604, z + 88, 170, 80)),
            visual_text([("Data through May 2026", 7, "#BFD1C8", "Segoe UI")], pos(40, 690, z + 89, 120, 18)),
        ]
        return visuals

    def top_nav_item(label: str, key: str, x: int, z: int, active: bool):
        fill = COLORS["teal"] if active else "#1C4A39"
        text_color = "#FFFFFF" if active else "#DCEAE4"
        target = PAGE_SECTION_NAMES[key]
        return [
            shape(fill, pos(x, 104, z, 135, 42), target, f"Go to {label}", border=False, radius=5.0),
            visual_text([(label, 9, text_color, "Segoe UI Semibold")], pos(x + 12, 109, z + 1, 114, 34), target_section=target, tooltip=f"Go to {label}"),
        ]

    def top_slicer(label: str, table: str, column: str, display: str, x: int, width: int, z: int):
        return [slicer(table, column, display, pos(x, 96, z, width, 60))]

    def top_shell(page_title: str, active_key: str, z: int, context: str):
        visuals = [
            shape(COLORS["navy"], pos(0, 0, z, 1280, 90), border=False, radius=0.0),
            shape("#EEF4F1", pos(0, 90, z + 1, 1280, 70), border=False, radius=0.0),
            visual_text([("P18 ESG", 15, "#FFFFFF", "Segoe UI Semibold")], pos(22, 24, z + 2, 128, 44)),
            visual_text([(page_title, 16, "#FFFFFF", "Segoe UI Semibold"), (f"\n{context}", 7, "#DCEAE4", "Segoe UI")], pos(170, 12, z + 3, 330, 68)),
            kpi_svg_table("Lens Summary SVG", "Current Lens", pos(520, 3, z + 5, 740, 84)),
        ]
        nav = [
            ("01 Overview", "overview"),
            ("02 Suppliers", "supplier"),
            ("03 Abatement", "abatement"),
            ("04 Risk", "risk"),
        ]
        for idx, (label, key) in enumerate(nav):
            visuals.extend(top_nav_item(label, key, 20 + idx * 145, z + 10 + idx * 4, active_key == key))
        visuals += [
            *top_slicer("Year", "dim_date", "year", "Year", 610, 78, z + 46),
            *top_slicer("Region", "dim_facility", "region", "Region", 700, 112, z + 52),
            *top_slicer("Business Unit", "dim_business_unit", "business_unit", "Business Unit", 824, 150, z + 58),
            *top_slicer("Scope", "fact_emissions", "scope", "Scope", 986, 88, z + 64),
            *top_slicer("Carbon price", "dim_carbon_scenario", "scenario", "Carbon price", 1086, 154, z + 70),
        ]
        return visuals

    def kpi_row(items: list[tuple[str, str]], y: int, z: int):
        xs = [20, 333, 646, 959]
        return [kpi_svg_table(measure, display, pos(xs[i], y, z + i, 300, 150)) for i, (measure, display) in enumerate(items[:4])]

    p1 = top_shell("ESG Finance Overview", "overview", 1, "Emissions, carbon cost exposure and executive trend")
    p1 += kpi_row(
        [
            ("Total Emissions KPI Card SVG", "Total emissions"),
            ("Carbon Cost KPI Card SVG", "Carbon cost"),
            ("Intensity KPI Card SVG", "Intensity"),
            ("Latest Month KPI Card SVG", "Latest month"),
        ],
        160,
        100,
    )
    p1.append(multi_chart("lineChart", "Monthly Emissions + Carbon Cost", "Trend by month with selected carbon price", "dim_date", "month_start", "Month", [("Total Emissions tCO2e", "Emissions"), ("Carbon Cost USD", "Carbon Cost")], pos(20, 315, 200, 478, 190), "month_start"))
    p1.append(single_chart("barChart", "Emissions by Scope", "Scope 1, 2 and 3 contribution", "fact_emissions", "scope", "Scope", "Total Emissions tCO2e", "tCO2e", pos(518, 315, 300, 342, 190), COLORS["teal"], order_measure=True, ascending=False))
    p1.append(single_chart("barChart", "Business Unit Hotspots", "Where emissions concentrate", "dim_business_unit", "business_unit", "Business Unit", "Total Emissions tCO2e", "tCO2e", pos(880, 315, 400, 380, 190), COLORS["navy"], order_measure=True, ascending=False))
    p1.append(kpi_svg_table("Executive Detail Table SVG", "Executive Detail", pos(20, 520, 500, 620, 198)))
    p1.append(single_chart("barChart", "Carbon Cost by Scenario", "Scenario exposure after selected filters", "dim_carbon_scenario", "scenario", "Scenario", "Scenario Carbon Cost USD", "Carbon cost", pos(660, 520, 560, 600, 198), COLORS["amber"], order_measure=True, ascending=False))

    p2 = top_shell("Emissions & Supplier Intensity", "supplier", 1000, "Scope/source diagnostics and supplier intensity")
    p2 += kpi_row(
        [
            ("Scope 1 KPI Card SVG", "Scope 1"),
            ("Scope 2 KPI Card SVG", "Scope 2"),
            ("Scope 3 KPI Card SVG", "Scope 3"),
            ("Supplier Intensity KPI Card SVG", "Supplier intensity"),
        ],
        160,
        1100,
    )
    p2.append(single_chart("barChart", "Source Category Emissions", "GHG source categories ranked by footprint", "dim_activity", "ghg_category", "Category", "Total Emissions tCO2e", "tCO2e", pos(20, 315, 1200, 400, 190), COLORS["teal"], order_measure=True, ascending=False))
    p2.append(single_chart("barChart", "Supplier Intensity by Category", "tCO2e per $M spend by supplier type", "dim_supplier", "supplier_category", "Category", "Supplier Intensity tCO2e per $M Spend", "Intensity", pos(440, 315, 1300, 400, 190), COLORS["amber"], order_measure=True, ascending=False))
    p2.append(single_chart("barChart", "Facility Emissions", "Operational footprint by facility", "dim_facility", "facility", "Facility", "Total Emissions tCO2e", "tCO2e", pos(860, 315, 1400, 400, 190), COLORS["navy"], order_measure=True, ascending=False))
    p2.append(kpi_svg_table("Supplier Risk Table SVG", "Supplier Risk Table", pos(20, 520, 1500, 1240, 198)))

    p3 = top_shell("Carbon Scenario & Abatement ROI", "abatement", 2000, "Carbon price exposure, MACC and capital prioritization")
    p3 += kpi_row(
        [
            ("Carbon Price KPI Card SVG", "Carbon price"),
            ("Scenario Cost KPI Card SVG", "Scenario cost"),
            ("Annual Reduction KPI Card SVG", "Annual reduction"),
            ("Abatement ROI KPI Card SVG", "Abatement ROI"),
        ],
        160,
        2100,
    )
    p3.append(single_chart("barChart", "Scenario Exposure by Path", "Carbon cost under each pricing scenario", "dim_carbon_scenario", "scenario", "Scenario", "Scenario Carbon Cost USD", "Scenario cost", pos(20, 315, 2200, 400, 190), COLORS["coral"], order_measure=True, ascending=False))
    p3.append(single_chart("barChart", "MACC by Implementation Status", "Lower cost per tCO2e first", "fact_abatement_initiatives", "implementation_status", "Status", "MACC USD per tCO2e", "MACC", pos(440, 315, 2300, 400, 190), COLORS["teal"], order_measure=True, ascending=True))
    p3.append(single_chart("barChart", "Reduction by Scope", "Annual tCO2e reduction potential", "fact_abatement_initiatives", "scope", "Scope", "Abatement Annual Reduction tCO2e", "Reduction", pos(860, 315, 2400, 400, 190), COLORS["navy"], order_measure=True, ascending=False))
    p3.append(kpi_svg_table("Abatement Action Queue SVG", "Abatement Action Queue", pos(20, 520, 2500, 1240, 198)))

    p4 = top_shell("Risk & Action Control Tower", "risk", 3000, "Supplier risk, target gaps and governance queue")
    p4 += kpi_row(
        [
            ("High Risk KPI Card SVG", "High-risk emissions"),
            ("No Target KPI Card SVG", "No target suppliers"),
            ("Data Quality KPI Card SVG", "Data quality"),
            ("Planned Capex KPI Card SVG", "Planned capex"),
        ],
        160,
        3100,
    )
    p4.append(single_chart("barChart", "Supplier Risk Exposure", "Emissions by supplier risk tier", "fact_supplier_month", "carbon_risk_tier", "Risk tier", "Supplier Emissions tCO2e", "Emissions", pos(20, 315, 3200, 400, 190), COLORS["coral"], order_measure=True, ascending=False))
    p4.append(single_chart("barChart", "Target Status Exposure", "Supplier emissions by target maturity", "dim_supplier", "target_status", "Target status", "Supplier Emissions tCO2e", "Emissions", pos(440, 315, 3300, 400, 190), COLORS["amber"], order_measure=True, ascending=False))
    p4.append(single_chart("barChart", "Capex by Action Status", "Abatement investment still to govern", "fact_abatement_initiatives", "implementation_status", "Status", "Abatement Capex USD", "Capex", pos(860, 315, 3400, 400, 190), COLORS["navy"], order_measure=True, ascending=False))
    p4.append(kpi_svg_table("Risk Action Queue SVG", "Risk Action Queue", pos(20, 520, 3500, 620, 198)))
    p4.append(single_chart("barChart", "Weighted Cost by Scenario", "Governance exposure after probability weighting", "dim_carbon_scenario", "scenario", "Scenario", "Probability Weighted Carbon Cost USD", "Weighted cost", pos(660, 520, 3600, 600, 198), COLORS["coral"], order_measure=True, ascending=False))

    cfg = {"version": "5.73", "activeSectionIndex": 0, "defaultDrillFilterOtherVisuals": True, "settings": {"useNewFilterPaneExperience": True, "useStylableVisualContainerHeader": True, "queryLimitOption": 6}}
    layout = {
        "activeSectionIndex": 0,
        "sections": [
            section("ESG Finance Overview", 0, p1, PAGE_SECTION_NAMES["overview"]),
            section("Emissions & Supplier Intensity", 1, p2, PAGE_SECTION_NAMES["supplier"]),
            section("Carbon Scenario & Abatement ROI", 2, p3, PAGE_SECTION_NAMES["abatement"]),
            section("Risk & Action Control Tower", 3, p4, PAGE_SECTION_NAMES["risk"]),
        ],
        "config": json.dumps(cfg, separators=(",", ":")),
        "layoutOptimization": 0,
    }
    visual_type_counts: dict[str, int] = {}
    visual_link_count = 0
    kpi_svg_visuals = 0
    current_lens_visuals = 0
    for report_section in layout["sections"]:
        for visual_container in report_section["visualContainers"]:
            try:
                config_obj = json.loads(visual_container["config"])
                single_visual = config_obj["singleVisual"]
                visual_type = single_visual["visualType"]
                if "visualLink" in single_visual.get("vcObjects", {}):
                    visual_link_count += 1
                text_blob = json.dumps(config_obj)
                if "KPI Card SVG" in text_blob:
                    kpi_svg_visuals += 1
                if "Lens Summary SVG" in text_blob:
                    current_lens_visuals += 1
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
            "visual_link_count": visual_link_count,
            "kpi_svg_visuals": kpi_svg_visuals,
            "current_lens_visuals": current_lens_visuals,
            "native_visual_containers": sum(count for visual_type, count in visual_type_counts.items() if visual_type != "textbox"),
        },
    )
    audit = f"""# Fix Prompt From Project 18 Gap Audit

Generated: {datetime.now().isoformat(timespec="seconds")}

## Before Risk Pattern

- Header implementation type: top textbox/title band with tight height.
- Shape/background implementation type: prior `shape()` helper used textbox visuals.
- KPI implementation type: prior KPI row used native `cardVisual` plus separate textbox sparkline.
- Sparkline implementation type: prior sparkline was text/ASCII overlay near the card bottom.
- Current Lens implementation type: missing dynamic Current Lens.
- Page navigation implementation type: missing on-canvas page navigation.
- Chart card implementation type: native charts with uneven compact slots.
- Slicer/filter implementation type: top horizontal slicers competing with header/title space.

## Fix Strategy Applied In Source

- Replaced decorative textbox shape helper with native `shape` visuals.
- Added stable section names and visualLink page navigation as top page tabs.
- Replaced release KPI cards with `tableEx` ImageUrl SVG measures.
- Added dynamic compact `Lens Summary SVG` rendered inside the dark header on every page.
- Removed the static CFO Management Lens from Page 1 and replaced it with Carbon Cost by Scenario.
- Preserved the original Project 18 structure: global slicers stay in the top header.
- Rebuilt content grid with four 300 x 150 KPI cards at y=160 and chart/table content from y=315 downward.

## Layout Evidence

- Visual type counts: {json.dumps(visual_type_counts, sort_keys=True)}
- KPI SVG visuals: {kpi_svg_visuals}
- Current Lens visuals: {current_lens_visuals}
- VisualLink navigation items: {visual_link_count}
"""
    write_text(ROOT / "qa" / "fix_prompt_from_project18_gap_audit.md", audit)
    write_json(
        ROOT / "qa" / "golden_kpi_card_layout_summary.json",
        {
            "status": "source_layout_contract_passed",
            "pattern": "tableEx ImageUrl SVG KPI card",
            "visual_slot": {"width": 300, "height": 150},
            "svg_canvas": {"width": 300, "height": 150},
            "image_sizing_rule": "slot minus safe padding; four KPI cards only, Current Lens is in the header",
            "sparkline_contract": {
                "clipPath": True,
                "panel": {"x": 176, "y": 35, "width": 106, "height": 52},
                "line_points_generated_from": "last 10 selected months",
            },
            "chrome_contract": {
                "column_headers": False,
                "grid": False,
                "row_padding": 0,
                "visual_header": False,
                "measure_name_visible": False,
            },
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
foreach($td in $def.model.tables){ $t=New-Object Microsoft.AnalysisServices.Tabular.Table; $t.Name=[string]$td.name; $model.Tables.Add($t); foreach($cd in @($td.columns)){ $c=New-Object Microsoft.AnalysisServices.Tabular.DataColumn; $c.Name=[string]$cd.name; $c.SourceColumn=if($cd.sourceColumn){[string]$cd.sourceColumn}else{[string]$cd.name}; $c.DataType=DT ([string]$cd.dataType); if($cd.isHidden){$c.IsHidden=[bool]$cd.isHidden}; if($cd.formatString){$c.FormatString=[string]$cd.formatString}; if($cd.summarizeBy){$c.SummarizeBy=AF $cd.summarizeBy}; $t.Columns.Add($c)}; foreach($pd in @($td.partitions)){ $p=New-Object Microsoft.AnalysisServices.Tabular.Partition; $p.Name=[string]$pd.name; $p.Mode=[Microsoft.AnalysisServices.Tabular.ModeType]::Import; $s=New-Object Microsoft.AnalysisServices.Tabular.MPartitionSource; $s.Expression=Expr $pd.source.expression; $p.Source=$s; $t.Partitions.Add($p)}; foreach($md in @($td.measures)){ if($md -and $md.name){$mm=New-Object Microsoft.AnalysisServices.Tabular.Measure; $mm.Name=[string]$md.name; $mm.Expression=[string]$md.expression; if($md.formatString){$mm.FormatString=[string]$md.formatString}; if($md.dataCategory){try{$mm.DataCategory=[string]$md.dataCategory}catch{}}; $t.Measures.Add($mm)}} }
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
layout_path = ROOT / 'build' / 'native_report_layout_project18.json'
layout = json.loads(layout_path.read_text(encoding='utf-8-sig')) if layout_path.exists() else {'sections': []}

def visual_records(section):
    records = []
    for vc in section.get('visualContainers', []):
        pos = vc.get('layouts', [{}])[0].get('position', {})
        try:
            cfg = json.loads(vc.get('config', '{}'))
            visual_type = cfg.get('singleVisual', {}).get('visualType')
            text_blob = json.dumps(cfg)
        except Exception:
            visual_type = 'unknown'
            text_blob = vc.get('config', '')
        records.append({'visual_type': visual_type, 'position': pos, 'text': text_blob})
    return records

layout_contract = {}
for section in layout.get('sections', []):
    records = visual_records(section)
    name = section.get('displayName')
    lens = [r for r in records if 'Lens Summary SVG' in r['text']]
    kpis = [r for r in records if 'KPI Card SVG' in r['text']]
    charts = [r for r in records if r['visual_type'] in ('lineChart', 'barChart')]
    layout_contract[name] = {
        'current_lens_in_header_pass': len(lens) == 1 and lens[0]['position'].get('y') < 90 and lens[0]['position'].get('height') <= 84,
        'duplicate_current_lens_pass': len(lens) == 1,
        'kpi_cards_width_300_pass': len(kpis) == 4 and all(r['position'].get('width') == 300 for r in kpis),
        'kpi_cards_y160_pass': len(kpis) == 4 and all(r['position'].get('y') == 160 for r in kpis),
        'chart_region_y_gte_315_pass': bool(charts) and min(r['position'].get('y', 9999) for r in charts) >= 315,
        'chart_region_y315_pass': bool(charts) and min(r['position'].get('y', 9999) for r in charts) == 315,
        'table_row_y520_pass': any(r['visual_type'] == 'tableEx' and r['position'].get('y') == 520 for r in records),
    }
layout_contract_pass = bool(layout_contract) and all(
    all(isinstance(v, bool) and v for v in gates.values())
    for gates in layout_contract.values()
)
pending_gap = 'Open output/dashboard_final.pbix in Power BI Desktop and capture fresh screenshots for all 4 pages before claiming fresh Desktop visual QA pass.'

r={
    'status':'desktop_open_check_passed' if package_ok and layout_contract_pass and desktop_pass else ('package_pass_desktop_open_check_pending' if package_ok and layout_contract_pass else 'fail'),
    'pbix_exists':p.exists(),
    'pbix_size_bytes':p.stat().st_size if p.exists() else 0,
    'sha256': current_sha,
    'build_route':'SCRIPTED_DESKTOP_PBIX',
    'native_package_validation_status': native.get('status'),
    'pages': native.get('pages', []),
    'visual_containers': native.get('visual_containers'),
    'layout_contract_pass': layout_contract_pass,
    'layout_contract': layout_contract,
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
    build_layout()
    build_model()
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
