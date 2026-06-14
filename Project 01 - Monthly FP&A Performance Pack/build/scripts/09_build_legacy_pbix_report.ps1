param(
  [string]$ModelPbix = "C:\Users\Win\OneDrive\Codex\Portfolio\BI\Project 01 - Monthly FP&A Performance Pack\output\dashboard_model.pbix",
  [string]$OutputPbix = "C:\Users\Win\OneDrive\Codex\Portfolio\BI\Project 01 - Monthly FP&A Performance Pack\output\dashboard_v01.pbix",
  [string]$FinalPbix = "C:\Users\Win\OneDrive\Codex\Portfolio\BI\Project 01 - Monthly FP&A Performance Pack\output\dashboard_final.pbix"
)

$ErrorActionPreference = "Stop"

$ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..")
$PreparedRoot = Join-Path $ProjectRoot "data\prepared"
$OutputRoot = Join-Path $ProjectRoot "output"
$QaRoot = Join-Path $ProjectRoot "qa"
$ScreenshotRoot = Join-Path $OutputRoot "screenshots"
New-Item -ItemType Directory -Force -Path $OutputRoot, $QaRoot, $ScreenshotRoot | Out-Null

$PowerBiBin = "C:\Program Files\WindowsApps\Microsoft.MicrosoftPowerBIDesktop_2.154.1260.0_x64__8wekyb3d8bbwe\bin"
$PackagingDll = Join-Path $PowerBiBin "Microsoft.PowerBI.Packaging.dll"
if (!(Test-Path -LiteralPath $PackagingDll)) {
  throw "Power BI Packaging assembly not found: $PackagingDll"
}
if (!(Test-Path -LiteralPath $ModelPbix)) {
  throw "Model PBIX not found: $ModelPbix"
}

[Reflection.Assembly]::LoadFrom($PackagingDll) | Out-Null
Add-Type -AssemblyName WindowsBase

function CsvRows([string]$Name) {
  Import-Csv -LiteralPath (Join-Path $PreparedRoot $Name)
}

function To-Dec($Value) {
  if ($null -eq $Value -or $Value -eq "") { return 0.0 }
  return [double]::Parse([string]$Value, [Globalization.CultureInfo]::InvariantCulture)
}

function To-Int($Value) {
  if ($null -eq $Value -or $Value -eq "") { return 0 }
  return [int]::Parse([string]$Value, [Globalization.CultureInfo]::InvariantCulture)
}

function Sum-Field($Rows, [string]$Field) {
  $total = 0.0
  foreach ($row in $Rows) { $total += To-Dec $row.$Field }
  return $total
}

function Short-M($Value) {
  $abs = [math]::Abs([double]$Value)
  if ($abs -ge 1000000000) { return ("{0:n1}B" -f ([double]$Value / 1000000000.0)) }
  if ($abs -ge 1000000) { return ("{0:n1}M" -f ([double]$Value / 1000000.0)) }
  if ($abs -ge 1000) { return ("{0:n1}K" -f ([double]$Value / 1000.0)) }
  return ("{0:n0}" -f [double]$Value)
}

function Short-Pct($Value) {
  return ("{0:n1}%" -f ([double]$Value * 100.0))
}

function Delta-Text($Value, [string]$Suffix = "") {
  if ([double]$Value -ge 0) { return ("+{0}{1}" -f (Short-M $Value), $Suffix) }
  return ("{0}{1}" -f (Short-M $Value), $Suffix)
}

function Add-MemberSafe($Object, [string]$Name, $Value) {
  $Object | Add-Member -NotePropertyName $Name -NotePropertyValue $Value -Force
}

function Literal([string]$Value) {
  return @{ expr = @{ Literal = @{ Value = $Value } } }
}

function StringLiteral([string]$Value) {
  return Literal ("'" + $Value.Replace("'", "''") + "'")
}

function BoolLiteral([bool]$Value) {
  if ($Value) { return Literal "true" }
  return Literal "false"
}

function NumberLiteral([string]$Value) {
  return Literal $Value
}

function SolidLiteral([string]$Color) {
  return @{ solid = @{ color = StringLiteral $Color } }
}

function New-VisualName {
  param([string]$Prefix)
  $guid = [guid]::NewGuid().ToString("N").Substring(0, 20)
  return ($Prefix + $guid).Substring(0, [math]::Min(($Prefix + $guid).Length, 28))
}

function New-Container {
  param(
    [string]$Name,
    [string]$VisualType,
    [double]$X,
    [double]$Y,
    [double]$Width,
    [double]$Height,
    [int]$Z,
    [hashtable]$Objects
  )

  $position = [ordered]@{
    x = $X
    y = $Y
    z = $Z
    width = $Width
    height = $Height
    tabOrder = $Z
  }

  $config = [ordered]@{
    name = $Name
    layouts = @(
      [ordered]@{
        id = 0
        position = $position
      }
    )
    singleVisual = [ordered]@{
      visualType = $VisualType
      drillFilterOtherVisuals = $true
    }
  }

  if ($Objects) {
    foreach ($key in $Objects.Keys) {
      $config.singleVisual[$key] = $Objects[$key]
    }
  }

  return [ordered]@{
    x = $X
    y = $Y
    z = $Z
    width = $Width
    height = $Height
    config = ($config | ConvertTo-Json -Depth 100 -Compress)
    filters = "[]"
    tabOrder = $Z
  }
}

function New-Shape {
  param(
    [double]$X,
    [double]$Y,
    [double]$Width,
    [double]$Height,
    [int]$Z,
    [string]$Fill = "#FFFFFF",
    [string]$Outline = "#E5E7EB",
    [bool]$ShowOutline = $true,
    [double]$Transparency = 0.0
  )

  $objects = @{
    objects = [ordered]@{
      shape = @(
        [ordered]@{
          properties = [ordered]@{
            tileShape = StringLiteral "rectangle"
          }
        }
      )
      fill = @(
        [ordered]@{
          properties = [ordered]@{
            show = BoolLiteral $true
            fillColor = SolidLiteral $Fill
            transparency = NumberLiteral ("{0:0.0}D" -f $Transparency)
          }
        }
      )
      outline = @(
        [ordered]@{
          properties = [ordered]@{
            show = BoolLiteral $ShowOutline
            color = SolidLiteral $Outline
            weight = NumberLiteral "1.0D"
          }
        }
      )
    }
    vcObjects = [ordered]@{
      background = @(
        [ordered]@{
          properties = [ordered]@{
            show = BoolLiteral $false
          }
        }
      )
      border = @(
        [ordered]@{
          properties = [ordered]@{
            show = BoolLiteral $false
          }
        }
      )
      visualHeader = @(
        [ordered]@{
          properties = [ordered]@{
            show = BoolLiteral $false
          }
        }
      )
    }
  }

  New-Container -Name (New-VisualName "shape") -VisualType "basicShape" -X $X -Y $Y -Width $Width -Height $Height -Z $Z -Objects $objects
}

function New-Text {
  param(
    [string]$Text,
    [double]$X,
    [double]$Y,
    [double]$Width,
    [double]$Height,
    [int]$Z,
    [string]$Color = "#111827",
    [string]$FontSize = "11pt",
    [string]$FontFamily = "Segoe UI",
    [bool]$Bold = $false,
    [string]$Background = $null
  )

  $style = [ordered]@{
    fontFamily = $FontFamily
    fontSize = $FontSize
    color = $Color
  }
  if ($Bold) { $style["fontWeight"] = "bold" }

  $single = [ordered]@{
    objects = [ordered]@{
      general = @(
        [ordered]@{
          properties = [ordered]@{
            paragraphs = @(
              [ordered]@{
                textRuns = @(
                  [ordered]@{
                    value = $Text
                    textStyle = $style
                  }
                )
              }
            )
          }
        }
      )
    }
  }

  if ($Background) {
    $single["vcObjects"] = [ordered]@{
      background = @(
        [ordered]@{
          properties = [ordered]@{
            show = BoolLiteral $true
            color = SolidLiteral $Background
            transparency = NumberLiteral "0.0D"
          }
        }
      )
    }
  }

  New-Container -Name (New-VisualName "text") -VisualType "textbox" -X $X -Y $Y -Width $Width -Height $Height -Z $Z -Objects $single
}

function Add-Text([System.Collections.ArrayList]$List, [string]$Text, [double]$X, [double]$Y, [double]$W, [double]$H, [int]$Z, [string]$Color = "#111827", [string]$Size = "11pt", [string]$Family = "Segoe UI", [bool]$Bold = $false, [string]$Background = $null) {
  [void]$List.Add((New-Text -Text $Text -X $X -Y $Y -Width $W -Height $H -Z $Z -Color $Color -FontSize $Size -FontFamily $Family -Bold $Bold -Background $Background))
}

function Add-Shape([System.Collections.ArrayList]$List, [double]$X, [double]$Y, [double]$W, [double]$H, [int]$Z, [string]$Fill = "#FFFFFF", [string]$Outline = "#E5E7EB", [bool]$ShowOutline = $true, [double]$Transparency = 0.0) {
  [void]$List.Add((New-Shape -X $X -Y $Y -Width $W -Height $H -Z $Z -Fill $Fill -Outline $Outline -ShowOutline $ShowOutline -Transparency $Transparency))
}

function Add-Panel([System.Collections.ArrayList]$List, [double]$X, [double]$Y, [double]$W, [double]$H, [int]$Z, [string]$Title, [string]$Subtitle = "") {
  Add-Shape $List $X $Y $W $H $Z "#FFFFFF" "#FED7AA" $true 0
  Add-Text $List $Title ($X + 16) ($Y + 12) ($W - 32) 24 ($Z + 1) "#111827" "12pt" "Segoe UI Semibold" $true
  if ($Subtitle) {
    Add-Text $List $Subtitle ($X + 16) ($Y + 36) ($W - 32) 20 ($Z + 2) "#64748B" "8pt"
  }
}

function Add-Header([System.Collections.ArrayList]$List, [string]$PageTitle, [string]$Subtitle) {
  Add-Shape $List 16 12 1248 58 0 "#F97316" "#F97316" $false 0
  Add-Text $List "Monthly FP&A Performance Pack" 34 22 430 28 100 "#FFFFFF" "17pt" "Segoe UI Semibold" $true "#F97316"
  Add-Text $List $PageTitle 790 22 452 22 101 "#FFFFFF" "12pt" "Segoe UI Semibold" $true "#F97316"
  Add-Text $List $Subtitle 790 44 452 18 102 "#FFEDD5" "8pt" "Segoe UI"
}

function Add-KpiCard([System.Collections.ArrayList]$List, [double]$X, [double]$Y, [double]$W, [string]$Label, [string]$Value, [string]$Delta, [string]$DeltaColor, [int]$Z) {
  Add-Shape $List $X $Y $W 82 $Z "#FFFFFF" "#FDBA74" $true 0
  Add-Text $List $Label ($X + 14) ($Y + 10) ($W - 28) 18 ($Z + 1) "#64748B" "8pt" "Segoe UI Semibold" $true
  Add-Text $List $Value ($X + 14) ($Y + 28) ($W - 28) 30 ($Z + 2) "#111827" "20pt" "Segoe UI Semibold" $true
  Add-Text $List $Delta ($X + 14) ($Y + 58) ($W - 28) 18 ($Z + 3) $DeltaColor "8pt" "Segoe UI Semibold" $true
}

function Add-BarList([System.Collections.ArrayList]$List, $Rows, [double]$X, [double]$Y, [double]$W, [double]$RowH, [int]$Z, [string]$NameField, [string]$ValueField, [string]$ColorPositive = "#2A9D8F", [string]$ColorNegative = "#DC2626") {
  $maxAbs = 1.0
  foreach ($r in $Rows) {
    $maxAbs = [math]::Max($maxAbs, [math]::Abs([double]$r.$ValueField))
  }
  $i = 0
  foreach ($r in $Rows) {
    $rowY = $Y + ($i * $RowH)
    $value = [double]$r.$ValueField
    $barW = [math]::Max(4, [math]::Abs($value) / $maxAbs * ($W - 175))
    $barX = $X + 132
    $color = if ($value -ge 0) { $ColorPositive } else { $ColorNegative }
    Add-Text $List ([string]$r.$NameField) $X ($rowY + 1) 126 16 ($Z + $i * 5 + 1) "#334155" "7.5pt" "Segoe UI"
    Add-Shape $List $barX ($rowY + 4) ($W - 175) 9 ($Z + $i * 5 + 2) "#F1F5F9" "#F1F5F9" $false 0
    Add-Shape $List $barX ($rowY + 4) $barW 9 ($Z + $i * 5 + 3) $color $color $false 0
    Add-Text $List (Delta-Text $value) ($X + $W - 40) ($rowY + 1) 50 16 ($Z + $i * 5 + 4) $color "7.5pt" "Segoe UI Semibold" $true
    $i++
  }
}

function Add-ColumnChart([System.Collections.ArrayList]$List, $Rows, [double]$X, [double]$Y, [double]$W, [double]$H, [int]$Z, [string]$LabelField, [string]$ActualField, [string]$BudgetField, [string]$ForecastField) {
  $max = 1.0
  foreach ($r in $Rows) {
    $max = [math]::Max($max, [double]$r.$ActualField)
    $max = [math]::Max($max, [double]$r.$BudgetField)
    $max = [math]::Max($max, [double]$r.$ForecastField)
  }
  $count = [math]::Max(1, $Rows.Count)
  $groupW = $W / $count
  $chartBottom = $Y + $H - 24
  Add-Shape $List $X $chartBottom $W 1 ($Z + 1) "#CBD5E1" "#CBD5E1" $false 0
  for ($i = 0; $i -lt $Rows.Count; $i++) {
    $r = $Rows[$i]
    $gx = $X + ($i * $groupW) + 5
    $barW = [math]::Max(3, ($groupW - 12) / 3.4)
    $values = @(
      @{Field=$ActualField; Color="#F97316"; Offset=0},
      @{Field=$BudgetField; Color="#94A3B8"; Offset=$barW + 2},
      @{Field=$ForecastField; Color="#FDBA74"; Offset=($barW + 2) * 2}
    )
    foreach ($v in $values) {
      $val = [double]$r.($v.Field)
      $bh = [math]::Max(2, ($val / $max) * ($H - 42))
      Add-Shape $List ($gx + $v.Offset) ($chartBottom - $bh) $barW $bh ($Z + 10 + $i * 10 + $v.Offset) $v.Color $v.Color $false 0
    }
    Add-Text $List ([string]$r.$LabelField) ($X + ($i * $groupW) - 2) ($chartBottom + 5) ($groupW + 6) 15 ($Z + 200 + $i) "#64748B" "6.5pt" "Segoe UI"
  }
}

function Add-Waterfall([System.Collections.ArrayList]$List, $Rows, [double]$X, [double]$Y, [double]$W, [double]$H, [int]$Z) {
  $maxAbs = 1.0
  foreach ($r in $Rows) { $maxAbs = [math]::Max($maxAbs, [math]::Abs([double]$r.Amount)) }
  $count = [math]::Max(1, $Rows.Count)
  $stepW = $W / $count
  $zeroY = $Y + ($H * 0.58)
  Add-Shape $List $X $zeroY $W 1 ($Z + 1) "#CBD5E1" "#CBD5E1" $false 0
  for ($i = 0; $i -lt $Rows.Count; $i++) {
    $r = $Rows[$i]
    $amount = [double]$r.Amount
    $barH = [math]::Max(4, [math]::Abs($amount) / $maxAbs * ($H * 0.46))
    $barX = $X + ($i * $stepW) + 10
    $barY = if ($amount -ge 0) { $zeroY - $barH } else { $zeroY }
    $color = if ($r.BridgeStep -like "*Budget*" -or $r.BridgeStep -like "*Actual*") { "#F97316" } elseif ($amount -ge 0) { "#2A9D8F" } else { "#DC2626" }
    Add-Shape $List $barX $barY ([math]::Max(14, $stepW - 20)) $barH ($Z + 10 + $i) $color $color $false 0
    Add-Text $List (Short-M $amount) ($barX - 4) ($barY - 17) ([math]::Max(34, $stepW)) 14 ($Z + 80 + $i) $color "6.5pt" "Segoe UI Semibold" $true
    Add-Text $List ([string]$r.BridgeStep) ($barX - 8) ($zeroY + 7) ([math]::Max(45, $stepW + 6)) 30 ($Z + 120 + $i) "#475569" "6pt" "Segoe UI"
  }
}

function Add-TableRows([System.Collections.ArrayList]$List, $Rows, [array]$Columns, [double]$X, [double]$Y, [double]$W, [double]$RowH, [int]$Z) {
  $colW = $W / $Columns.Count
  for ($c = 0; $c -lt $Columns.Count; $c++) {
    Add-Text $List $Columns[$c].Label ($X + $c * $colW) $Y ($colW - 4) 16 ($Z + $c) "#64748B" "7pt" "Segoe UI Semibold" $true
  }
  $i = 0
  foreach ($r in $Rows) {
    $rowY = $Y + 22 + ($i * $RowH)
    $fill = if ($i % 2 -eq 0) { "#FFF7ED" } else { "#FFFFFF" }
    Add-Shape $List $X ($rowY - 3) $W ($RowH - 1) ($Z + 50 + $i) $fill $fill $false 0
    for ($c = 0; $c -lt $Columns.Count; $c++) {
      $field = $Columns[$c].Field
      $text = [string]$r.$field
      $color = if ($text -like "+*" -or $text -like "*favorable*") { "#15803D" } elseif ($text -like "-*" -or $text -like "*risk*") { "#B91C1C" } else { "#111827" }
      Add-Text $List $text ($X + $c * $colW + 5) $rowY ($colW - 10) 16 ($Z + 100 + $i * 10 + $c) $color "7.5pt" "Segoe UI"
    }
    $i++
  }
}

function New-Section([string]$Name, [string]$DisplayName, [int]$Ordinal, [System.Collections.ArrayList]$Visuals) {
  return [ordered]@{
    id = $Ordinal
    name = $Name
    displayName = $DisplayName
    filters = "[]"
    ordinal = $Ordinal
    visualContainers = @($Visuals.ToArray())
    config = "{}"
    displayOption = 1
    width = 1280
    height = 720
  }
}

function Validate-Pbix([string]$Path) {
  $stream = [IO.File]::OpenRead($Path)
  try {
    [Microsoft.PowerBI.Packaging.PowerBIPackager]::Validate($stream)
  }
  finally {
    $stream.Dispose()
  }
}

$dates = CsvRows "dim_date.csv"
$bu = CsvRows "dim_business_unit.csv"
$products = CsvRows "dim_product.csv"
$regions = CsvRows "dim_region.csv"
$customers = CsvRows "dim_customer.csv"
$departments = CsvRows "dim_department.csv"
$financials = CsvRows "fact_financials.csv"
$cash = CsvRows "fact_cash.csv"
$bridge = CsvRows "fact_bridge.csv"
$opex = CsvRows "fact_opex_department.csv"
$commentary = CsvRows "fact_commentary.csv"

$dateByKey = @{}
foreach ($d in $dates) { $dateByKey[$d.DateKey] = $d }
$buByKey = @{}
foreach ($d in $bu) { $buByKey[$d.BusinessUnitKey] = $d.BusinessUnit }
$productByKey = @{}
foreach ($d in $products) { $productByKey[$d.ProductKey] = $d.Product }
$regionByKey = @{}
foreach ($d in $regions) { $regionByKey[$d.RegionKey] = $d.Region }
$customerByKey = @{}
foreach ($d in $customers) { $customerByKey[$d.CustomerKey] = $d.Customer }
$departmentByKey = @{}
foreach ($d in $departments) { $departmentByKey[$d.DepartmentKey] = $d.Department }

$latestActualDateKey = ($financials | Where-Object { $_.ScenarioKey -eq "S001" } | ForEach-Object { To-Int $_.DateKey } | Measure-Object -Maximum).Maximum
$currentMonth = $dateByKey[[string]$latestActualDateKey].MonthYear
$yearRows = $dates | Where-Object { $_.Year -eq "2026" } | Sort-Object { To-Int $_.MonthIndex }

$actualCurrent = $financials | Where-Object { $_.ScenarioKey -eq "S001" -and (To-Int $_.DateKey) -eq $latestActualDateKey }
$budgetCurrent = $financials | Where-Object { $_.ScenarioKey -eq "S002" -and (To-Int $_.DateKey) -eq $latestActualDateKey }
$forecastCurrent = $financials | Where-Object { $_.ScenarioKey -eq "S003" -and (To-Int $_.DateKey) -eq $latestActualDateKey }

$actualRevenue = Sum-Field $actualCurrent "Revenue"
$budgetRevenue = Sum-Field $budgetCurrent "Revenue"
$forecastRevenue = Sum-Field $forecastCurrent "Revenue"
$actualCogs = Sum-Field $actualCurrent "COGS"
$budgetCogs = Sum-Field $budgetCurrent "COGS"
$actualGrossMargin = $actualRevenue - $actualCogs
$budgetGrossMargin = $budgetRevenue - $budgetCogs
$actualEbitda = Sum-Field $actualCurrent "EBITDA"
$budgetEbitda = Sum-Field $budgetCurrent "EBITDA"
$actualOpex = Sum-Field $actualCurrent "AllocatedOpex"
$budgetOpex = Sum-Field $budgetCurrent "AllocatedOpex"
$orders = Sum-Field $actualCurrent "Orders"
$gmPct = if ($actualRevenue -ne 0) { $actualGrossMargin / $actualRevenue } else { 0 }
$ebitdaPct = if ($actualRevenue -ne 0) { $actualEbitda / $actualRevenue } else { 0 }

$actualCashRows = $cash | Where-Object { $_.ScenarioKey -eq "S001" -and (To-Int $_.DateKey) -eq $latestActualDateKey }
$budgetCashRows = $cash | Where-Object { $_.ScenarioKey -eq "S002" -and (To-Int $_.DateKey) -eq $latestActualDateKey }
$actualCash = Sum-Field $actualCashRows "CashBalance"
$budgetCash = Sum-Field $budgetCashRows "CashBalance"
$arBalance = Sum-Field $actualCashRows "ARBalance"
$weightedDsoNumerator = 0.0
foreach ($r in $actualCashRows) { $weightedDsoNumerator += (To-Dec $r.ARBalance) * (To-Dec $r.DSO) }
$weightedDso = if ($arBalance -ne 0) { $weightedDsoNumerator / $arBalance } else { 0 }

$trendRows = New-Object System.Collections.ArrayList
foreach ($d in $yearRows) {
  $dk = To-Int $d.DateKey
  $rowsA = $financials | Where-Object { $_.ScenarioKey -eq "S001" -and (To-Int $_.DateKey) -eq $dk }
  $rowsB = $financials | Where-Object { $_.ScenarioKey -eq "S002" -and (To-Int $_.DateKey) -eq $dk }
  $rowsF = $financials | Where-Object { $_.ScenarioKey -eq "S003" -and (To-Int $_.DateKey) -eq $dk }
  [void]$trendRows.Add([PSCustomObject]@{
    Month = $d.MonthName
    Actual = Sum-Field $rowsA "Revenue"
    Budget = Sum-Field $rowsB "Revenue"
    Forecast = Sum-Field $rowsF "Revenue"
  })
}

$buVariance = New-Object System.Collections.ArrayList
foreach ($b in $bu) {
  $rowsA = $actualCurrent | Where-Object { $_.BusinessUnitKey -eq $b.BusinessUnitKey }
  $rowsB = $budgetCurrent | Where-Object { $_.BusinessUnitKey -eq $b.BusinessUnitKey }
  [void]$buVariance.Add([PSCustomObject]@{
    Name = $b.BusinessUnit
    Value = (Sum-Field $rowsA "EBITDA") - (Sum-Field $rowsB "EBITDA")
  })
}
$buVariance = @($buVariance | Sort-Object Value)

$bridgeRows = New-Object System.Collections.ArrayList
$bridgeCurrent = $bridge | Where-Object { (To-Int $_.DateKey) -eq $latestActualDateKey }
foreach ($g in ($bridgeCurrent | Group-Object BridgeStep)) {
  $order = ($g.Group | Select-Object -First 1).BridgeOrder
  [void]$bridgeRows.Add([PSCustomObject]@{
    BridgeStep = $g.Name
    BridgeOrder = To-Int $order
    Amount = Sum-Field $g.Group "Amount"
  })
}
$bridgeRows = @($bridgeRows | Sort-Object BridgeOrder)

$customerRows = New-Object System.Collections.ArrayList
foreach ($c in $customers) {
  $rowsA = $actualCurrent | Where-Object { $_.CustomerKey -eq $c.CustomerKey }
  $rowsB = $budgetCurrent | Where-Object { $_.CustomerKey -eq $c.CustomerKey }
  $rev = Sum-Field $rowsA "Revenue"
  if ($rev -gt 0) {
    [void]$customerRows.Add([PSCustomObject]@{
      Customer = $c.Customer
      Revenue = $rev
      RevenueText = Short-M $rev
      VarText = Delta-Text ($rev - (Sum-Field $rowsB "Revenue"))
      Segment = $c.CustomerSegment
    })
  }
}
$customerRows = @($customerRows | Sort-Object Revenue -Descending | Select-Object -First 6)

$productRows = New-Object System.Collections.ArrayList
foreach ($p in $products) {
  $rowsA = $actualCurrent | Where-Object { $_.ProductKey -eq $p.ProductKey }
  $rowsB = $budgetCurrent | Where-Object { $_.ProductKey -eq $p.ProductKey }
  $rev = Sum-Field $rowsA "Revenue"
  [void]$productRows.Add([PSCustomObject]@{
    Name = $p.Product
    Value = $rev - (Sum-Field $rowsB "Revenue")
  })
}
$productRows = @($productRows | Sort-Object Value | Select-Object -First 6)

$regionRows = New-Object System.Collections.ArrayList
foreach ($r in $regions) {
  $rowsA = $actualCurrent | Where-Object { $_.RegionKey -eq $r.RegionKey }
  $rowsB = $budgetCurrent | Where-Object { $_.RegionKey -eq $r.RegionKey }
  $rev = Sum-Field $rowsA "Revenue"
  [void]$regionRows.Add([PSCustomObject]@{
    Region = $r.Region
    RevenueText = Short-M $rev
    VarText = Delta-Text ($rev - (Sum-Field $rowsB "Revenue"))
    EbitdaText = Short-M (Sum-Field $rowsA "EBITDA")
  })
}

$opexRows = New-Object System.Collections.ArrayList
$actualOpexRows = $opex | Where-Object { $_.ScenarioKey -eq "S001" -and (To-Int $_.DateKey) -eq $latestActualDateKey }
$budgetOpexRows = $opex | Where-Object { $_.ScenarioKey -eq "S002" -and (To-Int $_.DateKey) -eq $latestActualDateKey }
foreach ($d in $departments) {
  $rowsA = $actualOpexRows | Where-Object { $_.DepartmentKey -eq $d.DepartmentKey }
  $rowsB = $budgetOpexRows | Where-Object { $_.DepartmentKey -eq $d.DepartmentKey }
  $a = Sum-Field $rowsA "Opex"
  $b = Sum-Field $rowsB "Opex"
  [void]$opexRows.Add([PSCustomObject]@{
    Department = $d.Department
    ActualText = Short-M $a
    BudgetText = Short-M $b
    VarText = Delta-Text ($a - $b)
    Value = $a - $b
  })
}
$opexRowsSorted = @($opexRows | Sort-Object Value -Descending)

$cashRows = New-Object System.Collections.ArrayList
foreach ($r in $regions) {
  $rows = $actualCashRows | Where-Object { $_.RegionKey -eq $r.RegionKey }
  $cashBalance = Sum-Field $rows "CashBalance"
  $ar = Sum-Field $rows "ARBalance"
  $num = 0.0
  foreach ($cr in $rows) { $num += (To-Dec $cr.ARBalance) * (To-Dec $cr.DSO) }
  $dso = if ($ar -ne 0) { $num / $ar } else { 0 }
  [void]$cashRows.Add([PSCustomObject]@{
    Region = $r.Region
    CashText = Short-M $cashBalance
    ARText = Short-M $ar
    DSOText = ("{0:n1}" -f $dso)
  })
}

$comment = $commentary | Where-Object { (To-Int $_.DateKey) -eq $latestActualDateKey } | Select-Object -First 1

$pages = @()

$overview = New-Object System.Collections.ArrayList
Add-Header $overview "Executive Overview" "Actual vs Budget vs Forecast | Latest actual month: $currentMonth"
$revenueColor = if ($actualRevenue - $budgetRevenue -ge 0) { "#15803D" } else { "#B91C1C" }
$gmColor = if ($actualGrossMargin - $budgetGrossMargin -ge 0) { "#15803D" } else { "#B91C1C" }
$ebitdaColor = if ($actualEbitda - $budgetEbitda -ge 0) { "#15803D" } else { "#B91C1C" }
$opexColor = if ($actualOpex - $budgetOpex -le 0) { "#15803D" } else { "#B91C1C" }
$cashColor = if ($actualCash - $budgetCash -ge 0) { "#15803D" } else { "#B91C1C" }
Add-KpiCard $overview 24 88 186 "Revenue" (Short-M $actualRevenue) ((Delta-Text ($actualRevenue - $budgetRevenue)) + " vs Budget") $revenueColor 200
Add-KpiCard $overview 223 88 186 "Gross Margin %" (Short-Pct $gmPct) ((Delta-Text ($actualGrossMargin - $budgetGrossMargin)) + " GM") $gmColor 210
Add-KpiCard $overview 422 88 186 "EBITDA" (Short-M $actualEbitda) ((Delta-Text ($actualEbitda - $budgetEbitda)) + " vs Budget") $ebitdaColor 220
Add-KpiCard $overview 621 88 186 "Opex" (Short-M $actualOpex) ((Delta-Text ($actualOpex - $budgetOpex)) + " spend") $opexColor 230
Add-KpiCard $overview 820 88 186 "Cash" (Short-M $actualCash) ((Delta-Text ($actualCash - $budgetCash)) + " vs Budget") $cashColor 240
Add-KpiCard $overview 1019 88 186 "Orders" ("{0:n0}" -f $orders) ("EBITDA margin " + (Short-Pct $ebitdaPct)) "#C2410C" 250
Add-Panel $overview 24 192 760 328 300 "12M Revenue Trend" "Orange = Actual, gray = Budget, light orange = Forecast"
Add-ColumnChart $overview $trendRows 46 255 718 230 330 "Month" "Actual" "Budget" "Forecast"
Add-Text $overview "Actual" 590 211 50 16 610 "#F97316" "7pt" "Segoe UI Semibold" $true
Add-Text $overview "Budget" 645 211 50 16 611 "#64748B" "7pt" "Segoe UI Semibold" $true
Add-Text $overview "Forecast" 704 211 70 16 612 "#EA580C" "7pt" "Segoe UI Semibold" $true
Add-Panel $overview 812 192 444 328 700 "EBITDA Variance by Business Unit" "Actual less budget, current month"
Add-BarList $overview $buVariance 836 258 388 37 730 "Name" "Value"
Add-Panel $overview 24 540 602 150 900 "Commentary: What happened? Why? What next?" "Management narrative for monthly FP&A review"
Add-Text $overview ("What happened: " + $comment.WhatHappened) 44 595 560 28 930 "#111827" "8pt"
Add-Text $overview ("Why: " + $comment.Why) 44 624 560 28 931 "#111827" "8pt"
Add-Text $overview ("What next: " + $comment.WhatNext) 44 653 560 28 932 "#C2410C" "8pt" "Segoe UI Semibold" $true
Add-Panel $overview 650 540 606 150 950 "FP&A Readout" "Latest closed month operating posture"
Add-Text $overview ("Revenue " + (Short-M $actualRevenue) + " vs Budget " + (Short-M $budgetRevenue) + " and Forecast " + (Short-M $forecastRevenue) + ".") 670 596 560 22 970 "#111827" "9pt"
Add-Text $overview ("EBITDA " + (Short-M $actualEbitda) + " with margin " + (Short-Pct $ebitdaPct) + "; weighted DSO " + ("{0:n1}" -f $weightedDso) + " days.") 670 626 560 22 971 "#111827" "9pt"
Add-Text $overview "Primary drill path: Company -> BU -> Region -> Product -> Customer." 670 656 560 20 972 "#C2410C" "9pt" "Segoe UI Semibold" $true
$pages += New-Section "executive_overview_fpa" "Executive Overview" 0 $overview

$bridgePage = New-Object System.Collections.ArrayList
Add-Header $bridgePage "Variance Bridge" "Budget -> Actual EBITDA bridge and operating driver diagnostics"
Add-Panel $bridgePage 24 88 820 360 100 "Budget to Actual EBITDA Waterfall" "Bridge steps aggregate across business units and regions"
Add-Waterfall $bridgePage $bridgeRows 50 175 770 230 130
Add-Panel $bridgePage 874 88 382 360 500 "Key Variance Drivers" "Current month, by business unit"
Add-BarList $bridgePage $buVariance 900 158 320 40 530 "Name" "Value"
Add-Panel $bridgePage 24 470 604 220 800 "Product Variance Drilldown" "Actual revenue less budget"
Add-BarList $bridgePage $productRows 50 535 542 25 830 "Name" "Value"
Add-Panel $bridgePage 652 470 604 220 1000 "Region Snapshot" "Revenue, variance, EBITDA"
$regionTable = New-Object System.Collections.ArrayList
foreach ($r in $regionRows) {
  [void]$regionTable.Add([PSCustomObject]@{
    Region = $r.Region
    Revenue = $r.RevenueText
    Var = $r.VarText
    EBITDA = $r.EbitdaText
  })
}
Add-TableRows $bridgePage $regionTable @(
  @{Label="Region"; Field="Region"},
  @{Label="Revenue"; Field="Revenue"},
  @{Label="Var vs Budget"; Field="Var"},
  @{Label="EBITDA"; Field="EBITDA"}
) 680 530 548 28 1040
$pages += New-Section "variance_bridge_fpa" "Variance Bridge" 1 $bridgePage

$drillPage = New-Object System.Collections.ArrayList
Add-Header $drillPage "Customer / Product Drilldown" "Company -> department/product/customer detail for FP&A review"
Add-Panel $drillPage 24 88 596 602 100 "Top Customers" "Revenue and variance, current month"
$customerTable = New-Object System.Collections.ArrayList
foreach ($r in $customerRows) {
  [void]$customerTable.Add([PSCustomObject]@{
    Customer = $r.Customer
    Segment = $r.Segment
    Revenue = $r.RevenueText
    Var = $r.VarText
  })
}
Add-TableRows $drillPage $customerTable @(
  @{Label="Customer"; Field="Customer"},
  @{Label="Segment"; Field="Segment"},
  @{Label="Revenue"; Field="Revenue"},
  @{Label="Var"; Field="Var"}
) 48 155 548 40 130
Add-Panel $drillPage 652 88 604 282 500 "Product Variance" "Unfavorable and favorable movement by product"
Add-BarList $drillPage $productRows 680 158 540 31 530 "Name" "Value"
Add-Panel $drillPage 652 400 604 290 800 "Drilldown Guidance" "How this pack is intended to be used in monthly close"
Add-Text $drillPage "1. Start at company KPI cards, then isolate EBITDA variance by BU." 680 462 540 22 830 "#111827" "9pt"
Add-Text $drillPage "2. Use region and product views to separate mix/rate issues from controllable opex." 680 495 540 22 831 "#111827" "9pt"
Add-Text $drillPage "3. Review customer concentration and margin exposure before forecast lock." 680 528 540 22 832 "#111827" "9pt"
Add-Text $drillPage "4. Translate commentary into actions: pricing, demand recovery, and spend controls." 680 561 540 22 833 "#C2410C" "9pt" "Segoe UI Semibold" $true
Add-Shape $drillPage 680 612 520 36 840 "#FFF7ED" "#FED7AA" $true 0
Add-Text $drillPage "Semantic model included: DimDate, Scenario, BU, Product, Region, Customer, Department + facts for P&L, Opex, Cash, Bridge and Commentary." 696 622 488 22 841 "#9A3412" "8pt" "Segoe UI Semibold" $true
$pages += New-Section "customer_product_drilldown_fpa" "Customer / Product Drilldown" 2 $drillPage

$cashPage = New-Object System.Collections.ArrayList
Add-Header $cashPage "Opex & Cash Control" "Department spend, cash balance, AR and DSO"
Add-Panel $cashPage 24 88 604 282 100 "Department Opex Variance" "Actual less budget"
Add-BarList $cashPage $opexRowsSorted 52 158 540 31 130 "Department" "Value" "#DC2626" "#2A9D8F"
Add-Panel $cashPage 652 88 604 282 500 "Cash / AR / DSO by Region" "Latest actual month"
$cashTable = New-Object System.Collections.ArrayList
foreach ($r in $cashRows) {
  [void]$cashTable.Add([PSCustomObject]@{
    Region = $r.Region
    Cash = $r.CashText
    AR = $r.ARText
    DSO = $r.DSOText
  })
}
Add-TableRows $cashPage $cashTable @(
  @{Label="Region"; Field="Region"},
  @{Label="Cash"; Field="Cash"},
  @{Label="AR"; Field="AR"},
  @{Label="DSO"; Field="DSO"}
) 680 154 548 39 530
Add-KpiCard $cashPage 24 402 188 "Cash Balance" (Short-M $actualCash) ((Delta-Text ($actualCash - $budgetCash)) + " vs Budget") $cashColor 800
Add-KpiCard $cashPage 232 402 188 "AR Balance" (Short-M $arBalance) ("Weighted DSO " + ("{0:n1}" -f $weightedDso)) "#C2410C" 810
Add-KpiCard $cashPage 440 402 188 "Opex" (Short-M $actualOpex) ((Delta-Text ($actualOpex - $budgetOpex)) + " spend") $opexColor 820
Add-Panel $cashPage 652 402 604 288 900 "Management Actions" "Control loop for next forecast cycle"
Add-Text $cashPage "Cash: tighten collection follow-up on largest AR balances and protect minimum operating cash." 680 466 540 24 930 "#111827" "9pt"
Add-Text $cashPage "Opex: review departments above plan and separate timing from structural overspend." 680 505 540 24 931 "#111827" "9pt"
Add-Text $cashPage "Forecast: update run-rate assumptions for products below budget and lock owner actions." 680 544 540 24 932 "#111827" "9pt"
Add-Text $cashPage "Next month close: refresh CSV extracts, open PBIX, refresh model, validate KPI reconciliation." 680 583 540 24 933 "#C2410C" "9pt" "Segoe UI Semibold" $true
$pages += New-Section "opex_cash_control_fpa" "Opex & Cash Control" 3 $cashPage

Copy-Item -LiteralPath $ModelPbix -Destination $OutputPbix -Force

$package = [System.IO.Packaging.Package]::Open($OutputPbix, [IO.FileMode]::Open, [IO.FileAccess]::ReadWrite)
try {
  $layoutUri = New-Object System.Uri("/Report/Layout", [System.UriKind]::Relative)
  $layoutPart = $package.GetPart($layoutUri)
  $stream = $layoutPart.GetStream([IO.FileMode]::Open, [IO.FileAccess]::ReadWrite)
  try {
    $memory = New-Object IO.MemoryStream
    $stream.CopyTo($memory)
    $layoutText = [Text.Encoding]::Unicode.GetString($memory.ToArray())
    $layout = $layoutText | ConvertFrom-Json

    $layout.sections = @($pages)
    $config = $layout.config | ConvertFrom-Json
    $config.activeSectionIndex = 0
    $config.themeCollection.baseTheme.name = "CY26SU05"
    $layout.config = ($config | ConvertTo-Json -Depth 100 -Compress)

    $updatedLayoutText = $layout | ConvertTo-Json -Depth 100 -Compress
    $updatedBytes = [Text.Encoding]::Unicode.GetBytes($updatedLayoutText)
    $stream.SetLength(0)
    $stream.Position = 0
    $stream.Write($updatedBytes, 0, $updatedBytes.Length)
  }
  finally {
    $stream.Dispose()
  }
}
finally {
  $package.Close()
}

$package = [System.IO.Packaging.Package]::Open($OutputPbix, [IO.FileMode]::Open, [IO.FileAccess]::ReadWrite)
try {
  $securityUri = New-Object System.Uri("/SecurityBindings", [System.UriKind]::Relative)
  if ($package.PartExists($securityUri)) {
    $package.DeletePart($securityUri)
  }
}
finally {
  $package.Close()
}

Validate-Pbix $OutputPbix
Copy-Item -LiteralPath $OutputPbix -Destination $FinalPbix -Force
Validate-Pbix $FinalPbix

$buildInfo = [ordered]@{
  generated_at = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
  project = "Monthly FP&A Performance Pack"
  source_model_pbix = $ModelPbix
  output_pbix = $OutputPbix
  final_pbix = $FinalPbix
  latest_actual_month = $currentMonth
  pages = @("Executive Overview", "Variance Bridge", "Customer / Product Drilldown", "Opex & Cash Control")
  visual_containers = ($pages | ForEach-Object { $_.visualContainers.Count } | Measure-Object -Sum).Sum
  metrics = [ordered]@{
    revenue = [math]::Round($actualRevenue, 2)
    budget_revenue = [math]::Round($budgetRevenue, 2)
    forecast_revenue = [math]::Round($forecastRevenue, 2)
    gross_margin_pct = [math]::Round($gmPct, 4)
    ebitda = [math]::Round($actualEbitda, 2)
    opex = [math]::Round($actualOpex, 2)
    cash = [math]::Round($actualCash, 2)
    weighted_dso = [math]::Round($weightedDso, 2)
  }
  validation = "PowerBIPackager.Validate passed for output and final PBIX"
}

$buildInfo | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath (Join-Path $QaRoot "pbix_report_layout_validation.json") -Encoding UTF8
Write-Output ($buildInfo | ConvertTo-Json -Depth 10)
