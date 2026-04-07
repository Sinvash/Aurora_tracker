import streamlit as st
import streamlit_authenticator as stauth

def check_auth():
    # Дані користувачів
    credentials = {
        "usernames": {
            "admin": {"name": "Адмін", "password": "123"},
            "user1": {"name": "Користувач 1", "password": "456"}
        }
    }

    # Створюємо об'єкт
    authenticator = stauth.Authenticate(
        credentials,
        "aurora_cookie", 
        "signature_key_123", 
        cookie_expiry_days=30
    )

    # Виклик логіна (у версії 0.3.6 він не повертає значення одразу)
    authenticator.login(location="main")
    
    # Отримуємо дані з сесії
    authentication_status = st.session_state.get("authentication_status")
    name = st.session_state.get("name")
    username = st.session_state.get("username")
    
    return name, authentication_status, username, authenticator
