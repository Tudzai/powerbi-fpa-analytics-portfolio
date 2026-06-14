# Dashboard Complete Handoff

## Artifact

- Main interactive dashboard: `output/dashboard_complete.html`
- Power BI PBIX: `output/dashboard_final.pbix`
- Static preview: `output/dashboard_preview.html`

## Scope

Project 07 - Marketplace Seller Performance is a marketplace / seller performance dashboard for Shopee, Lazada, and Tiki-style seller operations.

Core metrics:

- Seller GMV
- Fulfillment rate
- Cancellation rate
- Average rating
- Stock availability
- Active sellers
- Top and bottom sellers
- Seller risk queue

## Dashboard Structure

1. Executive Cockpit: KPI strip, GMV trend, GMV by platform, top and bottom sellers.
2. Seller Portfolio: GMV vs cancellation scatter, seller concentration curve, seller tier contribution, leaderboard.
3. Growth Drivers: category share/growth quadrant, GMV vs ads and voucher trend, opportunity sellers.
4. Ops Risk: cancellation/stockout trend, cancellation reasons, high-risk sellers, action queue.

## Validation

- Reads from prepared Project 07 - Marketplace Seller Performance CSV files.
- Output validation written to `qa/dashboard_complete_validation.json`.
- Dashboard is self-contained: no external JavaScript or CDN dependency.
