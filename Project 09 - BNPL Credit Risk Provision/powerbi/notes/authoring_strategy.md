# PBIX Authoring Decision

Selected route: SCRIPTED_DESKTOP_PBIX with Computer Use verification.

Reason:
- Power BI Desktop EXE and pbi-tools are available.
- dotnet CLI is unavailable, so the route avoids global dotnet tooling.
- A valid PBIX seed will be copied, then the full Project 09 - BNPL Credit Risk Provision model is pushed through the local Power BI Desktop TOM/XMLA session.
- Native report layout is patched after the Project 09 - BNPL Credit Risk Provision model seed is saved.

Fallback:
- If Desktop save or session binding fails, the build remains PBIP/PBIT/HTML supplemental and PBIX is marked blocked.
