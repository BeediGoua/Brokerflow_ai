# Raw Dataset Integration

This document explains how the repository now relates to the original Zindi Loan Default Prediction dataset.

## Current state of the repository

At the moment:

- `data/synthetic/` contains the synthetic demo datasets used by the original portfolio pipeline.
- `data/processed/` contains derived tables generated from the raw Zindi archive.
- `data-science-nigeria-challenge-1-loan-default-prediction20250307-26022-im3qg9.zip` is the raw competition archive placed at the project root.

This means the contents of `data/` are a mix of:

1. synthetic demo files,
2. processed files derived from raw competition data.

## What is inside the ZIP

The raw competition archive contains these main files:

- `traindemographics.csv`
- `trainperf.csv`
- `testdemographics.csv`
- `testperf.csv`
- `SampleSubmission.csv`
- `trainprevloans.zip`
- `testprevloans.zip`

The nested ZIP files contain:

- `trainprevloans.csv`
- `testprevloans.csv`

## How the code handles it now

The repository now includes `src/data/raw_competition.py`, which can:

- read the raw competition ZIP directly without manual extraction
- validate the expected raw tables
- parse numeric and date columns where possible
- derive basic historical features from previous loans
- build enriched train/test current-loan tables by merging:
  - current loan performance tables
  - combined demographics lookup
  - aggregated previous-loan history

The notebook workflow currently materialises these outputs:

- `data/processed/train_enriched.csv`
- `data/processed/test_enriched.csv`
- `data/processed/history_features.csv`
- `data/processed/train_features.csv`
- `data/processed/test_features.csv`

Entry points available from the package:

- `load_raw_competition_bundle(...)`
- `load_enriched_raw_competition_tables(...)`

## Important caveats

### 1. `data/` contains both synthetic and processed-real files

This is intentional for backward compatibility with the demo pipeline, but it means the project has two operating modes:

- synthetic demo mode
- raw competition mode with derived processed tables

### 2. The competition split is not a simple customer split

Customer IDs overlap across train and test-related files. For this reason, the code combines demographics and previous-loan history into shared lookup tables, while keeping `trainperf.csv` and `testperf.csv` as the split-defining tables.

### 3. Some test date fields are malformed

The raw `testperf.csv` date columns contain malformed values in this dataset snapshot. The loader parses these with `errors="coerce"`, which converts invalid timestamps to missing values instead of crashing the pipeline.

### 4. Raw data and synthetic proxy fields are different things

The raw competition data does not natively include fields such as:

- `monthly_income`
- `credit_score_proxy`
- `free_text_note`

These remain synthetic or proxy variables and should be documented as such.

## Recommended project direction

For a credible underwriting portfolio:

1. Use the raw Zindi tables as the primary source of observed data.
2. Build derived features from `prevloans` first.
3. Keep synthetic proxies clearly labelled as proxies.
4. Keep free-text notes as an optional product layer, not as native data.
5. Treat the synthetic dataset as a demo mode, not as the main source of truth.
6. Keep exported files in `data/processed/` as reproducible intermediate artifacts for notebook and model audits.
