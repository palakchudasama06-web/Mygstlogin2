import streamlit as st
import pandas as pd
import io
import time
import json
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.os_manager import ChromeType

# -----------------------------------------------------------------------------
# DATABASE MANAGEMENT (LOCAL JSON)
# -----------------------------------------------------------------------------
DB_FILE = "database.json"

def load_db():
    try:
        with open(DB_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_db(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=4)

db = load_db()

# -----------------------------------------------------------------------------
# PAGE CONFIGURATION & METALLIC CSS
# -----------------------------------------------------------------------------
st.set_page_config(page_title="GST Login Tool - Palak Chudasama", page_icon="⚖️", layout="wide")

metallic_gold_css = """
<style>
    .stApp { background: linear-gradient(135deg, #111317 0%, #1e2229 50%, #121418 100%); color: #e0e6ed; }
    header, footer { visibility: hidden; }
    .gold-title { background: linear-gradient(45deg, #bf953f, #fcf6ba, #b38728, #fbf5b7, #aa771c); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-size: 2.3rem !important; font-weight: 800 !important; }
    .tagline { color: #a0aab5; font-size: 1rem; font-style: italic; margin-top: -5px; }
    .header-box { background: linear-gradient(145deg, #1f232b, #15171c); border-bottom: 2px solid #d4af37; border-radius: 8px; padding: 15px 25px; margin-bottom: 25px; display: flex; justify-content: space-between; align-items: center; }
    .client-card { background: linear-gradient(145deg, #1d2128, #17191f); border: 1px solid #2e3440; border-left: 4px solid #d4af37; border-radius: 8px; padding: 18px 22px; margin-bottom: 12px; }
    .stButton > button { background: linear-gradient(180deg, #d4af37 0%, #996e19 100%) !important; color: #0b0c0e !important; font-weight: 700 !important; border-radius: 6px !important; }
    .stButton > button:hover { background: linear-gradient(180deg, #ffffff 0%, #d4af37 100%) !important; color: #000000 !important; }
</style>
"""
st.markdown(metallic_gold_css, unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# SESSION STATE SETUP FOR CLOUD RELAY
# -----------------------------------------------------------------------------
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'username' not in st.session_state:
    st.session_state['username'] = ''
if 'driver' not in st.session_state:
    st.session_state['driver'] = None
if 'captcha_image' not in st.session_state:
    st.session_state['captcha_image'] = None
if 'active_gst_id' not in st.session_state:
    st.session_state['active_gst_id'] = None

# -----------------------------------------------------------------------------
# CLOUD SELENIUM AUTOMATION (USING CHROMIUM)
# -----------------------------------------------------------------------------
def init_headless_browser(gst_id, password):
    st.info("Initializing secure cloud browser... Please wait.")
    
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    
    try:
        # Automatically downloads and configures Linux Chromium driver on Streamlit Cloud
        service = Service(ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        driver.get("https://services.gst.gov.in/services/login")
        time.sleep(3)
        
        driver.find_element(By.ID, "username").send_keys(str(gst_id))
        driver.find_element(By.ID, "user_pass").send_keys(str(password))
        
        captcha_element = driver.find_element(By.ID, "imgCaptcha")
        captcha_screenshot = captcha_element.screenshot_as_png
        
        st.session_state['driver'] = driver
        st.session_state['captcha_image'] = captcha_screenshot
        st.session_state['active_gst_id'] = gst_id
        st.rerun()
        
    except Exception as e:
        st.error(f"Cloud Server Error: {str(e)}")
        if 'driver' in st.session_state and st.session_state['driver']:
            st.session_state['driver'].quit()
            st.session_state['driver'] = None

def submit_captcha(captcha_text):
    driver = st.session_state['driver']
    if driver:
        try:
            driver.find_element(By.ID, "captcha").send_keys(captcha_text)
            login_btn = driver.find_element(By.XPATH, "//button[contains(text(),'Login')]")
            driver.execute_script("arguments[0].click();", login_btn)
            time.sleep(3)
            
            result_screenshot = driver.get_screenshot_as_png()
            st.success("Login action submitted to GST portal!")
            st.image(result_screenshot, caption="Live Server Screen Capture")
            
            driver.quit()
            st.session_state['driver'] = None
            st.session_state['captcha_image'] = None
            st.session_state['active_gst_id'] = None
            
        except Exception as e:
            st.error(f"Login action failed: {str(e)}")
            driver.quit()
            st.session_state['driver'] = None

# -----------------------------------------------------------------------------
# LOGIN SCREEN
# -----------------------------------------------------------------------------
if not st.session_state['logged_in']:
    st.markdown("<br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.8, 1])
    with col2:
        st.markdown("""
            <div class="header-box" style="justify-content: center; flex-direction: column;">
                <h1 class="gold-title">GST LOGIN TOOL</h1>
                <p class="tagline">Palak Chudasama</p>
            </div>
        """, unsafe_allow_html=True)
        
        user_input = st.text_input("Username")
        pass_input = st.text_input("Password", type="password")
        
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.button("SIGN IN", use_container_width=True):
                if user_input in db and db[user_input]["password"] == pass_input:
                    st.session_state['logged_in'] = True
                    st.session_state['username'] = user_input
                    st.rerun()
                else:
                    st.error("Invalid credentials.")
        with col_btn2:
            if st.button("REGISTER", use_container_width=True):
                if user_input and pass_input and user_input not in db:
                    db[user_input] = {"password": pass_input, "clients": []}
                    save_db(db)
                    st.success("Registered! Please Sign In.")

# -----------------------------------------------------------------------------
# MAIN DASHBOARD
# -----------------------------------------------------------------------------
else:
    current_user = st.session_state['username']
    client_df = pd.DataFrame(db[current_user].get("clients", []))
    if client_df.empty:
        client_df = pd.DataFrame(columns=["Client Name", "GST ID", "Password"])

    st.markdown(f"""
        <div class="header-box">
            <div><h1 class="gold-title">GST Login Tool</h1><div class="tagline">Palak Chudasama</div></div>
            <div style="color: #fcf6ba; font-weight: bold;">👤 {current_user}</div>
        </div>
    """, unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["🏛️ CLIENT DIRECTORY & LOGIN", "⚙️ DATA MANAGEMENT"])

    with tab1:
        if st.session_state['captcha_image'] is not None:
            st.warning(f"Active Session: {st.session_state['active_gst_id']}")
            st.write("The cloud server has reached the GST portal. Please enter the CAPTCHA below.")
            
            col_cap1, col_cap2 = st.columns([1, 2])
            with col_cap1:
                st.image(st.session_state['captcha_image'], caption="Live GST Captcha")
            with col_cap2:
                captcha_input = st.text_input("Enter Captcha Text:")
                if st.button("SUBMIT TO GST PORTAL", use_container_width=True):
                    submit_captcha(captcha_input)
            
            if st.button("Cancel Session"):
                st.session_state['driver'].quit()
                st.session_state['driver'] = None
                st.session_state['captcha_image'] = None
                st.rerun()
        else:
            if client_df.empty:
                st.info("No clients found. Go to 'DATA MANAGEMENT' to upload data.")
            else:
                for idx, row in client_df.iterrows():
                    c_name, c_id, c_pass = row.get("Client Name", ""), row.get("GST ID", ""), row.get("Password", "")
                    if not str(c_id).strip(): continue

                    col_info, col_btn = st.columns([3.5, 1.2])
                    with col_info:
                        st.markdown(f"""
                            <div class="client-card">
                                <div style="font-size: 1.15rem; font-weight: 700; color: #fcf6ba;">{c_name}</div>
                                <div style="color: #a0aab5; font-size: 0.9rem;">GST ID: {c_id}</div>
                            </div>
                        """, unsafe_allow_html=True)
                    with col_btn:
                        st.write("") 
                        if st.button(f"CONNECT SERVER 🚀", key=f"btn_{idx}", use_container_width=True):
                            init_headless_browser(c_id, c_pass)

    with tab2:
        uploaded_file = st.file_uploader("Upload client sheet (Name, GST ID, Password)", type=['xlsx', 'xls'])
        if uploaded_file:
            new_df = pd.read_excel(uploaded_file)
            new_df.columns = ["Client Name", "GST ID", "Password"]
            db[current_user]["clients"] = new_df.to_dict('records')
            save_db(db)
            st.success("Uploaded!")
            time.sleep(0.5)
            st.rerun()

        st.write("---")
        edited_df = st.data_editor(client_df, num_rows="dynamic", use_container_width=True)
        if not edited_df.equals(client_df):
            db[current_user]["clients"] = edited_df.to_dict('records')
            save_db(db)