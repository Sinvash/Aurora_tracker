import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from streamlit_gsheets import GSheetsConnection
from datetime import datetime
from auth import check_auth

# --- КОНФІГУРАЦІЯ ---
st.set_page_config(page_title="Aurora Tracker", layout="wide")
SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1TX9osMipdC_l6K5Fa3xHu4IGJ3gBromanbFQQuyfax0/edit"

# Виклик авторизації
name, authentication_status, username, authenticator = check_auth()

if authentication_status:
    # Підключення до Google Sheets
    conn = st.connection("gsheets", type=GSheetsConnection)

    # --- SIDEBAR ---
    st.sidebar.title(f"👋 Вітаємо, {name}!")
    page = st.sidebar.radio("Навігація", ["📍 Мапа магазинів", "📜 Моя історія", "⚙️ Налаштування"])
    
    st.sidebar.divider()
    authenticator.logout("Вийти з аккаунту", "sidebar")

    # --- ЗАВАНТАЖЕННЯ ДАНИХ ---
    @st.cache_data(ttl=300) 
    def get_data():
        stores = pd.read_csv("avrora_stores.csv")
        # Читаємо візити (ttl=0 для миттєвого оновлення)
        visits = conn.read(spreadsheet=SPREADSHEET_URL, worksheet="visits", ttl=0)
        
        # Захист від порожньої таблиці або неправильних заголовків
        if not visits.empty:
            visits.columns = [str(c).strip().lower() for c in visits.columns]
        else:
            visits = pd.DataFrame(columns=["username", "store_name", "timestamp", "city"])
            
        return stores, visits

    df_stores, df_visits = get_data()

    # Фільтруємо візити тільки для поточного користувача
    # Використовуємо .get на випадок відсутності колонки після очищення
    my_visits = df_visits[df_visits['username'] == username]['store_name'].tolist() if 'username' in df_visits.columns else []

    # --- СТОРІНКА 1: МАПА ---
    if page == "📍 Мапа магазинів":
        st.title("📍 Мапа магазинів Аврора")

        # Вибір міста
        cities = sorted(df_stores['city'].unique())
        v_idx = cities.index("Вінниця") if "Вінниця" in cities else 0
        selected_city = st.sidebar.selectbox("Оберіть місто", cities, index=v_idx)

        filtered_df = df_stores[df_stores['city'] == selected_city]

        # Метрики прогресу
        total_in_city = len(filtered_df)
        visited_in_city = len(filtered_df[filtered_df['name'].isin(my_visits)])
        
        col_m1, col_m2 = st.columns(2)
        col_m1.metric("Магазинів у місті", total_in_city)
        col_m2.metric("Відвідано вами", f"{visited_in_city} ({int(visited_in_city/total_in_city*100) if total_in_city > 0 else 0}%)")

        # Створення мапи
        if not filtered_df.empty:
            center = [filtered_df['latitude'].mean(), filtered_df['longitude'].mean()]
            m = folium.Map(location=center, zoom_start=13)

            for _, row in filtered_df.iterrows():
                is_visited = row['name'] in my_visits
                color = "green" if is_visited else "blue"
                icon = "check" if is_visited else "shopping-cart"
                
                folium.Marker(
                    [row['latitude'], row['longitude']],
                    popup=f"<b>{row['name']}</b><br>{'✅ ВІДВІДАНО' if is_visited else '❌ Ще не були'}",
                    tooltip=row['name'], # Це важливо для розпізнавання кліку
                    icon=folium.Icon(color=color, icon=icon, prefix='fa')
                ).add_to(m)

            # Виведення мапи (зберігаємо результат у map_data)
            map_data = st_folium(m, width="100%", height=500, key="main_map")

            # --- ЛОГІКА КЛІКУ НА КАРТІ ---
            clicked_store = map_data.get("last_object_clicked_tooltip")
            
            st.divider()
            
            if clicked_store:
                st.subheader(f"📍 Обрано: {clicked_store}")
                if clicked_store in my_visits:
                    st.success("Ви вже відвідували цей магазин! 🎉")
                else:
                    if st.button(f"✅ Відмітити візит у {clicked_store}", type="primary", use_container_width=True):
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
                            st.error(f"Помилка запису: {e}")
            else:
                st.info("💡 Натисніть на маркер магазину на карті, щоб швидко зробити чекін.")

            # Альтернативний вибір через список
            with st.expander("Або оберіть зі списку вручну"):
                available_to_check = filtered_df[~filtered_df['name'].isin(my_visits)]['name'].tolist()
                if available_to_check:
                    col_s1, col_s2 = st.columns([2, 1])
                    with col_s1:
                        store_to_check = st.selectbox("Магазини:", available_to_check)
                    with col_s2:
                        if st.button("Зберегти", use_container_width=True):
                            # Логіка повторюється для стабільності
                            new_row = pd.DataFrame([{
                                "username": username,
                                "store_name": store_to_check,
                                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                "city": selected_city
                            }])
                            updated_df = pd.concat([df_visits, new_row], ignore_index=True)
                            conn.update(spreadsheet=SPREADSHEET_URL, worksheet="visits", data=updated_df)
                            st.cache_data.clear()
                            st.rerun()
                else:
                    st.write("Усі магазини в цьому місті відвідано!")

    # --- СТОРІНКА 2: ІСТОРІЯ ---
    elif page == "📜 Моя історія":
        st.title("📜 Історія ваших візитів")
        if not df_visits.empty and 'username' in df_visits.columns:
            user_history = df_visits[df_visits['username'] == username].sort_values(by="timestamp", ascending=False)
            if not user_history.empty:
                st.dataframe(user_history[["timestamp", "store_name", "city"]], use_container_width=True)
            else:
                st.warning("Ви ще не зробили жодного чекіну.")
        else:
            st.warning("Історія порожня.")

    # --- СТОРІНКА 3: НАЛАШТУВАННЯ ---
    elif page == "⚙️ Налаштування":
        st.title("⚙️ Налаштування")
        st.write(f"**Аккаунт:** {name} (@{username})")
        if st.button("Очистити кеш даних"):
            st.cache_data.clear()
            st.rerun()

elif authentication_status == False:
    st.error("Невірний логін або пароль.")
elif authentication_status == None:
    st.warning("Будь ласка, авторизуйтесь для доступу до карти.")
