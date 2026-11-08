"""Check that the dbt marts reproduce the reference SQL in references/sql/.

Each reference query runs on `users` and `events` views built the same way as in
notebook 0.9, and its result is compared row by row with the matching mart.

Run after `make pipeline`, which builds the marts in the DuckDB warehouse.
"""

from pathlib import Path

import duckdb
import pandas as pd
import pytest
from pandas.testing import assert_frame_equal

REPO_ROOT = Path(__file__).resolve().parents[1]
CLEAN_CSV = REPO_ROOT / "data" / "processed" / "clean_data.csv"
SQL_DIR = REPO_ROOT / "references" / "sql"
WAREHOUSE = REPO_ROOT / "data" / "warehouse" / "analytics.duckdb"

RELATIVE_TOLERANCE = 1e-9

# Reference SQL file, matching mart, and the columns that identify a row.
CASES = [
    ("installs_by_channel.sql", "mart_installs_by_channel", ["acquisition_channel"]),
    ("funnel_step_rates.sql", "mart_funnel_step_rates", ["n_users"]),
    ("funnel_by_channel.sql", "mart_funnel_by_channel", ["acquisition_channel"]),
    ("roi_by_channel.sql", "mart_channel_roi", ["acquisition_channel"]),
]

# Mart columns added after the migration, which the reference SQL does not have.
ADDED_COLUMNS = {"mart_channel_roi": ["revenue_per_install"]}

# Same view definition as notebooks/0.9-SQL-Validation-and-Samples.ipynb.
CREATE_USERS_VIEW = """
    CREATE OR REPLACE VIEW users AS
    SELECT
      TRY_CAST(TRIM(userid) AS BIGINT)                              AS userid,
      TRIM(version)                                                 AS version,
      TRY_CAST(TRIM(session_count) AS INTEGER)                      AS session_count,
      COALESCE(TRY_CAST(NULLIF(TRIM(retention_1), '') AS BOOLEAN), FALSE) AS retention_1,
      COALESCE(TRY_CAST(NULLIF(TRIM(retention_7), '') AS BOOLEAN), FALSE) AS retention_7,
      TRIM(acquisition_channel)                                     AS acquisition_channel,
      TRIM(country)                                                 AS country,
      TRIM(platform)                                                AS platform,
      COALESCE(TRY_CAST(NULLIF(TRIM(purchase), '') AS INTEGER), 0)  AS purchase,
      COALESCE(TRY_CAST(NULLIF(TRIM("CAC"), '') AS DOUBLE), 0.0)    AS cac,
      COALESCE(TRY_CAST(NULLIF(TRIM(revenue), '') AS DOUBLE), 0.0)  AS revenue,
      COALESCE(TRY_CAST(NULLIF(TRIM("ROI"), '') AS DOUBLE), 0.0)    AS roi_row
    FROM read_csv_auto(
      '{path}',
      HEADER=TRUE,
      SAMPLE_SIZE=-1,
      ALL_VARCHAR=TRUE
    );
"""


def _sorted(frame: pd.DataFrame, keys: list[str]) -> pd.DataFrame:
    return frame.sort_values(keys).reset_index(drop=True)


@pytest.fixture(scope="module")
def reference_connection():
    connection = duckdb.connect()
    connection.execute(CREATE_USERS_VIEW.format(path=CLEAN_CSV.as_posix()))
    connection.execute("CREATE OR REPLACE VIEW events AS SELECT * FROM users;")
    yield connection
    connection.close()


@pytest.fixture(scope="module")
def warehouse_connection():
    assert WAREHOUSE.exists(), f"{WAREHOUSE} not found; run `make pipeline` first."
    connection = duckdb.connect(str(WAREHOUSE), read_only=True)
    yield connection
    connection.close()


@pytest.mark.parametrize(("sql_file", "mart", "keys"), CASES)
def test_mart_matches_reference_sql(
    reference_connection, warehouse_connection, sql_file, mart, keys
):
    query = (SQL_DIR / sql_file).read_text(encoding="utf-8")
    expected = reference_connection.execute(query).df()
    actual = warehouse_connection.execute(f"SELECT * FROM main.{mart}").df()

    added = ADDED_COLUMNS.get(mart, [])
    assert list(actual.columns) == list(expected.columns) + added
    assert_frame_equal(
        _sorted(actual.drop(columns=added), keys),
        _sorted(expected, keys),
        check_dtype=False,
        check_exact=False,
        rtol=RELATIVE_TOLERANCE,
    )
