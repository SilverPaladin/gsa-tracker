import streamlit as st
from streamlit_quill import st_quill
import pandas as pd
from datetime import datetime

# --- CONFIG & SESSIONS ---
st.set_page_config(page_title="Arma Staff Portal", layout="wide")

# Mock User Login (In a real app, use Streamlit Authenticator)
# For now, we simulate you are logged in
USER_EMAIL = "armasupplyguy@gmail.com"

if "role_db" not in st.session_state:
    st.session_state.role_db = {
        "armasupplyguy@gmail.com": "SUPER_ADMIN",
        "staff1@gmail.com": "admin",
        "lead1@gmail.com": "CLPLEAD",
        "player1@gmail.com": "CLP"
    }

if "mods" not in st.session_state:
    st.session_state.mods = []

if "events" not in st.session_state:
    st.session_state.events = []

if "tutorials" not in st.session_state:
    st.session_state.tutorials = []

user_role = st.session_state.role_db.get(USER_EMAIL, "CLP")

# --- HELPER: SIDEBAR LIGHT LOGIC ---
def get_mod_status():
    if not st.session_state.mods:
        return "🟢"
    incomplete = any(not m['complete'] for m in st.session_state.mods)
    return "🔴" if incomplete else "🟢"

# --- SIDEBAR MENU ---
st.sidebar.title("🛠 Staff Portal")
st.sidebar.write(f"Logged in as: **{USER_EMAIL}**")
st.sidebar.divider()

menu_options = []

# Category: Server Admin
if user_role in ["admin", "SUPER_ADMIN"]:
    st.sidebar.subheader("Server Admin")
    mod_light = get_mod_status()
    if st.sidebar.button(f"{mod_light} Broken Mods"):
        st.session_state.page = "broken_mods"

# Category: CLP LEAD
st.sidebar.subheader("CLP Management")
if user_role in ["CLPLEAD", "SUPER_ADMIN", "CLP"]:
    if st.sidebar.button("📅 Events"):
        st.session_state.page = "events"
    if st.sidebar.button("📚 Tutorials"):
        st.session_state.page = "tutorials"

# Super Admin Only
if user_role == "SUPER_ADMIN":
    st.sidebar.divider()
    if st.sidebar.button("🔑 Assign Roles"):
        st.session_state.page = "roles"

# --- PAGE: BROKEN MODS ---
if st.session_state.get("page") == "broken_mods":
    st.title("Broken Mods Tracker")
    
    with st.expander("➕ Report New Broken Mod"):
        name = st.text_input("Mod Name")
        severity = st.select_slider("Severity", options=range(1, 11))
        assignment = st.text_input("Assign to User")
        st.write("Description (Rich Text):")
        desc = st_quill(placeholder="Describe the issue...", key="new_mod_desc")
        
        if st.button("Add to List"):
            st.session_state.mods.append({
                "name": name, "severity": severity, "assignment": assignment,
                "description": desc, "complete": False, "id": len(st.session_state.mods)
            })
            st.rerun()

    for i, mod in enumerate(st.session_state.mods):
        with st.container(border=True):
            col1, col2 = st.columns([4, 1])
            with col1:
                st.subheader(f"{'✅' if mod['complete'] else '❌'} {mod['name']}")
                st.markdown(mod['description'], unsafe_allow_html=True)
                st.caption(f"Assigned to: {mod['assignment']} | Severity: {mod['severity']}")
            with col2:
                if st.checkbox("Complete", value=mod['complete'], key=f"check_{i}"):
                    st.session_state.mods[i]['complete'] = True
                else:
                    st.session_state.mods[i]['complete'] = False
                if st.button("🗑️", key=f"del_{i}"):
                    st.session_state.mods.pop(i)
                    st.rerun()

# --- PAGE: EVENTS ---
elif st.session_state.get("page") == "events":
    st.title("CLP Events Calendar")
    
    if user_role in ["CLPLEAD", "SUPER_ADMIN"]:
        with st.expander("📅 Create New Event"):
            e_name = st.text_input("Event Name")
            e_date = st.date_input("Date")
            e_time = st.time_input("Time")
            e_tz = st.selectbox("Timezone", ["UTC", "EST", "PST", "GMT"])
            e_loc = st.text_input("Location (Server/Discord)")
            st.write("Event Details (Rich Text):")
            e_desc = st_quill(key="event_quill")
            
            if st.button("Publish Event"):
                st.session_state.events.append({
                    "name": e_name, "date": str(e_date), "time": str(e_time),
                    "tz": e_tz, "loc": e_loc, "desc": e_desc
                })
                st.success("Event Published!")

    for event in st.session_state.events:
        with st.chat_message("event"):
            st.write(f"### {event['name']}")
            st.write(f"🕒 {event['date']} at {event['time']} ({event['tz']}) | 📍 {event['loc']}")
            st.markdown(event['desc'], unsafe_allow_html=True)

# --- PAGE: ROLE MANAGEMENT ---
elif st.session_state.get("page") == "roles":
    st.title("Super Admin: Role Management")
    new_email = st.text_input("User Email")
    new_role = st.selectbox("Assign Role", ["admin", "CLPLEAD", "CLP"])
    if st.button("Update Role"):
        st.session_state.role_db[new_email] = new_role
        st.success(f"Updated {new_email} to {new_role}")
    
    st.table(pd.DataFrame(st.session_state.role_db.items(), columns=["Email", "Role"]))
