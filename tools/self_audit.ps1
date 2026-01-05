$ErrorActionPreference = "Stop"
function Assert($cond, $msg) { if (-not $cond) { throw $msg } }

$recordPath = ".\audit\AIMO3_AUDIT_RECORD.txt"
$zipPath    = ".\audit\AIMO3_Competition_Final_Audit_Bundle.zip"

$head = (git rev-parse HEAD).Trim()
$tag  = (git rev-parse aimo3-submission-ready).Trim()
$br   = (git rev-parse aimo3-kaggle-submit).Trim()

Assert ($head -eq $tag) "TAG_MISMATCH head=$head tag=$tag"
Assert ($head -eq $br)  "BRANCH_MISMATCH head=$head branch=$br"
Assert (Test-Path $recordPath) "MISSING_RECORD: $recordPath"
Assert (Test-Path $zipPath)    "MISSING_AUDIT_ZIP: $zipPath"

$recCommit = ((Select-String '^commit=' $recordPath).ToString().Split('=')[1]).Trim()
$recHash   = ((Select-String '^hash='   $recordPath).ToString().Split('=')[1]).Trim().ToUpperInvariant()
$zipHash   = (Get-FileHash -Algorithm SHA256 $zipPath).Hash.ToUpperInvariant()
$tracked   = (git ls-files -- $zipPath)

Assert ($recHash -eq $zipHash) "RECORD_HASH_MISMATCH record=$recHash zip=$zipHash"
Assert (-not [string]::IsNullOrWhiteSpace($tracked)) "ZIP_NOT_TRACKED: $zipPath"

"HEAD=$head"
"TAG=$tag"
"BRANCH=$br"
"RECORD_COMMIT=$recCommit"
"AUDIT_ZIP_SHA256=$zipHash"

$env:PYTHONPATH = (Get-Location).Path
python -c "from solver import solve; print('SOLVER 1+1 ->', solve('1+1'))"
python -c "import polars as pl; from kaggle_evaluation.aimo_3_gateway import AIMO3Gateway; g=AIMO3Gateway(); df=pl.DataFrame({'id':[0],'problem':['1+1']}); print(g.predict(df))"

"OK_SELF_AUDIT"
