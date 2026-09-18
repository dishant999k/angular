class Config:

    PARAMETERS = ["temp", "pres", "rhum"]

    #for injecting anomalies
    INJECTION_SEED = 42
    # Count-based control.
    # Set to None to fall back to rate-based injection.
    INJECTION_N_SPIKES = None          # e.g. 60 → inject exactly 60 spikes
    INJECTION_N_FLATLINES = None       # e.g. 12 → inject exactly 12 flatline events
    # Rate-based control (fallback when counts are None).
    INJECTION_SPIKE_RATE = 0.02
    INJECTION_FLATLINE_RATE = 0.01
    # Spike shape
    INJECTION_SPIKE_MAGNITUDE = 15.0   # mean |Δ| in °C
    INJECTION_SPIKE_STD = 5.0          # std of |Δ|
    # Flatline shape
    INJECTION_FLATLINE_LENGTH = 10     # rows per flatline event
    INJECTION_FLATLINE_MIN_LENGTH = 3  # for variable-length testing later

    #For layer A
    # Flatline detection — thresholds derived from clean-data run-length distribution
    # A run is a flatline if it exceeds the p99.9 of natural clean runs, per parameter.
    # Hardcoded fallbacks if the derivation isn't available:
    FLATLINE_RUN_FALLBACK = {"temp": 3, "pres": 3, "rhum": 5}
    FLATLINE_MARGIN = 1
    LAYER_A_PERCENTILE = 99
    MIN_FLATLINE_RUN = 3    # run of identical values that counts as "stuck"
    LONG_FLATLINE_RUN = 5   # run this long is a flatline regardless of residual
    LAYER_A_K = 6 
    MIN_BIN_SAMPLES = 30 

    #For layer B
    LAYER_B_PERCENTILE = 99
    CHANGE_PERCENTILE = 99
    LAYER_B_MIN_TRAIN_ROWS = 100

    #For layer C
    WINDOW = 6
    RANDOM_SEED = 42
    LAYER_C_MIN_TRAIN_ROWS = 50
    CONTAMINATION = 0.012 # Set below true injection rate (~0.027) to bias Isolation Forest toward precision

    # Layer D — shared
    MIN_NEIGHBORS = 2
    MIN_SPATIAL_OVERLAP = 10          # raise to ~50 once you have enough test data
    Z_SCORE_THRESH = 4.0

    # Layer D — temperature
    TEMP_DIFF_THRESH = 4.5            # °C absolute deviation from neighbor median
    MIN_NEIGHBOR_MAD_TEMP = 0.5       # °C floor on neighbor MAD
    LAPSE_RATE = 0.0065               # °C/m

    # Layer D — pressure
    PRES_DIFF_THRESH = 5.0            # hPa absolute deviation after barometric correction
    MIN_NEIGHBOR_MAD_PRES = 0.3       # hPa floor on neighbor MAD
    PRESSURE_SCALE_HEIGHT = 8400.0    # m, standard tropospheric scale height

    #weights of each layer
    WEIGHT_A = 1.0
    WEIGHT_B = 2.0
    WEIGHT_C = 1.0
    WEIGHT_D = 1.5

    MAX_LAYER_VOTES = 4   # A (collapsed) + B + C + D

    #Four main operating modes with Balanced as default
    OPERATING_MODES = {
        "Maintenance": {
            "threshold": 2.5,
            "min_votes": 3,
            "description": "Routine audits — very strict",
        },
        "Balanced": {
            "threshold": 2.0,
            "min_votes": 2,
            "description": "Standard operations",
        },
        "Extreme Weather": {
            "threshold": 1.6,
            "min_votes": 2,
            "description": "Cyclone / heavy rain",
        },
        "Forensic": {
            "threshold": 1.2,
            "min_votes": 1,
            "description": "Post-event — catch everything",
        },
    }
    DEFAULT_MODE = "Balanced"

    # Site
    SITE_LAT = 26.9124
    SITE_LON = 75.7873
    STATION_ID = "AWS_1042"
    DATE_START = "2023-01-01"
    DATE_END = "2025-12-31"

    # Split
    TRAIN_FRAC = 0.70
    VAL_FRAC = 0.15

    # Neighbors (dlat, dlon) relative to primary
    NEIGHBOR_OFFSETS = {
        "north": (+0.15, +0.05),
        "south": (-0.15, -0.05),
        "east":  (+0.05, +0.15),
        "west":  (-0.05, -0.15),
    }

    RANDOM_SEED = 42


    # Rough per-parameter residual scales for cross-parameter attribution.
    # Chosen so that a "typical anomaly" normalizes to ~1.0 across parameters.
    PARAMETER_SCALES = {"temp": 5.0, "pres": 5.0, "rhum": 15.0}

    PARAMETER_DISPLAY = {
        "temp": "Temperature",
        "pres": "Atmospheric Pressure",
        "rhum": "Relative Humidity",
    }

    # Evidence → confidence ordinal. Monotone in evidence strength.
    CONFIDENCE_BY_EVIDENCE = {
        "override_only": 95,    # flatline override fired; unambiguous stuck sensor
        "votes_4plus":  98,     # four or more layers agree
        "votes_3":      94,
        "votes_2":      88,
        "single":       72,     # one layer only — weakest alert
    }

    SEVERITY_BY_CONFIDENCE = [
        (95, "CRITICAL"),
        (90, "HIGH"),
        (80, "MEDIUM"),
        (0,  "LOW"),
    ]