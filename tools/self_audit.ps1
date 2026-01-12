# Simple hash check
$head = git rev-parse HEAD
$expected = "7b64214522812ee83f77c02118fdd29b469f095a"
if ($head -eq $expected) {
    exit 0
} else {
    Write-Host "Hash mismatch: $head vs $expected"
    exit 1
}
