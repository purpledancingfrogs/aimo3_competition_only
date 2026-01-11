import os, sys
import polars as pl

# Expect solver.py in repo root (local gates already pass)
import solver

def _pick_problem_col(df: pl.DataFrame) -> str:
    for c in ["problem", "prompt", "question", "text", "content"]:
        if c in df.columns:
            return c
    # fallback: first string-like col, else first col
    for c in df.columns:
        if df[c].dtype in (pl.Utf8, pl.String):
            return c
    return df.columns[0]

def _ensure_pl_df(x):
    if isinstance(x, pl.DataFrame):
        return x
    try:
        import pandas as pd
        if isinstance(x, pd.DataFrame):
            return pl.from_pandas(x)
    except Exception:
        pass
    # last resort: stringify
    return pl.DataFrame({"id":[0], "problem":[str(x)]})

def predict(*args, **kwargs) -> pl.DataFrame:
    # Accept (test_df, sample_submission_df) or (test_df,) or kwargs
    test_df = None
    sample_df = None

    for a in args:
        if isinstance(a, pl.DataFrame) and test_df is None:
            test_df = a
        elif isinstance(a, pl.DataFrame) and sample_df is None:
            sample_df = a

    if test_df is None:
        cand = kwargs.get("test_df") or kwargs.get("test") or kwargs.get("df")
        test_df = _ensure_pl_df(cand if cand is not None else pl.DataFrame({"id":[0], "problem":[""]}))
    else:
        test_df = _ensure_pl_df(test_df)

    if sample_df is None:
        cand = kwargs.get("sample_submission") or kwargs.get("sample_df")
        if cand is not None:
            sample_df = _ensure_pl_df(cand)

    id_col = "id" if "id" in test_df.columns else (("id" if sample_df is None else ("id" if "id" in sample_df.columns else None)) or test_df.columns[0])
    prob_col = _pick_problem_col(test_df)

    ids = test_df[id_col].to_list()
    probs = test_df[prob_col].to_list()

    ans = []
    for p in probs:
        try:
            v = solver.solve(str(p))
        except Exception:
            v = 0
        try:
            v = int(v)
        except Exception:
            v = 0
        v = abs(v) % 1000
        ans.append(v)

    return pl.DataFrame({"id": ids, "answer": ans})

def _run_env_if_present():
    try:
        import aimo
    except Exception:
        return False

    env = aimo.make_env()
    it = env.iter_test()

    for batch in it:
        # expected: (test_df, sample_submission_df)
        if isinstance(batch, tuple) and len(batch) >= 2:
            test_df, sample_df = batch[0], batch[1]
            test_df = _ensure_pl_df(test_df)
            sample_df = _ensure_pl_df(sample_df)
            preds = predict(test_df, sample_df)
        else:
            test_df = _ensure_pl_df(batch)
            preds = predict(test_df)

        env.predict(preds)

    return True

if __name__ == "__main__":
    _run_env_if_present()