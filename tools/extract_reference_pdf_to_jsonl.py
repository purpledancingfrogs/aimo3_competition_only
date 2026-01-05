import json, re, sys
from pathlib import Path

def _read_pdf_text(pdf_path: Path) -> str:
    try:
        from pypdf import PdfReader
    except Exception as e:
        raise SystemExit("MISSING_DEP:pypdf (run: python -m pip install pypdf)") from e
    r = PdfReader(str(pdf_path))
    parts = []
    for i, page in enumerate(r.pages):
        try:
            t = page.extract_text() or ""
        except Exception:
            t = ""
        if t.strip():
            parts.append(t)
    return "\n".join(parts)

def _split_problems(text: str):
    text = text.replace("\r\n", "\n")
    # conservative split: numbered items like "1." or "1)" on new lines
    pat = re.compile(r"(?m)^(?P<num>\d{1,3})[.)]\s+")
    hits = list(pat.finditer(text))
    if not hits:
        return []
    blocks = []
    for idx, h in enumerate(hits):
        start = h.start()
        end = hits[idx+1].start() if idx+1 < len(hits) else len(text)
        num = h.group("num")
        blk = text[start:end].strip()
        blocks.append((num, blk))
    return blocks

def _extract_expected(block: str):
    # optional: pull "Answer:" / "Final answer:" if present
    m = re.search(r"(?is)\b(?:answer|final answer)\b\s*[:\-]\s*([^\n]+)", block)
    if not m:
        return None
    s = m.group(1).strip()
    # keep only last integer token if present
    ints = re.findall(r"[-+]?\d+", s)
    return ints[-1] if ints else None

def main():
    if len(sys.argv) != 3:
        print("usage: extract_reference_pdf_to_jsonl.py <pdf_path> <out_jsonl>")
        raise SystemExit(2)
    pdf_path = Path(sys.argv[1])
    out_path = Path(sys.argv[2])
    if not pdf_path.exists():
        raise SystemExit(f"MISSING_PDF:{pdf_path}")
    text = _read_pdf_text(pdf_path)
    probs = _split_problems(text)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with out_path.open("w", encoding="utf-8") as f:
        for pid, blk in probs:
            expected = _extract_expected(blk)
            rec = {"id": pid, "text": blk, "expected": expected}
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            n += 1
    print(f"WROTE={n} -> {out_path}")

if __name__ == "__main__":
    main()
