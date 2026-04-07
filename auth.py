import streamlit as st
import streamlit_authenticator as stauth
from streamlit_gsheets import GSheetsConnection

def check_auth():
    # Підключаємось до Google Sheets
    conn = st.connection("gsheets", type=GSheetsConnection)
    
    # Читаємо аркуш users
    df_users = conn.read(worksheet="users")
    
    # Формуємо словник credentials з таблиці
    credentials = {"usernames": {}}
    for _, row in df_users.iterrows():
        credentials["usernames"][row['username']] = {
            "name": row['name'],
            "password": str(row['password']) # Паролі в таблиці мають бути рядками
        }

    # Далі стандартний код
    authenticator = stauth.Authenticate(
        credentials, "aurora_cookie", "signature_key", cookie_expiry_days=30
    )

    authenticator.login(location="main")
    
    return (st.session_state.get("name"), 
            st.session_state.get("authentication_status"), 
            st.session_state.get("username"), 
            authenticator)
