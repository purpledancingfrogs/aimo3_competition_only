import json, csv, time, subprocess, sys, pathlib, re

jl = pathlib.Path("tools/reference_problems.jsonl")
rows = [json.loads(x) for x in jl.read_text(encoding="utf-8").splitlines() if x.strip()]

def parse_int(s: str):
    # last integer in stdout
    m = re.findall(r"-?\d+", s)
    return int(m[-1]) if m else None

out_csv = pathlib.Path("tools/regression_results.csv")
out_fail = pathlib.Path("tools/regression_failures.txt")

fail_lines = []
with out_csv.open("w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["id","status","answer","elapsed_ms","stdout_tail"])
    for r in rows:
        pid = r.get("id")
        text = r.get("text","")
        t0 = time.time()
        try:
            p = subprocess.run(
                [sys.executable, "solver.py"],
                input=text.encode("utf-8", errors="ignore"),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                timeout=30
            )
            out = p.stdout.decode("utf-8", errors="ignore")
            ans = parse_int(out)
            status = "OK" if (p.returncode == 0 and ans is not None) else f"BAD(rc={p.returncode},ans={ans})"
        except subprocess.TimeoutExpired:
            out = "TIMEOUT"
            ans = None
            status = "TIMEOUT"
        elapsed_ms = int((time.time() - t0) * 1000)
        tail = out[-400:].replace("\r"," ").replace("\n"," ").strip()
        w.writerow([pid, status, ans, elapsed_ms, tail])
        if status != "OK":
            fail_lines.append(f"ID={pid} STATUS={status}\n{tail}\n")

out_fail.write_text("\n".join(fail_lines), encoding="utf-8")
print(f"WROTE {out_csv}")
print(f"WROTE {out_fail} (FAILS={len(fail_lines)})")
