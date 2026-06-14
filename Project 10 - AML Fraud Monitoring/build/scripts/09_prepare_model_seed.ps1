param(
  [string]$ProjectRoot = "C:\Users\Win\OneDrive\Codex\Portfolio\BI\Project 10 - AML Fraud Monitoring",
  [string]$SeedPbix = "C:\Users\Win\OneDrive\Codex\Portfolio\BI\Project 01 - Monthly FP&A Performance Pack\output\tmp_valid_base_inspect.pbix",
  [string]$ModelPbix = "C:\Users\Win\OneDrive\Codex\Portfolio\BI\Project 10 - AML Fraud Monitoring\output\dashboard_model.pbix"
)

$ErrorActionPreference = "Stop"

if (!(Test-Path -LiteralPath $SeedPbix)) {
  $fallback = "C:\Users\Win\OneDrive\Codex\Portfolio\BI\Project 01 - Monthly FP&A Performance Pack\output\dashboard_model.pbix"
  if (Test-Path -LiteralPath $fallback) {
    $SeedPbix = $fallback
  } else {
    throw "No valid technical seed PBIX found. Expected: $SeedPbix"
  }
}

New-Item -ItemType Directory -Force -Path (Split-Path -Parent $ModelPbix) | Out-Null
Copy-Item -LiteralPath $SeedPbix -Destination $ModelPbix -Force

$status = [ordered]@{
  generated_at = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
  project_root = $ProjectRoot
  seed_pbix = $SeedPbix
  model_pbix = $ModelPbix
  status = "technical seed copied; must be opened in Power BI Desktop and overwritten with Project 10 - AML Fraud Monitoring model before final use"
}
$status | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $ProjectRoot "qa\model_seed_status.json") -Encoding UTF8
$status | ConvertTo-Json -Depth 5
