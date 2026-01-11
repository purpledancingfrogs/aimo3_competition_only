import sys
import polars as pl

def solve(problem_text: str) -> int:
    return 0

def predict(*args, **kwargs) -> pl.DataFrame:
    try:
        if args and isinstance(args[0], pl.DataFrame):
            df = args[0]
            id_series = df["id"]
            problem_series = df["problem"]
        elif args and isinstance(args[0], pl.Series):
            id_series = args[0]
            problem_series = args[1] if len(args) > 1 else pl.Series([""])
        else:
            id_series = pl.Series([0])
            problem_series = pl.Series([kwargs.get("problem", kwargs.get("prompt", ""))])

        raw_answers = [solve(p) for p in problem_series.to_list()]
        answers = [abs(int(a)) % 1000 for a in raw_answers]

        return pl.DataFrame({
            "id": id_series.cast(pl.Int64),
            "answer": pl.Series(answers).cast(pl.Int64),
        })
    except Exception as e:
        print(f"Error in predict: {e}", file=sys.stderr)
        return pl.DataFrame({
            "id": pl.Series([0]).cast(pl.Int64),
            "answer": pl.Series([0]).cast(pl.Int64),
        })

from kaggle_evaluation.aimo_3.inference_server import AIMO3InferenceServer
inference_server = AIMO3InferenceServer(predict)
inference_server.serve()