$pbip = "C:\Users\Win\OneDrive\Codex\Portfolio\BI\Project 19 - Finance Data Quality BI Governance\output\powerbi_project\Finance_Data_Quality_BI_Governance.pbip"
$pbi = "C:\Program Files\Microsoft Power BI Desktop\bin\PBIDesktop.exe"
if (!(Test-Path -LiteralPath $pbip)) { throw "PBIP not found: $pbip" }
if (!(Test-Path -LiteralPath $pbi)) {
  $cmd = Get-Command PBIDesktop.exe -ErrorAction SilentlyContinue
  if (!$cmd) { throw "Power BI Desktop executable not found." }
  $pbi = $cmd.Source
}
Start-Process -FilePath $pbi -ArgumentList "`"$pbip`""
Write-Host "Opened Project 19 PBIP. Save final PBIX to: C:\Users\Win\OneDrive\Codex\Portfolio\BI\Project 19 - Finance Data Quality BI Governance\output\dashboard_final.pbix"
