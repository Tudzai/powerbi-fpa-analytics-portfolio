from pathlib import Path
import subprocess
import sys

root = Path(__file__).resolve().parents[2]
subprocess.check_call([sys.executable, str(root / "build" / "scripts" / "00_create_project_structure.py")])
