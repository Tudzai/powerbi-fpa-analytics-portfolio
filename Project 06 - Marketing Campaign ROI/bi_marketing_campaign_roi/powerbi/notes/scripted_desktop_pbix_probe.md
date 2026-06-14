# Scripted Desktop PBIX Probe

The prompt v2 requires checking `SCRIPTED_DESKTOP_PBIX` before falling back to manual-assisted authoring.

- Result: not feasible
- Evidence file: `_agent/scripted_desktop_pbix_probe.json`
- Main blockers:
  - No base/model PBIX, PBIT, PBIP, or pbixproj source exists inside this clean project.
  - Power BI Desktop assemblies were detected, but no documented project-local API/CLI was available to create a valid native report layout and package a new PBIX from CSV/DAX/page specs.
  - pbi-tools is available, but there is no valid Power BI source to compile.

No generated HTML, PNG, CSV, JSON, or Excel artifact is being treated as a PBIX final.
