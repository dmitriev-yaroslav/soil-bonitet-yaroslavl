import os
import pandas as pd
import pydeck as pdk
import streamlit as st
import plotly.express as px
import io 
import plotly.io as pio

page_title = "Анализ бонитета почв Ярославской области"
page_icon = "🌾"
layout = "wide"
max_points = 100000
bonitet_file = "data/processed/bonitet_yar.csv"
suitability_file = "data/processed/suitability_yar.csv"

if not os.path.exists(bonitet_file):
    bonitet_file = "data/sample/bonitet_yar_sample.csv"
if not os.path.exists(suitability_file):
    suitability_file = "data/sample/suitability_yar_sample.csv"

bonitet_classes = [
    {"range": (0, 20), "label": "Очень низкий", "color": [178, 24, 43]},
    {"range": (20, 30), "label": "Низкий", "color": [214, 96, 77]},
    {"range": (30, 40), "label": "Ниже среднего", "color": [244, 165, 130]},
    {"range": (40, 50), "label": "Средний", "color": [253, 219, 199]},
    {"range": (50, 60), "label": "Выше среднего", "color": [209, 229, 240]},
    {"range": (60, 70), "label": "Высокий", "color": [146, 197, 222]},
    {"range": (70, 100), "label": "Очень высокий", "color": [67, 147, 195]},
]

suitability_colors = {
    "оптимальная": [0, 153, 51],
    "подходящая": [255, 204, 51],
    "ограниченно пригодная": [255, 102, 0],
    "непригодная": [204, 0, 0]
}

district_translation = {
    "Bolsheselskiy_rayon": "Большесельский район",
    "Borisoglebskiy_rayon": "Борисоглебский район",
    "Breytovskiy_rayon": "Брейтовский район",
    "Danilovskiy_rayon": "Даниловский район",
    "Gavrilov-Yamskiy_rayon": "Гаврилов-Ямский район",
    "Lyubimskiy_rayon": "Любимский район",
    "Myshkinskiy_rayon": "Мышкинский район",
    "Nekouzskiy_rayon": "Некоузский район",
    "Nekrasovskiy_rayon": "Некрасовский район",
    "Pereslavskiy_rayon": "Переславский район",
    "Pervomayskiy_rayon": "Первомайский район",
    "Poshekhonskiy_rayon": "Пошехонский район",
    "Rostov": "Ростов",
    "Rostovskiy_rayon": "Ростовский район",
    "Rybinsk": "Рыбинск",
    "Rybinskiy_rayon": "Рыбинский район",
    "Tutaev": "Тутаев",
    "Tutaevskiy_rayon": "Тутаевский район",
    "Uglich": "Углич",
    "Uglichskiy_rayon": "Угличский район",
    "Water_body": "Водные объекты",
    "Yaroslavl": "Ярославль",
    "Yaroslavskiy_rayon": "Ярославский район"
}

@st.cache_data
def load_data():
    try:
        bonitet_df = pd.read_csv(bonitet_file, encoding='utf-8')
        required_cols = ['lat', 'lon', 'bonitet']
        if not all(col in bonitet_df.columns for col in required_cols):
            st.error(f"Отсутствуют необходимые столбцы: {required_cols}")
            st.stop()

        if os.path.exists(suitability_file):
            suitability_df = pd.read_csv(suitability_file, encoding='utf-8')
            if 'bonitet' in suitability_df.columns:
                suitability_df.drop(columns=['bonitet'], inplace=True)
            df = bonitet_df.merge(suitability_df, on=['lat', 'lon'], how='left')
            culture_cols = [col for col in suitability_df.columns if col not in ['lat', 'lon']]
            return df, culture_cols

        return bonitet_df, None
    except Exception as e:
        st.error(f"Ошибка при загрузке данных: {str(e)}")
        st.stop()

def load_rayon_data(rayon_name, display_mode, selected_culture=None):
    base_dir = "data/processed"
    subfolder = "bonitet_by_rayon" if display_mode == "Бонитет почв" else "suitability_by_rayon"
    file_path = os.path.join(base_dir, subfolder, f"{rayon_name}.csv")

    if not os.path.exists(file_path):
        return None

    try:
        df = pd.read_csv(file_path)
        if display_mode == "Бонитет почв":
            df['bonitet_class'] = df['bonitet'].apply(lambda x: get_bonitet_class(x)['label'])
            df['color'] = df['bonitet'].apply(lambda x: get_bonitet_class(x)['color'])
        else:
            df['color'] = df[selected_culture].map(suitability_colors)
        return df
    except Exception as e:
        st.warning(f"Не удалось загрузить {rayon_name}: {e}")
        return None

def get_bonitet_class(value):
    for cls in bonitet_classes:
        if cls["range"][0] <= value < cls["range"][1]:
            return cls
    return bonitet_classes[-1]

def sidebar_controls(df, culture_columns):
    st.sidebar.header("Параметры отображения")

    rayon_dir = "data/processed/bonitet_by_rayon"
    if os.path.exists(rayon_dir):
        rayon_files = sorted([
            f.replace(".csv", "") for f in os.listdir(rayon_dir) 
            if f.endswith(".csv")
        ])
    else:
        rayon_files = []

    display_names = ["Все районы"] + [
        district_translation.get(name, name) for name in rayon_files
    ]

    rayon_display_to_file = {"Все районы": "Все районы"}
    for eng_name in rayon_files:
        rayon_display_to_file[district_translation.get(eng_name, eng_name)] = eng_name

    selected_display_name = st.sidebar.selectbox("Выберите район:", display_names)
    selected_rayon = rayon_display_to_file[selected_display_name]

    display_options = ["Бонитет почв"]
    if culture_columns:
        display_options.append("Пригодность для культур")
    
    display_mode = st.sidebar.radio("Режим отображения:", display_options)

    if not culture_columns and display_mode != "Бонитет почв":
        st.sidebar.warning("Файл с культурами не найден. Отображается только бонитет.")
        display_mode = "Бонитет почв"

    min_b, max_b = int(df['bonitet'].min()), int(df['bonitet'].max())
    bonitet_range = st.sidebar.slider("Диапазон бонитета:", min_b, max_b, (min_b, max_b))

    selected_culture = None
    selected_suitability = "Все"

    if display_mode == "Пригодность для культур" and culture_columns:
        selected_culture = st.sidebar.selectbox("Выберите культуру:", sorted(culture_columns))
        if selected_culture in df.columns:
            values = df[selected_culture].dropna().unique().tolist()
            selected_suitability = st.sidebar.selectbox("Уровень пригодности:", ["Все"] + sorted(values))
        else:
            st.sidebar.warning(f"Данные по культуре '{selected_culture}' отсутствуют")
            selected_suitability = "Все"

    st.sidebar.markdown("### Визуализация")
    map_theme = st.sidebar.radio("Тема карты", ["Светлая", "Тёмная"], index=0)
    map_interface = st.sidebar.radio("Тема интерфейса", ["Светлая", "Тёмная"], index=0)

    return selected_rayon, display_mode, bonitet_range, selected_culture, selected_suitability, map_theme, map_interface

def filter_data(df, display_mode, bonitet_range, selected_culture, selected_suitability):
    df = df[(df['bonitet'] >= bonitet_range[0]) & (df['bonitet'] <= bonitet_range[1])].copy()

    if display_mode == "Пригодность для культур" and selected_culture and selected_suitability != "Все":
        df = df[df[selected_culture] == selected_suitability]

    if display_mode == "Бонитет почв":
        df['bonitet_class'] = df['bonitet'].apply(lambda x: get_bonitet_class(x)['label'])
        df['color'] = df['bonitet'].apply(lambda x: get_bonitet_class(x)['color'])
    else:
        df['color'] = df[selected_culture].map(suitability_colors)

    return df

def get_tooltip(display_mode, selected_culture):
    if display_mode == "Бонитет почв":
        return {
            "html": "<b>Координаты:</b> [{lat}, {lon}]<br><b>Бонитет:</b> {bonitet}<br><b>Класс:</b> {bonitet_class}",
            "style": {"backgroundColor": "white", "color": "black"}
        }
    else:
        return {
            "html": f"<b>Координаты:</b> [{{lat}}, {{lon}}]<br><b>Бонитет:</b> {{bonitet}}<br><b>{selected_culture}:</b> {{{selected_culture}}}",
            "style": {"backgroundColor": "white", "color": "black"}
        }

def render_map(df, tooltip, map_theme, full_view=False):
    if full_view and len(df) > max_points:
        st.warning(f"🔍 Обнаружено {len(df):,} точек — отображаются только {max_points:,} случайных точек.")
        df = df.sample(max_points, random_state=42)

    view_state = pdk.ViewState(
        latitude=df["lat"].mean(),
        longitude=df["lon"].mean(),
        zoom=10 if not full_view else 8,
        pitch=0
    )

    point_radius = 300 if full_view else 100

    layer = pdk.Layer(
        "ScatterplotLayer",
        df,
        get_position='[lon, lat]',
        get_fill_color='color',
        get_radius=point_radius,
        pickable=True,
        opacity=1.0,
    )
    map_style = "light" if map_theme == "Светлая" else "dark"

    st.pydeck_chart(pdk.Deck(
        layers=[layer],
        initial_view_state=view_state,
        tooltip=tooltip,
        map_style=map_style
    ))

def render_background(map_interface):
    if map_interface == "Тёмная":
        st.markdown("""
            <style>
                html, body, .stApp {
                    background-color: #1e1e1e !important;
                    color: #f0f0f0 !important;
                }

                /* Сайдбар */
                section[data-testid="stSidebar"] {
                    background-color: #2c2c2c !important;
                    color: #f0f0f0 !important;
                }

                /* Текст */
                div[data-testid="stMarkdownContainer"],
                div[class^="css-"] {
                    color: #f0f0f0 !important;
                }

                /* Кнопки */
                .stButton > button {
                    background-color: #444 !important;
                    color: #f0f0f0 !important;
                    border: 1px solid #777 !important;
                }

                /* Поля ввода */
                input, textarea, select {
                    background-color: #333 !important;
                    color: #f0f0f0 !important;
                    border: 1px solid #555 !important;
                }
            </style>
        """, unsafe_allow_html=True)
        return "plotly_dark"
    else:
        st.markdown("""
            <style>
                html, body, .stApp {
                    background-color: white !important;
                    color: black !important;
                }

                .stPlotlyChart {
                    background-color: #2c2c2c !important;
                    padding: 10px;
                    border-radius: 8px;
                }
                
                section[data-testid="stSidebar"] {
                    background-color: #f8f9fa !important;
                    color: black !important;
                }

                div[data-testid="stMarkdownContainer"],
                div[class^="css-"] {
                    color: black !important;
                }

                .stButton > button {
                    background-color: #f0f0f0 !important;
                    color: black !important;
                    border: 1px solid #ccc !important;
                }

                input, textarea, select {
                    background-color: white !important;
                    color: black !important;
                    border: 1px solid #ccc !important;
                }
            </style>
        """, unsafe_allow_html=True)
        return "plotly_white"


def render_legend(display_mode, selected_culture=None):
    st.subheader("🗺️ Легенда")
    if display_mode == "Бонитет почв":
        for cls in bonitet_classes:
            color = f"rgb({', '.join(map(str, cls['color']))})"
            st.markdown(
                f"<div style='display: flex; align-items: center; margin-bottom: 4px;'>"
                f"<div style='width: 20px; height: 20px; background-color: {color}; margin-right: 8px;'></div>"
                f"{cls['label']} ({cls['range'][0]}–{cls['range'][1]})</div>",
                unsafe_allow_html=True
            )
    else:
        for name, color in suitability_colors.items():
            color_hex = '#%02x%02x%02x' % tuple(color)
            st.markdown(
                f"<div style='display: flex; align-items: center; margin-bottom: 4px;'>"
                f"<div style='width: 20px; height: 20px; background-color: {color_hex}; margin-right: 8px;'></div>"
                f"{name.capitalize()}</div>",
                unsafe_allow_html=True
            )

def render_charts(df, display_mode, selected_culture, plotly_template):
    st.subheader("📈 Графики по выбранной области")

    st.markdown("**Распределение бонитета:**")
    df["bonitet_class"] = df["bonitet"].apply(lambda x: get_bonitet_class(x)['label'])

    bonitet_order = [cls['label'] for cls in bonitet_classes]
    bonitet_colors = {cls['label']: f"rgb({cls['color'][0]}, {cls['color'][1]}, {cls['color'][2]})" for cls in bonitet_classes}

    counts = df["bonitet_class"].value_counts().reindex(bonitet_order, fill_value=0).reset_index()
    counts.columns = ["bonitet_class", "count"]

    hist = px.bar(
        counts, x="bonitet_class", y="count", color="bonitet_class",
        category_orders={"bonitet_class": bonitet_order},
        color_discrete_map=bonitet_colors,
        template=plotly_template
    )
    hist.update_layout(xaxis_title="Класс бонитета", yaxis_title="Число точек", showlegend=False, template=plotly_template)
    st.plotly_chart(hist, use_container_width=True)

    if display_mode == "Пригодность для культур" and selected_culture:
        st.markdown(f"**Распределение пригодности для культуры: {selected_culture}**")
        pie_data = df[selected_culture].value_counts().reset_index()
        pie_data.columns = ["Пригодность", "Количество"]
        pie = px.pie(
            pie_data, names="Пригодность", values="Количество",
            color="Пригодность",
            color_discrete_map={k: f'rgb{tuple(v)}' for k, v in suitability_colors.items()},
            template=plotly_template
        )
        pie.update_layout(template=plotly_template)
        st.plotly_chart(pie, use_container_width=True)
if __name__ == "__main__":
    st.set_page_config(page_title=page_title, page_icon=page_icon, layout=layout)

    df, culture_columns = load_data()
    (
        selected_rayon, display_mode, bonitet_range,
        selected_culture, selected_suitability, map_theme, map_interface
    ) = sidebar_controls(df, culture_columns)

    plotly_template = render_background(map_interface)

    if selected_rayon == "Все районы":
        filtered_df = filter_data(df, display_mode, bonitet_range, selected_culture, selected_suitability)
        tooltip = get_tooltip(display_mode, selected_culture)
        render_map(filtered_df, tooltip, map_theme, full_view=True)
        render_legend(display_mode, selected_culture)
        render_charts(filtered_df, display_mode, selected_culture, plotly_template)
    else:
        rayon_df = load_rayon_data(selected_rayon, display_mode, selected_culture)
        if rayon_df is None:
            st.warning("Данные по выбранному району отсутствуют или повреждены.")
        else:
            filtered_df = filter_data(rayon_df, display_mode, bonitet_range, selected_culture, selected_suitability)
            tooltip = get_tooltip(display_mode, selected_culture)
            render_map(filtered_df, tooltip, map_theme)
            render_legend(display_mode, selected_culture)
            render_charts(filtered_df, display_mode, selected_culture, plotly_template)