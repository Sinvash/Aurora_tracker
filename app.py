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
    h1 { font-size: 20px !important; margin-bottom: 5px !important; padding-top: 0px !important; }
    h2, h3 { font-size: 16px !important; margin-bottom: 2px !important; }
    [data-testid="stMetricValue"] { font-size: 18px !important; }
    [data-testid="stMetricLabel"] { font-size: 12px !important; }
    .block-container { padding: 0.5rem 0.7rem !important; }
    [data-testid="stVerticalBlock"] > div { padding-bottom: 0px !important; margin-bottom: 2px !important; }
    .stButton>button { 
        height: 2.8em !important; 
        font-size: 14px !important; 
        font-weight: bold !important; 
        width: 100%; 
        border-radius: 8px !important;
    }
    .stDataFrame { font-size: 12px !important; }
    </style>
    """, unsafe_allow_html=True)

SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1TX9osMipdC_l6K5Fa3xHu4IGJ3gBromanbFQQuyfax0/edit"

# --- 2. ДОПОМІЖНІ ФУНКЦІЇ ---
def get_map_bounds(df, lat_col='latitude', lon_col='longitude'):
    # Дефолтні координати Вінниці (Вежа)
    vinn_center = [49.2328, 28.4808]
    vinn_bounds = [[49.20, 28.40], [49.26, 28.52]]
    
    if df is None or df.empty:
        return vinn_center, vinn_bounds
    
    min_lat, max_lat = df[lat_col].min(), df[lat_col].max()
    min_lon, max_lon = df[lon_col].min(), df[lon_col].max()
    
    # Якщо одна точка
    if min_lat == max_lat:
        return [min_lat, min_lon], [[min_lat-0.01, min_lon-0.01], [max_lat+0.01, max_lon+0.01]]

    lat_diff = max_lat - min_lat
    lon_diff = max_lon - min_lon
    
    sw = [min_lat - (lat_diff * 0.1), min_lon - (lon_diff * 0.1)]
    ne = [max_lat + (lat_diff * 0.1), max_lon + (lon_diff * 0.1)]
    center = [df[lat_col].mean(), df[lon_col].mean()]
    return center, [sw, ne]

# --- 3. АВТОРИЗАЦІЯ ---
name, authentication_status, username, authenticator = check_auth()

if authentication_status:
    conn = st.connection("gsheets", type=GSheetsConnection)

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
        
        if 'selected_city' not in st.session_state:
            st.session_state.selected_city = "Вінниця" if "Вінниця" in cities else cities[0]

        selected_city = st.sidebar.selectbox("Місто", cities, index=cities.index(st.session_state.selected_city))
        st.session_state.selected_city = selected_city
        
        filtered_df = df_stores[df_stores['city'] == selected_city]
        
        # Метрики
        m1, m2 = st.columns(2)
        total_city = len(filtered_df)
        visited_city = len(filtered_df[filtered_df['name'].isin(my_visits_names)])
        m1.metric("Магазинів", total_city)
        m2.metric("Відвідано", f"{visited_city} ({int(visited_city/total_city*100) if total_city > 0 else 0}%)")

        # Фокус на Вінницю, якщо дані ще не готові
        center, bounds = get_map_bounds(filtered_df)
        
        m = folium.Map(
            location=center, 
            tiles="OpenStreetMap", 
            zoom_start=13, 
            control_scale=True
        )
        
        if not filtered_df.empty:
            for _, row in filtered_df.iterrows():
                is_visited = row['name'] in my_visits_names
                color = "green" if is_visited else "blue"
                folium.Marker(
                    [row['latitude'], row['longitude']],
                    tooltip=row['name'],
                    icon=folium.Icon(color=color, icon="shopping-cart", prefix='fa')
                ).add_to(m)
            m.fit_bounds(bounds)

        # Унікальний ключ: username гарантує скидання при зміні користувача
        map_key = f"map_{username}_{selected_city}_{len(my_visits_names)}"
        map_data = st_folium(m, width="100%", height=300, key=map_key)

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

    # --- СТОРІНКА: ІСТОРІЯ ---
    elif page == "📜 Історія":
        st.subheader("📜 Ваша географія візитів")
        
        visited_with_coords = pd.merge(
            my_visits_df, 
            df_stores[['name', 'latitude', 'longitude']], 
            left_on='store_name', right_on='name', how='inner'
        )

        # Якщо візитів немає, історія теж показує Вінницю за замовчуванням
        center_v, bounds_v = get_map_bounds(visited_with_coords)
        mv = folium.Map(location=center_v, tiles="OpenStreetMap", zoom_start=12)
        
        if not visited_with_coords.empty:
            for _, row in visited_with_coords.iterrows():
                folium.Marker(
                    [row['latitude'], row['longitude']],
                    tooltip=f"{row['store_name']} ({row['timestamp']})",
                    icon=folium.Icon(color="green", icon="check", prefix='fa')
                ).add_to(mv)
            mv.fit_bounds(bounds_v)
            st_folium(mv, width="100%", height=350, key=f"hist_map_{username}")
            
            st.divider()
            with st.expander("Переглянути список візитів"):
                st.dataframe(my_visits_df.sort_values(by="timestamp", ascending=False)[["timestamp", "store_name", "city"]], use_container_width=True)
        else:
            st_folium(mv, width="100%", height=350, key="hist_map_empty")
            st.info("Ви ще не зробили жодного чекіну.")

    elif page == "⚙️ Налаштування":
        st.subheader("⚙️ Налаштування")
        st.write(f"Аккаунт: **{name}** (@{username})")
        if st.button("Очистити кеш"):
            st.cache_data.clear()
            st.rerun()

elif authentication_status == False:
    st.error("Логін або пароль невірні")
elif authentication_status == None:
    st.warning("Будь ласка, авторизуйтесь")
