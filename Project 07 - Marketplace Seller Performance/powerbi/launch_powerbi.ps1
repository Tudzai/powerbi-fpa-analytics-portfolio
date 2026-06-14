$ErrorActionPreference = "Continue"
$launchCommand = "C:\Program Files\Microsoft Power BI Desktop\bin\PBIDesktop.exe"
if ([string]::IsNullOrWhiteSpace($launchCommand)) {
  Write-Output "Power BI Desktop launch command not found."
  exit 1
}
Start-Process $launchCommand
Start-Sleep -Seconds 12
Get-Process | Where-Object {
  $_.ProcessName -like "*PBIDesktop*" -or
  $_.ProcessName -like "*PowerBI*" -or
  $_.MainWindowTitle -like "*Power BI*"
} | Select-Object ProcessName, Id, MainWindowTitle
