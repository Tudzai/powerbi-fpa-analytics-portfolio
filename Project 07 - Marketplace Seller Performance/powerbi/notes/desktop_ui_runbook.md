# Desktop UI Runbook

## Launch

Run `powerbi/launch_powerbi.ps1`.

## Import

Open a blank report and import all files in `data/prepared/`.

## Model

Mark `dim_date` as the date table. Create relationships from `model/relationship_map.md` with single-direction dimension filters.

## Measures

Add DAX from `model/dax_measures.md`. Format GMV as currency, rates as percentages, and rating as decimal.

## Pages

Build: Executive Cockpit, Seller Portfolio & Segmentation, Commercial Growth Drivers, Ops Health & Risk Monitor. Use global slicers: Date, Platform, Category, Seller Tier, Region, Fulfillment Model, Account Manager, Seller Search.

## Save

Save as `output/dashboard_final.pbix`. The file is final only after open/save/refresh QA.
