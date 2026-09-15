import geopandas as gpd

shapefile_path = "data/raw/GADM_1.shp"
gdf = gpd.read_file(shapefile_path)

print("Доступные столбцы в shapefile:")
print(gdf.columns)

print("\n Первые строки данных:")
print(gdf.head())

print("\n Уникальные значения в столбце 'NAME_1':")
print(gdf["NAME_1"].unique())
