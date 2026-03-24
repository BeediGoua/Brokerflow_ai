"""Tests for the raw Zindi competition ZIP loader."""

from io import BytesIO
from zipfile import ZipFile

import pandas as pd

from src.data.raw_competition import build_current_loan_tables, load_raw_competition_zip


def _write_nested_zip_csv(records: pd.DataFrame, nested_zip_name: str, csv_name: str) -> bytes:
    buffer = BytesIO()
    with ZipFile(buffer, "w") as nested_zip:
        nested_zip.writestr(csv_name, records.to_csv(index=False))
    return buffer.getvalue()


def test_load_raw_competition_zip_reads_expected_tables(tmp_path):
    zip_path = tmp_path / "challenge.zip"

    train_demographics = pd.DataFrame([
        {
            "customerid": "C1",
            "birthdate": "1980-01-01 00:00:00.000000",
            "bank_account_type": "Savings",
            "longitude_gps": "3.3",
            "latitude_gps": "6.5",
            "bank_name_clients": "GT Bank",
            "bank_branch_clients": "",
            "employment_status_clients": "Permanent",
            "level_of_education_clients": "Graduate",
        }
    ])
    test_demographics = pd.DataFrame([
        {
            "customerid": "C2",
            "birthdate": "1985-01-01 00:00:00.000000",
            "bank_account_type": "Savings",
            "longitude_gps": "3.4",
            "latitude_gps": "6.6",
            "bank_name_clients": "UBA",
            "bank_branch_clients": "",
            "employment_status_clients": "Self-Employed",
            "level_of_education_clients": "Secondary",
        }
    ])
    train_perf = pd.DataFrame([
        {
            "customerid": "C1",
            "systemloanid": "1001",
            "loannumber": "3",
            "approveddate": "2017-07-25 08:22:56.000000",
            "creationdate": "2017-07-25 07:22:47.000000",
            "loanamount": "30000.0000",
            "totaldue": "34500.0000",
            "termdays": "30",
            "referredby": "",
            "good_bad_flag": "Good",
        }
    ])
    test_perf = pd.DataFrame([
        {
            "customerid": "C2",
            "systemloanid": "2002",
            "loannumber": "4",
            "approveddate": "40:48.0",
            "creationdate": "39:35.0",
            "loanamount": "10000",
            "totaldue": "12250",
            "termdays": "30",
            "referredby": "",
        }
    ])
    prevloans = pd.DataFrame([
        {
            "customerid": "C1",
            "systemloanid": "9001",
            "loannumber": "1",
            "approveddate": "2016-08-15 18:22:40.000000",
            "creationdate": "2016-08-15 17:22:32.000000",
            "loanamount": "10000.0000",
            "totaldue": "13000.0000",
            "termdays": "30",
            "closeddate": "2016-09-01 16:06:48.000000",
            "referredby": "",
            "firstduedate": "2016-09-14 00:00:00.000000",
            "firstrepaiddate": "2016-09-20 15:51:43.000000",
        }
    ])
    sample_submission = pd.DataFrame([
        {"customerid": "C2", "Good_Bad_flag": 1}
    ])

    with ZipFile(zip_path, "w") as archive:
        archive.writestr("traindemographics.csv", train_demographics.to_csv(index=False))
        archive.writestr("testdemographics.csv", test_demographics.to_csv(index=False))
        archive.writestr("trainperf.csv", train_perf.to_csv(index=False))
        archive.writestr("testperf.csv", test_perf.to_csv(index=False))
        archive.writestr("SampleSubmission.csv", sample_submission.to_csv(index=False))
        archive.writestr(
            "trainprevloans.zip",
            _write_nested_zip_csv(prevloans, "trainprevloans.zip", "trainprevloans.csv"),
        )
        archive.writestr(
            "testprevloans.zip",
            _write_nested_zip_csv(prevloans.assign(customerid="C2"), "testprevloans.zip", "testprevloans.csv"),
        )

    bundle = load_raw_competition_zip(zip_path)
    train_table, test_table = build_current_loan_tables(bundle)

    assert list(bundle.train_demographics.columns) == list(train_demographics.columns)
    assert bundle.train_perf.loc[0, "target_risk_flag"] == 0
    assert pd.isna(bundle.test_perf.loc[0, "approveddate"])
    assert bundle.train_prevloans.loc[0, "late_days_first_installment"] == 6
    assert bundle.train_prevloans.loc[0, "ever_late_flag"] == 1
    assert "num_prev_loans" in train_table.columns
    assert "avg_prev_totaldue_to_loanamount" in test_table.columns
