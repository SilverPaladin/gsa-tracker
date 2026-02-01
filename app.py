import streamlit as st
import sqlite3
from datetime import datetime, date
import calendar

# --- 1. DATABASE (Fresh Start) ---
conn = sqlite3.connect('gsa_command_v30.db', check_same_thread=False)
c = conn.cursor()
c.execute('CREATE TABLE IF NOT EXISTS users (email TEXT UNIQUE, password TEXT, username TEXT, role TEXT)')
c.execute('''CREATE TABLE IF NOT EXISTS projects 
             (id INTEGER PRIMARY KEY AUTOINCREMENT, category TEXT, date_val TEXT, title TEXT, location TEXT, mission TEXT)''')
conn.commit()

# --- 2. SESSION STATE ---
if "view" not in st.session_state: st.session_state.view = "CALENDAR"
if "sel_date" not in st.session_state: st.session_state.sel_date = date.today()

# --- 3. THEME (Simplified) ---
st.set_page_config(page_title="GSA Command", layout="wide")
st.markdown("""
<style>
    [data-testid="stSidebar"] { background-color: #0e0e10 !important; }
    .stButton>button { width: 100%; border-radius: 4px; }
</style>
""", unsafe_allow_html=True)

# --- 4. SIDEBAR (Your Requested Categories Only) ---
with st.sidebar:
    st.title("✨ GSA HQ")
    
    with st.expander("📁 Server To Do List", expanded=True):
        if st.button("💬 master-list"): st.session_state.view = "MASTER"; st.rerun()
        if st.button("# bug-discussion"): st.session_state.view = "BUGS"; st.rerun()
    
    with st.expander("📅 CLP PANEL", expanded=True):
        if st.button("# training-calendar"): st.session_state.view = "CALENDAR"; st.rerun()
        if st.button("# tutorials"): st.session_state.view = "TUTS"; st.rerun()

    with st.expander("🛡️ ADMIN", expanded=True):
        if st.button("# player-repository"): st.session_state.view = "REPO"; st.rerun()

# --- 5. THE CALENDAR (Reliable Logic) ---
if st.session_state.view == "CALENDAR":
    st.header("🗓️ CLP Training Calendar")
    
    col_cal, col_form = st.columns([1.5, 1])

    with col_cal:
        # We use the built-in date_input as the "Master Selector"
        # This is 100% reliable and cannot break like custom grids
        selected = st.date_input("Select a date to view/edit:", value=st.session_state.sel_date)
        st.session_state.sel_date = selected
        
        st.divider()
        st.subheader(f"Schedule for {selected.strftime('%A, %b %d, %Y')}")
        
        # Fetch data for the selected day
        ev = c.execute("SELECT * FROM projects WHERE category='CAL' AND date_val=?", (str(selected),)).fetchone()
        
        if ev:
            st.info(f"**Time:** {ev[3]}  \n**Location:** {ev[4]}  \n**Mission:** {ev[5]}")
            if st.button("🗑️ Delete Event"):
                c.execute("DELETE FROM projects WHERE id=?", (ev[0],))
                conn.commit()
                st.rerun()
        else:
            st.warning("No training scheduled for this date.")

    with col_form:
        st.subheader("Edit/Create Event")
        with st.form("event_editor", clear_on_submit=False):
            new_time = st.text_input("Time (e.g. 20:00 EST)", value=ev[3] if ev else "")
            new_loc = st.text_input("Location", value=ev[4] if ev else "")
            new_miss = st.text_area("Mission Details", value=ev[5] if ev else "")
            
            submit = st.form_submit_button("Save to Calendar")
            if submit:
                if ev:
                    c.execute("UPDATE projects SET title=?, location=?, mission=? WHERE id=?", 
                              (new_time, new_loc, new_miss, ev[0]))
                else:
                    c.execute("INSERT INTO projects (category, date_val, title, location, mission) VALUES ('CAL',?,?,?,?)", 
                              (str(selected), new_time, new_loc, new_miss))
                conn.commit()
                st.success("Changes saved!")
                st.rerun()

# --- 6. OTHER VIEWS ---
elif st.session_state.view == "MASTER":
    st.title("💬 Master To-Do List")
    st.write("Content for Master List goes here.")

elif st.session_state.view == "BUGS":
    st.title("# Bug Discussion")
    st.write("Content for Bug Discussion goes here.")

else:
    st.title(st.session_state.view)
    st.write("Section under construction.")
