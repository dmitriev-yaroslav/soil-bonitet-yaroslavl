import pandas as pd
import numpy as np
from sklearn.neighbors import KDTree

coords_file = "data/raw/coords_yaroslavl.csv"
soil_file = "data/raw/soilgrids_processed.csv"
output_file = "data/processed/soilgrids_yaroslavl.csv"

coords_df = pd.read_csv(coords_file)
coords_array = coords_df[["lat", "lon"]].to_numpy()
soil_df = pd.read_csv(soil_file)

# Строим KD-дерево по координатам основного набора
soil_coords = soil_df[["lat", "lon"]].to_numpy()
tree = KDTree(soil_coords)

# Ищем ближайшие точки из soil_df для каждой точки из координат Ярославской области
distances, indices = tree.query(coords_array, k=1)

# Извлекаем уникальные найденные строки
filtered_data = soil_df.iloc[np.unique(indices.flatten())].copy()

# Заменяем нули на NaN для дальнейшего заполнения
columns_to_check = ["bdod", "cec", "cfvo", "clay", "ocd", "ph", "sand", "silt"]
filtered_data[columns_to_check] = filtered_data[columns_to_check].replace(0, np.nan)

# Интерполяция и заполнение пропусков (современная форма)
filtered_data[columns_to_check] = (
    filtered_data[columns_to_check]
    .interpolate(method="nearest", axis=0)
    .bfill()
    .ffill()
)

filtered_data.to_csv(output_file, index=False, float_format="%.3f")
print(f"Данные по Ярославской области сохранены в: {output_file}")
