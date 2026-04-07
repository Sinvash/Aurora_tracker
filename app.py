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
    /* Уніфікація шрифтів */
    html, body, [class*="css"] {
        font-family: 'Segoe UI', sans-serif !important;
    }
    /* Компактні заголовки */
    h1 { font-size: 20px !important; margin-bottom: 5px !important; padding-top: 0px !important; }
    h2, h3 { font-size: 16px !important; margin-bottom: 2px !important; }
    
    /* Зменшення метрик */
    [data-testid="stMetricValue"] { font-size: 18px !important; }
    [data-testid="stMetricLabel"] { font-size: 12px !important; }
    
    /* Прибирання відступів контейнерів */
    .block-container {
        padding-top: 0.5rem !important;
        padding-bottom: 0rem !important;
        padding-left: 0.7rem !important;
        padding-right: 0.7rem !important;
    }
    /* Щільність блоків */
    [data-testid="stVerticalBlock"] > div {
        padding-bottom: 0px !important;
        margin-bottom: 2px !important;
    }
    /* Стиль кнопки чекіну */
    .stButton>button {
        height: 2.8em !important;
        font-size: 14px !important;
        font-weight: bold !important;
        border-radius: 8px !important;
    }
    </style>
    """, unsafe_allow_html=True)

SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1TX9osMipdC_l6K5Fa3xHu4IGJ3gBromanbFQQuyfax0/edit"

# --- 2. АВТОРИЗАЦІЯ ---
name, authentication_status, username, authenticator = check_auth()

if authentication_status:
    conn = st.connection("gsheets", type=GSheetsConnection)

    # --- SIDEBAR ---
    st.sidebar.title(f"👋 {name}")
    page = st.sidebar.radio("Меню", ["📍 Мапа", "📜 Історія", "⚙️ Налаштування"])
    st.sidebar.divider()
    authenticator.logout("Вийти", "sidebar")

    # --- 3. ЗАВАНТАЖЕННЯ ДАНИХ ---
    @st.cache_data(ttl=300)
    def get_data():
        stores = pd.read_csv("avrora_stores.csv")
        visits = conn.read(spreadsheet=SPREADSHEET_URL, worksheet="visits", ttl=0)
        # Очищення колонок
        if not visits.empty:
            visits.columns = [str(c).strip().lower() for c in visits.columns]
        else:
            visits = pd.DataFrame(columns=["username", "store_name", "timestamp", "city"])
        return stores, visits

    df_stores, df_visits = get_data()
    
    # Список назв відвіданих магазинів для поточного юзера
    my_visits = []
    if not df_visits.empty and 'username' in df_visits.columns:
        my_visits = df_visits[df_visits['username'] == username]['store_name'].tolist()

    # --- СТОРІНКА: МАПА ---
    if page == "📍 Мапа":
        # Вибір міста (компактний)
        cities = sorted(df_stores['city'].unique())
        v_idx = cities.index("Вінниця") if "Вінниця" in cities else 0
        selected_city = st.sidebar.selectbox("Оберіть місто", cities, index=v_idx)
        
        filtered_df = df_stores[df_stores['city'] == selected_city]

        # Метрики в один рядок
        m1, m2 = st.columns(2)
        total_city = len(filtered_df)
        visited_city = len(filtered_df[filtered_df['name'].isin(my_visits)])
        m1.metric("Магазинів", total_city)
        m2.metric("Відвідано", f"{visited_city} ({int(visited_city/total_city*100) if total_city > 0 else 0}%)")

        if not filtered_df.empty:
            # --- ЛОГІКА ЦЕНТРУВАННЯ (Bounding Box + 10%) ---
            min_lat, max_lat = filtered_df['latitude'].min(), filtered_df['latitude'].max()
            min_lon, max_lon = filtered_df['longitude'].min(), filtered_df['longitude'].max()
            
            lat_diff = max_lat - min_lat
            lon_diff = max_lon - min_lon
            
            sw = [min_lat - (lat_diff * 0.1), min_lon - (lon_diff * 0.1)]
            ne = [max_lat + (lat_diff * 0.1), max_lon + (lon_diff * 0.1)]

            # Створення мапи з прив'язкою до центру міста (захист від "всього світу")
            city_center = [filtered_df['latitude'].mean(), filtered_df['longitude'].mean()]
            m = folium.Map(location=city_center, zoom_start=13, tiles="OpenStreetMap")
            m.fit_bounds([sw, ne]) 

            # Додавання маркерів
            for _, row in filtered_df.iterrows():
                is_visited = row['name'] in my_visits
                color = "green" if is_visited else "blue"
                folium.Marker(
                    [row['latitude'], row['longitude']],
                    tooltip=row['name'],
                    icon=folium.Icon(color=color, icon="shopping-cart", prefix='fa')
                ).add_to(m)

            # Відображення мапи з унікальним ключем для стабільності масштабу
            map_data = st_folium(m, width="100%", height=300, key=f"map_{selected_city}")

            # --- ЛОГІКА ЧЕКІНУ ПРИ КЛІКУ ---
            clicked_store = map_data.get("last_object_clicked_tooltip")
            
            if clicked_store:
                st.write(f"📍 **{clicked_store}**")
                if clicked_store in my_visits:
                    st.success("✅ Вже відвідано")
                else:
                    if st.button(f"Я ТУТ БУВ", type="primary", use_container_width=True):
                        try:
                            new_row = pd.DataFrame([{
                                "username": username,
                                "store_name": clicked_store,
                                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                "city": selected_city
                            }])
                            updated_df = pd.concat([df_visits, new_row], ignore_index=True)
                            conn.update(spreadsheet=SPREADSHEET_URL, worksheet="visits", data=updated_df)
                            st.balloons()
                            st.cache_data.clear()
                            st.rerun()
                        except Exception as e:
                            st.error(f"Помилка: {e}")
            else:
                st.info("Натисніть на маркер на мапі для чекіну")

    # --- СТОРІНКА: ІСТОРІЯ ---
    elif page == "📜 Історія":
        st.subheader("📜 Ваші візити")
        if not df_visits.empty:
            user_history = df_visits[df_visits['username'] == username].sort_values(by="timestamp", ascending=False)
            st.dataframe(user_history[["timestamp", "store_name", "city"]], use_container_width=True, height=450)
        else:
            st.write("Історія порожня.")

    # --- СТОРІНКА: НАЛАШТУВАННЯ ---
    elif page == "⚙️ Налаштування":
        st.subheader("⚙️ Налаштування")
        st.write(f"Ви увійшли як: **{name}**")
        if st.button("Очистити кеш"):
            st.cache_data.clear()
            st.rerun()

elif authentication_status == False:
    st.error("Логін або пароль невірні")
elif authentication_status == None:
    st.warning("Будь ласка, авторизуйтесь")
