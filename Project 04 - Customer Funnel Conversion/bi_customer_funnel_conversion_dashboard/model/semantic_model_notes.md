# Semantic Model Notes

- Primary funnel metrics use `fact_sessions`, one row per qualified session.
- Funnel visual counts can use `fact_stage_sessions` joined to `dim_funnel_stage` and sorted by `stage_order`.
- Transition/drop-off visuals use `fact_stage_transition`.
- Revenue and AOV use `fact_orders`; do not calculate revenue from session rows.
- Marketing efficiency uses `fact_marketing_spend` by date/channel/campaign. Category filters should not be forced onto spend unless a campaign/category allocation rule is added.
