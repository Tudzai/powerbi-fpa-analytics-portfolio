# Rebuild Guide

Recommended command from project root:

```powershell
& "C:\Users\Win\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" .\build\scripts\00_create_project_structure.py
```

Rebuild output:

- Regenerates synthetic raw data.
- Regenerates prepared star schema CSV files.
- Regenerates validation extracts and reconciliation workbook.
- Regenerates model docs, config files, QA notes, preview HTML, PNG, and PDF.

PBIX must still be built in Power BI Desktop unless a supported automated PBIX build path is added.
