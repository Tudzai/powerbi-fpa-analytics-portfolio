param(
  [int]$Port = 0,
  [string]$ProjectRoot = "C:\Users\Win\OneDrive\Codex\Portfolio\BI\Project 08 - Digital Payments Profitability"
)

$ErrorActionPreference = "Stop"

function Resolve-PowerBIPort {
  if ($Port -gt 0) { return $Port }

  $infoRaw = & pbi-tools info 2>&1 | Out-String
  $jsonStart = $infoRaw.IndexOf("{")
  if ($jsonStart -lt 0) {
    throw "Could not find JSON payload in pbi-tools info output."
  }

  $info = $infoRaw.Substring($jsonStart) | ConvertFrom-Json
  if (-not $info.pbiSessions -or $info.pbiSessions.Count -lt 1) {
    throw "No running Power BI Desktop session found."
  }

  return [int]$info.pbiSessions[0].Port
}

function Import-PowerBIAssemblies {
  $bin = "C:\Program Files\Microsoft Power BI Desktop\bin"
  [System.IO.Directory]::SetCurrentDirectory($bin)
  $dlls = @(
    "Microsoft.AnalysisServices.Server.Core.dll",
    "Microsoft.AnalysisServices.Server.Tabular.dll",
    "Microsoft.AnalysisServices.Server.Tabular.Json.dll"
  )
  foreach ($dll in $dlls) {
    $path = Join-Path $bin $dll
    if (-not (Test-Path $path)) {
      throw "Missing Power BI TOM assembly: $path"
    }
    [void][System.Reflection.Assembly]::LoadFrom($path)
  }
}

function Escape-MPath([string]$Path) {
  return $Path.Replace("\", "\\").Replace('"', '""')
}

function Get-ColumnType([string]$ColumnName) {
  $intCols = @(
    "date_key", "year", "month_no", "month_index", "is_latest_complete_month", "active_flag",
    "transaction_count", "successful_txn", "failed_txn", "refund_count", "chargeback_count",
    "bridge_order", "take_rate_delta_bps"
  )
  $dateCols = @("month_start_date", "onboarding_date")
  $doubleCols = @(
    "base_monthly_gmv", "avg_ticket_usd", "contracted_take_rate", "fixed_fee_usd",
    "variable_cost_rate", "fixed_cost_per_txn", "fraud_cost_rate", "default_mix_weight", "support_cost_rate",
    "gmv", "revenue_fee", "fixed_fee_revenue", "refund_amount", "chargeback_amount",
    "interchange_cost", "network_cost", "processor_cost", "fraud_loss", "incentives_cost",
    "total_cost", "contribution_margin", "auth_success_rate", "average_ticket", "take_rate",
    "cost_per_txn", "margin_rate", "cost_delta_pct", "volume_elasticity", "bridge_amount"
  )
  if ($intCols -contains $ColumnName) { return "Int64" }
  if ($dateCols -contains $ColumnName) { return "DateTime" }
  if ($doubleCols -contains $ColumnName) { return "Double" }
  return "String"
}

function New-MExpression {
  param(
    [string]$CsvPath,
    [array]$Columns
  )

  $typedRows = @()
  foreach ($col in $Columns) {
    $mType = switch ($col.Type) {
      "String" { "type text" }
      "Int64" { "Int64.Type" }
      "Double" { "type number" }
      "DateTime" { "type date" }
      default { "type text" }
    }
    $typedRows += "        {`"$($col.Name)`", $mType}"
  }

  $typedBlock = $typedRows -join ",`n"
  $escaped = Escape-MPath $CsvPath
  return @"
let
    Source = Csv.Document(File.Contents("$escaped"), [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]),
    PromotedHeaders = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    TypedColumns = Table.TransformColumnTypes(PromotedHeaders, {
$typedBlock
    }, "en-US")
in
    TypedColumns
"@
}

function Get-CsvColumns {
  param([string]$CsvPath)
  $reader = [System.IO.StreamReader]::new($CsvPath)
  try {
    $header = $reader.ReadLine()
  }
  finally {
    $reader.Close()
  }
  if (-not $header) { throw "CSV has no header: $CsvPath" }
  return $header.Split(",") | ForEach-Object {
    [ordered]@{ Name = $_.Trim('"'); Type = Get-ColumnType $_.Trim('"') }
  }
}

function Add-ImportTable {
  param(
    [Microsoft.AnalysisServices.Tabular.Model]$Model,
    [string]$Name,
    [string]$CsvPath
  )

  $columns = @(Get-CsvColumns -CsvPath $CsvPath)
  $table = New-Object Microsoft.AnalysisServices.Tabular.Table
  $table.Name = $Name

  foreach ($col in $columns) {
    $column = New-Object Microsoft.AnalysisServices.Tabular.DataColumn
    $column.Name = $col.Name
    $column.SourceColumn = $col.Name
    $column.DataType = [Microsoft.AnalysisServices.Tabular.DataType]::$($col.Type)
    $column.SummarizeBy = [Microsoft.AnalysisServices.Tabular.AggregateFunction]::None
    $table.Columns.Add($column) | Out-Null
  }

  $source = New-Object Microsoft.AnalysisServices.Tabular.MPartitionSource
  $source.Expression = New-MExpression -CsvPath $CsvPath -Columns $columns

  $partition = New-Object Microsoft.AnalysisServices.Tabular.Partition
  $partition.Name = "$Name-Import"
  $partition.Mode = [Microsoft.AnalysisServices.Tabular.ModeType]::Import
  $partition.Source = $source
  $table.Partitions.Add($partition) | Out-Null

  $Model.Tables.Add($table) | Out-Null
}

function Add-MeasureTable {
  param([Microsoft.AnalysisServices.Tabular.Model]$Model)

  $table = New-Object Microsoft.AnalysisServices.Tabular.Table
  $table.Name = "KPI Measures"

  $column = New-Object Microsoft.AnalysisServices.Tabular.DataColumn
  $column.Name = "Measure Group"
  $column.SourceColumn = "Measure Group"
  $column.DataType = [Microsoft.AnalysisServices.Tabular.DataType]::String
  $column.SummarizeBy = [Microsoft.AnalysisServices.Tabular.AggregateFunction]::None
  $column.IsHidden = $true
  $table.Columns.Add($column) | Out-Null

  $source = New-Object Microsoft.AnalysisServices.Tabular.MPartitionSource
  $source.Expression = @"
let
    Source = #table(type table [Measure Group = text], {{"Digital Payments Profitability"}})
in
    Source
"@

  $partition = New-Object Microsoft.AnalysisServices.Tabular.Partition
  $partition.Name = "KPI Measures-Import"
  $partition.Mode = [Microsoft.AnalysisServices.Tabular.ModeType]::Import
  $partition.Source = $source
  $table.Partitions.Add($partition) | Out-Null

  $Model.Tables.Add($table) | Out-Null
  return $table
}

function Add-Relationship {
  param(
    [Microsoft.AnalysisServices.Tabular.Model]$Model,
    [string]$FromTable,
    [string]$FromColumn,
    [string]$ToTable,
    [string]$ToColumn
  )

  $relationship = New-Object Microsoft.AnalysisServices.Tabular.SingleColumnRelationship
  $relationship.Name = "rel_${FromTable}_${FromColumn}_${ToTable}_${ToColumn}"
  $relationship.FromColumn = $Model.Tables[$FromTable].Columns[$FromColumn]
  $relationship.ToColumn = $Model.Tables[$ToTable].Columns[$ToColumn]
  $relationship.CrossFilteringBehavior = [Microsoft.AnalysisServices.Tabular.CrossFilteringBehavior]::OneDirection
  $Model.Relationships.Add($relationship) | Out-Null
}

function Add-KpiMeasure {
  param(
    [Microsoft.AnalysisServices.Tabular.Table]$Table,
    [string]$Name,
    [string]$Expression,
    [string]$FormatString = ""
  )

  $measure = New-Object Microsoft.AnalysisServices.Tabular.Measure
  $measure.Name = $Name
  $measure.Expression = $Expression
  if ($FormatString) { $measure.FormatString = $FormatString }
  $Table.Measures.Add($measure) | Out-Null
}

$portToUse = Resolve-PowerBIPort
Import-PowerBIAssemblies

$prepared = Join-Path $ProjectRoot "data\prepared"
$tableNames = @(
  "dim_date",
  "dim_merchant",
  "dim_payment_method",
  "dim_channel",
  "dim_scenario",
  "fact_payment_month",
  "fact_fee_bridge"
)

$server = New-Object Microsoft.AnalysisServices.Tabular.Server
$server.Connect("localhost:$portToUse")
try {
  if ($server.Databases.Count -lt 1) { throw "Connected to Power BI Desktop, but no database was found." }
  $database = $server.Databases[0]
  $model = $database.Model

  while ($model.Relationships.Count -gt 0) {
    $model.Relationships.Remove($model.Relationships[0])
  }
  while ($model.Tables.Count -gt 0) {
    $model.Tables.Remove($model.Tables[0])
  }

  $model.Culture = "en-US"
  $model.SourceQueryCulture = "en-US"
  $model.DataAccessOptions.LegacyRedirects = $true
  $model.DataAccessOptions.ReturnErrorValuesAsNull = $true

  foreach ($name in $tableNames) {
    $csvPath = Join-Path $prepared "$name.csv"
    if (-not (Test-Path $csvPath)) { throw "Missing prepared CSV: $csvPath" }
    Add-ImportTable -Model $model -Name $name -CsvPath $csvPath
  }

  $measureTable = Add-MeasureTable -Model $model

  Add-Relationship -Model $model -FromTable "fact_payment_month" -FromColumn "year_month" -ToTable "dim_date" -ToColumn "year_month"
  Add-Relationship -Model $model -FromTable "fact_payment_month" -FromColumn "merchant_id" -ToTable "dim_merchant" -ToColumn "merchant_id"
  Add-Relationship -Model $model -FromTable "fact_payment_month" -FromColumn "payment_method_id" -ToTable "dim_payment_method" -ToColumn "payment_method_id"
  Add-Relationship -Model $model -FromTable "fact_payment_month" -FromColumn "channel_id" -ToTable "dim_channel" -ToColumn "channel_id"
  Add-Relationship -Model $model -FromTable "fact_fee_bridge" -FromColumn "year_month" -ToTable "dim_date" -ToColumn "year_month"

  Add-KpiMeasure -Table $measureTable -Name "Payment GMV" -Expression "SUM ( fact_payment_month[gmv] )" -FormatString '$#,0'
  Add-KpiMeasure -Table $measureTable -Name "Transactions" -Expression "SUM ( fact_payment_month[transaction_count] )" -FormatString '#,0'
  Add-KpiMeasure -Table $measureTable -Name "Successful Transactions" -Expression "SUM ( fact_payment_month[successful_txn] )" -FormatString '#,0'
  Add-KpiMeasure -Table $measureTable -Name "Failed Transactions" -Expression "SUM ( fact_payment_month[failed_txn] )" -FormatString '#,0'
  Add-KpiMeasure -Table $measureTable -Name "Revenue" -Expression "SUM ( fact_payment_month[revenue_fee] )" -FormatString '$#,0'
  Add-KpiMeasure -Table $measureTable -Name "Fixed Fee Revenue" -Expression "SUM ( fact_payment_month[fixed_fee_revenue] )" -FormatString '$#,0'
  Add-KpiMeasure -Table $measureTable -Name "Refund Amount" -Expression "SUM ( fact_payment_month[refund_amount] )" -FormatString '$#,0'
  Add-KpiMeasure -Table $measureTable -Name "Refund Count" -Expression "SUM ( fact_payment_month[refund_count] )" -FormatString '#,0'
  Add-KpiMeasure -Table $measureTable -Name "Chargeback Amount" -Expression "SUM ( fact_payment_month[chargeback_amount] )" -FormatString '$#,0'
  Add-KpiMeasure -Table $measureTable -Name "Chargeback Count" -Expression "SUM ( fact_payment_month[chargeback_count] )" -FormatString '#,0'
  Add-KpiMeasure -Table $measureTable -Name "Interchange Cost" -Expression "SUM ( fact_payment_month[interchange_cost] )" -FormatString '$#,0'
  Add-KpiMeasure -Table $measureTable -Name "Network Cost" -Expression "SUM ( fact_payment_month[network_cost] )" -FormatString '$#,0'
  Add-KpiMeasure -Table $measureTable -Name "Processor Cost" -Expression "SUM ( fact_payment_month[processor_cost] )" -FormatString '$#,0'
  Add-KpiMeasure -Table $measureTable -Name "Fraud Loss" -Expression "SUM ( fact_payment_month[fraud_loss] )" -FormatString '$#,0'
  Add-KpiMeasure -Table $measureTable -Name "Incentives Cost" -Expression "SUM ( fact_payment_month[incentives_cost] )" -FormatString '$#,0'
  Add-KpiMeasure -Table $measureTable -Name "Variable Cost" -Expression "SUM ( fact_payment_month[total_cost] )" -FormatString '$#,0'
  Add-KpiMeasure -Table $measureTable -Name "Contribution Margin" -Expression "SUM ( fact_payment_month[contribution_margin] )" -FormatString '$#,0'
  Add-KpiMeasure -Table $measureTable -Name "Take Rate" -Expression "DIVIDE ( [Revenue], [Payment GMV] )" -FormatString '0.0%'
  Add-KpiMeasure -Table $measureTable -Name "Contribution Margin %" -Expression "DIVIDE ( [Contribution Margin], [Revenue] )" -FormatString '0.0%'
  Add-KpiMeasure -Table $measureTable -Name "Cost per Transaction" -Expression "DIVIDE ( [Variable Cost], [Transactions] )" -FormatString '$0.00'
  Add-KpiMeasure -Table $measureTable -Name "Refund Rate" -Expression "DIVIDE ( [Refund Amount], [Payment GMV] )" -FormatString '0.0%'
  Add-KpiMeasure -Table $measureTable -Name "Chargeback Bps" -Expression "DIVIDE ( [Chargeback Amount], [Payment GMV] ) * 10000" -FormatString '0.0'
  Add-KpiMeasure -Table $measureTable -Name "Chargeback Rate" -Expression "DIVIDE ( [Chargeback Count], [Transactions] )" -FormatString '0.00%'
  Add-KpiMeasure -Table $measureTable -Name "Auth Success Rate" -Expression "DIVIDE ( [Successful Transactions], [Successful Transactions] + [Failed Transactions] )" -FormatString '0.0%'
  Add-KpiMeasure -Table $measureTable -Name "Revenue per Transaction" -Expression "DIVIDE ( [Revenue], [Transactions] )" -FormatString '$0.00'
  Add-KpiMeasure -Table $measureTable -Name "Current Month Index" -Expression "COALESCE ( SELECTEDVALUE ( dim_date[month_index] ), MAXX ( ALL ( dim_date ), dim_date[month_index] ) )" -FormatString '#,0'
  Add-KpiMeasure -Table $measureTable -Name "Current GMV" -Expression "VAR CurrentMonth = [Current Month Index] RETURN CALCULATE ( [Payment GMV], FILTER ( ALL ( dim_date ), dim_date[month_index] = CurrentMonth ) )" -FormatString '$#,0'
  Add-KpiMeasure -Table $measureTable -Name "Current Transactions" -Expression "VAR CurrentMonth = [Current Month Index] RETURN CALCULATE ( [Transactions], FILTER ( ALL ( dim_date ), dim_date[month_index] = CurrentMonth ) )" -FormatString '#,0'
  Add-KpiMeasure -Table $measureTable -Name "Current Revenue" -Expression "VAR CurrentMonth = [Current Month Index] RETURN CALCULATE ( [Revenue], FILTER ( ALL ( dim_date ), dim_date[month_index] = CurrentMonth ) )" -FormatString '$#,0'
  Add-KpiMeasure -Table $measureTable -Name "Current Variable Cost" -Expression "VAR CurrentMonth = [Current Month Index] RETURN CALCULATE ( [Variable Cost], FILTER ( ALL ( dim_date ), dim_date[month_index] = CurrentMonth ) )" -FormatString '$#,0'
  Add-KpiMeasure -Table $measureTable -Name "Current Contribution Margin" -Expression "VAR CurrentMonth = [Current Month Index] RETURN CALCULATE ( [Contribution Margin], FILTER ( ALL ( dim_date ), dim_date[month_index] = CurrentMonth ) )" -FormatString '$#,0'
  Add-KpiMeasure -Table $measureTable -Name "Current Take Rate" -Expression "DIVIDE ( [Current Revenue], [Current GMV] )" -FormatString '0.0%'
  Add-KpiMeasure -Table $measureTable -Name "Current CM %" -Expression "DIVIDE ( [Current Contribution Margin], [Current Revenue] )" -FormatString '0.0%'
  Add-KpiMeasure -Table $measureTable -Name "Current Cost per Transaction" -Expression "DIVIDE ( [Current Variable Cost], [Current Transactions] )" -FormatString '$0.00'
  Add-KpiMeasure -Table $measureTable -Name "Previous GMV" -Expression "VAR CurrentMonth = [Current Month Index] RETURN CALCULATE ( [Payment GMV], FILTER ( ALL ( dim_date ), dim_date[month_index] = CurrentMonth - 1 ) )" -FormatString '$#,0'
  Add-KpiMeasure -Table $measureTable -Name "Previous Revenue" -Expression "VAR CurrentMonth = [Current Month Index] RETURN CALCULATE ( [Revenue], FILTER ( ALL ( dim_date ), dim_date[month_index] = CurrentMonth - 1 ) )" -FormatString '$#,0'
  Add-KpiMeasure -Table $measureTable -Name "MoM GMV Growth" -Expression "DIVIDE ( [Current GMV] - [Previous GMV], [Previous GMV] )" -FormatString '0.0%'
  Add-KpiMeasure -Table $measureTable -Name "MoM Revenue Growth" -Expression "DIVIDE ( [Current Revenue] - [Previous Revenue], [Previous Revenue] )" -FormatString '0.0%'
  Add-KpiMeasure -Table $measureTable -Name "Bridge Amount" -Expression "SUM ( fact_fee_bridge[bridge_amount] )" -FormatString '$#,0'
  Add-KpiMeasure -Table $measureTable -Name "Scenario Take Rate Delta Bps" -Expression "SELECTEDVALUE ( dim_scenario[take_rate_delta_bps], 0 )" -FormatString '0'
  Add-KpiMeasure -Table $measureTable -Name "Scenario Cost Delta %" -Expression "SELECTEDVALUE ( dim_scenario[cost_delta_pct], 0 )" -FormatString '0.0%'
  Add-KpiMeasure -Table $measureTable -Name "Scenario Volume Elasticity" -Expression "SELECTEDVALUE ( dim_scenario[volume_elasticity], 0 )" -FormatString '0.0%'
  Add-KpiMeasure -Table $measureTable -Name "Scenario GMV" -Expression "[Current GMV] * ( 1 + [Scenario Volume Elasticity] )" -FormatString '$#,0'
  Add-KpiMeasure -Table $measureTable -Name "Scenario Revenue" -Expression "[Current Revenue] + [Current GMV] * DIVIDE ( [Scenario Take Rate Delta Bps], 10000 )" -FormatString '$#,0'
  Add-KpiMeasure -Table $measureTable -Name "Scenario Variable Cost" -Expression "[Current Variable Cost] * ( 1 + [Scenario Cost Delta %] )" -FormatString '$#,0'
  Add-KpiMeasure -Table $measureTable -Name "Scenario Contribution Margin" -Expression "[Scenario Revenue] - [Scenario Variable Cost]" -FormatString '$#,0'
  Add-KpiMeasure -Table $measureTable -Name "Scenario CM %" -Expression "DIVIDE ( [Scenario Contribution Margin], [Scenario Revenue] )" -FormatString '0.0%'
  Add-KpiMeasure -Table $measureTable -Name "Scenario Margin Uplift" -Expression "[Scenario Contribution Margin] - [Current Contribution Margin]" -FormatString '$#,0'
  Add-KpiMeasure -Table $measureTable -Name "Merchant Rank by CM" -Expression "RANKX ( ALLSELECTED ( dim_merchant[merchant_id] ), [Current Contribution Margin], , DESC, Dense )" -FormatString '#,0'

  $model.SaveChanges()
  $model.RequestRefresh([Microsoft.AnalysisServices.Tabular.RefreshType]::Full)
  $model.SaveChanges()

  $summary = [ordered]@{
    status = "model_pushed"
    port = $portToUse
    database = $database.Name
    tables = @($model.Tables | ForEach-Object { $_.Name })
    table_count = $model.Tables.Count
    relationship_count = $model.Relationships.Count
    measure_count = ($model.Tables | ForEach-Object { $_.Measures.Count } | Measure-Object -Sum).Sum
    project_root = $ProjectRoot
  }
  $summary | ConvertTo-Json -Depth 5
}
finally {
  $server.Disconnect()
}
