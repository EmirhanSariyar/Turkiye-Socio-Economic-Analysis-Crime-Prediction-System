import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from config import PROCESSED_DATA_DIR


RICH_TARGET_COLUMN = "high_justice_risk"
RICH_MODEL_FILE_NAME = "province_year_modeling_2011_2021.csv"
MASTER_FILE_NAME = "province_year_master_2011_2021.csv"


def load_csv_dataset(file_name: str) -> pd.DataFrame:
    file_path = PROCESSED_DATA_DIR / file_name
    if not file_path.exists():
        raise FileNotFoundError(
            f"Dataset not found at {file_path}. "
            "Run `python src/prepare_raw_data.py` and `python src/merge_master_data.py` first."
        )
    return pd.read_csv(file_path)


def train_variant(
    title: str,
    df: pd.DataFrame,
    target_column: str,
    numeric_features: list[str],
    categorical_features: list[str],
) -> None:
    available_numeric = [column for column in numeric_features if column in df.columns]
    available_categorical = [column for column in categorical_features if column in df.columns]

    feature_columns = available_numeric + available_categorical
    if not feature_columns:
        raise ValueError(f"No usable feature columns were found for variant: {title}")

    modeling_df = df.dropna(subset=[target_column]).copy()
    x = modeling_df[feature_columns].copy()
    y = modeling_df[target_column].astype(int)

    if y.nunique() < 2:
        raise ValueError(f"Variant '{title}' needs at least two target classes.")

    stratify_target = y if y.value_counts().min() >= 2 else None

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
        x,
        y,
        test_size=0.25,
        random_state=42,
        stratify=stratify_target,
    )

    model.fit(x_train, y_train)
    predictions = model.predict(x_test)

    print()
    print(f"=== {title} ===")
    print(f"Rows used: {len(modeling_df)}")
    print(f"Features used: {', '.join(feature_columns)}")
    print(classification_report(y_test, predictions, zero_division=0))


def build_wide_coverage_dataset() -> pd.DataFrame:
    df = load_csv_dataset(MASTER_FILE_NAME)
    df = df.dropna(subset=["investigation_files_opened", "active_insured_total"]).copy()

    # Year-relative target is fairer because justice file volume trends upward over time.
    yearly_median = df.groupby("year")["investigation_files_opened"].transform("median")
    df["high_justice_flow"] = (df["investigation_files_opened"] >= yearly_median).astype(int)
    return df


def train_baseline_models() -> None:
    rich_df = load_csv_dataset(RICH_MODEL_FILE_NAME)

    rich_numeric_features = [
        "population",
        "in_migration",
        "out_migration",
        "net_migration",
        "active_insured_total",
        "active_insured_share_of_population",
        "general_secondary_gross_enrollment_rate",
        "vocational_secondary_gross_enrollment_rate",
        "illiterate_rate",
        "upper_secondary_rate",
        "university_rate",
        "postgraduate_rate",
        "higher_education_share",
    ]
    rich_categorical_features = ["geographical_region", "statistical_region"]

    train_variant(
        title="Rich Feature Rate Model",
        df=rich_df,
        target_column=RICH_TARGET_COLUMN,
        numeric_features=rich_numeric_features,
        categorical_features=rich_categorical_features,
    )

    wide_df = build_wide_coverage_dataset()
    wide_numeric_features = [
        "year",
        "active_insured_total",
        "general_secondary_gross_enrollment_rate",
        "vocational_secondary_gross_enrollment_rate",
    ]
    wide_categorical_features = ["geographical_region", "statistical_region"]

    train_variant(
        title="Wide Coverage Flow Model",
        df=wide_df,
        target_column="high_justice_flow",
        numeric_features=wide_numeric_features,
        categorical_features=wide_categorical_features,
    )


if __name__ == "__main__":
    train_baseline_models()
