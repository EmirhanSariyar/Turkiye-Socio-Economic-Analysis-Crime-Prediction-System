import re
import unicodedata
from pathlib import Path

import pandas as pd


BASE_DIR = Path(__file__).resolve().parent.parent
EXTERNAL_DIR = BASE_DIR / "data" / "external"
RAW_DIR = BASE_DIR / "data" / "raw"


def slugify(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", str(value))
    ascii_value = normalized.encode("ascii", "ignore").decode("ascii")
    ascii_value = ascii_value.lower().strip()
    ascii_value = re.sub(r"[^a-z0-9]+", "_", ascii_value)
    return ascii_value.strip("_")


def clean_cell(value):
    if pd.isna(value):
        return None
    text = str(value).replace("\n", " ").replace("\r", " ").strip()
    text = re.sub(r"\s+", " ", text)
    return text or None


def normalize_numeric(value):
    if pd.isna(value):
        return None

    if isinstance(value, (int, float)) and not isinstance(value, bool):
        number = float(value)
        if number.is_integer():
            return int(number)
        return number

    text = str(value).strip()
    if not text:
        return None

    text = text.replace("\xa0", "").replace(" ", "")
    text = text.replace(".", "")
    text = text.replace(",", ".")
    text = text.replace("−", "-").replace("–", "-")
    text = re.sub(r"(?<=-)\s+", "", text)

    try:
        number = float(text)
    except ValueError:
        return None

    if number.is_integer():
        return int(number)
    return number


def normalize_columns(columns) -> list[str]:
    normalized = []
    for column in columns:
        cell = clean_cell(column) or "unnamed"
        normalized.append(slugify(cell))
    return normalized


def first_matching_column(columns: list[str], candidates: list[str]) -> str:
    for candidate in candidates:
        for column in columns:
            if candidate in column:
                return column
    raise KeyError(f"No matching column found for candidates: {candidates}")


def yearly_columns(columns: list[str]) -> list[str]:
    return [column for column in columns if re.fullmatch(r"\d{4}", column)]


def read_excel_with_header_detection(file_path: Path, engine: str | None = None) -> tuple[pd.DataFrame, int]:
    preview = pd.read_excel(file_path, header=None, engine=engine)

    header_row = None
    for idx in range(min(len(preview), 12)):
        row_values = [clean_cell(value) or "" for value in preview.iloc[idx].tolist()]
        row_text = " ".join(row_values)
        if "İl" in row_text or "Province" in row_text or "İBBS 3" in row_text or "İBBS 1" in row_text:
            header_row = idx
            break

    if header_row is None:
        raise ValueError(f"Could not detect header row for {file_path}")

    dataframe = pd.read_excel(file_path, header=header_row, engine=engine)
    dataframe.columns = normalize_columns(dataframe.columns)
    dataframe = dataframe.dropna(how="all")
    return dataframe, header_row


def process_sgk() -> pd.DataFrame:
    sgk_dir = EXTERNAL_DIR / "sgk"
    dataframes = []

    for file_path in sorted(sgk_dir.glob("*.csv")):
        df = pd.read_csv(file_path)
        df.columns = normalize_columns(df.columns)

        year_cols = [column for column in df.columns if re.fullmatch(r"\d{4}", column)]
        id_cols = [
            "sehir",
            "kategori",
            "gosterge",
            "deger",
            "cografibolge",
            "istatistikibolge",
        ]

        melted = df[id_cols + year_cols].melt(
            id_vars=id_cols,
            value_vars=year_cols,
            var_name="year",
            value_name="active_insured_total",
        )

        melted["province"] = melted["sehir"].map(clean_cell)
        melted["year"] = melted["year"].astype(int)
        melted["active_insured_total"] = melted["active_insured_total"].map(normalize_numeric)
        melted["category"] = melted["kategori"].map(clean_cell)
        melted["indicator"] = melted["gosterge"].map(clean_cell)
        melted["unit"] = melted["deger"].map(clean_cell)
        melted["geographical_region"] = melted["cografibolge"].map(clean_cell)
        melted["statistical_region"] = melted["istatistikibolge"].map(clean_cell)

        melted = melted.loc[melted["province"].notna()]
        melted = melted.loc[melted["province"].str.lower() != "türkiye"]

        dataframes.append(
            melted[
                [
                    "province",
                    "year",
                    "active_insured_total",
                    "category",
                    "indicator",
                    "unit",
                    "geographical_region",
                    "statistical_region",
                ]
            ]
        )

    result = pd.concat(dataframes, ignore_index=True).sort_values(["province", "year"])
    result = result.drop_duplicates(subset=["province", "year"], keep="last")
    return result


def process_migration() -> pd.DataFrame:
    migration_dir = EXTERNAL_DIR / "migration"
    dataframes = []

    for file_path in sorted(migration_dir.glob("*.xls")):
        df = pd.read_excel(file_path, header=2, engine="xlrd")
        df.columns = normalize_columns(df.columns)
        df = df.dropna(how="all")
        title_preview = pd.read_excel(file_path, header=None, nrows=2, engine="xlrd")
        title_text = " ".join(filter(None, [clean_cell(v) for v in title_preview.fillna("").iloc[0].tolist()]))
        match = re.search(r"(20\d{2})", title_text)
        if not match:
            raise ValueError(f"Could not infer year from migration file: {file_path.name}")
        year = int(match.group(1))

        province_col = first_matching_column(df.columns.tolist(), ["il", "province"])
        population_col = first_matching_column(df.columns.tolist(), ["toplam_nufus", "total_population"])
        in_migration_col = first_matching_column(df.columns.tolist(), ["aldigi_goc", "in_migration"])
        out_migration_col = first_matching_column(df.columns.tolist(), ["verdigi_goc", "out_migration"])
        net_migration_col = first_matching_column(df.columns.tolist(), ["net_goc", "net_migration"])
        net_rate_col = first_matching_column(df.columns.tolist(), ["net_goc_hizi", "rate_of_net_migration"])

        cleaned = pd.DataFrame(
            {
                "province": df[province_col].map(clean_cell),
                "year": year,
                "population": df[population_col].map(normalize_numeric),
                "in_migration": df[in_migration_col].map(normalize_numeric),
                "out_migration": df[out_migration_col].map(normalize_numeric),
                "net_migration": df[net_migration_col].map(normalize_numeric),
                "net_migration_rate": df[net_rate_col].map(normalize_numeric),
            }
        )

        cleaned = cleaned.loc[cleaned["province"].notna()]
        cleaned = cleaned.loc[~cleaned["province"].str.lower().str.contains("toplam")]
        cleaned = cleaned.loc[~cleaned["province"].str.startswith("0 ")]
        cleaned = cleaned.loc[~cleaned["province"].str.contains("TurkStat|TÜİK", case=False, na=False)]
        dataframes.append(cleaned)

    result = pd.concat(dataframes, ignore_index=True).sort_values(["province", "year"])
    result = result.drop_duplicates(subset=["province", "year"], keep="last")
    return result


def process_justice() -> pd.DataFrame:
    justice_file = next((EXTERNAL_DIR / "justice").glob("Adalet_İst_2011-2023*.xlsx"))
    excel_file = pd.ExcelFile(justice_file, engine="openpyxl")
    dataframes = []

    for sheet_name in excel_file.sheet_names:
        year_match = re.fullmatch(r"(20\d{2})_il", sheet_name)
        if not year_match:
            continue

        year = int(year_match.group(1))
        df = pd.read_excel(justice_file, sheet_name=sheet_name, header=2, engine="openpyxl")
        df = df.dropna(how="all")

        cleaned = pd.DataFrame(
            {
                "province": df.iloc[:, 3].map(clean_cell),
                "year": year,
                "investigation_files_total_load": df.iloc[:, 4].map(normalize_numeric),
                "investigation_files_carry_in": df.iloc[:, 5].map(normalize_numeric),
                "investigation_files_opened": df.iloc[:, 6].map(normalize_numeric),
                "investigation_files_closed": df.iloc[:, 7].map(normalize_numeric),
                "investigation_files_carry_out": df.iloc[:, 8].map(normalize_numeric),
            }
        )

        cleaned = cleaned.loc[cleaned["province"].notna()]
        cleaned = cleaned.loc[~cleaned["province"].str.contains("TÜRKİYE|TURKIYE|TOPLAM", case=False, na=False)]
        dataframes.append(cleaned)

    result = pd.concat(dataframes, ignore_index=True).sort_values(["province", "year"])
    result = result.drop_duplicates(subset=["province", "year"], keep="last")
    return result


def process_education() -> pd.DataFrame:
    education_dir = EXTERNAL_DIR / "education"
    dataframes = []

    for file_path in sorted(education_dir.glob("*.xls")):
        df = pd.read_excel(file_path, header=4, engine="xlrd")
        df = df.dropna(how="all")

        cleaned = pd.DataFrame(
            {
                "province": df.iloc[:, 4].map(clean_cell),
                "year": pd.to_numeric(df.iloc[:, 0], errors="coerce"),
                "education_population_6_plus": df.iloc[:, 6].map(normalize_numeric),
                "illiterate_total": df.iloc[:, 10].map(normalize_numeric),
                "literate_no_diploma_total": df.iloc[:, 14].map(normalize_numeric),
                "lower_secondary_total": df.iloc[:, 26].map(normalize_numeric),
                "upper_secondary_total": df.iloc[:, 30].map(normalize_numeric),
                "university_total": df.iloc[:, 34].map(normalize_numeric),
                "masters_total": df.iloc[:, 38].map(normalize_numeric),
                "doctorate_total": df.iloc[:, 42].map(normalize_numeric),
            }
        )

        cleaned["year"] = cleaned["year"].ffill().astype("Int64")
        cleaned = cleaned.loc[cleaned["province"].notna()]
        cleaned = cleaned.loc[~cleaned["province"].str.contains("Türkiye|TURKIYE", case=False, na=False)]
        cleaned["province"] = cleaned["province"].str.strip()
        cleaned["province"] = cleaned["province"].replace(
            {
                "Afyon": "Afyonkarahisar",
                "K.Maraş": "Kahramanmaraş",
            }
        )

        denominator = cleaned["education_population_6_plus"].replace({0: pd.NA})
        cleaned["illiterate_rate"] = cleaned["illiterate_total"] / denominator
        cleaned["upper_secondary_rate"] = cleaned["upper_secondary_total"] / denominator
        cleaned["university_rate"] = cleaned["university_total"] / denominator
        cleaned["postgraduate_rate"] = (
            (cleaned["masters_total"].fillna(0) + cleaned["doctorate_total"].fillna(0)) / denominator
        )

        dataframes.append(cleaned)

    result = pd.concat(dataframes, ignore_index=True).sort_values(["province", "year"])
    result = result.drop_duplicates(subset=["province", "year"], keep="last")
    result["year"] = result["year"].astype(int)
    return result


def process_meb_education() -> pd.DataFrame:
    meb_file = EXTERNAL_DIR / "education" / "meb_ortaogretim_okulasma_oranlari_il_bazli.xlsx"
    df = pd.read_excel(meb_file, sheet_name="Long Format", header=2, engine="openpyxl")
    df = df.dropna(how="all")

    cleaned = pd.DataFrame(
        {
            "tr_code": df.iloc[:, 0].map(clean_cell),
            "province": df.iloc[:, 1].map(clean_cell),
            "academic_year": df.iloc[:, 2].map(clean_cell),
            "upper_secondary_gross_enrollment_rate": df.iloc[:, 3].map(normalize_numeric),
            "general_secondary_gross_enrollment_rate": df.iloc[:, 4].map(normalize_numeric),
            "vocational_secondary_gross_enrollment_rate": df.iloc[:, 5].map(normalize_numeric),
        }
    )

    cleaned = cleaned.loc[cleaned["province"].notna()].copy()
    cleaned["province"] = cleaned["province"].str.strip()
    cleaned["province"] = cleaned["province"].replace(
        {
            "Afyon": "Afyonkarahisar",
            "K.Maras": "Kahramanmaras",
            "Kahramanmaras": "Kahramanmaras",
        }
    )

    # Align academic years like 2010-2011 to the ending calendar year (2011).
    cleaned["year"] = cleaned["academic_year"].str.extract(r"(20\d{2})$")[0]
    cleaned["year"] = pd.to_numeric(cleaned["year"], errors="coerce").astype("Int64")
    cleaned = cleaned.loc[cleaned["year"].notna()].copy()
    cleaned["year"] = cleaned["year"].astype(int)

    for column in [
        "upper_secondary_gross_enrollment_rate",
        "general_secondary_gross_enrollment_rate",
        "vocational_secondary_gross_enrollment_rate",
    ]:
        cleaned[column] = pd.to_numeric(cleaned[column], errors="coerce").round(2)

    cleaned = cleaned.drop_duplicates(subset=["province", "year"], keep="last")
    return cleaned.sort_values(["province", "year"]).reset_index(drop=True)


def process_children_national() -> pd.DataFrame:
    children_file = EXTERNAL_DIR / "children" / "Geliş nedeni ve cinsiyete göre güvenlik birimine gelen veya getirilen çocukların karıştığı olay sayısı.xls"
    df = pd.read_excel(children_file, header=None, engine="xlrd")

    year_row = df.iloc[3].tolist()
    category_row = df.iloc[4].tolist()
    total_row = df.iloc[5].tolist()
    pushed_into_crime_row = df.iloc[6].tolist()
    victim_row = df.iloc[9].tolist()
    witness_row = df.iloc[10].tolist()

    records = []
    for idx, raw_year in enumerate(year_row):
        year_text = clean_cell(raw_year)
        if not year_text:
            continue

        match = re.search(r"(20\d{2})", year_text)
        if not match:
            continue

        year = int(match.group(1))
        if idx + 2 >= len(category_row):
            continue

        records.append(
            {
                "year": year,
                "children_incidents_total": normalize_numeric(total_row[idx + 1]),
                "children_pushed_into_crime_total": normalize_numeric(pushed_into_crime_row[idx + 1]),
                "children_victim_total": normalize_numeric(victim_row[idx + 1]),
                "children_witness_total": normalize_numeric(witness_row[idx + 1]),
            }
        )

    return pd.DataFrame(records).sort_values("year").drop_duplicates(subset=["year"], keep="last")


def write_outputs() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    process_sgk().to_csv(RAW_DIR / "sgk_active_insured_2009_2024.csv", index=False)
    process_migration().to_csv(RAW_DIR / "migration_provincial.csv", index=False)
    process_justice().to_csv(RAW_DIR / "justice_provincial_2011_2021.csv", index=False)
    process_education().to_csv(RAW_DIR / "education_provincial_2021_2024.csv", index=False)
    process_meb_education().to_csv(RAW_DIR / "meb_secondary_gross_enrollment_2011_2025.csv", index=False)
    process_children_national().to_csv(RAW_DIR / "children_security_unit_national_2015_2024.csv", index=False)

    print("Wrote:")
    print(" - data/raw/sgk_active_insured_2009_2024.csv")
    print(" - data/raw/migration_provincial.csv")
    print(" - data/raw/justice_provincial_2011_2021.csv")
    print(" - data/raw/education_provincial_2021_2024.csv")
    print(" - data/raw/meb_secondary_gross_enrollment_2011_2025.csv")
    print(" - data/raw/children_security_unit_national_2015_2024.csv")


if __name__ == "__main__":
    write_outputs()
