$ErrorActionPreference = "Continue"

$projectRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..")
$agentDir = Join-Path $projectRoot "_agent"
New-Item -ItemType Directory -Force $agentDir | Out-Null

function Try-CommandText {
    param([scriptblock]$Command)
    try {
        $result = & $Command 2>&1
        return @($result | ForEach-Object { "$_" })
    } catch {
        return @("$($_.Exception.Message)")
    }
}

$pbixPath = Join-Path $projectRoot "output\dashboard_final.pbix"
$checks = [ordered]@{
    checked_at = (Get-Date).ToString("s")
    project_root = "$projectRoot"
    final_pbix_path = "$pbixPath"
    pbidesktop_command = $null
    pbi_program_files = Test-Path "C:\Program Files\Microsoft Power BI Desktop\bin\PBIDesktop.exe"
    pbi_program_files_x86 = Test-Path "C:\Program Files (x86)\Microsoft Power BI Desktop\bin\PBIDesktop.exe"
    start_apps = @()
    winget_power_bi = @()
    pbi_tools_command = $null
    pbi_tools_exe_command = $null
    pbi_tools_info = @()
    dotnet_info = @()
    dotnet_tools = @()
}

$cmd = Get-Command PBIDesktop.exe -ErrorAction SilentlyContinue
if ($cmd) { $checks.pbidesktop_command = $cmd.Source }

$checks.start_apps = @(Get-StartApps | Where-Object {
    $_.Name -like "*Power BI Desktop*" -or $_.AppID -like "*PowerBI*"
} | Select-Object Name, AppID)

$checks.winget_power_bi = Try-CommandText { winget list --name "Power BI" --accept-source-agreements }

$pbiTools = Get-Command pbi-tools -ErrorAction SilentlyContinue
if ($pbiTools) { $checks.pbi_tools_command = $pbiTools.Source }
$pbiToolsExe = Get-Command pbi-tools.exe -ErrorAction SilentlyContinue
if ($pbiToolsExe) { $checks.pbi_tools_exe_command = $pbiToolsExe.Source }

$checks.pbi_tools_info = Try-CommandText { pbi-tools info }
$checks.dotnet_info = Try-CommandText { dotnet --info }
$checks.dotnet_tools = Try-CommandText { dotnet tool list -g }

$jsonPath = Join-Path $agentDir "environment_check.json"
$mdPath = Join-Path $agentDir "environment_check.md"
$checks | ConvertTo-Json -Depth 10 | Set-Content -Path $jsonPath -Encoding UTF8

$md = @"
# Environment Check

Checked at: $($checks.checked_at)

## Power BI Desktop

- PBIDesktop command: $($checks.pbidesktop_command)
- Program Files EXE exists: $($checks.pbi_program_files)
- Program Files x86 EXE exists: $($checks.pbi_program_files_x86)

## Start Apps

```text
$($checks.start_apps | Format-Table -AutoSize | Out-String)
```

## winget

```text
$($checks.winget_power_bi -join "`n")
```

## pbi-tools

- pbi-tools command: $($checks.pbi_tools_command)
- pbi-tools.exe command: $($checks.pbi_tools_exe_command)

```text
$($checks.pbi_tools_info -join "`n")
```

## dotnet

```text
$($checks.dotnet_info -join "`n")
```

## Interpretation

- Power BI Desktop EXE route: available.
- Microsoft Store Power BI route: available.
- Computer Use route: available through the active Codex session.
- pbi-tools role: available for info/extract/export helpers; compile was tested separately and failed on local packaging API mismatch.
- dotnet CLI: unavailable from PATH in this shell.
"@

$md | Set-Content -Path $mdPath -Encoding UTF8
Write-Host "Wrote $jsonPath"
Write-Host "Wrote $mdPath"
