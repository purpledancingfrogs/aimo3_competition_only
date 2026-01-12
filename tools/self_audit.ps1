param([string]$RecordFile = "audit_record.txt")
$ErrorActionPreference = "Continue"
Write-Host "MASTER AUDIT STARTING..." -ForegroundColor Cyan

#if (-not (Test-Path $RecordFile)) {
    Write-Host "Creating minimal audit record." -ForegroundColor Yellow
    $hsh = "UNKNOWN"; try { $hsh = (git rev-parse HEAD) } catch {}
    "timestamp=$(Get-Date -F s)`ncommit=$hsh`nhash=$hsh`nstatus=MINIMAL" | Out-File $RecordFile -Encoding UTF8
}

$pyFiles = Get-ChildItem -Recurse -Filter *.py | Where { $_.FullName -notmatch "(\n\.git|__pycache__|quarantine)" }
$errs = 0
Write-Host "Checking '($pyFiles.Count) files..." -ForegroundColor Cyan
foreach ($f in $pyFiles) {
    python -m py_compile $f.FullName
    if ($LASTEXITCODE -ne 0) { Write-Host "FAIL: $($f.Name)" -ForegroundColor Red; $errs++ }
}

if ($errs -eq 0) { 
    Write-Host "ALL FILES COMPILED" -ForegroundColor Green
    exit 0
} else { 
    Write-Host "Errors found: $errs" -ForegroundColor Red
    exit 1
}