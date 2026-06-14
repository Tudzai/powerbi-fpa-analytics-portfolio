$ErrorActionPreference = "Stop"

$ProjectRoot = "C:\Users\Win\OneDrive\Codex\Portfolio\BI\Project 01 - Monthly FP&A Performance Pack"
$PreparedRoot = Join-Path $ProjectRoot "data\prepared"
$PowerBiBin = "C:\Program Files\WindowsApps\Microsoft.MicrosoftPowerBIDesktop_2.154.1260.0_x64__8wekyb3d8bbwe\bin"

Add-Type -Path (Join-Path $PowerBiBin "Microsoft.PowerBI.Amo.dll") -ErrorAction SilentlyContinue

function Get-PowerBiPort {
  $pbi = Get-Process PBIDesktop -ErrorAction SilentlyContinue | Select-Object -First 1
  if (-not $pbi) {
    throw "Power BI Desktop is not running."
  }
  $msmd = Get-Process msmdsrv -ErrorAction SilentlyContinue | Sort-Object StartTime -Descending | Select-Object -First 1
  if (-not $msmd) {
    throw "Power BI Desktop local Analysis Services engine is not running."
  }
  $conn = Get-NetTCPConnection -OwningProcess $msmd.Id -State Listen -ErrorAction SilentlyContinue |
    Where-Object { $_.LocalAddress -in @("127.0.0.1", "::1") } |
    Sort-Object LocalPort |
    Select-Object -First 1
  if (-not $conn) {
    throw "Could not locate local Analysis Services port for Power BI Desktop."
  }
  return $conn.LocalPort
}

function New-MExpression($FileName) {
  $path = Join-Path $PreparedRoot $FileName
  $escaped = $path.Replace("\", "\\")
  return @"
let
    Source = Csv.Document(File.Contents("$escaped"), [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]),
    PromotedHeaders = Table.PromoteHeaders(Source, [PromoteAllScalars=true])
in
    PromotedHeaders
"@
}

function Add-ImportTable($Model, $Name, $FileName, $Columns) {
  $table = New-Object Microsoft.AnalysisServices.Tabular.Table
  $table.Name = $Name
  $Model.Tables.Add($table)

  foreach ($columnDef in $Columns) {
    $column = New-Object Microsoft.AnalysisServices.Tabular.DataColumn
    $column.Name = $columnDef.Name
    $column.SourceColumn = $columnDef.Name
    $column.DataType = $columnDef.Type
    $column.SummarizeBy = $columnDef.SummarizeBy
    if ($columnDef.FormatString) { $column.FormatString = $columnDef.FormatString }
    if ($columnDef.Hidden) { $column.IsHidden = $true }
    $table.Columns.Add($column)
  }

  $partition = New-Object Microsoft.AnalysisServices.Tabular.Partition
  $partition.Name = "${Name}-Import"
  $partition.Mode = [Microsoft.AnalysisServices.Tabular.ModeType]::Import
  $source = New-Object Microsoft.AnalysisServices.Tabular.MPartitionSource
  $source.Expression = New-MExpression $FileName
  $partition.Source = $source
  $table.Partitions.Add($partition)
  return $table
}

function Add-Measure($Table, $Name, $Expression, $FormatString = $null, $DisplayFolder = $null) {
  $measure = New-Object Microsoft.AnalysisServices.Tabular.Measure
  $measure.Name = $Name
  $measure.Expression = $Expression
  if ($FormatString) { $measure.FormatString = $FormatString }
  if ($DisplayFolder) { $measure.DisplayFolder = $DisplayFolder }
  $Table.Measures.Add($measure)
}

function Add-Relationship($Model, $Name, $FactTable, $FactColumn, $DimTable, $DimColumn) {
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

$none = [Microsoft.AnalysisServices.Tabular.AggregateFunction]::None
$sum = [Microsoft.AnalysisServices.Tabular.AggregateFunction]::Sum
$int = [Microsoft.AnalysisServices.Tabular.DataType]::Int64
$text = [Microsoft.AnalysisServices.Tabular.DataType]::String
$date = [Microsoft.AnalysisServices.Tabular.DataType]::DateTime
$dec = [Microsoft.AnalysisServices.Tabular.DataType]::Decimal
$dbl = [Microsoft.AnalysisServices.Tabular.DataType]::Double

$port = Get-PowerBiPort
$server = New-Object Microsoft.AnalysisServices.Tabular.Server
$server.Connect("localhost:$port")
$database = $server.Databases[0]
$model = $database.Model

# Clear the current model before rebuilding the semantic layer.
$model.Relationships.Clear()
$model.Tables.Clear()

Add-ImportTable $model "DimDate" "dim_date.csv" @(
  @{Name="DateKey"; Type=$int; SummarizeBy=$none; Hidden=$false},
  @{Name="MonthStart"; Type=$date; SummarizeBy=$none},
  @{Name="Year"; Type=$int; SummarizeBy=$none},
  @{Name="Quarter"; Type=$text; SummarizeBy=$none},
  @{Name="MonthNumber"; Type=$int; SummarizeBy=$none; Hidden=$true},
  @{Name="MonthName"; Type=$text; SummarizeBy=$none},
  @{Name="MonthYear"; Type=$text; SummarizeBy=$none},
  @{Name="MonthIndex"; Type=$int; SummarizeBy=$none; Hidden=$true},
  @{Name="IsActualClosed"; Type=$text; SummarizeBy=$none},
  @{Name="FiscalYear"; Type=$int; SummarizeBy=$none},
  @{Name="FiscalQuarter"; Type=$text; SummarizeBy=$none}
) | Out-Null

Add-ImportTable $model "DimScenario" "dim_scenario.csv" @(
  @{Name="ScenarioKey"; Type=$text; SummarizeBy=$none; Hidden=$true},
  @{Name="Scenario"; Type=$text; SummarizeBy=$none},
  @{Name="ScenarioSort"; Type=$int; SummarizeBy=$none; Hidden=$true},
  @{Name="ScenarioType"; Type=$text; SummarizeBy=$none}
) | Out-Null

Add-ImportTable $model "DimBusinessUnit" "dim_business_unit.csv" @(
  @{Name="BusinessUnitKey"; Type=$text; SummarizeBy=$none; Hidden=$true},
  @{Name="BusinessUnit"; Type=$text; SummarizeBy=$none}
) | Out-Null

Add-ImportTable $model "DimProduct" "dim_product.csv" @(
  @{Name="ProductKey"; Type=$text; SummarizeBy=$none; Hidden=$true},
  @{Name="BusinessUnit"; Type=$text; SummarizeBy=$none},
  @{Name="Product"; Type=$text; SummarizeBy=$none}
) | Out-Null

Add-ImportTable $model "DimRegion" "dim_region.csv" @(
  @{Name="RegionKey"; Type=$text; SummarizeBy=$none; Hidden=$true},
  @{Name="Region"; Type=$text; SummarizeBy=$none}
) | Out-Null

Add-ImportTable $model "DimCustomer" "dim_customer.csv" @(
  @{Name="CustomerKey"; Type=$text; SummarizeBy=$none; Hidden=$true},
  @{Name="Customer"; Type=$text; SummarizeBy=$none},
  @{Name="CustomerSegment"; Type=$text; SummarizeBy=$none},
  @{Name="Industry"; Type=$text; SummarizeBy=$none}
) | Out-Null

Add-ImportTable $model "DimDepartment" "dim_department.csv" @(
  @{Name="DepartmentKey"; Type=$text; SummarizeBy=$none; Hidden=$true},
  @{Name="Department"; Type=$text; SummarizeBy=$none}
) | Out-Null

Add-ImportTable $model "FactFinancials" "fact_financials.csv" @(
  @{Name="FactFinanceKey"; Type=$text; SummarizeBy=$none; Hidden=$true},
  @{Name="DateKey"; Type=$int; SummarizeBy=$none; Hidden=$true},
  @{Name="ScenarioKey"; Type=$text; SummarizeBy=$none; Hidden=$true},
  @{Name="BusinessUnitKey"; Type=$text; SummarizeBy=$none; Hidden=$true},
  @{Name="ProductKey"; Type=$text; SummarizeBy=$none; Hidden=$true},
  @{Name="RegionKey"; Type=$text; SummarizeBy=$none; Hidden=$true},
  @{Name="CustomerKey"; Type=$text; SummarizeBy=$none; Hidden=$true},
  @{Name="Revenue"; Type=$dec; SummarizeBy=$sum; FormatString="#,0"},
  @{Name="COGS"; Type=$dec; SummarizeBy=$sum; FormatString="#,0"},
  @{Name="GrossMargin"; Type=$dec; SummarizeBy=$sum; FormatString="#,0"},
  @{Name="AllocatedOpex"; Type=$dec; SummarizeBy=$sum; FormatString="#,0"},
  @{Name="EBITDA"; Type=$dec; SummarizeBy=$sum; FormatString="#,0"},
  @{Name="Orders"; Type=$int; SummarizeBy=$sum; FormatString="#,0"},
  @{Name="CashImpact"; Type=$dec; SummarizeBy=$sum; FormatString="#,0"}
) | Out-Null

Add-ImportTable $model "FactOpexDepartment" "fact_opex_department.csv" @(
  @{Name="FactOpexKey"; Type=$text; SummarizeBy=$none; Hidden=$true},
  @{Name="DateKey"; Type=$int; SummarizeBy=$none; Hidden=$true},
  @{Name="ScenarioKey"; Type=$text; SummarizeBy=$none; Hidden=$true},
  @{Name="BusinessUnitKey"; Type=$text; SummarizeBy=$none; Hidden=$true},
  @{Name="RegionKey"; Type=$text; SummarizeBy=$none; Hidden=$true},
  @{Name="DepartmentKey"; Type=$text; SummarizeBy=$none; Hidden=$true},
  @{Name="Opex"; Type=$dec; SummarizeBy=$sum; FormatString="#,0"},
  @{Name="FTE"; Type=$dbl; SummarizeBy=$sum; FormatString="#,0.0"}
) | Out-Null

Add-ImportTable $model "FactCash" "fact_cash.csv" @(
  @{Name="FactCashKey"; Type=$text; SummarizeBy=$none; Hidden=$true},
  @{Name="DateKey"; Type=$int; SummarizeBy=$none; Hidden=$true},
  @{Name="ScenarioKey"; Type=$text; SummarizeBy=$none; Hidden=$true},
  @{Name="BusinessUnitKey"; Type=$text; SummarizeBy=$none; Hidden=$true},
  @{Name="RegionKey"; Type=$text; SummarizeBy=$none; Hidden=$true},
  @{Name="CashBalance"; Type=$dec; SummarizeBy=$sum; FormatString="#,0"},
  @{Name="ARBalance"; Type=$dec; SummarizeBy=$sum; FormatString="#,0"},
  @{Name="DSO"; Type=$dbl; SummarizeBy=$none; FormatString="#,0.0"},
  @{Name="Capex"; Type=$dec; SummarizeBy=$sum; FormatString="#,0"}
) | Out-Null

Add-ImportTable $model "FactBridge" "fact_bridge.csv" @(
  @{Name="BridgeKey"; Type=$text; SummarizeBy=$none; Hidden=$true},
  @{Name="DateKey"; Type=$int; SummarizeBy=$none; Hidden=$true},
  @{Name="BusinessUnitKey"; Type=$text; SummarizeBy=$none; Hidden=$true},
  @{Name="RegionKey"; Type=$text; SummarizeBy=$none; Hidden=$true},
  @{Name="BridgeStep"; Type=$text; SummarizeBy=$none},
  @{Name="BridgeOrder"; Type=$int; SummarizeBy=$none; Hidden=$true},
  @{Name="Amount"; Type=$dec; SummarizeBy=$sum; FormatString="#,0"}
) | Out-Null

Add-ImportTable $model "FactCommentary" "fact_commentary.csv" @(
  @{Name="DateKey"; Type=$int; SummarizeBy=$none; Hidden=$true},
  @{Name="Audience"; Type=$text; SummarizeBy=$none},
  @{Name="WhatHappened"; Type=$text; SummarizeBy=$none},
  @{Name="Why"; Type=$text; SummarizeBy=$none},
  @{Name="WhatNext"; Type=$text; SummarizeBy=$none},
  @{Name="Severity"; Type=$text; SummarizeBy=$none}
) | Out-Null

$kpi = New-Object Microsoft.AnalysisServices.Tabular.Table
$kpi.Name = "KPI Measures"
$model.Tables.Add($kpi)
$kpiColumn = New-Object Microsoft.AnalysisServices.Tabular.DataColumn
$kpiColumn.Name = "MeasureKey"
$kpiColumn.SourceColumn = "MeasureKey"
$kpiColumn.DataType = $text
$kpiColumn.IsHidden = $true
$kpi.Columns.Add($kpiColumn)
$kpiPartition = New-Object Microsoft.AnalysisServices.Tabular.Partition
$kpiPartition.Name = "KPI Measures-Import"
$kpiPartition.Mode = [Microsoft.AnalysisServices.Tabular.ModeType]::Import
$kpiSource = New-Object Microsoft.AnalysisServices.Tabular.MPartitionSource
$kpiSource.Expression = "let Source = #table(type table [MeasureKey = text], {{""KPI""}}) in Source"
$kpiPartition.Source = $kpiSource
$kpi.Partitions.Add($kpiPartition)

Add-Relationship $model "FactFinancials_Date" "FactFinancials" "DateKey" "DimDate" "DateKey"
Add-Relationship $model "FactFinancials_Scenario" "FactFinancials" "ScenarioKey" "DimScenario" "ScenarioKey"
Add-Relationship $model "FactFinancials_BU" "FactFinancials" "BusinessUnitKey" "DimBusinessUnit" "BusinessUnitKey"
Add-Relationship $model "FactFinancials_Product" "FactFinancials" "ProductKey" "DimProduct" "ProductKey"
Add-Relationship $model "FactFinancials_Region" "FactFinancials" "RegionKey" "DimRegion" "RegionKey"
Add-Relationship $model "FactFinancials_Customer" "FactFinancials" "CustomerKey" "DimCustomer" "CustomerKey"
Add-Relationship $model "FactOpex_Date" "FactOpexDepartment" "DateKey" "DimDate" "DateKey"
Add-Relationship $model "FactOpex_Scenario" "FactOpexDepartment" "ScenarioKey" "DimScenario" "ScenarioKey"
Add-Relationship $model "FactOpex_BU" "FactOpexDepartment" "BusinessUnitKey" "DimBusinessUnit" "BusinessUnitKey"
Add-Relationship $model "FactOpex_Region" "FactOpexDepartment" "RegionKey" "DimRegion" "RegionKey"
Add-Relationship $model "FactOpex_Department" "FactOpexDepartment" "DepartmentKey" "DimDepartment" "DepartmentKey"
Add-Relationship $model "FactCash_Date" "FactCash" "DateKey" "DimDate" "DateKey"
Add-Relationship $model "FactCash_Scenario" "FactCash" "ScenarioKey" "DimScenario" "ScenarioKey"
Add-Relationship $model "FactCash_BU" "FactCash" "BusinessUnitKey" "DimBusinessUnit" "BusinessUnitKey"
Add-Relationship $model "FactCash_Region" "FactCash" "RegionKey" "DimRegion" "RegionKey"
Add-Relationship $model "FactBridge_Date" "FactBridge" "DateKey" "DimDate" "DateKey"
Add-Relationship $model "FactBridge_BU" "FactBridge" "BusinessUnitKey" "DimBusinessUnit" "BusinessUnitKey"
Add-Relationship $model "FactBridge_Region" "FactBridge" "RegionKey" "DimRegion" "RegionKey"
Add-Relationship $model "FactCommentary_Date" "FactCommentary" "DateKey" "DimDate" "DateKey"

$model.Tables["DimDate"].Columns["MonthName"].SortByColumn = $model.Tables["DimDate"].Columns["MonthNumber"]
$model.Tables["DimDate"].Columns["MonthYear"].SortByColumn = $model.Tables["DimDate"].Columns["MonthIndex"]
$model.Tables["DimScenario"].Columns["Scenario"].SortByColumn = $model.Tables["DimScenario"].Columns["ScenarioSort"]
$model.Tables["FactBridge"].Columns["BridgeStep"].SortByColumn = $model.Tables["FactBridge"].Columns["BridgeOrder"]

Add-Measure $kpi "Revenue" "SUM ( FactFinancials[Revenue] )" "#,0" "Core KPI"
Add-Measure $kpi "COGS" "SUM ( FactFinancials[COGS] )" "#,0" "Core KPI"
Add-Measure $kpi "Gross Margin" "[Revenue] - [COGS]" "#,0" "Core KPI"
Add-Measure $kpi "Gross Margin %" "DIVIDE ( [Gross Margin], [Revenue] )" "0.0%" "Core KPI"
Add-Measure $kpi "Allocated Opex" "SUM ( FactFinancials[AllocatedOpex] )" "#,0" "Core KPI"
Add-Measure $kpi "Department Opex" "SUM ( FactOpexDepartment[Opex] )" "#,0" "Core KPI"
Add-Measure $kpi "EBITDA" "[Gross Margin] - [Allocated Opex]" "#,0" "Core KPI"
Add-Measure $kpi "EBITDA %" "DIVIDE ( [EBITDA], [Revenue] )" "0.0%" "Core KPI"
Add-Measure $kpi "Orders" "SUM ( FactFinancials[Orders] )" "#,0" "Core KPI"
Add-Measure $kpi "Revenue per Order" "DIVIDE ( [Revenue], [Orders] )" "#,0" "Core KPI"
Add-Measure $kpi "Cash Impact" "SUM ( FactFinancials[CashImpact] )" "#,0" "Cash"
Add-Measure $kpi "Capex" "SUM ( FactCash[Capex] )" "#,0" "Cash"
Add-Measure $kpi "Cash Balance Latest Month" "VAR LatestVisibleDateKey = MAX ( DimDate[DateKey] ) RETURN CALCULATE ( SUM ( FactCash[CashBalance] ), DimDate[DateKey] = LatestVisibleDateKey )" "#,0" "Cash"
Add-Measure $kpi "AR Balance Latest Month" "VAR LatestVisibleDateKey = MAX ( DimDate[DateKey] ) RETURN CALCULATE ( SUM ( FactCash[ARBalance] ), DimDate[DateKey] = LatestVisibleDateKey )" "#,0" "Cash"
Add-Measure $kpi "Weighted DSO" "DIVIDE ( SUMX ( FactCash, FactCash[ARBalance] * FactCash[DSO] ), SUM ( FactCash[ARBalance] ) )" "#,0.0" "Cash"
Add-Measure $kpi "Latest Actual DateKey" "CALCULATE ( MAX ( FactFinancials[DateKey] ), DimScenario[Scenario] = ""Actual"", REMOVEFILTERS ( DimDate ) )" "0" "Time Intelligence"
Add-Measure $kpi "Actual Revenue" "CALCULATE ( [Revenue], DimScenario[Scenario] = ""Actual"" )" "#,0" "Scenario"
Add-Measure $kpi "Budget Revenue" "CALCULATE ( [Revenue], DimScenario[Scenario] = ""Budget"" )" "#,0" "Scenario"
Add-Measure $kpi "Forecast Revenue" "CALCULATE ( [Revenue], DimScenario[Scenario] = ""Forecast"" )" "#,0" "Scenario"
Add-Measure $kpi "Actual Gross Margin" "CALCULATE ( [Gross Margin], DimScenario[Scenario] = ""Actual"" )" "#,0" "Scenario"
Add-Measure $kpi "Budget Gross Margin" "CALCULATE ( [Gross Margin], DimScenario[Scenario] = ""Budget"" )" "#,0" "Scenario"
Add-Measure $kpi "Forecast Gross Margin" "CALCULATE ( [Gross Margin], DimScenario[Scenario] = ""Forecast"" )" "#,0" "Scenario"
Add-Measure $kpi "Actual EBITDA" "CALCULATE ( [EBITDA], DimScenario[Scenario] = ""Actual"" )" "#,0" "Scenario"
Add-Measure $kpi "Budget EBITDA" "CALCULATE ( [EBITDA], DimScenario[Scenario] = ""Budget"" )" "#,0" "Scenario"
Add-Measure $kpi "Forecast EBITDA" "CALCULATE ( [EBITDA], DimScenario[Scenario] = ""Forecast"" )" "#,0" "Scenario"
Add-Measure $kpi "Actual Opex" "CALCULATE ( [Allocated Opex], DimScenario[Scenario] = ""Actual"" )" "#,0" "Scenario"
Add-Measure $kpi "Budget Opex" "CALCULATE ( [Allocated Opex], DimScenario[Scenario] = ""Budget"" )" "#,0" "Scenario"
Add-Measure $kpi "Forecast Opex" "CALCULATE ( [Allocated Opex], DimScenario[Scenario] = ""Forecast"" )" "#,0" "Scenario"
Add-Measure $kpi "Actual Cash Balance" "CALCULATE ( [Cash Balance Latest Month], DimScenario[Scenario] = ""Actual"" )" "#,0" "Scenario"
Add-Measure $kpi "Budget Cash Balance" "CALCULATE ( [Cash Balance Latest Month], DimScenario[Scenario] = ""Budget"" )" "#,0" "Scenario"
Add-Measure $kpi "Forecast Cash Balance" "CALCULATE ( [Cash Balance Latest Month], DimScenario[Scenario] = ""Forecast"" )" "#,0" "Scenario"
Add-Measure $kpi "Actual Revenue Current Month" "VAR LatestActualDateKey = [Latest Actual DateKey] RETURN CALCULATE ( [Revenue], DimScenario[Scenario] = ""Actual"", DimDate[DateKey] = LatestActualDateKey )" "#,0" "Current Month"
Add-Measure $kpi "Budget Revenue Current Month" "VAR LatestActualDateKey = [Latest Actual DateKey] RETURN CALCULATE ( [Revenue], DimScenario[Scenario] = ""Budget"", DimDate[DateKey] = LatestActualDateKey )" "#,0" "Current Month"
Add-Measure $kpi "Forecast Revenue Current Month" "VAR LatestActualDateKey = [Latest Actual DateKey] RETURN CALCULATE ( [Revenue], DimScenario[Scenario] = ""Forecast"", DimDate[DateKey] = LatestActualDateKey )" "#,0" "Current Month"
Add-Measure $kpi "Actual EBITDA Current Month" "VAR LatestActualDateKey = [Latest Actual DateKey] RETURN CALCULATE ( [EBITDA], DimScenario[Scenario] = ""Actual"", DimDate[DateKey] = LatestActualDateKey )" "#,0" "Current Month"
Add-Measure $kpi "Budget EBITDA Current Month" "VAR LatestActualDateKey = [Latest Actual DateKey] RETURN CALCULATE ( [EBITDA], DimScenario[Scenario] = ""Budget"", DimDate[DateKey] = LatestActualDateKey )" "#,0" "Current Month"
Add-Measure $kpi "Actual Cash Balance Current Month" "VAR LatestActualDateKey = [Latest Actual DateKey] RETURN CALCULATE ( SUM ( FactCash[CashBalance] ), DimScenario[Scenario] = ""Actual"", DimDate[DateKey] = LatestActualDateKey )" "#,0" "Current Month"
Add-Measure $kpi "Budget Cash Balance Current Month" "VAR LatestActualDateKey = [Latest Actual DateKey] RETURN CALCULATE ( SUM ( FactCash[CashBalance] ), DimScenario[Scenario] = ""Budget"", DimDate[DateKey] = LatestActualDateKey )" "#,0" "Current Month"
Add-Measure $kpi "Weighted DSO Current Month" "VAR LatestActualDateKey = [Latest Actual DateKey] RETURN CALCULATE ( [Weighted DSO], DimScenario[Scenario] = ""Actual"", DimDate[DateKey] = LatestActualDateKey )" "#,0.0" "Current Month"
Add-Measure $kpi "Cash Var Current Month vs Budget" "[Actual Cash Balance Current Month] - [Budget Cash Balance Current Month]" "#,0" "Current Month"
Add-Measure $kpi "Revenue Var vs Budget" "[Actual Revenue] - [Budget Revenue]" "#,0" "Variance"
Add-Measure $kpi "Revenue Var % vs Budget" "DIVIDE ( [Revenue Var vs Budget], [Budget Revenue] )" "0.0%" "Variance"
Add-Measure $kpi "Gross Margin Var vs Budget" "[Actual Gross Margin] - [Budget Gross Margin]" "#,0" "Variance"
Add-Measure $kpi "EBITDA Var vs Budget" "[Actual EBITDA] - [Budget EBITDA]" "#,0" "Variance"
Add-Measure $kpi "EBITDA Var % vs Budget" "DIVIDE ( [EBITDA Var vs Budget], [Budget EBITDA] )" "0.0%" "Variance"
Add-Measure $kpi "Opex Var vs Budget" "[Actual Opex] - [Budget Opex]" "#,0" "Variance"
Add-Measure $kpi "Cash Var vs Budget" "[Actual Cash Balance] - [Budget Cash Balance]" "#,0" "Variance"
Add-Measure $kpi "Forecast Revenue Gap vs Budget" "[Forecast Revenue] - [Budget Revenue]" "#,0" "Forecast"
Add-Measure $kpi "Forecast EBITDA Gap vs Budget" "[Forecast EBITDA] - [Budget EBITDA]" "#,0" "Forecast"
Add-Measure $kpi "Bridge Amount" "SUM ( FactBridge[Amount] )" "#,0" "Bridge"
Add-Measure $kpi "Selected Commentary - What Happened" "CONCATENATEX ( VALUES ( FactCommentary[WhatHappened] ), FactCommentary[WhatHappened], UNICHAR ( 10 ) )" "" "Commentary"
Add-Measure $kpi "Selected Commentary - Why" "CONCATENATEX ( VALUES ( FactCommentary[Why] ), FactCommentary[Why], UNICHAR ( 10 ) )" "" "Commentary"
Add-Measure $kpi "Selected Commentary - What Next" "CONCATENATEX ( VALUES ( FactCommentary[WhatNext] ), FactCommentary[WhatNext], UNICHAR ( 10 ) )" "" "Commentary"

$model.SaveChanges()
$model.RequestRefresh([Microsoft.AnalysisServices.Tabular.RefreshType]::Full)
$model.SaveChanges()
$server.Disconnect()

Write-Host "Pushed FP&A model to Power BI Desktop on localhost:$port"
