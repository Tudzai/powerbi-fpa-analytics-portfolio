param(
  [string]$UiControlStatus = "unknown",
  [string]$ComputerUseEvidence = "not recorded"
)

$ErrorActionPreference = "Continue"
$ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..")
$AgentDir = Join-Path $ProjectRoot "_agent"
New-Item -ItemType Directory -Force -Path $AgentDir | Out-Null

$exe = Get-Command PBIDesktop.exe -ErrorAction SilentlyContinue
$programFiles = @(
  "C:\Program Files\Microsoft Power BI Desktop\bin\PBIDesktop.exe",
  "C:\Program Files (x86)\Microsoft Power BI Desktop\bin\PBIDesktop.exe"
) | Where-Object { Test-Path $_ } | Select-Object -First 1
$storeApp = Get-StartApps | Where-Object {
  $_.Name -like "*Power BI Desktop*" -or $_.AppID -like "*PowerBI*"
} | Select-Object -First 1

$launchMethod = "not_needed"
$launchCommand = $null
$existing = Get-Process | Where-Object {
  $_.ProcessName -like "*PBIDesktop*" -or $_.MainWindowTitle -like "*Power BI*"
}

if (-not $existing) {
  if ($exe) {
    $launchMethod = "path"
    $launchCommand = $exe.Source
    Start-Process -FilePath $exe.Source
  } elseif ($programFiles) {
    $launchMethod = "program_files"
    $launchCommand = $programFiles
    Start-Process -FilePath $programFiles
  } elseif ($storeApp) {
    $launchMethod = "microsoft_store"
    $launchCommand = "shell:AppsFolder\$($storeApp.AppID)"
    Start-Process $launchCommand
  } else {
    $launchMethod = "not_found"
  }
  Start-Sleep -Seconds 12
}

$process = Get-Process | Where-Object {
  $_.ProcessName -like "*PBIDesktop*" -or $_.MainWindowTitle -like "*Power BI*"
} | Select-Object ProcessName, Id, MainWindowTitle

$launchStatus = if ($process) { "launch_verified" } elseif ($launchMethod -eq "not_found") { "launch_failed" } else { "launch_unknown" }
$buildStatusAfterLaunch = if ($launchStatus -eq "launch_verified" -and $UiControlStatus -eq "ui_control_available") {
  "desktop_available_for_ui_authoring"
} elseif ($launchStatus -eq "launch_verified") {
  "launch_verified_assisted_build_pending"
} else {
  "blocked_for_powerbi_launch"
}

$result = [ordered]@{
  Timestamp = (Get-Date).ToString("s")
  LaunchMethod = $launchMethod
  LaunchCommand = $launchCommand
  LaunchStatus = $launchStatus
  UiControl = $UiControlStatus
  ComputerUseEvidence = $ComputerUseEvidence
  BuildStatusAfterLaunch = $buildStatusAfterLaunch
  ProcessCount = @($process).Count
  Process = $process
}

$result | ConvertTo-Json -Depth 6 | Set-Content -Encoding UTF8 (Join-Path $AgentDir "powerbi_launch_check.json")

$md = @"
# Power BI Launch Check

Generated: $($result.Timestamp)

- Launch method: $($result.LaunchMethod)
- Launch command: $($result.LaunchCommand)
- Launch status: $($result.LaunchStatus)
- UI control: $($result.UiControl)
- Computer Use evidence: $($result.ComputerUseEvidence)
- Build status after launch: $($result.BuildStatusAfterLaunch)
- Process count: $($result.ProcessCount)

## Process

````json
$($result.Process | ConvertTo-Json -Depth 6)
````
"@
$md | Set-Content -Encoding UTF8 (Join-Path $AgentDir "powerbi_launch_check.md")

$result | ConvertTo-Json -Depth 6
