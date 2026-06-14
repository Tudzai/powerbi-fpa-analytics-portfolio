from pathlib import Path
import json

root = Path(__file__).resolve().parents[2]
required = [
    "README.md",
    "data/source_summary.json",
    "data/data_quality_report.md",
    "model/dax_measures.md",
    "build/config/page_map.json",
    "_agent/pbix_authoring_decision.md",
    "_agent/scripted_desktop_pbix_check.md",
    "powerbi/launch_powerbi.ps1",
    "powerbi/notes/authoring_strategy.md",
    "qa/pbix_validation.json",
    "qa/scripted_desktop_pbix_check.json",
    "qa/scripted_model_push.json",
    "qa/native_report_layout_summary.json",
    "qa/pbix_native_report_validation.json",
    "docs/handoff_notes.md",
    "build/scripts/07_push_model_to_powerbi_desktop.ps1",
    "build/scripts/10_build_native_pbix_report.py",
    "build/scripts/10_apply_native_pbix_report.ps1",
    "build/native_report_layout_ecommerce.json",
    "output/dashboard_preview.html",
    "output/screenshots/dashboard_final.png",
]
result = {rel: (root / rel).exists() for rel in required}
print(json.dumps(result, indent=2))
if not all(result.values()):
    raise SystemExit(1)
