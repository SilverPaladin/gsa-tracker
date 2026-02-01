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

# --- 2. THE EDGE-TO-EDGE CSS ---
st.set_page_config(page_title="GSA Workspace", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
    /* FORCE EDGE-TO-EDGE: Removes the empty space on left/right */
    .main .block-container {
        max-width: 100vw !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
        padding-top: 1rem !important;
        height: 100vh;
    }

    /* KILL ALL OUTLINES & BORDERS */
    div[data-testid="stExpander"], .stButton>button, .stTextInput>div>div>input, 
    [data-testid="stForm"], [data-testid="stHeader"], .stTextArea>div>div>textarea,
    div[data-testid="stVerticalBlock"] > div, .stFileUploader section {
        border: none !important;
        box-shadow: none !important;
        border-radius: 0px !important;
        background-color: transparent !important;
    }

    /* SIDEBAR: Clean Flat Hover Rectangles */
    [data-testid="stSidebar"] { background-color: #1e1f20 !important; border-right: none !important; }
    .stButton>button {
        width: 100%;
        text-align: left !important;
        background-color: rgba(255,255,255,0.02) !important;
        padding: 15px !important;
        margin-bottom: 1px !important;
    }
    .stButton>button:hover { background-color: #333537 !important; }

    /* DISCUSSION: Bold, Big, and Responsive Text */
    .chat-line { 
        padding: 6px 0px; 
        font-size: 20px !important; /* Larger readable text */
        line-height: 1.2; 
        font-weight: 500;
    }
    .timestamp { color: #555; font-size: 12px; margin-left: 8px; font-weight: normal; }

    /* IMAGE HANDLING */
    [data-testid="stImage"] img { border-radius: 0px !important; }

    /* Hide redundant UI elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
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
    _, col, _ = st.columns([1, 1, 1])
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
        # 1:1 Column ratio to utilize the full width of the screen
        col_m, col_c = st.columns([1, 1], gap="medium")
        
        with col_m:
            st.markdown(f"<h1 style='font-size: 48px; margin-bottom: 0;'>{p[2].lower()}</h1>", unsafe_allow_html=True)
            st.caption(f"{p[1]} | {p[4]}")
            st.write(p[3])
            if p[7]: st.image(f"data:image/png;base64,{p[7]}", use_container_width=True)
        
        with col_c:
            st.markdown("### discussion")
            # Chat box uses a large percentage of vertical height
            chat_h = st.container(height=650, border=False)
            with chat_h:
                msgs = c.execute("SELECT user, message, timestamp, image_data FROM comments WHERE project_id=?", (p[0],)).fetchall()
                for cu, cm, ct, ci in msgs:
                    clr = get_user_color(cu)
                    # BIG, BOLD TEXT with color coded users
                    st.markdown(f"<div class='chat-line'><b style='color:{clr}'>{cu.lower()}:</b> {cm if cm else ''} <span class='timestamp'>{ct}</span></div>", unsafe_allow_html=True)
                    if ci: st.image(f"data:image/png;base64,{ci}", use_container_width=True)

            # Flat bottom input dock
            with st.form("chat_f", clear_on_submit=True):
                up = st.file_uploader("Upload", type=['png','jpg','jpeg'], label_visibility="collapsed")
                c1, c2 = st.columns([0.9, 0.1])
                msg = c1.text_input("msg", placeholder="type update...", label_visibility="collapsed")
                if c2.form_submit_button("↑"):
                    if msg or up:
                        b64 = img_to_base64(Image.open(up)) if up else None
                        now = datetime.now().strftime("%H:%M")
                        c.execute("INSERT INTO comments VALUES (?,?,?,?,?)", (p[0], st.session_state.user_name, msg, now, b64))
                        conn.commit(); st.rerun()

# --- OTHER VIEWS (Simplified for space) ---
elif st.session_state.view == "create_project":
    st.markdown("<h2>new task</h2>", unsafe_allow_html=True)
    with st.form("new_p"):
        t = st.text_input("title")
        d = st.text_area("details")
        if st.form_submit_button("initialize"):
            c.execute("INSERT INTO projects (category, title, details, assigned_user, is_done, importance) VALUES (?,?,?,?,0,?)", ("General", t, d, st.session_state.user_name, "Medium"))
            conn.commit(); st.session_state.view = "home"; st.rerun()
