import tkinter as tk
import threading



# ==================== GUI SETUP ====================
root = tk.Tk()
root.title("JIRA Downloader")
root.geometry("700x650")



# ==================== SETUP THREAD ====================
mode_lock = threading.Lock()
manual_thread = None
auto_thread = None
# To hold auto click flag
auto_click_enabled = True   


# ========== Global Variables ==========
destination_folder = ""
saved_username = tk.StringVar()
saved_password = tk.StringVar()
current_mode = tk.StringVar(value="idle")
auto_thread = None
auto_folder_path = r"Y:/02. Normal/04. Dowload request"
download_log = []
log_excel_path = "Y:/02. Normal/05. JIRA download tool_Log"
storage_folder_path = "C:/Tool Download/00. Storage"


 