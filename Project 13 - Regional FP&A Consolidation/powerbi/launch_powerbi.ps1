$ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$pbix = Join-Path $ProjectRoot "output\dashboard_final.pbix"
$pbi = "C:\Program Files\Microsoft Power BI Desktop\bin\PBIDesktop.exe"
if (-not (Test-Path $pbix)) {
  Write-Host "dashboard_final.pbix does not exist yet. Use this project as a Power BI-ready build package."
  exit 1
}
Start-Process -FilePath $pbi -ArgumentList "`"$pbix`""
