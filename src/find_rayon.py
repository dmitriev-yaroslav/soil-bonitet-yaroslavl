import geopandas as gpd

# Путь к файлу
shapefile_path = "data/raw/GADM_3.shp"

# Чтение shapefile
gdf = gpd.read_file(shapefile_path)

# Фильтрация по Ярославской области
yaroslavl_gdf = gdf[gdf["NAME_1"] == "Yaroslavl'"]

# Проверка наличия данных
if yaroslavl_gdf.empty:
    print("Не найдено данных по Ярославской области.")
else:
    # Вывод уникальных районов
    print("Районы Ярославской области:")
    print(yaroslavl_gdf["NAME_2"].unique())
