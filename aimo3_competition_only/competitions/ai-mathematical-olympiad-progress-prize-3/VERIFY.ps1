$ErrorActionPreference='Stop'; Set-StrictMode -Version Latest

$compRepo = 'C:\aureon-swarm\aimo3_competition_only\competitions\ai-mathematical-olympiad-progress-prize-3'
$zipPath  = Join-Path $compRepo 'audit_archive\AIMO3_Competition_Final_Audit_Bundle.zip'

$required = @(
  (Join-Path $compRepo 'test.csv'),
  (Join-Path $compRepo 'sample_submission.csv'),
  (Join-Path $compRepo 'submission_final.csv'),
  (Join-Path $compRepo 'AIMO3_SUBMISSION.json'),
  (Join-Path $compRepo 'evaluation\verifier.py'),
  (Join-Path $compRepo 'README.md'),
  (Join-Path $compRepo 'objective.json'),
  (Join-Path $compRepo 'reference.csv'),
  (Join-Path $compRepo 'submission_factual.csv'),
  $zipPath
)

$missing = @($required | Where-Object { -not (Test-Path $_) })
if($missing.Count -gt 0){ throw ("VERIFY FAIL - Missing:
" + ($missing -join "
")) }

$csv = Import-Csv (Join-Path $compRepo 'submission_final.csv')
if(-not $csv -or $csv.Count -lt 1){ throw "VERIFY FAIL - submission_final.csv has zero prediction rows" }
if(-not ($csv[0].PSObject.Properties.Name -contains 'id') -or -not ($csv[0].PSObject.Properties.Name -contains 'prediction')){
  throw "VERIFY FAIL - submission_final.csv missing columns id,prediction"
}

Write-Host "VERIFY OK - Files present + submission_final.csv rows:" $csv.Count
Write-Host "ZIP SHA256:" (Get-FileHash -Algorithm SHA256 $zipPath).Hash
