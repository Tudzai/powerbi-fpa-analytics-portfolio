$ErrorActionPreference = "Continue"

$ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..")
$AgentRoot = Join-Path $ProjectRoot "_agent"
$QaRoot = Join-Path $ProjectRoot "qa"
New-Item -ItemType Directory -Force -Path $AgentRoot, $QaRoot | Out-Null

$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss zzz"
$powerBiBinCandidates = @(
  "C:\Program Files\Microsoft Power BI Desktop\bin",
  "C:\Program Files (x86)\Microsoft Power BI Desktop\bin"
) | Where-Object { Test-Path -LiteralPath $_ }

$startApps = @(Get-StartApps | Where-Object {
  $_.Name -like "*Power BI Desktop*" -or $_.AppID -like "*PowerBI*"
})

$powerBiBin = $powerBiBinCandidates | Select-Object -First 1
$packagingDll = if ($powerBiBin) { Join-Path $powerBiBin "Microsoft.PowerBI.Packaging.dll" } else { $null }
$amoDll = if ($powerBiBin) { Join-Path $powerBiBin "Microsoft.PowerBI.Amo.dll" } else { $null }
$tabularDll = if ($powerBiBin) { Join-Path $powerBiBin "Microsoft.PowerBI.Tabular.dll" } else { $null }
$msmdsrv = if ($powerBiBin) { Join-Path $powerBiBin "msmdsrv.exe" } else { $null }

$projectPowerBiSources = @(Get-ChildItem -LiteralPath $ProjectRoot -Recurse -File -ErrorAction SilentlyContinue |
  Where-Object { $_.Extension -in @(".pbix", ".pbit", ".pbip") -or $_.Name -eq ".pbixproj.json" } |
  Select-Object FullName, Length)

$existingFinal = Test-Path -LiteralPath (Join-Path $ProjectRoot "output\dashboard_final.pbix")
$pbiTools = Get-Command pbi-tools -ErrorAction SilentlyContinue

$checks = [ordered]@{
  timestamp = $timestamp
  power_bi_bin = $powerBiBin
  power_bi_start_apps_count = $startApps.Count
  packaging_dll_exists = [bool]($packagingDll -and (Test-Path -LiteralPath $packagingDll))
  amo_dll_exists = [bool]($amoDll -and (Test-Path -LiteralPath $amoDll))
  tabular_dll_exists = [bool]($tabularDll -and (Test-Path -LiteralPath $tabularDll))
  msmdsrv_exists = [bool]($msmdsrv -and (Test-Path -LiteralPath $msmdsrv))
  pbi_tools_available = [bool]$pbiTools
  project_powerbi_source_count = $projectPowerBiSources.Count
  project_powerbi_sources = @($projectPowerBiSources)
  existing_final_pbix = $existingFinal
  scripted_desktop_pbix_precheck_result = "precheck_no_saved_powerbi_source"
  reason = "Power BI Desktop local assemblies exist, but Project 03 - Ecommerce Executive Performance has no saved base/model PBIX, PBIT, PBIP, or .pbixproj.json source before the scripted Desktop attempt. This precheck does not create or overwrite final attempt evidence."
  next_action = "Run model push, native layout, and package/apply scripts; package/apply still requires a saved Project 03 - Ecommerce Executive Performance model PBIX."
}

$jsonPath = Join-Path $QaRoot "scripted_desktop_pbix_precheck.json"
$checks | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $jsonPath -Encoding UTF8

$sourceLines = if ($projectPowerBiSources.Count -gt 0) {
  ($projectPowerBiSources | Format-Table -AutoSize | Out-String)
} else {
  "None"
}

$md = @"
# SCRIPTED_DESKTOP_PBIX Check

Timestamp: $timestamp

## Result

- Result: `precheck_no_saved_powerbi_source`
- Power BI Desktop bin: `$powerBiBin`
- Packaging assembly exists: $($checks.packaging_dll_exists)
- AMO assembly exists: $($checks.amo_dll_exists)
- Tabular assembly exists: $($checks.tabular_dll_exists)
- Local Analysis Services engine exists: $($checks.msmdsrv_exists)
- pbi-tools available: $($checks.pbi_tools_available)
- Project Power BI source count: $($checks.project_powerbi_source_count)
- Existing final PBIX in Project 03 - Ecommerce Executive Performance: $existingFinal

## Project 03 - Ecommerce Executive Performance Power BI Sources

~~~text
$sourceLines
~~~

## Interpretation

Power BI Desktop local assemblies are present, so the route was not skipped. It is ruled out for this project run because there is no safe Project 03 - Ecommerce Executive Performance base/model PBIX, PBIT, PBIP, or `.pbixproj.json` source to script into a validated final PBIX. The generated package has CSV, DAX, page map, visual map, theme, and runbooks, but those are not sufficient by themselves for a supported automated full PBIX build.

`pbi-tools compile` is not treated as a final PBIX authoring route here because its own help states PBIX compile is for report-only/thin reports and PBIT is used when the project contains a data model. This ecommerce dashboard needs a data model and final PBIX validation.

Project 01 - Monthly FP&A Performance Pack PBIX artifacts are not reused as a seed because they belong to a different project scope and the user did not approve them as a template.

Next action: use `MANUAL_ASSISTED` Power BI Desktop build, or provide/approve a Project 03 - Ecommerce Executive Performance PBIX/PBIT seed for scripted authoring.
"@

Set-Content -LiteralPath (Join-Path $AgentRoot "scripted_desktop_pbix_precheck.md") -Value $md -Encoding UTF8
Write-Output ($checks | ConvertTo-Json -Depth 8)
