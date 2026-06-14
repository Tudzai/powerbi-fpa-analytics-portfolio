# DAX Measures

```DAX
Visits =
DISTINCTCOUNT ( fact_sessions[session_id] )

Product View Sessions =
CALCULATE ( [Visits], fact_sessions[product_view_flag] = 1 )

Add to Cart Sessions =
CALCULATE ( [Visits], fact_sessions[add_to_cart_flag] = 1 )

Checkout Sessions =
CALCULATE ( [Visits], fact_sessions[checkout_flag] = 1 )

Purchase Sessions =
CALCULATE ( [Visits], fact_sessions[purchase_flag] = 1 )

Orders =
DISTINCTCOUNT ( fact_orders[order_id] )

Revenue =
SUM ( fact_orders[net_revenue] )

Gross Revenue =
SUM ( fact_orders[gross_revenue] )

Refund Amount =
SUM ( fact_orders[refund_amount] )

AOV =
DIVIDE ( [Revenue], [Orders] )

Product View Rate =
DIVIDE ( [Product View Sessions], [Visits] )

Add to Cart Rate =
DIVIDE ( [Add to Cart Sessions], [Product View Sessions] )

Checkout Start Rate =
DIVIDE ( [Checkout Sessions], [Add to Cart Sessions] )

Purchase Completion Rate =
DIVIDE ( [Purchase Sessions], [Checkout Sessions] )

Overall Conversion Rate =
DIVIDE ( [Purchase Sessions], [Visits] )

Visit to Product View Drop-off =
[Visits] - [Product View Sessions]

Product View to Cart Drop-off =
[Product View Sessions] - [Add to Cart Sessions]

Cart to Checkout Drop-off =
[Add to Cart Sessions] - [Checkout Sessions]

Checkout to Purchase Drop-off =
[Checkout Sessions] - [Purchase Sessions]

Checkout Abandonment Rate =
DIVIDE ( [Checkout Sessions] - [Purchase Sessions], [Checkout Sessions] )

Cart to Purchase Rate =
DIVIDE ( [Purchase Sessions], [Add to Cart Sessions] )

Stage Sessions =
SUM ( fact_stage_sessions[sessions] )

Previous Stage Sessions =
SUM ( fact_stage_transition[previous_stage_sessions] )

Current Stage Sessions =
SUM ( fact_stage_transition[current_stage_sessions] )

Drop-off Sessions =
SUM ( fact_stage_transition[dropoff_sessions] )

Step Conversion Rate =
DIVIDE ( [Current Stage Sessions], [Previous Stage Sessions] )

Marketing Spend =
SUM ( fact_marketing_spend[spend] )

ROAS =
DIVIDE ( [Revenue], [Marketing Spend] )

CAC =
DIVIDE ( [Marketing Spend], [Purchase Sessions] )

Revenue per Visit =
DIVIDE ( [Revenue], [Visits] )
```
