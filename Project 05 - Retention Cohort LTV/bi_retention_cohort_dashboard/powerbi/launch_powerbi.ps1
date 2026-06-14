$ErrorActionPreference = "Continue"
if (True) {
  $exe = "C:\Program Files\Microsoft Power BI Desktop\bin\PBIDesktop.exe"
  Start-Process -FilePath $exe
} elseif ("Microsoft.MicrosoftPowerBIDesktop_8wekyb3d8bbwe!Microsoft.MicrosoftPowerBIDesktop") {
  Start-Process 'shell:AppsFolder\Microsoft.MicrosoftPowerBIDesktop_8wekyb3d8bbwe!Microsoft.MicrosoftPowerBIDesktop'
} else {
  Write-Error "Power BI Desktop was not detected by environment check."
}
