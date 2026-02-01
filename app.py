import streamlit as st
import sqlite3
from datetime import datetime, date, timedelta
import time

# --- 1. DATABASE SETUP ---
conn = sqlite3.connect('gsa_command_v27.db', check_same_thread=False)
c = conn.cursor()
c.execute('CREATE TABLE IF NOT EXISTS users (email TEXT UNIQUE, password TEXT, username TEXT, role TEXT)')
c.execute('''CREATE TABLE IF NOT EXISTS projects 
             (id INTEGER PRIMARY KEY AUTOINCREMENT, category TEXT, sub_category TEXT, title TEXT, details TEXT, 
              author TEXT, date_val TEXT, location TEXT, mission TEXT, is_done INTEGER)''')
conn.commit()

# --- 2. SESSION STATE ---
if "logged_in" not in st.session_state: st.session_state.logged_in = False
if "view" not in st.session_state: st.session_state.view = "home"
if "sel_date" not in st.session_state: st.session_state.sel_date = str(date.today())

# --- 3. CSS: DISCORD THEME ---
st.set_page_config(page_title="GSA Command", layout="wide")
st.markdown("""
<style>
    [data-testid="stSidebar"] { background-color: #0e0e10 !important; border-right: 1px solid #222 !important; }
    .stButton>button { width: 100%; text-align: left !important; background-color: transparent !important; color: #b9bbbe !important; border: none !important; }
    .stButton>button:hover { background-color: #35373c !important; color: #fff !important; }
    
    .timeline-card { background-color: #1e1f22; border-radius: 8px; padding: 15px; margin-bottom: 5px; border-left: 5px solid #2f3136; }
    .active-card { border-left: 5px solid #5865f2 !important; background-color: #2b2d31 !important; }
    .date-header { color: #43b581; font-weight: bold; }
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
                role = "Super Admin" if re == "armasupplyguy@gmail.com" else "Competitive Player"
                c.execute("INSERT INTO users VALUES (?,?,?,?)", (re, rp, ru, role))
                conn.commit(); st.success("Created!")
    st.stop()

# --- 5. SIDEBAR (RESTORED FROM IMAGES) ---
role = st.session_state.role
is_lead = role in ["Super Admin", "Competitive Lead"]

with st.sidebar:
    st.markdown(f"### ✨ {st.session_state.user_name}")
    
    with st.expander("📁 Server To Do List", expanded=True):
        if st.button("💬 master-list"): st.session_state.view = "MASTER_LIST"; st.rerun()
        st.caption("↳ GSA 4 | Vietnam Dev")
        st.caption("↳ GSA 1 MASTER BUG THREAD")
        if st.button("# bug-discussion"): st.session_state.view = "BUG_DISCUSSION"; st.rerun()

    with st.expander("📅 CLP PANEL", expanded=True):
        if st.button("# training-roster"): st.session_state.view = "ROSTER"; st.rerun()
        if st.button("# training-tutorials"): st.session_state.view = "TUTORIALS"; st.rerun()

    if is_lead:
        with st.expander("🛡️ ADMIN", expanded=True):
            if st.button("# player-repository"): st.session_state.view = "REPO"; st.rerun()

    st.divider()
    if st.button("🚪 Logout"): st.session_state.logged_in = False; st.rerun()

# --- 6. ROSTER VIEW (FIXED SELECTION) ---
if st.session_state.view == "ROSTER":
    st.title("🗓️ Training Roster")
    col_timeline, col_editor = st.columns([1.5, 1])

    with col_timeline:
        today = date.today()
        for i in range(14):
            day = today + timedelta(days=i)
            d_str = str(day)
            
            # Highlight the currently selected date in the list
            is_selected = d_str == st.session_state.sel_date
            card_class = "timeline-card active-card" if is_selected else "timeline-card"
            
            ev = c.execute("SELECT * FROM projects WHERE category='CAL' AND date_val=?", (d_str,)).fetchone()
            
            st.markdown(f"""
            <div class="{card_class}">
                <span class="date-header">{day.strftime('%A, %b %d')}</span>
                <p style="margin:0; font-size:0.9em;">{'✅ Scheduled' if ev else '⚪ Empty'}</p>
                {f'<p style="margin:0; color:#5865f2;"><b>{ev[3]}</b> | {ev[7]}</p>' if ev else ''}
            </div>
            """, unsafe_allow_html=True)
            
            # Fixed Manage Button: Sets the state and reruns immediately
            if st.button(f"Manage {day.strftime('%d %b')}", key=f"btn_{d_str}"):
                st.session_state.sel_date = d_str
                st.rerun()

    with col_editor:
        active_date = st.session_state.sel_date
        st.subheader(f"Edit: {active_date}")
        
        current_ev = c.execute("SELECT * FROM projects WHERE category='CAL' AND date_val=?", (active_date,)).fetchone()
        
        with st.form("editor_form", clear_on_submit=False):
            f_time = st.text_input("Time", value=current_ev[3] if current_ev else "")
            f_loc = st.text_input("Location", value=current_ev[7] if current_ev else "")
            f_miss = st.text_area("Mission Info", value=current_ev[8] if current_ev else "")
            
            if st.form_submit_button("Save Entry"):
                if current_ev:
                    c.execute("UPDATE projects SET title=?, location=?, mission=? WHERE id=?", (f_time, f_loc, f_miss, current_ev[0]))
                else:
                    c.execute("INSERT INTO projects (category, date_val, title, location, mission) VALUES ('CAL',?,?,?,?)", (active_date, f_time, f_loc, f_miss))
                conn.commit()
                st.success("Saved!")
                time.sleep(0.5)
                st.rerun()

# --- 7. PLACEHOLDERS FOR OTHER VIEWS ---
elif st.session_state.view == "MASTER_LIST":
    st.title("📝 Master To-Do List")
    st.info("Logic for bug tracking goes here.")

else:
    st.markdown(f"## Welcome back, {st.session_state.user_name}")
    st.write("Select a channel from the sidebar.")
