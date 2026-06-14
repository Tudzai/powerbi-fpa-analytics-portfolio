# Issue Log

## ISSUE-001 - Final PBIX authoring was not complete in the pre-authoring package

- Status: Fixed
- Severity: Medium
- Found in: v03 build package
- Page: All
- Visual: All
- Expected: Automated PBIX created, opened, refreshed, saved, and QA checked.
- Actual: Fixed in v04 using callable Computer Use plus Power BI Desktop.
- Root cause: Earlier pass ran before the Computer Use skill exposed a callable Windows UI automation path.
- Fix: Pushed Project 07 - Marketplace Seller Performance model into Power BI Desktop via TOM/XMLA, created native visuals with Computer Use, saved real PBIX, and validated with pbi-tools.
- Regression: PASS; `output/dashboard_final.pbix` exists and pbi-tools extract/export passed.

## ISSUE-002 - Computer Use requested but not callable

- Status: Fixed
- Severity: Medium
- Found in: v03 build package
- Page: All
- Visual: All
- Expected: Computer Use click/screenshot/UI-control capability available to author Power BI Desktop.
- Actual: Fixed after invoking the Computer Use skill directly.
- Root cause: Computer Use needed the skill bootstrap path through the Windows automation runtime.
- Fix: Used Computer Use to target Power BI Desktop window `2428806`, create native visuals, and save the file.
- Regression: PASS; final PBIX ready.

## ISSUE-003 - Power BI saved to recent Project 06 - Marketing Campaign ROI output location first

- Status: Fixed
- Severity: Low
- Found in: v04 PBIX save
- Page: File save
- Visual: n/a
- Expected: Power BI saves directly to `Project 07 - Marketplace Seller Performance/output/dashboard_final.pbix`.
- Actual: Power BI's recent location initially pointed at `Project 06 - Marketing Campaign ROI/bi_marketing_campaign_roi/output/dashboard_final.pbix`.
- Root cause: Power BI Desktop remembered a prior output folder.
- Fix: Copied the real Power BI-saved PBIX to `Project 07 - Marketplace Seller Performance/output/dashboard_final.pbix` and validated the copied file.
- Regression: PASS; Project 07 - Marketplace Seller Performance final PBIX extracts and exports data successfully.
