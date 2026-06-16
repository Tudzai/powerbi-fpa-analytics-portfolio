param(
  [string]$SeedTemplate = "C:\Users\Win\OneDrive\Codex\Portfolio\BI\Template\04_Profitability_Margin\Microsoft_Customer_Profitability.pbix",
  [string]$TargetPbix = "C:\Users\Win\OneDrive\Codex\Portfolio\BI\Project 17 - Logistics Trade Lane Profitability\output\dashboard_model_seed.pbix"
)

$ErrorActionPreference = "Stop"
if (!(Test-Path -LiteralPath $SeedTemplate)) { throw "Seed template not found: $SeedTemplate" }
New-Item -ItemType Directory -Force -Path (Split-Path -Parent $TargetPbix) | Out-Null
Copy-Item -LiteralPath $SeedTemplate -Destination $TargetPbix -Force
[ordered]@{
  status = "seed_copied"
  seed_template = $SeedTemplate
  target_pbix = $TargetPbix
  target_bytes = (Get-Item -LiteralPath $TargetPbix).Length
} | ConvertTo-Json -Depth 5
