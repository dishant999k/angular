import logging
import pandas as pd
import numpy as np
from pathlib import Path
from types import SimpleNamespace
from skyguard.config import Config
from skyguard.preprocessing.anomaly_injection import inject_anomalies
from skyguard.data.weather_fetcher import (fetch_openmeteo,fetch_neighbor_data,fetch_elevation)
from skyguard.detection_layers.layer_a_statistical import layer_a_statistical
from skyguard.detection_layers.layer_b_mahalanobis import (fit_layer_b,layer_b_mahalanobis)
from skyguard.detection_layers.layer_c_isolation_forest import (fit_layer_c,layer_c_isolation_forest)
from skyguard.detection_layers.layer_d_spatial import layer_d_spatial
from skyguard.detection_layers.combined_layers_voting import combine_layers_weighted
from skyguard.evaluation.metrics import (print_metrics,plot_confusion_matrix,analyze_anomaly_types,plot_precision_recall_curve)
from skyguard.visualization.shap_explainer import explain_isolation_forest
from skyguard.visualization.dashboard import plot_dashboard
from skyguard.reporting.alert_intelligence import (
    generate_alert_intelligence_report
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

#for making graph folder(if doesnt exist)

GRAPH_DIR = Path("graphs")
GRAPH_DIR.mkdir(exist_ok=True)


def _build_mode_config(base_config, threshold, min_votes):
    """Create a lightweight config proxy for a specific operating mode."""

    config_values = {
        name: getattr(base_config, name)
        for name in dir(base_config)
        if name.isupper()
    }
    config_values["VOTING_THRESHOLD"] = threshold
    config_values["MIN_VOTES"] = min_votes
    return SimpleNamespace(**config_values)

def run_pipeline():

    logging.info("Starting SkyGuard AI Pipeline...")

    LAT, LON = 26.9124, 75.7873
    start_date = "2023-01-01"
    end_date = "2025-12-31"

    # --------------------------------------------------
    # 1. Fetch primary weather data
    # --------------------------------------------------

    logging.info(
        f"Fetching weather data for ({LAT}, {LON})..."
    )

    df = fetch_openmeteo(LAT,LON,start_date,end_date)

    if df is None or df.empty:
        logging.error("No data fetched for primary station.")
        return None

    logging.info(
        f"Primary data shape: {df.shape}"
    )

    # --------------------------------------------------
    # 2. Fetch neighboring stations
    # --------------------------------------------------

    neighbor_df, neighbor_alts = fetch_neighbor_data(
        LAT,
        LON,
        start_date,
        end_date,
        df.index
    )

    if neighbor_df.empty:
        logging.warning(
            "No neighbor data available. Layer D will be disabled."
        )
    else:
        logging.info(
            f"Neighbor data shape: {neighbor_df.shape}"
        )

    # --------------------------------------------------
    # 3. Get primary station elevation
    # --------------------------------------------------

    primary_alt = fetch_elevation(LAT, LON)

    # --------------------------------------------------
    # 4. Split dataset
    # --------------------------------------------------

    train_size = int(len(df) * Config.TRAIN_SPLIT)
    val_size = int(len(df) * 0.15)

    train_df = df.iloc[:train_size].copy()

    val_df = df.iloc[
        train_size:train_size + val_size
    ].copy()

    test_df = df.iloc[
        train_size + val_size:
    ].copy()

    neighbor_test_df = (
        neighbor_df.iloc[train_size + val_size:].copy()
        if not neighbor_df.empty
        else pd.DataFrame()
    )

    logging.info(
        f"Train: {len(train_df)}, "
        f"Validation: {len(val_df)}, "
        f"Test: {len(test_df)}"
    )

    # --------------------------------------------------
    # 5. Inject anomalies into TEST ONLY
    # --------------------------------------------------

    test_df_injected, ground_truth, anomaly_type = inject_anomalies(test_df)
    logging.info(f"💉 Injected {ground_truth.sum()} anomalies into the test set.")
    test_df_injected[["temp", "pres", "rhum"]] = test_df_injected[["temp", "pres", "rhum"]].astype(float)

    # --------------------------------------------------
    # 6. Fit detection models
    # --------------------------------------------------

    mean, cov_inv, mahalanobis_threshold, hourly_mean = (
        fit_layer_b(train_df, percentile=99)
    )

    if_model = fit_layer_c(train_df,Config)

    # --------------------------------------------------
    # 7. Run detection layers
    # --------------------------------------------------

    spike_flag_a, flatline_flag_a = layer_a_statistical(
        test_df_injected,
        train_df,
        Config,
        hourly_mean
    )

    flag_b = layer_b_mahalanobis(
        test_df_injected,
        mean,
        cov_inv,
        mahalanobis_threshold,
        hourly_mean
    )

    flag_c = layer_c_isolation_forest(
        test_df_injected,
        if_model,
        Config
    )

    flag_d, spatial_frac = layer_d_spatial(test_df_injected,neighbor_test_df,
        primary_alt,
        neighbor_alts,
        Config
    )

    # --------------------------------------------------
    # 8. Combine detection results
    # --------------------------------------------------

    mode_reports = {}
    mode_metrics = {}

    for mode_name, mode_cfg in Config.OPERATING_MODES.items():
        mode_config = _build_mode_config(
            Config,
            threshold=mode_cfg["threshold"],
            min_votes=mode_cfg["min_votes"],
        )

        rep = combine_layers_weighted(
            spike_flag_a,
            flatline_flag_a,
            flag_b,
            flag_c,
            flag_d,
            mode_config,
        )

        mode_reports[mode_name] = rep

        pred = rep["alert"].values
        tp = int((ground_truth & pred).sum())
        fp = int((~ground_truth & pred).sum())
        fn = int((ground_truth & ~pred).sum())
        precision = tp / (tp + fp) if (tp + fp) else 0.0
        recall = tp / (tp + fn) if (tp + fn) else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0

        mode_metrics[mode_name] = {
            "threshold": mode_cfg["threshold"],
            "alerts": int(pred.sum()),
            "tp": tp,
            "fp": fp,
            "fn": fn,
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1": round(f1, 4),
        }

    metrics_df = pd.DataFrame(mode_metrics).T
    print("\n" + "=" * 90)
    print("🎛️  OPERATIONAL MODES COMPARISON")
    print("=" * 90)
    print(metrics_df[["threshold", "alerts", "tp", "fp", "fn", "precision", "recall", "f1"]].to_string())
    print("=" * 90)

    default_mode = Config.DEFAULT_MODE
    if default_mode not in mode_reports:
        raise KeyError(
            f"DEFAULT_MODE '{default_mode}' is not defined in OPERATING_MODES."
        )

    report = mode_reports[default_mode]
    final_prediction = report["alert"].values
    
    # --------------------------------------------------
    # Alert Intelligence Report
    # --------------------------------------------------

    alert_report = generate_alert_intelligence_report(
        test_df=test_df_injected,
        report=report,
        anomaly_type=anomaly_type,
        config=Config,
        station_id="AWS_1042"
    )

    print("\n" + "=" * 60)
    print("🚨 SKYGUARD AI ALERT INTELLIGENCE REPORT")
    print("=" * 60)

    if alert_report.empty:

        print("✅ No active alerts detected.")

    else:

        print(
            f"Total Intelligent Alerts: {len(alert_report)}"
        )

        print("\nRecent Alerts:")

        print(
            alert_report[
                [
                    "alert_id",
                    "station_id",
                    "parameter",
                    "anomaly_type",
                    "root_cause",
                    "confidence",
                    "severity",
                    "votes"
                ]
            ]
            .head(10)
            .to_string(index=False)
        )

        # --------------------------------------------------
        # Detailed Alert
        # --------------------------------------------------

        alert = alert_report.iloc[0]

        print("\n" + "=" * 50)
        print("🚨 ALERT")
        print("=" * 50)

        print(f"\nStation: {alert['station_id']}")
        print(f"Parameter: {alert['parameter']}")

        print("\nAnomaly Type:")
        print(alert["anomaly_type"])

        print("\nRoot Cause:")
        print(alert["root_cause"])

        print("\nConfidence:")
        print(f"{alert['confidence']}%")

        print("\nSeverity:")
        print(alert["severity"])

        print("\nLayer Consensus:")
        print(f"{alert['votes']} layers")

        print("\nWeighted Score:")
        print(alert["weighted_score"])

        print("\n" + "=" * 50)


    # =========================================================
    # EVALUATION
    # =========================================================

    print_metrics(
        ground_truth,
        final_prediction
    )

    plot_confusion_matrix(
        ground_truth,
        final_prediction,
        save_path="graphs/confusion_matrix.png"
    )

    analyze_anomaly_types(
        anomaly_type,
        final_prediction
    )


    # =========================================================
    # PRECISION-RECALL ANALYSIS
    # =========================================================

    plot_precision_recall_curve(
        y_true=ground_truth,
        report=report,                             
        final_prediction=final_prediction,
        operating_threshold=Config.OPERATING_MODES[default_mode]["threshold"],
        save_path="graphs/skyguard_pr_curve.png",
        title="SkyGuard AI — Precision-Recall Trade-off",
    )


    # =========================================================
    # EXPLAINABILITY
    # =========================================================

    explain_isolation_forest(
        model=if_model,
        test_df=test_df_injected,
        flag_c=flag_c,
        window=Config.WINDOW
    )


    # =========================================================
    # DASHBOARD
    # =========================================================

    plot_dashboard(
        test_df=test_df_injected,
        report=report,
        config=Config,
        save_path="graphs/skyguard_dashboard.png"
    )

    # --------------------------------------------------
    # 10. Return results
    # --------------------------------------------------

    return {
        "train_df": train_df,
        "val_df": val_df,
        "test_df": test_df,

        # Ground truth
        "ground_truth": ground_truth,
        "anomaly_type": anomaly_type,

        # Layer outputs
        "layer_a_spikes": spike_flag_a,
        "layer_a_flatlines": flatline_flag_a,
        "layer_b": flag_b,
        "layer_c": flag_c,
        "layer_d": flag_d,
        "spatial_fraction": spatial_frac,

        # Final detection results
        "final_prediction": final_prediction,
        "report": report,
        "mode_reports": mode_reports,
        "mode_metrics": mode_metrics,
        "default_mode": default_mode,

        # Model
        "isolation_forest": if_model,
    }

if __name__ == "__main__":
    run_pipeline()