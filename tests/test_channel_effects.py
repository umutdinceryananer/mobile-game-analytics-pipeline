"""Check that retention channel effects set in the synthetic config are recovered.

The generator in data/make_dataset.py adds a per-channel `channel_lift` to the
logit of retention_1 and retention_7. These tests fit the same logistic form on
the pipeline output and compare the fitted channel effects with the config.

Raw channel rates are not enough: part of the D7 channel effect arrives indirectly
through D1, so D7 is only comparable to the config after adjusting for retention_1.

The thresholds were fixed before the first run on the real build. If a check fails,
investigate the pipeline rather than loosening them.
"""

from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd
import pytest
import yaml
from sklearn.linear_model import LogisticRegression

from mobile_game_analytics_pipeline.analytics import generate_retention, generate_roi

REPO_ROOT = Path(__file__).resolve().parents[1]
EVENTS_PATH = REPO_ROOT / "data" / "processed" / "events.parquet"
CONFIG_PATH = REPO_ROOT / "data" / "config" / "synthetic.yaml"

REFERENCE_CHANNEL = "Organic"
COMPARED_CHANNELS = ["Instagram", "Facebook", "TikTok"]
TARGETS = {"d1": "retention_1", "d7": "retention_7"}
STAGES = list(TARGETS)

# A fitted effect must sit within this many standard errors of the config value.
# Direction is only asserted when the config value is at least this far from zero.
Z_LIMIT = 3.0
SHUFFLE_SEED = 42


def _design_matrix(df: pd.DataFrame, stage: str) -> pd.DataFrame:
    """Mirror the covariates the generator uses for each retention stage."""
    columns = {
        "intercept": np.ones(len(df)),
        "log_sessions": np.log1p(df["session_count"].fillna(0).astype(float)),
        "app_store": (df["platform"] == "App Store").astype(float),
    }
    if stage == "d1":
        columns["purchase"] = df["purchase"].astype(float)
        columns["gate_30"] = (df["version"] == "gate_30").astype(float)
    else:
        columns["retained_d1"] = df["retention_1"].astype(float)
        columns["log_revenue"] = np.log1p(df["revenue"].clip(lower=0).astype(float))
    for channel in COMPARED_CHANNELS:
        columns[channel] = (df["acquisition_channel"] == channel).astype(float)
    return pd.DataFrame(columns, index=df.index)


def _fit_channel_effects(df: pd.DataFrame, stage: str) -> tuple[pd.Series, pd.Series]:
    """Return channel coefficients against the reference and their standard errors."""
    design = _design_matrix(df, stage)
    X = design.to_numpy()
    y = df[TARGETS[stage]].astype(int).to_numpy()
    model = LogisticRegression(
        penalty=None,
        fit_intercept=False,
        solver="newton-cholesky",
        max_iter=200,
        tol=1e-8,
    ).fit(X, y)

    proba = model.predict_proba(X)[:, 1]
    information = X.T @ (X * (proba * (1 - proba))[:, None])
    std_errors = np.sqrt(np.diag(np.linalg.inv(information)))

    coefficients = pd.Series(model.coef_[0], index=design.columns)
    errors = pd.Series(std_errors, index=design.columns)
    return coefficients[COMPARED_CHANNELS], errors[COMPARED_CHANNELS]


def _expected_effects(config: dict, stage: str) -> pd.Series:
    lifts = config["retention"][stage]["channel_lift"]
    return pd.Series(
        {c: lifts[c] - lifts[REFERENCE_CHANNEL] for c in COMPARED_CHANNELS}
    )


@pytest.fixture(scope="module")
def df() -> pd.DataFrame:
    return pd.read_parquet(EVENTS_PATH)


@pytest.fixture(scope="module")
def config() -> dict:
    with CONFIG_PATH.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


@pytest.fixture(scope="module")
def fits(df) -> dict[str, tuple[pd.Series, pd.Series]]:
    return {stage: _fit_channel_effects(df, stage) for stage in STAGES}


@pytest.fixture(scope="module")
def analytics_tables(df, tmp_path_factory) -> tuple[pd.DataFrame, pd.DataFrame]:
    matplotlib.use("Agg")
    output_dir = tmp_path_factory.mktemp("analytics")
    generate_retention(df, output_dir, output_dir)
    generate_roi(df, output_dir, output_dir)
    retention = pd.read_csv(output_dir / "retention_by_channel.csv")
    roi = pd.read_csv(output_dir / "roi_by_channel.csv")
    return (
        retention.set_index("acquisition_channel"),
        roi.set_index("acquisition_channel"),
    )


@pytest.mark.parametrize("stage", STAGES)
def test_channel_effects_match_config_within_tolerance(fits, config, stage):
    fitted, errors = fits[stage]
    expected = _expected_effects(config, stage)
    distance = (fitted - expected).abs()
    outside = distance[distance > Z_LIMIT * errors]
    assert outside.empty, (
        f"{stage}: fitted {fitted.to_dict()} vs config {expected.to_dict()}, "
        f"standard errors {errors.to_dict()}"
    )


@pytest.mark.parametrize("stage", STAGES)
def test_channel_effect_direction_where_identifiable(fits, config, stage):
    fitted, errors = fits[stage]
    expected = _expected_effects(config, stage)
    identifiable = expected.abs() >= Z_LIMIT * errors
    assert identifiable.any(), f"{stage}: no contrast is large enough to test"
    wrong_sign = np.sign(fitted[identifiable]) != np.sign(expected[identifiable])
    assert (
        not wrong_sign.any()
    ), f"{stage}: fitted {fitted.to_dict()} vs config {expected.to_dict()}"


@pytest.mark.parametrize("stage", STAGES)
def test_shuffled_channels_break_recovery(df, config, stage):
    """Negative control: without the real channel labels the check must fail."""
    rng = np.random.default_rng(SHUFFLE_SEED)
    shuffled = df.assign(
        acquisition_channel=rng.permutation(df["acquisition_channel"].to_numpy())
    )
    fitted, errors = _fit_channel_effects(shuffled, stage)
    expected = _expected_effects(config, stage)
    assert ((fitted - expected).abs() > Z_LIMIT * errors).any()


def test_retention_table_ranks_organic_above_tiktok(analytics_tables):
    retention, _ = analytics_tables
    for column in ["d1_rate", "d7_rate"]:
        assert retention.loc["Organic", column] > retention.loc["TikTok", column]


def test_roi_table_spend_per_user_equals_config_cac(analytics_tables, config):
    _, roi = analytics_tables
    spend_per_user = roi["ad_spend"] / roi["users"]
    for channel, cac in config["cac"].items():
        assert spend_per_user[channel] == pytest.approx(cac, abs=1e-6)
