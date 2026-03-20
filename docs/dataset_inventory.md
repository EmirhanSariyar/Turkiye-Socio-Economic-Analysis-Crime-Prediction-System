# Dataset Inventory

This file tracks the datasets currently copied into the repository under `data/external/`.

## Current Modeling Direction

The strongest current target candidate is:

- `justice investigation files opened` from provincial chief public prosecutor statistics for `2011-2021`

The strongest current socio-economic feature groups are:

- SGK active insured counts
- migration and net migration
- population
- education attainment
- children brought to security unit statistics

## Selected Files

### Justice

Folder: `data/external/justice/`

- `Adalet_İst_2011-2023_İl_Bölge_Suç_Verileri (1).xlsx`
  - status: primary target source
  - usable scope: `2011-2021` at province level
  - note: `2022-2023` continues only at region level
- `Adalet_İstatistikleri_2024_Bölgesel_Suç_Verileri.xlsx`
  - status: supplementary source
  - usable scope: `2024` at region level
  - note: useful for regional comparisons, not for province-level master table
- `Hükümlü ve Tutuklu Sayısı.xls`
  - status: background context only
  - usable scope: national totals
  - note: not suitable for province-level modeling

### SGK

Folder: `data/external/sgk/`

- `sgk_veri_2026-03-20 (3).csv`
  - years: `2009-2010`
- `sgk_veri_2026-03-20 (2).csv`
  - years: `2011-2015`
- `sgk_veri_2026-03-20 (1).csv`
  - years: `2016-2020`
- `sgk_veri_2026-03-20.csv`
  - years: `2021-2024`
  - extra note: also contains monthly `2025` columns

Recommended SGK feature:

- `active_insured_total`

### Children

Folder: `data/external/children/`

- `Geliş nedeni ve cinsiyete göre güvenlik birimine gelen veya getirilen çocukların karıştığı olay sayısı.xls`
- `Geliş nedenine göre güvenlik birimine gelen veya getirilen çocuklar.xls`
- `Geliş nedenine göre güvenlik birimine gelen veya getirilen çocuklar (1).xls`
- `Suça sürüklenme türü ve cinsiyete göre güvenlik birimine gelen veya getirilen çocukların karıştığı olay sayısı.xls`

Recommended use:

- evaluate one of these as an alternative target or secondary justice-risk indicator

### Migration

Folder: `data/external/migration/`

- `İllerin aldığı göç, verdiği göç, net göç ve net göç hızı.xls`
- `İllerin aldığı göç, verdiği göç, net göç ve net göç hızı (1).xls`
- `İllerin aldığı göç, verdiği göç, net göç ve net göç hızı (2).xls`
- `İllerin aldığı göç, verdiği göç, net göç ve net göç hızı (3).xls`

Recommended features:

- `in_migration`
- `out_migration`
- `net_migration`
- `net_migration_rate`

### Education

Folder: `data/external/education/`

- `İllere göre bitirilen eğitim durumu (6+ yaş).xls`
- `İllere göre bitirilen eğitim durumu (6+ yaş) (1).xls`
- `İllere göre bitirilen eğitim durumu (6+ yaş) (2).xls`

Recommended approach:

- convert into percentage-based province-year indicators
- prefer one compact summary metric for the first baseline

### Population

Folder: `data/external/population/`

- multiple population and density `.xls` files copied for screening

Recommended use:

- keep total province population as the main denominator
- use density only if year coverage is consistent

## Recommended Baseline Window

The cleanest first province-level modeling window is:

- `2011-2021`

Reason:

- justice proxy is province-level through `2021`
- SGK and demographic features cover this range
- this avoids mixing province-level and region-level targets in the baseline model

## Next Processing Steps

1. Standardize province names across all files.
2. Remove `Türkiye` total rows from province-level datasets.
3. Reshape wide year columns into long format: `province`, `year`, `value`.
4. Build one cleaned CSV per source under `data/raw/`.
5. Merge source tables into one province-year master dataset under `data/processed/`.
