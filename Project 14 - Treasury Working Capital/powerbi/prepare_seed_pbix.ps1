param(
  [string]$SeedTemplate = "C:\Users\Win\OneDrive\Codex\Portfolio\BI\Template\01_Core_Financial_Statements\Packt_Ch07_Group_Reporting.pbix",
  [string]$TargetPbix = "C:\Users\Win\OneDrive\Codex\Portfolio\BI\Project 14 - Treasury Working Capital\output\dashboard_model_seed_ch07.pbix"
)

$ErrorActionPreference = "Stop"
if (!(Test-Path -LiteralPath $SeedTemplate)) { throw "Seed template not found: $SeedTemplate" }
New-Item -ItemType Directory -Force -Path (Split-Path -Parent $TargetPbix) | Out-Null
Copy-Item -LiteralPath $SeedTemplate -Destination $TargetPbix -Force
[Reflection.Assembly]::LoadFrom("C:\Program Files\Microsoft Power BI Desktop\bin\Microsoft.PowerBI.Packaging.dll") | Out-Null
$stream = [IO.File]::OpenRead($TargetPbix)
try { [Microsoft.PowerBI.Packaging.PowerBIPackager]::Validate($stream) } finally { $stream.Dispose() }
[ordered]@{
  status = "seed_copied"
  seed_template = $SeedTemplate
  target_pbix = $TargetPbix
  target_bytes = (Get-Item -LiteralPath $TargetPbix).Length
} | ConvertTo-Json -Depth 5
