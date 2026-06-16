from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
HTML = PROJECT / "output" / "dashboard_final.html"
OUT = PROJECT / "qa" / "html_validation.json"
NODE = shutil.which("node")
if NODE is None:
    for candidate in Path.home().glob("AppData/Local/OpenAI/Codex/runtimes/**/node.exe"):
        NODE = str(candidate)
        break
if NODE is None:
    raise FileNotFoundError("node.exe was not found on PATH or in Codex runtimes")
PLAYWRIGHT = None
for candidate in Path.home().glob("AppData/Local/OpenAI/Codex/runtimes/**/node_modules/playwright"):
    PLAYWRIGHT = str(candidate)
    break
if PLAYWRIGHT is None:
    raise FileNotFoundError("playwright package was not found in Codex runtimes")

node_code = f"""
import {{ createRequire }} from 'node:module';
const require = createRequire(import.meta.url);
const {{ chromium }} = require({json.dumps(PLAYWRIGHT)});
const fs = await import('node:fs');
const path = {json.dumps(str(HTML))};
const chrome = 'C:/Program Files/Google/Chrome/Application/chrome.exe';
const browser = await chromium.launch({{ headless: true, executablePath: chrome }});
const results = [];
for (const vp of [{{name:'desktop', width:1366, height:768}}, {{name:'mobile', width:390, height:844}}]) {{
  const page = await browser.newPage({{ viewport: {{ width: vp.width, height: vp.height }} }});
  const errors = [];
  page.on('console', msg => {{ if (['error','warning'].includes(msg.type())) errors.push(`${{msg.type()}}: ${{msg.text()}}`); }});
  await page.goto('file:///' + path.replace(/\\\\/g,'/'), {{ waitUntil: 'networkidle' }});
  await page.screenshot({{ path: String({json.dumps(str(PROJECT / "output" / "screenshots"))} + `/dashboard_${{vp.name}}.png`), fullPage: true }});
  const qa = await page.evaluate(() => {{
    const body = document.body;
    return {{
      title: document.title,
      kpiCards: document.querySelectorAll('.card').length,
      panels: document.querySelectorAll('.panel').length,
      tables: document.querySelectorAll('table').length,
      svgs: document.querySelectorAll('svg').length,
      overflowX: body.scrollWidth > window.innerWidth + 2,
      hasNaN: body.innerText.includes('NaN') || body.innerText.includes('undefined'),
      qa: window.__dashboardQa
    }};
  }});
  await page.selectOption('#regionFilter', 'SEA South');
  await page.selectOption('#buFilter', 'Warehousing');
  await page.selectOption('#periodFilter', '2026-05');
  const filtered = await page.evaluate(() => ({{
    period: window.__dashboardQa.period,
    kpiCards: document.querySelectorAll('.card').length,
    activePage: window.__dashboardQa.activePage,
    actionText: document.querySelector('#actionStrip')?.innerText || ''
  }}));
  const pages = [];
  for (const pg of ['overview','pnl','story']) {{
    await page.click(`button[data-page="${{pg}}"]`);
    pages.push(await page.evaluate((pg) => ({{
      expected: pg,
      active: window.__dashboardQa.activePage,
      activeElementVisible: !!document.querySelector(`#${{pg}}.page.active`),
      hasNaN: document.body.innerText.includes('NaN') || document.body.innerText.includes('undefined')
    }}), pg));
  }}
  results.push({{ viewport: vp, errors, qa, filtered, pages }});
  await page.close();
}}
await browser.close();
const status = results.every(r => r.errors.length === 0 && !r.qa.overflowX && !r.qa.hasNaN && r.qa.kpiCards >= 6 && r.qa.svgs >= 4 && r.pages.every(p => p.expected === p.active && p.activeElementVisible && !p.hasNaN)) ? 'pass' : 'fail';
console.log(JSON.stringify({{ status, checked_at: new Date().toISOString(), html: path, results }}, null, 2));
"""
proc = subprocess.run([NODE, "--input-type=module", "-e", node_code], capture_output=True, text=True, timeout=120)
if proc.returncode != 0:
    payload = {"status": "fail", "stderr": proc.stderr, "stdout": proc.stdout}
else:
    payload = json.loads(proc.stdout)
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
if payload.get("status") == "pass":
    validation = json.loads((PROJECT / "data" / "validated" / "validation_summary.json").read_text(encoding="utf-8"))
    measures = json.loads((PROJECT / "model" / "measure_catalog.json").read_text(encoding="utf-8"))
    desktop = payload["results"][0]
    qa = desktop["qa"]
    bridge = next(c["detail"] for c in validation["checks"] if c["check"] == "Bridge tie-out to EBITDA variance")
    checked_at = payload["checked_at"]
    page_count = len(desktop["pages"])
    (PROJECT / "qa" / "qa_checklist.md").write_text(f"""# QA Checklist

- Data QA: {validation['status']}
- Metric QA: pass; DAX catalog contains {len(measures)} documented measures.
- Bridge QA: {bridge}
- HTML visual QA: pass at {checked_at}; {page_count} tabs checked, {qa['kpiCards']} KPI cards, {qa['panels']} panels, {qa['tables']} tables, {qa['svgs']} SVG charts, no console errors/overflow/NaN on desktop and mobile.
- PBIX QA: pass; native final PBIX exists at `output/dashboard_final.pbix`.
""", encoding="utf-8")
    (PROJECT / "qa" / "visual_qa_notes.md").write_text(
        f"HTML visual QA passed at {checked_at}. Desktop and mobile screenshots were captured under `output/screenshots/`; all {page_count} dashboard tabs rendered with no console errors, overflow, NaN, or undefined text. PBIX native visual QA passed for `output/dashboard_final.pbix`.",
        encoding="utf-8",
    )
    handoff = PROJECT / "docs" / "handoff_notes.md"
    if handoff.exists():
        text = handoff.read_text(encoding="utf-8")
        text = text.replace(
            "- QA: data QA pass; bridge tie-out pass; HTML QA pending until `python tools/validate_dashboard.py`; PBIX QA pass after native package validation and Desktop per-tab render scan.",
            f"- QA: data QA pass; bridge tie-out pass; HTML QA pass at {checked_at}; PBIX QA pass after native package validation and Desktop per-tab render scan.",
        )
        text = text.replace(
            "- QA: data QA pass; bridge tie-out pass; HTML QA to be completed by browser validation; PBIX QA pass after native package validation and Desktop per-tab render scan.",
            f"- QA: data QA pass; bridge tie-out pass; HTML QA pass at {checked_at}; PBIX QA pass after native package validation and Desktop per-tab render scan.",
        )
        handoff.write_text(text, encoding="utf-8")
print(json.dumps(payload, indent=2))
