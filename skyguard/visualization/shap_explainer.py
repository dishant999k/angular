import logging

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import shap


def explain_isolation_forest(
    model,
    test_df,
    flag_c,
    window=6,
    max_flagged=120,
    normal_contrast_size=30,
    save_prefix="skyguard_shap"
):
    """
    Generate SHAP explanations for Isolation Forest alerts.

    The explanation focuses primarily on points flagged by Layer C,
    with a small normal contrast sample.
    """

    if model is None:
        logging.warning(
            "Isolation Forest model is unavailable. "
            "Skipping SHAP explanation."
        )
        return None

    logging.info(
        "🧠 Generating SHAP explanation for flagged alerts..."
    )

    # ---------------------------------------------------------
    # 1. Build the exact features used by Layer C
    # ---------------------------------------------------------

    features_for_shap = pd.DataFrame(
        index=test_df.index
    )

    for col in ["temp", "pres", "rhum"]:
        features_for_shap[f"{col}_raw"] = test_df[col]
        features_for_shap[f"{col}_std"] = (
            test_df[col]
            .rolling(window)
            .std()
        )

    features_for_shap = features_for_shap.dropna()

    if features_for_shap.empty:
        logging.warning(
            "No valid rows available for SHAP."
        )
        return None

    # ---------------------------------------------------------
    # 2. Separate flagged and normal samples
    # ---------------------------------------------------------

    flag_c_aligned = flag_c.reindex(
        features_for_shap.index,
        fill_value=False
    )

    flagged_idx = features_for_shap.index[
        flag_c_aligned
    ]

    normal_idx = features_for_shap.index.difference(
        flagged_idx
    )

    logging.info(
        f"Flagged points available: {len(flagged_idx)}"
    )

    logging.info(
        f"Normal points available: {len(normal_idx)}"
    )

    # Take flagged points, capped for memory safety
    flagged_sample = features_for_shap.loc[
        flagged_idx
    ].head(max_flagged)

    # Small normal contrast sample
    normal_size = min(
        normal_contrast_size,
        len(normal_idx)
    )

    if normal_size > 0:
        normal_sample = features_for_shap.loc[
            normal_idx
        ].sample(
            normal_size,
            random_state=42
        )
    else:
        normal_sample = features_for_shap.iloc[0:0]

    X_sample = pd.concat(
        [flagged_sample, normal_sample]
    )

    if X_sample.empty:
        logging.warning(
            "SHAP sample is empty."
        )
        return None

    logging.info(
        f"SHAP sample: {len(flagged_sample)} flagged + "
        f"{len(normal_sample)} normal = "
        f"{len(X_sample)} total"
    )

    # ---------------------------------------------------------
    # 3. Compute SHAP values
    # ---------------------------------------------------------

    explainer = shap.TreeExplainer(
        model,
        feature_perturbation="tree_path_dependent"
    )

    shap_values = explainer.shap_values(
        X_sample
    )

    # Some SHAP versions can return a list
    if isinstance(shap_values, list):
        shap_values = shap_values[0]

    # ---------------------------------------------------------
    # 4. Beeswarm plot
    # ---------------------------------------------------------

    plt.figure(figsize=(10, 6))

    shap.summary_plot(
        shap_values,
        X_sample,
        feature_names=X_sample.columns.tolist(),
        max_display=6,
        plot_size=(10, 6),
        show=False
    )

    plt.title(
        "SHAP: Why These Readings Were Flagged as Anomalies",
        fontsize=13,
        fontweight="bold"
    )

    plt.tight_layout()

    beeswarm_path = (
        f"graphs/{save_prefix}_beeswarm.png"
    )

    plt.savefig(
        beeswarm_path,
        dpi=150,
        bbox_inches="tight"
    )

    plt.show()

    # ---------------------------------------------------------
    # 5. SHAP bar plot
    # ---------------------------------------------------------

    plt.figure(figsize=(9, 5))

    shap.summary_plot(
        shap_values,
        X_sample,
        plot_type="bar",
        max_display=6,
        plot_size=(9, 5),
        show=False
    )

    plt.title(
        "SHAP: Average Feature Impact on Anomaly Score",
        fontsize=13,
        fontweight="bold"
    )

    plt.tight_layout()

    bar_path = f"graphs/{save_prefix}_bar.png"

    plt.savefig(
        bar_path,
        dpi=150,
        bbox_inches="tight"
    )

    plt.show()

    # ---------------------------------------------------------
    # 6. Feature impact ranking
    # ---------------------------------------------------------

    avg_shap = np.abs(shap_values).mean(axis=0)

    feature_impact = pd.DataFrame({
        "Feature": X_sample.columns,
        "Avg |SHAP| Impact": avg_shap
    }).sort_values(
        "Avg |SHAP| Impact",
        ascending=False
    )

    print("\n" + "=" * 50)
    print("📊 SHAP FEATURE IMPACT RANKING")
    print("=" * 50)

    print(
        feature_impact.to_string(index=False)
    )

    # ---------------------------------------------------------
    # 7. Volatility vs raw-value analysis
    # ---------------------------------------------------------

    std_features = [
        c for c in X_sample.columns
        if c.endswith("_std")
    ]

    raw_features = [
        c for c in X_sample.columns
        if c.endswith("_raw")
    ]

    std_indices = [
        X_sample.columns.get_loc(c)
        for c in std_features
    ]

    raw_indices = [
        X_sample.columns.get_loc(c)
        for c in raw_features
    ]

    std_impact = np.abs(
        shap_values[:, std_indices]
    ).mean()

    raw_impact = np.abs(
        shap_values[:, raw_indices]
    ).mean()

    print("\n" + "=" * 50)
    print("🔍 SHAP DIAGNOSTIC")
    print("=" * 50)

    print(
        f"Average impact from STD features "
        f"(volatility): {std_impact:.4f}"
    )

    print(
        f"Average impact from RAW features "
        f"(values): {raw_impact:.4f}"
    )

    if std_impact > raw_impact:
        verdict = "VOLATILITY-DRIVEN"

        print(
            "✅ VERDICT: Model is primarily "
            "VOLATILITY-DRIVEN"
        )

        print(
            "→ The model reacts strongly to "
            "variance changes."
        )

        print(
            "→ Layer A's dedicated flatline "
            "logic remains complementary."
        )

    else:
        verdict = "VALUE-DRIVEN"

        print(
            "✅ VERDICT: Model is primarily "
            "VALUE-DRIVEN"
        )

        print(
            "→ The model reacts more strongly "
            "to absolute values."
        )

    logging.info(
        f"SHAP plots saved: "
        f"{beeswarm_path}, {bar_path}"
    )

    return {
        "feature_impact": feature_impact,
        "std_impact": std_impact,
        "raw_impact": raw_impact,
        "verdict": verdict,
        "beeswarm_path": beeswarm_path,
        "bar_path": bar_path
    }