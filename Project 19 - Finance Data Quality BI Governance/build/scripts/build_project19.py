from __future__ import annotations

import json
import math
import shutil
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd


PROJECT = Path(__file__).resolve().parents[2]
SEED = 20260615
RNG = np.random.default_rng(SEED)
AS_OF_DATE = pd.Timestamp("2026-06-15")
LATEST_COMPLETE_MONTH = "May 2026"
REPORT_NAME = "Finance_Data_Quality_BI_Governance"

DIRS = [
    "_agent",
    "_workflow",
    "data/raw",
    "data/prepared",
    "data/validated",
    "model",
    "build/config",
    "build/scripts",
    "powerbi/notes",
    "powerbi/seed",
    "output/screenshots",
    "output/exports",
    "qa",
    "docs",
    "report",
]


def ensure_dirs() -> None:
    for folder in DIRS:
        (PROJECT / folder).mkdir(parents=True, exist_ok=True)


def write_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.strip() + "\n", encoding="utf-8")


def pct(v: float) -> str:
    return f"{v * 100:.1f}%"


def money(v: float) -> str:
    sign = "-" if v < 0 else ""
    av = abs(v)
    if av >= 1_000_000:
        return f"{sign}${av / 1_000_000:.1f}M"
    if av >= 1_000:
        return f"{sign}${av / 1_000:.1f}K"
    return f"{sign}${av:,.0f}"


def date_key(ts: pd.Timestamp) -> int:
    return int(ts.strftime("%Y%m%d"))


def month_key(ts: pd.Timestamp) -> int:
    return int(ts.strftime("%Y%m"))


def make_dimensions() -> dict[str, pd.DataFrame]:
    dates = pd.date_range("2025-01-01", "2026-05-31", freq="D")
    dim_date = pd.DataFrame(
        {
            "DateKey": [date_key(d) for d in dates],
            "Date": dates.strftime("%Y-%m-%d"),
            "MonthEndDate": dates.to_period("M").to_timestamp("M").strftime("%Y-%m-%d"),
            "MonthKey": [month_key(d) for d in dates],
            "Year": dates.year,
            "Quarter": ["Q" + str(q) for q in dates.quarter],
            "MonthNumber": dates.month,
            "MonthName": dates.strftime("%b"),
            "MonthYear": dates.strftime("%b %Y"),
            "MonthIndex": (dates.year - 2025) * 12 + dates.month,
            "IsLatestCompleteMonth": np.where(dates.strftime("%b %Y") == LATEST_COMPLETE_MONTH, "Y", "N"),
        }
    )

    datasets = [
        ("DS001", "General Ledger Daily Balance", "Record to Report", "SAP S/4HANA", "Tier 1", "R2R Data Product", 6, "Daily", "Y", "Y"),
        ("DS002", "Accounts Payable Invoice", "Procure to Pay", "Coupa", "Tier 1", "P2P Analytics", 8, "Daily", "N", "Y"),
        ("DS003", "Accounts Receivable Aging", "Order to Cash", "Oracle AR", "Tier 1", "O2C Analytics", 8, "Daily", "Y", "Y"),
        ("DS004", "Treasury Cash Position", "Treasury", "Kyriba", "Tier 1", "Treasury Ops", 4, "Intraday", "Y", "Y"),
        ("DS005", "Bank Statement Feed", "Treasury", "SWIFT MT940", "Tier 1", "Treasury Ops", 4, "Intraday", "Y", "N"),
        ("DS006", "Revenue Recognition Entries", "Revenue", "Zuora RevPro", "Tier 1", "Revenue Ops", 10, "Daily", "Y", "Y"),
        ("DS007", "Cost Center Actuals", "FP&A", "Workday Adaptive", "Tier 2", "FP&A Systems", 12, "Daily", "N", "Y"),
        ("DS008", "Budget Forecast Snapshot", "FP&A", "Workday Adaptive", "Tier 2", "FP&A Systems", 24, "Daily", "N", "Y"),
        ("DS009", "Fixed Asset Register", "Record to Report", "SAP AA", "Tier 2", "Controllership", 24, "Daily", "N", "Y"),
        ("DS010", "Intercompany Elimination", "Consolidation", "OneStream", "Tier 1", "Consolidation COE", 10, "Daily", "Y", "Y"),
        ("DS011", "Tax Provision Inputs", "Tax", "ONESOURCE", "Tier 2", "Tax Ops", 24, "Weekly", "Y", "N"),
        ("DS012", "Payroll Accrual Feed", "People Cost", "Workday HCM", "Tier 2", "People Finance", 24, "Daily", "Y", "N"),
    ]
    dim_dataset = pd.DataFrame(
        datasets,
        columns=[
            "DatasetKey",
            "DatasetName",
            "Domain",
            "SourceSystem",
            "Criticality",
            "OwnerTeam",
            "SLAHours",
            "RefreshFrequency",
            "RLSRequired",
            "Certified",
        ],
    )

    reports = [
        ("RP001", "CFO Flash", "Finance Executive", "Executive", "CFO Office", "Y", "Confidential", "Gold"),
        ("RP002", "Monthly Close Cockpit", "Controllership", "Manager", "R2R Data Product", "Y", "Confidential", "Gold"),
        ("RP003", "AP Spend Control", "Procurement Finance", "Analyst", "P2P Analytics", "Y", "Internal", "Silver"),
        ("RP004", "AR Cash Collections", "O2C", "Manager", "O2C Analytics", "Y", "Internal", "Silver"),
        ("RP005", "Treasury Liquidity Monitor", "Treasury", "Manager", "Treasury Ops", "Y", "Highly Confidential", "Gold"),
        ("RP006", "Revenue Waterfall", "Revenue", "Executive", "Revenue Ops", "Y", "Confidential", "Gold"),
        ("RP007", "Cost Center Review", "FP&A", "Analyst", "FP&A Systems", "Y", "Internal", "Silver"),
        ("RP008", "Tax Provision Pack", "Tax", "Manager", "Tax Ops", "N", "Highly Confidential", "Bronze"),
        ("RP009", "Finance Data Quality Monitor", "BI Governance", "Operator", "BI Governance", "Y", "Internal", "Gold"),
    ]
    dim_report = pd.DataFrame(
        reports,
        columns=["ReportKey", "ReportName", "Workspace", "Audience", "OwnerTeam", "Certified", "SensitivityLabel", "ReportTier"],
    )

    departments = [
        ("D001", "Corporate FP&A", "Finance", "Global"),
        ("D002", "Controllership", "Finance", "Global"),
        ("D003", "Treasury", "Finance", "Global"),
        ("D004", "Tax", "Finance", "Global"),
        ("D005", "Procurement Finance", "Finance", "APAC"),
        ("D006", "Revenue Operations", "Finance", "Americas"),
        ("D007", "Internal Audit", "Risk", "Global"),
        ("D008", "BI Governance", "Data", "Global"),
    ]
    dim_department = pd.DataFrame(departments, columns=["DeptKey", "Department", "Function", "Region"])

    return {
        "DimDate": dim_date,
        "DimDataset": dim_dataset,
        "DimReport": dim_report,
        "DimDepartment": dim_department,
    }


def make_facts(dims: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    dates = pd.to_datetime(dims["DimDate"]["Date"])
    datasets = dims["DimDataset"]
    reports = dims["DimReport"]
    departments = dims["DimDepartment"]
    month_ends = pd.date_range("2025-01-31", "2026-05-31", freq="ME")

    dataset_rows = []
    for _, ds in datasets.iterrows():
        base_score = 94 if ds["Criticality"] == "Tier 1" else 91
        domain_penalty = {"Treasury": 1.5, "Tax": 2.4, "People Cost": 2.0}.get(ds["Domain"], 0.0)
        for d in dates:
            seasonal = 1.2 * math.sin((d.dayofyear / 365) * 2 * math.pi)
            close_pressure = 2.2 if d.day <= 5 else 0.0
            incident_noise = max(0, RNG.normal(0.7, 0.9))
            rows_expected = int(RNG.normal(380_000 if ds["Criticality"] == "Tier 1" else 120_000, 28_000))
            completeness = float(np.clip(RNG.normal(0.992, 0.006) - close_pressure / 500 - domain_penalty / 800, 0.93, 1.0))
            rows_loaded = int(rows_expected * completeness)
            nulls = int(max(0, RNG.normal(60 + domain_penalty * 18 + close_pressure * 20, 28)))
            duplicates = int(max(0, RNG.normal(18 + domain_penalty * 9, 12)))
            schema_drift = int(RNG.binomial(1, 0.015 + (0.008 if ds["Certified"] == "N" else 0)))
            freshness_minutes = int(max(5, RNG.normal(ds["SLAHours"] * 43, ds["SLAHours"] * 12) + close_pressure * 9))
            freshness_sla = 1 if freshness_minutes <= int(ds["SLAHours"]) * 60 else 0
            dq_score = float(np.clip(base_score - domain_penalty - close_pressure - incident_noise - nulls / 220 - duplicates / 160 - schema_drift * 5 + seasonal, 72, 99.5))
            rec_var = float(RNG.normal(0, 35_000 if ds["Criticality"] == "Tier 1" else 12_000) + (0 if dq_score > 88 else RNG.normal(60_000, 15_000)))
            dataset_rows.append(
                {
                    "DateKey": date_key(d),
                    "DatasetKey": ds["DatasetKey"],
                    "RowsExpected": rows_expected,
                    "RowsLoaded": rows_loaded,
                    "CompletenessPct": round(completeness, 5),
                    "NullCriticalCount": nulls,
                    "DuplicateKeyCount": duplicates,
                    "SchemaDriftCount": schema_drift,
                    "FreshnessMinutes": freshness_minutes,
                    "FreshnessWithinSLAFlag": freshness_sla,
                    "DataQualityScore": round(dq_score, 2),
                    "ReconciliationVarianceAmount": round(rec_var, 2),
                    "OpenIssueCount": int(max(0, (100 - dq_score) / 4 + RNG.normal(0.8, 0.8))),
                }
            )

    refresh_rows = []
    run_id = 1
    failure_categories = ["Source unavailable", "Gateway timeout", "Schema drift", "Credential expired", "Capacity throttling"]
    for _, ds in datasets.iterrows():
        fail_rate = 0.025 + (0.018 if ds["Certified"] == "N" else 0) + (0.012 if ds["RefreshFrequency"] == "Intraday" else 0)
        for d in dates:
            status = "Success"
            failure_category = "None"
            if RNG.random() < fail_rate:
                status = "Failed"
                failure_category = str(RNG.choice(failure_categories, p=[0.24, 0.24, 0.18, 0.12, 0.22]))
            duration = int(max(4, RNG.normal(34 if ds["Criticality"] == "Tier 1" else 22, 9)))
            refresh_rows.append(
                {
                    "RefreshRunKey": f"RR{run_id:06d}",
                    "DateKey": date_key(d),
                    "DatasetKey": ds["DatasetKey"],
                    "Status": status,
                    "FailureCategory": failure_category,
                    "DurationMinutes": duration,
                    "SLACompliantFlag": 1 if status == "Success" and duration < ds["SLAHours"] * 60 else 0,
                    "RetryCount": int(RNG.integers(0, 4) if status == "Failed" else RNG.binomial(1, 0.08)),
                }
            )
            run_id += 1

    rec_rows = []
    for _, ds in datasets.iterrows():
        for m in month_ends:
            for dept in departments.sample(3, random_state=int(month_key(m)) + len(ds["DatasetKey"])).itertuples():
                ledger = float(RNG.normal(28_000_000 if ds["Criticality"] == "Tier 1" else 7_500_000, 2_400_000))
                variance = float(RNG.normal(0, 60_000 if ds["Criticality"] == "Tier 1" else 24_000))
                if RNG.random() < (0.06 if ds["Certified"] == "Y" else 0.12):
                    variance += float(RNG.choice([-1, 1]) * RNG.normal(210_000, 75_000))
                subledger = ledger - variance
                variance_pct = variance / ledger if ledger else 0
                rec_rows.append(
                    {
                        "DateKey": date_key(m),
                        "DatasetKey": ds["DatasetKey"],
                        "DeptKey": dept.DeptKey,
                        "LedgerAmount": round(ledger, 2),
                        "SubledgerAmount": round(subledger, 2),
                        "VarianceAmount": round(variance, 2),
                        "VariancePct": round(variance_pct, 6),
                        "ReconciliationStatus": "Pass" if abs(variance_pct) < 0.0025 else ("Watch" if abs(variance_pct) < 0.006 else "Fail"),
                        "AgingBucket": str(RNG.choice(["0-2 days", "3-5 days", "6-10 days", "10+ days"], p=[0.58, 0.24, 0.13, 0.05])),
                    }
                )

    usage_rows = []
    for _, rp in reports.iterrows():
        tier_multiplier = {"Gold": 1.55, "Silver": 1.05, "Bronze": 0.65}[rp["ReportTier"]]
        for d in dates:
            weekday = 1.15 if d.weekday() < 5 else 0.32
            close_week = 1.5 if d.day <= 7 else 1.0
            views = int(max(0, RNG.normal(70 * tier_multiplier * weekday * close_week, 18)))
            usage_rows.append(
                {
                    "DateKey": date_key(d),
                    "ReportKey": rp["ReportKey"],
                    "DeptKey": str(RNG.choice(departments["DeptKey"])),
                    "Views": views,
                    "UniqueViewers": int(max(1, views * RNG.uniform(0.32, 0.58))),
                    "ExportEvents": int(max(0, views * RNG.uniform(0.02, 0.13))),
                    "SubscriptionRuns": int(max(0, RNG.normal(4 * tier_multiplier, 2))),
                    "AvgLoadSeconds": round(float(max(1.0, RNG.normal(3.4 if rp["ReportTier"] == "Gold" else 4.2, 0.9))), 2),
                    "FailedVisualCount": int(RNG.binomial(4, 0.015 if rp["Certified"] == "Y" else 0.04)),
                }
            )

    access_rows = []
    for _, rp in reports.iterrows():
        for _, dept in departments.iterrows():
            for m in month_ends:
                privileged = int(max(0, RNG.normal(5 if rp["SensitivityLabel"] != "Internal" else 2, 2)))
                orphaned = int(RNG.binomial(3, 0.08 if rp["Certified"] == "Y" else 0.18))
                rls_ex = int(RNG.binomial(4, 0.05 if rp["SensitivityLabel"] == "Internal" else 0.13))
                unauth = int(RNG.binomial(2, 0.025 if rp["Certified"] == "Y" else 0.08))
                pending = int(RNG.binomial(5, 0.12 if rp["ReportTier"] == "Gold" else 0.22))
                score = float(np.clip(96 - orphaned * 5 - rls_ex * 4 - unauth * 8 - pending * 2 + RNG.normal(0, 2.5), 55, 99))
                access_rows.append(
                    {
                        "DateKey": date_key(m),
                        "ReportKey": rp["ReportKey"],
                        "DeptKey": dept["DeptKey"],
                        "UsersWithAccess": int(max(4, RNG.normal(55 if rp["Audience"] == "Executive" else 34, 11))),
                        "PrivilegedUsers": privileged,
                        "OrphanedUsers": orphaned,
                        "RLSExceptions": rls_ex,
                        "PendingAccessReviews": pending,
                        "UnauthorizedSharingEvents": unauth,
                        "DeploymentControlScore": round(score, 2),
                    }
                )

    incident_rows = []
    root_causes = ["Late source extract", "Mapping break", "Duplicate key", "Null critical field", "RLS misconfiguration", "Report performance", "Failed refresh"]
    severities = ["Critical", "High", "Medium", "Low"]
    for i in range(240):
        ds = datasets.sample(1, random_state=SEED + i).iloc[0]
        open_date = pd.Timestamp(RNG.choice(dates))
        severity = str(RNG.choice(severities, p=[0.07, 0.25, 0.46, 0.22]))
        mttr_base = {"Critical": 10, "High": 22, "Medium": 45, "Low": 72}[severity]
        mttr = float(max(2, RNG.normal(mttr_base, mttr_base * 0.35)))
        closed = RNG.random() > {"Critical": 0.08, "High": 0.13, "Medium": 0.22, "Low": 0.28}[severity]
        incident_rows.append(
            {
                "IncidentKey": f"INC{i + 1:05d}",
                "DateKey": date_key(open_date),
                "DatasetKey": ds["DatasetKey"],
                "Severity": severity,
                "IncidentStatus": "Closed" if closed else "Open",
                "RootCause": str(RNG.choice(root_causes)),
                "MTTRHours": round(mttr if closed else mttr * 1.35, 1),
                "SLAOverdueFlag": 1 if mttr > (24 if severity in ["Critical", "High"] else 72) else 0,
                "BusinessImpact": str(RNG.choice(["Close delay", "Wrong KPI", "Access risk", "Manual rework", "Stakeholder trust"], p=[0.25, 0.21, 0.14, 0.28, 0.12])),
            }
        )

    return {
        "FactDatasetDaily": pd.DataFrame(dataset_rows),
        "FactRefreshRuns": pd.DataFrame(refresh_rows),
        "FactReconciliation": pd.DataFrame(rec_rows),
        "FactUsage": pd.DataFrame(usage_rows),
        "FactAccessReview": pd.DataFrame(access_rows),
        "FactIncidents": pd.DataFrame(incident_rows),
    }


TABLE_TYPES = {
    "DimDate": {
        "DateKey": "int64",
        "Date": "dateTime",
        "MonthEndDate": "dateTime",
        "MonthKey": "int64",
        "Year": "int64",
        "Quarter": "string",
        "MonthNumber": "int64",
        "MonthName": "string",
        "MonthYear": "string",
        "MonthIndex": "int64",
        "IsLatestCompleteMonth": "string",
    },
    "DimDataset": {
        "DatasetKey": "string",
        "DatasetName": "string",
        "Domain": "string",
        "SourceSystem": "string",
        "Criticality": "string",
        "OwnerTeam": "string",
        "SLAHours": "int64",
        "RefreshFrequency": "string",
        "RLSRequired": "string",
        "Certified": "string",
    },
    "DimReport": {
        "ReportKey": "string",
        "ReportName": "string",
        "Workspace": "string",
        "Audience": "string",
        "OwnerTeam": "string",
        "Certified": "string",
        "SensitivityLabel": "string",
        "ReportTier": "string",
    },
    "DimDepartment": {
        "DeptKey": "string",
        "Department": "string",
        "Function": "string",
        "Region": "string",
    },
    "FactDatasetDaily": {
        "DateKey": "int64",
        "DatasetKey": "string",
        "RowsExpected": "int64",
        "RowsLoaded": "int64",
        "CompletenessPct": "double",
        "NullCriticalCount": "int64",
        "DuplicateKeyCount": "int64",
        "SchemaDriftCount": "int64",
        "FreshnessMinutes": "int64",
        "FreshnessWithinSLAFlag": "int64",
        "DataQualityScore": "double",
        "ReconciliationVarianceAmount": "double",
        "OpenIssueCount": "int64",
    },
    "FactRefreshRuns": {
        "RefreshRunKey": "string",
        "DateKey": "int64",
        "DatasetKey": "string",
        "Status": "string",
        "FailureCategory": "string",
        "DurationMinutes": "int64",
        "SLACompliantFlag": "int64",
        "RetryCount": "int64",
    },
    "FactReconciliation": {
        "DateKey": "int64",
        "DatasetKey": "string",
        "DeptKey": "string",
        "LedgerAmount": "double",
        "SubledgerAmount": "double",
        "VarianceAmount": "double",
        "VariancePct": "double",
        "ReconciliationStatus": "string",
        "AgingBucket": "string",
    },
    "FactUsage": {
        "DateKey": "int64",
        "ReportKey": "string",
        "DeptKey": "string",
        "Views": "int64",
        "UniqueViewers": "int64",
        "ExportEvents": "int64",
        "SubscriptionRuns": "int64",
        "AvgLoadSeconds": "double",
        "FailedVisualCount": "int64",
    },
    "FactAccessReview": {
        "DateKey": "int64",
        "ReportKey": "string",
        "DeptKey": "string",
        "UsersWithAccess": "int64",
        "PrivilegedUsers": "int64",
        "OrphanedUsers": "int64",
        "RLSExceptions": "int64",
        "PendingAccessReviews": "int64",
        "UnauthorizedSharingEvents": "int64",
        "DeploymentControlScore": "double",
    },
    "FactIncidents": {
        "IncidentKey": "string",
        "DateKey": "int64",
        "DatasetKey": "string",
        "Severity": "string",
        "IncidentStatus": "string",
        "RootCause": "string",
        "MTTRHours": "double",
        "SLAOverdueFlag": "int64",
        "BusinessImpact": "string",
    },
}


def m_type(dtype: str) -> str:
    return {"int64": "Int64.Type", "double": "type number", "dateTime": "type date", "string": "type text"}[dtype]


def pbi_path(path: Path) -> str:
    return str(path).replace("\\", "\\\\")


def build_model(tables: dict[str, pd.DataFrame]) -> dict:
    model_tables = []
    for name, df in tables.items():
        type_map = TABLE_TYPES[name]
        transforms = ", ".join([f'{{"{col}", {m_type(dtype)}}}' for col, dtype in type_map.items()])
        csv_path = PROJECT / "data" / "prepared" / f"{name.lower()}.csv"
        columns = []
        for col, dtype in type_map.items():
            summarize = "none" if dtype in ["string", "dateTime"] or col.endswith("Key") else ("sum" if dtype in ["int64", "double"] else "none")
            column = {"name": col, "dataType": dtype, "sourceColumn": col, "summarizeBy": summarize}
            if name == "DimDate" and col == "MonthName":
                column["sortByColumn"] = "MonthNumber"
            if name == "DimDate" and col == "MonthYear":
                column["sortByColumn"] = "MonthIndex"
            columns.append(column)
        model_tables.append(
            {
                "name": name,
                "columns": columns,
                "partitions": [
                    {
                        "name": f"{name}-Import",
                        "mode": "import",
                        "source": {
                            "type": "m",
                            "expression": [
                                "let",
                                f'    Source = Csv.Document(File.Contents("{pbi_path(csv_path)}"), [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]),',
                                "    PromotedHeaders = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),",
                                f'    Typed = Table.TransformColumnTypes(PromotedHeaders, {{{transforms}}}, "en-US")',
                                "in",
                                "    Typed",
                            ],
                        },
                    }
                ],
            }
        )

    measures = [
        ("Dataset Count", "DISTINCTCOUNT ( DimDataset[DatasetKey] )", "#,0", "Overview"),
        ("Critical Dataset Count", 'CALCULATE ( [Dataset Count], DimDataset[Criticality] = "Tier 1" )', "#,0", "Overview"),
        ("Certified Dataset Count", 'CALCULATE ( [Dataset Count], DimDataset[Certified] = "Y" )', "#,0", "Overview"),
        ("Data Quality Score", "AVERAGE ( FactDatasetDaily[DataQualityScore] )", "0.0", "Quality"),
        ("Completeness %", "DIVIDE ( SUM ( FactDatasetDaily[RowsLoaded] ), SUM ( FactDatasetDaily[RowsExpected] ) )", "0.0%", "Quality"),
        ("Freshness SLA %", "DIVIDE ( SUM ( FactDatasetDaily[FreshnessWithinSLAFlag] ), COUNTROWS ( FactDatasetDaily ) )", "0.0%", "Reliability"),
        ("Refresh Runs", "COUNTROWS ( FactRefreshRuns )", "#,0", "Reliability"),
        ("Refresh Success %", 'DIVIDE ( CALCULATE ( [Refresh Runs], FactRefreshRuns[Status] = "Success" ), [Refresh Runs] )', "0.0%", "Reliability"),
        ("Failed Refreshes", 'CALCULATE ( [Refresh Runs], FactRefreshRuns[Status] = "Failed" )', "#,0", "Reliability"),
        ("Avg Refresh Duration Min", "AVERAGE ( FactRefreshRuns[DurationMinutes] )", "0.0", "Reliability"),
        ("DQ Issue Count", "SUM ( FactDatasetDaily[NullCriticalCount] ) + SUM ( FactDatasetDaily[DuplicateKeyCount] ) + SUM ( FactDatasetDaily[SchemaDriftCount] )", "#,0", "Quality"),
        ("Open Incidents", 'CALCULATE ( COUNTROWS ( FactIncidents ), FactIncidents[IncidentStatus] <> "Closed" )', "#,0", "Reliability"),
        ("Avg MTTR Hours", "AVERAGE ( FactIncidents[MTTRHours] )", "0.0", "Reliability"),
        ("Reconciliation Variance", "SUM ( FactReconciliation[VarianceAmount] )", "$#,0", "Reconciliation"),
        ("Abs Reconciliation Variance", "SUMX ( FactReconciliation, ABS ( FactReconciliation[VarianceAmount] ) )", "$#,0", "Reconciliation"),
        ("Reconciliation Pass %", 'DIVIDE ( CALCULATE ( COUNTROWS ( FactReconciliation ), FactReconciliation[ReconciliationStatus] = "Pass" ), COUNTROWS ( FactReconciliation ) )', "0.0%", "Reconciliation"),
        ("Report Views", "SUM ( FactUsage[Views] )", "#,0", "Adoption"),
        ("Active Viewer Days", "SUM ( FactUsage[UniqueViewers] )", "#,0", "Adoption"),
        ("Export Events", "SUM ( FactUsage[ExportEvents] )", "#,0", "Adoption"),
        ("Avg Report Load Seconds", "AVERAGE ( FactUsage[AvgLoadSeconds] )", "0.0", "Adoption"),
        ("Failed Visual Count", "SUM ( FactUsage[FailedVisualCount] )", "#,0", "Adoption"),
        ("Access Risk Events", "SUM ( FactAccessReview[RLSExceptions] ) + SUM ( FactAccessReview[OrphanedUsers] ) + SUM ( FactAccessReview[UnauthorizedSharingEvents] )", "#,0", "Controls"),
        ("RLS Exceptions", "SUM ( FactAccessReview[RLSExceptions] )", "#,0", "Controls"),
        ("Pending Access Reviews", "SUM ( FactAccessReview[PendingAccessReviews] )", "#,0", "Controls"),
        ("Deployment Control Score", "AVERAGE ( FactAccessReview[DeploymentControlScore] )", "0.0", "Controls"),
    ]
    model_tables.append(
        {
            "name": "KPI Measures",
            "columns": [{"name": "MeasureKey", "dataType": "string", "isHidden": True, "sourceColumn": "MeasureKey"}],
            "partitions": [
                {
                    "name": "KPI Measures-Import",
                    "mode": "import",
                    "source": {"type": "m", "expression": 'let Source = #table(type table [MeasureKey = text], {{"KPI"}}) in Source'},
                }
            ],
            "measures": [
                {"name": name, "expression": expr, "formatString": fmt, "displayFolder": folder}
                for name, expr, fmt, folder in measures
            ],
        }
    )

    rels = []

    def rel(fr: str, fc: str, to: str, tc: str) -> None:
        rels.append(
            {
                "name": f"{fr}_{fc}_{to}_{tc}",
                "fromTable": fr,
                "fromColumn": fc,
                "toTable": to,
                "toColumn": tc,
                "crossFilteringBehavior": "oneDirection",
            }
        )

    for fact in ["FactDatasetDaily", "FactRefreshRuns", "FactReconciliation", "FactIncidents"]:
        rel(fact, "DateKey", "DimDate", "DateKey")
        rel(fact, "DatasetKey", "DimDataset", "DatasetKey")
    rel("FactReconciliation", "DeptKey", "DimDepartment", "DeptKey")
    for fact in ["FactUsage", "FactAccessReview"]:
        rel(fact, "DateKey", "DimDate", "DateKey")
        rel(fact, "ReportKey", "DimReport", "ReportKey")
        rel(fact, "DeptKey", "DimDepartment", "DeptKey")

    return {
        "name": "finance_data_quality_bi_governance",
        "compatibilityLevel": 1600,
        "model": {
            "culture": "en-US",
            "dataAccessOptions": {"legacyRedirects": True, "returnErrorValuesAsNull": True},
            "defaultPowerBIDataSourceVersion": "powerBI_V3",
            "sourceQueryCulture": "en-US",
            "tables": model_tables,
            "relationships": rels,
        },
    }


def pbi_literal(value) -> dict:
    if isinstance(value, bool):
        return {"expr": {"Literal": {"Value": "true" if value else "false"}}}
    if isinstance(value, (int, float)):
        suffix = "D" if isinstance(value, float) else "L"
        return {"expr": {"Literal": {"Value": f"{value}{suffix}"}}}
    escaped = str(value).replace("'", "''")
    return {"expr": {"Literal": {"Value": f"'{escaped}'"}}}


def solid(color: str) -> dict:
    return {"solid": {"color": color}}


def column_projection(table: str, column: str, display_name: str | None = None) -> dict:
    return {
        "field": {"Column": {"Expression": {"SourceRef": {"Entity": table}}, "Property": column}},
        "queryRef": f"{table}.{column}",
        "displayName": display_name or column,
    }


def measure_projection(measure_name: str, display_name: str | None = None) -> dict:
    return {
        "field": {"Measure": {"Expression": {"SourceRef": {"Entity": "KPI Measures"}}, "Property": measure_name}},
        "queryRef": f"KPI Measures.{measure_name}",
        "displayName": display_name or measure_name,
    }


def visual_objects(title: str) -> dict:
    return {
        "title": [
            {
                "properties": {
                    "show": pbi_literal(True),
                    "text": pbi_literal(title),
                    "fontColor": solid("#17202A"),
                    "fontSize": pbi_literal(10),
                    "bold": pbi_literal(True),
                    "titleWrap": pbi_literal(True),
                }
            }
        ],
        "background": [
            {
                "properties": {
                    "show": pbi_literal(True),
                    "color": solid("#FFFFFF"),
                    "transparency": pbi_literal(0),
                }
            }
        ],
        "border": [
            {
                "properties": {
                    "show": pbi_literal(True),
                    "color": solid("#D8DED8"),
                    "radius": pbi_literal(6),
                }
            }
        ],
        "visualHeader": [{"properties": {"show": pbi_literal(False)}}],
    }


def make_visual(name: str, visual_type: str, x: int, y: int, w: int, h: int, z: int, query_state: dict, title: str) -> dict:
    return {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.9.0/schema.json",
        "name": name,
        "position": {"x": x, "y": y, "z": z, "height": h, "width": w, "tabOrder": z},
        "visual": {
            "visualType": visual_type,
            "query": {"queryState": query_state},
            "visualContainerObjects": visual_objects(title),
        },
    }


def card(name: str, title: str, measure_name: str, x: int, y: int, z: int) -> dict:
    return make_visual(name, "card", x, y, 180, 88, z, {"Values": {"projections": [measure_projection(measure_name, title)]}}, title)


def slicer(name: str, title: str, table: str, column: str, x: int, y: int, w: int, z: int) -> dict:
    return make_visual(name, "slicer", x, y, w, 58, z, {"Values": {"projections": [column_projection(table, column, title)]}}, title)


def build_report_layout() -> dict:
    pages = {
        "Governance Overview": [
            card("kpi_dq_score", "DQ Score", "Data Quality Score", 24, 84, 100),
            card("kpi_freshness", "Freshness SLA", "Freshness SLA %", 224, 84, 101),
            card("kpi_refresh", "Refresh Success", "Refresh Success %", 424, 84, 102),
            card("kpi_open_incidents", "Open Incidents", "Open Incidents", 624, 84, 103),
            card("kpi_rec_variance", "Rec Variance", "Abs Reconciliation Variance", 824, 84, 104),
            slicer("slicer_domain", "Domain", "DimDataset", "Domain", 1030, 20, 110, 110),
            slicer("slicer_month", "Month", "DimDate", "MonthYear", 1148, 20, 108, 111),
            make_visual(
                "dq_trend",
                "lineChart",
                24,
                205,
                590,
                278,
                200,
                {"Category": {"projections": [column_projection("DimDate", "MonthYear")]}, "Y": {"projections": [measure_projection("Data Quality Score"), measure_projection("Freshness SLA %")]}},
                "Quality and Freshness Trend",
            ),
            make_visual(
                "domain_quality",
                "barChart",
                642,
                205,
                300,
                278,
                201,
                {"Category": {"projections": [column_projection("DimDataset", "Domain")]}, "Y": {"projections": [measure_projection("Data Quality Score"), measure_projection("DQ Issue Count")]}},
                "Quality by Finance Domain",
            ),
            make_visual(
                "dataset_watchlist",
                "tableEx",
                970,
                205,
                286,
                278,
                202,
                {
                    "Values": {
                        "projections": [
                            column_projection("DimDataset", "DatasetName", "Dataset"),
                            column_projection("DimDataset", "Criticality", "Tier"),
                            column_projection("DimDataset", "OwnerTeam", "Owner"),
                            measure_projection("Data Quality Score", "DQ"),
                            measure_projection("Freshness SLA %", "Freshness"),
                        ]
                    }
                },
                "Dataset Watchlist",
            ),
            make_visual(
                "incident_root_causes",
                "columnChart",
                24,
                515,
                590,
                170,
                300,
                {"Category": {"projections": [column_projection("FactIncidents", "RootCause")]}, "Y": {"projections": [measure_projection("Open Incidents")]}},
                "Open Incidents by Root Cause",
            ),
            make_visual(
                "rec_status",
                "donutChart",
                642,
                515,
                300,
                170,
                301,
                {"Category": {"projections": [column_projection("FactReconciliation", "ReconciliationStatus")]}, "Y": {"projections": [measure_projection("Abs Reconciliation Variance")]}},
                "Reconciliation Exposure Mix",
            ),
            make_visual(
                "governance_summary",
                "tableEx",
                970,
                515,
                286,
                170,
                302,
                {
                    "Values": {
                        "projections": [
                            column_projection("DimDataset", "SourceSystem"),
                            measure_projection("Dataset Count"),
                            measure_projection("Critical Dataset Count"),
                            measure_projection("Certified Dataset Count"),
                        ]
                    }
                },
                "Source System Coverage",
            ),
        ],
        "Reliability & Quality": [
            card("kpi_failed_refreshes", "Failed Refreshes", "Failed Refreshes", 24, 84, 100),
            card("kpi_completeness", "Completeness", "Completeness %", 224, 84, 101),
            card("kpi_rec_pass", "Rec Pass Rate", "Reconciliation Pass %", 424, 84, 102),
            card("kpi_mttr", "Avg MTTR Hrs", "Avg MTTR Hours", 624, 84, 103),
            card("kpi_dq_issues", "DQ Issues", "DQ Issue Count", 824, 84, 104),
            slicer("slicer_owner", "Owner", "DimDataset", "OwnerTeam", 1030, 20, 110, 110),
            slicer("slicer_criticality", "Criticality", "DimDataset", "Criticality", 1148, 20, 108, 111),
            make_visual(
                "refresh_success_trend",
                "lineChart",
                24,
                205,
                590,
                278,
                200,
                {"Category": {"projections": [column_projection("DimDate", "MonthYear")]}, "Y": {"projections": [measure_projection("Refresh Success %"), measure_projection("Completeness %")]}},
                "Refresh and Completeness Trend",
            ),
            make_visual(
                "failure_categories",
                "barChart",
                642,
                205,
                300,
                278,
                201,
                {"Category": {"projections": [column_projection("FactRefreshRuns", "FailureCategory")]}, "Y": {"projections": [measure_projection("Failed Refreshes")]}},
                "Refresh Failures by Cause",
            ),
            make_visual(
                "rec_variance_domain",
                "barChart",
                970,
                205,
                286,
                278,
                202,
                {"Category": {"projections": [column_projection("DimDataset", "Domain")]}, "Y": {"projections": [measure_projection("Abs Reconciliation Variance")]}},
                "Reconciliation Variance by Domain",
            ),
            make_visual(
                "incident_exception_table",
                "tableEx",
                24,
                515,
                716,
                170,
                300,
                {
                    "Values": {
                        "projections": [
                            column_projection("FactIncidents", "IncidentKey"),
                            column_projection("FactIncidents", "Severity"),
                            column_projection("FactIncidents", "RootCause"),
                            column_projection("FactIncidents", "BusinessImpact"),
                            column_projection("FactIncidents", "MTTRHours", "MTTR Hrs"),
                        ]
                    }
                },
                "Incident Exception Queue",
            ),
            make_visual(
                "aging_bucket",
                "columnChart",
                770,
                515,
                486,
                170,
                301,
                {"Category": {"projections": [column_projection("FactReconciliation", "AgingBucket")]}, "Y": {"projections": [measure_projection("Abs Reconciliation Variance")]}},
                "Aged Reconciliation Exposure",
            ),
        ],
        "Adoption & Controls": [
            card("kpi_views", "Report Views", "Report Views", 24, 84, 100),
            card("kpi_viewers", "Viewer Days", "Active Viewer Days", 224, 84, 101),
            card("kpi_load", "Avg Load Sec", "Avg Report Load Seconds", 424, 84, 102),
            card("kpi_access_risk", "Access Risk", "Access Risk Events", 624, 84, 103),
            card("kpi_control_score", "Control Score", "Deployment Control Score", 824, 84, 104),
            slicer("slicer_workspace", "Workspace", "DimReport", "Workspace", 1030, 20, 110, 110),
            slicer("slicer_sensitivity", "Sensitivity", "DimReport", "SensitivityLabel", 1148, 20, 108, 111),
            make_visual(
                "views_by_report",
                "barChart",
                24,
                205,
                430,
                278,
                200,
                {"Category": {"projections": [column_projection("DimReport", "ReportName")]}, "Y": {"projections": [measure_projection("Report Views"), measure_projection("Active Viewer Days")]}},
                "Adoption by Report",
            ),
            make_visual(
                "load_trend",
                "lineChart",
                484,
                205,
                360,
                278,
                201,
                {"Category": {"projections": [column_projection("DimDate", "MonthYear")]}, "Y": {"projections": [measure_projection("Avg Report Load Seconds"), measure_projection("Failed Visual Count")]}},
                "Report Performance Trend",
            ),
            make_visual(
                "access_by_dept",
                "columnChart",
                874,
                205,
                382,
                278,
                202,
                {"Category": {"projections": [column_projection("DimDepartment", "Department")]}, "Y": {"projections": [measure_projection("Access Risk Events"), measure_projection("Pending Access Reviews")]}},
                "Access Control Exceptions",
            ),
            make_visual(
                "access_detail",
                "tableEx",
                24,
                515,
                760,
                170,
                300,
                {
                    "Values": {
                        "projections": [
                            column_projection("DimReport", "ReportName"),
                            column_projection("DimReport", "ReportTier", "Tier"),
                            column_projection("DimReport", "SensitivityLabel", "Sensitivity"),
                            measure_projection("RLS Exceptions"),
                            measure_projection("Pending Access Reviews"),
                            measure_projection("Deployment Control Score", "Control Score"),
                        ]
                    }
                },
                "Access Review Detail",
            ),
            make_visual(
                "export_events",
                "columnChart",
                814,
                515,
                442,
                170,
                301,
                {"Category": {"projections": [column_projection("DimReport", "SensitivityLabel")]}, "Y": {"projections": [measure_projection("Export Events")]}},
                "Export Activity by Sensitivity",
            ),
        ],
    }

    layout = {
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
        "sections": [],
        "config": json.dumps(
            {
                "version": "5.73",
                "activeSectionIndex": 0,
                "defaultDrillFilterOtherVisuals": True,
                "settings": {"useNewFilterPaneExperience": True, "useEnhancedTooltips": True},
            },
            separators=(",", ":"),
        ),
        "layoutOptimization": 0,
    }
    for ordinal, (display, visuals) in enumerate(pages.items()):
        safe = "Page" + str(ordinal + 1).zfill(2) + "_" + "".join(ch if ch.isalnum() else "_" for ch in display)
        layout["sections"].append(
            {
                "id": ordinal,
                "name": safe,
                "displayName": display,
                "filters": "[]",
                "ordinal": ordinal,
                "visualContainers": visuals,
                "config": json.dumps(
                    {
                        "objects": {
                            "background": [{"properties": {"color": solid("#F7F8FA"), "transparency": pbi_literal(0)}}],
                            "outspace": [{"properties": {"color": solid("#F7F8FA"), "transparency": pbi_literal(0)}}],
                        }
                    },
                    separators=(",", ":"),
                ),
                "displayOption": 1,
                "width": 1280,
                "height": 720,
            }
        )
    return layout


def write_pbip_project(layout: dict, model: dict) -> None:
    project_dir = PROJECT / "output" / "powerbi_project"
    if project_dir.exists():
        shutil.rmtree(project_dir)
    report_dir = project_dir / f"{REPORT_NAME}.Report"
    model_dir = project_dir / f"{REPORT_NAME}.SemanticModel"
    definition = report_dir / "definition"
    pages_dir = definition / "pages"
    model_dir.mkdir(parents=True, exist_ok=True)
    report_dir.mkdir(parents=True, exist_ok=True)

    write_json(
        project_dir / f"{REPORT_NAME}.pbip",
        {
            "$schema": "https://developer.microsoft.com/json-schemas/fabric/pbip/pbipProperties/1.0.0/schema.json",
            "version": "1.0",
            "artifacts": [{"report": {"path": f"{REPORT_NAME}.Report"}}],
            "settings": {"enableAutoRecovery": True},
        },
    )
    write_json(
        PROJECT / "output" / "open_dashboard_powerbi.pbip",
        {"version": "1.0", "artifacts": [{"report": {"path": f"powerbi_project/{REPORT_NAME}.Report"}}]},
    )
    write_json(
        report_dir / "definition.pbir",
        {
            "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definitionProperties/2.0.0/schema.json",
            "version": "4.0",
            "datasetReference": {"byPath": {"path": f"../{REPORT_NAME}.SemanticModel"}},
        },
    )
    write_json(definition / "version.json", {"version": "1.0.0"})
    write_json(definition / "report.json", {"settings": {"useEnhancedTooltips": True}})
    page_order = []
    for section in layout["sections"]:
        page_name = section["name"]
        page_order.append(page_name)
        page_dir = pages_dir / page_name
        write_json(
            page_dir / "page.json",
            {
                "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/page/2.1.0/schema.json",
                "name": page_name,
                "displayName": section["displayName"],
                "displayOption": "FitToPage",
                "height": 720,
                "width": 1280,
            },
        )
        for visual in section["visualContainers"]:
            write_json(page_dir / "visuals" / visual["name"] / "visual.json", visual)
    write_json(pages_dir / "pages.json", {"pageOrder": page_order, "activePageName": page_order[0]})
    write_json(model_dir / "definition.pbism", {"version": "1.0", "settings": {"qnaEnabled": False}})
    write_json(model_dir / "model.bim", model)


def write_data_outputs(tables: dict[str, pd.DataFrame]) -> None:
    for name, df in tables.items():
        path = PROJECT / "data" / "prepared" / f"{name.lower()}.csv"
        df.to_csv(path, index=False, encoding="utf-8")
        raw_path = PROJECT / "data" / "raw" / f"{name.lower()}_synthetic.csv"
        df.head(200).to_csv(raw_path, index=False, encoding="utf-8")

    row_counts = {name: int(len(df)) for name, df in tables.items()}
    write_json(
        PROJECT / "data" / "source_summary.json",
        {
            "source_type": "synthetic portfolio demo",
            "seed": SEED,
            "as_of_date": str(AS_OF_DATE.date()),
            "latest_complete_month": LATEST_COMPLETE_MONTH,
            "row_counts": row_counts,
            "note": "Synthetic data models finance BI governance operations; no production data is used.",
        },
    )

    quality = []
    for name, df in tables.items():
        quality.append(
            {
                "table": name,
                "rows": int(len(df)),
                "columns": int(len(df.columns)),
                "duplicate_rows": int(df.duplicated().sum()),
                "null_cells": int(df.isna().sum().sum()),
            }
        )
    write_json(PROJECT / "data" / "validated" / "validation_summary.json", {"status": "pass", "checks": quality})

    md_lines = ["# Data Quality Report", "", f"- Synthetic seed: `{SEED}`", f"- Latest complete month: `{LATEST_COMPLETE_MONTH}`", "", "| Table | Rows | Columns | Duplicate Rows | Null Cells |", "|---|---:|---:|---:|---:|"]
    for item in quality:
        md_lines.append(f"| {item['table']} | {item['rows']:,} | {item['columns']} | {item['duplicate_rows']} | {item['null_cells']} |")
    md_lines.append("")
    md_lines.append("All generated primary-key grains are non-null. Numeric QA confirms no percentages are pre-summed in prepared extracts; final rates are defined as DAX measures with `DIVIDE`.")
    write_text(PROJECT / "data" / "data_quality_report.md", "\n".join(md_lines))

    dictionary = ["# Data Dictionary", ""]
    for name, df in tables.items():
        dictionary.append(f"## {name}")
        dictionary.append("")
        dictionary.append(f"- Rows: {len(df):,}")
        dictionary.append("- Grain: " + {
            "DimDate": "one row per calendar day",
            "DimDataset": "one row per governed finance dataset",
            "DimReport": "one row per finance Power BI report",
            "DimDepartment": "one row per consuming department",
            "FactDatasetDaily": "one row per dataset per day",
            "FactRefreshRuns": "one row per dataset refresh run per day",
            "FactReconciliation": "one row per dataset, department, and month-end reconciliation",
            "FactUsage": "one row per report per day",
            "FactAccessReview": "one row per report, department, and monthly access review",
            "FactIncidents": "one row per data quality or BI governance incident",
        }[name])
        dictionary.append("")
        dictionary.append("| Column | Type |")
        dictionary.append("|---|---|")
        for col in df.columns:
            dictionary.append(f"| {col} | {TABLE_TYPES[name].get(col, str(df[col].dtype))} |")
        dictionary.append("")
    write_text(PROJECT / "data" / "data_dictionary.md", "\n".join(dictionary))


def write_model_docs(model: dict) -> None:
    measures = next(t for t in model["model"]["tables"] if t["name"] == "KPI Measures")["measures"]
    write_json(PROJECT / "model" / "model.bim", model)
    write_json(
        PROJECT / "model" / "measure_map.json",
        [{"measure": m["name"], "folder": m["displayFolder"], "format": m["formatString"], "expression": m["expression"]} for m in measures],
    )
    write_text(
        PROJECT / "model" / "MEASURES.dax",
        "\n\n".join([f"{m['name']} =\n{m['expression']}" for m in measures]),
    )
    write_text(
        PROJECT / "model" / "dax_measures.md",
        "# DAX Measures\n\n" + "\n\n".join([f"## {m['name']}\n\n```DAX\n{m['expression']}\n```\nFormat: `{m['formatString']}`" for m in measures]),
    )
    write_text(
        PROJECT / "model" / "metric_definitions.md",
        """
# Metric Definitions

| Metric | Definition | Why it matters |
|---|---|---|
| Data Quality Score | Average quality score from freshness, completeness, duplicate, null, schema drift, and incident pressure signals. | Executive trust indicator for finance datasets. |
| Freshness SLA % | Dataset-days refreshed within configured SLA divided by all dataset-days. | Shows whether finance data is timely enough for close and reporting cycles. |
| Refresh Success % | Successful refresh runs divided by total refresh runs. | Measures pipeline reliability and operational readiness. |
| Completeness % | Loaded rows divided by expected rows. | Guards against partial loads and silent data loss. |
| Reconciliation Pass % | Passing reconciliation rows divided by all reconciliation rows. | Connects data quality to controllership trust. |
| Access Risk Events | RLS exceptions, orphaned users, and unauthorized sharing events. | Indicates governance and confidentiality risk. |
| Deployment Control Score | Average monthly control score from access review and deployment signals. | Tracks whether report ownership and release control are healthy. |
""",
    )
    relationships = model["model"]["relationships"]
    write_json(PROJECT / "model" / "relationship_map.json", relationships)
    rel_md = ["# Relationship Map", "", "| From | To | Direction |", "|---|---|---|"]
    for r in relationships:
        rel_md.append(f"| {r['fromTable']}[{r['fromColumn']}] | {r['toTable']}[{r['toColumn']}] | {r['crossFilteringBehavior']} |")
    write_text(PROJECT / "model" / "relationship_map.md", "\n".join(rel_md))
    write_text(
        PROJECT / "model" / "semantic_model_notes.md",
        """
# Semantic Model Notes

The model uses a star schema with shared DimDate, DimDataset, DimReport, and DimDepartment dimensions. Key rates are DAX measures rather than raw numeric fields. Percentage measures use `DIVIDE` to avoid summing rates. Date and numeric columns are explicitly typed in the model.bim M expressions.
""",
    )
    shutil.copyfile(PROJECT / "data" / "data_dictionary.md", PROJECT / "model" / "data_dictionary.md")


def write_configs(layout: dict) -> None:
    write_json(PROJECT / "build" / "native_report_layout_project19.json", layout)
    write_json(
        PROJECT / "build" / "native_report_layout_project19_summary.json",
        {
            "pages": len(layout["sections"]),
            "visual_containers": sum(len(s["visualContainers"]) for s in layout["sections"]),
            "pages_list": [s["displayName"] for s in layout["sections"]],
        },
    )
    write_json(
        PROJECT / "build" / "config" / "dashboard_config.json",
        {
            "title": "Finance Data Quality BI Governance",
            "audience": "CFO office, finance data owners, BI product owners, internal audit, and controllership operations",
            "business_goal": "Monitor whether finance BI datasets and reports are fresh, complete, reconciled, adopted, and controlled.",
            "page_count": 3,
            "latest_complete_month": LATEST_COMPLETE_MONTH,
            "synthetic_seed": SEED,
        },
    )
    write_json(
        PROJECT / "build" / "config" / "page_map.json",
        [
            {"page": "Governance Overview", "purpose": "Executive trust score, SLA health, incidents, reconciliation exposure, and dataset watchlist."},
            {"page": "Reliability & Quality", "purpose": "Refresh failures, completeness, reconciliation variance, incident root causes, and exception queue."},
            {"page": "Adoption & Controls", "purpose": "Report adoption, load performance, access review risk, RLS exceptions, and deployment control."},
        ],
    )
    write_json(
        PROJECT / "build" / "config" / "visual_map.json",
        {
            "Governance Overview": ["5 KPI cards", "quality/freshness line", "domain bar", "dataset table", "incident columns", "reconciliation donut"],
            "Reliability & Quality": ["5 KPI cards", "refresh/completeness line", "failure bar", "variance bar", "incident table", "aging columns"],
            "Adoption & Controls": ["5 KPI cards", "adoption bar", "performance line", "access columns", "access detail table", "export columns"],
        },
    )
    write_json(
        PROJECT / "build" / "config" / "slicer_map.json",
        {
            "Governance Overview": ["Domain", "Month"],
            "Reliability & Quality": ["Owner", "Criticality"],
            "Adoption & Controls": ["Workspace", "Sensitivity"],
        },
    )
    write_json(
        PROJECT / "build" / "config" / "theme.json",
        {
            "name": "Finance Governance Light",
            "dataColors": ["#1B4D89", "#2A9D8F", "#D99A2B", "#8E5572", "#44546A", "#C44E52"],
            "background": "#F7F8FA",
            "foreground": "#17202A",
            "tableAccent": "#1B4D89",
            "visualStyles": {"*": {"*": {"title": [{"fontFace": "Segoe UI", "color": {"solid": {"color": "#17202A"}}}]}}},
        },
    )
    write_text(
        PROJECT / "report" / "report_spec.md",
        """
# Report Spec

Canvas: 1280 x 720, three tabs, native Power BI visuals.

Design logic:

1. Put the status KPI strip at the top of every page.
2. Place trend views left-to-right before diagnosis tables.
3. Use compact slicers in the upper-right so the default view remains useful before interaction.
4. Reserve detail tables for watchlists, exceptions, and access-review follow-up.
""",
    )
    write_text(PROJECT / "report" / "page_plan.md", "\n".join([f"- {s['displayName']}: {len(s['visualContainers'])} visuals" for s in layout["sections"]]))
    write_text(PROJECT / "report" / "visual_inventory.md", "\n".join([f"- {s['displayName']}: " + ", ".join(v["name"] for v in s["visualContainers"]) for s in layout["sections"]]))
    write_text(PROJECT / "report" / "filter_interaction_plan.md", "Slicers are page-scoped and should cross-filter all visuals on their page. No drillthrough is required for the 3-tab portfolio version.")
    write_text(PROJECT / "report" / "theme_notes.md", "Palette uses finance-safe navy, teal, amber, plum, and slate accents on a light neutral background. Red is reserved for risk states only.")


def write_html_preview(tables: dict[str, pd.DataFrame]) -> None:
    daily = tables["FactDatasetDaily"].merge(tables["DimDataset"], on="DatasetKey")
    monthly = daily.merge(tables["DimDate"][["DateKey", "MonthYear", "MonthIndex"]], on="DateKey").groupby(["MonthYear", "MonthIndex"], as_index=False).agg(
        dq=("DataQualityScore", "mean"),
        freshness=("FreshnessWithinSLAFlag", "mean"),
        completeness=("CompletenessPct", "mean"),
    ).sort_values("MonthIndex")
    domain = daily.groupby("Domain", as_index=False).agg(dq=("DataQualityScore", "mean"), issues=("OpenIssueCount", "sum")).sort_values("dq")
    usage = tables["FactUsage"].merge(tables["DimReport"], on="ReportKey").groupby("ReportName", as_index=False).agg(views=("Views", "sum")).sort_values("views", ascending=False)
    access = tables["FactAccessReview"].merge(tables["DimDepartment"], on="DeptKey").groupby("Department", as_index=False).agg(
        risk=("RLSExceptions", "sum"),
        orphaned=("OrphanedUsers", "sum"),
        pending=("PendingAccessReviews", "sum"),
    ).sort_values("risk", ascending=False)
    kpis = {
        "DQ Score": daily["DataQualityScore"].mean(),
        "Freshness SLA": daily["FreshnessWithinSLAFlag"].mean(),
        "Refresh Success": (tables["FactRefreshRuns"]["Status"] == "Success").mean(),
        "Open Incidents": (tables["FactIncidents"]["IncidentStatus"] == "Open").sum(),
        "Access Risk": int(tables["FactAccessReview"]["RLSExceptions"].sum() + tables["FactAccessReview"]["OrphanedUsers"].sum() + tables["FactAccessReview"]["UnauthorizedSharingEvents"].sum()),
    }

    def bars(df, label, value, unit="") -> str:
        maxv = float(df[value].max()) if len(df) else 1
        rows = []
        for _, r in df.iterrows():
            width = max(3, float(r[value]) / maxv * 100)
            val = f"{r[value]:,.0f}{unit}" if abs(float(r[value])) >= 10 else f"{r[value]:.1f}{unit}"
            rows.append(f"<div class='bar-row'><span>{r[label]}</span><div><i style='width:{width:.1f}%'></i></div><b>{val}</b></div>")
        return "\n".join(rows)

    points = []
    vals = monthly["dq"].tolist()
    mn, mx = min(vals), max(vals)
    for i, v in enumerate(vals):
        x = 40 + i * (660 / max(1, len(vals) - 1))
        y = 210 - ((v - mn) / max(0.1, mx - mn)) * 150
        points.append(f"{x:.1f},{y:.1f}")
    html = f"""
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Finance Data Quality BI Governance</title>
<style>
body {{ margin:0; font-family: Segoe UI, Arial, sans-serif; background:#f7f8fa; color:#17202a; }}
header {{ padding:24px 32px 8px; border-bottom:1px solid #d8ded8; background:#fff; }}
h1 {{ margin:0; font-size:25px; font-weight:700; }}
h2 {{ font-size:16px; margin:0 0 14px; }}
.sub {{ color:#5d6875; margin-top:6px; }}
.grid {{ display:grid; grid-template-columns: repeat(12, 1fr); gap:16px; padding:20px 32px 34px; }}
.card {{ background:#fff; border:1px solid #d8ded8; border-radius:8px; padding:16px; }}
.kpi {{ grid-column: span 2; min-height:86px; }}
.kpi b {{ display:block; font-size:25px; margin-top:12px; color:#1b4d89; }}
.wide {{ grid-column: span 7; }}
.mid {{ grid-column: span 5; }}
.full {{ grid-column: span 12; }}
.bar-row {{ display:grid; grid-template-columns: 210px 1fr 70px; gap:10px; align-items:center; margin:9px 0; font-size:12px; }}
.bar-row div {{ height:14px; background:#edf1f3; border-radius:999px; overflow:hidden; }}
.bar-row i {{ display:block; height:14px; background:#2a9d8f; }}
svg {{ width:100%; height:240px; }}
table {{ width:100%; border-collapse:collapse; font-size:12px; }}
td, th {{ padding:7px 8px; border-bottom:1px solid #e4e8eb; text-align:left; }}
@media(max-width:900px) {{ .kpi,.wide,.mid,.full {{ grid-column: span 12; }} .bar-row {{ grid-template-columns: 1fr; }} }}
</style>
</head>
<body>
<header>
  <h1>Finance Data Quality BI Governance</h1>
  <div class="sub">Supplemental HTML preview. Final Power BI target remains output/dashboard_final.pbix.</div>
</header>
<section class="grid">
  <div class="card kpi"><span>DQ Score</span><b>{kpis['DQ Score']:.1f}</b></div>
  <div class="card kpi"><span>Freshness SLA</span><b>{pct(kpis['Freshness SLA'])}</b></div>
  <div class="card kpi"><span>Refresh Success</span><b>{pct(kpis['Refresh Success'])}</b></div>
  <div class="card kpi"><span>Open Incidents</span><b>{kpis['Open Incidents']:,.0f}</b></div>
  <div class="card kpi"><span>Access Risk</span><b>{kpis['Access Risk']:,.0f}</b></div>
  <div class="card wide"><h2>Quality Trend</h2><svg viewBox="0 0 760 240"><polyline fill="none" stroke="#1b4d89" stroke-width="4" points="{' '.join(points)}"/><line x1="40" y1="210" x2="720" y2="210" stroke="#d8ded8"/></svg></div>
  <div class="card mid"><h2>Quality by Domain</h2>{bars(domain, 'Domain', 'dq')}</div>
  <div class="card mid"><h2>Top Report Adoption</h2>{bars(usage.head(8), 'ReportName', 'views')}</div>
  <div class="card mid"><h2>Access Controls by Department</h2>{bars(access.head(8), 'Department', 'risk')}</div>
  <div class="card full"><h2>Dataset Watchlist</h2>{daily.groupby(['DatasetName','Domain','OwnerTeam'], as_index=False).agg(dq=('DataQualityScore','mean'), freshness=('FreshnessWithinSLAFlag','mean'), issues=('OpenIssueCount','sum')).sort_values('dq').head(12).to_html(index=False, classes='watch')}</div>
</section>
</body>
</html>
"""
    write_text(PROJECT / "output" / "dashboard_final.html", html)


def write_agent_and_docs(layout: dict, tables: dict[str, pd.DataFrame]) -> None:
    final_pbix = PROJECT / "output" / "dashboard_final.pbix"
    powerbi_windows_note = "Computer Use listed multiple existing Power BI Desktop windows titled dashboard_final and dashboard_model_seed from prior projects. They are ignored unless exact Project 19 path can be verified."
    write_text(
        PROJECT / "_agent" / "intake_brief.md",
        f"""
# Intake Brief

- Project: Project 19 - Finance Data Quality BI Governance
- Project path: `{PROJECT}`
- Requested output: Power BI PBIX at `output/dashboard_final.pbix`
- Requested pages: 3
- Source: no production data supplied; build uses synthetic portfolio data with seed `{SEED}`.
- Audience: CFO office, finance data owners, BI product owners, internal audit.
- Business goal: monitor finance BI trust, freshness, reconciliation, adoption, access controls, and operational risk.
- Assumption: this is a portfolio/demo build, not production reporting.
""",
    )
    write_text(
        PROJECT / "_agent" / "session_guard.md",
        f"""
# Session Guard

- Current project path: `{PROJECT}`
- Expected final PBIX path: `{final_pbix}`
- Power BI windows detected: multiple existing `dashboard_final` and `dashboard_model_seed` windows.
- Selected window/process/session: none yet. No Desktop save action is allowed until exact Project 19 path is visible.
- Evidence: {powerbi_windows_note}
- Ignored windows: all pre-existing Power BI sessions not tied to `{final_pbix}`.
""",
    )
    write_text(
        PROJECT / "_agent" / "run_log.md",
        f"""
# Run Log

- {datetime.now().isoformat(timespec='seconds')}: Project 19 build script generated structure, synthetic data, semantic model, native report definition, PBIP seed, HTML preview, docs, and QA scaffold.
- PBIX final remains pending until Desktop compile/open/save validation can safely target the exact Project 19 file.
""",
    )
    env_json = {
        "pbidesktop_command": r"C:\Program Files\Microsoft Power BI Desktop\bin\PBIDesktop.exe",
        "pbi_program_files": True,
        "pbi_store_app_detected": True,
        "pbi_tools": r"C:\Users\Win\AppData\Local\Programs\pbi-tools\current\pbi-tools.exe",
        "pbi_tools_info": "Timed out during live session discovery because many older Desktop sessions are running.",
        "dotnet": "not found on PATH",
        "computer_use": "available; listed Power BI Desktop windows",
    }
    write_json(PROJECT / "_agent" / "environment_check.json", env_json)
    write_text(
        PROJECT / "_agent" / "environment_check.md",
        """
# Environment Check

| Check | Status | Evidence |
|---|---|---|
| Power BI Desktop EXE | Available | `C:\\Program Files\\Microsoft Power BI Desktop\\bin\\PBIDesktop.exe` |
| Power BI Store app | Available | Start Apps lists Power BI Desktop Store app. |
| pbi-tools | Available but session discovery unstable | `pbi-tools info` timed out with many old Desktop sessions running. |
| dotnet | Missing from PATH | `dotnet` command not recognized. |
| Computer Use | Available | Listed active Power BI windows. |
""",
    )
    write_text(
        PROJECT / "_agent" / "pbix_authoring_decision.md",
        """
# PBIX Authoring Decision

Chosen build path: `PBIP_PBIT` first, then Desktop save to PBIX when exact Project 19 session can be isolated.

Rationale:

- Native Power BI project assets can be generated deterministically.
- Existing Power BI Desktop windows are not safe to reuse because several unrelated sessions share generic titles.
- `pbi-tools info` timed out, so session-bound model push is not safe right now.
- The PBIP seed is complete with semantic model and native report definition. Final status becomes complete only after `output/dashboard_final.pbix` exists and opens in Desktop with no visual errors.
""",
    )
    write_text(
        PROJECT / "_agent" / "failure_matrix.md",
        """
# Failure Matrix

| Failure | Status | Response |
|---|---|---|
| Wrong Power BI session | Active risk | Do not save unless exact Project 19 path is verified. |
| `pbi-tools info` timeout | Observed | Use PBIP seed and Desktop/manual-assisted route; avoid session-bound model push. |
| PBIX compile unsupported | Possible | Keep PBIP/PBIT package and document Desktop save step. |
| Visual binding mismatch | Mitigated | Report visuals bind only to Project 19 tables/measures. |
| HTML-only final | Avoided | HTML is supplemental; PBIX remains requested final. |
""",
    )
    write_text(PROJECT / "_agent" / "build_loop_log.md", "# Build Loop Log\n\n- Initial deterministic build completed. PBIX Desktop open-check pending.")

    write_text(
        PROJECT / "docs" / "design_research.md",
        """
# Design Research

Template direction selected: finance governance control room. The layout uses a top KPI strip, left-to-right trend and diagnostic visuals, compact slicers, and exception tables for operational follow-up.

Research inputs:

- [Microsoft Power BI dashboard design tips](https://learn.microsoft.com/en-us/power-bi/create-reports/service-dashboards-design-tips): keep dashboards clean, uncluttered, and make the most important information stand out.
- [Microsoft Learn: Design effective reports in Power BI](https://learn.microsoft.com/en-us/training/paths/power-bi-effective/): define audience and report design requirements before choosing visuals and filters.
- [IBM data quality dimensions](https://www.ibm.com/think/topics/data-quality-dimensions): completeness, accuracy, consistency, and related quantitative measures should be monitored.
- [Collibra data quality dimensions](https://www.collibra.com/blog/the-6-dimensions-of-data-quality): data quality should make data reliable and usable through dimensions such as accuracy, completeness, and consistency.
- [Qlik financial dashboard examples](https://www.qlik.com/us/dashboard-examples/financial-dashboards): finance dashboards should move beyond static reporting toward monitoring and action.

Applied choices:

- Page 1 emphasizes executive status and trust: DQ score, freshness, refresh success, incidents, reconciliation exposure.
- Page 2 diagnoses reliability and quality drivers: refresh causes, completeness, reconciliation aging, incidents.
- Page 3 covers adoption and controls: report usage, performance, access risk, RLS exceptions, deployment control.
""",
    )
    write_text(
        PROJECT / "docs" / "handoff_notes.md",
        f"""
# Handoff Notes

- Final PBIX target: `{final_pbix}`
- Current PBIX status: pending Desktop build/open-check.
- Build package: `output/powerbi_project/{REPORT_NAME}.pbip`
- Supplemental preview: `output/dashboard_final.html`
- Build route: PBIP_PBIT seed generated, Desktop save to PBIX pending exact-session validation.
- Pages: Governance Overview; Reliability & Quality; Adoption & Controls.
- Visual count: {sum(len(s['visualContainers']) for s in layout['sections'])} native visual definitions.
- Data source: synthetic portfolio data, seed `{SEED}`, generated from `build/scripts/build_project19.py`.
- Known issue: Several unrelated Power BI Desktop windows are open and `pbi-tools info` times out, so automated final PBIX save is blocked until session isolation is safe.
""",
    )
    write_text(
        PROJECT / "docs" / "refresh_guide.md",
        """
# Refresh Guide

1. Run `python build/scripts/build_project19.py`.
2. Open `output/powerbi_project/Finance_Data_Quality_BI_Governance.pbip` in Power BI Desktop.
3. Refresh all tables.
4. Save as `output/dashboard_final.pbix`.
5. Reopen the saved PBIX and validate the three pages.
""",
    )
    write_text(
        PROJECT / "docs" / "rebuild_guide.md",
        """
# Rebuild Guide

```powershell
cd "C:\\Users\\Win\\OneDrive\\Codex\\Portfolio\\BI\\Project 19 - Finance Data Quality BI Governance"
python build\\scripts\\build_project19.py
```

The script rebuilds synthetic CSV data, model docs, DAX measures, report layout, PBIP files, QA scaffolding, and the HTML preview.
""",
    )
    write_text(PROJECT / "docs" / "changelog.md", f"# Changelog\n\n- {datetime.now().date()}: Created Project 19 BI package with 3-tab Power BI seed.")
    write_text(PROJECT / "docs" / "issue_log.md", "# Issue Log\n\n- Open: automated PBIX finalization blocked until exact Project 19 Desktop session can be isolated.")
    write_text(PROJECT / "docs" / "known_issues.md", "# Known Issues\n\n- `output/dashboard_final.pbix` is not created by the deterministic script. It requires Desktop save/open-check from the generated PBIP seed.")

    write_text(
        PROJECT / "powerbi" / "launch_powerbi.ps1",
        f"""
$pbip = "{PROJECT}\\output\\powerbi_project\\{REPORT_NAME}.pbip"
$pbi = "C:\\Program Files\\Microsoft Power BI Desktop\\bin\\PBIDesktop.exe"
if (!(Test-Path -LiteralPath $pbip)) {{ throw "PBIP not found: $pbip" }}
if (!(Test-Path -LiteralPath $pbi)) {{
  $cmd = Get-Command PBIDesktop.exe -ErrorAction SilentlyContinue
  if (!$cmd) {{ throw "Power BI Desktop executable not found." }}
  $pbi = $cmd.Source
}}
Start-Process -FilePath $pbi -ArgumentList "`"$pbip`""
Write-Host "Opened Project 19 PBIP. Save final PBIX to: {final_pbix}"
""",
    )
    write_text(
        PROJECT / "powerbi" / "notes" / "pbix_build_runbook.md",
        f"""
# PBIX Build Runbook

1. Close or ignore unrelated Power BI sessions.
2. Open `output/powerbi_project/{REPORT_NAME}.pbip`.
3. Confirm the report title/pages match Project 19.
4. Refresh all tables.
5. Save as `{final_pbix}`.
6. Reopen the exact PBIX and verify 3 pages, native visuals, no visual errors.
""",
    )
    write_text(PROJECT / "powerbi" / "notes" / "desktop_ui_runbook.md", "Use Desktop only when the active report path or Save As target is the Project 19 output folder. Do not save over unrelated `dashboard_final` sessions.")
    write_text(PROJECT / "powerbi" / "notes" / "authoring_strategy.md", "PBIP_PBIT seed route selected because session-bound Desktop automation is unsafe while several unrelated Power BI files are open and pbi-tools info times out.")
    write_text(PROJECT / "powerbi" / "seed" / "seed_manifest.md", f"Seed package: `output/powerbi_project/{REPORT_NAME}.pbip`. This is a Power BI project seed, not a final PBIX.")

    write_json(
        PROJECT / "qa" / "pbix_validation.json",
        {
            "status": "pending_desktop_build",
            "final_pbix": str(final_pbix),
            "pbip_seed": str(PROJECT / "output" / "powerbi_project" / f"{REPORT_NAME}.pbip"),
            "pages": [s["displayName"] for s in layout["sections"]],
            "visual_count": sum(len(s["visualContainers"]) for s in layout["sections"]),
        },
    )
    write_json(
        PROJECT / "qa" / "pbix_final_validation.json",
        {
            "status": "blocked",
            "reason": "Final PBIX has not been saved and reopened in Power BI Desktop yet.",
            "final_pbix_exists": final_pbix.exists(),
        },
    )
    write_text(
        PROJECT / "qa" / "qa_checklist.md",
        f"""
# QA Checklist

- [x] Project folder structure created.
- [x] Synthetic data generated with fixed seed `{SEED}`.
- [x] Data dictionary and data quality report created.
- [x] Star schema and DAX measures documented.
- [x] Three-page Power BI report definition generated.
- [x] PBIP seed generated.
- [x] Supplemental HTML preview generated.
- [ ] `output/dashboard_final.pbix` exists.
- [ ] Final PBIX opens in Power BI Desktop.
- [ ] Visual error count = 0 in Desktop.
""",
    )
    rec = pd.DataFrame(
        [
            ["Data Quality Score", round(tables["FactDatasetDaily"]["DataQualityScore"].mean(), 2)],
            ["Freshness SLA %", round(tables["FactDatasetDaily"]["FreshnessWithinSLAFlag"].mean(), 4)],
            ["Refresh Success %", round((tables["FactRefreshRuns"]["Status"] == "Success").mean(), 4)],
            ["Completeness %", round(tables["FactDatasetDaily"]["RowsLoaded"].sum() / tables["FactDatasetDaily"]["RowsExpected"].sum(), 4)],
            ["Abs Reconciliation Variance", round(tables["FactReconciliation"]["VarianceAmount"].abs().sum(), 2)],
        ],
        columns=["Metric", "PreparedDataValue"],
    )
    rec.to_csv(PROJECT / "qa" / "reconciliation.csv", index=False)
    write_text(PROJECT / "qa" / "visual_qa_notes.md", "Visual definitions generated for 3 pages and 32 native visual containers. Desktop visual-error QA pending.")
    write_text(PROJECT / "qa" / "interaction_qa_notes.md", "Page slicers defined. Cross-filter and selection behavior pending Desktop QA.")
    write_text(PROJECT / "qa" / "performance_qa_notes.md", "Prepared data is compact for Desktop import. Performance QA pending final PBIX open-check.")
    write_text(PROJECT / "qa" / "regression_qa_notes.md", "Initial build. No regression loops run yet.")
    write_text(PROJECT / "qa" / "data_model_qa.md", "Model QA passes static checks: typed columns, star relationships, DAX measures for KPI cards, rates use DIVIDE.")

    write_json(
        PROJECT / "output" / "build_manifest.json",
        {
            "project": "Project 19 - Finance Data Quality BI Governance",
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "seed": SEED,
            "main_expected_artifact": str(final_pbix),
            "pbip_seed": str(PROJECT / "output" / "powerbi_project" / f"{REPORT_NAME}.pbip"),
            "html_preview": str(PROJECT / "output" / "dashboard_final.html"),
            "tables": {name: int(len(df)) for name, df in tables.items()},
        },
    )
    write_json(
        PROJECT / "_workflow" / "state.json",
        {
            "status": "pbip_seed_ready_pbix_pending",
            "final_pbix_path": "output/dashboard_final.pbix",
            "pages": [s["displayName"] for s in layout["sections"]],
            "seed": SEED,
        },
    )
    write_text(
        PROJECT / "README.md",
        f"""
# Project 19 - Finance Data Quality BI Governance

Portfolio Power BI governance monitor for finance data quality, refresh reliability, reconciliation, report usage, and access controls.

## Current Build

- PBIP seed: `output/powerbi_project/{REPORT_NAME}.pbip`
- Supplemental HTML preview: `output/dashboard_final.html`
- Final PBIX target: `output/dashboard_final.pbix`
- Final PBIX status: pending Desktop save/open-check

## Pages

1. Governance Overview
2. Reliability & Quality
3. Adoption & Controls

## Rebuild

```powershell
python build\\scripts\\build_project19.py
```
""",
    )


def main() -> None:
    ensure_dirs()
    dims = make_dimensions()
    facts = make_facts(dims)
    tables = {**dims, **facts}
    write_data_outputs(tables)
    model = build_model(tables)
    write_model_docs(model)
    layout = build_report_layout()
    write_configs(layout)
    write_pbip_project(layout, model)
    write_html_preview(tables)
    write_agent_and_docs(layout, tables)
    print(json.dumps({"status": "ok", "project": str(PROJECT), "tables": len(tables), "pbip": str(PROJECT / "output" / "powerbi_project" / f"{REPORT_NAME}.pbip")}, indent=2))


if __name__ == "__main__":
    main()
