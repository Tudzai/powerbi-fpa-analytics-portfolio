from __future__ import annotations

import json
import os
import shutil
import tempfile
import zipfile
from collections import Counter
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
INPUT_PBIX = ROOT / "output" / "dashboard_final.pbix"
OUTPUT_PBIX = ROOT / "output" / "dashboard_native.pbix"
FINAL_PBIX = ROOT / "output" / "dashboard_final.pbix"
LAYOUT_JSON = ROOT / "build" / "native_report_layout_project8.json"
THEME_JSON = ROOT / "build" / "config" / "theme.json"


def clone_zip_info(info: zipfile.ZipInfo) -> zipfile.ZipInfo:
    cloned = zipfile.ZipInfo(info.filename, date_time=info.date_time)
    cloned.comment = info.comment
    cloned.extra = info.extra
    cloned.internal_attr = info.internal_attr
    cloned.external_attr = info.external_attr
    cloned.create_system = info.create_system
    cloned.compress_type = info.compress_type
    return cloned


def count_visual_types(layout: dict) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for section in layout.get("sections", []):
        for vc in section.get("visualContainers", []):
            cfg = json.loads(vc.get("config", "{}"))
            visual_type = cfg.get("singleVisual", {}).get("visualType", "unknown")
            counts[visual_type] += 1
    return dict(counts)


def apply_layout() -> dict:
    if not INPUT_PBIX.exists():
        raise FileNotFoundError(f"PBIX not found: {INPUT_PBIX}")
    if not LAYOUT_JSON.exists():
        raise FileNotFoundError(f"Layout JSON not found: {LAYOUT_JSON}")

    archive = ROOT / "archive" / "old_versions"
    archive.mkdir(parents=True, exist_ok=True)
    backup = archive / f"dashboard_final_before_native_layout_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pbix"
    shutil.copy2(INPUT_PBIX, backup)

    layout = json.loads(LAYOUT_JSON.read_text(encoding="utf-8"))
    theme_cfg = json.loads(THEME_JSON.read_text(encoding="utf-8")) if THEME_JSON.exists() else {}

    with zipfile.ZipFile(INPUT_PBIX, "r") as zin:
        infos = zin.infolist()
        zip_infos = {info.filename: clone_zip_info(info) for info in infos}
        entry_order = [info.filename for info in infos]
        entries = {info.filename: zin.read(info.filename) for info in infos}

    if "Report/Layout" not in entries:
        raise KeyError("Report/Layout not found in PBIX package.")

    theme_candidates = [
        name
        for name in entries
        if name.startswith("Report/StaticResources/SharedResources/BaseThemes/") and name.endswith(".json")
    ]
    theme_path = theme_candidates[0] if theme_candidates else None

    entries["Report/Layout"] = json.dumps(layout, separators=(",", ":"), ensure_ascii=False).encode("utf-16le")
    if theme_path:
        theme = json.loads(entries[theme_path].decode("utf-8"))
        theme.update(
            {
                "name": theme_cfg.get("name", "Digital Payments Profitability Light"),
                "dataColors": theme_cfg.get("dataColors", []),
                "background": theme_cfg.get("background", "#F5F7FA"),
                "foreground": theme_cfg.get("foreground", "#111827"),
                "tableAccent": theme_cfg.get("tableAccent", "#2563EB"),
                "good": theme_cfg.get("good", "#16A34A"),
                "neutral": theme_cfg.get("neutral", "#D97706"),
                "bad": theme_cfg.get("bad", "#DC2626"),
            }
        )
        entries[theme_path] = json.dumps(theme, separators=(",", ":"), ensure_ascii=False).encode("utf-8")

    fd, tmp_name = tempfile.mkstemp(suffix=".pbix")
    os.close(fd)
    tmp = Path(tmp_name)
    try:
        with zipfile.ZipFile(tmp, "w", compression=zipfile.ZIP_DEFLATED) as zout:
            for name in entry_order:
                if name == "SecurityBindings":
                    continue
                zout.writestr(zip_infos[name], entries[name])
        shutil.move(str(tmp), OUTPUT_PBIX)
    finally:
        if tmp.exists():
            tmp.unlink()

    shutil.copy2(OUTPUT_PBIX, FINAL_PBIX)
    result = {
        "status": "PASS",
        "input_pbix": str(INPUT_PBIX),
        "output_pbix": str(OUTPUT_PBIX),
        "final_pbix": str(FINAL_PBIX),
        "backup": str(backup),
        "layout_json": str(LAYOUT_JSON),
        "page_count": len(layout.get("sections", [])),
        "pages": [section.get("displayName") for section in layout.get("sections", [])],
        "visual_count": sum(len(section.get("visualContainers", [])) for section in layout.get("sections", [])),
        "visual_types": count_visual_types(layout),
        "security_bindings_removed": "SecurityBindings" in entries,
        "theme_path": theme_path,
    }
    (ROOT / "qa" / "native_layout_validation.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


def main() -> None:
    print(json.dumps(apply_layout(), indent=2))


if __name__ == "__main__":
    main()
