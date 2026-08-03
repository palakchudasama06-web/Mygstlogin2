import streamlit as st
import pandas as pd
import io
import time
import os
import json
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.os_manager import ChromeType

# -----------------------------------------------------------------------------
# 1. DATABASE MANAGEMENT (LOCAL JSON FILE)
# -----------------------------------------------------------------------------
DB_FILE = "database.json"

def load_db():
    """Loads the database from the local JSON file."""
    if not os.path.exists(DB_FILE):
        return {}
    with open(DB_FILE, "r") as f:
        return json.load(f)

def save_db(data):
    """Saves the database back to the local JSON file."""
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=4)

db = load_db()

# -----------------------------------------------------------------------------
# PAGE CONFIGURATION & CUSTOM CSS
# -----------------------------------------------------------------------------
st.set_page_config(page_title="GST Login Tool - Palak Chudasama", page_icon="⚖️", layout="wide", initial_sidebar_state="collapsed")

metallic_gold_css = """
<style>
    .stApp { background: linear-gradient(135deg, #111317 0%, #1e2229 50%, #121418 100%); color: #e0e6ed; font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; }
    header, footer { visibility: hidden; }
    .gold-title { background: linear-gradient(45deg, #bf953f, #fcf6ba, #b38728, #fbf5b7, #aa771c); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-size: 2.3rem !important; font-weight: 800 !important; letter-spacing: 1.5px; margin: 0; }
    .tagline { color: #a0aab5; font-size: 1rem; font-style: italic; letter-spacing: 1px; margin-top: -5px; }
    .header-box { background: linear-gradient(145deg, #1f232b, #15171c); border-bottom: 2px solid #d4af37; border-radius: 8px; padding: 15px 25px; margin-bottom: 25px; box-shadow: 0 4px 20px rgba(0, 0, 0, 0.6); display: flex; justify-content: space-between; align-items: center; }
    .user-badge { background: linear-gradient(135deg, #2a2e38, #1c1f26); border: 1px solid #d4af37; border-radius: 20px; padding: 6px 16px; color: #fcf6ba; font-weight: 600; font-size: 0.9rem; }
    .client-card { background: linear-gradient(145deg, #1d2128, #17191f); border: 1px solid #2e3440; border-left: 4px solid #d4af37; border-radius: 8px; padding: 18px 22px; margin-bottom: 12px; box-shadow: 3px 3px 10px rgba(0,0,0,0.4); transition: all 0.3s ease-in-out; }
    .client-card:hover { border-color: #d4af37; box-shadow: 0 0 15px rgba(212, 175, 55, 0.25); transform: translateY(-2px); }
    .stButton > button { background: linear-gradient(180deg, #d4af37 0%, #996e19 100%) !important; color: #0b0c0e !important; font-weight: 700 !important; border: 1px solid #fcf6ba !important; border-radius: 6px !important; padding: 8px 18px !important; text-transform: uppercase; letter-spacing: 0.5px; box-shadow: 0 4px 10px rgba(0, 0, 0, 0.4); transition: all 0.2s ease; }
    .stButton > button:hover { background: linear-gradient(180deg, #ffffff 0%, #d4af37 100%) !important; color: #000000 !important; box-shadow: 0 0 12px rgba(212, 175, 55, 0.8); cursor: pointer; }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; border-bottom: 1px solid #333945; }
    .stTabs [data-baseweb="tab"] { background: #17191f; border-radius: 6px 6px 0 0; color: #a0aab5; font-weight: 600; padding: 10px 20px; }
    .stTabs [aria-selected="true"] { background: linear-gradient(180deg, #2a2e38 0%, #1c1f26 100%) !important; color: #fcf6ba !important; border-top: 2px solid #d4af37 !important; }
    .stTextInput input { background-color: #15171c !important; color: #ffffff !important; border: 1px solid #3a404d !important; border-radius: 6px !important; }
    .stTextInput input:focus { border-color: #d4af37 !important; box-shadow: 0 0 8px rgba(212, 175, 55, 0.4) !important; }
</style>
"""
st.markdown(metallic_gold_css, unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# SESSION STATE SETUP
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
# CLOUD AUTOMATION FUNCTION (HEADLESS RELAY FOR STREAMLIT CLOUD)
# -----------------------------------------------------------------------------
def init_headless_browser(gst_id, password):
    st.info(f"⚡ Initializing cloud browser for GST ID: {gst_id}... Please wait.")
    
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    
    try:
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
        st.error(f"❌ Cloud Server Error: {str(e)}")
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
            st.success("✅ Login action submitted to GST portal!")
            st.image(result_screenshot, caption="Live Server Screen Capture")
            
            driver.quit()
            st.session_state['driver'] = None
            st.session_state['captcha_image'] = None
            st.session_state['active_gst_id'] = None
            
        except Exception as e:
            st.error(f"❌ Login action failed: {str(e)}")
            driver.quit()
            st.session_state['driver'] = None
            st.session_state['captcha_image'] = None
            st.session_state['active_gst_id'] = None

# -----------------------------------------------------------------------------
# LOGIN & REGISTRATION SCREEN
# -----------------------------------------------------------------------------
if not st.session_state['logged_in']:
    st.markdown("<br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.8, 1])
    
    with col2:
        st.markdown("""
            <div style="text-align: center; background: linear-gradient(145deg, #1d2128, #15171c); padding: 30px; border-radius: 12px; border: 1px solid #d4af37; box-shadow: 0 10px 30px rgba(0,0,0,0.7);">
                <h1 class="gold-title" style="font-size: 2rem !important;">GST LOGIN TOOL</h1>
                <p class="tagline">Palak Chudasama</p>
                <hr style="border-color: #333945; margin-bottom: 25px;">
            </div>
        """, unsafe_allow_html=True)
        
        st.write("")
        user_input = st.text_input("Software Username", placeholder="Enter your username")
        pass_input = st.text_input("Software Password", type="password", placeholder="Enter your password")
        
        st.write("")
        
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.button("SIGN IN", use_container_width=True):
                if user_input and pass_input:
                    if user_input in db and db[user_input]["password"] == pass_input:
                        st.session_state['logged_in'] = True
                        st.session_state['username'] = user_input
                        st.rerun()
                    else:
                        st.error("Incorrect Username or Password.")
                else:
                    st.warning("Please enter credentials.")
        
        with col_btn2:
            if st.button("CREATE NEW ACCOUNT", use_container_width=True):
                if user_input and pass_input:
                    if user_input in db:
                        st.warning("Username already exists! Please log in.")
                    else:
                        db[user_input] = {
                            "password": pass_input,
                            "clients": []
                        }
                        save_db(db)
                        st.success("Account created! You can now Sign In.")
                else:
                    st.warning("Please type a Username and Password to register.")

# -----------------------------------------------------------------------------
# MAIN DASHBOARD
# -----------------------------------------------------------------------------
else:
    current_user = st.session_state['username']
    
    user_clients_list = db[current_user].get("clients", [])
    if not user_clients_list:
        client_df = pd.DataFrame(columns=["Client Name", "GST ID", "Password"])
    else:
        client_df = pd.DataFrame(user_clients_list)

    st.markdown(f"""
        <div class="header-box">
            <div>
                <h1 class="gold-title">GST Login Tool</h1>
                <div class="tagline">Palak Chudasama</div>
            </div>
            <div style="display: flex; align-items: center; gap: 15px;">
                <span class="user-badge">👤 User: {current_user}</span>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    if st.button("Logout 🚪", key="logout"):
        st.session_state['logged_in'] = False
        st.session_state['username'] = ''
        if st.session_state['driver']:
            try:
                st.session_state['driver'].quit()
            except:
                pass
        st.session_state['driver'] = None
        st.session_state['captcha_image'] = None
        st.session_state['active_gst_id'] = None
        st.rerun()

    tab1, tab2 = st.tabs(["🏛️ CLIENT DIRECTORY & LOGIN", "⚙️ DATA MANAGEMENT & EDIT"])

    # --- TAB 1: CLIENT LIST & CLOUD CAPTCHA RELAY ---
    with tab1:
        if st.session_state['captcha_image'] is not None:
            st.warning(f"⚠️ Active Connection Session for GST ID: {st.session_state['active_gst_id']}")
            st.write("The cloud server has reached the GST portal login page. Please view the CAPTCHA image below, type the characters, and submit.")
            
            col_cap1, col_cap2 = st.columns([1, 2])
            with col_cap1:
                st.image(st.session_state['captcha_image'], caption="Live GST Portal Captcha")
            with col_cap2:
                captcha_input = st.text_input("Enter Captcha Text:", key="captcha_text_input")
                if st.button("SUBMIT CAPTCHA TO GST 🚀", use_container_width=True):
                    if captcha_input:
                        submit_captcha(captcha_input)
                    else:
                        st.warning("Please type the CAPTCHA text.")
            
            if st.button("Cancel Active Session"):
                if st.session_state['driver']:
                    st.session_state['driver'].quit()
                st.session_state['driver'] = None
                st.session_state['captcha_image'] = None
                st.session_state['active_gst_id'] = None
                st.rerun()
        else:
            st.markdown("<h3 style='color: #d4af37;'>Select Client to Login</h3>", unsafe_allow_html=True)

            if client_df.empty or client_df.dropna(how="all").empty:
                st.info("💡 No clients registered yet. Go to the 'DATA MANAGEMENT & EDIT' tab to upload your Excel sheet.")
            else:
                for idx, row in client_df.iterrows():
                    c_name = row.get("Client Name", "")
                    c_id = row.get("GST ID", "")
                    c_pass = row.get("Password", "")

                    if not str(c_name).strip() and not str(c_id).strip():
                        continue

                    col_info, col_btn = st.columns([3.5, 1.2])
                    with col_info:
                        st.markdown(f"""
                            <div class="client-card">
                                <div style="font-size: 1.15rem; font-weight: 700; color: #fcf6ba; margin-bottom: 4px;">
                                    {idx + 1}. {c_name}
                                </div>
                                <div style="font-size: 0.9rem; color: #a0aab5;">
                                    <b>GST ID:</b> <span style="color: #ffffff;">{c_id}</span> &nbsp;|&nbsp; 
                                    <b>Password:</b> <span style="color: #ffffff;">{'•' * len(str(c_pass))}</span>
                                </div>
                            </div>
                        """, unsafe_allow_html=True)

                    with col_btn:
                        st.write("") 
                        if st.button(f"CONNECT SERVER 🚀", key=f"btn_{idx}", use_container_width=True):
                            init_headless_browser(c_id, c_pass)

    # --- TAB 2: DATA UPLOAD/EDIT ---
    with tab2:
        col_up, col_down = st.columns([1, 1])

        with col_up:
            st.markdown("<h4 style='color: #d4af37;'>Upload Excel Data Sheet</h4>", unsafe_allow_html=True)
            uploaded_file = st.file_uploader("Upload client sheet (Format: Name, ID, Password)", type=['xlsx', 'xls'])
            
            if uploaded_file is not None:
                try:
                    new_df = pd.read_excel(uploaded_file)
                    new_df.columns = ["Client Name", "GST ID", "Password"]
                    
                    db[current_user]["clients"] = new_df.to_dict('records')
                    save_db(db)
                    
                    st.success("Data uploaded and saved permanently! Refreshing...")
                    time.sleep(0.5)
                    st.rerun()
                except Exception as e:
                    st.error(f"Error reading file. Ensure 3 columns: Name, ID, Password. Details: {e}")

        with col_down:
            st.markdown("<h4 style='color: #d4af37;'>Download Template</h4>", unsafe_allow_html=True)
            st.write("Get the blank Excel format with header columns required for uploading client records.")
            
            sample_df = pd.DataFrame(columns=["Client Name", "GST ID", "Password"])
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                sample_df.to_excel(writer, index=False)
            
            st.download_button(
                label="📥 DOWNLOAD BLANK EXCEL TEMPLATE",
                data=buffer.getvalue(),
                file_name="GST_Client_Template.xlsx",
                mime="application/vnd.ms-excel",
                use_container_width=True
            )

        st.write("---")
        st.markdown("<h4 style='color: #d4af37;'>Edit Client Credentials Directly</h4>", unsafe_allow_html=True)
        st.write("Any changes made in this grid are saved permanently to your profile.")

        edited_df = st.data_editor(
            client_df,
            num_rows="dynamic",
            use_container_width=True,
            key="client_data_editor" 
        )
        
        if not edited_df.equals(client_df):
            db[current_user]["clients"] = edited_df.to_dict('records')
            save_db(db)
