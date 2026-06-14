// Monthly FP&A Performance Pack
// In Power BI Desktop:
// 1. Create a Text parameter named pProjectRoot.
// 2. Set pProjectRoot to the absolute project path, for example:
//    C:\Users\Win\OneDrive\Codex\Portfolio\BI\Project 01 - Monthly FP&A Performance Pack
// 3. Create the helper query LoadPreparedCsv.
// 4. Create each table query below and apply the listed type transformations.

// Parameter query
// Query name: pProjectRoot
let
    Source = "C:\Users\Win\OneDrive\Codex\Portfolio\BI\Project 01 - Monthly FP&A Performance Pack"
in
    Source

// Helper query
// Query name: LoadPreparedCsv
(RelativePath as text) as table =>
let
    Source = Csv.Document(
        File.Contents(pProjectRoot & "\data\prepared\" & RelativePath),
        [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]
    ),
    PromotedHeaders = Table.PromoteHeaders(Source, [PromoteAllScalars = true])
in
    PromotedHeaders

// Query name: DimDate
let
    Source = LoadPreparedCsv("dim_date.csv"),
    ChangedType = Table.TransformColumnTypes(
        Source,
        {
            {"DateKey", Int64.Type},
            {"MonthStart", type date},
            {"Year", Int64.Type},
            {"Quarter", type text},
            {"MonthNumber", Int64.Type},
            {"MonthName", type text},
            {"MonthYear", type text},
            {"MonthIndex", Int64.Type},
            {"IsActualClosed", type text},
            {"FiscalYear", Int64.Type},
            {"FiscalQuarter", type text}
        }
    )
in
    ChangedType

// Query name: DimScenario
let
    Source = LoadPreparedCsv("dim_scenario.csv"),
    ChangedType = Table.TransformColumnTypes(
        Source,
        {
            {"ScenarioKey", type text},
            {"Scenario", type text},
            {"ScenarioSort", Int64.Type},
            {"ScenarioType", type text}
        }
    )
in
    ChangedType

// Query name: DimBusinessUnit
let
    Source = LoadPreparedCsv("dim_business_unit.csv"),
    ChangedType = Table.TransformColumnTypes(Source, {{"BusinessUnitKey", type text}, {"BusinessUnit", type text}})
in
    ChangedType

// Query name: DimProduct
let
    Source = LoadPreparedCsv("dim_product.csv"),
    ChangedType = Table.TransformColumnTypes(
        Source,
        {{"ProductKey", type text}, {"BusinessUnit", type text}, {"Product", type text}}
    )
in
    ChangedType

// Query name: DimRegion
let
    Source = LoadPreparedCsv("dim_region.csv"),
    ChangedType = Table.TransformColumnTypes(Source, {{"RegionKey", type text}, {"Region", type text}})
in
    ChangedType

// Query name: DimCustomer
let
    Source = LoadPreparedCsv("dim_customer.csv"),
    ChangedType = Table.TransformColumnTypes(
        Source,
        {{"CustomerKey", type text}, {"Customer", type text}, {"CustomerSegment", type text}, {"Industry", type text}}
    )
in
    ChangedType

// Query name: DimDepartment
let
    Source = LoadPreparedCsv("dim_department.csv"),
    ChangedType = Table.TransformColumnTypes(Source, {{"DepartmentKey", type text}, {"Department", type text}})
in
    ChangedType

// Query name: FactFinancials
let
    Source = LoadPreparedCsv("fact_financials.csv"),
    ChangedType = Table.TransformColumnTypes(
        Source,
        {
            {"FactFinanceKey", type text},
            {"DateKey", Int64.Type},
            {"ScenarioKey", type text},
            {"BusinessUnitKey", type text},
            {"ProductKey", type text},
            {"RegionKey", type text},
            {"CustomerKey", type text},
            {"Revenue", Currency.Type},
            {"COGS", Currency.Type},
            {"GrossMargin", Currency.Type},
            {"AllocatedOpex", Currency.Type},
            {"EBITDA", Currency.Type},
            {"Orders", Int64.Type},
            {"CashImpact", Currency.Type}
        }
    )
in
    ChangedType

// Query name: FactOpexDepartment
let
    Source = LoadPreparedCsv("fact_opex_department.csv"),
    ChangedType = Table.TransformColumnTypes(
        Source,
        {
            {"FactOpexKey", type text},
            {"DateKey", Int64.Type},
            {"ScenarioKey", type text},
            {"BusinessUnitKey", type text},
            {"RegionKey", type text},
            {"DepartmentKey", type text},
            {"Opex", Currency.Type},
            {"FTE", type number}
        }
    )
in
    ChangedType

// Query name: FactCash
let
    Source = LoadPreparedCsv("fact_cash.csv"),
    ChangedType = Table.TransformColumnTypes(
        Source,
        {
            {"FactCashKey", type text},
            {"DateKey", Int64.Type},
            {"ScenarioKey", type text},
            {"BusinessUnitKey", type text},
            {"RegionKey", type text},
            {"CashBalance", Currency.Type},
            {"ARBalance", Currency.Type},
            {"DSO", type number},
            {"Capex", Currency.Type}
        }
    )
in
    ChangedType

// Query name: FactBridge
let
    Source = LoadPreparedCsv("fact_bridge.csv"),
    ChangedType = Table.TransformColumnTypes(
        Source,
        {
            {"BridgeKey", type text},
            {"DateKey", Int64.Type},
            {"BusinessUnitKey", type text},
            {"RegionKey", type text},
            {"BridgeStep", type text},
            {"BridgeOrder", Int64.Type},
            {"Amount", Currency.Type}
        }
    )
in
    ChangedType

// Query name: FactCommentary
let
    Source = LoadPreparedCsv("fact_commentary.csv"),
    ChangedType = Table.TransformColumnTypes(
        Source,
        {
            {"DateKey", Int64.Type},
            {"Audience", type text},
            {"WhatHappened", type text},
            {"Why", type text},
            {"WhatNext", type text},
            {"Severity", type text}
        }
    )
in
    ChangedType
