import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from streamlit_gsheets import GSheetsConnection
from datetime import datetime
from auth import check_auth

# --- 1. КОНФІГУРАЦІЯ ТА CSS ---
st.set_page_config(page_title="Aurora Tracker", layout="wide")

st.markdown("""
    <style>
    html, body, [class*="css"] { font-family: 'Segoe UI', sans-serif !important; }
    h1 { font-size: 20px !important; margin-bottom: 5px !important; }
    h2, h3 { font-size: 16px !important; margin-bottom: 2px !important; }
    [data-testid="stMetricValue"] { font-size: 18px !important; }
    [data-testid="stMetricLabel"] { font-size: 12px !important; }
    .block-container { padding: 0.5rem 0.7rem !important; }
    [data-testid="stVerticalBlock"] > div { padding-bottom: 0px !important; margin-bottom: 2px !important; }
    .stButton>button { height: 2.8em !important; font-size: 14px !important; font-weight: bold !important; width: 100%; }
    /* Стиль для таблиці в експандері */
    .stDataFrame { font-size: 12px !important; }
    </style>
    """, unsafe_allow_html=True)

SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1TX9osMipdC_l6K5Fa3xHu4IGJ3gBromanbFQQuyfax0/edit"

# --- 2. АВТОРИЗАЦІЯ ---
name, authentication_status, username, authenticator = check_auth()

if authentication_status:
    conn = st.connection("gsheets", type=GSheetsConnection)

    # --- 3. ФУНКЦІЯ ГЕО-ФОКУСУ ---
    def get_map_bounds(df, lat_col='latitude', lon_col='longitude'):
        if df.empty:
            return [49.23, 28.46], [[49.20, 28.40], [49.26, 28.52]] # Дефолт Вінниця
        
        min_lat, max_lat = df[lat_col].min(), df[lat_col].max()
        min_lon, max_lon = df[lon_col].min(), df[lon_col].max()
        
        lat_diff = max_lat - min_lat if max_lat != min_lat else 0.01
        lon_diff = max_lon - min_lon if max_lon != min_lon else 0.01
        
        sw = [min_lat - (lat_diff * 0.1), min_lon - (lon_diff * 0.1)]
        ne = [max_lat + (lat_diff * 0.1), max_lon + (lon_diff * 0.1)]
        center = [df[lat_col].mean(), df[lon_col].mean()]
        return center, [sw, ne]

    # --- 4. ДАНІ ---
    @st.cache_data(ttl=300)
    def get_data():
        stores = pd.read_csv("avrora_stores.csv")
        visits = conn.read(spreadsheet=SPREADSHEET_URL, worksheet="visits", ttl=0)
        if not visits.empty:
            visits.columns = [str(c).strip().lower() for c in visits.columns]
        else:
            visits = pd.DataFrame(columns=["username", "store_name", "timestamp", "city"])
        return stores, visits

    df_stores, df_visits = get_data()
    my_visits_df = df_visits[df_visits['username'] == username] if 'username' in df_visits.columns else pd.DataFrame()
    my_visits_names = my_visits_df['store_name'].tolist()

    # --- SIDEBAR ---
    st.sidebar.title(f"👋 {name}")
    page = st.sidebar.radio("Меню", ["📍 Мапа", "📜 Історія", "⚙️ Налаштування"])
    st.sidebar.divider()
    authenticator.logout("Вийти", "sidebar")

    # --- СТОРІНКА: МАПА (ЧЕКІНИ) ---
    if page == "📍 Мапа":
        cities = sorted(df_stores['city'].unique())
        v_idx = cities.index("Вінниця") if "Вінниця" in cities else 0
        selected_city = st.sidebar.selectbox("Місто", cities, index=v_idx)
        
        filtered_df = df_stores[df_stores['city'] == selected_city]
        
        # Метрики
        m1, m2 = st.columns(2)
        total_city = len(filtered_df)
        visited_city = len(filtered_df[filtered_df['name'].isin(my_visits_names)])
        m1.metric("Магазинів", total_city)
        m2.metric("Відвідано", f"{visited_city} ({int(visited_city/total_city*100) if total_city > 0 else 0}%)")

        if not filtered_df.empty:
            center, bounds = get_map_bounds(filtered_df)
            m = folium.Map(location=center, tiles="OpenStreetMap")
            m.fit_bounds(bounds)

            for _, row in filtered_df.iterrows():
                is_visited = row['name'] in my_visits_names
                color = "green" if is_visited else "blue"
                folium.Marker(
                    [row['latitude'], row['longitude']],
                    tooltip=row['name'],
                    icon=folium.Icon(color=color, icon="shopping-cart", prefix='fa')
                ).add_to(m)

            # Ключ карти змінюється при кожній взаємодії для скидання "всього світу"
            map_data = st_folium(m, width="100%", height=300, key=f"checkin_map_{selected_city}_{len(my_visits_names)}")

            clicked_store = map_data.get("last_object_clicked_tooltip")
            if clicked_store:
                st.write(f"📍 **{clicked_store}**")
                if clicked_store in my_visits_names:
                    st.success("Вже відвідано")
                else:
                    if st.button(f"Я ТУТ БУВ", type="primary"):
                        new_row = pd.DataFrame([{"username": username, "store_name": clicked_store, "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "city": selected_city}])
                        updated_df = pd.concat([df_visits, new_row], ignore_index=True)
                        conn.update(spreadsheet=SPREADSHEET_URL, worksheet="visits", data=updated_df)
                        st.cache_data.clear()
                        st.rerun()

    # --- СТОРІНКА: ІСТОРІЯ (МАПА ВІДВІДАНИХ) ---
    elif page == "📜 Історія":
        st.subheader("📜 Ваша географія візитів")
        
        # Об'єднуємо візити з координатами магазинів
        visited_with_coords = pd.merge(
            my_visits_df, 
            df_stores[['name', 'latitude', 'longitude']], 
            left_on='store_name', 
            right_on='name', 
            how='inner'
        )

        if not visited_with_coords.empty:
            # Мапа тільки відвіданих
            center_v, bounds_v = get_map_bounds(visited_with_coords)
            mv = folium.Map(location=center_v, tiles="OpenStreetMap")
            mv.fit_bounds(bounds_v)

            for _, row in visited_with_coords.iterrows():
                folium.Marker(
                    [row['latitude'], row['longitude']],
                    tooltip=f"{row['store_name']} ({row['timestamp']})",
                    icon=folium.Icon(color="green", icon="check", prefix='fa')
                ).add_to(mv)
            
            st_folium(mv, width="100%", height=350, key="history_global_map")
            
            st.divider()
            # Компактний список
            with st.expander("Переглянути повний список візитів"):
                st.dataframe(
                    my_visits_df.sort_values(by="timestamp", ascending=False)[["timestamp", "store_name", "city"]],
                    use_container_width=True
                )
        else:
            st.info("Ви ще не відвідали жодного магазину. Час вирушати в дорогу!")

    elif page == "⚙️ Налаштування":
        st.subheader("⚙️ Налаштування")
        if st.button("Очистити кеш"):
            st.cache_data.clear()
            st.rerun()

elif authentication_status == False:
    st.error("Помилка входу")
