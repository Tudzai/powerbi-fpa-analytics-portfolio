param([int]$TargetProcessId, [string]$OutPath)

Add-Type -AssemblyName System.Drawing
Add-Type @"
using System;
using System.Runtime.InteropServices;
public class WinShot {
  [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr hWnd, out RECT lpRect);
  [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr hWnd);
  [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr hWnd, int nCmdShow);
  [DllImport("user32.dll")] public static extern bool PrintWindow(IntPtr hwnd, IntPtr hdcBlt, uint nFlags);
  public struct RECT { public int Left; public int Top; public int Right; public int Bottom; }
}
"@

$p = Get-Process -Id $TargetProcessId -ErrorAction Stop
$hwnd = [IntPtr]$p.MainWindowHandle
[void][WinShot]::ShowWindow($hwnd, 3)
[void][WinShot]::SetForegroundWindow($hwnd)
Start-Sleep -Milliseconds 1000

$rect = New-Object WinShot+RECT
[void][WinShot]::GetWindowRect($hwnd, [ref]$rect)
$w = $rect.Right - $rect.Left
$h = $rect.Bottom - $rect.Top

$bmp = New-Object System.Drawing.Bitmap $w, $h
$g = [System.Drawing.Graphics]::FromImage($bmp)
$hdc = $g.GetHdc()
$printed = [WinShot]::PrintWindow($hwnd, $hdc, 2)
$g.ReleaseHdc($hdc)
if (-not $printed) {
  $g.CopyFromScreen($rect.Left, $rect.Top, 0, 0, $bmp.Size)
}

$dir = Split-Path -Parent $OutPath
New-Item -ItemType Directory -Force -Path $dir | Out-Null
$bmp.Save($OutPath, [System.Drawing.Imaging.ImageFormat]::Jpeg)
$g.Dispose()
$bmp.Dispose()

[pscustomobject]@{
  pid = $TargetProcessId
  hwnd = $p.MainWindowHandle
  title = $p.MainWindowTitle
  out = $OutPath
  width = $w
  height = $h
} | ConvertTo-Json
