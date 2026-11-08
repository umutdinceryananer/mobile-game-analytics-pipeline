"""Write a fabricated Cookie-Cats-shaped raw file so CI can run without Kaggle.

The real dataset is not in this repository. Every value written here is made up,
so results built on this file say nothing about Cookie Cats and are never reported.
The row count matches the real file because the statistical tests need that sample
size.
"""

from pathlib import Path

import numpy as np
import pandas as pd

RAW_PATH = Path(__file__).resolve().parents[1] / "data" / "raw" / "cookie_cats.csv"
N_ROWS = 90_189
SEED = 2024


def main() -> None:
    if RAW_PATH.exists():
        raise FileExistsError(f"{RAW_PATH} already exists; refusing to overwrite it.")

    rng = np.random.default_rng(SEED)
    raw = pd.DataFrame(
        {
            "userid": np.arange(1000, 1000 + N_ROWS),
            "version": rng.choice(["gate_30", "gate_40"], N_ROWS),
            "sum_gamerounds": np.floor(rng.lognormal(2.8, 1.5, N_ROWS)).astype(int),
            "retention_1": False,
            "retention_7": False,
        }
    )
    RAW_PATH.parent.mkdir(parents=True, exist_ok=True)
    raw.to_csv(RAW_PATH, index=False)
    print(f"Fabricated raw data written to {RAW_PATH}")


if __name__ == "__main__":
    main()
