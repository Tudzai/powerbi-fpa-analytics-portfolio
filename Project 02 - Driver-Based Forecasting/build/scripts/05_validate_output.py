from __future__ import annotations

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]

REQUIRED_FILES = [
    "data/raw/driver_forecasting_raw.xlsx",
    "data/source_summary.json",
    "data/data_quality_report.md",
    "model/data_dictionary.md",
    "model/metric_definitions.md",
    "model/relationship_map.md",
    "model/semantic_model_notes.md",
    "model/measure_map.json",
    "build/config/dashboard_config.json",
    "build/config/page_map.json",
    "build/config/visual_map.json",
    "build/config/theme.json",
    "powerbi/Project2_Measures.dax",
    "powerbi/PowerQuery_M.txt",
    "powerbi/Build_Instructions.md",
    "qa/qa_checklist.md",
    "qa/reconciliation.xlsx",
    "qa/validation_summary.json",
    "docs/README.md",
    "docs/changelog.md",
    "docs/issue_log.md",
    "docs/handoff_notes.md",
    "output/exports/dashboard_preview.html",
    "output/screenshots/page_01_executive_overview.png",
    "output/screenshots/page_02_revenue_cost_drivers.png",
    "output/screenshots/page_03_headcount_capacity.png",
    "output/screenshots/page_04_cash_accuracy.png",
    "output/exports/powerbi_dashboard_mockup.html",
    "output/screenshots/powerbi_mockup/01_powerbi_executive_overview.png",
    "output/screenshots/powerbi_mockup/02_powerbi_revenue_cost_drivers.png",
    "output/screenshots/powerbi_mockup/03_powerbi_headcount_capacity.png",
    "output/screenshots/powerbi_mockup/04_powerbi_cash_accuracy.png",
    "output/screenshots/powerbi_mockup/05_powerbi_detail_exceptions.png",
]

REQUIRED_PREPARED = [
    "fact_revenue_driver.csv",
    "fact_cost_driver.csv",
    "fact_headcount_plan.csv",
    "fact_opex_driver.csv",
    "fact_cash_impact.csv",
    "fact_forecast_accuracy.csv",
    "dim_date.csv",
    "dim_scenario.csv",
    "dim_service.csv",
    "dim_region.csv",
    "dim_customer_segment.csv",
    "dim_department.csv",
    "what_if_parameters.csv",
]


def main() -> None:
    missing = []
    for rel in REQUIRED_FILES:
        path = PROJECT_ROOT / rel
        if not path.exists():
            missing.append(rel)
    for filename in REQUIRED_PREPARED:
        path = PROJECT_ROOT / "data" / "prepared" / filename
        if not path.exists():
            missing.append(f"data/prepared/{filename}")

    if missing:
        print("Missing required artifacts:")
        for item in missing:
            print(f"- {item}")
        raise SystemExit(1)

    pbix = PROJECT_ROOT / "output" / "dashboard_final.pbix"
    if pbix.exists():
        print(f"PBIX present: {pbix}")
    else:
        print("PBIX pending: output/dashboard_final.pbix is not present yet.")
        print("Build pack validation passed; final Power BI Desktop file QA remains open.")
    print("All non-PBIX build artifacts are present.")


if __name__ == "__main__":
    main()
