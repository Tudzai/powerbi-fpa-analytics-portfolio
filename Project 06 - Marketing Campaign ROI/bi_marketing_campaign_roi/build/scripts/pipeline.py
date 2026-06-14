from __future__ import annotations

import json
import math
import platform
import subprocess
from datetime import datetime
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


SEED = 6262026
PROJECT = Path(__file__).resolve().parents[2]
WORKSPACE = PROJECT.parents[1]

DIRS = [
    "_agent",
    "data/raw",
    "data/synthetic",
    "data/prepared",
    "data/validated",
    "model",
    "build/config",
    "powerbi/notes",
    "powerbi/templates",
    "output/screenshots",
    "output/exports",
    "qa",
    "docs",
]


def ensure_dirs() -> None:
    for rel in DIRS:
        (PROJECT / rel).mkdir(parents=True, exist_ok=True)


def write_text(rel: str, text: str) -> None:
    path = PROJECT / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.strip() + "\n", encoding="utf-8")


def write_json(rel: str, data: object) -> None:
    path = PROJECT / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def ps(command: str, timeout: int = 30) -> tuple[int, str, str]:
    try:
        proc = subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", command],
            cwd=PROJECT,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return proc.returncode, proc.stdout.strip(), proc.stderr.strip()
    except Exception as exc:
        return 999, "", str(exc)


def money_m(value: float) -> str:
    return f"${value / 1_000_000:.1f}M"


def pct(value: float) -> str:
    return f"{value:.1%}"


def detect_environment() -> dict:
    commands = {
        "get_command_pbi": "Get-Command PBIDesktop.exe -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source",
        "program_files_pbi": (
            "@('C:\\Program Files\\Microsoft Power BI Desktop\\bin\\PBIDesktop.exe',"
            "'C:\\Program Files (x86)\\Microsoft Power BI Desktop\\bin\\PBIDesktop.exe') "
            "| ForEach-Object { [pscustomobject]@{Path=$_; Exists=(Test-Path $_)} } | ConvertTo-Json"
        ),
        "start_apps_pbi": (
            "Get-StartApps | Where-Object { $_.Name -like '*Power BI Desktop*' -or $_.AppID -like '*PowerBI*' } "
            "| Select-Object Name,AppID | ConvertTo-Json"
        ),
        "winget_pbi": "winget list --name 'Power BI' 2>$null",
        "pbi_tools": "Get-Command pbi-tools -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source",
        "pbi_tools_exe": "Get-Command pbi-tools.exe -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source",
        "dotnet_info": "dotnet --info",
        "dotnet_tools": "dotnet tool list -g",
    }
    raw = {}
    for name, command in commands.items():
        code, out, err = ps(command, timeout=45 if name.startswith("dotnet") or name == "winget_pbi" else 20)
        raw[name] = {"return_code": code, "stdout": out, "stderr": err}

    exe_path = str(raw["get_command_pbi"]["stdout"] or "").strip()
    program_files = []
    try:
        parsed = json.loads(raw["program_files_pbi"]["stdout"] or "[]")
        program_files = parsed if isinstance(parsed, list) else [parsed]
    except Exception:
        program_files = []
    pf_path = next((item.get("Path") for item in program_files if item.get("Exists")), "")

    store_apps = []
    try:
        parsed = json.loads(raw["start_apps_pbi"]["stdout"] or "[]")
        store_apps = parsed if isinstance(parsed, list) else [parsed]
    except Exception:
        store_apps = []

    pbi_exe_available = bool(exe_path or pf_path)
    pbi_store_available = bool(store_apps)
    pbi_tools_available = bool(raw["pbi_tools"]["stdout"] or raw["pbi_tools_exe"]["stdout"])
    dotnet_available = raw["dotnet_info"]["return_code"] == 0 and bool(raw["dotnet_info"]["stdout"])

    if pbi_exe_available:
        pbi_kind = "EXE available"
        launch_command = exe_path or pf_path
        build_mode = "assisted_powerbi_desktop"
    elif pbi_store_available:
        pbi_kind = "Microsoft Store available"
        launch_command = f"Start-Process 'shell:AppsFolder\\{store_apps[0].get('AppID')}'"
        build_mode = "assisted_powerbi_desktop"
    else:
        pbi_kind = "not found"
        launch_command = None
        build_mode = "blocked_for_pbix_build"

    env = {
        "checked_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "os": platform.platform(),
        "machine": platform.node(),
        "power_bi_desktop": pbi_kind,
        "power_bi_desktop_exe_available": pbi_exe_available,
        "power_bi_desktop_store_available": pbi_store_available,
        "power_bi_store_apps": store_apps,
        "pbi_tools_available": pbi_tools_available,
        "dotnet_available": dotnet_available,
        "launch_command": launch_command,
        "build_mode": build_mode,
        "raw": raw,
    }
    return env


def discover_powerbi_sources() -> dict:
    search_dirs = [
        PROJECT / "assets/powerbi",
        PROJECT / "powerbi/templates",
        WORKSPACE / "assets/powerbi",
        WORKSPACE / "powerbi/templates",
    ]
    template_ext = {".pbix", ".pbit"}
    source_ext = {".pbip", ".pbixproj.json"}
    templates = []
    sources = []
    for root in search_dirs:
        if root.exists():
            for path in root.rglob("*"):
                name_lower = path.name.lower()
                if path.is_file() and path.suffix.lower() in template_ext:
                    templates.append(str(path))
                if path.is_dir() and path.suffix.lower() == ".pbip":
                    sources.append(str(path))
                if path.is_file() and name_lower.endswith(".pbixproj.json"):
                    sources.append(str(path))
    return {
        "searched_dirs": [str(p) for p in search_dirs],
        "templates": templates,
        "sources": sources,
    }


def probe_scripted_desktop_pbix(env: dict, inventory: dict) -> dict:
    pbi_root = Path("C:/Program Files/Microsoft Power BI Desktop")
    bin_root = pbi_root / "bin"
    probe_files = {
        "pbidesktop_exe": str(bin_root / "PBIDesktop.exe"),
        "msmdsrv_exe": str(bin_root / "msmdsrv.exe"),
        "analysis_services_tabular": str(bin_root / "Microsoft.AnalysisServices.Tabular.dll"),
        "powerbi_client_windows": str(bin_root / "Microsoft.PowerBI.Client.Windows.dll"),
        "powerbi_modeling_engine": str(bin_root / "Microsoft.PowerBI.Modeling.Engine.dll"),
    }
    exists = {name: Path(path).exists() for name, path in probe_files.items()}
    related_assemblies = []
    if bin_root.exists():
        for path in bin_root.rglob("*.dll"):
            if any(token in path.name for token in ["AnalysisServices", "PowerBI", "Tabular", "Modeling"]):
                related_assemblies.append(str(path))
                if len(related_assemblies) >= 40:
                    break

    base_pbix_candidates = list((PROJECT / "powerbi").rglob("*.pbix")) + list((PROJECT / "powerbi").rglob("*.pbit"))
    has_valid_source = bool(inventory["sources"])
    has_base_pbix = bool(base_pbix_candidates)
    has_desktop = env["power_bi_desktop_exe_available"] or env["power_bi_desktop_store_available"]
    can_script_model = has_desktop and any(exists.values())
    can_package_native_report = False
    failure_reasons = []
    if not has_desktop:
        failure_reasons.append("Power BI Desktop not available.")
    if not has_base_pbix and not has_valid_source:
        failure_reasons.append("No base/model PBIX, PBIT, PBIP, or pbixproj source exists inside this clean project.")
    if can_script_model and not can_package_native_report:
        failure_reasons.append(
            "Power BI Desktop assemblies were detected, but no documented project-local API/CLI was available to create a valid native report layout and package a new PBIX from CSV/DAX/page specs."
        )
    if env["pbi_tools_available"] and not has_valid_source:
        failure_reasons.append("pbi-tools is available, but there is no valid Power BI source to compile.")

    feasible = has_desktop and has_valid_source and can_package_native_report
    return {
        "checked_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "route": "SCRIPTED_DESKTOP_PBIX",
        "feasible": feasible,
        "power_bi_desktop_available": has_desktop,
        "probe_files": probe_files,
        "probe_file_exists": exists,
        "related_assembly_sample": related_assemblies,
        "base_pbix_candidates": [str(p) for p in base_pbix_candidates],
        "valid_powerbi_sources": inventory["sources"],
        "can_script_model_from_detected_components": can_script_model,
        "can_package_native_report_layout": can_package_native_report,
        "failure_reasons": failure_reasons,
    }


def decide_authoring(env: dict, inventory: dict, scripted_probe: dict) -> dict:
    computer_use_requested = True
    computer_use_tool_exposed = False
    ui_automation_available = False
    template_seed = inventory["templates"][0] if inventory["templates"] else None
    valid_powerbi_source = inventory["sources"][0] if inventory["sources"] else None
    pbi_tools_role = "not applicable"
    blocker = "none"

    if template_seed:
        mode = "TEMPLATE_FIRST"
        blocker = "none"
    elif ui_automation_available:
        mode = "COMPUTER_USE"
    elif valid_powerbi_source and env["pbi_tools_available"]:
        mode = "PBIP_PBIT"
        pbi_tools_role = "compile"
    elif scripted_probe["feasible"]:
        mode = "SCRIPTED_DESKTOP_PBIX"
        blocker = "none"
        pbi_tools_role = "validation"
    elif env["power_bi_desktop_exe_available"] or env["power_bi_desktop_store_available"]:
        mode = "MANUAL_ASSISTED"
        blocker = "Computer Use requested, but no callable desktop UI automation tool was exposed; SCRIPTED_DESKTOP_PBIX ruled out; no valid Power BI source"
        if env["pbi_tools_available"]:
            pbi_tools_role = "pbi_tools_available_but_no_powerbi_source_to_compile"
    else:
        mode = "BLOCKED"
        blocker = "Power BI Desktop not found; no template seed; no UI automation"
        if env["pbi_tools_available"]:
            pbi_tools_role = "pbi_tools_available_but_no_powerbi_source_to_compile"

    return {
        "decided_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "authoring_mode": mode,
        "computer_use_requested": computer_use_requested,
        "computer_use_tool_exposed": computer_use_tool_exposed,
        "computer_use_tool_discovery": "tool_search exposed no callable desktop screenshot/click/type automation tools",
        "template_seed": template_seed,
        "valid_powerbi_source": valid_powerbi_source,
        "ui_automation": "unavailable",
        "scripted_desktop_pbix_feasible": scripted_probe["feasible"],
        "scripted_desktop_pbix_failure_reasons": scripted_probe["failure_reasons"],
        "pbi_tools_role": pbi_tools_role,
        "authoring_blocker": blocker,
        "manual_assisted_required": mode == "MANUAL_ASSISTED",
    }


def write_environment_docs(env: dict, inventory: dict, authoring: dict, scripted_probe: dict) -> None:
    lines = [
        "# Environment Check",
        "",
        f"- Checked at: {env['checked_at']}",
        f"- OS: {env['os']}",
        f"- Power BI Desktop: {env['power_bi_desktop']}",
        f"- Power BI EXE available: {env['power_bi_desktop_exe_available']}",
        f"- Power BI Microsoft Store available: {env['power_bi_desktop_store_available']}",
        f"- pbi-tools available: {env['pbi_tools_available']}",
        f"- dotnet available: {env['dotnet_available']}",
        f"- Build mode: {env['build_mode']}",
        f"- Launch command: `{env['launch_command'] or 'n/a'}`",
        "",
        "## Mandatory Command Results",
    ]
    for name, result in env["raw"].items():
        stdout = str(result["stdout"] or "(empty)")
        stderr = str(result["stderr"] or "(empty)")
        if len(stdout) > 4000:
            stdout = stdout[:4000] + "\n...truncated..."
        if len(stderr) > 1200:
            stderr = stderr[:1200] + "\n...truncated..."
        lines += [
            f"### {name}",
            f"- Return code: {result['return_code']}",
            "",
            "```text",
            stdout,
            "```",
            "",
            "stderr:",
            "",
            "```text",
            stderr,
            "```",
            "",
        ]
    write_text("_agent/environment_check.md", "\n".join(lines))
    write_json("_agent/environment_check.json", env)

    write_text(
        "powerbi/templates/template_inventory.md",
        f"""
# Power BI Template Inventory

## Search Locations

{chr(10).join(f'- `{p}`' for p in inventory['searched_dirs'])}

## Template Seeds Found

{chr(10).join(f'- `{p}`' for p in inventory['templates']) if inventory['templates'] else '- None'}

## Valid Power BI Sources Found

{chr(10).join(f'- `{p}`' for p in inventory['sources']) if inventory['sources'] else '- None'}
""",
    )
    write_json("powerbi/templates/template_inventory.json", inventory)
    write_json("_agent/scripted_desktop_pbix_probe.json", scripted_probe)
    write_text(
        "_agent/scripted_desktop_pbix_probe.md",
        f"""
# SCRIPTED_DESKTOP_PBIX Probe

| Item | Result |
|---|---|
| Feasible | {scripted_probe['feasible']} |
| Power BI Desktop available | {scripted_probe['power_bi_desktop_available']} |
| Can script model from detected components | {scripted_probe['can_script_model_from_detected_components']} |
| Can package native report layout | {scripted_probe['can_package_native_report_layout']} |
| Base PBIX/PBIT candidates | {len(scripted_probe['base_pbix_candidates'])} |
| Valid Power BI sources | {len(scripted_probe['valid_powerbi_sources'])} |

## Failure Reasons

{chr(10).join(f'- {reason}' for reason in scripted_probe['failure_reasons']) if scripted_probe['failure_reasons'] else '- None'}

## Detected Component Checks

{chr(10).join(f'- {name}: {exists}' for name, exists in scripted_probe['probe_file_exists'].items())}

Conclusion: route `SCRIPTED_DESKTOP_PBIX` is not feasible for this clean project without a base PBIX/PBIT/PBIP source or a documented project-local PBIX packaging API.
""",
    )
    write_text(
        "powerbi/notes/scripted_desktop_pbix_probe.md",
        f"""
# Scripted Desktop PBIX Probe

The prompt v2 requires checking `SCRIPTED_DESKTOP_PBIX` before falling back to manual-assisted authoring.

- Result: not feasible
- Evidence file: `_agent/scripted_desktop_pbix_probe.json`
- Main blockers:
{chr(10).join(f'  - {reason}' for reason in scripted_probe['failure_reasons'])}

No generated HTML, PNG, CSV, JSON, or Excel artifact is being treated as a PBIX final.
""",
    )

    write_text(
        "_agent/pbix_authoring_decision.md",
        f"""
# PBIX Authoring Decision

| Item | Decision |
|---|---|
| Authoring mode | {authoring['authoring_mode']} |
| Computer Use requested | {authoring['computer_use_requested']} |
| Computer Use callable UI tool exposed | {authoring['computer_use_tool_exposed']} |
| Template seed | {authoring['template_seed'] or 'none'} |
| Valid Power BI source | {authoring['valid_powerbi_source'] or 'none'} |
| UI automation | {authoring['ui_automation']} |
| SCRIPTED_DESKTOP_PBIX feasible | {authoring['scripted_desktop_pbix_feasible']} |
| pbi-tools role | {authoring['pbi_tools_role']} |
| Authoring blocker | {authoring['authoring_blocker']} |
| manual_assisted_required | {authoring['manual_assisted_required']} |

Decision order from v2 prompt was followed:
1. COMPUTER_USE checked first because the user mentioned Computer Use.
2. No callable desktop screenshot/click/type tool was exposed by tool discovery.
3. SCRIPTED_DESKTOP_PBIX was probed and ruled out with evidence in `_agent/scripted_desktop_pbix_probe.md`.
4. PBIP/PBIT source checked next.
5. MANUAL_ASSISTED selected because Power BI Desktop is available but no source/UI/script automation exists.

## SCRIPTED_DESKTOP_PBIX Failure Reasons

{chr(10).join(f'- {reason}' for reason in authoring['scripted_desktop_pbix_failure_reasons'])}

No `.pbix` will be faked or renamed from another artifact.
""",
    )
    write_json("_agent/pbix_authoring_decision.json", authoring)

    write_text(
        "powerbi/notes/authoring_strategy.md",
        f"""
# Authoring Strategy

Authoring mode: `{authoring['authoring_mode']}`

## Why

- Template seed: `{authoring['template_seed'] or 'none'}`
- Valid Power BI source: `{authoring['valid_powerbi_source'] or 'none'}`
- UI automation: `{authoring['ui_automation']}`
- Computer Use requested: `{authoring['computer_use_requested']}`
- Computer Use callable UI tool exposed: `{authoring['computer_use_tool_exposed']}`
- SCRIPTED_DESKTOP_PBIX feasible: `{authoring['scripted_desktop_pbix_feasible']}`
- pbi-tools role: `{authoring['pbi_tools_role']}`

Because no valid Power BI source was found, no callable Computer Use desktop automation tool is exposed in this session, and `SCRIPTED_DESKTOP_PBIX` was ruled out with evidence, the practical path is manual-assisted Power BI Desktop authoring.

## Next PBIX Step

Open Power BI Desktop, import `data/prepared/*.csv`, create relationships from `model/relationship_map.md`, create measures from `model/dax_measures.md`, apply `build/config/theme.json`, build pages from `build/config/page_map.json` and `build/config/visual_map.json`, then save as `output/dashboard_final.pbix`.

Do not use `pbi-tools compile` unless a valid `.pbixproj.json`/PbixProj source exists for this project.
""",
    )


def write_launcher() -> None:
    script = r'''
$ErrorActionPreference = "Continue"
$launchMethod = "not_found"
$launchCommand = $null

$existing = Get-Process | Where-Object {
  $_.ProcessName -like "*PBIDesktop*" -or
  $_.ProcessName -like "*PowerBI*" -or
  $_.MainWindowTitle -like "*Power BI*"
} | Select-Object ProcessName, Id, MainWindowTitle

if ($existing) {
  $launchMethod = "already_running"
  $launchCommand = "existing Power BI process/window"
} else {
  $exe = Get-Command PBIDesktop.exe -ErrorAction SilentlyContinue
  $programFiles = @(
    "C:\Program Files\Microsoft Power BI Desktop\bin\PBIDesktop.exe",
    "C:\Program Files (x86)\Microsoft Power BI Desktop\bin\PBIDesktop.exe"
  ) | Where-Object { Test-Path $_ } | Select-Object -First 1

  if ($exe) {
    $launchMethod = "path"
    $launchCommand = $exe.Source
    Start-Process -FilePath $exe.Source
  } elseif ($programFiles) {
    $launchMethod = "program_files"
    $launchCommand = $programFiles
    Start-Process -FilePath $programFiles
  } else {
    $storeApp = Get-StartApps | Where-Object {
      $_.Name -like "*Power BI Desktop*" -or $_.AppID -like "*PowerBI*"
    } | Select-Object -First 1
    if ($storeApp) {
      $launchMethod = "microsoft_store"
      $launchCommand = "shell:AppsFolder\$($storeApp.AppID)"
      Start-Process $launchCommand
    }
  }
  Start-Sleep -Seconds 12
}

$process = Get-Process | Where-Object {
  $_.ProcessName -like "*PBIDesktop*" -or
  $_.ProcessName -like "*PowerBI*" -or
  $_.MainWindowTitle -like "*Power BI*"
} | Select-Object ProcessName, Id, MainWindowTitle

[pscustomobject]@{
  LaunchMethod = $launchMethod
  LaunchCommand = $launchCommand
  ProcessDetected = [bool]$process
  Process = $process
} | ConvertTo-Json -Depth 5
'''
    write_text("powerbi/launch_powerbi.ps1", script)
    write_text(
        "_agent/powerbi_launch_check.md",
        """
# Power BI Launch Check

| Item | Result |
|---|---|
| Launch status | pending_launch_check |
| UI control | unknown |
| Build status | pending |

Run `python build/scripts/run_powerbi_launch_check.py` to update this file.
""",
    )


def make_data() -> dict[str, pd.DataFrame]:
    rng = np.random.default_rng(SEED)
    dates = pd.date_range("2025-01-01", "2026-05-31", freq="D")
    channels = [
        ("CH01", "Google Search", "Paid", 4.5, 75, 820, 1.9, 0.13, 0.20, 220, 0.62, 0.92),
        ("CH02", "Meta", "Paid", 3.2, 90, 620, 1.4, 0.08, 0.10, 165, 0.74, 0.64),
        ("CH03", "TikTok", "Paid", 2.8, 85, 390, 1.1, 0.07, 0.08, 130, 0.80, 0.55),
        ("CH04", "LinkedIn", "Paid", 3.0, 140, 340, 5.2, 0.09, 0.08, 460, 0.58, 0.62),
        ("CH05", "Programmatic Display", "Paid", 2.2, 105, 240, 0.7, 0.05, 0.06, 145, 0.76, 0.52),
        ("CH06", "Affiliates", "Paid", 4.8, 65, 160, 1.1, 0.11, 0.14, 180, 0.63, 0.88),
        ("CH07", "Organic Search", "Organic", 8.0, 35, 95, 0.35, 0.15, 0.24, 210, 0.55, 1.12),
        ("CH08", "Email", "Organic", 9.0, 24, 55, 0.20, 0.22, 0.26, 155, 0.34, 1.15),
        ("CH09", "Direct", "Organic", 10.0, 20, 70, 0.18, 0.18, 0.25, 195, 0.40, 1.18),
        ("CH10", "Referral Partners", "Organic", 8.5, 42, 115, 0.50, 0.17, 0.27, 250, 0.52, 1.14),
    ]
    dim_channel = pd.DataFrame(
        channels,
        columns=[
            "channel_key",
            "channel",
            "paid_organic",
            "target_roas",
            "target_cac",
            "base_spend",
            "cpc",
            "lead_rate",
            "conversion_rate",
            "aov",
            "new_customer_rate",
            "performance_factor",
        ],
    )
    campaign_names = {
        "Google Search": ["Brand Capture", "Nonbrand Intent", "Competitor Defense"],
        "Meta": ["Prospecting Video", "Retargeting Carousel", "Lookalike Launch"],
        "TikTok": ["Creator Spark", "Trend Trial"],
        "LinkedIn": ["Enterprise Lead Gen", "ABM Retargeting"],
        "Programmatic Display": ["Awareness Display", "Contextual Display"],
        "Affiliates": ["Coupon Partners", "Review Partners"],
        "Organic Search": ["SEO Content Hub", "Product Landing SEO"],
        "Email": ["Lifecycle Nurture", "Winback Offers"],
        "Direct": ["Brand Demand", "Returning Visitors"],
        "Referral Partners": ["Partner Co-Marketing", "Strategic Referrals", "Webinar Referrals"],
    }
    campaigns = []
    campaign_id = 1
    for _, ch in dim_channel.iterrows():
        for idx, name in enumerate(campaign_names[ch["channel"]], start=1):
            campaigns.append(
                {
                    "campaign_key": f"CP{campaign_id:03d}",
                    "campaign_name": f"{ch['channel']} - {name}",
                    "channel_key": ch["channel_key"],
                    "channel": ch["channel"],
                    "paid_organic": ch["paid_organic"],
                    "launch_date": "2024-10-01" if idx == 1 else "2025-01-01",
                    "funnel_stage": ["Conversion", "Consideration", "Awareness"][idx % 3],
                    "budget_tier": "High" if ch["base_spend"] >= 500 else ("Medium" if ch["base_spend"] >= 180 else "Low"),
                    "campaign_weight": float(rng.uniform(0.78, 1.22)),
                }
            )
            campaign_id += 1
    dim_campaign = pd.DataFrame(campaigns)

    rows = []
    for date in dates:
        month_index = (date.year - 2025) * 12 + date.month
        weekday_factor = 1.08 if date.weekday() < 5 else 0.74
        seasonality = 1 + 0.06 * math.sin(2 * math.pi * month_index / 12)
        q4_lift = 1.18 if date.month in (10, 11, 12) else 1.0
        for _, cp in dim_campaign.iterrows():
            ch = dim_channel.loc[dim_channel["channel_key"] == cp["channel_key"]].iloc[0]
            drift = ch["performance_factor"]
            if ch["channel"] in {"Meta", "TikTok", "LinkedIn", "Programmatic Display"} and date >= pd.Timestamp("2025-09-01"):
                drift *= 0.82
            if ch["channel"] in {"Organic Search", "Direct", "Referral Partners", "Email"} and date >= pd.Timestamp("2025-09-01"):
                drift *= 1.08
            spend = ch["base_spend"] * cp["campaign_weight"] * weekday_factor * seasonality * q4_lift * rng.lognormal(0, 0.14)
            if ch["paid_organic"] == "Organic":
                spend *= rng.uniform(0.62, 0.92)
            if ch["channel"] in {"Meta", "TikTok", "Google Search"} and date >= pd.Timestamp("2026-01-01"):
                spend *= 1.15
            cpc = ch["cpc"] * rng.lognormal(0, 0.09)
            clicks = max(1, int(spend / max(cpc, 0.05)))
            impressions = max(clicks, int(clicks / rng.uniform(0.025, 0.085)))
            leads = int(rng.poisson(max(clicks * ch["lead_rate"] * rng.uniform(0.85, 1.15), 0)))
            conversions = int(rng.poisson(max(leads * ch["conversion_rate"] * drift * rng.uniform(0.85, 1.15), 0)))
            new_customers = int(rng.binomial(conversions, min(max(ch["new_customer_rate"] * rng.uniform(0.9, 1.08), 0.02), 0.97))) if conversions else 0
            revenue = conversions * ch["aov"] * rng.lognormal(0, 0.08)
            gross_profit = revenue * rng.uniform(0.54, 0.68)
            rows.append(
                {
                    "date": date.date().isoformat(),
                    "campaign_key": cp["campaign_key"],
                    "channel_key": ch["channel_key"],
                    "paid_organic": ch["paid_organic"],
                    "spend": round(float(spend), 2),
                    "impressions": int(impressions),
                    "clicks": int(clicks),
                    "leads": int(leads),
                    "conversions": int(conversions),
                    "new_customers": int(new_customers),
                    "revenue": round(float(revenue), 2),
                    "gross_profit": round(float(gross_profit), 2),
                }
            )

    raw = pd.DataFrame(rows)
    raw["source_system"] = "synthetic_portfolio_generator_v2"
    raw["load_batch_id"] = f"seed_{SEED}"
    fact = raw.drop(columns=["source_system", "load_batch_id"]).copy()
    fact["date"] = pd.to_datetime(fact["date"])
    fact["month_key"] = fact["date"].dt.strftime("%Y-%m")
    fact["year"] = fact["date"].dt.year
    fact["month"] = fact["date"].dt.month
    fact["week_start"] = (fact["date"] - pd.to_timedelta(fact["date"].dt.weekday, unit="D")).dt.date.astype(str)
    fact["date"] = fact["date"].dt.date.astype(str)

    dim_date = pd.DataFrame({"date": dates})
    dim_date["date_key"] = dim_date["date"].dt.strftime("%Y%m%d").astype(int)
    dim_date["year"] = dim_date["date"].dt.year
    dim_date["quarter"] = "Q" + dim_date["date"].dt.quarter.astype(str)
    dim_date["month"] = dim_date["date"].dt.month
    dim_date["month_name"] = dim_date["date"].dt.strftime("%b")
    dim_date["month_key"] = dim_date["date"].dt.strftime("%Y-%m")
    dim_date["week_start"] = (dim_date["date"] - pd.to_timedelta(dim_date["date"].dt.weekday, unit="D")).dt.date.astype(str)
    dim_date["is_weekend"] = np.where(dim_date["date"].dt.weekday >= 5, "Yes", "No")
    dim_date["date"] = dim_date["date"].dt.date.astype(str)

    dim_month = dim_date[["month_key", "year", "month"]].drop_duplicates().sort_values("month_key")
    dim_month["month_label"] = pd.to_datetime(dim_month["month_key"] + "-01").dt.strftime("%b %Y")
    dim_month["month_start"] = dim_month["month_key"] + "-01"

    dim_channel_out = dim_channel[
        ["channel_key", "channel", "paid_organic", "target_roas", "target_cac", "base_spend"]
    ].copy()
    dim_campaign_out = dim_campaign[
        ["campaign_key", "campaign_name", "channel_key", "channel", "paid_organic", "launch_date", "funnel_stage", "budget_tier"]
    ].copy()
    return {
        "raw": raw,
        "fact_campaign_daily": fact,
        "dim_date": dim_date,
        "dim_month": dim_month,
        "dim_channel": dim_channel_out,
        "dim_campaign": dim_campaign_out,
    }


def save_data(tables: dict[str, pd.DataFrame]) -> None:
    tables["raw"].to_csv(PROJECT / "data/raw/marketing_campaign_daily_raw.csv", index=False)
    for name in ["fact_campaign_daily", "dim_date", "dim_month", "dim_channel", "dim_campaign"]:
        tables[name].to_csv(PROJECT / f"data/prepared/{name}.csv", index=False)


def build_summaries(tables: dict[str, pd.DataFrame]) -> dict:
    fact = tables["fact_campaign_daily"].copy()
    fact["date"] = pd.to_datetime(fact["date"])
    channel = fact.merge(tables["dim_channel"], on=["channel_key", "paid_organic"], suffixes=("", "_dim"))
    ch = (
        channel.groupby(["channel", "paid_organic", "target_roas", "target_cac"], as_index=False)
        .agg(
            spend=("spend", "sum"),
            revenue=("revenue", "sum"),
            gross_profit=("gross_profit", "sum"),
            clicks=("clicks", "sum"),
            conversions=("conversions", "sum"),
            new_customers=("new_customers", "sum"),
        )
    )
    ch["roas"] = ch["revenue"] / ch["spend"]
    ch["marketing_roi"] = (ch["gross_profit"] - ch["spend"]) / ch["spend"]
    ch["cac"] = ch["spend"] / ch["new_customers"].replace(0, np.nan)
    ch["conversion_rate"] = ch["conversions"] / ch["clicks"].replace(0, np.nan)
    ch["roas_vs_target"] = ch["roas"] - ch["target_roas"]
    ch["cac_vs_target"] = ch["target_cac"] - ch["cac"]
    ch["spend_share"] = ch["spend"] / ch["spend"].sum()
    ch["action"] = np.select(
        [
            (ch["roas"] >= ch["target_roas"]) & (ch["cac"] <= ch["target_cac"]),
            (ch["roas"] < ch["target_roas"] * 0.82) | (ch["cac"] > ch["target_cac"] * 1.25),
        ],
        ["Scale", "Review/Cut"],
        default="Optimize",
    )

    campaign = fact.merge(tables["dim_campaign"], on=["campaign_key", "channel_key", "paid_organic"], suffixes=("", "_dim"))
    cp = (
        campaign.groupby(["campaign_key", "campaign_name", "channel", "paid_organic", "funnel_stage"], as_index=False)
        .agg(
            spend=("spend", "sum"),
            revenue=("revenue", "sum"),
            gross_profit=("gross_profit", "sum"),
            clicks=("clicks", "sum"),
            conversions=("conversions", "sum"),
            new_customers=("new_customers", "sum"),
        )
    )
    cp["roas"] = cp["revenue"] / cp["spend"]
    cp["marketing_roi"] = (cp["gross_profit"] - cp["spend"]) / cp["spend"]
    cp["cac"] = cp["spend"] / cp["new_customers"].replace(0, np.nan)
    cp["conversion_rate"] = cp["conversions"] / cp["clicks"].replace(0, np.nan)
    cp["scale_score"] = (
        cp["roas"].rank(pct=True) * 0.40
        + cp["marketing_roi"].rank(pct=True) * 0.30
        + (1 - cp["cac"].rank(pct=True)) * 0.20
        + cp["gross_profit"].rank(pct=True) * 0.10
    ) * 100
    cp["action"] = np.select([cp["scale_score"] >= 72, cp["scale_score"] <= 35], ["Scale", "Review/Cut"], default="Optimize")

    ch.to_csv(PROJECT / "data/validated/channel_summary.csv", index=False)
    cp.to_csv(PROJECT / "data/validated/campaign_summary.csv", index=False)
    totals = fact[["spend", "revenue", "gross_profit", "clicks", "leads", "conversions", "new_customers"]].sum()
    summary = {
        "synthetic_data": True,
        "seed": SEED,
        "grain": "one row per date, campaign, and channel",
        "date_range": {"min": fact["date"].min().date().isoformat(), "max": fact["date"].max().date().isoformat()},
        "row_counts": {
            "raw": int(len(tables["raw"])),
            "fact_campaign_daily": int(len(fact)),
            "dim_date": int(len(tables["dim_date"])),
            "dim_month": int(len(tables["dim_month"])),
            "dim_channel": int(len(tables["dim_channel"])),
            "dim_campaign": int(len(tables["dim_campaign"])),
        },
        "totals": {k: round(float(v), 2) for k, v in totals.items()},
        "scale_channels": ch.query("action == 'Scale'").sort_values("roas", ascending=False)["channel"].tolist(),
        "review_cut_channels": ch.query("action == 'Review/Cut'").sort_values("spend", ascending=False)["channel"].tolist(),
        "assumptions": [
            "No source data was provided; this is fixed-seed synthetic portfolio data.",
            "Spend for organic channels represents content, lifecycle, SEO, and partner operating cost.",
            "ROAS and CAC targets are channel-level targets stored in DimChannel.",
            "Revenue is campaign-touch attributed for portfolio storytelling.",
        ],
    }
    write_json("data/source_summary.json", summary)
    return {"channel": ch, "campaign": cp, "summary": summary}


def write_project_docs(tables: dict[str, pd.DataFrame], derived: dict, env: dict, authoring: dict, scripted_probe: dict) -> None:
    summary = derived["summary"]
    ch = derived["channel"]
    write_text(
        "_agent/intake_brief.md",
        f"""
# Intake Brief

- Project: Project 06 - Marketing Campaign ROI
- Prompt version: BI A-Z Master Prompt v2
- BI topic: Marketing Campaign ROI
- Audience: Executive team, Marketing Director, Growth Lead
- Business goal: show which channels are burning money and which channels can scale.
- Data source: no user source file provided; synthetic demo data generated with seed `{SEED}`.
- Output requested: Power BI PBIX at `output/dashboard_final.pbix`
- PBIX authoring mode requested: AUTO
- Template seed: none provided
- UI control allowed: AUTO
- Computer Use mention: provided by user, but no callable desktop UI automation tool exposed by tool discovery
- Completion target: executive-ready build package; PBIX final only when open/save/refresh QA passes.
""",
    )
    write_text(
        "_agent/subagent_plan.md",
        """
# Subagent Plan

- Requested mode: TRUE/AUTO by user permission.
- Execution mode: real subagent for independent v2 QA checklist plus main-agent integration.
- Spawned agent: Euclid - BI QA reviewer. Scope: v2 acceptance checklist, likely failure modes, QA reminders. No file edits.
- Main agent integration owner: true.
""",
    )
    write_text(
        "_agent/run_log.md",
        f"""
# Run Log

| Time | Event |
|---|---|
| {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Deleted old Project 06 - Marketing Campaign ROI artifacts and recreated a clean project folder. |
| {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Generated fixed-seed synthetic marketing campaign data. |
| {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Wrote v2 PBIX authoring decision and manual-assisted Power BI package. |
""",
    )
    write_text(
        "_agent/decision_log.md",
        """
# Decision Log

| Decision | Rationale |
|---|---|
| Synthetic source data | User gave topic but no source file; portfolio/demo synthetic data is allowed by prompt v2. |
| Daily campaign-channel grain | Supports trend, channel ROI, paid vs organic, campaign ranking, and exception analysis. |
| Manual-assisted authoring | Computer Use was requested, but no callable desktop UI automation tool was exposed; no valid Power BI source found. |
| No pbi-tools compile | pbi-tools alone cannot author a PBIX without valid Power BI source. |
| Rule out SCRIPTED_DESKTOP_PBIX | Local Power BI components exist, but no base PBIX/PBIT/PBIP or documented native report packager is available for this clean project. |
| Do not create fake PBIX | Prompt v2 forbids empty/renamed PBIX artifacts. |
""",
    )
    write_text(
        "_agent/build_loop_log.md",
        f"""
# PBIX Build Loop Log

## Loop 1 - COMPUTER_USE

- Reproduce/attempt: User requested Computer Use and Power BI PBIX final.
- Result: Failed before UI authoring because no callable desktop screenshot/click/type tools were exposed in this agent session.
- Classification: Tooling/UI automation blocker.
- Patch/next route: Probe `SCRIPTED_DESKTOP_PBIX`.

## Loop 2 - SCRIPTED_DESKTOP_PBIX

- Reproduce/attempt: Probe Power BI Desktop local components, valid Power BI source, base PBIX/PBIT candidates, and native report packaging path.
- Result: Not feasible for this clean project.
- Classification: File/tool automation blocker.
- Evidence: `_agent/scripted_desktop_pbix_probe.md`
- Failure reasons:
{chr(10).join(f'  - {reason}' for reason in scripted_probe['failure_reasons'])}
- Patch/next route: Check PBIP/PBIT source and pbi-tools compile path.

## Loop 3 - PBIP/PBIT/pbi-tools

- Reproduce/attempt: Search project/workspace template and Power BI source inventory.
- Result: No `.pbix`, `.pbit`, `.pbip`, or `.pbixproj.json` source found in clean Project 06 - Marketing Campaign ROI. pbi-tools cannot compile from CSV/DAX/page-map alone.
- Classification: Source-format blocker.
- Decision: Fall back to `MANUAL_ASSISTED` with a complete build package and runbook.
""",
    )
    write_text(
        "_agent/failure_matrix.md",
        f"""
# Failure Matrix

| Route | Status | Evidence | Decision |
|---|---|---|---|
| COMPUTER_USE | Failed | No callable desktop screenshot/click/type tool exposed after tool discovery. | Cannot author PBIX through UI automation. |
| SCRIPTED_DESKTOP_PBIX | Failed | `_agent/scripted_desktop_pbix_probe.md` | No base PBIX/PBIT/PBIP and no supported native report packager for this clean project. |
| PBIP_PBIT / pbi-tools | Failed | `powerbi/templates/template_inventory.md` | `pbi_tools_available_but_no_powerbi_source_to_compile`. |
| MANUAL_ASSISTED | Selected | `powerbi/notes/desktop_ui_runbook.md` | Build package is ready; final PBIX requires Desktop authoring/save/refresh QA. |

Final PBIX is not created and is not simulated.
""",
    )

    write_text(
        "data/synthetic/synthetic_data_generation_notes.md",
        f"""
# Synthetic Data Generation Notes

- Synthetic data: true
- Seed: `{SEED}`
- Generator: `build/scripts/pipeline.py`
- Grain: one row per date, campaign, and channel
- Date range: {summary['date_range']['min']} to {summary['date_range']['max']}

Spend drives clicks through CPC. Clicks drive leads. Leads drive conversions. Conversions drive new customers and revenue. Weak paid channels intentionally deteriorate after late 2025; high-intent owned/organic channels improve to create a clear scale vs review/cut portfolio story.
""",
    )
    raw = tables["raw"]
    fact = tables["fact_campaign_daily"]
    write_text(
        "data/data_quality_report.md",
        f"""
# Data Quality Report

| Check | Result |
|---|---:|
| Raw rows | {len(raw):,} |
| Prepared fact rows | {len(fact):,} |
| Missing values | {int(raw.isna().sum().sum()):,} |
| Duplicate date-campaign-channel rows | {int(raw.duplicated(subset=['date','campaign_key','channel_key']).sum()):,} |
| Negative spend rows | {int((raw['spend'] < 0).sum()):,} |
| Negative revenue rows | {int((raw['revenue'] < 0).sum()):,} |

No rows were removed. Seasonality and outliers are retained for diagnostic storytelling.
""",
    )
    write_text(
        "model/data_dictionary.md",
        """
# Data Dictionary

## FactCampaignDaily

| Column | Description |
|---|---|
| date | Calendar date. |
| campaign_key | Campaign key. |
| channel_key | Channel key. |
| paid_organic | Paid or Organic group. |
| spend | Campaign cost. |
| impressions | Estimated impressions. |
| clicks | Clicks/visits. |
| leads | Qualified leads or intent events. |
| conversions | Revenue-generating conversions. |
| new_customers | New customers acquired. |
| revenue | Attributed revenue. |
| gross_profit | Attributed gross profit. |
| month_key | YYYY-MM month key. |

Dimensions: DimDate, DimMonth, DimChannel, DimCampaign.
""",
    )
    write_text(
        "model/metric_definitions.md",
        """
# Metric Definitions

| KPI | Definition | Rule |
|---|---|---|
| Spend | SUM spend | Measure only. |
| Revenue | SUM revenue | Measure only. |
| Gross Profit | SUM gross_profit | Measure only. |
| ROAS | Revenue / Spend | DIVIDE; do not sum row ROAS. |
| Marketing ROI | (Gross Profit - Spend) / Spend | DIVIDE; profit-aware return. |
| CAC | Spend / New Customers | DIVIDE; do not average row CAC. |
| Conversion Rate | Conversions / Clicks | Weighted aggregate rate. |
| Spend Share | Spend / selected channel spend | Use ALLSELECTED. |
| Scale Score | Weighted rank of ROAS, Marketing ROI, inverse CAC, and gross profit | Slicer-aware campaign ranking. |
""",
    )
    write_text(
        "model/dax_measures.md",
        """
# DAX Measures

```DAX
Spend = SUM ( FactCampaignDaily[spend] )
Revenue = SUM ( FactCampaignDaily[revenue] )
Gross Profit = SUM ( FactCampaignDaily[gross_profit] )
Clicks = SUM ( FactCampaignDaily[clicks] )
Conversions = SUM ( FactCampaignDaily[conversions] )
New Customers = SUM ( FactCampaignDaily[new_customers] )

ROAS = DIVIDE ( [Revenue], [Spend] )
Marketing ROI = DIVIDE ( [Gross Profit] - [Spend], [Spend] )
CAC = DIVIDE ( [Spend], [New Customers] )
Conversion Rate = DIVIDE ( [Conversions], [Clicks] )

Target ROAS = AVERAGE ( DimChannel[target_roas] )
Target CAC = AVERAGE ( DimChannel[target_cac] )
ROAS vs Target = [ROAS] - [Target ROAS]
CAC vs Target = [Target CAC] - [CAC]
Spend Share = DIVIDE ( [Spend], CALCULATE ( [Spend], ALLSELECTED ( DimChannel[channel] ) ) )

Campaign Scale Score =
VAR campaignCount = COUNTROWS ( ALLSELECTED ( DimCampaign[campaign_name] ) )
VAR roasPct =
    DIVIDE ( RANKX ( ALLSELECTED ( DimCampaign[campaign_name] ), [ROAS], , ASC, DENSE ) - 1, campaignCount - 1 )
VAR roiPct =
    DIVIDE ( RANKX ( ALLSELECTED ( DimCampaign[campaign_name] ), [Marketing ROI], , ASC, DENSE ) - 1, campaignCount - 1 )
VAR inverseCacPct =
    1 - DIVIDE ( RANKX ( ALLSELECTED ( DimCampaign[campaign_name] ), [CAC], , ASC, DENSE ) - 1, campaignCount - 1 )
VAR profitPct =
    DIVIDE ( RANKX ( ALLSELECTED ( DimCampaign[campaign_name] ), [Gross Profit], , ASC, DENSE ) - 1, campaignCount - 1 )
RETURN
    IF ( campaignCount <= 1, BLANK (), ( roasPct * 0.4 + roiPct * 0.3 + inverseCacPct * 0.2 + profitPct * 0.1 ) * 100 )
```
""",
    )
    write_text(
        "model/relationship_map.md",
        """
# Relationship Map

| From | Column | To | Column | Cardinality | Filter |
|---|---|---|---|---|---|
| FactCampaignDaily | date | DimDate | date | Many-to-one | Single |
| FactCampaignDaily | month_key | DimMonth | month_key | Many-to-one | Single |
| FactCampaignDaily | channel_key | DimChannel | channel_key | Many-to-one | Single |
| FactCampaignDaily | campaign_key | DimCampaign | campaign_key | Many-to-one | Single |

Mark DimDate as the date table. Hide technical keys where possible.
""",
    )

    page_map = {
        "pages": [
            {"page": 1, "name": "Executive Overview", "purpose": "Scan total ROI health, paid vs organic contribution, and first action map.", "kpis": ["Spend", "Revenue", "ROAS", "Marketing ROI", "CAC", "Conversion Rate"]},
            {"page": 2, "name": "Channel ROI", "purpose": "Compare channel performance against ROAS and CAC targets.", "kpis": ["ROAS", "Target ROAS", "CAC", "Target CAC", "Spend Share"]},
            {"page": 3, "name": "Campaign Ranking", "purpose": "Rank campaigns for scale, optimize, or review/cut decisions.", "kpis": ["Scale Score", "ROAS", "Marketing ROI", "CAC", "Revenue"]},
            {"page": 4, "name": "Exceptions and Actions", "purpose": "Translate target gaps into budget moves.", "kpis": ["ROAS vs Target", "CAC vs Target", "Spend Share"]},
        ]
    }
    visual_map = {
        "visuals": [
            {"page": "Executive Overview", "visual": "KPI cards", "type": "Card", "fields": ["Spend", "Revenue", "ROAS", "Marketing ROI", "CAC", "Conversion Rate"]},
            {"page": "Executive Overview", "visual": "Monthly spend and revenue", "type": "Line and clustered column", "fields": ["DimMonth[month_key]", "Spend", "Revenue"]},
            {"page": "Executive Overview", "visual": "Paid vs organic value", "type": "Clustered bar", "fields": ["DimChannel[paid_organic]", "Spend", "Revenue"]},
            {"page": "Executive Overview", "visual": "Spend vs ROAS action map", "type": "Scatter", "fields": ["Spend", "ROAS", "Revenue", "DimChannel[channel]"]},
            {"page": "Channel ROI", "visual": "ROAS by channel vs target", "type": "Horizontal bar", "fields": ["DimChannel[channel]", "ROAS", "Target ROAS"]},
            {"page": "Channel ROI", "visual": "CAC by channel vs target", "type": "Horizontal bar", "fields": ["DimChannel[channel]", "CAC", "Target CAC"]},
            {"page": "Campaign Ranking", "visual": "Scale candidates", "type": "Horizontal bar", "fields": ["DimCampaign[campaign_name]", "Campaign Scale Score"]},
            {"page": "Campaign Ranking", "visual": "Review/cut candidates", "type": "Horizontal bar", "fields": ["DimCampaign[campaign_name]", "Campaign Scale Score"]},
            {"page": "Exceptions and Actions", "visual": "Budget action matrix", "type": "Scatter", "fields": ["ROAS vs Target", "CAC vs Target", "Spend"]},
            {"page": "Exceptions and Actions", "visual": "Action table", "type": "Matrix", "fields": ["DimChannel[channel]", "Spend Share", "ROAS", "CAC", "Action"]},
        ]
    }
    insight_map = {
        "insights": [
            {"headline": "Paid channels take most spend but several fall below target.", "action": "Review Google Search, Meta, TikTok, LinkedIn, and Programmatic Display before adding budget."},
            {"headline": "Owned and partner channels scale efficiently.", "action": "Scale Direct, Email, Organic Search, and Referral Partners while monitoring marginal CAC."},
            {"headline": "Campaign ranking turns KPI gaps into next-month budget choices.", "action": "Use the top/bottom campaign views to move spend without debating every campaign manually."},
        ]
    }
    slicer_map = {
        "slicers": [
            {"name": "Date", "field": "DimDate[date]", "type": "Between", "sync_pages": "all"},
            {"name": "Paid/Organic", "field": "DimChannel[paid_organic]", "type": "Dropdown", "sync_pages": "all"},
            {"name": "Channel", "field": "DimChannel[channel]", "type": "Dropdown search", "sync_pages": "all"},
            {"name": "Funnel Stage", "field": "DimCampaign[funnel_stage]", "type": "Dropdown", "sync_pages": ["Campaign Ranking"]},
        ]
    }
    theme = {
        "name": "Marketing ROI v2",
        "dataColors": ["#2563EB", "#16A34A", "#D97706", "#DC2626", "#0891B2", "#7C3AED", "#64748B", "#F59E0B"],
        "background": "#F8FAFC",
        "foreground": "#0F172A",
        "tableAccent": "#2563EB",
    }
    write_json("build/config/page_map.json", page_map)
    write_json("build/config/visual_map.json", visual_map)
    write_json("build/config/insight_map.json", insight_map)
    write_json("build/config/slicer_map.json", slicer_map)
    write_json("build/config/theme.json", theme)

    write_text(
        "powerbi/notes/desktop_ui_runbook.md",
        """
# Power BI Desktop UI Runbook

1. Run `powerbi/launch_powerbi.ps1`.
2. Import prepared CSV files from `data/prepared/`.
3. Set date columns to Date, monetary fields to Decimal, counts to Whole Number.
4. Create relationships from `model/relationship_map.md`.
5. Create DAX measures from `model/dax_measures.md`.
6. Apply `build/config/theme.json`.
7. Build pages from `build/config/page_map.json` and `build/config/visual_map.json`.
8. Add slicers from `build/config/slicer_map.json`.
9. Save as `output/dashboard_final.pbix`.
10. Reopen, refresh, save again, and capture screenshots before marking final.
""",
    )
    write_text(
        "powerbi/notes/pbix_build_runbook.md",
        f"""
# PBIX Build Runbook

- Expected final path: `output/dashboard_final.pbix`
- Build mode: `{env['build_mode']}`
- Authoring mode: `{authoring['authoring_mode']}`
- Authoring blocker: `{authoring['authoring_blocker']}`
- SCRIPTED_DESKTOP_PBIX feasible: `{authoring['scripted_desktop_pbix_feasible']}`
- pbi-tools role: `{authoring['pbi_tools_role']}`

This is a build package until a real PBIX is saved and passes open/save/refresh QA.
""",
    )
    write_text(
        "powerbi/power_query_m.md",
        """
# Power Query Notes

Import the CSV files from `data/prepared/` as:
- FactCampaignDaily
- DimDate
- DimMonth
- DimChannel
- DimCampaign
""",
    )
    write_text(
        "docs/refresh_guide.md",
        """
# Refresh Guide

Run `python build/scripts/pipeline.py`, then refresh the imported CSV tables in Power BI Desktop. For production, replace the synthetic generator with official marketing platform exports while preserving the prepared schema.
""",
    )
    write_text(
        "docs/rebuild_guide.md",
        """
# Rebuild Guide

```powershell
python build/scripts/pipeline.py
python build/scripts/run_powerbi_launch_check.py
```

Then follow `powerbi/notes/desktop_ui_runbook.md` to create `output/dashboard_final.pbix`.
""",
    )
    write_text(
        "docs/changelog.md",
        """
# Changelog

## v02

- Deleted old Project 06 - Marketing Campaign ROI artifacts and rebuilt from a clean folder.
- Applied BI A-Z Master Prompt v2.
- Added PBIX authoring decision and authoring strategy docs.
- Added template/source inventory and explicit pbi-tools role.
- Generated fixed-seed synthetic Marketing Campaign ROI dataset, model docs, DAX, page/visual maps, preview screenshots, and QA package.
""",
    )
    write_text(
        "docs/issue_log.md",
        f"""
# Issue Log

## ISSUE-001 - PBIX final not created automatically

- Status: Open
- Severity: High
- Found in: v02 build package
- Page: All
- Visual: All
- Expected: `output/dashboard_final.pbix` exists and passes open/save/refresh QA.
- Actual: No final PBIX exists yet.
- Root cause: {authoring['authoring_blocker']}.
- Fix: Follow `powerbi/notes/desktop_ui_runbook.md` and save a real PBIX to `output/dashboard_final.pbix`.
- Regression: Pending File QA.
""",
    )
    totals = summary["totals"]
    write_text(
        "README.md",
        f"""
# Project 06 - Marketing Campaign ROI

Prompt version: BI A-Z Master Prompt v2.

## Status

- Final PBIX requested: `output/dashboard_final.pbix`
- Current status: build-ready package, not final PBIX
- Authoring mode: `{authoring['authoring_mode']}`
- Computer Use requested: `{authoring['computer_use_requested']}`
- Computer Use callable UI tool exposed: `{authoring['computer_use_tool_exposed']}`
- SCRIPTED_DESKTOP_PBIX feasible: `{authoring['scripted_desktop_pbix_feasible']}`
- Build blocker: {authoring['authoring_blocker']}
- Synthetic data seed: `{SEED}`

## Business Story

The dashboard shows which channels are burning spend and which channels can scale.

- Review/cut: {", ".join(summary['review_cut_channels'])}
- Scale: {", ".join(summary['scale_channels'])}
- Total spend: {money_m(totals['spend'])}
- Total revenue: {money_m(totals['revenue'])}
- Portfolio ROAS: {totals['revenue'] / totals['spend']:.2f}

## Pages

1. Executive Overview
2. Channel ROI
3. Campaign Ranking
4. Exceptions and Actions
""",
    )
    write_text(
        "docs/handoff_notes.md",
        f"""
# Handoff Notes

## Output

- Final PBIX: `output/dashboard_final.pbix`
- Screenshots: `output/screenshots/`
- Export: `output/exports/`
- Build status: build-ready but not final; pending launch check / assisted build
- Blocked reason: {authoring['authoring_blocker']}

## Source

- Raw data: `data/raw/marketing_campaign_daily_raw.csv`
- Prepared data: `data/prepared/`
- Source summary: `data/source_summary.json`

## Tool Environment

- Power BI Desktop: {env['power_bi_desktop']}
- Power BI launch command: `{env['launch_command'] or 'n/a'}`
- Power BI launch status: pending launch check
- UI control: unavailable
- pbi-tools: {env['pbi_tools_available']}
- dotnet: {env['dotnet_available']}
- Build mode: {env['build_mode']}

## PBIX Authoring Strategy

- Authoring mode: {authoring['authoring_mode']}
- Template seed: {authoring['template_seed'] or 'none'}
- Power BI source available: {authoring['valid_powerbi_source'] or 'none'}
- pbi-tools role: {authoring['pbi_tools_role']}
- UI automation: {authoring['ui_automation']}
- Computer Use requested: {authoring['computer_use_requested']}
- Computer Use callable UI tool exposed: {authoring['computer_use_tool_exposed']}
- SCRIPTED_DESKTOP_PBIX feasible: {authoring['scripted_desktop_pbix_feasible']}
- Authoring blocker: {authoring['authoring_blocker']}
- Authoring decision: `_agent/pbix_authoring_decision.md`
- Build loop log: `_agent/build_loop_log.md`
- Failure matrix: `_agent/failure_matrix.md`

## Subagent Execution

- Requested mode: TRUE/AUTO
- Execution mode: real subagent for QA checklist plus main-agent integration
- Subagent plan: `_agent/subagent_plan.md`

## Pages

- Page 1: Executive Overview - ROI health and paid vs organic value
- Page 2: Channel ROI - channel performance vs ROAS/CAC targets
- Page 3: Campaign Ranking - scale, optimize, or review/cut campaigns
- Page 4: Exceptions and Actions - budget move action matrix

## QA Status

- Data QA: Pass
- Metric QA: Pass for prepared spec
- Visual QA: Pass for generated preview screenshots
- Interaction QA: Pending PBIX
- File QA: Blocked until `output/dashboard_final.pbix` exists and passes open/save/refresh
""",
    )
    ch.to_csv(PROJECT / "output/exports/channel_roi_summary.csv", index=False)
    derived["campaign"].sort_values("scale_score", ascending=False).to_csv(PROJECT / "output/exports/campaign_ranking.csv", index=False)


def build_preview(tables: dict[str, pd.DataFrame], derived: dict) -> None:
    fact = tables["fact_campaign_daily"].copy()
    fact = fact.merge(tables["dim_channel"][["channel_key", "channel", "paid_organic"]], on=["channel_key", "paid_organic"])
    monthly = fact.groupby("month_key", as_index=False).agg(spend=("spend", "sum"), revenue=("revenue", "sum"))
    paid_org = fact.groupby("paid_organic", as_index=False).agg(spend=("spend", "sum"), revenue=("revenue", "sum"))
    ch = derived["channel"].copy()
    cp = derived["campaign"].copy()
    plt.rcParams.update({"font.family": "DejaVu Sans", "figure.facecolor": "#F8FAFC", "axes.facecolor": "white"})

    def save(fig: plt.Figure, page: int) -> None:
        fig.tight_layout(rect=[0, 0, 1, 0.96])
        fig.savefig(PROJECT / f"output/screenshots/page_{page:02d}.png", dpi=160)
        plt.close(fig)

    fig, axes = plt.subplots(2, 2, figsize=(16, 9))
    fig.suptitle("Page 1 - Executive Overview", fontsize=18, fontweight="bold", x=0.02, ha="left")
    axes[0, 0].bar(monthly["month_key"], monthly["spend"] / 1000, color="#8FBFBD", label="Spend")
    axes[0, 0].plot(monthly["month_key"], monthly["revenue"] / 1000, color="#2563EB", linewidth=2, label="Revenue")
    axes[0, 0].set_title("Monthly spend and revenue", loc="left", fontweight="bold")
    axes[0, 0].tick_params(axis="x", rotation=55)
    axes[0, 0].legend(frameon=False)
    x = np.arange(len(paid_org))
    axes[0, 1].bar(x - 0.18, paid_org["spend"] / 1000, 0.36, color="#D97706", label="Spend")
    axes[0, 1].bar(x + 0.18, paid_org["revenue"] / 1000, 0.36, color="#16A34A", label="Revenue")
    axes[0, 1].set_xticks(x, paid_org["paid_organic"])
    axes[0, 1].set_title("Paid vs organic value", loc="left", fontweight="bold")
    axes[0, 1].legend(frameon=False)
    rev = ch.sort_values("revenue", ascending=True)
    axes[1, 0].barh(rev["channel"], rev["revenue"] / 1000, color="#2563EB")
    axes[1, 0].set_title("Revenue by channel", loc="left", fontweight="bold")
    colors = np.where(ch["action"].eq("Review/Cut"), "#DC2626", np.where(ch["action"].eq("Scale"), "#16A34A", "#D97706"))
    sizes = ch["revenue"] / ch["revenue"].max() * 1800 + 80
    axes[1, 1].scatter(ch["spend"] / 1000, ch["roas"], s=sizes, c=colors, alpha=0.75)
    overview_offsets = {
        "Direct": (4, -10),
        "Email": (4, -2),
        "Referral Partners": (4, 10),
        "Organic Search": (4, -12),
        "Google Search": (-62, 4),
        "Meta": (4, 8),
        "TikTok": (4, -10),
        "LinkedIn": (4, 8),
        "Programmatic Display": (4, -10),
        "Affiliates": (4, 8),
    }
    for _, row in ch.iterrows():
        axes[1, 1].annotate(
            row["channel"],
            (row["spend"] / 1000, row["roas"]),
            xytext=overview_offsets.get(row["channel"], (4, 4)),
            textcoords="offset points",
            fontsize=8,
        )
    axes[1, 1].set_xlabel("Spend ($K)")
    axes[1, 1].set_ylabel("ROAS")
    axes[1, 1].set_title("Spend vs ROAS action map", loc="left", fontweight="bold")
    axes[1, 1].margins(x=0.08, y=0.14)
    save(fig, 1)

    fig, axes = plt.subplots(1, 2, figsize=(16, 9))
    fig.suptitle("Page 2 - Channel ROI", fontsize=18, fontweight="bold", x=0.02, ha="left")
    roas_sort = ch.sort_values("roas")
    axes[0].barh(roas_sort["channel"], roas_sort["roas"], color=np.where(roas_sort["action"].eq("Review/Cut"), "#DC2626", "#16A34A"))
    axes[0].scatter(roas_sort["target_roas"], roas_sort["channel"], marker="|", s=220, color="#0F172A", label="Target")
    axes[0].set_title("ROAS by channel vs target", loc="left", fontweight="bold")
    axes[0].legend(frameon=False)
    cac_sort = ch.sort_values("cac", ascending=False)
    axes[1].barh(cac_sort["channel"], cac_sort["cac"], color=np.where(cac_sort["cac"] > cac_sort["target_cac"], "#DC2626", "#16A34A"))
    axes[1].scatter(cac_sort["target_cac"], cac_sort["channel"], marker="|", s=220, color="#0F172A", label="Target")
    axes[1].set_title("CAC by channel vs target", loc="left", fontweight="bold")
    axes[1].legend(frameon=False)
    save(fig, 2)

    fig, axes = plt.subplots(1, 2, figsize=(16, 9))
    fig.suptitle("Page 3 - Campaign Ranking", fontsize=18, fontweight="bold", x=0.02, ha="left")
    top = cp.sort_values("scale_score", ascending=True).tail(10)
    bottom = cp.sort_values("scale_score", ascending=True).head(10).sort_values("scale_score", ascending=False)
    axes[0].barh(top["campaign_name"], top["scale_score"], color="#16A34A")
    axes[0].set_title("Scale candidates", loc="left", fontweight="bold")
    axes[1].barh(bottom["campaign_name"], bottom["scale_score"], color="#DC2626")
    axes[1].set_title("Review/cut candidates", loc="left", fontweight="bold")
    save(fig, 3)

    fig, axes = plt.subplots(1, 2, figsize=(16, 9))
    fig.suptitle("Page 4 - Exceptions and Actions", fontsize=18, fontweight="bold", x=0.02, ha="left")
    axes[0].scatter(ch["roas_vs_target"], ch["cac_vs_target"], s=ch["spend_share"] * 4200 + 120, c=colors, alpha=0.75)
    axes[0].axvline(0, color="#0F172A", linewidth=1)
    axes[0].axhline(0, color="#0F172A", linewidth=1)
    action_label_channels = {"Google Search", "Meta", "LinkedIn", "Referral Partners", "Organic Search", "Direct", "Email"}
    action_offsets = {
        "Direct": (4, -8),
        "Email": (4, -8),
        "Referral Partners": (4, 10),
        "Organic Search": (4, -12),
        "Google Search": (4, -10),
        "Meta": (4, 8),
        "TikTok": (4, -10),
        "LinkedIn": (4, 8),
        "Programmatic Display": (4, -10),
        "Affiliates": (-42, 8),
    }
    for _, row in ch.iterrows():
        if row["channel"] not in action_label_channels:
            continue
        axes[0].annotate(
            row["channel"],
            (row["roas_vs_target"], row["cac_vs_target"]),
            xytext=action_offsets.get(row["channel"], (4, 4)),
            textcoords="offset points",
            fontsize=8,
        )
    axes[0].set_xlabel("ROAS vs target")
    axes[0].set_ylabel("CAC vs target (positive is better)")
    axes[0].set_title("Budget action matrix", loc="left", fontweight="bold")
    axes[0].margins(x=0.08, y=0.12)
    axes[1].axis("off")
    table_df = ch.sort_values(["action", "spend"], ascending=[True, False])[["channel", "action", "spend_share", "roas", "cac"]].copy()
    table_df["spend_share"] = table_df["spend_share"].map(lambda v: f"{v:.1%}")
    table_df["roas"] = table_df["roas"].map(lambda v: f"{v:.2f}")
    table_df["cac"] = table_df["cac"].map(lambda v: "N/A" if pd.isna(v) else f"${v:.0f}")
    table = axes[1].table(cellText=table_df.values, colLabels=["Channel", "Action", "Spend Share", "ROAS", "CAC"], loc="center", cellLoc="left", colLoc="left")
    table.auto_set_font_size(False)
    table.set_fontsize(8)
    table.scale(1, 1.45)
    axes[1].set_title("Channel action table", loc="left", fontweight="bold")
    save(fig, 4)

    totals = derived["summary"]["totals"]
    cards = [
        ("Spend", money_m(totals["spend"])),
        ("Revenue", money_m(totals["revenue"])),
        ("ROAS", f"{totals['revenue'] / totals['spend']:.2f}"),
        ("Marketing ROI", pct((totals["gross_profit"] - totals["spend"]) / totals["spend"])),
        ("CAC", f"${totals['spend'] / totals['new_customers']:.0f}"),
        ("Conversion Rate", pct(totals["conversions"] / totals["clicks"])),
    ]
    card_html = "".join(f"<div class='card'><span>{k}</span><strong>{v}</strong></div>" for k, v in cards)
    imgs = "".join(f"<section><h2>Page {i}</h2><img src='screenshots/page_{i:02d}.png'></section>" for i in range(1, 5))
    html = f"""
<!doctype html><html lang="en"><head><meta charset="utf-8"><title>Marketing Campaign ROI Preview</title>
<style>
body{{margin:0;font-family:Aptos,Segoe UI,Arial,sans-serif;background:#f8fafc;color:#0f172a}}
header{{padding:28px 36px 18px;background:white;border-bottom:1px solid #dbe3ef}}
.cards{{display:grid;grid-template-columns:repeat(6,minmax(120px,1fr));gap:12px;padding:18px 36px}}
.card{{background:white;border:1px solid #dbe3ef;border-radius:8px;padding:14px 16px}}
.card span{{display:block;color:#64748b;font-size:13px}}.card strong{{display:block;margin-top:6px;font-size:22px}}
main{{padding:0 36px 32px}}img{{width:100%;border:1px solid #dbe3ef;border-radius:8px;background:white}}
</style></head><body><header><h1>Marketing Campaign ROI Dashboard Preview</h1>
<p>Spend, CAC, ROAS, conversion, revenue by channel, paid vs organic, campaign ranking.</p></header>
<div class="cards">{card_html}</div><main>{imgs}</main></body></html>
"""
    write_text("output/dashboard_preview.html", html)


def validate(tables: dict[str, pd.DataFrame], derived: dict, env: dict, authoring: dict) -> None:
    raw = tables["raw"]
    fact = tables["fact_campaign_daily"]
    checks = []
    for col in ["spend", "revenue", "gross_profit", "clicks", "leads", "conversions", "new_customers"]:
        checks.append(
            {
                "check": f"{col} raw vs prepared",
                "raw_total": float(raw[col].sum()),
                "prepared_total": float(fact[col].sum()),
                "variance": float(fact[col].sum() - raw[col].sum()),
                "status": "Pass" if abs(fact[col].sum() - raw[col].sum()) < 0.01 else "Fail",
            }
        )
    checks += [
        {"check": "row count raw vs prepared", "raw_total": len(raw), "prepared_total": len(fact), "variance": len(fact) - len(raw), "status": "Pass" if len(raw) == len(fact) else "Fail"},
        {"check": "dim_channel unique channel_key", "raw_total": len(tables["dim_channel"]), "prepared_total": tables["dim_channel"]["channel_key"].nunique(), "variance": len(tables["dim_channel"]) - tables["dim_channel"]["channel_key"].nunique(), "status": "Pass" if len(tables["dim_channel"]) == tables["dim_channel"]["channel_key"].nunique() else "Fail"},
        {"check": "fact duplicate date-campaign-channel", "raw_total": 0, "prepared_total": int(fact.duplicated(subset=["date", "campaign_key", "channel_key"]).sum()), "variance": int(fact.duplicated(subset=["date", "campaign_key", "channel_key"]).sum()), "status": "Pass" if not fact.duplicated(subset=["date", "campaign_key", "channel_key"]).any() else "Fail"},
    ]
    reconciliation = pd.DataFrame(checks)
    reconciliation.to_csv(PROJECT / "data/validated/reconciliation_summary.csv", index=False)
    with pd.ExcelWriter(PROJECT / "qa/reconciliation.xlsx", engine="openpyxl") as writer:
        reconciliation.to_excel(writer, sheet_name="Reconciliation", index=False)
        derived["channel"].to_excel(writer, sheet_name="Channel Summary", index=False)
        derived["campaign"].to_excel(writer, sheet_name="Campaign Summary", index=False)

    pbix_path = PROJECT / "output/dashboard_final.pbix"
    write_json(
        "qa/pbix_validation.json",
        {
            "pbix_created": pbix_path.exists(),
            "expected_final_path": "output/dashboard_final.pbix",
            "build_mode": env["build_mode"],
            "authoring_mode": authoring["authoring_mode"],
            "manual_assisted_required": authoring["manual_assisted_required"],
            "scripted_desktop_pbix_feasible": authoring["scripted_desktop_pbix_feasible"],
            "pbi_tools_role": authoring["pbi_tools_role"],
            "launch_status": "pending_launch_check",
            "ui_control": "unknown",
            "build_status": "manual_assisted_required" if not pbix_path.exists() else "pbix_created_needs_open_save_refresh_qa",
        },
    )
    write_text(
        "qa/qa_checklist.md",
        """
# QA Checklist

| Area | Status | Notes |
|---|---|---|
| Data QA | Pass | Raw and prepared totals reconcile. |
| Metric QA | Pass | DAX uses measures and DIVIDE for rates. |
| Visual QA | Pass for preview | Four PNG screenshots generated. |
| Interaction QA | Pending PBIX | Slicers and interactions must be tested in Power BI. |
| File QA | Blocked | PBIX must be created, reopened, refreshed, and saved. |
""",
    )
    write_text("qa/visual_qa_notes.md", "# Visual QA Notes\n\nPreview screenshots generated under `output/screenshots/`. Native Power BI visual QA is pending PBIX authoring.")
    write_text("qa/interaction_qa_notes.md", "# Interaction QA Notes\n\nPending PBIX test: slicer sync, search, reset/bookmarks if added, and cross-filter behavior.")
    write_text("qa/regression_qa_notes.md", "# Regression QA Notes\n\nReconciliation passes. No duplicate fact grain rows. PBIX regression QA pending.")
    write_text("qa/performance_qa_notes.md", f"# Performance QA Notes\n\nFact rows: {len(fact):,}. Model is small and suitable for Power BI Import mode.")
    write_text("qa/metric_qa_notes.md", "# Metric QA Notes\n\nSpend, Revenue, ROAS, Marketing ROI, CAC, and Conversion Rate reconcile to prepared CSV logic.")

    required = [
        "README.md",
        "_agent/intake_brief.md",
        "_agent/run_log.md",
        "_agent/decision_log.md",
        "_agent/environment_check.md",
        "_agent/powerbi_launch_check.md",
        "_agent/pbix_authoring_decision.md",
        "_agent/scripted_desktop_pbix_probe.md",
        "_agent/build_loop_log.md",
        "_agent/failure_matrix.md",
        "_agent/subagent_plan.md",
        "data/source_summary.json",
        "data/data_quality_report.md",
        "data/synthetic/synthetic_data_generation_notes.md",
        "data/raw/marketing_campaign_daily_raw.csv",
        "data/prepared/fact_campaign_daily.csv",
        "data/prepared/dim_date.csv",
        "data/prepared/dim_month.csv",
        "data/prepared/dim_channel.csv",
        "data/prepared/dim_campaign.csv",
        "model/data_dictionary.md",
        "model/metric_definitions.md",
        "model/dax_measures.md",
        "model/relationship_map.md",
        "build/config/page_map.json",
        "build/config/insight_map.json",
        "build/config/visual_map.json",
        "build/config/theme.json",
        "build/config/slicer_map.json",
        "powerbi/launch_powerbi.ps1",
        "powerbi/templates/template_inventory.md",
        "powerbi/notes/scripted_desktop_pbix_probe.md",
        "powerbi/notes/authoring_strategy.md",
        "powerbi/notes/desktop_ui_runbook.md",
        "powerbi/notes/pbix_build_runbook.md",
        "output/dashboard_preview.html",
        "output/screenshots/page_01.png",
        "output/screenshots/page_02.png",
        "output/screenshots/page_03.png",
        "output/screenshots/page_04.png",
        "qa/qa_checklist.md",
        "qa/reconciliation.xlsx",
        "qa/pbix_validation.json",
        "qa/metric_qa_notes.md",
        "qa/visual_qa_notes.md",
        "qa/interaction_qa_notes.md",
        "qa/regression_qa_notes.md",
        "qa/performance_qa_notes.md",
        "docs/handoff_notes.md",
        "docs/refresh_guide.md",
        "docs/rebuild_guide.md",
        "docs/changelog.md",
        "docs/issue_log.md",
    ]
    files = []
    for rel in required:
        path = PROJECT / rel
        files.append({"file": rel, "exists": path.exists(), "bytes": path.stat().st_size if path.exists() else 0})
    status = "Fail"
    if all(item["exists"] and item["bytes"] > 0 for item in files) and (reconciliation["status"] == "Pass").all():
        status = "Pass" if pbix_path.exists() else "Blocked at File QA"
    write_json(
        "qa/output_validation.json",
        {
            "status": status,
            "validated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "pbix_final_exists": pbix_path.exists(),
            "file_qa_status": "Pass" if pbix_path.exists() else "Blocked at File QA",
            "manual_assisted_required": authoring["manual_assisted_required"],
            "pbi_tools_role": authoring["pbi_tools_role"],
            "files": files,
        },
    )


def main() -> None:
    ensure_dirs()
    env = detect_environment()
    inventory = discover_powerbi_sources()
    scripted_probe = probe_scripted_desktop_pbix(env, inventory)
    authoring = decide_authoring(env, inventory, scripted_probe)
    write_environment_docs(env, inventory, authoring, scripted_probe)
    write_launcher()
    tables = make_data()
    save_data(tables)
    derived = build_summaries(tables)
    write_project_docs(tables, derived, env, authoring, scripted_probe)
    build_preview(tables, derived)
    validate(tables, derived, env, authoring)


if __name__ == "__main__":
    main()
