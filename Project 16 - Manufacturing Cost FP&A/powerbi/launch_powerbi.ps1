$ErrorActionPreference = "Stop"
$pbix = "C:\Users\Win\OneDrive\Codex\Portfolio\BI\Project 16 - Manufacturing Cost FP&A\output\dashboard_final.pbix"
if (-not (Test-Path $pbix)) {
  throw "PBIX not found: $pbix"
}
& pbi-tools launch-pbi -pbixPath $pbix
