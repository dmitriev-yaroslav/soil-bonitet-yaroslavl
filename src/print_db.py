import sqlite3
import pandas as pd

db_path = "data/processed/soilgrids_yaroslavl.db"
conn = sqlite3.connect(db_path)
query = "SELECT * FROM soil_data ORDER BY lat, lon"
df = pd.read_sql_query(query, conn)

print(df.tail(20))
print(f"\nВсего строк: {len(df):,}, колонок: {len(df.columns)}")
print("Названия колонок:", df.columns.tolist())

conn.close()
