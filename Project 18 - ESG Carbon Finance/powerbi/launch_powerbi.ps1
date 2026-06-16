$ErrorActionPreference = 'Stop'
$pbi = 'C:\Program Files\Microsoft Power BI Desktop\bin\PBIDesktop.exe'
if (-not (Test-Path $pbi)) {
  throw 'Power BI Desktop EXE not found.'
}
Start-Process -FilePath $pbi
Write-Host 'Power BI Desktop launched. Build final PBIX at: C:\Users\Win\OneDrive\Codex\Portfolio\BI\Project 18 - ESG Carbon Finance\output\dashboard_final.pbix'
