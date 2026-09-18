import pandas as pd
import numpy as np
import logging
#--- Layer B: Mahalanobis on residuals ---

def fit_climatology(train_df, config):
    """
    Fit expected-value model conditioned on (month, hour).
    Returns a callable: DatetimeIndex → DataFrame[temp, pres, rhum].

    Falls back to hour-only for (month, hour) bins with fewer than
    MIN_BIN_SAMPLES training rows.
    """
    df = train_df.copy()
    df["_month"] = df.index.month
    df["_hour"] = df.index.hour

    mh_mean = df.groupby(["_month", "_hour"])[config.PARAMETERS].mean()
    h_mean = df.groupby("_hour")[config.PARAMETERS].mean()
    mh_count = df.groupby(["_month", "_hour"])[config.PARAMETERS[0]].count()

    def expected(idx):
        m = np.asarray(idx.month)
        h = np.asarray(idx.hour)
        keys = pd.MultiIndex.from_arrays([m, h])
        counts = mh_count.reindex(keys).fillna(0).values
        use_mh = counts >= config.MIN_BIN_SAMPLES

        out = np.full((len(idx), len(config.PARAMETERS)), np.nan)
        mh_vals = mh_mean.reindex(keys).values
        h_vals = h_mean.reindex(h).values
        out[use_mh] = mh_vals[use_mh]
        out[~use_mh] = h_vals[~use_mh]
        return pd.DataFrame(out, index=idx, columns=config.PARAMETERS)

    return expected


def compute_residuals(df, climatology, config):
    """Actual minus expected value. NaN where the (month, hour) bin is missing."""
    expected = climatology(df.index)
    residuals = df[config.PARAMETERS].copy()
    for col in config.PARAMETERS:
        residuals[col] = df[col] - expected[col]
    return residuals


def fit_layer_b(train_df, climatology, config, debug=False):
    """
    Mahalanobis on residuals (actual - expected). Seasonality removed before
    distance. Threshold at LAYER_B_PERCENTILE of train-set distances.
    """
    residuals = compute_residuals(train_df, climatology, config).dropna()

    if len(residuals) < config.LAYER_B_MIN_TRAIN_ROWS:
        logging.warning(f"Layer B: only {len(residuals)} clean residuals — skipping fit.")
        return None, None, None

    mean = residuals.mean(axis=0).values
    cov = residuals.cov().values

    try:
        cov_inv = np.linalg.inv(cov)
    except np.linalg.LinAlgError:
        logging.info("Layer B: covariance singular — using pseudo-inverse.")
        cov_inv = np.linalg.pinv(cov)

    diff = residuals.values - mean
    train_dist = np.sqrt(np.sum(np.dot(diff, cov_inv) * diff, axis=1))
    fixed_threshold = np.percentile(train_dist, config.LAYER_B_PERCENTILE)

    logging.info(f"Layer B: threshold (p{config.LAYER_B_PERCENTILE}) = {fixed_threshold:.2f}")

    if debug:
        return mean, cov_inv, fixed_threshold, train_dist
    return mean, cov_inv, fixed_threshold


def layer_b_mahalanobis(df, mean, cov_inv, fixed_threshold, climatology,
                        config, debug=False):
    """Apply Layer B threshold to residuals of the incoming frame."""
    if mean is None or cov_inv is None or fixed_threshold is None:
        return pd.Series(False, index=df.index)

    residuals_full = compute_residuals(df, climatology, config)
    residuals = residuals_full.dropna()

    missing_raw = int(df[config.PARAMETERS].isna().any(axis=1).sum())
    missing_bin = len(residuals_full) - len(residuals) - missing_raw
    if missing_bin > 0:
        logging.warning(f"Layer B: {missing_bin} rows dropped — "
                        f"(month, hour) bin missing from training.")
    if missing_raw > 0:
        logging.warning(f"Layer B: {missing_raw} rows dropped — NaN in raw readings.")

    flag_series = pd.Series(False, index=df.index)
    if residuals.empty:
        return flag_series

    diff = residuals.values - mean
    dist = np.sqrt(np.sum(np.dot(diff, cov_inv) * diff, axis=1))
    dist_series = pd.Series(dist, index=residuals.index)

    flag_series.loc[residuals.index] = dist_series > fixed_threshold

    if debug:
        return flag_series, dist_series
    return flag_series