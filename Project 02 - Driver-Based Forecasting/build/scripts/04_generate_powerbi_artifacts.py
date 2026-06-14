from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
PREPARED_DIR = PROJECT_ROOT / "data" / "prepared"
MODEL_DIR = PROJECT_ROOT / "model"
CONFIG_DIR = PROJECT_ROOT / "build" / "config"
POWERBI_DIR = PROJECT_ROOT / "powerbi"
DOCS_DIR = PROJECT_ROOT / "docs"
OUTPUT_DIR = PROJECT_ROOT / "output"
SCREENSHOT_DIR = OUTPUT_DIR / "screenshots"
EXPORT_DIR = OUTPUT_DIR / "exports"


def read_csv(name: str) -> pd.DataFrame:
    return pd.read_csv(PREPARED_DIR / f"{name}.csv")


def money(value: float) -> str:
    return f"${value / 1_000_000:,.1f}M"


def pct(value: float) -> str:
    return f"{value * 100:,.1f}%"


def write_json(path: Path, payload: dict | list) -> None:
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def build_measure_map() -> list[dict]:
    measures = [
        {
            "name": "Revenue",
            "display_name": "Revenue",
            "table": "KPI_Measures",
            "dax": "Revenue = SUM(FactRevenueDriver[RevenueUSD])",
            "format": "$#,0;($#,0);$0",
            "unit": "USD",
            "definition": "Net revenue after surcharge and discount at current filter context.",
        },
        {
            "name": "Direct Cost",
            "display_name": "Direct Cost",
            "table": "KPI_Measures",
            "dax": "Direct Cost = SUM(FactCostDriver[DirectCostUSD])",
            "format": "$#,0;($#,0);$0",
            "unit": "USD",
            "definition": "Carrier, handling, fuel and customs direct costs.",
        },
        {
            "name": "Gross Profit",
            "display_name": "Gross Profit",
            "table": "KPI_Measures",
            "dax": "Gross Profit = [Revenue] - [Direct Cost]",
            "format": "$#,0;($#,0);$0",
            "unit": "USD",
            "definition": "Revenue less direct cost.",
        },
        {
            "name": "Gross Margin %",
            "display_name": "Gross Margin %",
            "table": "KPI_Measures",
            "dax": "Gross Margin % = DIVIDE([Gross Profit], [Revenue])",
            "format": "0.0%",
            "unit": "%",
            "definition": "Gross profit divided by revenue.",
        },
        {
            "name": "Payroll Cost",
            "display_name": "Payroll Cost",
            "table": "KPI_Measures",
            "dax": "Payroll Cost = SUM(FactHeadcountPlan[PayrollCostUSD])",
            "format": "$#,0;($#,0);$0",
            "unit": "USD",
            "definition": "Salary cost from the headcount plan.",
        },
        {
            "name": "Non Payroll OPEX",
            "display_name": "Non Payroll OPEX",
            "table": "KPI_Measures",
            "dax": "Non Payroll OPEX = SUM(FactOpexDriver[NonPayrollOpexUSD])",
            "format": "$#,0;($#,0);$0",
            "unit": "USD",
            "definition": "Rent, software, marketing, travel and G&A cost excluding payroll.",
        },
        {
            "name": "EBITDA",
            "display_name": "EBITDA",
            "table": "KPI_Measures",
            "dax": "EBITDA = [Gross Profit] - [Payroll Cost] - [Non Payroll OPEX]",
            "format": "$#,0;($#,0);$0",
            "unit": "USD",
            "definition": "Forecast P&L operating profit proxy before tax and capex.",
        },
        {
            "name": "EBITDA Margin %",
            "display_name": "EBITDA Margin %",
            "table": "KPI_Measures",
            "dax": "EBITDA Margin % = DIVIDE([EBITDA], [Revenue])",
            "format": "0.0%",
            "unit": "%",
            "definition": "EBITDA divided by revenue.",
        },
        {
            "name": "Jobs",
            "display_name": "Jobs",
            "table": "KPI_Measures",
            "dax": "Jobs = SUM(FactRevenueDriver[VolumeJobs])",
            "format": "#,0",
            "unit": "jobs",
            "definition": "Total shipment or service jobs.",
        },
        {
            "name": "Revenue per Job",
            "display_name": "Revenue / Job",
            "table": "KPI_Measures",
            "dax": "Revenue per Job = DIVIDE([Revenue], [Jobs])",
            "format": "$#,0.0",
            "unit": "USD/job",
            "definition": "Revenue productivity per job.",
        },
        {
            "name": "Variable Cost per Job",
            "display_name": "Variable Cost / Job",
            "table": "KPI_Measures",
            "dax": "Variable Cost per Job = DIVIDE([Direct Cost], [Jobs])",
            "format": "$#,0.0",
            "unit": "USD/job",
            "definition": "Direct cost productivity per job.",
        },
        {
            "name": "Average FTE",
            "display_name": "Average FTE",
            "table": "KPI_Measures",
            "dax": "Average FTE = AVERAGEX(VALUES(DimDate[YearMonth]), SUM(FactHeadcountPlan[FTE]))",
            "format": "#,0.0",
            "unit": "FTE",
            "definition": "Average monthly FTE in the selected period.",
        },
        {
            "name": "Jobs per FTE",
            "display_name": "Jobs / FTE",
            "table": "KPI_Measures",
            "dax": "Jobs per FTE = DIVIDE([Jobs], [Average FTE])",
            "format": "#,0.0",
            "unit": "jobs/FTE",
            "definition": "Capacity productivity based on average monthly FTE.",
        },
        {
            "name": "Operating Cash Flow",
            "display_name": "Operating Cash Flow",
            "table": "KPI_Measures",
            "dax": "Operating Cash Flow = SUM(FactCashImpact[OperatingCashFlowUSD])",
            "format": "$#,0;($#,0);$0",
            "unit": "USD",
            "definition": "EBITDA less tax and working-capital drag.",
        },
        {
            "name": "Ending Cash Latest Month",
            "display_name": "Ending Cash",
            "table": "KPI_Measures",
            "dax": "Ending Cash Latest Month = CALCULATE(SUM(FactCashImpact[EndingCashUSD]), LASTNONBLANK(DimDate[Date], [Operating Cash Flow]))",
            "format": "$#,0;($#,0);$0",
            "unit": "USD",
            "definition": "Ending cash balance at latest visible period.",
        },
        {
            "name": "Working Capital",
            "display_name": "Working Capital",
            "table": "KPI_Measures",
            "dax": "Working Capital = SUM(FactCashImpact[WorkingCapitalUSD])",
            "format": "$#,0;($#,0);$0",
            "unit": "USD",
            "definition": "AR and AP timing impact based on DSO and DPO assumptions.",
        },
        {
            "name": "DSO Days",
            "display_name": "DSO",
            "table": "KPI_Measures",
            "dax": "DSO Days = AVERAGE(FactCashImpact[DSODays])",
            "format": "#,0",
            "unit": "days",
            "definition": "Average days sales outstanding in current scenario.",
        },
        {
            "name": "DPO Days",
            "display_name": "DPO",
            "table": "KPI_Measures",
            "dax": "DPO Days = AVERAGE(FactCashImpact[DPODays])",
            "format": "#,0",
            "unit": "days",
            "definition": "Average days payable outstanding in current scenario.",
        },
        {
            "name": "MAPE",
            "display_name": "MAPE",
            "table": "KPI_Measures",
            "dax": "MAPE = AVERAGE(FactForecastAccuracy[AbsolutePctError])",
            "format": "0.0%",
            "unit": "%",
            "definition": "Mean absolute percentage error for forecast accuracy tracking.",
        },
        {
            "name": "Forecast Bias %",
            "display_name": "Forecast Bias %",
            "table": "KPI_Measures",
            "dax": "Forecast Bias % = AVERAGE(FactForecastAccuracy[ForecastBiasPct])",
            "format": "0.0%",
            "unit": "%",
            "definition": "Average signed forecast bias.",
        },
        {
            "name": "Base Revenue",
            "display_name": "Base Revenue",
            "table": "KPI_Measures",
            "dax": "Base Revenue = CALCULATE([Revenue], DimScenario[Scenario] = \"Base\")",
            "format": "$#,0;($#,0);$0",
            "unit": "USD",
            "definition": "Base scenario revenue for variance comparisons.",
        },
        {
            "name": "Scenario Revenue Variance vs Base",
            "display_name": "Revenue Var vs Base",
            "table": "KPI_Measures",
            "dax": "Scenario Revenue Variance vs Base = [Revenue] - [Base Revenue]",
            "format": "$#,0;($#,0);$0",
            "unit": "USD",
            "definition": "Selected scenario revenue less base scenario revenue.",
        },
        {
            "name": "Scenario Revenue Variance % vs Base",
            "display_name": "Revenue Var % vs Base",
            "table": "KPI_Measures",
            "dax": "Scenario Revenue Variance % vs Base = DIVIDE([Scenario Revenue Variance vs Base], [Base Revenue])",
            "format": "0.0%",
            "unit": "%",
            "definition": "Selected scenario revenue variance percentage versus base.",
        },
    ]
    return measures


def write_metric_artifacts(measures: list[dict]) -> None:
    write_json(MODEL_DIR / "measure_map.json", measures)
    dax_lines = [
        "-- Project 02 - Driver-Based Forecasting & Scenario Planning",
        "-- Create a blank measure table named KPI_Measures, then add these measures.",
        "",
    ]
    for measure in measures:
        dax_lines.append(measure["dax"])
        dax_lines.append("")
    (POWERBI_DIR / "Project2_Measures.dax").write_text("\n".join(dax_lines), encoding="utf-8")

    lines = ["# Metric Definitions", "", "Currency: USD. Forecast horizon: June 2026 to December 2027. Historical actuals: January 2024 to May 2026.", ""]
    for measure in measures:
        lines.extend(
            [
                f"## {measure['display_name']}",
                "",
                f"- Business definition: {measure['definition']}",
                f"- DAX: `{measure['dax']}`",
                f"- Unit: {measure['unit']}",
                f"- Format: `{measure['format']}`",
                "- Filter context: Current report/page/visual filters.",
                "",
            ]
        )
    (MODEL_DIR / "metric_definitions.md").write_text("\n".join(lines), encoding="utf-8")


def write_power_query() -> None:
    prepared_root = str(PREPARED_DIR).replace("\\", "\\\\") + "\\\\"
    tables = [
        "fact_revenue_driver",
        "fact_cost_driver",
        "fact_headcount_plan",
        "fact_opex_driver",
        "fact_cash_impact",
        "fact_forecast_accuracy",
        "dim_date",
        "dim_scenario",
        "dim_service",
        "dim_region",
        "dim_customer_segment",
        "dim_department",
        "what_if_parameters",
    ]
    lines = [
        "// Power Query M snippets for Project 02 - Driver-Based Forecasting",
        "// Create a text parameter named PreparedRoot with this value:",
        f"// {prepared_root}",
        "",
        "let",
        f'    PreparedRoot = "{prepared_root}"',
        "in",
        "    PreparedRoot",
        "",
    ]
    for table in tables:
        query_name = "".join(part.capitalize() for part in table.split("_"))
        lines.extend(
            [
                f"// Query: {query_name}",
                "let",
                f'    Source = Csv.Document(File.Contents(PreparedRoot & "{table}.csv"), [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]),',
                "    PromotedHeaders = Table.PromoteHeaders(Source, [PromoteAllScalars=true])",
                "in",
                "    PromotedHeaders",
                "",
            ]
        )
    (POWERBI_DIR / "PowerQuery_M.txt").write_text("\n".join(lines), encoding="utf-8")


def write_relationship_map() -> None:
    relationships = [
        ("DimDate", "DateKey", "FactRevenueDriver", "DateKey", "1:*", "Single"),
        ("DimDate", "DateKey", "FactCostDriver", "DateKey", "1:*", "Single"),
        ("DimDate", "DateKey", "FactHeadcountPlan", "DateKey", "1:*", "Single"),
        ("DimDate", "DateKey", "FactOpexDriver", "DateKey", "1:*", "Single"),
        ("DimDate", "DateKey", "FactCashImpact", "DateKey", "1:*", "Single"),
        ("DimDate", "DateKey", "FactForecastAccuracy", "DateKey", "1:*", "Single"),
        ("DimScenario", "ScenarioKey", "FactRevenueDriver", "ScenarioKey", "1:*", "Single"),
        ("DimScenario", "ScenarioKey", "FactCostDriver", "ScenarioKey", "1:*", "Single"),
        ("DimScenario", "ScenarioKey", "FactHeadcountPlan", "ScenarioKey", "1:*", "Single"),
        ("DimScenario", "ScenarioKey", "FactOpexDriver", "ScenarioKey", "1:*", "Single"),
        ("DimScenario", "ScenarioKey", "FactCashImpact", "ScenarioKey", "1:*", "Single"),
        ("DimRegion", "RegionKey", "FactRevenueDriver", "RegionKey", "1:*", "Single"),
        ("DimRegion", "RegionKey", "FactCostDriver", "RegionKey", "1:*", "Single"),
        ("DimRegion", "RegionKey", "FactHeadcountPlan", "RegionKey", "1:*", "Single"),
        ("DimRegion", "RegionKey", "FactOpexDriver", "RegionKey", "1:*", "Single"),
        ("DimService", "ServiceKey", "FactRevenueDriver", "ServiceKey", "1:*", "Single"),
        ("DimService", "ServiceKey", "FactCostDriver", "ServiceKey", "1:*", "Single"),
        ("DimService", "ServiceKey", "FactForecastAccuracy", "ServiceKey", "1:*", "Single"),
        ("DimCustomerSegment", "SegmentKey", "FactRevenueDriver", "SegmentKey", "1:*", "Single"),
        ("DimCustomerSegment", "SegmentKey", "FactCostDriver", "SegmentKey", "1:*", "Single"),
        ("DimDepartment", "DepartmentKey", "FactHeadcountPlan", "DepartmentKey", "1:*", "Single"),
        ("DimDepartment", "DepartmentKey", "FactOpexDriver", "DepartmentKey", "1:*", "Single"),
    ]
    lines = [
        "# Relationship Map",
        "",
        "Use a star schema. Keep all filters single-direction from dimensions to facts.",
        "",
        "| From Table | From Column | To Table | To Column | Cardinality | Cross Filter |",
        "|---|---|---|---|---|---|",
    ]
    for row in relationships:
        lines.append("| " + " | ".join(row) + " |")
    lines.extend(
        [
            "",
            "## Notes",
            "",
            "- Do not create fact-to-fact relationships. Measures reconcile by shared conformed dimensions.",
            "- `FactCostDriver[RevenueDriverKey]` is retained for audit only; keep it hidden in report view.",
            "- `what_if_parameters` is disconnected and used as an assumptions reference table. For interactive sliders, create Power BI numeric parameters and connect them to adjusted measures.",
        ]
    )
    (MODEL_DIR / "relationship_map.md").write_text("\n".join(lines), encoding="utf-8")


def write_semantic_notes() -> None:
    lines = [
        "# Semantic Model Notes",
        "",
        "## Model Intent",
        "",
        "This model supports monthly business planning and scenario decisions, not only historical reporting. Actuals run through May 2026; forecast scenarios run from June 2026 through December 2027.",
        "",
        "## Fact Tables",
        "",
        "- `FactRevenueDriver`: volume, rate, surcharge, discount, and revenue by month/scenario/region/service/segment.",
        "- `FactCostDriver`: direct cost components tied to the same revenue-driver grain.",
        "- `FactHeadcountPlan`: FTE, hiring, attrition, salary and payroll by month/scenario/region/department.",
        "- `FactOpexDriver`: non-payroll OPEX by month/scenario/region/department.",
        "- `FactCashImpact`: monthly P&L-to-cash bridge by scenario.",
        "- `FactForecastAccuracy`: actual versus forecast revenue by month/horizon/region/service.",
        "",
        "## Dimensional Rules",
        "",
        "- `DimScenario` should be sorted by `SortOrder`: Actual, Base, Upside, Downside.",
        "- `DimDate[MonthName]` should be sorted by `DimDate[MonthNumber]`; `DimDate[YearMonth]` by `DimDate[MonthSort]`.",
        "- Hide technical keys after relationships are created.",
        "",
        "## What-if Guidance",
        "",
        "The `what_if_parameters` table documents the planning levers. In Power BI Desktop, create numeric What-if parameters for high-value levers such as Volume Growth %, Rate Change %, Direct Cost Inflation %, and DSO Days. Use these parameter values to create adjusted revenue, cost, and cash measures without overwriting the official Base/Upside/Downside scenarios.",
    ]
    (MODEL_DIR / "semantic_model_notes.md").write_text("\n".join(lines), encoding="utf-8")


def write_config_artifacts() -> None:
    dashboard_config = {
        "project": "Project 02 - Driver-Based Forecasting & Scenario Planning",
        "audience": ["CFO", "FP&A Manager", "Commercial Director", "Operations Director"],
        "business_goal": "Support planning and decision making with driver-based forecast scenarios, what-if levers, forecast P&L, cash impact, and forecast accuracy tracking.",
        "currency": "USD",
        "latest_actual_month": "2026-05-01",
        "forecast_horizon": "2026-06 to 2027-12",
        "prepared_data_path": str(PREPARED_DIR),
        "power_bi_desktop_path_found": True,
        "pbix_status": "Blocked for final PBIX build until Power BI Desktop UI build/save/refresh QA is completed. Microsoft documentation states PBIX/PBIP conversion is only available through Power BI Desktop File > Save as.",
    }
    write_json(CONFIG_DIR / "dashboard_config.json", dashboard_config)

    page_map = {
        "pages": [
            {
                "page": "01 Executive Planning Overview",
                "purpose": "Show scenario-level forecast P&L status and the main revenue, margin, EBITDA and cash implications.",
                "filters": ["Scenario", "Year", "Month", "Region"],
                "key_questions": ["Which scenario is on plan?", "How much revenue and EBITDA are at stake?", "What cash pressure appears by month?"],
                "visuals": ["KPI cards", "Revenue and EBITDA trend", "Scenario variance waterfall", "Cash bridge"],
            },
            {
                "page": "02 Revenue & Cost Drivers",
                "purpose": "Explain revenue movement through jobs, rate, mix, surcharge, discount and direct cost drivers.",
                "filters": ["Scenario", "Year", "Region", "Service Line", "Customer Segment"],
                "key_questions": ["Which service lines drive revenue?", "Where is margin quality improving or deteriorating?", "What variable-cost levers matter most?"],
                "visuals": ["Service revenue ranking", "Jobs vs revenue per job scatter", "Gross margin by segment", "Direct cost component stacked bar"],
            },
            {
                "page": "03 Headcount & Capacity Plan",
                "purpose": "Connect volume growth to capacity, hiring, payroll cost and productivity.",
                "filters": ["Scenario", "Year", "Region", "Department"],
                "key_questions": ["Does headcount match forecast volume?", "Which teams drive payroll growth?", "Where does productivity risk show up?"],
                "visuals": ["FTE trend", "Payroll by department", "Jobs per FTE", "Hiring and attrition table"],
            },
            {
                "page": "04 Cash & Forecast Accuracy",
                "purpose": "Show the cash impact of scenarios and whether forecast quality is good enough for planning decisions.",
                "filters": ["Scenario", "Year", "Service Line", "Region", "Forecast Horizon"],
                "key_questions": ["What happens to operating cash flow?", "How sensitive is cash to DSO/DPO?", "Where has forecast error been highest?"],
                "visuals": ["Operating cash flow trend", "Ending cash by scenario", "DSO/DPO cards", "MAPE and bias by horizon/service"],
            },
            {
                "page": "05 Detail & Exceptions",
                "purpose": "Provide lookup rows for low-margin services, high working-capital exposure, forecast-error outliers and headcount exceptions.",
                "filters": ["Scenario", "Year", "Region", "Service Line", "Department"],
                "key_questions": ["Which records need review before finalizing plan?", "Where should FP&A challenge assumptions?"],
                "visuals": ["Exception table", "Low margin table", "High MAPE table", "Headcount variance table"],
            },
        ]
    }
    write_json(CONFIG_DIR / "page_map.json", page_map)

    visual_map = {
        "global_slicers": {
            "Scenario": {"field": "DimScenario[Scenario]", "type": "dropdown", "sync_pages": "all", "sort": "DimScenario[SortOrder]"},
            "Year": {"field": "DimDate[Year]", "type": "dropdown", "sync_pages": "all"},
            "Month": {"field": "DimDate[YearMonth]", "type": "dropdown", "sync_pages": "all"},
            "Region": {"field": "DimRegion[Region]", "type": "dropdown", "sync_pages": "all"},
        },
        "visuals": [
            {"page": "01 Executive Planning Overview", "visual": "Revenue card", "type": "card", "measure": "[Revenue]"},
            {"page": "01 Executive Planning Overview", "visual": "EBITDA card", "type": "card", "measure": "[EBITDA]"},
            {"page": "01 Executive Planning Overview", "visual": "Gross Margin card", "type": "card", "measure": "[Gross Margin %]"},
            {"page": "01 Executive Planning Overview", "visual": "Ending Cash card", "type": "card", "measure": "[Ending Cash Latest Month]"},
            {"page": "01 Executive Planning Overview", "visual": "Revenue and EBITDA trend", "type": "combo line and column", "axis": "DimDate[YearMonth]", "values": ["[Revenue]", "[EBITDA]"], "legend": "DimScenario[Scenario]"},
            {"page": "02 Revenue & Cost Drivers", "visual": "Service revenue ranking", "type": "bar", "axis": "DimService[ServiceLine]", "value": "[Revenue]", "sort": "descending"},
            {"page": "02 Revenue & Cost Drivers", "visual": "Jobs vs revenue per job", "type": "scatter", "x": "[Jobs]", "y": "[Revenue per Job]", "size": "[Revenue]", "legend": "DimService[ServiceLine]"},
            {"page": "03 Headcount & Capacity Plan", "visual": "FTE trend", "type": "line", "axis": "DimDate[YearMonth]", "value": "[Average FTE]", "legend": "DimScenario[Scenario]"},
            {"page": "03 Headcount & Capacity Plan", "visual": "Payroll by department", "type": "stacked bar", "axis": "DimDepartment[Department]", "value": "[Payroll Cost]", "legend": "DimScenario[Scenario]"},
            {"page": "04 Cash & Forecast Accuracy", "visual": "Operating cash flow trend", "type": "line", "axis": "DimDate[YearMonth]", "value": "[Operating Cash Flow]", "legend": "DimScenario[Scenario]"},
            {"page": "04 Cash & Forecast Accuracy", "visual": "Forecast MAPE by horizon", "type": "column", "axis": "FactForecastAccuracy[ForecastHorizonMonths]", "value": "[MAPE]"},
            {"page": "05 Detail & Exceptions", "visual": "Exception table", "type": "table", "columns": ["MonthStart", "Scenario", "Region", "ServiceLine", "Revenue", "Gross Margin %", "MAPE"]},
        ],
        "bookmarks": ["Reset filters", "Base case focus", "Cash risk focus"],
        "interaction_rules": ["Scenario slicer filters all visuals", "Forecast accuracy visuals ignore Actual scenario slicer when needed", "Detail tables drill through from service and region visuals"],
    }
    write_json(CONFIG_DIR / "visual_map.json", visual_map)

    theme = {
        "name": "Project 02 - Driver-Based Forecasting Planning Executive",
        "dataColors": ["#2454A6", "#2A9D8F", "#D99A2B", "#C43E3E", "#7C3AED", "#5C6B73", "#00838F", "#9C6644"],
        "background": "#F7F8FA",
        "foreground": "#1C2530",
        "tableAccent": "#2454A6",
        "visualStyles": {
            "*": {
                "*": {
                    "title": [{"fontColor": {"solid": {"color": "#1C2530"}}, "fontSize": 11}],
                    "labels": [{"color": {"solid": {"color": "#3B4652"}}}],
                    "background": [{"color": {"solid": {"color": "#FFFFFF"}}, "transparency": 0}],
                    "border": [{"show": True, "color": {"solid": {"color": "#D9DEE7"}}, "radius": 4}],
                }
            },
            "card": {"*": {"categoryLabels": [{"fontColor": {"solid": {"color": "#5C6B73"}}}], "labels": [{"fontColor": {"solid": {"color": "#1C2530"}}, "fontSize": 18}]}},
        },
    }
    write_json(CONFIG_DIR / "theme.json", theme)


def write_docs(revenue: pd.DataFrame, cost: pd.DataFrame, cash: pd.DataFrame, accuracy: pd.DataFrame) -> None:
    actual_revenue = revenue.loc[revenue["ScenarioKey"] == "ACTUAL", "RevenueUSD"].sum()
    base_revenue = revenue.loc[revenue["ScenarioKey"] == "BASE", "RevenueUSD"].sum()
    upside_revenue = revenue.loc[revenue["ScenarioKey"] == "UPSIDE", "RevenueUSD"].sum()
    downside_revenue = revenue.loc[revenue["ScenarioKey"] == "DOWNSIDE", "RevenueUSD"].sum()
    base_cost = cost.loc[cost["ScenarioKey"] == "BASE", "DirectCostUSD"].sum()
    base_cash = cash.loc[cash["ScenarioKey"] == "BASE"].sort_values("MonthStart")["EndingCashUSD"].iloc[-1]
    mape = accuracy["AbsolutePctError"].mean()

    readme = [
        "# Project 02 - Driver-Based Forecasting & Scenario Planning",
        "",
        "## Objective",
        "",
        "Build a Power BI planning product that helps FP&A and business leaders compare Base, Upside and Downside scenarios, test key drivers, review forecast P&L, understand cash impact and monitor forecast accuracy.",
        "",
        "## Status",
        "",
        "- Data, model specs, DAX, Power Query snippets, theme, page map, visual map, QA and preview screenshots are ready.",
        "- Final PBIX is not marked complete until `output/dashboard_final.pbix` is built, opened, refreshed and saved in Power BI Desktop.",
        "- Power BI Desktop is installed on this machine, but Microsoft documents PBIX/PBIP conversion as a Desktop UI save action rather than a scriptable API.",
        "",
        "## Core Dataset",
        "",
        "- Raw source: `data/raw/driver_forecasting_raw.xlsx`",
        "- Prepared data: `data/prepared/*.csv`",
        "- Actual period: Jan 2024 to May 2026",
        "- Forecast period: Jun 2026 to Dec 2027",
        "- Scenarios: Actual, Base, Upside, Downside",
        "",
        "## Key Portfolio Signals",
        "",
        f"- Historical actual revenue: {money(actual_revenue)}",
        f"- Base forecast revenue: {money(base_revenue)}",
        f"- Upside forecast revenue: {money(upside_revenue)}",
        f"- Downside forecast revenue: {money(downside_revenue)}",
        f"- Base direct cost: {money(base_cost)}",
        f"- Base ending cash at forecast horizon: {money(base_cash)}",
        f"- Historical forecast MAPE: {pct(mape)}",
        "",
        "## Build Order",
        "",
        "1. Run `python build/scripts/00_generate_synthetic_raw.py`.",
        "2. Run `python build/scripts/01_profile_data.py`.",
        "3. Run `python build/scripts/02_prepare_data.py`.",
        "4. Run `python build/scripts/03_validate_prepared_data.py`.",
        "5. Run `python build/scripts/04_generate_powerbi_artifacts.py`.",
        "6. Open Power BI Desktop, import prepared CSVs, create relationships, paste DAX measures and apply `build/config/theme.json`.",
        "7. Build pages using `build/config/page_map.json` and `build/config/visual_map.json`.",
        "8. Save as `output/dashboard_v01.pbix`, QA, then copy final reviewed version to `output/dashboard_final.pbix`.",
    ]
    (DOCS_DIR / "README.md").write_text("\n".join(readme), encoding="utf-8")

    handoff = [
        "# Handoff Notes",
        "",
        "## Output",
        "",
        "- Required final BI file: `output/dashboard_final.pbix`",
        "- Current status: `blocked for PBIX build` until Power BI Desktop UI build and QA are completed.",
        "- Prepared data: `data/prepared/`",
        "- DAX measures: `powerbi/Project2_Measures.dax`",
        "- Power Query snippets: `powerbi/PowerQuery_M.txt`",
        "- Theme: `build/config/theme.json`",
        "- Page and visual maps: `build/config/page_map.json`, `build/config/visual_map.json`",
        "",
        "## Pages",
        "",
        "1. Executive Planning Overview",
        "2. Revenue & Cost Drivers",
        "3. Headcount & Capacity Plan",
        "4. Cash & Forecast Accuracy",
        "5. Detail & Exceptions",
        "",
        "## Refresh Instructions",
        "",
        "1. Replace or regenerate `data/raw/driver_forecasting_raw.xlsx`.",
        "2. Re-run profile, prepare and validate scripts.",
        "3. Open PBIX and refresh all queries.",
        "4. Check `qa/reconciliation.xlsx` and `qa/qa_checklist.md` before promoting to final.",
        "",
        "## Known Issues",
        "",
        "- PBIX file is pending because creating/saving a PBIX must be completed in Power BI Desktop.",
        "- What-if sliders must be created inside Power BI Desktop if interactive numeric parameters are required; the assumptions table is already prepared.",
    ]
    (DOCS_DIR / "handoff_notes.md").write_text("\n".join(handoff), encoding="utf-8")

    changelog = [
        "# Changelog",
        "",
        "## v01 Build Pack",
        "",
        "- Created synthetic driver-based planning dataset.",
        "- Added actuals through May 2026 and Base/Upside/Downside forecast through December 2027.",
        "- Added revenue drivers, cost drivers, headcount plan, OPEX plan, cash impact and forecast accuracy tables.",
        "- Added prepared star-schema CSV extracts.",
        "- Added DAX measure map, Power Query snippets, relationship map, page map, visual map and Power BI theme.",
        "- Added reconciliation workbook and QA checklist.",
        "- Added preview screenshots for page design direction.",
    ]
    (DOCS_DIR / "changelog.md").write_text("\n".join(changelog), encoding="utf-8")

    issue_log = [
        "# Issue Log",
        "",
        "## ISSUE-001 - PBIX final build pending",
        "",
        "- Status: Open",
        "- Severity: Medium",
        "- Found in: v01 build pack",
        "- Page: File output",
        "- Expected: `output/dashboard_final.pbix` exists and passes open/save/refresh QA.",
        "- Actual: Data/model/DAX/layout artifacts are ready; PBIX still needs to be built and tested in Power BI Desktop.",
        "- Root cause: Power BI Desktop PBIX creation is a UI save workflow, not exposed as a reliable local script API.",
        "- Fix: Build in Power BI Desktop using the prepared artifacts, save `dashboard_v01.pbix`, run QA, then promote to `dashboard_final.pbix`.",
    ]
    (DOCS_DIR / "issue_log.md").write_text("\n".join(issue_log), encoding="utf-8")


def create_preview_screenshots(revenue: pd.DataFrame, cost: pd.DataFrame, headcount: pd.DataFrame, cash: pd.DataFrame, accuracy: pd.DataFrame) -> None:
    SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

    revenue["MonthStart"] = pd.to_datetime(revenue["MonthStart"])
    cost["MonthStart"] = pd.to_datetime(cost["MonthStart"])
    headcount["MonthStart"] = pd.to_datetime(headcount["MonthStart"])
    cash["MonthStart"] = pd.to_datetime(cash["MonthStart"])
    accuracy["MonthStart"] = pd.to_datetime(accuracy["MonthStart"])

    colors = {"Actual": "#5C6B73", "Base": "#2454A6", "Upside": "#2A9D8F", "Downside": "#C43E3E"}
    scenario_label = {"ACTUAL": "Actual", "BASE": "Base", "UPSIDE": "Upside", "DOWNSIDE": "Downside"}

    # Page 1
    fig, axes = plt.subplots(2, 2, figsize=(16, 9))
    fig.suptitle("01 Executive Planning Overview", fontsize=18, fontweight="bold", x=0.02, ha="left")
    monthly = revenue.groupby(["MonthStart", "ScenarioKey"], as_index=False)["RevenueUSD"].sum()
    for key, label in scenario_label.items():
        subset = monthly[monthly["ScenarioKey"] == key]
        if not subset.empty:
            axes[0, 0].plot(subset["MonthStart"], subset["RevenueUSD"] / 1_000_000, label=label, color=colors[label], linewidth=2)
    axes[0, 0].set_title("Revenue by Scenario")
    axes[0, 0].set_ylabel("USD M")
    axes[0, 0].legend()
    pnl = (
        revenue.groupby("ScenarioKey", as_index=False)["RevenueUSD"].sum()
        .merge(cost.groupby("ScenarioKey", as_index=False)["DirectCostUSD"].sum(), on="ScenarioKey")
    )
    pnl["GrossMarginPct"] = (pnl["RevenueUSD"] - pnl["DirectCostUSD"]) / pnl["RevenueUSD"]
    axes[0, 1].bar([scenario_label.get(x, x) for x in pnl["ScenarioKey"]], pnl["GrossMarginPct"] * 100, color=[colors.get(scenario_label.get(x, x), "#2454A6") for x in pnl["ScenarioKey"]])
    axes[0, 1].set_title("Gross Margin %")
    axes[0, 1].set_ylabel("%")
    cash_base = cash[cash["ScenarioKey"].isin(["BASE", "UPSIDE", "DOWNSIDE"])]
    for key, label in scenario_label.items():
        subset = cash_base[cash_base["ScenarioKey"] == key]
        if not subset.empty:
            axes[1, 0].plot(subset["MonthStart"], subset["EndingCashUSD"] / 1_000_000, label=label, color=colors[label], linewidth=2)
    axes[1, 0].set_title("Ending Cash")
    axes[1, 0].set_ylabel("USD M")
    axes[1, 0].legend()
    scen_rev = pnl[pnl["ScenarioKey"].isin(["BASE", "UPSIDE", "DOWNSIDE"])].copy()
    axes[1, 1].bar(
        [scenario_label[x] for x in scen_rev["ScenarioKey"]],
        scen_rev["RevenueUSD"] / 1_000_000,
        color=[colors[scenario_label[x]] for x in scen_rev["ScenarioKey"]],
    )
    axes[1, 1].set_title("Forecast Revenue")
    axes[1, 1].set_ylabel("USD M")
    fig.tight_layout(rect=[0, 0, 1, 0.94])
    fig.savefig(SCREENSHOT_DIR / "page_01_executive_overview.png", dpi=140)
    plt.close(fig)

    # Page 2
    fig, axes = plt.subplots(2, 2, figsize=(16, 9))
    fig.suptitle("02 Revenue & Cost Drivers", fontsize=18, fontweight="bold", x=0.02, ha="left")
    service_rev = revenue[revenue["ScenarioKey"] == "BASE"].groupby("ServiceKey", as_index=False).agg(RevenueUSD=("RevenueUSD", "sum"), Jobs=("VolumeJobs", "sum"))
    service_dim = read_csv("dim_service")
    service_rev = service_rev.merge(service_dim[["ServiceKey", "ServiceLine"]], on="ServiceKey")
    service_rev = service_rev.sort_values("RevenueUSD")
    axes[0, 0].barh(service_rev["ServiceLine"], service_rev["RevenueUSD"] / 1_000_000, color="#2454A6")
    axes[0, 0].set_title("Base Revenue by Service")
    axes[0, 0].set_xlabel("USD M")
    service_cost = cost[cost["ScenarioKey"] == "BASE"].groupby("ServiceKey", as_index=False)["DirectCostUSD"].sum().merge(service_rev[["ServiceKey", "RevenueUSD", "ServiceLine"]], on="ServiceKey")
    service_cost["GrossMarginPct"] = (service_cost["RevenueUSD"] - service_cost["DirectCostUSD"]) / service_cost["RevenueUSD"]
    axes[0, 1].bar(service_cost["ServiceLine"], service_cost["GrossMarginPct"] * 100, color="#2A9D8F")
    axes[0, 1].set_title("Base Gross Margin by Service")
    axes[0, 1].tick_params(axis="x", rotation=30)
    axes[1, 0].scatter(service_rev["Jobs"], service_rev["RevenueUSD"] / service_rev["Jobs"], s=service_rev["RevenueUSD"] / 15000, color="#D99A2B", alpha=0.75)
    for _, row in service_rev.iterrows():
        axes[1, 0].annotate(row["ServiceLine"], (row["Jobs"], row["RevenueUSD"] / row["Jobs"]), fontsize=8)
    axes[1, 0].set_title("Jobs vs Revenue per Job")
    axes[1, 0].set_xlabel("Jobs")
    axes[1, 0].set_ylabel("USD / Job")
    component = cost[cost["ScenarioKey"] == "BASE"][["CarrierCostUSD", "HandlingCostUSD", "FuelCostUSD", "CustomsCostUSD"]].sum() / 1_000_000
    axes[1, 1].bar(component.index.str.replace("USD", ""), component.values, color=["#2454A6", "#2A9D8F", "#D99A2B", "#7C3AED"])
    axes[1, 1].set_title("Direct Cost Components")
    axes[1, 1].set_ylabel("USD M")
    fig.tight_layout(rect=[0, 0, 1, 0.94])
    fig.savefig(SCREENSHOT_DIR / "page_02_revenue_cost_drivers.png", dpi=140)
    plt.close(fig)

    # Page 3
    fig, axes = plt.subplots(2, 2, figsize=(16, 9))
    fig.suptitle("03 Headcount & Capacity Plan", fontsize=18, fontweight="bold", x=0.02, ha="left")
    hc_month = headcount[headcount["ScenarioKey"].isin(["BASE", "UPSIDE", "DOWNSIDE"])].groupby(["MonthStart", "ScenarioKey"], as_index=False)["FTE"].sum()
    for key in ["BASE", "UPSIDE", "DOWNSIDE"]:
        subset = hc_month[hc_month["ScenarioKey"] == key]
        axes[0, 0].plot(subset["MonthStart"], subset["FTE"], label=scenario_label[key], color=colors[scenario_label[key]], linewidth=2)
    axes[0, 0].set_title("FTE by Scenario")
    axes[0, 0].legend()
    dept_dim = read_csv("dim_department")
    payroll = headcount[headcount["ScenarioKey"] == "BASE"].groupby("DepartmentKey", as_index=False)["PayrollCostUSD"].sum().merge(dept_dim[["DepartmentKey", "Department"]], on="DepartmentKey")
    axes[0, 1].barh(payroll["Department"], payroll["PayrollCostUSD"] / 1_000_000, color="#2454A6")
    axes[0, 1].set_title("Base Payroll by Department")
    axes[0, 1].set_xlabel("USD M")
    jobs_month = revenue[revenue["ScenarioKey"] == "BASE"].groupby("MonthStart", as_index=False)["VolumeJobs"].sum()
    fte_month = headcount[headcount["ScenarioKey"] == "BASE"].groupby("MonthStart", as_index=False)["FTE"].sum()
    productivity = jobs_month.merge(fte_month, on="MonthStart")
    axes[1, 0].plot(productivity["MonthStart"], productivity["VolumeJobs"] / productivity["FTE"], color="#2A9D8F", linewidth=2)
    axes[1, 0].set_title("Jobs per FTE")
    hires = headcount[headcount["ScenarioKey"] == "BASE"].groupby("DepartmentKey", as_index=False)[["NewHires", "Attrition"]].sum().merge(dept_dim[["DepartmentKey", "Department"]], on="DepartmentKey")
    axes[1, 1].bar(hires["Department"], hires["NewHires"], label="New Hires", color="#2A9D8F")
    axes[1, 1].bar(hires["Department"], -hires["Attrition"], label="Attrition", color="#C43E3E")
    axes[1, 1].set_title("Hiring vs Attrition")
    axes[1, 1].tick_params(axis="x", rotation=30)
    axes[1, 1].legend()
    fig.tight_layout(rect=[0, 0, 1, 0.94])
    fig.savefig(SCREENSHOT_DIR / "page_03_headcount_capacity.png", dpi=140)
    plt.close(fig)

    # Page 4
    fig, axes = plt.subplots(2, 2, figsize=(16, 9))
    fig.suptitle("04 Cash & Forecast Accuracy", fontsize=18, fontweight="bold", x=0.02, ha="left")
    for key in ["BASE", "UPSIDE", "DOWNSIDE"]:
        subset = cash[cash["ScenarioKey"] == key]
        axes[0, 0].plot(subset["MonthStart"], subset["OperatingCashFlowUSD"] / 1_000_000, label=scenario_label[key], color=colors[scenario_label[key]], linewidth=2)
    axes[0, 0].set_title("Operating Cash Flow")
    axes[0, 0].set_ylabel("USD M")
    axes[0, 0].legend()
    wc = cash[cash["ScenarioKey"].isin(["BASE", "UPSIDE", "DOWNSIDE"])].groupby("ScenarioKey", as_index=False)["WorkingCapitalUSD"].mean()
    axes[0, 1].bar(
        [scenario_label[x] for x in wc["ScenarioKey"]],
        wc["WorkingCapitalUSD"] / 1_000_000,
        color=[colors[scenario_label[x]] for x in wc["ScenarioKey"]],
    )
    axes[0, 1].set_title("Average Working Capital")
    axes[0, 1].set_ylabel("USD M")
    mape = accuracy.groupby("ForecastHorizonMonths", as_index=False)["AbsolutePctError"].mean()
    axes[1, 0].bar(mape["ForecastHorizonMonths"].astype(str) + "M", mape["AbsolutePctError"] * 100, color="#D99A2B")
    axes[1, 0].set_title("MAPE by Forecast Horizon")
    axes[1, 0].set_ylabel("%")
    svc_acc = accuracy.groupby("ServiceKey", as_index=False)["AbsolutePctError"].mean().merge(read_csv("dim_service")[["ServiceKey", "ServiceLine"]], on="ServiceKey").sort_values("AbsolutePctError")
    axes[1, 1].barh(svc_acc["ServiceLine"], svc_acc["AbsolutePctError"] * 100, color="#7C3AED")
    axes[1, 1].set_title("MAPE by Service")
    axes[1, 1].set_xlabel("%")
    fig.tight_layout(rect=[0, 0, 1, 0.94])
    fig.savefig(SCREENSHOT_DIR / "page_04_cash_accuracy.png", dpi=140)
    plt.close(fig)


def write_html_preview() -> None:
    images = [
        ("Executive Planning Overview", "page_01_executive_overview.png"),
        ("Revenue & Cost Drivers", "page_02_revenue_cost_drivers.png"),
        ("Headcount & Capacity Plan", "page_03_headcount_capacity.png"),
        ("Cash & Forecast Accuracy", "page_04_cash_accuracy.png"),
    ]
    cards = "\n".join(
        f'<section><h2>{title}</h2><img src="../screenshots/{filename}" alt="{title}"></section>'
        for title, filename in images
    )
    html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Project 02 - Driver-Based Forecasting Power BI Preview</title>
  <style>
    body {{ margin: 0; font-family: Segoe UI, Arial, sans-serif; background: #f7f8fa; color: #1c2530; }}
    header {{ padding: 28px 40px 12px; background: #fff; border-bottom: 1px solid #d9dee7; }}
    h1 {{ margin: 0; font-size: 28px; }}
    p {{ color: #5c6b73; max-width: 920px; }}
    main {{ padding: 22px 40px 40px; }}
    section {{ margin: 0 0 26px; background: #fff; border: 1px solid #d9dee7; border-radius: 6px; padding: 18px; }}
    h2 {{ font-size: 18px; margin: 0 0 12px; }}
    img {{ width: 100%; height: auto; display: block; border: 1px solid #e6eaf0; }}
  </style>
</head>
<body>
  <header>
    <h1>Project 02 - Driver-Based Forecasting & Scenario Planning</h1>
    <p>Static preview for Power BI build direction. This is not a PBIX substitute; use the prepared data, DAX, theme and page maps to build and QA the final Power BI file.</p>
  </header>
  <main>
    {cards}
  </main>
</body>
</html>
"""
    (EXPORT_DIR / "dashboard_preview.html").write_text(html, encoding="utf-8")


def write_build_instructions() -> None:
    lines = [
        "# Power BI Build Instructions",
        "",
        "## 1. Import Data",
        "",
        "Use `powerbi/PowerQuery_M.txt` as the query source pattern. Import every CSV from `data/prepared/` in Import mode.",
        "",
        "## 2. Rename Tables",
        "",
        "- `fact_revenue_driver` -> `FactRevenueDriver`",
        "- `fact_cost_driver` -> `FactCostDriver`",
        "- `fact_headcount_plan` -> `FactHeadcountPlan`",
        "- `fact_opex_driver` -> `FactOpexDriver`",
        "- `fact_cash_impact` -> `FactCashImpact`",
        "- `fact_forecast_accuracy` -> `FactForecastAccuracy`",
        "- `dim_date` -> `DimDate`",
        "- `dim_scenario` -> `DimScenario`",
        "- `dim_service` -> `DimService`",
        "- `dim_region` -> `DimRegion`",
        "- `dim_customer_segment` -> `DimCustomerSegment`",
        "- `dim_department` -> `DimDepartment`",
        "- `what_if_parameters` -> `WhatIfParameters`",
        "",
        "## 3. Relationships",
        "",
        "Build relationships exactly as listed in `model/relationship_map.md`. Use single-direction filtering from dimensions to facts.",
        "",
        "## 4. Measures",
        "",
        "Create a blank measure table named `KPI_Measures`, then paste measures from `powerbi/Project2_Measures.dax`.",
        "",
        "## 5. Theme and Pages",
        "",
        "Import `build/config/theme.json`. Build pages using `build/config/page_map.json` and `build/config/visual_map.json`.",
        "",
        "## 6. Save and QA",
        "",
        "Save as `output/dashboard_v01.pbix`, refresh, run QA from `qa/qa_checklist.md`, then promote to `output/dashboard_final.pbix` once open/save/refresh and visual QA pass.",
    ]
    (POWERBI_DIR / "Build_Instructions.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    for directory in [MODEL_DIR, CONFIG_DIR, POWERBI_DIR, DOCS_DIR, SCREENSHOT_DIR, EXPORT_DIR]:
        directory.mkdir(parents=True, exist_ok=True)

    revenue = read_csv("fact_revenue_driver")
    cost = read_csv("fact_cost_driver")
    headcount = read_csv("fact_headcount_plan")
    opex = read_csv("fact_opex_driver")
    cash = read_csv("fact_cash_impact")
    accuracy = read_csv("fact_forecast_accuracy")

    measures = build_measure_map()
    write_metric_artifacts(measures)
    write_power_query()
    write_relationship_map()
    write_semantic_notes()
    write_config_artifacts()
    write_docs(revenue, cost, cash, accuracy)
    write_build_instructions()
    create_preview_screenshots(revenue, cost, headcount, cash, accuracy)
    write_html_preview()

    status_path = OUTPUT_DIR / "dashboard_final.pbix.status.txt"
    status_path.write_text(
        "PBIX final is pending. Build in Power BI Desktop using docs/handoff_notes.md and powerbi/Build_Instructions.md, then save as output/dashboard_final.pbix after QA.\n",
        encoding="utf-8",
    )
    print("Generated Power BI build artifacts.")
    print(f"Preview: {EXPORT_DIR / 'dashboard_preview.html'}")
    print(f"PBIX status: {status_path}")


if __name__ == "__main__":
    main()
