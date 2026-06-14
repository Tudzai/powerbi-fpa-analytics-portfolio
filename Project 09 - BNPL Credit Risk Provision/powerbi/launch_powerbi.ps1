param(
  [string]$PbixPath = ""
)

$ErrorActionPreference = "Stop"

$ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
if ([string]::IsNullOrWhiteSpace($PbixPath)) {
  $PbixPath = Join-Path $ProjectRoot "output\dashboard_model_seed.pbix"
}
if (!(Test-Path -LiteralPath $PbixPath)) {
  throw "PBIX path not found: $PbixPath"
}

$pbiTools = "C:\Users\Win\AppData\Local\Programs\pbi-tools\current\pbi-tools.exe"
if (Test-Path -LiteralPath $pbiTools) {
  & $pbiTools launch-pbi -pbixPath $PbixPath
}
else {
  $cmd = Get-Command PBIDesktop.exe -ErrorAction Stop
  Start-Process -FilePath $cmd.Source -ArgumentList "`"$PbixPath`""
}
