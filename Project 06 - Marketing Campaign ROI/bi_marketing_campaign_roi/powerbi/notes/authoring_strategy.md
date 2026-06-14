# Authoring Strategy

Authoring mode: `MANUAL_ASSISTED`

## Why

- Template seed: `none`
- Valid Power BI source: `none`
- UI automation: `unavailable`
- Computer Use requested: `True`
- Computer Use callable UI tool exposed: `False`
- SCRIPTED_DESKTOP_PBIX feasible: `False`
- pbi-tools role: `pbi_tools_available_but_no_powerbi_source_to_compile`

Because no valid Power BI source was found, no callable Computer Use desktop automation tool is exposed in this session, and `SCRIPTED_DESKTOP_PBIX` was ruled out with evidence, the practical path is manual-assisted Power BI Desktop authoring.

## Next PBIX Step

Open Power BI Desktop, import `data/prepared/*.csv`, create relationships from `model/relationship_map.md`, create measures from `model/dax_measures.md`, apply `build/config/theme.json`, build pages from `build/config/page_map.json` and `build/config/visual_map.json`, then save as `output/dashboard_final.pbix`.

Do not use `pbi-tools compile` unless a valid `.pbixproj.json`/PbixProj source exists for this project.
