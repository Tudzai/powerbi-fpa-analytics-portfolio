from __future__ import annotations

import json
from pathlib import Path
import subprocess


PROJECT_ROOT = Path(__file__).resolve().parents[2]


REQUIRED_FILES = [
    "data/prepared/dim_date.csv",
    "data/prepared/dim_scenario.csv",
    "data/prepared/dim_business_unit.csv",
    "data/prepared/dim_product.csv",
    "data/prepared/dim_region.csv",
    "data/prepared/dim_customer.csv",
    "data/prepared/dim_department.csv",
    "data/prepared/fact_financials.csv",
    "data/prepared/fact_opex_department.csv",
    "data/prepared/fact_cash.csv",
    "data/prepared/fact_bridge.csv",
    "data/prepared/fact_commentary.csv",
    "model/measures.dax",
    "model/relationship_map.md",
    "build/config/PowerQuery_AllTables.pq",
    "build/config/theme.json",
    "build/config/page_map.json",
    "build/config/visual_map.json",
]


def detect_power_bi_desktop() -> dict[str, str | bool]:
    command = [
        "powershell",
        "-NoProfile",
        "-Command",
        (
            "$pkg = Get-AppxPackage -Name 'Microsoft.MicrosoftPowerBIDesktop' -ErrorAction SilentlyContinue; "
            "if ($pkg) { "
            "  $exe = Join-Path $pkg.InstallLocation 'bin\\PBIDesktop.exe'; "
            "  [pscustomobject]@{Detected=$true; Version=$pkg.Version.ToString(); InstallLocation=$pkg.InstallLocation; Executable=$exe; AppId='Microsoft.MicrosoftPowerBIDesktop_8wekyb3d8bbwe!Microsoft.MicrosoftPowerBIDesktop'} | ConvertTo-Json -Compress "
            "} else { "
            "  $cmd = Get-Command PBIDesktop.exe -ErrorAction SilentlyContinue; "
            "  if ($cmd) { [pscustomobject]@{Detected=$true; Version='unknown'; InstallLocation='PATH'; Executable=$cmd.Source; AppId=''} | ConvertTo-Json -Compress } "
            "  else { [pscustomobject]@{Detected=$false; Version=''; InstallLocation=''; Executable=''; AppId=''} | ConvertTo-Json -Compress } "
            "}"
        ),
    ]
    try:
        completed = subprocess.run(command, capture_output=True, text=True, check=False)
        if completed.stdout.strip():
            import json

            data = json.loads(completed.stdout.strip())
            return {
                "detected": bool(data.get("Detected")),
                "version": str(data.get("Version", "")),
                "install_location": str(data.get("InstallLocation", "")),
                "executable": str(data.get("Executable", "")),
                "app_id": str(data.get("AppId", "")),
            }
    except Exception:
        pass
    return {"detected": False, "version": "", "install_location": "", "executable": "", "app_id": ""}


def main() -> None:
    missing = [path for path in REQUIRED_FILES if not (PROJECT_ROOT / path).exists()]
    power_bi = detect_power_bi_desktop()
    status = {
        "project": "Monthly FP&A Performance Pack",
        "checked_files": len(REQUIRED_FILES),
        "missing_files": missing,
        "power_bi_desktop": power_bi,
        "pbix_status": "pending Desktop build and QA",
        "pbix_target": "output/dashboard_final.pbix",
        "blocker": "Power BI Desktop Store app is detected, but PBIX authoring/visual QA has not been executed yet.",
        "next_action": "Open Power BI Desktop and follow powerbi/PBIX_build_instructions.md.",
    }
    output_path = PROJECT_ROOT / "output" / "pbix_build_status.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(status, indent=2), encoding="utf-8")
    if missing:
        raise SystemExit(f"Build package incomplete. Missing: {missing}")
    print(f"Build package complete. PBIX status written to {output_path}")


if __name__ == "__main__":
    main()
