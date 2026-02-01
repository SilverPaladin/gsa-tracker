import streamlit as st
import sqlite3
from datetime import datetime, date
import calendar
import base64
from io import BytesIO
from PIL import Image
import hashlib

# --- 1. DATABASE SETUP ---
conn = sqlite3.connect('gsa_command_v18.db', check_same_thread=False)
c = conn.cursor()
c.execute('CREATE TABLE IF NOT EXISTS users (email TEXT UNIQUE, password TEXT, username TEXT, role TEXT)')
c.execute('''CREATE TABLE IF NOT EXISTS projects 
             (id PRIMARY KEY, category TEXT, sub_category TEXT, title TEXT, details TEXT, 
              author TEXT, importance TEXT, image_data TEXT, date_val TEXT, 
              tz TEXT, location TEXT, mission TEXT, is_done INTEGER)''')
c.execute('CREATE TABLE IF NOT EXISTS attendance (event_id INTEGER, username TEXT)')
conn.commit()

# --- 2. SESSION STATE & NAVIGATION ---
if "logged_in" not in st.session_state: st.session_state.logged_in = False
if "view" not in st.session_state: st.session_state.view = "home"
if "cal_month" not in st.session_state: st.session_state.cal_month = datetime.now().month
if "cal_year" not in st.session_state: st.session_state.cal_year = datetime.now().year
if "sel_cal_date" not in st.session_state: st.session_state.sel_cal_date = str(date.today())

# --- 3. CSS: DISCORD THEME & COMPACT CALENDAR ---
st.set_page_config(page_title="GSA Command", layout="wide", initial_sidebar_state="expanded")
st.markdown("""
<style>
    .main .block-container { max-width: 100vw !important; padding: 1rem 2rem !important; }
    [data-testid="stSidebar"] { background-color: #0e0e10 !important; border-right: 1px solid #222 !important; }
    
    /* Sidebar Hierarchy Styling */
    .stButton>button { 
        width: 100%; text-align: left !important; background-color: transparent !important; 
        color: #b9bbbe !important; border: none !important; border-radius: 4px !important;
        padding: 4px 10px !important; font-size: 14px !important;
    }
    .stButton>button:hover { background-color: #35373c !important; color: #fff !important; }
    
    /* Calendar Grid Styling */
    .has-event { border: 2px solid #43b581 !important; color: #43b581 !important; font-weight: bold; }
    .is-selected { background-color: #5865f2 !important; color: white !important; }
    
    .status-light { height: 7px; width: 7px; border-radius: 50%; display: inline-block; margin-right: 10px; }
    .light-critical { background-color: #ff4444; box-shadow: 0 0 8px #ff4444; }
    .light-high     { background-color: #ffaa00; box-shadow: 0 0 8px #ffaa00; }
</style>
""", unsafe_allow_html=True)

# --- 4. UTILITIES ---
def process_img(file):
    img = Image.open(file)
    img.thumbnail((600, 600))
    buf = BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()

def change_month(delta):
    new_month = st.session_state.cal_month + delta
    if new_month > 12:
        st.session_state.cal_month = 1
        st.session_state.cal_year += 1
    elif new_month < 1:
        st.session_state.cal_month = 12
        st.session_state.cal_year -= 1
    else:
        st.session_state.cal_month = new_month

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

    with st.expander("SERVER 1", expanded=True):
        if st.button("# mods-to-create", key="btn_s1_c"): st.session_state.view = "S1_CREATE"; st.rerun()
        if st.button("# mods-to-fix", key="btn_s1_f"): st.session_state.view = "S1_FIX"; st.rerun()
    
    with st.expander("SERVER 2", expanded=True):
        if st.button("# mods-to-create", key="btn_s2_c"): st.session_state.view = "S2_CREATE"; st.rerun()
        if st.button("# mods-to-fix", key="btn_s2_f"): st.session_state.view = "S2_FIX"; st.rerun()

    if is_lead:
        with st.expander("CLP LEADS", expanded=True):
            if st.button("# player-repository", key="btn_l_repo"): st.session_state.view = "PLAYER_REPO"; st.rerun()
            if st.button("# training-calendar", key="btn_l_cal"): st.session_state.view = "CALENDAR"; st.rerun()
            if st.button("# training-tutorials", key="btn_l_tut"): st.session_state.view = "TUTORIAL_POST"; st.rerun()

    if is_lead or is_player:
        with st.expander("CLP PLAYERS", expanded=True):
            if st.button("# view-tutorials", key="btn_p_tut"): st.session_state.view = "TUTORIAL_VIEW"; st.rerun()
            if st.button("# view-calendar", key="btn_p_cal"): st.session_state.view = "CALENDAR"; st.rerun()

    if st.button("🚪 Logout", key="nav_logout"): st.session_state.logged_in = False; st.rerun()

# --- 7. CALENDAR VIEW ---
if st.session_state.view == "CALENDAR":
    st.title("🗓️ CLP Training Calendar")
    col_cal, col_panel = st.columns([1, 1.5])
    
    with col_cal:
        # Month Navigation
        nav_p, nav_t, nav_n = st.columns([1, 3, 1])
        if nav_p.button("◀", key="cal_prev"): change_month(-1); st.rerun()
        nav_t.markdown(f"<h3 style='text-align:center;'>{calendar.month_name[st.session_state.cal_month]} {st.session_state.cal_year}</h3>", unsafe_allow_html=True)
        if nav_n.button("▶", key="cal_next"): change_month(1); st.rerun()

        cal_obj = calendar.Calendar(firstweekday=6)
        weeks = cal_obj.monthdayscalendar(st.session_state.cal_year, st.session_state.cal_month)
        
        events = c.execute("SELECT date_val FROM projects WHERE category='CAL'").fetchall()
        event_days = [str(e[0]) for e in events]

        h_cols = st.columns(7)
        for i, d in enumerate(['S','M','T','W','T','F','S']):
            h_cols[i].markdown(f"<p style='text-align:center; color:grey; font-size:12px;'>{d}</p>", unsafe_allow_html=True)

        for week in weeks:
            d_cols = st.columns(7)
            for i, day in enumerate(week):
                if day != 0:
                    d_str = f"{st.session_state.cal_year}-{st.session_state.cal_month:02d}-{day:02d}"
                    b_key = f"day_btn_{st.session_state.cal_year}_{st.session_state.cal_month}_{day}"
                    
                    if d_cols[i].button(str(day), key=b_key):
                        st.session_state.sel_cal_date = d_str
                        st.rerun()
                    
                    # Highlight CSS
                    border = "2px solid #43b581" if d_str in event_days else "1px solid #333"
                    bg = "#5865f2" if d_str == st.session_state.sel_cal_date else "transparent"
                    st.markdown(f"<style>button[key='{b_key}'] {{ border: {border} !important; background-color: {bg} !important; }}</style>", unsafe_allow_html=True)

    with col_panel:
        selected = st.session_state.sel_cal_date
        event = c.execute("SELECT * FROM projects WHERE category='CAL' AND date_val=?", (selected,)).fetchone()
        st.subheader(f"Details: {selected}")
        
        if is_lead:
            with st.form("cal_edit_form"):
                tz = st.text_input("Time Zone", value=event[9] if event else "EST")
                tm = st.text_input("Time", value=event[3] if event else "")
                lc = st.text_input("Location", value=event[10] if event else "")
                ms = st.text_area("What are we playing?", value=event[11] if event else "")
                if st.form_submit_button("Save Day Details"):
                    if event:
                        c.execute("UPDATE projects SET title=?, tz=?, location=?, mission=? WHERE id=?", (tm, tz, lc, ms, event[0]))
                    else:
                        c.execute("INSERT INTO projects (category, date_val, title, tz, location, mission, is_done) VALUES ('CAL',?,?,?,?,?,0)", (selected, tm, tz, lc, ms))
                    conn.commit(); st.rerun()
        elif event:
            st.info(f"⏰ **Time:** {event[3]} ({event[9]})\n\n📍 **Location:** {event[10]}\n\n🎮 **Mission:** {event[11]}")

# --- 8. REMAINING VIEWS (TASK/REPO/TUTORIAL) ---
elif "CREATE" in st.session_state.view or "FIX" in st.session_state.view:
    cat, sub = st.session_state.view.split("_")
    st.title(f"{cat} | {sub}")
    with st.expander("＋ New Mod Entry"):
        with st.form(f"task_f_{cat}_{sub}"):
            t = st.text_input("Mod Name")
            s = st.selectbox("Severity", ["Low", "Medium", "High", "Critical"])
            d = st.text_area("Details")
            if st.form_submit_button("Post"):
                c.execute("INSERT INTO projects (category, sub_category, title, details, author, importance, is_done) VALUES (?,?,?,?,?,?,0)", (cat, sub, t, d, st.session_state.user_name, s))
                conn.commit(); st.rerun()

    tasks = c.execute("SELECT * FROM projects WHERE category=? AND sub_category=? AND is_done=0", (cat, sub)).fetchall()
    for tk in tasks:
        with st.container(border=True):
            st.markdown(f"<div class='status-light light-{tk[6].lower()}'></div> **{tk[3]}**", unsafe_allow_html=True)
            st.write(tk[4]); 
            if st.button("Complete", key=f"tk_res_{tk[0]}"):
                c.execute("UPDATE projects SET is_done=1 WHERE id=?", (tk[0],)); conn.commit(); st.rerun()

elif st.session_state.view == "PLAYER_REPO":
    st.title("👤 Player Repository")
    with st.expander("＋ New Player"):
        with st.form("p_repo_f"):
            p_n = st.text_input("Name")
            p_s = st.text_area("Bio / Stats")
            if st.form_submit_button("Save"):
                c.execute("INSERT INTO projects (category, title, details) VALUES ('REPO', ?, ?)", (p_n, p_s)); conn.commit(); st.rerun()
    players = c.execute("SELECT * FROM projects WHERE category='REPO'").fetchall()
    for p in players:
        with st.expander(f"Player: {p[3]}"): st.write(p[4])

elif "TUTORIAL" in st.session_state.view:
    st.title("📚 Tutorials")
    if st.session_state.view == "TUTORIAL_POST":
        with st.form("tut_post_f"):
            t_t = st.text_input("Title")
            t_d = st.text_area("Guide")
            if st.form_submit_button("Publish"):
                c.execute("INSERT INTO projects (category, title, details) VALUES ('TUT', ?, ?)", (t_t, t_d)); conn.commit(); st.rerun()
    tuts = c.execute("SELECT * FROM projects WHERE category='TUT'").fetchall()
    for tu in tuts:
        with st.expander(tu[3]): st.write(tu[4])

else:
    st.markdown("<h1 style='font-weight:200; margin-top:10vh; font-size: 5vw;'>welcome back.</h1>", unsafe_allow_html=True)
