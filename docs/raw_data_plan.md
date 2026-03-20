# Raw Data Output Plan

The first raw outputs to generate from the external source files are:

## Planned Files

### 1. `data/raw/justice_provincial_2011_2021.csv`

Source:

- `data/external/justice/Adalet_İst_2011-2023_İl_Bölge_Suç_Verileri (1).xlsx`

Expected columns:

- `province`
- `year`
- `investigation_files_total_load`
- `investigation_files_carry_in`
- `investigation_files_opened`
- `investigation_files_closed`
- optional `investigation_files_carry_out`

### 2. `data/raw/sgk_active_insured_2009_2024.csv`

Source:

- all SGK CSV fragments under `data/external/sgk/`

Expected columns:

- `province`
- `year`
- `active_insured_total`
- `category`
- `indicator`
- `unit`
- `geographical_region`
- `statistical_region`

### 3. `data/raw/migration_provincial.csv`

Source:

- all migration XLS files under `data/external/migration/`

Expected columns:

- `province`
- `year`
- `population`
- `in_migration`
- `out_migration`
- `net_migration`
- `net_migration_rate`

### 4. `data/raw/education_provincial_2021_2024.csv`

Source:

- all education XLS files under `data/external/education/`

Expected columns:

- `province`
- `year`
- `education_population_6_plus`
- `illiterate_total`
- `literate_no_diploma_total`
- `lower_secondary_total`
- `upper_secondary_total`
- `university_total`
- `masters_total`
- `doctorate_total`
- `illiterate_rate`
- `upper_secondary_rate`
- `university_rate`
- `postgraduate_rate`

### 5. `data/raw/children_security_unit_national_2015_2024.csv`

Source:

- `data/external/children/Geliş nedeni ve cinsiyete göre güvenlik birimine gelen veya getirilen çocukların karıştığı olay sayısı.xls`

Expected columns:

- `year`
- `children_incidents_total`
- `children_pushed_into_crime_total`
- `children_victim_total`
- `children_witness_total`

## Processing Script

The first-pass processor is:

- `src/prepare_raw_data.py`

## Notes

- Province-level baseline modeling window should remain `2011-2021`.
- `Türkiye` total rows must be removed from province-level outputs.
- The current children file is useful as a national time series, not as a province-level merge key.
- Raw outputs are intentionally not committed by default because `data/raw/` is ignored.
