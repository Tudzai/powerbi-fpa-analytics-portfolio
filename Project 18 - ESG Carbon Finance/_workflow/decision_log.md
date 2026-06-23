# Decision Log

Date: 2026-06-15

Decision: Use synthetic demo data with fixed seed.
Reason: No real source data was provided and the project is portfolio/demo oriented.
Impact: Dashboard can be rebuilt deterministically but is not a production GHG inventory.
Reversible: yes.

Decision: Upgrade from three tabs to four pages.
Reason: BI A-Z v3 standard separates risk/exception/action handling from scenario and ROI analysis.
Impact: The executive journey now has overview, diagnostics, scenario/ROI, and control-tower action review.
Reversible: yes.

Decision: Use Procurement PBIX as layout seed/reference only.
Reason: It is the closest local supplier/spend template but not ESG-specific.
Impact: Avoids stale domain bindings in final content.
Reversible: yes.

Decision: Keep native static textbox/shape visuals for the patched report layout.
Reason: They rendered reliably in the prior Desktop open-check while preserving the semantic model for Data/Model view exploration.
Impact: Canvas is executive-readable; deeper self-service analysis remains available through model fields and measures.
Reversible: yes, if a future build uses fully bound native visuals with Desktop QA.
