import os
import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
from tqdm import tqdm

shapefile_path = "data/raw/GADM.shp"
region_name = "Yaroslavl'"
output_csv = "data/raw/coords_yaroslavl.csv"
step = 0.001

gdf = gpd.read_file(shapefile_path)
region_gdf = gdf[gdf["NAME_1"] == region_name]

if region_gdf.empty:
    raise ValueError(f"Регион '{region_name}' не найден в GADM")

region_polygon = region_gdf.geometry.union_all()
minx, miny, maxx, maxy = region_polygon.bounds

print(f"Границы региона: lat {miny:.3f}–{maxy:.3f}, lon {minx:.3f}–{maxx:.3f}")

latitudes = np.arange(miny, maxy, step)
longitudes = np.arange(minx, maxx, step)

points = []
print("Генерация координат в пределах полигона...")
for lat in tqdm(latitudes):
    for lon in longitudes:
        point = Point(lon, lat)
        if region_polygon.contains(point):
            points.append((round(lat, 3), round(lon, 3)))

os.makedirs(os.path.dirname(output_csv), exist_ok=True)
df = pd.DataFrame(points, columns=["lat", "lon"])
df.to_csv(output_csv, index=False)

print(f"Сохранено координат: {len(df):,}")
print(f"Файл: {output_csv}")
