param(
  [int]$Port = 0,
  [string]$ProjectRoot = "C:\Users\Win\OneDrive\Codex\Portfolio\BI\Project 16 - Manufacturing Cost FP&A",
  [string]$PbixPath = "C:\Users\Win\OneDrive\Codex\Portfolio\BI\Project 16 - Manufacturing Cost FP&A\output\dashboard_final.pbix"
)

$ErrorActionPreference = "Stop"

function Resolve-PowerBIPort {
  if ($Port -gt 0) { return $Port }
  $infoRaw = & pbi-tools info 2>&1 | Out-String
  $jsonStart = $infoRaw.IndexOf("{")
  if ($jsonStart -lt 0) { throw "Could not find JSON payload in pbi-tools info output." }
  $info = $infoRaw.Substring($jsonStart) | ConvertFrom-Json
  $resolvedPbix = [System.IO.Path]::GetFullPath($PbixPath)
  $matches = @($info.pbiSessions | Where-Object { $_.PbixPath -and ([System.IO.Path]::GetFullPath($_.PbixPath) -ieq $resolvedPbix) })
  if ($matches.Count -ne 1) {
    $sessionText = ($info.pbiSessions | ForEach-Object { "PID=$($_.ProcessId) Port=$($_.Port) PbixPath=$($_.PbixPath)" }) -join "`n"
    throw "Expected exactly one Project 16 Power BI session for $resolvedPbix. Found $($matches.Count). Sessions:`n$sessionText"
  }
  return [int]$matches[0].Port
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
    if (-not (Test-Path $path)) { throw "Missing Power BI TOM assembly: $path" }
    [void][System.Reflection.Assembly]::LoadFrom($path)
  }
}

function Escape-MPath([string]$Path) {
  return $Path.Replace("\", "\\").Replace('"', '""')
}

function Get-ColumnType([string]$ColumnName) {
  $intCols = @("date_key", "year", "month_no", "month_index", "is_latest_complete_month", "bridge_order")
  $dateCols = @("month_start_date")
  $doubleCols = @(
    "productivity_index", "labor_rate_usd", "fixed_overhead_rate_usd", "material_price_index",
    "standard_price_usd", "standard_material_cost_usd", "standard_labor_hours", "standard_machine_hours", "complexity_index", "base_monthly_units",
    "monthly_capacity_units", "shift_count", "material_cost_reduction_pct", "labor_efficiency_gain_pct", "overhead_absorption_gain_pct", "scrap_reduction_pct", "volume_delta_pct",
    "budget_units", "produced_units", "good_units", "scrap_units", "rework_units", "capacity_units", "available_hours", "run_hours", "downtime_hours",
    "actual_revenue", "budget_revenue", "standard_material_cost", "standard_labor_cost", "standard_overhead_cost", "standard_cogs",
    "actual_material_cost", "actual_labor_cost", "actual_overhead_cost", "scrap_cost", "rework_cost", "actual_cogs",
    "material_variance", "labor_variance", "overhead_variance", "yield_loss_cost", "gross_margin", "inventory_units", "inventory_value", "slow_moving_inventory_value",
    "bridge_amount"
  )
  if ($intCols -contains $ColumnName) { return "Int64" }
  if ($dateCols -contains $ColumnName) { return "DateTime" }
  if ($doubleCols -contains $ColumnName) { return "Double" }
  return "String"
}

function New-MExpression {
  param([string]$CsvPath, [array]$Columns)
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
  try { $header = $reader.ReadLine() } finally { $reader.Close() }
  if (-not $header) { throw "CSV has no header: $CsvPath" }
  return $header.Split(",") | ForEach-Object { [ordered]@{ Name = $_.Trim('"'); Type = Get-ColumnType $_.Trim('"') } }
}

function Add-ImportTable {
  param([Microsoft.AnalysisServices.Tabular.Model]$Model, [string]$Name, [string]$CsvPath)
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
    Source = #table(type table [Measure Group = text], {"Manufacturing Cost FP&A"})
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
  param([Microsoft.AnalysisServices.Tabular.Model]$Model, [string]$FromTable, [string]$FromColumn, [string]$ToTable, [string]$ToColumn)
  $relationship = New-Object Microsoft.AnalysisServices.Tabular.SingleColumnRelationship
  $relationship.Name = "rel_${FromTable}_${FromColumn}_${ToTable}_${ToColumn}"
  $relationship.FromColumn = $Model.Tables[$FromTable].Columns[$FromColumn]
  $relationship.ToColumn = $Model.Tables[$ToTable].Columns[$ToColumn]
  $relationship.CrossFilteringBehavior = [Microsoft.AnalysisServices.Tabular.CrossFilteringBehavior]::OneDirection
  $Model.Relationships.Add($relationship) | Out-Null
}

function Add-KpiMeasure {
  param([Microsoft.AnalysisServices.Tabular.Table]$Table, [string]$Name, [string]$Expression, [string]$FormatString = "")
  $measure = New-Object Microsoft.AnalysisServices.Tabular.Measure
  $measure.Name = $Name
  $measure.Expression = $Expression
  if ($FormatString) { $measure.FormatString = $FormatString }
  $Table.Measures.Add($measure) | Out-Null
}

$portToUse = Resolve-PowerBIPort
Import-PowerBIAssemblies
$prepared = Join-Path $ProjectRoot "data\prepared"
$tableNames = @("dim_date", "dim_spark_date", "dim_plant", "dim_product", "dim_line", "dim_scenario", "fact_manufacturing_month", "fact_cost_variance_bridge")

$server = New-Object Microsoft.AnalysisServices.Tabular.Server
$server.Connect("localhost:$portToUse")
try {
  if ($server.Databases.Count -lt 1) { throw "Connected to Power BI Desktop, but no database was found." }
  $database = $server.Databases[0]
  $model = $database.Model
  while ($model.Relationships.Count -gt 0) { $model.Relationships.Remove($model.Relationships[0]) }
  while ($model.Tables.Count -gt 0) { $model.Tables.Remove($model.Tables[0]) }

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
  Add-Relationship -Model $model -FromTable "fact_manufacturing_month" -FromColumn "year_month" -ToTable "dim_date" -ToColumn "year_month"
  Add-Relationship -Model $model -FromTable "fact_manufacturing_month" -FromColumn "plant_id" -ToTable "dim_plant" -ToColumn "plant_id"
  Add-Relationship -Model $model -FromTable "fact_manufacturing_month" -FromColumn "line_id" -ToTable "dim_line" -ToColumn "line_id"
  Add-Relationship -Model $model -FromTable "fact_manufacturing_month" -FromColumn "product_id" -ToTable "dim_product" -ToColumn "product_id"
  Add-Relationship -Model $model -FromTable "fact_cost_variance_bridge" -FromColumn "year_month" -ToTable "dim_date" -ToColumn "year_month"

  Add-KpiMeasure -Table $measureTable -Name "Actual Revenue" -Expression "SUM ( fact_manufacturing_month[actual_revenue] )" -FormatString "$#,0"
  Add-KpiMeasure -Table $measureTable -Name "Budget Revenue" -Expression "SUM ( fact_manufacturing_month[budget_revenue] )" -FormatString "$#,0"
  Add-KpiMeasure -Table $measureTable -Name "Actual COGS" -Expression "SUM ( fact_manufacturing_month[actual_cogs] )" -FormatString "$#,0"
  Add-KpiMeasure -Table $measureTable -Name "Standard COGS" -Expression "SUM ( fact_manufacturing_month[standard_cogs] )" -FormatString "$#,0"
  Add-KpiMeasure -Table $measureTable -Name "Actual Material Cost" -Expression "SUM ( fact_manufacturing_month[actual_material_cost] )" -FormatString "$#,0"
  Add-KpiMeasure -Table $measureTable -Name "Actual Labor Cost" -Expression "SUM ( fact_manufacturing_month[actual_labor_cost] )" -FormatString "$#,0"
  Add-KpiMeasure -Table $measureTable -Name "Actual Overhead Cost" -Expression "SUM ( fact_manufacturing_month[actual_overhead_cost] )" -FormatString "$#,0"
  Add-KpiMeasure -Table $measureTable -Name "Scrap Cost" -Expression "SUM ( fact_manufacturing_month[scrap_cost] )" -FormatString "$#,0"
  Add-KpiMeasure -Table $measureTable -Name "Rework Cost" -Expression "SUM ( fact_manufacturing_month[rework_cost] )" -FormatString "$#,0"
  Add-KpiMeasure -Table $measureTable -Name "Yield Loss Cost" -Expression "SUM ( fact_manufacturing_month[yield_loss_cost] )" -FormatString "$#,0"
  Add-KpiMeasure -Table $measureTable -Name "Material Variance" -Expression "SUM ( fact_manufacturing_month[material_variance] )" -FormatString "$#,0"
  Add-KpiMeasure -Table $measureTable -Name "Labor Variance" -Expression "SUM ( fact_manufacturing_month[labor_variance] )" -FormatString "$#,0"
  Add-KpiMeasure -Table $measureTable -Name "Overhead Variance" -Expression "SUM ( fact_manufacturing_month[overhead_variance] )" -FormatString "$#,0"
  Add-KpiMeasure -Table $measureTable -Name "Cost Variance vs Standard" -Expression "[Actual COGS] - [Standard COGS]" -FormatString "$#,0"
  Add-KpiMeasure -Table $measureTable -Name "Gross Margin" -Expression "[Actual Revenue] - [Actual COGS]" -FormatString "$#,0"
  Add-KpiMeasure -Table $measureTable -Name "Gross Margin %" -Expression "DIVIDE ( [Gross Margin], [Actual Revenue] )" -FormatString "0.0%"
  Add-KpiMeasure -Table $measureTable -Name "Produced Units" -Expression "SUM ( fact_manufacturing_month[produced_units] )" -FormatString "#,0"
  Add-KpiMeasure -Table $measureTable -Name "Good Units" -Expression "SUM ( fact_manufacturing_month[good_units] )" -FormatString "#,0"
  Add-KpiMeasure -Table $measureTable -Name "Scrap Units" -Expression "SUM ( fact_manufacturing_month[scrap_units] )" -FormatString "#,0"
  Add-KpiMeasure -Table $measureTable -Name "Rework Units" -Expression "SUM ( fact_manufacturing_month[rework_units] )" -FormatString "#,0"
  Add-KpiMeasure -Table $measureTable -Name "Yield %" -Expression "DIVIDE ( [Good Units], [Produced Units] )" -FormatString "0.0%"
  Add-KpiMeasure -Table $measureTable -Name "Scrap Rate" -Expression "DIVIDE ( [Scrap Units], [Produced Units] )" -FormatString "0.0%"
  Add-KpiMeasure -Table $measureTable -Name "Unit Cost" -Expression "DIVIDE ( [Actual COGS], [Good Units] )" -FormatString "$0.00"
  Add-KpiMeasure -Table $measureTable -Name "Standard Unit Cost" -Expression "DIVIDE ( [Standard COGS], [Good Units] )" -FormatString "$0.00"
  Add-KpiMeasure -Table $measureTable -Name "Run Hours" -Expression "SUM ( fact_manufacturing_month[run_hours] )" -FormatString "#,0"
  Add-KpiMeasure -Table $measureTable -Name "Available Hours" -Expression "SUM ( fact_manufacturing_month[available_hours] )" -FormatString "#,0"
  Add-KpiMeasure -Table $measureTable -Name "Downtime Hours" -Expression "SUM ( fact_manufacturing_month[downtime_hours] )" -FormatString "#,0"
  Add-KpiMeasure -Table $measureTable -Name "Utilization %" -Expression "DIVIDE ( [Run Hours], [Available Hours] )" -FormatString "0.0%"
  Add-KpiMeasure -Table $measureTable -Name "Capacity Units" -Expression "SUM ( fact_manufacturing_month[capacity_units] )" -FormatString "#,0"
  Add-KpiMeasure -Table $measureTable -Name "Capacity Gap Units" -Expression "[Capacity Units] - [Produced Units]" -FormatString "#,0"
  Add-KpiMeasure -Table $measureTable -Name "Inventory Value" -Expression "SUM ( fact_manufacturing_month[inventory_value] )" -FormatString "$#,0"
  Add-KpiMeasure -Table $measureTable -Name "Slow Moving Inventory" -Expression "SUM ( fact_manufacturing_month[slow_moving_inventory_value] )" -FormatString "$#,0"
  Add-KpiMeasure -Table $measureTable -Name "Inventory Days" -Expression "DIVIDE ( [Inventory Value], [Actual COGS] ) * 30" -FormatString "0.0"
  Add-KpiMeasure -Table $measureTable -Name "Bridge Amount" -Expression "SUM ( fact_cost_variance_bridge[bridge_amount] )" -FormatString "$#,0"
  Add-KpiMeasure -Table $measureTable -Name "Current Month Index" -Expression "COALESCE ( SELECTEDVALUE ( dim_date[month_index] ), MAXX ( ALL ( dim_date ), dim_date[month_index] ) )" -FormatString ""
  Add-KpiMeasure -Table $measureTable -Name "Current Revenue" -Expression "VAR CurrentMonth = [Current Month Index] RETURN CALCULATE ( [Actual Revenue], FILTER ( ALL ( dim_date ), dim_date[month_index] = CurrentMonth ) )" -FormatString "$#,0"
  Add-KpiMeasure -Table $measureTable -Name "Current Actual COGS" -Expression "VAR CurrentMonth = [Current Month Index] RETURN CALCULATE ( [Actual COGS], FILTER ( ALL ( dim_date ), dim_date[month_index] = CurrentMonth ) )" -FormatString "$#,0"
  Add-KpiMeasure -Table $measureTable -Name "Current Standard COGS" -Expression "VAR CurrentMonth = [Current Month Index] RETURN CALCULATE ( [Standard COGS], FILTER ( ALL ( dim_date ), dim_date[month_index] = CurrentMonth ) )" -FormatString "$#,0"
  Add-KpiMeasure -Table $measureTable -Name "Current Gross Margin" -Expression "VAR CurrentMonth = [Current Month Index] RETURN CALCULATE ( [Gross Margin], FILTER ( ALL ( dim_date ), dim_date[month_index] = CurrentMonth ) )" -FormatString "$#,0"
  Add-KpiMeasure -Table $measureTable -Name "Current GM %" -Expression "DIVIDE ( [Current Gross Margin], [Current Revenue] )" -FormatString "0.0%"
  Add-KpiMeasure -Table $measureTable -Name "Current Cost Variance" -Expression "[Current Actual COGS] - [Current Standard COGS]" -FormatString "$#,0"
  Add-KpiMeasure -Table $measureTable -Name "Current Unit Cost" -Expression "VAR CurrentMonth = [Current Month Index] RETURN CALCULATE ( [Unit Cost], FILTER ( ALL ( dim_date ), dim_date[month_index] = CurrentMonth ) )" -FormatString "$0.00"
  Add-KpiMeasure -Table $measureTable -Name "Current Yield %" -Expression "VAR CurrentMonth = [Current Month Index] RETURN CALCULATE ( [Yield %], FILTER ( ALL ( dim_date ), dim_date[month_index] = CurrentMonth ) )" -FormatString "0.0%"
  Add-KpiMeasure -Table $measureTable -Name "Current Scrap Rate" -Expression "VAR CurrentMonth = [Current Month Index] RETURN CALCULATE ( [Scrap Rate], FILTER ( ALL ( dim_date ), dim_date[month_index] = CurrentMonth ) )" -FormatString "0.0%"
  Add-KpiMeasure -Table $measureTable -Name "Current Utilization %" -Expression "VAR CurrentMonth = [Current Month Index] RETURN CALCULATE ( [Utilization %], FILTER ( ALL ( dim_date ), dim_date[month_index] = CurrentMonth ) )" -FormatString "0.0%"
  Add-KpiMeasure -Table $measureTable -Name "Current Inventory Value" -Expression "VAR CurrentMonth = [Current Month Index] RETURN CALCULATE ( [Inventory Value], FILTER ( ALL ( dim_date ), dim_date[month_index] = CurrentMonth ) )" -FormatString "$#,0"
  Add-KpiMeasure -Table $measureTable -Name "Current Inventory Days" -Expression "VAR CurrentMonth = [Current Month Index] RETURN CALCULATE ( [Inventory Days], FILTER ( ALL ( dim_date ), dim_date[month_index] = CurrentMonth ) )" -FormatString "0.0"
  Add-KpiMeasure -Table $measureTable -Name "Current Material Variance" -Expression "VAR CurrentMonth = [Current Month Index] RETURN CALCULATE ( [Material Variance], FILTER ( ALL ( dim_date ), dim_date[month_index] = CurrentMonth ) )" -FormatString "$#,0"
  Add-KpiMeasure -Table $measureTable -Name "Current Labor Variance" -Expression "VAR CurrentMonth = [Current Month Index] RETURN CALCULATE ( [Labor Variance], FILTER ( ALL ( dim_date ), dim_date[month_index] = CurrentMonth ) )" -FormatString "$#,0"
  Add-KpiMeasure -Table $measureTable -Name "Current Overhead Variance" -Expression "VAR CurrentMonth = [Current Month Index] RETURN CALCULATE ( [Overhead Variance], FILTER ( ALL ( dim_date ), dim_date[month_index] = CurrentMonth ) )" -FormatString "$#,0"
  Add-KpiMeasure -Table $measureTable -Name "Current Yield Loss Cost" -Expression "VAR CurrentMonth = [Current Month Index] RETURN CALCULATE ( [Yield Loss Cost], FILTER ( ALL ( dim_date ), dim_date[month_index] = CurrentMonth ) )" -FormatString "$#,0"
  Add-KpiMeasure -Table $measureTable -Name "Current Capacity Gap Units" -Expression "VAR CurrentMonth = [Current Month Index] RETURN CALCULATE ( [Capacity Gap Units], FILTER ( ALL ( dim_date ), dim_date[month_index] = CurrentMonth ) )" -FormatString "#,0"
  Add-KpiMeasure -Table $measureTable -Name "Scenario Material Cost Reduction %" -Expression "SELECTEDVALUE ( dim_scenario[material_cost_reduction_pct], 0 )" -FormatString "0.0%"
  Add-KpiMeasure -Table $measureTable -Name "Scenario Labor Efficiency Gain %" -Expression "SELECTEDVALUE ( dim_scenario[labor_efficiency_gain_pct], 0 )" -FormatString "0.0%"
  Add-KpiMeasure -Table $measureTable -Name "Scenario OH Absorption Gain %" -Expression "SELECTEDVALUE ( dim_scenario[overhead_absorption_gain_pct], 0 )" -FormatString "0.0%"
  Add-KpiMeasure -Table $measureTable -Name "Scenario Scrap Reduction %" -Expression "SELECTEDVALUE ( dim_scenario[scrap_reduction_pct], 0 )" -FormatString "0.0%"
  Add-KpiMeasure -Table $measureTable -Name "Scenario Volume Delta %" -Expression "SELECTEDVALUE ( dim_scenario[volume_delta_pct], 0 )" -FormatString "0.0%"
  Add-KpiMeasure -Table $measureTable -Name "Scenario Cost Savings" -Expression "[Current Material Variance] * [Scenario Material Cost Reduction %] + [Current Labor Variance] * [Scenario Labor Efficiency Gain %] + [Current Overhead Variance] * [Scenario OH Absorption Gain %] + [Current Yield Loss Cost] * [Scenario Scrap Reduction %]" -FormatString "$#,0"
  Add-KpiMeasure -Table $measureTable -Name "Scenario Gross Margin" -Expression "[Current Gross Margin] + [Scenario Cost Savings] + [Current Gross Margin] * [Scenario Volume Delta %]" -FormatString "$#,0"
  Add-KpiMeasure -Table $measureTable -Name "Scenario GM %" -Expression "DIVIDE ( [Scenario Gross Margin], [Current Revenue] * ( 1 + [Scenario Volume Delta %] ) )" -FormatString "0.0%"
  Add-KpiMeasure -Table $measureTable -Name "Scenario EBITDA Uplift" -Expression "[Scenario Gross Margin] - [Current Gross Margin]" -FormatString "$#,0"
  Add-KpiMeasure -Table $measureTable -Name "Spark Revenue Trend" -Expression "VAR SparkMonth = SELECTEDVALUE ( dim_spark_date[year_month] ) RETURN CALCULATE ( [Actual Revenue], REMOVEFILTERS ( dim_date ), TREATAS ( { SparkMonth }, dim_date[year_month] ) )" -FormatString "$#,0"
  Add-KpiMeasure -Table $measureTable -Name "Spark Gross Margin Trend" -Expression "VAR SparkMonth = SELECTEDVALUE ( dim_spark_date[year_month] ) RETURN CALCULATE ( [Gross Margin], REMOVEFILTERS ( dim_date ), TREATAS ( { SparkMonth }, dim_date[year_month] ) )" -FormatString "$#,0"
  Add-KpiMeasure -Table $measureTable -Name "Spark GM % Trend" -Expression "VAR SparkMonth = SELECTEDVALUE ( dim_spark_date[year_month] ) RETURN CALCULATE ( [Gross Margin %], REMOVEFILTERS ( dim_date ), TREATAS ( { SparkMonth }, dim_date[year_month] ) )" -FormatString "0.0%"
  Add-KpiMeasure -Table $measureTable -Name "Spark Cost Variance Trend" -Expression "VAR SparkMonth = SELECTEDVALUE ( dim_spark_date[year_month] ) RETURN CALCULATE ( [Cost Variance vs Standard], REMOVEFILTERS ( dim_date ), TREATAS ( { SparkMonth }, dim_date[year_month] ) )" -FormatString "$#,0"
  Add-KpiMeasure -Table $measureTable -Name "Spark Unit Cost Trend" -Expression "VAR SparkMonth = SELECTEDVALUE ( dim_spark_date[year_month] ) RETURN CALCULATE ( [Unit Cost], REMOVEFILTERS ( dim_date ), TREATAS ( { SparkMonth }, dim_date[year_month] ) )" -FormatString "$0.00"
  Add-KpiMeasure -Table $measureTable -Name "Spark Yield Trend" -Expression "VAR SparkMonth = SELECTEDVALUE ( dim_spark_date[year_month] ) RETURN CALCULATE ( [Yield %], REMOVEFILTERS ( dim_date ), TREATAS ( { SparkMonth }, dim_date[year_month] ) )" -FormatString "0.0%"
  Add-KpiMeasure -Table $measureTable -Name "Spark Material Variance Trend" -Expression "VAR SparkMonth = SELECTEDVALUE ( dim_spark_date[year_month] ) RETURN CALCULATE ( [Material Variance], REMOVEFILTERS ( dim_date ), TREATAS ( { SparkMonth }, dim_date[year_month] ) )" -FormatString "$#,0"
  Add-KpiMeasure -Table $measureTable -Name "Spark Labor Variance Trend" -Expression "VAR SparkMonth = SELECTEDVALUE ( dim_spark_date[year_month] ) RETURN CALCULATE ( [Labor Variance], REMOVEFILTERS ( dim_date ), TREATAS ( { SparkMonth }, dim_date[year_month] ) )" -FormatString "$#,0"
  Add-KpiMeasure -Table $measureTable -Name "Spark Overhead Variance Trend" -Expression "VAR SparkMonth = SELECTEDVALUE ( dim_spark_date[year_month] ) RETURN CALCULATE ( [Overhead Variance], REMOVEFILTERS ( dim_date ), TREATAS ( { SparkMonth }, dim_date[year_month] ) )" -FormatString "$#,0"
  Add-KpiMeasure -Table $measureTable -Name "Spark Yield Loss Trend" -Expression "VAR SparkMonth = SELECTEDVALUE ( dim_spark_date[year_month] ) RETURN CALCULATE ( [Yield Loss Cost], REMOVEFILTERS ( dim_date ), TREATAS ( { SparkMonth }, dim_date[year_month] ) )" -FormatString "$#,0"
  Add-KpiMeasure -Table $measureTable -Name "Spark Actual COGS Trend" -Expression "VAR SparkMonth = SELECTEDVALUE ( dim_spark_date[year_month] ) RETURN CALCULATE ( [Actual COGS], REMOVEFILTERS ( dim_date ), TREATAS ( { SparkMonth }, dim_date[year_month] ) )" -FormatString "$#,0"
  Add-KpiMeasure -Table $measureTable -Name "Spark Standard COGS Trend" -Expression "VAR SparkMonth = SELECTEDVALUE ( dim_spark_date[year_month] ) RETURN CALCULATE ( [Standard COGS], REMOVEFILTERS ( dim_date ), TREATAS ( { SparkMonth }, dim_date[year_month] ) )" -FormatString "$#,0"
  Add-KpiMeasure -Table $measureTable -Name "Spark Scrap Rate Trend" -Expression "VAR SparkMonth = SELECTEDVALUE ( dim_spark_date[year_month] ) RETURN CALCULATE ( [Scrap Rate], REMOVEFILTERS ( dim_date ), TREATAS ( { SparkMonth }, dim_date[year_month] ) )" -FormatString "0.0%"
  Add-KpiMeasure -Table $measureTable -Name "Spark Utilization Trend" -Expression "VAR SparkMonth = SELECTEDVALUE ( dim_spark_date[year_month] ) RETURN CALCULATE ( [Utilization %], REMOVEFILTERS ( dim_date ), TREATAS ( { SparkMonth }, dim_date[year_month] ) )" -FormatString "0.0%"
  Add-KpiMeasure -Table $measureTable -Name "Spark Capacity Gap Trend" -Expression "VAR SparkMonth = SELECTEDVALUE ( dim_spark_date[year_month] ) RETURN CALCULATE ( [Capacity Gap Units], REMOVEFILTERS ( dim_date ), TREATAS ( { SparkMonth }, dim_date[year_month] ) )" -FormatString "#,0"
  Add-KpiMeasure -Table $measureTable -Name "Spark Inventory Value Trend" -Expression "VAR SparkMonth = SELECTEDVALUE ( dim_spark_date[year_month] ) RETURN CALCULATE ( [Inventory Value], REMOVEFILTERS ( dim_date ), TREATAS ( { SparkMonth }, dim_date[year_month] ) )" -FormatString "$#,0"
  Add-KpiMeasure -Table $measureTable -Name "Spark Inventory Days Trend" -Expression "VAR SparkMonth = SELECTEDVALUE ( dim_spark_date[year_month] ) RETURN CALCULATE ( [Inventory Days], REMOVEFILTERS ( dim_date ), TREATAS ( { SparkMonth }, dim_date[year_month] ) )" -FormatString "0.0"
  Add-KpiMeasure -Table $measureTable -Name "Spark Scenario EBITDA Uplift Trend" -Expression "VAR SparkMonth = SELECTEDVALUE ( dim_spark_date[year_month] ) RETURN CALCULATE ( [Scenario EBITDA Uplift], REMOVEFILTERS ( dim_date ), TREATAS ( { SparkMonth }, dim_date[year_month] ) )" -FormatString "$#,0"

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
    pbix_path = $PbixPath
  }
  $summary | ConvertTo-Json -Depth 5
}
finally {
  $server.Disconnect()
}
