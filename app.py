import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from auth import check_auth

# Конфігурація сторінки
st.set_page_config(page_title="Aurora Tracker", layout="wide")

# Виклик авторизації
name, authentication_status, username, authenticator = check_auth()

if authentication_status:
    # --- БОКОВА ПАНЕЛЬ (SIDEBAR) ---
    st.sidebar.title(f"👋 Вітаємо, {name}!")
    
    # Вибір сторінки
    page = st.sidebar.radio(
        "Навігація", 
        ["📍 Мапа магазинів", "📜 Моя історія", "⚙️ Налаштування"]
    )
    
    st.sidebar.divider()
    authenticator.logout("Вийти з аккаунту", "sidebar")

    # --- ЗАВАНТАЖЕННЯ ДАНИХ ---
    @st.cache_data
    def load_data():
        # Переконайтеся, що назва файлу збігається з вашим CSV на GitHub
        df = pd.read_csv("avrora_stores.csv")
        return df

    df = load_data()

    # --- СТОРІНКА 1: МАПА ---
    if page == "📍 Мапа магазинів":
        st.title("📍 Мапа магазинів Аврора")
        
        # Фільтрація по місту в боковій панелі
        cities = sorted(df['city'].unique())
        vinnitsia_idx = cities.index("Вінниця") if "Вінниця" in cities else 0
        selected_city = st.sidebar.selectbox("Оберіть місто", cities, index=vinnitsia_idx)

        filtered_df = df[df['city'] == selected_city]

        # Відображення мапи
        if not filtered_df.empty:
            center_lat = filtered_df['latitude'].mean()
            center_lng = filtered_df['longitude'].mean()
            
            m = folium.Map(location=[center_lat, center_lng], zoom_start=13)

            for idx, row in filtered_df.iterrows():
                folium.Marker(
                    [row['latitude'], row['longitude']],
                    popup=f"<b>{row['name']}</b>",
                    tooltip=row['name']
                ).add_to(m)

            st_folium(m, width="100%", height=500)
            
            # Секція чекіну
            st.divider()
            st.subheader("🏁 Відмітити візит")
            col1, col2 = st.columns([2, 1])
            
            with col1:
                store_to_check = st.selectbox("Оберіть магазин для чекіну", filtered_df['name'])
            with col2:
                if st.button("✅ Я тут був", use_container_width=True):
                    st.success(f"Супер! Візит у магазин на '{store_to_check}' зафіксовано (поки що локально).")
        else:
            st.warning("Магазинів у вибраному місті не знайдено.")

    # --- СТОРІНКА 2: ІСТОРІЯ ---
    elif page == "📜 Моя історія":
        st.title("📜 Історія ваших візитів")
        st.info("Тут будуть ваші записи з Google Sheets. Поки що тут порожньо, але ми це виправимо!")
        # Тимчасова заглушка таблиці
        st.write("Ваш прогрес у місті Вінниця: **0 / 19** магазинів")

    # --- СТОРІНКА 3: НАЛАШТУВАННЯ ---
    elif page == "⚙️ Налаштування":
        st.title("⚙️ Налаштування")
        st.write(f"**Ваш логін:** {username}")
        st.write("**Тип аккаунту:** Користувач")
        if st.button("Очистити кеш даних"):
            st.cache_data.clear()
            st.rerun()

elif authentication_status == False:
    st.error("Невірний логін або пароль. Спробуйте ще раз.")
elif authentication_status == None:
    st.warning("Будь ласка, введіть ваші дані для входу.")
