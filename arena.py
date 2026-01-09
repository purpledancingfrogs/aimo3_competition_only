import solver, sys

dataset = [
    ("2+2", "4"),
    ("Solve 2*x = 8 for x", "4"),
    ("What is 3 times 3?", "9"),
    ("15 mod 4", "3"),
    ("Solve x - 5 = 10", "15"),
    ("gcd(8, 12)", "4"),
    ("Evaluate 10 + 20", "30"),
    ("100 divided by 5", "20"),
    ("2*x + 3 = 11", "4"),
    ("Find the smallest prime greater than 10", "11"),
]

print(f"[ARENA] Loaded {len(dataset)} verification samples.")

problems  = [p for p,_ in dataset]
expected  = [a for _,a in dataset]

try:
    print("[ARENA] Sending batch to solver...")
    results = solver.predict(problems)

    correct = 0
    for i, (res, exp) in enumerate(zip(results, expected), start=1):
        got = str(res).strip()
        want = str(exp).strip()
        if got == want:
            correct += 1
            print(f"Problem {i}: PASS ({got})")
        else:
            print(f"Problem {i}: FAIL (Got '{got}', Expected '{want}')")

    print("-" * 30)
    print(f"CORRECT={correct} MISSES={len(dataset)-correct}")
    sys.exit(0 if correct == len(dataset) else 1)

except Exception as e:
    print(f"[ARENA] CRITICAL ERROR: {e}")
    import traceback; traceback.print_exc()
    sys.exit(1)
