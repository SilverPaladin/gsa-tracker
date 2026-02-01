import streamlit as st
import sqlite3

# --- DATABASE SETUP ---
conn = sqlite3.connect('gsa_v2026.db', check_same_thread=False)
c = conn.cursor()
c.execute('CREATE TABLE IF NOT EXISTS users (email TEXT UNIQUE, password TEXT, username TEXT)')
c.execute('CREATE TABLE IF NOT EXISTS categories (name TEXT UNIQUE)')
c.execute('''CREATE TABLE IF NOT EXISTS projects 
             (id INTEGER PRIMARY KEY, category TEXT, title TEXT, details TEXT, 
              assigned_user TEXT, is_done INTEGER)''')
conn.commit()

# --- 2026 MODERN UI STYLING ---
st.markdown("""
<style>
    /* Global Styles */
    .main { background: linear-gradient(135deg, #0f0c29, #302b63, #24243e); color: white; }
    [data-testid="stSidebar"] { background-color: rgba(255, 255, 255, 0.05); backdrop-filter: blur(10px); }
    
    /* Splash Screen Glass Cards */
    .glass-card {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 20px;
        padding: 40px;
        text-align: center;
        transition: 0.4s;
        margin-bottom: 20px;
    }
    .glass-card:hover {
        background: rgba(255, 255, 255, 0.1);
        border: 1px solid #5865f2;
        transform: translateY(-5px);
    }
    
    /* Project Cards */
    .project-card {
        background: #ffffff;
        padding: 25px;
        border-radius: 15px;
        color: #1a1a1a;
        border-left: 10px solid #5865f2;
        box-shadow: 0 10px 30px rgba(0,0,0,0.5);
    }
    .project-card-done {
        background: rgba(255,255,255,0.1);
        padding: 25px;
        border-radius: 15px;
        color: #a0a0a0;
        border-left: 10px solid #4e5058;
    }
</style>
""", unsafe_allow_html=True)

# --- SESSION STATE ---
if "logged_in" not in st.session_state: st.session_state.logged_in = False
if "user_name" not in st.session_state: st.session_state.user_name = "Guest"
if "view" not in st.session_state: st.session_state.view = "home"

# --- AUTHENTICATION (REPLACED PLACEHOLDER) ---
if not st.session_state.logged_in:
    st.title("🛡️ GSA Secure Access")
    t1, t2 = st.tabs(["Login", "Join"])
    with t2:
        reg_user = st.text_input("One-Word Username")
        reg_email = st.text_input("Email")
        reg_pw = st.text_input("Password", type="password")
        if st.button("Initialize Account"):
            c.execute("INSERT INTO users VALUES (?,?,?)", (reg_email, reg_pw, reg_user))
            conn.commit()
            st.success("Welcome aboard!")
    with t1:
        log_e = st.text_input("Email", key="l_e")
        log_p = st.text_input("Password", type="password", key="l_p")
        if st.button("Enter Dashboard"):
            c.execute("SELECT username FROM users WHERE email=? AND password=?", (log_e, log_p))
            res = c.fetchone()
            if res:
                st.session_state.logged_in = True
                st.session_state.user_name = res[0]
                st.rerun()
    st.stop()

# --- SIDEBAR NAV ---
with st.sidebar:
    st.markdown(f"### Welcome, **{st.session_state.user_name}**")
    if st.button("🏠 Dashboard"): st.session_state.view = "home"; st.rerun()
    if st.button("⚙️ Account Settings"): st.session_state.view = "settings"; st.rerun()
    st.divider()
    # (Category/Project Tree Logic remains here...)

# --- MAIN CONTENT ---

# 1. THE 2026 SPLASH SCREEN
if st.session_state.view == "home":
    st.markdown(f"<h1 style='text-align: center;'>System Online: {st.session_state.user_name}</h1>", unsafe_allow_html=True)
    st.write("---")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("<div class='glass-card'><h2>🔳</h2><h3>Initiate Task</h3><p>Create a new project pipeline</p></div>", unsafe_allow_html=True)
        if st.button("Launch Creator", key="b1"): 
            st.session_state.view = "create_project"; st.rerun()
            
    with col2:
        st.markdown("<div class='glass-card'><h2>📂</h2><h3>Active Archive</h3><p>Browse existing task trees</p></div>", unsafe_allow_html=True)
        if st.button("Open Library", key="b2"): 
            st.toast("Select a project from the sidebar!")

# 2. ACCOUNT MODIFICATION PANEL
elif st.session_state.view == "settings":
    st.title("⚙️ Account Modification")
    new_display_name = st.text_input("Edit Username", value=st.session_state.user_name)
    if st.button("Update Identity"):
        # Logic to update DB
        st.session_state.user_name = new_display_name
        st.success("Profile updated.")
