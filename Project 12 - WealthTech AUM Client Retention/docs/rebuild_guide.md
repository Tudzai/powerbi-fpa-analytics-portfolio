# Rebuild Guide

```powershell
$py = 'C:\Users\Win\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
& $py 'build\scripts\01_build_project.py'
.\build\scripts\00_environment_check.ps1
```

Create or copy a valid PBIX container to the Project 12 - WealthTech AUM Client Retention model path, then open it in Power BI Desktop:

```powershell
Copy-Item 'C:\Users\Win\OneDrive\Codex\Portfolio\BI\Project 11 - Neobank Growth Retention LTV\output\dashboard_model_seed.pbix' `
  'C:\Users\Win\OneDrive\Codex\Portfolio\BI\Project 12 - WealthTech AUM Client Retention\output\dashboard_model.pbix' -Force
pbi-tools launch-pbi 'C:\Users\Win\OneDrive\Codex\Portfolio\BI\Project 12 - WealthTech AUM Client Retention\output\dashboard_model.pbix'
```

Use `pbi-tools info` to get the Power BI Desktop process ID where `PbixPath` is `Project 12 - WealthTech AUM Client Retention\output\dashboard_model.pbix`, then push the model and save that window in Desktop:

```powershell
.\build\scripts\07_push_model_to_powerbi_desktop.ps1 -TargetProcessId <Project12PowerBIPid>
```

After `Ctrl+S` saves `output\dashboard_model.pbix`, patch the native report layout and validate the final package:

```powershell
.\build\scripts\10_apply_native_pbix_report.ps1
```

The portable HTML preview is:

```text
C:\Users\Win\OneDrive\Codex\Portfolio\BI\Project 12 - WealthTech AUM Client Retention\output\dashboard_preview.html
```
