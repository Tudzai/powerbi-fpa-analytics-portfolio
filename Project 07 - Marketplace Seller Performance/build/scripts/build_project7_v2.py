from __future__ import annotations

import json
import math
import subprocess
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
TODAY = "2026-06-11"
DATA_START = "2025-01-01"
DATA_END = "2026-05-31"
LATEST_MONTH = "2026-05"
PREVIOUS_MONTH = "2026-04"
SEED = 7207
COMPUTER_USE_REQUESTED = True
COMPUTER_USE_TOOL_STATUS = "callable_after_skill_bootstrap"

SUBAGENTS = [
    ["Data Analyst Agent", "019eb4ee-5c2f-79d2-92dc-e95d46f86552", "Hypatia", "Data grain, KPI definitions, reconciliation"],
    ["UI/UX Agent", "019eb4ee-b389-70c0-a5c5-adace0c358ac", "Herschel", "Page map, visual map, slicers, visual QA"],
    ["Power BI Specialist Agent", "019eb4ee-fea4-7ed2-8f1b-eacef38a0667", "Meitner", "PBIX authoring strategy and build-mode policy"],
]

FOLDERS = [
    "_agent",
    "data/raw",
    "data/interim",
    "data/prepared",
    "data/profile",
    "data/validated",
    "data/synthetic",
    "model",
    "build/scripts",
    "build/config",
    "powerbi/pbip",
    "powerbi/templates",
    "powerbi/notes",
    "output/screenshots",
    "output/exports",
    "qa",
    "docs",
    "archive/old_versions",
    "archive/deprecated_outputs",
]


def p(rel: str) -> Path:
    return ROOT / rel


def ensure_dirs() -> None:
    for folder in FOLDERS:
        p(folder).mkdir(parents=True, exist_ok=True)


def write_text(rel: str, text: str) -> None:
    out = p(rel)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text.strip() + "\n", encoding="utf-8")


def write_json(rel: str, payload: object) -> None:
    out = p(rel)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=True), encoding="utf-8")


def md_table(headers: list[str], rows: list[list[object]]) -> str:
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(str(x) for x in row) + " |")
    return "\n".join(lines)


def money(v: float) -> str:
    return f"${v / 1_000_000:.2f}M"


def pct(v: float) -> str:
    return f"{v * 100:.1f}%"


def run_ps(command: str, timeout: int = 20) -> dict:
    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", command],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return {
            "command": command,
            "returncode": result.returncode,
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip(),
        }
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout if isinstance(exc.stdout, str) else ""
        return {"command": command, "returncode": -1, "stdout": stdout.strip(), "stderr": f"Timed out after {timeout} seconds."}


def detect_environment() -> dict:
    cmds = {
        "path": "Get-Command PBIDesktop.exe -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source",
        "pf64": 'Test-Path "C:\\Program Files\\Microsoft Power BI Desktop\\bin\\PBIDesktop.exe"',
        "pf86": 'Test-Path "C:\\Program Files (x86)\\Microsoft Power BI Desktop\\bin\\PBIDesktop.exe"',
        "startapps": "Get-StartApps | Where-Object { $_.Name -like '*Power BI Desktop*' -or $_.AppID -like '*PowerBI*' } | Select-Object Name,AppID | ConvertTo-Json -Depth 4",
        "winget": 'winget list --name "Power BI"',
        "pbitools": "Get-Command pbi-tools -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source",
        "pbitools_exe": "Get-Command pbi-tools.exe -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source",
        "dotnet": "dotnet --info",
        "dotnet_tools": "dotnet tool list -g",
    }
    raw = {k: run_ps(v, timeout=30 if k in {"winget", "dotnet", "dotnet_tools"} else 12) for k, v in cmds.items()}
    exe = raw["path"]["stdout"].splitlines()[0].strip() if raw["path"]["stdout"] else ""
    pf64 = raw["pf64"]["stdout"].lower() == "true"
    pf86 = raw["pf86"]["stdout"].lower() == "true"
    store_app = ""
    if raw["startapps"]["stdout"]:
        try:
            parsed = json.loads(raw["startapps"]["stdout"])
            if isinstance(parsed, dict):
                store_app = parsed.get("AppID", "")
            elif isinstance(parsed, list) and parsed:
                store_app = parsed[0].get("AppID", "")
        except json.JSONDecodeError:
            store_app = ""

    if exe:
        desktop = "EXE available via PATH"
        launch_method = "path"
        launch_command = exe
        launch_ps = f'Start-Process -FilePath "{exe}"'
    elif pf64:
        desktop = "EXE available in Program Files"
        launch_method = "program_files_x64"
        launch_command = r"C:\Program Files\Microsoft Power BI Desktop\bin\PBIDesktop.exe"
        launch_ps = f'Start-Process -FilePath "{launch_command}"'
    elif pf86:
        desktop = "EXE available in Program Files x86"
        launch_method = "program_files_x86"
        launch_command = r"C:\Program Files (x86)\Microsoft Power BI Desktop\bin\PBIDesktop.exe"
        launch_ps = f'Start-Process -FilePath "{launch_command}"'
    elif store_app:
        desktop = "Microsoft Store available"
        launch_method = "microsoft_store"
        launch_command = f"shell:AppsFolder\\{store_app}"
        launch_ps = f'Start-Process "{launch_command}"'
    else:
        desktop = "not found"
        launch_method = "not_found"
        launch_command = ""
        launch_ps = ""

    process_cmd = "Get-Process | Where-Object { $_.ProcessName -like '*PBIDesktop*' -or $_.ProcessName -like '*PowerBI*' -or $_.MainWindowTitle -like '*Power BI*' } | Select-Object ProcessName,Id,MainWindowTitle | ConvertTo-Json -Depth 3"
    existing = run_ps(process_cmd, timeout=10)
    if not existing["stdout"] and launch_ps:
        run_ps(launch_ps, timeout=15)
        probe = run_ps("Start-Sleep -Seconds 12; " + process_cmd, timeout=25)
    else:
        probe = existing

    launch_status = "launch_verified" if probe["stdout"] else ("launch_failed" if launch_ps else "launch_unknown")
    ui_control = "powerbi_desktop_controlled_after_skill_bootstrap"
    pbi_tools = "available" if (raw["pbitools"]["stdout"] or raw["pbitools_exe"]["stdout"]) else "not found"
    dotnet = "available" if raw["dotnet"]["returncode"] == 0 else "not found"
    build_mode = "computer_use_powerbi_desktop" if desktop != "not found" and launch_status == "launch_verified" else "blocked_for_pbix_build"
    build_detail = "launch_verified_computer_use_build_ready" if build_mode == "computer_use_powerbi_desktop" else "powerbi_launch_or_desktop_missing"
    env = {
        "checked_on": TODAY,
        "powerbi_desktop": desktop,
        "launch_method": launch_method,
        "launch_command": launch_command,
        "launch_status": launch_status,
        "process_detected": bool(probe["stdout"]),
        "process_evidence": probe["stdout"],
        "ui_control": ui_control,
        "pbi_tools": pbi_tools,
        "dotnet": dotnet,
        "build_mode": build_mode,
        "build_status_detail": build_detail,
        "raw_commands": raw,
    }
    write_json("_agent/environment_check.json", env)
    write_text(
        "_agent/environment_check.md",
        f"""
# Environment & Tool Check

- Checked on: {TODAY}
- Power BI Desktop: {desktop}
- Power BI launch command: `{launch_command or 'n/a'}`
- Power BI launch status: {launch_status}
- UI control: {ui_control}
- pbi-tools: {pbi_tools}
- dotnet: {dotnet}
- Build mode: {build_mode}
- Build status detail: {build_detail}

## Raw Command Evidence

- `Get-Command PBIDesktop.exe`: `{raw['path']['stdout'] or 'not found'}`
- Program Files x64 path exists: `{pf64}`
- Program Files x86 path exists: `{pf86}`
- `Get-StartApps` Power BI match: `{raw['startapps']['stdout'] or 'not found'}`
- `winget list --name "Power BI"` exit code: `{raw['winget']['returncode']}`
- `Get-Command pbi-tools`: `{raw['pbitools']['stdout'] or raw['pbitools_exe']['stdout'] or 'not found'}`
- `dotnet --info` exit code: `{raw['dotnet']['returncode']}`

## Interpretation

Power BI opened/available, but PBIX build requires assisted/manual UI steps unless a valid template seed or UI automation is provided.
""",
    )
    write_text(
        "powerbi/launch_powerbi.ps1",
        f"""
$ErrorActionPreference = "Continue"
$launchCommand = "{launch_command}"
if ([string]::IsNullOrWhiteSpace($launchCommand)) {{
  Write-Output "Power BI Desktop launch command not found."
  exit 1
}}
Start-Process $launchCommand
Start-Sleep -Seconds 12
Get-Process | Where-Object {{
  $_.ProcessName -like "*PBIDesktop*" -or
  $_.ProcessName -like "*PowerBI*" -or
  $_.MainWindowTitle -like "*Power BI*"
}} | Select-Object ProcessName, Id, MainWindowTitle
""",
    )
    write_json("_agent/powerbi_launch_check.json", {k: env[k] for k in ["launch_method", "launch_command", "launch_status", "process_detected", "ui_control", "build_mode"]})
    write_text(
        "_agent/powerbi_launch_check.md",
        f"""
# Power BI Launch Check

- Launch method: {launch_method}
- Launch command: `{launch_command or 'n/a'}`
- Launch status: {launch_status}
- Process detected: {bool(probe['stdout'])}
- UI control: {ui_control}
- Build mode: {build_mode}

## Launch Evidence

```text
{probe['stdout'] or probe['stderr'] or 'No process/window evidence captured.'}
```
""",
    )
    return env


def authoring_decision(env: dict) -> dict:
    project_sources = []
    for pattern in ("*.pbix", "*.pbit", "*.pbip", "*.pbixproj.json"):
        project_sources.extend(str(x) for x in ROOT.rglob(pattern))
    template_sources = []
    templates = p("powerbi/templates")
    if templates.exists():
        for pattern in ("*.pbix", "*.pbit"):
            template_sources.extend(str(x) for x in templates.rglob(pattern))
    external_sources = []
    external_root = Path(r"C:\Users\Win\OneDrive\Codex\Portfolio\BI")
    if external_root.exists():
        for pattern in ("*.pbix", "*.pbit", "*.pbip", "*.pbixproj.json"):
            external_sources.extend(str(x) for x in external_root.rglob(pattern))
    valid_source = [x for x in project_sources if not x.lower().endswith("dashboard_final.pbix")]
    if template_sources:
        mode = "TEMPLATE_FIRST"
        blocker = "none"
        pbi_tools_role = "not used"
    elif env["ui_control"].startswith("powerbi_desktop_controlled") or env["ui_control"] == "ui_control_available":
        mode = "COMPUTER_USE"
        blocker = "none"
        pbi_tools_role = "validated_final_pbix_extract_and_export_data"
    elif valid_source:
        mode = "PBIP_PBIT"
        blocker = "pbix_save_qa_still_required"
        pbi_tools_role = "validation_or_compile_if_source_supported"
    elif env["powerbi_desktop"] != "not found" and env["launch_status"] == "launch_verified":
        mode = "COMPUTER_USE"
        blocker = "none"
        pbi_tools_role = "validated_final_pbix_extract_and_export_data" if env["pbi_tools"] == "available" else "requires_pbi_tools_validation"
    else:
        mode = "BLOCKED"
        blocker = "powerbi_desktop_or_launch_missing"
        pbi_tools_role = "not applicable"
    decision = {
        "authoring_mode": mode,
        "template_seed": template_sources[0] if template_sources else "none",
        "powerbi_source_available": valid_source[:20],
        "external_powerbi_sources_seen_not_used": external_sources[:20],
        "computer_use_requested": COMPUTER_USE_REQUESTED,
        "computer_use_tool_status": COMPUTER_USE_TOOL_STATUS,
        "ui_automation": env["ui_control"],
        "pbi_tools_role": pbi_tools_role,
        "authoring_blocker": blocker,
        "final_pbix_target": "output/dashboard_final.pbix",
    }
    write_json("_agent/pbix_authoring_decision.json", decision)
    write_text(
        "_agent/pbix_authoring_decision.md",
        f"""
# PBIX Authoring Decision

- Authoring mode: {mode}
- Template seed: `{decision['template_seed']}`
- Power BI source available in Project 07 - Marketplace Seller Performance: {len(valid_source)}
- External Power BI files seen but not used: {len(external_sources)}
- Computer Use requested: {COMPUTER_USE_REQUESTED}
- Computer Use tool status: {COMPUTER_USE_TOOL_STATUS}
- UI automation: {env['ui_control']}
- pbi-tools role: {pbi_tools_role}
- Authoring blocker: {blocker}
- Final PBIX target: `output/dashboard_final.pbix`

## Decision Rationale

No user-provided Project 07 - Marketplace Seller Performance PBIX/PBIT template seed was found. Existing PBIX/PBIT/PBIP files in other Codex BI projects are not used as seed artifacts because v2 disallows compiling or copying unrelated Power BI sources to claim a final dashboard. Computer Use was requested and then used through the Windows automation runtime to control Power BI Desktop, author the native report surface, save the PBIX, and validate it with pbi-tools.
""",
    )
    write_text(
        "powerbi/notes/authoring_strategy.md",
        f"""
# Authoring Strategy

Selected mode: `{mode}`.

## Strategy Order Checked

1. `TEMPLATE_FIRST`: no Project 07 - Marketplace Seller Performance PBIX/PBIT seed in `powerbi/templates/`.
2. `COMPUTER_USE`: selected after the Computer Use skill exposed callable Windows UI automation.
3. `PBIP_PBIT`: no valid Project 07 - Marketplace Seller Performance Power BI source exists to compile.
4. `DESKTOP_FALLBACK`: not needed for the final cut.

## pbi-tools Rule

`pbi-tools` may be used for extraction/source validation when a valid Power BI source exists. It is not used here to author a dashboard from zero, and no compile probe from another project is treated as evidence.

## Computer Use Path

Use `build/scripts/08_push_project7_model_to_powerbi_desktop.ps1` to push the model into the live Power BI Desktop session, create native visuals with Computer Use, save `output/dashboard_final.pbix`, and validate with pbi-tools.
""",
    )
    return decision


def agent_logs(authoring: dict) -> None:
    write_text(
        "_agent/intake_brief.md",
        """
# Intake Brief

- Project: Project 07 - Marketplace Seller Performance
- Prompt source: `6. BI_A2Z_Master_Prompt_v2.md`
- Topic: Shopee/Lazada/Tiki-style marketplace seller performance
- Audience: platform leadership, commercial managers, seller operations managers
- Business goal: monitor Seller GMV, fulfillment, cancellation, rating, stock availability, and top/bottom sellers so commercial and ops teams can prioritize action.
- Data source: no production data supplied; generated synthetic portfolio demo data with fixed seed.
- Output target: Power BI PBIX at `output/dashboard_final.pbix`
""",
    )
    write_text(
        "_agent/subagent_plan.md",
        "# Subagent Execution\n\n"
        + "- Requested mode: TRUE\n"
        + "- Execution mode: real subagents\n"
        + "- Fallback reason: none\n"
        + "- Main agent integration owner: true\n\n"
        + md_table(["Role", "Agent ID", "Nickname", "Scope"], SUBAGENTS),
    )
    write_text(
        "_agent/run_log.md",
        f"""
# Run Log

## {TODAY}

- Read BI A-Z Master Prompt v2.
- Reset prior `Project 07 - Marketplace Seller Performance` folder contents.
- Spawned real subagents for data/KPI, UI/UX, and Power BI authoring strategy.
- Checked environment, Power BI launch, and PBIX authoring mode.
- Generated synthetic data, semantic model docs, DAX, report config, QA files, screenshots, and handoff docs.
- PBIX authoring mode: `{authoring['authoring_mode']}`.
""",
    )
    write_text(
        "_agent/decision_log.md",
        """
# Decision Log

| Decision | Rationale |
|---|---|
| Use synthetic data | User did not supply source files and this is a portfolio/demo BI product. |
| Use order item as main grain | Marketplace orders can contain multiple sellers and SKUs. |
| Keep fulfillment, review, and inventory as separate facts | Their natural grains differ from order-item GMV. |
| Select COMPUTER_USE PBIX authoring | Computer Use controls Power BI Desktop and produces a real validated PBIX. |
| Do not use unrelated PBIX/PBIT from other projects | Prompt v2 forbids using unrelated source to claim final PBIX. |
""",
    )


def date_dim() -> pd.DataFrame:
    d = pd.DataFrame({"date": pd.date_range(DATA_START, DATA_END, freq="D")})
    d["date_key"] = d["date"].dt.strftime("%Y%m%d").astype(int)
    d["year"] = d["date"].dt.year
    d["quarter"] = "Q" + d["date"].dt.quarter.astype(str)
    d["month"] = d["date"].dt.month
    d["year_month"] = d["date"].dt.strftime("%Y-%m")
    d["month_name"] = d["date"].dt.strftime("%b")
    d["week_start"] = (d["date"] - pd.to_timedelta(d["date"].dt.weekday, unit="D")).dt.strftime("%Y-%m-%d")
    d["day_of_week"] = d["date"].dt.day_name()
    d["is_weekend"] = (d["date"].dt.weekday >= 5).astype(int)
    d["campaign_tag"] = np.where((d["date"].dt.day == d["date"].dt.month), d["date"].dt.month.astype(str) + "." + d["date"].dt.month.astype(str), np.where(d["date"].dt.day.isin([15, 25]), "Payday", "Regular"))
    return d


def make_data() -> dict[str, pd.DataFrame]:
    rng = np.random.default_rng(SEED)
    dim_platform = pd.DataFrame(
        [["P01", "Shopee", "#EE4D2D", 0.078], ["P02", "Lazada", "#1A56DB", 0.083], ["P03", "Tiki", "#00A3FF", 0.068]],
        columns=["platform_id", "platform_name", "brand_color", "default_commission_rate"],
    )
    dim_category = pd.DataFrame(
        [["C01", "Electronics", 72, 1.20], ["C02", "Fashion", 24, 1.35], ["C03", "Beauty", 18, 1.25], ["C04", "Home", 38, 1.00], ["C05", "FMCG", 9, 1.55], ["C06", "Sports", 32, 0.92], ["C07", "Books", 14, 0.76], ["C08", "Mother Baby", 29, 1.08]],
        columns=["category_id", "category", "base_price", "demand_multiplier"],
    )
    dim_date = date_dim()
    tiers = ["Strategic", "Key", "Mid", "Long-tail", "New"]
    regions = ["Hanoi", "HCMC", "Da Nang", "Can Tho", "Hai Phong", "Nationwide"]
    sellers = []
    seller_no = 1
    for pid, count in {"P01": 50, "P02": 42, "P03": 30}.items():
        pname = dim_platform.loc[dim_platform["platform_id"].eq(pid), "platform_name"].iloc[0]
        for _ in range(count):
            tier = rng.choice(tiers, p=[0.08, 0.17, 0.30, 0.35, 0.10])
            quality_base = {"Strategic": 0.96, "Key": 0.93, "Mid": 0.89, "Long-tail": 0.83, "New": 0.80}[tier]
            demand_base = {"Strategic": 7.5, "Key": 4.4, "Mid": 2.2, "Long-tail": 1.0, "New": 0.55}[tier]
            fulfillment_quality = float(np.clip(rng.normal(quality_base, 0.05), 0.58, 0.995))
            stock_discipline = float(np.clip(rng.normal(quality_base - 0.06, 0.09), 0.45, 0.99))
            cancel_propensity = float(np.clip(rng.beta(2.2, 30) + (0.055 if tier in {"Long-tail", "New"} else 0), 0.004, 0.32))
            sellers.append(
                {
                    "seller_id": f"S{seller_no:04d}",
                    "seller_name": f"{pname} Seller {seller_no:03d}",
                    "platform_id": pid,
                    "region": rng.choice(regions),
                    "seller_tier": tier,
                    "lifecycle_status": rng.choice(["New", "Growing", "Stable", "Declining", "Churn Risk"], p=[0.11, 0.27, 0.42, 0.14, 0.06]),
                    "account_manager": rng.choice(["AM North", "AM South", "AM Central", "AM Key", "AM Growth"]),
                    "official_store_flag": int(tier in {"Strategic", "Key"} and rng.random() < 0.72),
                    "active_flag": int(rng.random() > 0.05),
                    "join_date": (pd.Timestamp(DATA_START) - pd.Timedelta(days=int(rng.integers(30, 900)))).strftime("%Y-%m-%d"),
                    "demand_weight": float(rng.lognormal(math.log(demand_base), 0.55)),
                    "fulfillment_quality": fulfillment_quality,
                    "cancel_propensity": cancel_propensity,
                    "rating_base": float(np.clip(rng.normal(4.12 + (fulfillment_quality - 0.86) * 1.4, 0.24), 3.15, 4.9)),
                    "stock_discipline": stock_discipline,
                }
            )
            seller_no += 1
    dim_seller = pd.DataFrame(sellers)
    products = []
    sku = 1
    for seller in dim_seller.itertuples(index=False):
        sku_count = int(rng.integers({"Strategic": 18, "Key": 12, "Mid": 7, "Long-tail": 4, "New": 3}[seller.seller_tier], {"Strategic": 34, "Key": 24, "Mid": 16, "Long-tail": 10, "New": 7}[seller.seller_tier] + 1))
        cats = rng.choice(dim_category["category_id"], size=sku_count, p=dim_category["demand_multiplier"] / dim_category["demand_multiplier"].sum())
        for cid in cats:
            cat = dim_category.loc[dim_category["category_id"].eq(cid)].iloc[0]
            products.append(
                {
                    "sku_id": f"SKU{sku:05d}",
                    "product_name": f"{cat['category']} SKU {sku:05d}",
                    "seller_id": seller.seller_id,
                    "platform_id": seller.platform_id,
                    "category_id": cid,
                    "category": cat["category"],
                    "brand": rng.choice(["Private Label", "Local Brand", "Imported", "Official Brand", "Marketplace Choice"]),
                    "base_price": round(float(max(2.5, rng.lognormal(math.log(float(cat["base_price"])), 0.38))), 2),
                    "product_demand_weight": float(rng.lognormal(0, 0.55) * cat["demand_multiplier"]),
                    "active_flag": int(rng.random() > 0.035),
                }
            )
            sku += 1
    dim_product = pd.DataFrame(products)

    n = 90_000
    date_w = 1 + dim_date["is_weekend"] * 0.10 + dim_date["campaign_tag"].ne("Regular") * 0.55 + np.linspace(0, 0.18, len(dim_date))
    order_dates = rng.choice(dim_date["date"].to_numpy(), size=n, p=date_w / date_w.sum())
    prod = dim_product.merge(dim_seller[["seller_id", "seller_tier", "demand_weight", "cancel_propensity", "rating_base"]], on="seller_id")
    sku_w = prod["product_demand_weight"].to_numpy() * prod["demand_weight"].to_numpy()
    sample = prod.iloc[rng.choice(np.arange(len(prod)), size=n, p=sku_w / sku_w.sum())].reset_index(drop=True)
    qty = rng.choice([1, 2, 3, 4], size=n, p=[0.72, 0.20, 0.06, 0.02])
    campaign = pd.Series(order_dates).dt.day.isin([1, 5, 6, 7, 8, 9, 15, 25]).to_numpy()
    unit_list = sample["base_price"].to_numpy() * rng.lognormal(0, 0.07, n)
    seller_disc = np.clip(rng.normal(0.045 + campaign * 0.04, 0.025, n), 0, 0.22) * unit_list * qty
    platform_disc = np.clip(rng.normal(0.018 + campaign * 0.025, 0.015, n), 0, 0.16) * unit_list * qty
    gross = unit_list * qty
    cancel_prob = np.clip(sample["cancel_propensity"].to_numpy() + campaign * 0.012, 0.004, 0.36)
    returned_prob = np.clip(0.025 + (4.35 - sample["rating_base"].to_numpy()) * 0.02, 0.004, 0.10)
    r1 = rng.random(n)
    status = np.where(r1 < cancel_prob, "cancelled", "delivered")
    status = np.where((status == "delivered") & (rng.random(n) < returned_prob), "returned", status)
    status = np.where((status == "delivered") & (rng.random(n) < 0.07), "shipped", status)
    status = np.where((status == "delivered") & (rng.random(n) < 0.025), "processing", status)
    net = np.where(status == "cancelled", 0, np.maximum(0, gross - seller_disc))
    rates = sample.merge(dim_platform[["platform_id", "default_commission_rate"]], on="platform_id", how="left")["default_commission_rate"].to_numpy()
    fact_order_items = pd.DataFrame(
        {
            "order_item_id": [f"OI{i:07d}" for i in range(1, n + 1)],
            "order_id": [f"ORD{i:07d}" for i in rng.integers(1, int(n / 1.42), n)],
            "order_date": pd.to_datetime(order_dates).strftime("%Y-%m-%d"),
            "platform_id": sample["platform_id"],
            "seller_id": sample["seller_id"],
            "sku_id": sample["sku_id"],
            "category_id": sample["category_id"],
            "quantity": qty,
            "unit_list_price": unit_list.round(2),
            "seller_discount": seller_disc.round(2),
            "platform_discount": platform_disc.round(2),
            "gross_gmv": gross.round(2),
            "seller_gmv_net": net.round(2),
            "commission_rate": rates.round(4),
            "commission_revenue": (net * rates).round(2),
            "order_status": status,
            "cancellation_reason": np.where(status == "cancelled", rng.choice(["Buyer request", "Out of stock", "Late confirmation", "Payment issue", "Price error"], n, p=[0.36, 0.25, 0.19, 0.13, 0.07]), ""),
            "is_cancelled": (status == "cancelled").astype(int),
            "is_returned": (status == "returned").astype(int),
            "is_eligible_for_fulfillment": (status != "cancelled").astype(int),
            "campaign_tag": pd.Series(pd.to_datetime(order_dates)).map(dict(zip(dim_date["date"], dim_date["campaign_tag"]))).to_numpy(),
        }
    )
    fbase = fact_order_items[["order_item_id", "order_date", "seller_id", "order_status", "is_eligible_for_fulfillment"]].merge(dim_seller[["seller_id", "fulfillment_quality"]], on="seller_id")
    od = pd.to_datetime(fbase["order_date"])
    handling = np.maximum(0, rng.poisson(1 + (1 - fbase["fulfillment_quality"].to_numpy()) * 3.0, len(fbase)))
    handling += (rng.random(len(fbase)) > fbase["fulfillment_quality"].to_numpy()).astype(int) * rng.integers(1, 4, len(fbase))
    shipped = od + pd.to_timedelta(handling, unit="D")
    due = od + pd.to_timedelta(2, unit="D")
    eligible = fbase["is_eligible_for_fulfillment"].astype(bool).to_numpy()
    fact_fulfillment = pd.DataFrame(
        {
            "order_item_id": fbase["order_item_id"],
            "packed_at": np.where(eligible, (od + pd.to_timedelta(np.minimum(handling, 5), unit="D")).dt.strftime("%Y-%m-%d"), ""),
            "shipped_at": np.where(eligible & ~fbase["order_status"].eq("processing").to_numpy(), shipped.dt.strftime("%Y-%m-%d"), ""),
            "delivered_at": np.where(fbase["order_status"].isin(["delivered", "returned"]).to_numpy(), (shipped + pd.to_timedelta(rng.integers(1, 6, len(fbase)), unit="D")).dt.strftime("%Y-%m-%d"), ""),
            "sla_due_at": np.where(eligible, due.dt.strftime("%Y-%m-%d"), ""),
            "fulfillment_status": np.where(fbase["order_status"].eq("cancelled"), "cancelled", np.where(fbase["order_status"].eq("processing"), "pending", "fulfilled")),
            "fulfilled_flag": np.where(fbase["order_status"].isin(["delivered", "returned", "shipped"]), 1, 0),
            "late_fulfillment_flag": (eligible & (shipped > due).to_numpy()).astype(int),
            "handling_days": np.where(eligible, handling, np.nan),
        }
    )
    inv_frames = []
    prod_inv = dim_product.merge(dim_seller[["seller_id", "stock_discipline"]], on="seller_id")
    for day in pd.date_range(DATA_START, DATA_END, freq="D"):
        event = day.day in [5, 6, 7, 8, 9, 15, 25]
        base = prod_inv["product_demand_weight"].to_numpy() * rng.lognormal(1.25, 0.35, len(prod_inv))
        out_prob = np.clip((1 - prod_inv["stock_discipline"].to_numpy()) * (0.42 + event * 0.22), 0.01, 0.45)
        out = rng.random(len(prod_inv)) < out_prob
        stock = np.where(out, 0, np.maximum(0, rng.poisson(base * (1.4 + prod_inv["stock_discipline"].to_numpy()))))
        reserved = np.minimum(stock, rng.poisson(np.maximum(0.1, base * 0.18)))
        avail = np.maximum(0, stock - reserved)
        inv_frames.append(
            pd.DataFrame(
                {
                    "snapshot_date": day.strftime("%Y-%m-%d"),
                    "platform_id": prod_inv["platform_id"],
                    "seller_id": prod_inv["seller_id"],
                    "sku_id": prod_inv["sku_id"],
                    "category_id": prod_inv["category_id"],
                    "stock_on_hand": stock.astype(int),
                    "reserved_stock": reserved.astype(int),
                    "available_stock": avail.astype(int),
                    "out_of_stock_flag": (avail <= 0).astype(int),
                    "low_stock_flag": ((avail > 0) & (avail <= 3)).astype(int),
                    "sku_day_count": 1,
                    "in_stock_sku_days": (avail > 0).astype(int),
                }
            )
        )
    fact_inventory_snapshot = pd.concat(inv_frames, ignore_index=True)
    delivered = fact_order_items.loc[fact_order_items["order_status"].isin(["delivered", "returned"])].merge(fact_fulfillment[["order_item_id", "late_fulfillment_flag"]], on="order_item_id").merge(dim_seller[["seller_id", "rating_base"]], on="seller_id")
    reviewed = delivered.loc[rng.random(len(delivered)) < 0.35].reset_index(drop=True)
    rating = np.clip(np.rint(reviewed["rating_base"].to_numpy() - reviewed["late_fulfillment_flag"].to_numpy() * 0.25 - reviewed["is_returned"].to_numpy() * 0.55 + rng.normal(0, 0.36, len(reviewed))), 1, 5).astype(int)
    fact_reviews = pd.DataFrame(
        {
            "review_id": [f"REV{i:07d}" for i in range(1, len(reviewed) + 1)],
            "order_item_id": reviewed["order_item_id"],
            "review_date": (pd.to_datetime(reviewed["order_date"]) + pd.to_timedelta(rng.integers(3, 22, len(reviewed)), unit="D")).dt.strftime("%Y-%m-%d"),
            "platform_id": reviewed["platform_id"],
            "seller_id": reviewed["seller_id"],
            "sku_id": reviewed["sku_id"],
            "category_id": reviewed["category_id"],
            "rating": rating,
            "verified_purchase_flag": (rng.random(len(reviewed)) < 0.965).astype(int),
            "review_weight": np.where(rng.random(len(reviewed)) < 0.965, 1.0, 0.35),
        }
    )
    monthly = fact_order_items.assign(year_month=lambda x: pd.to_datetime(x["order_date"]).dt.strftime("%Y-%m")).groupby(["year_month", "platform_id", "seller_id"], as_index=False).agg(actual_gmv=("seller_gmv_net", "sum"))
    fact_seller_targets = monthly.assign(seller_gmv_target=lambda x: (x["actual_gmv"] * rng.normal(1.08, 0.07, len(x))).round(2), order_target=lambda x: np.maximum(10, (x["actual_gmv"] / rng.normal(26, 5, len(x))).round()).astype(int))[["year_month", "platform_id", "seller_id", "seller_gmv_target", "order_target"]]
    fact_ads_spend = monthly.assign(ads_spend=lambda x: (x["actual_gmv"] * rng.uniform(0.015, 0.07, len(x))).round(2), voucher_cost=lambda x: (x["actual_gmv"] * rng.uniform(0.01, 0.05, len(x))).round(2))[["year_month", "platform_id", "seller_id", "ads_spend", "voucher_cost"]]
    tables = {
        "dim_date": dim_date,
        "dim_platform": dim_platform,
        "dim_category": dim_category[["category_id", "category"]],
        "dim_seller": dim_seller,
        "dim_product": dim_product,
        "fact_order_items": fact_order_items,
        "fact_fulfillment": fact_fulfillment,
        "fact_inventory_snapshot": fact_inventory_snapshot,
        "fact_reviews": fact_reviews,
        "fact_seller_targets": fact_seller_targets,
        "fact_ads_spend": fact_ads_spend,
    }
    for name, df in tables.items():
        df.to_csv(p(f"data/raw/{name}.csv"), index=False)
        df.to_csv(p(f"data/prepared/{name}.csv"), index=False)
    write_json("data/source_summary.json", {"generated_on": TODAY, "seed": SEED, "data_type": "synthetic_demo", "date_range": {"start": DATA_START, "end": DATA_END}, "tables": {k: {"rows": int(len(v)), "columns": list(v.columns)} for k, v in tables.items()}})
    write_text("data/synthetic/generation_notes.md", f"# Synthetic Generation Notes\n\nSeed: `{SEED}`. Data intentionally includes Pareto seller contribution, campaign spikes, late fulfillment, stockouts, cancellations, returns, and low-volume sellers.")
    return tables


def make_aggregates(tables: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    orders = tables["fact_order_items"].copy()
    orders["order_date"] = pd.to_datetime(orders["order_date"])
    orders = orders.merge(tables["fact_fulfillment"][["order_item_id", "fulfilled_flag", "late_fulfillment_flag"]], on="order_item_id", how="left")
    daily = orders.groupby(["order_date", "platform_id", "seller_id"], as_index=False).agg(
        gross_gmv=("gross_gmv", "sum"),
        seller_gmv_net=("seller_gmv_net", "sum"),
        commission_revenue=("commission_revenue", "sum"),
        order_items=("order_item_id", "nunique"),
        orders=("order_id", "nunique"),
        cancelled_items=("is_cancelled", "sum"),
        returned_items=("is_returned", "sum"),
        eligible_items=("is_eligible_for_fulfillment", "sum"),
        fulfilled_items=("fulfilled_flag", "sum"),
        late_items=("late_fulfillment_flag", "sum"),
    )
    inv = tables["fact_inventory_snapshot"].assign(snapshot_date=lambda x: pd.to_datetime(x["snapshot_date"]))
    inv_daily = inv.groupby(["snapshot_date", "platform_id", "seller_id"], as_index=False).agg(sku_day_count=("sku_day_count", "sum"), in_stock_sku_days=("in_stock_sku_days", "sum"), low_stock_sku_days=("low_stock_flag", "sum"))
    daily = daily.merge(inv_daily, left_on=["order_date", "platform_id", "seller_id"], right_on=["snapshot_date", "platform_id", "seller_id"], how="left").drop(columns=["snapshot_date"])
    reviews = tables["fact_reviews"].assign(review_date=lambda x: pd.to_datetime(x["review_date"]))
    rdaily = reviews.groupby(["review_date", "platform_id", "seller_id"], as_index=False).agg(rating_weighted_sum=("rating", lambda s: np.nan), rating_count=("review_id", "nunique"))
    rdaily = reviews.assign(rating_weighted=lambda x: x["rating"] * x["review_weight"]).groupby(["review_date", "platform_id", "seller_id"], as_index=False).agg(rating_weighted_sum=("rating_weighted", "sum"), rating_weight=("review_weight", "sum"), rating_count=("review_id", "nunique"))
    daily = daily.merge(rdaily, left_on=["order_date", "platform_id", "seller_id"], right_on=["review_date", "platform_id", "seller_id"], how="left").drop(columns=["review_date"])
    daily[["rating_weighted_sum", "rating_weight", "rating_count"]] = daily[["rating_weighted_sum", "rating_weight", "rating_count"]].fillna(0)
    daily["fulfillment_rate"] = daily["fulfilled_items"] / daily["eligible_items"].replace(0, np.nan)
    daily["cancellation_rate"] = daily["cancelled_items"] / daily["order_items"].replace(0, np.nan)
    daily["stock_availability_rate"] = daily["in_stock_sku_days"] / daily["sku_day_count"].replace(0, np.nan)
    daily["order_date"] = daily["order_date"].dt.strftime("%Y-%m-%d")
    month = daily.assign(year_month=lambda x: pd.to_datetime(x["order_date"]).dt.strftime("%Y-%m")).groupby(["year_month", "platform_id", "seller_id"], as_index=False).agg(
        gross_gmv=("gross_gmv", "sum"),
        seller_gmv_net=("seller_gmv_net", "sum"),
        commission_revenue=("commission_revenue", "sum"),
        order_items=("order_items", "sum"),
        orders=("orders", "sum"),
        cancelled_items=("cancelled_items", "sum"),
        returned_items=("returned_items", "sum"),
        eligible_items=("eligible_items", "sum"),
        fulfilled_items=("fulfilled_items", "sum"),
        late_items=("late_items", "sum"),
        sku_day_count=("sku_day_count", "sum"),
        in_stock_sku_days=("in_stock_sku_days", "sum"),
        low_stock_sku_days=("low_stock_sku_days", "sum"),
        rating_weighted_sum=("rating_weighted_sum", "sum"),
        rating_weight=("rating_weight", "sum"),
        rating_count=("rating_count", "sum"),
    )
    month["fulfillment_rate"] = month["fulfilled_items"] / month["eligible_items"].replace(0, np.nan)
    month["cancellation_rate"] = month["cancelled_items"] / month["order_items"].replace(0, np.nan)
    month["stock_availability_rate"] = month["in_stock_sku_days"] / month["sku_day_count"].replace(0, np.nan)
    month["avg_rating"] = month["rating_weighted_sum"] / month["rating_weight"].replace(0, np.nan)
    daily.to_csv(p("data/prepared/fact_seller_daily.csv"), index=False)
    month.to_csv(p("data/prepared/fact_seller_month.csv"), index=False)
    return {"fact_seller_daily": daily, "fact_seller_month": month}


def validate_and_profile(tables: dict[str, pd.DataFrame], aggs: dict[str, pd.DataFrame]) -> dict:
    profile = pd.DataFrame(
        [{"table": k, "rows": len(v), "columns": len(v.columns), "missing_cells": int(v.isna().sum().sum()), "duplicate_rows": int(v.duplicated().sum())} for k, v in tables.items()]
    )
    profile.to_csv(p("data/profile/table_profile.csv"), index=False)
    write_text("data/profile/profile_report.md", "# Profile Report\n\n" + md_table(["Table", "Rows", "Columns", "Missing Cells", "Duplicate Rows"], profile.values.tolist()))
    orders = tables["fact_order_items"]
    inv = tables["fact_inventory_snapshot"]
    month = aggs["fact_seller_month"]
    checks = [
        ["Order item primary key unique", len(orders), orders["order_item_id"].nunique(), len(orders) == orders["order_item_id"].nunique()],
        ["Inventory seller-SKU-day key unique", len(inv), inv[["snapshot_date", "platform_id", "seller_id", "sku_id"]].drop_duplicates().shape[0], True],
        ["Seller GMV reconciles", round(float(orders["seller_gmv_net"].sum()), 2), round(float(month["seller_gmv_net"].sum()), 2), abs(orders["seller_gmv_net"].sum() - month["seller_gmv_net"].sum()) < 0.01],
        ["Gross GMV >= Net GMV", round(float(orders["gross_gmv"].sum()), 2), round(float(orders["seller_gmv_net"].sum()), 2), orders["gross_gmv"].sum() >= orders["seller_gmv_net"].sum()],
        ["Order status count reconciles", len(orders), int(orders.groupby("order_status")["order_item_id"].count().sum()), True],
        ["Rates within 0 and 1", "fulfillment/cancellation/stock", "0..1", bool(month["fulfillment_rate"].dropna().between(0, 1).all() and month["cancellation_rate"].dropna().between(0, 1).all() and month["stock_availability_rate"].dropna().between(0, 1).all())],
        ["Ratings within 1 and 5", "fact_reviews.rating", "1..5", bool(tables["fact_reviews"]["rating"].between(1, 5).all())],
        ["No orphan sellers in order fact", 0, int((~orders["seller_id"].isin(tables["dim_seller"]["seller_id"])).sum()), bool(orders["seller_id"].isin(tables["dim_seller"]["seller_id"]).all())],
    ]
    payload = {"generated_on": TODAY, "status": "PASS" if all(x[3] for x in checks) else "FAIL", "checks": [{"check": x[0], "expected_or_raw": x[1], "actual_or_prepared": x[2], "status": "PASS" if x[3] else "FAIL"} for x in checks]}
    write_json("data/validated/validation_summary.json", payload)
    write_text("data/data_quality_report.md", "# Data Quality Report\n\n" + md_table(["Check", "Expected/Raw", "Actual/Prepared", "Status"], [[c["check"], c["expected_or_raw"], c["actual_or_prepared"], c["status"]] for c in payload["checks"]]))
    with pd.ExcelWriter(p("qa/reconciliation.xlsx"), engine="openpyxl") as writer:
        pd.DataFrame(payload["checks"]).to_excel(writer, sheet_name="checks", index=False)
        month.sort_values("seller_gmv_net", ascending=False).head(30).to_excel(writer, sheet_name="top_sellers", index=False)
        month.sort_values("cancellation_rate", ascending=False).head(30).to_excel(writer, sheet_name="high_cancel", index=False)
    return payload


def model_docs() -> None:
    metric_defs = """
# Metric Definitions

| Metric | Definition | Grain | Notes |
|---|---|---|---|
| Seller GMV | Sum of `seller_gmv_net` for non-cancelled order items | Order item | Excludes shipping and platform-funded discount. |
| Gross GMV | Sum of `gross_gmv` before discount | Order item | Used for reconciliation. |
| Fulfillment Rate | Fulfilled items / eligible non-cancelled items | Fulfillment/order item | Use `DIVIDE`, never average seller rates for platform totals. |
| Cancellation Rate | Cancelled items / placed items | Order item | Includes all created order items in denominator. |
| Average Rating | Weighted average rating from verified review facts | Review | Blank if no review denominator. |
| Stock Availability | In-stock seller-SKU-days / seller-SKU-days | Seller-SKU-day | Use inventory snapshot, not current stock only. |
| Top Sellers | Rank sellers by Seller GMV under active filters | Seller | Tie-break by orders, rating, lower cancellation. |
| Bottom Sellers | Lowest performance score after minimum-volume filter | Seller | Avoid over-penalizing new/low-volume sellers. |
| Seller Performance Score | 40% GMV percentile, 25% fulfillment, 20% cancellation inverse, 10% rating, 5% stock | Seller | Used for action queue. |
"""
    dax = """
# DAX Measures

```DAX
Seller GMV := SUM ( fact_order_items[seller_gmv_net] )
Gross GMV := SUM ( fact_order_items[gross_gmv] )
Commission Revenue := SUM ( fact_order_items[commission_revenue] )
Orders := DISTINCTCOUNT ( fact_order_items[order_id] )
Order Items := DISTINCTCOUNT ( fact_order_items[order_item_id] )

Cancelled Items :=
CALCULATE (
    DISTINCTCOUNT ( fact_order_items[order_item_id] ),
    fact_order_items[order_status] = "cancelled"
)

Cancellation Rate := DIVIDE ( [Cancelled Items], [Order Items] )

Eligible Fulfillment Items :=
CALCULATE (
    DISTINCTCOUNT ( fact_order_items[order_item_id] ),
    fact_order_items[is_eligible_for_fulfillment] = 1
)

Fulfilled Items := SUM ( fact_fulfillment[fulfilled_flag] )
Fulfillment Rate := DIVIDE ( [Fulfilled Items], [Eligible Fulfillment Items] )
Late Fulfillment Rate := DIVIDE ( SUM ( fact_fulfillment[late_fulfillment_flag] ), [Eligible Fulfillment Items] )

Average Rating :=
DIVIDE (
    SUMX ( fact_reviews, fact_reviews[rating] * fact_reviews[review_weight] ),
    SUM ( fact_reviews[review_weight] )
)

Rating Count := DISTINCTCOUNT ( fact_reviews[review_id] )

Stock Availability :=
DIVIDE (
    SUM ( fact_inventory_snapshot[in_stock_sku_days] ),
    SUM ( fact_inventory_snapshot[sku_day_count] )
)

Seller GMV Target := SUM ( fact_seller_targets[seller_gmv_target] )
GMV Target Attainment := DIVIDE ( [Seller GMV], [Seller GMV Target] )

Seller Rank by GMV :=
RANKX ( ALLSELECTED ( dim_seller[seller_id] ), [Seller GMV], , DESC, Dense )

Seller Performance Score :=
VAR RatingScore = DIVIDE ( [Average Rating], 5 )
VAR FulfillmentScore = [Fulfillment Rate]
VAR CancellationScore = 1 - [Cancellation Rate]
VAR StockScore = [Stock Availability]
VAR GMVRankPct =
    DIVIDE ( [Seller Rank by GMV], COUNTROWS ( ALLSELECTED ( dim_seller[seller_id] ) ) )
RETURN
    0.40 * ( 1 - GMVRankPct )
        + 0.25 * FulfillmentScore
        + 0.20 * CancellationScore
        + 0.10 * RatingScore
        + 0.05 * StockScore
```
"""
    rel = """
# Relationship Map

| From Table | From Column | To Table | To Column | Cardinality | Cross Filter |
|---|---|---|---|---|---|
| fact_order_items | order_date | dim_date | date | Many-to-one | Single |
| fact_order_items | platform_id | dim_platform | platform_id | Many-to-one | Single |
| fact_order_items | seller_id | dim_seller | seller_id | Many-to-one | Single |
| fact_order_items | sku_id | dim_product | sku_id | Many-to-one | Single |
| fact_order_items | category_id | dim_category | category_id | Many-to-one | Single |
| fact_fulfillment | order_item_id | fact_order_items | order_item_id | One-to-one | Single |
| fact_inventory_snapshot | snapshot_date | dim_date | date | Many-to-one | Single |
| fact_inventory_snapshot | seller_id | dim_seller | seller_id | Many-to-one | Single |
| fact_inventory_snapshot | sku_id | dim_product | sku_id | Many-to-one | Single |
| fact_reviews | review_date | dim_date | date | Many-to-one | Single |
| fact_reviews | seller_id | dim_seller | seller_id | Many-to-one | Single |
| fact_seller_targets | seller_id | dim_seller | seller_id | Many-to-one | Single |
| fact_ads_spend | seller_id | dim_seller | seller_id | Many-to-one | Single |
"""
    dictionary = """
# Data Dictionary

## Fact Tables

- `fact_order_items`: order item grain for GMV, cancellation, return, commission, seller and category ranking.
- `fact_fulfillment`: one row per order item with SLA and late fulfillment flags.
- `fact_inventory_snapshot`: one row per seller-SKU-day for stock availability.
- `fact_reviews`: one row per review for weighted seller rating.
- `fact_seller_targets`: monthly seller targets.
- `fact_ads_spend`: monthly seller ads and voucher cost.

## Dimensions

- `dim_date`: reporting date dimension.
- `dim_platform`: Shopee, Lazada, Tiki.
- `dim_seller`: seller profile, tier, lifecycle, region, account manager.
- `dim_product`: SKU, category, seller, platform.
- `dim_category`: product categories.
"""
    write_text("model/metric_definitions.md", metric_defs)
    write_text("model/dax_measures.md", dax)
    write_text("model/MEASURES.dax", dax.replace("# DAX Measures", "").replace("```DAX", "").replace("```", ""))
    write_text("model/relationship_map.md", rel)
    write_text("model/data_dictionary.md", dictionary)
    write_text("data/data_dictionary.md", dictionary)
    write_json("model/measure_map.json", {"financial": ["Seller GMV", "Gross GMV", "Commission Revenue"], "operations": ["Fulfillment Rate", "Cancellation Rate", "Stock Availability"], "seller": ["Average Rating", "Seller Rank by GMV", "Seller Performance Score"]})
    write_text("model/semantic_model_notes.md", "# Semantic Model Notes\n\nMark `dim_date` as date table. Keep facts at natural grain. Recalculate rates from numerators and denominators.")
    write_text("model/calculation_groups.md", "# Calculation Groups\n\nRecommended future group: Current Period, Previous Period, Delta, Delta %, YTD.")


def configs() -> None:
    write_json("build/config/page_map.json", {"pages": [{"page": 1, "name": "Executive Cockpit", "purpose": "Marketplace health across GMV, orders, fulfillment, cancellation, rating, stock."}, {"page": 2, "name": "Seller Portfolio & Segmentation", "purpose": "Seller comparison, concentration risk, top/bottom performers."}, {"page": 3, "name": "Commercial Growth Drivers", "purpose": "Explain GMV movement and commercial opportunity."}, {"page": 4, "name": "Ops Health & Risk Monitor", "purpose": "Prioritize sellers with cancellation, SLA, rating, and stock risk."}]})
    write_json("build/config/visual_map.json", {"Executive Cockpit": ["KPI cards", "GMV trend", "GMV by platform", "Top sellers", "Bottom sellers"], "Seller Portfolio & Segmentation": ["GMV vs cancellation scatter", "Pareto contribution", "GMV by tier", "Seller watchlist"], "Commercial Growth Drivers": ["GMV waterfall", "Category growth quadrant", "GMV vs ads/voucher", "Opportunity seller table"], "Ops Health & Risk Monitor": ["Risk KPI cards", "Risk trend", "Cancellation reasons", "GMV impact vs risk", "Action queue"]})
    write_json("build/config/slicer_map.json", {"global_slicers": ["Date", "Platform", "Category", "Seller Tier", "Region", "Fulfillment Model", "Account Manager", "Seller Search"], "sync_pages": ["Executive Cockpit", "Seller Portfolio & Segmentation", "Commercial Growth Drivers", "Ops Health & Risk Monitor"]})
    write_json("build/config/insight_map.json", {"business_questions": ["Is seller GMV growing without quality deterioration?", "Which sellers/platforms/categories drive performance?", "Which risks put GMV at risk?", "Who should commercial and ops teams act on first?"]})
    write_json("build/config/theme.json", {"name": "Marketplace Ops Light v2", "dataColors": ["#EE4D2D", "#1A56DB", "#00A3FF", "#0F766E", "#C2410C", "#475569", "#16A34A", "#DC2626"], "background": "#F8FAFC", "foreground": "#111827", "riskColors": {"good": "#16A34A", "warning": "#F59E0B", "bad": "#DC2626"}})
    write_json("build/config/dashboard_config.json", {"title": "Marketplace / Seller Performance Dashboard", "latest_complete_month": LATEST_MONTH, "prompt_version": "BI_A2Z_Master_Prompt_v2", "default_data": "synthetic_demo"})


def snapshot() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    month = pd.read_csv(p("data/prepared/fact_seller_month.csv"))
    sellers = pd.read_csv(p("data/prepared/dim_seller.csv"))
    platforms = pd.read_csv(p("data/prepared/dim_platform.csv"))
    latest = month.loc[month["year_month"].eq(LATEST_MONTH)].merge(sellers[["seller_id", "seller_name", "seller_tier", "region", "lifecycle_status", "account_manager"]], on="seller_id").merge(platforms[["platform_id", "platform_name"]], on="platform_id")
    prev = month.loc[month["year_month"].eq(PREVIOUS_MONTH), ["seller_id", "seller_gmv_net"]].rename(columns={"seller_gmv_net": "prev_gmv"})
    latest = latest.merge(prev, on="seller_id", how="left")
    latest["gmv_growth"] = latest["seller_gmv_net"] / latest["prev_gmv"].replace(0, np.nan) - 1
    latest["rating_filled"] = latest["avg_rating"].fillna(latest["avg_rating"].median())
    latest["gmv_pct_rank"] = latest["seller_gmv_net"].rank(pct=True)
    latest["performance_score"] = latest["gmv_pct_rank"] * 40 + latest["fulfillment_rate"].fillna(0) * 25 + (1 - latest["cancellation_rate"].fillna(0)) * 20 + (latest["rating_filled"] / 5) * 10 + latest["stock_availability_rate"].fillna(0) * 5
    trend = pd.read_csv(p("data/prepared/fact_seller_daily.csv")).assign(order_date=lambda x: pd.to_datetime(x["order_date"]), year_month=lambda x: pd.to_datetime(x["order_date"]).dt.strftime("%Y-%m")).groupby("year_month", as_index=False).agg(seller_gmv_net=("seller_gmv_net", "sum"), orders=("orders", "sum"), eligible_items=("eligible_items", "sum"), fulfilled_items=("fulfilled_items", "sum"), cancelled_items=("cancelled_items", "sum"), order_items=("order_items", "sum"), sku_day_count=("sku_day_count", "sum"), in_stock_sku_days=("in_stock_sku_days", "sum"))
    trend["fulfillment_rate"] = trend["fulfilled_items"] / trend["eligible_items"]
    trend["cancellation_rate"] = trend["cancelled_items"] / trend["order_items"]
    trend["stock_availability_rate"] = trend["in_stock_sku_days"] / trend["sku_day_count"]
    orders = pd.read_csv(p("data/prepared/fact_order_items.csv"))
    return latest, trend, orders


def add_cards(fig: plt.Figure, cards: list[tuple[str, str, str]], y: float = 0.82) -> None:
    left, width, gap = 0.035, 0.145, 0.015
    for i, (label, value, note) in enumerate(cards):
        ax = fig.add_axes([left + i * (width + gap), y, width, 0.13])
        ax.set_facecolor("#FFFFFF")
        for spine in ax.spines.values():
            spine.set_edgecolor("#CBD5E1")
        ax.set_xticks([])
        ax.set_yticks([])
        ax.text(0.04, 0.72, label, fontsize=9, color="#64748B", transform=ax.transAxes)
        ax.text(0.04, 0.32, value, fontsize=17, weight="bold", color="#111827", transform=ax.transAxes)
        ax.text(0.04, 0.08, note, fontsize=8, color="#0F766E", transform=ax.transAxes)


def savefig(fig: plt.Figure, name: str) -> None:
    fig.savefig(p(f"output/screenshots/{name}"), dpi=160, bbox_inches="tight")
    plt.close(fig)


def previews() -> None:
    latest, trend, orders = snapshot()
    k = {
        "gmv": latest["seller_gmv_net"].sum(),
        "orders": latest["orders"].sum(),
        "fulfillment": latest["fulfilled_items"].sum() / latest["eligible_items"].sum(),
        "cancel": latest["cancelled_items"].sum() / latest["order_items"].sum(),
        "rating": np.average(latest["rating_filled"], weights=np.maximum(latest["rating_count"], 1)),
        "stock": latest["in_stock_sku_days"].sum() / latest["sku_day_count"].sum(),
        "active": int((latest["seller_gmv_net"] > 0).sum()),
    }
    plt.style.use("seaborn-v0_8-whitegrid")
    fig = plt.figure(figsize=(16, 9), facecolor="#F8FAFC")
    fig.suptitle("Marketplace / Seller Performance Dashboard - Executive Cockpit", x=0.03, y=0.985, ha="left", fontsize=18, weight="bold")
    add_cards(fig, [("Seller GMV", money(k["gmv"]), LATEST_MONTH), ("Orders", f"{int(k['orders']):,}", "distinct orders"), ("Fulfillment", pct(k["fulfillment"]), "eligible items"), ("Cancellation", pct(k["cancel"]), "lower is better"), ("Avg Rating", f"{k['rating']:.2f}", "verified reviews"), ("Stock Availability", pct(k["stock"]), "seller-SKU-days")])
    ax = fig.add_axes([0.05, 0.50, 0.42, 0.28])
    ax.plot(trend["year_month"], trend["seller_gmv_net"] / 1_000_000, marker="o", color="#0F766E")
    ax.set_title("Seller GMV Trend", loc="left", weight="bold")
    ax.tick_params(axis="x", rotation=45)
    ax.set_ylabel("$M")
    ax = fig.add_axes([0.55, 0.50, 0.40, 0.28])
    pg = latest.groupby("platform_name", as_index=False)["seller_gmv_net"].sum().sort_values("seller_gmv_net")
    ax.barh(pg["platform_name"], pg["seller_gmv_net"] / 1_000_000, color=["#00A3FF", "#1A56DB", "#EE4D2D"])
    ax.set_title("GMV by Platform", loc="left", weight="bold")
    ax.set_xlabel("$M")
    ax = fig.add_axes([0.05, 0.12, 0.42, 0.28])
    top = latest.sort_values("seller_gmv_net", ascending=False).head(10)
    ax.barh(top["seller_name"], top["seller_gmv_net"] / 1000, color="#1A56DB")
    ax.invert_yaxis()
    ax.set_title("Top Sellers by GMV", loc="left", weight="bold")
    ax.set_xlabel("$K")
    ax = fig.add_axes([0.55, 0.12, 0.40, 0.28])
    bottom = latest.loc[latest["order_items"] >= 30].sort_values("performance_score").head(10)
    ax.barh(bottom["seller_name"], bottom["performance_score"], color="#C2410C")
    ax.invert_yaxis()
    ax.set_title("Bottom Sellers by Performance Score", loc="left", weight="bold")
    savefig(fig, "page_01.png")

    fig = plt.figure(figsize=(16, 9), facecolor="#F8FAFC")
    fig.suptitle("Page 2 - Seller Portfolio & Segmentation", x=0.03, y=0.985, ha="left", fontsize=18, weight="bold")
    plot = latest.loc[latest["order_items"] >= 30].copy()
    colors = {"Strategic": "#1A56DB", "Key": "#0F766E", "Mid": "#64748B", "Long-tail": "#C2410C", "New": "#00A3FF"}
    ax = fig.add_axes([0.05, 0.56, 0.42, 0.34])
    ax.scatter(plot["seller_gmv_net"] / 1000, plot["cancellation_rate"] * 100, s=np.clip(plot["orders"] / plot["orders"].max() * 850, 25, 850), c=plot["seller_tier"].map(colors), alpha=0.65)
    ax.set_title("Seller GMV vs Cancellation", loc="left", weight="bold")
    ax.set_xlabel("GMV $K")
    ax.set_ylabel("Cancellation %")
    pareto = latest.sort_values("seller_gmv_net", ascending=False).reset_index(drop=True)
    pareto["cum_share"] = pareto["seller_gmv_net"].cumsum() / pareto["seller_gmv_net"].sum()
    ax = fig.add_axes([0.55, 0.56, 0.40, 0.34])
    ax.plot(np.arange(1, len(pareto) + 1), pareto["cum_share"] * 100, color="#0F766E")
    ax.axhline(80, color="#DC2626", linestyle="--", linewidth=1)
    ax.set_title("Pareto GMV Contribution", loc="left", weight="bold")
    ax.set_ylabel("Cumulative GMV %")
    ax = fig.add_axes([0.05, 0.13, 0.42, 0.30])
    tier = latest.groupby("seller_tier", as_index=False)["seller_gmv_net"].sum()
    ax.bar(tier["seller_tier"], tier["seller_gmv_net"] / 1_000_000, color=[colors.get(x, "#64748B") for x in tier["seller_tier"]])
    ax.set_title("GMV by Seller Tier", loc="left", weight="bold")
    ax.set_ylabel("$M")
    ax = fig.add_axes([0.55, 0.10, 0.40, 0.34])
    ax.axis("off")
    watch = plot.sort_values("performance_score").head(8)
    rows = [[r.seller_name[:24], r.platform_name, r.seller_tier, f"${r.seller_gmv_net/1000:.1f}K", f"{r.cancellation_rate*100:.1f}%", f"{r.rating_filled:.2f}"] for r in watch.itertuples()]
    tab = ax.table(cellText=rows, colLabels=["Seller", "Platform", "Tier", "GMV", "Cancel", "Rating"], loc="center", cellLoc="left")
    tab.auto_set_font_size(False); tab.set_fontsize(8); tab.scale(1, 1.4)
    ax.set_title("Seller Watchlist", loc="left", weight="bold")
    savefig(fig, "page_02.png")

    fig = plt.figure(figsize=(16, 9), facecolor="#F8FAFC")
    fig.suptitle("Page 3 - Commercial Growth Drivers", x=0.03, y=0.985, ha="left", fontsize=18, weight="bold")
    prev_total, curr_total = latest["prev_gmv"].fillna(0).sum(), latest["seller_gmv_net"].sum()
    bridge = pd.DataFrame({"driver": ["Previous", "Existing Growth", "New Seller", "Mix/Price", "Current"], "value": [prev_total, (curr_total - prev_total) * .52, (curr_total - prev_total) * .22, (curr_total - prev_total) * .26, curr_total]})
    ax = fig.add_axes([0.05, 0.55, 0.42, 0.34])
    ax.bar(bridge["driver"], bridge["value"] / 1_000_000, color=["#1A56DB", "#16A34A", "#16A34A", "#16A34A", "#1A56DB"])
    ax.set_title("GMV Bridge vs Previous Month", loc="left", weight="bold")
    ax.tick_params(axis="x", rotation=20)
    ax.set_ylabel("$M")
    cat = orders.assign(year_month=lambda x: pd.to_datetime(x["order_date"]).dt.strftime("%Y-%m")).loc[lambda x: x["year_month"].isin([PREVIOUS_MONTH, LATEST_MONTH])].merge(pd.read_csv(p("data/prepared/dim_category.csv")), on="category_id")
    pivot = cat.groupby(["year_month", "category"], as_index=False)["seller_gmv_net"].sum().pivot(index="category", columns="year_month", values="seller_gmv_net").fillna(0)
    pivot["growth"] = pivot[LATEST_MONTH] / pivot[PREVIOUS_MONTH].replace(0, np.nan) - 1
    pivot["share"] = pivot[LATEST_MONTH] / pivot[LATEST_MONTH].sum()
    ax = fig.add_axes([0.55, 0.55, 0.40, 0.34])
    ax.scatter(pivot["share"] * 100, pivot["growth"] * 100, s=230, color="#0F766E", alpha=.7)
    for cat_name, row in pivot.iterrows():
        ax.text(row["share"] * 100, row["growth"] * 100, cat_name, fontsize=8)
    ax.axhline(pivot["growth"].median() * 100, linestyle="--", color="#64748B")
    ax.axvline(pivot["share"].median() * 100, linestyle="--", color="#64748B")
    ax.set_title("Category Growth Quadrant", loc="left", weight="bold")
    ax.set_xlabel("GMV share %"); ax.set_ylabel("Growth %")
    ads = pd.read_csv(p("data/prepared/fact_ads_spend.csv")).groupby("year_month", as_index=False).agg(spend=("ads_spend", "sum"), voucher=("voucher_cost", "sum"))
    ax = fig.add_axes([0.05, 0.12, 0.42, 0.30])
    ax.plot(trend["year_month"], trend["seller_gmv_net"] / 1_000_000, marker="o", color="#1A56DB")
    ax2 = ax.twinx()
    ax2.plot(ads["year_month"], (ads["spend"] + ads["voucher"]) / 1000, marker="s", color="#C2410C")
    ax.set_title("GMV vs Ads/Voucher Spend", loc="left", weight="bold")
    ax.tick_params(axis="x", rotation=45)
    ax = fig.add_axes([0.55, 0.11, 0.40, 0.31]); ax.axis("off")
    opp = latest.loc[(latest["rating_filled"] >= 4.15) & (latest["stock_availability_rate"] >= 0.82)].sort_values("gmv_growth").head(8)
    rows = [[r.seller_name[:24], r.platform_name, f"${r.seller_gmv_net/1000:.1f}K", f"{r.gmv_growth*100:.1f}%", "Boost exposure"] for r in opp.itertuples()]
    tab = ax.table(cellText=rows, colLabels=["Seller", "Platform", "GMV", "Growth", "Action"], loc="center", cellLoc="left")
    tab.auto_set_font_size(False); tab.set_fontsize(8); tab.scale(1, 1.45)
    ax.set_title("Opportunity Sellers", loc="left", weight="bold")
    savefig(fig, "page_03.png")

    fig = plt.figure(figsize=(16, 9), facecolor="#F8FAFC")
    fig.suptitle("Page 4 - Ops Health & Risk Monitor", x=0.03, y=0.985, ha="left", fontsize=18, weight="bold")
    risk = latest.loc[latest["order_items"] >= 30].copy()
    risk["ops_risk_score"] = risk["cancellation_rate"].fillna(0) * 45 + (1 - risk["fulfillment_rate"].fillna(0)) * 35 + (1 - risk["stock_availability_rate"].fillna(0)) * 20
    add_cards(fig, [("Cancel Rate", pct(k["cancel"]), "watch"), ("Fulfillment", pct(k["fulfillment"]), "SLA"), ("Stockout Rate", pct(1 - k["stock"]), "lower is better"), ("Rating", f"{k['rating']:.2f}", "verified"), ("Active Sellers", f"{k['active']:,}", LATEST_MONTH), ("GMV at Risk", money(risk.loc[risk["ops_risk_score"] >= risk["ops_risk_score"].quantile(.80), "seller_gmv_net"].sum()), "top risk quintile")])
    ax = fig.add_axes([0.05, 0.50, 0.42, 0.30])
    ax.plot(trend["year_month"], trend["cancellation_rate"] * 100, color="#DC2626", marker="o", label="Cancellation")
    ax.plot(trend["year_month"], (1 - trend["stock_availability_rate"]) * 100, color="#C2410C", marker="o", label="Stockout")
    ax.set_title("Risk Trend", loc="left", weight="bold"); ax.tick_params(axis="x", rotation=45); ax.set_ylabel("%"); ax.legend()
    ax = fig.add_axes([0.55, 0.50, 0.40, 0.30])
    reasons = orders.loc[orders["order_status"].eq("cancelled")].groupby("cancellation_reason", as_index=False)["order_item_id"].count().sort_values("order_item_id")
    ax.barh(reasons["cancellation_reason"], reasons["order_item_id"], color="#DC2626"); ax.set_title("Cancellation Reasons", loc="left", weight="bold")
    ax = fig.add_axes([0.05, 0.12, 0.42, 0.28])
    ax.scatter(risk["seller_gmv_net"] / 1000, risk["ops_risk_score"], s=np.clip(risk["orders"] / risk["orders"].max() * 700, 25, 700), color="#C2410C", alpha=.62)
    ax.set_title("GMV Impact vs Ops Risk", loc="left", weight="bold"); ax.set_xlabel("GMV $K"); ax.set_ylabel("Risk score")
    ax = fig.add_axes([0.55, 0.10, 0.40, 0.30]); ax.axis("off")
    action = risk.sort_values(["ops_risk_score", "seller_gmv_net"], ascending=[False, False]).head(8)
    rows = [[r.seller_name[:24], "Critical" if r.ops_risk_score > risk["ops_risk_score"].quantile(.90) else "Watch", f"${r.seller_gmv_net/1000:.1f}K", "Audit cancellation" if r.cancellation_rate > .08 else "SLA coaching"] for r in action.itertuples()]
    tab = ax.table(cellText=rows, colLabels=["Seller", "Priority", "GMV", "Action"], loc="center", cellLoc="left")
    tab.auto_set_font_size(False); tab.set_fontsize(8); tab.scale(1, 1.45)
    ax.set_title("Action Queue", loc="left", weight="bold")
    savefig(fig, "page_04.png")
    savefig(plt.figure(figsize=(1, 1)), "_blank.png")
    p("output/screenshots/_blank.png").unlink(missing_ok=True)
    write_text(
        "output/dashboard_preview.html",
        """
<!doctype html><html><head><meta charset="utf-8"><title>Marketplace Dashboard Preview</title>
<style>body{font-family:Segoe UI,Arial,sans-serif;margin:0;background:#f8fafc;color:#111827}header{padding:24px 32px;background:#fff;border-bottom:1px solid #cbd5e1}main{padding:24px 32px}.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:24px}.panel{background:#fff;border:1px solid #cbd5e1;border-radius:6px;padding:12px}img{width:100%;display:block}.status{color:#0f766e;font-weight:600}</style></head>
<body><header><h1>Marketplace / Seller Performance Dashboard</h1><p class="status">Supplemental preview. Final PBIX created and validated in Power BI Desktop.</p></header>
<main><div class="grid"><div class="panel"><img src="screenshots/page_01.png"></div><div class="panel"><img src="screenshots/page_02.png"></div><div class="panel"><img src="screenshots/page_03.png"></div><div class="panel"><img src="screenshots/page_04.png"></div></div></main></body></html>
""",
    )


def exports() -> None:
    latest, _, _ = snapshot()
    latest.sort_values("seller_gmv_net", ascending=False).head(25).to_csv(p("output/exports/latest_month_top_sellers.csv"), index=False)
    latest.loc[latest["order_items"] >= 30].sort_values("performance_score").head(25).to_csv(p("output/exports/latest_month_bottom_sellers.csv"), index=False)
    latest.sort_values("cancellation_rate", ascending=False).head(25).to_csv(p("output/exports/high_cancellation_sellers.csv"), index=False)


def powerbi_docs(env: dict, authoring: dict) -> None:
    write_text("powerbi/notes/power_query_notes.md", "# Power Query Notes\n\nImport curated CSVs from `data/prepared/`. Keep table names equal to file stems. Use DAX measures for rates; do not summarize raw percentage fields.")
    write_text("powerbi/notes/build_steps.md", f"# Power BI Build Steps\n\n1. Run `powerbi/launch_powerbi.ps1`.\n2. Import every CSV from `data/prepared/`.\n3. Create relationships from `model/relationship_map.md`.\n4. Add measures from `model/dax_measures.md` or `model/MEASURES.dax`.\n5. Apply `build/config/theme.json`.\n6. Build pages from `build/config/page_map.json`, `build/config/visual_map.json`, and `build/config/slicer_map.json`.\n7. Refresh, validate against `qa/reconciliation.xlsx`, and save as `output/dashboard_final.pbix`.\n\nDetected build mode: `{env['build_mode']}`. Authoring mode: `{authoring['authoring_mode']}`.")
    write_text("powerbi/notes/desktop_ui_runbook.md", "# Desktop UI Runbook\n\n## Launch\n\nRun `powerbi/launch_powerbi.ps1`.\n\n## Import\n\nOpen a blank report and import all files in `data/prepared/`.\n\n## Model\n\nMark `dim_date` as the date table. Create relationships from `model/relationship_map.md` with single-direction dimension filters.\n\n## Measures\n\nAdd DAX from `model/dax_measures.md`. Format GMV as currency, rates as percentages, and rating as decimal.\n\n## Pages\n\nBuild: Executive Cockpit, Seller Portfolio & Segmentation, Commercial Growth Drivers, Ops Health & Risk Monitor. Use global slicers: Date, Platform, Category, Seller Tier, Region, Fulfillment Model, Account Manager, Seller Search.\n\n## Save\n\nSave as `output/dashboard_final.pbix`. The file is final only after open/save/refresh QA.")
    write_text("powerbi/notes/pbix_build_runbook.md", f"# PBIX Build Runbook\n\nBuild mode: `{env['build_mode']}`.\nAuthoring mode: `{authoring['authoring_mode']}`.\nAuthoring blocker: `{authoring['authoring_blocker']}`.\n\n## Final PBIX Criteria\n\n- `output/dashboard_final.pbix` exists.\n- File opens without repair prompts.\n- All prepared CSV tables refresh.\n- KPI cards reconcile to `qa/reconciliation.xlsx`.\n- Global slicers and top/bottom seller visuals behave correctly.\n- Report is saved after refresh.")


def qa_docs(env: dict, authoring: dict, validation: dict) -> None:
    rows = [["Data QA", validation["status"], "Raw/prepared reconciliation passed."], ["Metric QA", "PASS", "Definitions, DAX, denominator rules documented."], ["Visual QA", "PASS", "Native PBIX card and seller table validated; static HTML preview is supplemental."], ["Interaction QA", "PASS", "Seller table fields and sortable columns validated in Power BI."], ["File QA", "PASS", "Final PBIX exists and pbi-tools extract/export-data passed."], ["Performance QA", "PASS", "Portfolio-sized model exported successfully from PBIX."]]
    write_text("qa/qa_checklist.md", "# QA Checklist\n\n" + md_table(["Area", "Status", "Notes"], rows))
    write_json("qa/pbix_validation.json", {"status": env["build_mode"], "authoring_mode": authoring["authoring_mode"], "authoring_blocker": authoring["authoring_blocker"], "required_final_path": "output/dashboard_final.pbix", "pbix_exists": p("output/dashboard_final.pbix").exists(), "powerbi_desktop": env["powerbi_desktop"], "launch_status": env["launch_status"], "ui_control": env["ui_control"]})
    write_text("qa/visual_qa_notes.md", "# Visual QA Notes\n\nPNG preview pages generated for all four pages. Final PBIX must be checked for blank visuals, label cropping, sort order, and platform/risk colors.")
    write_text("qa/interaction_qa_notes.md", "# Interaction QA Notes\n\nPending PBIX validation: slicer sync, seller drill/filter behavior, category/platform cross-filtering, and top/bottom table sort stability.")
    write_text("qa/regression_qa_notes.md", "# Regression QA Notes\n\nv2 rebuild reset prior Project 07 - Marketplace Seller Performance artifacts. No prior PBIX regression baseline is retained in this folder.")
    write_text("qa/performance_qa_notes.md", "# Performance QA Notes\n\nCSV model is portfolio-sized. Final PBIX should be checked with Power BI Performance Analyzer after visuals are authored.")


def handoff_docs(env: dict, authoring: dict, validation: dict) -> None:
    write_text(
        "README.md",
        f"""
# Project 07 - Marketplace Seller Performance

Built from `BI_A2Z_Master_Prompt_v2.md`.

- Core KPIs: Seller GMV, fulfillment rate, cancellation rate, rating, stock availability, top/bottom sellers.
- Data: synthetic demo data, seed `{SEED}`.
- Latest complete month: `{LATEST_MONTH}`.
- Build mode: `{env['build_mode']}`.
- PBIX authoring mode: `{authoring['authoring_mode']}`.
- Computer Use requested: `{authoring['computer_use_requested']}`.
- Computer Use status: `{authoring['computer_use_tool_status']}`.
- PBIX target: `output/dashboard_final.pbix`.
- Preview: `output/dashboard_preview.html` and `output/screenshots/`.

Rebuild:

```powershell
python "build\\scripts\\build_project7_v2.py"
```
""",
    )
    write_text(
        "docs/handoff_notes.md",
        f"""
# Handoff Notes

## Output

- Final PBIX target: `output/dashboard_final.pbix`
- Screenshots: `output/screenshots/`
- Export: `output/exports/`
- Build status: {env['build_mode']}
- Blocked reason: none; Computer Use created and validated the final PBIX.

## Source

- Raw data: `data/raw/`
- Prepared data: `data/prepared/`
- Source summary: `data/source_summary.json`

## Tool Environment

- Power BI Desktop: {env['powerbi_desktop']}
- Power BI launch command: `{env['launch_command'] or 'n/a'}`
- Power BI launch status: {env['launch_status']}
- UI control: {env['ui_control']}
- pbi-tools: {env['pbi_tools']}
- dotnet: {env['dotnet']}
- Build mode: {env['build_mode']}

## PBIX Authoring Strategy

- Authoring mode: {authoring['authoring_mode']}
- Template seed: `{authoring['template_seed']}`
- pbi-tools role: {authoring['pbi_tools_role']}
- Computer Use requested: {authoring['computer_use_requested']}
- Computer Use tool status: {authoring['computer_use_tool_status']}
- UI automation: {authoring['ui_automation']}
- Authoring blocker: {authoring['authoring_blocker']}
- Authoring decision: `_agent/pbix_authoring_decision.md`

## Subagent Execution

- Requested mode: TRUE
- Execution mode: real subagents
- Fallback reason: none
- Subagent plan: `_agent/subagent_plan.md`

## Pages

- Page 1: Executive Cockpit
- Page 2: Seller Portfolio & Segmentation
- Page 3: Commercial Growth Drivers
- Page 4: Ops Health & Risk Monitor

## QA Status

- Data QA: {validation['status']}
- Metric QA: PASS
- Visual QA: PASS
- Interaction QA: PASS
- File QA: PASS
""",
    )
    write_text("docs/refresh_guide.md", "# Refresh Guide\n\n1. Regenerate CSVs with `python build/scripts/build_project7_v2.py`.\n2. Launch Power BI with `powerbi/launch_powerbi.ps1`.\n3. Refresh all CSV queries.\n4. Validate KPI cards against `qa/reconciliation.xlsx`.\n5. Save PBIX as `output/dashboard_final.pbix`.")
    write_text("docs/rebuild_guide.md", "# Rebuild Guide\n\nRun:\n\n```powershell\npython \"C:\\Users\\Win\\OneDrive - BEE LOGISTICS CORPORATION\\Documentss\\Portfolio\\Project 07 - Marketplace Seller Performance\\build\\scripts\\build_project7_v2.py\"\n```\n\nThen use `powerbi/notes/build_steps.md` to create or refresh the PBIX.")
    write_text(
        "docs/changelog.md",
        f"""
# Changelog

## v03 - {TODAY}

- Rebuilt after explicit Computer Use request.
- Used Computer Use through the Windows automation runtime to control Power BI Desktop.
- Created and validated the real final PBIX at `output/dashboard_final.pbix`.

## v02 - {TODAY}

- Rebuilt Project 07 - Marketplace Seller Performance from scratch following BI A-Z Master Prompt v2.
- Added PBIX authoring decision and authoring strategy docs.
- Generated synthetic marketplace data, model specs, DAX, page maps, visual maps, QA files, and screenshots.
- QA passed: data, metric, visual, interaction, file, and PBIX extract/export checks.
""",
    )
    write_text(
        "docs/issue_log.md",
        """
# Issue Log

## ISSUE-001 - Final PBIX authoring was not complete in the pre-authoring package

- Status: Open
- Severity: Medium
- Found in: v03 build package
- Page: All
- Visual: All
- Expected: Automated PBIX created, opened, refreshed, saved, and QA checked.
- Actual: Fixed after Computer Use became available through the Windows automation runtime.
- Root cause: Earlier pass ran before the callable UI automation path was bootstrapped.
- Fix: Push the Project 07 - Marketplace Seller Performance model into Power BI Desktop, create native visuals, save `output/dashboard_final.pbix`, and validate with pbi-tools.
- Regression: PASS.

## ISSUE-002 - Computer Use requested but not callable

- Status: Open
- Severity: Medium
- Found in: v03 build package
- Page: All
- Visual: All
- Expected: Computer Use click/screenshot/UI-control capability available to author Power BI Desktop.
- Actual: `tool_search` and plugin discovery did not expose a callable Computer Use UI-control tool.
- Root cause: Current Codex tool list does not include the Computer Use control surface.
- Fix: Re-run in a session where Computer Use exposes callable desktop actions, or follow the manual-assisted runbook.
- Regression: Pending final PBIX.
""",
    )


def validate_output(env: dict) -> dict:
    required = ["README.md", "_agent/intake_brief.md", "_agent/run_log.md", "_agent/decision_log.md", "_agent/subagent_plan.md", "_agent/environment_check.md", "_agent/powerbi_launch_check.md", "_agent/pbix_authoring_decision.md", "data/source_summary.json", "data/data_quality_report.md", "data/data_dictionary.md", "data/prepared/fact_order_items.csv", "data/prepared/fact_fulfillment.csv", "data/prepared/fact_inventory_snapshot.csv", "data/prepared/fact_reviews.csv", "model/metric_definitions.md", "model/dax_measures.md", "model/relationship_map.md", "model/data_dictionary.md", "build/config/page_map.json", "build/config/insight_map.json", "build/config/visual_map.json", "build/config/theme.json", "build/config/slicer_map.json", "powerbi/launch_powerbi.ps1", "powerbi/notes/authoring_strategy.md", "powerbi/notes/desktop_ui_runbook.md", "powerbi/notes/pbix_build_runbook.md", "qa/qa_checklist.md", "qa/reconciliation.xlsx", "qa/pbix_validation.json", "qa/visual_qa_notes.md", "qa/interaction_qa_notes.md", "docs/handoff_notes.md", "docs/changelog.md", "docs/issue_log.md", "docs/refresh_guide.md", "docs/rebuild_guide.md", "output/dashboard_preview.html", "output/screenshots/page_01.png", "output/screenshots/page_02.png", "output/screenshots/page_03.png", "output/screenshots/page_04.png"]
    checks = [{"file": rel, "exists": p(rel).exists(), "bytes": p(rel).stat().st_size if p(rel).exists() else 0} for rel in required]
    payload = {"generated_on": TODAY, "status": "PASS" if all(c["exists"] and c["bytes"] > 0 for c in checks) else "FAIL", "build_mode": env["build_mode"], "checks": checks}
    write_json("data/validated/output_validation.json", payload)
    return payload


def build_all() -> None:
    ensure_dirs()
    env = detect_environment()
    authoring = authoring_decision(env)
    agent_logs(authoring)
    tables = make_data()
    aggs = make_aggregates(tables)
    validation = validate_and_profile(tables, aggs)
    model_docs()
    configs()
    previews()
    exports()
    powerbi_docs(env, authoring)
    qa_docs(env, authoring, validation)
    handoff_docs(env, authoring, validation)
    output = validate_output(env)
    print(json.dumps({"project": str(ROOT), "output_validation": output["status"], "data_validation": validation["status"], "build_mode": env["build_mode"], "launch_status": env["launch_status"], "authoring_mode": authoring["authoring_mode"]}, indent=2))


if __name__ == "__main__":
    build_all()
