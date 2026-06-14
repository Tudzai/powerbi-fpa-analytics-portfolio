param(
  [string]$ModelPbix = "",
  [string]$LayoutJson = "",
  [string]$OutputPbix = "",
  [string]$FinalPbix = ""
)

$ErrorActionPreference = "Stop"

$ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..")
$OutputRoot = Join-Path $ProjectRoot "output"
$QaRoot = Join-Path $ProjectRoot "qa"
New-Item -ItemType Directory -Force -Path $OutputRoot, $QaRoot | Out-Null

function Resolve-ProjectPath([string]$PathValue, [string]$DefaultRelative) {
  if ([string]::IsNullOrWhiteSpace($PathValue)) { return Join-Path $ProjectRoot $DefaultRelative }
  if ([IO.Path]::IsPathRooted($PathValue)) { return $PathValue }
  return Join-Path $ProjectRoot $PathValue
}

function Get-PowerBiBin {
  $cmd = Get-Command PBIDesktop.exe -ErrorAction SilentlyContinue
  if ($cmd) { return Split-Path -Parent $cmd.Source }
  $candidates = @(
    "C:\Program Files\Microsoft Power BI Desktop\bin",
    "C:\Program Files (x86)\Microsoft Power BI Desktop\bin"
  ) | Where-Object { Test-Path -LiteralPath (Join-Path $_ "PBIDesktop.exe") }
  if ($candidates) { return ($candidates | Select-Object -First 1) }
  $windowsApps = Get-ChildItem -Path "C:\Program Files\WindowsApps" -Filter "Microsoft.MicrosoftPowerBIDesktop_*_x64__8wekyb3d8bbwe" -Directory -ErrorAction SilentlyContinue |
    Sort-Object Name -Descending |
    Select-Object -First 1
  if ($windowsApps) {
    $bin = Join-Path $windowsApps.FullName "bin"
    if (Test-Path -LiteralPath (Join-Path $bin "Microsoft.PowerBI.Packaging.dll")) { return $bin }
  }
  throw "Power BI Desktop bin folder not found."
}

function Write-Validation([hashtable]$Payload, [int]$ExitCode = 0) {
  $Payload.timestamp = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss zzz")
  $Payload | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath (Join-Path $QaRoot "pbix_native_report_validation.json") -Encoding UTF8
  Write-Output ($Payload | ConvertTo-Json -Depth 10)
  if ($ExitCode -ne 0) { exit $ExitCode }
}

$ModelPbix = Resolve-ProjectPath $ModelPbix "output\dashboard_model_seed.pbix"
$LayoutJson = Resolve-ProjectPath $LayoutJson "build\native_report_layout_project9.json"
$OutputPbix = Resolve-ProjectPath $OutputPbix "output\dashboard_v01.pbix"
$FinalPbix = Resolve-ProjectPath $FinalPbix "output\dashboard_final.pbix"

if (!(Test-Path -LiteralPath $ModelPbix)) {
  Write-Validation @{
    status = "failed_precondition_missing_model_pbix"
    source_model_pbix = $ModelPbix
    layout_json = $LayoutJson
    final_pbix_created = $false
    reason = "No valid model PBIX exists. Open Project 09 - BNPL Credit Risk Provision seed PBIX and run 12_push_model_bim_via_tom.ps1 first."
  } 2
}

if (!(Test-Path -LiteralPath $LayoutJson)) {
  Write-Validation @{
    status = "failed_precondition_missing_layout_json"
    source_model_pbix = $ModelPbix
    layout_json = $LayoutJson
    final_pbix_created = $false
    reason = "Native report layout JSON is missing. Run build/scripts/build_project9.py first."
  } 2
}

try {
  $PowerBiBin = Get-PowerBiBin
  $PackagingDll = Join-Path $PowerBiBin "Microsoft.PowerBI.Packaging.dll"
  if (!(Test-Path -LiteralPath $PackagingDll)) {
    Write-Validation @{
      status = "failed_precondition_missing_packaging_dll"
      power_bi_bin = $PowerBiBin
      packaging_dll = $PackagingDll
      final_pbix_created = $false
      reason = "Microsoft.PowerBI.Packaging.dll was not found."
    } 2
  }

  [Reflection.Assembly]::LoadFrom($PackagingDll) | Out-Null
  Add-Type -AssemblyName WindowsBase

  function Validate-Pbix([string]$Path) {
    $stream = [IO.File]::OpenRead($Path)
    try { [Microsoft.PowerBI.Packaging.PowerBIPackager]::Validate($stream) }
    finally { $stream.Dispose() }
  }

  Validate-Pbix $ModelPbix
  Copy-Item -LiteralPath $ModelPbix -Destination $OutputPbix -Force

  $layout = Get-Content -LiteralPath $LayoutJson -Raw | ConvertFrom-Json
  $layoutText = $layout | ConvertTo-Json -Depth 100 -Compress
  $layoutBytes = [Text.Encoding]::Unicode.GetBytes($layoutText)

  $package = [System.IO.Packaging.Package]::Open($OutputPbix, [IO.FileMode]::Open, [IO.FileAccess]::ReadWrite)
  try {
    $layoutUri = New-Object System.Uri("/Report/Layout", [System.UriKind]::Relative)
    if (-not $package.PartExists($layoutUri)) { throw "The source model PBIX does not contain /Report/Layout." }
    $layoutPart = $package.GetPart($layoutUri)
    $stream = $layoutPart.GetStream([IO.FileMode]::Open, [IO.FileAccess]::ReadWrite)
    try {
      $stream.SetLength(0)
      $stream.Position = 0
      $stream.Write($layoutBytes, 0, $layoutBytes.Length)
    }
    finally {
      $stream.Dispose()
    }

    $securityUri = New-Object System.Uri("/SecurityBindings", [System.UriKind]::Relative)
    if ($package.PartExists($securityUri)) { $package.DeletePart($securityUri) }
  }
  finally {
    $package.Close()
  }

  Validate-Pbix $OutputPbix
  Copy-Item -LiteralPath $OutputPbix -Destination $FinalPbix -Force
  Validate-Pbix $FinalPbix

  Write-Validation @{
    status = "passed"
    source_model_pbix = $ModelPbix
    layout_json = $LayoutJson
    output_pbix = $OutputPbix
    final_pbix = $FinalPbix
    final_pbix_created = $true
    final_pbix_size = (Get-Item -LiteralPath $FinalPbix).Length
    pages = @($layout.sections | ForEach-Object { $_.displayName })
    visual_containers = ($layout.sections | ForEach-Object { $_.visualContainers.Count } | Measure-Object -Sum).Sum
    validation = "PowerBIPackager.Validate passed for output and final PBIX after Project 09 - BNPL Credit Risk Provision native report layout patch."
  }
}
catch {
  Write-Validation @{
    status = "failed_exception"
    source_model_pbix = $ModelPbix
    layout_json = $LayoutJson
    output_pbix = $OutputPbix
    final_pbix = $FinalPbix
    final_pbix_created = (Test-Path -LiteralPath $FinalPbix)
    reason = $_.Exception.Message
  } 1
}
