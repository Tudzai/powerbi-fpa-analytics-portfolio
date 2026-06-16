param([string]$PbixPath='output\dashboard_final.pbix')
$ProjectRoot=Resolve-Path (Join-Path $PSScriptRoot '..')
$FullPath=Join-Path $ProjectRoot $PbixPath
pbi-tools launch-pbi $FullPath
