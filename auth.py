import streamlit as st
import streamlit_authenticator as stauth
from streamlit_gsheets import GSheetsConnection
import pandas as pd

def check_auth():
    conn = st.connection("gsheets", type=GSheetsConnection)
    
    @st.cache_data(ttl=600)
    def load_users():
        spreadsheet_url = "https://docs.google.com/spreadsheets/d/1TX9osMipdC_l6K5Fa3xHu4IGJ3gBromanbFQQuyfax0/edit"
        df = conn.read(spreadsheet=spreadsheet_url, worksheet="users")
        df.columns = [str(c).strip().lower() for c in df.columns]
        creds = {"usernames": {}}
        for _, row in df.iterrows():
            u = str(row.get('username', '')).strip()
            if u:
                creds["usernames"][u] = {
                    "name": str(row.get('name', 'Користувач')),
                    "password": str(row.get('password', ''))
                }
        return creds

    credentials = load_users()

    # 1. Ініціалізація з ОБОВ'ЯЗКОВИМ вказанням терміну дії кукі
    authenticator = stauth.Authenticate(
        credentials,
        "aurora_app_v2",   # Змінив назву кукі, щоб браузер створив нові
        "secret_key_2026", 
        cookie_expiry_days=30 
    )

    # 2. Виклик форми логіна
    # В нових версіях ми передаємо location та заголовок
    authenticator.login(location='main')

    # Перевіряємо стан
    auth_status = st.session_state.get("authentication_status")
    
    # 3. Додатковий CSS, щоб гарантувати видимість галочки
    st.markdown("""
        <style>
        /* Робимо чекбокс "Remember me" помітнішим */
        div[data-testid="stCheckbox"] {
            margin-top: -15px !important;
            margin-bottom: 10px !important;
        }
        </style>
    """, unsafe_allow_html=True)
    
    return (st.session_state.get("name"), 
            auth_status, 
            st.session_state.get("username"), 
            authenticator)
