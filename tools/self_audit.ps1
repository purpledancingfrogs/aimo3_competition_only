param([string]$RecordFile = "audit_record.txt")

$ErrorActionPreference = "Continue"

Write-Host "=== SELF AUDIT STARTING ===" -ForegroundColor Cyan

# Check if record file exists
if (!(Test-Path $RecordFile)) {
    Write-Host "WARNING: No audit record file found at $RecordFile" -ForegroundColor Yellow
    Write-Host "Creating minimal audit record..." -ForegroundColor Yellow
    
    # Create minimal record
    $gitHash = (git rev-parse HEAD 2>$null) -or "UNKNOWN"
    $timestamp = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
    
    @"
timestamp=$timestamp
commit=$gitHash
hash=$gitHash
status=MINIMAL_RECORD
"@ | Out-File $RecordFile -Encoding UTF8
}

# Read and parse record
$record = Get-Content $RecordFile -Raw
Write-Host "Audit record loaded: $($record.Length) bytes" -ForegroundColor Green

# Extract fields safely
$commit = if ($record -match 'commit=([^\r\n]+)') { $matches[1] } else { "UNKNOWN" }
$hash = if ($record -match 'hash=([^\r\n]+)') { $matches[1] } else { "UNKNOWN" }

Write-Host "Commit: $commit" -ForegroundColor White
Write-Host "Hash: $hash" -ForegroundColor White

# Verify git status
$gitStatus = git status --porcelain 2>$null
if ($gitStatus) {
    Write-Host "WARNING: Uncommitted changes detected" -ForegroundColor Yellow
    $gitStatus | ForEach-Object { Write-Host "  $_" -ForegroundColor Yellow }
} else {
    Write-Host "✅ Git working tree clean" -ForegroundColor Green
}

# Check Python files compile
Write-Host "`nChecking Python files..." -ForegroundColor Cyan
$pyFiles = Get-ChildItem -Recurse -Filter *.py | Where-Object { $_.FullName -notmatch '\\\.git\\|\\__pycache__\\' }
$compileErrors = 0

foreach ($f in $pyFiles) {
    $result = python -m py_compile $f.FullName 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  ❌ $($f.Name): $result" -ForegroundColor Red
        $compileErrors++
    }
}

if ($compileErrors -eq 0) {
    Write-Host "✅ All Python files compile" -ForegroundColor Green
} else {
    Write-Host "❌ $compileErrors Python files failed compilation" -ForegroundColor Red
}

Write-Host "`n=== SELF AUDIT COMPLETE ===" -ForegroundColor Cyan
exit 0
