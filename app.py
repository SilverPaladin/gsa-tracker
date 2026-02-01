import streamlit as st
import sqlite3
from datetime import datetime

# --- 1. DATABASE SETUP ---
conn = sqlite3.connect('gsa_gemini_v1.db', check_same_thread=False)
c = conn.cursor()
c.execute('CREATE TABLE IF NOT EXISTS users (email TEXT UNIQUE, password TEXT, username TEXT)')
c.execute('CREATE TABLE IF NOT EXISTS categories (name TEXT UNIQUE)')
c.execute('''CREATE TABLE IF NOT EXISTS projects 
             (id INTEGER PRIMARY KEY, category TEXT, title TEXT, details TEXT, 
              assigned_user TEXT, is_done INTEGER)''')
c.execute('CREATE TABLE IF NOT EXISTS comments (project_id INTEGER, user TEXT, message TEXT, timestamp TEXT)')
conn.commit()

# --- 2. THE GEMINI UI ENGINE (CLEAN & MODERN) ---
st.set_page_config(page_title="GSA Workspace", layout="wide")

st.markdown("""
<style>
    /* Gemini Clean Palette */
    .main { background-color: #131314; color: #e3e3e3; }
    [data-testid="stSidebar"] { background-color: #1e1f20 !important; border-right: none; }
    
    /* Typography */
    h1, h2, h3 { font-family: 'Google Sans', sans-serif; font-weight: 400 !important; letter-spacing: -0.5px; }
    
    /* Gemini Style Glass Cards */
    .gemini-card {
        background: #1e1f20;
        border-radius: 24px;
        padding: 32px;
        border: 1px solid #333537;
        transition: background 0.3s;
    }
    .gemini-card:hover { background: #28292a; }

    /* Clean Buttons / Pills */
    .stButton>button {
        border-radius: 100px !important;
        border: 1px solid #444746 !important;
        background: transparent !important;
        color: #c4c7c5 !important;
        padding: 8px 24px !important;
        transition: 0.3s;
    }
    .stButton>button:hover {
        background: #333537 !important;
        border-color: #a8c7fa !important;
        color: #a8c7fa !important;
    }

    /* Chat Bubbles - Clean Style */
    .chat-entry {
        margin-bottom: 20px;
        padding-left: 10px;
        border-left: 2px solid #333537;
    }
    .chat-user { font-weight: 500; color: #a8c7fa; font-size: 0.9em; }
    .chat-msg { color: #e3e3e3; margin-top: 4px; line-height: 1.5; }
    
    /* Sidebar Project Items */
    .nav-item { padding: 10px; border-radius: 12px; margin-bottom: 4px; cursor: pointer; }
    .nav-item:hover { background: #333537; }
</style>
""", unsafe_allow_html=True)

# --- 3. SESSION STATE ---
if "logged_in" not in st.session_state: st.session_state.logged_in = False
if "view" not in st.session_state: st.session_state.view = "home"
if "user_name" not in st.session_state: st.session_state.user_name = "User"

# --- 4. AUTHENTICATION (CLEAN MODAL) ---
if not st.session_state.logged_in:
    _, col, _ = st.columns([1, 1.5, 1])
    with col:
        st.markdown("<h2 style='text-align:center; margin-top:100px;'>Sign in</h2>", unsafe_allow_html=True)
        tab1, tab2 = st.tabs(["Login", "Create Identity"])
        with tab1:
            le = st.text_input("Email", placeholder="name@company.com")
            lp = st.text_input("Password", type="password")
            if st.button("Continue"):
                c.execute("SELECT username FROM users WHERE email=? AND password=?", (le, lp))
                res = c.fetchone()
                if res:
                    st.session_state.logged_in = True
                    st.session_state.user_name = res[0]
                    st.rerun()
        with tab2:
            nu = st.text_input("Display Name")
            ne = st.text_input("Email")
            np = st.text_input("Create Password", type="password")
            if st.button("Initialize"):
                try:
                    c.execute("INSERT INTO users VALUES (?,?,?)", (ne, np, nu))
                    conn.commit(); st.success("Ready to login.")
                except: st.error("Email taken.")
    st.stop()

# --- 5. SIDEBAR ---
with st.sidebar:
    st.markdown(f"<h3 style='padding-left:10px;'>Hello, {st.session_state.user_name}</h3>", unsafe_allow_html=True)
    if st.button("➕ New Chat / Project"): st.session_state.view = "create_project"; st.rerun()
    st.divider()
    
    c.execute("SELECT name FROM categories")
    for cat in c.fetchall():
        with st.expander(cat[0], expanded=True):
            c.execute("SELECT id, title FROM projects WHERE category=?", (cat[0],))
            for pid, ptitle in c.fetchall():
                if st.button(f"📄 {ptitle}", key=f"p_{pid}", help="Open project details"):
                    st.session_state.active_id = pid; st.session_state.view = "view_project"; st.rerun()
    
    st.divider()
    if st.button("⚙️ Settings"): st.session_state.view = "settings"; st.rerun()
    if st.button("Logout"): st.session_state.logged_in = False; st.rerun()

# --- 6. MAIN CONTENT ---

# 6a. HOME (GEMINI SPLASH)
if st.session_state.view == "home":
    st.markdown("<h1 style='font-size: 3rem; margin-top: 50px;'>How can I help you today?</h1>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("<div class='gemini-card'><h4>Create Task</h4><p style='color:#8e918f'>Start a new workflow pipeline.</p></div>", unsafe_allow_html=True)
        if st.button("Launch", key="h1"): st.session_state.view = "create_project"; st.rerun()
    with col2:
        st.markdown("<div class='gemini-card'><h4>Categories</h4><p style='color:#8e918f'>Organize your workspace tags.</p></div>", unsafe_allow_html=True)
        if st.button("Manage", key="h2"): st.session_state.view = "create_cat"; st.rerun()
    with col3:
        st.markdown("<div class='gemini-card'><h4>View All</h4><p style='color:#8e918f'>Check recent activity logs.</p></div>", unsafe_allow_html=True)
        if st.button("Explore", key="h3"): st.toast("Use the sidebar to explore.")

# 6b. VIEW PROJECT & CHAT
elif st.session_state.view == "view_project":
    c.execute("SELECT * FROM projects WHERE id=?", (st.session_state.active_id,))
    p = c.fetchone()
    if p:
        col_main, col_chat = st.columns([2, 1], gap="large")
        
        with col_main:
            st.markdown(f"<h1>{p[2]}</h1>", unsafe_allow_html=True)
            st.markdown(f"<span style='color:#a8c7fa'>Category: {p[1]}</span>", unsafe_allow_html=True)
            st.write(p[3]) # Project Details
            if st.button("Mark as Complete"):
                c.execute("UPDATE projects SET is_done=1 WHERE id=?", (p[0],))
                conn.commit(); st.rerun()

        with col_chat:
            st.markdown("<h3 style='margin-bottom:20px;'>Activity Feed</h3>", unsafe_allow_html=True)
            chat_container = st.container(height=500, border=False)
            with chat_container:
                c.execute("SELECT user, message, timestamp FROM comments WHERE project_id=?", (p[0],))
                for c_u, c_m, c_t in c.fetchall():
                    st.markdown(f"<div class='chat-entry'><div class='chat-user'>{c_u} <span style='color:#72767d; font-size:0.8em;'>{c_t}</span></div><div class='chat-msg'>{c_m}</div></div>", unsafe_allow_html=True)
            
            with st.chat_message("user"):
                m = st.text_input("Enter a message...", label_visibility="collapsed")
                if st.button("Send Message"):
                    t = datetime.now().strftime("%I:%M %p")
                    c.execute("INSERT INTO comments VALUES (?,?,?,?)", (p[0], st.session_state.user_name, m, t))
                    conn.commit(); st.rerun()

# 6c. CREATION SCREENS
elif st.session_state.view == "create_project":
    st.markdown("<h2>New Project</h2>", unsafe_allow_html=True)
    with st.container(border=True):
        cat = st.selectbox("Category", [r[0] for r in c.execute("SELECT name FROM categories").fetchall()] + ["General"])
        title = st.text_input("Project Name")
        details = st.text_area("Details")
        if st.button("Create Project"):
            c.execute("INSERT INTO projects (category, title, details, assigned_user, is_done) VALUES (?,?,?,?,0)", (cat, title, details, st.session_state.user_name))
            conn.commit(); st.session_state.view = "home"; st.rerun()

elif st.session_state.view == "create_cat":
    st.markdown("<h2>New Category</h2>", unsafe_allow_html=True)
    new_cat = st.text_input("Category Name")
    if st.button("Save Category"):
        c.execute("INSERT OR IGNORE INTO categories VALUES (?)", (new_cat,))
        conn.commit(); st.session_state.view = "home"; st.rerun()
