# Issue Log

- Resolved: initial Desktop open-check showed `Something went wrong / Failed to load the report` because `build/native_report_layout_project17.json` was generated before `output/dashboard_model_seed.pbix` existed, leaving `Report/Layout` without required top-level metadata.
- Fix: regenerated the layout after the seed PBIX was saved, preserving seed top-level `resourcePackages`, `pods`, and `layoutOptimization`; repatched final PBIX and reopened exact Project 17 final path.
- Current status: final PBIX opens and saves in Desktop; no render modal, no remaining loading state, package validation passed.
