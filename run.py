# run.py

import logging
import sys
from pathlib import Path

src_path = Path(__file__).parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from skyguard.config import Config
from skyguard.pipeline import run_pipeline
from skyguard.reporting.alert_intelligence import measure_attribution_accuracy
from skyguard.evaluation.metrics import (
    print_summary_for_results,
    print_metrics,
    print_per_type_breakdown,
    plot_confusion_matrix,
)
from skyguard.visualization.pr_curve import (
    plot_pr_curve,
    plot_pr_curve_all_modes,
)
from skyguard.visualization.shap_explainer import explain_shap_for_results
from skyguard.visualization.dashboard import plot_dashboard_for_results


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

GRAPH_DIR = Path("graphs")
GRAPH_DIR.mkdir(exist_ok=True)


def _print_alert_report(alert_report):
    print("\n" + "=" * 60)
    print("SKYGUARD AI ALERT INTELLIGENCE REPORT")
    print("=" * 60)
    if alert_report.empty:
        print("No active alerts.")
        return
    print(f"Total alerts: {len(alert_report)}")
    cols = ["alert_id", "parameter", "anomaly_type", "root_cause",
            "confidence", "severity", "votes"]
    print(alert_report[cols].head(10).to_string(index=False))
    alert = alert_report.iloc[0]
    print("\n" + "=" * 50)
    print("SAMPLE ALERT")
    print("=" * 50)
    print(f"Station:     {alert['station_id']}")
    print(f"Parameter:   {alert['parameter']}")
    print(f"Type:        {alert['anomaly_type']}")
    print(f"Root cause:  {alert['root_cause']}")
    print(f"Confidence:  {alert['confidence']}%")
    print(f"Severity:    {alert['severity']}")
    print(f"Votes:       {alert['votes']}")
    print(f"Score:       {alert['weighted_score']}")
    print("=" * 50)


def main():
    results = run_pipeline(Config)

    _print_alert_report(results["alert_report"])

    attribution = measure_attribution_accuracy(
        results["alert_report"], results["anomaly_type"]
    )
    if attribution["accuracy"] is not None:
        print(f"\nAttribution accuracy: {attribution['correct']}/{attribution['total']} "
              f"= {attribution['accuracy']:.3f}")

    print_summary_for_results(results)
    print_metrics(results["ground_truth"].values, results["final_prediction"])
    print_per_type_breakdown(
        results["ground_truth"].values,
        results["final_prediction"],
        results["anomaly_type"],
    )
    plot_confusion_matrix(
        results["ground_truth"].values,
        results["final_prediction"],
        save_path=str(GRAPH_DIR / "confusion_matrix.png"),
    )

    plot_pr_curve(results, save_path=str(GRAPH_DIR / "pr_balanced.png"))
    plot_pr_curve_all_modes(results, save_path=str(GRAPH_DIR / "pr_all_modes.png"))

    explain_shap_for_results(results, save_dir=str(GRAPH_DIR))

    plot_dashboard_for_results(
        results, save_path=str(GRAPH_DIR / "skyguard_dashboard.png")
    )

    logging.info("SkyGuard complete. Artifacts in ./graphs/")


if __name__ == "__main__":
    main()