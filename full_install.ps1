Write-Host "=== PCA SSH — Private Control Administration ===" -ForegroundColor Cyan

# Find Python — check common install paths too
$python = $null
$tryPaths = @(
    "python",
    "python3",
    "py",
    "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe",
    "$env:LOCALAPPDATA\Programs\Python\Python311\python.exe",
    "C:\Python312\python.exe",
    "C:\Python311\python.exe",
    "$env:APPDATA\Python\Python312\Scripts\..\python.exe"
)
foreach ($cmd in $tryPaths) {
    try {
        $ver = & $cmd --version 2>$null
        if ($ver -match "Python 3") {
            $python = $cmd
            Write-Host "Python: $ver" -ForegroundColor Green
            break
        }
    } catch {}
}

if (-not $python) {
    Write-Host "Python not found. Downloading..." -ForegroundColor Yellow
    $pyUrl = "https://www.python.org/ftp/python/3.12.7/python-3.12.7-amd64.exe"
    $pyInst = Join-Path $env:TEMP "python-installer.exe"
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
    Invoke-WebRequest -Uri $pyUrl -OutFile $pyInst -UseBasicParsing
    Write-Host "Installing Python..." -ForegroundColor Yellow
    Start-Process -FilePath $pyInst -ArgumentList "/quiet","InstallAllUsers=0","PrependPath=1","Include_pip=1" -Wait
    Remove-Item $pyInst -ErrorAction SilentlyContinue

    $searchPaths = @(
        "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe",
        "C:\Python312\python.exe",
        "C:\Program Files\Python312\python.exe"
    )
    foreach ($p in $searchPaths) {
        if (Test-Path $p) {
            $python = $p
            Write-Host "Python at: $p" -ForegroundColor Green
            break
        }
    }
    if (-not $python) {
        Write-Host "Cannot find python after install!" -ForegroundColor Red
        Read-Host "Press Enter"
        exit 1
    }
}

Write-Host "Installing deps..." -ForegroundColor Yellow
& $python -m pip install --upgrade pip 2>&1 | ForEach-Object { if ($_ -notmatch "WARNING") { $_ } }
& $python -m pip install paramiko pillow pyinstaller 2>&1 | ForEach-Object { if ($_ -notmatch "WARNING") { $_ } }

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
if (-not $scriptDir) { $scriptDir = Get-Location }

$localDir = Join-Path $env:TEMP "pca-ssh-build"
if (Test-Path $localDir) { Remove-Item $localDir -Recurse -Force }
New-Item -ItemType Directory -Path $localDir | Out-Null
Copy-Item (Join-Path $scriptDir "ssh_manager.py") $localDir
Copy-Item (Join-Path $scriptDir "gen_icon.py") $localDir

Set-Location $localDir

# Generate .ico
Write-Host "Generating icon..." -ForegroundColor Yellow
& $python gen_icon.py 2>&1 | ForEach-Object { Write-Host $_ }

$icoFile = Join-Path $localDir "pca_ssh.ico"
if (Test-Path $icoFile) {
    $iconArg = "--icon=pca_ssh.ico"
} else {
    $iconArg = ""
}

Write-Host "Building PCA_SSH.exe..." -ForegroundColor Yellow
& $python -m PyInstaller --onefile --noconsole --name "PCA_SSH" $iconArg ssh_manager.py 2>&1 | ForEach-Object { Write-Host $_ }

$exe = Join-Path $localDir "dist\PCA_SSH.exe"
if (Test-Path $exe) {
    $desktop = [Environment]::GetFolderPath("Desktop")
    Copy-Item $exe (Join-Path $desktop "PCA_SSH.exe") -Force
    Write-Host ""
    Write-Host "DONE! PCA_SSH.exe on Desktop" -ForegroundColor Green
} else {
    Write-Host "Build FAILED" -ForegroundColor Red
}

Read-Host "Press Enter"
