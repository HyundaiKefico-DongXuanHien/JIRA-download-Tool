from cfg import *

from tkinter.scrolledtext import ScrolledText
import os
import pandas as pd
import datetime
import time
from datetime import datetime
import psutil
import pyautogui
import pyperclip
import shutil
from tkinter import messagebox
import traceback

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
import re

# ======================================== FUNCTION TO SETUP ========================================
# ===== Status Logging Function =====
def log_status(message):
    status_box.configure(state="normal")
    status_box.insert("end", f"{message}\n")
    status_box.see("end")
    status_box.configure(state="disabled")

# ===== Focus Chrome Function =====
def focus_chrome():
    windows = pyautogui.getWindowsWithTitle("Google Chrome")
    for window in windows:
        if not window.isActive:
            window.activate()
            time.sleep(1)
        return True
    return False

# ===== Ensrure kill Chrome driver =====
def kill_chrome_driver():
    for proc in psutil.process_iter(['pid', 'name']):
        if proc.info['name'] in ['chromedriver.exe', 'chrome.exe']:
            try:
                proc.kill()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

# ==== Auto Click Function ====
def auto_click():
    global auto_click_enabled
    while True:
        if auto_click_enabled and current_mode.get() in ["auto", "manual"]:
            pyautogui.click(1487, 823)
        time.sleep(30)


# ======================================== FUNCTION TO HANDLE WEB ========================================
# ===== Save Account =====
def save_account(): 
    saved_username.set(username_entry.get())
    saved_password.set(password_entry.get())
    log_status("💾 Saved temporary account!") 

# ===== Delete storage path =====
def remove_storage_path(path):
    for filename in os.listdir(path):
        if filename.lower().endswith(".zip"):
            file_path = os.path.join(path, filename)
            if os.path.isfile(file_path):
                os.remove(file_path)
                
# ===== Save download log =====         
def save_download_log():
    if download_log:
        now = datetime.now()
        date_str = now.strftime("%Y_%m_%d")  # ví dụ: 2025_06_11
        os.makedirs(log_excel_path, exist_ok=True)
        log_file_path = os.path.join(log_excel_path, f"{date_str}.xlsx")
        
        columns = ["Name", "Time", "Note", "Project_Name", "Requester"]

        # Tạo DataFrame mới từ log hiện tại
        new_df = pd.DataFrame(download_log, columns=columns)

        # Ép kiểu cột Time sang datetime để tránh lỗi
        new_df["Time"] = pd.to_datetime(new_df["Time"], errors="coerce")

        # Nếu file log đã tồn tại, đọc file cũ
        if os.path.exists(log_file_path):
            old_df = pd.read_excel(log_file_path)

            # Ép kiểu datetime cho log cũ
            old_df["Time"] = pd.to_datetime(old_df["Time"], errors="coerce")

            # Gộp và loại trùng theo cặp Name + Time (để tránh log trùng dòng)
            full_df = pd.concat([old_df, new_df], ignore_index=True)
            full_df = full_df.drop_duplicates(subset=["Name", "Time"])
        else:
            # Nếu chưa có file, chỉ lưu phần mới
            full_df = new_df

        # Ghi đè file log cho ngày đó
        full_df.to_excel(log_file_path, index=False)
        log_status(f"📁 Updated daily log: {log_file_path}")
        
# ===== Save log each minute ===== 
def auto_save_log_each_hour():
    last_saved_hour = None
    while True:
        now = datetime.now()
        current_minute = now.minute
        if current_minute != last_saved_hour:
            save_download_log()
            last_saved_hour = current_minute
        time.sleep(60)  # Kiểm tra mỗi phút
 
# ===== Login =====
def login(saved_username, saved_password):
   # Path to: chromedriver.exe (Put the same folder with .py)
    driver_path = os.path.join(os.getcwd(), "chromedriver.exe")
    service = Service(executable_path=driver_path)
    
    # Setup Selenium to run interface (headless)
    options = Options()
    #options.add_argument("--headless=new")  # Run browser non-interface
    options.add_argument('--no-sandbox')  # Vô hiệu hóa sandbox
    options.add_argument('--disable-dev-shm-usage')  # Tránh sử dụng /dev/shm
    options.add_argument('--remote-debugging-port=9222')  # Mở cổng gỡ lỗi từ xa
    options.add_argument('--disable-gpu')
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-software-rasterizer")
    options.add_argument("--no-zygote")
    
    driver = None
    #--------------------------------------------------------------------------------
    try:
        # Start browser
        driver = webdriver.Chrome(service=service, options=options)

        # Open login page JIRA
        driver.get("https://jira.hmg-corp.io/login.jsp")

        # Wait page loading done
        WebDriverWait(driver, 20).until(
            EC.presence_of_all_elements_located((By.ID, "username-field"))
        )

        # Insert account
        username_field = driver.find_element(By.ID, "username-field")
        time.sleep(3)
        password_field = driver.find_element(By.ID, "password-field")
        time.sleep(3)
        login_button = driver.find_element(By.ID, "login-button")

        username_field.send_keys(saved_username.get())
        time.sleep(2)
        password_field.send_keys(saved_password.get())

        # Press login
        login_button.click()

        # Wait to ensure login sucessfull
        time.sleep(5)
        
        #---------------------------------------------------------------------------------------------
        
    finally:
        # Close browser when finished
        if driver:
            driver.quit()
        kill_chrome_driver()    

def start_login():
    login(saved_username, saved_password)  
           
# ===== Login + View page source of JIRA -> get title (By Selenium + Beautifulsoup4) =====
def get_jira_title(ticket_code, username, password):
    # Path to: chromedriver.exe (Put the same folder with .py)
    driver_path = os.path.join(os.getcwd(), "chromedriver.exe")
    service = Service(executable_path=driver_path)
    
    # Setup Selenium to run interface (headless)
    options = Options()
    #options.add_argument("--headless=new")  # Run browser non-interface
    options.add_argument('--no-sandbox')  # Vô hiệu hóa sandbox
    options.add_argument('--disable-dev-shm-usage')  # Tránh sử dụng /dev/shm
    options.add_argument('--remote-debugging-port=9222')  # Mở cổng gỡ lỗi từ xa
    options.add_argument('--disable-gpu')
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-software-rasterizer")
    options.add_argument("--no-zygote")
    
    driver = None
    
    try:
        # Start browser
        driver = webdriver.Chrome(service=service, options=options)

        # Open login page JIRA
        driver.get("https://jira.hmg-corp.io/login.jsp")

        # Wait page loading done
        WebDriverWait(driver, 20).until(
            EC.presence_of_all_elements_located((By.ID, "username-field"))
        )

        # Insert account
        username_field = driver.find_element(By.ID, "username-field")
        password_field = driver.find_element(By.ID, "password-field")
        login_button = driver.find_element(By.ID, "login-button")

        username_field.send_keys(username)
        password_field.send_keys(password)

        # Press login
        login_button.click()

        # Wait to ensure login sucessfull
        time.sleep(5)

        # URL with page Jira with code ticket
        url = f"https://jira.hmg-corp.io/browse/{ticket_code}"

        # Open page ticket
        driver.get(url)

        # Get title
        page_title = driver.title

        # Print title
        print(f"Page Title: {page_title}")

        # Find all parts within square brackets
        prefix = ticket_code.split("-")[0].upper() #Take first part before "-"
        if prefix == "KVPCW" or prefix == "KVPSCUCW":
            project_name = "BLANK"
        if prefix == "KVP":       
            matches = re.findall(r"\[(.*?)\]", page_title)
            project_name = matches[1]
        if prefix == "KVHSICCU": 
            project_name = "ICCU"

        print(f"Detected project: {project_name}")
        return project_name, page_title
    
    finally:
        # Close browser when finished
        if driver:
            driver.quit()
        kill_chrome_driver()

# ===== Login + Download + Logout ===== 
def login_download_logout(ticket_code, username, password):
    # Path to: chromedriver.exe (Put the same folder with .py)
    driver_path = os.path.join(os.getcwd(), "chromedriver.exe")
    service = Service(executable_path=driver_path)
    
    # Setup Selenium to run interface (headless)
    options = Options()
    #options.add_argument("--headless=new")  # Run browser non-interface
    options.add_argument('--no-sandbox')  # Vô hiệu hóa sandbox
    options.add_argument('--disable-dev-shm-usage')  # Tránh sử dụng /dev/shm
    options.add_argument('--remote-debugging-port=9222')  # Mở cổng gỡ lỗi từ xa
    options.add_argument('--disable-gpu')
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-software-rasterizer")
    options.add_argument("--no-zygote")
    
    driver = None
    
    #---------------------------------------------------------------------------------
        # Đường dẫn thư mục bạn muốn tải về (chỉnh lại theo đường dẫn của bạn)
    download_folder = "C:/Tool Download/00. Storage"

    # Tạo thư mục tải về nếu chưa có
    if not os.path.exists(download_folder):
        os.makedirs(download_folder)

    # Cấu hình ChromeOptions để chỉ định thư mục tải về
    chrome_options = Options()
    prefs = {
        "download.default_directory": download_folder,  # Đặt thư mục tải về mặc định
        "download.prompt_for_download": False,  # Không hiện hộp thoại hỏi người dùng
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True
    }
    chrome_options.add_experimental_option("prefs", prefs)
    #--------------------------------------------------------------------------------
    
    try:
        # Start browser
        driver = webdriver.Chrome(service=service, options=options)

        # Open login page JIRA
        driver.get("https://jira.hmg-corp.io/login.jsp")

        # Wait page loading done
        WebDriverWait(driver, 20).until(
            EC.presence_of_all_elements_located((By.ID, "username-field"))
        )

        # Insert account
        username_field = driver.find_element(By.ID, "username-field")
        time.sleep(3)
        password_field = driver.find_element(By.ID, "password-field")
        time.sleep(3)
        login_button = driver.find_element(By.ID, "login-button")

        username_field.send_keys(username.get())
        time.sleep(2)
        password_field.send_keys(password.get())

        # Press login
        login_button.click()

        # Wait to ensure login sucessfull
        time.sleep(5)

        # URL with page Jira with code ticket
        url = f"https://jira.hmg-corp.io/browse/{ticket_code}"

        
        # Open page ticket
        driver.get(url)
        
        #---------------------------------------------------------------------------------------------
            # Sử dụng WebDriverWait để đợi nút "Download All" xuất hiện trên trang
        time.sleep(10)
        wait = WebDriverWait(driver, 20)  # Chờ tối đa 20 giây
        
        # Tìm và nhấp vào biểu tượng "Details, Description" để đóng
        details_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[aria-label='Details']")))
        details_button.click()
        time.sleep(2)
        description_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[aria-label='Description']")))
        description_button.click()        
        
        # Tìm và nhấp vào biểu tượng "..." để mở menu
        ellipsis_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[aria-label='Attachments Options']")))
        ellipsis_button.click()

        # Đợi menu mở ra
        time.sleep(2)
        download_all_button = wait.until(EC.element_to_be_clickable((By.ID, "aszip")))
        download_all_button.click()
        
        print(f"Tải tất cả các tệp đính kèm thành công vào thư mục: {download_folder}")
        time.sleep(10)
        pyautogui.hotkey("ctrl", "l")
        download_folder = r"C:/Tool Download/00. Storage"
        pyperclip.copy(download_folder)
        time.sleep(2)
        pyautogui.hotkey("ctrl", "v")
        pyautogui.press("enter")
        time.sleep(2)
        pyautogui.press("enter")
        time.sleep(2)
        pyautogui.press("enter")
        time.sleep(2)
        pyautogui.press("enter")
        time.sleep(5)
        #---------------------------------------------------------------------------------------------
        #---------------------WAIT DOWNLOAD DONE-------------------------------------------
        wait_time = 5  # second between check
        max_wait = 300  # max time to wait (second)
        # Wait until there is no more file .crdownload
        waited = 0
        while any(f.endswith(".crdownload") for f in os.listdir(download_folder)):
            log_status("⏳ Waiting for downloads to complete...")
            time.sleep(wait_time)
            waited += wait_time
            if waited >= max_wait:
                log_status("⚠️ Timeout waiting for downloads to finish.")
                return
        #---------------------------------------------------------------------------------------------
        #---------------------LOG OUT-------------------------------------------
        # Log out
        user_button = wait.until(EC.element_to_be_clickable((By.ID, "user-options")))
        user_button.click()
        time.sleep(2)
        logout_button = wait.until(EC.element_to_be_clickable((By.ID, "log_out")))
        logout_button.click()
        time.sleep(2)
        #---------------------------------------------------------------------------------------------
        
    finally:
        # Close browser when finished
        if driver:
            driver.quit()
        kill_chrome_driver()

# ===== Move Downloaded Files =====  
def move_downloaded_files(project_name, name_request):
    source_folder = r"C:/Tool Download/00. Storage"
    wait_time = 5  # second between check
    max_wait = 120  # max time to wait (second)
    
    if not destination_folder:
        log_status("⚠️ You haven't choose destination folder!")
        return

    os.makedirs(destination_folder, exist_ok=True)
    
    # Wait until there is no more file .crdownload
    waited = 0
    while any(f.endswith(".crdownload") for f in os.listdir(source_folder)):
        log_status("⏳ Waiting for downloads to complete...")
        time.sleep(wait_time)
        waited += wait_time
        if waited >= max_wait:
            log_status("⚠️ Timeout waiting for downloads to finish.")
            return

    # When there is no more file .crdownload, move  file .zip
    files = os.listdir(source_folder)
    zip_files = [f for f in files if f.lower().endswith(".zip")]

    if not zip_files:
        log_status("⚠️ No file to transfer")
        return

    for filename in zip_files:
        source_path = os.path.join(source_folder, filename)
        destination_path = os.path.join(destination_folder, filename)
        if os.path.isfile(source_path):
            try:
                shutil.move(source_path, destination_path)
                log_status(f"✅ Transfered: {filename}")

                if current_mode.get() in ["auto", "manual"]:
                    download_log.append([filename, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "Success", project_name, name_request])

            except Exception as e:
                log_status(f"❌ Error when transfer {filename}: {e}")
        else:
            log_status(f"⏩ Ignore when not file: {filename}")

    log_status("📦 Conpleted transfer file!")

# ===== Manual Check Function =====
def manual_loop():
    while current_mode.get() == "manual":
        try:
            txt_files = [f for f in os.listdir(auto_folder_path) if f.endswith(".txt")]
            if txt_files:
                for file_name in txt_files:
                    try:
                        remove_storage_path(storage_folder_path)
                        
                        ticket_info = file_name.replace(".txt", "")
                        if "_" not in ticket_info:
                            log_status(f"⚠️ File '{file_name}' is not true format. Ignore.")
                            continue
 
                        ticket_code, destination_key, name_request = ticket_info.split("_")
                                               
                        global auto_click_enabled
                        auto_click_enabled = False
                        
                        log_status(f"📄 Detected file: {file_name} → Ticket: {ticket_code}, Folder: {destination_key}, Name: {name_request}")
                        
                        #project_name, page_title, attachment_names = get_jira_title(ticket_code, saved_username.get(), saved_password.get())
                        #-------------------------------------LOGIN + NOTIFICATION + CHECK ---------------------------------------------------
                        # Path to: chromedriver.exe (Put the same folder with .py)
                        driver_path = os.path.join(os.getcwd(), "chromedriver.exe")
                        service = Service(executable_path=driver_path)
                        
                        # Setup Selenium to run interface (headless)
                        options = Options()
                        #options.add_argument("--headless=new")  # Run browser non-interface
                        options.add_argument('--no-sandbox')  # Vô hiệu hóa sandbox
                        options.add_argument('--disable-dev-shm-usage')  # Tránh sử dụng /dev/shm
                        options.add_argument('--remote-debugging-port=9222')  # Mở cổng gỡ lỗi từ xa
                        options.add_argument('--disable-gpu')
                        options.add_argument("--window-size=1920,1080")
                        options.add_argument("--disable-software-rasterizer")
                        options.add_argument("--no-zygote")
                        
                        driver = None
 
 
                        # Start browser
                        driver = webdriver.Chrome(service=service, options=options)

                        # Open login page JIRA
                        driver.get("https://jira.hmg-corp.io/login.jsp")

                        # Wait page loading done
                        WebDriverWait(driver, 20).until(
                            EC.presence_of_all_elements_located((By.ID, "login-form-username"))
                        )

                        # Insert account
                        username_field = driver.find_element(By.ID, "login-form-username")
                        password_field = driver.find_element(By.ID, "login-form-password")
                        login_button = driver.find_element(By.ID, "login-form-submit")

                        username_field.send_keys(saved_username.get())
                        password_field.send_keys(saved_password.get())

                        # Press login
                        login_button.click()

                        # Wait to ensure login sucessfull
                        time.sleep(5)

                        # URL with page Jira with code ticket
                        url = f"https://jira.hmg-corp.io/browse/{ticket_code}"

                        # Open page ticket
                        driver.get(url)             
                        
                        # Get title
                        page_title = driver.title

                        # Find all parts within square brackets
                        prefix = ticket_code.split("-")[0].upper() #Take first part before "-"
                        if prefix == "KVPCW" or prefix == "KVPSCUCW":
                            project_name = "BLANK"
                        if prefix == "KVP":       
                            matches = re.findall(r"\[(.*?)\]", page_title)
                            project_name = matches[1]    
                        if prefix == "KVHSICCU": 
                            project_name = "ICCU"                             
                        #---------------------------------------------------------------------------------------------------------------------

                        # Định dạng chuỗi message để bao gồm thông tin bổ sung
                        message = (
                            f"Download ticket: {ticket_code} to {destination_key}?\n\n"
                            #f"📄 Page Title: {page_title}\n"
                            #f"📎 Attachment file: {attachment_names}"
                        )

                        # Hiển thị hộp thoại xác nhận
                        confirm = messagebox.askokcancel("Confirm", message)
                        
                        if not confirm:
                            download_log.append([file_name.replace(".txt", ""), datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "Reject", project_name, name_request])
                            os.remove(os.path.join(auto_folder_path, file_name))
                            log_status(f"❌ Rejected ticket. File deleted: {file_name}")
                            
                            #-------------------------------------LOG OUT ---------------------------------------------------
                            wait = WebDriverWait(driver, 10)  # Chờ tối đa 10 giây
                            user_button = wait.until(EC.element_to_be_clickable((By.ID, "user-options")))
                            user_button.click()
                            time.sleep(2)
                            logout_button = wait.until(EC.element_to_be_clickable((By.ID, "log_out")))
                            logout_button.click()
                            time.sleep(2)                           
                            # Close browser when finished
                            if driver:
                                driver.quit()
                            kill_chrome_driver()
                            #---------------------------------------------------------------------------------------------------------------------
                            auto_click_enabled = True
                            
                            continue
                        
                        # Close browser when finished
                        if driver:
                            driver.quit()
                        kill_chrome_driver()
                        time.sleep(10)
                        login_download_logout(ticket_code, saved_username, saved_password)
                        
                        global destination_folder
                        if (destination_key.upper() == "TMS") and (project_name == "BLANK"):
                            destination_folder = r"Y:/02. Normal/02. TMS/00. Test Request/2025/2025_Q1"
                        elif (destination_key.upper() == "EMS") and (project_name == "GDI"):
                            destination_folder = r"Y:/01. National Core/_Test_Request"
                        elif (destination_key.upper() == "EMS") and (project_name == "MPI"):
                            destination_folder = r"Y:/02. Normal/01. EMS/_Test_Request"
                        elif (destination_key.upper() == "BSW") and (project_name == "ICCU"):
                            destination_folder = r"Z:/ICCU"
                        elif (destination_key.upper() == "BSW") and (project_name == "BLANK"):
                            destination_folder = r"Z:/SCU"
                        else:
                            log_status(f"⚠️ Can't detect destination folder from: {destination_key}")
                            os.remove(os.path.join(auto_folder_path, file_name))
                            log_status(f"🧹 Deleted file: {file_name} to avoid handle again")
                            auto_click_enabled = True
                            continue

                        move_downloaded_files(project_name, name_request)
                        os.remove(os.path.join(auto_folder_path, file_name))
                        log_status(f"🧹 Deleted file: {file_name} to avoid handle again")
                        
                        auto_click_enabled = True
                        
                    except Exception as inner_e:
                        log_status(f"⚠️ Error when handle file {file_name}: {inner_e}")
                        traceback.print_exc()                    
            else:
                log_status("🔎 No file in Auto folder...")
                
            time.sleep(30)
                
        except Exception as e:
            log_status(f"❌ Error in Manual Mode: {e}")
            traceback.print_exc()

# ===== Auto Mode Loop =====
def auto_loop():
    while current_mode.get() == "auto":
        try:
            txt_files = [f for f in os.listdir(auto_folder_path) if f.endswith(".txt")]
            if txt_files:
                for file_name in txt_files:
                    try:
                        remove_storage_path(storage_folder_path)
                        
                        ticket_info = file_name.replace(".txt", "")
                        if "_" not in ticket_info:
                            log_status(f"⚠️ File '{file_name}' is not true format. Ignore.")
                            continue

                        ticket_code, destination_key, name_request = ticket_info.split("_")
                        
                        global auto_click_enabled
                        auto_click_enabled = False                       

                        log_status(f"📄 Detected file: {file_name} → Ticket: {ticket_code}, Folder: {destination_key}, Name: {name_request}")

                        login_download_logout(ticket_code, saved_username, saved_password)
                        project_name, page_title = get_jira_title(ticket_code, saved_username.get(), saved_password.get())
                        
                        global destination_folder
                        if (destination_key.upper() == "TMS") and (project_name == "BLANK"):
                            destination_folder = r"Y:/02. Normal/02. TMS/00. Test Request/2025/2025_Q1"
                        elif (destination_key.upper() == "EMS") and (project_name == "GDI"):
                            destination_folder = r"Y:/01. National Core/_Test_Request"
                        elif (destination_key.upper() == "EMS") and (project_name == "MPI"):
                            destination_folder = r"Y:/02. Normal/01. EMS/_Test_Request"
                        elif (destination_key.upper() == "BSW") and (project_name == "ICCU"):
                            destination_folder = r"Z:/ICCU"
                        elif (destination_key.upper() == "BSW") and (project_name == "BLANK"):
                            destination_folder = r"Z:/SCU"
                        else:
                            log_status(f"⚠️ Can't detect destination folder from: {destination_key}")
                            os.remove(os.path.join(auto_folder_path, file_name))
                            log_status(f"🧹 Deleted file: {file_name} to avoid handle again")
                            auto_click_enabled = True
                            continue

                        move_downloaded_files(project_name, name_request)
                        
                        os.remove(os.path.join(auto_folder_path, file_name))
                        log_status(f"🧹 Deleted file: {file_name} to avoid handle again")

                        auto_click_enabled = True

                    except Exception as inner_e:
                        log_status(f"⚠️ Error when handle file {file_name}: {inner_e}")
                        traceback.print_exc()
            else:
                log_status("🔎 No file in Auto folder...")
                
            time.sleep(30)

        except Exception as e:
            log_status(f"❌ Error in Auto Mode: {e}")
            traceback.print_exc()

# ===== Switch Modes =====
def switch_to_manual():
    global auto_thread
    with mode_lock:
        if current_mode.get() == "manual":
            return
        current_mode.set("manual")
    
    # If auto_thread has gone, cancle it
    if auto_thread is not None and auto_thread.is_alive():
        auto_thread.join()
    
    # Creat new thread
    manual_thread = threading.Thread(target=manual_loop, daemon=True)
    manual_thread.start()
    
    # save_download_log()
    log_status("🛠️ Switched to MANUAL mode.")

def switch_to_auto():
    global manual_thread
    with mode_lock:
        if current_mode.get() == "auto":
            return
        current_mode.set("auto")

    # If manual_thread has gone, cancle it
    if manual_thread is not None and manual_thread.is_alive():
        manual_thread.join()    

    # Creat new thread
    auto_thread = threading.Thread(target=auto_loop, daemon=True)
    auto_thread.start()
    
    # save_download_log()
    log_status("🤖 Switched to AUTO mode.")



# ======================================== MAIN ========================================
threading.Thread(target=auto_save_log_each_hour, daemon=True).start()
threading.Thread(target=auto_click, daemon=True).start()   



# ==================== GUI ELEMENTS (basic layout only) ====================
tk.Button(root, text="🛠️ Manual", command=switch_to_manual, width=15).grid(row=0, column=0, pady=10)
tk.Button(root, text="🤖 Auto", command=switch_to_auto, width=15).grid(row=0, column=1, pady=10)

# Username & Password
tk.Label(root, text="👤 Account:").grid(row=2, column=0, sticky="e")
username_entry = tk.Entry(root, width=60)
username_entry.grid(row=2, column=1, padx=10, pady=5)

tk.Label(root, text="🔑 Password:").grid(row=3, column=0, sticky="e")
password_entry = tk.Entry(root, width=60, show="*")
password_entry.grid(row=3, column=1, padx=10, pady=5)

# Save Account Button
tk.Button(root, text="💾 Save account", command=save_account).grid(row=3, column=2, padx=10)

# Save Log Button
tk.Button(root, text="💾 Save Log", command=save_download_log).grid(row=5, column=2, padx=15)

# Status Box
status_box = ScrolledText(root, height=15, width=85, state="disabled")
status_box.grid(row=7, column=0, columnspan=3, padx=10, pady=10)

# Login
tk.Button(root, text="🔐 Log in JIRA", command=start_login, width=30).grid(row=1, column=0, columnspan=2)

root.mainloop()
            
            
            