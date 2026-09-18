import logging
import requests
import pandas as pd
import numpy as np
def fetch_openmeteo(lat, lon, start_date, end_date, config):
    """Fetch hourly temp/pres/rhum for one grid point."""
    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude": lat, "longitude": lon,
        "start_date": start_date, "end_date": end_date,
        "hourly": ["temperature_2m", "surface_pressure", "relative_humidity_2m"],
    }
    try:
        r = requests.get(url, params=params, timeout=30)
        r.raise_for_status()
        data = r.json()
        if "hourly" not in data:
            return None
        df = pd.DataFrame(data["hourly"])
        df["time"] = pd.to_datetime(df["time"])
        df.set_index("time", inplace=True)
        df.rename(columns={
            "temperature_2m": "temp",
            "surface_pressure": "pres",
            "relative_humidity_2m": "rhum",
        }, inplace=True)
        return df[config.PARAMETERS].astype(float)
    except Exception as e:
        logging.error(f"Open-Meteo fetch failed for ({lat}, {lon}): {e}")
        return None


def fetch_elevation(lat, lon):
    """Return elevation in metres, or None on failure."""
    try:
        r = requests.get(
            f"https://api.open-meteo.com/v1/elevation?latitude={lat}&longitude={lon}",
            timeout=10,
        )
        r.raise_for_status()
        return float(r.json()["elevation"][0])
    except Exception as e:
        logging.warning(f"Elevation fetch failed for ({lat}, {lon}): {e}")
        return None


def clean_primary(df, config):
    """Fill missing pres/rhum synthetically if the fetch returned mostly NaN."""
    if df["pres"].isna().all():
        logging.warning("Pressure missing — synthesizing from temp.")
        df["pres"] = 1013 - (df["temp"] - 25) * 3 + np.random.normal(0, 1, len(df))
    if df["rhum"].isna().all():
        logging.warning("Humidity missing — synthesizing from temp.")
        df["rhum"] = 60 - (df["temp"] - 25) * 2 + np.random.normal(0, 5, len(df))
    return df[config.PARAMETERS].dropna().astype(float)


def fetch_neighbors(lat, lon, start_date, end_date, index, config):
    """
    Fetch temp + pressure + elevation for every configured neighbor.
    Returns (temp_df, pres_df, alts). alts is empty if any elevation is missing —
    a partial altitude set biases the lapse correction more than none.
    """
    temp_df = pd.DataFrame(index=index)
    pres_df = pd.DataFrame(index=index)
    alts = {}

    for name, (dlat, dlon) in config.NEIGHBOR_OFFSETS.items():
        nlat, nlon = lat + dlat, lon + dlon
        ndf = fetch_openmeteo(nlat, nlon, start_date, end_date, config)
        if ndf is None or ndf.empty:
            logging.warning(f"Neighbor '{name}' fetch failed.")
            continue

        temp_df[name] = ndf["temp"].reindex(index)
        pres_df[name] = ndf["pres"].reindex(index)

        alt = fetch_elevation(nlat, nlon)
        if alt is None:
            logging.warning(f"Neighbor '{name}' has no elevation — clearing all altitudes.")
            alts = {}
            break
        alts[name] = alt
        logging.info(f"Neighbor '{name}' fetched (alt={alt:.0f} m).")

    return temp_df, pres_df, alts