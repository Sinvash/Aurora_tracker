import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from streamlit_gsheets import GSheetsConnection
from datetime import datetime
from auth import check_auth

# --- КОНФІГУРАЦІЯ ТА СТИЛІ ---
st.set_page_config(page_title="Aurora Tracker", layout="wide")

st.markdown("""
    <style>
    /* Уніфікація шрифтів та розмірів */
    html, body, [class*="css"]  {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    h1 {
        font-size: 22px !important;
        margin-bottom: 8px !important;
        padding-top: 0px !important;
    }
    h2, h3 {
        font-size: 16px !important;
        margin-bottom: 4px !important;
    }
    /* Компактні метрики */
    [data-testid="stMetricValue"] {
        font-size: 18px !important;
    }
    [data-testid="stMetricLabel"] {
        font-size: 12px !important;
    }
    /* Прибираємо зайві відступи */
    .block-container {
        padding-top: 0.5rem !important;
        padding-bottom: 0rem !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
    }
    [data-testid="stVerticalBlock"] > div {
        padding-bottom: 0px !important;
        margin-bottom: 0px !important;
    }
    /* Кнопка чекіну */
    .stButton>button {
        height: 2.5em !important;
        font-size: 14px !important;
        margin-top: 10px !important;
    }
    </style>
    """, unsafe_allow_html=True)

SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1TX9osMipdC_l6K5Fa3xHu4IGJ3gBromanbFQQuyfax0/edit"

name, authentication_status, username, authenticator = check_auth()

if authentication_status:
    conn = st.connection("gsheets", type=GSheetsConnection)

    # --- SIDEBAR ---
    st.sidebar.title(f"👋 {name}")
    page = st.sidebar.radio("Навігація", ["📍 Мапа", "📜 Історія", "⚙️ Налаштування"])
    st.sidebar.divider()
    authenticator.logout("Вийти", "sidebar")

    # --- ДАНІ ---
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
    my_visits = df_visits[df_visits['username'] == username]['store_name'].tolist() if 'username' in df_visits.columns else []

    if page == "📍 Мапа":
        # Вибір міста
        cities = sorted(df_stores['city'].unique())
        v_idx = cities.index("Вінниця") if "Вінниця" in cities else 0
        selected_city = st.sidebar.selectbox("Місто", cities, index=v_idx)
        
        filtered_df = df_stores[df_stores['city'] == selected_city]

        # Метрики в один рядок
        m1, m2 = st.columns(2)
        total_city = len(filtered_df)
        visited_city = len(filtered_df[filtered_df['name'].isin(my_visits)])
        m1.metric("Всього магазинів", total_city)
        m2.metric("Відвідано", f"{visited_city} ({int(visited_city/total_city*100) if total_city > 0 else 0}%)")

        if not filtered_df.empty:
            # --- НОВА ЛОГІКА ЦЕНТРУВАННЯ (Bounding Box + 10% Margin) ---
            min_lat, max_lat = filtered_df['latitude'].min(), filtered_df['latitude'].max()
            min_lon, max_lon = filtered_df['longitude'].min(), filtered_df['longitude'].max()
            
            lat_diff = max_lat - min_lat
            lon_diff = max_lon - min_lon
            
            # Додаємо 10% запасу
            margin_lat = lat_diff * 0.1
            margin_lon = lon_diff * 0.1
            
            # Крайні точки для фокусування
            sw = [min_lat - margin_lat, min_lon - margin_lon] # South-West
            ne = [max_lat + margin_lat, max_lon + margin_lon] # North-East

            # Створюємо мапу (без фіксованого zoom, боfit_bounds його перекриє)
            m = folium.Map()
            m.fit_bounds([sw, ne]) 

            for _, row in filtered_df.iterrows():
                is_visited = row['name'] in my_visits
                color = "green" if is_visited else "blue"
                folium.Marker(
                    [row['latitude'], row['longitude']],
                    tooltip=row['name'],
                    icon=folium.Icon(color=color, icon="shopping-cart", prefix='fa')
                ).add_to(m)

            # Висота карти 300px для мобільних
            map_data = st_folium(m, width="100%", height=300, key="main_map")

            # --- ЛОГІКА КЛІКУ ---
            clicked_store = map_data.get("last_object_clicked_tooltip")
            
            if clicked_store:
                st.write(f"📍 **{clicked_store}**")
                if clicked_store in my_visits:
                    st.success("Вже відвідано")
                else:
                    if st.button(f"✅ Я ТУТ БУВ", type="primary", use_container_width=True):
                        try:
                            new_row = pd.DataFrame([{
                                "username": username, "store_name": clicked_store,
                                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                "city": selected_city
                            }])
                            updated_df = pd.concat([df_visits, new_row], ignore_index=True)
                            conn.update(spreadsheet=SPREADSHEET_URL, worksheet="visits", data=updated_df)
                            st.cache_data.clear()
                            st.rerun()
                        except Exception as e:
                            st.error(f"Помилка: {e}")
            else:
                st.info("Натисніть на маркер на карті")

    elif page == "📜 Історія":
        st.title("Ваші візити")
        user_history = df_visits[df_visits['username'] == username].sort_values(by="timestamp", ascending=False)
        st.dataframe(user_history[["timestamp", "store_name", "city"]], use_container_width=True, height=400)

elif authentication_status == False:
    st.error("Помилка входу")
