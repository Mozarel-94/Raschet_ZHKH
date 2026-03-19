param(
    [string]$PythonExe = "C:\Users\user\AppData\Local\Programs\Python\Python314\python.exe",
    [string]$OutputDir = ""
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
if (-not $OutputDir) {
    $OutputDir = Join-Path $repoRoot "dist\Raschet_ZHKH_Windows_Portable"
}

if (-not (Test-Path $PythonExe)) {
    $pythonRoot = Join-Path $env:LocalAppData "Programs\Python"
    $candidates = @()

    if (Test-Path $pythonRoot) {
        $candidates += Get-ChildItem -Path $pythonRoot -Directory -Filter "Python*" |
            Sort-Object Name -Descending |
            ForEach-Object { Join-Path $_.FullName "python.exe" }
    }

    $candidates += @(
        "C:\Users\user\AppData\Local\Programs\Python\Python314\python.exe",
        "C:\Users\user\AppData\Local\Programs\Python\Python313\python.exe"
    )

    foreach ($candidate in $candidates) {
        if (Test-Path $candidate) {
            $PythonExe = $candidate
            break
        }
    }
}

if (-not (Test-Path $PythonExe)) {
    throw "Python not found. Pass -PythonExe with the full path to python.exe."
}

$pythonDir = Split-Path -Parent $PythonExe
$portablePythonDir = Join-Path $OutputDir ".portable\python"
$zipPath = "$OutputDir.zip"

if (Test-Path $OutputDir) {
    Remove-Item $OutputDir -Recurse -Force
}

if (Test-Path $zipPath) {
    Remove-Item $zipPath -Force
}

New-Item -ItemType Directory -Path $portablePythonDir -Force | Out-Null

$appFiles = @(
    "app.py",
    "calculator.py",
    "history_analytics.py",
    "storage.py",
    "meter_history.json",
    "run_local.bat",
    "README.md"
)

foreach ($relativePath in $appFiles) {
    Copy-Item (Join-Path $repoRoot $relativePath) -Destination (Join-Path $OutputDir $relativePath) -Force
}

$robocopyArgs = @(
    $pythonDir,
    $portablePythonDir,
    "/E",
    "/NFL",
    "/NDL",
    "/NJH",
    "/NJS",
    "/NP",
    "/XD", "__pycache__", "Scripts", "Tools", "Doc", "tcl", "include", "share"
)

& robocopy @robocopyArgs | Out-Null
$robocopyExitCode = $LASTEXITCODE
if ($robocopyExitCode -ge 8) {
    throw "robocopy failed with exit code $robocopyExitCode"
}

$portableReadme = @'
# Windows portable

1. Open this folder.
2. Double-click `run_local.bat`.
3. The application will open at `http://127.0.0.1:8000`.

This folder already contains Python, so no separate installation is required.
'@

Set-Content -Path (Join-Path $OutputDir "README-portable.txt") -Value $portableReadme -Encoding UTF8

Compress-Archive -Path (Join-Path $OutputDir "*") -DestinationPath $zipPath -Force

Write-Host "Portable folder created:" $OutputDir
Write-Host "Portable zip created:" $zipPath
