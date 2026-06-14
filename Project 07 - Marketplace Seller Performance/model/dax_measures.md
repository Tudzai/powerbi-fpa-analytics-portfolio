# DAX Measures

```DAX
Seller GMV := SUM ( fact_order_items[seller_gmv_net] )
Gross GMV := SUM ( fact_order_items[gross_gmv] )
Commission Revenue := SUM ( fact_order_items[commission_revenue] )
Orders := DISTINCTCOUNT ( fact_order_items[order_id] )
Order Items := DISTINCTCOUNT ( fact_order_items[order_item_id] )

Cancelled Items :=
CALCULATE (
    DISTINCTCOUNT ( fact_order_items[order_item_id] ),
    fact_order_items[order_status] = "cancelled"
)

Cancellation Rate := DIVIDE ( [Cancelled Items], [Order Items] )

Eligible Fulfillment Items :=
CALCULATE (
    DISTINCTCOUNT ( fact_order_items[order_item_id] ),
    fact_order_items[is_eligible_for_fulfillment] = 1
)

Fulfilled Items := SUM ( fact_fulfillment[fulfilled_flag] )
Fulfillment Rate := DIVIDE ( [Fulfilled Items], [Eligible Fulfillment Items] )
Late Fulfillment Rate := DIVIDE ( SUM ( fact_fulfillment[late_fulfillment_flag] ), [Eligible Fulfillment Items] )

Average Rating :=
DIVIDE (
    SUMX ( fact_reviews, fact_reviews[rating] * fact_reviews[review_weight] ),
    SUM ( fact_reviews[review_weight] )
)

Rating Count := DISTINCTCOUNT ( fact_reviews[review_id] )

Stock Availability :=
DIVIDE (
    SUM ( fact_inventory_snapshot[in_stock_sku_days] ),
    SUM ( fact_inventory_snapshot[sku_day_count] )
)

Seller GMV Target := SUM ( fact_seller_targets[seller_gmv_target] )
GMV Target Attainment := DIVIDE ( [Seller GMV], [Seller GMV Target] )

Seller Rank by GMV :=
RANKX ( ALLSELECTED ( dim_seller[seller_id] ), [Seller GMV], , DESC, Dense )

Seller Performance Score :=
VAR RatingScore = DIVIDE ( [Average Rating], 5 )
VAR FulfillmentScore = [Fulfillment Rate]
VAR CancellationScore = 1 - [Cancellation Rate]
VAR StockScore = [Stock Availability]
VAR GMVRankPct =
    DIVIDE ( [Seller Rank by GMV], COUNTROWS ( ALLSELECTED ( dim_seller[seller_id] ) ) )
RETURN
    0.40 * ( 1 - GMVRankPct )
        + 0.25 * FulfillmentScore
        + 0.20 * CancellationScore
        + 0.10 * RatingScore
        + 0.05 * StockScore
```
