$ErrorActionPreference = "Continue"
$launchMethod = "not_found"
$launchCommand = $null

$exe = Get-Command PBIDesktop.exe -ErrorAction SilentlyContinue
$programFiles = @(
  "C:\Program Files\Microsoft Power BI Desktop\bin\PBIDesktop.exe",
  "C:\Program Files (x86)\Microsoft Power BI Desktop\bin\PBIDesktop.exe"
) | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1

if ($exe) {
  $launchMethod = "path"
  $launchCommand = $exe.Source
  Start-Process -FilePath $exe.Source
} elseif ($programFiles) {
  $launchMethod = "program_files"
  $launchCommand = $programFiles
  Start-Process -FilePath $programFiles
} else {
  $storeApp = Get-StartApps | Where-Object {
    $_.Name -like "*Power BI Desktop*" -or $_.AppID -like "*PowerBI*"
  } | Select-Object -First 1
  if ($storeApp) {
    $launchMethod = "microsoft_store"
    $launchCommand = "shell:AppsFolder\$($storeApp.AppID)"
    Start-Process $launchCommand
  }
}

Start-Sleep -Seconds 20
$process = Get-Process | Where-Object {
  $_.ProcessName -like "*PBIDesktop*" -or
  $_.ProcessName -like "*PowerBI*" -or
  $_.MainWindowTitle -like "*Power BI*"
} | Select-Object ProcessName, Id, MainWindowTitle

[pscustomobject]@{
  LaunchMethod = $launchMethod
  LaunchCommand = $launchCommand
  ProcessDetected = [bool]$process
  Process = $process
}
