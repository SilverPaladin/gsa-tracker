import streamlit as st
import sqlite3

# --- DATABASE SETUP ---
conn = sqlite3.connect('gsa_discord.db', check_same_thread=False)
c = conn.cursor()
c.execute('CREATE TABLE IF NOT EXISTS categories (name TEXT UNIQUE)')
c.execute('''CREATE TABLE IF NOT EXISTS projects 
             (id INTEGER PRIMARY KEY, category TEXT, title TEXT, details TEXT, is_done INTEGER)''')
conn.commit()

# --- CSS FOR DISCORD LOOK ---
st.markdown("""
<style>
    [data-testid="stSidebar"] { background-color: #2f3136; color: white; }
    .stButton>button { width: 100%; border-radius: 5px; text-align: left; }
    .category-header { font-size: 12px; font-weight: bold; color: #8e9297; text-transform: uppercase; margin-top: 15px; display: flex; justify-content: space-between; }
    .project-card { background-color: white; padding: 20px; border-radius: 8px; color: black; border-left: 5px solid #5865f2; }
    .project-card-done { background-color: #f2f2f2; padding: 20px; border-radius: 8px; color: #72767d; border-left: 5px solid #b9bbbe; }
</style>
""", unsafe_allow_html=True)

# --- SESSION STATE ---
if "active_project" not in st.session_state: st.session_state.active_project = None
if "view" not in st.session_state: st.session_state.view = "home"

# --- SIDEBAR (DISCORD STYLE) ---
with st.sidebar:
    st.title("🎮 GSA Work")
    if st.button("🏠 Home"):
        st.session_state.active_project = None
        st.session_state.view = "home"
        st.rerun()

    st.divider()
    
    # Category Management
    c.execute("SELECT name FROM categories")
    all_cats = [r[0] for r in c.fetchall()]

    for cat in all_cats:
        # Header with small + icon
        col_cat, col_add = st.columns([4, 1])
        with col_cat:
            st.markdown(f"<div class='category-header'>{cat}</div>", unsafe_allow_html=True)
        with col_add:
            if st.button("➕", key=f"add_to_{cat}"):
                st.session_state.view = "create_project"
                st.session_state.target_cat = cat
                st.rerun()
        
        # Projects under this category
        c.execute("SELECT id, title, is_done FROM projects WHERE category=?", (cat,))
        for pid, ptitle, pdone in c.fetchall():
            prefix = "✅ " if pdone else "# "
            if st.button(f"{prefix} {ptitle}", key=f"nav_{pid}"):
                st.session_state.active_project = pid
                st.session_state.view = "project_view"
                st.rerun()

    st.divider()
    if st.button("➕ Create Category"):
        st.session_state.view = "create_category"
        st.rerun()

# --- MAIN CONTENT AREA ---

# 1. SPLASH SCREEN (HOME)
if st.session_state.view == "home":
    st.title("Welcome back, User")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔳\n\nCreate New Task", height=150):
            st.session_state.view = "create_project"
            st.rerun()
    with col2:
        if st.button("📂\n\nView All Tasks", height=150):
            st.session_state.active_project = None # Logic to show list
            st.rerun()

# 2. CREATE CATEGORY
elif st.session_state.view == "create_category":
    st.subheader("New Category")
    new_cat_name = st.text_input("Name")
    if st.button("Save Category"):
        c.execute("INSERT OR IGNORE INTO categories VALUES (?)", (new_cat_name,))
        conn.commit()
        st.session_state.view = "home"
        st.rerun()

# 3. CREATE PROJECT
elif st.session_state.view == "create_project":
    st.subheader(f"New Project in {st.session_state.get('target_cat', 'General')}")
    p_title = st.text_input("Project Name")
    p_details = st.text_area("Project Details (Markdown supported)")
    if st.button("Create Project"):
        cat = st.session_state.get('target_cat', 'General')
        c.execute("INSERT INTO projects (category, title, details, is_done) VALUES (?,?,?,?)", (cat, p_title, p_details, 0))
        conn.commit()
        st.session_state.view = "home"
        st.rerun()

# 4. PROJECT VIEW (SELECTED)
elif st.session_state.view == "project_view":
    c.execute("SELECT * FROM projects WHERE id=?", (st.session_state.active_project,))
    proj = c.fetchone()
    if proj:
        style = "project-card-done" if proj[4] else "project-card"
        st.markdown(f"<div class='{style}'>", unsafe_allow_html=True)
        st.title(proj[2])
        st.caption(f"Category: {proj[1]}")
        st.markdown("### Project Details")
        st.markdown(proj[3])
        
        if not proj[4]:
            if st.button("Mark as Complete"):
                c.execute("UPDATE projects SET is_done=1 WHERE id=?", (proj[0],))
                conn.commit()
                st.toast("Project completed!")
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
