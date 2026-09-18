import pandas as pd
import numpy as np

def _can_run_spatial(df, neighbor_df, config):
    """Input gate. Returns (ok, reason)."""
    if neighbor_df is None or neighbor_df.empty:
        return False, "no_neighbor_data"
    if len(neighbor_df.columns) < config.MIN_NEIGHBORS:
        return False, f"only_{len(neighbor_df.columns)}_neighbors"
    common = df.index.intersection(neighbor_df.index)
    if len(common) < config.MIN_SPATIAL_OVERLAP:
        return False, f"only_{len(common)}_overlapping_timestamps"
    return True, "ok"


def _all_altitudes_available(neighbor_df, station_alt, neighbor_alts):
    """True only if primary and every neighbor has a real altitude."""
    if station_alt is None or not neighbor_alts:
        return False
    return all(
        name in neighbor_alts and neighbor_alts[name] is not None
        for name in neighbor_df.columns
    )


def _apply_lapse_correction(neighbor_df, station_alt, neighbor_alts, config):
    """
    Shift neighbor temperatures to the primary station's altitude.
    T_corrected = T_neighbor + (alt_neighbor - alt_primary) * lapse_rate

    Skipped entirely if any altitude is missing.
    """
    if not _all_altitudes_available(neighbor_df, station_alt, neighbor_alts):
        return neighbor_df, False
    corrected = neighbor_df.copy()
    for name in corrected.columns:
        alt_diff = neighbor_alts[name] - station_alt
        corrected[name] = corrected[name] + alt_diff * config.LAPSE_RATE
    return corrected, True


def _apply_barometric_correction(neighbor_df, station_alt, neighbor_alts, config):
    """
    Reduce neighbor surface pressure to the primary station's altitude.
    P_corrected = P_neighbor * exp((alt_neighbor - alt_primary) / scale_height)

    """
    if not _all_altitudes_available(neighbor_df, station_alt, neighbor_alts):
        return neighbor_df, False
    corrected = neighbor_df.copy()
    for name in corrected.columns:
        alt_diff = neighbor_alts[name] - station_alt
        corrected[name] = corrected[name] * np.exp(alt_diff / config.PRESSURE_SCALE_HEIGHT)
    return corrected, True


def _spatial_check_one_parameter(
    primary_series, neighbor_df, correction_fn,
    station_alt, neighbor_alts, abs_threshold, mad_floor, config
):
    """
    Robust-MAD spatial check for one parameter.
    Flags when BOTH the absolute deviation and the robust z-score exceed thresholds.
    Returns (flag_series, concordance_series, diag_dict).
    """
    corrected, correction_applied = correction_fn(
        neighbor_df, station_alt, neighbor_alts, config
    )

    median_neighbor = corrected.median(axis=1)
    mad_neighbor = (corrected.sub(median_neighbor, axis=0)).abs().median(axis=1)

    # Floor MAD: homogeneous neighbors (identical readings) would otherwise
    # produce z-scores in the millions on any small deviation.
    mad_safe = mad_neighbor.clip(lower=mad_floor)

    deviation = primary_series - median_neighbor
    abs_deviation = deviation.abs()
    robust_z = deviation / (1.4826 * mad_safe)

    flag = (abs_deviation > abs_threshold) & (robust_z.abs() > config.Z_SCORE_THRESH)


    concordance = 1 - (abs_deviation / (abs_deviation + mad_safe))

    diag = {
        "correction_applied": correction_applied,
        "median_neighbor": median_neighbor,
        "mad_neighbor": mad_neighbor,
        "mad_safe": mad_safe,
        "abs_deviation": abs_deviation,
        "robust_z": robust_z,
    }
    return flag, concordance, diag


def layer_d_spatial(
    df, neighbor_temp_df, neighbor_pres_df,
    station_alt, neighbor_alts, config, debug=False
):
    """
    Spatial consistency across temperature and pressure.

    Runs an independent robust-MAD check per parameter and ORs the flags:
    a row is flagged if either temperature OR pressure disagrees with the
    neighbor consensus beyond thresholds.

    Abstention (per parameter): if a parameter has fewer than MIN_NEIGHBORS
    neighbors or fewer than MIN_SPATIAL_OVERLAP shared timestamps, that
    parameter contributes no flag. If both parameters abstain, Layer D
    returns all-False and the pipeline effectively runs on A+B+C — the
    weighted-vote gate downstream is unchanged.

    Lapse-rate and barometric corrections are applied only when the primary
    AND every neighbor has a real altitude. Otherwise the comparison runs
    on raw values — a partial correction introduces a systematic bias
    larger than the correction itself.
    """
    empty_flag = pd.Series(False, index=df.index)
    empty_conc = pd.Series(0.0, index=df.index)

    temp_ok, temp_reason = _can_run_spatial(df, neighbor_temp_df, config)
    pres_ok, pres_reason = _can_run_spatial(df, neighbor_pres_df, config)

    if not temp_ok:
        logging.info(f"Layer D [temp]: abstaining ({temp_reason}).")
    if not pres_ok:
        logging.info(f"Layer D [pressure]: abstaining ({pres_reason}).")

    if not temp_ok and not pres_ok:
        logging.info("Layer D: abstaining entirely — voting continues on A+B+C.")
        if debug:
            return empty_flag, empty_conc, {
                "status": "abstained",
                "temp_reason": temp_reason,
                "pres_reason": pres_reason,
            }
        return empty_flag, empty_conc

    combined_flag = pd.Series(False, index=df.index)
    concordances = []
    diag = {"status": "ok", "temp": None, "pressure": None}

    if temp_ok:
        common = df.index.intersection(neighbor_temp_df.index)
        temp_flag, temp_conc, temp_diag = _spatial_check_one_parameter(
            df.loc[common, "temp"],
            neighbor_temp_df.loc[common],
            _apply_lapse_correction,
            station_alt, neighbor_alts,
            config.TEMP_DIFF_THRESH, config.MIN_NEIGHBOR_MAD_TEMP,
            config,
        )
        combined_flag.loc[common] |= temp_flag
        concordances.append(temp_conc)
        diag["temp"] = temp_diag
        if not temp_diag["correction_applied"] and neighbor_alts:
            logging.warning("Layer D [temp]: altitude data incomplete — lapse correction skipped.")

    if pres_ok:
        common = df.index.intersection(neighbor_pres_df.index)
        pres_flag, pres_conc, pres_diag = _spatial_check_one_parameter(
            df.loc[common, "pres"],
            neighbor_pres_df.loc[common],
            _apply_barometric_correction,
            station_alt, neighbor_alts,
            config.PRES_DIFF_THRESH, config.MIN_NEIGHBOR_MAD_PRES,
            config,
        )
        combined_flag.loc[common] |= pres_flag
        concordances.append(pres_conc)
        diag["pressure"] = pres_diag
        if not pres_diag["correction_applied"] and neighbor_alts:
            logging.warning("Layer D [pressure]: altitude data incomplete — barometric correction skipped.")

    # Mean concordance when both parameters ran; single series otherwise.
    if concordances:
        combined_conc = pd.concat(concordances, axis=1).mean(axis=1).reindex(df.index, fill_value=0.0)
    else:
        combined_conc = empty_conc

    if debug:
        return combined_flag, combined_conc, diag
    return combined_flag, combined_conc