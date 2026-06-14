# Data Quality Report

| Check | Expected/Raw | Actual/Prepared | Status |
| --- | --- | --- | --- |
| Order item primary key unique | 90000 | 90000 | PASS |
| Inventory seller-SKU-day key unique | 667704 | 667704 | PASS |
| Seller GMV reconciles | 3300792.7 | 3300792.7 | PASS |
| Gross GMV >= Net GMV | 3801191.8 | 3300792.7 | PASS |
| Order status count reconciles | 90000 | 90000 | PASS |
| Rates within 0 and 1 | fulfillment/cancellation/stock | 0..1 | PASS |
| Ratings within 1 and 5 | fact_reviews.rating | 1..5 | PASS |
| No orphan sellers in order fact | 0 | 0 | PASS |
