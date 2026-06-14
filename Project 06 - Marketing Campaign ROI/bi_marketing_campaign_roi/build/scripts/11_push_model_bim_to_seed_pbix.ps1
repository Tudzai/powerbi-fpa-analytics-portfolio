param(
  [string]$ProjectRoot = "",
  [string]$TargetPbix = "",
  [string]$ModelBim = ""
)

$ErrorActionPreference = "Stop"
if ([string]::IsNullOrWhiteSpace($ProjectRoot)) {
  $ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..")
}
if ([string]::IsNullOrWhiteSpace($TargetPbix)) {
  $TargetPbix = Join-Path $ProjectRoot "output\dashboard_model_seed.pbix"
}
if ([string]::IsNullOrWhiteSpace($ModelBim)) {
  $ModelBim = Join-Path $ProjectRoot "powerbi\pbip\Project6_Marketing_ROI_Native\Project6_Marketing_ROI_Native.SemanticModel\model.bim"
}

$QaRoot = Join-Path $ProjectRoot "qa"
New-Item -ItemType Directory -Force -Path $QaRoot | Out-Null

function Get-PowerBiBin {
  $cmd = Get-Command PBIDesktop.exe -ErrorAction SilentlyContinue
  if ($cmd) { return Split-Path -Parent $cmd.Source }
  $candidates = @(
    "C:\Program Files\Microsoft Power BI Desktop\bin",
    "C:\Program Files (x86)\Microsoft Power BI Desktop\bin"
  ) | Where-Object { Test-Path -LiteralPath (Join-Path $_ "PBIDesktop.exe") }
  if ($candidates) { return ($candidates | Select-Object -First 1) }
  throw "Power BI Desktop EXE bin folder not found."
}

function Get-PowerBiSessionForPbix([string]$Path) {
  $resolved = [IO.Path]::GetFullPath($Path)
  $infoText = & "C:\Users\Win\AppData\Local\Programs\pbi-tools\current\pbi-tools.exe" info 2>&1 | Out-String
  $jsonStart = $infoText.IndexOf("{")
  if ($jsonStart -lt 0) { throw "pbi-tools info did not return JSON." }
  $info = $infoText.Substring($jsonStart) | ConvertFrom-Json
  $matches = @($info.pbiSessions | Where-Object {
    $_.PbixPath -and ([IO.Path]::GetFullPath([string]$_.PbixPath) -ieq $resolved)
  })
  if ($matches.Count -ne 1) {
    $info.pbiSessions | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $QaRoot "seed_pbi_sessions_debug.json") -Encoding UTF8
    throw "Expected exactly one Power BI Desktop session for '$resolved'. Found $($matches.Count)."
  }
  return $matches[0]
}

if (!(Test-Path -LiteralPath $TargetPbix)) { throw "Target PBIX missing: $TargetPbix" }
if (!(Test-Path -LiteralPath $ModelBim)) { throw "model.bim missing: $ModelBim" }

$powerBiBin = Get-PowerBiBin
Add-Type -Path (Join-Path $powerBiBin "Microsoft.PowerBI.Amo.dll")

$session = Get-PowerBiSessionForPbix $TargetPbix
$server = New-Object Microsoft.AnalysisServices.Tabular.Server
$server.Connect("localhost:$($session.Port)")
$database = $server.Databases[0]
$dbName = $database.Name
$dbId = $database.ID

$modelBimText = Get-Content -LiteralPath $ModelBim -Raw -Encoding UTF8
$modelBim = $modelBimText | ConvertFrom-Json

$replacement = [ordered]@{
  createOrReplace = [ordered]@{
    object = [ordered]@{
      database = $dbName
    }
    database = [ordered]@{
      name = $dbName
      id = $dbId
      compatibilityLevel = $modelBim.compatibilityLevel
      model = $modelBim.model
    }
  }
}

$tmsl = $replacement | ConvertTo-Json -Depth 100 -Compress
$server.Execute($tmsl) | Out-Null

$server.Disconnect()
$server = New-Object Microsoft.AnalysisServices.Tabular.Server
$server.Connect("localhost:$($session.Port)")
$database = $server.Databases[$dbName]
$model = $database.Model

$model.RequestRefresh([Microsoft.AnalysisServices.Tabular.RefreshType]::Full)
$model.SaveChanges()

$tables = @($model.Tables | ForEach-Object { $_.Name })
$relationships = $model.Relationships.Count
$measures = @($model.Tables | ForEach-Object { $_.Measures } | ForEach-Object { $_.Name })

$result = [ordered]@{
  timestamp = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss zzz")
  status = "project6_model_pushed_to_seed_pbix_session"
  target_pbix = [IO.Path]::GetFullPath($TargetPbix)
  power_bi_port = $session.Port
  process_id = $session.ProcessId
  database = $dbName
  tables = $tables
  relationship_count = $relationships
  measure_count = $measures.Count
  measures = $measures
}
$result | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath (Join-Path $QaRoot "seed_model_push.json") -Encoding UTF8
$server.Disconnect()
Write-Output ($result | ConvertTo-Json -Depth 10)
