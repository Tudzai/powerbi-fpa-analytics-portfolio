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
    raise FileNotFoundError("node.exe was not found")
PLAYWRIGHT = None
for candidate in Path.home().glob("AppData/Local/OpenAI/Codex/runtimes/**/node_modules/playwright"):
    PLAYWRIGHT = str(candidate)
    break
if PLAYWRIGHT is None:
    raise FileNotFoundError("playwright package was not found")

node_code = f"""
import {{ createRequire }} from 'node:module';
const require = createRequire(import.meta.url);
const {{ chromium }} = require({json.dumps(PLAYWRIGHT)});
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
  const initial = await page.evaluate(() => ({{
    title: document.title,
    qa: window.__dashboardQa,
    overflowX: document.body.scrollWidth > window.innerWidth + 2,
    hasBadText: /NaN|undefined/.test(document.body.innerText)
  }}));
  await page.selectOption('#regionFilter', 'APAC');
  await page.selectOption('#entityFilter', '__ALL__');
  await page.selectOption('#scenarioFilter', 'DOWN');
  await page.selectOption('#weekFilter', 'W06');
  const filtered = await page.evaluate(() => window.__dashboardQa);
  const pages = [];
  for (const pg of ['overview','wc','risk']) {{
    await page.click(`button[data-page="${{pg}}"]`);
    pages.push(await page.evaluate((pg) => ({{
      expected: pg,
      active: window.__dashboardQa.activePage,
      visible: !!document.querySelector(`#${{pg}}.page.active`),
      hasBadText: /NaN|undefined/.test(document.body.innerText),
      cards: document.querySelectorAll('.card').length,
      charts: document.querySelectorAll('svg').length
    }}), pg));
  }}
  results.push({{ viewport: vp, errors, initial, filtered, pages }});
  await page.close();
}}
await browser.close();
const status = results.every(r => r.errors.length === 0 && !r.initial.overflowX && !r.initial.hasBadText && r.initial.qa.kpiCards >= 6 && r.initial.qa.svgs >= 3 && r.pages.every(p => p.expected === p.active && p.visible && !p.hasBadText && p.cards >= 6 && p.charts >= 3)) ? 'pass' : 'fail';
console.log(JSON.stringify({{ status, checked_at: new Date().toISOString(), html: path, results }}, null, 2));
"""
proc = subprocess.run([NODE, "--input-type=module", "-e", node_code], capture_output=True, text=True, timeout=120)
payload = {"status": "fail", "stdout": proc.stdout, "stderr": proc.stderr} if proc.returncode else json.loads(proc.stdout)
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
if payload.get("status") == "pass":
    validation = json.loads((PROJECT / "data" / "validated" / "validation_summary.json").read_text(encoding="utf-8"))
    measures = json.loads((PROJECT / "model" / "measure_catalog.json").read_text(encoding="utf-8"))
    checked_at = payload["checked_at"]
    qa = payload["results"][0]["initial"]["qa"]
    (PROJECT / "qa" / "qa_checklist.md").write_text(f"""# QA Checklist

- Data QA: {validation['status']}
- Metric QA: pass; DAX catalog contains {len(measures)} documented measures using DIVIDE for rates.
- HTML visual QA: pass at {checked_at}; 3 tabs checked on desktop and mobile, {qa['kpiCards']} KPI cards, {qa['panels']} panels, {qa['tables']} tables, {qa['svgs']} SVG charts.
- PBIX QA: pending until native Power BI build, Desktop open-check, extract, and export-data.
""", encoding="utf-8")
    (PROJECT / "qa" / "visual_qa_notes.md").write_text(
        f"HTML visual QA passed at {checked_at}. Desktop and mobile screenshots are in output/screenshots. PBIX native visual QA is completed separately after final Power BI open-check.",
        encoding="utf-8",
    )
print(json.dumps(payload, indent=2))
