import streamlit as st
import streamlit_authenticator as stauth
from streamlit_gsheets import GSheetsConnection

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

    # Створюємо об'єкт (важливо: cookie_name має бути без пробілів)
    authenticator = stauth.Authenticate(
        credentials,
        "aurora_tracker_v4", 
        "constant_key_2026", 
        cookie_expiry_days=30 
    )

    # Виклик логіна з явною назвою для активації кукі
    authenticator.login(location='main')

    return (st.session_state.get("name"), 
            st.session_state.get("authentication_status"), 
            st.session_state.get("username"), 
            authenticator)
