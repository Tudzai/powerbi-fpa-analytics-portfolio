param(
  [string]$ProjectRoot = ""
)

$ErrorActionPreference = "Stop"
if ([string]::IsNullOrWhiteSpace($ProjectRoot)) {
  $ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..")
}
$PreparedRoot = Join-Path $ProjectRoot "data\prepared"
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

function Get-PowerBiSession {
  $infoText = pbi-tools info 2>&1 | Out-String
  $jsonStart = $infoText.IndexOf("{")
  if ($jsonStart -lt 0) { throw "pbi-tools info did not return JSON." }
  $info = $infoText.Substring($jsonStart) | ConvertFrom-Json
  if (-not $info.pbiSessions -or $info.pbiSessions.Count -eq 0) {
    throw "No active Power BI Desktop local Analysis Services session found. Launch Power BI Desktop first."
  }
  return @($info.pbiSessions | Sort-Object ProcessId -Descending | Select-Object -First 1)[0]
}

function Get-ColumnType([string]$ColumnName) {
  $lower = $ColumnName.ToLowerInvariant()
  if ($lower -in @("date", "session_date", "order_date", "month_start", "week_start", "launch_date", "start_date", "end_date")) {
    return [Microsoft.AnalysisServices.Tabular.DataType]::DateTime
  }
  if ($lower -in @("date_key", "stage_key", "previous_stage_key", "reached_stage_key", "stage_order", "sort_order", "month_number", "year", "is_weekend", "is_bot_traffic", "qualified_session_flag", "paid_flag", "refund_flag")) {
    return [Microsoft.AnalysisServices.Tabular.DataType]::Int64
  }
  if ($lower -match "(flag|order|number|sessions|visits|views|carts|checkouts|purchases|orders|quantity|impressions|clicks)$") {
    return [Microsoft.AnalysisServices.Tabular.DataType]::Int64
  }
  if ($lower -match "(rate|revenue|amount|spend|price|budget|aov|roas|cac)") {
    return [Microsoft.AnalysisServices.Tabular.DataType]::Double
  }
  return [Microsoft.AnalysisServices.Tabular.DataType]::String
}

function Get-MType([string]$ColumnName) {
  $type = Get-ColumnType $ColumnName
  if ($type -eq [Microsoft.AnalysisServices.Tabular.DataType]::DateTime) { return "type date" }
  if ($type -eq [Microsoft.AnalysisServices.Tabular.DataType]::Int64) { return "Int64.Type" }
  if ($type -eq [Microsoft.AnalysisServices.Tabular.DataType]::Double) { return "type number" }
  return "type text"
}

function New-MExpression([string]$FileName, [object[]]$ColumnNames) {
  $path = Join-Path $PreparedRoot $FileName
  $escaped = $path.Replace("\", "\\")
  $typePairs = @($ColumnNames | ForEach-Object {
    $name = [string]$_
    $escapedName = $name -replace '"', '""'
    "{`"$escapedName`", $(Get-MType $name)}"
  }) -join ",`n        "
  return @"
let
    Source = Csv.Document(File.Contents("$escaped"), [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]),
    PromotedHeaders = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    TypedColumns = Table.TransformColumnTypes(PromotedHeaders, {
        $typePairs
    }, "en-US")
in
    TypedColumns
"@
}

function Get-SummarizeBy([string]$TableName, [string]$ColumnName) {
  $type = Get-ColumnType $ColumnName
  if ($type -in @([Microsoft.AnalysisServices.Tabular.DataType]::Double, [Microsoft.AnalysisServices.Tabular.DataType]::Int64) -and $TableName.StartsWith("fact_")) {
    if ($ColumnName.ToLowerInvariant() -notmatch "(key|flag|rate)$") {
      return [Microsoft.AnalysisServices.Tabular.AggregateFunction]::Sum
    }
  }
  return [Microsoft.AnalysisServices.Tabular.AggregateFunction]::None
}

function Add-ImportTable([Microsoft.AnalysisServices.Tabular.Model]$Model, [string]$Name, [string]$FileName) {
  $path = Join-Path $PreparedRoot $FileName
  if (!(Test-Path -LiteralPath $path)) { throw "Prepared CSV missing: $path" }
  $first = Import-Csv -LiteralPath $path | Select-Object -First 1
  if (-not $first) { throw "Prepared CSV has no rows: $path" }

  $table = New-Object Microsoft.AnalysisServices.Tabular.Table
  $table.Name = $Name
  $Model.Tables.Add($table)
  foreach ($columnName in $first.PSObject.Properties.Name) {
    $column = New-Object Microsoft.AnalysisServices.Tabular.DataColumn
    $column.Name = $columnName
    $column.SourceColumn = $columnName
    $column.DataType = Get-ColumnType $columnName
    $column.SummarizeBy = Get-SummarizeBy $Name $columnName
    if ($columnName.ToLowerInvariant() -match "(^|_)(key)$") { $column.IsHidden = $true }
    $table.Columns.Add($column)
  }
  $partition = New-Object Microsoft.AnalysisServices.Tabular.Partition
  $partition.Name = "${Name}-Import"
  $partition.Mode = [Microsoft.AnalysisServices.Tabular.ModeType]::Import
  $source = New-Object Microsoft.AnalysisServices.Tabular.MPartitionSource
  $source.Expression = New-MExpression $FileName $first.PSObject.Properties.Name
  $partition.Source = $source
  $table.Partitions.Add($partition)
}

function Add-Relationship($Model, $Name, $FactTable, $FactColumn, $DimTable, $DimColumn) {
  if (-not $Model.Tables.Contains($FactTable) -or -not $Model.Tables.Contains($DimTable)) { return }
  if (-not $Model.Tables[$FactTable].Columns.Contains($FactColumn) -or -not $Model.Tables[$DimTable].Columns.Contains($DimColumn)) { return }
  $rel = New-Object Microsoft.AnalysisServices.Tabular.SingleColumnRelationship
  $rel.Name = $Name
  $rel.FromColumn = $Model.Tables[$FactTable].Columns[$FactColumn]
  $rel.ToColumn = $Model.Tables[$DimTable].Columns[$DimColumn]
  $rel.FromCardinality = [Microsoft.AnalysisServices.Tabular.RelationshipEndCardinality]::Many
  $rel.ToCardinality = [Microsoft.AnalysisServices.Tabular.RelationshipEndCardinality]::One
  $rel.CrossFilteringBehavior = [Microsoft.AnalysisServices.Tabular.CrossFilteringBehavior]::OneDirection
  $rel.IsActive = $true
  $Model.Relationships.Add($rel)
}

function Add-Measure($Table, $Name, $Expression, $FormatString = $null) {
  $measure = New-Object Microsoft.AnalysisServices.Tabular.Measure
  $measure.Name = $Name
  $measure.Expression = $Expression
  if ($FormatString) { $measure.FormatString = $FormatString }
  $Table.Measures.Add($measure)
}

$powerBiBin = Get-PowerBiBin
Add-Type -Path (Join-Path $powerBiBin "Microsoft.PowerBI.Amo.dll")
$session = Get-PowerBiSession
$server = New-Object Microsoft.AnalysisServices.Tabular.Server
$server.Connect("localhost:$($session.Port)")
$database = $server.Databases[0]
$model = $database.Model
$model.Relationships.Clear()
$model.Tables.Clear()

$tables = @(
  "dim_date", "dim_device", "dim_channel", "dim_campaign", "dim_category", "dim_product", "dim_funnel_stage",
  "fact_sessions", "fact_orders", "fact_stage_sessions", "fact_stage_transition", "fact_monthly_funnel", "fact_marketing_spend"
)
foreach ($tableName in $tables) { Add-ImportTable $model $tableName "$tableName.csv" }

foreach ($fact in @("fact_sessions", "fact_orders", "fact_stage_sessions", "fact_stage_transition", "fact_monthly_funnel", "fact_marketing_spend")) {
  Add-Relationship $model "${fact}_date" $fact "date_key" "dim_date" "date_key"
  Add-Relationship $model "${fact}_device" $fact "device_key" "dim_device" "device_key"
  Add-Relationship $model "${fact}_channel" $fact "channel_key" "dim_channel" "channel_key"
  Add-Relationship $model "${fact}_campaign" $fact "campaign_key" "dim_campaign" "campaign_key"
  Add-Relationship $model "${fact}_category" $fact "category_key" "dim_category" "category_key"
  Add-Relationship $model "${fact}_product" $fact "product_key" "dim_product" "product_key"
  Add-Relationship $model "${fact}_stage" $fact "stage_key" "dim_funnel_stage" "stage_key"
}

$kpi = New-Object Microsoft.AnalysisServices.Tabular.Table
$kpi.Name = "KPI Measures"
$model.Tables.Add($kpi)
$kpiCol = New-Object Microsoft.AnalysisServices.Tabular.DataColumn
$kpiCol.Name = "MeasureKey"
$kpiCol.SourceColumn = "MeasureKey"
$kpiCol.DataType = [Microsoft.AnalysisServices.Tabular.DataType]::String
$kpiCol.IsHidden = $true
$kpi.Columns.Add($kpiCol)
$kpiPartition = New-Object Microsoft.AnalysisServices.Tabular.Partition
$kpiPartition.Name = "KPI Measures-Import"
$kpiPartition.Mode = [Microsoft.AnalysisServices.Tabular.ModeType]::Import
$kpiSource = New-Object Microsoft.AnalysisServices.Tabular.MPartitionSource
$kpiSource.Expression = "let Source = #table(type table [MeasureKey = text], {{""KPI""}}) in Source"
$kpiPartition.Source = $kpiSource
$kpi.Partitions.Add($kpiPartition)

Add-Measure $kpi "Visits" "DISTINCTCOUNT ( fact_sessions[session_id] )" "#,0"
Add-Measure $kpi "Product View Sessions" "CALCULATE ( [Visits], fact_sessions[product_view_flag] = 1 )" "#,0"
Add-Measure $kpi "Add to Cart Sessions" "CALCULATE ( [Visits], fact_sessions[add_to_cart_flag] = 1 )" "#,0"
Add-Measure $kpi "Checkout Sessions" "CALCULATE ( [Visits], fact_sessions[checkout_flag] = 1 )" "#,0"
Add-Measure $kpi "Purchase Sessions" "CALCULATE ( [Visits], fact_sessions[purchase_flag] = 1 )" "#,0"
Add-Measure $kpi "Orders" "DISTINCTCOUNT ( fact_orders[order_id] )" "#,0"
Add-Measure $kpi "Revenue" "SUM ( fact_orders[net_revenue] )" "$#,0"
Add-Measure $kpi "Gross Revenue" "SUM ( fact_orders[gross_revenue] )" "$#,0"
Add-Measure $kpi "AOV" "DIVIDE ( [Revenue], [Orders] )" "$#,0.00"
Add-Measure $kpi "Overall Conversion Rate" "DIVIDE ( [Purchase Sessions], [Visits] )" "0.00%"
Add-Measure $kpi "Product View Rate" "DIVIDE ( [Product View Sessions], [Visits] )" "0.00%"
Add-Measure $kpi "Add to Cart Rate" "DIVIDE ( [Add to Cart Sessions], [Product View Sessions] )" "0.00%"
Add-Measure $kpi "Checkout Start Rate" "DIVIDE ( [Checkout Sessions], [Add to Cart Sessions] )" "0.00%"
Add-Measure $kpi "Purchase Completion Rate" "DIVIDE ( [Purchase Sessions], [Checkout Sessions] )" "0.00%"
Add-Measure $kpi "Stage Sessions" "SUM ( fact_stage_sessions[sessions] )" "#,0"
Add-Measure $kpi "Drop-off Sessions" "SUM ( fact_stage_transition[dropoff_sessions] )" "#,0"
Add-Measure $kpi "Step Conversion Rate" "DIVIDE ( SUM ( fact_stage_transition[current_stage_sessions] ), SUM ( fact_stage_transition[previous_stage_sessions] ) )" "0.00%"
Add-Measure $kpi "Checkout Abandonment Rate" "DIVIDE ( [Checkout Sessions] - [Purchase Sessions], [Checkout Sessions] )" "0.00%"
Add-Measure $kpi "Marketing Spend" "SUM ( fact_marketing_spend[spend] )" "$#,0"
Add-Measure $kpi "ROAS" "DIVIDE ( [Revenue], [Marketing Spend] )" "0.00x"
Add-Measure $kpi "CAC" "DIVIDE ( [Marketing Spend], [Purchase Sessions] )" "$#,0.00"
Add-Measure $kpi "Revenue per Visit" "DIVIDE ( [Revenue], [Visits] )" "$#,0.00"

$model.SaveChanges()
$model.RequestRefresh([Microsoft.AnalysisServices.Tabular.RefreshType]::Full)
$model.SaveChanges()

$result = [ordered]@{
  timestamp = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss zzz")
  status = "model_pushed_to_powerbi_desktop_local_session"
  power_bi_port = $session.Port
  process_id = $session.ProcessId
  tables = $model.Tables.Count
  relationships = $model.Relationships.Count
  measures = $kpi.Measures.Count
  output_model_pbix = "not_created_by_tom_requires_desktop_save"
}
$result | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $QaRoot "scripted_model_push.json") -Encoding UTF8
$server.Disconnect()
Write-Output ($result | ConvertTo-Json -Depth 6)
