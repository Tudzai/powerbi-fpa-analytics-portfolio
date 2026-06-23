# Project 20 Style Upgrade Before Audit

Date: 2026-06-23

Target: Project 16 - Manufacturing Cost FP&A.

Reference read:
- `Md Registry/7. BI_A2Z_Master_Prompt_v3.md`
- `Md Registry/PROJECT_20_STYLE_UPGRADE_PROMPT.md`
- Project 20 README, handoff notes, changelog, interaction QA, verification JSON, measure map, and slicer/chart/KPI notes.

Before-state:
- Project has 3 report pages, 45 native visual containers, and 12 native slicers.
- Slicers were positioned in the header row near the title (`y=18`) rather than in a dedicated filter band.
- KPI cards started at `y=88`, leaving the title/slicer/KPI areas visually compressed.
- Supplemental PNG screenshots did not show slicers, so preview evidence did not reflect the requested control placement.
- PBIX status was already `BLOCKED_PBIX_PERSISTENCE` because offline export still showed the seed DataModel.

Upgrade target:
- Keep the light manufacturing FP&A style and domain-specific page flow.
- Move slicers to the top in a clear four-slot filter bar.
- Preserve native visuals, report page count, and existing metrics.
- Do not claim final PBIX completion until the existing DataModel persistence blocker is resolved.
