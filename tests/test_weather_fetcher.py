from skyguard.data.weather_fetcher import (
    fetch_openmeteo,
    fetch_neighbor_data,
    fetch_elevation
)

LAT, LON = 26.9124, 75.7873

start_date = "2023-01-01"
end_date = "2023-01-03"


print("Testing primary weather fetch...")

df = fetch_openmeteo(
    LAT,
    LON,
    start_date,
    end_date
)

print(df.head())
print("\nShape:", df.shape)
print("Columns:", df.columns.tolist())


print("\nTesting neighbor fetch...")

neighbor_df, neighbor_alts = fetch_neighbor_data(
    LAT,
    LON,
    start_date,
    end_date,
    df.index
)

print(neighbor_df.head())
print("\nNeighbor shape:", neighbor_df.shape)
print("Neighbors:", neighbor_df.columns.tolist())
print("Altitudes:", neighbor_alts)


print("\nTesting elevation fetch...")

primary_alt = fetch_elevation(LAT, LON)

print("Primary elevation:", primary_alt)

print("\nAll weather fetcher tests completed!")