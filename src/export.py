import sqlite3
import pandas as pd
import os

csv_path = "data/processed/soilgrids_yaroslavl.csv"
db_path = "data/processed/soilgrids_yaroslavl.db"

df = pd.read_csv(csv_path)

required_columns = {"lat", "lon"}
if not required_columns.issubset(df.columns):
    raise ValueError(f"Файл должен содержать как минимум колонки: {required_columns}")

conn = sqlite3.connect(db_path)
df.to_sql("soil_data", conn, index=False)

with conn:
    conn.execute("CREATE INDEX idx_lat_lon ON soil_data (lat, lon)")

conn.close()
print(f"Успешно импортировано {len(df):,} строк в базу данных: {db_path}")
