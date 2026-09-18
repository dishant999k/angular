# skyguard/reporting/alert_intelligence.py

import logging

import numpy as np
import pandas as pd


# ---------- Evidence extraction ----------

def _evidence(row):
    return {
        "a_spike": bool(row.get("layer_a_spike", False)),
        "a_flat":  bool(row.get("layer_a_flatline", False)),
        "b":       bool(row.get("layer_b", False)),
        "c":       bool(row.get("layer_c", False)),
        "d":       bool(row.get("layer_d", False)),
        "override": bool(row.get("flatline_override", False)),
        "votes":   int(row.get("votes", 0)),
        "score":   float(row.get("weighted_score", 0.0)),
    }


# ---------- Parameter attribution ----------

def _attribute_from_residual(test_df, idx, expected_row, config):
    """Attribution by post-hoc residual vs climatology. Returns (label, deviations)."""
    deviations = {}
    for col in config.PARAMETERS:
        exp = expected_row.get(col, np.nan)
        if pd.isna(exp):
            deviations[col] = 0.0
            continue
        scale = config.PARAMETER_SCALES.get(col, 1.0)
        deviations[col] = abs(float(test_df.loc[idx, col]) - float(exp)) / scale

    if not deviations or max(deviations.values()) == 0.0:
        return "Sensor", deviations
    top = max(deviations, key=deviations.get)
    if deviations[top] < 0.5:
        return "Multi-Parameter", deviations
    return config.PARAMETER_DISPLAY[top], deviations


def _attribute_from_freeze(test_df, idx, config):
    """Attribution for override alerts: parameter with near-zero first-difference."""
    idx_ts = pd.Timestamp(idx)
    prev_candidates = test_df.index[test_df.index < idx_ts]
    if len(prev_candidates) == 0:
        return "Sensor"
    prev = prev_candidates[-1]
    changes = {
        col: abs(float(test_df.loc[idx_ts, col]) - float(test_df.loc[prev, col]))
        for col in config.PARAMETERS
    }
    min_col = min(changes, key=changes.get)
    if changes[min_col] > 0.01:
        return "Sensor"  # nothing actually frozen — fall back
    return config.PARAMETER_DISPLAY[min_col]


# ---------- Narrative ----------

def _anomaly_name(ev):
    if ev["override"]:
        return "Persistent Sensor Reading"
    if ev["a_spike"] and ev["a_flat"]:
        return "Multi-Condition Sensor Fault"
    if ev["a_spike"]:
        return "Sensor Spike"
    if ev["a_flat"]:
        return "Sensor Flatline"
    if ev["votes"] >= 3:
        return "Multi-Layer Anomaly"
    return "Unusual Weather Observation"


def _root_cause(ev, parameter):
    if ev["override"]:
        return f"{parameter} reading frozen — sensor likely stuck"
    if ev["a_spike"]:
        return f"Sudden {parameter} spike inconsistent with hourly norm"
    if ev["a_flat"]:
        return f"{parameter} frozen over multiple consecutive readings"
    if ev["votes"] >= 3:
        return f"Independent detectors disagree on {parameter} — investigate sensor"
    if ev["votes"] >= 2:
        return f"{parameter} anomalous across multiple detectors"
    return "Requires meteorological verification"


def _confidence(ev, config):
    """Ordinal evidence strength, not a calibrated probability."""
    if ev["override"] and ev["votes"] < 2:
        return config.CONFIDENCE_BY_EVIDENCE["override_only"]
    if ev["votes"] >= 4:
        return config.CONFIDENCE_BY_EVIDENCE["votes_4plus"]
    if ev["votes"] == 3:
        return config.CONFIDENCE_BY_EVIDENCE["votes_3"]
    if ev["votes"] == 2:
        return config.CONFIDENCE_BY_EVIDENCE["votes_2"]
    return config.CONFIDENCE_BY_EVIDENCE["single"]


def _severity(confidence, config):
    for threshold, label in config.SEVERITY_BY_CONFIDENCE:
        if confidence >= threshold:
            return label
    return "LOW"


# ---------- Main report ----------

def generate_alert_intelligence_report(
    test_df, report, config, climatology, station_id="AWS_1042",
):
    """
    Convert detection evidence into human-readable alerts.

    Consumes only detection outputs and the fitted climatology — never the
    injected ground-truth labels. Parameter attribution uses post-hoc residuals
    (or, for override alerts, the frozen-parameter heuristic).
    """
    alert_mask = report["alert"].fillna(False)
    alert_index = report.index[alert_mask]
    if len(alert_index) == 0:
        return pd.DataFrame()

    # One climatology call for all alert rows
    expected_all = climatology(alert_index)

    alerts = []
    for idx in alert_index:
        ev = _evidence(report.loc[idx])

        if ev["override"]:
            parameter = _attribute_from_freeze(test_df, idx, config)
            deviations = {col: 0.0 for col in config.PARAMETERS}
        else:
            parameter, deviations = _attribute_from_residual(
                test_df, idx, expected_all.loc[idx], config
            )

        confidence = _confidence(ev, config)

        alerts.append({
            "alert_id":     f"ALERT-{station_id}-{pd.Timestamp(idx).isoformat()}",
            "station_id":   station_id,
            "timestamp":    pd.Timestamp(idx).isoformat(),
            "parameter":    parameter,
            "anomaly_type": _anomaly_name(ev),
            "root_cause":   _root_cause(ev, parameter),
            "confidence":   confidence,
            "severity":     _severity(confidence, config),
            "votes":        ev["votes"],
            "weighted_score": round(ev["score"], 2),
            "layer_a_spike":  ev["a_spike"],
            "layer_a_flatline": ev["a_flat"],
            "layer_b":        ev["b"],
            "layer_c":        ev["c"],
            "layer_d":        ev["d"],
            "override":       ev["override"],
            "temp_dev":  round(deviations.get("temp", 0.0), 2),
            "pres_dev":  round(deviations.get("pres", 0.0), 2),
            "rhum_dev":  round(deviations.get("rhum", 0.0), 2),
            "temperature": round(float(test_df.loc[idx, "temp"]), 2),
            "pressure":    round(float(test_df.loc[idx, "pres"]), 2),
            "humidity":    round(float(test_df.loc[idx, "rhum"]), 2),
        })

    return pd.DataFrame(alerts)


# ---------- Validation ----------

def measure_attribution_accuracy(alert_report, anomaly_type):
    """
    How often the alert report attributes to the same parameter as injected.
    Validation-only — never used to produce the report.
    """
    if alert_report.empty:
        return {"total": 0, "correct": 0, "accuracy": None}

    gt_to_display = {
        "spike":          "Temperature",
        "flatline_temp":  "Temperature",
        "flatline_pres":  "Atmospheric Pressure",
        "flatline_rhum":  "Relative Humidity",
    }

    correct = 0
    evaluated = 0
    for _, row in alert_report.iterrows():
        ts = pd.Timestamp(row["timestamp"])
        if ts not in anomaly_type.index:
            logging.warning(f"attribution_accuracy: {ts} not in anomaly_type — skipping.")
            continue
        gt_label = anomaly_type.loc[ts]
        if gt_label not in gt_to_display:
            continue
        evaluated += 1
        if row["parameter"] == gt_to_display[gt_label]:
            correct += 1

    return {
        "total": evaluated,
        "correct": correct,
        "accuracy": correct / evaluated if evaluated else None,
    }