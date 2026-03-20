import re
import unicodedata
from pathlib import Path

import pandas as pd


BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / "data" / "raw"
PROCESSED_DIR = BASE_DIR / "data" / "processed"

BASELINE_START_YEAR = 2011
BASELINE_END_YEAR = 2021

PROVINCE_ALIASES = {
    "afyon": "afyonkarahisar",
    "maras": "kahramanmaras",
    "kahramanmaras": "kahramanmaras",
    "sanliurfa": "sanliurfa",
    "tekirdag": "tekirdag",
    "kirikkale": "kirikkale",
    "kirklareli": "kirklareli",
    "kirsehir": "kirsehir",
    "usak": "usak",
    "igdir": "igdir",
    "canakkale": "canakkale",
    "corum": "corum",
    "eskisehir": "eskisehir",
    "gumushane": "gumushane",
}


def normalize_province_name(value: str) -> str:
    text = str(value).strip().lower()
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^a-z0-9]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return PROVINCE_ALIASES.get(text, text.replace(" ", ""))


def load_csv(file_name: str) -> pd.DataFrame:
    file_path = RAW_DIR / file_name
    if not file_path.exists():
        raise FileNotFoundError(
            f"Raw file not found: {file_path}. Run `python src/prepare_raw_data.py` first."
        )
    return pd.read_csv(file_path)


def with_standard_keys(df: pd.DataFrame) -> pd.DataFrame:
    frame = df.copy()
    frame["province"] = frame["province"].astype(str).str.strip()
    frame["province_key"] = frame["province"].map(normalize_province_name)
    frame["year"] = pd.to_numeric(frame["year"], errors="coerce").astype("Int64")
    frame = frame.loc[frame["year"].notna()].copy()
    frame["year"] = frame["year"].astype(int)
    return frame


def build_baseline_year_frame(provinces: pd.Series) -> pd.DataFrame:
    unique_provinces = sorted(provinces.dropna().unique())
    records = []
    for province_key in unique_provinces:
        for year in range(BASELINE_START_YEAR, BASELINE_END_YEAR + 1):
            records.append({"province_key": province_key, "year": year})
    return pd.DataFrame(records)


def merge_sources() -> pd.DataFrame:
    justice = with_standard_keys(load_csv("justice_provincial_2011_2021.csv"))
    sgk = with_standard_keys(load_csv("sgk_active_insured_2009_2024.csv"))
    migration = with_standard_keys(load_csv("migration_provincial.csv"))
    education = with_standard_keys(load_csv("education_provincial_2021_2024.csv"))

    justice = justice.loc[justice["year"].between(BASELINE_START_YEAR, BASELINE_END_YEAR)]
    sgk = sgk.loc[sgk["year"].between(BASELINE_START_YEAR, BASELINE_END_YEAR)]
    migration = migration.loc[migration["year"].between(BASELINE_START_YEAR, BASELINE_END_YEAR)]
    education = education.loc[education["year"].between(BASELINE_START_YEAR, BASELINE_END_YEAR)]

    province_name_map = (
        justice[["province_key", "province"]]
        .dropna()
        .drop_duplicates(subset=["province_key"])
        .rename(columns={"province": "province_name"})
    )

    master = build_baseline_year_frame(justice["province_key"])
    master = master.merge(province_name_map, on="province_key", how="left")

    justice_columns = [
        "province_key",
        "year",
        "investigation_files_total_load",
        "investigation_files_carry_in",
        "investigation_files_opened",
        "investigation_files_closed",
    ]
    if "investigation_files_carry_out" in justice.columns:
        justice_columns.append("investigation_files_carry_out")

    sgk_columns = [
        "province_key",
        "year",
        "active_insured_total",
        "geographical_region",
        "statistical_region",
    ]
    migration_columns = [
        "province_key",
        "year",
        "population",
        "in_migration",
        "out_migration",
        "net_migration",
        "net_migration_rate",
    ]
    education_columns = [
        "province_key",
        "year",
        "education_population_6_plus",
        "illiterate_total",
        "literate_no_diploma_total",
        "lower_secondary_total",
        "upper_secondary_total",
        "university_total",
        "masters_total",
        "doctorate_total",
        "illiterate_rate",
        "upper_secondary_rate",
        "university_rate",
        "postgraduate_rate",
    ]

    master = master.merge(justice[justice_columns], on=["province_key", "year"], how="left")
    master = master.merge(sgk[sgk_columns], on=["province_key", "year"], how="left")
    master = master.merge(migration[migration_columns], on=["province_key", "year"], how="left")
    master = master.merge(education[education_columns], on=["province_key", "year"], how="left")

    master = master.rename(columns={"province_name": "province"})

    population_denominator = master["population"].replace({0: pd.NA})
    education_denominator = master["education_population_6_plus"].replace({0: pd.NA})

    master["investigation_files_opened_per_100k"] = (
        master["investigation_files_opened"] / population_denominator * 100000
    )
    master["investigation_files_total_load_per_100k"] = (
        master["investigation_files_total_load"] / population_denominator * 100000
    )
    master["active_insured_share_of_population"] = (
        master["active_insured_total"] / population_denominator
    )
    master["migration_turnover_rate"] = (
        (master["in_migration"] + master["out_migration"]) / population_denominator
    )
    master["higher_education_share"] = (
        (master["university_total"] + master["masters_total"] + master["doctorate_total"])
        / education_denominator
    )

    ordered_columns = [
        "province",
        "province_key",
        "year",
        "geographical_region",
        "statistical_region",
        "population",
        "in_migration",
        "out_migration",
        "net_migration",
        "net_migration_rate",
        "active_insured_total",
        "active_insured_share_of_population",
        "education_population_6_plus",
        "illiterate_total",
        "literate_no_diploma_total",
        "lower_secondary_total",
        "upper_secondary_total",
        "university_total",
        "masters_total",
        "doctorate_total",
        "illiterate_rate",
        "upper_secondary_rate",
        "university_rate",
        "postgraduate_rate",
        "higher_education_share",
        "investigation_files_total_load",
        "investigation_files_carry_in",
        "investigation_files_opened",
        "investigation_files_closed",
        "investigation_files_total_load_per_100k",
        "investigation_files_opened_per_100k",
    ]

    if "investigation_files_carry_out" in master.columns:
        ordered_columns.insert(29, "investigation_files_carry_out")

    master = master[ordered_columns].sort_values(["province", "year"]).reset_index(drop=True)
    return master


def build_modeling_frame(master: pd.DataFrame) -> pd.DataFrame:
    modeling = master.copy()
    modeling = modeling.loc[
        modeling[
            [
                "population",
                "active_insured_total",
                "net_migration",
                "investigation_files_opened",
            ]
        ].notna().all(axis=1)
    ].copy()

    median_threshold = modeling["investigation_files_opened_per_100k"].median()
    modeling["high_justice_risk"] = (
        modeling["investigation_files_opened_per_100k"] >= median_threshold
    ).astype(int)
    return modeling


def write_outputs() -> None:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    master = merge_sources()
    modeling = build_modeling_frame(master)

    master.to_csv(PROCESSED_DIR / "province_year_master_2011_2021.csv", index=False)
    modeling.to_csv(PROCESSED_DIR / "province_year_modeling_2011_2021.csv", index=False)

    print("Wrote:")
    print(" - data/processed/province_year_master_2011_2021.csv")
    print(" - data/processed/province_year_modeling_2011_2021.csv")


if __name__ == "__main__":
    write_outputs()
