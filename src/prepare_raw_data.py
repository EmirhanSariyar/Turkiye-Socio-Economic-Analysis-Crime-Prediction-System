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
        df, _ = read_excel_with_header_detection(file_path, engine="xlrd")
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
        df.columns = normalize_columns(df.columns)
        df = df.dropna(how="all")

        province_col = first_matching_column(df.columns.tolist(), ["il_adi"])
        total_col = first_matching_column(df.columns.tolist(), ["toplam", "yil_ici_yuk"])
        carry_in_col = first_matching_column(df.columns.tolist(), ["gecen_yildan_devir"])
        opened_col = first_matching_column(df.columns.tolist(), ["yil_icinde_acilan"])
        closed_col = first_matching_column(df.columns.tolist(), ["karara_baglanan"])

        carry_out_col = None
        for candidate in ["gelecek_yila_devir", "gelecek_yila_devredilen", "gelecek_yila_devir_files"]:
            try:
                carry_out_col = first_matching_column(df.columns.tolist(), [candidate])
                break
            except KeyError:
                continue

        cleaned = pd.DataFrame(
            {
                "province": df[province_col].map(clean_cell),
                "year": year,
                "investigation_files_total_load": df[total_col].map(normalize_numeric),
                "investigation_files_carry_in": df[carry_in_col].map(normalize_numeric),
                "investigation_files_opened": df[opened_col].map(normalize_numeric),
                "investigation_files_closed": df[closed_col].map(normalize_numeric),
            }
        )

        if carry_out_col is not None:
            cleaned["investigation_files_carry_out"] = df[carry_out_col].map(normalize_numeric)

        cleaned = cleaned.loc[cleaned["province"].notna()]
        cleaned = cleaned.loc[~cleaned["province"].str.lower().str.contains("türkiye")]
        dataframes.append(cleaned)

    result = pd.concat(dataframes, ignore_index=True).sort_values(["province", "year"])
    result = result.drop_duplicates(subset=["province", "year"], keep="last")
    return result


def process_education() -> pd.DataFrame:
    education_dir = EXTERNAL_DIR / "education"
    dataframes = []

    for file_path in sorted(education_dir.glob("*.xls")):
        df = pd.read_excel(file_path, header=4, engine="xlrd")
        df.columns = normalize_columns(df.columns)
        df = df.dropna(how="all")

        year_col = first_matching_column(df.columns.tolist(), ["yil_year"])
        province_col = first_matching_column(df.columns.tolist(), ["il_adi"])
        total_col = first_matching_column(df.columns.tolist(), ["toplam_total"])
        illiterate_col = first_matching_column(df.columns.tolist(), ["okuma_yazma_bilmeyen"])
        literate_no_diploma_col = first_matching_column(
            df.columns.tolist(),
            ["okuma_yazma_bilen_fakat_bir_okul_bitirmeyen"],
        )
        lower_secondary_col = first_matching_column(
            df.columns.tolist(),
            ["ortaokul_ve_dengi_meslek_okulu"],
        )
        upper_secondary_col = first_matching_column(
            df.columns.tolist(),
            ["lise_ve_dengi_meslek_okulu"],
        )
        university_col = first_matching_column(
            df.columns.tolist(),
            ["yuksekokul_veya_fakulte"],
        )
        masters_col = first_matching_column(df.columns.tolist(), ["yuksek_lisans"])
        doctorate_col = first_matching_column(df.columns.tolist(), ["doktora"])

        cleaned = pd.DataFrame(
            {
                "province": df[province_col].map(clean_cell),
                "year": pd.to_numeric(df[year_col], errors="coerce"),
                "education_population_6_plus": df[total_col].map(normalize_numeric),
                "illiterate_total": df[illiterate_col].map(normalize_numeric),
                "literate_no_diploma_total": df[literate_no_diploma_col].map(normalize_numeric),
                "lower_secondary_total": df[lower_secondary_col].map(normalize_numeric),
                "upper_secondary_total": df[upper_secondary_col].map(normalize_numeric),
                "university_total": df[university_col].map(normalize_numeric),
                "masters_total": df[masters_col].map(normalize_numeric),
                "doctorate_total": df[doctorate_col].map(normalize_numeric),
            }
        )

        cleaned["year"] = cleaned["year"].ffill().astype("Int64")
        cleaned = cleaned.loc[cleaned["province"].notna()]
        cleaned = cleaned.loc[~cleaned["province"].str.lower().str.contains("türkiye")]
        cleaned["province"] = cleaned["province"].str.strip()

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
    process_children_national().to_csv(RAW_DIR / "children_security_unit_national_2015_2024.csv", index=False)

    print("Wrote:")
    print(" - data/raw/sgk_active_insured_2009_2024.csv")
    print(" - data/raw/migration_provincial.csv")
    print(" - data/raw/justice_provincial_2011_2021.csv")
    print(" - data/raw/education_provincial_2021_2024.csv")
    print(" - data/raw/children_security_unit_national_2015_2024.csv")


if __name__ == "__main__":
    write_outputs()
