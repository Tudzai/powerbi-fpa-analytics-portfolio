param([int]$TargetProcessId, [int]$X, [int]$Y)

Add-Type @"
using System;
using System.Runtime.InteropServices;
public class WinClick {
  [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr hWnd, out RECT lpRect);
  [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr hWnd);
  [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr hWnd, int nCmdShow);
  [DllImport("user32.dll")] public static extern bool SetCursorPos(int X, int Y);
  [DllImport("user32.dll")] public static extern void mouse_event(uint dwFlags, uint dx, uint dy, uint dwData, UIntPtr dwExtraInfo);
  public struct RECT { public int Left; public int Top; public int Right; public int Bottom; }
}
"@

$p = Get-Process -Id $TargetProcessId -ErrorAction Stop
$hwnd = [IntPtr]$p.MainWindowHandle
[void][WinClick]::ShowWindow($hwnd, 3)
[void][WinClick]::SetForegroundWindow($hwnd)
Start-Sleep -Milliseconds 500

$rect = New-Object WinClick+RECT
[void][WinClick]::GetWindowRect($hwnd, [ref]$rect)
$screenX = $rect.Left + $X
$screenY = $rect.Top + $Y
[void][WinClick]::SetCursorPos($screenX, $screenY)
Start-Sleep -Milliseconds 100
[WinClick]::mouse_event(0x0002, 0, 0, 0, [UIntPtr]::Zero)
Start-Sleep -Milliseconds 100
[WinClick]::mouse_event(0x0004, 0, 0, 0, [UIntPtr]::Zero)
Start-Sleep -Milliseconds 700

[pscustomobject]@{
  pid = $TargetProcessId
  hwnd = $p.MainWindowHandle
  windowX = $X
  windowY = $Y
  screenX = $screenX
  screenY = $screenY
} | ConvertTo-Json
