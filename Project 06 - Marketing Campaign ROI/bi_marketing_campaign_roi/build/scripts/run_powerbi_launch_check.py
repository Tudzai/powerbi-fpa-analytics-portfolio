from __future__ import annotations

import json
import subprocess
from datetime import datetime
from pathlib import Path


PROJECT = Path(__file__).resolve().parents[2]


def read_json(path: Path, default: dict) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8")) if path.exists() else default
    except Exception:
        return default


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.strip() + "\n", encoding="utf-8")


def main() -> None:
    script = PROJECT / "powerbi/launch_powerbi.ps1"
    proc = subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(script)],
        cwd=PROJECT,
        capture_output=True,
        text=True,
        timeout=90,
    )
    stdout = proc.stdout.strip()
    stderr = proc.stderr.strip()
    try:
        launch_result = json.loads(stdout) if stdout else {}
    except Exception:
        launch_result = {"raw_stdout": stdout}

    process_detected = bool(launch_result.get("ProcessDetected"))
    launch_status = "launch_verified" if process_detected else "launch_failed"
    ui_control = "ui_control_unavailable"

    authoring = read_json(PROJECT / "_agent/pbix_authoring_decision.json", {})
    pbix_path = PROJECT / "output/dashboard_final.pbix"
    if pbix_path.exists():
        build_status = "pbix_created_needs_open_save_refresh_qa"
    elif process_detected:
        build_status = "launch_verified_assisted_build_pending"
    else:
        build_status = "manual_assisted_required"

    enriched = {
        "checked_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "return_code": proc.returncode,
        "launch_status": launch_status,
        "ui_control": ui_control,
        "build_status": build_status,
        "authoring_mode": authoring.get("authoring_mode", "unknown"),
        "manual_assisted_required": authoring.get("manual_assisted_required", False),
        "stdout": stdout,
        "stderr": stderr,
        "result": launch_result,
    }
    write_json(PROJECT / "_agent/powerbi_launch_check.json", enriched)
    write_text(
        PROJECT / "_agent/powerbi_launch_check.md",
        f"""
# Power BI Launch Check

| Item | Result |
|---|---|
| Checked at | {enriched['checked_at']} |
| Launch status | {launch_status} |
| UI control | {ui_control} |
| Build status | {build_status} |
| Authoring mode | {enriched['authoring_mode']} |
| Return code | {proc.returncode} |

## Launcher Output

```json
{json.dumps(launch_result, indent=2, ensure_ascii=False)}
```

## Stderr

```text
{stderr or '(empty)'}
```

Power BI can be launched or detected when launch status is `launch_verified`, but this session does not expose reliable UI automation to import data, create relationships, build visuals, save, reopen, and refresh a PBIX automatically.
""",
    )

    validation_path = PROJECT / "qa/pbix_validation.json"
    validation = read_json(validation_path, {})
    validation.update(
        {
            "pbix_created": pbix_path.exists(),
            "expected_final_path": "output/dashboard_final.pbix",
            "launch_status": launch_status,
            "ui_control": ui_control,
            "build_status": build_status,
        }
    )
    write_json(validation_path, validation)

    output_validation_path = PROJECT / "qa/output_validation.json"
    output_validation = read_json(output_validation_path, {})
    if output_validation:
        for item in output_validation.get("files", []):
            rel = item.get("file")
            if rel:
                path = PROJECT / rel
                item["exists"] = path.exists()
                item["bytes"] = path.stat().st_size if path.exists() else 0
        output_validation["powerbi_launch_status"] = launch_status
        output_validation["ui_control"] = ui_control
        output_validation["pbix_build_status"] = build_status
        output_validation["file_qa_status"] = "Pass" if pbix_path.exists() else "Blocked at File QA"
        write_json(output_validation_path, output_validation)

    handoff_path = PROJECT / "docs/handoff_notes.md"
    if handoff_path.exists():
        handoff = handoff_path.read_text(encoding="utf-8")
        handoff = handoff.replace("- Power BI launch status: pending launch check", f"- Power BI launch status: {launch_status}")
        handoff = handoff.replace("- Build status: build-ready but not final; pending launch check / assisted build", f"- Build status: build-ready but not final; {build_status}")
        handoff_path.write_text(handoff, encoding="utf-8")


if __name__ == "__main__":
    main()
