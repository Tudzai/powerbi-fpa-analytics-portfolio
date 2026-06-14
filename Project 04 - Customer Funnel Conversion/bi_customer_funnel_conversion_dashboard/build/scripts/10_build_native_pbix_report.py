from __future__ import annotations

import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
BUILD_DIR = PROJECT_ROOT / "build"
QA_DIR = PROJECT_ROOT / "qa"

layout = {
    "status": "layout_spec_generated",
    "note": "Native Power BI layout generation is documented in build/config/visual_map.json. This placeholder JSON is used by the package step only after a valid model PBIX exists.",
    "pages": ["Executive Funnel", "Segment Diagnostics", "Category and Product", "Marketing Efficiency"],
}
(BUILD_DIR / "native_report_layout_funnel.json").write_text(json.dumps(layout, indent=2), encoding="utf-8")
(QA_DIR / "native_report_layout_summary.json").write_text(json.dumps({"status": "generated", "pages": layout["pages"]}, indent=2), encoding="utf-8")
print(json.dumps({"status": "generated", "layout": str(BUILD_DIR / "native_report_layout_funnel.json")}, indent=2))
