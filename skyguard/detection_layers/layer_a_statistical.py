import pandas as pd
import numpy as np
import logging
from skyguard.detection_layers.layer_b_mahalanobis import fit_climatology

#--- Layer A STATISITCIAL for FLATLINES and SPIKES ---
def derive_flatline_thresholds(train_df, config, margin=1):
    """
    Per-parameter flatline run-length thresholds, derived from clean training data.

    A run of N identical values is flagged as a flatline only if N exceeds what
    naturally occurs in clean data for that parameter. `margin` rows are added
    on top of the observed max as a safety buffer.

    rhum naturally freezes for longer than temp/pres, so a single global
    threshold over-flags humidity.
    """
    natural_max = {}
    for col in config.PARAMETERS:
        is_dup = train_df[col].eq(train_df[col].shift(1))
        run_id = (~is_dup).cumsum()
        run_sizes = run_id.value_counts()
        natural_max[col] = int(run_sizes.max()) if len(run_sizes) else 1

    return {col: natural_max[col] + margin for col in config.PARAMETERS}

def compute_residual_thresholds(train_df, climatology, parameters, k=6):
    """
    Robust deviation threshold per parameter: median + k * 1.4826 * MAD.
    MAD is resilient to the tail of real anomalies in the training set
    (which the p99 percentile is not).
    """
    thresholds = {}
    expected = climatology(train_df.index)
    for col in parameters:
        residuals = (train_df[col] - expected[col]).dropna()
        median = residuals.median()
        mad = (residuals - median).abs().median()
        thresholds[col] = median + k * 1.4826 * mad
    return thresholds


def layer_a_statistical(df, train_df, config, climatology=None, debug=False):
    """
    Layer A: statistical anomaly detection.

    Spike: unusual deviation from expected value AND unusual first-difference.
    Flatline: identical-value run exceeding the natural run length for that
    parameter, either on an anomalous value or unconditionally if very long.
    """
    spike_flag = pd.Series(False, index=df.index)
    flatline_flag = pd.Series(False, index=df.index)
    debug_masks = {} if debug else None

    if climatology is None:
        climatology = fit_climatology(train_df, config)

    # Per-parameter deviation thresholds: median + k * 1.4826 * MAD on |residual|
    deviation_thresholds = compute_residual_thresholds(
        train_df, climatology, config.PARAMETERS, k=config.LAYER_A_K
    )

    change_thresholds = {}
    for col in config.PARAMETERS:
        normal_changes = train_df[col].diff().abs().dropna()
        change_thresholds[col] = np.percentile(normal_changes, config.CHANGE_PERCENTILE)

    try:
        flatline_runs = derive_flatline_thresholds(
            train_df, config, margin=config.FLATLINE_MARGIN
        )
    except Exception as e:
        logging.warning(f"Layer A: flatline derivation failed ({e}) — using fallback.")
        flatline_runs = dict(config.FLATLINE_RUN_FALLBACK)

    expected = climatology(df.index)   # DataFrame[temp, pres, rhum], aligned to df.index

    for col in config.PARAMETERS:
        if col not in df.columns:
            continue

        residual = df[col] - expected[col]
        residual_abs = residual.abs()
        deviation_condition = residual_abs > deviation_thresholds[col]

        sudden_change = df[col].diff().abs()
        spike_condition = deviation_condition & (sudden_change > change_thresholds[col])
        spike_flag |= spike_condition

        changes = df[col].ne(df[col].shift(1))
        run_id = changes.cumsum()
        run_length = run_id.map(run_id.value_counts())

        threshold = flatline_runs.get(col, config.FLATLINE_RUN_FALLBACK.get(col, 5))

        stuck_and_wrong = (run_length >= threshold) & deviation_condition
        very_long = run_length >= threshold + 2
        flatline_condition = stuck_and_wrong | very_long
        flatline_flag |= flatline_condition

        if debug:
            debug_masks[col] = pd.DataFrame({
                "residual": residual,
                "residual_abs": residual_abs,
                "deviation_threshold": deviation_thresholds[col],
                "deviation": deviation_condition,
                "sudden_change": sudden_change,
                "change_threshold": change_thresholds[col],
                "spike": spike_condition,
                "run_length": run_length,
                "flatline_threshold": threshold,
                "flatline": flatline_condition,
            }, index=df.index)

    if debug:
        return spike_flag, flatline_flag, debug_masks
    return spike_flag, flatline_flag