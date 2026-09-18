import pandas as pd
import logging
#--- Combined Layer Analysis ---
def _renormalize_weights(config, present_layers):
    """
    Scale B/C/D weights so their sum stays constant when a layer abstains.
    Layer A is excluded — it's a rule-based flag, not a distributional vote.
    """
    full_sum = config.WEIGHT_B + config.WEIGHT_C + config.WEIGHT_D
    present_sum = (
        (config.WEIGHT_B if "b" in present_layers else 0.0)
        + (config.WEIGHT_C if "c" in present_layers else 0.0)
        + (config.WEIGHT_D if "d" in present_layers else 0.0)
    )
    if present_sum == 0:
        # Nothing to vote with — return zeros rather than divide by zero.
        return 0.0, 0.0, 0.0
    scale = full_sum / present_sum
    return (
        config.WEIGHT_B * scale if "b" in present_layers else 0.0,
        config.WEIGHT_C * scale if "c" in present_layers else 0.0,
        config.WEIGHT_D * scale if "d" in present_layers else 0.0,
    )


def combine_layers_weighted(
    spike_flag_a, flatline_flag_a, flag_b, flag_c, flag_d, config,
    threshold, min_votes, mode_name="unknown",
    renormalize=True, watch_margin=0.5,
):
    """
    Fuse layer outputs into a single alert decision.

    Voting:
      - Layer A collapses its spike and flatline flags into ONE vote; a
        spike and a flatline firing together shouldn't count as two layers.
      - Layers B/C/D contribute one vote each. Pass None for a layer that
        abstained (e.g. Layer D without neighbors).
      - min_votes gates on the number of distinct layers agreeing.
      - weighted_score combines A (fixed) with renormalized B/C/D weights.
        Renormalization keeps the threshold semantics stable when a layer
        abstains — the sum of B+C+D weights is preserved.
      - Flatline is a hard override, bypassing the vote entirely.

    Output:
      - alert:   final decision (override OR vote)
      - watch:   borderline tier (score within watch_margin of threshold)
      - votes:   distinct-layer count that fired
      - weighted_score: renormalized score
      - flatline_override: whether the flatline path fired
    """
    # Normalize None → all-False so downstream code is uniform.
    def _or_default(series):
        return pd.Series(False, index=spike_flag_a.index) if series is None else series

    flag_b = _or_default(flag_b)
    flag_c = _or_default(flag_c)
    flag_d = _or_default(flag_d)

    present_layers = {"b", "c"}
    if flag_d is not None:
        present_layers.add("d")

    w_b, w_c, w_d = (
        _renormalize_weights(config, present_layers) if renormalize
        else (config.WEIGHT_B, config.WEIGHT_C, config.WEIGHT_D)
    )

    flatline_override = flatline_flag_a.astype(bool)
    layer_a_vote = (spike_flag_a | flatline_flag_a).astype(int)

    total_votes = (
        layer_a_vote
        + flag_b.astype(int)
        + flag_c.astype(int)
        + flag_d.astype(int)
    )

    weighted_score = (
        config.WEIGHT_A * spike_flag_a.astype(float)
        + w_b * flag_b.astype(float)
        + w_c * flag_c.astype(float)
        + w_d * flag_d.astype(float)
    )

    ml_alert = (weighted_score >= threshold) & (total_votes >= min_votes)
    watch_zone = (
        (weighted_score >= threshold - watch_margin)
        & (total_votes >= min_votes)
        & ~ml_alert
    )

    alert = flatline_override | ml_alert
    watch = flatline_override | ml_alert | watch_zone

    logging.info(
        f"[{mode_name}] alerts={int(alert.sum())} "
        f"(vote={int(ml_alert.sum())}, "
        f"override_only={int((flatline_override & ~ml_alert).sum())}, "
        f"watch_only={int((watch_zone & ~alert).sum())})"
    )

    return pd.DataFrame({
        "mode": mode_name,
        "threshold": threshold,
        "min_votes": min_votes,
        "layer_a_spike": spike_flag_a,
        "layer_a_flatline": flatline_flag_a,
        "layer_b": flag_b,
        "layer_c": flag_c,
        "layer_d": flag_d,
        "votes": total_votes,
        "flatline_override": flatline_override,
        "weighted_score": weighted_score,
        "ml_alert": ml_alert,
        "watch_zone": watch_zone,
        "watch": watch,
        "alert": alert,
    })