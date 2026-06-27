param(
  [string]$SeedTemplate,
  [string]$TargetPbix
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
if ([string]::IsNullOrWhiteSpace($SeedTemplate)) {
  $SeedTemplate = Join-Path (Split-Path $ProjectRoot -Parent) "Template\01_Core_Financial_Statements\Packt_Ch07_Group_Reporting.pbix"
}
if ([string]::IsNullOrWhiteSpace($TargetPbix)) {
  $TargetPbix = Join-Path $ProjectRoot "output\dashboard_model_seed.pbix"
}
if (!(Test-Path -LiteralPath $SeedTemplate)) { throw "Seed template not found: $SeedTemplate" }
New-Item -ItemType Directory -Force -Path (Split-Path -Parent $TargetPbix) | Out-Null
Copy-Item -LiteralPath $SeedTemplate -Destination $TargetPbix -Force
[ordered]@{
  status = "seed_copied"
  seed_template = $SeedTemplate
  target_pbix = $TargetPbix
  target_bytes = (Get-Item -LiteralPath $TargetPbix).Length
} | ConvertTo-Json -Depth 5
