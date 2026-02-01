import streamlit as st
import sqlite3
from datetime import datetime, date
import calendar
import time

# --- 1. DATABASE SETUP ---
# Stores users, project tasks, and calendar events
conn = sqlite3.connect('gsa_command_v20.db', check_same_thread=False)
c = conn.cursor()
c.execute('CREATE TABLE IF NOT EXISTS users (email TEXT UNIQUE, password TEXT, username TEXT, role TEXT)')
c.execute('''CREATE TABLE IF NOT EXISTS projects 
             (id INTEGER PRIMARY KEY AUTOINCREMENT, category TEXT, sub_category TEXT, title TEXT, details TEXT, 
              author TEXT, importance TEXT, image_data TEXT, date_val TEXT, 
              tz TEXT, location TEXT, mission TEXT, is_done INTEGER)''')
c.execute('CREATE TABLE IF NOT EXISTS attendance (event_id INTEGER, username TEXT)')
conn.commit()

# --- 2. SESSION STATE ---
if "logged_in" not in st.session_state: st.session_state.logged_in = False
if "view" not in st.session_state: st.session_state.view = "home"
if "cal_month" not in st.session_state: st.session_state.cal_month = datetime.now().month
if "cal_year" not in st.session_state: st.session_state.cal_year = datetime.now().year
if "sel_cal_date" not in st.session_state: st.session_state.sel_cal_date = str(date.today())

# --- 3. CSS: UI & CALENDAR LOGIC ---
st.set_page_config(page_title="GSA Command", layout="wide", initial_sidebar_state="expanded")
st.markdown("""
<style>
    /* Global Sidebar Style */
    [data-testid="stSidebar"] { background-color: #0e0e10 !important; border-right: 1px solid #222 !important; }
    .stButton>button { width: 100%; text-align: left !important; background-color: transparent !important; color: #b9bbbe !important; border: none !important; }
    .stButton>button:hover { background-color: #35373c !important; color: #fff !important; }

    /* Calendar Grid - Boxed Days */
    .stButton>button[key^="day_btn_"] {
        border: 1px solid #333 !important;
        background-color: #1e1f22 !important;
        aspect-ratio: 1/1 !important;
        min-height: 48px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        margin: 1px !important;
        text-align: center !important;
    }
    
    /* Green Circle for Scheduled Events */
    div[data-event="true"] button {
        border: 2px solid #43b581 !important;
        border-radius: 50% !important;
        color: #43b581 !important;
    }

    /* SELECTION PRIORITY (Blue Highlight) */
    div[data-selected="true"] button {
        background-color: #5865f2 !important;
        color: white !important;
        border: 2px solid #ffffff !important;
        border-radius: 4px !important;
    }

    .save-notif {
        padding: 10px; background-color: #43b581; color: white;
        border-radius: 5px; text-align: center; margin-bottom: 10px;
    }
</style>
""", unsafe_allow_html=True)

# --- 4. FUNCTIONS ---
def change_month(delta):
    st.session_state.cal_month += delta
    if st.session_state.cal_month > 12:
        st.session_state.cal_month = 1
        st.session_state.cal_year += 1
    elif st.session_state.cal_month < 1:
        st.session_state.cal_month = 12
        st.session_state.cal_year -= 1

# --- 5. AUTHENTICATION ---
if not st.session_state.logged_in:
    _, col, _ = st.columns([1, 1.2, 1])
    with col:
        st.markdown("<h2 style='text-align:center;'>GSA GATEWAY</h2>", unsafe_allow_html=True)
        t1, t2 = st.tabs(["SIGN IN", "REGISTER"])
        with t1:
            le = st.text_input("EMAIL").strip().lower()
            lp = st.text_input("PASSWORD", type="password")
            if st.button("UNLOCK"):
                res = c.execute("SELECT username, role FROM users WHERE email=? AND password=?", (le, lp)).fetchone()
                if res: 
                    st.session_state.update({"logged_in": True, "user_name": res[0], "role": res[1]})
                    st.rerun()
    st.stop()

# --- 6. SIDEBAR NAVIGATION ---
role = st.session_state.role
is_lead = role in ["Super Admin", "Competitive Lead"]
is_player = role == "Competitive Player"

with st.sidebar:
    st.markdown(f"### ✨ {st.session_state.user_name}")
    if st.button("🏠 Home", key="nav_home"): st.session_state.view = "home"; st.rerun()
    st.divider()

    # Server Channels
    for s_id in [1, 2]:
        with st.expander(f"SERVER {s_id}", expanded=True):
            if st.button("# mods-to-create", key=f"s{s_id}_create"): st.session_state.view = f"S{s_id}_CREATE"; st.rerun()
            if st.button("# mods-to-fix", key=f"s{s_id}_fix"): st.session_state.view = f"S{s_id}_FIX"; st.rerun()

    # Management Channels
    if is_lead:
        with st.expander("CLP LEADS", expanded=True):
            if st.button("# player-repository", key="l_repo_btn"): st.session_state.view = "PLAYER_REPO"; st.rerun()
            if st.button("# training-calendar", key="l_cal_btn"): st.session_state.view = "CALENDAR"; st.rerun()
            if st.button("# training-tutorials", key="l_tut_btn"): st.session_state.view = "TUT_POST"; st.rerun()

    # Player Channels
    if is_lead or is_player:
        with st.expander("CLP PLAYERS", expanded=True):
            if st.button("# view-tutorials", key="p_tut_btn"): st.session_state.view = "TUT_VIEW"; st.rerun()
            if st.button("# view-calendar", key="p_cal_btn"): st.session_state.view = "CALENDAR"; st.rerun()

    if st.button("🚪 Logout", key="nav_logout"): st.session_state.logged_in = False; st.rerun()

# --- 7. VIEWS ---

# COMPACT BOXED CALENDAR
if st.session_state.view == "CALENDAR":
    st.title("🗓️ CLP Training Calendar")
    col_cal, col_panel = st.columns([1, 1.2])

    with col_cal:
        m_col1, m_col2, m_col3 = st.columns([1, 3, 1])
        if m_col1.button("◀", key="m_prev"): change_month(-1); st.rerun()
        m_col2.markdown(f"<h3 style='text-align:center;'>{calendar.month_name[st.session_state.cal_month]} {st.session_state.cal_year}</h3>", unsafe_allow_html=True)
        if m_col3.button("▶", key="m_next"): change_month(1); st.rerun()

        cal = calendar.Calendar(firstweekday=6)
        weeks = cal.monthdayscalendar(st.session_state.cal_year, st.session_state.cal_month)
        events = [str(e[0]) for e in c.execute("SELECT date_val FROM projects WHERE category='CAL'").fetchall()]

        h_cols = st.columns(7)
        for d in ['Su','Mo','Tu','We','Th','Fr','Sa']:
            h_cols[['Su','Mo','Tu','We','Th','Fr','Sa'].index(d)].markdown(f"<p style='text-align:center; color:grey; font-size:12px;'>{d}</p>", unsafe_allow_html=True)

        for week in weeks:
            d_cols = st.columns(7)
            for i, day in enumerate(week):
                if day != 0:
                    d_str = f"{st.session_state.cal_year}-{st.session_state.cal_month:02d}-{day:02d}"
                    has_ev = "true" if d_str in events else "false"
                    is_sel = "true" if d_str == st.session_state.sel_cal_date else "false"
                    with d_cols[i]:
                        st.markdown(f'<div data-event="{has_ev}" data-selected="{is_sel}">', unsafe_allow_html=True)
                        if st.button(str(day), key=f"day_btn_{d_str}"):
                            st.session_state.sel_cal_date = d_str; st.rerun()
                        st.markdown('</div>', unsafe_allow_html=True)

    with col_panel:
        selected = st.session_state.sel_cal_date
        event = c.execute("SELECT * FROM projects WHERE category='CAL' AND date_val=?", (selected,)).fetchone()
        st.subheader(f"Selected: {selected}")
        
        if is_lead:
            with st.form("cal_form"):
                tz = st.text_input("Time Zone", value=event[9] if event else "EST")
                tm = st.text_input("Time", value=event[3] if event else "")
                lc = st.text_input("Location", value=event[10] if event else "")
                ms = st.text_area("Mission Details", value=event[11] if event else "")
                if st.form_submit_button("Save Event"):
                    if event: c.execute("UPDATE projects SET title=?, tz=?, location=?, mission=? WHERE id=?", (tm, tz, lc, ms, event[0]))
                    else: c.execute("INSERT INTO projects (category, date_val, title, tz, location, mission, is_done) VALUES ('CAL',?,?,?,?,?,0)", (selected, tm, tz, lc, ms))
                    conn.commit(); st.success("Saved!"); time.sleep(1); st.rerun()
        elif event:
            st.info(f"⏰ {event[3]} {event[9]} | 📍 {event[10]}\n\n🎮 {event[11]}")
        else:
            st.write("No training scheduled for this date.")

# MODS, REPO, TUTORIALS (Logic simplified from V19)
elif "CREATE" in st.session_state.view or "FIX" in st.session_state.view:
    cat, sub = st.session_state.view.split("_")
    st.title(f"{cat} | {sub.lower()}")
    # ... (Rest of Task logic) ...
    st.write("Use the Lead Panel to add or fix mods for this server.")

elif st.session_state.view == "PLAYER_REPO":
    st.title("👤 Player Repository")
    # ... (Rest of Repo logic) ...
    st.write("Track player information and availability here.")

else:
    st.markdown("<h1 style='font-weight:200; margin-top:10vh; font-size: 5vw;'>GSA COMMAND</h1>", unsafe_allow_html=True)
