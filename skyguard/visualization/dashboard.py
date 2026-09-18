import logging
import matplotlib.pyplot as plt
import numpy as np


def plot_dashboard(test_df, report, config, mode_name=None, save_path=None):
    """
    Two-panel monitoring dashboard.

    Panel 1: raw temperature with watch and alert markers.
    Panel 2: vote count per timestamp with the mode's min_votes gate.

    report must be indexed the same as test_df. If not, it's reindexed here
    so the two panels share an x-axis.
    """
    logging.info("Plotting SkyGuard dashboard...")

    mode_name = mode_name or config.DEFAULT_MODE
    mode_cfg = config.OPERATING_MODES[mode_name]

    # Align report to the frame being plotted — no-op if already aligned.
    report = report.reindex(test_df.index).fillna(False)
    # Numeric columns need fillna(0), not fillna(False)
    report["votes"] = report["votes"].fillna(0).astype(int)
    report["weighted_score"] = report["weighted_score"].fillna(0.0).astype(float)

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(16, 10), sharex=True)

    # ---------------- Panel 1: temperature + markers ----------------
    ax1.plot(test_df.index, test_df["temp"],
             color="teal", alpha=0.4, label="Raw temperature")

    watch_pts = test_df[report["watch"]]
    alert_pts = test_df[report["alert"]]

    if not watch_pts.empty:
        ax1.scatter(watch_pts.index, watch_pts["temp"],
                    color="orange", s=20, zorder=3, label="Watch")
    if not alert_pts.empty:
        ax1.scatter(alert_pts.index, alert_pts["temp"],
                    color="red", s=50, marker="x", zorder=4, label="Alert")

    ax1.set_title(f"SkyGuard AI — {mode_name} mode")
    ax1.set_ylabel("Temperature (°C)")
    ax1.legend(loc="upper right")
    ax1.grid(alpha=0.3)

    # ---------------- Panel 2: votes + gate ----------------
    ax2.fill_between(report.index, 0, report["votes"],
                     color="purple", alpha=0.2, label="Vote count")
    ax2.axhline(y=mode_cfg["min_votes"], color="red", ls="--", alpha=0.5,
                label=f"min_votes = {mode_cfg['min_votes']}")

    # Y-axis bound from config rather than a hardcoded 4
    ax2.set_ylim(-0.1, config.MAX_LAYER_VOTES + 0.1)
    ax2.set_ylabel(f"Votes (0–{config.MAX_LAYER_VOTES})")
    ax2.set_title("Detection confidence (voting system)")
    ax2.legend(loc="upper right")
    ax2.grid(alpha=0.3)

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches="tight")
    plt.show()

    logging.info("Dashboard generated.")


def plot_dashboard_for_results(results, mode_name=None, save_path=None):
    """
    Thin wrapper: unpack a run_pipeline() results dict and plot.
    """
    return plot_dashboard(
        test_df=results["test_df_injected"],
        report=results["report"],
        config=results["config"],
        mode_name=mode_name or results["config"].DEFAULT_MODE,
        save_path=save_path,
    )