import os
from pypdf import PdfReader

pdf_path = "AIMO3_Reference_Problems.pdf"
out_path = os.path.join("tools", "reference_dump.txt")

r = PdfReader(pdf_path)

with open(out_path, "w", encoding="utf-8") as f:
    f.write(f"PDF={pdf_path}\nPAGES={len(r.pages)}\n")
    for i, page in enumerate(r.pages, start=1):
        f.write(f"\n\n===== PAGE {i}/{len(r.pages)} =====\n")
        text = page.extract_text() or ""
        f.write(text)

print(f"WROTE {out_path}")
