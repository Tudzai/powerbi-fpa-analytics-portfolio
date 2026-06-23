# Project 20 Upgrade QA

Status: PASS. Project 20-style source artifacts regenerated; final PBIX rebuilt, Desktop-rendered, saved, and copied back to the exact final path.

Checks completed:
- Project inventory and Project 20 reference review.
- Backup created under `archive/old_versions/`.
- Data QA: pass.
- Generated layout has 3 pages, 4 SVG KPI card slots per page, Current Lens SVG, decision chips, left sidebar slicers, synchronized top chart slots, and explicit table column widths.
- SVG measures are tagged as `ImageUrl` in the generated model metadata.
- Sidebar page navigation uses 9 Power BI `actionButton` overlays with `PageNavigation` targets.
- Seed PBIX was opened as the exact Project 15 model seed and TOM-pushed through direct Analysis Services port binding.
- Native layout patch produced `output/dashboard_final.pbix` with 3 pages and 89 visual containers.
- Power BI Desktop rendered all 3 pages through a uniquely named copy of the exact final PBIX; that Desktop-saved copy was copied back to `output/dashboard_final.pbix`.

Desktop check notes:
- SVG KPI cards render as images on all checked pages and include sparklines.
- Left sidebar lens controls and synced page structure are visible across all 3 pages.
- Dropdown slicer labels/values were visible without clipping at Desktop zoom 57%.
- No blank pages or visual errors were visible in the final walkthrough.
- An unrelated Project 18 report named `dashboard_final.pbix` was open; process command-line checks were used to exclude that window from Project 15 validation.

Evidence:
- `qa/project20_upgrade_verification.json`
- `build/config/navigation_map.json`
- `build/config/table_style_map.json`
- `qa/pbix_final_validation.json`
- `qa/pbix_native_report_validation.json`
- `qa/powerbi_desktop_evidence.json`
