import pandas as pd
import numpy as np
import os

# Пути к данным
input_csv = "data/processed/soilgrids_yaroslavl.csv"
bonitet_csv = "data/processed/bonitet_yar.csv"
suitability_csv = "data/processed/suitability_yar.csv"

# Каталоги
rayon_dir = "data/processed/rayon_coords"
output_dir_bonitet = "data/processed/bonitet_by_rayon"
output_dir_suitability = "data/processed/suitability_by_rayon"
os.makedirs(output_dir_bonitet, exist_ok=True)

# Проверка данных
try:
    df = pd.read_csv(input_csv)
    required_columns = ['lat','lon','bdod','cec','cfvo','clay','ocd','ph','sand','silt']
    if not all(col in df.columns for col in required_columns):
        missing = [col for col in required_columns if col not in df.columns]
        raise ValueError(f"Отсутствуют столбцы: {missing}")
except Exception as e:
    print(f"Ошибка загрузки данных: {e}")
    exit()

def calculate_bonitet(row):
    score = 0

    # 1. Органический углерод (макс 25)
    ocd = row["ocd"]
    if ocd > 6.5:
        score += 25
    elif 5.0 <= ocd <= 6.5:
        score += 20
    elif 3.5 <= ocd < 5.0:
        score += 15
    elif 2.5 <= ocd < 3.5:
        score += 10
    elif 1.5 <= ocd < 2.5:
        score += 5
    else:
        score += 2

    # 2. Кислотность (макс 18)
    ph = row["ph"]
    if 5.8 <= ph <= 6.2:
        score += 18
    elif 5.4 <= ph < 5.8 or 6.2 < ph <= 6.6:
        score += 14
    elif 5.0 <= ph < 5.4 or 6.6 < ph <= 7.0:
        score += 10
    elif 4.5 <= ph < 5.0 or 7.0 < ph <= 7.5:
        score += 6
    else:
        score += 2

    # 3. Гранулометрия (макс 18)
    clay, silt, sand = row["clay"], row["silt"], row["sand"]
    if (20 <= clay <= 28) and (35 <= silt <= 45) and (25 <= sand <= 35):
        score += 18
    elif (18 <= clay <= 30) and (30 <= silt <= 50) and (20 <= sand <= 40):
        score += 14
    elif (10 <= clay < 18 and sand < 60) or (30 < clay <= 40 and sand < 30):
        score += 10
    else:
        score += 6

    # 4. ЕКО (макс 15)
    cec = row["cec"]
    if cec > 30:
        score += 15
    elif 20 <= cec <= 30:
        score += 12
    elif 15 <= cec < 20:
        score += 9
    elif 10 <= cec < 15:
        score += 6
    elif 5 <= cec < 10:
        score += 3
    else:
        score += 1

    # 5. Плотность (макс 14)
    bdod = row["bdod"]
    if 1.1 <= bdod <= 1.25:
        score += 14
    elif 1.0 <= bdod < 1.1 or 1.25 < bdod <= 1.35:
        score += 10
    elif 0.9 <= bdod < 1.0 or 1.35 < bdod <= 1.45:
        score += 6
    else:
        score += 3

    # 6. Влагоемкость (макс 10)
    cfvo = row["cfvo"]
    if 17 <= cfvo <= 23:
        score += 10
    elif 14 <= cfvo < 17 or 23 < cfvo <= 26:
        score += 7
    elif 10 <= cfvo < 14 or 26 < cfvo <= 30:
        score += 5
    else:
        score += 2

    # Выбросы — -30%
    if (ocd > 15 or ph < 3.5 or ph > 8.5 or bdod < 0.5 or bdod > 1.8 or cfvo > 50):
        score = int(score * 0.7)

    return min(100, int(score))

df["bonitet"] = df.apply(calculate_bonitet, axis=1)
df["lat"] = df["lat"].round(3)
df["lon"] = df["lon"].round(3)

df[["lat", "lon", "bonitet"]].to_csv(bonitet_csv, index=False)

# Классификация культур по пригодности
crop_params = {
    'лён': {
        'ph': (5.8, 7.2),
        'ocd': (1.5, 4.0),
        'clay': (15, 35),
        'bonitet_min': 35,
        'cfvo': (15, 40)
    },
    'картофель': {
        'ph': (5.0, 6.5),
        'ocd': (2.0, 4.0),
        'clay': (10, 30),
        'bonitet_min': 40,
        'bdod': (1.2, 1.5)
    },
    'овёс': {
        'ph': (5.8, 7.2),
        'ocd': (2.0, 4.0),
        'clay': (15, 35),
        'bonitet_min': 30,
        'cec': (30, 55)
    },
    'рожь': {
        'ph': (5.8, 7.2),
        'ocd': (1.5, 3.5),
        'clay': (15, 35),
        'bonitet_min': 35,
        'sand': (30, 50)
    },
    'пшеница': {
        'ph': (6.0, 7.2),
        'ocd': (2.0, 4.0),
        'clay': (15, 35),
        'bonitet_min': 45,
        'cec': (50, 60)
    }
}

def classify_suitability(row, crop):
    req = crop_params[crop]
    score = 0
    max_score = 0

    def score_param(val, min_val, max_val, optimal=None, weight=1):
        if pd.isna(val):
            return 0, weight
        if min_val <= val <= max_val:
            if optimal is not None:
                range_span = max_val - min_val
                if range_span == 0:
                    return weight, weight  # избежать деления на 0
                distance = abs(val - optimal)
                closeness = 1 - (distance / (range_span / 2))
                return max(closeness, 0) * weight, weight
            return weight, weight
        return 0, weight

    params = []

    # Универсальный способ добавить параметры
    def add_param(name, weight=1):
        if name in req:
            values = req[name]
            min_val = values[0]
            max_val = values[1]
            optimal = values[2] if len(values) > 2 else None
            params.append((name, min_val, max_val, optimal, weight))

    add_param('ph', weight=2)
    add_param('ocd')
    add_param('clay')
    add_param('cfvo')
    add_param('bdod')
    add_param('cec')
    add_param('sand')
    add_param('silt')

    for param, min_val, max_val, optimal, weight in params:
        val = row.get(param)
        s, w = score_param(val, min_val, max_val, optimal, weight)
        score += s
        max_score += w

    # Оценка бонитета
    bonitet_score = 1 if row['bonitet'] >= req['bonitet_min'] else 0
    score += bonitet_score * 2
    max_score += 2

    ratio = score / max_score if max_score > 0 else 0

    if ratio >= 0.9:
        return "оптимальная"
    elif ratio >= 0.75:
        return "подходящая"
    elif ratio >= 0.5:
        return "ограниченно пригодная"
    return "непригодная"
# Добавление пригодности для культур
suitability_df = df[["lat", "lon", "bonitet"]].copy()
for crop in crop_params:
    suitability_df[crop] = df.apply(lambda row: classify_suitability(row, crop), axis=1)

suitability_df.to_csv(suitability_csv, index=False)

print(f"Средний бонитет: {df['bonitet'].mean():.1f}")
print("Данные сохранены:", bonitet_csv, suitability_csv)


print("\nНачинаем обработку по районам...")

bonitet_short = df[["lat", "lon", "bonitet"]].copy()
suitability_short = suitability_df.copy()

for filename in os.listdir(rayon_dir):
    if filename.endswith(".csv"):
        rayon_name = filename.replace(".csv", "")
        rayon_path = os.path.join(rayon_dir, filename)

        try:
            rayon_df = pd.read_csv(rayon_path)
            rayon_df["lat"] = rayon_df["lat"].round(3)
            rayon_df["lon"] = rayon_df["lon"].round(3)

            merged_bonitet = pd.merge(rayon_df, bonitet_short, on=["lat", "lon"], how="left")
            merged_suitability = pd.merge(rayon_df, suitability_short, on=["lat", "lon"], how="left")

            merged_bonitet.to_csv(os.path.join(output_dir_bonitet, f"{rayon_name}.csv"), index=False)
            merged_suitability.to_csv(os.path.join(output_dir_suitability, f"{rayon_name}.csv"), index=False)

            print(f"Обработан: {rayon_name}")

        except Exception as e:
            print(f"Ошибка в {filename}: {e}")