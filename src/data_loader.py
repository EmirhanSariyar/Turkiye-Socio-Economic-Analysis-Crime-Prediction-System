from pathlib import Path

import pandas as pd


def load_csv_dataset(file_path: str | Path) -> pd.DataFrame:
    """Load a CSV dataset into a pandas DataFrame."""
    return pd.read_csv(file_path)
