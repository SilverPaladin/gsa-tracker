import streamlit as st
import sqlite3

# --- DATABASE SETUP ---
conn = sqlite3.connect('gsa_vision_2026.db', check_same_thread=False)
c = conn.cursor()
c.execute('CREATE TABLE IF NOT EXISTS users (email TEXT UNIQUE, password TEXT, username TEXT)')
conn.commit()

# --- IPHONE GLASS CHIC CSS ---
st.markdown("""
<style>
    /* Dark Gradient Background */
    .main { 
        background: radial-gradient(circle at top right, #2b2b4b, #000000); 
        color: white; 
    }

    /* Glass Tile Styling */
    .glass-tile {
        background: rgba(255, 255, 255, 0.03);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 30px;
        padding: 50px 20px;
        text-align: center;
        transition: all 0.4s ease-in-out;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
    }
    
    .glass-tile:hover {
        background: rgba(255, 255, 255, 0.08);
        border: 1px solid rgba(255, 255, 255, 0.3);
        transform: translateY(-10px);
        box-shadow: 0 12px 40px 0 rgba(88, 101, 242, 0.2);
    }

    /* Icon Styling */
    .tile-icon {
        font-size: 50px;
        margin-bottom: 15px;
        display: block;
    }

    .tile-text {
        font-family: 'SF Pro Display', -apple-system, sans-serif;
        font-weight: 200;
        letter-spacing: 1px;
        color: #ffffff;
    }
</style>
""", unsafe_allow_html=True)

# --- SESSION STATE ---
if "logged_in" not in st.session_state: st.session_state.logged_in = False
if "user_name" not in st.session_state: st.session_state.user_name = ""
if "view" not in st.session_state: st.session_state.view = "home"

# --- LOGIN (Simplified for focus on Splash) ---
if not st.session_state.logged_in:
    # ... (Keep your current login logic here)
    st.title("GSA SECURE ACCESS")
    # For testing, let's bypass if you're struggling to log in
    if st.button("DEBUG: BYPASS TO SPLASH"):
        st.session_state.logged_in = True
        st.session_state.user_name = "Admin"
        st.rerun()
    st.stop()

# --- THE CHIC SPLASH SCREEN ---
if st.session_state.view == "home":
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown(f"<h1 style='text-align: center; font-weight: 100; font-size: 50px;'>Welcome, {st.session_state.user_name}</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; opacity: 0.5;'>System Status: Online</p>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    col1, col2 = st.columns(2, gap="large")

    with col1:
        st.markdown("""
            <div class='glass-tile'>
                <span class='tile-icon'>⊕</span>
                <h2 class='tile-text'>NEW TASK</h2>
            </div>
        """, unsafe_allow_html=True)
        if st.button("Launch Pipeline", key="btn_new", use_container_width=True):
            st.session_state.view = "create_project"
            st.rerun()

    with col2:
        st.markdown("""
            <div class='glass-tile'>
                <span class='tile-icon'>▤</span>
                <h2 class='tile-text'>ARCHIVE</h2>
            </div>
        """, unsafe_allow_html=True)
        if st.button("Browse Vault", key="btn_view", use_container_width=True):
            st.toast("Select a project from the sidebar to begin.")

    st.markdown("<br><br>", unsafe_allow_html=True)
    if st.button("Logout", type="secondary"):
        st.session_state.logged_in = False
        st.rerun()
