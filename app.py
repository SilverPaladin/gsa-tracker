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

# --- 2. FULL-SCREEN FLAT STYLING ---
st.set_page_config(page_title="GSA Workspace", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
    /* 100% Height and Width Reset */
    .main .block-container {
        max-width: 100% !important;
        padding: 1rem 2rem !important;
        height: 100vh;
    }

    /* Flat Aesthetic: Remove all borders, shadows, and outlines */
    div[data-testid="stExpander"], .stButton>button, .stTextInput>div>div>input, 
    [data-testid="stForm"], [data-testid="stHeader"], .stTextArea>div>div>textarea,
    div[data-testid="stVerticalBlock"] > div {
        border: none !important;
        box-shadow: none !important;
        border-radius: 0px !important;
    }

    /* Sidebar Clean Flat Rectangles */
    [data-testid="stSidebar"] { background-color: #1e1f20 !important; border-right: none !important; }
    .stButton>button {
        width: 100%;
        text-align: left !important;
        background-color: rgba(255,255,255,0.02) !important;
        padding: 15px !important;
        font-size: 16px !important;
    }
    .stButton>button:hover { background-color: #333537 !important; }

    /* Discussion/Chat Typography - Bigger & Sharper */
    .chat-line { 
        padding: 4px 0px; 
        font-size: 18px !important; /* Larger text as requested */
        line-height: 1.3; 
        font-weight: 500;
    }
    .timestamp { color: #555; font-size: 12px; margin-left: 8px; font-weight: normal; }

    /* Importance Dots */
    .priority-dot { height: 10px; width: 10px; border-radius: 50%; display: inline-block; margin-right: 12px; }
    .dot-Critical { background-color: #ff4b4b; } 
    .dot-High     { background-color: #ffa500; } 
    .dot-Medium   { background-color: #00d4ff; } 
    .dot-Low      { background-color: #4b89ff; }

    /* Hide the 'Browse Files' native border */
    [data-testid="stFileUploader"] { border: none !important; }
</style>
""", unsafe_allow_html=True)

# --- 3. UTILITIES ---
def img_to_base64(image):
    buffered = BytesIO()
    image.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode()

def get_user_color(username):
    hash_obj = hashlib.md5(username.lower().encode())
    return f"#{hash_obj.hexdigest()[:6]}"

# --- 4. AUTH & NAVIGATION ---
if "logged_in" not in st.session_state: st.session_state.logged_in = False
if "view" not in st.session_state: st.session_state.view = "home"

if not st.session_state.logged_in:
    _, col, _ = st.columns([1, 1.2, 1])
    with col:
        st.markdown("<h2 style='text-align:center; margin-top:100px;'>GSA Access</h2>", unsafe_allow_html=True)
        le = st.text_input("Email", key="l_e")
        lp = st.text_input("Password", type="password", key="l_p")
        if st.button("Sign In"):
            res = c.execute("SELECT username FROM users WHERE email=? AND password=?", (le, lp)).fetchone()
            if res: 
                st.session_state.logged_in, st.session_state.user_name = True, res[0]
                st.rerun()
    st.stop()

# --- 5. SIDEBAR ---
with st.sidebar:
    st.markdown(f"### ✨ {st.session_state.user_name.lower()}")
    if st.button("＋ Create New Task"): st.session_state.view = "create_project"; st.rerun()
    if st.button("🏠 Home"): st.session_state.view = "home"; st.rerun()
    st.divider()
    
    cats = [r[0] for r in c.execute("SELECT name FROM categories").fetchall()]
    for cat in cats:
        with st.expander(cat.upper(), expanded=True):
            projs = c.execute("SELECT id, title, importance FROM projects WHERE category=?", (cat,)).fetchall()
            for pid, ptitle, pimp in projs:
                if st.button(f"{ptitle}", key=f"p_{pid}"):
                    st.session_state.active_id, st.session_state.view = pid, "view_project"
                    st.rerun()
    
    st.divider()
    if st.button("＋ Manage Categories"): st.session_state.view = "create_cat"; st.rerun()

# --- 6. PAGE VIEWS ---
if st.session_state.view == "home":
    st.markdown("<h1 style='font-weight:200; margin-top:50px;'>welcome back.</h1>", unsafe_allow_html=True)

elif st.session_state.view == "view_project":
    p = c.execute("SELECT * FROM projects WHERE id=?", (st.session_state.active_id,)).fetchone()
    if p:
        # Columns expand to fill screen width
        col_m, col_c = st.columns([1, 1], gap="large")
        
        with col_m:
            st.markdown(f"<h1 style='font-size: 42px;'>{p[2].lower()}</h1>", unsafe_allow_html=True)
            st.caption(f"{p[1]} | {p[4]}")
            st.write(p[3])
            if p[7]: st.image(f"data:image/png;base64,{p[7]}", use_container_width=True)
        
        with col_c:
            st.markdown("### discussion")
            # Chat container expands to fit available height
            chat_h = st.container(height=600, border=False)
            with chat_h:
                msgs = c.execute("SELECT user, message, timestamp, image_data FROM comments WHERE project_id=?", (p[0],)).fetchall()
                for cu, cm, ct, ci in msgs:
                    clr = get_user_color(cu)
                    # BIGGER TEXT RENDER
                    st.markdown(f"<div class='chat-line'><b style='color:{clr}'>{cu.lower()}:</b> {cm if cm else ''} <span class='timestamp'>{ct}</span></div>", unsafe_allow_html=True)
                    if ci: st.image(f"data:image/png;base64,{ci}", use_container_width=True)

            # Flat bottom input dock
            with st.container():
                with st.form("chat_f", clear_on_submit=True):
                    up = st.file_uploader("Upload", type=['png','jpg','jpeg'], label_visibility="collapsed")
                    c1, c2 = st.columns([0.9, 0.1])
                    msg = c1.text_input("msg", placeholder="type update...", label_visibility="collapsed")
                    if c2.form_submit_button("↑"):
                        if msg or up:
                            b64 = img_to_base64(Image.open(up)) if up else None
                            c.execute("INSERT INTO comments VALUES (?,?,?,?,?)", 
                                      (p[0], st.session_state.user_name, msg, datetime.now().strftime("%H:%M"), b64))
                            conn.commit(); st.rerun()

elif st.session_state.view == "create_project":
    st.markdown("<h2>new task</h2>", unsafe_allow_html=True)
    user_list = [r[0] for r in c.execute("SELECT username FROM users").fetchall()]
    cat_list = [r[0] for r in c.execute("SELECT name FROM categories").fetchall()]
    with st.form("new_p"):
        cat = st.selectbox("category", cat_list if cat_list else ["general"])
        t = st.text_input("title")
        u = st.selectbox("assignee", user_list if user_list else [st.session_state.user_name])
        imp = st.select_slider("importance", options=["Low", "Medium", "High", "Critical"])
        d = st.text_area("details")
        if st.form_submit_button("initialize"):
            c.execute("INSERT INTO projects (category, title, details, assigned_user, is_done, importance) VALUES (?,?,?,?,0,?)", 
                      (cat, t, d, u, imp))
            conn.commit(); st.session_state.view = "home"; st.rerun()
