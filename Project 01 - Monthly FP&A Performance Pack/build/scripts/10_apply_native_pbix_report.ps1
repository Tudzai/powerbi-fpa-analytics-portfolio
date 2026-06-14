param(
  [string]$ModelPbix = "C:\Users\Win\OneDrive\Codex\Portfolio\BI\Project 01 - Monthly FP&A Performance Pack\output\dashboard_model.pbix",
  [string]$LayoutJson = "C:\Users\Win\OneDrive\Codex\Portfolio\BI\Project 01 - Monthly FP&A Performance Pack\build\native_report_layout_v06.json",
  [string]$OutputPbix = "C:\Users\Win\OneDrive\Codex\Portfolio\BI\Project 01 - Monthly FP&A Performance Pack\output\dashboard_v02.pbix",
  [string]$FinalPbix = "C:\Users\Win\OneDrive\Codex\Portfolio\BI\Project 01 - Monthly FP&A Performance Pack\output\dashboard_final.pbix"
)

$ErrorActionPreference = "Stop"

$ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..")
$OutputRoot = Join-Path $ProjectRoot "output"
$QaRoot = Join-Path $ProjectRoot "qa"
New-Item -ItemType Directory -Force -Path $OutputRoot, $QaRoot | Out-Null

$PowerBiBin = "C:\Program Files\WindowsApps\Microsoft.MicrosoftPowerBIDesktop_2.154.1260.0_x64__8wekyb3d8bbwe\bin"
$PackagingDll = Join-Path $PowerBiBin "Microsoft.PowerBI.Packaging.dll"
if (!(Test-Path -LiteralPath $PackagingDll)) {
  throw "Power BI Packaging assembly not found: $PackagingDll"
}
if (!(Test-Path -LiteralPath $ModelPbix)) {
  throw "Model PBIX not found: $ModelPbix"
}
if (!(Test-Path -LiteralPath $LayoutJson)) {
  throw "Layout JSON not found: $LayoutJson"
}

[Reflection.Assembly]::LoadFrom($PackagingDll) | Out-Null
Add-Type -AssemblyName WindowsBase

function Validate-Pbix([string]$Path) {
  $stream = [IO.File]::OpenRead($Path)
  try {
    [Microsoft.PowerBI.Packaging.PowerBIPackager]::Validate($stream)
  }
  finally {
    $stream.Dispose()
  }
}

Copy-Item -LiteralPath $ModelPbix -Destination $OutputPbix -Force

$layout = Get-Content -LiteralPath $LayoutJson -Raw | ConvertFrom-Json
$layoutText = $layout | ConvertTo-Json -Depth 100 -Compress
$layoutBytes = [Text.Encoding]::Unicode.GetBytes($layoutText)

$package = [System.IO.Packaging.Package]::Open($OutputPbix, [IO.FileMode]::Open, [IO.FileAccess]::ReadWrite)
try {
  $layoutUri = New-Object System.Uri("/Report/Layout", [System.UriKind]::Relative)
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
  if ($package.PartExists($securityUri)) {
    $package.DeletePart($securityUri)
  }
}
finally {
  $package.Close()
}

Validate-Pbix $OutputPbix
Copy-Item -LiteralPath $OutputPbix -Destination $FinalPbix -Force
Validate-Pbix $FinalPbix

$metadata = [ordered]@{
  generated_at = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
  version = "v06-native-visuals"
  source_model_pbix = $ModelPbix
  layout_json = $LayoutJson
  output_pbix = $OutputPbix
  final_pbix = $FinalPbix
  pages = @($layout.sections | ForEach-Object { $_.displayName })
  visual_containers = ($layout.sections | ForEach-Object { $_.visualContainers.Count } | Measure-Object -Sum).Sum
  commentary_removed = $true
  validation = "PowerBIPackager.Validate passed for output and final PBIX"
  known_scope = "Native Power BI visual containers generated from the existing semantic model; no commentary text blocks on dashboard canvas."
}

$metadata | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath (Join-Path $QaRoot "pbix_native_report_validation_v06.json") -Encoding UTF8
Write-Output ($metadata | ConvertTo-Json -Depth 10)
