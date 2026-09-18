import logging
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    precision_recall_curve,
    average_precision_score
)


# evaluation.py
"""
Evaluation utilities for SkyGuard.

Computes classification metrics, prints reports, and plots diagnostics.
All functions take plain (y_true, y_pred) arrays so they're independent of
the pipeline's results dict — usable in tests and notebooks alike.
"""

import logging

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    precision_score,
    recall_score,
    f1_score,
    accuracy_score,
)


# ==========================================================
# Core metric computation
# ==========================================================

def calculate_metrics(y_true, y_pred):
    """
    Return a dict of classification metrics with the anomaly class as positive.

    y_true, y_pred are boolean or 0/1 arrays of the same length.
    All returned scalar values are Python floats/ints (not numpy types) so
    they serialize cleanly to JSON.
    """
    y_true = np.asarray(y_true).astype(bool)
    y_pred = np.asarray(y_pred).astype(bool)

    if y_true.shape != y_pred.shape:
        raise ValueError(f"Shape mismatch: y_true={y_true.shape}, y_pred={y_pred.shape}")

    cm = confusion_matrix(y_true, y_pred, labels=[False, True])
    tn, fp, fn, tp = (int(x) for x in cm.ravel())

    total_injected = int(y_true.sum())
    total_detected = int(y_pred.sum())

    precision = float(precision_score(y_true, y_pred, zero_division=0))
    recall = float(recall_score(y_true, y_pred, zero_division=0))
    f1 = float(f1_score(y_true, y_pred, zero_division=0))
    accuracy = float(accuracy_score(y_true, y_pred))
    detection_rate = tp / total_injected if total_injected else 0.0

    return {
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1_score": f1,
        "detection_rate": detection_rate,
        "true_positives": tp,
        "true_negatives": tn,
        "false_positives": fp,
        "false_negatives": fn,
        "total_injected": total_injected,
        "total_detected": total_detected,
        "confusion_matrix": cm,
    }


# ==========================================================
# Reporting
# ==========================================================

def print_metrics(y_true, y_pred):
    """Print classification report + SkyGuard summary. Returns metrics dict."""
    y_true = np.asarray(y_true).astype(bool)
    y_pred = np.asarray(y_pred).astype(bool)

    print("\n" + "=" * 50)
    print("SKYGUARD PERFORMANCE METRICS")
    print("=" * 50)

    print("\nClassification Report:")
    print(classification_report(y_true, y_pred,
                                target_names=["Normal", "Anomaly"],
                                zero_division=0))

    m = calculate_metrics(y_true, y_pred)

    print("-" * 50)
    print(f"Total Injected Anomalies : {m['total_injected']}")
    print(f"Total System Alerts      : {m['total_detected']}")
    print(f"True Positives           : {m['true_positives']}")
    print(f"False Positives          : {m['false_positives']}")
    print(f"False Negatives          : {m['false_negatives']}")
    print(f"Detection Rate           : {m['detection_rate'] * 100:.2f}%")
    print(f"Precision                : {m['precision']:.4f}")
    print(f"Recall                   : {m['recall']:.4f}")
    print(f"F1-Score                 : {m['f1_score']:.4f}")
    print(f"Accuracy                 : {m['accuracy']:.4f}")
    print("=" * 50)

    return m


def print_per_type_breakdown(y_true, y_pred, anomaly_type):
    """
    Per-anomaly-type detection rate. Validation-only — never used to build alerts.

    anomaly_type is a pandas Series aligned with y_true/y_pred; rows where it
    is "none" are excluded.
    """
    y_true = np.asarray(y_true).astype(bool)
    y_pred = np.asarray(y_pred).astype(bool)
    anomaly_type = pd.Series(np.asarray(anomaly_type))

    diag = pd.DataFrame({"type": anomaly_type.values, "detected": y_pred})
    diag = diag[diag["type"] != "none"]

    if diag.empty:
        print("\nNo injected anomalies to break down.")
        return pd.DataFrame()

    print("\nPer-type detection rate:")
    breakdown = diag.groupby("type")["detected"].agg(["sum", "count", "mean"])
    print(breakdown)
    return breakdown


def print_modes_table(mode_metrics):
    """
    Print the four-mode operating comparison.

    mode_metrics is a dict[modename, metrics_dict] as returned by
    calculate_metrics for each operating mode.
    """
    rows = []
    for mode_name, m in mode_metrics.items():
        rows.append({
            "mode": mode_name,
            "threshold": m.get("threshold"),
            "alerts": m["total_detected"],
            "tp": m["true_positives"],
            "fp": m["false_positives"],
            "fn": m["false_negatives"],
            "precision": round(m["precision"], 4),
            "recall": round(m["recall"], 4),
            "f1": round(m["f1_score"], 4),
        })
    df = pd.DataFrame(rows).set_index("mode")

    print("\n" + "=" * 90)
    print("OPERATIONAL MODES COMPARISON")
    print("=" * 90)
    print(df.to_string())
    print("=" * 90)
    return df


# ==========================================================
# Plots
# ==========================================================

def plot_confusion_matrix(y_true, y_pred, save_path=None, title="SkyGuard Confusion Matrix"):
    """Plot the confusion matrix. Returns the matrix for downstream use."""
    y_true = np.asarray(y_true).astype(bool)
    y_pred = np.asarray(y_pred).astype(bool)

    cm = confusion_matrix(y_true, y_pred, labels=[False, True])

    plt.figure(figsize=(6, 4))
    sns.heatmap(cm, annot=True, fmt="d", cmap="Blues",
                xticklabels=["Normal", "Anomaly"],
                yticklabels=["Normal", "Anomaly"])
    plt.title(title)
    plt.ylabel("Actual (Ground Truth)")
    plt.xlabel("Predicted")
    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches="tight")

    plt.show()
    return cm


# ==========================================================
# Convenience: run everything for a results dict
# ==========================================================

def evaluate_results(results, save_plots_dir=None):
    """
    Run the full evaluation suite on a pipeline results dict.

    Returns a dict of the computed metrics and the per-type breakdown, so
    callers can log or serialize them.
    """
    y_true = np.asarray(results["ground_truth"]).astype(bool)
    y_pred = np.asarray(results["final_prediction"]).astype(bool)
    anomaly_type = results["anomaly_type"]

    metrics = print_metrics(y_true, y_pred)
    breakdown = print_per_type_breakdown(y_true, y_pred, anomaly_type)

    cm_path = f"{save_plots_dir}/confusion_matrix.png" if save_plots_dir else None
    plot_confusion_matrix(y_true, y_pred, save_path=cm_path)

    if "mode_metrics" in results:
        print_modes_table(results["mode_metrics"])

    return {"metrics": metrics, "per_type": breakdown}

    

def print_summary_from_metrics(metrics):
    """
    Compact summary block, formatted from a metrics dict produced by
    calculate_metrics(). Avoids recomputing TP/FP/FN.
    """
    print("\n" + "=" * 50)
    print("AWS ANOMALY REPORT SUMMARY")
    print("=" * 50)
    print(f"Total Injected Anomalies:        {metrics['total_injected']}")
    print(f"Total System Alerts:             {metrics['total_detected']}")
    print(f"Correctly Detected (TP):         {metrics['true_positives']}")
    print(f"Missed (FN):                     {metrics['false_negatives']}")
    print(f"False Alarms (FP):               {metrics['false_positives']}")
    print(f"Detection Rate (recall):         {metrics['detection_rate'] * 100:.2f}%")
    print(f"Precision:                       {metrics['precision']:.4f}")
    print("=" * 50)


def print_summary_for_results(results):
    """Convenience wrapper: extract arrays, compute metrics, print summary."""
    y_true = np.asarray(results["ground_truth"]).astype(bool)
    y_pred = np.asarray(results["final_prediction"]).astype(bool)
    metrics = calculate_metrics(y_true, y_pred)
    print_summary_from_metrics(metrics)
    return metrics