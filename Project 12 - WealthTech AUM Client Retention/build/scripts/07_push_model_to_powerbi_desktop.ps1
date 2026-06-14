param(
  [string]$ProjectRoot = "",
  [int]$TargetProcessId = 0
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
  throw "Power BI Desktop EXE bin folder not found."
}

function Get-PowerBiSession([int]$TargetProcessId = 0) {
  $infoText = pbi-tools info 2>&1 | Out-String
  $jsonStart = $infoText.IndexOf("{")
  if ($jsonStart -lt 0) { throw "pbi-tools info did not return a JSON payload." }
  $info = $infoText.Substring($jsonStart) | ConvertFrom-Json
  if (-not $info.pbiSessions -or $info.pbiSessions.Count -eq 0) {
    throw "No active Power BI Desktop local Analysis Services session found. Launch Power BI Desktop first."
  }
  $sessions = @($info.pbiSessions)
  if ($TargetProcessId -gt 0) {
    $target = @($sessions | Where-Object { $_.ProcessId -eq $TargetProcessId })
    if ($target.Count -eq 0) { throw "No active Power BI Desktop session found for TargetProcessId $TargetProcessId." }
    return $target[0]
  }
  $blank = @($sessions | Where-Object { -not $_.PbixPath } | Sort-Object ProcessId -Descending | Select-Object -First 1)
  if ($blank.Count -gt 0) { return $blank[0] }
  return @($sessions | Sort-Object ProcessId -Descending | Select-Object -First 1)[0]
}

function Get-ColumnType([string]$ColumnName) {
  $lower = $ColumnName.ToLowerInvariant()
  if ($lower -match "(monthstart|joinmonth|date)$") { return [Microsoft.AnalysisServices.Tabular.DataType]::DateTime }
  if ($lower -match "(monthkey|monthindex|year|flag|clients|count)$") { return [Microsoft.AnalysisServices.Tabular.DataType]::Int64 }
  if ($lower -match "(aum|inflow|outflow|money|effect|revenue|return|pct|score|bps|rate|share|amount|risk)") { return [Microsoft.AnalysisServices.Tabular.DataType]::Double }
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
  if ($type -in @([Microsoft.AnalysisServices.Tabular.DataType]::Double, [Microsoft.AnalysisServices.Tabular.DataType]::Int64) -and $TableName.StartsWith("Fact")) {
    if ($ColumnName.ToLowerInvariant() -notmatch "(id|key|flag|pct|score|bps|rate)$") {
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
    if ($columnName.ToLowerInvariant() -match "(clientid|actionid)$") { $column.SummarizeBy = [Microsoft.AnalysisServices.Tabular.AggregateFunction]::None }
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
$session = Get-PowerBiSession -TargetProcessId $TargetProcessId
$server = New-Object Microsoft.AnalysisServices.Tabular.Server
$server.Connect("localhost:$($session.Port)")
$database = $server.Databases[0]
$model = $database.Model
$model.Relationships.Clear()
$model.Tables.Clear()

$tableSpecs = @(
  @{Name="DimDate"; File="dim_date.csv"},
  @{Name="DimClient"; File="dim_client.csv"},
  @{Name="DimPortfolio"; File="dim_portfolio.csv"},
  @{Name="FactAUMMonthly"; File="fact_aum_monthly.csv"},
  @{Name="FactAllocationMonthly"; File="fact_allocation_monthly.csv"},
  @{Name="FactRetentionActions"; File="fact_retention_actions.csv"}
)
foreach ($spec in $tableSpecs) { Add-ImportTable $model $spec.Name $spec.File }

Add-Relationship $model "AUM_Date" "FactAUMMonthly" "MonthStart" "DimDate" "MonthStart"
Add-Relationship $model "Allocation_Date" "FactAllocationMonthly" "MonthStart" "DimDate" "MonthStart"
Add-Relationship $model "Actions_Date" "FactRetentionActions" "MonthStart" "DimDate" "MonthStart"
Add-Relationship $model "AUM_Client" "FactAUMMonthly" "ClientID" "DimClient" "ClientID"
Add-Relationship $model "Allocation_Client" "FactAllocationMonthly" "ClientID" "DimClient" "ClientID"
Add-Relationship $model "Actions_Client" "FactRetentionActions" "ClientID" "DimClient" "ClientID"
Add-Relationship $model "AUM_Portfolio" "FactAUMMonthly" "ModelPortfolio" "DimPortfolio" "ModelPortfolio"
Add-Relationship $model "Allocation_Portfolio" "FactAllocationMonthly" "ModelPortfolio" "DimPortfolio" "ModelPortfolio"

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

Add-Measure $kpi "Latest Month" "MAX ( DimDate[MonthStart] )" 'yyyy-mm-dd'
Add-Measure $kpi "Total AUM" "SUM ( FactAUMMonthly[EndingAUM] )" '$#,0,,.0M'
Add-Measure $kpi "Beginning AUM" "SUM ( FactAUMMonthly[BeginningAUM] )" '$#,0,,.0M'
Add-Measure $kpi "Inflows" "SUM ( FactAUMMonthly[Inflows] )" '$#,0,,.0M'
Add-Measure $kpi "Outflows" "SUM ( FactAUMMonthly[Outflows] )" '$#,0,,.0M'
Add-Measure $kpi "Net New Money" "SUM ( FactAUMMonthly[NetNewMoney] )" '$#,0,,.0M'
Add-Measure $kpi "Market Effect" "SUM ( FactAUMMonthly[MarketEffect] )" '$#,0,,.0M'
Add-Measure $kpi "Advisory Revenue" "SUM ( FactAUMMonthly[AdvisoryRevenue] )" '$#,0,.0K'
Add-Measure $kpi "Allocation Amount" "SUM ( FactAllocationMonthly[AllocationAmount] )" '$#,0,,.0M'
Add-Measure $kpi "Active Clients" "CALCULATE ( DISTINCTCOUNT ( FactAUMMonthly[ClientID] ), FactAUMMonthly[ActiveClientFlag] = 1 )" '#,0'
Add-Measure $kpi "Net Flow Rate" "DIVIDE ( [Net New Money], [Beginning AUM] )" '0.0%'
Add-Measure $kpi "Portfolio Return %" "DIVIDE ( SUMX ( FactAUMMonthly, FactAUMMonthly[EndingAUM] * FactAUMMonthly[PortfolioReturnPct] ), [Total AUM] )" '0.0%'
Add-Measure $kpi "Benchmark Return %" "DIVIDE ( SUMX ( FactAUMMonthly, FactAUMMonthly[EndingAUM] * FactAUMMonthly[BenchmarkReturnPct] ), [Total AUM] )" '0.0%'
Add-Measure $kpi "Alpha %" "[Portfolio Return %] - [Benchmark Return %]" '0.0%'
Add-Measure $kpi "Risk Mismatch Clients" "CALCULATE ( DISTINCTCOUNT ( FactAUMMonthly[ClientID] ), FactAUMMonthly[RiskMismatchFlag] = 1 )" '#,0'
Add-Measure $kpi "Risk Mismatch Rate" "DIVIDE ( [Risk Mismatch Clients], [Active Clients] )" '0.0%'
Add-Measure $kpi "Rebalance Needed Clients" "CALCULATE ( DISTINCTCOUNT ( FactAUMMonthly[ClientID] ), FactAUMMonthly[RebalanceNeededFlag] = 1 )" '#,0'
Add-Measure $kpi "Rebalance Needed Rate" "DIVIDE ( [Rebalance Needed Clients], [Active Clients] )" '0.0%'
Add-Measure $kpi "High Churn Risk Clients" "CALCULATE ( DISTINCTCOUNT ( FactAUMMonthly[ClientID] ), FactAUMMonthly[ChurnRiskScore] >= 0.70 )" '#,0'
Add-Measure $kpi "High Outflow Risk Clients" "CALCULATE ( DISTINCTCOUNT ( FactAUMMonthly[ClientID] ), FactAUMMonthly[OutflowRiskScore] >= 0.65 )" '#,0'
Add-Measure $kpi "Churn Risk AUM" "SUMX ( FILTER ( FactAUMMonthly, FactAUMMonthly[ChurnRiskScore] >= 0.70 ), FactAUMMonthly[EndingAUM] )" '$#,0,,.0M'
Add-Measure $kpi "Churn Risk AUM Rate" "DIVIDE ( [Churn Risk AUM], [Total AUM] )" '0.0%'
Add-Measure $kpi "Top 10 Client AUM Share" "VAR t = TOPN ( 10, SUMMARIZE ( DimClient, DimClient[ClientID], ""AUMValue"", [Total AUM] ), [AUMValue], DESC ) RETURN DIVIDE ( SUMX ( t, [AUMValue] ), [Total AUM] )" '0.0%'
Add-Measure $kpi "Retention Action AUM" "SUM ( FactRetentionActions[ExpectedRetainedAUM] )" '$#,0,,.0M'
Add-Measure $kpi "Open Retention Actions" "COUNTROWS ( FactRetentionActions )" '#,0'

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
  output_model_pbix = "not_created_requires_desktop_save"
  expected_save_path = (Join-Path $ProjectRoot "output\dashboard_model.pbix")
}
$result | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $QaRoot "scripted_model_push.json") -Encoding UTF8
$server.Disconnect()
$result | ConvertTo-Json -Depth 8
