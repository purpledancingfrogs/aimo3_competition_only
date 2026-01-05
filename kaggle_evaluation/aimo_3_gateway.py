"""Gateway notebook for https://www.kaggle.com/competitions/ai-mathematical-olympiad-progress-prize-3"""

import os
from collections.abc import Generator

import kaggle_evaluation.core.templates
import polars as pl
from kaggle_evaluation.core.base_gateway import (
    GatewayRuntimeError,
    GatewayRuntimeErrorType,
)

# Set to True during the private rerun to disable shuffling
USE_PRIVATE_SET = False


class AIMO3Gateway(kaggle_evaluation.core.templates.Gateway):
    def __init__(self, data_paths=None):
        self.data_paths = data_paths or []
        self.unpack_data_paths()

    def unpack_data_paths(self):
        if self.data_paths:
            base = self.data_paths[0]
            self.test_path = os.path.join(base, "test.csv")
        else:
            self.test_path = "/kaggle/input/ai-mathematical-olympiad-progress-prize-3/test.csv"

    def generate_data_batches(self) -> Generator[tuple[pl.DataFrame, pl.DataFrame], None, None]:
        random_seed = int.from_bytes(os.urandom(4), byteorder="big")

        test = pl.read_csv(self.test_path)
        if not USE_PRIVATE_SET:
            test = test.sample(fraction=1.0, shuffle=True, with_replacement=False, seed=random_seed)

        for row in test.iter_slices(n_rows=1):
            yield row, row.select("id")

    def predict(self, data_batch: pl.DataFrame) -> pl.DataFrame:
        try:
            from solver import solve as solve_one
        except Exception as e:
            raise GatewayRuntimeError(GatewayRuntimeErrorType.RUNTIME_ERROR, f"Failed to import solver: {e}")

        probs = data_batch.select("problem").to_series().to_list()
        outs = []
        for p in probs:
            try:
                v = solve_one(p)
                s = str(v).strip()
                outs.append(int(s))
            except Exception:
                outs.append(0)
        return pl.DataFrame({"answer": outs})

    def competition_specific_validation(self, prediction_batch, row_ids, data_batch) -> None:
        pass


if __name__ == "__main__":
    if os.getenv("KAGGLE_IS_COMPETITION_RERUN"):
        gateway = AIMO3Gateway()
        gateway.run()
    else:
        print("Skipping run for now")
