"""Helpers for loading the raw Zindi Loan Default Prediction competition ZIP.

This module keeps the raw competition ingestion separate from the synthetic
portfolio dataset used elsewhere in the project.  It allows the repository to
support both flows:
- synthetic demo data under data/synthetic
- real raw competition tables loaded directly from the ZIP archive
"""

from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

import pandas as pd


RAW_DEMOGRAPHICS_COLUMNS = [
    "customerid",
    "birthdate",
    "bank_account_type",
    "longitude_gps",
    "latitude_gps",
    "bank_name_clients",
    "bank_branch_clients",
    "employment_status_clients",
    "level_of_education_clients",
]

RAW_TRAIN_PERF_COLUMNS = [
    "customerid",
    "systemloanid",
    "loannumber",
    "approveddate",
    "creationdate",
    "loanamount",
    "totaldue",
    "termdays",
    "referredby",
    "good_bad_flag",
]

RAW_TEST_PERF_COLUMNS = [
    "customerid",
    "systemloanid",
    "loannumber",
    "approveddate",
    "creationdate",
    "loanamount",
    "totaldue",
    "termdays",
    "referredby",
]

RAW_PREVLOANS_COLUMNS = [
    "customerid",
    "systemloanid",
    "loannumber",
    "approveddate",
    "creationdate",
    "loanamount",
    "totaldue",
    "termdays",
    "closeddate",
    "referredby",
    "firstduedate",
    "firstrepaiddate",
]

RAW_SUBMISSION_COLUMNS = [
    "customerid",
    "Good_Bad_flag",
]


@dataclass
class RawCompetitionBundle:
    train_demographics: pd.DataFrame
    train_perf: pd.DataFrame
    train_prevloans: pd.DataFrame
    test_demographics: pd.DataFrame
    test_perf: pd.DataFrame
    test_prevloans: pd.DataFrame
    sample_submission: pd.DataFrame


def _validate_columns(df: pd.DataFrame, expected_columns: list[str], dataset_name: str) -> None:
    missing = [column for column in expected_columns if column not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns for {dataset_name}: {missing}")


def _read_csv_from_archive(archive: ZipFile, member_name: str) -> pd.DataFrame:
    with archive.open(member_name) as file_obj:
        return pd.read_csv(file_obj)


def _read_nested_csv_from_archive(archive: ZipFile, nested_zip_name: str, nested_csv_name: str) -> pd.DataFrame:
    with archive.open(nested_zip_name) as nested_file:
        nested_bytes = BytesIO(nested_file.read())
    with ZipFile(nested_bytes) as nested_archive:
        with nested_archive.open(nested_csv_name) as inner_file:
            return pd.read_csv(inner_file)


def _prepare_demographics(df: pd.DataFrame) -> pd.DataFrame:
    prepared = df.copy()
    _validate_columns(prepared, RAW_DEMOGRAPHICS_COLUMNS, "demographics")
    prepared["birthdate"] = pd.to_datetime(prepared["birthdate"], errors="coerce")
    for column in ["longitude_gps", "latitude_gps"]:
        prepared[column] = pd.to_numeric(prepared[column], errors="coerce")
    return prepared


def _prepare_perf(df: pd.DataFrame, is_train: bool) -> pd.DataFrame:
    prepared = df.copy()
    expected = RAW_TRAIN_PERF_COLUMNS if is_train else RAW_TEST_PERF_COLUMNS
    _validate_columns(prepared, expected, "train_perf" if is_train else "test_perf")
    for column in ["systemloanid", "loannumber", "loanamount", "totaldue", "termdays"]:
        prepared[column] = pd.to_numeric(prepared[column], errors="coerce")
    prepared["approveddate"] = pd.to_datetime(prepared["approveddate"], errors="coerce")
    prepared["creationdate"] = pd.to_datetime(prepared["creationdate"], errors="coerce")
    if is_train:
        prepared["target_risk_flag"] = prepared["good_bad_flag"].map({"Good": 0, "Bad": 1})
    return prepared


def _prepare_prevloans(df: pd.DataFrame) -> pd.DataFrame:
    prepared = df.copy()
    _validate_columns(prepared, RAW_PREVLOANS_COLUMNS, "prevloans")
    for column in ["systemloanid", "loannumber", "loanamount", "totaldue", "termdays"]:
        prepared[column] = pd.to_numeric(prepared[column], errors="coerce")
    for column in ["approveddate", "creationdate", "closeddate", "firstduedate", "firstrepaiddate"]:
        prepared[column] = pd.to_datetime(prepared[column], errors="coerce")
    prepared["late_days_first_installment"] = (
        prepared["firstrepaiddate"] - prepared["firstduedate"]
    ).dt.days.clip(lower=0)
    prepared["ever_late_flag"] = (prepared["late_days_first_installment"] > 0).astype(int)
    prepared["ever_late_30d_flag"] = (prepared["late_days_first_installment"] > 30).astype(int)
    prepared["prev_totaldue_to_loanamount"] = prepared["totaldue"] / prepared["loanamount"].replace({0: pd.NA})
    return prepared


def _prepare_sample_submission(df: pd.DataFrame) -> pd.DataFrame:
    prepared = df.copy()
    _validate_columns(prepared, RAW_SUBMISSION_COLUMNS, "sample submission")
    return prepared


def load_raw_competition_zip(zip_path: str | Path) -> RawCompetitionBundle:
    """Load the competition ZIP without extracting it on disk."""
    archive_path = Path(zip_path)
    with ZipFile(archive_path) as archive:
        train_demographics = _prepare_demographics(_read_csv_from_archive(archive, "traindemographics.csv"))
        train_perf = _prepare_perf(_read_csv_from_archive(archive, "trainperf.csv"), is_train=True)
        test_demographics = _prepare_demographics(_read_csv_from_archive(archive, "testdemographics.csv"))
        test_perf = _prepare_perf(_read_csv_from_archive(archive, "testperf.csv"), is_train=False)
        train_prevloans = _prepare_prevloans(
            _read_nested_csv_from_archive(archive, "trainprevloans.zip", "trainprevloans.csv")
        )
        test_prevloans = _prepare_prevloans(
            _read_nested_csv_from_archive(archive, "testprevloans.zip", "testprevloans.csv")
        )
        sample_submission = _prepare_sample_submission(_read_csv_from_archive(archive, "SampleSubmission.csv"))
    return RawCompetitionBundle(
        train_demographics=train_demographics,
        train_perf=train_perf,
        train_prevloans=train_prevloans,
        test_demographics=test_demographics,
        test_perf=test_perf,
        test_prevloans=test_prevloans,
        sample_submission=sample_submission,
    )


def combine_demographics(bundle: RawCompetitionBundle) -> pd.DataFrame:
    """Build a customer-level lookup table from train and test demographics."""
    combined = pd.concat([bundle.train_demographics, bundle.test_demographics], ignore_index=True)
    combined = combined.sort_values("customerid").drop_duplicates(subset=["customerid"], keep="last")
    return combined.reset_index(drop=True)


def combine_prevloans(bundle: RawCompetitionBundle) -> pd.DataFrame:
    """Return a unified previous-loans table for historical feature engineering."""
    combined = pd.concat([bundle.train_prevloans, bundle.test_prevloans], ignore_index=True)
    return combined.reset_index(drop=True)


def build_history_features(prevloans: pd.DataFrame) -> pd.DataFrame:
    """Aggregate customer-level historical features from previous loans."""
    grouped = prevloans.groupby("customerid", dropna=False)
    history = grouped.agg(
        num_prev_loans=("systemloanid", "count"),
        late_payment_rate=("ever_late_flag", "mean"),
        max_late_days=("late_days_first_installment", "max"),
        ever_late_flag=("ever_late_flag", "max"),
        ever_late_30d_flag=("ever_late_30d_flag", "max"),
        avg_prev_totaldue_to_loanamount=("prev_totaldue_to_loanamount", "mean"),
        latest_prev_closeddate=("closeddate", "max"),
    ).reset_index()
    return history


def build_current_loan_tables(bundle: RawCompetitionBundle) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Create train/test tables enriched with demographics and loan history."""
    demographics = combine_demographics(bundle)
    history = build_history_features(combine_prevloans(bundle))

    train_table = bundle.train_perf.merge(demographics, on="customerid", how="left")
    train_table = train_table.merge(history, on="customerid", how="left")

    test_table = bundle.test_perf.merge(demographics, on="customerid", how="left")
    test_table = test_table.merge(history, on="customerid", how="left")

    return train_table, test_table
