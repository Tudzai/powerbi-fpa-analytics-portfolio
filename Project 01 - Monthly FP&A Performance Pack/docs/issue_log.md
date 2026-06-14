# Issue Log

## ISSUE-001 - PBIX report visuals not yet authored and QA-tested

- Status: Open
- Severity: High
- Found in: build environment
- Expected: Create and QA report visuals inside `output/dashboard_final.pbix`.
- Actual: `output/dashboard_final.pbix` exists as a valid Desktop-authored semantic-model PBIX, but the report canvas visuals are not fully authored.
- Root cause: Power BI Desktop is a GUI authoring surface. Direct internal PBIX report-layout patching was rejected by Desktop as a corrupted file, so only Desktop-authored visual layout should be used.
- Fix: Open `output/dashboard_final.pbix` in Power BI Desktop and build report pages from `build/config/page_map.json` and `build/config/visual_map.json`, using `output/exports/fpa_dashboard_preview.html` as the reference.
- Regression: Run `qa/qa_checklist.md` after PBIX build.

## ISSUE-002 - Synthetic source data caveat

- Status: Accepted
- Severity: Medium
- Found in: source layer
- Expected: Real company finance data.
- Actual: Portfolio sample dataset generated locally.
- Root cause: No company source data was provided.
- Fix: Replace files in `data/raw/`, then rerun build scripts.
- Regression: Re-run `01_profile_data.py`, `02_prepare_data.py`, and `03_validate_prepared_data.py`.

## ISSUE-003 - Generator date constructor error

- Status: Fixed
- Severity: Low
- Found in: `build/scripts/00_generate_sample_raw.py`
- Expected: May 2026 story modifiers run without error.
- Actual: `date(2026, 5)` missed the day argument.
- Root cause: Python date constructor requires year, month, and day.
- Fix: Changed to `date(2026, 5, 1)`.
- Regression: Raw generation reran successfully.

## ISSUE-004 - QA script XLSX column mismatch

- Status: Fixed
- Severity: Low
- Found in: `build/scripts/03_validate_prepared_data.py`
- Expected: Reconciliation XLSX writes all check rows.
- Actual: Relationship checks lacked `Delta`.
- Root cause: Mixed row schema in validation output.
- Fix: Added blank `Delta` to relationship check rows.
- Regression: Validation passed and `qa/reconciliation.xlsx` was created.

## ISSUE-005 - Static preview not browser-verified in current environment

- Status: Open
- Severity: Low
- Found in: preview QA
- Expected: Open `output/exports/fpa_dashboard_preview.html` in browser and inspect layout.
- Actual: In-app browser blocked direct `file://` navigation by policy.
- Root cause: Browser security policy blocks local file URL navigation.
- Fix: Open the HTML manually in a local browser, or QA after building PBIX.
- Regression: Confirm KPI cards, charts, and commentary render without clipping.

## ISSUE-006 - Direct PBIX layout patch rejected by Power BI Desktop

- Status: Accepted
- Severity: Medium
- Found in: report automation attempt
- Expected: Inject report page layout into `Report/Layout`.
- Actual: Power BI Desktop showed "This file is corrupted or was created by an unrecognized version of Power BI Desktop."
- Root cause: Modern PBIX files include integrity/security metadata; unsupported zip-level report edits are not a safe authoring path.
- Fix: Restored `output/dashboard_final.pbix` from the valid Desktop-authored model PBIX and removed the generated patch script.
- Regression: Open `output/dashboard_final.pbix` in Desktop and author report visuals through the UI.

## ISSUE-007 - Legacy generated dashboard hid data and overused textboxes

- Status: Fixed
- Severity: High
- Found in: `output/dashboard_final.pbix` v05 report canvas.
- Expected: A clean orange FP&A dashboard with visible KPI cards and native Power BI charts/tables.
- Actual: The v05 canvas used 366 generated visual containers, mostly textbox/basic-shape layers. In Power BI Desktop edit mode, object handles and dense overlays made the dashboard look cluttered and hid data at the right edge.
- Root cause: The report layout was built as a static textbox/shape composition instead of native Power BI visuals.
- Fix: Rebuilt the PBIX report canvas with `build/scripts/10_build_native_pbix_report.py` and `build/scripts/10_apply_native_pbix_report.ps1`. The v06 final uses 40 visual containers, native cards/charts/tables/slicers, no commentary section, corrected currency formatting, and a safe visual zone with max right edge 966 on a 1280px canvas.
- Regression: `PowerBIPackager.Validate` passed; DAX KPI spot checks passed; screenshot saved at `output/screenshots/dashboard_final_v06_native_safezone_final.png`.
