import streamlit as st
import sqlite3

# --- DATABASE SETUP ---
# We use a permanent connection name to ensure it stays stable during the session
conn = sqlite3.connect('gsa_final_v1.db', check_same_thread=False)
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
    .main { background: linear-gradient(135deg, #0f0c29, #302b63, #24243e); color: white; }
    [data-testid="stSidebar"] { background-color: rgba(255, 255, 255, 0.03); backdrop-filter: blur(15px); border-right: 1px solid rgba(255,255,255,0.1); }
    .stTextInput>div>div>input { background-color: rgba(255,255,255,0.05); color: white; border: 1px solid rgba(255,255,255,0.2); }
    
    .glass-card {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 20px;
        padding: 30px;
        text-align: center;
        margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)

# --- SESSION STATE ---
if "logged_in" not in st.session_state: st.session_state.logged_in = False
if "user_name" not in st.session_state: st.session_state.user_name = ""
if "view" not in st.session_state: st.session_state.view = "home"

# --- AUTHENTICATION FLOW ---
if not st.session_state.logged_in:
    st.markdown("<h1 style='text-align: center;'>GSA SECURE ACCESS</h1>", unsafe_allow_html=True)
    
    col_a, col_b, col_c = st.columns([1, 2, 1])
    with col_b:
        tab1, tab2 = st.tabs(["EXISTING USER", "NEW IDENTITY"])
        
        with tab2:
            reg_user = st.text_input("One-Word Username", placeholder="e.g. Maverick")
            reg_email = st.text_input("Email", placeholder="user@gsa.com")
            reg_pw = st.text_input("Password", type="password")
            if st.button("INITIALIZE ACCOUNT"):
                if reg_user and reg_email and reg_pw:
                    try:
                        c.execute("INSERT INTO users (email, password, username) VALUES (?,?,?)", (reg_email, reg_pw, reg_user))
                        conn.commit()
                        st.success("Identity Verified. Switch to Login tab.")
                    except sqlite3.IntegrityError:
                        st.error("This email is already in the system.")
                else:
                    st.warning("All fields are mandatory.")

        with tab1:
            log_e = st.text_input("Email", key="l_e_2026")
            log_p = st.text_input("Password", type="password", key="l_p_2026")
            if st.button("UNLOCK DASHBOARD"):
                c.execute("SELECT username FROM users WHERE email=? AND password=?", (log_e, log_p))
                result = c.fetchone()
                if result:
                    st.session_state.logged_in = True
                    st.session_state.user_name = result[0]
                    st.rerun()
                else:
                    st.error("Access Denied. Check credentials.")
    st.stop()

# --- PROTECTED DASHBOARD ---
with st.sidebar:
    st.markdown(f"### ⚡ **{st.session_state.user_name}**")
    if st.button("🏠 Dashboard"): st.session_state.view = "home"; st.rerun()
    if st.button("⚙️ Identity Settings"): st.session_state.view = "settings"; st.rerun()
    st.divider()
    
    # Quick Navigation Tree
    st.caption("CORE PROJECTS")
    c.execute("SELECT name FROM categories")
    for cat in c.fetchall():
        st.markdown(f"**{cat[0].upper()}**")
        c.execute("SELECT id, title FROM projects WHERE category=?", (cat[0],))
        for p_id, p_title in c.fetchall():
            if st.button(f"# {p_title}", key=f"nav_{p_id}"):
                st.session_state.view = "view_project"
                st.session_state.active_id = p_id
                st.rerun()

# --- PAGE ROUTING ---
if st.session_state.view == "home":
    st.markdown(f"<h1 style='text-align: center;'>Welcome, {st.session_state.user_name}</h1>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("<div class='glass-card'><h2>🔳</h2><h3>Task Initiation</h3><p>Open a new project pipeline</p></div>", unsafe_allow_html=True)
        if st.button("Launch", key="btn_create"):
            st.session_state.view = "create_project"; st.rerun()
    with col2:
        st.markdown("<div class='glass-card'><h2>📂</h2><h3>Active Archive</h3><p>Manage current tree</p></div>", unsafe_allow_html=True)
        if st.button("Browse", key="btn_browse"):
            st.toast("Use the sidebar to pick a project!", icon="👈")

elif st.session_state.view == "settings":
    st.title("⚙️ Identity Settings")
    new_name = st.text_input("Change Username", value=st.session_state.user_name)
    if st.button("Sync Profile"):
        c.execute("UPDATE users SET username=? WHERE username=?", (new_name, st.session_state.user_name))
        conn.commit()
        st.session_state.user_name = new_name
        st.success("Identity Updated.")
