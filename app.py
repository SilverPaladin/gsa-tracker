import streamlit as st
import sqlite3
from datetime import datetime
import base64
from io import BytesIO
from PIL import Image
import hashlib

# --- 1. DATABASE SETUP ---
conn = sqlite3.connect('gsa_workspace_v8.db', check_same_thread=False)
c = conn.cursor()
c.execute('CREATE TABLE IF NOT EXISTS users (email TEXT UNIQUE, password TEXT, username TEXT, role TEXT)')
c.execute('CREATE TABLE IF NOT EXISTS categories (name TEXT UNIQUE, role_required TEXT)')
c.execute('''CREATE TABLE IF NOT EXISTS projects 
             (id INTEGER PRIMARY KEY, category TEXT, title TEXT, details TEXT, 
              assigned_user TEXT, is_done INTEGER, importance TEXT, image_data TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS comments 
             (project_id INTEGER, user TEXT, message TEXT, timestamp TEXT, image_data TEXT)''')
conn.commit()

# --- 2. INITIALIZE CATEGORIES (If empty) ---
# This ensures your requested sections exist and are linked to the specific roles.
sections = {
    "Server Admin": "Server Admin",
    "Game Admin": "Game Admin",
    "Competitive Lead": "Competitive Lead",
    "Competitive Player": "Competitive Player",
    "Media Team": "Media Team",
    "Pathfinders": "Pathfinders"
}
for cat_name, role_req in sections.items():
    c.execute("INSERT OR IGNORE INTO categories (name, role_required) VALUES (?,?)", (cat_name, role_req))
conn.commit()

# --- 3. FULL-SCREEN FLAT STYLING ---
st.set_page_config(page_title="GSA Workspace", layout="wide", initial_sidebar_state="expanded")
st.markdown("""
<style>
    .main .block-container { max-width: 100vw !important; padding: 1rem 2rem !important; height: 100vh !important; }
    div[data-testid="stExpander"], .stButton>button, .stTextInput>div>div>input, 
    [data-testid="stForm"], [data-testid="stHeader"], .stTextArea>div>div>textarea,
    div[data-testid="stVerticalBlock"] > div, .stFileUploader section {
        border: none !important; box-shadow: none !important; border-radius: 0px !important; background-color: transparent !important;
    }
    [data-testid="stSidebar"] { background-color: #111 !important; border-right: none !important; }
    .stButton>button { width: 100%; text-align: left !important; background-color: rgba(255,255,255,0.02) !important; padding: 18px !important; }
    .stButton>button:hover { background-color: #222 !important; }
    .chat-line { padding: 6px 0px; font-size: clamp(16px, 1.2vw, 22px) !important; line-height: 1.2; font-weight: 600; }
    .timestamp { color: #444; font-size: 11px; margin-left: 10px; }
</style>
""", unsafe_allow_html=True)

# --- 4. UTILITIES ---
def get_user_color(username):
    hash_obj = hashlib.md5(username.lower().encode())
    return f"#{hash_obj.hexdigest()[:6]}"

# --- 5. AUTH & SESSION STATE ---
for key in ["logged_in", "role", "user_name", "view"]:
    if key not in st.session_state:
        st.session_state[key] = False if key == "logged_in" else ("home" if key == "view" else None)

if not st.session_state.logged_in:
    _, col, _ = st.columns([1, 1, 1])
    with col:
        st.markdown("<h2 style='text-align:center; margin-top:20vh;'>GSA ACCESS</h2>", unsafe_allow_html=True)
        t1, t2 = st.tabs(["SIGN IN", "REGISTER"])
        with t1:
            le, lp = st.text_input("EMAIL"), st.text_input("PASSWORD", type="password")
            if st.button("SIGN IN", use_container_width=True):
                res = c.execute("SELECT username, role FROM users WHERE email=? AND password=?", (le, lp)).fetchone()
                if res: 
                    st.session_state.update({"logged_in": True, "user_name": res[0], "role": res[1]})
                    st.rerun()
        with t2:
            nu, ne, np = st.text_input("USERNAME"), st.text_input("REG_EMAIL"), st.text_input("REG_PASSWORD", type="password")
            if st.button("CREATE ACCOUNT"):
                count = c.execute("SELECT COUNT(*) FROM users").fetchone()[0]
                role = "Super Admin" if count == 0 else "pending"
                c.execute("INSERT INTO users VALUES (?,?,?,?)", (ne, np, nu, role))
                conn.commit(); st.success(f"Registered as {role}.")
    st.stop()

# --- 6. PERMISSION LOGIC ---
user_role = st.session_state.role
is_super_admin = user_role == "Super Admin"

# --- 7. SIDEBAR (ROLE-BASED FILTERING) ---
with st.sidebar:
    st.markdown(f"### ✨ {st.session_state.user_name.lower()}")
    st.caption(f"Role: {user_role}")
    
    if user_role != "pending":
        if st.button("🏠 HOME"): st.session_state.view = "home"; st.rerun()
        
        # Super Admins see ALL categories. Others only see categories matching their role.
        if is_super_admin:
            visible_cats = c.execute("SELECT name FROM categories").fetchall()
        else:
            visible_cats = c.execute("SELECT name FROM categories WHERE role_required = ?", (user_role,)).fetchall()
        
        st.divider()
        for (cat_name,) in visible_cats:
            with st.expander(cat_name.upper(), expanded=True):
                # Buttons to view projects
                projs = c.execute("SELECT id, title FROM projects WHERE category=?", (cat_name,)).fetchall()
                for pid, ptitle in projs:
                    if st.button(ptitle, key=f"p_{pid}"):
                        st.session_state.active_id, st.session_state.view = pid, "view_project"; st.rerun()
                # Button to create task in this specific category
                if st.button(f"＋ New {cat_name} Task", key=f"add_{cat_name}"):
                    st.session_state.target_cat, st.session_state.view = cat_name, "create_project"; st.rerun()

        if is_super_admin:
            st.divider()
            if st.button("⚙️ ADMIN PANEL"): st.session_state.view = "admin_panel"; st.rerun()
    
    if st.button("🚪 LOGOUT"): st.session_state.logged_in = False; st.rerun()

# --- 8. VIEWS ---
if user_role == "pending":
    st.markdown("<h1 style='font-weight:200; margin-top:15vh;'>awaiting clearance.</h1>", unsafe_allow_html=True)

elif st.session_state.view == "admin_panel" and is_super_admin:
    st.markdown("<h1>super admin control</h1>", unsafe_allow_html=True)
    all_users = c.execute("SELECT username, email, role FROM users").fetchall()
    role_options = ["pending", "Server Admin", "Game Admin", "Competitive Lead", "Competitive Player", "Media Team", "Pathfinders", "Super Admin"]
    for u_name, u_email, u_role in all_users:
        col1, col2, col3 = st.columns([1, 1, 1])
        col1.write(f"**{u_name}** ({u_email})")
        new_role = col2.selectbox("Role", role_options, index=role_options.index(u_role), key=f"sel_{u_email}")
        if col3.button("Save", key=f"save_{u_email}"):
            c.execute("UPDATE users SET role=? WHERE email=?", (new_role, u_email))
            conn.commit(); st.rerun()

elif st.session_state.view == "create_project":
    st.markdown(f"<h1>new {st.session_state.target_cat} task</h1>", unsafe_allow_html=True)
    with st.form("new_task"):
        t = st.text_input("Title")
        d = st.text_area("Details")
        if st.form_submit_button("Initialize"):
            c.execute("INSERT INTO projects (category, title, details, assigned_user, is_done, importance) VALUES (?,?,?,?,0,?)", 
                      (st.session_state.target_cat, t, d, st.session_state.user_name, "Normal"))
            conn.commit(); st.session_state.view = "home"; st.rerun()

elif st.session_state.view == "view_project":
    p = c.execute("SELECT * FROM projects WHERE id=?", (st.session_state.active_id,)).fetchone()
    if p:
        col_m, col_c = st.columns([1, 1], gap="medium")
        with col_m:
            st.markdown(f"<h1 style='font-size: 3.5vw;'>{p[2].lower()}</h1>", unsafe_allow_html=True)
            st.caption(f"{p[1]} | {p[4]}")
            st.write(p[3])
        with col_c:
            st.markdown("### discussion")
            chat_box = st.container(height=500, border=False)
            with chat_box:
                msgs = c.execute("SELECT user, message, timestamp FROM comments WHERE project_id=?", (p[0],)).fetchall()
                for cu, cm, ct in msgs:
                    st.markdown(f"<div class='chat-line'><b style='color:{get_user_color(cu)}'>{cu.lower()}:</b> {cm} <span class='timestamp'>{ct}</span></div>", unsafe_allow_html=True)
            with st.form("chat", clear_on_submit=True):
                m = st.text_input("msg", placeholder="type...", label_visibility="collapsed")
                if st.form_submit_button("↑") and m:
                    c.execute("INSERT INTO comments (project_id, user, message, timestamp) VALUES (?,?,?,?)", 
                              (p[0], st.session_state.user_name, m, datetime.now().strftime("%H:%M")))
                    conn.commit(); st.rerun()

else:
    st.markdown("<h1 style='font-weight:200; margin-top:10vh; font-size: 5vw;'>welcome back.</h1>", unsafe_allow_html=True)
