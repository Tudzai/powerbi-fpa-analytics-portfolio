# DAX Measures

```DAX
GMV = SUM ( fact_orders[gmv] )

Net Revenue = SUM ( fact_orders[net_revenue] )

Orders = DISTINCTCOUNT ( fact_orders[order_id] )

Completed Orders =
CALCULATE (
    [Orders],
    fact_orders[status] = "Completed"
)

Refunded Orders =
CALCULATE (
    [Orders],
    fact_orders[status] = "Refunded"
)

Cancelled Orders =
CALCULATE (
    [Orders],
    fact_orders[status] = "Cancelled"
)

AOV = DIVIDE ( [GMV], [Orders] )

Sessions = SUM ( fact_sessions[sessions] )

Visitors = SUM ( fact_sessions[visitors] )

Conversion Rate = DIVIDE ( [Orders], [Sessions] )

Refund/Cancel Rate =
DIVIDE ( [Refunded Orders] + [Cancelled Orders], [Orders] )

Marketing Spend = SUM ( fact_marketing_spend[spend] )

ROAS = DIVIDE ( [Net Revenue], [Marketing Spend] )

Contribution Margin = SUM ( fact_orders[contribution_margin] )

Contribution Margin % = DIVIDE ( [Contribution Margin], [Net Revenue] )

Top Category =
VAR t =
    TOPN (
        1,
        SUMMARIZE ( dim_product, dim_product[category], "GMVValue", [GMV] ),
        [GMVValue],
        DESC
    )
RETURN
    CONCATENATEX ( t, dim_product[category], ", " )

Top Traffic Channel =
VAR t =
    TOPN (
        1,
        SUMMARIZE ( dim_channel, dim_channel[channel], "GMVValue", [GMV] ),
        [GMVValue],
        DESC
    )
RETURN
    CONCATENATEX ( t, dim_channel[channel], ", " )

GMV PY =
CALCULATE ( [GMV], SAMEPERIODLASTYEAR ( dim_date[date] ) )

GMV YoY % = DIVIDE ( [GMV] - [GMV PY], [GMV PY] )

Net Revenue PY =
CALCULATE ( [Net Revenue], SAMEPERIODLASTYEAR ( dim_date[date] ) )

Net Revenue YoY % = DIVIDE ( [Net Revenue] - [Net Revenue PY], [Net Revenue PY] )
```
