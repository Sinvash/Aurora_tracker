import streamlit as st
import streamlit_authenticator as stauth

def check_auth():
    # Налаштування користувачів (можна додати більше)
    names = ["Адмін", "Користувач 1"]
    usernames = ["admin", "user1"]
    passwords = ["123", "456"] 

    # Хешування
    hashed_passwords = stauth.Hasher(passwords).generate()

    authenticator = stauth.Authenticate(
        {"credentials": {"usernames": {u: {"name": n, "password": p} 
         for u, n, p in zip(usernames, names, hashed_passwords)}}},
        "aurora_cookie", "auth_key", cookie_expiry_days=30
    )

    # Повертаємо результат логіна
    name, authentication_status, username = authenticator.login("Login", "main")
    
    return name, authentication_status, username, authenticator
