# Uninstall WallpaperHub
# This script stops the engine and removes the configuration

Write-Host "Uninstalling WallpaperHub..." -ForegroundColor Cyan

# 1. Kill any running Python processes related to the app
Get-Process | Where-Object { $_.ProcessName -eq "python" -and $_.CommandLine -like "*app.py*" } | Stop-Process -Force -ErrorAction SilentlyContinue

# 2. Reset the wallpaper to a default color or clear the WorkerW hack
# The easiest way to clear the WorkerW hack is to restart Explorer or change the wallpaper once
Write-Host "Resetting desktop background..."
Add-Type -TypeDefinition @"
using System;
using System.Runtime.InteropServices;
public class Win32 {
    [DllImport("user32.dll", CharSet = CharSet.Auto)]
    public static extern int SystemParametersInfo(int uAction, int uParam, string lpvParam, int fuWinIni);
}
"@
# Trigger a wallpaper refresh (this usually clears the WorkerW injection)
$currentWallpaper = (Get-ItemProperty -Path 'HKCU:\Control Panel\Desktop\' -Name Wallpaper).Wallpaper
[Win32]::SystemParametersInfo(20, 0, $currentWallpaper, 3)

# 3. Remove configuration files
if (Test-Path "config.json") {
    Remove-Item "config.json"
    Write-Host "Removed config.json"
}

# 4. Remove downloads (Optional - commented out for safety)
# if (Test-Path "downloads") {
#     Remove-Item "downloads" -Recurse
#     Write-Host "Removed downloads folder"
# }

Write-Host "Uninstall complete. You can now delete the 'wallpaperhub' folder." -ForegroundColor Green
