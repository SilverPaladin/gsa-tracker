import streamlit as st
import sqlite3
from datetime import datetime, date
import calendar
import time

# --- 1. DATABASE SETUP ---
conn = sqlite3.connect('gsa_master_v25.db', check_same_thread=False)
c = conn.cursor()
c.execute('CREATE TABLE IF NOT EXISTS users (email TEXT UNIQUE, password TEXT, username TEXT, role TEXT)')
c.execute('''CREATE TABLE IF NOT EXISTS projects 
             (id INTEGER PRIMARY KEY AUTOINCREMENT, category TEXT, sub_category TEXT, title TEXT, details TEXT, 
              author TEXT, importance TEXT, date_val TEXT, tz TEXT, location TEXT, mission TEXT, is_done INTEGER)''')
conn.commit()

# --- 2. SESSION STATE ---
if "logged_in" not in st.session_state: st.session_state.logged_in = False
if "view" not in st.session_state: st.session_state.view = "home"
if "cal_month" not in st.session_state: st.session_state.cal_month = datetime.now().month
if "cal_year" not in st.session_state: st.session_state.cal_year = datetime.now().year
if "sel_cal_date" not in st.session_state: st.session_state.sel_cal_date = str(date.today())

# --- 3. CSS: DISCORD DARK THEME & BUTTON STATES ---
st.set_page_config(page_title="GSA Command", layout="wide")
st.markdown("""
<style>
    [data-testid="stSidebar"] { background-color: #0e0e10 !important; border-right: 1px solid #222 !important; }
    .stButton>button { width: 100%; text-align: left !important; background-color: transparent !important; color: #b9bbbe !important; border: none !important; }
    .stButton>button:hover { background-color: #35373c !important; color: #fff !important; }
    
    /* Calendar Button Base */
    div.stButton > button[key^="day_"] {
        height: 50px !important;
        width: 100% !important;
        border-radius: 4px !important;
        border: 1px solid #333 !important;
        background-color: #1e1f22 !important;
        margin: 1px !important;
        text-align: center !important;
    }
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
                else: st.error("Access Denied.")
        with t2:
            re = st.text_input("NEW EMAIL").strip().lower()
            ru = st.text_input("USERNAME").strip()
            rp = st.text_input("NEW PASSWORD", type="password")
            if st.button("CREATE ACCOUNT"):
                try:
                    role = "Super Admin" if re == "armasupplyguy@gmail.com" else "Competitive Player"
                    c.execute("INSERT INTO users VALUES (?,?,?,?)", (re, rp, ru, role))
                    conn.commit()
                    st.success("Registered! Log in above.")
                except: st.error("User exists.")
    st.stop()

# --- 5. SIDEBAR NAVIGATION ---
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

    # LEAD CATEGORIES
    if is_lead:
        with st.expander("CLP LEADS", expanded=True):
            if st.button("# training-calendar", key="l_cal"): st.session_state.view = "CALENDAR"; st.rerun()
            if st.button("# player-repository", key="l_repo"): st.session_state.view = "REPO"; st.rerun()

    # PLAYER CATEGORIES
    with st.expander("CLP PLAYERS", expanded=True):
        if st.button("# view-calendar", key="p_cal"): st.session_state.view = "CALENDAR"; st.rerun()
        if st.button("# tutorials", key="p_tut"): st.session_state.view = "TUTORIALS"; st.rerun()

    st.divider()
    if st.button("🚪 Logout"): st.session_state.logged_in = False; st.rerun()

# --- 6. SCHEDULING TAB (REBUILT CALENDAR) ---
if st.session_state.view == "CALENDAR":
    st.title("🗓️ CLP Training Schedule")
    
    col_cal, col_form = st.columns([1.2, 1])

    with col_cal:
        # Month Controls
        m1, m2, m3 = st.columns([1, 2, 1])
        if m1.button("◀"):
            st.session_state.cal_month -= 1
            if st.session_state.cal_month < 1: st.session_state.cal_month = 12; st.session_state.cal_year -= 1
            st.rerun()
        m2.markdown(f"<h3 style='text-align:center;'>{calendar.month_name[st.session_state.cal_month]} {st.session_state.cal_year}</h3>", unsafe_allow_html=True)
        if m3.button("▶"):
            st.session_state.cal_month += 1
            if st.session_state.cal_month > 12: st.session_state.cal_month = 1; st.session_state.cal_year += 1
            st.rerun()

        # Build Calendar Logic
        cal = calendar.Calendar(firstweekday=6)
        weeks = cal.monthdayscalendar(st.session_state.cal_year, st.session_state.cal_month)
        scheduled_dates = [x[0] for x in c.execute("SELECT date_val FROM projects WHERE category='CAL'").fetchall()]

        # Display Weekdays
        cols = st.columns(7)
        for i, d in enumerate(['S', 'M', 'T', 'W', 'T', 'F', 'S']):
            cols[i].markdown(f"<p style='text-align:center;color:gray;'>{d}</p>", unsafe_allow_html=True)

        for week in weeks:
            cols = st.columns(7)
            for i, day in enumerate(week):
                if day != 0:
                    d_str = f"{st.session_state.cal_year}-{st.session_state.cal_month:02d}-{day:02d}"
                    
                    # DETERMINING BUTTON STYLE
                    # Green if has event, Blue if selected
                    btn_color = "#1e1f22" # Default
                    btn_border = "1px solid #333"
                    
                    if d_str in scheduled_dates:
                        btn_border = "2px solid #43b581" # Green border for event
                    if d_str == st.session_state.sel_cal_date:
                        btn_color = "#5865f2" # Blue background for selection
                        btn_border = "2px solid white"

                    # CSS Injection for this specific button
                    st.markdown(f"""<style>button[key="day_{d_str}"] {{ 
                        background-color: {btn_color} !important; 
                        border: {btn_border} !important; 
                        color: white !important; 
                        border-radius: {'50%' if d_str in scheduled_dates and d_str != st.session_state.sel_cal_date else '4px'} !important;
                    }}</style>""", unsafe_allow_html=True)
                    
                    if cols[i].button(str(day), key=f"day_{d_str}"):
                        st.session_state.sel_cal_date = d_str
                        st.rerun()

    with col_form:
        active_date = st.session_state.sel_cal_date
        db_ev = c.execute("SELECT * FROM projects WHERE category='CAL' AND date_val=?", (active_date,)).fetchone()
        
        st.subheader(f"Training Details: {active_date}")
        if is_lead:
            with st.form("sch_form"):
                f_t = st.text_input("Time", value=db_ev[3] if db_ev else "")
                f_l = st.text_input("Location", value=db_ev[9] if db_ev else "")
                f_m = st.text_area("Mission", value=db_ev[10] if db_ev else "")
                if st.form_submit_button("Save"):
                    if db_ev:
                        c.execute("UPDATE projects SET title=?, location=?, mission=? WHERE id=?", (f_t, f_l, f_m, db_ev[0]))
                    else:
                        c.execute("INSERT INTO projects (category, date_val, title, location, mission) VALUES ('CAL',?,?,?,?)", (active_date, f_t, f_l, f_m))
                    conn.commit()
                    st.success("Updated")
                    time.sleep(0.5); st.rerun()
        elif db_ev:
            st.info(f"**TIME:** {db_ev[3]}\n\n**LOC:** {db_ev[9]}\n\n**INFO:** {db_ev[10]}")
        else:
            st.write("No training scheduled.")

# --- 7. MOD TASK VIEWS (SERVER 1 & 2) ---
elif "CREATE" in st.session_state.view or "FIX" in st.session_state.view:
    title = st.session_state.view.replace("_", " ")
    st.title(title)
    
    with st.expander("＋ Add Entry"):
        with st.form("task_f"):
            m_n = st.text_input("Mod Name")
            m_d = st.text_area("Details")
            if st.form_submit_button("Post"):
                c.execute("INSERT INTO projects (category, sub_category, title, details, is_done) VALUES (?,?,?,?,0)", 
                          (st.session_state.view, "TASK", m_n, m_d))
                conn.commit(); st.rerun()
                
    tasks = c.execute("SELECT * FROM projects WHERE category=? AND is_done=0", (st.session_state.view,)).fetchall()
    for t in tasks:
        with st.container(border=True):
            st.markdown(f"**{t[3]}**")
            st.write(t[4])
            if st.button("Resolve", key=f"res_{t[0]}"):
                c.execute("UPDATE projects SET is_done=1 WHERE id=?", (t[0],)); conn.commit(); st.rerun()

else:
    st.markdown(f"## Welcome back, {st.session_state.user_name}")
