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

    # Створюємо об'єкт аутентифікації
    # 'aurora_cookie' - назва кукі в браузері
    # 'signature_key' - будь-який довгий випадковий рядок для шифрування
    authenticator = stauth.Authenticate(
        credentials,
        "aurora_cookie", 
        "some_signature_key_123", 
        cookie_expiry_days=30
    )

    # login повертає результат. Якщо кукі є - статус одразу буде True
    name, authentication_status, username = authenticator.login("Вхід", "main")
    
    return name, authentication_status, username, authenticator
