import re, pathlib

def insert_pathfix(s: str) -> str:
    if "AUREON_PATHFIX" in s:
        return s
    lines = s.splitlines(True)
    i = 0
    # after shebang/encoding + initial imports
    while i < len(lines) and (lines[i].startswith("#!") or lines[i].lower().startswith("# -*-") or lines[i].strip()=="" or lines[i].lstrip().startswith("import ") or lines[i].lstrip().startswith("from ")):
        i += 1
        # stop once we passed a non-import after first imports
        if i < len(lines) and lines[i].strip()=="":
            # keep scanning through blank lines between import block
            j=i
            while j < len(lines) and lines[j].strip()=="":
                j+=1
            if j < len(lines) and (lines[j].lstrip().startswith("import ") or lines[j].lstrip().startswith("from ")):
                i=j
            else:
                i=j
                break
    patch = (
        "# AUREON_PATHFIX\n"
        "import os as _os, sys as _sys\n"
        "_ROOT = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))\n"
        "if _ROOT not in _sys.path: _sys.path.insert(0, _ROOT)\n"
        "\n"
    )
    lines.insert(i, patch)
    return "".join(lines)

def patch_solver(s: str) -> str:
    if "AUREON_DETERMINISM_PATCH" not in s:
        m = re.search(r'^(?:#!.*\n)?(?:#.*coding[:=].*\n)?', s)
        start = m.end(0) if m else 0
        # insert after initial imports block if possible; else top
        ins = 0
        lines = s.splitlines(True)
        ins = 0
        # keep shebang/encoding
        while ins < len(lines) and (lines[ins].startswith("#!") or lines[ins].lower().startswith("# -*-") or "coding" in lines[ins].lower()):
            ins += 1
        # keep leading comments/blanks
        while ins < len(lines) and (lines[ins].strip()=="" or lines[ins].lstrip().startswith("#")):
            ins += 1
        # keep contiguous import block
        while ins < len(lines) and (lines[ins].lstrip().startswith("import ") or lines[ins].lstrip().startswith("from ")):
            ins += 1
        pre = (
            "# AUREON_DETERMINISM_PATCH\n"
            "import os as _os\n"
            "_os.environ.setdefault('PYTHONHASHSEED','0')\n"
            "import unicodedata as _unicodedata\n"
            "import re as _re\n"
            "def _aureon_normalize(_t):\n"
            "    if _t is None: return ''\n"
            "    _t = _unicodedata.normalize('NFKC', str(_t))\n"
            "    _t = _t.replace('\\u200b','').replace('\\ufeff','').replace('\\u00a0',' ')\n"
            "    _t = _t.translate(str.maketrans({'−':'-','–':'-','—':'-','﹣':'-','‐':'-','-':'-'}))\n"
            "    _t = _re.sub(r'[ \\t]+',' ', _t)\n"
            "    _t = _re.sub(r'\\n{3,}','\\n\\n', _t)\n"
            "    return _t.strip()\n"
            "def _aureon_sorted_glob(*args, **kwargs):\n"
            "    import glob as _glob\n"
            "    return sorted(_glob.glob(*args, **kwargs))\n"
            "\n"
        )
        lines.insert(ins, pre)
        s = "".join(lines)

    # stabilize glob usage (best-effort, safe if glob not used)
    s = s.replace("glob.glob(", "_aureon_sorted_glob(")

    # stabilize mtime sort ties (best-effort)
    s = s.replace("key=lambda p: os.path.getmtime(p)", "key=lambda p: (os.path.getmtime(p), p)")

    # ensure normalize at solve() entry (module-level)
    def repl(m):
        indent = m.group(1)
        header = m.group(0)
        return header + f"{indent}    text = _aureon_normalize(text)\n"
    # only insert if first statement isn't already normalization
    out_lines = s.splitlines(True)
    out = []
    i = 0
    while i < len(out_lines):
        line = out_lines[i]
        m = re.match(r"^([ \t]*)def solve\s*\(\s*text\b.*\)\s*:\s*$", line)
        if m:
            out.append(line)
            # peek next non-empty line
            j = i + 1
            while j < len(out_lines) and out_lines[j].strip() == "":
                out.append(out_lines[j]); j += 1
            if j < len(out_lines) and "_aureon_normalize" in out_lines[j]:
                i = j
                continue
            out.append(m.group(1) + "    text = _aureon_normalize(text)\n")
            i = i + 1
            continue
        out.append(line)
        i += 1
    s = "".join(out)

    return s

def write_if_changed(path: pathlib.Path, new: str):
    old = path.read_text(encoding="utf-8")
    if old != new:
        path.write_text(new, encoding="utf-8")

root = pathlib.Path(".")
solver = root / "solver.py"
gw = root / "kaggle_evaluation" / "aimo_3_gateway.py"
srv = root / "kaggle_evaluation" / "aimo_3_inference_server.py"

write_if_changed(gw, insert_pathfix(gw.read_text(encoding="utf-8")))
write_if_changed(srv, insert_pathfix(srv.read_text(encoding="utf-8")))
write_if_changed(solver, patch_solver(solver.read_text(encoding="utf-8")))

print("PATCH_OK")
