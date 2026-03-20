# Processed Data Plan

This document defines the first merged province-year datasets built from the raw source tables.

## Baseline Modeling Window

- `2011-2021`

Reason:

- provincial justice proxy is available through `2021`
- SGK and migration overlap well in this range
- education is shorter, so it will enrich only the latest years unless more history is added later

## Planned Processed Files

### 1. `data/processed/province_year_master_2011_2021.csv`

Primary use:

- unified analysis table
- exploratory analysis
- feature engineering

Expected content:

- province identifiers
- regional identifiers
- population and migration indicators
- SGK formal employment proxy
- education indicators
- justice proxy fields
- normalized per-capita metrics

### 2. `data/processed/province_year_modeling_2011_2021.csv`

Primary use:

- first-pass machine learning experiments

Expected additions:

- rows filtered to usable modeling coverage
- binary target `high_justice_risk`

## Justice Proxy Definition

Current target proxy:

- `investigation_files_opened`

Current normalized target:

- `investigation_files_opened_per_100k`

Reason:

- it captures the current year flow more cleanly than total file load
- total load includes backlog from previous years

## Province Name Standardization

The merge layer normalizes province names before joining.

Examples:

- `Afyon` -> `Afyonkarahisar`
- Turkish diacritics are normalized
- spaces and punctuation differences are removed from join keys

## Script

The merge entry point is:

- `src/merge_master_data.py`

## Recommended Run Order

1. `python src/prepare_raw_data.py`
2. `python src/merge_master_data.py`

## Current Limitation

Education data currently starts much later than the justice series. This means:

- the master table can still be created for `2011-2021`
- but education-based features will only be populated for the overlapping years

That is acceptable for the first version, but expanding education history later would improve coverage.
