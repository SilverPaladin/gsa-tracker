import streamlit as st
import sqlite3
from datetime import datetime

# --- 1. DATABASE SETUP (V3) ---
conn = sqlite3.connect('gsa_gemini_v3.db', check_same_thread=False)
c = conn.cursor()
c.execute('CREATE TABLE IF NOT EXISTS users (email TEXT UNIQUE, password TEXT, username TEXT)')
c.execute('CREATE TABLE IF NOT EXISTS categories (name TEXT UNIQUE)')
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
    [data-testid="stSidebar"] { background-color: #1e1f20 !important; border-right: none; }
    
    /* Importance Dots */
    .priority-dot {
        height: 12px;
        width: 12px;
        border-radius: 50%;
        display: inline-block;
        margin-right: 10px;
        vertical-align: middle;
    }
    .dot-high { background-color: #ff4b4b; box-shadow: 0 0 10px rgba(255, 75, 75, 0.4); }
    .dot-low { background-color: #0083ff; box-shadow: 0 0 10px rgba(0, 131, 255, 0.4); }
    
    /* Chat Styling Fix */
    .chat-container {
        padding: 10px;
        border-radius: 15px;
        background-color: rgba(255,255,255,0.03);
        margin-bottom: 10px;
        border: 1px solid rgba(255,255,255,0.1);
    }
</style>
""", unsafe_allow_html=True)

# --- 3. SESSION STATE ---
if "logged_in" not in st.session_state: st.session_state.logged_in = False
if "view" not in st.session_state: st.session_state.view = "home"
if "user_name" not in st.session_state: st.session_state.user_name = ""

# --- 4. AUTHENTICATION ---
if not st.session_state.logged_in:
    _, col, _ = st.columns([1, 1.5, 1])
    with col:
        st.markdown("<h2 style='text-align:center; margin-top:80px;'>GSA Workspace</h2>", unsafe_allow_html=True)
        tab1, tab2 = st.tabs(["Sign In", "Register"])
        with tab1:
            le = st.text_input("Email")
            lp = st.text_input("Password", type="password")
            if st.button("Unlock Dashboard"):
                res = c.execute("SELECT username FROM users WHERE email=? AND password=?", (le, lp)).fetchone()
                if res:
                    st.session_state.logged_in = True
                    st.session_state.user_name = res[0]
                    st.rerun()
                else: st.error("Access Denied. Check credentials.")
        with tab2:
            nu = st.text_input("Username")
            ne = st.text_input("Email")
            np = st.text_input("Password", type="password")
            if st.button("Register Identity"):
                try:
                    c.execute("INSERT INTO users VALUES (?,?,?)", (ne, np, nu))
                    conn.commit(); st.success("Account created!")
                except: st.error("Email already exists.")
    st.stop()

# --- 5. SIDEBAR ---
with st.sidebar:
    st.markdown(f"### ✨ {st.session_state.user_name}")
    if st.button("🏠 Home", use_container_width=True): 
        st.session_state.view = "home"; st.rerun()
    st.divider()
    
    cats = [r[0] for r in c.execute("SELECT name FROM categories").fetchall()]
    for cat in cats:
        with st.expander(f"📁 {cat}", expanded=True):
            projects = c.execute("SELECT id, title, importance FROM projects WHERE category=?", (cat,)).fetchall()
            for pid, ptitle, pimp in projects:
                dot_color = "dot-high" if pimp == "High" else "dot-low"
                col_dot, col_btn = st.columns([0.1, 0.9])
                with col_dot:
                    st.markdown(f"<div style='margin-top:12px;' class='priority-dot {dot_color}'></div>", unsafe_allow_html=True)
                with col_btn:
                    if st.button(ptitle, key=f"nav_{pid}", use_container_width=True):
                        st.session_state.active_id = pid; st.session_state.view = "view_project"; st.rerun()
    
    st.divider()
    if st.button("＋ New Category", use_container_width=True):
        st.session_state.view = "create_cat"; st.rerun()
    if st.button("Logout"):
        st.session_state.logged_in = False; st.rerun()

# --- 6. PAGE ROUTING ---

if st.session_state.view == "home":
    st.markdown("<h1 style='font-size: 3rem; margin-top: 50px;'>How can I help you?</h1>", unsafe_allow_html=True)
    # UPDATED BUTTON LABEL
    if st.button("🔳 Create New Task", use_container_width=True): 
        st.session_state.view = "create_project"; st.rerun()

elif st.session_state.view == "create_project":
    st.markdown("<h2>New Task</h2>", unsafe_allow_html=True)
    user_list = [r[0] for r in c.execute("SELECT username FROM users").fetchall()]
    cat_list = [r[0] for r in c.execute("SELECT name FROM categories").fetchall()]
    
    with st.container(border=True):
        p_cat = st.selectbox("Category", cat_list if cat_list else ["General"])
        p_title = st.text_input("Project Name")
        p_user = st.selectbox("Assign to Team Member", user_list)
        p_imp = st.select_slider("Priority Level", options=["Low", "High"])
        p_details = st.text_area("Details (Markdown supported)")
        
        if st.button("Initialize Project"):
            c.execute("INSERT INTO projects (category, title, details, assigned_user, is_done, importance) VALUES (?,?,?,?,0,?)", 
                      (p_cat, p_title, p_details, p_user, p_imp))
            conn.commit(); st.session_state.view = "home"; st.rerun()

elif st.session_state.view == "view_project":
    c.execute("SELECT * FROM projects WHERE id=?", (st.session_state.active_id,))
    p = c.fetchone()
    if p:
        col_main, col_chat = st.columns([2, 1], gap="large")
        with col_main:
            st.markdown(f"<h1>{p[2]}</h1>", unsafe_allow_html=True)
            st.markdown(f"<span style='color:#a8c7fa'>📂 {p[1]} | 👤 Assigned: {p[4]}</span>", unsafe_allow_html=True)
            st.markdown("---")
            st.markdown(p[3])
        
        with col_chat:
            st.markdown("### Discussion")
            chat_box = st.container(height=450)
            with chat_box:
                msgs = c.execute("SELECT user, message, timestamp FROM comments WHERE project_id=?", (p[0],)).fetchall()
                for cu, cm, ct in msgs:
                    # FIXED FORMATTING: Using pure Markdown for clean rendering
                    st.markdown(f"**{cu}** <span style='color:grey; font-size:12px;'>{ct}</span>", unsafe_allow_html=True)
                    st.markdown(f"{cm}")
                    st.markdown("---")
            
            # Using st.chat_input for a cleaner Gemini feel
            m_input = st.chat_input("Message...")
            if m_input:
                now = datetime.now().strftime("%I:%M %p")
                c.execute("INSERT INTO comments VALUES (?,?,?,?)", (p[0], st.session_state.user_name, m_input, now))
                conn.commit(); st.rerun()

elif st.session_state.view == "create_cat":
    nc = st.text_input("New Category Name")
    if st.button("Save Category"):
        c.execute("INSERT OR IGNORE INTO categories VALUES (?)", (nc,))
        conn.commit(); st.session_state.view = "home"; st.rerun()
