$pbix = "C:\Users\Win\OneDrive\Codex\Portfolio\BI\Project 14 - Treasury Working Capital\output\dashboard_final.pbix"
$pbi = "C:\Program Files\Microsoft Power BI Desktop\bin\PBIDesktop.exe"
if (-not (Test-Path -LiteralPath $pbix)) {
  Write-Host "dashboard_final.pbix does not exist yet. Run the native PBIX build scripts first."
  exit 1
}
Start-Process -FilePath $pbi -ArgumentList "`"$pbix`""
