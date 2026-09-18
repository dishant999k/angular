import numpy as np
import pandas as pd
import logging
# --- 2. ANOMALY INJECTOR (Generates Ground Truth) ---
def compute_natural_run_lengths(train_df, config):
    """
    For each parameter, distribution of consecutive-identical-value run lengths
    in clean training data.

    Returns per-parameter dict with p95 / p99 / max run length (in rows, not
    duplicate-count). A run of 5 identical values reports as 5, not 4.
    """
    natural_max_runs = {}
    for col in config.PARAMETERS:
        # is_dup[i] is True when row i equals row i-1 (i.e. row i is inside a run)
        # The first row of each run is NOT marked; the run starts there.
        is_dup = train_df[col].eq(train_df[col].shift(1))
        run_id = (~is_dup).cumsum()

        # Run length = number of rows sharing a run_id.
        # Add 1 to account for the run-start row, which isn't in is_dup as True.
        run_sizes = run_id.value_counts().sort_index()

        natural_max_runs[col] = {
            "p95": float(run_sizes.quantile(0.95)),
            "p99": float(run_sizes.quantile(0.99)),
            "max": int(run_sizes.max()),
        }
    return natural_max_runs


def inject_anomalies(df, config, seed=None):
    """
    Inject spikes and flatlines into a clean test frame.

    Two modes of anomaly count control:
      - Count mode (preferred for testing): set INJECTION_N_SPIKES and
        INJECTION_N_FLATLINES to exact integers.
      - Rate mode: leave those as None and set INJECTION_SPIKE_RATE /
        INJECTION_FLATLINE_RATE to fractions of frame length.

    Returns (injected_df, labels, anomaly_type) where:
      - labels:        pd.Series[bool]  True on anomalous rows
      - anomaly_type:  pd.Series[str]   "spike" / "flatline_<param>" / "none"
    """
    seed = config.INJECTION_SEED if seed is None else seed
    rng = np.random.default_rng(seed)

    missing = set(config.PARAMETERS) - set(df.columns)
    if missing:
        raise ValueError(f"inject_anomalies: missing columns {missing}")

    df = df.copy()
    labels = pd.Series(False, index=df.index)
    anomaly_type = pd.Series("none", index=df.index)
    n = len(df)
    length = config.INJECTION_FLATLINE_LENGTH


    # 1. Spike count
    if config.INJECTION_N_SPIKES is not None:
        n_spikes = int(config.INJECTION_N_SPIKES)
    else:
        n_spikes = int(n * config.INJECTION_SPIKE_RATE)

    n_spikes = min(n_spikes, n)
    if n_spikes < 0:
        raise ValueError(f"INJECTION_N_SPIKES must be >= 0, got {n_spikes}")


    # 2. Flatline count
    if config.INJECTION_N_FLATLINES is not None:
        n_flatlines = int(config.INJECTION_N_FLATLINES)
    else:
        n_flatlines = max(1, int(n * config.INJECTION_FLATLINE_RATE / length))


    # 3. Spike injection (temperature, randomized direction)
    spike_idx = np.array([], dtype=int)
    if n_spikes > 0:
        spike_idx = rng.choice(n, n_spikes, replace=False)
        magnitudes = np.abs(rng.normal(
            config.INJECTION_SPIKE_MAGNITUDE, config.INJECTION_SPIKE_STD, n_spikes
        ))
        signs = rng.choice([-1, 1], n_spikes)
        df.iloc[spike_idx, df.columns.get_loc("temp")] += magnitudes * signs
        labels.iloc[spike_idx] = True
        anomaly_type.iloc[spike_idx] = "spike"



    # 4. Flatline injection (rotate params, disjoint from spikes)
    if n_flatlines > 0:
        # Candidate starts must allow room for `length` rows and not overlap spikes.
        candidate_starts = np.setdiff1d(np.arange(n - length), spike_idx)
        if len(candidate_starts) == 0:
            logging.warning(
                "inject_anomalies: no room for flatlines after excluding spike rows."
            )
            n_flatlines = 0
        else:
            n_flatlines = min(n_flatlines, len(candidate_starts))

        starts = rng.choice(candidate_starts, n_flatlines, replace=False) if n_flatlines else []

        for i, s in enumerate(starts):
            col = config.PARAMETERS[i % len(config.PARAMETERS)]
            frozen_value = df.iloc[s][col]
            # Overwrite rows s+1 .. s+length-1 (row s keeps its real value)
            df.iloc[s + 1 : s + length, df.columns.get_loc(col)] = frozen_value
            labels.iloc[s + 1 : s + length] = True
            anomaly_type.iloc[s + 1 : s + length] = f"flatline_{col}"

    total_rows = int(labels.sum())
    logging.info(
        f"inject_anomalies: {n_spikes} spikes + {n_flatlines} flatline events "
        f"({length} rows each) → {total_rows} anomalous rows "
        f"({total_rows / n:.2%} of frame)."
    )

    return df, labels, anomaly_type