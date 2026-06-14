param(
  [string]$ProjectRoot = "",
  [string]$TargetPbix = ""
)

$ErrorActionPreference = "Stop"
if ([string]::IsNullOrWhiteSpace($ProjectRoot)) {
  $ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..")
}
if ([string]::IsNullOrWhiteSpace($TargetPbix)) {
  $TargetPbix = Join-Path $ProjectRoot "output\Project4_Customer_Funnel_Conversion_Dashboard.pbix"
}

$CompatRoot = Join-Path $ProjectRoot "data\powerbi_template_compat"
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
  $infoText = pbi-tools info 2>&1 | Out-String
  $jsonStart = $infoText.IndexOf("{")
  if ($jsonStart -lt 0) { throw "pbi-tools info did not return JSON." }
  $info = $infoText.Substring($jsonStart) | ConvertFrom-Json
  $matches = @($info.pbiSessions | Where-Object {
    $_.PbixPath -and ([IO.Path]::GetFullPath([string]$_.PbixPath) -ieq $resolved)
  })
  if ($matches.Count -ne 1) {
    $info.pbiSessions | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $QaRoot "pbi_sessions_debug.json") -Encoding UTF8
    throw "Expected exactly one Power BI Desktop session for '$resolved'. Found $($matches.Count)."
  }
  return $matches[0]
}

function Get-ColumnType([string]$ColumnName) {
  $lower = $ColumnName.ToLowerInvariant()
  if ($lower -in @("date", "session_date", "order_date", "signup_date", "launch_date", "week_start")) {
    return [Microsoft.AnalysisServices.Tabular.DataType]::DateTime
  }
  if ($lower -match "(key|year|month_number|is_weekend|active_flag|quantity|impressions|clicks|sessions|visitors|add_to_cart|checkout_starts|is_first_order|completed_order_flag|refund_order_flag|cancel_order_flag)$") {
    return [Microsoft.AnalysisServices.Tabular.DataType]::Int64
  }
  if ($lower -match "(rate|price|cost|amount|fee|gmv|revenue|margin|spend|tax)") {
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
  $path = Join-Path $CompatRoot $FileName
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
  $lower = $ColumnName.ToLowerInvariant()
  if ($type -in @([Microsoft.AnalysisServices.Tabular.DataType]::Double, [Microsoft.AnalysisServices.Tabular.DataType]::Int64) -and $TableName.StartsWith("fact_")) {
    if ($lower -notmatch "(key|flag|rate)$") { return [Microsoft.AnalysisServices.Tabular.AggregateFunction]::Sum }
  }
  return [Microsoft.AnalysisServices.Tabular.AggregateFunction]::None
}

function Add-ImportTable([Microsoft.AnalysisServices.Tabular.Model]$Model, [string]$Name, [string]$FileName) {
  $path = Join-Path $CompatRoot $FileName
  if (!(Test-Path -LiteralPath $path)) { throw "Compat CSV missing: $path" }
  $first = Import-Csv -LiteralPath $path | Select-Object -First 1
  if (-not $first) { throw "Compat CSV has no rows: $path" }

  $table = New-Object Microsoft.AnalysisServices.Tabular.Table
  $table.Name = $Name
  $Model.Tables.Add($table)
  foreach ($columnName in $first.PSObject.Properties.Name) {
    $column = New-Object Microsoft.AnalysisServices.Tabular.DataColumn
    $column.Name = $columnName
    $column.SourceColumn = $columnName
    $column.DataType = Get-ColumnType $columnName
    $column.SummarizeBy = Get-SummarizeBy $Name $columnName
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
$session = Get-PowerBiSessionForPbix $TargetPbix
$server = New-Object Microsoft.AnalysisServices.Tabular.Server
$server.Connect("localhost:$($session.Port)")
$database = $server.Databases[0]
$model = $database.Model
$model.Relationships.Clear()
$model.Tables.Clear()

$tables = @(
  "dim_date", "dim_product", "dim_customer", "dim_region", "dim_channel", "dim_device",
  "fact_orders", "fact_sessions", "fact_marketing_spend"
)
foreach ($tableName in $tables) { Add-ImportTable $model $tableName "$tableName.csv" }

Add-Relationship $model "Orders_Date" "fact_orders" "order_date" "dim_date" "date"
Add-Relationship $model "Sessions_Date" "fact_sessions" "session_date" "dim_date" "date"
Add-Relationship $model "Orders_Product" "fact_orders" "product_id" "dim_product" "product_id"
Add-Relationship $model "Orders_Customer" "fact_orders" "customer_id" "dim_customer" "customer_id"
Add-Relationship $model "Orders_Region" "fact_orders" "region" "dim_region" "region"
Add-Relationship $model "Sessions_Region" "fact_sessions" "region" "dim_region" "region"
Add-Relationship $model "Orders_Channel" "fact_orders" "channel" "dim_channel" "channel"
Add-Relationship $model "Sessions_Channel" "fact_sessions" "channel" "dim_channel" "channel"
Add-Relationship $model "Spend_Channel" "fact_marketing_spend" "channel" "dim_channel" "channel"
Add-Relationship $model "Orders_Device" "fact_orders" "device" "dim_device" "device"
Add-Relationship $model "Sessions_Device" "fact_sessions" "device" "dim_device" "device"

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

Add-Measure $kpi "GMV" "SUM ( fact_orders[gmv] )" "$#,0"
Add-Measure $kpi "Net Revenue" "SUM ( fact_orders[net_revenue] )" "$#,0"
Add-Measure $kpi "Orders" "DISTINCTCOUNT ( fact_orders[order_id] )" "#,0"
Add-Measure $kpi "Completed Orders" "CALCULATE ( [Orders], fact_orders[status] = ""Completed"" )" "#,0"
Add-Measure $kpi "Refunded Orders" "CALCULATE ( [Orders], fact_orders[status] = ""Refunded"" )" "#,0"
Add-Measure $kpi "Cancelled Orders" "CALCULATE ( [Orders], fact_orders[status] = ""Cancelled"" )" "#,0"
Add-Measure $kpi "AOV" "DIVIDE ( [GMV], [Orders] )" "$#,0.00"
Add-Measure $kpi "Sessions" "SUM ( fact_sessions[sessions] )" "#,0"
Add-Measure $kpi "Visitors" "SUM ( fact_sessions[visitors] )" "#,0"
Add-Measure $kpi "Conversion Rate" "DIVIDE ( [Orders], [Sessions] )" "0.00%"
Add-Measure $kpi "Refund/Cancel Rate" "DIVIDE ( [Refunded Orders] + [Cancelled Orders], [Orders] )" "0.00%"
Add-Measure $kpi "Marketing Spend" "SUM ( fact_marketing_spend[spend] )" "$#,0"
Add-Measure $kpi "ROAS" "DIVIDE ( [Net Revenue], [Marketing Spend] )" "0.00x"
Add-Measure $kpi "Contribution Margin" "SUM ( fact_orders[contribution_margin] )" "$#,0"
Add-Measure $kpi "Contribution Margin %" "DIVIDE ( [Contribution Margin], [Net Revenue] )" "0.00%"
Add-Measure $kpi "Top Category" "VAR t = TOPN ( 1, SUMMARIZE ( dim_product, dim_product[category], ""GMVValue"", [GMV] ), [GMVValue], DESC ) RETURN CONCATENATEX ( t, dim_product[category], "", "" )"
Add-Measure $kpi "Top Traffic Channel" "VAR t = TOPN ( 1, SUMMARIZE ( dim_channel, dim_channel[channel], ""GMVValue"", [GMV] ), [GMVValue], DESC ) RETURN CONCATENATEX ( t, dim_channel[channel], "", "" )"

$model.SaveChanges()
$model.RequestRefresh([Microsoft.AnalysisServices.Tabular.RefreshType]::Full)
$model.SaveChanges()

$result = [ordered]@{
  timestamp = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss zzz")
  status = "template_compat_model_pushed"
  target_pbix = [IO.Path]::GetFullPath($TargetPbix)
  power_bi_port = $session.Port
  process_id = $session.ProcessId
  tables = $model.Tables.Count
  relationships = $model.Relationships.Count
  measures = $kpi.Measures.Count
}
$result | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $QaRoot "template_compat_model_push.json") -Encoding UTF8
$server.Disconnect()
Write-Output ($result | ConvertTo-Json -Depth 8)
