import pandas as pd 
from sklearn.ensemble import IsolationForest as IForest
import logging

def build_isolation_features(df, config):
    """Raw values + rolling std per parameter. The window std is what gives the
    model visibility into flatlines (std → 0 when a sensor freezes)."""
    features = pd.DataFrame(index=df.index)
    for col in config.PARAMETERS:
        features[f"{col}_raw"] = df[col]
        features[f"{col}_std"] = df[col].rolling(config.WINDOW).std()
    return features


def fit_layer_c(train_df, config, debug=False):
    """
    Isolation Forest on raw values + rolling std.

    The rolling std features are what let IF flag flatlines: a frozen sensor
    produces std=0, which is out-of-distribution for clean weather data — but
    only after WINDOW-1 rows into the freeze (the window needs to fill with
    flat values first). Layer A's run-length logic covers the leading rows.
    """
    features = build_isolation_features(train_df, config).dropna()

    if len(features) < config.LAYER_C_MIN_TRAIN_ROWS:
        logging.warning(f"Layer C: only {len(features)} clean rows — skipping fit.")
        return None

    clf = IForest(contamination=config.CONTAMINATION,
                  random_state=config.RANDOM_SEED)
    clf.fit(features)
    logging.info(f"Layer C: trained on {len(features)} clean rows.")
    return clf


def layer_c_isolation_forest(df, model, config, debug=False):
    if model is None:
        return pd.Series(False, index=df.index)

    features_full = build_isolation_features(df, config)
    features = features_full.dropna()

    dropped = len(features_full) - len(features)
    if dropped > 0:
        logging.warning(f"Layer C: dropped {dropped} rows with NaN features "
                        f"(rolling-std warmup or missing raw values).")

    flag_series = pd.Series(False, index=df.index)
    if features.empty:
        return flag_series

    preds = model.predict(features)
    scores = model.score_samples(features)

    flag_series.loc[features.index] = (preds == -1)

    if debug:
        return flag_series, pd.Series(scores, index=features.index)
    return flag_series