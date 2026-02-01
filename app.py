import streamlit as st
import sqlite3

# --- DATABASE SETUP ---
conn = sqlite3.connect('gsa.db', check_same_thread=False)
c = conn.cursor()

c.execute('CREATE TABLE IF NOT EXISTS users (email TEXT UNIQUE, password TEXT)')
c.execute('CREATE TABLE IF NOT EXISTS categories (name TEXT UNIQUE)')
c.execute('''CREATE TABLE IF NOT EXISTS projects 
             (id INTEGER PRIMARY KEY, owner TEXT, category TEXT, title TEXT, 
              importance TEXT, notes TEXT, is_done INTEGER)''')
conn.commit()

# --- SESSION STATE ---
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
    st.session_state["user"] = None

# --- AUTHENTICATION UI ---
if not st.session_state["logged_in"]:
    st.title("🔐 Project Tracker Login")
    tab1, tab2 = st.tabs(["Login", "Create Account"])
    
    with tab2:
        new_email = st.text_input("Email Address", key="reg_email")
        new_pw = st.text_input("Password", type="password", key="reg_pw")
        if st.button("Sign Up"):
            if new_email and new_pw:
                try:
                    c.execute("INSERT INTO users VALUES (?,?)", (new_email, new_pw))
                    conn.commit()
                    st.success("Account created! Now go to the Login tab.")
                except:
                    st.error("That email is already registered.")
            else:
                st.warning("Please fill out both fields.")

    with tab1:
        login_email = st.text_input("Email", key="log_email")
        login_pw = st.text_input("Password", type="password", key="log_pw")
        if st.button("Login"):
            c.execute("SELECT * FROM users WHERE email=? AND password=?", (login_email, login_pw))
            # FIX: changed 'f' to 'c'
            user_record = c.fetchone()
            if user_record:
                st.session_state["logged_in"] = True
                st.session_state["user"] = login_email
                st.rerun()
            else:
                st.error("Invalid email or password.")

# --- MAIN APP ---
else:
    st.sidebar.title(f"👤 {st.session_state['user']}")
    if st.sidebar.button("Logout"):
        st.session_state["logged_in"] = False
        st.rerun()

    st.title("🏗️ GSA Project Software")

    with st.sidebar.expander("📁 Categories"):
        cat_name = st.text_input("New Category")
        if st.button("Add"):
            c.execute("INSERT OR IGNORE INTO categories VALUES (?)", (cat_name,))
            conn.commit()
            st.rerun()
    
    c.execute("SELECT name FROM categories")
    all_cats = [r[0] for r in c.fetchall()]

    with st.expander("➕ New Project"):
        p_title = st.text_input("Title")
        p_cat = st.selectbox("Category", all_cats if all_cats else ["General"])
        p_imp = st.select_slider("Priority", ["Low", "Med", "High"])
        p_notes = st.text_area("Notes")
        
        if st.button("Save Project"):
            c.execute("INSERT INTO projects (owner, category, title, importance, notes, is_done) VALUES (?,?,?,?,?,?)",
                      (st.session_state["user"], p_cat, p_title, p_imp, p_notes, 0))
            conn.commit()
            st.success("Project Saved!")
            st.rerun()

    st.header("📋 Your Projects")
    for cat in all_cats:
        with st.expander(f"📂 {cat}", expanded=True):
            c.execute("SELECT * FROM projects WHERE category=? AND owner=?", (cat, st.session_state["user"]))
            for p in c.fetchall():
                st.write(f"**{'✅' if p[6] else '⏳'} {p[3]}** | Priority: {p[4]}")
                st.markdown(p[5])
                if not p[6]:
                    if st.button("Mark Done", key=f"done_{p[0]}"):
                        c.execute("UPDATE projects SET is_done=1 WHERE id=?", (p[0],))
                        conn.commit()
                        st.rerun()
                st.divider()
