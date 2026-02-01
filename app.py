import streamlit as st
import sqlite3
from datetime import datetime, date, timedelta
from streamlit_quill import st_quill 

# --- 1. DATABASE ---
conn = sqlite3.connect('gsa_portal_v5_2.db', check_same_thread=False)
c = conn.cursor()
c.execute('CREATE TABLE IF NOT EXISTS users (email TEXT UNIQUE, password TEXT, username TEXT, role TEXT, status TEXT)')
c.execute('CREATE TABLE IF NOT EXISTS mods (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, severity INTEGER, details TEXT, is_done INTEGER)')
c.execute('CREATE TABLE IF NOT EXISTS comments (id INTEGER PRIMARY KEY AUTOINCREMENT, mod_id INTEGER, user TEXT, timestamp TEXT, comment TEXT)')
c.execute('CREATE TABLE IF NOT EXISTS events (date_val TEXT PRIMARY KEY, type TEXT)')
conn.commit()

# --- 2. SESSION STATE ---
if "logged_in" not in st.session_state: st.session_state.logged_in = False
if "view" not in st.session_state: st.session_state.view = "HOME"
if "active_mod_id" not in st.session_state: st.session_state.active_mod_id = None
if "sel_date" not in st.session_state: st.session_state.sel_date = str(date.today())

# --- 3. CSS (Matching image_4ef91a.png & image_4f04d3.png) ---
st.set_page_config(page_title="GSA COMMAND", layout="wide")
st.markdown("""
<style>
    /* Dark Theme Base */
    .stApp { background-color: #0b0c0e; }
    [data-testid="stSidebar"] { background-color: #000000 !important; border-right: 1px solid #1e1e1e !important; }
    
    /* Top Menu Styling (The part I broke previously) */
    .top-brand {
        color: #5865f2;
        font-size: 20px;
        font-weight: 900;
        font-family: sans-serif;
        padding-left: 10px;
        margin-bottom: 0px;
    }
    .top-operator {
        color: #888;
        font-size: 11px;
        font-family: sans-serif;
        padding-left: 10px;
        margin-top: -5px;
        margin-bottom: 20px;
        text-transform: uppercase;
    }

    /* Grey Section Bars (image_4f04d3.png) */
    .section-bar {
        background-color: #2b2d31;
        color: #ffffff;
        padding: 8px 15px;
        font-weight: 800;
        font-size: 11px;
        letter-spacing: 0.5px;
        text-transform: uppercase;
        margin-top: 15px;
        margin-bottom: 5px;
    }

    /* Sidebar Buttons (image_4ef91a.png) */
    .stButton>button {
        width: 100% !important;
        background-color: transparent !important;
        border: none !important;
        color: #949ba4 !important;
        text-align: left !important;
        padding: 5px 20px !important;
        font-size: 13px !important;
        font-weight: 500 !important;
        border-radius: 0px !important;
    }

    /* Blue Vertical Line on Hover */
    .stButton>button:hover, .stButton>button:focus, .stButton>button:active {
        color: #ffffff !important;
        background-color: #1e1f22 !important;
        border-left: 3px solid #5865f2 !important;
        box-shadow: none !important;
    }

    /* Content Styling */
    .block-container { padding: 2rem 3rem !important; }
    div[data-testid="stVerticalBlock"] { gap: 0rem !important; }
    
    /* Custom Components */
    .chat-msg { background: #111214; border-left: 2px solid #5865f2; padding: 10px; margin-bottom: 5px; font-size: 13px; }
    .roster-card { background: #111214; border: 1px solid #1e1e1e; padding: 12px; margin-bottom: 5px; }
</style>
""", unsafe_allow_html=True)

# --- 4. LOGIN (With Admin Fix) ---
if not st.session_state.logged_in:
    _, col, _ = st.columns([1, 1, 1])
    with col:
        st.markdown("<h2 style='text-align:center; color:#5865f2;'>GSA HQ</h2>", unsafe_allow_html=True)
        email = st.text_input("EMAIL").lower().strip()
        pwd = st.text_input("PASSWORD", type="password")
        
        c1, c2 = st.columns(2)
        if c1.button("LOG IN"):
            # FORCE ADMIN
            if email == "armasupplyguy@gmail.com":
                c.execute("INSERT OR REPLACE INTO users (email, password, username, role, status) VALUES (?, ?, 'SUPPLY', 'Super Admin', 'Approved')", (email, pwd))
                conn.commit()

            user = c.execute("SELECT username, role, status FROM users WHERE email=? AND password=?", (email, pwd)).fetchone()
            if user and user[2] == "Approved":
                st.session_state.update({"logged_in": True, "user": user[0], "role": user[1]})
                st.rerun()
            else: st.error("ACCESS DENIED.")

        if c2.button("REGISTER"):
            st.session_state.view = "REGISTER"
            st.rerun()
            
    if st.session_state.view == "REGISTER":
        with col:
            new_u = st.text_input("USERNAME")
            if st.button("SEND REQUEST"):
                try:
                    c.execute("INSERT INTO users VALUES (?,?,?,?,?)", (email, pwd, new_u, "User", "Pending"))
                    conn.commit(); st.success("SENT.")
                except: st.error("TAKEN.")
    st.stop()

# --- 5. SIDEBAR (Restored Top Menu) ---
role = st.session_state.role
with st.sidebar:
    # 1. TOP MENU RESTORED
    st.markdown('<div class="top-brand">GSA HQ</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="top-operator">OPERATOR: {st.session_state.user.upper()}</div>', unsafe_allow_html=True)
    
    # 2. SECTIONS
    if role == "Super Admin":
        st.markdown('<div class="section-bar">MASTER CONTROL</div>', unsafe_allow_html=True)
        if st.button("USER PERMISSIONS"): st.session_state.view = "PERMISSIONS"; st.rerun()

    st.markdown('<div class="section-bar">SERVER ADMIN</div>', unsafe_allow_html=True)
    if st.button("NEW PROBLEM"): st.session_state.view = "LOG_MOD"; st.rerun()
    for mid, mname in c.execute("SELECT id, name FROM mods WHERE is_done=0").fetchall():
        if st.button(mname.upper(), key=f"nav_{mid}"):
            st.session_state.active_mod_id, st.session_state.view = mid, "MOD_VIEW"; st.rerun()
    
    st.markdown('<div class="section-bar">CLP LEADS</div>', unsafe_allow_html=True)
    if st.button("TRAINING ROSTER"): st.session_state.view = "CALENDAR"; st.rerun()
    
    st.markdown('<div class="section-bar">ARCHIVE</div>', unsafe_allow_html=True)
    for aid, aname in c.execute("SELECT id, name FROM mods WHERE is_done=1").fetchall():
        if st.button(f"✓ {aname.upper()}", key=f"arch_{aid}"):
            st.session_state.active_mod_id, st.session_state.view = aid, "MOD_VIEW"; st.rerun()

    st.markdown("<div style='margin-top: 50px;'></div>", unsafe_allow_html=True)
    if st.button("DISCONNECT"): st.session_state.logged_in = False; st.rerun()

# --- 6. WORKSPACES ---

# A. TRAINING ROSTER
if st.session_state.view == "CALENDAR":
    st.markdown("### 🗓️ TRAINING ROSTER")
    c1, c2 = st.columns([1.5, 1])
    with c1:
        for i in range(12):
            d = date.today() + timedelta(days=i)
            ev = c.execute("SELECT type FROM events WHERE date_val=?", (str(d),)).fetchone()
            st.markdown(f"""
            <div class="roster-card">
                <span style="color:#43b581; font-weight:bold;">{d.strftime("%A, %b %d")}</span><br>
                <span style="color:#aaa; font-size:12px;">{ev[0] if ev else "EMPTY"}</span>
            </div>
            """, unsafe_allow_html=True)
            if st.button(f"EDIT {d.strftime('%d %b')}", key=f"ed_{d}"):
                st.session_state.sel_date = str(d); st.rerun()
    with c2:
        st.markdown(f"#### MANAGE: {st.session_state.sel_date}")
        with st.form("cal"):
            txt = st.text_area("BRIEFING", height=150)
            if st.form_submit_button("SAVE"):
                c.execute("INSERT OR REPLACE INTO events (date_val, type) VALUES (?,?)", (st.session_state.sel_date, txt))
                conn.commit(); st.rerun()

# B. MOD VIEW (Chat Restored)
elif st.session_state.view == "MOD_VIEW":
    mod = c.execute("SELECT * FROM mods WHERE id=?", (st.session_state.active_mod_id,)).fetchone()
    if mod:
        st.markdown(f"### {mod[1].upper()}")
        l, r = st.columns([1.8, 1])
        with l:
            st.markdown(mod[3], unsafe_allow_html=True)
            st.write("---")
            if st.button("MARK RESOLVED" if not mod[4] else "RE-OPEN"):
                c.execute("UPDATE mods SET is_done=? WHERE id=?", (1 if not mod[4] else 0, mod[0]))
                conn.commit(); st.rerun()
        with r:
            st.markdown("#### STAFF LOGS")
            new_msg = st.text_input("Log update...", key="chat_in")
            if new_msg:
                c.execute("INSERT INTO comments (mod_id, user, timestamp, comment) VALUES (?,?,?,?)", 
                          (mod[0], st.session_state.user, datetime.now().strftime("%H:%M"), new_msg))
                conn.commit(); st.rerun()
            for u, t, m in c.execute("SELECT user, timestamp, comment FROM comments WHERE mod_id=? ORDER BY id DESC", (mod[0],)).fetchall():
                st.markdown(f'<div class="chat-msg"><b>{u}</b> <span style="color:#5865f2; font-size:11px;">{t}</span><br>{m}</div>', unsafe_allow_html=True)

# C. NEW PROBLEM
elif st.session_state.view == "LOG_MOD":
    st.markdown("### LOG NEW PROBLEM")
    with st.form("new_mod"):
        name = st.text_input("PROBLEM NAME")
        sev = st.select_slider("SEVERITY", options=range(1, 11))
        det = st_quill(placeholder="Enter details...")
        if st.form_submit_button("COMMIT"):
            c.execute("INSERT INTO mods (name, severity, details, is_done) VALUES (?,?,?,0)", (name, sev, det))
            conn.commit(); st.session_state.view = "HOME"; st.rerun()

# D. PERMISSIONS (Admin)
elif st.session_state.view == "PERMISSIONS" and role == "Super Admin":
    st.markdown("### USER PERMISSIONS")
    for row in c.execute("SELECT email, username, role, status FROM users").fetchall():
        with st.container():
            c1, c2, c3 = st.columns([2, 1, 1])
            c1.write(f"**{row[1]}** ({row[0]})")
            nr = c2.selectbox("Role", ["User","Admin","CLPLEAD","Super Admin"], index=["User","Admin","CLPLEAD","Super Admin"].index(row[2]), key=f"r_{row[0]}")
            ns = c3.selectbox("Status", ["Pending","Approved"], index=["Pending","Approved"].index(row[3]), key=f"s_{row[0]}")
            if st.button("UPDATE", key=f"u_{row[0]}"):
                c.execute("UPDATE users SET role=?, status=? WHERE email=?", (nr, ns, row[0]))
                conn.commit(); st.rerun()
