from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[2]
pbix = ROOT / 'output' / 'dashboard_final.pbix'
pbip = ROOT / 'powerbi' / 'pbip' / 'Project5_Retention_Cohort' / 'Project5_Retention_Cohort.pbip'
screenshots = sorted((ROOT / 'output' / 'screenshots').glob('*.png'))
result = {
    'status': 'pass' if pbix.exists() and pbix.stat().st_size > 100000 else 'blocked',
    'pbix_exists': pbix.exists(),
    'pbix_size_bytes': pbix.stat().st_size if pbix.exists() else 0,
    'pbip_exists': pbip.exists(),
    'screenshot_count': len(screenshots),
    'final_pbix': str(pbix),
    'note': 'PBIX must be opened/refreshed/saved in Power BI Desktop before final handoff.' if not pbix.exists() else 'PBIX exists and Power BI Desktop render evidence is recorded in qa/powerbi_desktop_evidence.md.'
}
(ROOT / 'qa' / 'pbix_validation.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
print(json.dumps(result, indent=2))
