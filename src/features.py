import pandas as pd


def prepare_features(df: pd.DataFrame, target_column: str) -> tuple[pd.DataFrame, pd.Series]:
    """Split dataframe into features and target."""
    if target_column not in df.columns:
        raise ValueError(f"Target column '{target_column}' was not found in the dataset.")

    x = df.drop(columns=[target_column])
    y = df[target_column]
    return x, y
