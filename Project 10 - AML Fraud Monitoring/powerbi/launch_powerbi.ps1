param(
  [string]$PbixPath = ""
)

$ErrorActionPreference = "Stop"
$exe = "C:\Program Files\Microsoft Power BI Desktop\bin\PBIDesktop.exe"
if (!(Test-Path -LiteralPath $exe)) {
  $cmd = Get-Command PBIDesktop.exe -ErrorAction SilentlyContinue
  if ($cmd) { $exe = $cmd.Source }
}
if (!(Test-Path -LiteralPath $exe)) { throw "Power BI Desktop executable not found." }
if ($PbixPath) {
  Start-Process -FilePath $exe -ArgumentList "`"$PbixPath`""
} else {
  Start-Process -FilePath $exe
}
