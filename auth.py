import streamlit as st
import streamlit_authenticator as stauth
from streamlit_gsheets import GSheetsConnection
import pandas as pd

def check_auth():
    # 1. Завантаження даних (додаємо кеш, щоб не смикати таблицю при кожному F5)
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
                    "name": str(row.get('name', 'User')),
                    "password": str(row.get('password', ''))
                }
        return creds

    credentials = load_users()

    # 2. Створюємо аутентифікатор лише один раз за сесію
    if 'authenticator' not in st.session_state:
        st.session_state.authenticator = stauth.Authenticate(
            credentials,
            "aurora_tracker_v1", # Спробуйте змінити назву кукі на нову
            "constant_key_2026", 
            cookie_expiry_days=30
        )

    # 3. Виклик логіна
    # login() повертає status, але він також дублюється в st.session_state['authentication_status']
    st.session_state.authenticator.login(location="main")
    
    return (st.session_state.get("name"), 
            st.session_state.get("authentication_status"), 
            st.session_state.get("username"), 
            st.session_state.authenticator)
