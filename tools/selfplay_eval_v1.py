# tools/selfplay_eval_v1.py
from __future__ import annotations
import json, time, statistics
import solver

def main():
    rows=[]
    with open("tools/selfplay_v1.jsonl","r",encoding="utf-8") as f:
        for ln in f:
            rows.append(json.loads(ln))
    times=[]
    ok=0
    bad=[]
    for r in rows:
        t0=time.time()
        try:
            out = solver.Solver().solve(r["prompt"])
            out = str(out).strip()
            pred = int(out)
        except Exception as e:
            pred = 0
        dt=time.time()-t0
        times.append(dt)
        if pred == int(r["answer"]):
            ok += 1
        else:
            bad.append({"id":r["id"],"tag":r["tag"],"pred":pred,"ans":int(r["answer"]), "prompt":r["prompt"][:220]})
    acc=ok/len(rows)
    p90=statistics.quantiles(times,n=10)[8] if len(times)>=10 else max(times)
    print(f"SELFPLAY rows={len(rows)} ok={ok} acc={acc:.6f} t_med={statistics.median(times):.4f}s t_p90={p90:.4f}s t_max={max(times):.4f}s")
    with open("tools/selfplay_failures_v1.json","w",encoding="utf-8") as f:
        json.dump(bad[:200], f, ensure_ascii=False, indent=2)
    print("FAILURES_WROTE tools/selfplay_failures_v1.json", len(bad))
if __name__=="__main__":
    main()
