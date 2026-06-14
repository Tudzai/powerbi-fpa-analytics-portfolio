param(
    [string]$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
)

$ErrorActionPreference = "Stop"

$outputDir = Join-Path $ProjectRoot "output"
$sourceProject = Join-Path $outputDir "powerbi_project"
$sourceReport = Join-Path $sourceProject "AML_Fraud_Monitoring_Command_Center.Report"
$sourceTmdl = Join-Path $ProjectRoot "qa\model_tmdl_from_live"
$sourceBim = Join-Path $ProjectRoot "qa\extract_live_after_repush.bim"
$finalProject = Join-Path $outputDir "dashboard_final_project"
$finalReport = Join-Path $finalProject "AML_Fraud_Monitoring_Command_Center.Report"
$finalSemantic = Join-Path $finalProject "AML_Fraud_Monitoring_Command_Center.SemanticModel"
$finalSemanticDefinition = Join-Path $finalSemantic "definition"
$finalPbip = Join-Path $finalProject "dashboard_final.pbip"
$namedFinalPbip = Join-Path $finalProject "AML_Fraud_Monitoring_Command_Center.pbip"
$shortcutPbip = Join-Path $outputDir "dashboard_final.pbip"
$utf8NoBom = New-Object System.Text.UTF8Encoding($false)

if (-not (Test-Path $sourceReport)) {
    throw "Source report folder missing: $sourceReport"
}
if (-not (Test-Path $sourceBim)) {
    throw "BIM model file missing: $sourceBim. Run pbi-tools generate-bim first."
}

if (Test-Path $finalProject) {
    Remove-Item -LiteralPath $finalProject -Recurse -Force
}
New-Item -ItemType Directory -Path $finalProject | Out-Null

Copy-Item -LiteralPath $sourceReport -Destination $finalReport -Recurse
New-Item -ItemType Directory -Path $finalSemantic -Force | Out-Null
Copy-Item -LiteralPath $sourceBim -Destination (Join-Path $finalSemantic "model.bim")

$pbism = [ordered]@{
    version = "4.2"
    settings = [ordered]@{
        qnaEnabled = $false
    }
}
[System.IO.File]::WriteAllText((Join-Path $finalSemantic "definition.pbism"), ($pbism | ConvertTo-Json -Depth 10), $utf8NoBom)

$reportPlatform = [ordered]@{
    '$schema' = "https://developer.microsoft.com/json-schemas/fabric/gitIntegration/platformProperties/2.0.0/schema.json"
    metadata = [ordered]@{
        type = "Report"
        displayName = "AML Fraud Monitoring Command Center"
    }
    config = [ordered]@{
        version = "2.0"
        logicalId = ([guid]::NewGuid()).ToString()
    }
}
[System.IO.File]::WriteAllText((Join-Path $finalReport ".platform"), ($reportPlatform | ConvertTo-Json -Depth 10), $utf8NoBom)

$semanticPlatform = [ordered]@{
    '$schema' = "https://developer.microsoft.com/json-schemas/fabric/gitIntegration/platformProperties/2.0.0/schema.json"
    metadata = [ordered]@{
        type = "SemanticModel"
        displayName = "AML Fraud Monitoring Command Center"
    }
    config = [ordered]@{
        version = "2.0"
        logicalId = ([guid]::NewGuid()).ToString()
    }
}
[System.IO.File]::WriteAllText((Join-Path $finalSemantic ".platform"), ($semanticPlatform | ConvertTo-Json -Depth 10), $utf8NoBom)

$pbip = [ordered]@{
    '$schema' = "https://developer.microsoft.com/json-schemas/fabric/pbip/pbipProperties/1.0.0/schema.json"
    version = "1.0"
    artifacts = @(
        [ordered]@{
            report = [ordered]@{
                path = "AML_Fraud_Monitoring_Command_Center.Report"
            }
        }
    )
    settings = [ordered]@{
        enableAutoRecovery = $true
    }
}
$pbipJson = $pbip | ConvertTo-Json -Depth 10
[System.IO.File]::WriteAllText($finalPbip, $pbipJson, $utf8NoBom)
[System.IO.File]::WriteAllText($namedFinalPbip, $pbipJson, $utf8NoBom)

$shortcut = [ordered]@{
    '$schema' = "https://developer.microsoft.com/json-schemas/fabric/pbip/pbipProperties/1.0.0/schema.json"
    version = "1.0"
    artifacts = @(
        [ordered]@{
            report = [ordered]@{
                path = "dashboard_final_project/AML_Fraud_Monitoring_Command_Center.Report"
            }
        }
    )
    settings = [ordered]@{
        enableAutoRecovery = $true
    }
}
[System.IO.File]::WriteAllText($shortcutPbip, ($shortcut | ConvertTo-Json -Depth 10), $utf8NoBom)

$manifest = [ordered]@{
    status = "repaired_pbip_ready"
    generated_at = (Get-Date).ToString("s")
    final_pbip = $finalPbip
    named_final_pbip = $namedFinalPbip
    shortcut_pbip = $shortcutPbip
    report_folder = $finalReport
    semantic_model_folder = $finalSemantic
    semantic_model_file = (Join-Path $finalSemantic "model.bim")
    semantic_model_format = "BIM"
    tmdl_file_count = 0
}
$manifestJson = $manifest | ConvertTo-Json -Depth 10
[System.IO.File]::WriteAllText((Join-Path $outputDir "dashboard_final_pbip_manifest.json"), $manifestJson, $utf8NoBom)

Write-Output ($manifest | ConvertTo-Json -Depth 10)
