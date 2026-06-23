import json
import hashlib
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
p=ROOT/'output'/'dashboard_final.pbix'
native_path = ROOT / 'qa' / 'pbix_native_report_validation.json'
native = json.loads(native_path.read_text(encoding='utf-8-sig')) if native_path.exists() else {}
desktop_path = ROOT / 'qa' / 'desktop_open_check.json'
desktop = json.loads(desktop_path.read_text(encoding='utf-8-sig')) if desktop_path.exists() else {}

def sha256(path: Path) -> str | None:
    if not path.exists():
        return None
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest().upper()

current_sha = sha256(p)
package_ok = p.exists() and p.stat().st_size > 100000
screenshots = desktop.get('screenshots', [])
screenshots_ok = bool(screenshots) and all((ROOT / s).exists() for s in screenshots)
desktop_pass = (
    desktop.get('status') == 'passed'
    and desktop.get('pbix_sha256') == current_sha
    and desktop.get('visual_error_count') == 0
    and screenshots_ok
)
pending_gap = 'Open output/dashboard_final.pbix in Power BI Desktop and capture fresh screenshots for all 4 pages before claiming fresh Desktop visual QA pass.'

r={
    'status':'desktop_open_check_passed' if package_ok and desktop_pass else ('package_pass_desktop_open_check_pending' if package_ok else 'fail'),
    'pbix_exists':p.exists(),
    'pbix_size_bytes':p.stat().st_size if p.exists() else 0,
    'sha256': current_sha,
    'build_route':'SCRIPTED_DESKTOP_PBIX',
    'native_package_validation_status': native.get('status'),
    'pages': native.get('pages', []),
    'visual_containers': native.get('visual_containers'),
    'desktop_open_check':'passed' if desktop_pass else 'not_rerun_after_v3_patch',
    'desktop_checked_at': desktop.get('checked_at') if desktop_pass else None,
    'visual_error_count': 0 if desktop_pass else None,
    'screenshots': screenshots if desktop_pass else [],
    'known_gap': None if desktop_pass else pending_gap
}
(ROOT/'qa'/'pbix_final_validation.json').write_text(json.dumps(r,indent=2),encoding='utf-8')
(ROOT/'qa'/'pbix_validation.json').write_text(json.dumps({
    'final_pbix_path': str(p),
    'opened_in_power_bi_desktop': bool(desktop_pass),
    'saved_after_open': False,
    'page_count': len(r['pages']),
    'visual_count': r['visual_containers'],
    'visual_error_count': r['visual_error_count'],
    'screenshots': r['screenshots'],
    'qa_status': r['status'],
    'native_package_validation': r['native_package_validation_status'],
    'build_route': r['build_route'],
    'known_issues': [] if desktop_pass else [r['known_gap']],
}, indent=2), encoding='utf-8')
print(json.dumps(r,indent=2))
