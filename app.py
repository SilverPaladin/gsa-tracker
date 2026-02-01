import streamlit as st
import sqlite3
from datetime import datetime

# --- PAGE CONFIG ---
st.set_page_config(page_title="GSA Pro-Tracker", layout="wide", initial_sidebar_state="expanded")

# --- DATABASE UPGRADES ---
conn = sqlite3.connect('gsa_pro.db', check_same_thread=False)
c = conn.cursor()
c.execute('CREATE TABLE IF NOT EXISTS users (email TEXT UNIQUE, password TEXT)')
c.execute('CREATE TABLE IF NOT EXISTS categories (name TEXT UNIQUE)')
c.execute('''CREATE TABLE IF NOT EXISTS projects 
             (id INTEGER PRIMARY KEY, owner TEXT, assigned_to TEXT, category TEXT, 
              title TEXT, importance TEXT, details TEXT, is_done INTEGER)''')
c.execute('CREATE TABLE IF NOT EXISTS comments (id INTEGER PRIMARY KEY, project_id INTEGER, user TEXT, msg TEXT, timestamp TEXT)')
conn.commit()

# --- CUSTOM CSS FOR STYLING ---
st.markdown("""
<style>
    .project-card-white { background-color: #ffffff; padding: 20px; border-radius: 10px; border: 1px solid #ddd; margin-bottom: 10px; color: black; }
    .project-card-grey { background-color: #e0e0e0; padding: 20px; border-radius: 10px; border: 1px solid #bbb; margin-bottom: 10px; color: #777; }
    .splash-card { background: #262730; color: white; padding: 50px; border-radius: 15px; text-align: center; cursor: pointer; transition: 0.3s; }
    .splash-card:hover { background: #ff4b4b; }
</style>
""", unsafe_allow_html=True)

# --- SESSION STATE INITIALIZATION ---
if "page" not in st.session_state: st.session_state.page = "splash"
if "logged_in" not in st.session_state: st.session_state.logged_in = False

# --- SPLASH SCREEN ---
if st.session_state.page == "splash":
    st.title("🌟 GSA Welcome Screen")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔳 CREATE NEW TASK", use_container_width=True):
            st.session_state.page = "app"
            st.session_state.auto_open_add = True
            st.rerun()
            
    with col2:
        if st.button("🗂️ OPEN EXISTING TASKS", use_container_width=True):
            st.session_state.page = "app"
            st.rerun()
    st.stop()

# --- MAIN APP LOGIC ---
if st.session_state.page == "app":
    # Sidebar Searchable User Dropdown
    c.execute("SELECT email FROM users")
    user_list = [r[0] for r in c.fetchall()]
    
    with st.sidebar:
        st.title("🍔 Menu")
        if st.button("⬅️ Back to Splash"): 
            st.session_state.page = "splash"
            st.rerun()
        
        st.divider()
        st.header("Project Tree")
        c.execute("SELECT name FROM categories")
        categories = [r[0] for r in c.fetchall()]
        
        selected_cat = st.radio("Categories", ["All"] + categories)

    # Project Creation Form
    with st.expander("➕ Create a New Task", expanded=st.session_state.get("auto_open_add", False)):
        t_title = st.text_input("Project Name")
        t_assign = st.selectbox("Assign Project to User (Searchable)", ["Unassigned"] + user_list)
        t_cat = st.selectbox("Category", categories if categories else ["General"])
        t_details = st.text_area("Project Details", help="Supports **Bold**, *Italics*, and - Bullet Points")
        
        if st.button("Launch Project"):
            c.execute("INSERT INTO projects (owner, assigned_to, category, title, importance, details, is_done) VALUES (?,?,?,?,?,?,?)",
                      ("Admin", t_assign, t_cat, t_title, "Medium", t_details, 0))
            conn.commit()
            st.toast(f"New Project Created: {t_title}", icon="🚀")
            st.rerun()

    # The Project List
    st.header(f"Showing: {selected_cat}")
    query = "SELECT * FROM projects" if selected_cat == "All" else f"SELECT * FROM projects WHERE category='{selected_cat}'"
    c.execute(query)
    
    for p in c.fetchall():
        card_style = "project-card-grey" if p[7] else "project-card-white"
        
        with st.container():
            st.markdown(f"<div class='{card_style}'>", unsafe_allow_html=True)
            col_txt, col_btn = st.columns([4,1])
            with col_txt:
                st.subheader(f"{p[4]}")
                st.write(f"👤 **Responsible:** {p[2]}")
                st.markdown(p[6]) # Renders Markdown details
            with col_btn:
                if not p[7]:
                    if st.button("Mark Complete", key=f"done_{p[0]}"):
                        c.execute("UPDATE projects SET is_done=1 WHERE id=?", (p[0],))
                        conn.commit()
                        st.toast(f"Project '{p[4]}' is Finished!", icon="✅")
                        st.rerun()
            
            # --- CHAT SECTION ---
            with st.expander("💬 Comments & Chat"):
                c.execute("SELECT user, msg, timestamp FROM comments WHERE project_id=?", (p[0],))
                for com in c.fetchall():
                    st.caption(f"**{com[0]}** ({com[2]}): {com[1]}")
                
                new_msg = st.text_input("Add a comment...", key=f"msg_{p[0]}")
                if st.button("Send", key=f"send_{p[0]}"):
                    ts = datetime.now().strftime("%H:%M")
                    c.execute("INSERT INTO comments (project_id, user, msg, timestamp) VALUES (?,?,?,?)",
                              (p[0], "User", new_msg, ts))
                    conn.commit()
                    st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)
            st.divider()
