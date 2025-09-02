# Search for Python installations in common locations
$pythonPaths = @(
    "C:\\Python*\\python.exe",
    "C:\\Program Files\\Python*\\python.exe",
    "C:\\Program Files (x86)\\Python*\\python.exe",
    "$env:LOCALAPPDATA\\Programs\\Python\\Python*\\python.exe"
)

Write-Host "Searching for Python installations..."
$found = $false

foreach ($path in $pythonPaths) {
    $pythonMatches = Get-ChildItem -Path $path -ErrorAction SilentlyContinue
    foreach ($python in $pythonMatches) {
        $version = & $python.FullName --version 2>&1
        Write-Host "Found Python at: $($python.FullName)"
        Write-Host "  Version: $version"
        $found = $true
    }
}

if (-not $found) {
    Write-Host "No Python installations found in common locations."
    Write-Host "Please install Python 3.8 or later from https://www.python.org/downloads/"
    Write-Host "Make sure to check 'Add Python to PATH' during installation."
}
