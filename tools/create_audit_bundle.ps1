param(
  [string]$RepoRoot = (Get-Location).Path,
  [string]$OutZip = (Join-Path (Get-Location).Path "audit\AIMO3_Competition_Final_Audit_Bundle.zip")
)
$ErrorActionPreference="Stop"; function Assert($c,$m){if(-not $c){throw $m}}

Set-Location $RepoRoot
$head = (git rev-parse HEAD).Trim()
Assert (Test-Path ".\solver.py") "MISSING solver.py"
Assert (Test-Path ".\kaggle_evaluation") "MISSING kaggle_evaluation/"
Assert (Test-Path ".\kaggle_evaluation\aimo_3_gateway.py") "MISSING kaggle_evaluation/aimo_3_gateway.py"
Assert (Test-Path ".\requirements.txt") "MISSING requirements.txt"

$stage = Join-Path $env:TEMP ("aimo3_audit_stage_" + $head.Substring(0,8))
if (Test-Path $stage) { Remove-Item -Recurse -Force $stage }
New-Item -ItemType Directory -Force -Path $stage | Out-Null

# Copy minimal Kaggle-execution surface + solver modules (deterministic)
Copy-Item ".\solver.py" $stage -Force
Copy-Item ".\requirements.txt" $stage -Force
Copy-Item ".\run_all.py" $stage -Force -ErrorAction SilentlyContinue
Copy-Item ".\kaggle_evaluation" (Join-Path $stage "kaggle_evaluation") -Recurse -Force
if (Test-Path ".\modules") { Copy-Item ".\modules" (Join-Path $stage "modules") -Recurse -Force }

# Include audit record template + refs note (filled by caller after zip hash)
$refs = "HEAD=$head`n"
Set-Content -Encoding UTF8 -Path (Join-Path $stage "AUDIT_REFS.txt") -Value $refs

$zipDir = Split-Path -Parent $OutZip
New-Item -ItemType Directory -Force -Path $zipDir | Out-Null
if (Test-Path $OutZip) { Remove-Item -Force $OutZip }

Compress-Archive -Path (Join-Path $stage "*") -DestinationPath $OutZip -Force
Write-Output ("BUNDLE_OK " + $OutZip)
