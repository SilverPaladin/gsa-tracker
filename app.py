import streamlit as st
import sqlite3

# --- DATABASE SETUP ---
conn = sqlite3.connect('gsa_discord_v2.db', check_same_thread=False)
c = conn.cursor()
c.execute('CREATE TABLE IF NOT EXISTS users (email TEXT UNIQUE)')
c.execute('CREATE TABLE IF NOT EXISTS categories (name TEXT UNIQUE)')
c.execute('''CREATE TABLE IF NOT EXISTS projects 
             (id INTEGER PRIMARY KEY, category TEXT, title TEXT, details TEXT, 
              assigned_user TEXT, is_done INTEGER)''')
conn.commit()

# --- DISCORD STYLING ---
st.markdown("""
<style>
    /* Sidebar Styling */
    [data-testid="stSidebar"] { background-color: #2f3136; }
    .stButton>button { width: 100%; border-radius: 4px; text-align: left; transition: 0.2s; }
    
    /* Category Headers */
    .cat-header { color: #8e9297; font-size: 11px; font-weight: 800; text-transform: uppercase; margin: 15px 0 5px 0; }
    
    /* Project Cards */
    .project-card-white { background-color: #ffffff; padding: 25px; border-radius: 10px; border-left: 8px solid #5865f2; color: #2e3338; margin-bottom: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
    .project-card-grey { background-color: #f2f3f5; padding: 25px; border-radius: 10px; border-left: 8px solid #b9bbbe; color: #747f8d; margin-bottom: 15px; }
</style>
""", unsafe_allow_html=True)

# --- NAVIGATION LOGIC ---
if "view" not in st.session_state: st.session_state.view = "home"
if "active_id" not in st.session_state: st.session_state.active_id = None

# --- SIDEBAR: DISCORD STYLE ---
with st.sidebar:
    st.title("💬 GSA Dash")
    if st.button("🏠 Home Server"):
        st.session_state.view = "home"
        st.rerun()
    
    st.divider()
    
    # List Categories
    c.execute("SELECT name FROM categories")
    cats = [r[0] for r in c.fetchall()]
    
    for cat in cats:
        col_name, col_plus = st.columns([5, 1])
        with col_name:
            st.markdown(f"<div class='cat-header'>{cat}</div>", unsafe_allow_html=True)
        with col_plus:
            if st.button("＋", key=f"add_to_{cat}"):
                st.session_state.view = "create_project"
                st.session_state.temp_cat = cat
                st.rerun()
        
        # List Projects under Category
        c.execute("SELECT id, title, is_done FROM projects WHERE category=?", (cat,))
        for pid, ptitle, pdone in c.fetchall():
            label = f"✅ {ptitle}" if pdone else f"# {ptitle}"
            if st.button(label, key=f"proj_{pid}"):
                st.session_state.active_id = pid
                st.session_state.view = "view_project"
                st.rerun()

    st.divider()
    if st.button("➕ Create New Category"):
        st.session_state.view = "create_category"
        st.rerun()

# --- MAIN CONTENT ---

# 1. HOME SCREEN (SPLASH)
if st.session_state.view == "home":
    st.title("Welcome back, User")
    st.markdown("### What would you like to do today?")
    
    col1, col2 = st.columns(2)
    # Fixed height error by using CSS containers instead of 'height' parameter
    with col1:
        st.info("### 🔳 Create New Task")
        if st.button("Launch Creation Tool", key="big_btn_1"):
            st.session_state.view = "create_project"
            st.rerun()
    with col2:
        st.success("### 📂 Open Existing Tasks")
        if st.button("Open Project List", key="big_btn_2"):
            # This logic just keeps them on Home but shows they can use the sidebar
            st.toast("Use the left sidebar to browse projects!", icon="👈")

# 2. CREATE CATEGORY
elif st.session_state.view == "create_category":
    st.title("New Category")
    cat_input = st.text_input("Category Name")
    if st.button("Add to Server"):
        c.execute("INSERT OR IGNORE INTO categories VALUES (?)", (cat_input,))
        conn.commit()
        st.session_state.view = "home"
        st.rerun()

# 3. CREATE PROJECT
elif st.session_state.view == "create_project":
    target = st.session_state.get("temp_cat", "General")
    st.title(f"New Project in {target}")
    with st.form("new_proj"):
        title = st.text_input("Task Title")
        details = st.text_area("Project Details (Supports Bullet Points & Bold)")
        # Searchable user list
        c.execute("SELECT email FROM users")
        u_list = [r[0] for r in c.fetchall()]
        assigned = st.selectbox("Assign User (Searchable)", ["Unassigned"] + u_list)
        
        if st.form_submit_button("Create"):
            c.execute("INSERT INTO projects (category, title, details, assigned_user, is_done) VALUES (?,?,?,?,?)",
                      (target, title, details, assigned, 0))
            conn.commit()
            st.session_state.view = "home"
            st.rerun()

# 4. VIEW PROJECT
elif st.session_state.view == "view_project":
    c.execute("SELECT * FROM projects WHERE id=?", (st.session_state.active_id,))
    p = c.fetchone()
    if p:
        style = "project-card-grey" if p[5] else "project-card-white"
        
        st.markdown(f"<div class='{style}'>", unsafe_allow_html=True)
        st.title(p[2])
        st.write(f"📂 **Category:** {p[1]} | 👤 **Assigned to:** {p[4]}")
        st.divider()
        st.markdown("### Project Details")
        st.markdown(p[3]) # Renders formatting like bullet points
        
        if not p[5]:
            if st.button("Mark Complete"):
                c.execute("UPDATE projects SET is_done=1 WHERE id=?", (p[0],))
                conn.commit()
                st.toast("Notification: Task Completed!", icon="🔔")
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
