import json, csv, time, subprocess, sys, pathlib, re

jl = pathlib.Path("tools/reference_problems.jsonl")
rows = [json.loads(x) for x in jl.read_text(encoding="utf-8").splitlines() if x.strip()]

def parse_last_int(s: str):
    m = re.findall(r"-?\d+", s)
    return int(m[-1]) if m else None

out_csv = pathlib.Path("tools/regression_results.csv")
out_fail = pathlib.Path("tools/regression_failures.txt")

fails = []
ok = wrong = bad = timeout = 0

with out_csv.open("w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["id","status","expected","got","elapsed_ms","stdout_tail"])
    for r in rows:
        pid = r["id"]
        text = r.get("text","")
        exp = r.get("expected", None)

        t0 = time.time()
        try:
            p = subprocess.run(
                [sys.executable, "solver.py"],
                input=text.encode("utf-8", errors="ignore"),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                timeout=45
            )
            out = p.stdout.decode("utf-8", errors="ignore")
            got = parse_last_int(out)
            if p.returncode != 0 or got is None:
                status = f"BAD(rc={p.returncode},got={got})"
                bad += 1
            elif exp is not None and got != exp:
                status = "WRONG"
                wrong += 1
            else:
                status = "OK"
                ok += 1
        except subprocess.TimeoutExpired:
            out = "TIMEOUT"
            got = None
            status = "TIMEOUT"
            timeout += 1

        ms = int((time.time() - t0) * 1000)
        tail = out[-400:].replace("\r"," ").replace("\n"," ").strip()
        w.writerow([pid, status, exp, got, ms, tail])

        if status != "OK":
            fails.append(f"ID={pid} STATUS={status} EXPECTED={exp} GOT={got}\n{tail}\n")

out_fail.write_text("\n".join(fails), encoding="utf-8")
print(f"TOTAL={len(rows)} OK={ok} WRONG={wrong} BAD={bad} TIMEOUT={timeout}")
print(f"WROTE {out_csv}")
print(f"WROTE {out_fail}")
