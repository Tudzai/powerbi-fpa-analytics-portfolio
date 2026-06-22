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
Latest Revenue = VAR LatestMonth = MAXX(CALCULATETABLE(VALUES(DimDate[MonthStart]), ALLSELECTED(DimDate), REMOVEFILTERS(DimDate[IsLatestCompleteMonth])), DimDate[MonthStart]) RETURN CALCULATE([Revenue], FILTER(ALL(DimDate), DimDate[MonthStart] = LatestMonth))
```

Format: `$#,0;($#,0);$0`

## Latest Gross Margin %

```DAX
Latest Gross Margin % = VAR LatestMonth = MAXX(CALCULATETABLE(VALUES(DimDate[MonthStart]), ALLSELECTED(DimDate), REMOVEFILTERS(DimDate[IsLatestCompleteMonth])), DimDate[MonthStart]) RETURN CALCULATE([Gross Margin %], FILTER(ALL(DimDate), DimDate[MonthStart] = LatestMonth))
```

Format: `0.0%`

## Latest EBITDA

```DAX
Latest EBITDA = VAR LatestMonth = MAXX(CALCULATETABLE(VALUES(DimDate[MonthStart]), ALLSELECTED(DimDate), REMOVEFILTERS(DimDate[IsLatestCompleteMonth])), DimDate[MonthStart]) RETURN CALCULATE([EBITDA], FILTER(ALL(DimDate), DimDate[MonthStart] = LatestMonth))
```

Format: `$#,0;($#,0);$0`

## Latest EBITDA Margin %

```DAX
Latest EBITDA Margin % = VAR LatestMonth = MAXX(CALCULATETABLE(VALUES(DimDate[MonthStart]), ALLSELECTED(DimDate), REMOVEFILTERS(DimDate[IsLatestCompleteMonth])), DimDate[MonthStart]) RETURN CALCULATE([EBITDA Margin %], FILTER(ALL(DimDate), DimDate[MonthStart] = LatestMonth))
```

Format: `0.0%`

## Latest Cash Balance

```DAX
Latest Cash Balance = VAR ScenarioID = SELECTEDVALUE(DimScenario[ScenarioID], "Base") VAR LatestMonth = MAXX(CALCULATETABLE(VALUES(DimDate[MonthStart]), ALLSELECTED(DimDate), REMOVEFILTERS(DimDate[IsLatestCompleteMonth])), DimDate[MonthStart]) RETURN CALCULATE(MAX(FactCashMonthly[CashBalance]), FactCashMonthly[ScenarioID] = ScenarioID, FILTER(ALL(DimDate), DimDate[MonthStart] = LatestMonth))
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
Latest Free Cash Flow = VAR ScenarioID = SELECTEDVALUE(DimScenario[ScenarioID], "Base") VAR LatestMonth = MAXX(CALCULATETABLE(VALUES(DimDate[MonthStart]), ALLSELECTED(DimDate), REMOVEFILTERS(DimDate[IsLatestCompleteMonth])), DimDate[MonthStart]) RETURN CALCULATE(MAX(FactCashMonthly[FreeCashFlow]), FactCashMonthly[ScenarioID] = ScenarioID, FILTER(ALL(DimDate), DimDate[MonthStart] = LatestMonth))
```

Format: `$#,0;($#,0);$0`

## Net Burn

```DAX
Net Burn = VAR ScenarioID = SELECTEDVALUE(DimScenario[ScenarioID], "Base") RETURN CALCULATE(MAX(FactCashMonthly[NetBurn]), FactCashMonthly[ScenarioID] = ScenarioID)
```

Format: `$#,0;($#,0);$0`

## Latest Net Burn

```DAX
Latest Net Burn = VAR ScenarioID = SELECTEDVALUE(DimScenario[ScenarioID], "Base") VAR LatestMonth = MAXX(CALCULATETABLE(VALUES(DimDate[MonthStart]), ALLSELECTED(DimDate), REMOVEFILTERS(DimDate[IsLatestCompleteMonth])), DimDate[MonthStart]) RETURN CALCULATE(MAX(FactCashMonthly[NetBurn]), FactCashMonthly[ScenarioID] = ScenarioID, FILTER(ALL(DimDate), DimDate[MonthStart] = LatestMonth))
```

Format: `$#,0;($#,0);$0`

## Runway Months

```DAX
Runway Months = VAR ScenarioID = SELECTEDVALUE(DimScenario[ScenarioID], "Base") RETURN CALCULATE(MAX(FactCashMonthly[RunwayMonths]), FactCashMonthly[ScenarioID] = ScenarioID)
```

Format: `0.0x`

## Latest Runway Months

```DAX
Latest Runway Months = VAR ScenarioID = SELECTEDVALUE(DimScenario[ScenarioID], "Base") VAR LatestMonth = MAXX(CALCULATETABLE(VALUES(DimDate[MonthStart]), ALLSELECTED(DimDate), REMOVEFILTERS(DimDate[IsLatestCompleteMonth])), DimDate[MonthStart]) RETURN CALCULATE(MAX(FactCashMonthly[RunwayMonths]), FactCashMonthly[ScenarioID] = ScenarioID, FILTER(ALL(DimDate), DimDate[MonthStart] = LatestMonth))
```

Format: `0.0x`

## Funding Need

```DAX
Funding Need = VAR ScenarioID = SELECTEDVALUE(DimScenario[ScenarioID], "Base") RETURN CALCULATE(MAX(FactCashMonthly[FundingNeed]), FactCashMonthly[ScenarioID] = ScenarioID)
```

Format: `$#,0;($#,0);$0`

## Latest Funding Need

```DAX
Latest Funding Need = VAR ScenarioID = SELECTEDVALUE(DimScenario[ScenarioID], "Base") VAR LatestMonth = MAXX(CALCULATETABLE(VALUES(DimDate[MonthStart]), ALLSELECTED(DimDate), REMOVEFILTERS(DimDate[IsLatestCompleteMonth])), DimDate[MonthStart]) RETURN CALCULATE(MAX(FactCashMonthly[FundingNeed]), FactCashMonthly[ScenarioID] = ScenarioID, FILTER(ALL(DimDate), DimDate[MonthStart] = LatestMonth))
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
Leverage Ratio = VAR ScenarioID = SELECTEDVALUE(DimScenario[ScenarioID], "Base") VAR LatestMonth = MAXX(CALCULATETABLE(VALUES(DimDate[MonthStart]), ALLSELECTED(DimDate), REMOVEFILTERS(DimDate[IsLatestCompleteMonth])), DimDate[MonthStart]) RETURN CALCULATE(MAX(FactCovenantMonthly[LeverageRatio]), FactCovenantMonthly[ScenarioID] = ScenarioID, FILTER(ALL(DimDate), DimDate[MonthStart] = LatestMonth))
```

Format: `0.0x`

## Leverage Limit

```DAX
Leverage Limit = VAR ScenarioID = SELECTEDVALUE(DimScenario[ScenarioID], "Base") RETURN CALCULATE(MAX(FactCovenantMonthly[LeverageLimit]), FactCovenantMonthly[ScenarioID] = ScenarioID)
```

Format: `0.0x`

## Leverage Headroom

```DAX
Leverage Headroom = VAR ScenarioID = SELECTEDVALUE(DimScenario[ScenarioID], "Base") VAR LatestMonth = MAXX(CALCULATETABLE(VALUES(DimDate[MonthStart]), ALLSELECTED(DimDate), REMOVEFILTERS(DimDate[IsLatestCompleteMonth])), DimDate[MonthStart]) RETURN CALCULATE(MAX(FactCovenantMonthly[LeverageHeadroom]), FactCovenantMonthly[ScenarioID] = ScenarioID, FILTER(ALL(DimDate), DimDate[MonthStart] = LatestMonth))
```

Format: `0.0x`

## Interest Coverage

```DAX
Interest Coverage = VAR ScenarioID = SELECTEDVALUE(DimScenario[ScenarioID], "Base") VAR LatestMonth = MAXX(CALCULATETABLE(VALUES(DimDate[MonthStart]), ALLSELECTED(DimDate), REMOVEFILTERS(DimDate[IsLatestCompleteMonth])), DimDate[MonthStart]) RETURN CALCULATE(MAX(FactCovenantMonthly[InterestCoverage]), FactCovenantMonthly[ScenarioID] = ScenarioID, FILTER(ALL(DimDate), DimDate[MonthStart] = LatestMonth))
```

Format: `0.0x`

## Liquidity Headroom

```DAX
Liquidity Headroom = VAR ScenarioID = SELECTEDVALUE(DimScenario[ScenarioID], "Base") VAR LatestMonth = MAXX(CALCULATETABLE(VALUES(DimDate[MonthStart]), ALLSELECTED(DimDate), REMOVEFILTERS(DimDate[IsLatestCompleteMonth])), DimDate[MonthStart]) RETURN CALCULATE(MAX(FactCovenantMonthly[LiquidityHeadroom]), FactCovenantMonthly[ScenarioID] = ScenarioID, FILTER(ALL(DimDate), DimDate[MonthStart] = LatestMonth))
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

## Revenue Display

```DAX
Revenue Display = VAR Value = [Revenue] RETURN SWITCH(TRUE(), ABS(Value) >= 1000000000, FORMAT(DIVIDE(Value, 1000000000), "$#,0.0B;($#,0.0B);$0.0B"), ABS(Value) >= 1000000, FORMAT(DIVIDE(Value, 1000000), "$#,0M;($#,0M);$0M"), FORMAT(Value, "$#,0;($#,0);$0"))
```

Format: `text/image`

## Gross Margin % Display

```DAX
Gross Margin % Display = FORMAT([Gross Margin %], "0.0%")
```

Format: `text/image`

## EBITDA Display

```DAX
EBITDA Display = VAR Value = [EBITDA] RETURN SWITCH(TRUE(), ABS(Value) >= 1000000000, FORMAT(DIVIDE(Value, 1000000000), "$#,0.0B;($#,0.0B);$0.0B"), ABS(Value) >= 1000000, FORMAT(DIVIDE(Value, 1000000), "$#,0M;($#,0M);$0M"), FORMAT(Value, "$#,0;($#,0);$0"))
```

Format: `text/image`

## Cash Balance Display

```DAX
Cash Balance Display = VAR Value = [Cash Balance] RETURN SWITCH(TRUE(), ABS(Value) >= 1000000000, FORMAT(DIVIDE(Value, 1000000000), "$#,0.0B;($#,0.0B);$0.0B"), ABS(Value) >= 1000000, FORMAT(DIVIDE(Value, 1000000), "$#,0M;($#,0M);$0M"), FORMAT(Value, "$#,0;($#,0);$0"))
```

Format: `text/image`

## Runway Months Display

```DAX
Runway Months Display = FORMAT([Runway Months], "0.0x")
```

Format: `text/image`

## Free Cash Flow Display

```DAX
Free Cash Flow Display = VAR Value = [Free Cash Flow] RETURN SWITCH(TRUE(), ABS(Value) >= 1000000000, FORMAT(DIVIDE(Value, 1000000000), "$#,0.0B;($#,0.0B);$0.0B"), ABS(Value) >= 1000000, FORMAT(DIVIDE(Value, 1000000), "$#,0M;($#,0M);$0M"), FORMAT(Value, "$#,0;($#,0);$0"))
```

Format: `text/image`

## Net Burn Display

```DAX
Net Burn Display = VAR Value = [Net Burn] RETURN SWITCH(TRUE(), ABS(Value) >= 1000000000, FORMAT(DIVIDE(Value, 1000000000), "$#,0.0B;($#,0.0B);$0.0B"), ABS(Value) >= 1000000, FORMAT(DIVIDE(Value, 1000000), "$#,0M;($#,0M);$0M"), FORMAT(Value, "$#,0;($#,0);$0"))
```

Format: `text/image`

## Funding Need Display

```DAX
Funding Need Display = VAR Value = [Funding Need] RETURN SWITCH(TRUE(), ABS(Value) >= 1000000000, FORMAT(DIVIDE(Value, 1000000000), "$#,0.0B;($#,0.0B);$0.0B"), ABS(Value) >= 1000000, FORMAT(DIVIDE(Value, 1000000), "$#,0M;($#,0M);$0M"), FORMAT(Value, "$#,0;($#,0);$0"))
```

Format: `text/image`

## Enterprise Value Display

```DAX
Enterprise Value Display = VAR Value = [Enterprise Value] RETURN SWITCH(TRUE(), ABS(Value) >= 1000000000, FORMAT(DIVIDE(Value, 1000000000), "$#,0.0B;($#,0.0B);$0.0B"), ABS(Value) >= 1000000, FORMAT(DIVIDE(Value, 1000000), "$#,0M;($#,0M);$0M"), FORMAT(Value, "$#,0;($#,0);$0"))
```

Format: `text/image`

## Equity Value Display

```DAX
Equity Value Display = VAR Value = [Equity Value] RETURN SWITCH(TRUE(), ABS(Value) >= 1000000000, FORMAT(DIVIDE(Value, 1000000000), "$#,0.0B;($#,0.0B);$0.0B"), ABS(Value) >= 1000000, FORMAT(DIVIDE(Value, 1000000), "$#,0M;($#,0M);$0M"), FORMAT(Value, "$#,0;($#,0);$0"))
```

Format: `text/image`

## Leverage Ratio Display

```DAX
Leverage Ratio Display = FORMAT([Leverage Ratio], "0.0x")
```

Format: `text/image`

## Leverage Headroom Display

```DAX
Leverage Headroom Display = FORMAT([Leverage Headroom], "0.0x")
```

Format: `text/image`

## Risk Exposure Display

```DAX
Risk Exposure Display = VAR Value = [Risk Exposure] RETURN SWITCH(TRUE(), ABS(Value) >= 1000000000, FORMAT(DIVIDE(Value, 1000000000), "$#,0.0B;($#,0.0B);$0.0B"), ABS(Value) >= 1000000, FORMAT(DIVIDE(Value, 1000000), "$#,0M;($#,0M);$0M"), FORMAT(Value, "$#,0;($#,0);$0"))
```

Format: `text/image`

## Revenue KPI

```DAX
Revenue KPI = DIVIDE([Latest Revenue], 1000000)
```

Format: `$#,0.0M;($#,0.0M);$0.0M`

## Gross Margin KPI

```DAX
Gross Margin KPI = [Latest Gross Margin %]
```

Format: `0.0%`

## EBITDA KPI

```DAX
EBITDA KPI = DIVIDE([Latest EBITDA], 1000000)
```

Format: `$#,0.0M;($#,0.0M);$0.0M`

## Cash Balance KPI

```DAX
Cash Balance KPI = DIVIDE([Latest Cash Balance], 1000000)
```

Format: `$#,0.0M;($#,0.0M);$0.0M`

## Runway Months KPI

```DAX
Runway Months KPI = [Latest Runway Months]
```

Format: `0.0x`

## Free Cash Flow KPI

```DAX
Free Cash Flow KPI = DIVIDE([Latest Free Cash Flow], 1000000)
```

Format: `$#,0.0M;($#,0.0M);$0.0M`

## Net Burn KPI

```DAX
Net Burn KPI = DIVIDE([Latest Net Burn], 1000000)
```

Format: `$#,0M;($#,0M);$0M`

## Funding Need KPI

```DAX
Funding Need KPI = DIVIDE([Latest Funding Need], 1000000)
```

Format: `$#,0M;($#,0M);$0M`

## Enterprise Value KPI

```DAX
Enterprise Value KPI = DIVIDE([Enterprise Value], 1000000000)
```

Format: `$#,0.0B;($#,0.0B);$0.0B`

## Equity Value KPI

```DAX
Equity Value KPI = DIVIDE([Equity Value], 1000000000)
```

Format: `$#,0.0B;($#,0.0B);$0.0B`

## Leverage KPI

```DAX
Leverage KPI = [Leverage Ratio]
```

Format: `0.0x`

## Headroom KPI

```DAX
Headroom KPI = [Leverage Headroom]
```

Format: `0.0x`

## Risk Exposure KPI

```DAX
Risk Exposure KPI = DIVIDE([Risk Exposure], 1000000)
```

Format: `$#,0M;($#,0M);$0M`

## Revenue Sparkline SVG

```DAX
Revenue Sparkline SVG = VAR LatestMonth = MAXX(CALCULATETABLE(VALUES(DimDate[MonthStart]), ALLSELECTED(DimDate), REMOVEFILTERS(DimDate[IsLatestCompleteMonth])), DimDate[MonthStart])
VAR MonthTable =
    ADDCOLUMNS(
        FILTER(ALLSELECTED(DimDate), DimDate[MonthStart] <= LatestMonth),
        "__Value", [Revenue]
    )
VAR CleanTable = FILTER(MonthTable, NOT ISBLANK([__Value]))
VAR RowCount = COUNTROWS(CleanTable)
VAR MinValue = MINX(CleanTable, [__Value])
VAR MaxValue = MAXX(CleanTable, [__Value])
VAR FirstValue = MINX(TOPN(1, CleanTable, DimDate[MonthStart], ASC), [__Value])
VAR LastValue = MINX(TOPN(1, CleanTable, DimDate[MonthStart], DESC), [__Value])
VAR StartYValue = 37 - DIVIDE(FirstValue - MinValue, MaxValue - MinValue, 0.5) * 30
VAR EndYValue = 37 - DIVIDE(LastValue - MinValue, MaxValue - MinValue, 0.5) * 30
VAR TrendColor = IF(LastValue >= FirstValue, "%234F87F5", "%23C94A4A")
VAR Points =
    CONCATENATEX(
        CleanTable,
        VAR RankValue = RANKX(CleanTable, DimDate[MonthStart], , ASC, DENSE) - 1
        VAR XValue = 2 + DIVIDE(RankValue, MAX(1, RowCount - 1), 0) * 116
        VAR YValue = 37 - DIVIDE([__Value] - MinValue, MaxValue - MinValue, 0.5) * 30
        RETURN FORMAT(XValue, "0.0") & "," & FORMAT(YValue, "0.0"),
        " ",
        DimDate[MonthStart],
        ASC
    )
RETURN
    "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 120 44'><rect x='0' y='0' width='120' height='44' rx='7' fill='%23F3EFFA'/><rect x='0' y='16' width='120' height='12' rx='6' fill='%23DDEEDC'/><line x1='0' y1='22' x2='120' y2='22' stroke='%23B8AECF' stroke-width='1' stroke-dasharray='4 5'/><polyline points='" & Points & "' fill='none' stroke='" & TrendColor & "' stroke-width='3' stroke-linecap='round' stroke-linejoin='round'/><circle cx='2' cy='" & FORMAT(StartYValue, "0.0") & "' r='3' fill='%23FFFFFF' stroke='%238F7BAE' stroke-width='1.5'/><circle cx='118' cy='" & FORMAT(EndYValue, "0.0") & "' r='4' fill='" & TrendColor & "' stroke='%23FFFFFF' stroke-width='1.5'/></svg>"
```

Format: `text/image`

## Gross Margin Sparkline SVG

```DAX
Gross Margin Sparkline SVG = VAR LatestMonth = MAXX(CALCULATETABLE(VALUES(DimDate[MonthStart]), ALLSELECTED(DimDate), REMOVEFILTERS(DimDate[IsLatestCompleteMonth])), DimDate[MonthStart])
VAR MonthTable =
    ADDCOLUMNS(
        FILTER(ALLSELECTED(DimDate), DimDate[MonthStart] <= LatestMonth),
        "__Value", [Gross Margin %]
    )
VAR CleanTable = FILTER(MonthTable, NOT ISBLANK([__Value]))
VAR RowCount = COUNTROWS(CleanTable)
VAR MinValue = MINX(CleanTable, [__Value])
VAR MaxValue = MAXX(CleanTable, [__Value])
VAR FirstValue = MINX(TOPN(1, CleanTable, DimDate[MonthStart], ASC), [__Value])
VAR LastValue = MINX(TOPN(1, CleanTable, DimDate[MonthStart], DESC), [__Value])
VAR StartYValue = 37 - DIVIDE(FirstValue - MinValue, MaxValue - MinValue, 0.5) * 30
VAR EndYValue = 37 - DIVIDE(LastValue - MinValue, MaxValue - MinValue, 0.5) * 30
VAR TrendColor = IF(LastValue >= FirstValue, "%230F9F95", "%23C94A4A")
VAR Points =
    CONCATENATEX(
        CleanTable,
        VAR RankValue = RANKX(CleanTable, DimDate[MonthStart], , ASC, DENSE) - 1
        VAR XValue = 2 + DIVIDE(RankValue, MAX(1, RowCount - 1), 0) * 116
        VAR YValue = 37 - DIVIDE([__Value] - MinValue, MaxValue - MinValue, 0.5) * 30
        RETURN FORMAT(XValue, "0.0") & "," & FORMAT(YValue, "0.0"),
        " ",
        DimDate[MonthStart],
        ASC
    )
RETURN
    "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 120 44'><rect x='0' y='0' width='120' height='44' rx='7' fill='%23F3EFFA'/><rect x='0' y='16' width='120' height='12' rx='6' fill='%23DDEEDC'/><line x1='0' y1='22' x2='120' y2='22' stroke='%23B8AECF' stroke-width='1' stroke-dasharray='4 5'/><polyline points='" & Points & "' fill='none' stroke='" & TrendColor & "' stroke-width='3' stroke-linecap='round' stroke-linejoin='round'/><circle cx='2' cy='" & FORMAT(StartYValue, "0.0") & "' r='3' fill='%23FFFFFF' stroke='%238F7BAE' stroke-width='1.5'/><circle cx='118' cy='" & FORMAT(EndYValue, "0.0") & "' r='4' fill='" & TrendColor & "' stroke='%23FFFFFF' stroke-width='1.5'/></svg>"
```

Format: `text/image`

## EBITDA Sparkline SVG

```DAX
EBITDA Sparkline SVG = VAR LatestMonth = MAXX(CALCULATETABLE(VALUES(DimDate[MonthStart]), ALLSELECTED(DimDate), REMOVEFILTERS(DimDate[IsLatestCompleteMonth])), DimDate[MonthStart])
VAR MonthTable =
    ADDCOLUMNS(
        FILTER(ALLSELECTED(DimDate), DimDate[MonthStart] <= LatestMonth),
        "__Value", [EBITDA]
    )
VAR CleanTable = FILTER(MonthTable, NOT ISBLANK([__Value]))
VAR RowCount = COUNTROWS(CleanTable)
VAR MinValue = MINX(CleanTable, [__Value])
VAR MaxValue = MAXX(CleanTable, [__Value])
VAR FirstValue = MINX(TOPN(1, CleanTable, DimDate[MonthStart], ASC), [__Value])
VAR LastValue = MINX(TOPN(1, CleanTable, DimDate[MonthStart], DESC), [__Value])
VAR StartYValue = 37 - DIVIDE(FirstValue - MinValue, MaxValue - MinValue, 0.5) * 30
VAR EndYValue = 37 - DIVIDE(LastValue - MinValue, MaxValue - MinValue, 0.5) * 30
VAR TrendColor = IF(LastValue >= FirstValue, "%231F8E45", "%23C94A4A")
VAR Points =
    CONCATENATEX(
        CleanTable,
        VAR RankValue = RANKX(CleanTable, DimDate[MonthStart], , ASC, DENSE) - 1
        VAR XValue = 2 + DIVIDE(RankValue, MAX(1, RowCount - 1), 0) * 116
        VAR YValue = 37 - DIVIDE([__Value] - MinValue, MaxValue - MinValue, 0.5) * 30
        RETURN FORMAT(XValue, "0.0") & "," & FORMAT(YValue, "0.0"),
        " ",
        DimDate[MonthStart],
        ASC
    )
RETURN
    "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 120 44'><rect x='0' y='0' width='120' height='44' rx='7' fill='%23F3EFFA'/><rect x='0' y='16' width='120' height='12' rx='6' fill='%23DDEEDC'/><line x1='0' y1='22' x2='120' y2='22' stroke='%23B8AECF' stroke-width='1' stroke-dasharray='4 5'/><polyline points='" & Points & "' fill='none' stroke='" & TrendColor & "' stroke-width='3' stroke-linecap='round' stroke-linejoin='round'/><circle cx='2' cy='" & FORMAT(StartYValue, "0.0") & "' r='3' fill='%23FFFFFF' stroke='%238F7BAE' stroke-width='1.5'/><circle cx='118' cy='" & FORMAT(EndYValue, "0.0") & "' r='4' fill='" & TrendColor & "' stroke='%23FFFFFF' stroke-width='1.5'/></svg>"
```

Format: `text/image`

## Cash Sparkline SVG

```DAX
Cash Sparkline SVG = VAR LatestMonth = MAXX(CALCULATETABLE(VALUES(DimDate[MonthStart]), ALLSELECTED(DimDate), REMOVEFILTERS(DimDate[IsLatestCompleteMonth])), DimDate[MonthStart])
VAR MonthTable =
    ADDCOLUMNS(
        FILTER(ALLSELECTED(DimDate), DimDate[MonthStart] <= LatestMonth),
        "__Value", [Cash Balance]
    )
VAR CleanTable = FILTER(MonthTable, NOT ISBLANK([__Value]))
VAR RowCount = COUNTROWS(CleanTable)
VAR MinValue = MINX(CleanTable, [__Value])
VAR MaxValue = MAXX(CleanTable, [__Value])
VAR FirstValue = MINX(TOPN(1, CleanTable, DimDate[MonthStart], ASC), [__Value])
VAR LastValue = MINX(TOPN(1, CleanTable, DimDate[MonthStart], DESC), [__Value])
VAR StartYValue = 37 - DIVIDE(FirstValue - MinValue, MaxValue - MinValue, 0.5) * 30
VAR EndYValue = 37 - DIVIDE(LastValue - MinValue, MaxValue - MinValue, 0.5) * 30
VAR TrendColor = IF(LastValue >= FirstValue, "%23BE7C10", "%23C94A4A")
VAR Points =
    CONCATENATEX(
        CleanTable,
        VAR RankValue = RANKX(CleanTable, DimDate[MonthStart], , ASC, DENSE) - 1
        VAR XValue = 2 + DIVIDE(RankValue, MAX(1, RowCount - 1), 0) * 116
        VAR YValue = 37 - DIVIDE([__Value] - MinValue, MaxValue - MinValue, 0.5) * 30
        RETURN FORMAT(XValue, "0.0") & "," & FORMAT(YValue, "0.0"),
        " ",
        DimDate[MonthStart],
        ASC
    )
RETURN
    "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 120 44'><rect x='0' y='0' width='120' height='44' rx='7' fill='%23F3EFFA'/><rect x='0' y='16' width='120' height='12' rx='6' fill='%23DDEEDC'/><line x1='0' y1='22' x2='120' y2='22' stroke='%23B8AECF' stroke-width='1' stroke-dasharray='4 5'/><polyline points='" & Points & "' fill='none' stroke='" & TrendColor & "' stroke-width='3' stroke-linecap='round' stroke-linejoin='round'/><circle cx='2' cy='" & FORMAT(StartYValue, "0.0") & "' r='3' fill='%23FFFFFF' stroke='%238F7BAE' stroke-width='1.5'/><circle cx='118' cy='" & FORMAT(EndYValue, "0.0") & "' r='4' fill='" & TrendColor & "' stroke='%23FFFFFF' stroke-width='1.5'/></svg>"
```

Format: `text/image`

## Runway Sparkline SVG

```DAX
Runway Sparkline SVG = VAR LatestMonth = MAXX(CALCULATETABLE(VALUES(DimDate[MonthStart]), ALLSELECTED(DimDate), REMOVEFILTERS(DimDate[IsLatestCompleteMonth])), DimDate[MonthStart])
VAR MonthTable =
    ADDCOLUMNS(
        FILTER(ALLSELECTED(DimDate), DimDate[MonthStart] <= LatestMonth),
        "__Value", [Runway Months]
    )
VAR CleanTable = FILTER(MonthTable, NOT ISBLANK([__Value]))
VAR RowCount = COUNTROWS(CleanTable)
VAR MinValue = MINX(CleanTable, [__Value])
VAR MaxValue = MAXX(CleanTable, [__Value])
VAR FirstValue = MINX(TOPN(1, CleanTable, DimDate[MonthStart], ASC), [__Value])
VAR LastValue = MINX(TOPN(1, CleanTable, DimDate[MonthStart], DESC), [__Value])
VAR StartYValue = 37 - DIVIDE(FirstValue - MinValue, MaxValue - MinValue, 0.5) * 30
VAR EndYValue = 37 - DIVIDE(LastValue - MinValue, MaxValue - MinValue, 0.5) * 30
VAR TrendColor = IF(LastValue >= FirstValue, "%234F87F5", "%23C94A4A")
VAR Points =
    CONCATENATEX(
        CleanTable,
        VAR RankValue = RANKX(CleanTable, DimDate[MonthStart], , ASC, DENSE) - 1
        VAR XValue = 2 + DIVIDE(RankValue, MAX(1, RowCount - 1), 0) * 116
        VAR YValue = 37 - DIVIDE([__Value] - MinValue, MaxValue - MinValue, 0.5) * 30
        RETURN FORMAT(XValue, "0.0") & "," & FORMAT(YValue, "0.0"),
        " ",
        DimDate[MonthStart],
        ASC
    )
RETURN
    "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 120 44'><rect x='0' y='0' width='120' height='44' rx='7' fill='%23F3EFFA'/><rect x='0' y='16' width='120' height='12' rx='6' fill='%23DDEEDC'/><line x1='0' y1='22' x2='120' y2='22' stroke='%23B8AECF' stroke-width='1' stroke-dasharray='4 5'/><polyline points='" & Points & "' fill='none' stroke='" & TrendColor & "' stroke-width='3' stroke-linecap='round' stroke-linejoin='round'/><circle cx='2' cy='" & FORMAT(StartYValue, "0.0") & "' r='3' fill='%23FFFFFF' stroke='%238F7BAE' stroke-width='1.5'/><circle cx='118' cy='" & FORMAT(EndYValue, "0.0") & "' r='4' fill='" & TrendColor & "' stroke='%23FFFFFF' stroke-width='1.5'/></svg>"
```

Format: `text/image`

## Funding Sparkline SVG

```DAX
Funding Sparkline SVG = VAR LatestMonth = MAXX(CALCULATETABLE(VALUES(DimDate[MonthStart]), ALLSELECTED(DimDate), REMOVEFILTERS(DimDate[IsLatestCompleteMonth])), DimDate[MonthStart])
VAR MonthTable =
    ADDCOLUMNS(
        FILTER(ALLSELECTED(DimDate), DimDate[MonthStart] <= LatestMonth),
        "__Value", [Funding Need]
    )
VAR CleanTable = FILTER(MonthTable, NOT ISBLANK([__Value]))
VAR RowCount = COUNTROWS(CleanTable)
VAR MinValue = MINX(CleanTable, [__Value])
VAR MaxValue = MAXX(CleanTable, [__Value])
VAR FirstValue = MINX(TOPN(1, CleanTable, DimDate[MonthStart], ASC), [__Value])
VAR LastValue = MINX(TOPN(1, CleanTable, DimDate[MonthStart], DESC), [__Value])
VAR StartYValue = 37 - DIVIDE(FirstValue - MinValue, MaxValue - MinValue, 0.5) * 30
VAR EndYValue = 37 - DIVIDE(LastValue - MinValue, MaxValue - MinValue, 0.5) * 30
VAR TrendColor = IF(LastValue <= FirstValue, "%231F8E45", "%23C94A4A")
VAR Points =
    CONCATENATEX(
        CleanTable,
        VAR RankValue = RANKX(CleanTable, DimDate[MonthStart], , ASC, DENSE) - 1
        VAR XValue = 2 + DIVIDE(RankValue, MAX(1, RowCount - 1), 0) * 116
        VAR YValue = 37 - DIVIDE([__Value] - MinValue, MaxValue - MinValue, 0.5) * 30
        RETURN FORMAT(XValue, "0.0") & "," & FORMAT(YValue, "0.0"),
        " ",
        DimDate[MonthStart],
        ASC
    )
RETURN
    "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 120 44'><rect x='0' y='0' width='120' height='44' rx='7' fill='%23F3EFFA'/><rect x='0' y='16' width='120' height='12' rx='6' fill='%23DDEEDC'/><line x1='0' y1='22' x2='120' y2='22' stroke='%23B8AECF' stroke-width='1' stroke-dasharray='4 5'/><polyline points='" & Points & "' fill='none' stroke='" & TrendColor & "' stroke-width='3' stroke-linecap='round' stroke-linejoin='round'/><circle cx='2' cy='" & FORMAT(StartYValue, "0.0") & "' r='3' fill='%23FFFFFF' stroke='%238F7BAE' stroke-width='1.5'/><circle cx='118' cy='" & FORMAT(EndYValue, "0.0") & "' r='4' fill='" & TrendColor & "' stroke='%23FFFFFF' stroke-width='1.5'/></svg>"
```

Format: `text/image`

## Leverage Sparkline SVG

```DAX
Leverage Sparkline SVG = VAR LatestMonth = MAXX(CALCULATETABLE(VALUES(DimDate[MonthStart]), ALLSELECTED(DimDate), REMOVEFILTERS(DimDate[IsLatestCompleteMonth])), DimDate[MonthStart])
VAR MonthTable =
    ADDCOLUMNS(
        FILTER(ALLSELECTED(DimDate), DimDate[MonthStart] <= LatestMonth),
        "__Value", [Leverage Ratio]
    )
VAR CleanTable = FILTER(MonthTable, NOT ISBLANK([__Value]))
VAR RowCount = COUNTROWS(CleanTable)
VAR MinValue = MINX(CleanTable, [__Value])
VAR MaxValue = MAXX(CleanTable, [__Value])
VAR FirstValue = MINX(TOPN(1, CleanTable, DimDate[MonthStart], ASC), [__Value])
VAR LastValue = MINX(TOPN(1, CleanTable, DimDate[MonthStart], DESC), [__Value])
VAR StartYValue = 37 - DIVIDE(FirstValue - MinValue, MaxValue - MinValue, 0.5) * 30
VAR EndYValue = 37 - DIVIDE(LastValue - MinValue, MaxValue - MinValue, 0.5) * 30
VAR TrendColor = IF(LastValue <= FirstValue, "%231F8E45", "%23C94A4A")
VAR Points =
    CONCATENATEX(
        CleanTable,
        VAR RankValue = RANKX(CleanTable, DimDate[MonthStart], , ASC, DENSE) - 1
        VAR XValue = 2 + DIVIDE(RankValue, MAX(1, RowCount - 1), 0) * 116
        VAR YValue = 37 - DIVIDE([__Value] - MinValue, MaxValue - MinValue, 0.5) * 30
        RETURN FORMAT(XValue, "0.0") & "," & FORMAT(YValue, "0.0"),
        " ",
        DimDate[MonthStart],
        ASC
    )
RETURN
    "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 120 44'><rect x='0' y='0' width='120' height='44' rx='7' fill='%23F3EFFA'/><rect x='0' y='16' width='120' height='12' rx='6' fill='%23DDEEDC'/><line x1='0' y1='22' x2='120' y2='22' stroke='%23B8AECF' stroke-width='1' stroke-dasharray='4 5'/><polyline points='" & Points & "' fill='none' stroke='" & TrendColor & "' stroke-width='3' stroke-linecap='round' stroke-linejoin='round'/><circle cx='2' cy='" & FORMAT(StartYValue, "0.0") & "' r='3' fill='%23FFFFFF' stroke='%238F7BAE' stroke-width='1.5'/><circle cx='118' cy='" & FORMAT(EndYValue, "0.0") & "' r='4' fill='" & TrendColor & "' stroke='%23FFFFFF' stroke-width='1.5'/></svg>"
```

Format: `text/image`

## Interest Coverage Sparkline SVG

```DAX
Interest Coverage Sparkline SVG = VAR LatestMonth = MAXX(CALCULATETABLE(VALUES(DimDate[MonthStart]), ALLSELECTED(DimDate), REMOVEFILTERS(DimDate[IsLatestCompleteMonth])), DimDate[MonthStart])
VAR MonthTable =
    ADDCOLUMNS(
        FILTER(ALLSELECTED(DimDate), DimDate[MonthStart] <= LatestMonth),
        "__Value", [Interest Coverage]
    )
VAR CleanTable = FILTER(MonthTable, NOT ISBLANK([__Value]))
VAR RowCount = COUNTROWS(CleanTable)
VAR MinValue = MINX(CleanTable, [__Value])
VAR MaxValue = MAXX(CleanTable, [__Value])
VAR FirstValue = MINX(TOPN(1, CleanTable, DimDate[MonthStart], ASC), [__Value])
VAR LastValue = MINX(TOPN(1, CleanTable, DimDate[MonthStart], DESC), [__Value])
VAR StartYValue = 37 - DIVIDE(FirstValue - MinValue, MaxValue - MinValue, 0.5) * 30
VAR EndYValue = 37 - DIVIDE(LastValue - MinValue, MaxValue - MinValue, 0.5) * 30
VAR TrendColor = IF(LastValue >= FirstValue, "%231F8E45", "%23C94A4A")
VAR Points =
    CONCATENATEX(
        CleanTable,
        VAR RankValue = RANKX(CleanTable, DimDate[MonthStart], , ASC, DENSE) - 1
        VAR XValue = 2 + DIVIDE(RankValue, MAX(1, RowCount - 1), 0) * 116
        VAR YValue = 37 - DIVIDE([__Value] - MinValue, MaxValue - MinValue, 0.5) * 30
        RETURN FORMAT(XValue, "0.0") & "," & FORMAT(YValue, "0.0"),
        " ",
        DimDate[MonthStart],
        ASC
    )
RETURN
    "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 120 44'><rect x='0' y='0' width='120' height='44' rx='7' fill='%23F3EFFA'/><rect x='0' y='16' width='120' height='12' rx='6' fill='%23DDEEDC'/><line x1='0' y1='22' x2='120' y2='22' stroke='%23B8AECF' stroke-width='1' stroke-dasharray='4 5'/><polyline points='" & Points & "' fill='none' stroke='" & TrendColor & "' stroke-width='3' stroke-linecap='round' stroke-linejoin='round'/><circle cx='2' cy='" & FORMAT(StartYValue, "0.0") & "' r='3' fill='%23FFFFFF' stroke='%238F7BAE' stroke-width='1.5'/><circle cx='118' cy='" & FORMAT(EndYValue, "0.0") & "' r='4' fill='" & TrendColor & "' stroke='%23FFFFFF' stroke-width='1.5'/></svg>"
```

Format: `text/image`

## Statement Trend SVG

```DAX
Statement Trend SVG = VAR LatestMonth = MAXX(CALCULATETABLE(VALUES(DimDate[MonthStart]), ALLSELECTED(DimDate), REMOVEFILTERS(DimDate[IsLatestCompleteMonth])), DimDate[MonthStart])
VAR MonthTable =
    ADDCOLUMNS(
        FILTER(ALLSELECTED(DimDate), DimDate[MonthStart] <= LatestMonth),
        "__Value", [Statement Actual]
    )
VAR CleanTable = FILTER(MonthTable, NOT ISBLANK([__Value]))
VAR RowCount = COUNTROWS(CleanTable)
VAR MinValue = MINX(CleanTable, [__Value])
VAR MaxValue = MAXX(CleanTable, [__Value])
VAR FirstValue = MINX(TOPN(1, CleanTable, DimDate[MonthStart], ASC), [__Value])
VAR LastValue = MINX(TOPN(1, CleanTable, DimDate[MonthStart], DESC), [__Value])
VAR StartYValue = 37 - DIVIDE(FirstValue - MinValue, MaxValue - MinValue, 0.5) * 30
VAR EndYValue = 37 - DIVIDE(LastValue - MinValue, MaxValue - MinValue, 0.5) * 30
VAR TrendColor = IF(LastValue >= FirstValue, "%230F9F95", "%23C94A4A")
VAR Points =
    CONCATENATEX(
        CleanTable,
        VAR RankValue = RANKX(CleanTable, DimDate[MonthStart], , ASC, DENSE) - 1
        VAR XValue = 2 + DIVIDE(RankValue, MAX(1, RowCount - 1), 0) * 116
        VAR YValue = 37 - DIVIDE([__Value] - MinValue, MaxValue - MinValue, 0.5) * 30
        RETURN FORMAT(XValue, "0.0") & "," & FORMAT(YValue, "0.0"),
        " ",
        DimDate[MonthStart],
        ASC
    )
RETURN
    "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 120 44'><rect x='0' y='0' width='120' height='44' rx='7' fill='%23F3EFFA'/><rect x='0' y='16' width='120' height='12' rx='6' fill='%23DDEEDC'/><line x1='0' y1='22' x2='120' y2='22' stroke='%23B8AECF' stroke-width='1' stroke-dasharray='4 5'/><polyline points='" & Points & "' fill='none' stroke='" & TrendColor & "' stroke-width='3' stroke-linecap='round' stroke-linejoin='round'/><circle cx='2' cy='" & FORMAT(StartYValue, "0.0") & "' r='3' fill='%23FFFFFF' stroke='%238F7BAE' stroke-width='1.5'/><circle cx='118' cy='" & FORMAT(EndYValue, "0.0") & "' r='4' fill='" & TrendColor & "' stroke='%23FFFFFF' stroke-width='1.5'/></svg>"
```

Format: `text/image`

## Board KPI Trend SVG

```DAX
Board KPI Trend SVG = VAR MetricName = SELECTEDVALUE(FactKpiScorecard[MetricName])
RETURN
    SWITCH(
        TRUE(),
        MetricName = "Revenue", [Revenue Sparkline SVG],
        MetricName = "Gross Margin", [Gross Margin Sparkline SVG],
        MetricName = "EBITDA", [EBITDA Sparkline SVG],
        MetricName = "Cash Balance", [Cash Sparkline SVG],
        MetricName = "Runway", [Runway Sparkline SVG],
        MetricName = "Funding Need", [Funding Sparkline SVG],
        MetricName = "Leverage", [Leverage Sparkline SVG],
        MetricName = "Interest Coverage", [Interest Coverage Sparkline SVG],
        [Revenue Sparkline SVG]
    )
```

Format: `text/image`

## Risk Signal SVG

```DAX
Risk Signal SVG = VAR SeverityValue = SELECTEDVALUE(FactRiskRegister[Severity], "Watch")
VAR ProbabilityValue = MIN(0.98, MAX(0.02, MAX(FactRiskRegister[Probability])))
VAR MarkerX = 12 + ProbabilityValue * 96
VAR SeverityColor =
    SWITCH(
        SeverityValue,
        "Critical", "%23B73535",
        "High", "%23BE7C10",
        "%231F8E45"
    )
VAR SVG =
    "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 120 44'>" &
    "<rect x='0' y='0' width='120' height='44' rx='7' fill='%23F8F5FC'/>" &
    "<rect x='12' y='17' width='32' height='10' rx='5' fill='%23DDEEDC'/>" &
    "<rect x='44' y='17' width='32' height='10' rx='5' fill='%23FFF3D6'/>" &
    "<rect x='76' y='17' width='32' height='10' rx='5' fill='%23F3D7D7'/>" &
    "<line x1='12' y1='32' x2='108' y2='32' stroke='%23B8AECF' stroke-width='1' stroke-dasharray='3 4'/>" &
    "<circle cx='" & FORMAT(MarkerX, "0.0") & "' cy='22' r='6' fill='" & SeverityColor & "' stroke='%23FFFFFF' stroke-width='2'/>" &
    "<circle cx='" & FORMAT(MarkerX, "0.0") & "' cy='22' r='2' fill='%23FFFFFF'/>" &
    "</svg>"
RETURN "data:image/svg+xml;utf8," & SVG
```

Format: `text/image`

## Portfolio Signature SVG

```DAX
Portfolio Signature SVG = VAR SVG =
    "<svg xmlns='http://www.w3.org/2000/svg' width='64' height='64' viewBox='0 0 64 64'>" &
    "<defs>" &
    "<linearGradient id='bg' x1='7' y1='58' x2='57' y2='6' gradientUnits='userSpaceOnUse'>" &
    "<stop stop-color='%230A1323'/>" &
    "<stop offset='0.58' stop-color='%23101B2D'/>" &
    "<stop offset='1' stop-color='%2314303A'/>" &
    "</linearGradient>" &
    "<linearGradient id='accent' x1='12' y1='51' x2='52' y2='44' gradientUnits='userSpaceOnUse'>" &
    "<stop stop-color='%238AB8FF'/>" &
    "<stop offset='1' stop-color='%238DE1D6'/>" &
    "</linearGradient>" &
    "</defs>" &
    "<rect width='64' height='64' rx='14' fill='url(%23bg)'/>" &
    "<rect x='6' y='6' width='52' height='52' rx='11' fill='%23F8FBFF' opacity='0.025'/>" &
    "<rect x='6.5' y='6.5' width='51' height='51' rx='10.5' fill='none' stroke='%23F8FBFF' opacity='0.13' stroke-width='1.6'/>" &
    "<text x='8.5' y='43' fill='%23F8FBFF' font-family='Arial' font-size='31' font-weight='900'>AT</text>" &
    "<path d='M12 50C22 46.5 35 48 52 42.5' fill='none' stroke='url(%23accent)' stroke-width='2.8' stroke-linecap='round' opacity='0.88'/>" &
    "<circle cx='52' cy='42.5' r='2.85' fill='%23E9BF72'/>" &
    "</svg>"
RETURN "data:image/svg+xml;utf8," & SVG
```

Format: `text/image`

## Revenue KPI Card SVG

```DAX
Revenue KPI Card SVG = VAR LatestMonth = MAXX(CALCULATETABLE(VALUES(DimDate[MonthStart]), ALLSELECTED(DimDate), REMOVEFILTERS(DimDate[IsLatestCompleteMonth])), DimDate[MonthStart])
VAR PriorMonth = EDATE(LatestMonth, -12)
VAR CurrentValue = CALCULATE([Revenue], FILTER(ALL(DimDate), DimDate[MonthStart] = LatestMonth))
VAR PriorValue = CALCULATE([Revenue], FILTER(ALL(DimDate), DimDate[MonthStart] = PriorMonth))
VAR ChangeValue = CurrentValue - PriorValue
VAR ValueTextRaw = FORMAT(DIVIDE(CurrentValue, 1000000), "$#,0.0M;($#,0.0M);$0.0M")
VAR PYTextRaw = IF(ISBLANK(PriorValue), "n/a", FORMAT(DIVIDE(PriorValue, 1000000), "$#,0.0M;($#,0.0M);$0.0M"))
VAR RateValue = DIVIDE(ChangeValue, ABS(PriorValue))
VAR YoYTextRaw = IF(ISBLANK(CurrentValue) || ISBLANK(PriorValue), "n/a", FORMAT(RateValue, "+0.0%;-0.0%;0.0%"))
VAR ValueText = SUBSTITUTE(ValueTextRaw, "%", "%25")
VAR PYText = SUBSTITUTE(PYTextRaw, "%", "%25")
VAR YoYText = SUBSTITUTE(YoYTextRaw, "%", "%25")
VAR YoYColor = IF(ISBLANK(CurrentValue) || ISBLANK(PriorValue), "%236E667B", IF(ChangeValue >= 0, "%234CAF65", "%23C94A4A"))
VAR MonthTable =
    ADDCOLUMNS(
        FILTER(ALLSELECTED(DimDate), DimDate[MonthStart] <= LatestMonth),
        "__Value", [Revenue]
    )
VAR CleanTable = FILTER(MonthTable, NOT ISBLANK([__Value]))
VAR RowCount = COUNTROWS(CleanTable)
VAR MinValue = MINX(CleanTable, [__Value])
VAR MaxValue = MAXX(CleanTable, [__Value])
VAR FirstValue = MINX(TOPN(1, CleanTable, DimDate[MonthStart], ASC), [__Value])
VAR LastValue = MINX(TOPN(1, CleanTable, DimDate[MonthStart], DESC), [__Value])
VAR LowMonth = MINX(TOPN(1, CleanTable, [__Value], ASC, DimDate[MonthStart], ASC), DimDate[MonthStart])
VAR LowValue = MINX(FILTER(CleanTable, DimDate[MonthStart] = LowMonth), [__Value])
VAR StartYValue = 80 - DIVIDE(FirstValue - MinValue, MaxValue - MinValue, 0.5) * 42
VAR EndYValue = 80 - DIVIDE(LastValue - MinValue, MaxValue - MinValue, 0.5) * 42
VAR LowRank = RANKX(CleanTable, DimDate[MonthStart], LowMonth, ASC, DENSE) - 1
VAR LowXValue = 136 + DIVIDE(LowRank, MAX(1, RowCount - 1), 0) * 92
VAR LowYValue = 80 - DIVIDE(LowValue - MinValue, MaxValue - MinValue, 0.5) * 42
VAR TrendColor = IF(LastValue >= FirstValue, "%234F87F5", "%23C94A4A")
VAR BandColor = IF(LastValue >= FirstValue, "%23DDEEDC", "%23F3D7D7")
VAR LinePoints =
    CONCATENATEX(
        CleanTable,
        VAR RankValue = RANKX(CleanTable, DimDate[MonthStart], , ASC, DENSE) - 1
        VAR XValue = 136 + DIVIDE(RankValue, MAX(1, RowCount - 1), 0) * 92
        VAR YValue = 80 - DIVIDE([__Value] - MinValue, MaxValue - MinValue, 0.5) * 42
        RETURN FORMAT(XValue, "0.0") & "," & FORMAT(YValue, "0.0"),
        " ",
        DimDate[MonthStart],
        ASC
    )
VAR AreaPath =
    "M136 84 " &
    CONCATENATEX(
        CleanTable,
        VAR RankValue = RANKX(CleanTable, DimDate[MonthStart], , ASC, DENSE) - 1
        VAR XValue = 136 + DIVIDE(RankValue, MAX(1, RowCount - 1), 0) * 92
        VAR YValue = 80 - DIVIDE([__Value] - MinValue, MaxValue - MinValue, 0.5) * 42
        RETURN "L" & FORMAT(XValue, "0.0") & " " & FORMAT(YValue, "0.0"),
        " ",
        DimDate[MonthStart],
        ASC
    ) & " L228 84 Z"
VAR SVG =
    "<svg xmlns='http://www.w3.org/2000/svg' width='240' height='132' viewBox='0 0 248 140'>" &
    "<rect x='5' y='5' width='238' height='130' rx='14' fill='%23F4EFFA' stroke='%237142A4' stroke-width='2.5'/>" &
    "<rect x='18' y='13' width='212' height='4' rx='2' fill='%234F87F5' opacity='0.9'/>" &
    "<rect x='18' y='29' width='12' height='12' rx='3' fill='%234F87F5' opacity='0.95'/>" &
    "<circle cx='24' cy='35' r='2' fill='%23FFFFFF' opacity='0.85'/>" &
    "<text x='36' y='39' font-family='Segoe UI' font-size='14' font-weight='750' fill='%23211A32'>Revenue</text>" &
    "<text x='18' y='80' font-family='Segoe UI' font-size='27' font-weight='750' fill='%234F87F5'>" & ValueText & "</text>" &
    "<rect x='130' y='34' width='104' height='54' rx='8' fill='%23FFFFFF' opacity='0.46'/>" &
    "<rect x='136' y='59' width='92' height='12' rx='6' fill='" & BandColor & "'/>" &
    "<rect x='141' y='52' width='12' height='26' rx='2' fill='%23D9D1EB' opacity='0.34'/>" &
    "<rect x='160' y='48' width='12' height='30' rx='2' fill='%23D9D1EB' opacity='0.28'/>" &
    "<rect x='179' y='44' width='12' height='34' rx='2' fill='%23D9D1EB' opacity='0.24'/>" &
    "<rect x='198' y='40' width='12' height='38' rx='2' fill='%23D9D1EB' opacity='0.20'/>" &
    "<line x1='136' y1='65' x2='228' y2='65' stroke='%23B8AECF' stroke-width='1' stroke-dasharray='4 5'/>" &
    "<path d='" & AreaPath & "' fill='%23B8AEE6' opacity='0.55'/>" &
    "<polyline points='" & LinePoints & "' fill='none' stroke='" & TrendColor & "' stroke-width='3' stroke-linecap='round' stroke-linejoin='round'/>" &
    "<circle cx='136' cy='" & FORMAT(StartYValue, "0.0") & "' r='4' fill='%23FFFFFF' stroke='%2377A4F5' stroke-width='2'/>" &
    "<circle cx='" & FORMAT(LowXValue, "0.0") & "' cy='" & FORMAT(LowYValue, "0.0") & "' r='4' fill='%23D96A5D' stroke='%23FFFFFF' stroke-width='2'/>" &
    "<circle cx='228' cy='" & FORMAT(EndYValue, "0.0") & "' r='5' fill='" & TrendColor & "' stroke='%23FFFFFF' stroke-width='2'/>" &
    "<rect x='16' y='94' width='98' height='34' rx='8' fill='%23FFFFFF' opacity='0.64'/>" &
    "<rect x='122' y='94' width='110' height='34' rx='8' fill='%23FFFFFF' opacity='0.64'/>" &
    "<text x='24' y='108' font-family='Segoe UI' font-size='11' font-weight='750' fill='%23211A32'>PY</text>" &
    "<text x='24' y='123' font-family='Segoe UI' font-size='12' fill='%236E667B'>" & PYText & "</text>" &
    "<text x='132' y='108' font-family='Segoe UI' font-size='11' font-weight='750' fill='%23211A32'>YoY</text>" &
    "<polygon points='134,114 140,124 128,124' fill='" & YoYColor & "'/>" &
    "<text x='148' y='123' font-family='Segoe UI' font-size='12' font-weight='750' fill='" & YoYColor & "'>" & YoYText & "</text>" &
    "</svg>"
RETURN IF(RowCount = 0, BLANK(), "data:image/svg+xml;utf8," & SVG)
```

Format: `text/image`

## Margin KPI Card SVG

```DAX
Margin KPI Card SVG = VAR LatestMonth = MAXX(CALCULATETABLE(VALUES(DimDate[MonthStart]), ALLSELECTED(DimDate), REMOVEFILTERS(DimDate[IsLatestCompleteMonth])), DimDate[MonthStart])
VAR PriorMonth = EDATE(LatestMonth, -12)
VAR CurrentValue = CALCULATE([Gross Margin %], FILTER(ALL(DimDate), DimDate[MonthStart] = LatestMonth))
VAR PriorValue = CALCULATE([Gross Margin %], FILTER(ALL(DimDate), DimDate[MonthStart] = PriorMonth))
VAR ChangeValue = CurrentValue - PriorValue
VAR ValueTextRaw = FORMAT(DIVIDE(CurrentValue, 1), "0.0%")
VAR PYTextRaw = IF(ISBLANK(PriorValue), "n/a", FORMAT(DIVIDE(PriorValue, 1), "0.0%"))
VAR YoYTextRaw = IF(ISBLANK(CurrentValue) || ISBLANK(PriorValue), "n/a", FORMAT(ChangeValue * 100, "+0.0;-0.0;0.0") & "pt")
VAR ValueText = SUBSTITUTE(ValueTextRaw, "%", "%25")
VAR PYText = SUBSTITUTE(PYTextRaw, "%", "%25")
VAR YoYText = SUBSTITUTE(YoYTextRaw, "%", "%25")
VAR YoYColor = IF(ISBLANK(CurrentValue) || ISBLANK(PriorValue), "%236E667B", IF(ChangeValue >= 0, "%234CAF65", "%23C94A4A"))
VAR MonthTable =
    ADDCOLUMNS(
        FILTER(ALLSELECTED(DimDate), DimDate[MonthStart] <= LatestMonth),
        "__Value", [Gross Margin %]
    )
VAR CleanTable = FILTER(MonthTable, NOT ISBLANK([__Value]))
VAR RowCount = COUNTROWS(CleanTable)
VAR MinValue = MINX(CleanTable, [__Value])
VAR MaxValue = MAXX(CleanTable, [__Value])
VAR FirstValue = MINX(TOPN(1, CleanTable, DimDate[MonthStart], ASC), [__Value])
VAR LastValue = MINX(TOPN(1, CleanTable, DimDate[MonthStart], DESC), [__Value])
VAR LowMonth = MINX(TOPN(1, CleanTable, [__Value], ASC, DimDate[MonthStart], ASC), DimDate[MonthStart])
VAR LowValue = MINX(FILTER(CleanTable, DimDate[MonthStart] = LowMonth), [__Value])
VAR StartYValue = 80 - DIVIDE(FirstValue - MinValue, MaxValue - MinValue, 0.5) * 42
VAR EndYValue = 80 - DIVIDE(LastValue - MinValue, MaxValue - MinValue, 0.5) * 42
VAR LowRank = RANKX(CleanTable, DimDate[MonthStart], LowMonth, ASC, DENSE) - 1
VAR LowXValue = 136 + DIVIDE(LowRank, MAX(1, RowCount - 1), 0) * 92
VAR LowYValue = 80 - DIVIDE(LowValue - MinValue, MaxValue - MinValue, 0.5) * 42
VAR TrendColor = IF(LastValue >= FirstValue, "%230F9F95", "%23C94A4A")
VAR BandColor = IF(LastValue >= FirstValue, "%23DDEEDC", "%23F3D7D7")
VAR LinePoints =
    CONCATENATEX(
        CleanTable,
        VAR RankValue = RANKX(CleanTable, DimDate[MonthStart], , ASC, DENSE) - 1
        VAR XValue = 136 + DIVIDE(RankValue, MAX(1, RowCount - 1), 0) * 92
        VAR YValue = 80 - DIVIDE([__Value] - MinValue, MaxValue - MinValue, 0.5) * 42
        RETURN FORMAT(XValue, "0.0") & "," & FORMAT(YValue, "0.0"),
        " ",
        DimDate[MonthStart],
        ASC
    )
VAR AreaPath =
    "M136 84 " &
    CONCATENATEX(
        CleanTable,
        VAR RankValue = RANKX(CleanTable, DimDate[MonthStart], , ASC, DENSE) - 1
        VAR XValue = 136 + DIVIDE(RankValue, MAX(1, RowCount - 1), 0) * 92
        VAR YValue = 80 - DIVIDE([__Value] - MinValue, MaxValue - MinValue, 0.5) * 42
        RETURN "L" & FORMAT(XValue, "0.0") & " " & FORMAT(YValue, "0.0"),
        " ",
        DimDate[MonthStart],
        ASC
    ) & " L228 84 Z"
VAR SVG =
    "<svg xmlns='http://www.w3.org/2000/svg' width='240' height='132' viewBox='0 0 248 140'>" &
    "<rect x='5' y='5' width='238' height='130' rx='14' fill='%23F4EFFA' stroke='%237142A4' stroke-width='2.5'/>" &
    "<rect x='18' y='13' width='212' height='4' rx='2' fill='%230F9F95' opacity='0.9'/>" &
    "<rect x='18' y='29' width='12' height='12' rx='3' fill='%230F9F95' opacity='0.95'/>" &
    "<circle cx='24' cy='35' r='2' fill='%23FFFFFF' opacity='0.85'/>" &
    "<text x='36' y='39' font-family='Segoe UI' font-size='14' font-weight='750' fill='%23211A32'>Margin</text>" &
    "<text x='18' y='80' font-family='Segoe UI' font-size='27' font-weight='750' fill='%230F9F95'>" & ValueText & "</text>" &
    "<rect x='130' y='34' width='104' height='54' rx='8' fill='%23FFFFFF' opacity='0.46'/>" &
    "<rect x='136' y='59' width='92' height='12' rx='6' fill='" & BandColor & "'/>" &
    "<rect x='141' y='52' width='12' height='26' rx='2' fill='%23D9D1EB' opacity='0.34'/>" &
    "<rect x='160' y='48' width='12' height='30' rx='2' fill='%23D9D1EB' opacity='0.28'/>" &
    "<rect x='179' y='44' width='12' height='34' rx='2' fill='%23D9D1EB' opacity='0.24'/>" &
    "<rect x='198' y='40' width='12' height='38' rx='2' fill='%23D9D1EB' opacity='0.20'/>" &
    "<line x1='136' y1='65' x2='228' y2='65' stroke='%23B8AECF' stroke-width='1' stroke-dasharray='4 5'/>" &
    "<path d='" & AreaPath & "' fill='%23B8AEE6' opacity='0.55'/>" &
    "<polyline points='" & LinePoints & "' fill='none' stroke='" & TrendColor & "' stroke-width='3' stroke-linecap='round' stroke-linejoin='round'/>" &
    "<circle cx='136' cy='" & FORMAT(StartYValue, "0.0") & "' r='4' fill='%23FFFFFF' stroke='%2377A4F5' stroke-width='2'/>" &
    "<circle cx='" & FORMAT(LowXValue, "0.0") & "' cy='" & FORMAT(LowYValue, "0.0") & "' r='4' fill='%23D96A5D' stroke='%23FFFFFF' stroke-width='2'/>" &
    "<circle cx='228' cy='" & FORMAT(EndYValue, "0.0") & "' r='5' fill='" & TrendColor & "' stroke='%23FFFFFF' stroke-width='2'/>" &
    "<rect x='16' y='94' width='98' height='34' rx='8' fill='%23FFFFFF' opacity='0.64'/>" &
    "<rect x='122' y='94' width='110' height='34' rx='8' fill='%23FFFFFF' opacity='0.64'/>" &
    "<text x='24' y='108' font-family='Segoe UI' font-size='11' font-weight='750' fill='%23211A32'>PY</text>" &
    "<text x='24' y='123' font-family='Segoe UI' font-size='12' fill='%236E667B'>" & PYText & "</text>" &
    "<text x='132' y='108' font-family='Segoe UI' font-size='11' font-weight='750' fill='%23211A32'>YoY</text>" &
    "<polygon points='134,114 140,124 128,124' fill='" & YoYColor & "'/>" &
    "<text x='148' y='123' font-family='Segoe UI' font-size='12' font-weight='750' fill='" & YoYColor & "'>" & YoYText & "</text>" &
    "</svg>"
RETURN IF(RowCount = 0, BLANK(), "data:image/svg+xml;utf8," & SVG)
```

Format: `text/image`

## EBITDA KPI Card SVG

```DAX
EBITDA KPI Card SVG = VAR LatestMonth = MAXX(CALCULATETABLE(VALUES(DimDate[MonthStart]), ALLSELECTED(DimDate), REMOVEFILTERS(DimDate[IsLatestCompleteMonth])), DimDate[MonthStart])
VAR PriorMonth = EDATE(LatestMonth, -12)
VAR CurrentValue = CALCULATE([EBITDA], FILTER(ALL(DimDate), DimDate[MonthStart] = LatestMonth))
VAR PriorValue = CALCULATE([EBITDA], FILTER(ALL(DimDate), DimDate[MonthStart] = PriorMonth))
VAR ChangeValue = CurrentValue - PriorValue
VAR ValueTextRaw = FORMAT(DIVIDE(CurrentValue, 1000000), "$#,0.0M;($#,0.0M);$0.0M")
VAR PYTextRaw = IF(ISBLANK(PriorValue), "n/a", FORMAT(DIVIDE(PriorValue, 1000000), "$#,0.0M;($#,0.0M);$0.0M"))
VAR RateValue = DIVIDE(ChangeValue, ABS(PriorValue))
VAR YoYTextRaw = IF(ISBLANK(CurrentValue) || ISBLANK(PriorValue), "n/a", FORMAT(RateValue, "+0.0%;-0.0%;0.0%"))
VAR ValueText = SUBSTITUTE(ValueTextRaw, "%", "%25")
VAR PYText = SUBSTITUTE(PYTextRaw, "%", "%25")
VAR YoYText = SUBSTITUTE(YoYTextRaw, "%", "%25")
VAR YoYColor = IF(ISBLANK(CurrentValue) || ISBLANK(PriorValue), "%236E667B", IF(ChangeValue >= 0, "%234CAF65", "%23C94A4A"))
VAR MonthTable =
    ADDCOLUMNS(
        FILTER(ALLSELECTED(DimDate), DimDate[MonthStart] <= LatestMonth),
        "__Value", [EBITDA]
    )
VAR CleanTable = FILTER(MonthTable, NOT ISBLANK([__Value]))
VAR RowCount = COUNTROWS(CleanTable)
VAR MinValue = MINX(CleanTable, [__Value])
VAR MaxValue = MAXX(CleanTable, [__Value])
VAR FirstValue = MINX(TOPN(1, CleanTable, DimDate[MonthStart], ASC), [__Value])
VAR LastValue = MINX(TOPN(1, CleanTable, DimDate[MonthStart], DESC), [__Value])
VAR LowMonth = MINX(TOPN(1, CleanTable, [__Value], ASC, DimDate[MonthStart], ASC), DimDate[MonthStart])
VAR LowValue = MINX(FILTER(CleanTable, DimDate[MonthStart] = LowMonth), [__Value])
VAR StartYValue = 80 - DIVIDE(FirstValue - MinValue, MaxValue - MinValue, 0.5) * 42
VAR EndYValue = 80 - DIVIDE(LastValue - MinValue, MaxValue - MinValue, 0.5) * 42
VAR LowRank = RANKX(CleanTable, DimDate[MonthStart], LowMonth, ASC, DENSE) - 1
VAR LowXValue = 136 + DIVIDE(LowRank, MAX(1, RowCount - 1), 0) * 92
VAR LowYValue = 80 - DIVIDE(LowValue - MinValue, MaxValue - MinValue, 0.5) * 42
VAR TrendColor = IF(LastValue >= FirstValue, "%231F8E45", "%23C94A4A")
VAR BandColor = IF(LastValue >= FirstValue, "%23DDEEDC", "%23F3D7D7")
VAR LinePoints =
    CONCATENATEX(
        CleanTable,
        VAR RankValue = RANKX(CleanTable, DimDate[MonthStart], , ASC, DENSE) - 1
        VAR XValue = 136 + DIVIDE(RankValue, MAX(1, RowCount - 1), 0) * 92
        VAR YValue = 80 - DIVIDE([__Value] - MinValue, MaxValue - MinValue, 0.5) * 42
        RETURN FORMAT(XValue, "0.0") & "," & FORMAT(YValue, "0.0"),
        " ",
        DimDate[MonthStart],
        ASC
    )
VAR AreaPath =
    "M136 84 " &
    CONCATENATEX(
        CleanTable,
        VAR RankValue = RANKX(CleanTable, DimDate[MonthStart], , ASC, DENSE) - 1
        VAR XValue = 136 + DIVIDE(RankValue, MAX(1, RowCount - 1), 0) * 92
        VAR YValue = 80 - DIVIDE([__Value] - MinValue, MaxValue - MinValue, 0.5) * 42
        RETURN "L" & FORMAT(XValue, "0.0") & " " & FORMAT(YValue, "0.0"),
        " ",
        DimDate[MonthStart],
        ASC
    ) & " L228 84 Z"
VAR SVG =
    "<svg xmlns='http://www.w3.org/2000/svg' width='240' height='132' viewBox='0 0 248 140'>" &
    "<rect x='5' y='5' width='238' height='130' rx='14' fill='%23F4EFFA' stroke='%237142A4' stroke-width='2.5'/>" &
    "<rect x='18' y='13' width='212' height='4' rx='2' fill='%231F8E45' opacity='0.9'/>" &
    "<rect x='18' y='29' width='12' height='12' rx='3' fill='%231F8E45' opacity='0.95'/>" &
    "<circle cx='24' cy='35' r='2' fill='%23FFFFFF' opacity='0.85'/>" &
    "<text x='36' y='39' font-family='Segoe UI' font-size='14' font-weight='750' fill='%23211A32'>EBITDA</text>" &
    "<text x='18' y='80' font-family='Segoe UI' font-size='27' font-weight='750' fill='%231F8E45'>" & ValueText & "</text>" &
    "<rect x='130' y='34' width='104' height='54' rx='8' fill='%23FFFFFF' opacity='0.46'/>" &
    "<rect x='136' y='59' width='92' height='12' rx='6' fill='" & BandColor & "'/>" &
    "<rect x='141' y='52' width='12' height='26' rx='2' fill='%23D9D1EB' opacity='0.34'/>" &
    "<rect x='160' y='48' width='12' height='30' rx='2' fill='%23D9D1EB' opacity='0.28'/>" &
    "<rect x='179' y='44' width='12' height='34' rx='2' fill='%23D9D1EB' opacity='0.24'/>" &
    "<rect x='198' y='40' width='12' height='38' rx='2' fill='%23D9D1EB' opacity='0.20'/>" &
    "<line x1='136' y1='65' x2='228' y2='65' stroke='%23B8AECF' stroke-width='1' stroke-dasharray='4 5'/>" &
    "<path d='" & AreaPath & "' fill='%23B8AEE6' opacity='0.55'/>" &
    "<polyline points='" & LinePoints & "' fill='none' stroke='" & TrendColor & "' stroke-width='3' stroke-linecap='round' stroke-linejoin='round'/>" &
    "<circle cx='136' cy='" & FORMAT(StartYValue, "0.0") & "' r='4' fill='%23FFFFFF' stroke='%2377A4F5' stroke-width='2'/>" &
    "<circle cx='" & FORMAT(LowXValue, "0.0") & "' cy='" & FORMAT(LowYValue, "0.0") & "' r='4' fill='%23D96A5D' stroke='%23FFFFFF' stroke-width='2'/>" &
    "<circle cx='228' cy='" & FORMAT(EndYValue, "0.0") & "' r='5' fill='" & TrendColor & "' stroke='%23FFFFFF' stroke-width='2'/>" &
    "<rect x='16' y='94' width='98' height='34' rx='8' fill='%23FFFFFF' opacity='0.64'/>" &
    "<rect x='122' y='94' width='110' height='34' rx='8' fill='%23FFFFFF' opacity='0.64'/>" &
    "<text x='24' y='108' font-family='Segoe UI' font-size='11' font-weight='750' fill='%23211A32'>PY</text>" &
    "<text x='24' y='123' font-family='Segoe UI' font-size='12' fill='%236E667B'>" & PYText & "</text>" &
    "<text x='132' y='108' font-family='Segoe UI' font-size='11' font-weight='750' fill='%23211A32'>YoY</text>" &
    "<polygon points='134,114 140,124 128,124' fill='" & YoYColor & "'/>" &
    "<text x='148' y='123' font-family='Segoe UI' font-size='12' font-weight='750' fill='" & YoYColor & "'>" & YoYText & "</text>" &
    "</svg>"
RETURN IF(RowCount = 0, BLANK(), "data:image/svg+xml;utf8," & SVG)
```

Format: `text/image`

## Cash KPI Card SVG

```DAX
Cash KPI Card SVG = VAR LatestMonth = MAXX(CALCULATETABLE(VALUES(DimDate[MonthStart]), ALLSELECTED(DimDate), REMOVEFILTERS(DimDate[IsLatestCompleteMonth])), DimDate[MonthStart])
VAR PriorMonth = EDATE(LatestMonth, -12)
VAR CurrentValue = CALCULATE([Cash Balance], FILTER(ALL(DimDate), DimDate[MonthStart] = LatestMonth))
VAR PriorValue = CALCULATE([Cash Balance], FILTER(ALL(DimDate), DimDate[MonthStart] = PriorMonth))
VAR ChangeValue = CurrentValue - PriorValue
VAR ValueTextRaw = FORMAT(DIVIDE(CurrentValue, 1000000), "$#,0.0M;($#,0.0M);$0.0M")
VAR PYTextRaw = IF(ISBLANK(PriorValue), "n/a", FORMAT(DIVIDE(PriorValue, 1000000), "$#,0.0M;($#,0.0M);$0.0M"))
VAR RateValue = DIVIDE(ChangeValue, ABS(PriorValue))
VAR YoYTextRaw = IF(ISBLANK(CurrentValue) || ISBLANK(PriorValue), "n/a", FORMAT(RateValue, "+0.0%;-0.0%;0.0%"))
VAR ValueText = SUBSTITUTE(ValueTextRaw, "%", "%25")
VAR PYText = SUBSTITUTE(PYTextRaw, "%", "%25")
VAR YoYText = SUBSTITUTE(YoYTextRaw, "%", "%25")
VAR YoYColor = IF(ISBLANK(CurrentValue) || ISBLANK(PriorValue), "%236E667B", IF(ChangeValue >= 0, "%234CAF65", "%23C94A4A"))
VAR MonthTable =
    ADDCOLUMNS(
        FILTER(ALLSELECTED(DimDate), DimDate[MonthStart] <= LatestMonth),
        "__Value", [Cash Balance]
    )
VAR CleanTable = FILTER(MonthTable, NOT ISBLANK([__Value]))
VAR RowCount = COUNTROWS(CleanTable)
VAR MinValue = MINX(CleanTable, [__Value])
VAR MaxValue = MAXX(CleanTable, [__Value])
VAR FirstValue = MINX(TOPN(1, CleanTable, DimDate[MonthStart], ASC), [__Value])
VAR LastValue = MINX(TOPN(1, CleanTable, DimDate[MonthStart], DESC), [__Value])
VAR LowMonth = MINX(TOPN(1, CleanTable, [__Value], ASC, DimDate[MonthStart], ASC), DimDate[MonthStart])
VAR LowValue = MINX(FILTER(CleanTable, DimDate[MonthStart] = LowMonth), [__Value])
VAR StartYValue = 80 - DIVIDE(FirstValue - MinValue, MaxValue - MinValue, 0.5) * 42
VAR EndYValue = 80 - DIVIDE(LastValue - MinValue, MaxValue - MinValue, 0.5) * 42
VAR LowRank = RANKX(CleanTable, DimDate[MonthStart], LowMonth, ASC, DENSE) - 1
VAR LowXValue = 136 + DIVIDE(LowRank, MAX(1, RowCount - 1), 0) * 92
VAR LowYValue = 80 - DIVIDE(LowValue - MinValue, MaxValue - MinValue, 0.5) * 42
VAR TrendColor = IF(LastValue >= FirstValue, "%23BE7C10", "%23C94A4A")
VAR BandColor = IF(LastValue >= FirstValue, "%23DDEEDC", "%23F3D7D7")
VAR LinePoints =
    CONCATENATEX(
        CleanTable,
        VAR RankValue = RANKX(CleanTable, DimDate[MonthStart], , ASC, DENSE) - 1
        VAR XValue = 136 + DIVIDE(RankValue, MAX(1, RowCount - 1), 0) * 92
        VAR YValue = 80 - DIVIDE([__Value] - MinValue, MaxValue - MinValue, 0.5) * 42
        RETURN FORMAT(XValue, "0.0") & "," & FORMAT(YValue, "0.0"),
        " ",
        DimDate[MonthStart],
        ASC
    )
VAR AreaPath =
    "M136 84 " &
    CONCATENATEX(
        CleanTable,
        VAR RankValue = RANKX(CleanTable, DimDate[MonthStart], , ASC, DENSE) - 1
        VAR XValue = 136 + DIVIDE(RankValue, MAX(1, RowCount - 1), 0) * 92
        VAR YValue = 80 - DIVIDE([__Value] - MinValue, MaxValue - MinValue, 0.5) * 42
        RETURN "L" & FORMAT(XValue, "0.0") & " " & FORMAT(YValue, "0.0"),
        " ",
        DimDate[MonthStart],
        ASC
    ) & " L228 84 Z"
VAR SVG =
    "<svg xmlns='http://www.w3.org/2000/svg' width='240' height='132' viewBox='0 0 248 140'>" &
    "<rect x='5' y='5' width='238' height='130' rx='14' fill='%23F4EFFA' stroke='%237142A4' stroke-width='2.5'/>" &
    "<rect x='18' y='13' width='212' height='4' rx='2' fill='%23BE7C10' opacity='0.9'/>" &
    "<rect x='18' y='29' width='12' height='12' rx='3' fill='%23BE7C10' opacity='0.95'/>" &
    "<circle cx='24' cy='35' r='2' fill='%23FFFFFF' opacity='0.85'/>" &
    "<text x='36' y='39' font-family='Segoe UI' font-size='14' font-weight='750' fill='%23211A32'>Cash</text>" &
    "<text x='18' y='80' font-family='Segoe UI' font-size='27' font-weight='750' fill='%23BE7C10'>" & ValueText & "</text>" &
    "<rect x='130' y='34' width='104' height='54' rx='8' fill='%23FFFFFF' opacity='0.46'/>" &
    "<rect x='136' y='59' width='92' height='12' rx='6' fill='" & BandColor & "'/>" &
    "<rect x='141' y='52' width='12' height='26' rx='2' fill='%23D9D1EB' opacity='0.34'/>" &
    "<rect x='160' y='48' width='12' height='30' rx='2' fill='%23D9D1EB' opacity='0.28'/>" &
    "<rect x='179' y='44' width='12' height='34' rx='2' fill='%23D9D1EB' opacity='0.24'/>" &
    "<rect x='198' y='40' width='12' height='38' rx='2' fill='%23D9D1EB' opacity='0.20'/>" &
    "<line x1='136' y1='65' x2='228' y2='65' stroke='%23B8AECF' stroke-width='1' stroke-dasharray='4 5'/>" &
    "<path d='" & AreaPath & "' fill='%23B8AEE6' opacity='0.55'/>" &
    "<polyline points='" & LinePoints & "' fill='none' stroke='" & TrendColor & "' stroke-width='3' stroke-linecap='round' stroke-linejoin='round'/>" &
    "<circle cx='136' cy='" & FORMAT(StartYValue, "0.0") & "' r='4' fill='%23FFFFFF' stroke='%2377A4F5' stroke-width='2'/>" &
    "<circle cx='" & FORMAT(LowXValue, "0.0") & "' cy='" & FORMAT(LowYValue, "0.0") & "' r='4' fill='%23D96A5D' stroke='%23FFFFFF' stroke-width='2'/>" &
    "<circle cx='228' cy='" & FORMAT(EndYValue, "0.0") & "' r='5' fill='" & TrendColor & "' stroke='%23FFFFFF' stroke-width='2'/>" &
    "<rect x='16' y='94' width='98' height='34' rx='8' fill='%23FFFFFF' opacity='0.64'/>" &
    "<rect x='122' y='94' width='110' height='34' rx='8' fill='%23FFFFFF' opacity='0.64'/>" &
    "<text x='24' y='108' font-family='Segoe UI' font-size='11' font-weight='750' fill='%23211A32'>PY</text>" &
    "<text x='24' y='123' font-family='Segoe UI' font-size='12' fill='%236E667B'>" & PYText & "</text>" &
    "<text x='132' y='108' font-family='Segoe UI' font-size='11' font-weight='750' fill='%23211A32'>YoY</text>" &
    "<polygon points='134,114 140,124 128,124' fill='" & YoYColor & "'/>" &
    "<text x='148' y='123' font-family='Segoe UI' font-size='12' font-weight='750' fill='" & YoYColor & "'>" & YoYText & "</text>" &
    "</svg>"
RETURN IF(RowCount = 0, BLANK(), "data:image/svg+xml;utf8," & SVG)
```

Format: `text/image`

## Runway KPI Card SVG

```DAX
Runway KPI Card SVG = VAR LatestMonth = MAXX(CALCULATETABLE(VALUES(DimDate[MonthStart]), ALLSELECTED(DimDate), REMOVEFILTERS(DimDate[IsLatestCompleteMonth])), DimDate[MonthStart])
VAR PriorMonth = EDATE(LatestMonth, -12)
VAR CurrentValue = CALCULATE([Runway Months], FILTER(ALL(DimDate), DimDate[MonthStart] = LatestMonth))
VAR PriorValue = CALCULATE([Runway Months], FILTER(ALL(DimDate), DimDate[MonthStart] = PriorMonth))
VAR ChangeValue = CurrentValue - PriorValue
VAR ValueTextRaw = FORMAT(DIVIDE(CurrentValue, 1), "0.0x")
VAR PYTextRaw = IF(ISBLANK(PriorValue), "n/a", FORMAT(DIVIDE(PriorValue, 1), "0.0x"))
VAR YoYTextRaw = IF(ISBLANK(CurrentValue) || ISBLANK(PriorValue), "n/a", FORMAT(ChangeValue, "+0.0x;-0.0x;0.0x"))
VAR ValueText = SUBSTITUTE(ValueTextRaw, "%", "%25")
VAR PYText = SUBSTITUTE(PYTextRaw, "%", "%25")
VAR YoYText = SUBSTITUTE(YoYTextRaw, "%", "%25")
VAR YoYColor = IF(ISBLANK(CurrentValue) || ISBLANK(PriorValue), "%236E667B", IF(ChangeValue >= 0, "%234CAF65", "%23C94A4A"))
VAR MonthTable =
    ADDCOLUMNS(
        FILTER(ALLSELECTED(DimDate), DimDate[MonthStart] <= LatestMonth),
        "__Value", [Runway Months]
    )
VAR CleanTable = FILTER(MonthTable, NOT ISBLANK([__Value]))
VAR RowCount = COUNTROWS(CleanTable)
VAR MinValue = MINX(CleanTable, [__Value])
VAR MaxValue = MAXX(CleanTable, [__Value])
VAR FirstValue = MINX(TOPN(1, CleanTable, DimDate[MonthStart], ASC), [__Value])
VAR LastValue = MINX(TOPN(1, CleanTable, DimDate[MonthStart], DESC), [__Value])
VAR LowMonth = MINX(TOPN(1, CleanTable, [__Value], ASC, DimDate[MonthStart], ASC), DimDate[MonthStart])
VAR LowValue = MINX(FILTER(CleanTable, DimDate[MonthStart] = LowMonth), [__Value])
VAR StartYValue = 80 - DIVIDE(FirstValue - MinValue, MaxValue - MinValue, 0.5) * 42
VAR EndYValue = 80 - DIVIDE(LastValue - MinValue, MaxValue - MinValue, 0.5) * 42
VAR LowRank = RANKX(CleanTable, DimDate[MonthStart], LowMonth, ASC, DENSE) - 1
VAR LowXValue = 136 + DIVIDE(LowRank, MAX(1, RowCount - 1), 0) * 92
VAR LowYValue = 80 - DIVIDE(LowValue - MinValue, MaxValue - MinValue, 0.5) * 42
VAR TrendColor = IF(LastValue >= FirstValue, "%234F87F5", "%23C94A4A")
VAR BandColor = IF(LastValue >= FirstValue, "%23DDEEDC", "%23F3D7D7")
VAR LinePoints =
    CONCATENATEX(
        CleanTable,
        VAR RankValue = RANKX(CleanTable, DimDate[MonthStart], , ASC, DENSE) - 1
        VAR XValue = 136 + DIVIDE(RankValue, MAX(1, RowCount - 1), 0) * 92
        VAR YValue = 80 - DIVIDE([__Value] - MinValue, MaxValue - MinValue, 0.5) * 42
        RETURN FORMAT(XValue, "0.0") & "," & FORMAT(YValue, "0.0"),
        " ",
        DimDate[MonthStart],
        ASC
    )
VAR AreaPath =
    "M136 84 " &
    CONCATENATEX(
        CleanTable,
        VAR RankValue = RANKX(CleanTable, DimDate[MonthStart], , ASC, DENSE) - 1
        VAR XValue = 136 + DIVIDE(RankValue, MAX(1, RowCount - 1), 0) * 92
        VAR YValue = 80 - DIVIDE([__Value] - MinValue, MaxValue - MinValue, 0.5) * 42
        RETURN "L" & FORMAT(XValue, "0.0") & " " & FORMAT(YValue, "0.0"),
        " ",
        DimDate[MonthStart],
        ASC
    ) & " L228 84 Z"
VAR SVG =
    "<svg xmlns='http://www.w3.org/2000/svg' width='240' height='132' viewBox='0 0 248 140'>" &
    "<rect x='5' y='5' width='238' height='130' rx='14' fill='%23F4EFFA' stroke='%237142A4' stroke-width='2.5'/>" &
    "<rect x='18' y='13' width='212' height='4' rx='2' fill='%234F87F5' opacity='0.9'/>" &
    "<rect x='18' y='29' width='12' height='12' rx='3' fill='%234F87F5' opacity='0.95'/>" &
    "<circle cx='24' cy='35' r='2' fill='%23FFFFFF' opacity='0.85'/>" &
    "<text x='36' y='39' font-family='Segoe UI' font-size='14' font-weight='750' fill='%23211A32'>Runway</text>" &
    "<text x='18' y='80' font-family='Segoe UI' font-size='27' font-weight='750' fill='%234F87F5'>" & ValueText & "</text>" &
    "<rect x='130' y='34' width='104' height='54' rx='8' fill='%23FFFFFF' opacity='0.46'/>" &
    "<rect x='136' y='59' width='92' height='12' rx='6' fill='" & BandColor & "'/>" &
    "<rect x='141' y='52' width='12' height='26' rx='2' fill='%23D9D1EB' opacity='0.34'/>" &
    "<rect x='160' y='48' width='12' height='30' rx='2' fill='%23D9D1EB' opacity='0.28'/>" &
    "<rect x='179' y='44' width='12' height='34' rx='2' fill='%23D9D1EB' opacity='0.24'/>" &
    "<rect x='198' y='40' width='12' height='38' rx='2' fill='%23D9D1EB' opacity='0.20'/>" &
    "<line x1='136' y1='65' x2='228' y2='65' stroke='%23B8AECF' stroke-width='1' stroke-dasharray='4 5'/>" &
    "<path d='" & AreaPath & "' fill='%23B8AEE6' opacity='0.55'/>" &
    "<polyline points='" & LinePoints & "' fill='none' stroke='" & TrendColor & "' stroke-width='3' stroke-linecap='round' stroke-linejoin='round'/>" &
    "<circle cx='136' cy='" & FORMAT(StartYValue, "0.0") & "' r='4' fill='%23FFFFFF' stroke='%2377A4F5' stroke-width='2'/>" &
    "<circle cx='" & FORMAT(LowXValue, "0.0") & "' cy='" & FORMAT(LowYValue, "0.0") & "' r='4' fill='%23D96A5D' stroke='%23FFFFFF' stroke-width='2'/>" &
    "<circle cx='228' cy='" & FORMAT(EndYValue, "0.0") & "' r='5' fill='" & TrendColor & "' stroke='%23FFFFFF' stroke-width='2'/>" &
    "<rect x='16' y='94' width='98' height='34' rx='8' fill='%23FFFFFF' opacity='0.64'/>" &
    "<rect x='122' y='94' width='110' height='34' rx='8' fill='%23FFFFFF' opacity='0.64'/>" &
    "<text x='24' y='108' font-family='Segoe UI' font-size='11' font-weight='750' fill='%23211A32'>PY</text>" &
    "<text x='24' y='123' font-family='Segoe UI' font-size='12' fill='%236E667B'>" & PYText & "</text>" &
    "<text x='132' y='108' font-family='Segoe UI' font-size='11' font-weight='750' fill='%23211A32'>YoY</text>" &
    "<polygon points='134,114 140,124 128,124' fill='" & YoYColor & "'/>" &
    "<text x='148' y='123' font-family='Segoe UI' font-size='12' font-weight='750' fill='" & YoYColor & "'>" & YoYText & "</text>" &
    "</svg>"
RETURN IF(RowCount = 0, BLANK(), "data:image/svg+xml;utf8," & SVG)
```

Format: `text/image`

## FCF KPI Card SVG

```DAX
FCF KPI Card SVG = VAR LatestMonth = MAXX(CALCULATETABLE(VALUES(DimDate[MonthStart]), ALLSELECTED(DimDate), REMOVEFILTERS(DimDate[IsLatestCompleteMonth])), DimDate[MonthStart])
VAR PriorMonth = EDATE(LatestMonth, -12)
VAR CurrentValue = CALCULATE([Free Cash Flow], FILTER(ALL(DimDate), DimDate[MonthStart] = LatestMonth))
VAR PriorValue = CALCULATE([Free Cash Flow], FILTER(ALL(DimDate), DimDate[MonthStart] = PriorMonth))
VAR ChangeValue = CurrentValue - PriorValue
VAR ValueTextRaw = FORMAT(DIVIDE(CurrentValue, 1000000), "$#,0.0M;($#,0.0M);$0.0M")
VAR PYTextRaw = IF(ISBLANK(PriorValue), "n/a", FORMAT(DIVIDE(PriorValue, 1000000), "$#,0.0M;($#,0.0M);$0.0M"))
VAR RateValue = DIVIDE(ChangeValue, ABS(PriorValue))
VAR YoYTextRaw = IF(ISBLANK(CurrentValue) || ISBLANK(PriorValue), "n/a", FORMAT(RateValue, "+0.0%;-0.0%;0.0%"))
VAR ValueText = SUBSTITUTE(ValueTextRaw, "%", "%25")
VAR PYText = SUBSTITUTE(PYTextRaw, "%", "%25")
VAR YoYText = SUBSTITUTE(YoYTextRaw, "%", "%25")
VAR YoYColor = IF(ISBLANK(CurrentValue) || ISBLANK(PriorValue), "%236E667B", IF(ChangeValue >= 0, "%234CAF65", "%23C94A4A"))
VAR MonthTable =
    ADDCOLUMNS(
        FILTER(ALLSELECTED(DimDate), DimDate[MonthStart] <= LatestMonth),
        "__Value", [Free Cash Flow]
    )
VAR CleanTable = FILTER(MonthTable, NOT ISBLANK([__Value]))
VAR RowCount = COUNTROWS(CleanTable)
VAR MinValue = MINX(CleanTable, [__Value])
VAR MaxValue = MAXX(CleanTable, [__Value])
VAR FirstValue = MINX(TOPN(1, CleanTable, DimDate[MonthStart], ASC), [__Value])
VAR LastValue = MINX(TOPN(1, CleanTable, DimDate[MonthStart], DESC), [__Value])
VAR LowMonth = MINX(TOPN(1, CleanTable, [__Value], ASC, DimDate[MonthStart], ASC), DimDate[MonthStart])
VAR LowValue = MINX(FILTER(CleanTable, DimDate[MonthStart] = LowMonth), [__Value])
VAR StartYValue = 80 - DIVIDE(FirstValue - MinValue, MaxValue - MinValue, 0.5) * 42
VAR EndYValue = 80 - DIVIDE(LastValue - MinValue, MaxValue - MinValue, 0.5) * 42
VAR LowRank = RANKX(CleanTable, DimDate[MonthStart], LowMonth, ASC, DENSE) - 1
VAR LowXValue = 136 + DIVIDE(LowRank, MAX(1, RowCount - 1), 0) * 92
VAR LowYValue = 80 - DIVIDE(LowValue - MinValue, MaxValue - MinValue, 0.5) * 42
VAR TrendColor = IF(LastValue >= FirstValue, "%230F9F95", "%23C94A4A")
VAR BandColor = IF(LastValue >= FirstValue, "%23DDEEDC", "%23F3D7D7")
VAR LinePoints =
    CONCATENATEX(
        CleanTable,
        VAR RankValue = RANKX(CleanTable, DimDate[MonthStart], , ASC, DENSE) - 1
        VAR XValue = 136 + DIVIDE(RankValue, MAX(1, RowCount - 1), 0) * 92
        VAR YValue = 80 - DIVIDE([__Value] - MinValue, MaxValue - MinValue, 0.5) * 42
        RETURN FORMAT(XValue, "0.0") & "," & FORMAT(YValue, "0.0"),
        " ",
        DimDate[MonthStart],
        ASC
    )
VAR AreaPath =
    "M136 84 " &
    CONCATENATEX(
        CleanTable,
        VAR RankValue = RANKX(CleanTable, DimDate[MonthStart], , ASC, DENSE) - 1
        VAR XValue = 136 + DIVIDE(RankValue, MAX(1, RowCount - 1), 0) * 92
        VAR YValue = 80 - DIVIDE([__Value] - MinValue, MaxValue - MinValue, 0.5) * 42
        RETURN "L" & FORMAT(XValue, "0.0") & " " & FORMAT(YValue, "0.0"),
        " ",
        DimDate[MonthStart],
        ASC
    ) & " L228 84 Z"
VAR SVG =
    "<svg xmlns='http://www.w3.org/2000/svg' width='240' height='132' viewBox='0 0 248 140'>" &
    "<rect x='5' y='5' width='238' height='130' rx='14' fill='%23F4EFFA' stroke='%237142A4' stroke-width='2.5'/>" &
    "<rect x='18' y='13' width='212' height='4' rx='2' fill='%230F9F95' opacity='0.9'/>" &
    "<rect x='18' y='29' width='12' height='12' rx='3' fill='%230F9F95' opacity='0.95'/>" &
    "<circle cx='24' cy='35' r='2' fill='%23FFFFFF' opacity='0.85'/>" &
    "<text x='36' y='39' font-family='Segoe UI' font-size='14' font-weight='750' fill='%23211A32'>FCF</text>" &
    "<text x='18' y='80' font-family='Segoe UI' font-size='27' font-weight='750' fill='%230F9F95'>" & ValueText & "</text>" &
    "<rect x='130' y='34' width='104' height='54' rx='8' fill='%23FFFFFF' opacity='0.46'/>" &
    "<rect x='136' y='59' width='92' height='12' rx='6' fill='" & BandColor & "'/>" &
    "<rect x='141' y='52' width='12' height='26' rx='2' fill='%23D9D1EB' opacity='0.34'/>" &
    "<rect x='160' y='48' width='12' height='30' rx='2' fill='%23D9D1EB' opacity='0.28'/>" &
    "<rect x='179' y='44' width='12' height='34' rx='2' fill='%23D9D1EB' opacity='0.24'/>" &
    "<rect x='198' y='40' width='12' height='38' rx='2' fill='%23D9D1EB' opacity='0.20'/>" &
    "<line x1='136' y1='65' x2='228' y2='65' stroke='%23B8AECF' stroke-width='1' stroke-dasharray='4 5'/>" &
    "<path d='" & AreaPath & "' fill='%23B8AEE6' opacity='0.55'/>" &
    "<polyline points='" & LinePoints & "' fill='none' stroke='" & TrendColor & "' stroke-width='3' stroke-linecap='round' stroke-linejoin='round'/>" &
    "<circle cx='136' cy='" & FORMAT(StartYValue, "0.0") & "' r='4' fill='%23FFFFFF' stroke='%2377A4F5' stroke-width='2'/>" &
    "<circle cx='" & FORMAT(LowXValue, "0.0") & "' cy='" & FORMAT(LowYValue, "0.0") & "' r='4' fill='%23D96A5D' stroke='%23FFFFFF' stroke-width='2'/>" &
    "<circle cx='228' cy='" & FORMAT(EndYValue, "0.0") & "' r='5' fill='" & TrendColor & "' stroke='%23FFFFFF' stroke-width='2'/>" &
    "<rect x='16' y='94' width='98' height='34' rx='8' fill='%23FFFFFF' opacity='0.64'/>" &
    "<rect x='122' y='94' width='110' height='34' rx='8' fill='%23FFFFFF' opacity='0.64'/>" &
    "<text x='24' y='108' font-family='Segoe UI' font-size='11' font-weight='750' fill='%23211A32'>PY</text>" &
    "<text x='24' y='123' font-family='Segoe UI' font-size='12' fill='%236E667B'>" & PYText & "</text>" &
    "<text x='132' y='108' font-family='Segoe UI' font-size='11' font-weight='750' fill='%23211A32'>YoY</text>" &
    "<polygon points='134,114 140,124 128,124' fill='" & YoYColor & "'/>" &
    "<text x='148' y='123' font-family='Segoe UI' font-size='12' font-weight='750' fill='" & YoYColor & "'>" & YoYText & "</text>" &
    "</svg>"
RETURN IF(RowCount = 0, BLANK(), "data:image/svg+xml;utf8," & SVG)
```

Format: `text/image`

## Burn KPI Card SVG

```DAX
Burn KPI Card SVG = VAR LatestMonth = MAXX(CALCULATETABLE(VALUES(DimDate[MonthStart]), ALLSELECTED(DimDate), REMOVEFILTERS(DimDate[IsLatestCompleteMonth])), DimDate[MonthStart])
VAR PriorMonth = EDATE(LatestMonth, -12)
VAR CurrentValue = CALCULATE([Net Burn], FILTER(ALL(DimDate), DimDate[MonthStart] = LatestMonth))
VAR PriorValue = CALCULATE([Net Burn], FILTER(ALL(DimDate), DimDate[MonthStart] = PriorMonth))
VAR ChangeValue = CurrentValue - PriorValue
VAR ValueTextRaw = FORMAT(DIVIDE(CurrentValue, 1000000), "$#,0.0M;($#,0.0M);$0.0M")
VAR PYTextRaw = IF(ISBLANK(PriorValue), "n/a", FORMAT(DIVIDE(PriorValue, 1000000), "$#,0.0M;($#,0.0M);$0.0M"))
VAR RateValue = DIVIDE(ChangeValue, ABS(PriorValue))
VAR YoYTextRaw = IF(ISBLANK(CurrentValue) || ISBLANK(PriorValue), "n/a", FORMAT(RateValue, "+0.0%;-0.0%;0.0%"))
VAR ValueText = SUBSTITUTE(ValueTextRaw, "%", "%25")
VAR PYText = SUBSTITUTE(PYTextRaw, "%", "%25")
VAR YoYText = SUBSTITUTE(YoYTextRaw, "%", "%25")
VAR YoYColor = IF(ISBLANK(CurrentValue) || ISBLANK(PriorValue), "%236E667B", IF(ChangeValue <= 0, "%234CAF65", "%23C94A4A"))
VAR MonthTable =
    ADDCOLUMNS(
        FILTER(ALLSELECTED(DimDate), DimDate[MonthStart] <= LatestMonth),
        "__Value", [Net Burn]
    )
VAR CleanTable = FILTER(MonthTable, NOT ISBLANK([__Value]))
VAR RowCount = COUNTROWS(CleanTable)
VAR MinValue = MINX(CleanTable, [__Value])
VAR MaxValue = MAXX(CleanTable, [__Value])
VAR FirstValue = MINX(TOPN(1, CleanTable, DimDate[MonthStart], ASC), [__Value])
VAR LastValue = MINX(TOPN(1, CleanTable, DimDate[MonthStart], DESC), [__Value])
VAR LowMonth = MINX(TOPN(1, CleanTable, [__Value], ASC, DimDate[MonthStart], ASC), DimDate[MonthStart])
VAR LowValue = MINX(FILTER(CleanTable, DimDate[MonthStart] = LowMonth), [__Value])
VAR StartYValue = 80 - DIVIDE(FirstValue - MinValue, MaxValue - MinValue, 0.5) * 42
VAR EndYValue = 80 - DIVIDE(LastValue - MinValue, MaxValue - MinValue, 0.5) * 42
VAR LowRank = RANKX(CleanTable, DimDate[MonthStart], LowMonth, ASC, DENSE) - 1
VAR LowXValue = 136 + DIVIDE(LowRank, MAX(1, RowCount - 1), 0) * 92
VAR LowYValue = 80 - DIVIDE(LowValue - MinValue, MaxValue - MinValue, 0.5) * 42
VAR TrendColor = IF(LastValue <= FirstValue, "%23B73535", "%23C94A4A")
VAR BandColor = IF(LastValue <= FirstValue, "%23DDEEDC", "%23F3D7D7")
VAR LinePoints =
    CONCATENATEX(
        CleanTable,
        VAR RankValue = RANKX(CleanTable, DimDate[MonthStart], , ASC, DENSE) - 1
        VAR XValue = 136 + DIVIDE(RankValue, MAX(1, RowCount - 1), 0) * 92
        VAR YValue = 80 - DIVIDE([__Value] - MinValue, MaxValue - MinValue, 0.5) * 42
        RETURN FORMAT(XValue, "0.0") & "," & FORMAT(YValue, "0.0"),
        " ",
        DimDate[MonthStart],
        ASC
    )
VAR AreaPath =
    "M136 84 " &
    CONCATENATEX(
        CleanTable,
        VAR RankValue = RANKX(CleanTable, DimDate[MonthStart], , ASC, DENSE) - 1
        VAR XValue = 136 + DIVIDE(RankValue, MAX(1, RowCount - 1), 0) * 92
        VAR YValue = 80 - DIVIDE([__Value] - MinValue, MaxValue - MinValue, 0.5) * 42
        RETURN "L" & FORMAT(XValue, "0.0") & " " & FORMAT(YValue, "0.0"),
        " ",
        DimDate[MonthStart],
        ASC
    ) & " L228 84 Z"
VAR SVG =
    "<svg xmlns='http://www.w3.org/2000/svg' width='240' height='132' viewBox='0 0 248 140'>" &
    "<rect x='5' y='5' width='238' height='130' rx='14' fill='%23F4EFFA' stroke='%237142A4' stroke-width='2.5'/>" &
    "<rect x='18' y='13' width='212' height='4' rx='2' fill='%23B73535' opacity='0.9'/>" &
    "<rect x='18' y='29' width='12' height='12' rx='3' fill='%23B73535' opacity='0.95'/>" &
    "<circle cx='24' cy='35' r='2' fill='%23FFFFFF' opacity='0.85'/>" &
    "<text x='36' y='39' font-family='Segoe UI' font-size='14' font-weight='750' fill='%23211A32'>Burn</text>" &
    "<text x='18' y='80' font-family='Segoe UI' font-size='27' font-weight='750' fill='%23B73535'>" & ValueText & "</text>" &
    "<rect x='130' y='34' width='104' height='54' rx='8' fill='%23FFFFFF' opacity='0.46'/>" &
    "<rect x='136' y='59' width='92' height='12' rx='6' fill='" & BandColor & "'/>" &
    "<rect x='141' y='52' width='12' height='26' rx='2' fill='%23D9D1EB' opacity='0.34'/>" &
    "<rect x='160' y='48' width='12' height='30' rx='2' fill='%23D9D1EB' opacity='0.28'/>" &
    "<rect x='179' y='44' width='12' height='34' rx='2' fill='%23D9D1EB' opacity='0.24'/>" &
    "<rect x='198' y='40' width='12' height='38' rx='2' fill='%23D9D1EB' opacity='0.20'/>" &
    "<line x1='136' y1='65' x2='228' y2='65' stroke='%23B8AECF' stroke-width='1' stroke-dasharray='4 5'/>" &
    "<path d='" & AreaPath & "' fill='%23B8AEE6' opacity='0.55'/>" &
    "<polyline points='" & LinePoints & "' fill='none' stroke='" & TrendColor & "' stroke-width='3' stroke-linecap='round' stroke-linejoin='round'/>" &
    "<circle cx='136' cy='" & FORMAT(StartYValue, "0.0") & "' r='4' fill='%23FFFFFF' stroke='%2377A4F5' stroke-width='2'/>" &
    "<circle cx='" & FORMAT(LowXValue, "0.0") & "' cy='" & FORMAT(LowYValue, "0.0") & "' r='4' fill='%23D96A5D' stroke='%23FFFFFF' stroke-width='2'/>" &
    "<circle cx='228' cy='" & FORMAT(EndYValue, "0.0") & "' r='5' fill='" & TrendColor & "' stroke='%23FFFFFF' stroke-width='2'/>" &
    "<rect x='16' y='94' width='98' height='34' rx='8' fill='%23FFFFFF' opacity='0.64'/>" &
    "<rect x='122' y='94' width='110' height='34' rx='8' fill='%23FFFFFF' opacity='0.64'/>" &
    "<text x='24' y='108' font-family='Segoe UI' font-size='11' font-weight='750' fill='%23211A32'>PY</text>" &
    "<text x='24' y='123' font-family='Segoe UI' font-size='12' fill='%236E667B'>" & PYText & "</text>" &
    "<text x='132' y='108' font-family='Segoe UI' font-size='11' font-weight='750' fill='%23211A32'>YoY</text>" &
    "<polygon points='134,114 140,124 128,124' fill='" & YoYColor & "'/>" &
    "<text x='148' y='123' font-family='Segoe UI' font-size='12' font-weight='750' fill='" & YoYColor & "'>" & YoYText & "</text>" &
    "</svg>"
RETURN IF(RowCount = 0, BLANK(), "data:image/svg+xml;utf8," & SVG)
```

Format: `text/image`

## Funding KPI Card SVG

```DAX
Funding KPI Card SVG = VAR LatestMonth = MAXX(CALCULATETABLE(VALUES(DimDate[MonthStart]), ALLSELECTED(DimDate), REMOVEFILTERS(DimDate[IsLatestCompleteMonth])), DimDate[MonthStart])
VAR PriorMonth = EDATE(LatestMonth, -12)
VAR CurrentValue = CALCULATE([Funding Need], FILTER(ALL(DimDate), DimDate[MonthStart] = LatestMonth))
VAR PriorValue = CALCULATE([Funding Need], FILTER(ALL(DimDate), DimDate[MonthStart] = PriorMonth))
VAR ChangeValue = CurrentValue - PriorValue
VAR ValueTextRaw = FORMAT(DIVIDE(CurrentValue, 1000000), "$#,0M;($#,0M);$0M")
VAR PYTextRaw = IF(ISBLANK(PriorValue), "n/a", FORMAT(DIVIDE(PriorValue, 1000000), "$#,0M;($#,0M);$0M"))
VAR RateValue = DIVIDE(ChangeValue, ABS(PriorValue))
VAR YoYTextRaw = IF(ISBLANK(CurrentValue) || ISBLANK(PriorValue), "n/a", FORMAT(RateValue, "+0.0%;-0.0%;0.0%"))
VAR ValueText = SUBSTITUTE(ValueTextRaw, "%", "%25")
VAR PYText = SUBSTITUTE(PYTextRaw, "%", "%25")
VAR YoYText = SUBSTITUTE(YoYTextRaw, "%", "%25")
VAR YoYColor = IF(ISBLANK(CurrentValue) || ISBLANK(PriorValue), "%236E667B", IF(ChangeValue <= 0, "%234CAF65", "%23C94A4A"))
VAR MonthTable =
    ADDCOLUMNS(
        FILTER(ALLSELECTED(DimDate), DimDate[MonthStart] <= LatestMonth),
        "__Value", [Funding Need]
    )
VAR CleanTable = FILTER(MonthTable, NOT ISBLANK([__Value]))
VAR RowCount = COUNTROWS(CleanTable)
VAR MinValue = MINX(CleanTable, [__Value])
VAR MaxValue = MAXX(CleanTable, [__Value])
VAR FirstValue = MINX(TOPN(1, CleanTable, DimDate[MonthStart], ASC), [__Value])
VAR LastValue = MINX(TOPN(1, CleanTable, DimDate[MonthStart], DESC), [__Value])
VAR LowMonth = MINX(TOPN(1, CleanTable, [__Value], ASC, DimDate[MonthStart], ASC), DimDate[MonthStart])
VAR LowValue = MINX(FILTER(CleanTable, DimDate[MonthStart] = LowMonth), [__Value])
VAR StartYValue = 80 - DIVIDE(FirstValue - MinValue, MaxValue - MinValue, 0.5) * 42
VAR EndYValue = 80 - DIVIDE(LastValue - MinValue, MaxValue - MinValue, 0.5) * 42
VAR LowRank = RANKX(CleanTable, DimDate[MonthStart], LowMonth, ASC, DENSE) - 1
VAR LowXValue = 136 + DIVIDE(LowRank, MAX(1, RowCount - 1), 0) * 92
VAR LowYValue = 80 - DIVIDE(LowValue - MinValue, MaxValue - MinValue, 0.5) * 42
VAR TrendColor = IF(LastValue <= FirstValue, "%231F8E45", "%23C94A4A")
VAR BandColor = IF(LastValue <= FirstValue, "%23DDEEDC", "%23F3D7D7")
VAR LinePoints =
    CONCATENATEX(
        CleanTable,
        VAR RankValue = RANKX(CleanTable, DimDate[MonthStart], , ASC, DENSE) - 1
        VAR XValue = 136 + DIVIDE(RankValue, MAX(1, RowCount - 1), 0) * 92
        VAR YValue = 80 - DIVIDE([__Value] - MinValue, MaxValue - MinValue, 0.5) * 42
        RETURN FORMAT(XValue, "0.0") & "," & FORMAT(YValue, "0.0"),
        " ",
        DimDate[MonthStart],
        ASC
    )
VAR AreaPath =
    "M136 84 " &
    CONCATENATEX(
        CleanTable,
        VAR RankValue = RANKX(CleanTable, DimDate[MonthStart], , ASC, DENSE) - 1
        VAR XValue = 136 + DIVIDE(RankValue, MAX(1, RowCount - 1), 0) * 92
        VAR YValue = 80 - DIVIDE([__Value] - MinValue, MaxValue - MinValue, 0.5) * 42
        RETURN "L" & FORMAT(XValue, "0.0") & " " & FORMAT(YValue, "0.0"),
        " ",
        DimDate[MonthStart],
        ASC
    ) & " L228 84 Z"
VAR SVG =
    "<svg xmlns='http://www.w3.org/2000/svg' width='240' height='132' viewBox='0 0 248 140'>" &
    "<rect x='5' y='5' width='238' height='130' rx='14' fill='%23F4EFFA' stroke='%237142A4' stroke-width='2.5'/>" &
    "<rect x='18' y='13' width='212' height='4' rx='2' fill='%231F8E45' opacity='0.9'/>" &
    "<rect x='18' y='29' width='12' height='12' rx='3' fill='%231F8E45' opacity='0.95'/>" &
    "<circle cx='24' cy='35' r='2' fill='%23FFFFFF' opacity='0.85'/>" &
    "<text x='36' y='39' font-family='Segoe UI' font-size='14' font-weight='750' fill='%23211A32'>Funding</text>" &
    "<text x='18' y='80' font-family='Segoe UI' font-size='27' font-weight='750' fill='%231F8E45'>" & ValueText & "</text>" &
    "<rect x='130' y='34' width='104' height='54' rx='8' fill='%23FFFFFF' opacity='0.46'/>" &
    "<rect x='136' y='59' width='92' height='12' rx='6' fill='" & BandColor & "'/>" &
    "<rect x='141' y='52' width='12' height='26' rx='2' fill='%23D9D1EB' opacity='0.34'/>" &
    "<rect x='160' y='48' width='12' height='30' rx='2' fill='%23D9D1EB' opacity='0.28'/>" &
    "<rect x='179' y='44' width='12' height='34' rx='2' fill='%23D9D1EB' opacity='0.24'/>" &
    "<rect x='198' y='40' width='12' height='38' rx='2' fill='%23D9D1EB' opacity='0.20'/>" &
    "<line x1='136' y1='65' x2='228' y2='65' stroke='%23B8AECF' stroke-width='1' stroke-dasharray='4 5'/>" &
    "<path d='" & AreaPath & "' fill='%23B8AEE6' opacity='0.55'/>" &
    "<polyline points='" & LinePoints & "' fill='none' stroke='" & TrendColor & "' stroke-width='3' stroke-linecap='round' stroke-linejoin='round'/>" &
    "<circle cx='136' cy='" & FORMAT(StartYValue, "0.0") & "' r='4' fill='%23FFFFFF' stroke='%2377A4F5' stroke-width='2'/>" &
    "<circle cx='" & FORMAT(LowXValue, "0.0") & "' cy='" & FORMAT(LowYValue, "0.0") & "' r='4' fill='%23D96A5D' stroke='%23FFFFFF' stroke-width='2'/>" &
    "<circle cx='228' cy='" & FORMAT(EndYValue, "0.0") & "' r='5' fill='" & TrendColor & "' stroke='%23FFFFFF' stroke-width='2'/>" &
    "<rect x='16' y='94' width='98' height='34' rx='8' fill='%23FFFFFF' opacity='0.64'/>" &
    "<rect x='122' y='94' width='110' height='34' rx='8' fill='%23FFFFFF' opacity='0.64'/>" &
    "<text x='24' y='108' font-family='Segoe UI' font-size='11' font-weight='750' fill='%23211A32'>PY</text>" &
    "<text x='24' y='123' font-family='Segoe UI' font-size='12' fill='%236E667B'>" & PYText & "</text>" &
    "<text x='132' y='108' font-family='Segoe UI' font-size='11' font-weight='750' fill='%23211A32'>YoY</text>" &
    "<polygon points='134,114 140,124 128,124' fill='" & YoYColor & "'/>" &
    "<text x='148' y='123' font-family='Segoe UI' font-size='12' font-weight='750' fill='" & YoYColor & "'>" & YoYText & "</text>" &
    "</svg>"
RETURN IF(RowCount = 0, BLANK(), "data:image/svg+xml;utf8," & SVG)
```

Format: `text/image`

## EV KPI Card SVG

```DAX
EV KPI Card SVG = VAR LatestMonth = MAXX(CALCULATETABLE(VALUES(DimDate[MonthStart]), ALLSELECTED(DimDate), REMOVEFILTERS(DimDate[IsLatestCompleteMonth])), DimDate[MonthStart])
VAR PriorMonth = EDATE(LatestMonth, -12)
VAR CurrentValue = CALCULATE([Enterprise Value], FILTER(ALL(DimDate), DimDate[MonthStart] = LatestMonth))
VAR PriorValue = CALCULATE([Enterprise Value], FILTER(ALL(DimDate), DimDate[MonthStart] = PriorMonth))
VAR ChangeValue = CurrentValue - PriorValue
VAR ValueTextRaw = FORMAT(DIVIDE(CurrentValue, 1000000000), "$#,0.0B;($#,0.0B);$0.0B")
VAR PYTextRaw = IF(ISBLANK(PriorValue), "n/a", FORMAT(DIVIDE(PriorValue, 1000000000), "$#,0.0B;($#,0.0B);$0.0B"))
VAR RateValue = DIVIDE(ChangeValue, ABS(PriorValue))
VAR YoYTextRaw = IF(ISBLANK(CurrentValue) || ISBLANK(PriorValue), "n/a", FORMAT(RateValue, "+0.0%;-0.0%;0.0%"))
VAR ValueText = SUBSTITUTE(ValueTextRaw, "%", "%25")
VAR PYText = SUBSTITUTE(PYTextRaw, "%", "%25")
VAR YoYText = SUBSTITUTE(YoYTextRaw, "%", "%25")
VAR YoYColor = IF(ISBLANK(CurrentValue) || ISBLANK(PriorValue), "%236E667B", IF(ChangeValue >= 0, "%234CAF65", "%23C94A4A"))
VAR MonthTable =
    ADDCOLUMNS(
        FILTER(ALLSELECTED(DimDate), DimDate[MonthStart] <= LatestMonth),
        "__Value", [Enterprise Value]
    )
VAR CleanTable = FILTER(MonthTable, NOT ISBLANK([__Value]))
VAR RowCount = COUNTROWS(CleanTable)
VAR MinValue = MINX(CleanTable, [__Value])
VAR MaxValue = MAXX(CleanTable, [__Value])
VAR FirstValue = MINX(TOPN(1, CleanTable, DimDate[MonthStart], ASC), [__Value])
VAR LastValue = MINX(TOPN(1, CleanTable, DimDate[MonthStart], DESC), [__Value])
VAR LowMonth = MINX(TOPN(1, CleanTable, [__Value], ASC, DimDate[MonthStart], ASC), DimDate[MonthStart])
VAR LowValue = MINX(FILTER(CleanTable, DimDate[MonthStart] = LowMonth), [__Value])
VAR StartYValue = 80 - DIVIDE(FirstValue - MinValue, MaxValue - MinValue, 0.5) * 42
VAR EndYValue = 80 - DIVIDE(LastValue - MinValue, MaxValue - MinValue, 0.5) * 42
VAR LowRank = RANKX(CleanTable, DimDate[MonthStart], LowMonth, ASC, DENSE) - 1
VAR LowXValue = 136 + DIVIDE(LowRank, MAX(1, RowCount - 1), 0) * 92
VAR LowYValue = 80 - DIVIDE(LowValue - MinValue, MaxValue - MinValue, 0.5) * 42
VAR TrendColor = IF(LastValue >= FirstValue, "%234F87F5", "%23C94A4A")
VAR BandColor = IF(LastValue >= FirstValue, "%23DDEEDC", "%23F3D7D7")
VAR LinePoints =
    CONCATENATEX(
        CleanTable,
        VAR RankValue = RANKX(CleanTable, DimDate[MonthStart], , ASC, DENSE) - 1
        VAR XValue = 136 + DIVIDE(RankValue, MAX(1, RowCount - 1), 0) * 92
        VAR YValue = 80 - DIVIDE([__Value] - MinValue, MaxValue - MinValue, 0.5) * 42
        RETURN FORMAT(XValue, "0.0") & "," & FORMAT(YValue, "0.0"),
        " ",
        DimDate[MonthStart],
        ASC
    )
VAR AreaPath =
    "M136 84 " &
    CONCATENATEX(
        CleanTable,
        VAR RankValue = RANKX(CleanTable, DimDate[MonthStart], , ASC, DENSE) - 1
        VAR XValue = 136 + DIVIDE(RankValue, MAX(1, RowCount - 1), 0) * 92
        VAR YValue = 80 - DIVIDE([__Value] - MinValue, MaxValue - MinValue, 0.5) * 42
        RETURN "L" & FORMAT(XValue, "0.0") & " " & FORMAT(YValue, "0.0"),
        " ",
        DimDate[MonthStart],
        ASC
    ) & " L228 84 Z"
VAR SVG =
    "<svg xmlns='http://www.w3.org/2000/svg' width='240' height='132' viewBox='0 0 248 140'>" &
    "<rect x='5' y='5' width='238' height='130' rx='14' fill='%23F4EFFA' stroke='%237142A4' stroke-width='2.5'/>" &
    "<rect x='18' y='13' width='212' height='4' rx='2' fill='%234F87F5' opacity='0.9'/>" &
    "<rect x='18' y='29' width='12' height='12' rx='3' fill='%234F87F5' opacity='0.95'/>" &
    "<circle cx='24' cy='35' r='2' fill='%23FFFFFF' opacity='0.85'/>" &
    "<text x='36' y='39' font-family='Segoe UI' font-size='14' font-weight='750' fill='%23211A32'>EV</text>" &
    "<text x='18' y='80' font-family='Segoe UI' font-size='27' font-weight='750' fill='%234F87F5'>" & ValueText & "</text>" &
    "<rect x='130' y='34' width='104' height='54' rx='8' fill='%23FFFFFF' opacity='0.46'/>" &
    "<rect x='136' y='59' width='92' height='12' rx='6' fill='" & BandColor & "'/>" &
    "<rect x='141' y='52' width='12' height='26' rx='2' fill='%23D9D1EB' opacity='0.34'/>" &
    "<rect x='160' y='48' width='12' height='30' rx='2' fill='%23D9D1EB' opacity='0.28'/>" &
    "<rect x='179' y='44' width='12' height='34' rx='2' fill='%23D9D1EB' opacity='0.24'/>" &
    "<rect x='198' y='40' width='12' height='38' rx='2' fill='%23D9D1EB' opacity='0.20'/>" &
    "<line x1='136' y1='65' x2='228' y2='65' stroke='%23B8AECF' stroke-width='1' stroke-dasharray='4 5'/>" &
    "<path d='" & AreaPath & "' fill='%23B8AEE6' opacity='0.55'/>" &
    "<polyline points='" & LinePoints & "' fill='none' stroke='" & TrendColor & "' stroke-width='3' stroke-linecap='round' stroke-linejoin='round'/>" &
    "<circle cx='136' cy='" & FORMAT(StartYValue, "0.0") & "' r='4' fill='%23FFFFFF' stroke='%2377A4F5' stroke-width='2'/>" &
    "<circle cx='" & FORMAT(LowXValue, "0.0") & "' cy='" & FORMAT(LowYValue, "0.0") & "' r='4' fill='%23D96A5D' stroke='%23FFFFFF' stroke-width='2'/>" &
    "<circle cx='228' cy='" & FORMAT(EndYValue, "0.0") & "' r='5' fill='" & TrendColor & "' stroke='%23FFFFFF' stroke-width='2'/>" &
    "<rect x='16' y='94' width='98' height='34' rx='8' fill='%23FFFFFF' opacity='0.64'/>" &
    "<rect x='122' y='94' width='110' height='34' rx='8' fill='%23FFFFFF' opacity='0.64'/>" &
    "<text x='24' y='108' font-family='Segoe UI' font-size='11' font-weight='750' fill='%23211A32'>PY</text>" &
    "<text x='24' y='123' font-family='Segoe UI' font-size='12' fill='%236E667B'>" & PYText & "</text>" &
    "<text x='132' y='108' font-family='Segoe UI' font-size='11' font-weight='750' fill='%23211A32'>YoY</text>" &
    "<polygon points='134,114 140,124 128,124' fill='" & YoYColor & "'/>" &
    "<text x='148' y='123' font-family='Segoe UI' font-size='12' font-weight='750' fill='" & YoYColor & "'>" & YoYText & "</text>" &
    "</svg>"
RETURN IF(RowCount = 0, BLANK(), "data:image/svg+xml;utf8," & SVG)
```

Format: `text/image`

## Equity KPI Card SVG

```DAX
Equity KPI Card SVG = VAR LatestMonth = MAXX(CALCULATETABLE(VALUES(DimDate[MonthStart]), ALLSELECTED(DimDate), REMOVEFILTERS(DimDate[IsLatestCompleteMonth])), DimDate[MonthStart])
VAR PriorMonth = EDATE(LatestMonth, -12)
VAR CurrentValue = CALCULATE([Equity Value], FILTER(ALL(DimDate), DimDate[MonthStart] = LatestMonth))
VAR PriorValue = CALCULATE([Equity Value], FILTER(ALL(DimDate), DimDate[MonthStart] = PriorMonth))
VAR ChangeValue = CurrentValue - PriorValue
VAR ValueTextRaw = FORMAT(DIVIDE(CurrentValue, 1000000000), "$#,0.0B;($#,0.0B);$0.0B")
VAR PYTextRaw = IF(ISBLANK(PriorValue), "n/a", FORMAT(DIVIDE(PriorValue, 1000000000), "$#,0.0B;($#,0.0B);$0.0B"))
VAR RateValue = DIVIDE(ChangeValue, ABS(PriorValue))
VAR YoYTextRaw = IF(ISBLANK(CurrentValue) || ISBLANK(PriorValue), "n/a", FORMAT(RateValue, "+0.0%;-0.0%;0.0%"))
VAR ValueText = SUBSTITUTE(ValueTextRaw, "%", "%25")
VAR PYText = SUBSTITUTE(PYTextRaw, "%", "%25")
VAR YoYText = SUBSTITUTE(YoYTextRaw, "%", "%25")
VAR YoYColor = IF(ISBLANK(CurrentValue) || ISBLANK(PriorValue), "%236E667B", IF(ChangeValue >= 0, "%234CAF65", "%23C94A4A"))
VAR MonthTable =
    ADDCOLUMNS(
        FILTER(ALLSELECTED(DimDate), DimDate[MonthStart] <= LatestMonth),
        "__Value", [Equity Value]
    )
VAR CleanTable = FILTER(MonthTable, NOT ISBLANK([__Value]))
VAR RowCount = COUNTROWS(CleanTable)
VAR MinValue = MINX(CleanTable, [__Value])
VAR MaxValue = MAXX(CleanTable, [__Value])
VAR FirstValue = MINX(TOPN(1, CleanTable, DimDate[MonthStart], ASC), [__Value])
VAR LastValue = MINX(TOPN(1, CleanTable, DimDate[MonthStart], DESC), [__Value])
VAR LowMonth = MINX(TOPN(1, CleanTable, [__Value], ASC, DimDate[MonthStart], ASC), DimDate[MonthStart])
VAR LowValue = MINX(FILTER(CleanTable, DimDate[MonthStart] = LowMonth), [__Value])
VAR StartYValue = 80 - DIVIDE(FirstValue - MinValue, MaxValue - MinValue, 0.5) * 42
VAR EndYValue = 80 - DIVIDE(LastValue - MinValue, MaxValue - MinValue, 0.5) * 42
VAR LowRank = RANKX(CleanTable, DimDate[MonthStart], LowMonth, ASC, DENSE) - 1
VAR LowXValue = 136 + DIVIDE(LowRank, MAX(1, RowCount - 1), 0) * 92
VAR LowYValue = 80 - DIVIDE(LowValue - MinValue, MaxValue - MinValue, 0.5) * 42
VAR TrendColor = IF(LastValue >= FirstValue, "%231F8E45", "%23C94A4A")
VAR BandColor = IF(LastValue >= FirstValue, "%23DDEEDC", "%23F3D7D7")
VAR LinePoints =
    CONCATENATEX(
        CleanTable,
        VAR RankValue = RANKX(CleanTable, DimDate[MonthStart], , ASC, DENSE) - 1
        VAR XValue = 136 + DIVIDE(RankValue, MAX(1, RowCount - 1), 0) * 92
        VAR YValue = 80 - DIVIDE([__Value] - MinValue, MaxValue - MinValue, 0.5) * 42
        RETURN FORMAT(XValue, "0.0") & "," & FORMAT(YValue, "0.0"),
        " ",
        DimDate[MonthStart],
        ASC
    )
VAR AreaPath =
    "M136 84 " &
    CONCATENATEX(
        CleanTable,
        VAR RankValue = RANKX(CleanTable, DimDate[MonthStart], , ASC, DENSE) - 1
        VAR XValue = 136 + DIVIDE(RankValue, MAX(1, RowCount - 1), 0) * 92
        VAR YValue = 80 - DIVIDE([__Value] - MinValue, MaxValue - MinValue, 0.5) * 42
        RETURN "L" & FORMAT(XValue, "0.0") & " " & FORMAT(YValue, "0.0"),
        " ",
        DimDate[MonthStart],
        ASC
    ) & " L228 84 Z"
VAR SVG =
    "<svg xmlns='http://www.w3.org/2000/svg' width='240' height='132' viewBox='0 0 248 140'>" &
    "<rect x='5' y='5' width='238' height='130' rx='14' fill='%23F4EFFA' stroke='%237142A4' stroke-width='2.5'/>" &
    "<rect x='18' y='13' width='212' height='4' rx='2' fill='%231F8E45' opacity='0.9'/>" &
    "<rect x='18' y='29' width='12' height='12' rx='3' fill='%231F8E45' opacity='0.95'/>" &
    "<circle cx='24' cy='35' r='2' fill='%23FFFFFF' opacity='0.85'/>" &
    "<text x='36' y='39' font-family='Segoe UI' font-size='14' font-weight='750' fill='%23211A32'>Equity</text>" &
    "<text x='18' y='80' font-family='Segoe UI' font-size='27' font-weight='750' fill='%231F8E45'>" & ValueText & "</text>" &
    "<rect x='130' y='34' width='104' height='54' rx='8' fill='%23FFFFFF' opacity='0.46'/>" &
    "<rect x='136' y='59' width='92' height='12' rx='6' fill='" & BandColor & "'/>" &
    "<rect x='141' y='52' width='12' height='26' rx='2' fill='%23D9D1EB' opacity='0.34'/>" &
    "<rect x='160' y='48' width='12' height='30' rx='2' fill='%23D9D1EB' opacity='0.28'/>" &
    "<rect x='179' y='44' width='12' height='34' rx='2' fill='%23D9D1EB' opacity='0.24'/>" &
    "<rect x='198' y='40' width='12' height='38' rx='2' fill='%23D9D1EB' opacity='0.20'/>" &
    "<line x1='136' y1='65' x2='228' y2='65' stroke='%23B8AECF' stroke-width='1' stroke-dasharray='4 5'/>" &
    "<path d='" & AreaPath & "' fill='%23B8AEE6' opacity='0.55'/>" &
    "<polyline points='" & LinePoints & "' fill='none' stroke='" & TrendColor & "' stroke-width='3' stroke-linecap='round' stroke-linejoin='round'/>" &
    "<circle cx='136' cy='" & FORMAT(StartYValue, "0.0") & "' r='4' fill='%23FFFFFF' stroke='%2377A4F5' stroke-width='2'/>" &
    "<circle cx='" & FORMAT(LowXValue, "0.0") & "' cy='" & FORMAT(LowYValue, "0.0") & "' r='4' fill='%23D96A5D' stroke='%23FFFFFF' stroke-width='2'/>" &
    "<circle cx='228' cy='" & FORMAT(EndYValue, "0.0") & "' r='5' fill='" & TrendColor & "' stroke='%23FFFFFF' stroke-width='2'/>" &
    "<rect x='16' y='94' width='98' height='34' rx='8' fill='%23FFFFFF' opacity='0.64'/>" &
    "<rect x='122' y='94' width='110' height='34' rx='8' fill='%23FFFFFF' opacity='0.64'/>" &
    "<text x='24' y='108' font-family='Segoe UI' font-size='11' font-weight='750' fill='%23211A32'>PY</text>" &
    "<text x='24' y='123' font-family='Segoe UI' font-size='12' fill='%236E667B'>" & PYText & "</text>" &
    "<text x='132' y='108' font-family='Segoe UI' font-size='11' font-weight='750' fill='%23211A32'>YoY</text>" &
    "<polygon points='134,114 140,124 128,124' fill='" & YoYColor & "'/>" &
    "<text x='148' y='123' font-family='Segoe UI' font-size='12' font-weight='750' fill='" & YoYColor & "'>" & YoYText & "</text>" &
    "</svg>"
RETURN IF(RowCount = 0, BLANK(), "data:image/svg+xml;utf8," & SVG)
```

Format: `text/image`

## Leverage KPI Card SVG

```DAX
Leverage KPI Card SVG = VAR LatestMonth = MAXX(CALCULATETABLE(VALUES(DimDate[MonthStart]), ALLSELECTED(DimDate), REMOVEFILTERS(DimDate[IsLatestCompleteMonth])), DimDate[MonthStart])
VAR PriorMonth = EDATE(LatestMonth, -12)
VAR CurrentValue = CALCULATE([Leverage Ratio], FILTER(ALL(DimDate), DimDate[MonthStart] = LatestMonth))
VAR PriorValue = CALCULATE([Leverage Ratio], FILTER(ALL(DimDate), DimDate[MonthStart] = PriorMonth))
VAR ChangeValue = CurrentValue - PriorValue
VAR ValueTextRaw = FORMAT(DIVIDE(CurrentValue, 1), "0.0x")
VAR PYTextRaw = IF(ISBLANK(PriorValue), "n/a", FORMAT(DIVIDE(PriorValue, 1), "0.0x"))
VAR YoYTextRaw = IF(ISBLANK(CurrentValue) || ISBLANK(PriorValue), "n/a", FORMAT(ChangeValue, "+0.0x;-0.0x;0.0x"))
VAR ValueText = SUBSTITUTE(ValueTextRaw, "%", "%25")
VAR PYText = SUBSTITUTE(PYTextRaw, "%", "%25")
VAR YoYText = SUBSTITUTE(YoYTextRaw, "%", "%25")
VAR YoYColor = IF(ISBLANK(CurrentValue) || ISBLANK(PriorValue), "%236E667B", IF(ChangeValue <= 0, "%234CAF65", "%23C94A4A"))
VAR MonthTable =
    ADDCOLUMNS(
        FILTER(ALLSELECTED(DimDate), DimDate[MonthStart] <= LatestMonth),
        "__Value", [Leverage Ratio]
    )
VAR CleanTable = FILTER(MonthTable, NOT ISBLANK([__Value]))
VAR RowCount = COUNTROWS(CleanTable)
VAR MinValue = MINX(CleanTable, [__Value])
VAR MaxValue = MAXX(CleanTable, [__Value])
VAR FirstValue = MINX(TOPN(1, CleanTable, DimDate[MonthStart], ASC), [__Value])
VAR LastValue = MINX(TOPN(1, CleanTable, DimDate[MonthStart], DESC), [__Value])
VAR LowMonth = MINX(TOPN(1, CleanTable, [__Value], ASC, DimDate[MonthStart], ASC), DimDate[MonthStart])
VAR LowValue = MINX(FILTER(CleanTable, DimDate[MonthStart] = LowMonth), [__Value])
VAR StartYValue = 80 - DIVIDE(FirstValue - MinValue, MaxValue - MinValue, 0.5) * 42
VAR EndYValue = 80 - DIVIDE(LastValue - MinValue, MaxValue - MinValue, 0.5) * 42
VAR LowRank = RANKX(CleanTable, DimDate[MonthStart], LowMonth, ASC, DENSE) - 1
VAR LowXValue = 136 + DIVIDE(LowRank, MAX(1, RowCount - 1), 0) * 92
VAR LowYValue = 80 - DIVIDE(LowValue - MinValue, MaxValue - MinValue, 0.5) * 42
VAR TrendColor = IF(LastValue <= FirstValue, "%23BE7C10", "%23C94A4A")
VAR BandColor = IF(LastValue <= FirstValue, "%23DDEEDC", "%23F3D7D7")
VAR LinePoints =
    CONCATENATEX(
        CleanTable,
        VAR RankValue = RANKX(CleanTable, DimDate[MonthStart], , ASC, DENSE) - 1
        VAR XValue = 136 + DIVIDE(RankValue, MAX(1, RowCount - 1), 0) * 92
        VAR YValue = 80 - DIVIDE([__Value] - MinValue, MaxValue - MinValue, 0.5) * 42
        RETURN FORMAT(XValue, "0.0") & "," & FORMAT(YValue, "0.0"),
        " ",
        DimDate[MonthStart],
        ASC
    )
VAR AreaPath =
    "M136 84 " &
    CONCATENATEX(
        CleanTable,
        VAR RankValue = RANKX(CleanTable, DimDate[MonthStart], , ASC, DENSE) - 1
        VAR XValue = 136 + DIVIDE(RankValue, MAX(1, RowCount - 1), 0) * 92
        VAR YValue = 80 - DIVIDE([__Value] - MinValue, MaxValue - MinValue, 0.5) * 42
        RETURN "L" & FORMAT(XValue, "0.0") & " " & FORMAT(YValue, "0.0"),
        " ",
        DimDate[MonthStart],
        ASC
    ) & " L228 84 Z"
VAR SVG =
    "<svg xmlns='http://www.w3.org/2000/svg' width='240' height='132' viewBox='0 0 248 140'>" &
    "<rect x='5' y='5' width='238' height='130' rx='14' fill='%23F4EFFA' stroke='%237142A4' stroke-width='2.5'/>" &
    "<rect x='18' y='13' width='212' height='4' rx='2' fill='%23BE7C10' opacity='0.9'/>" &
    "<rect x='18' y='29' width='12' height='12' rx='3' fill='%23BE7C10' opacity='0.95'/>" &
    "<circle cx='24' cy='35' r='2' fill='%23FFFFFF' opacity='0.85'/>" &
    "<text x='36' y='39' font-family='Segoe UI' font-size='14' font-weight='750' fill='%23211A32'>Leverage</text>" &
    "<text x='18' y='80' font-family='Segoe UI' font-size='27' font-weight='750' fill='%23BE7C10'>" & ValueText & "</text>" &
    "<rect x='130' y='34' width='104' height='54' rx='8' fill='%23FFFFFF' opacity='0.46'/>" &
    "<rect x='136' y='59' width='92' height='12' rx='6' fill='" & BandColor & "'/>" &
    "<rect x='141' y='52' width='12' height='26' rx='2' fill='%23D9D1EB' opacity='0.34'/>" &
    "<rect x='160' y='48' width='12' height='30' rx='2' fill='%23D9D1EB' opacity='0.28'/>" &
    "<rect x='179' y='44' width='12' height='34' rx='2' fill='%23D9D1EB' opacity='0.24'/>" &
    "<rect x='198' y='40' width='12' height='38' rx='2' fill='%23D9D1EB' opacity='0.20'/>" &
    "<line x1='136' y1='65' x2='228' y2='65' stroke='%23B8AECF' stroke-width='1' stroke-dasharray='4 5'/>" &
    "<path d='" & AreaPath & "' fill='%23B8AEE6' opacity='0.55'/>" &
    "<polyline points='" & LinePoints & "' fill='none' stroke='" & TrendColor & "' stroke-width='3' stroke-linecap='round' stroke-linejoin='round'/>" &
    "<circle cx='136' cy='" & FORMAT(StartYValue, "0.0") & "' r='4' fill='%23FFFFFF' stroke='%2377A4F5' stroke-width='2'/>" &
    "<circle cx='" & FORMAT(LowXValue, "0.0") & "' cy='" & FORMAT(LowYValue, "0.0") & "' r='4' fill='%23D96A5D' stroke='%23FFFFFF' stroke-width='2'/>" &
    "<circle cx='228' cy='" & FORMAT(EndYValue, "0.0") & "' r='5' fill='" & TrendColor & "' stroke='%23FFFFFF' stroke-width='2'/>" &
    "<rect x='16' y='94' width='98' height='34' rx='8' fill='%23FFFFFF' opacity='0.64'/>" &
    "<rect x='122' y='94' width='110' height='34' rx='8' fill='%23FFFFFF' opacity='0.64'/>" &
    "<text x='24' y='108' font-family='Segoe UI' font-size='11' font-weight='750' fill='%23211A32'>PY</text>" &
    "<text x='24' y='123' font-family='Segoe UI' font-size='12' fill='%236E667B'>" & PYText & "</text>" &
    "<text x='132' y='108' font-family='Segoe UI' font-size='11' font-weight='750' fill='%23211A32'>YoY</text>" &
    "<polygon points='134,114 140,124 128,124' fill='" & YoYColor & "'/>" &
    "<text x='148' y='123' font-family='Segoe UI' font-size='12' font-weight='750' fill='" & YoYColor & "'>" & YoYText & "</text>" &
    "</svg>"
RETURN IF(RowCount = 0, BLANK(), "data:image/svg+xml;utf8," & SVG)
```

Format: `text/image`

## Headroom KPI Card SVG

```DAX
Headroom KPI Card SVG = VAR LatestMonth = MAXX(CALCULATETABLE(VALUES(DimDate[MonthStart]), ALLSELECTED(DimDate), REMOVEFILTERS(DimDate[IsLatestCompleteMonth])), DimDate[MonthStart])
VAR PriorMonth = EDATE(LatestMonth, -12)
VAR CurrentValue = CALCULATE([Leverage Headroom], FILTER(ALL(DimDate), DimDate[MonthStart] = LatestMonth))
VAR PriorValue = CALCULATE([Leverage Headroom], FILTER(ALL(DimDate), DimDate[MonthStart] = PriorMonth))
VAR ChangeValue = CurrentValue - PriorValue
VAR ValueTextRaw = FORMAT(DIVIDE(CurrentValue, 1), "0.0x")
VAR PYTextRaw = IF(ISBLANK(PriorValue), "n/a", FORMAT(DIVIDE(PriorValue, 1), "0.0x"))
VAR YoYTextRaw = IF(ISBLANK(CurrentValue) || ISBLANK(PriorValue), "n/a", FORMAT(ChangeValue, "+0.0x;-0.0x;0.0x"))
VAR ValueText = SUBSTITUTE(ValueTextRaw, "%", "%25")
VAR PYText = SUBSTITUTE(PYTextRaw, "%", "%25")
VAR YoYText = SUBSTITUTE(YoYTextRaw, "%", "%25")
VAR YoYColor = IF(ISBLANK(CurrentValue) || ISBLANK(PriorValue), "%236E667B", IF(ChangeValue >= 0, "%234CAF65", "%23C94A4A"))
VAR MonthTable =
    ADDCOLUMNS(
        FILTER(ALLSELECTED(DimDate), DimDate[MonthStart] <= LatestMonth),
        "__Value", [Leverage Headroom]
    )
VAR CleanTable = FILTER(MonthTable, NOT ISBLANK([__Value]))
VAR RowCount = COUNTROWS(CleanTable)
VAR MinValue = MINX(CleanTable, [__Value])
VAR MaxValue = MAXX(CleanTable, [__Value])
VAR FirstValue = MINX(TOPN(1, CleanTable, DimDate[MonthStart], ASC), [__Value])
VAR LastValue = MINX(TOPN(1, CleanTable, DimDate[MonthStart], DESC), [__Value])
VAR LowMonth = MINX(TOPN(1, CleanTable, [__Value], ASC, DimDate[MonthStart], ASC), DimDate[MonthStart])
VAR LowValue = MINX(FILTER(CleanTable, DimDate[MonthStart] = LowMonth), [__Value])
VAR StartYValue = 80 - DIVIDE(FirstValue - MinValue, MaxValue - MinValue, 0.5) * 42
VAR EndYValue = 80 - DIVIDE(LastValue - MinValue, MaxValue - MinValue, 0.5) * 42
VAR LowRank = RANKX(CleanTable, DimDate[MonthStart], LowMonth, ASC, DENSE) - 1
VAR LowXValue = 136 + DIVIDE(LowRank, MAX(1, RowCount - 1), 0) * 92
VAR LowYValue = 80 - DIVIDE(LowValue - MinValue, MaxValue - MinValue, 0.5) * 42
VAR TrendColor = IF(LastValue >= FirstValue, "%230F9F95", "%23C94A4A")
VAR BandColor = IF(LastValue >= FirstValue, "%23DDEEDC", "%23F3D7D7")
VAR LinePoints =
    CONCATENATEX(
        CleanTable,
        VAR RankValue = RANKX(CleanTable, DimDate[MonthStart], , ASC, DENSE) - 1
        VAR XValue = 136 + DIVIDE(RankValue, MAX(1, RowCount - 1), 0) * 92
        VAR YValue = 80 - DIVIDE([__Value] - MinValue, MaxValue - MinValue, 0.5) * 42
        RETURN FORMAT(XValue, "0.0") & "," & FORMAT(YValue, "0.0"),
        " ",
        DimDate[MonthStart],
        ASC
    )
VAR AreaPath =
    "M136 84 " &
    CONCATENATEX(
        CleanTable,
        VAR RankValue = RANKX(CleanTable, DimDate[MonthStart], , ASC, DENSE) - 1
        VAR XValue = 136 + DIVIDE(RankValue, MAX(1, RowCount - 1), 0) * 92
        VAR YValue = 80 - DIVIDE([__Value] - MinValue, MaxValue - MinValue, 0.5) * 42
        RETURN "L" & FORMAT(XValue, "0.0") & " " & FORMAT(YValue, "0.0"),
        " ",
        DimDate[MonthStart],
        ASC
    ) & " L228 84 Z"
VAR SVG =
    "<svg xmlns='http://www.w3.org/2000/svg' width='240' height='132' viewBox='0 0 248 140'>" &
    "<rect x='5' y='5' width='238' height='130' rx='14' fill='%23F4EFFA' stroke='%237142A4' stroke-width='2.5'/>" &
    "<rect x='18' y='13' width='212' height='4' rx='2' fill='%230F9F95' opacity='0.9'/>" &
    "<rect x='18' y='29' width='12' height='12' rx='3' fill='%230F9F95' opacity='0.95'/>" &
    "<circle cx='24' cy='35' r='2' fill='%23FFFFFF' opacity='0.85'/>" &
    "<text x='36' y='39' font-family='Segoe UI' font-size='14' font-weight='750' fill='%23211A32'>Headroom</text>" &
    "<text x='18' y='80' font-family='Segoe UI' font-size='27' font-weight='750' fill='%230F9F95'>" & ValueText & "</text>" &
    "<rect x='130' y='34' width='104' height='54' rx='8' fill='%23FFFFFF' opacity='0.46'/>" &
    "<rect x='136' y='59' width='92' height='12' rx='6' fill='" & BandColor & "'/>" &
    "<rect x='141' y='52' width='12' height='26' rx='2' fill='%23D9D1EB' opacity='0.34'/>" &
    "<rect x='160' y='48' width='12' height='30' rx='2' fill='%23D9D1EB' opacity='0.28'/>" &
    "<rect x='179' y='44' width='12' height='34' rx='2' fill='%23D9D1EB' opacity='0.24'/>" &
    "<rect x='198' y='40' width='12' height='38' rx='2' fill='%23D9D1EB' opacity='0.20'/>" &
    "<line x1='136' y1='65' x2='228' y2='65' stroke='%23B8AECF' stroke-width='1' stroke-dasharray='4 5'/>" &
    "<path d='" & AreaPath & "' fill='%23B8AEE6' opacity='0.55'/>" &
    "<polyline points='" & LinePoints & "' fill='none' stroke='" & TrendColor & "' stroke-width='3' stroke-linecap='round' stroke-linejoin='round'/>" &
    "<circle cx='136' cy='" & FORMAT(StartYValue, "0.0") & "' r='4' fill='%23FFFFFF' stroke='%2377A4F5' stroke-width='2'/>" &
    "<circle cx='" & FORMAT(LowXValue, "0.0") & "' cy='" & FORMAT(LowYValue, "0.0") & "' r='4' fill='%23D96A5D' stroke='%23FFFFFF' stroke-width='2'/>" &
    "<circle cx='228' cy='" & FORMAT(EndYValue, "0.0") & "' r='5' fill='" & TrendColor & "' stroke='%23FFFFFF' stroke-width='2'/>" &
    "<rect x='16' y='94' width='98' height='34' rx='8' fill='%23FFFFFF' opacity='0.64'/>" &
    "<rect x='122' y='94' width='110' height='34' rx='8' fill='%23FFFFFF' opacity='0.64'/>" &
    "<text x='24' y='108' font-family='Segoe UI' font-size='11' font-weight='750' fill='%23211A32'>PY</text>" &
    "<text x='24' y='123' font-family='Segoe UI' font-size='12' fill='%236E667B'>" & PYText & "</text>" &
    "<text x='132' y='108' font-family='Segoe UI' font-size='11' font-weight='750' fill='%23211A32'>YoY</text>" &
    "<polygon points='134,114 140,124 128,124' fill='" & YoYColor & "'/>" &
    "<text x='148' y='123' font-family='Segoe UI' font-size='12' font-weight='750' fill='" & YoYColor & "'>" & YoYText & "</text>" &
    "</svg>"
RETURN IF(RowCount = 0, BLANK(), "data:image/svg+xml;utf8," & SVG)
```

Format: `text/image`

## Risk KPI Card SVG

```DAX
Risk KPI Card SVG = VAR LatestMonth = MAXX(CALCULATETABLE(VALUES(DimDate[MonthStart]), ALLSELECTED(DimDate), REMOVEFILTERS(DimDate[IsLatestCompleteMonth])), DimDate[MonthStart])
VAR PriorMonth = EDATE(LatestMonth, -12)
VAR CurrentValue = CALCULATE([Risk Exposure], FILTER(ALL(DimDate), DimDate[MonthStart] = LatestMonth))
VAR PriorValue = CALCULATE([Risk Exposure], FILTER(ALL(DimDate), DimDate[MonthStart] = PriorMonth))
VAR ChangeValue = CurrentValue - PriorValue
VAR ValueTextRaw = FORMAT(DIVIDE(CurrentValue, 1000000), "$#,0M;($#,0M);$0M")
VAR PYTextRaw = IF(ISBLANK(PriorValue), "n/a", FORMAT(DIVIDE(PriorValue, 1000000), "$#,0M;($#,0M);$0M"))
VAR RateValue = DIVIDE(ChangeValue, ABS(PriorValue))
VAR YoYTextRaw = IF(ISBLANK(CurrentValue) || ISBLANK(PriorValue), "n/a", FORMAT(RateValue, "+0.0%;-0.0%;0.0%"))
VAR ValueText = SUBSTITUTE(ValueTextRaw, "%", "%25")
VAR PYText = SUBSTITUTE(PYTextRaw, "%", "%25")
VAR YoYText = SUBSTITUTE(YoYTextRaw, "%", "%25")
VAR YoYColor = IF(ISBLANK(CurrentValue) || ISBLANK(PriorValue), "%236E667B", IF(ChangeValue <= 0, "%234CAF65", "%23C94A4A"))
VAR MonthTable =
    ADDCOLUMNS(
        FILTER(ALLSELECTED(DimDate), DimDate[MonthStart] <= LatestMonth),
        "__Value", [Risk Exposure]
    )
VAR CleanTable = FILTER(MonthTable, NOT ISBLANK([__Value]))
VAR RowCount = COUNTROWS(CleanTable)
VAR MinValue = MINX(CleanTable, [__Value])
VAR MaxValue = MAXX(CleanTable, [__Value])
VAR FirstValue = MINX(TOPN(1, CleanTable, DimDate[MonthStart], ASC), [__Value])
VAR LastValue = MINX(TOPN(1, CleanTable, DimDate[MonthStart], DESC), [__Value])
VAR LowMonth = MINX(TOPN(1, CleanTable, [__Value], ASC, DimDate[MonthStart], ASC), DimDate[MonthStart])
VAR LowValue = MINX(FILTER(CleanTable, DimDate[MonthStart] = LowMonth), [__Value])
VAR StartYValue = 80 - DIVIDE(FirstValue - MinValue, MaxValue - MinValue, 0.5) * 42
VAR EndYValue = 80 - DIVIDE(LastValue - MinValue, MaxValue - MinValue, 0.5) * 42
VAR LowRank = RANKX(CleanTable, DimDate[MonthStart], LowMonth, ASC, DENSE) - 1
VAR LowXValue = 136 + DIVIDE(LowRank, MAX(1, RowCount - 1), 0) * 92
VAR LowYValue = 80 - DIVIDE(LowValue - MinValue, MaxValue - MinValue, 0.5) * 42
VAR TrendColor = IF(LastValue <= FirstValue, "%23B73535", "%23C94A4A")
VAR BandColor = IF(LastValue <= FirstValue, "%23DDEEDC", "%23F3D7D7")
VAR LinePoints =
    CONCATENATEX(
        CleanTable,
        VAR RankValue = RANKX(CleanTable, DimDate[MonthStart], , ASC, DENSE) - 1
        VAR XValue = 136 + DIVIDE(RankValue, MAX(1, RowCount - 1), 0) * 92
        VAR YValue = 80 - DIVIDE([__Value] - MinValue, MaxValue - MinValue, 0.5) * 42
        RETURN FORMAT(XValue, "0.0") & "," & FORMAT(YValue, "0.0"),
        " ",
        DimDate[MonthStart],
        ASC
    )
VAR AreaPath =
    "M136 84 " &
    CONCATENATEX(
        CleanTable,
        VAR RankValue = RANKX(CleanTable, DimDate[MonthStart], , ASC, DENSE) - 1
        VAR XValue = 136 + DIVIDE(RankValue, MAX(1, RowCount - 1), 0) * 92
        VAR YValue = 80 - DIVIDE([__Value] - MinValue, MaxValue - MinValue, 0.5) * 42
        RETURN "L" & FORMAT(XValue, "0.0") & " " & FORMAT(YValue, "0.0"),
        " ",
        DimDate[MonthStart],
        ASC
    ) & " L228 84 Z"
VAR SVG =
    "<svg xmlns='http://www.w3.org/2000/svg' width='240' height='132' viewBox='0 0 248 140'>" &
    "<rect x='5' y='5' width='238' height='130' rx='14' fill='%23F4EFFA' stroke='%237142A4' stroke-width='2.5'/>" &
    "<rect x='18' y='13' width='212' height='4' rx='2' fill='%23B73535' opacity='0.9'/>" &
    "<rect x='18' y='29' width='12' height='12' rx='3' fill='%23B73535' opacity='0.95'/>" &
    "<circle cx='24' cy='35' r='2' fill='%23FFFFFF' opacity='0.85'/>" &
    "<text x='36' y='39' font-family='Segoe UI' font-size='14' font-weight='750' fill='%23211A32'>Risk</text>" &
    "<text x='18' y='80' font-family='Segoe UI' font-size='27' font-weight='750' fill='%23B73535'>" & ValueText & "</text>" &
    "<rect x='130' y='34' width='104' height='54' rx='8' fill='%23FFFFFF' opacity='0.46'/>" &
    "<rect x='136' y='59' width='92' height='12' rx='6' fill='" & BandColor & "'/>" &
    "<rect x='141' y='52' width='12' height='26' rx='2' fill='%23D9D1EB' opacity='0.34'/>" &
    "<rect x='160' y='48' width='12' height='30' rx='2' fill='%23D9D1EB' opacity='0.28'/>" &
    "<rect x='179' y='44' width='12' height='34' rx='2' fill='%23D9D1EB' opacity='0.24'/>" &
    "<rect x='198' y='40' width='12' height='38' rx='2' fill='%23D9D1EB' opacity='0.20'/>" &
    "<line x1='136' y1='65' x2='228' y2='65' stroke='%23B8AECF' stroke-width='1' stroke-dasharray='4 5'/>" &
    "<path d='" & AreaPath & "' fill='%23B8AEE6' opacity='0.55'/>" &
    "<polyline points='" & LinePoints & "' fill='none' stroke='" & TrendColor & "' stroke-width='3' stroke-linecap='round' stroke-linejoin='round'/>" &
    "<circle cx='136' cy='" & FORMAT(StartYValue, "0.0") & "' r='4' fill='%23FFFFFF' stroke='%2377A4F5' stroke-width='2'/>" &
    "<circle cx='" & FORMAT(LowXValue, "0.0") & "' cy='" & FORMAT(LowYValue, "0.0") & "' r='4' fill='%23D96A5D' stroke='%23FFFFFF' stroke-width='2'/>" &
    "<circle cx='228' cy='" & FORMAT(EndYValue, "0.0") & "' r='5' fill='" & TrendColor & "' stroke='%23FFFFFF' stroke-width='2'/>" &
    "<rect x='16' y='94' width='98' height='34' rx='8' fill='%23FFFFFF' opacity='0.64'/>" &
    "<rect x='122' y='94' width='110' height='34' rx='8' fill='%23FFFFFF' opacity='0.64'/>" &
    "<text x='24' y='108' font-family='Segoe UI' font-size='11' font-weight='750' fill='%23211A32'>PY</text>" &
    "<text x='24' y='123' font-family='Segoe UI' font-size='12' fill='%236E667B'>" & PYText & "</text>" &
    "<text x='132' y='108' font-family='Segoe UI' font-size='11' font-weight='750' fill='%23211A32'>YoY</text>" &
    "<polygon points='134,114 140,124 128,124' fill='" & YoYColor & "'/>" &
    "<text x='148' y='123' font-family='Segoe UI' font-size='12' font-weight='750' fill='" & YoYColor & "'>" & YoYText & "</text>" &
    "</svg>"
RETURN IF(RowCount = 0, BLANK(), "data:image/svg+xml;utf8," & SVG)
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

## Lens Summary SVG

```DAX
Lens Summary SVG = VAR YearText =
    IF(HASONEVALUE(DimDate[Year]), FORMAT(SELECTEDVALUE(DimDate[Year]), "0"), "All Years")
VAR ScenarioText =
    IF(HASONEVALUE(DimScenario[ScenarioName]), SELECTEDVALUE(DimScenario[ScenarioName]), FORMAT(COUNTROWS(VALUES(DimScenario[ScenarioName])), "0") & " scenarios")
VAR BUCount = COUNTROWS(VALUES(DimBusinessUnit[BusinessUnit]))
VAR BUTotal = CALCULATE(COUNTROWS(VALUES(DimBusinessUnit[BusinessUnit])), ALL(DimBusinessUnit[BusinessUnit]))
VAR BUText =
    IF(NOT ISFILTERED(DimBusinessUnit[BusinessUnit]) || BUCount = BUTotal,
        "All BU",
        IF(BUCount = 1, SELECTEDVALUE(DimBusinessUnit[BusinessUnit]), FORMAT(BUCount, "0") & " BU"))
VAR RegionCount = COUNTROWS(VALUES(DimRegion[Region]))
VAR RegionTotal = CALCULATE(COUNTROWS(VALUES(DimRegion[Region])), ALL(DimRegion[Region]))
VAR RegionText =
    IF(NOT ISFILTERED(DimRegion[Region]) || RegionCount = RegionTotal,
        "All Regions",
        IF(RegionCount = 1, SELECTEDVALUE(DimRegion[Region]), FORMAT(RegionCount, "0") & " Regions"))
VAR Line1 = LEFT(YearText & " | " & ScenarioText, 23)
VAR Line2 = LEFT(BUText & " | " & RegionText, 25)
VAR SVG =
    "<svg xmlns='http://www.w3.org/2000/svg' width='142' height='42' viewBox='0 0 142 42'>" &
    "<rect x='0.5' y='0.5' width='141' height='41' rx='6' fill='%233F1A63' stroke='%238E73E7' stroke-width='1'/>" &
    "<text x='9' y='14' font-family='Segoe UI' font-size='9' font-weight='700' fill='%23CFC3E6'>Current Lens</text>" &
    "<circle cx='123' cy='11' r='3' fill='%236EE4CF'/>" &
    "<text x='9' y='27' font-family='Segoe UI' font-size='10' font-weight='700' fill='%23FFFFFF'>" & Line1 & "</text>" &
    "<text x='9' y='38' font-family='Segoe UI' font-size='8.5' fill='%23CFC3E6'>" & Line2 & "</text>" &
    "</svg>"
RETURN "data:image/svg+xml;utf8," & SVG
```

Format: `text/image`

## Performance Decision Chips SVG

```DAX
Performance Decision Chips SVG = VAR ScenarioID = SELECTEDVALUE(DimScenario[ScenarioID], "Base")
VAR Chip1Text = "Scenario: " & SWITCH(ScenarioID, "Upside", "Upside", "Downside", "Downside", "Base")
VAR Chip2Text = SWITCH(ScenarioID, "Upside", "GM: +1.4 pts", "Downside", "GM: -0.7 pts", "GM: +0.8 pts")
VAR Chip3Text = SWITCH(ScenarioID, "Upside", "Runway: >99 mo", "Downside", "Runway: 18.5 mo", "Runway: >99 mo")
VAR Chip1Accent = SWITCH(ScenarioID, "Upside", "%230F9F95", "Downside", "%23BE7C10", "%232FA66A")
VAR Chip1Fill = SWITCH(ScenarioID, "Upside", "%23EAF7FF", "Downside", "%23FFF3D6", "%23E6F4EC")
VAR Chip2Accent = SWITCH(ScenarioID, "Downside", "%23B73535", "%230F9F95")
VAR Chip2Fill = SWITCH(ScenarioID, "Downside", "%23FCE7E7", "%23E7F0FF")
VAR Chip3Accent = SWITCH(ScenarioID, "Downside", "%23BE7C10", "%232FA66A")
VAR Chip3Fill = SWITCH(ScenarioID, "Downside", "%23FFF3D6", "%23E6F4EC")
VAR SVG =
    "<svg xmlns='http://www.w3.org/2000/svg' width='490' height='38' viewBox='0 0 490 38'>" &
    "<rect x='0' y='0' width='490' height='38' rx='8' fill='none'/>" &
    "<rect x='0.5' y='2.5' width='142' height='33' rx='7' fill='" & Chip1Fill & "' stroke='%23FFFFFF' stroke-width='0.9'/>" &
    "<rect x='13' y='13' width='11' height='11' rx='3' fill='" & Chip1Accent & "'/>" &
    "<text x='36' y='23.5' font-family='Segoe UI Semibold' font-size='12.5' fill='%23261C3C'>" & Chip1Text & "</text>" &
    "<rect x='156.5' y='2.5' width='150' height='33' rx='7' fill='" & Chip2Fill & "' stroke='%23FFFFFF' stroke-width='0.9'/>" &
    "<rect x='169' y='13' width='11' height='11' rx='3' fill='" & Chip2Accent & "'/>" &
    "<text x='192' y='23.5' font-family='Segoe UI Semibold' font-size='12.5' fill='%23261C3C'>" & Chip2Text & "</text>" &
    "<rect x='320.5' y='2.5' width='168' height='33' rx='7' fill='" & Chip3Fill & "' stroke='%23FFFFFF' stroke-width='0.9'/>" &
    "<rect x='333' y='13' width='11' height='11' rx='3' fill='" & Chip3Accent & "'/>" &
    "<text x='356' y='23.5' font-family='Segoe UI Semibold' font-size='12.5' fill='%23261C3C'>" & Chip3Text & "</text>" &
    "</svg>"
RETURN "data:image/svg+xml;utf8," & SVG
```

Format: `text/image`

## Cash Decision Chips SVG

```DAX
Cash Decision Chips SVG = VAR ScenarioID = SELECTEDVALUE(DimScenario[ScenarioID], "Base")
VAR Chip1Text = "Scenario: " & SWITCH(ScenarioID, "Upside", "Upside", "Downside", "Downside", "Base")
VAR Chip2Text = SWITCH(ScenarioID, "Upside", "Funding: $0M", "Downside", "Funding: $14M", "Funding: $0M")
VAR Chip3Text = SWITCH(ScenarioID, "Upside", "FCF: $38.0M", "Downside", "FCF: ($8.5M)", "FCF: $22.5M")
VAR Chip1Accent = SWITCH(ScenarioID, "Upside", "%230F9F95", "Downside", "%23BE7C10", "%232FA66A")
VAR Chip1Fill = SWITCH(ScenarioID, "Upside", "%23EAF7FF", "Downside", "%23FFF3D6", "%23E6F4EC")
VAR Chip2Accent = SWITCH(ScenarioID, "Downside", "%23BE7C10", "%232FA66A")
VAR Chip2Fill = SWITCH(ScenarioID, "Downside", "%23FFF3D6", "%23E6F4EC")
VAR Chip3Accent = SWITCH(ScenarioID, "Downside", "%23B73535", "%230F9F95")
VAR Chip3Fill = SWITCH(ScenarioID, "Downside", "%23FCE7E7", "%23E7F0FF")
VAR SVG =
    "<svg xmlns='http://www.w3.org/2000/svg' width='490' height='38' viewBox='0 0 490 38'>" &
    "<rect x='0' y='0' width='490' height='38' rx='8' fill='none'/>" &
    "<rect x='0.5' y='2.5' width='142' height='33' rx='7' fill='" & Chip1Fill & "' stroke='%23FFFFFF' stroke-width='0.9'/>" &
    "<rect x='13' y='13' width='11' height='11' rx='3' fill='" & Chip1Accent & "'/>" &
    "<text x='36' y='23.5' font-family='Segoe UI Semibold' font-size='12.5' fill='%23261C3C'>" & Chip1Text & "</text>" &
    "<rect x='156.5' y='2.5' width='150' height='33' rx='7' fill='" & Chip2Fill & "' stroke='%23FFFFFF' stroke-width='0.9'/>" &
    "<rect x='169' y='13' width='11' height='11' rx='3' fill='" & Chip2Accent & "'/>" &
    "<text x='192' y='23.5' font-family='Segoe UI Semibold' font-size='12.5' fill='%23261C3C'>" & Chip2Text & "</text>" &
    "<rect x='320.5' y='2.5' width='168' height='33' rx='7' fill='" & Chip3Fill & "' stroke='%23FFFFFF' stroke-width='0.9'/>" &
    "<rect x='333' y='13' width='11' height='11' rx='3' fill='" & Chip3Accent & "'/>" &
    "<text x='356' y='23.5' font-family='Segoe UI Semibold' font-size='12.5' fill='%23261C3C'>" & Chip3Text & "</text>" &
    "</svg>"
RETURN "data:image/svg+xml;utf8," & SVG
```

Format: `text/image`

## Risk Decision Chips SVG

```DAX
Risk Decision Chips SVG = VAR ScenarioID = SELECTEDVALUE(DimScenario[ScenarioID], "Base")
VAR Chip1Text = "Scenario: " & SWITCH(ScenarioID, "Upside", "Upside", "Downside", "Downside", "Base")
VAR Chip2Text = SWITCH(ScenarioID, "Upside", "Headroom: 2.1x", "Downside", "Headroom: 0.4x", "Headroom: 1.3x")
VAR Chip3Text = SWITCH(ScenarioID, "Upside", "Risk: $7M", "Downside", "Risk: $26M", "Risk: $14M")
VAR Chip1Accent = SWITCH(ScenarioID, "Upside", "%230F9F95", "Downside", "%23BE7C10", "%232FA66A")
VAR Chip1Fill = SWITCH(ScenarioID, "Upside", "%23EAF7FF", "Downside", "%23FFF3D6", "%23E6F4EC")
VAR Chip2Accent = SWITCH(ScenarioID, "Downside", "%23BE7C10", "%230F9F95")
VAR Chip2Fill = SWITCH(ScenarioID, "Downside", "%23FFF3D6", "%23E7F0FF")
VAR Chip3Accent = SWITCH(ScenarioID, "Downside", "%23B73535", "Upside", "%232FA66A", "%23BE7C10")
VAR Chip3Fill = SWITCH(ScenarioID, "Downside", "%23FCE7E7", "Upside", "%23E6F4EC", "%23FFF3D6")
VAR SVG =
    "<svg xmlns='http://www.w3.org/2000/svg' width='490' height='38' viewBox='0 0 490 38'>" &
    "<rect x='0' y='0' width='490' height='38' rx='8' fill='none'/>" &
    "<rect x='0.5' y='2.5' width='142' height='33' rx='7' fill='" & Chip1Fill & "' stroke='%23FFFFFF' stroke-width='0.9'/>" &
    "<rect x='13' y='13' width='11' height='11' rx='3' fill='" & Chip1Accent & "'/>" &
    "<text x='36' y='23.5' font-family='Segoe UI Semibold' font-size='12.5' fill='%23261C3C'>" & Chip1Text & "</text>" &
    "<rect x='156.5' y='2.5' width='150' height='33' rx='7' fill='" & Chip2Fill & "' stroke='%23FFFFFF' stroke-width='0.9'/>" &
    "<rect x='169' y='13' width='11' height='11' rx='3' fill='" & Chip2Accent & "'/>" &
    "<text x='192' y='23.5' font-family='Segoe UI Semibold' font-size='12.5' fill='%23261C3C'>" & Chip2Text & "</text>" &
    "<rect x='320.5' y='2.5' width='168' height='33' rx='7' fill='" & Chip3Fill & "' stroke='%23FFFFFF' stroke-width='0.9'/>" &
    "<rect x='333' y='13' width='11' height='11' rx='3' fill='" & Chip3Accent & "'/>" &
    "<text x='356' y='23.5' font-family='Segoe UI Semibold' font-size='12.5' fill='%23261C3C'>" & Chip3Text & "</text>" &
    "</svg>"
RETURN "data:image/svg+xml;utf8," & SVG
```

Format: `text/image`
