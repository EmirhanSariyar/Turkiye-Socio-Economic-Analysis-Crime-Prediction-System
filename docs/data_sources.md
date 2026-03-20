# Data Source Plan

This document defines the first-pass data acquisition strategy for the `Turkiye-Socio-Economic-Analysis-Crime-Prediction-System` project.

## Strategy

We will use a hybrid data strategy:

- Official sources for the core target variable and high-trust socio-economic indicators
- Kaggle and similar portals for auxiliary datasets, backup options, and faster prototyping

The core modeling table should ideally be built at `province + year` level.

## Target Table Design

The first production-ready dataset should follow a structure similar to:

```text
province, year, population, unemployment_rate, migration_rate, education_index, income_level, crime_count, crime_rate, target_class
```

## Priority 1: Core Official Sources

### 1. Crime / Justice Data

Purpose: define the prediction target.

Potential sources:

- TURKSTAT justice statistics
- Public prosecution, conviction, or criminal court statistics
- Province-level or region-level crime-related annual indicators

Needed fields:

- province or region name
- year
- crime count or court case count
- crime category if available

Modeling note:

If direct province-level crime counts are not available, we can begin with a proxy target such as conviction volume or judgment totals.

### 2. Population Data

Purpose: normalize crime counts into rates.

Potential sources:

- Address Based Population Registration System data
- Province annual population statistics

Needed fields:

- province
- year
- total population
- optional age group and gender breakdowns

### 3. Migration Data

Purpose: capture internal movement and urban pressure.

Potential sources:

- Internal migration statistics
- Net migration by province

Needed fields:

- province
- year
- in-migration
- out-migration
- net migration

### 4. Employment / Unemployment Data

Purpose: measure labour-market stress.

Potential sources:

- Labour force indicators
- Regional unemployment statistics

Needed fields:

- province or region
- year
- unemployment rate
- labour force participation rate

### 5. Education Data

Purpose: capture human capital and social structure.

Potential sources:

- Education attainment indicators
- Literacy or graduation level statistics

Needed fields:

- province or region
- year
- education level indicators

## Priority 2: Supportive Official Sources

These are valuable after the first baseline dataset is ready:

- income or household consumption indicators
- urbanization indicators
- young population ratio
- divorce or household structure indicators
- regional development scores

## Priority 3: Kaggle / Community Sources

Use these to speed up experimentation, enrich features, or compare with official datasets.

Potential examples:

- Turkiye judgment / conviction datasets
- Istanbul socio-economic datasets
- pre-cleaned province-level Turkish indicators

Selection rule:

Only use Kaggle data in the main model if the source, year coverage, and variable definitions are clear.

## Folder Usage

- `data/external/`: downloaded files from Kaggle, TUİK exports, ZIP files, XLSX files, raw source snapshots
- `data/raw/`: cleaned but source-faithful CSV files ready for merging
- `data/interim/`: partially merged transformation outputs
- `data/processed/`: final modeling tables

## Recommended First Download Batch

The first data collection round should focus on:

1. annual province population
2. annual migration by province
3. annual unemployment or labour-force statistics
4. annual education indicators
5. annual crime, conviction, or justice-related statistics

## Data Quality Checks

Each incoming dataset should be checked for:

- province naming consistency
- year coverage consistency
- missing values
- duplicate rows
- whether the unit is province, region, or national
- whether values are counts, percentages, or indexes

## Practical Rule

If a source does not align to `province + year`, it should not go directly into the master table before transformation.

## Next Implementation Step

After collecting the first 3 to 5 datasets, we should create:

- a source inventory CSV
- a province name standardization map
- a merge pipeline in `src/`
