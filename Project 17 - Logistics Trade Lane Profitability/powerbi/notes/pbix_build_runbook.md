# Rebuild Guide

```powershell
cd "C:\Users\Win\OneDrive\Codex\Portfolio\BI\Project 17 - Logistics Trade Lane Profitability"
python tools/build_project17.py
./powerbi/prepare_seed_pbix.ps1
Start-Process -FilePath "C:\Program Files\Microsoft Power BI Desktop\bin\PBIDesktop.exe" -ArgumentList "`"C:\Users\Win\OneDrive\Codex\Portfolio\BI\Project 17 - Logistics Trade Lane Profitability\output\dashboard_model_seed.pbix`""
./powerbi/push_model_bim_to_desktop.ps1
# Save the exact seed PBIX in Desktop, then:
./powerbi/apply_native_layout_to_pbix.ps1
```
