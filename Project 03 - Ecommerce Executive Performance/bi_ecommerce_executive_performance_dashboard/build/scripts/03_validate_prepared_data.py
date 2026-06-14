from pathlib import Path
import pandas as pd

root = Path(__file__).resolve().parents[2]
checks = pd.read_csv(root / "data" / "validated" / "data_quality_checks.csv")
print(checks.to_string(index=False))
