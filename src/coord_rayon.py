import os
import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
from tqdm import tqdm

# Параметры
shapefile_path = "data/raw/GADM_3.shp"
region_name = "Yaroslavl'"
output_dir = "data/processed/rayon_coords"
step = 0.001

# Загрузка данных
gdf = gpd.read_file(shapefile_path)

# Фильтрация по региону
region_gdf = gdf[gdf["NAME_1"] == region_name]

if region_gdf.empty:
    raise ValueError(f"Регион '{region_name}' не найден в GADM")

# Создание выходной директории
os.makedirs(output_dir, exist_ok=True)

# Перебор всех районов в регионе
districts = region_gdf["NAME_2"].unique()

print(f"Найдено районов: {len(districts)}")

for district in tqdm(districts):
    # Фильтрация по району
    district_gdf = region_gdf[region_gdf["NAME_2"] == district]
    
    if district_gdf.empty:
        continue

    # Объединение геометрий района
    district_polygon = district_gdf.geometry.union_all()
    minx, miny, maxx, maxy = district_polygon.bounds

    # Генерация координат в пределах границ
    latitudes = np.arange(miny, maxy, step)
    longitudes = np.arange(minx, maxx, step)

    points = []
    for lat in latitudes:
        for lon in longitudes:
            point = Point(lon, lat)
            if district_polygon.contains(point):
                points.append((round(lat, 3), round(lon, 3)))

    # Сохранение координат в CSV
    if points:
        df = pd.DataFrame(points, columns=["lat", "lon"])
        district_name_clean = district.replace("'", "").replace(" ", "_")
        output_csv = os.path.join(output_dir, f"{district_name_clean}.csv")
        df.to_csv(output_csv, index=False)

print("Генерация завершена.")
