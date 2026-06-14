$ErrorActionPreference = "Stop"
$ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$AgentDir = Join-Path $ProjectRoot "_agent"
New-Item -ItemType Directory -Force -Path $AgentDir | Out-Null
$cmd = Get-Command PBIDesktop.exe -ErrorAction SilentlyContinue
if (-not $cmd) { throw "PBIDesktop.exe not found." }
Start-Process -FilePath $cmd.Source
Start-Sleep -Seconds 15
$process = Get-Process PBIDesktop -ErrorAction SilentlyContinue | Select-Object ProcessName, Id, MainWindowTitle
$process | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $AgentDir "powerbi_windows_after_launch.json") -Encoding UTF8
$process | ConvertTo-Json -Depth 4
