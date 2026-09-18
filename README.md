# SkyGuard AI

**Multi-Layer Anomaly Detection Pipeline for Weather Station Data**

SkyGuard AI is a modular anomaly detection system designed to identify abnormal weather-station readings using multiple complementary detection techniques.

Instead of relying on a single machine-learning model, SkyGuard combines **statistical, probabilistic, machine-learning, and spatial methods** into a weighted decision system. This makes the system more robust against different types of anomalies such as temperature spikes, sensor flatlines, unusual multivariate combinations, and spatial inconsistencies.

---

## Features

* 🌡️ Weather data collection using Open-Meteo

* 🔬 Multi-layer anomaly detection

* 📊 Statistical spike and flatline detection

* 📐 Mahalanobis-distance based multivariate detection

* 🤖 Isolation Forest based machine-learning detection

* 🌍 Spatial consistency checking using neighboring stations

* 🗳️ Weighted voting and alert generation

🚨 Alert Intelligence Report

* 🧪 Synthetic anomaly injection for controlled evaluation

* 📈 Precision, recall, F1-score and confusion matrix

* 🔍 Anomaly-type detection analysis

* 📉 Precision-Recall curve

* 🧠 SHAP-based model explainability

* 📊 Final anomaly monitoring dashboard

* 🧩 Modular Python package architecture

---

# System Architecture

SkyGuard follows a multi-stage pipeline:

```text

             ┌─────────────────────┐

             │   Open-Meteo API     │

             └──────────┬──────────┘

                        │

                        ▼

             ┌─────────────────────┐

             │   Weather Dataset   │

             └──────────┬──────────┘

                        │

                        ▼

             ┌─────────────────────┐

             │ Train / Val / Test  │

             │       Split         │

             └──────────┬──────────┘

                        │

                        ▼

             ┌─────────────────────┐

             │ Anomaly Injection   │

             │    (Test Only)      │

             └──────────┬──────────┘

                        │

          ┌─────────────┼─────────────┐

          ▼             ▼             ▼

    ┌──────────┐  ┌──────────┐  ┌──────────┐

    │ Layer A  │  │ Layer B  │  │ Layer C  │

    │Statistical│ │Mahalanobis│ │Isolation │

    │ Detection │ │ Distance │ │  Forest  │

    └─────┬────┘  └─────┬────┘  └─────┬────┘

          │             │             │

          └─────────────┼─────────────┘

                        │

                        ▼

                ┌──────────────┐

                │   Layer D    │

                │    Spatial   │

                │ Consistency  │

                └──────┬───────┘

                       │

                       ▼

             ┌─────────────────────┐

             │ Weighted Combination│

             │     & Voting        │

             └──────────┬──────────┘

                        │

                        ▼

             ┌─────────────────────┐

             │ Watch / Alert /     │

             │ Final Prediction    │

             └──────────┬──────────┘

                        │

         ┌──────────────┼──────────────┐

         ▼              ▼              ▼

    Evaluation      Explainability  Dashboard

    & Metrics          (SHAP)       Visualization

```

---

# Detection Layers

## Layer A — Statistical Detection

Layer A detects anomalies using statistical behavior of individual weather variables.

It primarily identifies:

* Sudden temperature spikes

* Unusual pressure/humidity changes

* Sensor flatlines

The layer also uses historical training data to establish normal behavior and flatline thresholds.

### Main idea

A reading is considered suspicious when it significantly deviates from the expected local behavior of the signal.

---

## Layer B — Mahalanobis Distance

Layer B detects unusual **multivariate combinations** of weather variables.

Instead of examining temperature, pressure, and humidity independently, it considers their relationship.

Mahalanobis distance is used to measure how far an observation is from the normal multivariate distribution.

The model is fitted using clean training data.

A percentile-based threshold is then calculated from the training distances.

This layer is particularly useful when individual values may look normal but their combination is unusual.

---

## Layer C — Isolation Forest

Layer C uses an **Isolation Forest** to detect observations that are difficult to classify as part of the normal data distribution.

The model uses weather features together with rolling statistical features.

The feature set includes:

* Temperature

* Pressure

* Relative humidity

* Rolling temperature standard deviation

* Rolling pressure standard deviation

* Rolling humidity standard deviation

The trained model is fitted only on clean training data.

SHAP is later used to explain the Isolation Forest predictions.

---

## Layer D — Spatial Detection

Layer D compares the primary weather station against nearby stations.

The system:

1. Retrieves data from neighboring locations.

2. Applies altitude correction.

3. Calculates a robust neighborhood reference.

4. Compares the primary station against neighboring observations.

5. Flags readings that differ significantly from the surrounding stations.

This helps identify anomalies that may not be obvious from the primary station's own historical data.

---

# Final Decision System

The outputs of the detection layers are combined using a weighted voting mechanism.

The system calculates a weighted score from:

* Layer B — Mahalanobis

* Layer C — Isolation Forest

* Layer D — Spatial detection

Layer A flatline detection can trigger an immediate override.

The final result classifies observations into states such as:

```text

Normal

│

├── Watch

│

└── Alert

```

The voting system allows SkyGuard to avoid depending entirely on one detection method.

---

# Data Flow

The pipeline follows this general sequence:

```text

Fetch Weather Data

    ↓

Prepare Dataset

    ↓

Train / Validation / Test Split

    ↓

Inject Synthetic Anomalies

    ↓

Fit Detection Models on Clean Training Data

    ↓

Run Layer A

    ↓

Run Layer B

    ↓

Run Layer C

    ↓

Run Layer D

    ↓

Combine Detection Results

    ↓

Generate Final Predictions

    ↓

Evaluate Performance

    ↓

Generate Visualizations

    ↓

Generate SHAP Explanations

```

Synthetic anomalies are injected **only into the test dataset**, keeping the training data clean for model fitting and preventing artificial anomalies from contaminating the learned normal behavior.

---

# Project Structure

```text

skyguard-ai/

│

├── README.md

├── requirements.txt

├── .gitignore

│

├── data/

│   ├── raw/

│   └── processed/

│

├── tests/

│

└── src/

└── skyguard/

    │

    ├── \_\_init\_\_.py

    ├── config.py

    ├── pipeline.py

    │

    ├── data/

    │   ├── \_\_init\_\_.py

    │   └── weather\_fetcher.py

    │

    ├── detection/

    │   ├── \_\_init\_\_.py

    │   ├── statistical.py

    │   ├── mahalanobis.py

    │   ├── isolation\_forest.py

    │   └── spatial.py

    │

    ├── preprocessing/

    │   ├── \_\_init\_\_.py

    │   └── anomaly\_injection.py

    │

    ├── evaluation/

    │   ├── \_\_init\_\_.py

    │   └── metrics.py

    │

    └── visualization/

        ├── \_\_init\_\_.py

        ├── dashboard.py

        └── shap\_explainer.py

```

### Module Responsibilities

| Module                               | Responsibility                                 |

| ------------------------------------ | ---------------------------------------------- |

| `config.py`                          | Central configuration and detection thresholds |

| `pipeline.py`                        | Main pipeline orchestration                    |

| `data/weather_fetcher.py`            | Weather and elevation data retrieval           |

| `detection/statistical.py`           | Layer A statistical detection                  |

| `detection/mahalanobis.py`           | Layer B Mahalanobis detection                  |

| `detection/isolation_forest.py`      | Layer C Isolation Forest                       |

| `detection/spatial.py`               | Layer D spatial detection                      |

| `preprocessing/anomaly_injection.py` | Synthetic anomaly generation                   |

| `evaluation/metrics.py`              | Performance metrics and evaluation plots       |

| `visualization/dashboard.py`         | Final monitoring dashboard                     |

| `visualization/shap_explainer.py`    | SHAP-based model explanations                  |

---

# Installation

## 1. Clone the repository

```bash

git clone <repository-url>

cd skyguard-ai

```

## 2. Create a virtual environment

### Linux / macOS

```bash

python3 -m venv .venv

source .venv/bin/activate

```

### Windows

```powershell

python -m venv .venv

.venv\Scripts\activate

```

## 3. Install dependencies

```bash

pip install -r requirements.txt

```

---

# Running the Pipeline

SkyGuard uses a `src` package layout.

From the project root:

### Linux / macOS

```bash

PYTHONPATH=src python src/skyguard/pipeline.py

```

### Windows PowerShell

```powershell

$env:PYTHONPATH="src"

python src/skyguard/pipeline.py

```

### Windows CMD

```cmd

set PYTHONPATH=src

python src/skyguard/pipeline.py

```

The pipeline entry point is:

```python

if __name__ == "__main__":

run\_pipeline()

```

---

# Data Source

SkyGuard currently uses the **Open-Meteo Archive API** to retrieve historical weather observations.

The pipeline retrieves:

* Temperature

* Surface pressure

* Relative humidity

The primary station and surrounding neighboring locations are used for the detection process.

---

# Configuration

Detection parameters are centralized in:

```text

src/skyguard/config.py

```

Important parameters include:

```text

WINDOW

TRAIN_SPLIT

CONTAMINATION

FLATLINE_MULTIPLIER

MIN_TEMP_STD

MIN_PRES_STD

MIN_RHUM_STD

LAPSE_RATE

TEMP_DIFF_THRESH

MIN_VOTES

WEIGHT_B

WEIGHT_C

WEIGHT_D

VOTING_THRESHOLD

```

Keeping these values in one configuration module makes it easier to tune the system without modifying the detection algorithms themselves.

---

# Evaluation

SkyGuard evaluates its predictions against the synthetic ground truth generated during anomaly injection.

The evaluation module provides:

* Accuracy

* Precision

* Recall

* F1-score

* True positives

* True negatives

* False positives

* False negatives

* Detection rate

* Confusion matrix

* Anomaly-type detection analysis

* Precision-Recall curve

Example output:

```text

==================================================

📊 SKYGUARD PERFORMANCE METRICS

==================================================

Classification Report:

          precision    recall  f1-score

Normal          ...

Anomaly         ...

--------------------------------------------------

Total Injected Anomalies : ...

Total System Alerts      : ...

True Positives           : ...

False Positives          : ...

False Negatives          : ...

Detection Rate           : ...

Precision                : ...

Recall                   : ...

F1-Score                 : ...

Accuracy                 : ...

```

---

# Explainability

SkyGuard uses **SHAP (SHapley Additive exPlanations)** to provide insight into the Isolation Forest model.

The SHAP module produces:

```text

skyguard_shap_beeswarm.png

skyguard_shap_bar.png

```

These visualizations help determine which features contributed most strongly to the model's anomaly decisions.

The system also compares the contribution of:

* Raw weather measurements

* Rolling volatility features

This provides additional insight into whether anomalies are primarily driven by unusual values or unusual changes in behavior.

---

# Visualizations

The pipeline generates several visual outputs.

### Confusion Matrix

```text

confusion_matrix.png

```

Shows:

* True positives

* True negatives

* False positives

* False negatives

### Precision-Recall Curve

```text

skyguard_pr_curve.png

```

Shows the trade-off between precision and recall for different voting-confidence thresholds.

### SHAP Visualizations

```text

skyguard_shap_beeswarm.png

skyguard_shap_bar.png

```

Explain the contribution of Isolation Forest features.

### Dashboard

```text

skyguard_dashboard.png

```

Provides a combined view of:

* Temperature

* Watch/alert points

* Voting confidence

* Detection threshold

---

# Pipeline Output

`run_pipeline()` returns the major intermediate and final results as a dictionary.

Example:

```python

results = run_pipeline()

```

Available outputs include:

```python

results["train_df"]

results["val_df"]

results["test_df"]

results["ground_truth"]

results["anomaly_type"]

results["layer_a_spikes"]

results["layer_a_flatlines"]

results["layer_b"]

results["layer_c"]

results["layer_d"]

results["spatial_fraction"]

results["final_prediction"]

results["report"]

results["isolation_forest"]

```

This makes the pipeline reusable by other modules without requiring them to rerun the detection process.

---

# Design Philosophy

SkyGuard is intentionally designed as a **modular multi-layer detection system**.

Each detection method has a different strength:

```text

Statistical

↓

Detects unusual individual behavior

Mahalanobis

↓

Detects unusual multivariate relationships

Isolation Forest

↓

Detects complex distributional anomalies

Spatial

↓

Detects disagreement with neighboring stations

```

Combining these methods provides multiple independent signals before generating a final alert.

The architecture also separates:

```text

Data

↓

Preprocessing

↓

Detection

↓

Evaluation

↓

Visualization

```

This keeps individual components easier to understand, test, modify, and extend.

---

# Technologies Used

* **Python**

* **Pandas** — data manipulation

* **NumPy** — numerical computation

* **Scikit-learn** — Isolation Forest and evaluation metrics

* **SciPy** — Mahalanobis distance and statistical operations

* **SHAP** — model explainability

* **Matplotlib** — visualization

* **Seaborn** — statistical visualization

* **Requests** — API communication

* **Open-Meteo** — weather data source

---

# License

This project is currently intended for educational, research, and experimental purposes.

Add an appropriate open-source license before public distribution.