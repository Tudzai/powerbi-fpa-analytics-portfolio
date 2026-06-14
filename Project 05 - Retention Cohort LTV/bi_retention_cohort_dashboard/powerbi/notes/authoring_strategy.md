# PBIX Authoring Strategy

Preferred route is Power BI Desktop with Computer Use assistance where safe. The generated PBIP package contains the semantic model, DAX measures, and PBIR report definition.

If Desktop opens the PBIP correctly, refresh the CSV import model and save as `output/dashboard_final.pbix`.

Programmatic PBIX compile is not treated as sufficient for this import model unless it produces a real PBIX that opens, saves, refreshes, and passes QA. pbi-tools PBIX compile is primarily reliable for thin report projects; import models generally require PBIT/PBIP plus Desktop save.
