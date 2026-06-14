param(
  [int]$Port = 0,
  [string]$ProjectRoot = "C:\Users\Win\OneDrive - BEE LOGISTICS CORPORATION\Documentss\Portfolio\Project 07 - Marketplace Seller Performance"
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

function Add-ImportTable {
  param(
    [Microsoft.AnalysisServices.Tabular.Model]$Model,
    [string]$Name,
    [string]$CsvPath,
    [array]$Columns
  )

  $table = New-Object Microsoft.AnalysisServices.Tabular.Table
  $table.Name = $Name

  foreach ($col in $Columns) {
    $column = New-Object Microsoft.AnalysisServices.Tabular.DataColumn
    $column.Name = $col.Name
    $column.SourceColumn = $col.Name
    $column.DataType = [Microsoft.AnalysisServices.Tabular.DataType]::$($col.Type)
    $column.SummarizeBy = [Microsoft.AnalysisServices.Tabular.AggregateFunction]::None
    $table.Columns.Add($column) | Out-Null
  }

  $source = New-Object Microsoft.AnalysisServices.Tabular.MPartitionSource
  $source.Expression = New-MExpression -CsvPath $CsvPath -Columns $Columns

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
    Source = #table(type table [Measure Group = text], {{"Project 07 - Marketplace Seller Performance Marketplace Seller Performance"}})
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
$tables = @(
  @{
    Name = "dim_platform"; File = "dim_platform.csv"; Columns = @(
      @{Name="platform_id"; Type="String"}, @{Name="platform_name"; Type="String"}, @{Name="brand_color"; Type="String"}, @{Name="default_commission_rate"; Type="Double"}
    )
  },
  @{
    Name = "dim_seller"; File = "dim_seller.csv"; Columns = @(
      @{Name="seller_id"; Type="String"}, @{Name="seller_name"; Type="String"}, @{Name="platform_id"; Type="String"}, @{Name="region"; Type="String"}, @{Name="seller_tier"; Type="String"}, @{Name="lifecycle_status"; Type="String"}, @{Name="account_manager"; Type="String"}, @{Name="official_store_flag"; Type="Int64"}, @{Name="active_flag"; Type="Int64"}, @{Name="join_date"; Type="DateTime"}, @{Name="demand_weight"; Type="Double"}, @{Name="fulfillment_quality"; Type="Double"}, @{Name="cancel_propensity"; Type="Double"}, @{Name="rating_base"; Type="Double"}, @{Name="stock_discipline"; Type="Double"}
    )
  },
  @{
    Name = "dim_category"; File = "dim_category.csv"; Columns = @(
      @{Name="category_id"; Type="String"}, @{Name="category"; Type="String"}
    )
  },
  @{
    Name = "dim_product"; File = "dim_product.csv"; Columns = @(
      @{Name="sku_id"; Type="String"}, @{Name="product_name"; Type="String"}, @{Name="seller_id"; Type="String"}, @{Name="platform_id"; Type="String"}, @{Name="category_id"; Type="String"}, @{Name="category"; Type="String"}, @{Name="brand"; Type="String"}, @{Name="base_price"; Type="Double"}, @{Name="product_demand_weight"; Type="Double"}, @{Name="active_flag"; Type="Int64"}
    )
  },
  @{
    Name = "fact_seller_month"; File = "fact_seller_month.csv"; Columns = @(
      @{Name="year_month"; Type="String"}, @{Name="platform_id"; Type="String"}, @{Name="seller_id"; Type="String"}, @{Name="gross_gmv"; Type="Double"}, @{Name="seller_gmv_net"; Type="Double"}, @{Name="commission_revenue"; Type="Double"}, @{Name="order_items"; Type="Int64"}, @{Name="orders"; Type="Int64"}, @{Name="cancelled_items"; Type="Int64"}, @{Name="returned_items"; Type="Int64"}, @{Name="eligible_items"; Type="Int64"}, @{Name="fulfilled_items"; Type="Int64"}, @{Name="late_items"; Type="Int64"}, @{Name="sku_day_count"; Type="Int64"}, @{Name="in_stock_sku_days"; Type="Int64"}, @{Name="low_stock_sku_days"; Type="Int64"}, @{Name="rating_weighted_sum"; Type="Double"}, @{Name="rating_weight"; Type="Double"}, @{Name="rating_count"; Type="Double"}, @{Name="fulfillment_rate"; Type="Double"}, @{Name="cancellation_rate"; Type="Double"}, @{Name="stock_availability_rate"; Type="Double"}, @{Name="avg_rating"; Type="Double"}
    )
  },
  @{
    Name = "fact_seller_targets"; File = "fact_seller_targets.csv"; Columns = @(
      @{Name="year_month"; Type="String"}, @{Name="platform_id"; Type="String"}, @{Name="seller_id"; Type="String"}, @{Name="seller_gmv_target"; Type="Double"}, @{Name="order_target"; Type="Int64"}
    )
  },
  @{
    Name = "fact_ads_spend"; File = "fact_ads_spend.csv"; Columns = @(
      @{Name="year_month"; Type="String"}, @{Name="platform_id"; Type="String"}, @{Name="seller_id"; Type="String"}, @{Name="ads_spend"; Type="Double"}, @{Name="voucher_cost"; Type="Double"}
    )
  }
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

  foreach ($spec in $tables) {
    $csvPath = Join-Path $prepared $spec.File
    if (-not (Test-Path $csvPath)) { throw "Missing prepared CSV: $csvPath" }
    Add-ImportTable -Model $model -Name $spec.Name -CsvPath $csvPath -Columns $spec.Columns
  }

  $measureTable = Add-MeasureTable -Model $model

  Add-Relationship -Model $model -FromTable "dim_product" -FromColumn "seller_id" -ToTable "dim_seller" -ToColumn "seller_id"
  Add-Relationship -Model $model -FromTable "dim_product" -FromColumn "category_id" -ToTable "dim_category" -ToColumn "category_id"
  Add-Relationship -Model $model -FromTable "fact_seller_month" -FromColumn "seller_id" -ToTable "dim_seller" -ToColumn "seller_id"
  Add-Relationship -Model $model -FromTable "fact_seller_month" -FromColumn "platform_id" -ToTable "dim_platform" -ToColumn "platform_id"
  Add-Relationship -Model $model -FromTable "fact_seller_targets" -FromColumn "seller_id" -ToTable "dim_seller" -ToColumn "seller_id"
  Add-Relationship -Model $model -FromTable "fact_seller_targets" -FromColumn "platform_id" -ToTable "dim_platform" -ToColumn "platform_id"
  Add-Relationship -Model $model -FromTable "fact_ads_spend" -FromColumn "seller_id" -ToTable "dim_seller" -ToColumn "seller_id"
  Add-Relationship -Model $model -FromTable "fact_ads_spend" -FromColumn "platform_id" -ToTable "dim_platform" -ToColumn "platform_id"

  Add-KpiMeasure -Table $measureTable -Name "Seller GMV" -Expression "SUM ( fact_seller_month[seller_gmv_net] )" -FormatString '$#,0'
  Add-KpiMeasure -Table $measureTable -Name "Gross GMV" -Expression "SUM ( fact_seller_month[gross_gmv] )" -FormatString '$#,0'
  Add-KpiMeasure -Table $measureTable -Name "Commission Revenue" -Expression "SUM ( fact_seller_month[commission_revenue] )" -FormatString '$#,0'
  Add-KpiMeasure -Table $measureTable -Name "Orders" -Expression "SUM ( fact_seller_month[orders] )" -FormatString '#,0'
  Add-KpiMeasure -Table $measureTable -Name "Order Items" -Expression "SUM ( fact_seller_month[order_items] )" -FormatString '#,0'
  Add-KpiMeasure -Table $measureTable -Name "Cancelled Items" -Expression "SUM ( fact_seller_month[cancelled_items] )" -FormatString '#,0'
  Add-KpiMeasure -Table $measureTable -Name "Cancellation Rate" -Expression "DIVIDE ( [Cancelled Items], [Order Items] )" -FormatString '0.0%'
  Add-KpiMeasure -Table $measureTable -Name "Eligible Fulfillment Items" -Expression "SUM ( fact_seller_month[eligible_items] )" -FormatString '#,0'
  Add-KpiMeasure -Table $measureTable -Name "Fulfilled Items" -Expression "SUM ( fact_seller_month[fulfilled_items] )" -FormatString '#,0'
  Add-KpiMeasure -Table $measureTable -Name "Fulfillment Rate" -Expression "DIVIDE ( [Fulfilled Items], [Eligible Fulfillment Items] )" -FormatString '0.0%'
  Add-KpiMeasure -Table $measureTable -Name "Late Fulfillment Rate" -Expression "DIVIDE ( SUM ( fact_seller_month[late_items] ), [Eligible Fulfillment Items] )" -FormatString '0.0%'
  Add-KpiMeasure -Table $measureTable -Name "Average Rating" -Expression "DIVIDE ( SUM ( fact_seller_month[rating_weighted_sum] ), SUM ( fact_seller_month[rating_weight] ) )" -FormatString '0.00'
  Add-KpiMeasure -Table $measureTable -Name "Rating Count" -Expression "SUM ( fact_seller_month[rating_count] )" -FormatString '#,0'
  Add-KpiMeasure -Table $measureTable -Name "Stock Availability" -Expression "DIVIDE ( SUM ( fact_seller_month[in_stock_sku_days] ), SUM ( fact_seller_month[sku_day_count] ) )" -FormatString '0.0%'
  Add-KpiMeasure -Table $measureTable -Name "Seller GMV Target" -Expression "SUM ( fact_seller_targets[seller_gmv_target] )" -FormatString '$#,0'
  Add-KpiMeasure -Table $measureTable -Name "GMV Target Attainment" -Expression "DIVIDE ( [Seller GMV], [Seller GMV Target] )" -FormatString '0.0%'
  Add-KpiMeasure -Table $measureTable -Name "Ads Spend" -Expression "SUM ( fact_ads_spend[ads_spend] )" -FormatString '$#,0'
  Add-KpiMeasure -Table $measureTable -Name "Voucher Cost" -Expression "SUM ( fact_ads_spend[voucher_cost] )" -FormatString '$#,0'
  Add-KpiMeasure -Table $measureTable -Name "Take Rate" -Expression "DIVIDE ( [Commission Revenue], [Seller GMV] )" -FormatString '0.0%'
  Add-KpiMeasure -Table $measureTable -Name "Active Sellers" -Expression "DISTINCTCOUNT ( fact_seller_month[seller_id] )" -FormatString '#,0'
  Add-KpiMeasure -Table $measureTable -Name "Seller Rank by GMV" -Expression "RANKX ( ALLSELECTED ( dim_seller[seller_id] ), [Seller GMV], , DESC, Dense )" -FormatString '#,0'
  Add-KpiMeasure -Table $measureTable -Name "Seller Performance Score" -Expression @"
VAR RatingScore = DIVIDE ( [Average Rating], 5 )
VAR FulfillmentScore = [Fulfillment Rate]
VAR CancellationScore = 1 - [Cancellation Rate]
VAR StockScore = [Stock Availability]
VAR SellerCount = COUNTROWS ( ALLSELECTED ( dim_seller[seller_id] ) )
VAR GMVRankPct = DIVIDE ( [Seller Rank by GMV], SellerCount )
RETURN
    0.40 * ( 1 - GMVRankPct )
        + 0.25 * FulfillmentScore
        + 0.20 * CancellationScore
        + 0.10 * RatingScore
        + 0.05 * StockScore
"@ -FormatString '0.0%'

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
