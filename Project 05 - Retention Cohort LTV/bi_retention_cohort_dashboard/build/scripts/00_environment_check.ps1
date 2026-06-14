$ErrorActionPreference = "Continue"

$ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..")
$AgentDir = Join-Path $ProjectRoot "_agent"
$PowerBiDir = Join-Path $ProjectRoot "powerbi"
New-Item -ItemType Directory -Force -Path $AgentDir, $PowerBiDir | Out-Null

$pathCommand = Get-Command PBIDesktop.exe -ErrorAction SilentlyContinue
$programFilesCandidates = @(
  "C:\Program Files\Microsoft Power BI Desktop\bin\PBIDesktop.exe",
  "C:\Program Files (x86)\Microsoft Power BI Desktop\bin\PBIDesktop.exe"
)
$programFilesExe = $programFilesCandidates | Where-Object { Test-Path $_ } | Select-Object -First 1
$storeApp = Get-StartApps | Where-Object {
  $_.Name -like "*Power BI Desktop*" -or $_.AppID -like "*PowerBI*"
} | Select-Object -First 1

$pbiTools = Get-Command pbi-tools -ErrorAction SilentlyContinue
if (-not $pbiTools) {
  $pbiTools = Get-Command pbi-tools.exe -ErrorAction SilentlyContinue
}
$dotnet = Get-Command dotnet -ErrorAction SilentlyContinue
$tabularEditor = Get-Command TabularEditor.exe -ErrorAction SilentlyContinue

$wingetOutput = $null
try {
  $wingetOutput = (winget list --name "Power BI" 2>$null) -join "`n"
} catch {
  $wingetOutput = "winget unavailable or timed out"
}

$pbiToolsInfo = $null
if ($pbiTools) {
  try {
    $pbiToolsInfo = (pbi-tools info 2>&1) -join "`n"
  } catch {
    $pbiToolsInfo = $_.Exception.Message
  }
}

$detectedPowerBI = "not found"
$launchCommand = $null
if ($pathCommand) {
  $detectedPowerBI = "Power BI Desktop EXE available"
  $launchCommand = "Start-Process '$($pathCommand.Source)'"
} elseif ($programFilesExe) {
  $detectedPowerBI = "Power BI Desktop EXE available"
  $launchCommand = "Start-Process '$programFilesExe'"
} elseif ($storeApp) {
  $detectedPowerBI = "Power BI Desktop Microsoft Store available"
  $launchCommand = "Start-Process 'shell:AppsFolder\$($storeApp.AppID)'"
}

$buildMode = "blocked_for_pbix_build"
if ($detectedPowerBI -ne "not found") {
  $buildMode = "assisted_powerbi_desktop"
}
if ($detectedPowerBI -ne "not found" -and $pbiTools) {
  $buildMode = "pbit_or_pbip_ready"
}

$result = [ordered]@{
  Timestamp = (Get-Date).ToString("s")
  DetectedPowerBI = $detectedPowerBI
  PathCommand = if ($pathCommand) { $pathCommand.Source } else { $null }
  ProgramFilesExe = $programFilesExe
  StoreAppName = if ($storeApp) { $storeApp.Name } else { $null }
  StoreAppID = if ($storeApp) { $storeApp.AppID } else { $null }
  PbiTools = [bool]$pbiTools
  PbiToolsPath = if ($pbiTools) { $pbiTools.Source } else { $null }
  DotnetInPath = [bool]$dotnet
  DotnetPath = if ($dotnet) { $dotnet.Source } else { $null }
  TabularEditorInPath = [bool]$tabularEditor
  TabularEditorPath = if ($tabularEditor) { $tabularEditor.Source } else { $null }
  BuildMode = $buildMode
  LaunchCommand = $launchCommand
}

$json = $result | ConvertTo-Json -Depth 6
$json | Set-Content -Encoding UTF8 (Join-Path $AgentDir "environment_check.json")

$launcherPath = Join-Path $PowerBiDir "launch_powerbi.ps1"
@"
`$ErrorActionPreference = "Continue"
if ($($pathCommand -ne $null -or $programFilesExe -ne $null)) {
  `$exe = "$($(if ($pathCommand) { $pathCommand.Source } else { $programFilesExe }))"
  Start-Process -FilePath `$exe
} elseif ("$($storeApp.AppID)") {
  Start-Process 'shell:AppsFolder\$($storeApp.AppID)'
} else {
  Write-Error "Power BI Desktop was not detected by environment check."
}
"@ | Set-Content -Encoding UTF8 $launcherPath

$md = @"
# Environment Check

Generated: $($result.Timestamp)

## Detected Environment

- Power BI Desktop: $($result.DetectedPowerBI)
- Path command: $($result.PathCommand)
- Program Files EXE: $($result.ProgramFilesExe)
- Microsoft Store app: $($result.StoreAppName)
- Store AppID: $($result.StoreAppID)
- pbi-tools: $($result.PbiTools) $($result.PbiToolsPath)
- dotnet in PATH: $($result.DotnetInPath) $($result.DotnetPath)
- Tabular Editor in PATH: $($result.TabularEditorInPath) $($result.TabularEditorPath)
- Build mode from environment: $($result.BuildMode)
- Launch command: $($result.LaunchCommand)

## pbi-tools info

````text
$pbiToolsInfo
````

## winget Power BI check

````text
$wingetOutput
````
"@
$md | Set-Content -Encoding UTF8 (Join-Path $AgentDir "environment_check.md")

$json
