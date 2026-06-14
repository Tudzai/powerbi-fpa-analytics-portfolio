# Data Dictionary

## Fact Tables

- `fact_order_items`: order item grain for GMV, cancellation, return, commission, seller and category ranking.
- `fact_fulfillment`: one row per order item with SLA and late fulfillment flags.
- `fact_inventory_snapshot`: one row per seller-SKU-day for stock availability.
- `fact_reviews`: one row per review for weighted seller rating.
- `fact_seller_targets`: monthly seller targets.
- `fact_ads_spend`: monthly seller ads and voucher cost.

## Dimensions

- `dim_date`: reporting date dimension.
- `dim_platform`: Shopee, Lazada, Tiki.
- `dim_seller`: seller profile, tier, lifecycle, region, account manager.
- `dim_product`: SKU, category, seller, platform.
- `dim_category`: product categories.
