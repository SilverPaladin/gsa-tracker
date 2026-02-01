import streamlit as st
import sqlite3
from datetime import datetime
import base64
from io import BytesIO
from PIL import Image
import hashlib

# --- 1. DATABASE SETUP ---
conn = sqlite3.connect('gsa_workspace_v11.db', check_same_thread=False)
c = conn.cursor()
c.execute('CREATE TABLE IF NOT EXISTS users (email TEXT UNIQUE, password TEXT, username TEXT, role TEXT)')
c.execute('CREATE TABLE IF NOT EXISTS categories (name TEXT UNIQUE, role_required TEXT, sort_order INTEGER)')
c.execute('''CREATE TABLE IF NOT EXISTS projects 
             (id INTEGER PRIMARY KEY, category TEXT, title TEXT, details TEXT, 
              assigned_user TEXT, is_done INTEGER, importance TEXT, image_data TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS comments 
             (project_id INTEGER, user TEXT, message TEXT, timestamp TEXT, image_data TEXT)''')
conn.commit()

# --- 2. INITIALIZE CATEGORIES ---
sections = ["Server Admin", "Game Admin", "Competitive Lead", "Competitive Player", "Media Team", "Pathfinders"]
for i, name in enumerate(sections):
    c.execute("INSERT OR IGNORE INTO categories (name, role_required, sort_order) VALUES (?,?,?)", (name, name, i))
conn.commit()

# --- 3. CSS: FLAT DESIGN & STATUS LIGHTS ---
st.set_page_config(page_title="GSA Workspace", layout="wide", initial_sidebar_state="expanded")
st.markdown("""
<style>
    .main .block-container { max-width: 100vw !important; padding: 1rem 2rem !important; }
    .status-light { height: 8px; width: 8px; border-radius: 50%; display: inline-block; margin-right: 12px; box-shadow: 0 0 5px currentColor; }
    .light-low      { color: #0088ff; background-color: #0088ff; }
    .light-medium   { color: #00ff88; background-color: #00ff88; }
    .light-high     { color: #ffaa00; background-color: #ffaa00; }
    .light-critical { color: #ff4444; background-color: #ff4444; }
    [data-testid="stSidebar"] { background-color: #111 !important; border-right: none !important; }
    .stButton>button { 
        width: 100%; text-align: left !important; 
        background-color: rgba(255,255,255,0.02) !important; 
        padding: 12px 15px !important; border: none !important; border-radius: 0px !important;
    }
    .stButton>button:hover { background-color: #222 !important; }
    .chat-line { padding: 6px 0px; font-size: 18px !important; font-weight: 600; }
    .timestamp { color: #444; font-size: 11px; margin-left: 10px; }
</style>
""", unsafe_allow_html=True)

# --- 4. UTILITIES ---
def img_to_base64(image):
    buffered = BytesIO()
    image.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode()

def get_user_color(username):
    hash_obj = hashlib.md5(username.lower().encode())
    return f"#{hash_obj.hexdigest()[:6]}"

# --- 5. AUTHENTICATION ---
if "logged_in" not in st.session_state: st.session_state.logged_in = False
if "view" not in st.session_state: st.session_state.view = "home"

if not st.session_state.logged_in:
    _, col, _ = st.columns([1, 1.2, 1])
    with col:
        st.markdown("<h2 style='text-align:center; margin-top:15vh;'>GSA ACCESS</h2>", unsafe_allow_html=True)
        auth_tab1, auth_tab2 = st.tabs(["SIGN IN", "CREATE ACCOUNT"])
        
        with auth_tab1:
            login_email = st.text_input("EMAIL", key="log_e").strip().lower()
            login_pass = st.text_input("PASSWORD", type="password", key="log_p")
            if st.button("UNLOCK", use_container_width=True):
                user_res = c.execute("SELECT username, role FROM users WHERE email=? AND password=?", (login_email, login_pass)).fetchone()
                if user_res:
                    st.session_state.logged_in = True
                    st.session_state.user_name = user_res[0]
                    st.session_state.role = user_res[1]
                    st.rerun()
                else: st.error("Invalid credentials.")
        
        with auth_tab2:
            new_user = st.text_input("USERNAME", key="reg_u")
            new_email = st.text_input("EMAIL", key="reg_e").strip().lower()
            new_pass = st.text_input("PASSWORD", type="password", key="reg_p")
            if st.button("REGISTER", use_container_width=True):
                if new_user and new_email and new_pass:
                    try:
                        # SUPER ADMIN CHECK: Only your email gets the crown
                        assigned_role = "Super Admin" if new_email == "armasupplyguy@gmail.com" else "pending"
                        c.execute("INSERT INTO users VALUES (?,?,?,?)", (new_email, new_pass, new_user, assigned_role))
                        conn.commit()
                        st.success(f"Registered as {assigned_role}. Please sign in.")
                    except sqlite3.IntegrityError:
                        st.error("Email already in use.")
                else: st.warning("Please fill all fields.")
    st.stop()

# --- 6. PERMISSIONS & SIDEBAR ---
user_role = st.session_state.role
is_super = user_role == "Super Admin"

with st.sidebar:
    st.markdown(f"### ✨ {st.session_state.user_name.lower()}")
    st.caption(f"Role: {user_role}")
    
    if user_role != "pending":
        if st.button("🏠 HOME"): st.session_state.view = "home"; st.rerun()
        
        cats = c.execute("SELECT name FROM categories ORDER BY sort_order ASC").fetchall() if is_super else \
               c.execute("SELECT name FROM categories WHERE role_required=? ORDER BY sort_order ASC", (user_role,)).fetchall()

        st.divider()
        for (cat_name,) in cats:
            with st.expander(cat_name.upper(), expanded=True):
                projs = c.execute("SELECT id, title, importance FROM projects WHERE category=?", (cat_name,)).fetchall()
                for pid, ptitle, pimp in projs:
                    light_class = f"light-{pimp.lower()}"
                    col_l, col_b = st.columns([0.15, 0.85])
                    col_l.markdown(f'<div style="margin-top:16px" class="status-light {light_class}"></div>', unsafe_allow_html=True)
                    if col_b.button(ptitle, key=f"p_{pid}"):
                        st.session_state.active_id, st.session_state.view = pid, "view_project"; st.rerun()
                
                if st.button(f"＋ NEW TASK", key=f"add_{cat_name}"):
                    st.session_state.target_cat, st.session_state.view = cat_name, "create_project"; st.rerun()

    if is_super:
        st.divider()
        if st.button("⚙️ ADMIN CONTROL"): st.session_state.view = "admin_panel"; st.rerun()
    
    if st.button("🚪 LOGOUT"):
        st.session_state.logged_in = False
        st.rerun()

# --- 7. MAIN VIEWS ---
if user_role == "pending":
    st.markdown("<h1 style='font-weight:200; margin-top:15vh;'>access restricted.</h1>", unsafe_allow_html=True)
    st.write(f"Account ({st.session_state.user_name}) is pending admin approval.")

elif st.session_state.view == "admin_panel" and is_super:
    st.markdown("<h1>control panel</h1>", unsafe_allow_html=True)
    t1, t2 = st.tabs(["USER ROLES", "ARRANGE CATEGORIES"])
    with t1:
        users_list = c.execute("SELECT username, email, role FROM users").fetchall()
        role_opts = ["pending", "Server Admin", "Game Admin", "Competitive Lead", "Competitive Player", "Media Team", "Pathfinders", "Super Admin"]
        for un, ue, ur in users_list:
            c1, c2, c3 = st.columns([1,1,1])
            c1.write(f"**{un}**\n{ue}")
            nr = c2.selectbox("Role", role_opts, index=role_opts.index(ur), key=f"r_{ue}")
            if c3.button("Save", key=f"u_{ue}"):
                c.execute("UPDATE users SET role=? WHERE email=?", (nr, ue)); conn.commit(); st.rerun()
    with t2:
        all_cats = c.execute("SELECT name, sort_order FROM categories ORDER BY sort_order ASC").fetchall()
        for cn, co in all_cats:
            col1, col2 = st.columns([0.8, 0.2])
            col1.write(f"**{cn}**")
            new_ord = col2.number_input("Order", value=co, key=f"ord_{cn}", step=1)
            if new_ord != co:
                c.execute("UPDATE categories SET sort_order=? WHERE name=?", (new_ord, cn)); conn.commit(); st.rerun()

elif st.session_state.view == "create_project":
    st.markdown(f"<h1>new {st.session_state.target_cat.lower()} task</h1>", unsafe_allow_html=True)
    with st.form("new_task_f"):
        t_input, s_input = st.text_input("Title"), st.selectbox("Severity", ["Low", "Medium", "High", "Critical"])
        d_input, i_file = st.text_area("Details"), st.file_uploader("Photo", type=['png', 'jpg', 'jpeg'])
        if st.form_submit_button("Initialize Task"):
            b64 = img_to_base64(Image.open(i_file)) if i_file else None
            c.execute("INSERT INTO projects (category, title, details, assigned_user, is_done, importance, image_data) VALUES (?,?,?,?,0,?,?)",
                      (st.session_state.target_cat, t_input, d_input, st.session_state.user_name, s_input, b64))
            conn.commit(); st.session_state.view = "home"; st.rerun()

elif st.session_state.view == "view_project":
    p_data = c.execute("SELECT * FROM projects WHERE id=?", (st.session_state.active_id,)).fetchone()
    if p_data:
        col_m, col_c = st.columns([1, 1], gap="large")
        with col_m:
            st.markdown(f"<h1>{p_data[2].lower()}</h1>", unsafe_allow_html=True)
            st.write(p_data[3])
            if p_data[7]: st.image(f"data:image/png;base64,{p_data[7]}", use_container_width=True)
        with col_c:
            st.markdown("### discussion")
            chat_h = st.container(height=500, border=False)
            with chat_h:
                msgs = c.execute("SELECT user, message, timestamp FROM comments WHERE project_id=?", (p_data[0],)).fetchall()
                for cu, cm, ct in msgs:
                    st.markdown(f"<div class='chat-line'><b style='color:{get_user_color(cu)}'>{cu.lower()}:</b> {cm} <span class='timestamp'>{ct}</span></div>", unsafe_allow_html=True)
            with st.form("chat_f"):
                msg_in = st.text_input("msg", placeholder="type...", label_visibility="collapsed")
                if st.form_submit_button("↑") and msg_in:
                    c.execute("INSERT INTO comments (project_id, user, message, timestamp) VALUES (?,?,?,?)", 
                              (p_data[0], st.session_state.user_name, msg_in, datetime.now().strftime("%H:%M")))
                    conn.commit(); st.rerun()
else:
    st.markdown("<h1 style='font-weight:200; margin-top:10vh; font-size: 5vw;'>welcome back.</h1>", unsafe_allow_html=True)
