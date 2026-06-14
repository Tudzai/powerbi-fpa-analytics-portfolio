$ErrorActionPreference = "Continue"
$ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..")
$AgentDir = Join-Path $ProjectRoot "_agent"
New-Item -ItemType Directory -Force -Path $AgentDir | Out-Null
$result = [ordered]@{
  Timestamp = (Get-Date).ToString("s")
  ProjectRoot = $ProjectRoot.Path
  PBIDesktop = (Get-Command PBIDesktop.exe -ErrorAction SilentlyContinue).Source
  PowerBIStore = (Get-AppxPackage -Name Microsoft.MicrosoftPowerBIDesktop -ErrorAction SilentlyContinue).InstallLocation
  PbiTools = (Get-Command pbi-tools.exe -ErrorAction SilentlyContinue).Source
  PbiToolsInfo = ((pbi-tools info 2>&1) -join "`n")
  Python = (Get-Command python.exe -ErrorAction SilentlyContinue).Source
  ExistingPowerBIWindows = @(Get-Process PBIDesktop -ErrorAction SilentlyContinue | Select-Object ProcessName,Id,MainWindowTitle)
}
$result | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $AgentDir "environment_check.json") -Encoding UTF8
$md = "# Environment Check`n`n- Project: $($result.ProjectRoot)`n- PBIDesktop: $($result.PBIDesktop)`n- Power BI Store: $($result.PowerBIStore)`n- pbi-tools: $($result.PbiTools)`n- Python: $($result.Python)`n`n## Existing Power BI Windows`n`n````json`n$($result.ExistingPowerBIWindows | ConvertTo-Json -Depth 6)`n````"
$md | Set-Content -LiteralPath (Join-Path $AgentDir "environment_check.md") -Encoding UTF8
$result | ConvertTo-Json -Depth 8
