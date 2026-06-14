from __future__ import annotations

import csv
import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def row_count(relative_path: str) -> int:
    path = PROJECT_ROOT / relative_path
    with path.open("r", newline="", encoding="utf-8") as handle:
        return sum(1 for _ in csv.DictReader(handle))


def main() -> None:
    status_path = PROJECT_ROOT / "output" / "pbix_build_status.json"
    if not status_path.exists():
        raise FileNotFoundError("Run 04_build_or_update_model.py before output validation.")
    status = json.loads(status_path.read_text(encoding="utf-8"))

    validation = {
        "project": "Monthly FP&A Performance Pack",
        "prepared_row_counts": {
            "FactFinancials": row_count("data/prepared/fact_financials.csv"),
            "FactOpexDepartment": row_count("data/prepared/fact_opex_department.csv"),
            "FactCash": row_count("data/prepared/fact_cash.csv"),
            "FactBridge": row_count("data/prepared/fact_bridge.csv"),
            "FactCommentary": row_count("data/prepared/fact_commentary.csv"),
            "DimDate": row_count("data/prepared/dim_date.csv"),
            "DimCustomer": row_count("data/prepared/dim_customer.csv")
        },
        "qa_artifacts": {
            "source_summary": (PROJECT_ROOT / "data/source_summary.json").exists(),
            "quality_report": (PROJECT_ROOT / "data/data_quality_report.md").exists(),
            "reconciliation_xlsx": (PROJECT_ROOT / "qa/reconciliation.xlsx").exists(),
            "qa_checklist": (PROJECT_ROOT / "qa/qa_checklist.md").exists()
        },
        "dashboard_artifacts": {
            "dashboard_html": (PROJECT_ROOT / "output/dashboard.html").exists(),
            "export_mirror_html": (PROJECT_ROOT / "output/exports/fpa_dashboard_preview.html").exists()
        },
        "pbix_status": status["pbix_status"],
        "pbix_target_exists": (PROJECT_ROOT / "output/dashboard_final.pbix").exists()
    }
    output_path = PROJECT_ROOT / "output" / "output_validation.json"
    output_path.write_text(json.dumps(validation, indent=2), encoding="utf-8")
    print(f"Output validation written to {output_path}")


if __name__ == "__main__":
    main()
