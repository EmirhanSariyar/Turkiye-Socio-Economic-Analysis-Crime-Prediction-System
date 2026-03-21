# Turkiye Socioeconomic Justice Risk Analysis

Province-level socio-economic analysis and justice-risk modeling project for Turkiye, built with official public datasets and an interactive Streamlit dashboard.

## Overview

This project studies how province-level socio-economic indicators relate to recorded justice-file intensity in Turkiye.

The system combines:

- provincial justice investigation statistics
- SGK active insured counts
- migration indicators
- education indicators from both TURKSTAT and MEB
- an interactive dashboard for province and year comparisons

The project does **not** claim to measure absolute crime truth directly.  
Its main target is a **justice proxy** based on recorded investigation-file volume.

## Problem Definition

The core modeling question is:

> Can province-level socio-economic indicators help explain or classify recorded justice-file intensity across Turkish provinces?

In the current implementation, the strongest province-level target is:

- `investigation_files_opened`

This target comes from provincial chief public prosecutor statistics and is used to derive yearly `Low / Medium / High` justice-risk bands.

## Dataset Summary

The harmonized baseline modeling window is:

- `2011-2021`

This window was selected because it is the cleanest province-level overlap across the main justice and socio-economic sources.

### Main Sources

- `Justice`: provincial investigation-file statistics, `2011-2021`
- `SGK`: active insured totals, `2009-2024`
- `Migration`: in-migration, out-migration, net migration, province population
- `TURKSTAT education`: attainment-style indicators for recent years
- `MEB education`: province-level gross enrollment ratios for upper secondary education, `2011-2025`

### Current Feature Groups

- `active_insured_total`
- `population`
- `in_migration`, `out_migration`, `net_migration`
- `general_secondary_gross_enrollment_rate`
- `vocational_secondary_gross_enrollment_rate`
- `illiterate_rate`
- `university_rate`
- region-based categorical indicators

### Important Interpretation Note

MEB education variables in this repository are **gross enrollment rates**, not attainment rates.

That means:

- values may exceed `100`
- they should be interpreted as enrollment intensity / participation proxies
- they should not be interpreted as direct graduation or attainment levels

## Modeling Approach

The repository currently includes two baseline model variants:

### 1. Rich Feature Rate Model

- narrower overlap
- richer socio-economic feature set
- useful for detailed cross-sectional analysis

### 2. Wide Coverage Flow Model

- broader temporal coverage
- stronger support across `2011-2021`
- currently the most stable baseline for wide province-year analysis

The `Wide Coverage Flow Model` is the stronger general-purpose baseline at the moment because it retains much broader data support.

## Dashboard

The Streamlit dashboard includes:

- province and year selection
- justice-risk metrics for the selected province
- province-level trend charts
- choropleth map of Turkish provinces
- province ranking for the selected year
- a recent monitoring view for post-2021 SGK and MEB trends

The dashboard is intentionally split into two views:

- `Main Risk View (2011-2021)`
- `Recent Trends View (2011-2025)`

This keeps the main methodology clean while still exposing newer education and employment trends.

## Project Structure

```text
.
|-- app.py
|-- requirements.txt
|-- README.md
|-- data/
|   |-- external/
|   |-- raw/
|   `-- processed/
|-- docs/
|   |-- data_sources.md
|   |-- dataset_inventory.md
|   |-- raw_data_plan.md
|   `-- processed_data_plan.md
|-- models/
|-- notebooks/
|-- reports/
|-- src/
|   |-- config.py
|   |-- merge_master_data.py
|   |-- prepare_raw_data.py
|   |-- source_inventory.py
|   `-- train.py
`-- tests/
```

## How To Run

Create and activate a virtual environment:

```bash
git clone <repository-url>
cd Turkiye-Socioeconomic-Justice-Risk-Analysis
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Build the raw and processed datasets:

```bash
python src/prepare_raw_data.py
python src/merge_master_data.py
```

Train the baseline models:

```bash
python src/train.py
```

Run the dashboard:

```bash
streamlit run app.py
```

## Current Outputs

Generated raw datasets include:

- `data/raw/justice_provincial_2011_2021.csv`
- `data/raw/sgk_active_insured_2009_2024.csv`
- `data/raw/migration_provincial.csv`
- `data/raw/education_provincial_2021_2024.csv`
- `data/raw/meb_secondary_gross_enrollment_2011_2025.csv`

Generated processed datasets include:

- `data/processed/province_year_master_2011_2021.csv`
- `data/processed/province_year_modeling_2011_2021.csv`

## Limitations

- The project uses a **justice proxy**, not direct crime truth.
- The strongest province-level justice target currently ends at `2021`.
- Some richer socio-economic features are only available for narrower year ranges.
- Newer post-2021 trends are currently presented as monitoring views rather than unified justice-risk labels.

## Future Improvements

- improve README visuals with final dashboard screenshots
- refine evaluation outputs and model interpretation
- revisit smoother map interactivity in the final frontend polish stage
- add stronger explainability around province-level risk differences
- remove temporary internal planning files before final public release

## License

This project includes an MIT license file in the repository.
