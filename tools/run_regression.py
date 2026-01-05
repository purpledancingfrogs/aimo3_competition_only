import json, csv, time, re, pathlib, importlib, sys

rows = [json.loads(x) for x in pathlib.Path("tools/reference_problems.jsonl").read_text(encoding="utf-8").splitlines() if x.strip()]

def parse_last_int(s: str):
    m = re.findall(r"-?\d+", s)
    return int(m[-1]) if m else None

# Resolve callable deterministically:
# Priority: inference_server.predict / inference_server.infer / inference_server.solve / solver.solve / solver.predict / solver.Solver().solve
callable_fn = None
callable_name = None

def pick_callable():
    global callable_fn, callable_name

    # Try inference_server first (matches Kaggle runtime path)
    try:
        ims = importlib.import_module("kaggle_evaluation.aimo_3_inference_server")
        for name in ["predict", "inference", "infer", "solve", "solve_one", "solve_problem"]:
            fn = getattr(ims, name, None)
            if callable(fn):
                callable_fn = fn
                callable_name = f"inference_server.{name}"
                return
    except Exception:
        pass

    # Then solver module
    try:
        sm = importlib.import_module("solver")
        for name in ["solve", "predict", "infer", "answer", "run_one", "solve_one", "solve_problem"]:
            fn = getattr(sm, name, None)
            if callable(fn):
                callable_fn = fn
                callable_name = f"solver.{name}"
                return
        # Class-based
        for cname in ["Solver", "Model", "AIMO", "AimoSolver"]:
            C = getattr(sm, cname, None)
            if C is not None:
                try:
                    obj = C()
                    for mname in ["solve", "predict", "infer", "run"]:
                        fn = getattr(obj, mname, None)
                        if callable(fn):
                            callable_fn = fn
                            callable_name = f"solver.{cname}().{mname}"
                            return
                except Exception:
                    continue
    except Exception:
        pass

pick_callable()
if callable_fn is None:
    print("ERROR: could not resolve solver callable")
    sys.exit(2)

print("USING_CALLABLE:", callable_name)

out_csv = pathlib.Path("tools/regression_results.csv")
out_fail = pathlib.Path("tools/regression_failures.txt")

fails = []
ok = wrong = bad = 0

with out_csv.open("w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["id","status","expected","got","elapsed_ms","callable"])
    for r in rows:
        pid = r["id"]
        exp = r.get("expected")
        text = r.get("text","")

        t0 = time.time()
        try:
            # Support multiple signatures deterministically
            got = None
            try:
                res = callable_fn(text)
            except TypeError:
                try:
                    res = callable_fn({"question": text, "prompt": text, "input": text, "text": text})
                except TypeError:
                    res = callable_fn(pid, text)

            if isinstance(res, int):
                got = res
            elif isinstance(res, str):
                got = parse_last_int(res)
            elif res is None:
                got = None
            else:
                got = parse_last_int(str(res))

            if got is None:
                status = "BAD(got=None)"
                bad += 1
            elif exp is not None and got != exp:
                status = "WRONG"
                wrong += 1
            else:
                status = "OK"
                ok += 1
        except Exception as e:
            status = f"BAD({type(e).__name__})"
            got = None
            bad += 1

        ms = int((time.time() - t0) * 1000)
        w.writerow([pid, status, exp, got, ms, callable_name])

        if status != "OK":
            fails.append(f"ID={pid} STATUS={status} EXPECTED={exp} GOT={got} CALLABLE={callable_name}")

out_fail.write_text("\n".join(fails) + ("\n" if fails else ""), encoding="utf-8")
print(f"TOTAL={len(rows)} OK={ok} WRONG={wrong} BAD={bad}")
print(f"WROTE {out_csv}")
print(f"WROTE {out_fail}")
