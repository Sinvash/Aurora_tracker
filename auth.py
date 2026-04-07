import streamlit as st
import streamlit_authenticator as stauth
from streamlit_gsheets import GSheetsConnection
import pandas as pd

def check_auth():
    conn = st.connection("gsheets", type=GSheetsConnection)
    
    try:
        spreadsheet_url = "https://docs.google.com/spreadsheets/d/1TX9osMipdC_l6K5Fa3xHu4IGJ3gBromanbFQQuyfax0/edit"
        # Використовуємо невеликий ttl для балансу швидкості та актуальності
        df_users = conn.read(spreadsheet=spreadsheet_url, worksheet="users", ttl=600)
        
        df_users.columns = [str(c).strip().lower() for c in df_users.columns]
        credentials = {"usernames": {}}
        for _, row in df_users.iterrows():
            u_name = str(row.get('username', '')).strip()
            if u_name:
                credentials["usernames"][u_name] = {
                    "name": str(row.get('name', 'Користувач')).strip(),
                    "password": str(row.get('password', '')).strip()
                }
            
    except Exception as e:
        st.error(f"Помилка бази даних: {e}")
        st.stop()

    # Створюємо об'єкт аутентифікації
    # ВАЖЛИВО: cookie_name та key мають бути унікальними та незмінними
    authenticator = stauth.Authenticate(
        credentials, 
        "aurora_tracker_cookie", # Назва кукі в браузері
        "random_signature_key_12345", # Ключ шифрування (не міняйте його!)
        cookie_expiry_days=30
    )

    # Виклик форми логіна
    # Аргумент clear_on_submit=False допомагає кукам
    authenticator.login(location="main")
    
    return (st.session_state.get("name"), 
            st.session_state.get("authentication_status"), 
            st.session_state.get("username"), 
            authenticator)
