param(
  [string]$ProjectRoot = "C:\Users\Win\OneDrive\Codex\Portfolio\BI\Project 10 - AML Fraud Monitoring",
  [int]$Port = 0
)

$ErrorActionPreference = "Stop"

$PreparedRoot = Join-Path $ProjectRoot "data\prepared"
$SchemaPath = Join-Path $ProjectRoot "build\config\powerbi_table_schema.json"
$RelationshipPath = Join-Path $ProjectRoot "build\config\relationship_map.json"
$MeasurePath = Join-Path $ProjectRoot "model\measure_map.json"
$OutputRoot = Join-Path $ProjectRoot "output"
$QaRoot = Join-Path $ProjectRoot "qa"
New-Item -ItemType Directory -Force -Path $OutputRoot, $QaRoot | Out-Null

function Resolve-PowerBiBin {
  $candidates = @(
    "C:\Program Files\Microsoft Power BI Desktop\bin",
    "C:\Program Files (x86)\Microsoft Power BI Desktop\bin"
  )
  foreach ($candidate in $candidates) {
    if (Test-Path -LiteralPath (Join-Path $candidate "PBIDesktop.exe")) { return $candidate }
  }
  $storeBins = Get-ChildItem -LiteralPath "C:\Program Files\WindowsApps" -Directory -Filter "Microsoft.MicrosoftPowerBIDesktop_*_x64__8wekyb3d8bbwe" -ErrorAction SilentlyContinue |
    Sort-Object Name -Descending |
    ForEach-Object { Join-Path $_.FullName "bin" }
  foreach ($candidate in $storeBins) {
    if (Test-Path -LiteralPath (Join-Path $candidate "PBIDesktop.exe")) { return $candidate }
  }
  throw "Power BI Desktop bin folder not found."
}

$PowerBiBin = Resolve-PowerBiBin
$AmoDll = Join-Path $PowerBiBin "Microsoft.PowerBI.Amo.dll"
if (!(Test-Path -LiteralPath $AmoDll)) { throw "Power BI AMO assembly not found: $AmoDll" }
Add-Type -Path $AmoDll

function Get-PowerBiPort {
  if ($Port -gt 0) { return $Port }
  $pbi = Get-Process PBIDesktop -ErrorAction SilentlyContinue | Sort-Object StartTime -Descending | Select-Object -First 1
  if (-not $pbi) { throw "Power BI Desktop is not running." }
  $msmd = Get-Process msmdsrv -ErrorAction SilentlyContinue | Sort-Object StartTime -Descending | Select-Object -First 1
  if (-not $msmd) { throw "Power BI Desktop local Analysis Services engine is not running." }
  $conn = Get-NetTCPConnection -OwningProcess $msmd.Id -State Listen -ErrorAction SilentlyContinue |
    Where-Object { $_.LocalAddress -in @("127.0.0.1", "::1") } |
    Sort-Object LocalPort |
    Select-Object -First 1
  if (-not $conn) { throw "Could not locate local Analysis Services port for Power BI Desktop." }
  return $conn.LocalPort
}

function Convert-PowerQueryType([string]$TypeName) {
  switch ($TypeName) {
    "Int64" { return "Int64.Type" }
    "Decimal" { return "type number" }
    "Double" { return "type number" }
    "DateTime" { return "type datetime" }
    default { return "type text" }
  }
}

function New-MExpression($FileName, $Columns) {
  $path = Join-Path $PreparedRoot $FileName
  if (!(Test-Path -LiteralPath $path)) { throw "Prepared CSV not found: $path" }
  $escaped = $path.Replace("\", "\\")
  $typePairs = @()
  foreach ($col in $Columns) {
    $mType = Convert-PowerQueryType $col.type
    $typePairs += "{`"$($col.name)`", $mType}"
  }
  $typeList = $typePairs -join ", "
  return @"
let
    Source = Csv.Document(File.Contents("$escaped"), [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]),
    PromotedHeaders = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    Typed = Table.TransformColumnTypes(PromotedHeaders, {$typeList}, "en-US")
in
    Typed
"@
}

function Convert-DataType($Name) {
  switch ($Name) {
    "Int64" { return [Microsoft.AnalysisServices.Tabular.DataType]::Int64 }
    "Decimal" { return [Microsoft.AnalysisServices.Tabular.DataType]::Decimal }
    "Double" { return [Microsoft.AnalysisServices.Tabular.DataType]::Double }
    "DateTime" { return [Microsoft.AnalysisServices.Tabular.DataType]::DateTime }
    default { return [Microsoft.AnalysisServices.Tabular.DataType]::String }
  }
}

function Convert-SummarizeBy($Name) {
  switch ($Name) {
    "Sum" { return [Microsoft.AnalysisServices.Tabular.AggregateFunction]::Sum }
    default { return [Microsoft.AnalysisServices.Tabular.AggregateFunction]::None }
  }
}

function Add-ImportTable($Model, $TableDef) {
  $table = New-Object Microsoft.AnalysisServices.Tabular.Table
  $table.Name = $TableDef.name
  $Model.Tables.Add($table)

  foreach ($columnDef in $TableDef.columns) {
    $column = New-Object Microsoft.AnalysisServices.Tabular.DataColumn
    $column.Name = $columnDef.name
    $column.SourceColumn = $columnDef.name
    $column.DataType = Convert-DataType $columnDef.type
    $column.SummarizeBy = Convert-SummarizeBy $columnDef.summarize_by
    if ($columnDef.format) { $column.FormatString = $columnDef.format }
    if ($columnDef.hidden) { $column.IsHidden = $true }
    $table.Columns.Add($column)
  }

  $partition = New-Object Microsoft.AnalysisServices.Tabular.Partition
  $partition.Name = "$($TableDef.name)-Import"
  $partition.Mode = [Microsoft.AnalysisServices.Tabular.ModeType]::Import
  $source = New-Object Microsoft.AnalysisServices.Tabular.MPartitionSource
  $source.Expression = New-MExpression $TableDef.file $TableDef.columns
  $partition.Source = $source
  $table.Partitions.Add($partition)
  return $table
}

function Add-Relationship($Model, $RelDef) {
  $rel = New-Object Microsoft.AnalysisServices.Tabular.SingleColumnRelationship
  $rel.Name = $RelDef.name
  $rel.FromColumn = $Model.Tables[$RelDef.from_table].Columns[$RelDef.from_column]
  $rel.ToColumn = $Model.Tables[$RelDef.to_table].Columns[$RelDef.to_column]
  $rel.FromCardinality = [Microsoft.AnalysisServices.Tabular.RelationshipEndCardinality]::Many
  $rel.ToCardinality = [Microsoft.AnalysisServices.Tabular.RelationshipEndCardinality]::One
  $rel.CrossFilteringBehavior = [Microsoft.AnalysisServices.Tabular.CrossFilteringBehavior]::OneDirection
  $rel.IsActive = $true
  $Model.Relationships.Add($rel)
}

function Add-Measure($Table, $MeasureDef) {
  $measure = New-Object Microsoft.AnalysisServices.Tabular.Measure
  $measure.Name = $MeasureDef.name
  $measure.Expression = $MeasureDef.expression
  if ($MeasureDef.format) { $measure.FormatString = $MeasureDef.format }
  if ($MeasureDef.display_folder) { $measure.DisplayFolder = $MeasureDef.display_folder }
  $Table.Measures.Add($measure)
}

if (!(Test-Path -LiteralPath $SchemaPath)) { throw "Missing schema: $SchemaPath" }
if (!(Test-Path -LiteralPath $RelationshipPath)) { throw "Missing relationship map: $RelationshipPath" }
if (!(Test-Path -LiteralPath $MeasurePath)) { throw "Missing measure map: $MeasurePath" }

$schema = Get-Content -LiteralPath $SchemaPath -Raw | ConvertFrom-Json
$relationships = Get-Content -LiteralPath $RelationshipPath -Raw | ConvertFrom-Json
$measures = Get-Content -LiteralPath $MeasurePath -Raw | ConvertFrom-Json

$port = Get-PowerBiPort
$server = New-Object Microsoft.AnalysisServices.Tabular.Server
$server.Connect("localhost:$port")
$database = $server.Databases[0]
$model = $database.Model

$model.Relationships.Clear()
$model.Tables.Clear()

foreach ($tableDef in $schema) { Add-ImportTable $model $tableDef | Out-Null }

$kpi = New-Object Microsoft.AnalysisServices.Tabular.Table
$kpi.Name = "KPI Measures"
$model.Tables.Add($kpi)
$kpiColumn = New-Object Microsoft.AnalysisServices.Tabular.DataColumn
$kpiColumn.Name = "MeasureKey"
$kpiColumn.SourceColumn = "MeasureKey"
$kpiColumn.DataType = [Microsoft.AnalysisServices.Tabular.DataType]::String
$kpiColumn.IsHidden = $true
$kpi.Columns.Add($kpiColumn)
$kpiPartition = New-Object Microsoft.AnalysisServices.Tabular.Partition
$kpiPartition.Name = "KPI Measures-Import"
$kpiPartition.Mode = [Microsoft.AnalysisServices.Tabular.ModeType]::Import
$kpiSource = New-Object Microsoft.AnalysisServices.Tabular.MPartitionSource
$kpiSource.Expression = "let Source = #table(type table [MeasureKey = text], {{""KPI""}}) in Source"
$kpiPartition.Source = $kpiSource
$kpi.Partitions.Add($kpiPartition)

foreach ($rel in $relationships) { Add-Relationship $model $rel }
foreach ($measure in $measures) { Add-Measure $kpi $measure }

if ($model.Tables["DimDate"]) {
  $model.Tables["DimDate"].Columns["MonthName"].SortByColumn = $model.Tables["DimDate"].Columns["MonthNumber"]
  $model.Tables["DimDate"].Columns["MonthYear"].SortByColumn = $model.Tables["DimDate"].Columns["MonthIndex"]
}

$model.SaveChanges()
$model.RequestRefresh([Microsoft.AnalysisServices.Tabular.RefreshType]::Full)
$model.SaveChanges()
$server.Disconnect()

$status = [ordered]@{
  generated_at = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
  project_root = $ProjectRoot
  powerbi_bin = $PowerBiBin
  port = $port
  tables = @($schema | ForEach-Object { $_.name })
  table_count = $schema.Count + 1
  relationship_count = $relationships.Count
  measure_count = $measures.Count
  status = "model pushed to running Power BI Desktop session"
}
$status | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath (Join-Path $QaRoot "model_push_status.json") -Encoding UTF8
$status | ConvertTo-Json -Depth 10
