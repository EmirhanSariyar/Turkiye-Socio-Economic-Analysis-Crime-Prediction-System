import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from config import PROCESSED_DATA_DIR


TARGET_COLUMN = "high_justice_risk"
MODEL_FILE_NAME = "province_year_modeling_2011_2021.csv"


def load_modeling_dataset() -> pd.DataFrame:
    file_path = PROCESSED_DATA_DIR / MODEL_FILE_NAME
    if not file_path.exists():
        raise FileNotFoundError(
            f"Modeling dataset not found at {file_path}. "
            "Run `python src/prepare_raw_data.py` and `python src/merge_master_data.py` first."
        )
    return pd.read_csv(file_path)


def train_baseline_model() -> None:
    df = load_modeling_dataset()

    numeric_features = [
        "population",
        "in_migration",
        "out_migration",
        "net_migration",
        "active_insured_total",
        "active_insured_share_of_population",
        "illiterate_rate",
        "upper_secondary_rate",
        "university_rate",
        "postgraduate_rate",
        "higher_education_share",
    ]
    categorical_features = ["geographical_region", "statistical_region"]

    available_numeric = [column for column in numeric_features if column in df.columns]
    available_categorical = [column for column in categorical_features if column in df.columns]

    feature_columns = available_numeric + available_categorical
    if not feature_columns:
        raise ValueError("No usable feature columns were found in the modeling dataset.")

    x = df[feature_columns].copy()
    y = df[TARGET_COLUMN]

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
            ("num", numeric_pipeline, available_numeric),
            ("cat", categorical_pipeline, available_categorical),
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
    print(f"Rows used: {len(df)}")
    print(f"Features used: {', '.join(feature_columns)}")
    print(classification_report(y_test, predictions, zero_division=0))


if __name__ == "__main__":
    train_baseline_model()
