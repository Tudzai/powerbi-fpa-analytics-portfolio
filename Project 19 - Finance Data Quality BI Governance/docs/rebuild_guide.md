# Rebuild Guide

Use a Python environment with `pandas` and `numpy`. Verified local command:

```powershell
cd "C:\Users\Win\OneDrive\Codex\Portfolio\BI\Project 19 - Finance Data Quality BI Governance"
& "C:\Users\Win\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" build\scripts\build_project19.py
```

Portable command, if your default Python has the required packages:

```powershell
python build\scripts\build_project19.py
```

The script rebuilds synthetic CSV data, model docs, DAX measures, report layout, PBIP files, QA scaffolding, and the HTML preview.
