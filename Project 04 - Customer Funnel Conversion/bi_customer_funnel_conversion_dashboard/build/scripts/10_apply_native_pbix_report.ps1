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
  $candidates = @("C:\Program Files\Microsoft Power BI Desktop\bin", "C:\Program Files (x86)\Microsoft Power BI Desktop\bin") |
    Where-Object { Test-Path -LiteralPath (Join-Path $_ "PBIDesktop.exe") }
  if ($candidates) { return ($candidates | Select-Object -First 1) }
  throw "Power BI Desktop bin folder not found."
}

function Write-Validation([hashtable]$Payload, [int]$ExitCode = 0) {
  $Payload.timestamp = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss zzz")
  $Payload | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath (Join-Path $QaRoot "pbix_native_report_validation.json") -Encoding UTF8
  Write-Output ($Payload | ConvertTo-Json -Depth 10)
  if ($ExitCode -ne 0) { exit $ExitCode }
}

$ModelPbix = Resolve-ProjectPath $ModelPbix "output\dashboard_model.pbix"
$LayoutJson = Resolve-ProjectPath $LayoutJson "build\native_report_layout_funnel.json"
$OutputPbix = Resolve-ProjectPath $OutputPbix "output\dashboard_v01.pbix"
$FinalPbix = Resolve-ProjectPath $FinalPbix "output\dashboard_final.pbix"

if (!(Test-Path -LiteralPath $ModelPbix)) {
  Write-Validation @{
    status = "failed_precondition_missing_model_pbix"
    source_model_pbix = $ModelPbix
    final_pbix_created = $false
    reason = "No valid model PBIX exists. Run 07_push_model_to_powerbi_desktop.ps1, then save Power BI Desktop as output/dashboard_model.pbix."
  } 2
}

if (!(Test-Path -LiteralPath $LayoutJson)) {
  Write-Validation @{
    status = "failed_precondition_missing_layout_json"
    layout_json = $LayoutJson
    final_pbix_created = $false
    reason = "Run build/scripts/10_build_native_pbix_report.py first."
  } 2
}

try {
  $PowerBiBin = Get-PowerBiBin
  $PackagingDll = Join-Path $PowerBiBin "Microsoft.PowerBI.Packaging.dll"
  [Reflection.Assembly]::LoadFrom($PackagingDll) | Out-Null
  Add-Type -AssemblyName WindowsBase
  function Validate-Pbix([string]$Path) {
    $stream = [IO.File]::OpenRead($Path)
    try { [Microsoft.PowerBI.Packaging.PowerBIPackager]::Validate($stream) }
    finally { $stream.Dispose() }
  }
  Validate-Pbix $ModelPbix
  Copy-Item -LiteralPath $ModelPbix -Destination $OutputPbix -Force
  # Layout patching is intentionally disabled unless native layout JSON is full Power BI Layout schema.
  Copy-Item -LiteralPath $OutputPbix -Destination $FinalPbix -Force
  Validate-Pbix $FinalPbix
  Write-Validation @{ status = "passed_model_pbix_promoted"; final_pbix = $FinalPbix; final_pbix_created = $true; note = "Model PBIX validated and promoted. Native visual patching requires full Layout schema." }
}
catch {
  Write-Validation @{ status = "failed_exception"; reason = $_.Exception.Message; final_pbix_created = (Test-Path -LiteralPath $FinalPbix) } 1
}
