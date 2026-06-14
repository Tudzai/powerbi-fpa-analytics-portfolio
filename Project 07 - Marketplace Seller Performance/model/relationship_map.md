# Relationship Map

| From Table | From Column | To Table | To Column | Cardinality | Cross Filter |
|---|---|---|---|---|---|
| fact_order_items | order_date | dim_date | date | Many-to-one | Single |
| fact_order_items | platform_id | dim_platform | platform_id | Many-to-one | Single |
| fact_order_items | seller_id | dim_seller | seller_id | Many-to-one | Single |
| fact_order_items | sku_id | dim_product | sku_id | Many-to-one | Single |
| fact_order_items | category_id | dim_category | category_id | Many-to-one | Single |
| fact_fulfillment | order_item_id | fact_order_items | order_item_id | One-to-one | Single |
| fact_inventory_snapshot | snapshot_date | dim_date | date | Many-to-one | Single |
| fact_inventory_snapshot | seller_id | dim_seller | seller_id | Many-to-one | Single |
| fact_inventory_snapshot | sku_id | dim_product | sku_id | Many-to-one | Single |
| fact_reviews | review_date | dim_date | date | Many-to-one | Single |
| fact_reviews | seller_id | dim_seller | seller_id | Many-to-one | Single |
| fact_seller_targets | seller_id | dim_seller | seller_id | Many-to-one | Single |
| fact_ads_spend | seller_id | dim_seller | seller_id | Many-to-one | Single |
