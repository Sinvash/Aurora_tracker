import streamlit as st
import streamlit_authenticator as stauth
from streamlit_gsheets import GSheetsConnection
import pandas as pd

def check_auth():
    # 1. Підключаємось до Google Sheets
    # Налаштування сервісного акаунта мають бути у Secrets під ключем [connections.gsheets]
    conn = st.connection("gsheets", type=GSheetsConnection)
    
    try:
        # 2. Читаємо дані користувачів з вашої таблиці
        # Використовуємо ваш ID таблиці
        spreadsheet_url = "https://docs.google.com/spreadsheets/d/1TX9osMipdC_l6K5Fa3xHu4IGJ3gBromanbFQQuyfax0/edit"
        df_users = conn.read(spreadsheet=spreadsheet_url, worksheet="users")
        
        # Перетворюємо дані в словник, який розуміє аутентифікатор
        credentials = {"usernames": {}}
        for _, row in df_users.iterrows():
            # Перетворюємо всі значення в рядки, щоб уникнути помилок з числами в паролях
            username = str(row['username']).strip()
            credentials["usernames"][username] = {
                "name": str(row['name']),
                "password": str(row['password'])
            }

    except Exception as e:
        st.error(f"Помилка підключення до бази даних: {e}")
        st.stop()

    # 3. Ініціалізація аутентифікатора
    # cookie_name та key можуть бути будь-якими рядками
    authenticator = stauth.Authenticate(
        credentials, 
        "aurora_cookie", 
        "aurora_secret_key_2026", 
        cookie_expiry_days=30
    )

    # 4. Виклик форми логіна
    # У версії 0.3.x вона автоматично керує session_state
    authenticator.login(location="main")
    
    # Отримуємо результати з session_state
    name = st.session_state.get("name")
    authentication_status = st.session_state.get("authentication_status")
    username = st.session_state.get("username")
    
    return name, authentication_status, username, authenticator
