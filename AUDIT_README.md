# AIMO-3 Submission Audit (Deterministic)

## Rule
Do NOT validate by rebuilding the zip with PowerShell `Compress-Archive` and comparing SHA256.
`Compress-Archive` zip bytes vary across environments (metadata/order/normalization).

## What to verify
1) Freeze invariants: HEAD == submit branches == tag
2) Banned imports/strings scan
3) Compile gate
4) Content truth: SUBMISSION_BLOB_SHA256.txt uses git blob bytes (CRLF-proof)
5) Deterministic rebuild: ONLY valid rebuild is the script below

## Deterministic rebuild command
python tools/deterministic_submission_artifact.py --zip_out <TEMP_ZIP> --hash_out SUBMISSION_BLOB_SHA256.txt

Properties:
- sources bytes from git blobs (git show HEAD:<path>)
- fixed entry order
- fixed timestamps (1980-01-01)
- ZIP_STORED (no compression)
- identical zip bytes everywhere
