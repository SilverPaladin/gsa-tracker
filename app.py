import streamlit as st
import sqlite3
from datetime import datetime

# --- 1. DATABASE SETUP ---
conn = sqlite3.connect('gsa_gemini_v2.db', check_same_thread=False)
c = conn.cursor()
c.execute('CREATE TABLE IF NOT EXISTS users (email TEXT UNIQUE, password TEXT, username TEXT)')
c.execute('CREATE TABLE IF NOT EXISTS categories (name TEXT UNIQUE)')
# Added 'importance' column to projects
c.execute('''CREATE TABLE IF NOT EXISTS projects 
             (id INTEGER PRIMARY KEY, category TEXT, title TEXT, details TEXT, 
              assigned_user TEXT, is_done INTEGER, importance TEXT)''')
c.execute('CREATE TABLE IF NOT EXISTS comments (project_id INTEGER, user TEXT, message TEXT, timestamp TEXT)')
conn.commit()

# --- 2. GEMINI UI STYLING ---
st.set_page_config(page_title="GSA Workspace", layout="wide")
st.markdown("""
<style>
    .main { background-color: #131314; color: #e3e3e3; }
    [data-testid="stSidebar"] { background-color: #1e1f20 !important; }
    .priority-dot { height: 10px; width: 10px; border-radius: 50%; display: inline-block; margin-right: 8px; }
    .dot-high { background-color: #ff4b4b; box-shadow: 0 0 8px #ff4b4b; }
    .dot-low { background-color: #0083ff; box-shadow: 0 0 8px #0083ff; }
</style>
""", unsafe_allow_html=True)

# --- 3. SESSION STATE ---
if "logged_in" not in st.session_state: st.session_state.logged_in = False
if "view" not in st.session_state: st.session_state.view = "home"

# --- 4. LOGIN LOGIC ---
if not st.session_state.logged_in:
    # (Keeping your login/register logic)
    st.title("GSA SECURE")
    t1, t2 = st.tabs(["Login", "Register"])
    with t1:
        e = st.text_input("Email")
        p = st.text_input("Password", type="password")
        if st.button("Continue"):
            res = c.execute("SELECT username FROM users WHERE email=? AND password=?", (e, p)).fetchone()
            if res: 
                st.session_state.logged_in = True
                st.session_state.user_name = res[0]
                st.rerun()
    with t2:
        nu = st.text_input("Name")
        ne = st.text_input("New Email")
        np = st.text_input("New Password", type="password")
        if st.button("Register"):
            c.execute("INSERT INTO users VALUES (?,?,?)", (ne, np, nu)); conn.commit()
            st.success("Registered!")
    st.stop()

# --- 5. SIDEBAR WITH COLOR DOTS ---
with st.sidebar:
    st.markdown(f"### ✨ {st.session_state.user_name}")
    if st.button("🏠 Home", use_container_width=True): st.session_state.view = "home"; st.rerun()
    st.divider()
    
    # Get all categories
    cats = [r[0] for r in c.execute("SELECT name FROM categories").fetchall()]
    for cat in cats:
        with st.expander(f"📁 {cat}", expanded=True):
            # Get projects and their importance
            projects = c.execute("SELECT id, title, importance FROM projects WHERE category=?", (cat,)).fetchall()
            for pid, ptitle, pimp in projects:
                # Assign dot color
                dot_class = "dot-high" if pimp == "High" else "dot-low"
                
                # Render project link with a custom HTML dot
                if st.button(f"{ptitle}", key=f"nav_{pid}", use_container_width=True):
                    st.session_state.active_id = pid
                    st.session_state.view = "view_project"
                    st.rerun()
                st.markdown(f"<div class='priority-dot {dot_class}'></div> <small>{pimp} Priority</small>", unsafe_allow_html=True)

# --- 6. TASK CREATION (FIXED DROPDOWNS) ---
if st.session_state.view == "create_project":
    st.markdown("<h2>New Task</h2>", unsafe_allow_html=True)
    
    # Refresh user list from DB every time we open this screen
    user_list = [r[0] for r in c.execute("SELECT username FROM users").fetchall()]
    cat_list = [r[0] for r in c.execute("SELECT name FROM categories").fetchall()]
    
    with st.form("new_project_form"):
        p_cat = st.selectbox("Category", cat_list if cat_list else ["General"])
        p_title = st.text_input("Task Title")
        p_user = st.selectbox("Assign User", user_list) # Your username will show here now
        p_imp = st.select_slider("Importance", options=["Low", "High"]) # Blue vs Red
        p_details = st.text_area("Details")
        
        if st.form_submit_button("Create"):
            c.execute("INSERT INTO projects (category, title, details, assigned_user, is_done, importance) VALUES (?,?,?,?,0,?)", 
                      (p_cat, p_title, p_details, p_user, p_imp))
            conn.commit()
            st.session_state.view = "home"
            st.rerun()

# (Add your view_project and create_cat screens as per previous version)
