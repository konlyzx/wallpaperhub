# Setup script for WallpaperHub
Write-Host "Setting up WallpaperHub development environment..." -ForegroundColor Cyan

$buildDir = "build"
if (!(Test-Path $buildDir)) {
    New-Item -ItemType Directory -Path $buildDir
    Write-Host "Created build directory." -ForegroundColor Green
}

Write-Host "Checking for dependencies..."
# Check for CMake
if (Get-Command cmake -ErrorAction SilentlyContinue) {
    Write-Host "CMake found." -ForegroundColor Green
} else {
    Write-Host "CMake not found. Please install CMake to build the C++ project." -ForegroundColor Yellow
}

# Check for Python
if (Get-Command python -ErrorAction SilentlyContinue) {
    Write-Host "Python found." -ForegroundColor Green
} else {
    Write-Host "Python not found. Required for utility scripts." -ForegroundColor Yellow
}

Write-Host "Setup complete!" -ForegroundColor Cyan
Write-Host "To run the Python version (no compiler needed):" -ForegroundColor White
Write-Host "python wallpaper_engine.py" -ForegroundColor Green
