$ErrorActionPreference = "Stop"
$pbix = "C:\Users\Win\OneDrive\Codex\Portfolio\BI\Project 08 - Digital Payments Profitability\output\dashboard_final.pbix"
if (Test-Path $pbix) {
  & pbi-tools launch-pbi -pbixPath $pbix
} else {
  & pbi-tools launch-pbi
}
