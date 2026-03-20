from pathlib import Path

import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


def build_sample_dataset() -> pd.DataFrame:
    """Create a small placeholder dataset until real data is added."""
    return pd.DataFrame(
        {
            "unemployment_rate": [8.1, 12.4, 10.0, 7.3, 15.2, 9.4, 11.1, 6.9],
            "education_index": [0.72, 0.51, 0.60, 0.78, 0.48, 0.67, 0.55, 0.80],
            "migration_rate": [1.2, 3.5, 2.2, 0.8, 4.1, 1.5, 2.8, 0.6],
            "region_type": ["urban", "urban", "mixed", "urban", "mixed", "rural", "urban", "rural"],
            "high_crime_risk": [0, 1, 1, 0, 1, 0, 1, 0],
        }
    )


def train_baseline_model() -> None:
    df = build_sample_dataset()

    x = df.drop(columns=["high_crime_risk"])
    y = df["high_crime_risk"]

    numeric_features = ["unemployment_rate", "education_index", "migration_rate"]
    categorical_features = ["region_type"]

    numeric_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )

    categorical_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("onehot", OneHotEncoder(handle_unknown="ignore")),
        ]
    )

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", numeric_pipeline, numeric_features),
            ("cat", categorical_pipeline, categorical_features),
        ]
    )

    model = Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("classifier", LogisticRegression(max_iter=1000)),
        ]
    )

    x_train, x_test, y_train, y_test = train_test_split(
        x, y, test_size=0.25, random_state=42, stratify=y
    )

    model.fit(x_train, y_train)
    predictions = model.predict(x_test)

    print("Baseline model trained successfully.")
    print(classification_report(y_test, predictions, zero_division=0))


if __name__ == "__main__":
    train_baseline_model()
