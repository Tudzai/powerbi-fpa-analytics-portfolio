# Visual QA Notes

v58 recreated from the chat checkpoint requested by the user.

- Final product is a real PBIX rebuilt through the TOM model push and native layout patch pipeline, not an HTML-only preview.
- The 3 main detail tables were upgraded: `Board KPI Details`, `3-Statement Summary`, and `Risk Register`.
- Table polish includes explicit column widths, alignment rules, header fill, banded rows, row padding, and SVG trend/signal columns.
- Chart units are verified: runway/leverage charts keep native units, while money charts retain compact `$M` display units.
- Playwright evidence is generated from a Power BI Desktop render crop.

Evidence:

- Direct PBIX verification: `qa/pbix_direct_verification_v58.json`
- Desktop capture: `qa/screenshots/project20_v58_desktop_full.jpg`
- Playwright crop: `output/playwright/project20_v58_desktop_crops.png`
