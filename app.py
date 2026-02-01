import streamlit as st
import sqlite3
from datetime import datetime

# --- DATABASE SETUP ---
conn = sqlite3.connect('gsa_master_v1.db', check_same_thread=False)
c = conn.cursor()
c.execute('CREATE TABLE IF NOT EXISTS users (email TEXT UNIQUE, password TEXT, username TEXT)')
c.execute('CREATE TABLE IF NOT EXISTS categories (name TEXT UNIQUE)')
c.execute('''CREATE TABLE IF NOT EXISTS projects 
             (id INTEGER PRIMARY KEY, category TEXT, title TEXT, details TEXT, 
              assigned_user TEXT, is_done INTEGER)''')
conn.commit()

# --- THE "CHIC" CSS ---
st.markdown("""
<style>
    .main { background: #000000; color: white; }
    [data-testid="stSidebar"] { 
        background-color: rgba(255, 255, 255, 0.03) !important; 
        backdrop-filter: blur(25px);
        border-right: 1px solid rgba(255, 255, 255, 0.1);
    }
    .glass-tile {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(15px);
        border-radius: 25px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 40px 20px;
        text-align: center;
    }
    .stButton>button {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        color: white;
        border-radius: 12px;
    }
    .cat-header { color: #8e9297; font-size: 11px; font-weight: 800; text-transform: uppercase; margin-top: 20px; }
</style>
""", unsafe_allow_html=True)

# --- SESSION STATE ---
if "logged_in" not in st.session_state: st.session_state.logged_in = False
if "user_name" not in st.session_state: st.session_state.user_name = "User"
if "view" not in st.session_state: st.session_state.view = "home"

# --- SIDEBAR (DISCORD STYLE) ---
if st.session_state.logged_in:
    with st.sidebar:
        st.markdown(f"<h2 style='font-weight:100;'>{st.session_state.user_name}</h2>", unsafe_allow_html=True)
        if st.button("🏠 Home Dashboard"): st.session_state.view = "home"; st.rerun()
        if st.button("⚙️ Account Settings"): st.session_state.view = "settings"; st.rerun()
        st.divider()
        
        # Category Management
        st.markdown("<div class='cat-header'>Categories</div>", unsafe_allow_html=True)
        c.execute("SELECT name FROM categories")
        all_cats = [r[0] for r in c.fetchall()]
        for cat in all_cats:
            col_a, col_b = st.columns([4,1])
            with col_a: st.write(f"📁 {cat}")
            with col_b: 
                if st.button("＋", key=f"add_{cat}"):
                    st.session_state.view = "create_project"
                    st.session_state.target_cat = cat
                    st.rerun()
            
            # Show Projects under Category
            c.execute("SELECT id, title, is_done FROM projects WHERE category=?", (cat,))
            for pid, ptitle, pdone in c.fetchall():
                icon = "✅" if pdone else "#"
                if st.button(f"{icon} {ptitle}", key=f"p_{pid}"):
                    st.session_state.view = "view_project"
                    st.session_state.active_id = pid
                    st.rerun()
        
        if st.button("＋ New Category", type="secondary"):
            st.session_state.view = "create_category"; st.rerun()

# --- PAGE ROUTING ---
if not st.session_state.logged_in:
    # Minimalist Chic Login
    st.markdown("<h1 style='text-align:center; font-weight:100; margin-top:100px;'>GSA SECURE</h1>", unsafe_allow_html=True)
    e = st.text_input("Email")
    p = st.text_input("Password", type="password")
    if st.button("Unlock System"):
        # For now, let's bypass to let you see the work
        st.session_state.logged_in = True
        st.rerun()

elif st.session_state.view == "home":
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown(f"<h1 style='text-align:center; font-weight:100; font-size:60px;'>Welcome, {st.session_state.user_name}</h1>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2, gap="large")
    with col1:
        st.markdown("<div class='glass-tile'><h1>🔳</h1><h3>Initiate Task</h3></div>", unsafe_allow_html=True)
        if st.button("Launch Pipeline", use_container_width=True): 
            st.session_state.view = "create_project"; st.rerun()
    with col2:
        st.markdown("<div class='glass-tile'><h1>📂</h1><h3>Active Archive</h3></div>", unsafe_allow_html=True)
        if st.button("Browse Vault", use_container_width=True): 
            st.toast("Select a project from the sidebar!")

elif st.session_state.view == "create_category":
    name = st.text_input("New Category Name")
    if st.button("Save"):
        c.execute("INSERT OR IGNORE INTO categories VALUES (?)", (name,))
        conn.commit()
        st.session_state.view = "home"; st.rerun()

elif st.session_state.view == "create_project":
    cat = st.session_state.get("target_cat", "General")
    st.title(f"New Task: {cat}")
    title = st.text_input("Project Name")
    details = st.text_area("Project Details", placeholder="Bullet points and bold text work here...")
    user = st.text_input("Assign to User")
    if st.button("Create"):
        c.execute("INSERT INTO projects (category, title, details, assigned_user, is_done) VALUES (?,?,?,?,0)", 
                  (cat, title, details, user))
        conn.commit()
        st.session_state.view = "home"; st.rerun()

elif st.session_state.view == "view_project":
    c.execute("SELECT * FROM projects WHERE id=?", (st.session_state.active_id,))
    p = c.fetchone()
    if p:
        st.title(p[2])
        st.caption(f"Category: {p[1]} | Assigned: {p[4]}")
        st.markdown("---")
        st.markdown("### Project Details")
        st.markdown(p[3]) # This shows your formatting
        if not p[5]:
            if st.button("Mark as Done"):
                c.execute("UPDATE projects SET is_done=1 WHERE id=?", (p[0],))
                conn.commit()
                st.rerun()
