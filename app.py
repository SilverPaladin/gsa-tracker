import streamlit as st
import sqlite3
from datetime import datetime

# --- 1. DATABASE SETUP ---
conn = sqlite3.connect('gsa_gemini_final.db', check_same_thread=False)
c = conn.cursor()
c.execute('CREATE TABLE IF NOT EXISTS users (email TEXT UNIQUE, password TEXT, username TEXT)')
c.execute('CREATE TABLE IF NOT EXISTS categories (name TEXT UNIQUE)')
c.execute('''CREATE TABLE IF NOT EXISTS projects 
             (id INTEGER PRIMARY KEY, category TEXT, title TEXT, details TEXT, 
              assigned_user TEXT, is_done INTEGER)''')
c.execute('CREATE TABLE IF NOT EXISTS comments (project_id INTEGER, user TEXT, message TEXT, timestamp TEXT)')
conn.commit()

# --- 2. THE GEMINI UI ENGINE ---
st.set_page_config(page_title="GSA Workspace", layout="wide")

st.markdown("""
<style>
    .main { background-color: #131314; color: #e3e3e3; }
    [data-testid="stSidebar"] { background-color: #1e1f20 !important; border-right: none; }
    
    /* Gemini Input Styling */
    .stTextInput>div>div>input, .stTextArea>div>textarea, .stSelectbox>div>div>div {
        background-color: #1e1f20 !important;
        color: #e3e3e3 !important;
        border-radius: 12px !important;
        border: 1px solid #444746 !important;
    }

    /* Side Chat Feed */
    .chat-bubble {
        background: #1e1f20;
        border-radius: 16px;
        padding: 12px 16px;
        margin-bottom: 12px;
        border: 1px solid #333537;
    }
    .chat-user { color: #a8c7fa; font-weight: 500; font-size: 0.85rem; }
</style>
""", unsafe_allow_html=True)

# --- 3. SESSION STATE ---
if "logged_in" not in st.session_state: st.session_state.logged_in = False
if "view" not in st.session_state: st.session_state.view = "home"
if "user_name" not in st.session_state: st.session_state.user_name = "User"

# --- 4. AUTHENTICATION (Simplified for functionality) ---
if not st.session_state.logged_in:
    _, col, _ = st.columns([1, 1.5, 1])
    with col:
        st.markdown("<h2 style='text-align:center; margin-top:80px;'>GSA Secure Login</h2>", unsafe_allow_html=True)
        tab1, tab2 = st.tabs(["Login", "Register"])
        with tab1:
            le = st.text_input("Email")
            lp = st.text_input("Password", type="password")
            if st.button("Continue"):
                c.execute("SELECT username FROM users WHERE email=? AND password=?", (le, lp))
                res = c.fetchone()
                if res:
                    st.session_state.logged_in = True
                    st.session_state.user_name = res[0]
                    st.rerun()
        with tab2:
            nu = st.text_input("Display Name (One Word)")
            ne = st.text_input("Email Address")
            np = st.text_input("Choose Password", type="password")
            if st.button("Initialize Identity"):
                try:
                    c.execute("INSERT INTO users VALUES (?,?,?)", (ne, np, nu))
                    conn.commit(); st.success("Initialized. Now Login.")
                except: st.error("User already exists.")
    st.stop()

# --- 5. SIDEBAR ---
with st.sidebar:
    st.markdown(f"### ✨ {st.session_state.user_name}")
    if st.button("🏠 Home Dashboard", use_container_width=True): 
        st.session_state.view = "home"; st.rerun()
    
    st.divider()
    st.caption("WORKSPACE ARCHIVE")
    
    # Get categories
    c.execute("SELECT name FROM categories")
    cats = [r[0] for r in c.fetchall()]
    
    for cat in cats:
        with st.expander(f"📁 {cat}", expanded=True):
            c.execute("SELECT id, title FROM projects WHERE category=?", (cat,))
            for pid, ptitle in c.fetchall():
                if st.button(f"📄 {ptitle}", key=f"nav_{pid}"):
                    st.session_state.active_id = pid
                    st.session_state.view = "view_project"
                    st.rerun()
    
    st.divider()
    if st.button("＋ New Category", use_container_width=True):
        st.session_state.view = "create_cat"; st.rerun()
    if st.button("Logout", type="secondary"):
        st.session_state.logged_in = False; st.rerun()

# --- 6. PAGE ROUTING ---

# 6a. HOME (GEMINI SPLASH)
if st.session_state.view == "home":
    st.markdown("<h1 style='font-size: 3rem; margin-top: 50px;'>How can I help you today?</h1>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔳 Create New Task", use_container_width=True):
            st.session_state.view = "create_project"; st.rerun()
    with col2:
        if st.button("📂 Manage Categories", use_container_width=True):
            st.session_state.view = "create_cat"; st.rerun()

# 6b. VIEW PROJECT & SIDE CHAT
elif st.session_state.view == "view_project":
    c.execute("SELECT * FROM projects WHERE id=?", (st.session_state.active_id,))
    p = c.fetchone()
    if p:
        col_main, col_chat = st.columns([2, 1], gap="large")
        
        with col_main:
            st.markdown(f"<h1>{p[2]}</h1>", unsafe_allow_html=True)
            st.markdown(f"<span style='color:#a8c7fa'>📂 {p[1]} | 👤 Assigned: {p[4]}</span>", unsafe_allow_html=True)
            st.markdown("---")
            st.markdown("### Project Details")
            st.markdown(p[3]) # Details with markdown
            if st.button("Mark Complete"):
                c.execute("UPDATE projects SET is_done=1 WHERE id=?", (p[0],))
                conn.commit(); st.rerun()

        with col_chat:
            st.markdown("### Discussion")
            chat_box = st.container(height=500, border=False)
            with chat_box:
                c.execute("SELECT user, message, timestamp FROM comments WHERE project_id=?", (p[0],))
                for c_u, c_m, c_t in c.fetchall():
                    st.markdown(f"<div class='chat-bubble'><div class='chat-user'>{c_u} • {c_t}</div>{c_m}</div>", unsafe_allow_html=True)
            
            with st.form("msg_form", clear_on_submit=True):
                m = st.text_input("Message...", label_visibility="collapsed")
                if st.form_submit_button("Send"):
                    if m:
                        t = datetime.now().strftime("%I:%M %p")
                        c.execute("INSERT INTO comments VALUES (?,?,?,?)", (p[0], st.session_state.user_name, m, t))
                        conn.commit(); st.rerun()

# 6c. CREATION SCREENS (RESTORED FEATURES)
elif st.session_state.view == "create_project":
    st.markdown("<h2>Initiate New Project</h2>", unsafe_allow_html=True)
    with st.container(border=True):
        # RESTORED: Category Selection
        c.execute("SELECT name FROM categories")
        cat_options = [r[0] for r in c.fetchall()]
        p_cat = st.selectbox("Assign to Category", cat_options if cat_options else ["General"])
        
        p_title = st.text_input("Project Name")
        p_details = st.text_area("Project Details (Markdown supported)")
        
        # RESTORED: User Assignment
        c.execute("SELECT username FROM users")
        user_options = [r[0] for r in c.fetchall()]
        p_user = st.selectbox("Assign User Responsibility", ["Unassigned"] + user_options)
        
        if st.button("Create Pipeline"):
            c.execute("INSERT INTO projects (category, title, details, assigned_user, is_done) VALUES (?,?,?,?,0)", 
                      (p_cat, p_title, p_details, p_user))
            conn.commit(); st.session_state.view = "home"; st.rerun()

elif st.session_state.view == "create_cat":
    st.markdown("<h2>Workspace Organization</h2>", unsafe_allow_html=True)
    nc = st.text_input("New Category Name")
    if st.button("Save Category"):
        c.execute("INSERT OR IGNORE INTO categories VALUES (?)", (nc,))
        conn.commit(); st.session_state.view = "home"; st.rerun()
