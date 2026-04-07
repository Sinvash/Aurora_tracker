import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

# Налаштування сторінки
st.set_page_config(page_title="Aurora Tracker", layout="wide", initial_sidebar_state="expanded")

st.title("📍 Мій Щоденник Аврори")

# Функція завантаження даних
@st.cache_data
def load_data():
    df = pd.read_csv("avrora_stores.csv")
    return df

try:
    df = load_data()

    # Бокова панель для фільтрації
    st.sidebar.header("Фільтри")
    cities = sorted(df['city'].unique())
    # Намагаємось автоматично обрати Вінницю, якщо вона є в списку
    default_city_index = cities.index("Вінниця") if "Вінниця" in cities else 0
    selected_city = st.sidebar.selectbox("Оберіть місто", cities, index=default_city_index)

    filtered_df = df[df['city'] == selected_city]

    # Вивід статистики
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Магазинів у місті", len(filtered_df))
    with col2:
        st.metric("Ваші візити (скоро)", "0")

    # Створення мапи
    st.subheader(f"Мапа магазинів: {selected_city}")
    
    # Визначаємо центр мапи по середнім координатам
    center_lat = filtered_df['latitude'].mean()
    center_lng = filtered_df['longitude'].mean()
    
    m = folium.Map(location=[center_lat, center_lng], zoom_start=13)

    for idx, row in filtered_df.iterrows():
        folium.Marker(
            [row['latitude'], row['longitude']],
            popup=f"<b>{row['name']}</b><br>{row['city']}",
            tooltip=row['name']
        ).add_to(m)

    st_folium(m, width="100%", height=500)

    # Список під мапою
    st.subheader("Список адрес")
    st.dataframe(filtered_df[['name', 'city', 'pickup_time']], use_container_width=True)

except Exception as e:
    st.error(f"Помилка завантаження даних: {e}")
    st.info("Переконайтеся, що файл avrora_stores.csv знаходиться в тому самому репозиторії.")
