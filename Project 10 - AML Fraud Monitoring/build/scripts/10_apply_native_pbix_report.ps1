param(
  [string]$ProjectRoot = "C:\Users\Win\OneDrive\Codex\Portfolio\BI\Project 10 - AML Fraud Monitoring",
  [string]$ModelPbix = "C:\Users\Win\OneDrive\Codex\Portfolio\BI\Project 10 - AML Fraud Monitoring\output\dashboard_model.pbix",
  [string]$LayoutJson = "C:\Users\Win\OneDrive\Codex\Portfolio\BI\Project 10 - AML Fraud Monitoring\build\native_report_layout_aml.json",
  [string]$OutputPbix = "C:\Users\Win\OneDrive\Codex\Portfolio\BI\Project 10 - AML Fraud Monitoring\output\dashboard_v01.pbix",
  [string]$FinalPbix = "C:\Users\Win\OneDrive\Codex\Portfolio\BI\Project 10 - AML Fraud Monitoring\output\dashboard_final.pbix"
)

$ErrorActionPreference = "Stop"

$OutputRoot = Join-Path $ProjectRoot "output"
$QaRoot = Join-Path $ProjectRoot "qa"
New-Item -ItemType Directory -Force -Path $OutputRoot, $QaRoot | Out-Null

function Resolve-PowerBiBin {
  $candidates = @(
    "C:\Program Files\Microsoft Power BI Desktop\bin",
    "C:\Program Files (x86)\Microsoft Power BI Desktop\bin"
  )
  foreach ($candidate in $candidates) {
    if (Test-Path -LiteralPath (Join-Path $candidate "Microsoft.PowerBI.Packaging.dll")) { return $candidate }
  }
  $storeBins = Get-ChildItem -LiteralPath "C:\Program Files\WindowsApps" -Directory -Filter "Microsoft.MicrosoftPowerBIDesktop_*_x64__8wekyb3d8bbwe" -ErrorAction SilentlyContinue |
    Sort-Object Name -Descending |
    ForEach-Object { Join-Path $_.FullName "bin" }
  foreach ($candidate in $storeBins) {
    if (Test-Path -LiteralPath (Join-Path $candidate "Microsoft.PowerBI.Packaging.dll")) { return $candidate }
  }
  throw "Power BI Packaging assembly folder not found."
}

$PowerBiBin = Resolve-PowerBiBin
$PackagingDll = Join-Path $PowerBiBin "Microsoft.PowerBI.Packaging.dll"
if (!(Test-Path -LiteralPath $ModelPbix)) { throw "Model PBIX not found: $ModelPbix" }
if (!(Test-Path -LiteralPath $LayoutJson)) { throw "Layout JSON not found: $LayoutJson" }

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
  if (!$package.PartExists($layoutUri)) { throw "PBIX does not contain /Report/Layout." }
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

$visualTypeCounts = @{}
foreach ($section in $layout.sections) {
  foreach ($visual in $section.visualContainers) {
    $type = $visual.visual.visualType
    if (!$visualTypeCounts.ContainsKey($type)) { $visualTypeCounts[$type] = 0 }
    $visualTypeCounts[$type] += 1
  }
}

$metadata = [ordered]@{
  generated_at = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
  project_root = $ProjectRoot
  source_model_pbix = $ModelPbix
  layout_json = $LayoutJson
  output_pbix = $OutputPbix
  final_pbix = $FinalPbix
  pages = @($layout.sections | ForEach-Object { $_.displayName })
  visual_containers = ($layout.sections | ForEach-Object { $_.visualContainers.Count } | Measure-Object -Sum).Sum
  visual_type_counts = $visualTypeCounts
  validation = "PowerBIPackager.Validate passed for output and final PBIX"
  security_bindings_removed = $true
}

$metadata | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath (Join-Path $QaRoot "pbix_native_report_validation.json") -Encoding UTF8
$metadata | ConvertTo-Json -Depth 10
