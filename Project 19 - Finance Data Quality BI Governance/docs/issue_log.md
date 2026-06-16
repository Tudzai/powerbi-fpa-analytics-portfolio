# Issue Log

- Open: automated PBIX finalization blocked until exact Project 19 Desktop session can be isolated.
- Observed: `pbi-tools compile` failed because the output seed is a Fabric PBIP project, while this pbi-tools compile command expects legacy PbixProj parts such as `Version.txt`.
- Observed: Project 19 PBIP process launched with the correct command line, but Desktop visual capture was obstructed by an unrelated SQL Server credential prompt from another Power BI session. No credentials were entered and no file was saved.
