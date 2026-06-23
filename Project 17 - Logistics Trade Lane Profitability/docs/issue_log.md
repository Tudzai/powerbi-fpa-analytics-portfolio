# Issue Log

- Resolved: initial Desktop open-check showed Something went wrong / Failed to load the report because uild/native_report_layout_project17.json was generated before output/dashboard_model_seed.pbix existed, leaving Report/Layout without required top-level metadata.
- Fix: regenerated the layout after the seed PBIX was saved, preserving seed top-level 
esourcePackages, pods, and layoutOptimization; repatched final PBIX and reopened exact Project 17 final path.
- Resolved: Project 20-style top filter row had a clipping risk because slicers were 44px tall and duplicated labels through both slicer header and visual-container title. Final patch increased slicer height to 56px and hid slicer container titles.
- Live Desktop render recheck after the latest slicer-polish patch was attempted but not accepted as evidence: pbi-tools showed no open Project 17 final PBIX session; the open dashboard_final session belonged to Project 18.
