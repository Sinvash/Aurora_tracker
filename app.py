import streamlit as st
from auth import check_auth

# Перевірка авторизації (кукі спрацюють тут автоматично)
name, authentication_status, username, authenticator = check_auth()

if authentication_status:
    # 1. Бокова панель з логаутом та меню
    authenticator.logout("Вийти", "sidebar")
    st.sidebar.title(f"Вітаємо, {name}!")
    
    # 2. Навігація між сторінками
    page = st.sidebar.radio("Меню", ["📍 Мапа магазинів", "📜 Моя історія", "⚙️ Налаштування"])

    # --- СТОРІНКА 1: МАПА ---
    if page == "📍 Мапа магазинів":
        st.title("Мапа магазинів Аврора")
        # Тут ваш старий код з завантаженням CSV та folium
        st.info("Тут відображається мапа з усіма точками Вінниці...")

    # --- СТОРІНКА 2: ІСТОРІЯ ---
    elif page == "📜 Моя історія":
        st.title("Ваші минулі візити")
        st.write("Тут ми згодом виведемо таблицю з вашими чекінами.")

    # --- СТОРІНКА 3: НАЛАШТУВАННЯ ---
    elif page == "⚙️ Налаштування":
        st.title("Налаштування профілю")
        st.write(f"Ви зайшли як: {username}")

elif authentication_status == False:
    st.error("Логін/пароль невірні")
elif authentication_status == None:
    st.warning("Будь ласка, введіть дані для входу")
