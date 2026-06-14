from __future__ import annotations

import json
import shutil
import uuid
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PBIXPROJ = ROOT / "build" / "pbixproj" / "Project6_Marketing_ROI"
PBIP_ROOT = ROOT / "powerbi" / "pbip" / "Project6_Marketing_ROI_Native"
REPORT_NAME = "Project6_Marketing_ROI_Native"
LAYOUT_PATH = ROOT / "build" / "native_report_layout_project6.json"


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def compact_json(payload: object) -> str:
    return json.dumps(payload, separators=(",", ":"), ensure_ascii=False)


def platform_file(item_type: str) -> dict:
    return {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/gitIntegration/platformProperties/2.0.0/schema.json",
        "metadata": {"type": item_type, "displayName": REPORT_NAME},
        "config": {"version": "2.0", "logicalId": str(uuid.uuid4())},
    }


def build_pbip() -> None:
    if PBIP_ROOT.exists():
        shutil.rmtree(PBIP_ROOT, ignore_errors=True)

    report_dir = PBIP_ROOT / f"{REPORT_NAME}.Report"
    semantic_dir = PBIP_ROOT / f"{REPORT_NAME}.SemanticModel"
    (report_dir / ".pbi").mkdir(parents=True, exist_ok=True)
    (semantic_dir / ".pbi").mkdir(parents=True, exist_ok=True)

    write_json(
        PBIP_ROOT / f"{REPORT_NAME}.pbip",
        {
            "$schema": "https://developer.microsoft.com/json-schemas/fabric/pbip/pbipProperties/1.0.0/schema.json",
            "version": "1.0",
            "artifacts": [{"report": {"path": f"{REPORT_NAME}.Report"}}],
            "settings": {"enableAutoRecovery": True},
        },
    )
    write_json(
        report_dir / "definition.pbir",
        {
            "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definitionProperties/2.0.0/schema.json",
            "version": "4.0",
            "datasetReference": {"byPath": {"path": f"../{REPORT_NAME}.SemanticModel"}},
        },
    )
    write_json(
        semantic_dir / "definition.pbism",
        {
            "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/semanticModel/definitionProperties/1.0.0/schema.json",
            "version": "1.0",
            "settings": {"qnaEnabled": False},
        },
    )
    write_json(
        report_dir / "report.json",
        {
            "config": compact_json({"version": "5.68", "themeCollection": {}, "activeSectionIndex": 0, "linguisticSchemaSyncVersion": 2}),
            "layoutOptimization": 0,
            "report": {},
            "sections": [],
        },
    )
    write_json(report_dir / ".platform", platform_file("Report"))
    write_json(semantic_dir / ".platform", platform_file("SemanticModel"))
    write_json(report_dir / ".pbi" / "localSettings.json", {"version": "1.0"})
    write_json(semantic_dir / ".pbi" / "localSettings.json", {"version": "1.0"})
    write_json(semantic_dir / ".pbi" / "editorSettings.json", {"version": "1.0"})

    database = json.loads((PBIXPROJ / "Model" / "database.json").read_text(encoding="utf-8"))
    model_bim = {"compatibilityLevel": database.get("compatibilityLevel", 1600), "model": database["model"]}
    model = model_bim["model"]
    model.setdefault("cultures", [{"name": "en-US"}])
    annotations = model.setdefault("annotations", [])
    table_order = [table["name"] for table in model.get("tables", [])]
    annotations.append({"name": "PBI_QueryOrder", "value": json.dumps(table_order)})
    annotations.append({"name": "PBI_ProTooling", "value": "[\"DevMode\"]"})
    write_json(semantic_dir / "model.bim", model_bim)

    diagram = PBIXPROJ / "DiagramLayout.json"
    if diagram.exists():
        shutil.copyfile(diagram, semantic_dir / "diagramLayout.json")


def build_layout() -> None:
    report_dir = PBIXPROJ / "Report"
    root_config = json.loads((report_dir / "config.json").read_text(encoding="utf-8"))
    report_json = json.loads((report_dir / "report.json").read_text(encoding="utf-8"))
    layout = {
        "id": 0,
        "resourcePackages": report_json.get("resourcePackages", []),
        "sections": [],
        "config": compact_json(root_config),
        "layoutOptimization": report_json.get("layoutOptimization", 0),
    }

    for idx, section_dir in enumerate(sorted((report_dir / "sections").iterdir())):
        if not section_dir.is_dir():
            continue
        section = json.loads((section_dir / "section.json").read_text(encoding="utf-8"))
        section_config = json.loads((section_dir / "config.json").read_text(encoding="utf-8"))
        section_filters_path = section_dir / "filters.json"
        filters = json.loads(section_filters_path.read_text(encoding="utf-8")) if section_filters_path.exists() else []
        out_section = {
            "id": idx,
            "name": section.get("name", f"ReportSection{idx}"),
            "displayName": section["displayName"],
            "filters": compact_json(filters),
            "ordinal": section["ordinal"],
            "visualContainers": [],
            "config": compact_json(section_config),
            "displayOption": section.get("displayOption", 1),
            "width": section.get("width", 1280),
            "height": section.get("height", 720),
        }
        for visual_dir in sorted((section_dir / "visualContainers").iterdir()):
            if not visual_dir.is_dir():
                continue
            config = json.loads((visual_dir / "config.json").read_text(encoding="utf-8"))
            pos = config["layouts"][0]["position"]
            visual = {
                "x": pos["x"],
                "y": pos["y"],
                "z": pos["z"],
                "width": pos["width"],
                "height": pos["height"],
                "config": compact_json(config),
                "filters": compact_json(json.loads((visual_dir / "filters.json").read_text(encoding="utf-8"))),
                "tabOrder": pos["tabOrder"],
            }
            query_path = visual_dir / "query.json"
            transforms_path = visual_dir / "dataTransforms.json"
            if query_path.exists():
                visual["query"] = compact_json(json.loads(query_path.read_text(encoding="utf-8")))
            if transforms_path.exists():
                visual["dataTransforms"] = compact_json(json.loads(transforms_path.read_text(encoding="utf-8")))
            out_section["visualContainers"].append(visual)
        layout["sections"].append(out_section)

    write_json(LAYOUT_PATH, layout)


def main() -> None:
    build_pbip()
    build_layout()
    print(f"PBIP: {PBIP_ROOT / (REPORT_NAME + '.pbip')}")
    print(f"Layout: {LAYOUT_PATH}")


if __name__ == "__main__":
    main()
