import streamlit as st
import sqlite3
from datetime import datetime, date, timedelta
import time

# --- 1. DATABASE SETUP ---
conn = sqlite3.connect('gsa_command_v26.db', check_same_thread=False)
c = conn.cursor()
c.execute('CREATE TABLE IF NOT EXISTS users (email TEXT UNIQUE, password TEXT, username TEXT, role TEXT)')
c.execute('''CREATE TABLE IF NOT EXISTS projects 
             (id INTEGER PRIMARY KEY AUTOINCREMENT, category TEXT, sub_category TEXT, title TEXT, details TEXT, 
              author TEXT, date_val TEXT, location TEXT, mission TEXT, is_done INTEGER)''')
conn.commit()

# --- 2. SESSION STATE ---
if "logged_in" not in st.session_state: st.session_state.logged_in = False
if "view" not in st.session_state: st.session_state.view = "home"
if "roster_offset" not in st.session_state: st.session_state.roster_offset = 0

# --- 3. THEME & CSS ---
st.set_page_config(page_title="GSA Command", layout="wide")
st.markdown("""
<style>
    [data-testid="stSidebar"] { background-color: #0e0e10 !important; border-right: 1px solid #222 !important; }
    .stButton>button { width: 100%; text-align: left !important; background-color: transparent !important; color: #b9bbbe !important; border: none !important; }
    .stButton>button:hover { background-color: #35373c !important; color: #fff !important; }
    
    .timeline-card { background-color: #2b2d31; border-radius: 8px; padding: 15px; margin-bottom: 10px; border-left: 5px solid #5865f2; }
    .date-header { color: #43b581; font-weight: bold; font-size: 1.1em; }
</style>
""", unsafe_allow_html=True)

# --- 4. AUTHENTICATION ---
if not st.session_state.logged_in:
    _, col, _ = st.columns([1, 1.2, 1])
    with col:
        st.markdown("<h2 style='text-align:center;'>GSA GATEWAY</h2>", unsafe_allow_html=True)
        t1, t2 = st.tabs(["SIGN IN", "REGISTER"])
        with t1:
            le = st.text_input("EMAIL").strip().lower()
            lp = st.text_input("PASSWORD", type="password")
            if st.button("UNLOCK"):
                user = c.execute("SELECT username, role FROM users WHERE email=? AND password=?", (le, lp)).fetchone()
                if user:
                    st.session_state.update({"logged_in": True, "user_name": user[0], "role": user[1]})
                    st.rerun()
        with t2:
            re = st.text_input("NEW EMAIL").strip().lower()
            ru = st.text_input("USERNAME").strip()
            rp = st.text_input("NEW PASSWORD", type="password")
            if st.button("CREATE ACCOUNT"):
                try:
                    # Auto-admin for you
                    role = "Super Admin" if re == "armasupplyguy@gmail.com" else "Competitive Player"
                    c.execute("INSERT INTO users VALUES (?,?,?,?)", (re, rp, ru, role))
                    conn.commit()
                    st.success("Account Created! Login above.")
                except: st.error("Email already in use.")
    st.stop()

# --- 5. SIDEBAR ---
role = st.session_state.role
is_lead = role in ["Super Admin", "Competitive Lead"]

with st.sidebar:
    st.markdown(f"### ✨ {st.session_state.user_name}")
    if st.button("🏠 Home"): st.session_state.view = "home"; st.rerun()
    st.divider()

    # SERVER CATEGORIES
    for s in ["SERVER 1", "SERVER 2"]:
        with st.expander(s, expanded=True):
            if st.button(f"# mods-to-create", key=f"btn_{s}_c"): st.session_state.view = f"{s}_CREATE"; st.rerun()
            if st.button(f"# mods-to-fix", key=f"btn_{s}_f"): st.session_state.view = f"{s}_FIX"; st.rerun()

    # CLP PANEL (Combined view)
    with st.expander("CLP PANEL", expanded=True):
        if st.button("# scheduling-roster", key="nav_sch"): st.session_state.view = "ROSTER"; st.rerun()
        if st.button("# tutorials", key="nav_tut"): st.session_state.view = "TUTORIALS"; st.rerun()

    if is_lead:
        with st.expander("ADMIN", expanded=True):
            if st.button("# player-repository", key="nav_repo"): st.session_state.view = "REPO"; st.rerun()

    st.divider()
    if st.button("🚪 Logout"): st.session_state.logged_in = False; st.rerun()

# --- 6. TIMELINE ROSTER VIEW (BETTER THAN CALENDAR) ---
if st.session_state.view == "ROSTER":
    st.title("🗓️ Training Roster")
    st.write("A vertical timeline of the next 14 days.")

    # Show 14 days starting from today
    today = date.today()
    
    col_timeline, col_editor = st.columns([1.5, 1])

    with col_timeline:
        for i in range(14):
            day = today + timedelta(days=i)
            d_str = day.strftime("%Y-%m-%d")
            d_pretty = day.strftime("%A, %b %d")
            
            # Check if event exists
            ev = c.execute("SELECT * FROM projects WHERE category='CAL' AND date_val=?", (d_str,)).fetchone()
            
            with st.container():
                st.markdown(f"""
                <div class="timeline-card">
                    <span class="date-header">{d_pretty}</span>
                    <hr style="margin: 5px 0; border: 0.5px solid #444;">
                    <p style="margin:0;"><b>Status:</b> {'✅ Scheduled' if ev else '⚪ Empty'}</p>
                    {f'<p style="margin:0; color:#5865f2;"><b>Time:</b> {ev[3]} | <b>Loc:</b> {ev[7]}</p>' if ev else ''}
                </div>
                """, unsafe_allow_html=True)
                
                # Selection button for the editor
                if st.button(f"Manage {day.strftime('%d %b')}", key=f"sel_{d_str}"):
                    st.session_state.sel_date = d_str
                    st.rerun()

    with col_editor:
        sel_date = st.session_state.get("sel_date", str(today))
        st.subheader(f"Edit Details: {sel_date}")
        
        if is_lead:
            current_ev = c.execute("SELECT * FROM projects WHERE category='CAL' AND date_val=?", (sel_date,)).fetchone()
            with st.form("edit_roster"):
                f_time = st.text_input("Time", value=current_ev[3] if current_ev else "")
                f_loc = st.text_input("Location", value=current_ev[7] if current_ev else "")
                f_miss = st.text_area("Mission Info", value=current_ev[8] if current_ev else "")
                
                if st.form_submit_button("Save Entry"):
                    if current_ev:
                        c.execute("UPDATE projects SET title=?, location=?, mission=? WHERE id=?", (f_time, f_loc, f_miss, current_ev[0]))
                    else:
                        c.execute("INSERT INTO projects (category, date_val, title, location, mission) VALUES ('CAL',?,?,?,?)", (sel_date, f_time, f_loc, f_miss))
                    conn.commit()
                    st.success("Roster Updated")
                    time.sleep(0.5); st.rerun()
            
            if current_ev and st.button("🗑️ Delete Event"):
                c.execute("DELETE FROM projects WHERE id=?", (current_ev[0],))
                conn.commit(); st.rerun()
        else:
            st.warning("Only Leads can edit the roster.")

# --- 7. SERVER TASKS (RESTORED) ---
elif "CREATE" in st.session_state.view or "FIX" in st.session_state.view:
    st.title(st.session_state.view.replace("_", " "))
    with st.expander("＋ Post New Mod Task"):
        with st.form("task_entry"):
            t_name = st.text_input("Mod Name")
            t_det = st.text_area("What needs to be done?")
            if st.form_submit_button("Submit"):
                c.execute("INSERT INTO projects (category, title, details, is_done) VALUES (?,?,?,0)", 
                          (st.session_state.view, t_name, t_det))
                conn.commit(); st.rerun()

    tasks = c.execute("SELECT * FROM projects WHERE category=? AND is_done=0", (st.session_state.view,)).fetchall()
    for t in tasks:
        with st.container(border=True):
            st.write(f"**{t[3]}**")
            st.write(t[4])
            if st.button("Complete", key=f"done_{t[0]}"):
                c.execute("UPDATE projects SET is_done=1 WHERE id=?", (t[0],)); conn.commit(); st.rerun()

else:
    st.markdown(f"## Welcome back, {st.session_state.user_name}")
    st.write("Use the sidebar to navigate to the timeline or server tasks.")
