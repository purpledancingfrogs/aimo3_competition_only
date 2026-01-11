from __future__ import annotations
import os, warnings
os.environ.setdefault("PYTHONWARNINGS", "ignore")
warnings.filterwarnings("ignore", category=SyntaxWarning)
warnings.filterwarnings("ignore", category=FutureWarning)

import polars as pl
import solver

def _clamp_0_99999(x) -> int:
    try:
        v = int(float(str(x).strip()))
    except Exception:
        return 0
    if v < 0: v = -v
    if v > 99999: v = 99999
    return v

def predict(*args, **kwargs) -> pl.DataFrame:
    """
    Expected gateway call pattern:
      - args[0]: polars.DataFrame (row batch) with columns including 'problem' and often 'id'
      - args[1]: polars.DataFrame with column 'id' (row.select('id')) may be provided
    Output:
      - polars.DataFrame with columns ['id','answer'] (Int64), same height as input batch
    """
    try:
        df = args[0] if (len(args) >= 1 and isinstance(args[0], pl.DataFrame)) else None
        id_df = args[1] if (len(args) >= 2 and isinstance(args[1], pl.DataFrame)) else None

        if df is None:
            return pl.DataFrame({"id":[0], "answer":[0]}).with_columns([
                pl.col("id").cast(pl.Int64),
                pl.col("answer").cast(pl.Int64),
            ])

        n = df.height
        # ids
        if id_df is not None and "id" in id_df.columns and id_df.height == n:
            ids = id_df["id"]
        elif "id" in df.columns:
            ids = df["id"]
        else:
            ids = pl.Series([0] * n)

        # prompts
        if "problem" in df.columns:
            prompts = df["problem"]
        else:
            prompts = pl.Series([""] * n)

        answers = []
        for p in prompts.to_list():
            try:
                raw = solver.solve(str(p))
                answers.append(_clamp_0_99999(raw))
            except Exception:
                answers.append(0)

        return pl.DataFrame({
            "id": ids.cast(pl.Int64),
            "answer": pl.Series(answers).cast(pl.Int64),
        })

    except Exception:
        return pl.DataFrame({"id":[0], "answer":[0]}).with_columns([
            pl.col("id").cast(pl.Int64),
            pl.col("answer").cast(pl.Int64),
        ])

from kaggle_evaluation.aimo_3_inference_server import AIMO3InferenceServer

if __name__ == "__main__":
    print("SERVER_START")
    AIMO3InferenceServer(predict).serve()