## Total Revenue

```DAX
Total Revenue =
SUM ( FactFinancialSummary[external_revenue_usd] )
```

Format: `$#,0;($#,0);$0`

Consolidated external revenue after excluding intercompany revenue.

## Gross Revenue

```DAX
Gross Revenue =
SUM ( FactFinancialSummary[gross_revenue_usd] )
```

Format: `$#,0;($#,0);$0`

External plus intercompany revenue before elimination.

## Intercompany Revenue

```DAX
Intercompany Revenue =
SUM ( FactFinancialSummary[intercompany_revenue_usd] )
```

Format: `$#,0;($#,0);$0`

Intercompany revenue requiring elimination.

## Intercompany Elimination

```DAX
Intercompany Elimination =
SUM ( FactFinancialSummary[intercompany_elimination_usd] )
```

Format: `$#,0;($#,0);$0`

Net intercompany elimination impact.

## Gross Profit

```DAX
Gross Profit =
SUM ( FactFinancialSummary[gross_profit_usd] )
```

Format: `$#,0;($#,0);$0`

Revenue minus cost of services.

## Gross Margin %

```DAX
Gross Margin % =
DIVIDE ( [Gross Profit], [Total Revenue] )
```

Format: `0.0%`

Gross profit divided by consolidated external revenue.

## OPEX

```DAX
OPEX =
SUM ( FactFinancialSummary[opex_usd] )
```

Format: `$#,0;($#,0);$0`

Personnel, facilities, sales and marketing, and G&A.

## EBITDA

```DAX
EBITDA =
SUM ( FactFinancialSummary[ebitda_usd] )
```

Format: `$#,0;($#,0);$0`

Gross profit plus OPEX after intercompany elimination.

## EBITDA Margin %

```DAX
EBITDA Margin % =
DIVIDE ( [EBITDA], [Total Revenue] )
```

Format: `0.0%`

EBITDA divided by consolidated external revenue.

## Operating Income

```DAX
Operating Income =
SUM ( FactFinancialSummary[operating_income_usd] )
```

Format: `$#,0;($#,0);$0`

EBITDA less depreciation.

## Net Income

```DAX
Net Income =
SUM ( FactFinancialSummary[net_income_usd] )
```

Format: `$#,0;($#,0);$0`

Operating income less interest and tax.

## Cash Position

```DAX
Cash Position =
SUM ( FactFinancialSummary[cash_position_usd] )
```

Format: `$#,0;($#,0);$0`

Period-end cash position by entity and BU allocation.

## Operating Cash Flow

```DAX
Operating Cash Flow =
SUM ( FactFinancialSummary[operating_cash_flow_usd] )
```

Format: `$#,0;($#,0);$0`

Operating cash flow proxy tied to EBITDA conversion.

## Working Capital

```DAX
Working Capital =
SUM ( FactFinancialSummary[working_capital_usd] )
```

Format: `$#,0;($#,0);$0`

Working capital proxy for close review.

## Actual Revenue

```DAX
Actual Revenue =
CALCULATE ( [Total Revenue], DimScenario[scenario] = "Actual" )
```

Format: `$#,0;($#,0);$0`

Actual consolidated revenue.

## Budget Revenue

```DAX
Budget Revenue =
CALCULATE ( [Total Revenue], DimScenario[scenario] = "Budget" )
```

Format: `$#,0;($#,0);$0`

Budget consolidated revenue.

## Revenue Var vs Budget

```DAX
Revenue Var vs Budget =
[Actual Revenue] - [Budget Revenue]
```

Format: `$#,0;($#,0);$0`

Actual revenue less budget revenue.

## Revenue Var %

```DAX
Revenue Var % =
DIVIDE ( [Revenue Var vs Budget], [Budget Revenue] )
```

Format: `0.0%`

Revenue variance divided by budget revenue.

## Actual EBITDA

```DAX
Actual EBITDA =
CALCULATE ( [EBITDA], DimScenario[scenario] = "Actual" )
```

Format: `$#,0;($#,0);$0`

Actual EBITDA.

## Budget EBITDA

```DAX
Budget EBITDA =
CALCULATE ( [EBITDA], DimScenario[scenario] = "Budget" )
```

Format: `$#,0;($#,0);$0`

Budget EBITDA.

## EBITDA Var vs Budget

```DAX
EBITDA Var vs Budget =
[Actual EBITDA] - [Budget EBITDA]
```

Format: `$#,0;($#,0);$0`

Actual EBITDA less budget EBITDA.

## EBITDA Var %

```DAX
EBITDA Var % =
DIVIDE ( [EBITDA Var vs Budget], [Budget EBITDA] )
```

Format: `0.0%`

EBITDA variance divided by budget EBITDA.

## Forecast EBITDA

```DAX
Forecast EBITDA =
CALCULATE ( [EBITDA], DimScenario[scenario] = "Forecast" )
```

Format: `$#,0;($#,0);$0`

Forecast EBITDA.

## Forecast Accuracy %

```DAX
Forecast Accuracy % =
1 - ABS ( DIVIDE ( [Actual EBITDA] - [Forecast EBITDA], [Actual EBITDA] ) )
```

Format: `0.0%`

Directional forecast accuracy for EBITDA.

## Open Exception Count

```DAX
Open Exception Count =
CALCULATE ( COUNTROWS ( FactCloseExceptions ), FactCloseExceptions[status] <> "Closed" )
```

Format: `#,0`

Open or in-progress close exceptions.

## Open Exception Value

```DAX
Open Exception Value =
CALCULATE ( SUM ( FactCloseExceptions[amount_usd] ), FactCloseExceptions[status] <> "Closed" )
```

Format: `$#,0;($#,0);$0`

Value attached to unresolved close exceptions.
