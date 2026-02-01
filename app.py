import streamlit as st
import sqlite3
from datetime import datetime
import base64
from io import BytesIO
from PIL import Image
import hashlib

# --- 1. DATABASE SETUP ---
conn = sqlite3.connect('gsa_gemini_v6.db', check_same_thread=False)
c = conn.cursor()
c.execute('CREATE TABLE IF NOT EXISTS users (email TEXT UNIQUE, password TEXT, username TEXT)')
c.execute('CREATE TABLE IF NOT EXISTS categories (name TEXT UNIQUE)')
c.execute('''CREATE TABLE IF NOT EXISTS projects 
             (id INTEGER PRIMARY KEY, category TEXT, title TEXT, details TEXT, 
              assigned_user TEXT, is_done INTEGER, importance TEXT, image_data TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS comments 
             (project_id INTEGER, user TEXT, message TEXT, timestamp TEXT, image_data TEXT)''')
conn.commit()

# --- 2. CLEAN RECTANGULAR UI STYLING ---
st.set_page_config(page_title="GSA Workspace", layout="wide")
st.markdown("""
<style>
    /* Dark Theme Base */
    .main { background-color: #131314; color: #e3e3e3; font-family: 'Inter', sans-serif; }
    [data-testid="stSidebar"] { background-color: #1e1f20 !important; border-right: 1px solid #333 !important; }

    /* Remove Bubbles: Clean Rectangles */
    div[data-testid="stExpander"], .stButton>button, .stTextInput>div>div>input, [data-testid="stForm"] {
        border-radius: 0px !important; /* Sharp corners */
        border: 1px solid #333537 !important;
    }

    /* Hover Effects for Sidebar Rectangles */
    .stButton>button {
        width: 100%;
        text-align: left !important;
        background-color: transparent !important;
        padding: 10px 15px !important;
        transition: background-color 0.2s ease;
    }
    .stButton>button:hover {
        background-color: #333537 !important; /* Highlight on hover */
        border-color: #444 !important;
    }

    /* Importance Dots */
    .priority-dot { height: 8px; width: 8px; border-radius: 50%; display: inline-block; margin-right: 10px; }
    .dot-Critical { background-color: #ff4b4b; box-shadow: 0 0 5px #ff4b4b; } 
    .dot-High     { background-color: #ffa500; } 
    .dot-Medium   { background-color: #00d4ff; } 
    .dot-Low      { background-color: #4b89ff; }

    /* Condensed Chat - Zero Erroneous Spacing */
    .chat-container { display: flex; flex-direction: column; gap: 0px; }
    .chat-line { 
        padding: 2px 0px; 
        font-size: 14px; 
        line-height: 1.1; 
        border-bottom: 1px solid rgba(255,255,255,0.02);
    }
    .timestamp { color: #5f6368; font-size: 10px; margin-left: 5px; }
</style>
""", unsafe_allow_html=True)

# --- 3. UTILITIES ---
def img_to_base64(image):
    buffered = BytesIO()
    image.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode()

def get_user_color(username):
    hash_obj = hashlib.md5(username.encode())
    return f"#{hash_obj.hexdigest()[:6]}"

# --- 4. AUTHENTICATION ---
if "logged_in" not in st.session_state: st.session_state.logged_in = False
if "view" not in st.session_state: st.session_state.view = "home"

if not st.session_state.logged_in:
    _, col, _ = st.columns([1, 1.2, 1])
    with col:
        st.markdown("<h2 style='text-align:center;'>GSA Login</h2>", unsafe_allow_html=True)
        le = st.text_input("Email", key="l_e")
        lp = st.text_input("Password", type="password", key="l_p")
        if st.button("Sign In"):
            res = c.execute("SELECT username FROM users WHERE email=? AND password=?", (le, lp)).fetchone()
            if res: 
                st.session_state.logged_in, st.session_state.user_name = True, res[0]
                st.rerun()
    st.stop()

# --- 5. CLEAN SIDEBAR ---
with st.sidebar:
    st.markdown(f"### ✨ {st.session_state.user_name.lower()}")
    st.button("＋ Create New Task", on_click=lambda: st.session_state.update({"view": "create_project"}))
    st.button("🏠 Home", on_click=lambda: st.session_state.update({"view": "home"}))
    st.divider()
    
    cats = [r[0] for r in c.execute("SELECT name FROM categories").fetchall()]
    for cat in cats:
        with st.expander(cat.upper(), expanded=True):
            projs = c.execute("SELECT id, title, importance FROM projects WHERE category=?", (cat,)).fetchall()
            for pid, ptitle, pimp in projs:
                dot = f"<span class='priority-dot dot-{pimp}'></span>"
                if st.button(f"{ptitle}", key=f"p_{pid}"):
                    st.session_state.active_id, st.session_state.view = pid, "view_project"
                    st.rerun()
    
    st.divider()
    if st.button("＋ Manage Categories"): 
        st.session_state.view = "create_cat"; st.rerun()

# --- 6. PAGE VIEWS ---
if st.session_state.view == "home":
    st.markdown("<h1 style='font-weight:400; margin-top:50px;'>Workspace Dashboard</h1>", unsafe_allow_html=True)

elif st.session_state.view == "view_project":
    p = c.execute("SELECT * FROM projects WHERE id=?", (st.session_state.active_id,)).fetchone()
    if p:
        col_m, col_c = st.columns([1.5, 1.5], gap="large")
        with col_m:
            st.markdown(f"<h2>{p[2]}</h2>", unsafe_allow_html=True)
            st.caption(f"{p[1]} | Assigned to {p[4]}")
            st.write(p[3])
            if p[7]: st.image(f"data:image/png;base64,{p[7]}")
        
        with col_c:
            st.markdown("### Discussion")
            # Scrollable chat area
            chat_h = st.container(height=500, border=False)
            with chat_h:
                msgs = c.execute("SELECT user, message, timestamp, image_data FROM comments WHERE project_id=?", (p[0],)).fetchall()
                for cu, cm, ct, ci in msgs:
                    clr = get_user_color(cu)
                    # Compressed line: Username: Message [Time]
                    st.markdown(f"<div class='chat-line'><b style='color:{clr}'>{cu.lower()}:</b> {cm if cm else ''} <span class='timestamp'>{ct}</span></div>", unsafe_allow_html=True)
                    if ci: st.image(f"data:image/png;base64,{ci}", width=200)

            # Fixed Bottom Input
            with st.container():
                with st.form("chat_form", clear_on_submit=True):
                    up = st.file_uploader("Upload", type=['png','jpg','jpeg'], label_visibility="collapsed")
                    c1, c2 = st.columns([0.85, 0.15])
                    msg = c1.text_input("Msg", placeholder="Type message...", label_visibility="collapsed")
                    if c2.form_submit_button("Send"):
                        if msg or up:
                            b64 = img_to_base64(Image.open(up)) if up else None
                            c.execute("INSERT INTO comments VALUES (?,?,?,?,?)", 
                                      (p[0], st.session_state.user_name, msg, datetime.now().strftime("%H:%M"), b64))
                            conn.commit(); st.rerun()

elif st.session_state.view == "create_project":
    st.markdown("<h2>New Task</h2>", unsafe_allow_html=True)
    with st.form("new_proj"):
        t = st.text_input("Title")
        d = st.text_area("Details")
        imp = st.select_slider("Importance", options=["Low", "Medium", "High", "Critical"])
        if st.form_submit_button("Create"):
            c.execute("INSERT INTO projects (category, title, details, assigned_user, is_done, importance) VALUES (?,?,?,?,0,?)", 
                      ("General", t, d, st.session_state.user_name, imp))
            conn.commit(); st.session_state.view = "home"; st.rerun()
