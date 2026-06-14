# Rebuild Guide

```powershell
$py = 'C:\Users\Win\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
& $py 'build\scripts\00_build_project4.py'
& $py 'build\scripts\11_render_complete_dashboard.py'
```

Optional native PBIX path:

```powershell
.\powerbi\launch_powerbi.ps1
.\build\scripts\07_push_model_to_powerbi_desktop.ps1
.\build\scripts\08_try_save_powerbi_model_pbix.ps1
.\build\scripts\10_build_native_pbix_report.py
.\build\scripts\10_apply_native_pbix_report.ps1
```

If keyboard save automation does not create `output/dashboard_model.pbix`, use Power BI Desktop Save As manually on a clean Project 04 - Customer Funnel Conversion report layout, then rerun the final two commands.
