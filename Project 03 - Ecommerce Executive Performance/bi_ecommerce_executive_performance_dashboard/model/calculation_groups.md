# Calculation Groups

Optional calculation group for production model:

| Calculation Item | Expression Pattern |
|---|---|
| Current | `SELECTEDMEASURE()` |
| Previous Year | `CALCULATE(SELECTEDMEASURE(), SAMEPERIODLASTYEAR(dim_date[date]))` |
| YoY Delta | `SELECTEDMEASURE() - CALCULATE(SELECTEDMEASURE(), SAMEPERIODLASTYEAR(dim_date[date]))` |
| YoY % | `DIVIDE([YoY Delta], CALCULATE(SELECTEDMEASURE(), SAMEPERIODLASTYEAR(dim_date[date])))` |

This is documented but not required for the manual PBIX build.
