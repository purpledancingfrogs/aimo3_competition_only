import sys
from pathlib import Path

def main():
    if len(sys.argv) < 2:
        print("usage: python tools/eval_local.py <csv_path> [problem_col=problem] [answer_col=answer]")
        return 2
    csv_path = Path(sys.argv[1])
    prob_col = sys.argv[2] if len(sys.argv) >= 3 else "problem"
    ans_col  = sys.argv[3] if len(sys.argv) >= 4 else "answer"
    import polars as pl
    from solver import solve

    df = pl.read_csv(csv_path)
    if prob_col not in df.columns:
        raise SystemExit(f"missing column: {prob_col}")
    has_labels = ans_col in df.columns

    probs = df[prob_col].to_list()
    preds = []
    for p in probs:
        try:
            preds.append(int(str(solve(p)).strip()))
        except Exception:
            preds.append(0)

    out = df.with_columns(pl.Series("pred", preds))

    if has_labels:
        y = out[ans_col].cast(pl.Int64, strict=False)
        ok = (out["pred"] == y).fill_null(False)
        correct = int(ok.sum())
        total = out.height
        print(f"correct={correct} total={total} acc={correct/total:.4f}")
    else:
        print("no labels found; wrote preds only")

    out_path = csv_path.with_suffix(".pred.csv")
    out.write_csv(out_path)
    print(f"wrote: {out_path}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
