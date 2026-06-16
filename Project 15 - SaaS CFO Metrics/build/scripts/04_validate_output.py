from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[2]
p=ROOT/'output'/'dashboard_final.pbix'
r={'status':'pass' if p.exists() and p.stat().st_size>100000 else 'fail','pbix_exists':p.exists(),'pbix_size_bytes':p.stat().st_size if p.exists() else 0}
(ROOT/'qa'/'pbix_final_validation.json').write_text(json.dumps(r,indent=2),encoding='utf-8')
print(json.dumps(r,indent=2))
