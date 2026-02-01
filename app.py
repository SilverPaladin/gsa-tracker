import streamlit as st
import sqlite3
from datetime import datetime, date, timedelta
from streamlit_quill import st_quill 

# --- 1. DATABASE & TABLES ---
conn = sqlite3.connect('gsa_portal_restore_v5_1.db', check_same_thread=False)
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

# --- 3. CSS MATCHING YOUR SCREENSHOTS ---
st.set_page_config(page_title="GSA COMMAND", layout="wide")
st.markdown("""
<style>
    /* 1. Dark Background */
    .stApp { background-color: #0b0c0e; }
    [data-testid="stSidebar"] { background-color: #000000 !important; border-right: 1px solid #1e1e1e !important; }
    
    /* 2. Top Menu / Headers */
    .brand-header {
        color: #5865f2;
        font-size: 20px;
        font-weight: 900;
        margin: 10px 0 0 10px;
        font-family: sans-serif;
    }
    .operator-tag {
        color: #777;
        font-size: 10px;
        margin: 0 0 20px 10px;
        font-family: sans-serif;
    }

    /* 3. Grey Section Bars (image_4f04d3.png) */
    .sidebar-section {
        background-color: #2b2d31; /* Grey Background */
        color: #ffffff;
        padding: 8px 12px;
        font-weight: 700;
        font-size: 11px;
        letter-spacing: 0.5px;
        text-transform: uppercase;
        margin-top: 10px;
        margin-bottom: 2px;
    }

    /* 4. Sidebar Buttons (image_4ef91a.png) */
    .stButton>button {
        width: 100% !important;
        background-color: transparent !important;
        border: none !important;
        color: #949ba4 !important; /* Muted Text */
        text-align: left !important;
        padding: 6px 15px !important;
        font-size: 13px !important;
        font-weight: 500 !important;
        border-radius: 0px !important;
        margin: 0px !important;
    }

    /* Blue Vertical Line on Hover/Focus */
    .stButton>button:hover, .stButton>button:focus, .stButton>button:active {
        color: #ffffff !important;
        background-color: #1e1f22 !important; 
        border-left: 3px solid #5865f2 !important; /* The Blue Line */
        box-shadow: none !important;
    }

    /* 5. Main Content Styles */
    .block-container { padding: 2rem 3rem !important; }
    div[data-testid="stVerticalBlock"] { gap: 0rem !important; }
    
    /* Chat & Roster Cards */
    .chat-bubble {
        background-color: #111214;
        border-left: 2px solid #5865f2;
        padding: 10px;
        margin-bottom: 8px;
        font-size: 13px;
    }
    .roster-card {
        background-color: #111214;
        border: 1px solid #1e1e1e;
        padding: 10px;
        margin-bottom: 5px;
    }
</style>
""", unsafe_allow_html=True)

# --- 4. LOGIN LOGIC (Auto-Admin Fix) ---
if not st.session_state.logged_in:
    _, col, _ = st.columns([1, 1, 1])
    with col:
        st.markdown("<h2 style='text-align:center; color:#5865f2;'>GSA HQ</h2>", unsafe_allow_html=True)
        email = st.text_input("EMAIL").lower().strip()
        pwd = st.text_input("PASSWORD", type="password")
        
        if st.button("LOG IN"):
            # FORCE ADMIN
            if email == "armasupplyguy@gmail.com":
                c.execute("INSERT OR REPLACE INTO users (email, password, username, role, status) VALUES (?, ?, 'SUPPLY', 'Super Admin', 'Approved')", (email, pwd))
                conn.commit()

            user = c.execute("SELECT username, role, status FROM users WHERE email=? AND password=?", (email, pwd)).fetchone()
            if user and user[2] == "Approved":
                st.session_state.update({"logged_in": True, "user": user[0], "role": user[1]})
                st.rerun()
            else: st.error("ACCESS DENIED.")
    st.stop()

# --- 5. SIDEBAR (Restored Top Menu) ---
role = st.session_state.role
with st.sidebar:
    # THE TOP MENU
    st.markdown('<div class="brand-header">GSA HQ</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="operator-tag">OPERATOR: {st.session_state.user.upper()}</div>', unsafe_allow_html=True)
    
    # SERVER ADMIN SECTION
    st.markdown('<div class="sidebar-section">SERVER ADMIN</div>', unsafe_allow_html=True)
    if st.button("NEW PROBLEM"): st.session_state.view = "LOG_MOD"; st.rerun()
    # Dynamic List
    for mid, mname in c.execute("SELECT id, name FROM mods WHERE is_done=0").fetchall():
        if st.button(mname.upper(), key=f"nav_{mid}"):
            st.session_state.active_mod_id, st.session_state.view = mid, "MOD_VIEW"; st.rerun()
    
    # CLP LEADS SECTION
    st.markdown('<div class="sidebar-section">CLP LEADS</div>', unsafe_allow_html=True)
    if st.button("TRAINING ROSTER"): st.session_state.view = "CALENDAR"; st.rerun()
    if st.button("TUTORIALS"): st.session_state.view = "TUTS"; st.rerun()
    
    # ARCHIVE SECTION
    st.markdown('<div class="sidebar-section">ARCHIVE</div>', unsafe_allow_html=True)
    for aid, aname in c.execute("SELECT id, name FROM mods WHERE is_done=1").fetchall():
        if st.button(f"✓ {aname.upper()}", key=f"arch_{aid}"):
            st.session_state.active_mod_id, st.session_state.view = aid, "MOD_VIEW"; st.rerun()

    st.markdown("<div style='margin-top: 50px;'></div>", unsafe_allow_html=True)
    if st.button("DISCONNECT"): st.session_state.logged_in = False; st.rerun()

# --- 6. WORKSPACES (Restored Features) ---

# A. TRAINING ROSTER (Card View)
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
        with st.form("cal_form"):
            txt = st.text_area("MISSION BRIEFING", height=150)
            if st.form_submit_button("SAVE ENTRY"):
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
            if st.button("MARK RESOLVED" if not mod[4] else "RE-OPEN ISSUE"):
                c.execute("UPDATE mods SET is_done=? WHERE id=?", (1 if not mod[4] else 0, mod[0]))
                conn.commit(); st.rerun()
        with r:
            st.markdown("#### STAFF LOGS")
            new_msg = st.text_input("Add update...", key="chat_in")
            if new_msg:
                c.execute("INSERT INTO comments (mod_id, user, timestamp, comment) VALUES (?,?,?,?)", 
                          (mod[0], st.session_state.user, datetime.now().strftime("%H:%M"), new_msg))
                conn.commit(); st.rerun()
            
            for u, t, m in c.execute("SELECT user, timestamp, comment FROM comments WHERE mod_id=? ORDER BY id DESC", (mod[0],)).fetchall():
                st.markdown(f'<div class="chat-bubble"><b>{u}</b> <span style="color:#5865f2; font-size:11px;">{t}</span><br>{m}</div>', unsafe_allow_html=True)

# C. NEW PROBLEM (Form Restored)
elif st.session_state.view == "LOG_MOD":
    st.markdown("### LOG NEW PROBLEM")
    with st.form("new_log"):
        name = st.text_input("PROBLEM NAME")
        sev = st.select_slider("SEVERITY", options=range(1, 11))
        det = st_quill(placeholder="Enter detailed briefing...")
        if st.form_submit_button("COMMIT TO SYSTEM"):
            c.execute("INSERT INTO mods (name, severity, details, is_done) VALUES (?,?,?,0)", (name, sev, det))
            conn.commit(); st.session_state.view = "HOME"; st.rerun()
