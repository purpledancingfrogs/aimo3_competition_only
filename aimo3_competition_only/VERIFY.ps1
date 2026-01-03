param(
    [string]$Root = (Get-Location).Path
)

Write-Host "Recomputing SHA256 manifest..."

$out = Join-Path $Root "RECOMPUTED_SHA256.csv"

Get-ChildItem $Root -Recurse -File |
    Where-Object {
        $_.Name -ne "PROOF_MANIFEST_SHA256.csv" -and
        $_.FullName -ne $out
    } |
    Get-FileHash -Algorithm SHA256 |
    Sort-Object Path |
    Export-Csv $out -NoTypeInformation

Write-Host "Generated RECOMPUTED_SHA256.csv"
Write-Host "Next: compare with PROOF_MANIFEST_SHA256.csv"
