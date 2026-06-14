# Metric Definitions

| Metric | Definition | Grain | Notes |
|---|---|---|---|
| Seller GMV | Sum of `seller_gmv_net` for non-cancelled order items | Order item | Excludes shipping and platform-funded discount. |
| Gross GMV | Sum of `gross_gmv` before discount | Order item | Used for reconciliation. |
| Fulfillment Rate | Fulfilled items / eligible non-cancelled items | Fulfillment/order item | Use `DIVIDE`, never average seller rates for platform totals. |
| Cancellation Rate | Cancelled items / placed items | Order item | Includes all created order items in denominator. |
| Average Rating | Weighted average rating from verified review facts | Review | Blank if no review denominator. |
| Stock Availability | In-stock seller-SKU-days / seller-SKU-days | Seller-SKU-day | Use inventory snapshot, not current stock only. |
| Top Sellers | Rank sellers by Seller GMV under active filters | Seller | Tie-break by orders, rating, lower cancellation. |
| Bottom Sellers | Lowest performance score after minimum-volume filter | Seller | Avoid over-penalizing new/low-volume sellers. |
| Seller Performance Score | 40% GMV percentile, 25% fulfillment, 20% cancellation inverse, 10% rating, 5% stock | Seller | Used for action queue. |
