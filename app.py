import streamlit as st
import sqlite3
from datetime import datetime, date
from streamlit_quill import st_quill 

# --- 1. DATABASE SETUP ---
conn = sqlite3.connect('gsa_portal_final.db', check_same_thread=False)
c = conn.cursor()

c.execute('''CREATE TABLE IF NOT EXISTS users 
             (email TEXT UNIQUE, password TEXT, username TEXT, role TEXT, status TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS mods 
             (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, photo_url TEXT, 
              severity INTEGER, assigned_to TEXT, details TEXT, is_done INTEGER)''')
c.execute('''CREATE TABLE IF NOT EXISTS comments 
             (id INTEGER PRIMARY KEY AUTOINCREMENT, mod_id INTEGER, user TEXT, timestamp TEXT, comment TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS events 
             (id INTEGER PRIMARY KEY AUTOINCREMENT, date_val TEXT, time_val TEXT, tz TEXT, type TEXT, location TEXT, details TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS tutorials 
             (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, content TEXT)''')
conn.commit()

# --- 2. SESSION STATE ---
if "logged_in" not in st.session_state: st.session_state.logged_in = False
if "view" not in st.session_state: st.session_state.view = "HOME"
if "active_mod_id" not in st.session_state: st.session_state.active_mod_id = None

# --- 3. SLEEK UI STYLING (No Borders / No Bubbles) ---
st.set_page_config(page_title="GSA Command", layout="wide")
st.markdown("""
<style>
    /* Dark Command Background */
    [data-testid="stSidebar"] { background-color: #0b0c0e !important; border-right: 1px solid #1e1e1e !important; }
    
    /* Sleek Rectangular Buttons */
    .stButton>button {
        width: 100% !important;
        border-radius: 0px !important; 
        border: 1px solid #222 !important;
        background-color: transparent !important;
        text-align: left !important;
        padding: 8px 15px !important;
        color: #d1d1d1 !important;
        font-size: 13px !important;
        margin-bottom: -1px !important;
        transition: 0.2s;
    }
    .stButton>button:hover {
        background-color: #1a1b1e !important;
        border-color: #5865f2 !important;
        color: white !important;
    }

    /* Minimalist Sidebar Containers */
    [data-testid="stExpander"] {
        border: none !important;
        background: transparent !important;
        padding: 0px !important;
        margin-bottom: 20px !important;
    }
    [data-testid="stExpander"] details summary {
        font-weight: bold;
        text-transform: uppercase;
        letter-spacing: 1px;
        color: #5865f2;
    }

    /* Flat Chat Bubbles */
    .chat-bubble {
        background-color: #161719;
        padding: 12px;
        border-left: 3px solid #5865f2;
        margin-bottom: 5px;
        font-size: 13px;
    }

    /* Status Indicators */
    .indicator { height: 8px; width: 8px; border-radius: 0px; display: inline-block; margin-right: 10px; }
    .red { background-color: #ff4b4b; }
    .green { background-color: #43b581; }

    /* Space Management */
    .stMainBlockContainer { padding-top: 2rem !important; }
</style>
""", unsafe_allow_html=True)

# --- 4. AUTHENTICATION ---
if not st.session_state.logged_in:
    _, col, _ = st.columns([1, 1.2, 1])
    with col:
        st.title("GSA GATEWAY")
        auth_tab = st.tabs(["LOGIN", "REGISTER"])
        with auth_tab[0]:
            le = st.text_input("Email").lower().strip()
            lp = st.text_input("Password", type="password")
            if st.button("UNLOCK PORTAL"):
                user = c.execute("SELECT email, username, role, status FROM users WHERE email=? AND password=?", (le, lp)).fetchone()
                if user and user[3] == "Approved":
                    st.session_state.update({"logged_in": True, "email": user[0], "user": user[1], "role": user[2]})
                    st.rerun()
                else: st.error("Access Denied.")
        with auth_tab[1]:
            re = st.text_input("New Email").lower().strip()
            ru = st.text_input("Username")
            rp = st.text_input("New Password", type="password")
            if st.button("SUBMIT ACCESS REQUEST"):
                role = "Super Admin" if re == "armasupplyguy@gmail.com" else "Pending"
                try:
                    c.execute("INSERT INTO users VALUES (?,?,?,?,?)", (re, rp, ru, role, "Approved" if role == "Super Admin" else "Pending"))
                    conn.commit(); st.success("Requested.")
                except: st.error("Email exists.")
    st.stop()

# --- 5. SIDEBAR NAVIGATION ---
role = st.session_state.role
with st.sidebar:
    st.markdown("### GSA COMMAND")
    st.caption(f"OPERATOR: {st.session_state.user.upper()} | {role.upper()}")
    st.divider()
    
    if role == "Super Admin":
        with st.expander("MASTER CONTROL", expanded=False):
            if st.button("USER PERMISSIONS"): st.session_state.view = "PERMISSIONS"; st.rerun()

    if role in ["Super Admin", "Admin"]:
        with st.expander("SERVER ADMIN", expanded=True):
            if st.button("NEW PROBLEM"): st.session_state.view = "LOG_MOD"; st.rerun()
            st.divider()
            
            pending = c.execute("SELECT id, name FROM mods WHERE is_done=0 ORDER BY severity DESC").fetchall()
            for p_id, p_name in pending:
                if st.button(f"■ {p_name.upper()}", key=f"side_{p_id}"):
                    st.session_state.active_mod_id, st.session_state.view = p_id, "MOD_VIEW"; st.rerun()

        with st.expander("COMPLETED ARCHIVE", expanded=False):
            finished = c.execute("SELECT id, name FROM mods WHERE is_done=1 ORDER BY id DESC").fetchall()
            for f_id, f_name in finished:
                if st.button(f"□ {f_name.upper()}", key=f"arch_{f_id}"):
                    st.session_state.active_mod_id, st.session_state.view = f_id, "MOD_VIEW"; st.rerun()

    if role in ["Super Admin", "CLPLEAD", "CLP"]:
        with st.expander("CLP PANEL", expanded=True):
            if st.button("TRAINING CALENDAR"): st.session_state.view = "CALENDAR"; st.rerun()
            if st.button("DOCS / TUTORIALS"): st.session_state.view = "TUTS"; st.rerun()

    st.divider()
    if st.button("DISCONNECT"): st.session_state.logged_in = False; st.rerun()

# --- 6. VIEWS ---

if st.session_state.view == "PERMISSIONS" and role == "Super Admin":
    st.header("USER ACCESS CONTROL")
    users = c.execute("SELECT email, username, role, status FROM users").fetchall()
    for e, u, r, s in users:
        with st.container():
            c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
            c1.markdown(f"**{u.upper()}** \n{e}")
            nr = c2.selectbox("ROLE", ["Pending", "Admin", "CLPLEAD", "CLP", "Super Admin"], index=["Pending", "Admin", "CLPLEAD", "CLP", "Super Admin"].index(r), key=f"r{e}")
            ns = c3.selectbox("STATUS", ["Pending", "Approved"], index=["Pending", "Approved"].index(s), key=f"s{e}")
            if c4.button("SAVE", key=f"btn{e}"):
                c.execute("UPDATE users SET role=?, status=? WHERE email=?", (nr, ns, e)); conn.commit(); st.rerun()

elif st.session_state.view == "LOG_MOD":
    st.header("LOG NEW PROBLEM")
    with st.form("new_problem_form", border=False):
        n = st.text_input("MOD NAME")
        i = st.text_input("PHOTO URL")
        s = st.select_slider("SEVERITY", options=range(1, 11), value=5)
        u = st.text_input("ASSIGN TO")
        st.write("INTEL / DESCRIPTION:")
        d = st_quill(placeholder="Log the problem...")
        if st.form_submit_button("COMMIT TO LOG"):
            c.execute("INSERT INTO mods (name, photo_url, severity, assigned_to, details, is_done) VALUES (?,?,?,?,?,0)", (n, i, s, u, d))
            conn.commit(); st.session_state.view = "HOME"; st.rerun()

elif st.session_state.view == "MOD_VIEW":
    mod = c.execute("SELECT * FROM mods WHERE id=?", (st.session_state.active_mod_id,)).fetchone()
    if mod:
        col_main, col_chat = st.columns([1.6, 1])
        with col_main:
            st.title(mod[1].upper())
            if mod[2]: st.image(mod[2], use_container_width=True)
            
            b1, b2 = st.columns(2)
            if mod[6] == 0:
                if b1.button("MARK AS RESOLVED", type="primary"):
                    c.execute("UPDATE mods SET is_done=1 WHERE id=?", (mod[0],)); conn.commit(); st.rerun()
            else:
                if b1.button("RE-OPEN PROBLEM"):
                    c.execute("UPDATE mods SET is_done=0 WHERE id=?", (mod[0],)); conn.commit(); st.rerun()
            
            if role == "Super Admin":
                if b2.button("PERMANENT WIPE"):
                    c.execute("DELETE FROM mods WHERE id=?", (mod[0],)); c.execute("DELETE FROM comments WHERE mod_id=?", (mod[0],))
                    conn.commit(); st.session_state.view = "HOME"; st.rerun()

            st.divider()
            st.markdown(mod[5], unsafe_allow_html=True)
            st.caption(f"SEVERITY: {mod[3]} | ASSIGNED: {mod[4].upper()}")

        with col_chat:
            st.subheader("STAFF DISCUSSION")
            with st.form("chat_form", clear_on_submit=True, border=False):
                msg = st.text_area("ADD NOTE...")
                if st.form_submit_button("SEND"):
                    if msg:
                        now = datetime.now().strftime("%b %d, %H:%M")
                        c.execute("INSERT INTO comments (mod_id, user, timestamp, comment) VALUES (?,?,?,?)", (mod[0], st.session_state.user, now, msg))
                        conn.commit(); st.rerun()
            
            chats = c.execute("SELECT user, timestamp, comment FROM comments WHERE mod_id=? ORDER BY id DESC", (mod[0],)).fetchall()
            for u, t, m in chats:
                st.markdown(f'<div class="chat-bubble"><b>{u.upper()}</b> <small style="color:#5865f2">{t}</small><br>{m}</div>', unsafe_allow_html=True)

elif st.session_state.view == "CALENDAR":
    st.header("TRAINING CALENDAR")
    if role in ["Super Admin", "CLPLEAD"]:
        with st.expander("SCHEDULE NEW EVENT"):
            with st.form("ev_form", border=False):
                d_val, t_val, tz_val = st.date_input("DATE"), st.text_input("TIME"), st.selectbox("TZ", ["EST", "GMT", "PST"])
                type_val, loc_val = st.text_input("TYPE"), st.text_input("LOCATION")
                det_val = st_quill()
                if st.form_submit_button("LOG EVENT"):
                    c.execute("INSERT INTO events (date_val, time_val, tz, type, location, details) VALUES (?,?,?,?,?,?)", (str(d_val), t_val, tz_val, type_val, loc_val, det_val))
                    conn.commit(); st.rerun()
    
    evs = c.execute("SELECT * FROM events ORDER BY date_val ASC").fetchall()
    for e in evs:
        with st.container():
            st.markdown(f"### {e[1]} @ {e[2]} {e[3]} | {e[4].upper()}")
            st.markdown(e[6], unsafe_allow_html=True)
            st.divider()

elif st.session_state.view == "TUTS":
    st.header("DOCS / TUTORIALS")
    if role in ["Super Admin", "CLPLEAD"]:
        with st.expander("CREATE NEW DOCUMENT"):
            tit = st.text_input("TITLE")
            con = st_quill()
            if st.button("PUBLISH DOC"):
                c.execute("INSERT INTO tutorials (title, content) VALUES (?,?)", (tit, con)); conn.commit(); st.rerun()
    
    for t in c.execute("SELECT * FROM tutorials").fetchall():
        with st.expander(f"DOC: {t[1].upper()}"):
            st.markdown(t[2], unsafe_allow_html=True)

else:
    st.title(f"GSA COMMAND: {st.session_state.user.upper()}")
    st.write("SYSTEM ONLINE. AWAITING INPUT FROM SIDEBAR.")
