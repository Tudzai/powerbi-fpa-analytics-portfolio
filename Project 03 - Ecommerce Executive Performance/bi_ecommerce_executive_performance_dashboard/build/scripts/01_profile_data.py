from pathlib import Path
import json
import pandas as pd

root = Path(__file__).resolve().parents[2]
profiles = {}
for path in sorted((root / "data" / "raw").glob("*.csv")):
    df = pd.read_csv(path)
    profiles[path.name] = {"rows": len(df), "columns": list(df.columns)}
print(json.dumps(profiles, indent=2))
