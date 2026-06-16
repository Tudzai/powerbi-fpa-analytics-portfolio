# DAX Measures

## Revenue

```DAX
Revenue = VAR ScenarioID = SELECTEDVALUE(DimScenario[ScenarioID], "Base") RETURN CALCULATE(SUM(FactPnlMonthly[Revenue]), FactPnlMonthly[ScenarioID] = ScenarioID)
```

Format: `$#,0;($#,0);$0`

## Plan Revenue

```DAX
Plan Revenue = VAR ScenarioID = SELECTEDVALUE(DimScenario[ScenarioID], "Base") RETURN CALCULATE(SUM(FactPnlMonthly[PlanRevenue]), FactPnlMonthly[ScenarioID] = ScenarioID)
```

Format: `$#,0;($#,0);$0`

## Forecast Revenue

```DAX
Forecast Revenue = VAR ScenarioID = SELECTEDVALUE(DimScenario[ScenarioID], "Base") RETURN CALCULATE(SUM(FactPnlMonthly[ForecastRevenue]), FactPnlMonthly[ScenarioID] = ScenarioID)
```

Format: `$#,0;($#,0);$0`

## Revenue vs Plan

```DAX
Revenue vs Plan = [Revenue] - [Plan Revenue]
```

Format: `$#,0;($#,0);$0`

## Revenue vs Plan %

```DAX
Revenue vs Plan % = DIVIDE([Revenue vs Plan], [Plan Revenue])
```

Format: `0.0%`

## Gross Profit

```DAX
Gross Profit = VAR ScenarioID = SELECTEDVALUE(DimScenario[ScenarioID], "Base") RETURN CALCULATE(SUM(FactPnlMonthly[GrossProfit]), FactPnlMonthly[ScenarioID] = ScenarioID)
```

Format: `$#,0;($#,0);$0`

## Gross Margin %

```DAX
Gross Margin % = DIVIDE([Gross Profit], [Revenue])
```

Format: `0.0%`

## EBITDA

```DAX
EBITDA = VAR ScenarioID = SELECTEDVALUE(DimScenario[ScenarioID], "Base") RETURN CALCULATE(SUM(FactPnlMonthly[EBITDA]), FactPnlMonthly[ScenarioID] = ScenarioID)
```

Format: `$#,0;($#,0);$0`

## Plan EBITDA

```DAX
Plan EBITDA = VAR ScenarioID = SELECTEDVALUE(DimScenario[ScenarioID], "Base") RETURN CALCULATE(SUM(FactPnlMonthly[PlanEBITDA]), FactPnlMonthly[ScenarioID] = ScenarioID)
```

Format: `$#,0;($#,0);$0`

## EBITDA vs Plan

```DAX
EBITDA vs Plan = [EBITDA] - [Plan EBITDA]
```

Format: `$#,0;($#,0);$0`

## EBITDA Margin %

```DAX
EBITDA Margin % = DIVIDE([EBITDA], [Revenue])
```

Format: `0.0%`

## Net Income

```DAX
Net Income = VAR ScenarioID = SELECTEDVALUE(DimScenario[ScenarioID], "Base") RETURN CALCULATE(SUM(FactPnlMonthly[NetIncome]), FactPnlMonthly[ScenarioID] = ScenarioID)
```

Format: `$#,0;($#,0);$0`

## Operating Expense

```DAX
Operating Expense = VAR ScenarioID = SELECTEDVALUE(DimScenario[ScenarioID], "Base") RETURN CALCULATE(SUM(FactOpexMonthly[OperatingExpense]), FactOpexMonthly[ScenarioID] = ScenarioID)
```

Format: `$#,0;($#,0);$0`

## Latest Revenue

```DAX
Latest Revenue = CALCULATE([Revenue], DimDate[IsLatestCompleteMonth] = 1)
```

Format: `$#,0;($#,0);$0`

## Latest Gross Margin %

```DAX
Latest Gross Margin % = CALCULATE([Gross Margin %], DimDate[IsLatestCompleteMonth] = 1)
```

Format: `0.0%`

## Latest EBITDA

```DAX
Latest EBITDA = CALCULATE([EBITDA], DimDate[IsLatestCompleteMonth] = 1)
```

Format: `$#,0;($#,0);$0`

## Latest EBITDA Margin %

```DAX
Latest EBITDA Margin % = CALCULATE([EBITDA Margin %], DimDate[IsLatestCompleteMonth] = 1)
```

Format: `0.0%`

## Latest Cash Balance

```DAX
Latest Cash Balance = VAR ScenarioID = SELECTEDVALUE(DimScenario[ScenarioID], "Base") RETURN CALCULATE(MAX(FactCashMonthly[CashBalance]), FactCashMonthly[ScenarioID] = ScenarioID, DimDate[IsLatestCompleteMonth] = 1)
```

Format: `$#,0;($#,0);$0`

## Cash Balance

```DAX
Cash Balance = VAR ScenarioID = SELECTEDVALUE(DimScenario[ScenarioID], "Base") RETURN CALCULATE(MAX(FactCashMonthly[CashBalance]), FactCashMonthly[ScenarioID] = ScenarioID)
```

Format: `$#,0;($#,0);$0`

## Operating Cash Flow

```DAX
Operating Cash Flow = VAR ScenarioID = SELECTEDVALUE(DimScenario[ScenarioID], "Base") RETURN CALCULATE(SUM(FactCashMonthly[OperatingCashFlow]), FactCashMonthly[ScenarioID] = ScenarioID)
```

Format: `$#,0;($#,0);$0`

## Free Cash Flow

```DAX
Free Cash Flow = VAR ScenarioID = SELECTEDVALUE(DimScenario[ScenarioID], "Base") RETURN CALCULATE(SUM(FactCashMonthly[FreeCashFlow]), FactCashMonthly[ScenarioID] = ScenarioID)
```

Format: `$#,0;($#,0);$0`

## Latest Free Cash Flow

```DAX
Latest Free Cash Flow = VAR ScenarioID = SELECTEDVALUE(DimScenario[ScenarioID], "Base") RETURN CALCULATE(MAX(FactCashMonthly[FreeCashFlow]), FactCashMonthly[ScenarioID] = ScenarioID, DimDate[IsLatestCompleteMonth] = 1)
```

Format: `$#,0;($#,0);$0`

## Net Burn

```DAX
Net Burn = VAR ScenarioID = SELECTEDVALUE(DimScenario[ScenarioID], "Base") RETURN CALCULATE(MAX(FactCashMonthly[NetBurn]), FactCashMonthly[ScenarioID] = ScenarioID)
```

Format: `$#,0;($#,0);$0`

## Latest Net Burn

```DAX
Latest Net Burn = VAR ScenarioID = SELECTEDVALUE(DimScenario[ScenarioID], "Base") RETURN CALCULATE(MAX(FactCashMonthly[NetBurn]), FactCashMonthly[ScenarioID] = ScenarioID, DimDate[IsLatestCompleteMonth] = 1)
```

Format: `$#,0;($#,0);$0`

## Runway Months

```DAX
Runway Months = VAR ScenarioID = SELECTEDVALUE(DimScenario[ScenarioID], "Base") RETURN CALCULATE(MAX(FactCashMonthly[RunwayMonths]), FactCashMonthly[ScenarioID] = ScenarioID)
```

Format: `0.0x`

## Latest Runway Months

```DAX
Latest Runway Months = VAR ScenarioID = SELECTEDVALUE(DimScenario[ScenarioID], "Base") RETURN CALCULATE(MAX(FactCashMonthly[RunwayMonths]), FactCashMonthly[ScenarioID] = ScenarioID, DimDate[IsLatestCompleteMonth] = 1)
```

Format: `0.0x`

## Funding Need

```DAX
Funding Need = VAR ScenarioID = SELECTEDVALUE(DimScenario[ScenarioID], "Base") RETURN CALCULATE(MAX(FactCashMonthly[FundingNeed]), FactCashMonthly[ScenarioID] = ScenarioID)
```

Format: `$#,0;($#,0);$0`

## Latest Funding Need

```DAX
Latest Funding Need = VAR ScenarioID = SELECTEDVALUE(DimScenario[ScenarioID], "Base") RETURN CALCULATE(MAX(FactCashMonthly[FundingNeed]), FactCashMonthly[ScenarioID] = ScenarioID, DimDate[IsLatestCompleteMonth] = 1)
```

Format: `$#,0;($#,0);$0`

## Statement Actual

```DAX
Statement Actual = VAR ScenarioID = SELECTEDVALUE(DimScenario[ScenarioID], "Base") RETURN CALCULATE(SUM(FactStatementLines[ValueActual]), FactStatementLines[ScenarioID] = ScenarioID)
```

Format: `$#,0;($#,0);$0`

## Statement Plan

```DAX
Statement Plan = VAR ScenarioID = SELECTEDVALUE(DimScenario[ScenarioID], "Base") RETURN CALCULATE(SUM(FactStatementLines[ValuePlan]), FactStatementLines[ScenarioID] = ScenarioID)
```

Format: `$#,0;($#,0);$0`

## Statement Forecast

```DAX
Statement Forecast = VAR ScenarioID = SELECTEDVALUE(DimScenario[ScenarioID], "Base") RETURN CALCULATE(SUM(FactStatementLines[ValueForecast]), FactStatementLines[ScenarioID] = ScenarioID)
```

Format: `$#,0;($#,0);$0`

## Statement Variance %

```DAX
Statement Variance % = DIVIDE([Statement Actual] - [Statement Plan], [Statement Plan])
```

Format: `0.0%`

## Enterprise Value

```DAX
Enterprise Value = VAR ScenarioID = SELECTEDVALUE(DimScenario[ScenarioID], "Base") RETURN CALCULATE(AVERAGE(FactValuation[EnterpriseValue]), FactValuation[ScenarioID] = ScenarioID)
```

Format: `$#,0;($#,0);$0`

## Equity Value

```DAX
Equity Value = VAR ScenarioID = SELECTEDVALUE(DimScenario[ScenarioID], "Base") RETURN CALCULATE(AVERAGE(FactValuation[EquityValue]), FactValuation[ScenarioID] = ScenarioID)
```

Format: `$#,0;($#,0);$0`

## Valuation Low

```DAX
Valuation Low = VAR ScenarioID = SELECTEDVALUE(DimScenario[ScenarioID], "Base") RETURN CALCULATE(AVERAGE(FactValuation[LowValue]), FactValuation[ScenarioID] = ScenarioID)
```

Format: `$#,0;($#,0);$0`

## Valuation High

```DAX
Valuation High = VAR ScenarioID = SELECTEDVALUE(DimScenario[ScenarioID], "Base") RETURN CALCULATE(AVERAGE(FactValuation[HighValue]), FactValuation[ScenarioID] = ScenarioID)
```

Format: `$#,0;($#,0);$0`

## Sensitivity Delta

```DAX
Sensitivity Delta = VAR ScenarioID = SELECTEDVALUE(DimScenario[ScenarioID], "Base") RETURN CALCULATE(SUM(FactSensitivity[EquityValueDelta]), FactSensitivity[ScenarioID] = ScenarioID)
```

Format: `$#,0;($#,0);$0`

## Leverage Ratio

```DAX
Leverage Ratio = VAR ScenarioID = SELECTEDVALUE(DimScenario[ScenarioID], "Base") RETURN CALCULATE(MAX(FactCovenantMonthly[LeverageRatio]), FactCovenantMonthly[ScenarioID] = ScenarioID, DimDate[IsLatestCompleteMonth] = 1)
```

Format: `0.0x`

## Leverage Limit

```DAX
Leverage Limit = VAR ScenarioID = SELECTEDVALUE(DimScenario[ScenarioID], "Base") RETURN CALCULATE(MAX(FactCovenantMonthly[LeverageLimit]), FactCovenantMonthly[ScenarioID] = ScenarioID)
```

Format: `0.0x`

## Leverage Headroom

```DAX
Leverage Headroom = VAR ScenarioID = SELECTEDVALUE(DimScenario[ScenarioID], "Base") RETURN CALCULATE(MAX(FactCovenantMonthly[LeverageHeadroom]), FactCovenantMonthly[ScenarioID] = ScenarioID, DimDate[IsLatestCompleteMonth] = 1)
```

Format: `0.0x`

## Interest Coverage

```DAX
Interest Coverage = VAR ScenarioID = SELECTEDVALUE(DimScenario[ScenarioID], "Base") RETURN CALCULATE(MAX(FactCovenantMonthly[InterestCoverage]), FactCovenantMonthly[ScenarioID] = ScenarioID, DimDate[IsLatestCompleteMonth] = 1)
```

Format: `0.0x`

## Liquidity Headroom

```DAX
Liquidity Headroom = VAR ScenarioID = SELECTEDVALUE(DimScenario[ScenarioID], "Base") RETURN CALCULATE(MAX(FactCovenantMonthly[LiquidityHeadroom]), FactCovenantMonthly[ScenarioID] = ScenarioID, DimDate[IsLatestCompleteMonth] = 1)
```

Format: `$#,0;($#,0);$0`

## Risk Exposure

```DAX
Risk Exposure = VAR ScenarioID = SELECTEDVALUE(DimScenario[ScenarioID], "Base") RETURN CALCULATE(SUM(FactRiskRegister[ExposureUSD]), FactRiskRegister[ScenarioID] = ScenarioID)
```

Format: `$#,0;($#,0);$0`

## Critical Risk Count

```DAX
Critical Risk Count = VAR ScenarioID = SELECTEDVALUE(DimScenario[ScenarioID], "Base") RETURN CALCULATE(COUNTROWS(FactRiskRegister), FactRiskRegister[ScenarioID] = ScenarioID, FactRiskRegister[Severity] = "Critical")
```

Format: `#,0`

## Revenue Sparkline SVG

```DAX
Revenue Sparkline SVG = VAR LatestMonth = CALCULATE(MAX(DimDate[MonthStart]), ALL(DimDate), DimDate[IsLatestCompleteMonth] = 1)
VAR MonthTable =
    ADDCOLUMNS(
        FILTER(ALLSELECTED(DimDate), DimDate[MonthStart] <= LatestMonth),
        "__Value", [Revenue]
    )
VAR CleanTable = FILTER(MonthTable, NOT ISBLANK([__Value]))
VAR RowCount = COUNTROWS(CleanTable)
VAR MinValue = MINX(CleanTable, [__Value])
VAR MaxValue = MAXX(CleanTable, [__Value])
VAR Points =
    CONCATENATEX(
        CleanTable,
        VAR RankValue = RANKX(CleanTable, DimDate[MonthStart], , ASC, DENSE) - 1
        VAR XValue = 2 + DIVIDE(RankValue, MAX(1, RowCount - 1), 0) * 116
        VAR YValue = 38 - DIVIDE([__Value] - MinValue, MaxValue - MinValue, 0.5) * 32
        RETURN FORMAT(XValue, "0.0") & "," & FORMAT(YValue, "0.0"),
        " ",
        DimDate[MonthStart],
        ASC
    )
RETURN
    "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 120 44'><rect x='0' y='0' width='120' height='44' rx='7' fill='%23D8CDEE'/><polyline points='" & Points & "' fill='none' stroke='%234F87F5' stroke-width='3' stroke-linecap='round' stroke-linejoin='round'/><circle cx='114' cy='10' r='3.2' fill='%23111827'/></svg>"
```

Format: `text/image`

## Gross Margin Sparkline SVG

```DAX
Gross Margin Sparkline SVG = VAR LatestMonth = CALCULATE(MAX(DimDate[MonthStart]), ALL(DimDate), DimDate[IsLatestCompleteMonth] = 1)
VAR MonthTable =
    ADDCOLUMNS(
        FILTER(ALLSELECTED(DimDate), DimDate[MonthStart] <= LatestMonth),
        "__Value", [Gross Margin %]
    )
VAR CleanTable = FILTER(MonthTable, NOT ISBLANK([__Value]))
VAR RowCount = COUNTROWS(CleanTable)
VAR MinValue = MINX(CleanTable, [__Value])
VAR MaxValue = MAXX(CleanTable, [__Value])
VAR Points =
    CONCATENATEX(
        CleanTable,
        VAR RankValue = RANKX(CleanTable, DimDate[MonthStart], , ASC, DENSE) - 1
        VAR XValue = 2 + DIVIDE(RankValue, MAX(1, RowCount - 1), 0) * 116
        VAR YValue = 38 - DIVIDE([__Value] - MinValue, MaxValue - MinValue, 0.5) * 32
        RETURN FORMAT(XValue, "0.0") & "," & FORMAT(YValue, "0.0"),
        " ",
        DimDate[MonthStart],
        ASC
    )
RETURN
    "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 120 44'><rect x='0' y='0' width='120' height='44' rx='7' fill='%23D8CDEE'/><polyline points='" & Points & "' fill='none' stroke='%230F9F95' stroke-width='3' stroke-linecap='round' stroke-linejoin='round'/><circle cx='114' cy='10' r='3.2' fill='%23111827'/></svg>"
```

Format: `text/image`

## EBITDA Sparkline SVG

```DAX
EBITDA Sparkline SVG = VAR LatestMonth = CALCULATE(MAX(DimDate[MonthStart]), ALL(DimDate), DimDate[IsLatestCompleteMonth] = 1)
VAR MonthTable =
    ADDCOLUMNS(
        FILTER(ALLSELECTED(DimDate), DimDate[MonthStart] <= LatestMonth),
        "__Value", [EBITDA]
    )
VAR CleanTable = FILTER(MonthTable, NOT ISBLANK([__Value]))
VAR RowCount = COUNTROWS(CleanTable)
VAR MinValue = MINX(CleanTable, [__Value])
VAR MaxValue = MAXX(CleanTable, [__Value])
VAR Points =
    CONCATENATEX(
        CleanTable,
        VAR RankValue = RANKX(CleanTable, DimDate[MonthStart], , ASC, DENSE) - 1
        VAR XValue = 2 + DIVIDE(RankValue, MAX(1, RowCount - 1), 0) * 116
        VAR YValue = 38 - DIVIDE([__Value] - MinValue, MaxValue - MinValue, 0.5) * 32
        RETURN FORMAT(XValue, "0.0") & "," & FORMAT(YValue, "0.0"),
        " ",
        DimDate[MonthStart],
        ASC
    )
RETURN
    "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 120 44'><rect x='0' y='0' width='120' height='44' rx='7' fill='%23D8CDEE'/><polyline points='" & Points & "' fill='none' stroke='%231F8E45' stroke-width='3' stroke-linecap='round' stroke-linejoin='round'/><circle cx='114' cy='10' r='3.2' fill='%23111827'/></svg>"
```

Format: `text/image`

## Cash Sparkline SVG

```DAX
Cash Sparkline SVG = VAR LatestMonth = CALCULATE(MAX(DimDate[MonthStart]), ALL(DimDate), DimDate[IsLatestCompleteMonth] = 1)
VAR MonthTable =
    ADDCOLUMNS(
        FILTER(ALLSELECTED(DimDate), DimDate[MonthStart] <= LatestMonth),
        "__Value", [Cash Balance]
    )
VAR CleanTable = FILTER(MonthTable, NOT ISBLANK([__Value]))
VAR RowCount = COUNTROWS(CleanTable)
VAR MinValue = MINX(CleanTable, [__Value])
VAR MaxValue = MAXX(CleanTable, [__Value])
VAR Points =
    CONCATENATEX(
        CleanTable,
        VAR RankValue = RANKX(CleanTable, DimDate[MonthStart], , ASC, DENSE) - 1
        VAR XValue = 2 + DIVIDE(RankValue, MAX(1, RowCount - 1), 0) * 116
        VAR YValue = 38 - DIVIDE([__Value] - MinValue, MaxValue - MinValue, 0.5) * 32
        RETURN FORMAT(XValue, "0.0") & "," & FORMAT(YValue, "0.0"),
        " ",
        DimDate[MonthStart],
        ASC
    )
RETURN
    "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 120 44'><rect x='0' y='0' width='120' height='44' rx='7' fill='%23D8CDEE'/><polyline points='" & Points & "' fill='none' stroke='%23BE7C10' stroke-width='3' stroke-linecap='round' stroke-linejoin='round'/><circle cx='114' cy='10' r='3.2' fill='%23111827'/></svg>"
```

Format: `text/image`

## Runway Sparkline SVG

```DAX
Runway Sparkline SVG = VAR LatestMonth = CALCULATE(MAX(DimDate[MonthStart]), ALL(DimDate), DimDate[IsLatestCompleteMonth] = 1)
VAR MonthTable =
    ADDCOLUMNS(
        FILTER(ALLSELECTED(DimDate), DimDate[MonthStart] <= LatestMonth),
        "__Value", [Runway Months]
    )
VAR CleanTable = FILTER(MonthTable, NOT ISBLANK([__Value]))
VAR RowCount = COUNTROWS(CleanTable)
VAR MinValue = MINX(CleanTable, [__Value])
VAR MaxValue = MAXX(CleanTable, [__Value])
VAR Points =
    CONCATENATEX(
        CleanTable,
        VAR RankValue = RANKX(CleanTable, DimDate[MonthStart], , ASC, DENSE) - 1
        VAR XValue = 2 + DIVIDE(RankValue, MAX(1, RowCount - 1), 0) * 116
        VAR YValue = 38 - DIVIDE([__Value] - MinValue, MaxValue - MinValue, 0.5) * 32
        RETURN FORMAT(XValue, "0.0") & "," & FORMAT(YValue, "0.0"),
        " ",
        DimDate[MonthStart],
        ASC
    )
RETURN
    "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 120 44'><rect x='0' y='0' width='120' height='44' rx='7' fill='%23D8CDEE'/><polyline points='" & Points & "' fill='none' stroke='%23B73535' stroke-width='3' stroke-linecap='round' stroke-linejoin='round'/><circle cx='114' cy='10' r='3.2' fill='%23111827'/></svg>"
```

Format: `text/image`

## Board Status Icon

```DAX
Board Status Icon = SWITCH(TRUE(), [Revenue vs Plan %] >= 0.03, UNICHAR(9650), [Revenue vs Plan %] >= -0.02, UNICHAR(8212), UNICHAR(9660))
```

Format: `text/image`

## Board Status Color

```DAX
Board Status Color = SWITCH(TRUE(), [Revenue vs Plan %] >= 0.03, "#2FA66A", [Revenue vs Plan %] >= -0.02, "#C58A18", "#C94A4A")
```

Format: `text/image`
