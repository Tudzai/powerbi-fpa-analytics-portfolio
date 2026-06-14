param(
  [string]$OutputPath = ""
)

$ErrorActionPreference = "Continue"
if ([string]::IsNullOrWhiteSpace($OutputPath)) {
  $ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..")
  $OutputPath = Join-Path $ProjectRoot "output\dashboard_model.pbix"
}

Add-Type @"
using System;
using System.Runtime.InteropServices;
public class Win32 {
  [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr hWnd);
  [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr hWnd, int nCmdShow);
}
"@
Add-Type -AssemblyName System.Windows.Forms

$pbi = Get-Process PBIDesktop -ErrorAction SilentlyContinue | Where-Object { $_.MainWindowHandle -ne 0 } | Select-Object -First 1
if (-not $pbi) { throw "Power BI Desktop window not found." }
[Win32]::ShowWindow($pbi.MainWindowHandle, 9) | Out-Null
[Win32]::SetForegroundWindow($pbi.MainWindowHandle) | Out-Null
Start-Sleep -Seconds 2

[System.Windows.Forms.SendKeys]::SendWait("^s")
Start-Sleep -Seconds 4
[System.Windows.Forms.SendKeys]::SendWait($OutputPath)
Start-Sleep -Seconds 1
[System.Windows.Forms.SendKeys]::SendWait("{ENTER}")
Start-Sleep -Seconds 25

[pscustomobject]@{
  attempted_output = $OutputPath
  file_exists = (Test-Path -LiteralPath $OutputPath)
  note = "Keyboard save automation is best-effort. If file_exists is false, use manual-assisted runbook."
}
