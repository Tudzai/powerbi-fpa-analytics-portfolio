$pbix = "C:\Users\Win\OneDrive\Codex\Portfolio\BI\Project 17 - Logistics Trade Lane Profitability\output\dashboard_final.pbix"
$pbi = "C:\Program Files\Microsoft Power BI Desktop\bin\PBIDesktop.exe"
if (-not (Test-Path $pbix)) {
  Write-Host "dashboard_final.pbix does not exist yet."
  exit 1
}
Start-Process -FilePath $pbi -ArgumentList "`"$pbix`""
