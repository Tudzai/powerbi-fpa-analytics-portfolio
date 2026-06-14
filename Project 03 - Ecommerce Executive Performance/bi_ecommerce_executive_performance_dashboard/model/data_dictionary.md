## dim_date

| Column | Type | Description |
|---|---|---|
| `date` | `str` | dim_date field used for ecommerce executive reporting. |
| `year` | `int64` | dim_date field used for ecommerce executive reporting. |
| `quarter` | `str` | dim_date field used for ecommerce executive reporting. |
| `month_number` | `int64` | dim_date field used for ecommerce executive reporting. |
| `month_name` | `str` | dim_date field used for ecommerce executive reporting. |
| `year_month` | `str` | dim_date field used for ecommerce executive reporting. |
| `week_start` | `str` | dim_date field used for ecommerce executive reporting. |
| `day_of_week` | `str` | dim_date field used for ecommerce executive reporting. |
| `is_weekend` | `str` | dim_date field used for ecommerce executive reporting. |

## dim_product

| Column | Type | Description |
|---|---|---|
| `product_id` | `str` | dim_product field used for ecommerce executive reporting. |
| `product_name` | `str` | dim_product field used for ecommerce executive reporting. |
| `category` | `str` | Product category. |
| `subcategory` | `str` | dim_product field used for ecommerce executive reporting. |
| `brand` | `str` | dim_product field used for ecommerce executive reporting. |
| `base_price` | `float64` | dim_product field used for ecommerce executive reporting. |
| `unit_cost` | `float64` | dim_product field used for ecommerce executive reporting. |
| `launch_date` | `str` | dim_product field used for ecommerce executive reporting. |
| `active_flag` | `str` | dim_product field used for ecommerce executive reporting. |

## dim_customer

| Column | Type | Description |
|---|---|---|
| `customer_id` | `str` | dim_customer field used for ecommerce executive reporting. |
| `signup_date` | `str` | dim_customer field used for ecommerce executive reporting. |
| `customer_segment` | `str` | dim_customer field used for ecommerce executive reporting. |
| `region` | `str` | dim_customer field used for ecommerce executive reporting. |
| `country` | `str` | dim_customer field used for ecommerce executive reporting. |
| `marketing_opt_in` | `str` | dim_customer field used for ecommerce executive reporting. |

## dim_region

| Column | Type | Description |
|---|---|---|
| `region` | `str` | dim_region field used for ecommerce executive reporting. |
| `country` | `str` | dim_region field used for ecommerce executive reporting. |

## dim_channel

| Column | Type | Description |
|---|---|---|
| `channel` | `str` | Traffic acquisition channel. |
| `channel_type` | `str` | dim_channel field used for ecommerce executive reporting. |
| `default_conversion_rate` | `float64` | dim_channel field used for ecommerce executive reporting. |

## dim_device

| Column | Type | Description |
|---|---|---|
| `device` | `str` | dim_device field used for ecommerce executive reporting. |

## fact_orders

| Column | Type | Description |
|---|---|---|
| `order_key` | `int64` | fact_orders field used for ecommerce executive reporting. |
| `order_id` | `str` | Business order identifier. |
| `order_date` | `str` | Date when the order was placed. |
| `customer_id` | `str` | fact_orders field used for ecommerce executive reporting. |
| `product_id` | `str` | fact_orders field used for ecommerce executive reporting. |
| `category` | `str` | Product category. |
| `subcategory` | `str` | fact_orders field used for ecommerce executive reporting. |
| `region` | `str` | fact_orders field used for ecommerce executive reporting. |
| `channel` | `str` | Traffic acquisition channel. |
| `device` | `str` | fact_orders field used for ecommerce executive reporting. |
| `customer_segment` | `str` | fact_orders field used for ecommerce executive reporting. |
| `customer_home_region` | `str` | fact_orders field used for ecommerce executive reporting. |
| `status` | `str` | Order lifecycle status. |
| `quantity` | `int64` | fact_orders field used for ecommerce executive reporting. |
| `unit_price` | `float64` | fact_orders field used for ecommerce executive reporting. |
| `discount_amount` | `float64` | fact_orders field used for ecommerce executive reporting. |
| `shipping_fee` | `float64` | fact_orders field used for ecommerce executive reporting. |
| `tax_amount` | `float64` | fact_orders field used for ecommerce executive reporting. |
| `gmv` | `float64` | Gross merchandise value before refund and cancellation impact. |
| `net_revenue` | `float64` | Revenue recognized for completed orders after discount plus shipping. |
| `refund_amount` | `float64` | fact_orders field used for ecommerce executive reporting. |
| `contribution_margin` | `float64` | fact_orders field used for ecommerce executive reporting. |
| `payment_method` | `str` | fact_orders field used for ecommerce executive reporting. |
| `is_first_order` | `str` | fact_orders field used for ecommerce executive reporting. |
| `order_month` | `str` | fact_orders field used for ecommerce executive reporting. |
| `completed_order_flag` | `int64` | fact_orders field used for ecommerce executive reporting. |
| `refund_order_flag` | `int64` | fact_orders field used for ecommerce executive reporting. |
| `cancel_order_flag` | `int64` | fact_orders field used for ecommerce executive reporting. |

## fact_sessions

| Column | Type | Description |
|---|---|---|
| `session_key` | `int64` | fact_sessions field used for ecommerce executive reporting. |
| `session_date` | `str` | Date of web/app traffic activity. |
| `channel` | `str` | Traffic acquisition channel. |
| `device` | `str` | fact_sessions field used for ecommerce executive reporting. |
| `region` | `str` | fact_sessions field used for ecommerce executive reporting. |
| `sessions` | `int64` | Total sessions in the grain. |
| `visitors` | `int64` | Estimated unique visitors in the grain. |
| `add_to_cart` | `int64` | fact_sessions field used for ecommerce executive reporting. |
| `checkout_starts` | `int64` | fact_sessions field used for ecommerce executive reporting. |
| `session_month` | `str` | fact_sessions field used for ecommerce executive reporting. |

## fact_marketing_spend

| Column | Type | Description |
|---|---|---|
| `month` | `str` | fact_marketing_spend field used for ecommerce executive reporting. |
| `channel` | `str` | Traffic acquisition channel. |
| `spend` | `float64` | Marketing spend for month and channel. |
| `impressions` | `int64` | fact_marketing_spend field used for ecommerce executive reporting. |
| `clicks` | `int64` | fact_marketing_spend field used for ecommerce executive reporting. |
