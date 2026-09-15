import os
import rasterio
import numpy as np
import pandas as pd
from glob import glob
import re

data_dir = "soilgrids_data"
file_pattern = os.path.join(data_dir, "out (*.tif")

tif_files = glob(os.path.join(data_dir, "out (*).tif"))

tif_files = sorted(tif_files, key=lambda x: int(re.search(r'out \((\d+)\)', x).group(1)))

# Слои (по 8 файлов на каждый из 4-х тайлов)
layer_names = [
    "ocd",   # Organic carbon density
    "bdod",  # Bulk density
    "clay",  # Clay
    "cfvo",  # Coarse fragments
    "sand",  # Sand
    "silt",  # Silt
    "cec",   # Cation exchange capacity
    "ph"     # pH in water
]

# Преобразование единиц
transformations = {
    "ocd": lambda x: x / 100,     # г/кг - %
    "bdod": lambda x: x / 100,   # cg/cm³ → g/cm³
    "clay": lambda x: x / 10,    # %
    "cfvo": lambda x: x / 10,    # %
    "sand": lambda x: x / 10,    # %
    "silt": lambda x: x / 10,    # %
    "cec": lambda x: x / 100,     # ммоль/кг - смоль/кг
    "ph": lambda x: x / 10       # ×10 → pH
}

expected_files = 48
if len(tif_files) != expected_files:
    raise ValueError(f"Ожидалось {expected_files} файла, найдено {len(tif_files)}")

num_blocks = 6
files_per_block = len(layer_names)
all_dataframes = []

for block_index in range(num_blocks):
    block_files = tif_files[block_index * files_per_block : (block_index + 1) * files_per_block]

    with rasterio.open(block_files[0]) as src:
        transform = src.transform
        width, height = src.width, src.height
        rows, cols = np.meshgrid(np.arange(height), np.arange(width), indexing="ij")
        xs, ys = rasterio.transform.xy(transform, rows, cols)
        lon_arr = np.array(xs)
        lat_arr = np.array(ys)

    df_block = pd.DataFrame({
        "lat": lat_arr.flatten(),
        "lon": lon_arr.flatten()
    })

    for file, name in zip(block_files, layer_names):
        with rasterio.open(file) as src:
            data = src.read(1).astype(np.float32)
            data[data == src.nodata] = np.nan
            df_block[name] = transformations[name](data.flatten())

    df_block.dropna(subset=layer_names, how="all", inplace=True)
    all_dataframes.append(df_block)

df_total = pd.concat(all_dataframes, ignore_index=True)

df_total.to_csv("data/raw/soilgrids_processed.csv", index=False, float_format="%.3f")
print("Объединённый CSV сохранён: soilgrids_processed.csv")
